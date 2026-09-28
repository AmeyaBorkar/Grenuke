#!/usr/bin/env python3
"""Compose a submission per country group from two finished, audited submissions: the countries WITH training labels
(US/India) from --labelled, the countries WITHOUT labels (France) from --unlabelled, optionally minus 7B drop lists of
(s1, r) eids (applied to every row; each list holds one country). Matching and candidate rows are taken per S1 from the same source, so matches stay a subset
of candidates; records never cross countries, so one owner per record is preserved. Run the validator and
audit_matching.py on the output.

    python compose_tsv.py --labelled DIR_A --unlabelled DIR_B --s1-tsv test_source1.tsv --train-s1-tsv train_source1.tsv \
        [--drop fr_scored_*.parquet --drop-logit -6] --out DIR
"""
from __future__ import annotations

import argparse
import glob
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


def countries(path: Path) -> pd.Series:
    t = pacsv.read_csv(path, parse_options=pacsv.ParseOptions(delimiter="\t", quote_char=False),
                       convert_options=pacsv.ConvertOptions(include_columns=["entity_id", "country"],
                                                            column_types={"entity_id": pa.string(),
                                                                          "country": pa.string()})).to_pandas()
    return pd.Series(t["country"].to_numpy(), index=t["entity_id"].to_numpy())


def eid(x: str) -> int:
    """'S2-000123' -> 2_000_000_123 (ber.ids convention: source * 1e9 + number)."""
    return int(x[1]) * 1_000_000_000 + int(x[3:])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--labelled", required=True, type=Path)
    ap.add_argument("--unlabelled", required=True, type=Path)
    ap.add_argument("--s1-tsv", required=True, type=Path)
    ap.add_argument("--train-s1-tsv", required=True, type=Path, help="to read which countries have labels")
    ap.add_argument("--drop", nargs="*", default=[])
    ap.add_argument("--drop-logit", type=float, default=-6.0)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    cty = countries(a.s1_tsv)
    labelled = set(countries(a.train_s1_tsv).unique())
    unl = ~cty.isin(labelled)
    print(f"countries with labels {sorted(labelled)}; test S1 without labels: {int(unl.sum()):,}")
    a.out.mkdir(parents=True, exist_ok=True)

    drop = set()
    if a.drop:
        d = pd.concat([pd.read_parquet(f) for p in a.drop for f in sorted(glob.glob(p))])
        d = d[(d["q7__logit"] < a.drop_logit) & (d["p1"] > 0.99)]
        drop = set(zip(d["s1"].to_numpy(np.int64).tolist(), d["r"].to_numpy(np.int64).tolist()))
        print(f"drop list: {len(drop):,} pairs (q7 logit < {a.drop_logit}, p1 > 0.99)")

    for fname, col in (("matching_results.tsv", "matched_entity_ids"), ("candidate_pairs.tsv", "candidate_entity_ids")):
        A, B = read(a.labelled / fname), read(a.unlabelled / fname)
        assert A.columns.tolist() == B.columns.tolist() and col in A.columns, (A.columns, B.columns)
        assert set(A["source1_entity_id"]) == set(B["source1_entity_id"]) == set(cty.index), f"{fname}: S1 sets differ"
        Bi = B.set_index("source1_entity_id")[col]
        is_unl = unl.reindex(A["source1_entity_id"]).to_numpy()
        out = A[col].to_numpy(dtype=object).copy()
        out[is_unl] = Bi.reindex(A["source1_entity_id"][is_unl]).to_numpy()
        n_drop = 0
        if drop and fname == "matching_results.tsv":
            for i in range(len(A)):   # each drop list holds pairs of one country only
                s1 = eid(A["source1_entity_id"].iat[i])
                if out[i]:
                    ms = out[i].split(",")
                    kept = [m for m in ms if (s1, eid(m)) not in drop]
                    n_drop += len(ms) - len(kept)
                    out[i] = ",".join(kept)
        res = pd.DataFrame({"source1_entity_id": A["source1_entity_id"], col: out})
        res.to_csv(a.out / fname, sep="\t", index=False, lineterminator="\n")
        print(f"{fname}: {int(is_unl.sum()):,} rows from {a.unlabelled.name}, the rest from {a.labelled.name}"
              + (f"; {n_drop:,} pairs dropped (7B drop lists)" if fname == "matching_results.tsv" else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
