"""Seed bagging for stage 2: average p2 and pc of several stage-2 score tables with identical rows.

    python experiments/ameya/model-v1/bag_scores.py --scores ameya-s2-v7ce3,ameya-s2-v7ce3-seed1 --tag ameya-s2-v7ce3-bag

Each table's pc is already calibrated (its own isotonic map); the mean of calibrated probabilities is taken as is.
Writes work/scores/<tag>/{train,test}.parquet with the first table's other columns.
"""
from __future__ import annotations

import argparse

import numpy as np

from ber.artifacts import read_table, write_table


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores", required=True, help="comma-separated stage-2 score tags")
    ap.add_argument("--tag", required=True)
    args = ap.parse_args()
    tags = args.scores.split(",")
    for split in ("train", "test"):
        base = read_table("scores", tags[0], split)
        p2 = base["p2"].to_numpy(np.float64).copy()
        pc = base["pc"].to_numpy(np.float64).copy()
        for t in tags[1:]:
            o = read_table("scores", t, split, ["s1", "r", "p2", "pc"])
            if not (np.array_equal(o["s1"].to_numpy(), base["s1"].to_numpy()) and
                    np.array_equal(o["r"].to_numpy(), base["r"].to_numpy())):
                raise ValueError(f"{t} rows differ from {tags[0]} ({split})")
            p2 += o["p2"].to_numpy(np.float64)
            pc += o["pc"].to_numpy(np.float64)
        base["p2"] = (p2 / len(tags)).astype(np.float32)
        base["pc"] = (pc / len(tags)).astype(np.float32)
        write_table(base, "scores", args.tag, split, command=f"python experiments/ameya/model-v1/bag_scores.py --scores {args.scores} --tag {args.tag}",
                    inputs={f"scores{i}": t for i, t in enumerate(tags)})
        print(split, len(base))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
