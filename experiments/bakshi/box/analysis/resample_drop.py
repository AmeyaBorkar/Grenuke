#!/usr/bin/env python3
"""Public/private split noise and the stability of the 7B drop rule, on the labelled holdout (METHODOLOGY_bakshi.md §5).

1. Sampling noise of a public/private split: per-S1 macro F0.5 of the g0 stage-3 decisions on the shared holdout
   (549,699 US/India S1); for each public fraction, the sd of (public mean - private mean) over 3,000 random S1 splits.
2. The 7B drop rule (drop a predicted pair outside the band, p1 > 0.99, when its q7 logit < --t) on the holdout sample
   scored by score_pairs.py (186,897 S1): the gain on all S1, then its mean, sd and P(gain <= 0) over 3,000 random 25%
   subsets of S1.

One generator (seed 0) drives both parts in this order, as in the run of 29 Sep that the methodology cites.

    python resample_drop.py --g0 work/matches/ameya-model-g0-s3/train.parquet --rescore box/rescore
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from ber.records import load_truth
from common import holdout_universe

K = 4_000_000_000


def key(d: pd.DataFrame) -> np.ndarray:
    return d.s1.to_numpy(np.int64) * K + d.r.to_numpy(np.int64)


def per_s1_f05(pred: pd.DataFrame, truth: pd.DataFrame, universe: np.ndarray, ntrue: np.ndarray) -> np.ndarray:
    """F0.5 of every S1 in `universe` (an empty prediction on an S1 without matches scores 1)."""
    p = pred.copy()
    p["y"] = np.isin(key(p), key(truth))
    g = p.groupby("s1").agg(tp=("y", "sum"), n=("y", "size")).reindex(universe).fillna(0)
    tp, n = g.tp.to_numpy(), g.n.to_numpy()
    fp, fn = n - tp, ntrue - tp
    den = 1.25 * tp + 0.25 * fn + fp
    return np.where((n == 0) & (ntrue == 0), 1.0, np.where(den > 0, 1.25 * tp / np.maximum(den, 1e-12), 0.0))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--g0", required=True, help="stage-3 decision matches of g0 on the train split (parquet s1, r)")
    ap.add_argument("--rescore", required=True, help="dir with hold_scored.parquet and hold_truth.parquet")
    ap.add_argument("--t", type=float, default=-6.0)
    ap.add_argument("--draws", type=int, default=3000)
    a = ap.parse_args()
    rng = np.random.default_rng(0)

    universe, country = holdout_universe()
    universe = np.asarray(universe)
    c = country.reindex(universe).to_numpy()
    truth = load_truth()
    truth = truth[np.isin(truth.s1.to_numpy(), universe)]
    ntrue = truth.groupby("s1").size().reindex(universe).fillna(0).to_numpy()
    pred = pd.read_parquet(a.g0, columns=["s1", "r"])
    f = per_s1_f05(pred[np.isin(pred.s1.to_numpy(), universe)], truth, universe, ntrue)
    print(f"g0-s3 holdout: {universe.size:,} S1, macro F0.5 {f.mean():.6f} "
          f"(US {f[c == 'US'].mean():.6f}, India {f[c == 'India'].mean():.6f})")
    for frac in (0.1, 0.25, 0.5):
        gap = []
        for _ in range(a.draws):
            m = rng.random(universe.size) < frac
            gap.append(f[m].mean() - f[~m].mean())
        gap = np.array(gap)
        print(f"  public = {int(frac * 100)}% of S1: public - private gap sd {gap.std():.6f} (95% within +/-{1.96 * gap.std():.6f})")

    h = pd.read_parquet(f"{a.rescore}/hold_scored.parquet")
    ht = pd.read_parquet(f"{a.rescore}/hold_truth.parquet").set_index("s1")
    u, nt = ht.index.to_numpy(), ht.n_true.to_numpy()
    base = per_s1_f05(h[["s1", "r"]], truth, u, nt)
    drop = ((h.q7__logit < a.t) & (h.p1 > 0.99)).to_numpy()
    d = per_s1_f05(h.loc[~drop, ["s1", "r"]], truth, u, nt) - base
    print(f"7B drop rule (q7 < {a.t}, p1 > 0.99) on {u.size:,} holdout S1: {int(drop.sum())} drops, gain {d.mean():+.7f}")
    g = np.array([d[rng.random(u.size) < 0.25].mean() for _ in range(a.draws)])
    print(f"  on {a.draws:,} random 25% subsets of S1: mean {g.mean():+.7f}, sd {g.std():.7f}, P(gain <= 0) {(g <= 0).mean():.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
