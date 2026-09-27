import numpy as np, pandas as pd, pyarrow.parquet as pq
from sklearn.linear_model import LogisticRegression
from ber.artifacts import read_table
from ber.records import load_truth
from ber.paths import records_path
from common import holdout_universe
K = 4_000_000_000; B = "/workspace/grenuke/box"
CES = ["e5l", "qst", "e5ls", "bge", "q7st", "q34st"]; F = ["pc_l", "p1_l"] + CES
key = lambda d: d.s1.to_numpy(np.int64) * K + d.r.to_numpy(np.int64)
lg = lambda p: np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6)))
h = pd.read_parquet(f"{B}/rescore/meta_hold.parquet")
universe, _ = holdout_universe(); universe = np.asarray(universe)
truth = load_truth(); truth = truth[np.isin(truth.s1.to_numpy(), universe)]
ntrue = truth.groupby("s1").size().reindex(universe).fillna(0).to_numpy()
D = read_table("matches", "ameya-model-g1w-s3", "train")[["s1", "r"]]; D = D[np.isin(D.s1.to_numpy(), universe)].reset_index(drop=True)
D["y"] = np.isin(key(D), key(truth))
h["pred"] = np.isin(key(h), key(D)); owned = set(D.r.to_numpy())
def f05(tp, n, nt):
    fp, fn = n - tp, nt - tp; den = 1.25 * tp + 0.25 * fn + fp
    return np.where((n == 0) & (nt == 0), 1.0, np.where(den > 0, 1.25 * tp / np.maximum(den, 1e-12), 0.0))
def macro(P):
    g = P.groupby("s1").agg(tp=("y", "sum"), n=("y", "size")).reindex(universe).fillna(0)
    return f05(g.tp.to_numpy(), g.n.to_numpy(), ntrue)
hh = (universe // 7) % 2; base = macro(D)
print(f"holdout decisions {len(D):,}; band predicted {int(h.pred.sum()):,} (true {h.y[h.pred].mean():.4f}); band unpredicted {int((~h.pred).sum()):,}")
for t in (0.1, 0.2, 0.3, 0.4):
    dk = set(key(h[h.pred & (h.blend < t)])); P = D[~np.isin(key(D), list(dk))]
    d = macro(P) - base; n = len(D) - len(P)
    print(f"DROP band pred with blend < {t}: n={n:,} true={int(D.y[np.isin(key(D), list(dk))].sum()):,}  dF {d.mean():+.6f}  A {d[hh==0].mean():+.6f}  B {d[hh==1].mean():+.6f}")
for t in (0.9, 0.95, 0.98):
    a = h[~h.pred & (h.blend > t) & ~h.r.isin(owned)].sort_values("blend", ascending=False).drop_duplicates("r")
    P = pd.concat([D, a[["s1", "r", "y"]]]); d = macro(P) - base
    print(f"ADD band unpred with blend > {t} (record free): n={len(a):,} true={a.y.mean():.3f}  dF {d.mean():+.6f}  A {d[hh==0].mean():+.6f}  B {d[hh==1].mean():+.6f}")
# test lists (fit on all holdout)
X = h[F].fillna(0).to_numpy(np.float64); m = LogisticRegression(C=1.0, max_iter=3000).fit(X, h.y.to_numpy().astype(int))
bt = pd.read_parquet(f"{B}/band_test.parquet")
for n in CES:
    c = pd.read_parquet(f"{B}/out_{n}/ce_test.parquet"); bt[n] = pd.Series(c.ce__logit.to_numpy(), index=c.row.to_numpy()).reindex(bt.row.to_numpy()).to_numpy(np.float32)
s3t = read_table("scores", "ameya-s3-g1w", "test", ["s1", "r", "pc"])
bt["pc"] = pd.Series(s3t.pc.to_numpy(), index=key(s3t)).reindex(key(bt)).to_numpy(np.float32); bt = bt[bt.pc.notna()].reset_index(drop=True)
bt["pc_l"] = lg(bt.pc.to_numpy()); bt["p1_l"] = lg(bt.p1.to_numpy()); bt["blend"] = m.predict_proba(bt[F].fillna(0).to_numpy(np.float64))[:, 1]
rec = pq.read_table(records_path("test"), columns=["eid", "source", "country"]).to_pandas(); cty = pd.Series(rec.country.to_numpy(), index=rec.eid.to_numpy())
bt["country"] = cty.reindex(bt.s1.to_numpy()).to_numpy()
bt[["s1", "r", "p1", "pc", "blend", "country"]].to_parquet(f"{B}/rescore/meta_test_band.parquet", index=False)
print("test band rows with blend:", len(bt), bt.groupby("country").blend.apply(lambda x: f"<0.2: {(x<0.2).mean():.3%} >0.95: {(x>0.95).mean():.3%}").to_dict())
