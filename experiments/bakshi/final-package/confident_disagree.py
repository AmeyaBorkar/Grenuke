#!/usr/bin/env python3
"""How large is the "confident substitution" population in France, and is cross-encoder disagreement a
usable way to find it?

The diagnosis (RESEARCH_v6 6.16, issue #45 at 09:05 IST) is that 97% of the final French predictions sit at
pc >= 0.99, so the remaining French loss is pairs the model is confident about and wrong about. Thresholds
and rules cannot reach those. The open question is whether they are *findable* another way, and how many
there are.

Cross-encoder disagreement is the natural candidate: on France the encoders disagree about 4x as often as on
US/India (6.6), and bge is a different family whose French errors are decorrelated from e5's. So: among pairs
the model KEPT, how often does bge vote against?

Two things make this measurable without any labels:

1. **US/India is the calibration.** Their final predictions are ~99.8% precise, so their disagreement rate is
   the background rate among pairs that are almost all correct. France's EXCESS over that background
   estimates how many French kept-pairs are suspect.
2. **The rule populations give a direct false-alarm rate.** Final French predictions that fall in the
   A/APP/ACR populations are known-true (97-99.8% in US/India). If the disagreement signal fires on lots of
   those, it is not selective enough to act on, whatever the excess says.

Coverage caveat, stated in the output: the cross-encoder band is stage-1 p1 in [0.02, 0.99], so pairs that
were already certain at stage 1 have no cross-encoder logit at all. Everything here is restricted to final
predictions that were in the band, and the share is reported.

    python confident_disagree.py --matching M.tsv --s1-tsv test_source1.tsv \
        --band-test band_test.parquet --rule-pop rulepop_fr.parquet \
        --run e5l=out_e5l --run e5l2=out_e5l2 --run bge=out_bge
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
from pyarrow import csv as pacsv

K = 4_000_000_000
COL = "ce__logit"


def eid(ids: np.ndarray) -> np.ndarray:
    s = pd.Series(ids, dtype="string")
    return (s.str.slice(1, 2).astype("int64") * 1_000_000_000 + s.str.slice(3).astype("int64")).to_numpy()


def read_src(path: Path, cols: list[str]) -> pd.DataFrame:
    return pacsv.read_csv(
        path, parse_options=pacsv.ParseOptions(delimiter="\t", quote_char=False),
        convert_options=pacsv.ConvertOptions(include_columns=cols,
                                             column_types={c: pa.string() for c in cols}),
    ).to_pandas()


def final_pairs(path: Path) -> tuple[np.ndarray, np.ndarray]:
    t = pacsv.read_csv(
        path, parse_options=pacsv.ParseOptions(delimiter="\t", quote_char=False),
        convert_options=pacsv.ConvertOptions(
            column_types={"source1_entity_id": pa.string(), "matched_entity_ids": pa.string()},
            strings_can_be_null=False, null_values=[]),
    ).to_pandas()
    t.columns = ["s1", "lists"]
    lists = t["lists"].fillna("")
    split = lists.str.split(",")
    n = np.where(lists.str.len().to_numpy() == 0, 0, split.str.len().to_numpy())
    flat = np.concatenate([np.asarray(x, dtype=object) for x in split[n > 0]])
    return eid(np.repeat(t["s1"].to_numpy(), n)), eid(flat)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--matching", required=True, type=Path)
    ap.add_argument("--s1-tsv", required=True, type=Path)
    ap.add_argument("--band-test", required=True, type=Path)
    ap.add_argument("--rule-pop", required=True, type=Path)
    ap.add_argument("--run", action="append", required=True)
    args = ap.parse_args()

    runs = {}
    for spec in args.run:
        n, _, d = spec.partition("=")
        runs[n] = Path(d)
    if not {"e5l", "bge"} <= set(runs):
        raise SystemExit("need at least --run e5l=... and --run bge=...")

    s1src = read_src(args.s1_tsv, ["entity_id", "country"])
    cty = pd.Series(s1src["country"].to_numpy(),
                    index=(1_000_000_000 + s1src["entity_id"].str.slice(3).astype("int64")).to_numpy())

    fs1, fr_ = final_pairs(args.matching)
    fkey = fs1 * K + fr_
    fcty = cty.reindex(fs1).to_numpy()
    print(f"final predictions: {len(fkey)}")
    print("  by country:", pd.Series(fcty).value_counts().to_dict())

    band = pd.read_parquet(args.band_test, columns=["s1", "r", "row", "p1"])
    bkey = band["s1"].to_numpy() * K + band["r"].to_numpy()
    row_of = pd.Series(band["row"].to_numpy(), index=bkey)
    row_of = row_of[~row_of.index.duplicated()]
    frow = row_of.reindex(fkey).to_numpy()
    in_band = ~np.isnan(frow)
    print(f"\nfinal predictions inside the cross-encoder band (stage-1 p1 in [0.02,0.99]): "
          f"{int(in_band.sum())} ({in_band.mean():.1%})")
    for c in sorted(pd.unique(pd.Series(fcty).dropna())):
        m = fcty == c
        print(f"  {c:<8} {int((m & in_band).sum()):>8} of {int(m.sum()):>8}  ({(m & in_band).sum()/m.sum():.1%})")
    print("  Pairs already certain at stage 1 have NO cross-encoder logit, so everything below is the band "
          "subset only.")

    # logits for the in-band final pairs
    idx = frow[in_band].astype(np.int64)
    L = {}
    for n, d in runs.items():
        ce = pd.read_parquet(d / "ce_test.parquet", columns=["row", COL])
        L[n] = pd.Series(ce[COL].to_numpy(), index=ce["row"].to_numpy()).reindex(idx).to_numpy()
    bc = fcty[in_band]
    bkeys = fkey[in_band]

    # the disagreement signals. Raw logit sign is meaningful: >0 means the encoder calls it a match.
    e5_pos = L["e5l"] > 0
    if "e5l2" in L:
        e5_pos = e5_pos & (L["e5l2"] > 0)
    against = L["bge"] < 0
    bge_q = pd.Series(L["bge"]).rank(pct=True).to_numpy()

    print("\n== among pairs the model KEPT, how often does bge vote against? ==")
    print(f"{'country':<8} {'kept in band':>13} {'bge<0':>9} {'bge<0 & e5>0':>14} {'bge in low 10%':>15}")
    stats = {}
    for c in sorted(pd.unique(pd.Series(bc).dropna())):
        m = bc == c
        s = {"n": int(m.sum()), "bge_neg": float(against[m].mean()),
             "flip": float((against & e5_pos)[m].mean()), "low10": float((bge_q < 0.10)[m].mean())}
        stats[c] = s
        print(f"{c:<8} {s['n']:>13} {s['bge_neg']:>8.2%} {s['flip']:>13.2%} {s['low10']:>14.2%}")

    lab = [c for c in stats if c in ("US", "India")]
    if lab and "France" in stats:
        bg = float(np.mean([stats[c]["flip"] for c in lab]))
        fr = stats["France"]["flip"]
        excess = fr - bg
        n_fr = stats["France"]["n"]
        print(f"\n== France's excess over the labelled-country background ==")
        print(f"  background (US/India mean) flip rate : {bg:.3%}")
        print(f"  France flip rate                     : {fr:.3%}")
        print(f"  excess                               : {excess:+.3%}")
        print(f"  estimated suspect French pairs        : {excess * n_fr:,.0f} "
              f"(of {n_fr:,} kept in band)")
        # what an S1-equivalent gain would need
        need = 0.0008 * 1_732_544
        print(f"\n  For context, +0.0008 LB needs about {need:,.0f} S1 worth of summed F0.5 gain.")
        print(f"  Dropping a false positive gains about 0.18 of one S1's F0.5, so the suspect population")
        print(f"  above is worth at most {excess * n_fr * 0.18:,.0f} summed F0.5 "
              f"= {excess * n_fr * 0.18 / 1_732_544:+.6f} LB if EVERY one of them is wrong.")

    # false-alarm rate: final French pairs with KNOWN-true labels from the rule populations
    pop = pd.read_parquet(args.rule_pop)
    pk = pop["s1"].to_numpy() * K + pop["r"].to_numpy()
    py = pd.Series(pop["y"].to_numpy(), index=pk)
    py = py[~py.index.duplicated()]
    y = py.reindex(bkeys).to_numpy()
    known = ~pd.isna(y)
    ktrue = known & (y == 1)
    print(f"\n== false-alarm check on known-true French pairs ==")
    isfr = bc == "France"
    n_kt = int((ktrue & isfr).sum())
    if n_kt:
        fa = float((against & e5_pos)[ktrue & isfr].mean())
        print(f"  final French kept pairs with a KNOWN-TRUE rule-population label: {n_kt}")
        print(f"  of those, bge votes against while e5 agrees: {fa:.2%}")
        print(f"  That is the signal's FALSE-ALARM rate on France. A drop rule built on this signal would")
        print(f"  discard about {fa:.1%} of pairs we know are true.")
        if "France" in stats:
            prec = 1 - fa / max(stats["France"]["flip"], 1e-12) * (1 - 0) if stats["France"]["flip"] else 0
            print(f"  Compare it with the flip rate on all French kept pairs, {stats['France']['flip']:.2%}: "
                  f"if the false-alarm rate is close to the overall rate, the signal is not selective and "
                  f"must not be used.")
    else:
        print("  no overlap; cannot estimate a false-alarm rate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
