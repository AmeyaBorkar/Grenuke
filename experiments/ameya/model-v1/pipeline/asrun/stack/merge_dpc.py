"""US/India (the labelled countries) from the decide winner's parquet, every other country from a France-stack matches tag.
usage: merge_dpc.py <decided parquet> <france-stack matches tag> <out parquet>"""
import sys
import numpy as np, pandas as pd, pyarrow.parquet as pq
from ber.artifacts import read_table
from ber.paths import records_path
dec, ftag, out = sys.argv[1:4]
r = pq.read_table(records_path("test"), columns=["eid", "source", "country"]).to_pandas()
s1c = r[r.source == 1].set_index("eid").country
lab = ["US", "India"]
d = pd.read_parquet(dec)[["s1", "r"]].astype("int64")
f = read_table("matches", ftag, "test", ["s1", "r"]).astype("int64")
dl = d[s1c.reindex(d.s1).isin(lab).to_numpy()]
fo = f[~s1c.reindex(f.s1).isin(lab).to_numpy()]
m = pd.concat([dl, fo], ignore_index=True)
assert not m.r.duplicated().any(), "a record has two owners"
m.to_parquet(out, index=False)
print(f"US/India {len(dl)} from {dec.split('/')[-1]}; other countries {len(fo)} from {ftag}; total {len(m)}")
