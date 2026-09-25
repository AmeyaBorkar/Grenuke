"""Baseline v0 (Submission 1, issue #11): token candidates -> pair signals -> XGBoost -> argmax -> threshold.

    python experiments/ameya/baseline/baseline_v0.py --cands ameya-block-v0 --tag ameya-baseline-v0

- Trains on a sample of training-fold S1 (folds 5-19, C2); early stopping on a disjoint slice of training folds.
- Scores every candidate pair (streamed in chunks), keeps each record under its best S1 (exclusivity), and tunes one
  global threshold on the shared holdout (folds 0-4). Nothing is fitted on the holdout except that scalar.
- Writes C9 matches for train (holdout evaluation) and test, a report, and the dev-sample features (C8 layout) that
  Sachi uses to build the real model (issue #8).
Then: python -m ber.pipeline --stage write --split test --tag <tag> --in candidates=<cands> --in matches=<tag>
"""
from __future__ import annotations

import argparse
import json
import logging
import time

import numpy as np
import pandas as pd

from ber.artifacts import read_table, write_report, write_table
from ber.eval.metric import report
from ber.eval.splits import fold_of, in_dev_sample, is_holdout, splitmix64
from ber.paths import artifact_dir
from ber.records import load_truth
from pairfeat import add_context, load_records, pair_features

log = logging.getLogger("baseline")
CHUNK = 8_000_000


def label(cands: pd.DataFrame, truth: pd.DataFrame) -> np.ndarray:
    key = cands["s1"].to_numpy() * 4_000_000_000 + cands["r"].to_numpy()
    tkey = truth["s1"].to_numpy() * 4_000_000_000 + truth["r"].to_numpy()
    return np.isin(key, tkey).astype(np.int8)


def score_all(model, rec: dict, cands: pd.DataFrame, features: list[str]) -> np.ndarray:
    p = np.empty(len(cands), np.float32)
    for a in range(0, len(cands), CHUNK):
        b = min(a + CHUNK, len(cands))
        X = pair_features(rec, cands.iloc[a:b])[features].to_numpy(np.float32)
        p[a:b] = model.inplace_predict(X, iteration_range=(0, model.best_iteration + 1))
        log.info("scored %d / %d", b, len(cands))
    return p


def argmax_owner(cands: pd.DataFrame, p: np.ndarray) -> np.ndarray:
    """True where the pair's S1 has the highest p among all candidate S1 of that record (ties: lower s1)."""
    r = cands["r"].to_numpy()
    order = np.lexsort((cands["s1"].to_numpy(), -p, r))  # by r, then p descending, then s1
    rs = r[order]
    first = np.ones(rs.size, bool)
    first[1:] = rs[1:] != rs[:-1]
    out = np.zeros(len(p), bool)
    out[order[first]] = True
    return out


