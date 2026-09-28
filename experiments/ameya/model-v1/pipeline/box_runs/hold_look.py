import sys
import numpy as np, pandas as pd
sys.path[1:1] = ["C:/Users/ameya/Documents/GrenukeAmazon/.claude/worktrees/final-stack/experiments/ameya/model-v1/stack",
                 "C:/Users/ameya/Documents/GrenukeAmazon/.claude/worktrees/final-stack/experiments/ameya/model-v1"]
from textlib import load_text
D = "C:/Users/ameya/Documents/GrenukeAmazon/work/bakshi_pull/train/box/rescore"
h = pd.read_parquet(f"{D}/hold_scored.parquet")
print(h.columns.tolist(), len(h))
d = h[(h.q7__logit < -4) & (h.p1 > 0.99)].sort_values("q7__logit")
t = load_text("train", np.r_[d.s1.to_numpy(), d.r.to_numpy()])
for _, r in d.iterrows():
    print(f"y={int(r.y)} q7 {r.q7__logit:6.1f} | {t.name.get(r.s1, '')[:30]:30s} | {t.address.get(r.s1, '')[:42]:42s} || {t.name.get(r.r, '')[:30]:30s} | {t.address.get(r.r, '')[:42]}")
# how many holdout predicted pairs have identical normalized addresses (candidates for a pre-filter)
import unicodedata, re
def nz(s): return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower())
t2 = load_text("train", np.r_[h.s1.to_numpy(), h.r.to_numpy()])
same = t2.address.reindex(h.s1).map(nz).to_numpy() == t2.address.reindex(h.r).map(nz).to_numpy()
sn = t2.name.reindex(h.s1).map(nz).to_numpy() == t2.name.reindex(h.r).map(nz).to_numpy()
print("holdout predicted pairs:", len(h), "identical address:", int(same.sum()), "identical name:", int(sn.sum()), "both:", int((same & sn).sum()))
print("q7 < -6 among identical-address pairs:", int(((h.q7__logit < -6) & same).sum()), "; among different-address:", int(((h.q7__logit < -6) & ~same).sum()))
