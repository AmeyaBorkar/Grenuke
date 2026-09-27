import json, numpy as np, pandas as pd
from ber.artifacts import read_table
from ber.paths import artifact_dir
from ber.records import load_truth
from common import holdout_universe
K = 4_000_000_000
key = lambda d: d["s1"].to_numpy(np.int64) * K + d["r"].to_numpy(np.int64)
uni, country = holdout_universe()
uni = np.asarray(uni)
tau0 = json.loads((artifact_dir("models", "ameya-s1-v6all") / "config.json").read_text())["tau0"]
tr = load_truth(); tr = tr[np.isin(tr.s1.to_numpy(), uni)]
sc = read_table("scores", "ameya-s1-v6all", "train", ["s1", "r", "p0", "p1"])
sc = sc[np.isin(sc.s1.to_numpy(), uni)]
pred = read_table("matches", "ameya-model-g0-s3", "train")[["s1", "r"]]
pred = pred[np.isin(pred.s1.to_numpy(), uni)]
tk = key(tr); s = pd.DataFrame({"p0": sc.p0.to_numpy(), "p1": sc.p1.to_numpy()}, index=key(sc)).reindex(tk)
inp = np.isin(tk, key(pred))
cls = np.select([inp, s.p1.isna().to_numpy(), (s.p0 < tau0).to_numpy(), (s.p1 < 0.002).to_numpy(), (s.p1 < 0.02).to_numpy()],
                ["predicted", "not a candidate (blocking)", "stage-0 cut", "p1 < 0.002", "p1 0.002-0.02 (never CE-scored)"], "in band/high, not predicted")
print(f"holdout S1 {uni.size:,}; true pairs {len(tr):,}; predicted pairs {len(pred):,}; tau0 {tau0:.4f}")
print(pd.Series(cls).value_counts().to_string())
# F0.5 loss decomposition per holdout S1
t_n = tr.groupby("s1").size(); p_n = pred.groupby("s1").size()
tp = pd.Series(inp.astype(int), index=tr.s1.to_numpy()).groupby(level=0).sum()
d = pd.DataFrame(index=uni); d["nt"] = t_n.reindex(uni).fillna(0); d["np"] = p_n.reindex(uni).fillna(0); d["tp"] = tp.reindex(uni).fillna(0)
fp, fn = d.np - d.tp, d.nt - d.tp
f = np.where((d.np == 0) & (d.nt == 0), 1.0, 1.25 * d.tp / np.maximum(1.25 * d.tp + 0.25 * fn + fp, 1e-12))
loss = 1 - f
print(f"macro F0.5 {f.mean():.6f}; total loss {loss.sum():,.0f} S1-equivalents")
cat = np.select([(d.nt > 0) & (d.np == 0), (d.nt == 0) & (d.np > 0), (fp > 0) & (fn > 0), fp > 0, fn > 0], ["missed entirely", "false on singleton", "both FP+FN", "FP only", "FN only"], "correct")
print(pd.Series(loss, index=cat).groupby(level=0).agg(["size", "sum"]).rename(columns={"size": "S1", "sum": "loss"}).sort_values("loss", ascending=False).to_string())
