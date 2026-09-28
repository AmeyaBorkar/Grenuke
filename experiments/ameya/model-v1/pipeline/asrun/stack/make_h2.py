"""v7s final + the hunt's changes, narrowed for France: US/India keep acr adds, cap drops and nsa drops; France keeps
only acr adds whose record address has no digit (the number-dropped acronym copies) and no cap drops (the French pc
cannot rank near-identical copies). Checks that final + all hunt changes reproduces the hunt's own parquet.
usage: make_h2.py <final tag> <hunted parquet> <changes csv> <out parquet>"""
import sys
import numpy as np, pandas as pd, pyarrow as pa, pyarrow.parquet as pq
from ber.artifacts import read_table
from ber.paths import records_path
K = 4_000_000_000
final, hunted, changes, out = sys.argv[1:5]
f = read_table("matches", final, "test", ["s1", "r"]).astype("int64")
h = pd.read_parquet(hunted)[["s1", "r"]].astype("int64")
ch = pd.read_csv(changes)
key = lambda d: d.s1.to_numpy() * K + d.r.to_numpy()
def apply(base, c):
    drop = c[c.action == "drop"]; add = c[c.action == "add"]
    b = base[~np.isin(key(base), key(drop))]
    return pd.concat([b, add[["s1", "r"]]], ignore_index=True).astype("int64")
re_all = apply(f, ch)
assert set(key(re_all)) == set(key(h)), "changes csv does not reproduce the hunted parquet"
fr_acr = ch[(ch.country == "France") & (ch.rule == "acr")]
ids = fr_acr.r.unique()
parts = [b.filter(pa.array(np.isin(b.column(0).to_numpy(), ids))).to_pandas()
         for b in pq.ParquetFile(records_path("test")).iter_batches(batch_size=2_000_000, columns=["eid", "address"])]
addr = pd.concat(parts).set_index("eid").address.fillna("")
nodigit = ~addr.reindex(fr_acr.r).str.contains(r"\d").to_numpy()
keep = pd.concat([ch[ch.country != "France"], fr_acr[nodigit]], ignore_index=True)
h2 = apply(f, keep)
assert not h2.r.duplicated().any()
h2.to_parquet(out, index=False)
print(f"final {len(f)}; hunt all {len(h)}; h2 {len(h2)}")
print(keep.groupby(["rule", "action", "country"]).size().to_string())
