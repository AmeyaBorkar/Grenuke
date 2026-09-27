#!/usr/bin/env python3
"""Consensus editing of the best measured submission, using the other validated candidates as voters.

Mechanism, and why it is not just hand-waving: under macro F0.5 a false positive costs about 0.18 of an
entity's score while a miss costs about 0.07, so raising precision is worth roughly 2.6x as much as raising
recall. A pair that the best model predicts but almost no other candidate does is an outlier accept -- exactly
the population where dropping is favourable. A pair that nearly every other candidate predicts but the best
model does not is an outlier reject.

So this does NOT build a fresh ensemble from scratch. It starts from the measured best and makes only the two
edits the vote supports strongly, which keeps the 0.990545 baseline intact everywhere the voters agree with it:

    drop  a base pair if at most --drop-max of the other voters predict it
    add   a non-base pair if at least --add-min of the other voters predict it

Ownership is re-enforced after editing: if an addition would give a record a second owner, it is refused
(the base model's owner wins), because one-owner-per-record is a hard invariant of the task.

Nothing here can be validated offline -- France has no labels and the holdout has no French rows. What CAN
be decided offline is whether the edit footprint is large enough to matter at all, using the measured anchor:
v7nst -> v7sq-dpc changed France by 16.6 predictions per 1000 S1 for +0.000281, i.e. about 0.000016 LB per
unit. That makes this a screen, not a gate.

    python consensus.py --base name=matching.tsv --voter name=matching.tsv [--voter ...] \
        --s1-tsv test_source1.tsv --drop-max 1 --add-min 4 [--out out.tsv]
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


def read_pairs(path: Path) -> tuple[np.ndarray, np.ndarray, pd.Series]:
    """Return (s1_per_pair, key_per_pair, s1_order) -- s1_order preserves the file's row order."""
    t = pacsv.read_csv(
        path, parse_options=pacsv.ParseOptions(delimiter="\t", quote_char=False),
        convert_options=pacsv.ConvertOptions(
            column_types={"source1_entity_id": pa.string(), "matched_entity_ids": pa.string()},
            strings_can_be_null=False, null_values=[])).to_pandas()
    t.columns = ["s1", "lists"]
    order = pd.Series(eid(t["s1"].to_numpy()))
    lists = t["lists"].fillna("")
    sp = lists.str.split(",")
    n = np.where(lists.str.len().to_numpy() == 0, 0, sp.str.len().to_numpy())
    flat = np.concatenate([np.asarray(x, dtype=object) for x in sp[n > 0]]) if (n > 0).any() else np.array([], object)
    s1 = np.repeat(order.to_numpy(), n)
    return s1, s1 * K + eid(flat), order


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--voter", action="append", required=True)
    ap.add_argument("--s1-tsv", required=True, type=Path)
    ap.add_argument("--drop-max", type=int, default=1)
    ap.add_argument("--add-min", type=int, default=4)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    src = pacsv.read_csv(
        args.s1_tsv, parse_options=pacsv.ParseOptions(delimiter="\t", quote_char=False),
        convert_options=pacsv.ConvertOptions(include_columns=["entity_id", "country"],
                                             column_types={"entity_id": pa.string(), "country": pa.string()})).to_pandas()
    cty = pd.Series(src["country"].to_numpy(),
                    index=(1_000_000_000 + src["entity_id"].str.slice(3).astype("int64")).to_numpy())
    n_s1 = cty.value_counts().to_dict()

    bname, _, bpath = args.base.partition("=")
    b_s1, b_key, order = read_pairs(Path(bpath))
    print(f"base {bname}: {len(b_key):,} pairs over {len(order):,} S1")

    votes = pd.Series(0, index=pd.Index(b_key, name="key"), dtype="int16")
    votes = votes[~votes.index.duplicated()]
    extra = {}
    names = []
    for spec in args.voter:
        n, _, p = spec.partition("=")
        names.append(n)
        _, k, _ = read_pairs(Path(p))
        ks = pd.Index(k).unique()
        hit = votes.index.isin(ks)
        votes.iloc[:] = votes.to_numpy() + hit.astype("int16")
        for nk in ks.difference(votes.index):
            extra[nk] = extra.get(nk, 0) + 1
        print(f"  voter {n:<12} agrees with base on {int(hit.sum()):>9,} / {len(votes):,}  "
              f"({hit.mean():.3%});  proposes {len(ks.difference(votes.index)):>7,} the base lacks")
    V = len(names)

    # ---- the two edits ----
    drop_mask = votes.to_numpy() <= args.drop_max
    drop_keys = votes.index.to_numpy()[drop_mask]
    ex = pd.Series(extra, dtype="int16") if extra else pd.Series(dtype="int16")
    add_keys = ex.index.to_numpy()[ex.to_numpy() >= args.add_min] if len(ex) else np.array([], dtype="int64")

    # ownership: refuse an addition whose record already has an owner in the kept base
    kept = set(votes.index.to_numpy()[~drop_mask])
    owned = {k % K for k in kept}
    add_ok = np.array([ (k % K) not in owned for k in add_keys ], dtype=bool) if len(add_keys) else np.array([], bool)
    refused = int((~add_ok).sum()) if len(add_keys) else 0
    add_keys = add_keys[add_ok] if len(add_keys) else add_keys

    print(f"\nvoters {V}; drop if <= {args.drop_max} agree, add if >= {args.add_min} agree")
    print(f"  drops {len(drop_keys):,}   adds {len(add_keys):,}   additions refused for ownership {refused:,}")

    print(f"\n{'country':<8} {'dropped':>9} {'added':>9} {'net':>9} {'changed/1000 S1':>17} {'ceiling LB':>12}")
    tot_ch = 0
    for c in ("France", "India", "US"):
        d = int((cty.reindex(drop_keys // K).to_numpy() == c).sum())
        a = int((cty.reindex(add_keys // K).to_numpy() == c).sum()) if len(add_keys) else 0
        per = n_s1.get(c, 1) / 1000
        ch = (d + a) / per
        ceil = ch * 0.000016 * (per * 1000 / 1_732_544) / (259_452 / 1_732_544) if c == "France" else 0.0
        print(f"{c:<8} {d:>9,} {a:>9,} {a-d:>9,} {ch:>17.2f} "
              f"{(ch*0.000016 if c=='France' else float('nan')):>12.6f}")
        if c == "France":
            tot_ch = ch
    print(f"\nFrance footprint {tot_ch:.2f} changed per 1000 S1  ->  ceiling about "
          f"{tot_ch*0.000016:+.6f} LB if every edit is right.")
    print("0.991811 needs +0.001266, i.e. about 79 changed per 1000 French S1. 0.991 needs about 28.")

    if args.out:
        keep = kept | set(add_keys.tolist())
        s1a = np.array([k // K for k in keep], dtype="int64")
        ra = np.array([k % K for k in keep], dtype="int64")
        df = pd.DataFrame({"s1": s1a, "r": ra})
        assert not df.r.duplicated().any(), "a record has two owners"
        def fmt(v):
            return ("S" + (v // 1_000_000_000).astype(str) + "-" + (v % 1_000_000_000).astype(str))
        df["rs"] = fmt(df.r)
        g = df.groupby("s1").rs.apply(lambda s: ",".join(sorted(s)))
        out = pd.DataFrame({"source1_entity_id": fmt(order.to_numpy()),
                            "matched_entity_ids": g.reindex(order.to_numpy()).fillna("").to_numpy()})
        args.out.parent.mkdir(parents=True, exist_ok=True)
        out.to_csv(args.out, sep="\t", index=False, lineterminator="\n")
        print(f"\nwritten {args.out}  ({len(out):,} rows, {len(df):,} pairs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
