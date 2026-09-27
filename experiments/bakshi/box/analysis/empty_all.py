import numpy as np, pandas as pd, pyarrow.parquet as pq
from ber.artifacts import read_table
from ber.paths import records_path
from ber.records import load_truth
K = 4_000_000_000
key = lambda s1, r: s1.astype(np.int64) * K + r.astype(np.int64)
rec = pq.read_table(records_path("train"), columns=["eid", "source", "name", "address"]).to_pandas()
STOP = r"\b(llc|inc|ltd|limited|private|pvt|corp|corporation|co|company|enterprises?|group|partners|services?|trading|centre|center|llp|plc|the|and|of|holdings|international|intl)\b"
c = (rec.name.fillna("").str.lower().str.translate(str.maketrans("0183", "oibe")).str.replace(r"[^a-z]+", " ", regex=True)
     .str.replace(STOP, " ", regex=True).str.split().str.join(" "))
core = pd.Series(c.to_numpy(), index=rec.eid.to_numpy())
empty = pd.Series(rec.address.fillna("").str.strip().eq("").to_numpy(), index=rec.eid.to_numpy())
sc = read_table("scores", "ameya-s1-v6all", "train", ["s1", "r", "p1"])
sc = sc[empty.reindex(sc.r.to_numpy()).to_numpy()].reset_index(drop=True)          # empty-address records only
s3 = read_table("scores", "ameya-s3-g0", "train", ["s1", "r", "pc"])
sc["pc"] = pd.Series(s3.pc.to_numpy(), index=key(s3.s1.to_numpy(), s3.r.to_numpy())).reindex(key(sc.s1.to_numpy(), sc.r.to_numpy())).fillna(0).to_numpy()
del s3
tr = load_truth(); sc["y"] = np.isin(key(sc.s1.to_numpy(), sc.r.to_numpy()), key(tr.s1.to_numpy(), tr.r.to_numpy()))
sc["cs"] = core.reindex(sc.s1.to_numpy()).to_numpy(); sc["cr"] = core.reindex(sc.r.to_numpy()).to_numpy()
sc["same"] = (sc.cs == sc.cr) & (sc.cs != "")
n_same = sc[sc.same].groupby("r").size(); sc["n_same"] = n_same.reindex(sc.r.to_numpy()).fillna(0).to_numpy()
mx = sc.groupby("r").pc.max(); sc["r_maxpc"] = mx.reindex(sc.r.to_numpy()).to_numpy()
print(f"train candidate pairs with empty-address record: {len(sc):,}; truth {sc.y.mean():.3f}")
base = sc.same & (sc.n_same == 1)
for lab, m in [("core equal, ONE core-equal S1 among ALL train S1", base),
               ("... record claimed by nobody (max pc < 0.5)", base & (sc.r_maxpc < 0.5)),
               ("... and pair pc < 0.7 (not predicted)", base & (sc.r_maxpc < 0.5) & (sc.pc < 0.7))]:
    x = sc[m]; print(f"{lab:<52} pairs {len(x):>9,} true {x.y.mean():.3f}  new-true {int((x.y & (x.pc < 0.7)).sum()):,}")
x = sc[base & (sc.r_maxpc < 0.5) & (sc.pc < 0.7)]
print(x.groupby(pd.cut(x.p1, [0, 0.002, 0.02, 0.1, 0.3, 0.5, 0.8, 1]), observed=True).y.agg(["size", "mean"]).to_string())
