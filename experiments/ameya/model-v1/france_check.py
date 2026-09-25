"""Eyeball test predictions for one country (default France, unseen in train; FINAL_PLAN section 6 hand checks).

    python experiments/ameya/model-v1/france_check.py --matches ameya-model-v1 --scores ameya-s2-v1 [--country France]

Prints a sample of S1 with their predicted records, then a sample of S1 left empty with their best owned candidate.
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from ber.artifacts import read_table
from ber.records import load_records
from common import argmax_owner

ap = argparse.ArgumentParser()
ap.add_argument("--matches", required=True)
ap.add_argument("--scores", required=True)
ap.add_argument("--col", default="pc")
ap.add_argument("--country", default="France")
ap.add_argument("--n", type=int, default=15)
args = ap.parse_args()

rec = load_records("test").set_index("eid")
m = read_table("matches", args.matches, "test")
sc = read_table("scores", args.scores, "test", ["s1", "r", args.col])
p = sc[args.col].to_numpy(np.float32)
own = argmax_owner(sc["s1"].to_numpy(), sc["r"].to_numpy(), p)
s1c = rec.index[(rec["source"] == 1) & (rec["country"] == args.country)]
pm = pd.Series(p, index=pd.MultiIndex.from_arrays([sc["s1"], sc["r"]]))
rng = np.random.default_rng(0)
with_pred = m[m["s1"].isin(s1c)]
print(f"{args.country}: {len(s1c)} S1, {with_pred['s1'].nunique()} with predictions, "
      f"{len(with_pred) / len(s1c):.2f} predicted records per S1")
for s in rng.choice(with_pred["s1"].unique(), size=min(args.n, with_pred["s1"].nunique()), replace=False):
    print(f"\nS1   {rec.at[s, 'name'][:45]:45s} | {rec.at[s, 'address'][:70]}")
    for r in with_pred.loc[with_pred["s1"] == s, "r"]:
        print(f"R{r // 10**9} p={pm[(s, r)]:.3f} {rec.at[r, 'name'][:40]:40s} | {rec.at[r, 'address'][:70]}")
empty = np.setdiff1d(s1c.to_numpy(), with_pred["s1"].unique())
best = sc[own & sc["s1"].isin(empty).to_numpy()].assign(p=p[own & sc["s1"].isin(empty).to_numpy()])
best = best.sort_values("p", ascending=False).drop_duplicates("s1")
print(f"\n=== {len(empty)} empty S1; best owned candidate for a sample")
for _, x in best.sample(min(args.n, len(best)), random_state=1).iterrows():
    s, r = int(x["s1"]), int(x["r"])
    print(f"S1   {rec.at[s, 'name'][:45]:45s} | {rec.at[s, 'address'][:70]}")
    print(f"R{r // 10**9} p={x['p']:.3f} {rec.at[r, 'name'][:40]:40s} | {rec.at[r, 'address'][:70]}\n")
