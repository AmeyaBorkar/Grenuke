"""Gate + headroom check for the name-uniqueness features (sachi-fx2-name-dev vs ameya-fx2-dev, stage 1 only)."""
import numpy as np
import pandas as pd

from ber.artifacts import read_table
from ber.eval import in_dev_sample, in_folds, is_holdout, paired_bootstrap
from ber.model.decision import EvalIndex, f_vector
from ber.records import load_records, load_truth

BASE, CAND, FEAT = "sachi-s1-fx2-dev", "sachi-s1-name-dev", "sachi-fx2-name-dev"
key = lambda s1, r: np.asarray(s1, np.int64) * 4_000_000_000 + np.asarray(r, np.int64)

rec = load_records("train", columns=["eid", "source"])
s1 = rec.loc[rec["source"] == 1, "eid"].to_numpy()
U = s1[is_holdout(s1)]
U = U[in_folds(U, (0,))]
U = U[in_dev_sample(U)]
truth = load_truth()
ev = EvalIndex(U, truth.rename(columns={"s1": "s1_eid", "r": "r_eid"}))


def matches(tag):
    m = read_table("matches", tag, "train")
    return m[m["s1"].isin(U)]


fa = f_vector(matches(BASE).rename(columns={"s1": "s1_eid", "r": "r_eid"}), ev)
fb = f_vector(matches(CAND).rename(columns={"s1": "s1_eid", "r": "r_eid"}), ev)
g = paired_bootstrap(fa, fb)
keep = g["delta"] >= 0.002 and g["ci_low"] > 0
print(f"gate: {fa.mean():.5f} -> {fb.mean():.5f}  delta {g['delta']:+.5f}  CI [{g['ci_low']:+.5f}, {g['ci_high']:+.5f}]  "
      f"p_better {g['p_better']:.3f}  -> {'KEEP' if keep else 'do not keep'}")

# headroom: TRUE pairs whose record has an empty address
f = read_table("features", FEAT, "train", ["s1", "r", "addr__r_empty", "name__core_eq", "name__core_eq_unique", "ctx__r_core_n"])
t = truth[truth["s1"].isin(U)]
tf = t.merge(f, on=["s1", "r"], how="inner")                 # true pairs that are candidates
e = tf[tf["addr__r_empty"] == 1].copy()
kb, kc = key(matches(BASE)["s1"], matches(BASE)["r"]), key(matches(CAND)["s1"], matches(CAND)["r"])
ek = key(e["s1"], e["r"])
e["found_base"], e["found_cand"] = np.isin(ek, kb), np.isin(ek, kc)
print(f"\ntrue candidate pairs with an empty R address: {len(e):,} ({len(e) / len(tf):.1%} of true candidates)")
print(f"  exact core name:            {e['name__core_eq'].mean():.1%}")
print(f"  exact core name and unique: {e['name__core_eq_unique'].mean():.1%}")
print(f"  records' names shared by how many S1 (country): median {e['ctx__r_core_n'].median():.0f}, "
      f"0 = {(e['ctx__r_core_n'] == 0).mean():.1%}, 1 = {(e['ctx__r_core_n'] == 1).mean():.1%}, >=5 = {(e['ctx__r_core_n'] >= 5).mean():.1%}")
print(f"  found: baseline {e['found_base'].mean():.1%} -> with feature {e['found_cand'].mean():.1%}")
for name, grp in (("exact+unique", e[e["name__core_eq_unique"] == 1]), ("exact, not unique", e[(e["name__core_eq"] == 1) & (e["name__core_eq_unique"] == 0)]),
                  ("not exact", e[e["name__core_eq"] == 0])):
    if len(grp):
        print(f"    {name:18s} n={len(grp):6,}  found {grp['found_base'].mean():.1%} -> {grp['found_cand'].mean():.1%}")
