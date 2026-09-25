"""Test matches for a decision variant of an existing model (a leaderboard probe; FINAL_PLAN section 5.7).

    python experiments/ameya/model-v1/variant.py --scores ameya-s2-v1 --col pc --shift -0.5 --tag ameya-model-v1-sm05

Applies argmax ownership + the expected-F0.5 decision with the given logit shift (or --threshold t) to the test
scores and writes C9 test matches under --tag; also reports the holdout macro F0.5 of the same rule on train.
"""
from __future__ import annotations

import argparse
import json

import numpy as np

from ber.artifacts import read_table, write_table
from ber.records import load_truth
from common import FastEval, argmax_owner, holdout_universe
from decide import expected_f_select

ap = argparse.ArgumentParser()
ap.add_argument("--scores", required=True)
ap.add_argument("--col", default="pc")
ap.add_argument("--tag", required=True)
g = ap.add_mutually_exclusive_group(required=True)
g.add_argument("--shift", type=float)
g.add_argument("--threshold", type=float)
args = ap.parse_args()
rule = {"method": "expected_f05", "shift": args.shift} if args.shift is not None else \
    {"method": "threshold", "threshold": args.threshold}
command = "python experiments/ameya/model-v1/variant.py " + " ".join(f"--{k} {v}" for k, v in vars(args).items() if v is not None)


def select(s1, r, p):
    own = argmax_owner(s1, r, p)
    return expected_f_select(s1, p, own, args.shift) if args.shift is not None else own & (p > args.threshold)


sc = read_table("scores", args.scores, "train", ["s1", "r", args.col])
s1, r, p = sc["s1"].to_numpy(), sc["r"].to_numpy(), sc[args.col].to_numpy(np.float32)
universe, _ = holdout_universe()
hold = np.isin(s1, universe)
sel = np.zeros(p.size, bool)
own = argmax_owner(s1, r, p)
sel[hold] = (expected_f_select(s1[hold], p[hold], own[hold], args.shift) if args.shift is not None
             else (own & (p > args.threshold))[hold])
f = FastEval(s1, r, load_truth(), universe).score(sel)
del sc, s1, r, p
st = read_table("scores", args.scores, "test", ["s1", "r", args.col])
m = st.loc[select(st["s1"].to_numpy(), st["r"].to_numpy(), st[args.col].to_numpy(np.float32)), ["s1", "r"]]
write_table(m.reset_index(drop=True), "matches", args.tag, "test", command=command, inputs={"scores": args.scores},
            rule=rule, holdout_macro_f05=f)
print(json.dumps({"rule": rule, "holdout_macro_f05": round(f, 5), "test_pairs": len(m),
                  "test_pred_per_s1": round(len(m) / st["s1"].nunique(), 4)}))
