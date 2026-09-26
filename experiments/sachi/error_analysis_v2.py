"""G4 evidence + error analysis of model v2 on dev fold 0 (dev kit v2).

    python experiments/sachi/error_analysis_v2.py
"""
import re

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from ber.artifacts import read_table
from ber.eval import in_dev_sample, in_folds, is_holdout, paired_bootstrap
from ber.model.decision import EvalIndex, argmax_ownership, f_vector
from ber.paths import records_path
from ber.records import load_records, load_truth

V2_SCORES, V2_MATCH, S1_MATCH, CANDS = "ameya-s2-v2-dev", "sachi-decide-v2", "sachi-s1-fx2-dev", "ameya-block-v1-dev"
key = lambda s1, r: np.asarray(s1, np.int64) * 4_000_000_000 + np.asarray(r, np.int64)

# ---- universe: dev-sample holdout S1 of fold 0
rec = load_records("train", columns=["eid", "source"])
s1 = rec.loc[rec["source"] == 1, "eid"].to_numpy()
U = s1[is_holdout(s1)]
U = U[in_folds(U, (0,))]
U = U[in_dev_sample(U)]
truth = load_truth()
ev = EvalIndex(U, truth.rename(columns={"s1": "s1_eid", "r": "r_eid"}))
print(f"holdout S1: {len(U):,}")


def fvec(tag):
    m = read_table("matches", tag, "train").rename(columns={"s1": "s1_eid", "r": "r_eid"})
    return f_vector(m[m["s1_eid"].isin(U)], ev)


# ---- G4: stage 1 only (79 features) -> v2 (stage 2)
fa, fb = fvec(S1_MATCH), fvec(V2_MATCH)
g = paired_bootstrap(fa, fb)
print(f"\nG4 stage-1 {fa.mean():.5f} -> v2 {fb.mean():.5f}: delta {g['delta']:+.5f}, "
      f"CI [{g['ci_low']:+.5f}, {g['ci_high']:+.5f}], p_better {g['p_better']:.3f}")

# ---- where do v2's errors come from?
t = truth[truth["s1"].isin(U)]
c = read_table("candidates", CANDS, "train", ["s1", "r"])
m = read_table("matches", V2_MATCH, "train")
m = m[m["s1"].isin(U)]
sc = read_table("scores", V2_SCORES, "train", ["s1", "r", "pc"])
own = argmax_ownership(sc.rename(columns={"s1": "s1_eid", "r": "r_eid", "pc": "p"}))
owner = pd.Series(own["s1_eid"].to_numpy(), index=own["r_eid"].to_numpy())
pc = pd.Series(sc["pc"].to_numpy(), index=key(sc["s1"], sc["r"]))

tk = key(t["s1"], t["r"])
in_c = np.isin(tk, key(c["s1"], c["r"]))
in_m = np.isin(tk, key(m["s1"], m["r"]))
stolen = in_c & ~in_m & (owner.reindex(t["r"]).to_numpy() != t["s1"].to_numpy())
low_p = in_c & ~in_m & ~stolen
n = len(t)
print(f"\ntrue pairs {n:,}: found {in_m.sum() / n:.2%}")
print(f"  missed by blocking             {(~in_c).sum() / n:.2%}")
print(f"  record owned by another S1     {stolen.sum() / n:.2%}")
print(f"  owned but p below threshold    {low_p.sum() / n:.2%}")
pl = pc.reindex(tk[low_p]).to_numpy()
print(f"  (below-threshold p: median {np.nanmedian(pl):.2f}, share with p >= 0.5: {(pl >= 0.5).mean():.1%})")
fp = m[~np.isin(key(m["s1"], m["r"]), tk)]
print(f"false matches {len(fp):,} ({len(fp) / len(m):.2%} of predictions)")

# ---- what do the error records look like vs correctly found ones?
groups = {"found": t[in_m], "blocking miss": t[~in_c], "stolen": t[stolen], "p too low": t[low_p], "false match": fp}
need = np.unique(np.concatenate([np.concatenate([g["s1"].to_numpy(), g["r"].to_numpy()]) for g in groups.values()]))
txt = pq.read_table(records_path("train"), columns=["eid", "country", "name", "address"],
                    filters=[("eid", "in", need.tolist())]).to_pandas().set_index("eid")
NUM = re.compile(r"\d+")


def profile(df):
    a, b = txt.reindex(df["s1"]), txt.reindex(df["r"])
    an, bn = a["address"].fillna("").to_numpy(), b["address"].fillna("").to_numpy()
    n1 = [NUM.findall(x)[:1] for x in an]
    n2 = [NUM.findall(x)[:1] for x in bn]
    return {
        "n": len(df),
        "India": (a["country"].to_numpy() == "India").mean(),
        "R name non-ASCII": b["name"].fillna("").str.contains(r"[^\x00-\x7f]", regex=True).mean(),
        "R addr empty/null": pd.Series(bn).str.strip().str.upper().isin(["", "NULL", "<NULL>"]).mean(),
        "R addr <=3 tokens": np.mean([len(x.split()) <= 3 for x in bn]),
        "1st number differs": np.mean([bool(x and y and x[0].lstrip("0") != y[0].lstrip("0")) for x, y in zip(n1, n2)]),
        "R has no number": np.mean([not y for y in n2]),
    }


tab = pd.DataFrame({k: profile(v) for k, v in groups.items()}).T
fmt = tab.copy()
for col in tab.columns[1:]:
    fmt[col] = (tab[col] * 100).round(1).astype(str) + "%"
fmt["n"] = tab["n"].astype(int)
pd.set_option("display.width", 200)
print("\nprofile of each group (compare each error group to 'found'):\n" + fmt.to_string())

# ---- a few examples of each error type
for name in ("stolen", "p too low", "false match"):
    g = groups[name].sample(min(6, len(groups[name])), random_state=0)
    print(f"\n--- {name} (examples) ---")
    for s, r in zip(g["s1"], g["r"]):
        a, b = txt.loc[s], txt.loc[r]
        print(f"  S1 {a['name']!r} | {a['address']!r}\n  R  {b['name']!r} | {b['address']!r}   pc={pc.get(key([s], [r])[0], float('nan')):.2f}")
