"""Stage 0 + stage 1 (model-v1 experiments): a cheap filter, then XGBoost with out-of-fold scores.

    python experiments/ameya/model-v1/s1.py --feats ameya-fx1 --tag ameya-s1-v1

- Stage 0: a small XGBoost on a 10% S1 sample of training folds. Pairs with p0 < tau0 skip stage 1 (p1 = p0);
  tau0 keeps 99.95% of the training positives outside the sample.
- Stage 1: one model per OOF group (C2). Each trains on the other two groups' kept rows (minus a 2% S1 slice used
  for early stopping) and scores its own group; the holdout and test get the mean of the three models.
  With ``--all`` (final fit) the holdout is a fourth group: four models, each on the other three groups (75% of train
  instead of 50%); every train pair, holdout included, gets an out-of-fold score and test gets the mean of four.
- Writes work/scores/<tag>/{train,test}.parquet (s1, r, p0, p1; fold, y on train; row-aligned with the
  candidates), the models, and a report: holdout macro F0.5 with argmax ownership + the best global threshold.
"""
from __future__ import annotations

import argparse
import json
import logging
import time

import numpy as np
import pandas as pd
import xgboost as xgb

from ber.artifacts import write_report, write_table
from ber.eval.gates import compare
from ber.eval.splits import is_holdout, oof_group
from ber.paths import artifact_dir, artifact_path
from ber.records import load_truth
from common import (argmax_owner, feature_names, holdout_report, holdout_universe, iter_matrix, load_keys,
                    load_matrix, s1_hash_slice, sweep)

log = logging.getLogger("s1")
BASE = {"objective": "binary:logistic", "eval_metric": "logloss", "tree_method": "hist", "device": "cuda",
        "max_bin": 256, "subsample": 0.8, "min_child_weight": 5}
PARAMS0 = {**BASE, "max_depth": 6, "eta": 0.2, "colsample_bytree": 0.8}
PARAMS1 = {**BASE, "max_depth": 9, "eta": 0.06, "colsample_bytree": 0.7, "min_child_weight": 10, "lambda": 2.0}
SALT0, SALT1 = 0x51A6E0, 0x51A6E1


def n_trees(b) -> int:
    """Trees to use: up to the early-stopping best iteration when there is one."""
    best = b.attr("best_iteration")
    return int(best) + 1 if best is not None else b.num_boosted_rounds()


def predict(boosters: list, feats: str, split: str, features: list[str], rows: np.ndarray | None, n: int) -> np.ndarray:
    """Mean prediction of ``boosters`` for the rows where ``rows`` is True (NaN elsewhere)."""
    out = np.full(n, np.nan, np.float32)
    for start, sel, X in iter_matrix(feats, split, features, rows):
        p = np.mean([b.inplace_predict(X, iteration_range=(0, n_trees(b))) for b in boosters], axis=0)
        idx = start + np.flatnonzero(sel)
        out[idx] = p
    return out


