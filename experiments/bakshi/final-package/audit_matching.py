#!/usr/bin/env python3
"""Strict audit of a submission matching TSV (and optionally its candidate TSV).

The official validator (``student_resource/utils/validate_submission.py``) only
*warns* about the two checks that matter most for a final package: a missing
candidate file, and matches that fall outside the candidate set.  It also never
checks owner uniqueness or country consistency, which are Grenuke pipeline
invariants rather than portal rules.  This script checks all of it and exits
non-zero on any hard failure, so "PASS" cannot hide a broken package.

Checks
------
1. header is exactly the expected two tab-separated columns;
2. one row per test S1, no duplicate rows, no missing/extra S1;
3. no repeated ID inside a list;
4. every target ID is S2-/S3- prefixed and exists in the test sources;
5. each S2/S3 target is claimed by at most one S1 (owner uniqueness);
6. every matched pair joins an S1 and a target of the *same* country;
7. if a candidate file is given, matches are a strict subset of candidates.

Also reports the pair/match distribution and per-country breakdown, which is
what the threshold and model comparisons are argued from.

Usage::

    python audit_matching.py --matching M.tsv [--candidate C.tsv] --test-dir DIR
                             [--json OUT.json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
from pyarrow import csv as pacsv

MATCHING_HEADER = ["source1_entity_id", "matched_entity_ids"]
CANDIDATE_HEADER = ["source1_entity_id", "candidate_entity_ids"]


def sha256(path: Path, chunk: int = 1 << 22) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def read_source(path: Path) -> pd.DataFrame:
    """Read entity_id + country from a source TSV, quoting disabled."""
    table = pacsv.read_csv(
        path,
        parse_options=pacsv.ParseOptions(delimiter="\t", quote_char=False),
        convert_options=pacsv.ConvertOptions(
            include_columns=["entity_id", "country"],
            column_types={"entity_id": pa.string(), "country": pa.string()},
        ),
    )
    return table.to_pandas()


def read_id_list_file(path: Path, expected_header: list[str]) -> tuple[pd.Series, pd.Series]:
    """Return (s1 ids, raw list strings) from a results-style TSV.

    ``null`` / empty list cells are normalised to the empty string so that an S1
    with no matches survives as a row rather than being dropped.
    """
    table = pacsv.read_csv(
        path,
        parse_options=pacsv.ParseOptions(delimiter="\t", quote_char=False),
        read_options=pacsv.ReadOptions(column_names=None),
        convert_options=pacsv.ConvertOptions(
            column_types={c: pa.string() for c in expected_header},
            # keep an empty cell as "" instead of NA so empty rows are preserved
            strings_can_be_null=False,
            null_values=[],
        ),
    )
    cols = [c.strip().lower() for c in table.column_names]
    if cols != expected_header:
        raise SystemExit(f"FAIL {path.name}: header {cols} != expected {expected_header}")
    df = table.to_pandas()
    df.columns = expected_header
    return df[expected_header[0]], df[expected_header[1]].fillna("")


def explode_pairs(s1: pd.Series, lists: pd.Series) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Explode "a,b,c" list cells into parallel (s1, target) arrays.

    Returns (s1_per_pair, target_per_pair, n_per_row).
    """
    split = lists.str.split(",")
    # an empty cell must contribute zero pairs, not one empty-string pair
    n = np.where(lists.str.len().to_numpy() == 0, 0, split.str.len().to_numpy())
    flat = np.concatenate([np.asarray(x, dtype=object) for x in split[n > 0]]) if (n > 0).any() else np.array([], dtype=object)
    s1_rep = np.repeat(s1.to_numpy(), n)
    return s1_rep, flat, n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--matching", required=True, type=Path)
    ap.add_argument("--candidate", type=Path, default=None)
    ap.add_argument("--test-dir", required=True, type=Path)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    errors: list[str] = []
    report: dict = {"matching": {}, "candidate": {}, "checks": {}}

    print("== files ==")
    for label, p in (("matching", args.matching), ("candidate", args.candidate)):
        if p is None:
            print(f"  {label}: (not supplied)")
            continue
        if not p.is_file():
            errors.append(f"{label} file not found: {p}")
            continue
        digest = sha256(p)
        size = p.stat().st_size
        report[label] = {"path": str(p), "bytes": size, "sha256": digest}
        print(f"  {label}: {p.name}  {size} bytes  sha256={digest}")
    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        return 1

    print("== test sources ==")
    s1_src = read_source(args.test_dir / "test_source1.tsv")
    required = s1_src["entity_id"]
    print(f"  test S1 rows: {len(s1_src)}")
    tgt = pd.concat(
        [read_source(args.test_dir / "test_source2.tsv"), read_source(args.test_dir / "test_source3.tsv")],
        ignore_index=True,
    )
    print(f"  test S2+S3 rows: {len(tgt)}")
    report["checks"]["n_test_s1"] = int(len(s1_src))
    report["checks"]["n_test_targets"] = int(len(tgt))

    s1_country = pd.Series(s1_src["country"].to_numpy(), index=s1_src["entity_id"].to_numpy())
    tgt_country = pd.Series(tgt["country"].to_numpy(), index=tgt["entity_id"].to_numpy())
    del s1_src, tgt

    # ---- matching file -------------------------------------------------
    print("== matching ==")
    m_s1, m_lists = read_id_list_file(args.matching, MATCHING_HEADER)
    report["checks"]["matching_rows"] = int(len(m_s1))
    print(f"  rows: {len(m_s1)}")

    if len(m_s1) != len(required):
        errors.append(f"matching has {len(m_s1)} rows, expected {len(required)} (one per test S1)")
    dup_rows = int(m_s1.duplicated().sum())
    if dup_rows:
        errors.append(f"matching has {dup_rows} duplicate source1_entity_id row(s)")
    req_set = set(required.to_numpy())
    seen_set = set(m_s1.to_numpy())
    missing, extra = req_set - seen_set, seen_set - req_set
    if missing:
        errors.append(f"matching is missing {len(missing)} required S1, e.g. {sorted(missing)[:5]}")
    if extra:
        errors.append(f"matching has {len(extra)} S1 not in the test set, e.g. {sorted(extra)[:5]}")
    print(f"  duplicate rows: {dup_rows} | missing S1: {len(missing)} | extra S1: {len(extra)}")

    m_pair_s1, m_pair_tgt, m_n = explode_pairs(m_s1, m_lists)
    n_pairs = int(m_pair_tgt.size)
    n_empty = int((m_n == 0).sum())
    report["checks"]["matching_pairs"] = n_pairs
    report["checks"]["matching_empty_rows"] = n_empty
    report["checks"]["matching_mean_matches_per_s1"] = float(n_pairs / len(m_s1)) if len(m_s1) else 0.0
    print(f"  pairs: {n_pairs} | empty rows: {n_empty} | mean per S1: {n_pairs/len(m_s1):.4f}")

    # intra-row duplicates
    pair_df = pd.DataFrame({"s1": m_pair_s1, "tgt": m_pair_tgt})
    intra = int(pair_df.duplicated(["s1", "tgt"]).sum())
    if intra:
        errors.append(f"matching repeats an ID inside a list {intra} time(s)")
    print(f"  duplicate (s1,target) pairs: {intra}")

    # prefixes
    pref = pd.Series(m_pair_tgt).str.slice(0, 3)
    bad_pref = pref[~pref.isin(["S2-", "S3-"])]
    if len(bad_pref):
        errors.append(f"matching has {len(bad_pref)} target(s) without an S2-/S3- prefix, e.g. {bad_pref.unique()[:5].tolist()}")
    print(f"  bad prefixes: {len(bad_pref)} | S2 targets: {int((pref=='S2-').sum())} | S3 targets: {int((pref=='S3-').sum())}")

    # target existence
    tgt_c = tgt_country.reindex(m_pair_tgt)
    unknown_mask = tgt_c.isna().to_numpy()
    n_unknown = int(unknown_mask.sum())
    if n_unknown:
        errors.append(f"matching references {n_unknown} target ID(s) that are not in test_source2/3")
    print(f"  targets not in test sources: {n_unknown}")

    # owner uniqueness: each target claimed by at most one S1
    tgt_series = pd.Series(m_pair_tgt)
    owners = tgt_series.groupby(tgt_series).size()
    multi = owners[owners > 1]
    if len(multi):
        errors.append(
            f"owner conflict: {len(multi)} target(s) are claimed by more than one S1, "
            f"e.g. {multi.index[:5].tolist()}"
        )
    print(f"  targets claimed by >1 S1: {len(multi)}")
    report["checks"]["owner_conflicts"] = int(len(multi))

    # country consistency
    s1_c = s1_country.reindex(m_pair_s1)
    same = (s1_c.to_numpy() == tgt_c.to_numpy())
    cross = int((~same & ~unknown_mask).sum())
    if cross:
        errors.append(f"{cross} matched pair(s) join two different countries")
    print(f"  cross-country pairs: {cross}")
    report["checks"]["cross_country_pairs"] = cross

    # per-country breakdown
    print("  per-country final pairs / S1:")
    per_country_pairs = pd.Series(s1_c.to_numpy()).value_counts()
    per_country_s1 = s1_country.reindex(m_s1.to_numpy()).value_counts()
    nonempty_s1 = pd.Series(s1_country.reindex(m_s1.to_numpy()).to_numpy())[m_n > 0].value_counts()
    cc = {}
    for c in sorted(per_country_s1.index):
        pairs = int(per_country_pairs.get(c, 0))
        n_s1 = int(per_country_s1.get(c, 0))
        ne = int(nonempty_s1.get(c, 0))
        cc[c] = {"s1": n_s1, "s1_nonempty": ne, "pairs": pairs, "pairs_per_s1": pairs / n_s1 if n_s1 else 0.0}
        print(f"    {c:<8} S1={n_s1:>9} non-empty={ne:>9} pairs={pairs:>9} pairs/S1={pairs/n_s1:.4f}")
    report["checks"]["per_country"] = cc

    # ---- candidate file ------------------------------------------------
    if args.candidate is not None:
        print("== candidate ==")
        c_s1, c_lists = read_id_list_file(args.candidate, CANDIDATE_HEADER)
        print(f"  rows: {len(c_s1)}")
        if len(c_s1) != len(required):
            errors.append(f"candidate has {len(c_s1)} rows, expected {len(required)}")
        if c_s1.duplicated().any():
            errors.append("candidate has duplicate source1_entity_id row(s)")
        if set(c_s1.to_numpy()) != req_set:
            errors.append("candidate S1 set does not equal the test S1 set")
        c_pair_s1, c_pair_tgt, c_n = explode_pairs(c_s1, c_lists)
        print(f"  pairs: {c_pair_tgt.size} | empty rows: {int((c_n==0).sum())}")
        report["checks"]["candidate_rows"] = int(len(c_s1))
        report["checks"]["candidate_pairs"] = int(c_pair_tgt.size)

        # subset check: this is the one the official validator only warns about
        cand_keys = pd.Index(pd.Series(c_pair_s1).str.cat(pd.Series(c_pair_tgt), sep="|"))
        match_keys = pd.Series(m_pair_s1).str.cat(tgt_series, sep="|")
        outside = ~match_keys.isin(cand_keys)
        n_outside = int(outside.sum())
        n_outside_s1 = int(pd.Series(m_pair_s1)[outside].nunique())
        report["checks"]["matches_outside_candidates"] = n_outside
        report["checks"]["s1_with_matches_outside_candidates"] = n_outside_s1
        if n_outside:
            errors.append(
                f"NOT A VALID PACKAGE PAIR: {n_outside} matched pair(s) across {n_outside_s1} S1 "
                f"are absent from the candidate file (the official validator only WARNS about this)"
            )
        print(f"  matched pairs outside candidates: {n_outside} (over {n_outside_s1} S1)")
        if n_outside:
            ex = match_keys[outside].head(5).tolist()
            print(f"    examples: {ex}")
            report["checks"]["outside_examples"] = ex

    # ---- verdict -------------------------------------------------------
    print()
    if errors:
        print(f"AUDIT FAIL — {len(errors)} hard issue(s):")
        for i, e in enumerate(errors, 1):
            print(f"  {i}. {e}")
    else:
        print("AUDIT PASS — every hard check satisfied.")
    report["errors"] = errors
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"report written to {args.json}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
