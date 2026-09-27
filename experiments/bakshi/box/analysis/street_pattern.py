import re, glob, numpy as np, pandas as pd, pyarrow.parquet as pq
from ber.paths import records_path
D = "/workspace/grenuke/box/rescore"
STOPW = set("rue avenue av bd boulevard chemin route place allee impasse quai cours de du des la le les l d street st road rd drive dr lane ln avenue ave court ct way blvd highway hwy".split())
def parse(a):
    a = (a or "").lower().split(",")[0]
    m = re.search(r"\b(\d{1,5})\b", a)
    num = m.group(1) if m else ""
    words = frozenset(w for w in re.findall(r"[a-zà-ÿ]+", a) if len(w) > 1 and w not in STOPW)
    return num, words
def tag(pairs, split):
    ids = np.unique(np.r_[pairs.s1.to_numpy(), pairs.r.to_numpy()])
    t = pq.read_table(records_path(split), columns=["eid", "name", "address"]).to_pandas()
    t = t[t.eid.isin(ids)].set_index("eid")
    P = {e: parse(a) for e, a in t.address.items()}
    N = t.name.fillna("").str.lower().str.replace(r"[^a-z0-9à-ÿ]+", " ", regex=True).str.strip()
    out = []
    for s, r in zip(pairs.s1.to_numpy(), pairs.r.to_numpy()):
        (ns, ws), (nr, wr) = P.get(s, ("", frozenset())), P.get(r, ("", frozenset()))
        same_num = ns != "" and ns == nr
        jac = len(ws & wr) / max(1, len(ws | wr)) if (ws and wr) else -1
        out.append((same_num, jac, N.get(s, "") == N.get(r, "")))
    o = pd.DataFrame(out, columns=["same_num", "street_jac", "same_name"], index=pairs.index)
    return pairs.join(o)
h = tag(pd.read_parquet(f"{D}/hold_scored.parquet"), "train")
f = tag(pd.concat([pd.read_parquet(x) for x in sorted(glob.glob(f"{D}/fr_scored_*.parquet"))], ignore_index=True), "test")
for lab, d in (("US/India holdout (labelled)", h), ("France final", f)):
    pat = d.same_num & (d.street_jac >= 0) & (d.street_jac < 0.34)
    print(f"\n== {lab}: predicted pairs {len(d):,}; same number + different street: {int(pat.sum()):,} ({pat.mean():.2%})")
    if "y" in d: print(f"   truth rate of that pattern: {d.y[pat].mean():.3f}  (all predictions {d.y.mean():.4f}); with same name: {d.y[pat & d.same_name].mean():.3f} n={int((pat & d.same_name).sum())}")
    print(f"   7B logit on the pattern: median {d.q7__logit[pat].median():.2f}; share < 0: {(d.q7__logit[pat] < 0).mean():.2%}; share < -6: {(d.q7__logit[pat] < -6).mean():.2%}")
    print(f"   same name within the pattern: {int((pat & d.same_name).sum()):,}")
f[f.same_num & (f.street_jac >= 0) & (f.street_jac < 0.34)].to_parquet(f"{D}/fr_street_pattern.parquet", index=False)
def s1_name_freq(split):
    t = pq.read_table(records_path(split), columns=["eid", "source", "name"]).to_pandas()
    t = t[t.source == 1]
    n = t.name.fillna("").str.lower().str.replace(r"[^a-z0-9à-ÿ]+", " ", regex=True).str.strip()
    return pd.Series(n.map(n.value_counts()).to_numpy(), index=t.eid.to_numpy())
for lab, d, split in (("US/India holdout", h, "train"), ("France", f, "test")):
    d["s1_name_n"] = s1_name_freq(split).reindex(d.s1.to_numpy()).to_numpy()
    pat = d.same_num & (d.street_jac >= 0) & (d.street_jac < 0.34)
    for k in (2, 3, 5):
        m = pat & (d.s1_name_n >= k)
        extra = f" true {d.y[m].mean():.3f}" if "y" in d else ""
        print(f"{lab}: pattern & S1 name shared by >= {k} S1: {int(m.sum()):,}{extra}; 7B < 0: {(d.q7__logit[m] < 0).mean():.2%}")
    m = d.s1_name_n >= 3
    extra = f" true {d.y[m].mean():.3f}" if "y" in d else ""
    print(f"{lab}: ANY prediction whose S1 name is shared by >= 3 S1: {int(m.sum()):,}{extra}; 7B < 0: {(d.q7__logit[m] < 0).mean():.2%}")
