"""Pseudo-labels for the France (target-country) test pairs, from a finished chain's decisions (self-training input
for ce_box.py --pseudo and s2.py --pseudo).

    python experiments/ameya/model-v1/pseudo_labels.py ameya-model-v7ce3-s3 ameya-s3-v7ce3 ameya-model-v7ce3-s3-ops3 ameya-model-v7ce3-s3-ops3a \
        s1:ameya-s1-v6all <out.parquet>

y = 1: in the final matches with pc >= POS, or added by the rules / the acronym join;
y = 0: not in the final matches with pc <= NEG, or an op-B prediction the rules dropped;
y = -1: the rest (unlabelled; still cross-fitted and scored by the model that did not see its S1 group).
The pairs are the cross-encoder band (band_test.parquet) or every stage-2 row of a stage-1 tag (s1:<tag>).
"""
import sys
import numpy as np, pandas as pd, pyarrow.parquet as pq, pyarrow.compute as pc
from ber.paths import records_path
from ber.artifacts import read_table
K = 4_000_000_000
POS, NEG = 0.9, 0.05
m_tag, s_tag, ops_tag, fin_tag, band, out = sys.argv[1:7]
tr = pq.read_table(records_path("train"), columns=["country"])
labelled = set(pc.unique(tr["country"]).to_pylist())
t = pq.read_table(records_path("test"), columns=["eid", "source", "country"]).to_pandas()
s1 = t[t.source == 1]
target = np.sort(s1.eid[~s1.country.isin(labelled)].to_numpy())
if band.startswith("s1:"):  # every target stage-2 row of a stage-1 tag (p0 >= tau0, p1 >= 0.002)
    import json
    from ber.paths import artifact_dir
    tag = band[3:]
    tau0 = json.loads((artifact_dir("models", tag) / "config.json").read_text())["tau0"]
    b = read_table("scores", tag, "test", ["s1", "r", "p0", "p1"])
    b = b[(b.p0.to_numpy() >= tau0) & (b.p1.to_numpy() >= 0.002)][["s1", "r"]]
else:
    b = pd.read_parquet(band, columns=["s1", "r"])
b = b[np.isin(b.s1.to_numpy(), target)].reset_index(drop=True)
bk = b.s1.to_numpy() * K + b.r.to_numpy()
key = lambda d: d.s1.to_numpy() * K + d.r.to_numpy()
sc = read_table("scores", s_tag, "test", ["s1", "r", "pc"])
sc = sc[np.isin(sc.s1.to_numpy(), target)]
pcs = pd.Series(sc.pc.to_numpy(), index=key(sc)).reindex(bk).fillna(0).to_numpy()
mod, ops, fin = (np.sort(key(read_table("matches", x, "test"))) for x in (m_tag, ops_tag, fin_tag))
in_m, in_ops, in_fin = (np.isin(bk, x) for x in (mod, ops, fin))
rule_add = in_ops & ~in_m
op_b = in_m & ~in_ops
acr_add = in_fin & ~in_ops
y = np.full(bk.size, -1, np.int8)
y[(in_fin & (pcs >= POS)) | rule_add | acr_add] = 1
y[(~in_fin & (pcs <= NEG)) | op_b] = 0
b["y"] = y
b.to_parquet(out, index=False)
print(f"target band pairs {len(b)}: positive {int((y == 1).sum())} (rule adds {int(rule_add.sum())}, acr {int(acr_add.sum())}), "
      f"negative {int((y == 0).sum())} (op-B drops {int(op_b.sum())}), unlabelled {int((y == -1).sum())}")
