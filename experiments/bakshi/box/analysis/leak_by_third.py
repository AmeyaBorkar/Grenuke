#!/usr/bin/env python3
"""Leakage check of the 7B re-check (METHODOLOGY_bakshi.md §5).

adapter_0 of q7st trained on the French pseudo-labels of the S1 thirds it did not own (fold_of(s1) % 3 in {1, 2}; band
pairs only) and scored every French final prediction. If its rejections came from memorised labels, French pairs of
thirds 1-2 would be rejected at a different rate than those of the unseen third 0. Reports, per third, for the French
final predictions outside the band (p1 > 0.99): count, share with q7 < --t, share with q7 < 0, median q7.

    python leak_by_third.py --rescore box/rescore          # reads fr_scored_*.parquet
"""
from __future__ import annotations

import argparse
import glob

import pandas as pd

from ber.eval.splits import fold_of


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rescore", required=True)
    ap.add_argument("--t", type=float, default=-6.0)
    a = ap.parse_args()
    f = pd.concat([pd.read_parquet(x) for x in sorted(glob.glob(f"{a.rescore}/fr_scored_*.parquet"))])
    f = f[f.p1 > 0.99]
    f["third"] = fold_of(f.s1.to_numpy()) % 3
    g = f.groupby("third").q7__logit.agg(n="size", drop_rate=lambda x: (x < a.t).mean(), neg=lambda x: (x < 0).mean(),
                                          med="median")
    print(g.to_string())
    print("adapter_0 never saw the pseudo-labels of third 0; it trained on those of thirds 1-2 (band pairs only).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
