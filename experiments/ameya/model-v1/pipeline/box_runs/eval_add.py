"""Does ADDING unpredicted candidate pairs the 7B likes help macro F0.5? Holdout sample (labelled US/India), base = our
v7sq3 stage-3 predictions; one addition per record (the highest q7). Then counts on test by country."""
import glob
import numpy as np, pandas as pd, pyarrow.parquet as pq
from ber.paths import records_path
SP = "$SCRATCH"
R = "$REPO/work/bakshi_pull/train/box/rescore"
def f05(tp, npred, ntrue):
    fp, fn = npred - tp, ntrue - tp
    den = 1.25 * tp + 0.25 * fn + fp
    return np.where((npred == 0) & (ntrue == 0), 1.0, np.where(den > 0, 1.25 * tp / np.maximum(den, 1e-12), 0.0))
truth = pd.read_parquet(f"{R}/hold_truth.parquet").set_index("s1")
base = pd.read_parquet(f"{SP}/q7add/hold_base.parquet")
a = pd.read_parquet(f"{SP}/q7add/hold_add_scored.parquet")
cty = pq.read_table(records_path("train"), columns=["eid", "source", "country"], filters=[("source", "==", 1)]).to_pandas().set_index("eid").country
truth["c"] = cty.reindex(truth.index).to_numpy()
g0 = base.groupby("s1").agg(tp=("y", "sum"), n=("y", "size")).reindex(truth.index).fillna(0)
F0 = f05(g0.tp.to_numpy(), g0.n.to_numpy(), truth.n_true.to_numpy())
half = (truth.index.to_numpy() // 7) % 2
print(f"holdout sample {len(truth):,} S1, base F {F0.mean():.6f}; addable pairs {len(a):,} (true {a.y.mean():.3f})")
print("true rate by 7B logit bucket:", {str(k): (int(v[0]), round(float(v[1]), 3)) for k, v in a.groupby(pd.cut(a.q7__logit, [-99, 0, 2, 4, 6, 8, 10, 99])).y.agg(["size", "mean"]).iterrows()})
print(f"{'t':>5} {'adds':>6} {'true':>6} {'prec':>6} {'dF all':>10} {'dF A':>10} {'dF B':>10} {'dF US':>10} {'dF India':>10}")
for t in [0, 2, 4, 5, 6, 7, 8, 9, 10]:
    x = a[a.q7__logit > t].sort_values("q7__logit", ascending=False).drop_duplicates("r")
    g = pd.concat([base[["s1", "y"]], x[["s1", "y"]]]).groupby("s1").agg(tp=("y", "sum"), n=("y", "size")).reindex(truth.index).fillna(0)
    d = f05(g.tp.to_numpy(), g.n.to_numpy(), truth.n_true.to_numpy()) - F0
    us, ind = (truth.c == "US").to_numpy(), (truth.c == "India").to_numpy()
    print(f"{t:>5} {len(x):>6} {int(x.y.sum()):>6} {x.y.mean() if len(x) else 0:>6.3f} {d.mean():>+10.6f} {d[half == 0].mean():>+10.6f} {d[half == 1].mean():>+10.6f} "
          f"{d[us].mean():>+10.6f} {d[ind].mean():>+10.6f}")
tt = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(f"{SP}/q7add/test_add_scored_*.parquet"))], ignore_index=True)
ct = pq.read_table(records_path("test"), columns=["eid", "source", "country"], filters=[("source", "==", 1)]).to_pandas().set_index("eid").country
tt["c"] = ct.reindex(tt.s1).to_numpy()
print(f"\ntest addable scored {len(tt):,}")
for t in [4, 6, 8, 10]:
    x = tt[tt.q7__logit > t].sort_values("q7__logit", ascending=False).drop_duplicates("r")
    print(f"  q7 > {t}: adds {len(x):,} by country {x.c.value_counts().to_dict()}")
tt.to_parquet(f"{SP}/q7add/test_add_all.parquet", index=False)
