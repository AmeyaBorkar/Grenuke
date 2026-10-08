"""The 7B out-of-band drop rule on the WHOLE US/India holdout: Bakshi's sample (hold_scored, 186,897 S1) + the rest
(hold2_scored, the other holdout S1's v7sq3 stage-3 predictions with p1 > 0.99). dF = sum of per-S1 F changes / all
holdout S1; fixed halves (s1 // 7 % 2) and per country."""
import numpy as np, pandas as pd, pyarrow.parquet as pq
from ber.artifacts import read_table
from ber.paths import artifact_path, records_path
from ber.records import load_truth
K = 4_000_000_000
SP = "$SCRATCH"
R = "$REPO/work/bakshi_pull/train/box/rescore"
def f05(tp, n, nt):
    fp, fn = n - tp, nt - tp; den = 1.25 * tp + 0.25 * fn + fp
    return np.where((n == 0) & (nt == 0), 1.0, np.where(den > 0, 1.25 * tp / np.maximum(den, 1e-12), 0.0))
# sample part: all predicted pairs with y, and n_true
h = pd.read_parquet(f"{R}/hold_scored.parquet"); ht = pd.read_parquet(f"{R}/hold_truth.parquet").set_index("s1")
# rest: predicted pairs of the other holdout S1 (all, for tp/n), their scores, and n_true from the truth
h2 = pd.read_parquet(f"{SP}/q7ens/hold2_scored.parquet")
s1s = np.unique(h2.s1.to_numpy())
mt = read_table("matches", "ameya-model-v7sq3-s3", "train", ["s1", "r"]); mt = mt[np.isin(mt.s1.to_numpy(), s1s)]
tr = load_truth(); tk = set((tr.s1.to_numpy(np.int64) * K + tr.r.to_numpy(np.int64)).tolist()) if "s1" in tr else None
cols = [c for c in tr.columns][:2]
tr = tr.rename(columns={cols[0]: "s1", cols[1]: "r"})
tk = np.sort(tr.s1.to_numpy(np.int64) * K + tr.r.to_numpy(np.int64))
mk = mt.s1.to_numpy(np.int64) * K + mt.r.to_numpy(np.int64)
j = np.searchsorted(tk, mk); j[j >= tk.size] = 0; mt["y"] = (tk[j] == mk).astype(np.int8)
nt2 = tr[np.isin(tr.s1.to_numpy(), s1s)].groupby("s1").size()
cty = pq.read_table(records_path("train"), columns=["eid", "source", "country"], filters=[("source", "==", 1)]).to_pandas().set_index("eid").country
N_HOLD = 549_699
def delta(pred, ntrue, drop_key):
    """pred: s1, r, y of all predicted pairs; ntrue: Series n_true by s1; returns per-S1 dF for S1 that lose a pair."""
    k = pred.s1.to_numpy(np.int64) * K + pred.r.to_numpy(np.int64)
    d = np.isin(k, drop_key)
    if not d.any():
        return pd.Series(dtype=float)
    s = np.unique(pred.s1.to_numpy()[d]); p = pred[np.isin(pred.s1.to_numpy(), s)]
    kk = p.s1.to_numpy(np.int64) * K + p.r.to_numpy(np.int64); dd = np.isin(kk, drop_key)
    g0 = p.groupby("s1").agg(tp=("y", "sum"), n=("y", "size"))
    g1 = p[~dd].groupby("s1").agg(tp=("y", "sum"), n=("y", "size")).reindex(g0.index).fillna(0)
    nt = ntrue.reindex(g0.index).fillna(0).to_numpy()
    return pd.Series(f05(g1.tp.to_numpy(), g1.n.to_numpy(), nt) - f05(g0.tp.to_numpy(), g0.n.to_numpy(), nt), index=g0.index)
a = pd.concat([h[["s1", "r", "p1", "q7__logit", "y"]], h2[["s1", "r", "p1", "q7__logit", "y"]]], ignore_index=True)
print(f"scored out-of-band holdout predictions: {int((a.p1 > 0.99).sum()):,} (sample {int((h.p1 > 0.99).sum()):,} + rest {len(h2):,})")
print(f"{'t':>4} {'drops':>6} {'true':>5} {'dF (all holdout)':>17} {'half A':>10} {'half B':>10} {'US':>10} {'India':>10}")
for t in [-8, -7, -6, -5, -4, -3]:
    dk = a[(a.q7__logit < t) & (a.p1 > 0.99)]
    key = dk.s1.to_numpy(np.int64) * K + dk.r.to_numpy(np.int64)
    d = pd.concat([delta(h[["s1", "r", "y"]], ht.n_true, key), delta(mt[["s1", "r", "y"]], nt2, key)])
    s1 = d.index.to_numpy(); half = (s1 // 7) % 2; c = cty.reindex(s1).to_numpy()
    tot = d.sum() / N_HOLD
    print(f"{t:>4} {len(dk):>6} {int(dk.y.fillna(0).sum()):>5} {tot:>+17.6f} {d[half == 0].sum() / (N_HOLD / 2):>+10.6f} {d[half == 1].sum() / (N_HOLD / 2):>+10.6f} "
          f"{d[c == 'US'].sum() / N_HOLD:>+10.6f} {d[c == 'India'].sum() / N_HOLD:>+10.6f}")