def main() -> int:
    import xgboost as xgb

    ap = argparse.ArgumentParser()
    ap.add_argument("--cands", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--train-frac", type=float, default=0.3)
    ap.add_argument("--rounds", type=int, default=800)
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    t0 = time.perf_counter()
    command = "python experiments/ameya/baseline/baseline_v0.py " + " ".join(f"--{k.replace('_', '-')} {v}" for k, v in vars(args).items())

    # ---- train split
    rec = load_records("train")
    cands = add_context(read_table("candidates", args.cands, "train"))
    truth = load_truth()
    y = label(cands, truth)
    s1 = cands["s1"].to_numpy()
    fold = fold_of(s1)
    log.info("train: %d pairs, %.3f positive, records loaded in %.0fs", len(cands), y.mean(), time.perf_counter() - t0)

    # dev-sample features for the model owner (C8 layout)
    dev = in_dev_sample(s1)
    Xd = pair_features(rec, cands[dev])
    features = list(Xd.columns)
    dev_df = pd.concat([cands.loc[dev, ["s1", "r"]].reset_index(drop=True),
                        pd.DataFrame({"fold": fold[dev].astype(np.int8), "y": y[dev]}), Xd], axis=1)
    write_table(dev_df, "features", f"{args.tag}-dev", "train", command=command, inputs={"candidates": args.cands},
                subset="dev sample (ber.eval.splits.in_dev_sample)")
    log.info("dev features: %d rows, %d features", len(dev_df), len(features))
    del Xd, dev_df

    # training sample: training folds, S1 sampled by a hash independent of the fold
    pick = (splitmix64(s1 ^ 0x5DEECE66D) % np.uint64(1000)) < np.uint64(int(args.train_frac * 1000))
    tr = (fold >= 5) & (fold <= 16) & pick
    va = (fold >= 17) & pick
    Xtr = pair_features(rec, cands[tr])[features].to_numpy(np.float32)
    Xva = pair_features(rec, cands[va])[features].to_numpy(np.float32)
    params = {"objective": "binary:logistic", "eval_metric": "logloss", "tree_method": "hist", "device": "cuda",
              "max_depth": 8, "eta": 0.08, "subsample": 0.8, "colsample_bytree": 0.8, "min_child_weight": 5,
              "max_bin": 256, "seed": args.seed}
    dtr = xgb.QuantileDMatrix(Xtr, y[tr], feature_names=features)
    dva = xgb.DMatrix(Xva, y[va], feature_names=features)
    model = xgb.train(params, dtr, args.rounds, evals=[(dva, "valid")], early_stopping_rounds=40, verbose_eval=100)
    log.info("trained: %d rows, best iteration %d", int(tr.sum()), model.best_iteration)
    del Xtr, Xva, dtr, dva

    p = score_all(model, rec, cands, features)
    own = argmax_owner(cands, p)
    hold = is_holdout(s1)
    s1_all = rec["eid"][rec["source"] == 1]
    universe = s1_all[is_holdout(s1_all)]
    country = pd.Series(load_country("train"))
    grid, best = [], (None, -1.0)
    for t in np.round(np.arange(0.20, 0.96, 0.025), 3):
        m = cands.loc[hold & own & (p > t), ["s1", "r"]]
        f = report(m, truth, universe)["macro_f05"]
        grid.append((float(t), f))
        if f > best[1]:
            best = (float(t), f)
    t_best = best[0]
    log.info("threshold %.3f -> holdout macro F0.5 %.4f", *best)
    m_train = cands.loc[own & (p > t_best), ["s1", "r"]].reset_index(drop=True)
    write_table(m_train, "matches", args.tag, "train", command=command, inputs={"candidates": args.cands},
                threshold=t_best)
    rep = report(m_train[m_train["s1"].isin(universe)], truth, universe, groups=country)
    rep["by_country"] = rep.pop("by_group")
    importance = model.get_score(importance_type="gain")

    # ---- test split (waits for the test candidates if blocking is still running)
    from ber.paths import artifact_path
    while not artifact_path("candidates", args.cands, "test").exists():
        log.info("waiting for the test candidates of %s", args.cands)
        time.sleep(30)
    rec_t = load_records("test")
    cands_t = add_context(read_table("candidates", args.cands, "test"))
    p_t = score_all(model, rec_t, cands_t, features)
    own_t = argmax_owner(cands_t, p_t)
    m_test = cands_t.loc[own_t & (p_t > t_best), ["s1", "r"]].reset_index(drop=True)
    write_table(m_test, "matches", args.tag, "test", command=command, inputs={"candidates": args.cands},
                threshold=t_best)
    ct = pd.Series(load_country("test"))
    diag = (m_test.assign(c=ct.reindex(m_test["s1"]).to_numpy()).groupby("c").size()
            / ct[ct.index // 1_000_000_000 == 1].value_counts()).round(3).to_dict()
    in_hold = m_train["s1"].isin(universe)
    hold_pred = (m_train[in_hold].assign(c=country.reindex(m_train.loc[in_hold, "s1"]).to_numpy()).groupby("c").size()
                 / country.loc[universe].value_counts()).round(3).to_dict()
    payload = {"holdout": rep, "threshold": t_best, "threshold_grid": grid, "best_iteration": model.best_iteration,
               "mean_pred_per_s1": {"holdout": hold_pred, "test": diag}, "features": features,
               "gain": dict(sorted(importance.items(), key=lambda kv: -kv[1])[:15]),
               "runtime_s": round(time.perf_counter() - t0)}
    write_report(args.tag, payload, command=command, inputs={"candidates": args.cands})
    model_dir = artifact_dir("models", args.tag)
    model_dir.mkdir(parents=True, exist_ok=True)
    model.save_model(str(model_dir / "xgb.ubj"))
    (model_dir / "decide.json").write_text(json.dumps({"threshold": t_best, "features": features}), encoding="utf-8")
    print(json.dumps({k: payload[k] for k in ("holdout", "threshold", "mean_pred_per_s1", "gain", "runtime_s")}, indent=1, default=str))
    return 0


def load_country(split: str) -> pd.Series:
    import pyarrow.parquet as pq

    from ber.paths import records_path

    t = pq.read_table(records_path(split), columns=["eid", "country"])
    return pd.Series(t["country"].to_numpy(zero_copy_only=False), index=t["eid"].to_numpy())


if __name__ == "__main__":
    raise SystemExit(main())
