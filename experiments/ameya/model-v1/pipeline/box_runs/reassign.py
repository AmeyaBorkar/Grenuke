"""For the 859 French pairs the 7B rejects: is the R a real copy of ANOTHER French S1 with the same name (then reassign),
or a pure distractor (then drop)? Also: per-S1 prediction counts, France vs US/India."""
import re, sys, unicodedata
import numpy as np, pandas as pd, pyarrow.parquet as pq
from rapidfuzz.distance import Indel
from ber.paths import records_path
from ber.artifacts import read_table
SP = "C:/Users/ameya/AppData/Local/Temp/claude/C--Users-ameya-Documents-GrenukeAmazon/19e315ba-0725-4d6f-ae6a-972e1c1f0aa9/scratchpad"
K = 4_000_000_000
LEG = {"sarl", "sas", "sasu", "eurl", "sa", "sci", "snc", "ei", "s.a.r.l.", "s.a.s.", "s.a.s.u.", "e.u.r.l.", "s.a.", "s.c.i.", "e.i."}
def fold(s): return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
def nname(s): return " ".join(w for w in re.split(r"[\s\[\]()]+", fold(s)) if w and w.strip(".") not in {l.strip(".") for l in LEG})
TYPES = set("rue r ru avenue av ave boulevard bd allee all place pl chemin ch route rte impasse imp cours crs quai q square passage voie residence cite cour".split())
STOP = set("de du des la le les l d et en sur a au aux".split())
def street(addr):
    for p in fold(addr).split(","):
        m = re.search(r"(\d{1,4})\s*(?:bis|ter|[a-d])?\s*\)?\s+([a-z][a-z' .-]+)", p.strip())
        if m:
            return int(m.group(1)), " ".join(w for w in re.split(r"[\s'.-]+", m.group(2)) if w and w not in TYPES and w not in STOP)
    return None, ""
d = pd.read_parquet(f"{SP}/q7drop/fr_q7drop_pairs.parquet")
t = pq.read_table(records_path("test"), columns=["eid", "source", "country", "name", "address"]).to_pandas()
fr1 = t[(t.source == 1) & (t.country == "France")].copy()
fr1["nn"] = fr1.name.map(nname)
by_name = fr1.groupby("nn").eid.apply(list)
cands = read_table("candidates", "ameya-cands-mixqc", "test", ["s1", "r"])
ck = set((cands.s1.to_numpy(np.int64) * K + cands.r.to_numpy(np.int64)).tolist())
addr = t.set_index("eid").address
res = []
for _, x in d.iterrows():
    rn, rs = street(addr.get(x.r, ""))
    others = [e for e in by_name.get(nname(x.s1_name), []) if e != x.s1]
    hit = [e for e in others if rs and street(addr.get(e, ""))[1] and Indel.normalized_similarity(street(addr.get(e, ""))[1], rs) >= 0.7]
    hit_num = [e for e in hit if street(addr.get(e, ""))[0] == rn]
    res.append((len(others), len(hit), len(hit_num), sum((e * K + x.r) in ck for e in hit)))
r = pd.DataFrame(res, columns=["same_name_s1", "same_street", "same_street_num", "in_cands"])
print(f"rejected pairs {len(d)}: S1 has other same-name French S1: {int((r.same_name_s1 > 0).sum())} (median {r.same_name_s1.median():.0f})")
print(f"  another same-name S1 at the R's street: {int((r.same_street > 0).sum())}; with the same number too: {int((r.same_street_num > 0).sum())}; that pair in candidates: {int((r.in_cands > 0).sum())}")
m = read_table("matches", "ameya-model-mixf1", "test", ["s1", "r"])
c1 = t[t.source == 1].set_index("eid").country
m["c"] = c1.reindex(m.s1).to_numpy()
n = m.groupby("s1").agg(n=("r", "size"), c=("c", "first"))
tot = c1.value_counts()
print("\npredictions per S1 (mixf1), share of S1 with 0 / 1 / 2-4 / 5-7 / 8+ predictions:")
for c in ["US", "India", "France"]:
    k = n[n.c == c].n; z = tot[c] - len(k)
    b = [z, (k == 1).sum(), ((k >= 2) & (k <= 4)).sum(), ((k >= 5) & (k <= 7)).sum(), (k >= 8).sum()]
    print(f"  {c:7s} " + "  ".join(f"{v / tot[c]:.4f}" for v in b) + f"   mean {len(m[m.c == c]) / tot[c]:.3f}")
