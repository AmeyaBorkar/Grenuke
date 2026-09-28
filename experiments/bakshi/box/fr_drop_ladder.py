#!/usr/bin/env python3
"""The French drop ladder behind the final upload (B7), reproduced from the inline builds of 27 Sep 22:40-23:35 IST.

Start: Composite B (matching sha256 df4bccd7..., LB 0.990879). Every step edits France only; US/India stay as in B.
Scores: q7 = Qwen2.5-7B adapter_0 logit (score_pairs.py) for pairs outside the band, the cross-fitted band logit for
pairs inside it; q4 = the Qwen3-4B equivalent. "Out-of-band" = stage-1 p1 > 0.99 (no cross-encoder in the pipeline
ever read those pairs). Break-even for a French drop is about 18-25% false (a false drop costs ~1/4 of what a true
drop gains, except on single-match S1).

  B+   restore the look-alike pairs swapsim removed when q7 > 2 (255); drop mixmdp's never-scored pairs with q7 < -6 (83)
  B++  + drop in-band pairs with q7 < -6 (113)                              [holdout: q7 < -6 out-of-band +33e-6, both halves]
  B3   + drop all pairs with q7 in [-6, -4) (440)                            [holdout: 14% false; France shows ~4x the count]
  B4   + drop out-of-band pairs with q7 in [-4, -2) (443)                    [gamble; superseded by B5's agreement rule]
  B5   = B3 + drop out-of-band pairs with q7 in [-4, 0) AND q4 < -2 (295)   [4B agreement: France 2-15x the US/India rate]
  B6   = B5 + drop in-band pairs with q7 in [-4, 0) AND q4 < -2 (514)       [holdout: +8e-6, halves -7e-6 / +24e-6]
  B7   = B6 + drop the remaining out-of-band pairs with q7 in [-4, -2) (258) [UPLOADED, matching sha256 3d7b09d6...]
  B8   = B7 + drop in-band pairs with q7 in [-4, -2) AND q4 < 0 (172)        [not uploaded]

Inputs (all produced by score_pairs.py / llm_group.py, kept in Drive grenuke-train-backup/rescore and box/out_q34st):
  fr_scored_*.parquet      q7 for every French final prediction of g0-dpcsf (s1, r, p1, pc, q7__logit)
  bplus_scored.parquet     q7 for the look-alike pairs (src=lookalike) and mixmdp's never-scored pairs (src=mixmdp_unscored)
  b5_test_4b.parquet       q7 and q4 for the out-of-band French pairs with q7 < 0
  band_test.parquet + out_q7st/ce_test.parquet + out_q34st/ce_test.parquet   in-band q7 / q4 by band row

    python fr_drop_ladder.py --base DIR_B --rescore DIR --band band_test.parquet --q7 out_q7st/ce_test.parquet \
        --q4 out_q34st/ce_test.parquet --s1-tsv test_source1.tsv --out DIR [--stop B7]
"""
from __future__ import annotations

import argparse
import glob
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
from pyarrow import csv as pacsv


def eid(x: str) -> int:
    return int(x[1]) * 1_000_000_000 + int(x[3:])


def read_tsv(path: Path) -> pd.DataFrame:
    return pacsv.read_csv(path, parse_options=pacsv.ParseOptions(delimiter="\t", quote_char=False),
                          convert_options=pacsv.ConvertOptions(column_types={c: pa.string() for c in (
                              "source1_entity_id", "matched_entity_ids", "candidate_entity_ids", "entity_id", "country")},
                              strings_can_be_null=False, null_values=[])).to_pandas()


