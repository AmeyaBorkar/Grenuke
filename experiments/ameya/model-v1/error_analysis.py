"""Where does baseline v0 lose macro F0.5? Loss buckets on the dev holdout (dev sample, fold 0) from the dev kit.

    python experiments/ameya/model-v1/error_analysis.py [--model work/models/ameya-baseline-v0]

Ownership is computed inside the dev sample, so records lose rivals outside it (a slight optimistic bias on
wrong-owner errors). Buckets (per S1, loss = 1 - F0.5):
- singleton FP: a singleton S1 got a prediction;
- FP: predicted pairs that are not true (split: the record's true owner is another S1 / the record is an orphan);
- FN: true pairs not predicted (split: not a candidate / p below threshold / taken by another S1 through ownership).
"""
from __future__ import annotations

import argparse
import json
import re

import numpy as np
import pandas as pd
import xgboost as xgb

from ber.eval.metric import per_entity_f05
from ber.eval.splits import in_dev_sample, in_folds
from ber.paths import artifact_dir, artifact_path, records_path
from ber.records import load_truth

INDIC = re.compile("[ऀ-෿]")

ap = argparse.ArgumentParser()
ap.add_argument("--features", default="ameya-baseline-v0-dev")
ap.add_argument("--model", default="ameya-baseline-v0")
ap.add_argument("--examples", type=int, default=12)
args = ap.parse_args()

df = pd.read_parquet(artifact_path("features", args.features, "train"))
decide = json.loads((artifact_dir("models", args.model) / "decide.json").read_text())
booster = xgb.Booster(model_file=str(artifact_dir("models", args.model) / "xgb.ubj"))
booster.set_param({"device": "cpu"})
p = booster.inplace_predict(df[decide["features"]].to_numpy(np.float32))
t = decide["threshold"]

rec = pd.read_parquet(records_path("train"))
s1_all = rec.loc[rec["source"] == 1, "eid"].to_numpy()
universe = s1_all[in_dev_sample(s1_all) & in_folds(s1_all, (0,))]
truth = load_truth()
owner = truth.set_index("r")["s1"]

d = df.loc[df["fold"] == 0, ["s1", "r", "y"]].copy()
d["p"] = p[(df["fold"] == 0).to_numpy()]
# ownership inside the dev sample (every dev fold, so holdout records keep their dev rivals)
allp = df[["s1", "r"]].assign(p=p)
best = allp.sort_values(["r", "p"], ascending=[True, False]).drop_duplicates("r").set_index("r")["s1"]
d["own"] = best.reindex(d["r"]).to_numpy() == d["s1"].to_numpy()
d["pred"] = d["own"] & (d["p"] > t)
pred = d.loc[d["pred"], ["s1", "r"]]
th = truth[truth["s1"].isin(universe)]
ent = per_entity_f05(pred, th, universe)
ent["loss"] = 1 - ent["f05"]
print(f"dev holdout: {len(universe)} S1, macro F0.5 {ent['f05'].mean():.4f}, threshold {t}")

# pair-level buckets
fp = d[d["pred"] & (d["y"] == 0)].copy()
fp["kind"] = np.where(fp["r"].isin(owner.index), "fp_record_owned_elsewhere", "fp_record_is_orphan")
tp_pairs = th.merge(d[["s1", "r", "p", "own", "pred"]], on=["s1", "r"], how="left")
fn = tp_pairs[tp_pairs["pred"] != True].copy()  # noqa: E712 (NaN = not a candidate)
fn["kind"] = np.select([fn["p"].isna(), ~fn["own"].astype(bool)], ["fn_not_candidate", "fn_lost_to_other_s1"],
                       "fn_below_threshold")

