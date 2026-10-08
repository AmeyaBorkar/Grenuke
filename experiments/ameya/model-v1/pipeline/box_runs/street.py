"""French final pairs: house number + street name of S1 vs R; how often 'same number, different street' and what the 7B says."""
import glob, re, sys, unicodedata
import numpy as np, pandas as pd
from rapidfuzz.distance import Indel
sys.path[1:1] = ["$REPO/.claude/worktrees/final-stack/experiments/ameya/model-v1/stack",
                 "$REPO/.claude/worktrees/final-stack/experiments/ameya/model-v1"]
from textlib import load_text
K = 4_000_000_000
OUT = "$SCRATCH/q7drop"
D = "$REPO/work/bakshi_pull/train/box/rescore"
fr = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(f"{D}/fr_scored_*.parquet"))], ignore_index=True)
t = load_text("test", np.r_[fr.s1.to_numpy(), fr.r.to_numpy()])
TYPES = set("rue r ru avenue av ave boulevard bd bld blvd allee allees all place pl chemin ch che route rte impasse imp cours crs quai q square sq passage pass voie residence res lotissement lot cite hameau lieu dit lieu-dit chaussee parvis esplanade promenade rond-point faubourg fbg sentier villa cour".split())
STOP = set("de du des la le les l d et en sur sous a au aux".split())
NUM = re.compile(r"(?:^|[\s(#])(?:n°|no|n)?\s*\(?(\d{1,4})\)?\s*(bis|ter|[a-d])?\b")
def fold(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
def street(addr):
    """(number, street-name tokens) from the first comma part that has a number followed by words."""
    for p in fold(addr).split(","):
        p = p.strip()
        m = re.search(r"(\d{1,4})\s*(?:bis|ter|[a-d])?\s*\)?\s+([a-z][a-z' .-]+)", p)
        if m:
            words = [w for w in re.split(r"[\s'.-]+", m.group(2)) if w]
            name = [w for w in words if w not in TYPES and w not in STOP]
            return int(m.group(1)), " ".join(name)
    return None, ""
sn = t.address.reindex(fr.s1).fillna("").map(street)
rn = t.address.reindex(fr.r).fillna("").map(street)
fr["s_num"] = [a for a, _ in sn]; fr["s_st"] = [b for _, b in sn]
fr["r_num"] = [a for a, _ in rn]; fr["r_st"] = [b for _, b in rn]
both = fr.s_st.ne("") & fr.r_st.ne("") & fr.s_num.notna() & fr.r_num.notna()
fr["st_sim"] = np.nan
fr.loc[both, "st_sim"] = [Indel.normalized_similarity(a, b) for a, b in zip(fr.s_st[both], fr.r_st[both])]
fr["same_num"] = both & (fr.s_num == fr.r_num)
fr["mismatch"] = both & (fr.st_sim < 0.5)
fr.to_parquet(f"{OUT}/fr_street.parquet", index=False)
print(f"French final pairs {len(fr):,}; both addresses parsed {int(both.sum()):,}; street sim < 0.5: {int(fr.mismatch.sum()):,}"
      f" (same number {int((fr.mismatch & fr.same_num).sum()):,})")
qb = pd.cut(fr.q7__logit, [-99, -6, -4, -2, 0, 2, 99], right=False)
print("\nshare with a street mismatch, by 7B logit bucket (parsed pairs only):")
print(fr[both].groupby(qb[both], observed=True).agg(n=("mismatch", "size"), mismatch=("mismatch", "mean"), same_num_mis=("same_num", lambda s: float((s & fr.loc[s.index, "mismatch"]).mean()))).to_string())
print("\n7B logit of street-mismatch pairs:", fr.q7__logit[fr.mismatch].describe().round(2).to_dict())
print("p1 of street-mismatch pairs: >0.99", int((fr.p1[fr.mismatch] > 0.99).sum()), "<=0.99", int((fr.p1[fr.mismatch] <= 0.99).sum()))
s = fr[fr.mismatch & (fr.q7__logit >= 0)].sample(12, random_state=2)
print("\nstreet mismatch but the 7B says match (q7 >= 0):")
for _, r in s.iterrows():
    print(f"q7 {r.q7__logit:5.1f} p1 {r.p1:.3f} sim {r.st_sim:.2f} | {t.name.get(r.s1, '')[:30]:30s} | {t.address.get(r.s1, '')[:40]:40s} || {t.name.get(r.r, '')[:30]:30s} | {t.address.get(r.r, '')[:40]}")
