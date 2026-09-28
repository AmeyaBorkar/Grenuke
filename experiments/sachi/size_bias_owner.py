"""Can copy counts break the empty-address name ties? (the largest US/India loss; labels on the holdout)

    python experiments/sachi/size_bias_owner.py --kit work/kits/france-kit-v1

Hypothesis: an empty-address record whose exact name is shared by several S1 is abstained on as a coin flip (69% of
US/India misses). But the generator gives each S1 a copy count T from a fixed distribution with source caps, so the
S1s competing for the record are NOT exchangeable: how many copies each already holds changes how likely it is to own
one more. If the true owner is identifiable from the rivals' predicted copy counts well above chance, a rule can add
the argmax owner when its posterior clears the F0.5 break-even (~0.73-0.77 for an S1's extra record).

Test (holdout labels, honest split): records with an empty address and an exact-name match to >= 2 S1 of the kit's
holdout pairs, exactly one of them true. Features per candidate S1: its predicted copies excluding this record,
split by source. Posterior tables are fit on half A of the records (hash of r) and the add-rule is scored on half B
as the macro F0.5 change over the holdout universe (549,699 S1), and LB ~= 0.85 x that.
"""
from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

LEGAL = set("sarl sas sasu eurl sa sci snc ei llc inc ltd pvt private limited co corp corporation company llp lp pllc "
            "pc plc the".split())
TOK = re.compile(r"[a-z0-9]+")
N_UNIVERSE = 549_699


def fold(s) -> str:
    s = "" if s is None or (isinstance(s, float) and np.isnan(s)) else str(s)
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def key(s) -> str:
    return " ".join(sorted(t for t in TOK.findall(fold(s)) if t not in LEGAL))


def f05(h, t, p):
    d = 0.25 * t + p
    return np.where(d > 0, 1.25 * h / np.where(d > 0, d, 1), 1.0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kit", default="work/kits/france-kit-v1")
    ap.add_argument("--truth", default="work/records/truth.parquet")
    a = ap.parse_args()
    pd.set_option("display.width", 200)
    ho = pd.read_parquet(Path(a.kit) / "holdout_pairs.parquet",
                         columns=["s1", "r", "pc", "y", "pred", "country", "s1_group", "s1_name", "r_name", "r_address"])
    ho["y"] = ho["y"].astype(int)
    ho["pred"] = ho["pred"].astype(int)
    ho["src"] = (ho["r"] // 1_000_000_000).astype(int)
    addr = ho["r_address"].map(fold).str.strip()
    ho["noaddr"] = addr.isin(["", "null", "<null>", "none", "nan"]).to_numpy()
    ho["same"] = (ho["s1_name"].map(key) == ho["r_name"].map(key)).to_numpy() & (ho["s1_name"].map(key) != "")
    print(f"holdout pairs {len(ho):,}; S1 {ho.s1.nunique():,}")

    per = ho[ho.pred == 1].groupby(["s1", "src"]).size().unstack(fill_value=0)
    per.columns = [f"n{c}" for c in per.columns]
    for c in ("n2", "n3"):
        if c not in per:
            per[c] = 0
    truth = pd.read_parquet(a.truth, columns=["s1", "r"])
    n_true = truth.groupby("s1").size()

    c = ho[ho.noaddr & ho.same & (ho.s1_group >= 2)].copy()
    c = c.join(per, on="s1").fillna({"n2": 0, "n3": 0})
    c["own_src_n"] = np.where(c.src == 2, c.n2, c.n3) - c.pred
    c["other_n"] = c.n2 + c.n3 - c.pred
    g = c.groupby("r")
    c["k"] = g.s1.transform("size")
    c["n_true_in"] = g.y.transform("sum")
    c = c[(c.k >= 2) & (c.n_true_in == 1)].copy()
    print(f"ambiguous empty-address records with >= 2 holdout rivals and one true owner: {c.r.nunique():,} "
          f"({c.r.nunique() / N_UNIVERSE * 1000:.1f} per 1000 S1); model predicted {c.groupby('r').pred.max().mean():.3f}")
    if c.empty:
        return 0

    rng = np.random.default_rng(0)
    c["tie"] = rng.random(len(c))
    rows = []
    for feat in ("other_n", "own_src_n"):
        for how in ("min", "max"):
            s = c.sort_values(["r", feat, "tie"], ascending=[True, how == "min", True]).groupby("r").head(1)
            rows.append((feat, how, s.y.mean()))
    chance = (1 / c.groupby("r").k.first()).mean()
    print(f"\nchance (mean 1/k) {chance:.3f}")
    print(pd.DataFrame(rows, columns=["feature", "pick", "owner accuracy"]).round(3).to_string(index=False))

    k2 = c[c.k == 2].copy()
    k2["d"] = k2.other_n - k2.groupby("r").other_n.transform("sum") + k2.other_n
    tab = k2.groupby(k2.d.clip(-6, 6)).y.agg(["size", "mean"])
    print("\nk=2: P(true | own copies - rival copies)")
    print(tab.round(3).to_string())
    capped = c[((c.src == 2) & (c.n2 - c.pred >= 5)) | ((c.src == 3) & (c.n3 - c.pred >= 6))]
    print(f"\npairs whose S1 already holds the source cap: {len(capped):,}, true rate {capped.y.mean() if len(capped) else float('nan'):.3f}")

    c["rank"] = c.groupby("r").other_n.rank(method="first")
    half = (pd.util.hash_array(c.r.to_numpy()) % 2).astype(bool)
    post = c[~half].groupby([c.k.clip(upper=4), "rank"]).y.mean()
    b = c[half].copy()
    b["post"] = post.reindex(pd.MultiIndex.from_arrays([b.k.clip(upper=4), b["rank"]])).to_numpy()
    b = b[b.groupby("r").pred.transform("max") == 0]
    best = b.sort_values(["r", "post"], ascending=[True, False]).groupby("r").head(1)
    base = ho.groupby("s1").agg(p=("pred", "sum"), h=("y", lambda v: 0)).copy()
    hits = ho[ho.pred == 1].groupby("s1").y.sum()
    base["h"] = hits.reindex(base.index).fillna(0)
    base["t"] = n_true.reindex(base.index).fillna(0)
    print("\nadd the best-posterior owner of unpredicted records (half B, posterior from half A):")
    for thr in (0.5, 0.6, 0.7, 0.75, 0.8, 0.9):
        add = best[best.post >= thr]
        if add.empty:
            print(f"  post >= {thr:.2f}: 0 pairs")
            continue
        d = add.groupby("s1").agg(dp=("y", "size"), dh=("y", "sum"))
        bb = base.reindex(d.index)
        delta = (f05(bb.h + d.dh, bb.t, bb.p + d.dp) - f05(bb.h, bb.t, bb.p)).sum() * 2 / N_UNIVERSE
        print(f"  post >= {thr:.2f}: {len(add):,} pairs, precision {add.y.mean():.3f}, holdout dF {delta:+.6f}, "
              f"LB ~ {0.85 * delta:+.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
