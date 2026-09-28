import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from ber.artifacts import read_table
from ber.records import load_truth
from common import argmax_owner, holdout_universe
K = 4_000_000_000; B = "/workspace/grenuke/box"
CES = ["e5l", "qst", "e5ls", "bge", "q7st", "q34st"]
key = lambda d: d.s1.to_numpy(np.int64) * K + d.r.to_numpy(np.int64)
lg = lambda p: np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6)))
band = pd.read_parquet(f"{B}/band_train.parquet")
for n in CES:
    c = pd.read_parquet(f"{B}/out_{n}/ce_train.parquet")
    band[n] = pd.Series(c.ce__logit.to_numpy(), index=c.row.to_numpy()).reindex(band.row.to_numpy()).to_numpy(np.float32)
universe, country = holdout_universe(); universe = np.asarray(universe)
s3 = read_table("scores", "ameya-s3-g1w", "train", ["s1", "r", "pc"])
s3 = s3[np.isin(s3.s1.to_numpy(), universe)].reset_index(drop=True)
truth = load_truth(); truth = truth[np.isin(truth.s1.to_numpy(), universe)]
tk = key(truth); s3["y"] = np.isin(key(s3), tk)
ntrue = truth.groupby("s1").size().reindex(universe).fillna(0).to_numpy()
hold = band[np.isin(band.s1.to_numpy(), universe)].copy()
hold["pc"] = pd.Series(s3.pc.to_numpy(), index=key(s3)).reindex(key(hold)).to_numpy(np.float32)
hold = hold[hold.pc.notna()].reset_index(drop=True)
hold["pc_l"] = lg(hold.pc.to_numpy()); hold["p1_l"] = lg(hold.p1.to_numpy())
F = ["pc_l", "p1_l"] + CES
X = hold[F].fillna(0).to_numpy(np.float64); y = hold.y.to_numpy().astype(int)
half = (hold.s1.to_numpy() // 7) % 2
print(f"holdout band rows {len(hold):,} (true {y.mean():.3f}); AUCs:", {n: round(roc_auc_score(y, hold[n].fillna(0)), 4) for n in CES + ["pc"]})
blend = np.zeros(len(hold)); co = []
for a in (0, 1):
    m = LogisticRegression(C=1.0, max_iter=3000).fit(X[half == a], y[half == a])
    blend[half != a] = m.predict_proba(X[half != a])[:, 1]; co.append(m.coef_[0])
print("blend AUC (cross-fitted)", round(roc_auc_score(y, blend), 4), "| coefs", dict(zip(F, np.round(np.mean(co, 0), 2))))
def f05(tp, n, nt):
    fp, fn = n - tp, nt - tp; den = 1.25 * tp + 0.25 * fn + fp
    return np.where((n == 0) & (nt == 0), 1.0, np.where(den > 0, 1.25 * tp / np.maximum(den, 1e-12), 0.0))
def macro(pred):
    g = s3[pred].groupby("s1").agg(tp=("y", "sum"), n=("y", "size")).reindex(universe).fillna(0)
    return f05(g.tp.to_numpy(), g.n.to_numpy(), ntrue)
hh = (universe // 7) % 2
s1a, ra = s3.s1.to_numpy(), s3.r.to_numpy()
pc0 = s3.pc.to_numpy(np.float32)
idx = pd.Series(np.arange(len(s3)), index=key(s3)).reindex(key(hold)).to_numpy()
pcn = pc0.copy(); pcn[idx] = blend
for name, p in (("pc (current)", pc0), ("blend", pcn)):
    own = argmax_owner(s1a, ra, p)
    best = None
    for t in np.arange(0.5, 0.86, 0.025):
        f = macro(own & (p > t)); 
        if best is None or f.mean() > best[1]: best = (t, f.mean(), f[hh == 0].mean(), f[hh == 1].mean())
    print(f"{name:13} best t {best[0]:.3f}  macro F0.5 {best[1]:.6f}  halfA {best[2]:.6f}  halfB {best[3]:.6f}")
own0 = argmax_owner(s1a, ra, pc0); own1 = argmax_owner(s1a, ra, pcn)
b0 = macro(own0 & (pc0 > 0.7))
for t in (0.65, 0.7, 0.75):
    d = macro(own1 & (pcn > t)) - b0
    print(f"blend @ t={t}: dF all {d.mean():+.6f}  halfA {d[hh == 0].mean():+.6f}  halfB {d[hh == 1].mean():+.6f}")
np.save(f"{B}/rescore/meta_coefs.npy", np.array(co)); hold.assign(blend=blend).to_parquet(f"{B}/rescore/meta_hold.parquet", index=False)
