"""France's rule populations with their truth known from US/India, for label-free model comparisons.

    python experiments/ameya/model-v1/rule_pop.py <out.parquet>

post_ops.classify (rules v3, robust address) sorts the test candidate pairs of the countries without labels into
operations: A / APP / ACR true-copy edits (97-99.8% true in US/India, y=1) and op-B look-alikes (0-1.2% true, y=0).
Writes (s1, r, op, y); rule_auc.py and ce_rule_auc.py score models on it (RESEARCH_v6.md section 6.8).
"""
import sys
import numpy as np, pandas as pd, pyarrow.parquet as pq, pyarrow.compute as pc
from ber.paths import records_path
from post_ops import preselect, record_text, classify, s1_vocab
out = sys.argv[1]
tr = pq.read_table(records_path("train"), columns=["source", "country"])
labelled = set(pc.unique(tr["country"]).to_pylist())
rec = pq.read_table(records_path("test"), columns=["source", "country"])
targets = set(pc.unique(rec["country"]).to_pylist()) - labelled
cty, vocab = s1_vocab("test", targets)
target = cty[cty.isin(targets)]
d = preselect("ameya-fx5", "test", np.sort(target.index.to_numpy()))
names, keys, parts = record_text("test", np.unique(np.r_[d.s1.to_numpy(), d.r.to_numpy()]), True)
d = classify(d.assign(cty=target.reindex(d.s1).to_numpy()), names, keys, vocab, parts)
d = d[d.op.isin(["A", "APP", "ACR", "B"])].reset_index(drop=True)
d["y"] = (d.op != "B").astype(np.int8)
d[["s1", "r", "op", "y"]].to_parquet(out, index=False)
print(d.groupby("op").size().to_dict())
