"""Our US/India final pairs (mixqc = v7sq3-s3-ops3a-dpc for the labelled countries) with stage-1 p1, for a 7B rescoring:
all of them (s1, r, p1); the drop rule only uses p1 > 0.99."""
import numpy as np, pandas as pd, pyarrow.compute as pc, pyarrow.parquet as pq
from ber.artifacts import read_table
from ber.paths import artifact_path, records_path
K = 4_000_000_000
OUT = "$SCRATCH/q7drop"
labelled = set(pc.unique(pq.read_table(records_path("train"), columns=["country"])["country"]).to_pylist())
r = pq.read_table(records_path("test"), columns=["eid", "source", "country"]).to_pandas()
s1c = r[r.source == 1].set_index("eid").country; del r
m = read_table("matches", "ameya-model-mixqc", "test", ["s1", "r"])
m = m[s1c.reindex(m.s1).isin(labelled).to_numpy()].reset_index(drop=True)
mk = m.s1.to_numpy(np.int64) * K + m.r.to_numpy(np.int64)
order = np.argsort(mk); ks = mk[order]
p1 = np.full(len(m), np.nan, np.float32)
f = pq.ParquetFile(artifact_path("scores", "ameya-s1-v6all", "test"))
for i in range(f.num_row_groups):
    t = f.read_row_group(i, columns=["s1", "r", "p1"])
    k = t["s1"].to_numpy().astype(np.int64) * K + t["r"].to_numpy().astype(np.int64)
    j = np.searchsorted(ks, k); j[j >= ks.size] = 0; hit = ks[j] == k
    p1[order[j[hit]]] = t["p1"].to_numpy()[hit]
m["p1"] = p1
print(f"US/India final pairs {len(m):,}; p1 found {int(np.isfinite(p1).sum()):,}; p1 > 0.99: {int((p1 > 0.99).sum()):,}")
m.to_parquet(f"{OUT}/ameya_usin_final.parquet", index=False)
