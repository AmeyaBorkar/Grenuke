"""Families (a) global threshold, (b) per-country threshold, (c) expected-F0.5 DP with logit shift (global and
per country), plus the baseline check. Writes res1_<tag>.json and per-entity arrays of the grid points (npz)."""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
import pandas as pd

from ber.artifacts import read_table
from core import D, Hold, expected_f_select, to_q

TAG = sys.argv[1] if len(sys.argv) > 1 else "ameya-s3-v7nst"
BASE = sys.argv[2] if len(sys.argv) > 2 else "ameya-model-v7nst-s3"


def main() -> int:
    t0 = time.perf_counter()
    H = Hold(TAG)
    out = {"tag": TAG, "base": BASE}
    # baseline: the current predictions (matches table) and the reproduced rule own & p > 0.675
    bm = read_table("matches", BASE, "train", ["s1", "r"])
    bm = bm[np.isin(bm["s1"].to_numpy(), H.U)]
    key = H.s1 * 4_000_000_000 + H.r
    in_base = np.isin(key, bm["s1"].to_numpy() * 4_000_000_000 + bm["r"].to_numpy())
    print(f"base pairs on holdout {len(bm):,}; found among rows {int(in_base.sum()):,}", flush=True)
    f_base = H.per_entity(in_base)
    rep = H.own & (H.p > 0.675)
    f_rep = H.per_entity(rep)
    out["base"] = H.summary(f_base)
    out["base_reproduced_0.675"] = H.summary(f_rep)
    out["base_diff_pairs"] = int((rep != in_base).sum())
    print("base", out["base"], "diff pairs", out["base_diff_pairs"], flush=True)
    arrays = {"base": f_base.astype(np.float32)}

    rows = []
    # (a) global threshold
    for t in np.round(np.arange(0.60, 0.8501, 0.005), 3):
        f = H.per_entity(H.own & (H.p > t))
        rows.append({"fam": "thr", "t": float(t), **H.summary(f)})
        arrays[f"thr_{t:.3f}"] = f.astype(np.float32)
    print(f"(a) done {time.perf_counter() - t0:.0f}s", flush=True)
    # (c) DP shift
    for sh in np.round(np.arange(-0.5, 0.5001, 0.05), 2):
        sel = expected_f_select(H.s1, to_q(H.p, sh), H.own)
        f = H.per_entity(sel)
        rows.append({"fam": "dp", "shift": float(sh), **H.summary(f)})
        arrays[f"dp_{sh:+.2f}"] = f.astype(np.float32)
        print(f"dp {sh:+.2f} A {rows[-1]['A']:.6f} B {rows[-1]['B']:.6f} full {rows[-1]['full']:.6f} "
              f"({time.perf_counter() - t0:.0f}s)", flush=True)
    out["rows"] = rows
    json.dump(out, open(os.path.join(D, f"res1_{TAG}.json"), "w"), indent=1)
    np.savez_compressed(os.path.join(D, f"arr1_{TAG}.npz"), **arrays)
    print(f"done {time.perf_counter() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
