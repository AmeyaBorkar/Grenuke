#!/usr/bin/env python3
"""The confident final predictions of the countries with training labels, for the 7B re-check (score_pairs.py).

Keeps the pairs of --matches whose S1 is in a country that has training labels (read from the train records, never
hard-coded) and whose stage-1 p1 > 0.99, i.e. the pairs no cross-encoder ever scored. On 27 Sep: g1w-dpc, 4,744,395 US/India
pairs. Defaults reproduce that run.

    python export_usin.py [--matches ameya-model-g1w-s3-ops3a-dpc] [--s1 ameya-s1-v6all] [--out <dir>/usin_final_pairs.parquet]
"""
from __future__ import annotations

import argparse
import os

import numpy as np
import pandas as pd
import pyarrow.compute as pc
import pyarrow.parquet as pq

from ber.artifacts import read_table
from ber.paths import records_path

K = 4_000_000_000


def key(d: pd.DataFrame) -> np.ndarray:
    return d.s1.to_numpy(np.int64) * K + d.r.to_numpy(np.int64)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--matches", default="ameya-model-g1w-s3-ops3a-dpc")
    ap.add_argument("--s1", default="ameya-s1-v6all", help="stage-1 scores tag (p1)")
    ap.add_argument("--out", default=os.path.join(os.environ.get("CE_BOX_DIR", "/workspace/grenuke/box"), "rescore",
                                                  "usin_final_pairs.parquet"))
    a = ap.parse_args()
    labelled = pc.unique(pq.read_table(records_path("train"), columns=["country"])["country"]).to_pylist()
    t = pq.read_table(records_path("test"), columns=["eid", "source", "country"]).to_pandas()
    lab = t.loc[(t.source == 1) & t.country.isin(labelled), "eid"].to_numpy()
    m = read_table("matches", a.matches, "test")[["s1", "r"]]
    m = m[np.isin(m.s1.to_numpy(), lab)].reset_index(drop=True)
    p1 = read_table("scores", a.s1, "test", ["s1", "r", "p1"])
    m["p1"] = pd.Series(p1.p1.to_numpy(), index=key(p1)).reindex(key(m)).to_numpy(np.float32)
    m = m[m.p1 > 0.99].reset_index(drop=True)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    m.to_parquet(a.out, index=False)
    print(f"countries with labels {sorted(labelled)}; their final pairs outside the band: {len(m):,} -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
