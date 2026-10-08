"""Evaluate an out-of-band detector (a synth3 CE's logit on confident predicted pairs) like Bakshi's rescore_eval.py:
drop a predicted pair when det < t and p1 > 0.99; macro F0.5 on the labelled US/India holdout sample (+ fixed halves);
France drop counts and overlap with the 7B's (q7 < -6) drops. usage: eval_det.py <out dir with ce_train/ce_test.parquet>"""
import glob, sys
import numpy as np, pandas as pd
SP = "$SCRATCH"
R = "$REPO/work/bakshi_pull/train/box/rescore"
K = 4_000_000_000
out = sys.argv[1]
def f05(tp, npred, ntrue):
    fp, fn = npred - tp, ntrue - tp
    den = 1.25 * tp + 0.25 * fn + fp
    return np.where((npred == 0) & (ntrue == 0), 1.0, np.where(den > 0, 1.25 * tp / np.maximum(den, 1e-12), 0.0))
def macro(h, keep, truth):
    g = h[keep].groupby("s1").agg(tp=("y", "sum"), npred=("y", "size")).reindex(truth.index).fillna(0)
    return pd.Series(f05(g.tp.to_numpy(), g.npred.to_numpy(), truth.n_true.to_numpy()), index=truth.index)
bt = pd.read_parquet(f"{SP}/oob/band_train.parquet", columns=["s1", "r", "row"])
ct = pd.read_parquet(f"{out}/ce_train.parquet")
bt["det"] = pd.Series(ct.ce__logit.to_numpy(), index=ct.row.to_numpy()).reindex(bt.row).to_numpy()
h = pd.read_parquet(f"{R}/hold_scored.parquet")
h["det"] = pd.Series(bt.det.to_numpy(), index=bt.s1.to_numpy() * K + bt.r.to_numpy()).reindex(h.s1.to_numpy() * K + h.r.to_numpy()).to_numpy()
truth = pd.read_parquet(f"{R}/hold_truth.parquet").set_index("s1")
print(f"holdout predicted pairs {len(h):,}, detector logit present {int(h.det.notna().sum()):,}")
fr = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(f"{R}/fr_scored_*.parquet"))], ignore_index=True)
te = pd.read_parquet(f"{SP}/oob/band_test.parquet", columns=["s1", "r", "row"])
cte = pd.read_parquet(f"{out}/ce_test.parquet")
te["det"] = pd.Series(cte.ce__logit.to_numpy(), index=cte.row.to_numpy()).reindex(te.row).to_numpy()
fr["det"] = pd.Series(te.det.to_numpy(), index=te.s1.to_numpy() * K + te.r.to_numpy()).reindex(fr.s1.to_numpy() * K + fr.r.to_numpy()).to_numpy()
print(f"French final pairs {len(fr):,}, detector logit present {int(fr.det.notna().sum()):,}")
ob_h, ob_f = (h.p1 > 0.99).to_numpy(), (fr.p1 > 0.99).to_numpy()
q7_h, q7_f = (h.q7__logit < -6).to_numpy() & ob_h, (fr.q7__logit < -6).to_numpy() & ob_f
half = (truth.index.to_numpy() // 7) % 2
base = macro(h, np.ones(len(h), bool), truth)
d7 = macro(h, ~q7_h, truth) - base
print(f"7B rule alone (q7 < -6): holdout drops {int(q7_h.sum())} (true {int(h.y[q7_h].sum())}), dF {d7.mean():+.6f}; France drops {int(q7_f.sum())}")
print("detector logit quantiles on out-of-band holdout pairs:", np.nanpercentile(h.det[ob_h], [0.01, 0.1, 1, 5, 50]).round(2))
print(f"{'t':>6} {'drops':>6} {'true':>5} {'dF':>10} {'dF A':>10} {'dF B':>10} {'FR drops':>8} {'FR & 7B':>7} | {'union dF':>10} {'union FR':>8}")
for t in [-8, -7, -6, -5, -4, -3, -2]:
    dh = (h.det < t).to_numpy() & ob_h
    d = macro(h, ~dh, truth) - base
    df_ = (fr.det < t).to_numpy() & ob_f
    du = macro(h, ~(dh | q7_h), truth) - base
    print(f"{t:>6} {int(dh.sum()):>6} {int(h.y[dh].sum()):>5} {d.mean():>+10.6f} {d[half == 0].mean():>+10.6f} {d[half == 1].mean():>+10.6f} "
          f"{int(df_.sum()):>8} {int((df_ & q7_f).sum()):>7} | {du.mean():>+10.6f} {int((df_ | q7_f).sum()):>8}")
fr.to_parquet(f"{out}/fr_det.parquet", index=False); h.to_parquet(f"{out}/hold_det.parquet", index=False)
