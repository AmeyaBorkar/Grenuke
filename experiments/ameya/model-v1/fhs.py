"""French heuristic score (label-free): how a candidate's French final predictions differ from a reference in two
populations whose truth the generator fixes:
- COPY: the same content words up to typos (Cie = Compagnie), same address or an empty record address -> true copies;
- SWAP: one content word replaced (not a decoration word), same address -> look-alikes.
score per 1000 French S1 = (copies added - copies dropped) + (swaps dropped - swaps added).
usage: python experiments/ameya/model-v1/fhs.py <reference matches tag> <candidate matches tag> ...

The COPY column is the trusted one (RESEARCH_v6.md 6.14). SWAP mixes look-alikes with typo copies once op-B has
dropped the real-word swaps, so its sign is not known for France."""
import sys
import numpy as np, pandas as pd, pyarrow as pa, pyarrow.parquet as pq
import post_ops as po
from ber.block.text import fold
from ber.paths import records_path
from ber.artifacts import read_table
K = 4_000_000_000
NORM = {"cie": "compagnie", "ets": "etablissements", "st": "saint", "ste": "sainte", "cte": "comite", "asso": "association"}
t = pq.read_table(records_path("test"), columns=["eid", "source", "country", "name", "address"]).to_pandas().set_index("eid")
n_fr = int(((t.source == 1) & (t.country == "France")).sum())
def norm_name(s):
    return " ".join(NORM.get(w, w) for w in po.tokens(s))
def classify(d):
    s1, r = d.s1.to_numpy(), d.r.to_numpy()
    sn = fold(pa.array(t.name.reindex(s1).fillna("").tolist())).to_pylist(); rn = fold(pa.array(t.name.reindex(r).fillna("").tolist())).to_pylist()
    sa = fold(pa.array(t.address.reindex(s1).fillna("").tolist())).to_pylist(); ra = fold(pa.array(t.address.reindex(r).fillna("").tolist())).to_pylist()
    out = []
    for a, b, x, y in zip(sn, rn, sa, ra):
        kind, pos, add, drop = po.name_edit(norm_name(a), norm_name(b))
        ps, pr = po.addr_parts(x), po.addr_parts(y)
        empty = y.strip() == ""
        same = po.same_address(ps, pr)
        if kind in ("same", "acr") and (empty or same):
            out.append("COPY")
        elif kind == "swap" and same and add not in po.LIST_A and drop not in po.LIST_A:
            out.append("SWAP")
        else:
            out.append("other")
    return np.array(out)
ref = sys.argv[1]
A = read_table("matches", ref, "test")
A = A[t.country.reindex(A.s1).to_numpy() == "France"]
ka = A.s1.to_numpy() * K + A.r.to_numpy()
rows = []
for tag in sys.argv[2:]:
    B = read_table("matches", tag, "test")
    B = B[t.country.reindex(B.s1).to_numpy() == "France"]
    kb = B.s1.to_numpy() * K + B.r.to_numpy()
    drop, add = A[~np.isin(ka, kb)], B[~np.isin(kb, ka)]
    cd, ca = classify(drop), classify(add)
    f = lambda c, k: 1000 * (c == k).sum() / n_fr
    score = (f(ca, "COPY") - f(cd, "COPY")) + (f(cd, "SWAP") - f(ca, "SWAP"))
    rows.append({"candidate": tag.replace("ameya-model-", ""), "drops": len(drop), "adds": len(add),
                 "COPY +/-": f"+{f(ca, 'COPY'):.2f}/-{f(cd, 'COPY'):.2f}", "SWAP +/-": f"+{f(ca, 'SWAP'):.2f}/-{f(cd, 'SWAP'):.2f}",
                 "other +/-": f"+{f(ca, 'other'):.2f}/-{f(cd, 'other'):.2f}", "score/1000": round(score, 2)})
pd.set_option("display.width", 220)
print(f"reference {ref}; French S1 {n_fr}")
print(pd.DataFrame(rows).to_string(index=False))
