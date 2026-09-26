"""Follow-up to france_hypotheses.py: split the populations whose France prediction rate differs from the holdout
(H2 brand at the number, H3 list words, H4b same name + other number) by name collisions (s1_group) and by whether
the address shares the S1's street, to separate a real France error from France's much higher name-collision rate.

    python experiments/sachi/france_hyp_split.py --kit work/kits/france-kit-v1
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd

from france_hypotheses import HYP, enrich, fold

STREET_TYPES = set("rue r av avenue bd boulevard all allee chemin ch route rte place pl cours crs impasse imp quai "
                   "street st road rd lane ln drive dr nagar marg".split())
WORD = re.compile(r"[a-z]{3,}")


def street_words(s) -> frozenset:
    return frozenset(w for w in WORD.findall(fold(s)) if w not in STREET_TYPES)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kit", default="work/kits/france-kit-v1")
    a = ap.parse_args()
    kit = Path(a.kit)
    pd.set_option("display.width", 220)
    cols = ["s1", "r", "pc", "op", "same_num", "s1_group", "s1_name", "s1_address", "r_name", "r_address"]
    fr = pd.read_parquet(kit / "france_pairs.parquet", columns=cols + ["pred_final"])
    fr = enrich(fr, np.array(["France"] * len(fr)))
    ho = pd.read_parquet(kit / "holdout_pairs.parquet", columns=cols + ["y", "pred", "country"])
    ho = enrich(ho, ho["country"].to_numpy())
    for d in (fr, ho):
        sw = [len(street_words(x) & street_words(y)) > 0 for x, y in zip(d["s1_address"], d["r_address"])]
        d["street"] = np.where(sw, "street_shared", "street_diff")
        d["grp"] = pd.cut(d["s1_group"], [0, 1, 2, 10, np.inf], labels=["g1", "g2", "g3-10", "g11+"]).astype(str)
    fr["country"] = "France"
    for key in ("H2 one-word brand name at the S1's number, no shared word",
                "H3 no op, extra words all list words (+ maybe drops)",
                "H4b no op, same name, address present, number differs"):
        mf, mh = HYP[key](fr).to_numpy(), HYP[key](ho).to_numpy()
        h = ho[mh].groupby(["grp", "street", "country"]).agg(n=("y", "size"), truth=("y", "mean"),
                                                             pred=("pred", "mean")).unstack("country")
        h.columns = [f"{m}_{c}" for m, c in h.columns]
        f = fr[mf].groupby(["grp", "street"]).agg(fr_n=("r", "size"), fr_pred=("pred_final", "mean"),
                                                  fr_pc=("pc", "median"))
        t = f.join(h, how="outer")
        t["fr_per_1000"] = 1000 * t["fr_n"] / fr["s1"].nunique()
        tc = [c for c in t if c.startswith("truth_")]
        t["truth_min"] = t[tc].min(axis=1)
        t["gap"] = t["truth_min"] - t["fr_pred"]
        t["flag"] = np.where((t.truth_min >= 0.9) & (t.gap >= 0.2) & (t.fr_n >= 200), "ADD?", "")
        print(f"\n=== {key}")
        print(t.round(3).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
