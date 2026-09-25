"""Loss buckets on the full shared holdout for any scores + matches pair (model-v1 experiments).

    python experiments/ameya/model-v1/buckets.py --scores ameya-s2-v1 --col pc --matches ameya-model-v1 \
        [--base ameya-baseline-v0] [--examples 0]

For every bucket: pairs, and the macro F0.5 gained if only that bucket were fixed (counterfactual):
- fp_owned_elsewhere / fp_orphan: predicted pairs that are wrong (the record belongs to another S1 / to none);
- fn_not_candidate / fn_below / fn_lost: true pairs missed (not a candidate / p too low / taken by another S1).
Also the loss share of singletons, per country, and of S1 with an Indic-script true record.
"""
from __future__ import annotations

import argparse
import re

import numpy as np
import pandas as pd

from ber.artifacts import read_table
from ber.eval.metric import per_entity_f05
from ber.records import load_records, load_truth
from common import argmax_owner, holdout_universe

INDIC = re.compile("[ऀ-෿]")


def buckets(pred: pd.DataFrame, sc: pd.DataFrame, p: np.ndarray, truth: pd.DataFrame, universe: np.ndarray) -> dict:
    th = truth[truth["s1"].isin(universe)]
    hold = sc["s1"].isin(universe).to_numpy()
    own = argmax_owner(sc["s1"].to_numpy(), sc["r"].to_numpy(), p)
    d = sc.loc[hold, ["s1", "r"]].assign(p=p[hold], own=own[hold])
    pred = pred[pred["s1"].isin(universe)]
    base = per_entity_f05(pred, th, universe)["f05"].mean()
    owner = truth.set_index("r")["s1"]
    fp = pred.merge(th.assign(t=1), on=["s1", "r"], how="left")
    fp = fp[fp["t"].isna()][["s1", "r"]]
    fp["kind"] = np.where(fp["r"].isin(owner.index), "fp_owned_elsewhere", "fp_orphan")
    tp = th.merge(d, on=["s1", "r"], how="left").merge(pred.assign(hit=1), on=["s1", "r"], how="left")
    fn = tp[tp["hit"].isna()].copy()
    fn["kind"] = np.select([fn["p"].isna(), ~fn["own"].astype(bool)], ["fn_not_candidate", "fn_lost"], "fn_below")
    out = {"macro_f05": float(base)}
    for k in ("fp_owned_elsewhere", "fp_orphan"):
        key = fp.loc[fp["kind"] == k, ["s1", "r"]]
        pp = pred.merge(key.assign(x=1), on=["s1", "r"], how="left")
        pp = pp[pp["x"].isna()][["s1", "r"]]
        out[k] = (int(len(key)), round(float(per_entity_f05(pp, th, universe)["f05"].mean() - base), 5))
    for k in ("fn_not_candidate", "fn_below", "fn_lost"):
        add = fn.loc[fn["kind"] == k, ["s1", "r"]]
        pp = pd.concat([pred[["s1", "r"]], add])
        out[k] = (int(len(add)), round(float(per_entity_f05(pp, th, universe)["f05"].mean() - base), 5))
    out["_fp"], out["_fn"] = fp, fn
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores", required=True)
    ap.add_argument("--col", default="pc")
    ap.add_argument("--matches", required=True)
    ap.add_argument("--examples", type=int, default=0)
    args = ap.parse_args()
    sc = read_table("scores", args.scores, "train", ["s1", "r", args.col])
    p = sc[args.col].to_numpy(np.float32)
    pred = read_table("matches", args.matches, "train")
    truth = load_truth()
    universe, country = holdout_universe()
    b = buckets(pred, sc, p, truth, universe)
    fp, fn = b.pop("_fp"), b.pop("_fn")
    print(f"holdout macro F0.5 {b.pop('macro_f05'):.5f}")
    print("bucket                  pairs   gain if fixed")
    for k, (n, g) in b.items():
        print(f"{k:22s} {n:7d}   +{g:.5f}")
    ent = per_entity_f05(pred[pred["s1"].isin(universe)], truth[truth["s1"].isin(universe)], universe)
    ent["loss"] = 1 - ent["f05"]
    ent["country"] = country.reindex(ent.index).to_numpy()
    single = ent["n_true"] == 0
    print(f"singletons {single.mean():.3f} of S1, F0.5 {ent.loc[single, 'f05'].mean():.4f}, "
          f"loss share {ent.loc[single, 'loss'].sum() / ent['loss'].sum():.3f}")
    print("by country:", ent.groupby("country")["f05"].mean().round(4).to_dict())
    if args.examples:
        rec = load_records("train").set_index("eid")
        indic_r = truth.loc[truth["s1"].isin(universe), "r"]
        indic_r = indic_r[rec["name"].reindex(indic_r).str.contains(INDIC).to_numpy()]
        has = ent.index.isin(truth.loc[truth["r"].isin(indic_r), "s1"])
        print("S1 with an Indic true record: F0.5", round(ent.loc[has, "f05"].mean(), 4), "loss share",
              round(ent.loc[has, "loss"].sum() / ent["loss"].sum(), 3))
        owner = truth.set_index("r")["s1"]
        pmap = pd.Series(p, index=pd.MultiIndex.from_arrays([sc["s1"], sc["r"]]))

        def show(frame: pd.DataFrame, title: str) -> None:
            print(f"\n=== {title}")
            for _, x in frame.sample(min(args.examples, len(frame)), random_state=0).iterrows():
                s, r = int(x["s1"]), int(x["r"])
                pv = pmap.get((s, r), np.nan)
                print(f"p={pv:.3f} S1: {rec.at[s, 'name'][:42]:42s} | {rec.at[s, 'address'][:66]}")
                print(f"        R{r // 10**9}: {rec.at[r, 'name'][:42]:42s} | {rec.at[r, 'address'][:66]}")
                if r in owner.index and owner[r] != s:
                    o = owner[r]
                    print(f"  owner S1: {rec.at[o, 'name'][:42]:42s} | {rec.at[o, 'address'][:66]}")

        show(fp[fp["kind"] == "fp_orphan"], "FP orphan (look-alikes)")
        show(fp[fp["kind"] == "fp_owned_elsewhere"], "FP owned elsewhere")
        show(fn[fn["kind"] == "fn_below"], "FN below")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