# counterfactual loss per bucket: fix only that bucket and re-score
def fixed(drop_fp=None, add_fn=None) -> float:
    pp = pred
    if drop_fp is not None:
        key = fp.loc[fp["kind"] == drop_fp, ["s1", "r"]]
        pp = pp.merge(key, how="left", indicator=True).query("_merge == 'left_only'")[["s1", "r"]]
    if add_fn is not None:
        pp = pd.concat([pp, fn.loc[fn["kind"] == add_fn, ["s1", "r"]]])
    return per_entity_f05(pp, th, universe)["f05"].mean() - ent["f05"].mean()

base = ent["f05"].mean()
rows = []
for k in ("fp_record_owned_elsewhere", "fp_record_is_orphan"):
    rows.append((k, int((fp["kind"] == k).sum()), fixed(drop_fp=k)))
for k in ("fn_not_candidate", "fn_below_threshold", "fn_lost_to_other_s1"):
    rows.append((k, int((fn["kind"] == k).sum()), fixed(add_fn=k)))
print("\nbucket                          pairs    F0.5 gain if fixed")
for k, n, g in rows:
    print(f"{k:30s} {n:7d}    +{g:.4f}")
single = ent["n_true"] == 0
print(f"\nsingletons: {single.mean():.3f} of S1, F0.5 {ent.loc[single, 'f05'].mean():.4f}, "
      f"loss share {ent.loc[single, 'loss'].sum() / ent['loss'].sum():.3f}")
print("loss share by true set size:",
      (ent.groupby(ent["n_true"].clip(upper=7))["loss"].sum() / ent["loss"].sum()).round(3).to_dict())

# slices: country, Indic-script names among the true records
country = rec.set_index("eid")["country"]
name = rec.set_index("eid")["name"]
addr = rec.set_index("eid")["address"]
ent["country"] = country.reindex(ent.index).to_numpy()
indic_r = th["r"][name.reindex(th["r"]).str.contains(INDIC).to_numpy()]
ent["has_indic_true"] = ent.index.isin(th.loc[th["r"].isin(indic_r), "s1"])
print("\nby country:", ent.groupby("country")["f05"].mean().round(4).to_dict())
print("India S1 with an Indic-name true record:", round(ent.loc[ent["country"] == "India", "has_indic_true"].mean(), 3),
      "F0.5", ent.groupby("has_indic_true")["f05"].mean().round(4).to_dict(),
      "loss share", round(ent.loc[ent["has_indic_true"], "loss"].sum() / ent["loss"].sum(), 3))
fn["indic"] = fn["r"].isin(indic_r)
print("FN below threshold / lost: Indic share", fn.loc[fn["kind"] != "fn_not_candidate"].groupby("kind")["indic"].mean().round(3).to_dict())
print("p of FN below threshold (quantiles):", fn.loc[fn["kind"] == "fn_below_threshold", "p"].quantile([.1, .25, .5, .75, .9]).round(3).to_dict())
print("p of FP (quantiles):", fp["p"].quantile([.1, .25, .5, .75, .9]).round(3).to_dict())

def show(frame: pd.DataFrame, title: str) -> None:
    print(f"\n=== {title}")
    for _, x in frame.head(args.examples).iterrows():
        print(f"p={x['p']:.3f}  S1: {name[x['s1']][:45]:45s} | {addr[x['s1']][:70]}")
        print(f"         R{x['r'] // 10**9}: {name[x['r']][:45]:45s} | {addr[x['r']][:70]}")
        if x["r"] in owner.index and owner[x["r"]] != x["s1"]:
            o = owner[x["r"]]
            print(f"   owner S1: {name[o][:45]:45s} | {addr[o][:70]}")

rng = np.random.default_rng(0)
show(fp.sample(frac=1, random_state=1).query("kind == 'fp_record_is_orphan'"), "FP, record is an orphan (look-alikes?)")
show(fp.sample(frac=1, random_state=1).query("kind == 'fp_record_owned_elsewhere'"), "FP, record belongs to another S1")
show(fn.sample(frac=1, random_state=1).query("kind == 'fn_below_threshold'"), "FN below threshold")
show(fn.sample(frac=1, random_state=1).query("kind == 'fn_lost_to_other_s1'"), "FN lost to another S1")
