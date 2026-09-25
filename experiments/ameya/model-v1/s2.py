"""Stage 2 (collective model, FINAL_PLAN section 4.6) + isotonic calibration, on stage-1 out-of-fold scores.

    python experiments/ameya/model-v1/s2.py --feats ameya-fx1 --s1 ameya-s1-v1 --tag ameya-s2-v1

- Group features over the **full** candidate graph (every S1 and record of the split), from p1:
  - per record: best and second-best p1 among its S1, this pair's margin to the best rival, its rank, the number of
    S1 above 0.5, the sum of p1 and this pair's share of it;
  - per S1: this record's rank, the max and sum of p1 (expected cluster size), counts above 0.5/0.8/0.95, the gaps
    to the neighbouring ranks, and the same-source sums and confident counts without this pair (source balance).
- Stage-2 rows: stage-1 rows (p0 >= tau0) with p1 >= P_MIN (the others keep p2 = p1; they are never predicted). Features: the group
  features, p1 and its logit, and the top stage-1 features by gain.
- Out of fold over the same three groups (C2): p1 of training folds is already out of fold, so stage 2 learns from
  honest scores; the holdout and test get the mean of the three stage-2 models.
- Isotonic calibration fitted on the out-of-fold p2 of training folds only (never the holdout), applied everywhere.
Writes work/scores/<tag>/{train,test}.parquet: s1, r, p1, p2, pc (calibrated p2), plus fold, y on train.
"""
from __future__ import annotations

import argparse
import json
import logging
import time

import numpy as np
import pandas as pd
import xgboost as xgb
from numba import njit, prange

from ber.artifacts import read_table, write_report, write_table
from ber.eval.gates import compare
from ber.eval.splits import oof_group
from ber.paths import artifact_dir, artifact_path
from ber.records import load_truth
from common import FastEval, argmax_owner, holdout_report, holdout_universe, load_matrix, s1_hash_slice

log = logging.getLogger("s2")
P_MIN = 0.002
PARAMS2 = {"objective": "binary:logistic", "eval_metric": "logloss", "tree_method": "hist", "device": "cuda",
           "max_bin": 256, "subsample": 0.8, "min_child_weight": 10, "max_depth": 7, "eta": 0.05,
           "colsample_bytree": 0.8, "lambda": 2.0}
SALT2 = 0x51A6E2
R_FEATS = ("r_rank", "r_best", "r_second", "r_margin", "r_n05", "r_sum", "r_share", "r_n")
S_FEATS = ("s_rank", "s_max", "s_sum", "s_n05", "s_n08", "s_n095", "s_gap_up", "s_gap_down", "s_sum_same_src",
           "s_n08_same_src", "s_sum_other_src", "s_n")


@njit(parallel=True, cache=True)
def _record_side(starts, order, p, pos, out):
    for g in prange(starts.size - 1):
        a, b = starts[g], starts[g + 1]
        best = p[order[a]]
        second = p[order[a + 1]] if b - a > 1 else 0.0
        tot = 0.0
        n05 = 0
        for k in range(a, b):
            v = p[order[k]]
            tot += v
            if v > 0.5:
                n05 += 1
        for k in range(a, b):
            i = order[k]
            o = pos[i]
            if o < 0:
                continue
            v = p[i]
            out[0, o] = k - a
            out[1, o] = best
            out[2, o] = second
            out[3, o] = v - (second if k == a else best)
            out[4, o] = n05
            out[5, o] = tot
            out[6, o] = v / tot if tot > 0 else 0.0
            out[7, o] = b - a


@njit(parallel=True, cache=True)
def _s1_side(starts, order, p, is_s3, pos, out):
    for g in prange(starts.size - 1):
        a, b = starts[g], starts[g + 1]
        tot = 0.0
        n05 = 0
        n08 = 0
        n095 = 0
        sum2 = 0.0
        sum3 = 0.0
        c2 = 0
        c3 = 0
        for k in range(a, b):
            i = order[k]
            v = p[i]
            tot += v
            if v > 0.5:
                n05 += 1
            if v > 0.8:
                n08 += 1
                if is_s3[i]:
                    c3 += 1
                else:
                    c2 += 1
            if v > 0.95:
                n095 += 1
            if is_s3[i]:
                sum3 += v
            else:
                sum2 += v
        for k in range(a, b):
            i = order[k]
            o = pos[i]
            if o < 0:
                continue
            v = p[i]
            same_sum, other_sum, same_n = (sum3, sum2, c3) if is_s3[i] else (sum2, sum3, c2)
            out[0, o] = k - a
            out[1, o] = p[order[a]]
            out[2, o] = tot
            out[3, o] = n05
            out[4, o] = n08
            out[5, o] = n095
            out[6, o] = p[order[k - 1]] - v if k > a else 0.0
            out[7, o] = v - p[order[k + 1]] if k + 1 < b else v
            out[8, o] = same_sum - v
            out[9, o] = same_n - (1 if v > 0.8 else 0)
            out[10, o] = other_sum
            out[11, o] = b - a


