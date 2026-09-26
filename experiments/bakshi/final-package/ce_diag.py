#!/usr/bin/env python3
"""Distribution diagnostics for cross-encoder logits, per country.

Motivation: the French rule-population screen showed 77.5% tied values in e5l's raw logits and 81.2% in
bge's. A z-mean is a scale-and-shift average, so heavily tied or saturated inputs combine badly -- the tied
mass carries no ordering information yet still sets the standard deviation that fixes each run's weight. If
that is what is happening, a rank/normal-score transform before averaging should beat a z-mean.

Reports, per run and per country: unique-value count, the most frequent values and their mass, saturation at
the extremes, and the pairwise correlations (so §6.6's table can be checked).

    python ce_diag.py --band-test band_test.parquet --s1-tsv test_source1.tsv \
        --run e5l=out_e5l --run e5l2=out_e5l2 --run bge=out_bge
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
from pyarrow import csv as pacsv

COL = "ce__logit"


def s1_country(path: Path) -> pd.Series:
    t = pacsv.read_csv(
        path,
        parse_options=pacsv.ParseOptions(delimiter="\t", quote_char=False),
        convert_options=pacsv.ConvertOptions(include_columns=["entity_id", "country"],
                                             column_types={"entity_id": pa.string(),
                                                           "country": pa.string()}),
    ).to_pandas()
    # "S1-123" -> 1_000_000_123, matching ber.ids
    num = t["entity_id"].str.slice(3).astype("int64")
    return pd.Series(t["country"].to_numpy(), index=(1_000_000_000 + num).to_numpy())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--band-test", required=True, type=Path)
    ap.add_argument("--s1-tsv", required=True, type=Path)
    ap.add_argument("--run", action="append", required=True, help="name=dir")
    args = ap.parse_args()

    band = pd.read_parquet(args.band_test, columns=["s1", "r", "row"])
    cty = s1_country(args.s1_tsv).reindex(band["s1"].to_numpy()).to_numpy()
    band["cty"] = cty
    print(f"test band rows: {len(band)}")
    print("by country:", band["cty"].value_counts().to_dict())

    runs = {}
    for spec in args.run:
        name, _, d = spec.partition("=")
        ce = pd.read_parquet(Path(d) / "ce_test.parquet", columns=["row", COL])
        s = pd.Series(ce[COL].to_numpy(), index=ce["row"].to_numpy())
        runs[name] = s.reindex(band["row"].to_numpy()).to_numpy()

    print("\n== distribution, all countries ==")
    print(f"{'run':<6} {'n_unique':>9} {'ties':>7} {'min':>9} {'max':>9} "
          f"{'top value':>10} {'its mass':>9} {'|x|>10':>8} {'>0':>7}")
    for name, v in runs.items():
        vals, cnts = np.unique(v, return_counts=True)
        top = vals[cnts.argmax()]
        print(f"{name:<6} {vals.size:>9} {1 - vals.size/len(v):>6.1%} {v.min():>9.3f} {v.max():>9.3f} "
              f"{top:>10.3f} {cnts.max()/len(v):>8.2%} {np.mean(np.abs(v) > 10):>7.2%} "
              f"{np.mean(v > 0):>6.2%}")

    print("\n== share of logit > 0, per country (compare RESEARCH_v6 6.6) ==")
    hdr = "  ".join(f"{n:>7}" for n in runs)
    print(f"{'country':<8} {hdr}")
    for c in sorted(pd.unique(band['cty'].dropna())):
        m = (band["cty"] == c).to_numpy()
        print(f"{c:<8} " + "  ".join(f"{np.mean(runs[n][m] > 0):>6.1%} " for n in runs))

    print("\n== ties per country ==")
    print(f"{'country':<8} {hdr}")
    for c in sorted(pd.unique(band['cty'].dropna())):
        m = (band["cty"] == c).to_numpy()
        print(f"{c:<8} " + "  ".join(
            f"{1 - np.unique(runs[n][m]).size/m.sum():>6.1%} " for n in runs))

    names = list(runs)
    print("\n== pairwise Pearson correlation per country ==")
    for c in sorted(pd.unique(band['cty'].dropna())):
        m = (band["cty"] == c).to_numpy()
        out = []
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                out.append(f"{names[i]}-{names[j]} {np.corrcoef(runs[names[i]][m], runs[names[j]][m])[0,1]:+.3f}")
        print(f"  {c:<8} " + "   ".join(out))

    print("\n== pairwise SPEARMAN (rank) correlation per country ==")
    print("   If Spearman is much below Pearson, the linear scale is dominated by saturated mass and a")
    print("   rank-based combiner should extract more than a z-mean.")
    for c in sorted(pd.unique(band['cty'].dropna())):
        m = (band["cty"] == c).to_numpy()
        ranks = {n: pd.Series(runs[n][m]).rank().to_numpy() for n in names}
        out = []
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                out.append(f"{names[i]}-{names[j]} {np.corrcoef(ranks[names[i]], ranks[names[j]])[0,1]:+.3f}")
        print(f"  {c:<8} " + "   ".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
