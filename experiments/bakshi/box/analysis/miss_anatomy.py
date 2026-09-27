import json, re, numpy as np, pandas as pd, pyarrow as pa, pyarrow.parquet as pq
from ber.artifacts import read_table
from ber.paths import records_path
from ber.records import load_truth
from common import holdout_universe
K = 4_000_000_000
key = lambda d: d["s1"].to_numpy(np.int64) * K + d["r"].to_numpy(np.int64)
uni, country = holdout_universe(); uni = np.asarray(uni)
tr = load_truth(); tr = tr[np.isin(tr.s1.to_numpy(), uni)].reset_index(drop=True)
pred = read_table("matches", "ameya-model-g0-s3", "train")[["s1", "r"]]; pred = pred[np.isin(pred.s1.to_numpy(), uni)]
sc1 = read_table("scores", "ameya-s1-v6all", "train", ["s1", "r", "p1"])
s3 = read_table("scores", "ameya-s3-g0", "train", ["s1", "r", "pc"])
tk = key(tr); miss = tr[~np.isin(tk, key(pred))].copy(); mk = key(miss)
miss["p1"] = pd.Series(sc1.p1.to_numpy(), index=key(sc1)).reindex(mk).to_numpy()
miss["pc"] = pd.Series(s3.pc.to_numpy(), index=key(s3)).reindex(mk).to_numpy()
own = pred.drop_duplicates("r").set_index("r").s1
miss["r_owner"] = own.reindex(miss.r.to_numpy()).to_numpy()
cand = miss.p1.notna()
print(f"missed true pairs {len(miss):,} (of {len(tr):,})")
print(f"  record predicted for ANOTHER S1 (substitution): {(miss.r_owner.notna()).sum():,}")
print(f"  record predicted for nobody:                    {(miss.r_owner.isna()).sum():,}")
print(f"  not a candidate at all (blocking):              {(~cand).sum():,}")
c = miss[cand & miss.r_owner.isna()]
print("\nrejected candidates whose record is free, by stage-3 pc:")
print(pd.cut(c.pc.fillna(-1), [-2, -0.5, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 1.01]).value_counts().sort_index().to_string())
# S1 context of the misses
tn = tr.groupby("s1").size(); pn = pred.groupby("s1").size()
miss["s1_ntrue"] = tn.reindex(miss.s1).to_numpy(); miss["s1_npred"] = pn.reindex(miss.s1).fillna(0).to_numpy()
print("\nmissed pairs by the S1's number of true matches:")
print(pd.cut(miss.s1_ntrue, [0, 1, 2, 4, 8, 12, 99]).value_counts().sort_index().to_string())
# text of a sample: blocking misses and free rejected
rec = pq.read_table(records_path("train"), columns=["eid", "name", "address"]).to_pandas().set_index("eid")
def show(d, title, n=12):
    print(f"\n--- {title} (sample of {n}) ---")
    for _, x in d.sample(min(n, len(d)), random_state=1).iterrows():
        a, b = rec.loc[x.s1], rec.loc[x.r]
        print(f"S1 [{a['name'][:45]}] [{str(a['address'])[:50]}]\n R [{b['name'][:45]}] [{str(b['address'])[:50]}]  pc={x.pc if x.pc==x.pc else '-'}")
show(miss[~cand], "blocking misses")
show(c[c.pc < 0.3], "rejected, record free, pc < 0.3")
show(miss[miss.r_owner.notna()], "record went to another S1")
