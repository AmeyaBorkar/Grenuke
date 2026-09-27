#!/usr/bin/env python3
"""Pairs for a 7B rescoring of FINAL predictions, most of which lie outside the cross-encoder band (p1 > 0.99), so no
cross-encoder ever looked at them.

Writes to --out:
  fr_final_pairs.parquet   every French predicted pair of the final model (s1, r, p1, pc)
  hold_pred_pairs.parquet  the model's stage-3 predictions for a sample of US/India HOLDOUT S1 (s1, r, p1, pc, y)
  hold_truth.parquet       n_true per sampled holdout S1 (for the macro F0.5 of a drop rule)
The holdout S1 (folds 0-4) were never trained on by any q7st adapter, so their logits are out of sample.

    python rescore_export.py --final ameya-model-g0-s3-ops3a-dpcsf --s3 ameya-s3-g0 --pred ameya-model-g0-s3 --out DIR
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ameya", "model-v1"))
from ber.artifacts import read_table  # noqa: E402
from ber.paths import records_path  # noqa: E402
from ber.records import load_truth  # noqa: E402
from common import holdout_universe  # noqa: E402

K = 4_000_000_000


def key(d: pd.DataFrame) -> np.ndarray:
    return d["s1"].to_numpy(np.int64) * K + d["r"].to_numpy(np.int64)


def attach(d: pd.DataFrame, split: str, s3: str) -> pd.DataFrame:
    p1 = read_table("scores", "ameya-s1-v6all", split, ["s1", "r", "p1"])
    d["p1"] = pd.Series(p1["p1"].to_numpy(), index=key(p1)).reindex(key(d)).to_numpy(np.float32)
    del p1
    pc = read_table("scores", s3, split, ["s1", "r", "pc"])
    d["pc"] = pd.Series(pc["pc"].to_numpy(), index=key(pc)).reindex(key(d)).to_numpy(np.float32)
    return d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--final", required=True, help="final matches tag (test)")
    ap.add_argument("--s3", required=True, help="stage-3 scores tag (pc)")
    ap.add_argument("--pred", required=True, help="stage-3 decision matches tag (train split = holdout predictions)")
    ap.add_argument("--hold-frac", type=float, default=0.34)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    t = pq.read_table(records_path("test"), columns=["eid", "source", "country"]).to_pandas()
    fr = t.loc[(t["source"] == 1) & (t["country"] == "France"), "eid"].to_numpy()
    m = read_table("matches", a.final, "test")[["s1", "r"]]
    m = attach(m[np.isin(m["s1"].to_numpy(), fr)].reset_index(drop=True), "test", a.s3)
    m.to_parquet(f"{a.out}/fr_final_pairs.parquet", index=False)
    print(f"France final pairs {len(m):,}; outside the band (p1 > 0.99) {(m.p1 > 0.99).mean():.1%}")

    universe, _country = holdout_universe()
    rng = np.random.default_rng(7)
    uni = np.asarray(universe)
    samp = np.sort(rng.choice(uni, int(uni.size * a.hold_frac), replace=False))
    h = read_table("matches", a.pred, "train")[["s1", "r"]]
    h = attach(h[np.isin(h["s1"].to_numpy(), samp)].reset_index(drop=True), "train", a.s3)
    tr = load_truth()
    tr = tr[np.isin(tr["s1"].to_numpy(), samp)]
    h["y"] = np.isin(key(h), key(tr)).astype(np.int8)
    h.to_parquet(f"{a.out}/hold_pred_pairs.parquet", index=False)
    nt = tr.groupby("s1").size()
    pd.DataFrame({"s1": samp, "n_true": nt.reindex(samp).fillna(0).astype(int).to_numpy()}).to_parquet(
        f"{a.out}/hold_truth.parquet", index=False)
    print(f"holdout sample: {samp.size:,} S1, {len(h):,} predicted pairs (precision {h.y.mean():.4f}), "
          f"outside the band {(h.p1 > 0.99).mean():.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