def score_test(args, command: str, test_groups: list[str]) -> None:
    """Test scores from the saved stage-0/1 models (lean re-run, e.g. with other test feature groups)."""
    import common
    mdir = artifact_dir("models", args.models or args.tag)
    cfg = json.loads((mdir / "config.json").read_text())
    features, tau0 = cfg["features"], cfg["tau0"]
    b0 = xgb.Booster(model_file=str(mdir / "stage0.ubj"))
    boosters = [xgb.Booster(model_file=str(mdir / f"stage1_g{g}.ubj")) for g in range(len(cfg["best_iterations"]))]
    for b, it in zip(boosters, cfg["best_iterations"]):
        b.set_attr(best_iteration=str(it))
    common.GROUPS[:] = test_groups
    kt = load_keys(args.feats, "test")
    nt = len(kt)
    p0t = predict([b0], args.feats, "test", features, None, nt)
    keep_t = p0t >= tau0
    p1t = p0t.copy()
    pt = predict(boosters, args.feats, "test", features, keep_t, nt)
    p1t[keep_t] = pt[keep_t]
    out_dir = artifact_dir("models", args.tag)
    if out_dir != mdir:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "config.json").write_text(json.dumps({**cfg, "models_from": args.models,
                                                         "test_groups": test_groups}, indent=1))
    write_table(pd.DataFrame({"s1": kt["s1"], "r": kt["r"], "p0": p0t, "p1": p1t}), "scores", args.tag, "test",
                command=command, inputs={"features": args.feats, "models": args.models or args.tag}, tau0=tau0)
    log.info("test scores written: %d pairs, %d kept by stage 0", nt, int(keep_t.sum()))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--feats", default="ameya-fx1")
    ap.add_argument("--tag", default="ameya-s1-v1")
    ap.add_argument("--rounds", type=int, default=4000)
    ap.add_argument("--keep-pos", type=float, default=0.9995)
    ap.add_argument("--drop", default="", help="comma-separated features to leave out")
    ap.add_argument("--no-test", action="store_true")
    ap.add_argument("--groups", default="str,cx", help="feature files <feats>-<group> to use")
    ap.add_argument("--test-groups", default="", help="feature groups for test (default: --groups), e.g. lop for lo")
    ap.add_argument("--test-only", action="store_true", help="only score test with the saved models of --models")
    ap.add_argument("--models", default="", help="tag of the saved models for --test-only (default: --tag)")
    ap.add_argument("--all", action="store_true", help="final fit: the holdout is a fourth OOF group")
    args = ap.parse_args()
    import common
    common.GROUPS[:] = args.groups.split(",")
    test_groups = (args.test_groups or args.groups).split(",")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    command = "python experiments/ameya/model-v1/s1.py " + " ".join(f"--{k.replace('_', '-')} {v}" for k, v in vars(args).items())
    t0 = time.perf_counter()
    import warnings
    warnings.filterwarnings("ignore", message=".*Falling back to prediction using DMatrix.*")
    warnings.filterwarnings("ignore", category=UserWarning, module="xgboost")

    if args.test_only:
        score_test(args, command, test_groups)
        return 0
    drop = set(filter(None, args.drop.split(",")))
    features = [f for f in feature_names(args.feats) if f not in drop]
    keys = load_keys(args.feats, "train")
    s1, r, fold, y = (keys[c].to_numpy() for c in ("s1", "r", "fold", "y"))
    n = len(keys)
    train_rows = fold >= 5
    log.info("train: %d pairs, %d features, %.3f positive", n, len(features), y.mean())

    # ---- stage 0
    sample = train_rows & s1_hash_slice(s1, SALT0, 10)
    X0 = load_matrix(args.feats, "train", features, sample)
    b0 = xgb.train(PARAMS0, xgb.QuantileDMatrix(X0, y[sample], feature_names=features), 200)
    del X0
    p0 = predict([b0], args.feats, "train", features, None, n)
    honest = train_rows & ~sample & (y == 1)
    tau0 = float(np.quantile(p0[honest], 1 - args.keep_pos))
    kept = p0 >= tau0
    log.info("stage 0: tau0 %.5f keeps %.4f of pairs and %.5f of positives (%.0fs)", tau0, kept.mean(),
             kept[honest].mean(), time.perf_counter() - t0)

    # ---- stage 1, out of fold
    rows1 = kept if args.all else train_rows & kept
    X1 = load_matrix(args.feats, "train", features, rows1)
    y1, g1 = y[rows1], oof_group(s1[rows1])
    n_groups = 3
    if args.all:
        g1 = np.where(g1 < 0, 3, g1).astype(np.int8)
        n_groups = 4
    es1 = s1_hash_slice(s1[rows1], SALT1, 50)
    idx1 = np.flatnonzero(rows1)
    p1 = p0.copy()
    boosters, best_its = [], []
    for g in range(n_groups):
        tr, va = (g1 != g) & ~es1, (g1 != g) & es1
        dtr = xgb.QuantileDMatrix(X1[tr], y1[tr], feature_names=features)
        dva = xgb.QuantileDMatrix(X1[va], y1[va], feature_names=features, ref=dtr)
        b = xgb.train(PARAMS1, dtr, args.rounds, evals=[(dva, "es")], early_stopping_rounds=60, verbose_eval=250)
        del dtr, dva
        own = g1 == g
        p1[idx1[own]] = b.inplace_predict(X1[own], iteration_range=(0, n_trees(b)))
        boosters.append(b)
        best_its.append(int(b.best_iteration))
        log.info("stage 1 group %d: best iteration %d, es logloss %.5f (%.0fs)", g, b.best_iteration, b.best_score,
                 time.perf_counter() - t0)
    del X1
    if not args.all:  # the holdout gets the mean of the three models (with --all it is out of fold already)
        hold_rows = ~train_rows & kept
        ph = predict(boosters, args.feats, "train", features, hold_rows, n)
        p1[hold_rows] = ph[hold_rows]

    out_dir = artifact_dir("models", args.tag)
    out_dir.mkdir(parents=True, exist_ok=True)
    b0.save_model(str(out_dir / "stage0.ubj"))
    for g, b in enumerate(boosters):
        b.save_model(str(out_dir / f"stage1_g{g}.ubj"))
    (out_dir / "config.json").write_text(json.dumps({"features": features, "tau0": tau0, "params0": PARAMS0,
                                                     "params1": PARAMS1, "best_iterations": best_its}, indent=1))
    scores = pd.DataFrame({"s1": s1, "r": r, "fold": fold, "y": y, "p0": p0, "p1": p1})
    write_table(scores, "scores", args.tag, "train", command=command, inputs={"features": args.feats}, tau0=tau0)

    # ---- holdout: argmax + global threshold, and the gate against the baseline
    truth = load_truth()
    universe, country = holdout_universe()
    own = argmax_owner(s1, r, p1)
    t_best, f_best, grid = sweep(scores, p1, own, truth, universe)
    pred = scores.loc[own & (p1 > t_best), ["s1", "r"]]
    rep = holdout_report(pred, truth, universe, country)
    from ber.artifacts import read_table
    base = read_table("matches", "ameya-baseline-v0", "train")
    gate = compare(base, pred, truth[truth["s1"].isin(universe)], universe, groups=country)
    imp = boosters[0].get_score(importance_type="gain")
    payload = {"holdout": rep, "threshold": t_best, "grid": grid, "gate_vs_baseline_v0": gate, "tau0": tau0,
               "kept_share": float(kept.mean()), "best_iterations": best_its,
               "gain_top25": dict(sorted(imp.items(), key=lambda kv: -kv[1])[:25])}
    log.info("holdout macro F0.5 %.4f at threshold %.3f (baseline v0 %.4f, delta %+.4f CI [%.4f, %.4f])",
             rep["macro_f05"], t_best, gate["base_f05"], gate["delta"], gate["ci_low"], gate["ci_high"])

    # ---- test
    if not args.no_test:
        common.GROUPS[:] = test_groups
        while not artifact_path("features", f"{args.feats}-cx", "test").exists() or \
                not artifact_path("features", f"{args.feats}-str", "test").exists():
            log.info("waiting for the test features")
            time.sleep(60)
        kt = load_keys(args.feats, "test")
        nt = len(kt)
        p0t = predict([b0], args.feats, "test", features, None, nt)
        keep_t = p0t >= tau0
        p1t = p0t.copy()
        pt = predict(boosters, args.feats, "test", features, keep_t, nt)
        p1t[keep_t] = pt[keep_t]
        write_table(pd.DataFrame({"s1": kt["s1"], "r": kt["r"], "p0": p0t, "p1": p1t}), "scores", args.tag, "test",
                    command=command, inputs={"features": args.feats}, tau0=tau0)
        payload["test_kept_share"] = float(keep_t.mean())
    payload["runtime_s"] = round(time.perf_counter() - t0)
    write_report(args.tag, payload, command=command, inputs={"features": args.feats})
    print(json.dumps({k: payload[k] for k in ("holdout", "threshold", "gate_vs_baseline_v0", "kept_share",
                                              "best_iterations", "runtime_s")}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
