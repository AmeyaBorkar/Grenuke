import numpy as np, pandas as pd, pyarrow.parquet as pq
from ber.artifacts import read_table
from ber.paths import records_path
K = 4_000_000_000
key = lambda d: d.s1.to_numpy(np.int64) * K + d.r.to_numpy(np.int64)
t = pq.read_table(records_path("test"), columns=["eid", "source", "country"]).to_pandas()
lab = t.loc[(t.source == 1) & t.country.isin(["US", "India"]), "eid"].to_numpy()
m = read_table("matches", "ameya-model-g1w-s3-ops3a-dpc", "test")[["s1", "r"]]
m = m[np.isin(m.s1.to_numpy(), lab)].reset_index(drop=True)
p1 = read_table("scores", "ameya-s1-v6all", "test", ["s1", "r", "p1"])
m["p1"] = pd.Series(p1.p1.to_numpy(), index=key(p1)).reindex(key(m)).to_numpy(np.float32)
m = m[m.p1 > 0.99].reset_index(drop=True)
m.to_parquet("/workspace/grenuke/box/rescore/usin_final_pairs.parquet", index=False)
print(f"US/India final pairs outside the band: {len(m):,}")
