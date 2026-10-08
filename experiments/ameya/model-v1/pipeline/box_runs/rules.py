"""Two French recall rules suggested by the 7B's add candidates, measured on unpredicted + unowned candidate pairs:
A) acronym copy: R name == initials of the S1's core words (parenthesized tokens, legal forms, stopwords excluded), and the
   address agrees (same house number, or R address empty); B) exact-name copy with an empty R address, name unique among
   the country's S1. Precision on the labelled US/India holdout sample; counts on test by country."""
import re, sys, unicodedata
import numpy as np, pandas as pd, pyarrow.parquet as pq
from ber.paths import records_path
SP = "$SCRATCH"
LEG = set("sarl sas sasu eurl sa sci snc ei llc inc ltd limited pvt private corp co llp pllc pc lp plc".split())
STOP = set("de du des la le les l d et en sur a au aux the of and &".split())
def fold(s): return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
def core(name):
    s = re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", fold(name))
    return [w for w in re.split(r"[^a-z0-9]+", s) if w and w.replace(".", "") not in LEG and w not in STOP]
def acr(name): return "".join(w[0] for w in core(name) if w[0].isalpha())
def nname(name): return " ".join(core(name))
def num(addr):
    m = re.search(r"(?:^|[\s,#(])(?:n°|no|n)?\s*\(?0*(\d{1,4})\)?\s*(?:bis|ter|[a-d])?\s*\)?\s+[a-z]", fold(addr)); return m.group(1) if m else None
def feats(pairs, split):
    t = pq.read_table(records_path(split), columns=["eid", "source", "country", "name", "address"]).to_pandas()
    s1 = t[t.source == 1]
    cnt = s1.assign(nn=s1.name.map(nname)).groupby(["country", "nn"]).size()
    t = t.set_index("eid")
    sn, rn = t.name.reindex(pairs.s1).fillna("").to_numpy(), t.name.reindex(pairs.r).fillna("").to_numpy()
    sa, ra = t.address.reindex(pairs.s1).fillna("").to_numpy(), t.address.reindex(pairs.r).fillna("").to_numpy()
    c = t.country.reindex(pairs.s1).to_numpy()
    rl = np.array([re.sub(r"[^a-z]", "", fold(x)) for x in rn])
    A = np.array([len(r) >= 2 and r == acr(s) and (ra_.strip() == "" or (num(sa_) is not None and num(sa_) == num(ra_)))
                  for r, s, sa_, ra_ in zip(rl, sn, sa, ra)])
    nns = [nname(x) for x in sn]
    B = np.array([ra_.strip() == "" and n != "" and n == nname(r) and cnt.get((cc, n), 0) == 1 for ra_, n, r, cc in zip(ra, nns, rn, c)])
    return A, B, c
h = pd.read_parquet(f"{SP}/q7add/hold_add_scored.parquet")
A, B, c = feats(h, "train")
for nm, m in [("A acronym", A), ("B empty-address exact name, unique", B)]:
    print(f"holdout {nm}: {int(m.sum())} pairs, true {int(h.y[m].sum())} ({h.y[m].mean() if m.any() else float('nan'):.3f}); "
          f"US {int((m & (c == 'US')).sum())} / India {int((m & (c == 'India')).sum())}")
tt = pd.read_parquet(f"{SP}/q7add/test_add_all.parquet")
A2, B2, c2 = feats(tt, "test")
for nm, m in [("A acronym", A2), ("B empty-address exact name, unique", B2)]:
    x = tt[m].drop_duplicates("r")
    print(f"test {nm}: {len(x)} pairs by country {pd.Series(c2[m]).value_counts().to_dict()}; q7 median {x.q7__logit.median():.1f}")
tt.assign(ruleA=A2, ruleB=B2).to_parquet(f"{SP}/q7add/test_add_rules.parquet", index=False)
h.assign(ruleA=A, ruleB=B).to_parquet(f"{SP}/q7add/hold_add_rules.parquet", index=False)
