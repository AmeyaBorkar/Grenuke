"""Build a compact holdout cache of v7nst stage-3 candidate pairs (read-only on work/).

Output D/cache_train.parquet: candidate pairs (p1 >= 0.02 and the record's top-2 S1 by p1) of every record that has a
candidate holdout S1, with s1, r, p1, pc, y, own, pred (threshold 0.675, argmax owner).
"""
from __future__ import annotations

import os
import sys
import time

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from ber.paths import artifact_path
from ber.eval.splits import is_holdout
from common import argmax_owner, candidate_mask

D = os.path.dirname(os.path.abspath(__file__))
TAG = sys.argv[1] if len(sys.argv) > 1 else "ameya-s3-v7nst"
MTAG = sys.argv[2] if len(sys.argv) > 2 else "ameya-model-v7nst-s3"
THR = 0.675


def main():
    t0 = time.time()
    global THR
    import json
    md = pq.ParquetFile(artifact_path("matches", MTAG, "train")).schema_arrow.metadata or {}
    rule = json.loads(md.get(b"ber", b"{}")).get("rule", {})
    if rule.get("method") == "threshold":
        THR = float(rule["threshold"])
    print("threshold", THR, flush=True)
    f = pq.ParquetFile(artifact_path("scores", TAG, "train"))
    parts = []
    for g in range(f.num_row_groups):
        t = f.read_row_group(g, columns=["s1", "r", "p1", "pc", "y"])
        p1 = t.column("p1").to_numpy()
        keep = p1 >= 0.02
        parts.append({c: t.column(c).to_numpy()[keep] for c in ["s1", "r", "p1", "pc", "y"]})
    s1 = np.concatenate([p["s1"] for p in parts]); r = np.concatenate([p["r"] for p in parts])
    p1 = np.concatenate([p["p1"] for p in parts]); pc = np.concatenate([p["pc"] for p in parts])
    y = np.concatenate([p["y"] for p in parts])
    del parts
    print("p1>=0.02 rows", s1.size, round(time.time() - t0), "s", flush=True)
    cand = candidate_mask(s1, r, p1, 0.02, 2)
    print("candidate rows", cand.sum(), flush=True)
    own = argmax_owner(s1, r, np.where(cand, pc, np.float32(0)))
    pred = own & cand & (pc > THR)
    hold = is_holdout(s1)
    rh = np.unique(r[hold & cand])
    keep = np.isin(r, rh)
    df = pd.DataFrame({"s1": s1[keep], "r": r[keep], "p1": p1[keep], "pc": pc[keep], "y": y[keep],
                       "own": own[keep] & cand[keep], "pred": pred[keep], "hold": hold[keep], "cand": cand[keep]})
    print("rows kept (records touching holdout S1)", len(df), flush=True)
    # verify against the stored holdout matches
    m = pq.read_table(artifact_path("matches", MTAG, "train")).to_pandas()
    m = m[is_holdout(m.s1.to_numpy())]
    K = 4_000_000_000
    mk = np.sort(m.s1.to_numpy() * K + m.r.to_numpy())
    ph = df[df.pred & df.hold]
    assert not (df.pred & ~df.cand).any()
    pk = np.sort(ph.s1.to_numpy() * K + ph.r.to_numpy())
    print("stored holdout matches", mk.size, "rebuilt", pk.size, "identical", mk.size == pk.size and bool((mk == pk).all()))
    df.to_parquet(os.path.join(D, f"cache_all{os.environ.get('HUNT_SUFFIX', '')}.parquet"), index=False)
    print("done", round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
