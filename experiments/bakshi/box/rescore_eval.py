#!/usr/bin/env python3
"""Does dropping predicted pairs the 7B rejects help macro F0.5? Measured on labelled US/India holdout S1 (never trained
on by the adapter), with fold-parity halves A/B as a second, independent check; then counted on France.

Rule: drop a predicted pair when q7__logit < t (optionally only outside the band, p1 > 0.99). Per-S1 F0.5 with the
grader's convention (empty prediction on an S1 with no true match scores 1).

    python rescore_eval.py --dir box/rescore [--out-band-only]
"""
from __future__ import annotations

import argparse
import glob

import numpy as np
import pandas as pd


def f05(tp: np.ndarray, npred: np.ndarray, ntrue: np.ndarray) -> np.ndarray:
    fp, fn = npred - tp, ntrue - tp
    den = 1.25 * tp + 0.25 * fn + fp
    return np.where((npred == 0) & (ntrue == 0), 1.0, np.where(den > 0, 1.25 * tp / np.maximum(den, 1e-12), 0.0))


def macro(h: pd.DataFrame, keep: np.ndarray, truth: pd.DataFrame) -> pd.Series:
    k = h[keep]
    g = k.groupby("s1").agg(tp=("y", "sum"), npred=("y", "size"))
    g = g.reindex(truth.index).fillna(0)
    return pd.Series(f05(g.tp.to_numpy(), g.npred.to_numpy(), truth.n_true.to_numpy()), index=truth.index)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out-band-only", action="store_true")
    a = ap.parse_args()
    h = pd.read_parquet(f"{a.dir}/hold_scored.parquet")
    truth = pd.read_parquet(f"{a.dir}/hold_truth.parquet").set_index("s1")
    fr = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(f"{a.dir}/fr_scored_*.parquet"))], ignore_index=True)
    band_h = (h.p1 > 0.99).to_numpy() if a.out_band_only else np.ones(len(h), bool)
    band_f = (fr.p1 > 0.99).to_numpy() if a.out_band_only else np.ones(len(fr), bool)
    half = (truth.index.to_numpy() // 7) % 2           # a fixed split of S1 into two halves, independent of the rule

    print(f"holdout: {len(truth):,} S1, {len(h):,} predicted pairs, precision {h.y.mean():.5f}")
    print("truth rate of predicted pairs by 7B logit bucket (holdout):")
    q = h.q7__logit.to_numpy()
    for lo, hi in [(-99, -6), (-6, -4), (-4, -2), (-2, 0), (0, 2), (2, 99)]:
        m = (q >= lo) & (q < hi) & band_h
        mf = (fr.q7__logit.to_numpy() >= lo) & (fr.q7__logit.to_numpy() < hi) & band_f
        print(f"  [{lo:>4},{hi:>3})  holdout n={m.sum():>7,} true={h.y[m].mean() if m.any() else float('nan'):.3f}"
              f"   France n={mf.sum():>7,} ({mf.mean():.2%} of French predictions)")

    base = macro(h, np.ones(len(h), bool), truth)
    print(f"\nbase holdout macro F0.5 (sample) {base.mean():.6f}")
    print(f"{'t':>6} {'drops':>7} {'true dropped':>12} {'dF all':>10} {'dF half A':>10} {'dF half B':>10} {'FR drops':>9} {'FR /1000 S1':>11}")
    n_fr_s1 = 259_452
    for t in [-8, -6, -5, -4, -3, -2, -1, 0]:
        drop = (q < t) & band_h
        new = macro(h, ~drop, truth)
        d = new - base
        frd = int(((fr.q7__logit.to_numpy() < t) & band_f).sum())
        print(f"{t:>6} {int(drop.sum()):>7,} {int(h.y[drop].sum()):>12,} {d.mean():>+10.6f} {d[half == 0].mean():>+10.6f} "
              f"{d[half == 1].mean():>+10.6f} {frd:>9,} {frd / n_fr_s1 * 1000:>11.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
