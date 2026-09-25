"""Recall vs candidates per S1 for trim settings, from one wide blocking run (rank metadata), on the shared holdout.
Then writes the chosen trim as the final candidate tags (train + test, and the train dev subset).

python experiments/ameya/block-v0/trim_curve.py <wide tag> [--write <final tag> --trim-s1 N --trim-r M --dev-tag <tag>]
"""
import argparse

import numpy as np
import pandas as pd

from ber.artifacts import read_meta, read_table, write_table
from ber.eval.metric import oracle_f05
from ber.eval.splits import in_dev_sample, is_holdout
from ber.paths import artifact_path
from ber.records import load_records, load_truth

ap = argparse.ArgumentParser()
ap.add_argument("wide")
ap.add_argument("--write")
ap.add_argument("--trim-s1", type=int, default=30)
ap.add_argument("--trim-r", type=int, default=2)
ap.add_argument("--dev-tag")
args = ap.parse_args()

c = read_table("candidates", args.wide, "train")
rec = load_records("train", columns=["eid", "source", "country"])
s1_all = rec.loc[rec["source"] == 1, "eid"].to_numpy()
hold = s1_all[is_holdout(s1_all)]
truth = load_truth()
th = truth[truth["s1"].isin(hold)]
ch = c[c["s1"].isin(hold)]
hit = th.merge(ch, on=["s1", "r"], how="left")
rs1 = hit["rank_s1_tok"].fillna(-1).to_numpy()
rr = hit["rank_r_tok"].fillna(-1).to_numpy()
cs1 = ch["rank_s1_tok"].to_numpy()
cr = ch["rank_r_tok"].to_numpy()
rows = []
for a in (10, 15, 20, 25, 30, 35, 40):
    for b in (0, 1, 2, 3, 4):
        keep_t = ((rs1 >= 0) & (rs1 < a)) | ((rr >= 0) & (rr < b))
        keep_c = ((cs1 >= 0) & (cs1 < a)) | ((cr >= 0) & (cr < b))
        rows.append({"trim_s1": a, "trim_r": b, "recall": keep_t.mean(), "cands_per_s1": keep_c.sum() / hold.size})
tab = pd.DataFrame(rows)
print(tab.pivot(index="trim_s1", columns="trim_r", values="recall").round(4).to_string())
print(tab.pivot(index="trim_s1", columns="trim_r", values="cands_per_s1").round(1).to_string())

if args.write:
    for split in ("train", "test"):
        w = c if split == "train" else read_table("candidates", args.wide, "test")
        keep = ((w["rank_s1_tok"] >= 0) & (w["rank_s1_tok"] < args.trim_s1)) | ((w["rank_r_tok"] >= 0) & (w["rank_r_tok"] < args.trim_r))
        out = w[keep].reset_index(drop=True)
        meta = read_meta(artifact_path("candidates", args.wide, split))
        params = {**meta.get("params", {}), "trim_s1": args.trim_s1, "trim_r": args.trim_r}
        cmd = f"python experiments/ameya/block-v0/trim_curve.py {args.wide} --write {args.write} --trim-s1 {args.trim_s1} --trim-r {args.trim_r}"
        write_table(out, "candidates", args.write, split, command=cmd, inputs={"candidates": args.wide}, params=params)
        print(split, len(out), "pairs")
        if split == "train":
            ok = oracle_f05(out[out["s1"].isin(hold)], th, hold)
            print("holdout oracle F0.5", round(ok, 4))
            if args.dev_tag:
                dev = out[in_dev_sample(out["s1"].to_numpy())].reset_index(drop=True)
                write_table(dev, "candidates", args.dev_tag, "train", command=cmd, inputs={"candidates": args.wide},
                            params=params, subset="dev sample (ber.eval.splits.in_dev_sample)")
                print("dev", len(dev), "pairs")
