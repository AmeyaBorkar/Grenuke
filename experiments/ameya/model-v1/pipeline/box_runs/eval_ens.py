"""3-adapter q7st ensemble for the out-of-band drop rule. Adapter 0 scored every pair; adapters 1 and 2 re-scored the pairs
adapter 0 put below 0 (the others cannot be dropped by any rule here). Holdout macro F0.5 (Bakshi's sample + fixed
halves) for mean / max over the 3 adapters, against the single-adapter rule (q0 < -6); counts on test."""
import glob, sys
import numpy as np, pandas as pd, pyarrow.parquet as pq
from ber.paths import records_path
SP = "$SCRATCH"
R = "$REPO/work/bakshi_pull/train/box/rescore"
K = 4_000_000_000
key = lambda d: d.s1.to_numpy(np.int64) * K + d.r.to_numpy(np.int64)
def attach(d, split):
    for a in (1, 2):
        s = pd.read_parquet(f"{SP}/q7ens/adapter_{a}_{split}.parquet")
        v = pd.Series(s.q7__logit.to_numpy(), index=key(s)).reindex(key(d)).to_numpy()
        d[f"q{a}"] = np.where(np.isnan(v), d.q7__logit.to_numpy(), v)   # pairs not re-scored had q0 >= 0
    d["q0"] = d.q7__logit
    d["qmean"] = d[["q0", "q1", "q2"]].mean(axis=1); d["qmax"] = d[["q0", "q1", "q2"]].max(axis=1)
    return d
def f05(tp, n, nt):
    fp, fn = n - tp, nt - tp; den = 1.25 * tp + 0.25 * fn + fp
    return np.where((n == 0) & (nt == 0), 1.0, np.where(den > 0, 1.25 * tp / np.maximum(den, 1e-12), 0.0))
h = attach(pd.read_parquet(f"{R}/hold_scored.parquet"), "train")
truth = pd.read_parquet(f"{R}/hold_truth.parquet").set_index("s1")
def macro(keep):
    g = h[keep].groupby("s1").agg(tp=("y", "sum"), n=("y", "size")).reindex(truth.index).fillna(0)
    return f05(g.tp.to_numpy(), g.n.to_numpy(), truth.n_true.to_numpy())
base = macro(np.ones(len(h), bool)); half = (truth.index.to_numpy() // 7) % 2; ob = (h.p1 > 0.99).to_numpy()
fr = attach(pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(f"{R}/fr_scored_*.parquet"))], ignore_index=True), "test")
us = attach(pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(f"{SP}/q7drop/usin/usin_scored_*.parquet"))], ignore_index=True), "test")
print(f"adapter agreement on re-scored holdout pairs: corr(q0,q1) {h.loc[h.q0 < 0, ['q0', 'q1']].corr().iloc[0, 1]:.3f}, corr(q0,q2) {h.loc[h.q0 < 0, ['q0', 'q2']].corr().iloc[0, 1]:.3f}")
rows = []
for col in ["q0", "qmean", "qmax"]:
    for t in [-8, -7, -6, -5, -4, -3]:
        dh = (h[col] < t).to_numpy() & ob
        d = macro(~dh) - base
        nf = int(((fr[col] < t) & (fr.p1 > 0.99)).sum()); nu = int(((us[col] < t) & (us.p1 > 0.99)).sum())
        rows.append((col, t, int(dh.sum()), int(h.y[dh].sum()), d.mean(), d[half == 0].mean(), d[half == 1].mean(), nf, nu))
t = pd.DataFrame(rows, columns=["score", "t", "drops", "true", "dF", "dF_A", "dF_B", "FR drops", "US/IN drops"])
pd.set_option("display.width", 200); print(t.to_string(index=False, formatters={c: "{:+.6f}".format for c in ["dF", "dF_A", "dF_B"]}))
fr.to_parquet(f"{SP}/q7ens/fr_ens.parquet", index=False); us.to_parquet(f"{SP}/q7ens/us_ens.parquet", index=False)