def pairs(d: pd.DataFrame) -> set:
    return {(int(s), int(r)) for s, r in zip(d["s1"], d["r"])}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, type=Path)
    ap.add_argument("--rescore", required=True, type=Path)
    ap.add_argument("--band", required=True, type=Path)
    ap.add_argument("--q7", required=True, type=Path)
    ap.add_argument("--q4", required=True, type=Path)
    ap.add_argument("--s1-tsv", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--stop", default="B7", choices=["B+", "B++", "B3", "B4", "B5", "B6", "B7", "B8"])
    a = ap.parse_args()

    src = read_tsv(a.s1_tsv)
    fr_s1 = {eid(x) for x in src["entity_id"][src["country"] == "France"]}
    fr = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(str(a.rescore / "fr_scored_*.parquet")))])
    fr = fr[fr["p1"] > 0.99]
    bp = pd.read_parquet(a.rescore / "bplus_scored.parquet")
    look = bp[bp["src"] == "lookalike"]
    unsc = bp[bp["src"] == "mixmdp_unscored"]
    t4 = pd.read_parquet(a.rescore / "b5_test_4b.parquet")          # out-of-band, q7 < 0, columns q7 and q4
    band = pd.read_parquet(a.band, columns=["s1", "r", "row"])
    q7 = pd.read_parquet(a.q7).rename(columns={"ce__logit": "q7"})
    q4 = pd.read_parquet(a.q4).rename(columns={"ce__logit": "q4"})
    inb = band.merge(q7, on="row").merge(q4, on="row")
    inb = inb[inb["s1"].isin(fr_s1)]
    oob = pd.concat([fr.rename(columns={"q7__logit": "q7"})[["s1", "r", "q7"]],
                     unsc.rename(columns={"q7__logit": "q7"})[["s1", "r", "q7"]]])

    steps = [
        ("B+", "restore", pairs(look[look["q7__logit"] > 2])),
        ("B+", "drop", pairs(unsc[unsc["q7__logit"] < -6]) | pairs(fr[fr["q7__logit"] < -6])),
        ("B++", "drop", pairs(inb[inb["q7"] < -6])),
        ("B3", "drop", pairs(oob[(oob["q7"] >= -6) & (oob["q7"] < -4)]) | pairs(inb[(inb["q7"] >= -6) & (inb["q7"] < -4)])),
        ("B4", "drop", pairs(oob[(oob["q7"] >= -4) & (oob["q7"] < -2)])),   # B4 branch; B5 starts again from B3
        ("B5", "drop", pairs(t4[(t4["q7"] >= -4) & (t4["q7"] < 0) & (t4["q4"] < -2)])),
        ("B6", "drop", pairs(inb[(inb["q7"] >= -4) & (inb["q7"] < 0) & (inb["q4"] < -2)])),
        ("B7", "drop", pairs(oob[(oob["q7"] >= -4) & (oob["q7"] < -2)])),
        ("B8", "drop", pairs(inb[(inb["q7"] >= -4) & (inb["q7"] < -2) & (inb["q4"] < 0)])),
    ]
    order = ["B+", "B++", "B3", "B4", "B5", "B6", "B7", "B8"]
    wanted = set(order[: order.index(a.stop) + 1]) - ({"B4"} if a.stop != "B4" else set())

    M = read_tsv(a.base / "matching_results.tsv")
    C = read_tsv(a.base / "candidate_pairs.tsv").set_index("source1_entity_id")["candidate_entity_ids"]
    matches = {s: (m.split(",") if m else []) for s, m in zip(M["source1_entity_id"], M["matched_entity_ids"])}
    owner = {x for ms in matches.values() for x in ms}
    by_eid = {eid(k): k for k in matches}
    for name, kind, plist in steps:
        if name not in wanted:
            continue
        n = 0
        for s1, r in plist:
            k = by_eid.get(s1)
            if k is None or s1 not in fr_s1:
                continue
            if kind == "drop":
                keep = [m for m in matches[k] if eid(m) != r]
                n += len(matches[k]) - len(keep)
                matches[k] = keep
            else:  # restore: only inside the candidates, only onto a record nobody owns
                rec = next((c for c in (C.get(k, "") or "").split(",") if c and eid(c) == r), None)
                if rec is not None and rec not in owner:
                    matches[k].append(rec); owner.add(rec); n += 1
        print(f"{name:4} {kind:7} {n:5} pairs")
    a.out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"source1_entity_id": M["source1_entity_id"],
                  "matched_entity_ids": [",".join(matches[k]) for k in M["source1_entity_id"]]}).to_csv(
        a.out / "matching_results.tsv", sep="\t", index=False, lineterminator="\n")
    shutil.copy(a.base / "candidate_pairs.tsv", a.out / "candidate_pairs.tsv")
    print(f"written {a.out} (stop {a.stop}); run the validator and audit_matching.py on it")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
