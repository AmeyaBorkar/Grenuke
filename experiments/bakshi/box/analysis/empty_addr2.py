import re, numpy as np, pandas as pd, pyarrow.parquet as pq
from ber.artifacts import read_table
from ber.paths import records_path
from ber.records import load_truth
from common import holdout_universe
K = 4_000_000_000
key = lambda d: d["s1"].to_numpy(np.int64) * K + d["r"].to_numpy(np.int64)
uni, _ = holdout_universe(); uni = np.asarray(uni)
rec = pq.read_table(records_path("train"), columns=["eid", "source", "name", "address"]).to_pandas().set_index("eid")
empty = rec.address.fillna("").str.strip().eq("")
print(f"train records: {len(rec):,}; S2/S3 with empty address: {empty[rec.source > 1].mean():.1%}")
STOP = set("llc inc ltd limited private pvt corp corporation co company enterprises enterprise group partners services service trading center centre llp plc the and of & holdings international intl".split())
def core(s):
    s = s.lower().translate(str.maketrans("0183", "oibe"))
    t = [w for w in re.split(r"[^a-z]+", s) if w and w not in STOP]
    return " ".join(sorted(t))
sc = read_table("scores", "ameya-s1-v6all", "train", ["s1", "r", "p1"])
sc = sc[np.isin(sc.s1.to_numpy(), uni)].reset_index(drop=True)
tr = load_truth(); tr = tr[np.isin(tr.s1.to_numpy(), uni)]
sc["y"] = np.isin(key(sc), key(tr))
pred = read_table("matches", "ameya-model-g0-s3", "train")[["s1", "r"]]
sc["pred"] = np.isin(key(sc), key(pred))
sc["r_empty"] = empty.reindex(sc.r.to_numpy()).to_numpy()
e = sc[sc.r_empty].copy()
print(f"holdout candidate pairs {len(sc):,}; with empty record address {len(e):,}; truth rate {e.y.mean():.3f}; predicted {e.pred.mean():.3f}")
names = rec.name.fillna("")
e["cs"] = [core(x) for x in names.reindex(e.s1.to_numpy())]
e["cr"] = [core(x) for x in names.reindex(e.r.to_numpy())]
e["same"] = (e.cs == e.cr) & (e.cs != "")
nq = e[e.same].groupby("r").size(); e["n_eq_s1"] = nq.reindex(e.r.to_numpy()).fillna(0).to_numpy()
r_owned = set(pred.r.to_numpy())
e["r_free"] = ~e.r.isin(r_owned)
for lab, m in [("core-name equal", e.same), ("core equal, record has ONE core-equal S1", e.same & (e.n_eq_s1 == 1)),
               ("... and record free (not predicted anywhere)", e.same & (e.n_eq_s1 == 1) & e.r_free),
               ("... and not already predicted", e.same & (e.n_eq_s1 == 1) & e.r_free & ~e.pred)]:
    x = e[m]; print(f"{lab:<48} pairs {len(x):>8,}  true {x.y.mean():.3f}  already predicted {x.pred.mean():.3f}  new true {int((x.y & ~x.pred).sum()):,}")
x = e[e.same & (e.n_eq_s1 == 1) & e.r_free & ~e.pred].copy()
pp = pred.copy(); pp["cr"] = [core(v) for v in names.reindex(pp.r.to_numpy())]; pp["src"] = rec.source.reindex(pp.r.to_numpy()).to_numpy()
x["src"] = rec.source.reindex(x.r.to_numpy()).to_numpy()
npred = pp.groupby("s1").size(); x["s1_npred"] = npred.reindex(x.s1.to_numpy()).fillna(0).to_numpy()
sib = set(zip(pp.s1.to_numpy(), pp.cr.to_numpy()))
x["sib_same_core"] = [(a, b) in sib for a, b in zip(x.s1.to_numpy(), x.cr.to_numpy())]
sib2 = set(zip(pp.s1.to_numpy(), pp.src.to_numpy()))
x["s1_has_pred_same_src"] = [(a, b) in sib2 for a, b in zip(x.s1.to_numpy(), x.src.to_numpy())]
print("ambiguous free pairs:", len(x), "true", round(x.y.mean(), 3))
print(x.groupby(["sib_same_core"]).y.agg(["size", "mean"]).to_string())
print(x.groupby(["s1_has_pred_same_src"]).y.agg(["size", "mean"]).to_string())
print(x.groupby([pd.cut(x.s1_npred, [-1, 0, 1, 2, 3, 5, 20])], observed=True).y.agg(["size", "mean"]).to_string())
print(x.groupby(["sib_same_core", "s1_has_pred_same_src", pd.cut(x.p1, [0, 0.1, 0.5, 1])], observed=True).y.agg(["size", "mean"]).to_string())
