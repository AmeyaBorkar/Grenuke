"""Recall vs candidates per S1 for tok-view trim settings, from one wide blocking run, on the shared holdout; then
write the chosen trim as the final candidate tags. Pairs from the other views (already trimmed inside their view,
e.g. name_short) are always kept.

python experiments/ameya/block-v0/trim_curve.py <wide tag>                                   # curve only (train)
python experiments/ameya/block-v0/trim_curve.py <wide tag> --write <tag> --trim-s1 30 --trim-r 2 --splits train \
       --dev-tag <dev tag>
python experiments/ameya/block-v0/trim_curve.py <wide tag> --write <tag> --trim-s1 30 --trim-r 2 --splits test --no-curve
"""
import argparse

import numpy as np
import pandas as pd

from ber.artifacts import read_meta, read_table, write_table
from ber.block import VIEW_BITS
from ber.eval.metric import oracle_f05
from ber.eval.splits import in_dev_sample, is_holdout
from ber.paths import artifact_path
from ber.records import load_records, load_truth

TOK = VIEW_BITS["tok"]


def keep_mask(df: pd.DataFrame, a: int, b: int) -> np.ndarray:
    rs1, rr = df["rank_s1_tok"].to_numpy(), df["rank_r_tok"].to_numpy()
    tok = ((rs1 >= 0) & (rs1 < a)) | ((rr >= 0) & (rr < b))
    other = (df["views"].to_numpy().astype(np.int64) & ~TOK) != 0
    return tok | other


ap = argparse.ArgumentParser()
ap.add_argument("wide")
ap.add_argument("--write")
ap.add_argument("--trim-s1", type=int, default=30)
ap.add_argument("--trim-r", type=int, default=2)
ap.add_argument("--dev-tag")
ap.add_argument("--splits", default="train,test")
ap.add_argument("--no-curve", action="store_true")
args = ap.parse_args()

hold = th = None
if not args.no_curve or "train" in args.splits.split(","):
    rec = load_records("train", columns=["eid", "source"])
    s1_all = rec.loc[rec["source"] == 1, "eid"].to_numpy()
    hold = s1_all[is_holdout(s1_all)]
    truth = load_truth()
    th = truth[truth["s1"].isin(hold)]

if not args.no_curve:
    c = read_table("candidates", args.wide, "train", ["s1", "r", "views", "rank_s1_tok", "rank_r_tok"])
    ch = c[c["s1"].isin(hold)]
    hit = th.merge(ch, on=["s1", "r"], how="left")
    found = hit["views"].notna().to_numpy()
    hit = hit.fillna({"views": 0, "rank_s1_tok": -1, "rank_r_tok": -1})
    print(f"wide: holdout recall {found.mean():.4f}, {len(ch) / hold.size:.1f} candidates per S1")
    rows = []
    for a in (10, 15, 20, 25, 30, 35, 40):
        for b in (0, 1, 2, 3, 4):
            rows.append({"trim_s1": a, "trim_r": b, "recall": (keep_mask(hit, a, b) & found).mean(),
                         "cands_per_s1": keep_mask(ch, a, b).sum() / hold.size})
    tab = pd.DataFrame(rows)
    print(tab.pivot(index="trim_s1", columns="trim_r", values="recall").round(4).to_string())
    print(tab.pivot(index="trim_s1", columns="trim_r", values="cands_per_s1").round(1).to_string())
    del c, ch

if args.write:
    for split in args.splits.split(","):
        w = read_table("candidates", args.wide, split)
        out = w[keep_mask(w, args.trim_s1, args.trim_r)].reset_index(drop=True)
        meta = read_meta(artifact_path("candidates", args.wide, split))
        params = {**meta.get("params", {}), "final_trim_tok": [args.trim_s1, args.trim_r]}
        cmd = (f"python experiments/ameya/block-v0/trim_curve.py {args.wide} --write {args.write} "
               f"--trim-s1 {args.trim_s1} --trim-r {args.trim_r}")
        write_table(out, "candidates", args.write, split, command=cmd, inputs={"candidates": args.wide}, params=params)
        print(split, len(out), "pairs")
        if split == "train":
            print("holdout oracle F0.5", round(oracle_f05(out[out["s1"].isin(hold)], th, hold), 4))
            if args.dev_tag:
                dev = out[in_dev_sample(out["s1"].to_numpy())].reset_index(drop=True)
                write_table(dev, "candidates", args.dev_tag, "train", command=cmd, inputs={"candidates": args.wide},
                            params=params, subset="dev sample (ber.eval.splits.in_dev_sample)")
                print("dev", len(dev), "pairs")
        del w, out
