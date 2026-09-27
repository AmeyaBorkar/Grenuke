"""Guarded round-2 pseudo-labels for self-training on France (the v7sqwg recipe, RESEARCH_v6.md 6.17).

    python experiments/ameya/model-v1/pseudo_guard.py <round-1 labels> <new labels> <rule populations> <out.parquet>

The new labels (pseudo_labels.py on a later final, e.g. v7sq-dpc) are kept, except:
 (i) pairs whose record has an empty address keep their round-1 label: the new teacher turns about 12.7k empty-address
     same-name collision pairs (median 12 S1 per record, 95% with no owner in the final) from unlabelled into
     confident negatives, which would teach the students that such copies never match;
 (ii) the French rule populations (rule_pop.py: A/APP/ACR true-copy edits y=1, op-B look-alikes y=0) override, so the
     only external French truth stays in the training set.
Both label files must hold the same (s1, r) rows in the same order (pseudo_labels.py on the same pair set). Writes
(s1, r, y int8). v7sqwg: s2.py --pseudo <out> --pseudo-weight 3 on v7sq's features.
"""
import sys

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from ber.paths import records_path

K = 4_000_000_000


def key(d: pd.DataFrame) -> np.ndarray:
    return d.s1.to_numpy(np.int64) * K + d.r.to_numpy(np.int64)


def main(old_path: str, new_path: str, pop_path: str, out: str) -> None:
    o, n = pd.read_parquet(old_path), pd.read_parquet(new_path)
    if not (np.array_equal(o.s1.to_numpy(), n.s1.to_numpy()) and np.array_equal(o.r.to_numpy(), n.r.to_numpy())):
        raise SystemExit("the two label files do not hold the same rows in the same order")
    pop = pd.read_parquet(pop_path)
    ps = pd.Series(pop.y.to_numpy(), index=key(pop))
    ps = ps[~ps.index.duplicated()]
    ids = np.unique(n.r.to_numpy())
    parts = []
    for b in pq.ParquetFile(records_path("test")).iter_batches(batch_size=1_000_000, columns=["eid", "address"]):
        m = np.isin(b.column(0).to_numpy(), ids)
        if m.any():
            parts.append(b.filter(pa.array(m)))
    t = pa.Table.from_batches(parts)
    addr = pd.Series(t["address"].to_pylist(), index=t["eid"].to_numpy())
    empty = addr.fillna("").str.strip().eq("").reindex(n.r.to_numpy()).fillna(False).to_numpy()
    y = n.y.to_numpy().copy()
    y[empty] = o.y.to_numpy()[empty]
    yr = ps.reindex(key(n)).to_numpy()
    k = ~np.isnan(yr)
    y[k] = yr[k].astype(np.int8)
    d = n[["s1", "r"]].copy()
    d["y"] = y.astype(np.int8)
    d.to_parquet(out, index=False)
    print(f"pairs {len(d)}, empty record address {int(empty.sum())} (round-1 label kept; changed vs new "
          f"{int((n.y.to_numpy()[empty] != o.y.to_numpy()[empty]).sum())}), rule pairs {int(k.sum())}: positive "
          f"{int((y == 1).sum())}, negative {int((y == 0).sum())}, unlabelled {int((y == -1).sum())}")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit(__doc__)
    main(*sys.argv[1:5])
