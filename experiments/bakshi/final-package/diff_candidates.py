#!/usr/bin/env python3
"""Changed final predictions between candidate submissions, per country and per 1000 S1.

Net pair counts hide what matters: a candidate can add 5,000 and drop 5,000 and look identical in total.
What decides whether a candidate is worth an upload slot is how many predictions it actually CHANGES, and
where. The team's own history gives the yardstick -- v7nst -> v7sq-dpc changed France by +7.1 / -9.5 per
1000 S1 and gained +0.000281, so a candidate that changes France by well under that is very likely inside
the ~0.00005 noise floor and would spend a slot to learn nothing.

    python diff_candidates.py --base name=matching.tsv --cand name=matching.tsv [--cand ...] \
        --s1-tsv test_source1.tsv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
from pyarrow import csv as pacsv

K = 4_000_000_000


def eid(a: np.ndarray) -> np.ndarray:
    s = pd.Series(a, dtype="string")
    return (s.str.slice(1, 2).astype("int64") * 1_000_000_000 + s.str.slice(3).astype("int64")).to_numpy()


def pairs(path: Path) -> tuple[np.ndarray, np.ndarray]:
    t = pacsv.read_csv(
        path, parse_options=pacsv.ParseOptions(delimiter="\t", quote_char=False),
        convert_options=pacsv.ConvertOptions(
            column_types={"source1_entity_id": pa.string(), "matched_entity_ids": pa.string()},
            strings_can_be_null=False, null_values=[])).to_pandas()
    t.columns = ["s1", "lists"]
    lists = t["lists"].fillna("")
    sp = lists.str.split(",")
    n = np.where(lists.str.len().to_numpy() == 0, 0, sp.str.len().to_numpy())
    flat = np.concatenate([np.asarray(x, dtype=object) for x in sp[n > 0]])
    s1 = eid(np.repeat(t["s1"].to_numpy(), n))
    return s1, s1 * K + eid(flat)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="name=path")
    ap.add_argument("--cand", action="append", required=True, help="name=path")
    ap.add_argument("--s1-tsv", required=True, type=Path)
    args = ap.parse_args()

    src = pacsv.read_csv(
        args.s1_tsv, parse_options=pacsv.ParseOptions(delimiter="\t", quote_char=False),
        convert_options=pacsv.ConvertOptions(include_columns=["entity_id", "country"],
                                             column_types={"entity_id": pa.string(),
                                                           "country": pa.string()})).to_pandas()
    cty = pd.Series(src["country"].to_numpy(),
                    index=(1_000_000_000 + src["entity_id"].str.slice(3).astype("int64")).to_numpy())
    n_s1 = cty.value_counts().to_dict()

    bname, _, bpath = args.base.partition("=")
    bs1, bkey = pairs(Path(bpath))
    print(f"base {bname}: {len(bkey):,} pairs")
    bset = pd.Index(bkey)

    print(f"\n{'candidate':<12} {'country':<8} {'added':>8} {'dropped':>8} {'net':>8} "
          f"{'+/1000 S1':>11} {'-/1000 S1':>11} {'changed/1000':>13}")
    for spec in args.cand:
        name, _, path = spec.partition("=")
        cs1, ckey = pairs(Path(path))
        cset = pd.Index(ckey)
        added = cset.difference(bset)
        dropped = bset.difference(cset)
        a_c = cty.reindex(added.to_numpy() // K).to_numpy()
        d_c = cty.reindex(dropped.to_numpy() // K).to_numpy()
        for c in ("France", "India", "US"):
            na = int((a_c == c).sum())
            nd = int((d_c == c).sum())
            per = n_s1.get(c, 1) / 1000
            print(f"{name:<12} {c:<8} {na:>8,} {nd:>8,} {na-nd:>8,} "
                  f"{na/per:>11.2f} {nd/per:>11.2f} {(na+nd)/per:>13.2f}")
        print()

    print("Yardstick: v7nst -> v7sq-dpc changed France by +7.1 / -9.5 per 1000 S1 (16.6 changed) and gained")
    print("+0.000281 measured. A candidate changing France by far less than that is very likely inside the")
    print("~0.00005 noise floor, and an upload slot spent on it buys no information.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
