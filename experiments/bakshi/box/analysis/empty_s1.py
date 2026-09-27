import numpy as np, pandas as pd
from ber.artifacts import read_table
from ber.records import load_truth
from common import holdout_universe
K = 4_000_000_000
key = lambda d: d.s1.to_numpy(np.int64) * K + d.r.to_numpy(np.int64)
uni, _ = holdout_universe(); uni = np.asarray(uni)
tr = load_truth(); tr = tr[np.isin(tr.s1.to_numpy(), uni)]
pred = read_table("matches", "ameya-model-g1w-s3", "train")[["s1", "r"]]; pred = pred[np.isin(pred.s1.to_numpy(), uni)]
s3 = read_table("scores", "ameya-s3-g1w", "train", ["s1", "r", "pc"]); s3 = s3[np.isin(s3.s1.to_numpy(), uni)]
s3["y"] = np.isin(key(s3), key(tr))
empty = np.setdiff1d(uni, pred.s1.unique())
has_true = np.isin(empty, tr.s1.unique())
print(f"holdout S1 {uni.size:,}; predicted empty {empty.size:,}; of those with a true match {int(has_true.sum()):,} (singletons {int((~has_true).sum()):,})")
e = s3[np.isin(s3.s1.to_numpy(), empty)]
top = e.sort_values("pc", ascending=False).drop_duplicates("s1")
owned = set(pred.r.to_numpy()); top = top[~top.r.isin(owned)]
top["s1_has_true"] = top.s1.isin(tr.s1.unique())
print("empty S1: add its top free candidate; by pc of that candidate:")
g = top.groupby(pd.cut(top.pc, [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 1]), observed=True)
print(g.agg(n=("y", "size"), top_true=("y", "mean"), s1_has_match=("s1_has_true", "mean")).to_string())
# expected dF: true add -> F of that S1 goes 0 -> 1.25/(1.25+0.25*(nt-1)); false add on a singleton -> 1 -> 0; false add on non-singleton -> 0 -> 0
nt = tr.groupby("s1").size()
top["gain"] = np.where(top.y, 1.25 / (1.25 + 0.25 * (nt.reindex(top.s1).fillna(1).to_numpy() - 1)), np.where(top.s1_has_true, 0.0, -1.0))
for t in (0.2, 0.3, 0.4, 0.5, 0.6):
    m = top.pc >= t
    print(f"rescue if pc >= {t}: adds {int(m.sum()):,}, net S1-equivalents {top.gain[m].sum():+.1f} -> dF {top.gain[m].sum()/uni.size:+.6f}")
