"""Is 'same name + same house number + different street' a copy operation (true) or a decoy (false)? Labelled US/India
holdout sample: predicted pairs (hold_scored, with q7) and unpredicted cut rows (hold_add_scored); by name genericity."""
import re, unicodedata
import numpy as np, pandas as pd, pyarrow.parquet as pq
from rapidfuzz.distance import Indel
from ber.paths import records_path
SP = "C:/Users/ameya/AppData/Local/Temp/claude/C--Users-ameya-Documents-GrenukeAmazon/19e315ba-0725-4d6f-ae6a-972e1c1f0aa9/scratchpad"
R = "C:/Users/ameya/Documents/GrenukeAmazon/work/bakshi_pull/train/box/rescore"
TYPES = set("rue r ru avenue av ave boulevard bd blvd allee all place pl chemin ch route rte impasse imp cours crs quai q street st road rd drive dr lane ln court ct way highway hwy circle cir place pl parkway pkwy terrace ter trail trl".split())
STOP = set("de du des la le les l d et en sur a au aux the of and".split())
LEG = set("sarl sas sasu eurl sa sci snc ei llc inc ltd limited pvt private corp co llp pllc pc lp plc".split())
def fold(s): return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
def street(addr):
    for p in fold(addr).split(","):
        m = re.search(r"(\d{1,5})\s*(?:bis|ter|[a-d])?\s*\)?\s+([a-z][a-z' .-]+)", p.strip())
        if m:
            return m.group(1), " ".join(w for w in re.split(r"[\s'.-]+", m.group(2)) if w and w not in TYPES and w not in STOP)
    return None, ""
def nname(s): return " ".join(w for w in re.split(r"[^a-z0-9]+", re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", fold(s))) if w and w not in LEG)
t = pq.read_table(records_path("train"), columns=["eid", "source", "name", "address"]).to_pandas()
s1 = t[t.source == 1]; nn = s1.name.map(nname); freq = pd.Series(nn.map(nn.value_counts()).to_numpy(), index=s1.eid.to_numpy())
t = t.set_index("eid")
def tag(d):
    sa, ra = t.address.reindex(d.s1).fillna("").map(street), t.address.reindex(d.r).fillna("").map(street)
    sn_, rn_ = t.name.reindex(d.s1).fillna("").map(nname).to_numpy(), t.name.reindex(d.r).fillna("").map(nname).to_numpy()
    d = d.copy()
    d["same_num"] = [a[0] is not None and a[0] == b[0] for a, b in zip(sa, ra)]
    d["num_both"] = [a[0] is not None and b[0] is not None for a, b in zip(sa, ra)]
    d["num_gap"] = [abs(int(a[0]) - int(b[0])) if a[0] is not None and b[0] is not None else -1 for a, b in zip(sa, ra)]
    d["st_sim"] = [Indel.normalized_similarity(a[1], b[1]) if a[1] and b[1] else np.nan for a, b in zip(sa, ra)]
    d["same_name"] = sn_ == rn_
    d["gen"] = freq.reindex(d.s1).fillna(1).to_numpy()
    d["pat"] = (~d.same_num) & d.num_both & (d.st_sim >= 0.8) & (d.num_gap > 2)
    return d
for lab, f in [("PREDICTED (hold_scored)", f"{R}/hold_scored.parquet"), ("UNPREDICTED cut rows (hold_add_scored)", f"{SP}/q7add/hold_add_scored.parquet")]:
    d = tag(pd.read_parquet(f))
    print(f"\n== US/India holdout, {lab}: {len(d):,} pairs, true {d.y.mean():.4f}")
    for nm, m in [("pattern (same street, number differs by > 2)", d.pat), ("pattern & same name", d.pat & d.same_name),
                  ("pattern & same name & S1 name shared by >= 3 S1", d.pat & d.same_name & (d.gen >= 3)),
                  ("pattern & same name & shared by >= 10", d.pat & d.same_name & (d.gen >= 10))]:
        print(f"   {nm}: n={int(m.sum()):,}, true {d.y[m].mean() if m.any() else float('nan'):.3f}, 7B<-6 {int((m & (d.q7__logit < -6)).sum())}, 7B median {d.q7__logit[m].median() if m.any() else float('nan'):.1f}")
