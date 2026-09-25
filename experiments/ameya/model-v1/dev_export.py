"""Export the dev-sample slice of a full-scale feature set and its scores for small machines (dev kit v2).

    python experiments/ameya/model-v1/dev_export.py --feats ameya-fx2 --groups str,cx,lo --s1 ameya-s1-v2 \
        --s2 ameya-s2-v2 --matches ameya-model-v2

Writes (dev sample = ber.eval.splits.in_dev_sample; fold 0 is the dev holdout, folds 5/10/15 one OOF group each):
- work/features/<feats>-dev/train.parquet: C8 layout, s1, r, fold, y + every feature of the groups (float32);
- work/scores/<s2>-dev/train.parquet: s1, r, fold, y, p0 (stage-0 filter), p1 (stage 1, out of fold),
  p2 (stage 2, out of fold), pc (p2 calibrated); scored on the full candidate graph, so the rivalry inside p2 sees
  every S1, not only the dev sample;
and prints the dev-holdout reference: the macro F0.5 of <matches> on dev fold 0.
"""
from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

import common
from ber.artifacts import read_table, write_table
from ber.eval.metric import report
from ber.eval.splits import in_dev_sample, in_folds
from ber.records import load_records, load_truth
from common import feature_names, iter_matrix, load_keys

ap = argparse.ArgumentParser()
ap.add_argument("--feats", default="ameya-fx2")
ap.add_argument("--groups", default="str,cx,lo")
ap.add_argument("--s1", default="ameya-s1-v2")
ap.add_argument("--s2", default="ameya-s2-v2")
ap.add_argument("--matches", default="ameya-model-v2")
args = ap.parse_args()
common.GROUPS[:] = args.groups.split(",")
command = "python experiments/ameya/model-v1/dev_export.py " + " ".join(f"--{k} {v}" for k, v in vars(args).items())

keys = load_keys(args.feats, "train")
dev = in_dev_sample(keys["s1"].to_numpy())
features = feature_names(args.feats)
X = np.concatenate([Xg for _, _, Xg in iter_matrix(args.feats, "train", features, dev)])
df = pd.concat([keys[dev].reset_index(drop=True), pd.DataFrame(X, columns=features)], axis=1)
df["fold"] = df["fold"].astype(np.int8)
df["y"] = df["y"].astype(np.int8)
write_table(df, "features", f"{args.feats}-dev", "train", command=command, inputs={"features": args.feats},
            subset="dev sample (ber.eval.splits.in_dev_sample)", groups=args.groups)
print(f"features: {len(df):,} rows x {len(features)} features -> {args.feats}-dev")

s1s = read_table("scores", args.s1, "train", ["p0"])["p0"].to_numpy()
s2s = read_table("scores", args.s2, "train")
if not (s2s["s1"].to_numpy() == keys["s1"].to_numpy()).all():
    raise ValueError("scores and features are not row-aligned")
sc = s2s[dev].reset_index(drop=True).assign(p0=s1s[dev])[["s1", "r", "fold", "y", "p0", "p1", "p2", "pc"]]
write_table(sc, "scores", f"{args.s2}-dev", "train", command=command, inputs={"scores": args.s2},
            subset="dev sample (ber.eval.splits.in_dev_sample)")
print(f"scores: {len(sc):,} rows -> {args.s2}-dev")

rec = load_records("train", ["eid", "source", "country"])
s1_all = rec.loc[rec["source"] == 1, "eid"].to_numpy()
universe = s1_all[in_dev_sample(s1_all) & in_folds(s1_all, (0,))]
country = rec.set_index("eid")["country"]
m = read_table("matches", args.matches, "train")
truth = load_truth()
rep = report(m[m["s1"].isin(universe)], truth[truth["s1"].isin(universe)], universe, groups=country)
print("dev holdout (dev sample, fold 0) reference:", json.dumps({k: (round(v, 4) if isinstance(v, float) else v)
                                                                  for k, v in rep.items()}))