def _grouped(key: np.ndarray, p: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    order = np.lexsort((-p, key))
    k = key[order]
    starts = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return np.append(starts, k.size).astype(np.int64), order.astype(np.int64)


def group_features(s1: np.ndarray, r: np.ndarray, p1: np.ndarray, rows: np.ndarray) -> dict[str, np.ndarray]:
    """Group features over all pairs, returned for the pairs where ``rows`` is True (in row order)."""
    m = int(rows.sum())
    pos = np.full(p1.size, -1, np.int64)
    pos[rows] = np.arange(m)
    out_r = np.zeros((len(R_FEATS), m), np.float32)
    starts, order = _grouped(r, p1)
    _record_side(starts, order, p1, pos, out_r)
    out_s = np.zeros((len(S_FEATS), m), np.float32)
    starts, order = _grouped(s1, p1)
    _s1_side(starts, order, p1, (r // 1_000_000_000 == 3), pos, out_s)
    cols = {f"s2__{f}": out_r[i] for i, f in enumerate(R_FEATS)}
    cols.update({f"s2__{f}": out_s[i] for i, f in enumerate(S_FEATS)})
    return cols


def build(scores: pd.DataFrame, feats: str, split: str, s1_feats: list[str], rows: np.ndarray,
          cluster: bool = False) -> tuple[np.ndarray, list[str]]:
    cols = group_features(scores["s1"].to_numpy(), scores["r"].to_numpy(), scores["p1"].to_numpy(np.float32), rows)
    if cluster:  # gate G9: similarity to the S1's confident records
        from cluster import support
        from feats import load_records
        rec, _ = load_records(split, pd.read_parquet(artifact_dir("models", feats) / "indic_dict.parquet"),
                              strings=False)
        cols.update(support(rec, scores["s1"].to_numpy(), scores["r"].to_numpy(), scores["p1"].to_numpy(np.float32),
                            rows))
        del rec
    p1 = np.clip(scores["p1"].to_numpy(np.float32)[rows], 1e-6, 1 - 1e-6)
    cols["s2__p1"] = p1
    cols["s2__logit_p1"] = np.log(p1 / (1 - p1)).astype(np.float32)
    names = list(cols)
    X = np.empty((int(rows.sum()), len(names) + len(s1_feats)), np.float32)
    for i, c in enumerate(names):
        X[:, i] = cols[c]
    del cols
    X[:, len(names):] = load_matrix(feats, split, s1_feats, rows)
    return X, names + s1_feats


def score_test(args, command: str) -> None:
    """Test scores from the saved stage-2 models and calibration; no train data in memory (lean re-run)."""
    cfg1 = json.loads((artifact_dir("models", args.s1) / "config.json").read_text())
    mdir = artifact_dir("models", args.tag)
    cfg2 = json.loads((mdir / "config.json").read_text())
    boosters = [xgb.Booster(model_file=str(mdir / f"stage2_g{g}.ubj")) for g in range(3)]
    iso = pd.read_parquet(mdir / "isotonic.parquet")
    st = read_table("scores", args.s1, "test")
    rows_t = (st["p0"].to_numpy() >= cfg1["tau0"]) & (st["p1"].to_numpy() >= P_MIN)
    Xt, names = build(st, args.feats, "test", cfg2["s1_feats"], rows_t, args.cluster)
    if names != cfg2["features"]:
        raise ValueError("test features do not match the saved stage-2 models")
    p2t = st["p1"].to_numpy(np.float32).copy()
    idt = np.flatnonzero(rows_t)
    p2t[idt] = np.mean([b.inplace_predict(Xt, iteration_range=(0, it + 1))
                        for b, it in zip(boosters, cfg2["best_iterations"])], axis=0)
    del Xt
    pct = p2t.copy()
    pct[idt] = np.interp(p2t[idt], iso["x"].to_numpy(), iso["y"].to_numpy()).astype(np.float32)  # = isotonic (clip)
    write_table(pd.DataFrame({"s1": st["s1"], "r": st["r"], "p1": st["p1"], "p2": p2t, "pc": pct}), "scores",
                args.tag, "test", command=command, inputs={"scores": args.s1, "features": args.feats})
    log.info("test scores written: %d pairs, %d stage-2 rows", len(st), idt.size)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--feats", default="ameya-fx1")
    ap.add_argument("--s1", default="ameya-s1-v1")
    ap.add_argument("--tag", default="ameya-s2-v1")
    ap.add_argument("--top", type=int, default=30, help="stage-1 features kept, by gain")
    ap.add_argument("--rounds", type=int, default=3000)
    ap.add_argument("--no-test", action="store_true")
    ap.add_argument("--groups", default="str,cx", help="feature files <feats>-<group> to use")
    ap.add_argument("--cluster", action="store_true", help="add cluster-support features (G9)")
    ap.add_argument("--test-only", action="store_true", help="only score test with the saved models (lean re-run)")
    args = ap.parse_args()
    import common
    common.GROUPS[:] = args.groups.split(",")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning, module="xgboost")
    command = "python experiments/ameya/model-v1/s2.py " + " ".join(f"--{k.replace('_', '-')} {v}" for k, v in vars(args).items())
    t0 = time.perf_counter()
    if args.test_only:
        score_test(args, command)
        return 0

    cfg = json.loads((artifact_dir("models", args.s1) / "config.json").read_text())
    b = xgb.Booster(model_file=str(artifact_dir("models", args.s1) / "stage1_g0.ubj"))
    gain = b.get_score(importance_type="gain")
    s1_feats = [f for f, _ in sorted(gain.items(), key=lambda kv: -kv[1])][:args.top]
    del b

    sc = read_table("scores", args.s1, "train")
    fold, y = sc["fold"].to_numpy(), sc["y"].to_numpy()
    rows = (sc["p0"].to_numpy() >= cfg["tau0"]) & (sc["p1"].to_numpy() >= P_MIN)  # stage-1 rows only
    X, names = build(sc, args.feats, "train", s1_feats, rows, args.cluster)
    idx = np.flatnonzero(rows)
    yr, fr = y[rows], fold[rows]
    train_rows = fr >= 5
    g2 = np.where(train_rows, oof_group(np.where(train_rows, sc["s1"].to_numpy()[rows], 0)), -1)
    es = s1_hash_slice(sc["s1"].to_numpy()[rows], SALT2, 50)
    log.info("stage 2: %d rows (%.3f of pairs, %.5f of positives), %d features (%.0fs)", rows.sum(), rows.mean(),
             rows[y == 1].mean(), len(names), time.perf_counter() - t0)

    p2 = sc["p1"].to_numpy(np.float32).copy()
    boosters, best_its = [], []
    for g in range(3):
        tr = train_rows & (g2 != g) & ~es
        va = train_rows & (g2 != g) & es
        dtr = xgb.QuantileDMatrix(X[tr], yr[tr], feature_names=names)
        dva = xgb.QuantileDMatrix(X[va], yr[va], feature_names=names, ref=dtr)
        bst = xgb.train(PARAMS2, dtr, args.rounds, evals=[(dva, "es")], early_stopping_rounds=60, verbose_eval=250)
        del dtr, dva
        own = train_rows & (g2 == g)
        p2[idx[own]] = bst.inplace_predict(X[own], iteration_range=(0, bst.best_iteration + 1))
        boosters.append(bst)
        best_its.append(int(bst.best_iteration))
        log.info("stage 2 group %d: best iteration %d, es logloss %.5f (%.0fs)", g, bst.best_iteration,
                 bst.best_score, time.perf_counter() - t0)
    hold = ~train_rows
    p2[idx[hold]] = np.mean([bst.inplace_predict(X[hold], iteration_range=(0, bst.best_iteration + 1))
                             for bst in boosters], axis=0)
    del X

    # isotonic calibration on out-of-fold p2 of training folds (stage-2 rows only; the rest are ~0)
    from sklearn.isotonic import IsotonicRegression
    iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    fit_rows = idx[train_rows]
    iso.fit(p2[fit_rows].astype(np.float64), y[fit_rows])
    pc = p2.copy()
    pc[idx] = iso.predict(p2[idx].astype(np.float64)).astype(np.float32)

    out_dir = artifact_dir("models", args.tag)
    out_dir.mkdir(parents=True, exist_ok=True)
    for g, bst in enumerate(boosters):
        bst.save_model(str(out_dir / f"stage2_g{g}.ubj"))
    pd.DataFrame({"x": iso.X_thresholds_, "y": iso.y_thresholds_}).to_parquet(out_dir / "isotonic.parquet")
    (out_dir / "config.json").write_text(json.dumps({"features": names, "s1_feats": s1_feats, "p_min": P_MIN,
                                                     "params2": PARAMS2, "best_iterations": best_its}, indent=1))
    out = pd.DataFrame({"s1": sc["s1"], "r": sc["r"], "fold": fold, "y": y, "p1": sc["p1"], "p2": p2, "pc": pc})
    write_table(out, "scores", args.tag, "train", command=command, inputs={"scores": args.s1, "features": args.feats})

    # holdout: reliability and argmax + threshold on p2, against the baseline and stage 1
    truth = load_truth()
    universe, country = holdout_universe()
    s1a, ra = out["s1"].to_numpy(), out["r"].to_numpy()
    hmask = np.isin(s1a, universe) & (p2 > 0.01)
    bins = np.clip((pc[hmask] * 10).astype(int), 0, 9)
    rel = pd.DataFrame({"bin": bins, "p": pc[hmask], "y": y[hmask]}).groupby("bin").agg(p=("p", "mean"), y=("y", "mean"), n=("y", "size"))
    res = {}
    base = read_table("matches", "ameya-baseline-v0", "train")
    th = truth[truth["s1"].isin(universe)]
    fe = FastEval(s1a, ra, truth, universe)
    for name, p in (("p1", out["p1"].to_numpy(np.float32)), ("p2", p2), ("pc", pc)):
        own = argmax_owner(s1a, ra, p)
        t_best, f_best, grid = fe.sweep(p, own)
        pred = out.loc[own & (p > t_best), ["s1", "r"]]
        res[name] = {"threshold": t_best, "holdout": holdout_report(pred, truth, universe, country),
                     "gate_vs_baseline_v0": compare(base, pred, th, universe, groups=country)}
        log.info("%s: holdout macro F0.5 %.4f at threshold %.3f (delta vs v0 %+.4f)", name,
                 res[name]["holdout"]["macro_f05"], t_best, res[name]["gate_vs_baseline_v0"]["delta"])
    payload = {"results": res, "reliability_holdout": rel.round(4).reset_index().to_dict("records"),
               "stage2_rows": int(rows.sum()), "best_iterations": best_its}

    if not args.no_test:
        st = read_table("scores", args.s1, "test")
        rows_t = (st["p0"].to_numpy() >= cfg["tau0"]) & (st["p1"].to_numpy() >= P_MIN)
        Xt, _ = build(st, args.feats, "test", s1_feats, rows_t, args.cluster)
        p2t = st["p1"].to_numpy(np.float32).copy()
        idt = np.flatnonzero(rows_t)
        p2t[idt] = np.mean([bst.inplace_predict(Xt, iteration_range=(0, bst.best_iteration + 1)) for bst in boosters],
                           axis=0)
        del Xt
        pct = p2t.copy()
        pct[idt] = iso.predict(p2t[idt].astype(np.float64)).astype(np.float32)
        write_table(pd.DataFrame({"s1": st["s1"], "r": st["r"], "p1": st["p1"], "p2": p2t, "pc": pct}), "scores",
                    args.tag, "test", command=command, inputs={"scores": args.s1, "features": args.feats})
    payload["runtime_s"] = round(time.perf_counter() - t0)
    write_report(args.tag, payload, command=command, inputs={"scores": args.s1, "features": args.feats})
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "gate_vs_baseline_v0"} for k, v in res.items()},
                     indent=1, default=str))
    print(json.dumps(payload["reliability_holdout"], default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
