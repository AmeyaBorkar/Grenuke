"""Look at the French final pairs Bakshi's 7B (q7st) rejects hardest: q7 logit < -6 and p1 > 0.99 (outside the CE band)."""
import glob, sys
import numpy as np, pandas as pd
sys.path[1:1] = ["$REPO/.claude/worktrees/final-stack/experiments/ameya/model-v1/stack",
                 "$REPO/.claude/worktrees/final-stack/experiments/ameya/model-v1"]
from textlib import load_text
from ber.artifacts import read_table
K = 4_000_000_000
D = "$REPO/work/bakshi_pull/train/box/rescore"
fr = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(f"{D}/fr_scored_*.parquet"))], ignore_index=True)
print("rescored French pairs", len(fr), "columns", list(fr.columns))
d = fr[(fr.q7__logit < -6) & (fr.p1 > 0.99)].copy()
d["k"] = d.s1.to_numpy(np.int64) * K + d.r.to_numpy(np.int64)
print("q7 < -6 & p1 > 0.99:", len(d))
for tag in ["ameya-model-mixqc", "ameya-model-mixmdp", "ameya-model-mixnc"]:
    m = read_table("matches", tag, "test", ["s1", "r"])
    mk = np.unique(m.s1.to_numpy(np.int64) * K + m.r.to_numpy(np.int64))
    print(f"  in {tag}: {int(np.isin(d.k, mk).sum())}")
lk = pd.read_parquet("$SCRATCH/novel/drop_swapsim_all.parquet")
lkk = lk.s1.to_numpy(np.int64) * K + lk.r.to_numpy(np.int64)
print("  in the look-alike (swapsim) drop list:", int(np.isin(d.k, lkk).sum()), "of", len(lk))
# how many S1 lose all their predictions / how many predictions those S1 have
m = read_table("matches", "ameya-model-mixqc", "test", ["s1", "r"])
n_pred = m.groupby("s1").size()
d["n_pred_s1"] = n_pred.reindex(d.s1).fillna(0).to_numpy()
d["n_drop_s1"] = d.groupby("s1").s1.transform("size")
print("  S1 affected", d.s1.nunique(), "; drops that empty the S1:", int((d.n_pred_s1 == d.n_drop_s1).sum()),
      "; n_pred per affected S1 median", float(d.groupby('s1').n_pred_s1.first().median()))
t = load_text("test", np.r_[d.s1.to_numpy(), d.r.to_numpy()])
d["s1_name"] = t.name.reindex(d.s1).fillna("").to_numpy(); d["r_name"] = t.name.reindex(d.r).fillna("").to_numpy()
d["s1_addr"] = t.address.reindex(d.s1).fillna("").to_numpy(); d["r_addr"] = t.address.reindex(d.r).fillna("").to_numpy()
d.to_parquet("$SCRATCH/q7drop/fr_q7drop_pairs.parquet", index=False)
pd.set_option("display.width", 250)
for _, r in d.sample(40, random_state=1).iterrows():
    print(f"q7 {r.q7__logit:6.1f} p1 {r.p1:.4f} | S1: {r.s1_name[:38]:38s} | {r.s1_addr[:45]}")
    print(f"{'':20s}|  R: {r.r_name[:38]:38s} | {r.r_addr[:45]}")
