#!/usr/bin/env python3
"""B+ : edit a finished, audited submission (Composite B) with 7B-scored pair lists.

- restore: French look-alike pairs that swapsim removed (Ameya's calibrated estimate: that drop cost ~-27e-6) AND the
  7B accepts (logit > --restore-logit). A pair is added only if the record is in that S1's candidate row and no S1
  in the submission owns the record (one owner per record, matches within candidates: both hold by construction).
- drop: predicted pairs the 7B rejects (logit < --drop-logit), e.g. mixmdp's French pairs no earlier list scored.

    python bplus_tsv.py --base DIR --scored bplus_scored.parquet --out DIR [--restore-logit 2 --drop-logit -6]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
from pyarrow import csv as pacsv


def read(path: Path) -> pd.DataFrame:
    return pacsv.read_csv(path, parse_options=pacsv.ParseOptions(delimiter="\t", quote_char=False),
                          convert_options=pacsv.ConvertOptions(column_types={c: pa.string() for c in (
                              "source1_entity_id", "matched_entity_ids", "candidate_entity_ids")},
                              strings_can_be_null=False, null_values=[])).to_pandas()


def sid(v: int) -> str:
    return f"S{v // 1_000_000_000}-{v % 1_000_000_000:09d}"


def eid(x: str) -> int:
    return int(x[1]) * 1_000_000_000 + int(x[3:])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, type=Path)
    ap.add_argument("--scored", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--restore-logit", type=float, default=2.0)
    ap.add_argument("--drop-logit", type=float, default=-6.0)
    a = ap.parse_args()
    M = read(a.base / "matching_results.tsv")
    C = read(a.base / "candidate_pairs.tsv").set_index("source1_entity_id")["candidate_entity_ids"]
    s = pd.read_parquet(a.scored)
    print(s.groupby("src").q7__logit.describe(percentiles=[0.05, 0.25, 0.5]).to_string())

    matches = {r: (m.split(",") if m else []) for r, m in zip(M.source1_entity_id, M.matched_entity_ids)}
    owner = {x: s1 for s1, ms in matches.items() for x in ms}
    # the IDs in the files may or may not be zero-padded: map by parsed eid, write back the file's own spelling
    by_eid_s1 = {eid(k): k for k in matches}
    rec_spelling = {eid(x): x for x in owner}
    cand_rows = {}

    n_drop = n_add = n_skip_owned = n_skip_cand = 0
    for _, x in s[(s.src != "lookalike") & (s.q7__logit < a.drop_logit)].iterrows():
        k = by_eid_s1.get(int(x.s1))
        if k is None:
            continue
        ms = matches[k]
        keep = [m for m in ms if eid(m) != int(x.r)]
        if len(keep) != len(ms):
            matches[k] = keep
            owner.pop(rec_spelling.get(int(x.r), ""), None)
            n_drop += 1
    for _, x in s[(s.src == "lookalike") & (s.q7__logit > a.restore_logit)].sort_values("q7__logit", ascending=False).iterrows():
        k = by_eid_s1.get(int(x.s1))
        if k is None:
            continue
        if k not in cand_rows:
            cand_rows[k] = {eid(c): c for c in (C.get(k, "") or "").split(",") if c}
        rec = cand_rows[k].get(int(x.r))
        if rec is None:
            n_skip_cand += 1
            continue
        if rec in owner:
            n_skip_owned += 1
            continue
        matches[k].append(rec)
        owner[rec] = k
        n_add += 1
    print(f"dropped {n_drop:,} (7B < {a.drop_logit}); restored {n_add:,} look-alikes (7B > {a.restore_logit}); "
          f"skipped {n_skip_owned:,} (record owned) and {n_skip_cand:,} (not a candidate)")
    a.out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"source1_entity_id": M.source1_entity_id,
                  "matched_entity_ids": [",".join(matches[k]) for k in M.source1_entity_id]}).to_csv(
        a.out / "matching_results.tsv", sep="\t", index=False, lineterminator="\n")
    read(a.base / "candidate_pairs.tsv").to_csv(a.out / "candidate_pairs.tsv", sep="\t", index=False, lineterminator="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
