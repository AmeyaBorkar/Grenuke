import re, numpy as np, pandas as pd, pyarrow.parquet as pq
from rapidfuzz import fuzz
from sklearn.tree import DecisionTreeClassifier, export_text
from ber.paths import records_path
D = "/workspace/grenuke/box/rescore"
h = pd.read_parquet(f"{D}/hold_scored.parquet")                 # s1, r, p1, pc, y, q7__logit
truth = pd.read_parquet(f"{D}/hold_truth.parquet").set_index("s1")
t = pq.read_table(records_path("train"), columns=["eid", "source", "name", "address"]).to_pandas().set_index("eid")
nm = t.name.fillna("").str.lower(); ad = t.address.fillna("").str.lower()
s1n = nm[t.source == 1].str.replace(r"[^a-z0-9]+", " ", regex=True).str.strip()
freq = s1n.map(s1n.value_counts())
num = lambda a: (re.search(r"\b(\d{1,5})\b", a) or [None, ""])[1] if isinstance(a, str) else ""
A1, A2 = ad.reindex(h.s1).to_numpy(), ad.reindex(h.r).to_numpy()
N1, N2 = nm.reindex(h.s1).to_numpy(), nm.reindex(h.r).to_numpy()
h["r_addr_empty"] = (A2 == "").astype(int)
h["name_sim"] = [fuzz.token_set_ratio(a, b) for a, b in zip(N1, N2)]
h["addr_sim"] = [fuzz.token_set_ratio(a, b) if b else -1 for a, b in zip(A1, A2)]
h["same_num"] = [int(num(a) != "" and num(a) == num(b)) for a, b in zip(A1, A2)]
h["s1_name_freq"] = freq.reindex(h.s1).fillna(1).to_numpy()
h["npred"] = h.groupby("s1").r.transform("size")
h["r_src"] = (h.r // 1_000_000_000).astype(int)
F = ["q7__logit", "p1", "pc", "r_addr_empty", "name_sim", "addr_sim", "same_num", "s1_name_freq", "npred", "r_src"]
X = h[F].fillna(-1).to_numpy(); y = h.y.to_numpy()
half = (h.s1.to_numpy() // 7) % 2
dt = DecisionTreeClassifier(max_depth=5, min_samples_leaf=40, class_weight={0: 50, 1: 1}, random_state=0).fit(X[half == 0], y[half == 0])
leaf = dt.apply(X)
L = pd.DataFrame({"leaf": leaf, "y": y, "half": half})
st = L.groupby("leaf").agg(n=("y", "size"), true=("y", "mean"), nA=("half", lambda s: (s == 0).sum()))
st["trueA"] = L[L.half == 0].groupby("leaf").y.mean(); st["trueB"] = L[L.half == 1].groupby("leaf").y.mean()
bad = st[(st.trueA < 0.7)].sort_values("n", ascending=False)
print(f"holdout predictions {len(h):,}, precision {y.mean():.5f}, false {int((1 - y).sum()):,}")
print("leaves with train-half truth < 0.70 (candidate drop slices):"); print(bad.to_string())
def f05(tp, npred, ntrue):
    fp, fn = npred - tp, ntrue - tp; den = 1.25 * tp + 0.25 * fn + fp
    return np.where((npred == 0) & (ntrue == 0), 1.0, np.where(den > 0, 1.25 * tp / np.maximum(den, 1e-12), 0.0))
def macro(keep):
    g = h[keep].groupby("s1").agg(tp=("y", "sum"), n=("y", "size")).reindex(truth.index).fillna(0)
    return pd.Series(f05(g.tp.to_numpy(), g.n.to_numpy(), truth.n_true.to_numpy()), index=truth.index)
base = macro(np.ones(len(h), bool)); hh = (truth.index.to_numpy() // 7) % 2
drop = np.isin(leaf, bad.index.to_numpy())
d = macro(~drop) - base
print(f"\ndrop all those leaves: {int(drop.sum()):,} pairs ({int(y[drop].sum()):,} true) -> dF all {d.mean():+.6f}, "
      f"train half A {d[hh == 0].mean():+.6f}, held-out half B {d[hh == 1].mean():+.6f}")
for lf in bad.index[:8]:
    dd = macro(leaf != lf) - base
    print(f"  leaf {lf}: n={int((leaf == lf).sum())} dF A {dd[hh == 0].mean():+.7f}  B {dd[hh == 1].mean():+.7f}")
print(export_text(dt, feature_names=F, max_depth=5)[:3500])
