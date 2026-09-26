"""Signed house-number relations (group ``nx``), row-aligned with <feats>-str.

    python experiments/ameya/model-v1/feats_nx.py --feats ameya-fx4 --split train
    python experiments/ameya/model-v1/feats_nx.py --feats ameya-fx4 --split test

The str group's number features are unsigned (num__rel1: equal / trailing digits dropped / |d| <= 10 / other;
num__logdiff1 = log(1 + |d|)). The generator uses the sign:
- look-alikes move the first house number up by d in {1, 2, 3, 4, 5, 7, 9, 11, 13, 21};
- true-copy noise moves it both ways (mostly -2..+2), substitutes or swaps a digit, or drops leading digits
  (13031 -> 3031).
On the holdout, same name + same street with a small negative d is 100% true but found at 0.935. Features, from
d = the record's first address number minus the S1's (NaN when either side has none):
- nx__d1: d clipped to [-50, 50];
- nx__nudge: d in the look-alike nudge set;
- nx__digit_sub: same length, one digit differs;
- nx__digit_swap: same length, two digits swapped (|d| = 9 k 10^m);
- nx__suffix: different lengths and the shorter number is the longer one's tail;
- nx__len_diff: digits of the record's number minus the S1's.
Writes work/features/<feats>-nx/<split>.parquet with the same row groups as <feats>-str.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import time

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from ber.artifacts import provenance
from ber.block import text
from ber.paths import artifact_path, records_path

log = logging.getLogger("feats_nx")
NUDGE = np.array([1, 2, 3, 4, 5, 7, 9, 11, 13, 21], np.int64)


def first_numbers(split: str) -> tuple[np.ndarray, np.ndarray]:
    """(eid, first address number or -1) per record, as the str group computes it."""
    tbl = pq.read_table(records_path(split), columns=["eid", "address"])
    nums = text.address_numbers(tbl["address"].combine_chunks())
    n = tbl.num_rows
    rows_u, idx = np.unique(nums.rows, return_index=True)
    vals = nums.values.to_numpy(zero_copy_only=False)[idx]
    first = np.full(n, -1, np.int64)
    first[rows_u] = np.array([int(v[:12]) for v in vals], np.int64)
    return tbl["eid"].to_numpy(), first


def n_digits(x: np.ndarray) -> np.ndarray:
    return np.where(x > 0, np.floor(np.log10(np.maximum(x, 1))).astype(np.int64) + 1, 1)


def digit_edits(a: np.ndarray, b: np.ndarray, length: int = 12) -> tuple[np.ndarray, np.ndarray]:
    """(one digit substituted, two adjacent digits swapped) for equal-length non-negative numbers."""
    da = np.empty((a.size, length), np.int8)
    db = np.empty((b.size, length), np.int8)
    qa, qb = a.copy(), b.copy()
    for i in range(length - 1, -1, -1):
        da[:, i], db[:, i] = qa % 10, qb % 10
        qa //= 10
        qb //= 10
    diff = da != db
    nd = diff.sum(1)
    p = np.clip(diff.argmax(1), 0, length - 2)
    k = np.arange(a.size)
    swap = (nd == 2) & diff[k, p + 1] & (da[k, p] == db[k, p + 1]) & (da[k, p + 1] == db[k, p])
    return nd == 1, swap


def relations(a: np.ndarray, b: np.ndarray) -> dict[str, np.ndarray]:
    """a = S1 first numbers, b = record first numbers (-1 = none)."""
    ok = (a >= 0) & (b >= 0)
    d = b - a
    la, lb = n_digits(a), n_digits(b)
    same = ok & (la == lb) & (d != 0)
    sub = np.zeros(d.size, bool)
    swap = np.zeros(d.size, bool)
    idx = np.flatnonzero(same)
    if idx.size:
        sub[idx], swap[idx] = digit_edits(a[idx], b[idx])
    lo, hi = np.minimum(a, b), np.maximum(a, b)
    llo = np.where(a < b, la, lb)
    suffix = ok & (la != lb) & (lo > 0) & (hi % np.power(10, np.minimum(llo, 18)) == lo)
    nan = np.float32(np.nan)
    f = lambda x: np.where(ok, x.astype(np.float32), nan)
    return {"nx__d1": f(np.clip(d, -50, 50)), "nx__nudge": f(np.isin(d, NUDGE)), "nx__digit_sub": f(sub),
            "nx__digit_swap": f(swap), "nx__suffix": f(suffix), "nx__len_diff": f(lb - la)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--feats", required=True)
    ap.add_argument("--split", required=True, choices=["train", "test"])
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    command = f"python experiments/ameya/model-v1/feats_nx.py --feats {args.feats} --split {args.split}"
    t0 = time.perf_counter()
    eid, first = first_numbers(args.split)
    order = np.argsort(eid)
    eid_s, first_s = eid[order], first[order]
    log.info("%s: first numbers of %d records (%.0f%% have one) in %.0fs", args.split, eid.size,
             100 * (first >= 0).mean(), time.perf_counter() - t0)
    src = pq.ParquetFile(artifact_path("features", f"{args.feats}-str", args.split))
    path = artifact_path("features", f"{args.feats}-nx", args.split)
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = provenance(command, {"features": f"{args.feats}-str"}, split=args.split, kind="features",
                      tag=f"{args.feats}-nx")
    w = None
    for g in range(src.num_row_groups):
        t = src.read_row_group(g, columns=["s1", "r"])
        s1, r = t["s1"].to_numpy(), t["r"].to_numpy()
        a = first_s[np.searchsorted(eid_s, s1)]
        b = first_s[np.searchsorted(eid_s, r)]
        cols = relations(a, b)
        table = pa.table(cols)
        if w is None:
            schema = table.schema.with_metadata({b"ber": json.dumps(meta, default=str).encode()})
            w = pq.ParquetWriter(str(path) + ".tmp", schema, compression="zstd")
        w.write_table(table, row_group_size=table.num_rows)
    w.close()
    os.replace(str(path) + ".tmp", path)
    log.info("%s: %d row groups written to %s (%.0fs)", args.split, src.num_row_groups, path, time.perf_counter() - t0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
