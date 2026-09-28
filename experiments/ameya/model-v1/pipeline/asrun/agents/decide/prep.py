"""Prepare compact holdout tables for decision-rule tuning (read-only on work/).

Reads train scores (rows with p1 >= 0.02 only), applies the candidate cut (p1 >= 0.02 and the record's top-2 S1
by p1, common.candidate_mask), ownership (common.argmax_owner) over ALL train S1 (so rivals outside the holdout
count), then keeps holdout-S1 rows with p > 0.

Writes (in this directory):
  hold_<tag>.parquet : s1, r, p (pc inside cut else 0), y, own, riv (best rival p for the same record), rank info
  universe.parquet   : s1, country, n_true, half (splitmix64(s1) % 2 -> 0 = A, 1 = B)
"""
from __future__ import annotations

import os
import sys
import time

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from ber.eval.splits import splitmix64
from ber.paths import artifact_path
from ber.records import load_truth
from common import argmax_owner, candidate_mask, holdout_universe

D = os.path.dirname(os.path.abspath(__file__))


def load_rows(tag: str, split: str, cols=("s1", "r", "p1", "pc")) -> dict:
    f = pq.ParquetFile(artifact_path("scores", tag, split))
    names = f.schema_arrow.names
    cols = [c for c in cols if c in names]
    out = {c: [] for c in cols}
    for g in range(f.num_row_groups):
        t = f.read_row_group(g, columns=cols)
        m = t.column("p1").to_numpy() >= 0.02
        for c in cols:
            out[c].append(t.column(c).to_numpy()[m])
    return {c: np.concatenate(v) for c, v in out.items()}


def rival_p(r: np.ndarray, p: np.ndarray, own: np.ndarray) -> np.ndarray:
    """Best p among the record's OTHER S1 (for the owner: 2nd best; for non-owners: the owner's p)."""
    order = np.lexsort((-p, r))
    rs, ps = r[order], p[order]
    start = np.ones(rs.size, bool)
    start[1:] = rs[1:] != rs[:-1]
    first = np.maximum.accumulate(np.where(start, np.arange(rs.size), 0))
    top1 = ps[first]
    # second best: the element after the first in each group, if same group
    nxt = np.minimum(first + 1, rs.size - 1)
    top2 = np.where((nxt < rs.size) & (rs[nxt] == rs) & (nxt != first), ps[nxt], 0.0)
    is_first = np.arange(rs.size) == first
    riv_sorted = np.where(is_first, top2, top1)
    out = np.empty(p.size, np.float32)
    out[order] = riv_sorted
    return out


def build(tag: str, split: str = "train") -> pd.DataFrame:
    t0 = time.perf_counter()
    cols = ("s1", "r", "p1", "pc", "y") if split == "train" else ("s1", "r", "p1", "pc")
    d = load_rows(tag, split, cols)
    s1, r, p1, pc = d["s1"], d["r"], d["p1"], d["pc"]
    cut = candidate_mask(s1, r, p1, 0.02, 2)
    p = np.where(cut, pc, np.float32(0)).astype(np.float32)
    print(f"{tag}/{split}: rows p1>=0.02 {s1.size:,}, in cut {int(cut.sum()):,}, pc>0 outside cut "
          f"{int(((pc > 0) & ~cut).sum()):,} ({time.perf_counter() - t0:.0f}s)", flush=True)
    own = argmax_owner(s1, r, p)
    riv = rival_p(r, p, own)
    df = pd.DataFrame({"s1": s1, "r": r, "p": p, "own": own, "riv": riv})
    if "y" in d:
        df["y"] = d["y"]
    return df[df["p"] > 0].reset_index(drop=True)


def main() -> int:
    tag = sys.argv[1] if len(sys.argv) > 1 else "ameya-s3-v7nst"
    df = build(tag, "train")
    universe, country = holdout_universe("train")
    hold = df[np.isin(df["s1"].to_numpy(), universe)].reset_index(drop=True)
    hold.to_parquet(os.path.join(D, f"hold_{tag}.parquet"), index=False)
    print(f"holdout rows {len(hold):,}", flush=True)
    upath = os.path.join(D, "universe.parquet")
    if not os.path.exists(upath):
        truth = load_truth()
        th = truth[truth["s1"].isin(universe)]
        u = np.sort(universe)
        n_true = np.bincount(np.searchsorted(u, th["s1"].to_numpy()), minlength=u.size)
        half = (splitmix64(u.astype(np.int64)) % np.uint64(2)).astype(np.int8)
        pd.DataFrame({"s1": u, "country": country.reindex(u).to_numpy(), "n_true": n_true.astype(np.int16),
                      "half": half}).to_parquet(upath, index=False)
        th[["s1", "r"]].to_parquet(os.path.join(D, "truth_hold.parquet"), index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
