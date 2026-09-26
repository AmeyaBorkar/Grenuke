"""The final candidate set: exactly the pairs stage 2 scores (p0 >= tau0 and p1 >= P_MIN).

    python experiments/ameya/model-v1/cands_final.py --s1 ameya-s1-v3 --tag ameya-cands-v3

The README asks for `candidate_pairs.tsv` to be "the exact set of records you feed into your matching model for
inference ... if your pipeline has several blocking/filtering stages, the last one". Our cascade is blocking ->
stage-0 filter (p0 >= tau0) -> stage 1 -> stage 2 on p1 >= P_MIN; pairs below that are never predicted. So the
candidate set is the stage-2 input. On the holdout (model v3): 4.75 pairs per S1 instead of 34, pair recall 0.98926
instead of 0.98992, oracle F0.5 0.99676 instead of 0.99697, and no prediction outside it (analysis in
ANALYSIS_v3.md). Writes work/candidates/<tag>/<split>.parquet (s1, r), for the write stage (--in candidates=<tag>).

The organisers rank a smaller candidate set per S1 higher, so --p-cand/--top-r cut it further (cand_size.py):
p1 >= 0.02 and the record's top 2 S1 by p1 give 3.70 pairs per test S1 instead of 4.68 with the holdout F0.5
unchanged. decide.py takes the same options so that the matches stay inside the set.
"""
from __future__ import annotations

import argparse
import json
import logging

import numpy as np

from ber.artifacts import read_table, write_table
from ber.paths import artifact_dir
from common import candidate_mask
from s2 import P_MIN

log = logging.getLogger("cands_final")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--s1", required=True, help="stage-1 scores tag (p0, p1)")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--split", default="test", choices=["train", "test"])
    ap.add_argument("--p-cand", type=float, default=P_MIN, help="keep p1 >= this (at least P_MIN)")
    ap.add_argument("--top-r", type=int, default=0, help="keep the record's top-r S1 by p1 (0: all)")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    tau0 = json.loads((artifact_dir("models", args.s1) / "config.json").read_text())["tau0"]
    sc = read_table("scores", args.s1, args.split, ["s1", "r", "p0", "p1"])
    keep = (sc["p0"].to_numpy() >= tau0) & candidate_mask(sc["s1"].to_numpy(), sc["r"].to_numpy(), sc["p1"].to_numpy(),
                                                          max(args.p_cand, P_MIN), args.top_r)
    out = sc.loc[keep, ["s1", "r"]].reset_index(drop=True)
    n_s1 = int(np.unique(sc["s1"].to_numpy()).size)
    command = (f"python experiments/ameya/model-v1/cands_final.py --s1 {args.s1} --tag {args.tag} --split {args.split}"
               f" --p-cand {args.p_cand} --top-r {args.top_r}")
    write_table(out, "candidates", args.tag, args.split, command=command, inputs={"scores": args.s1},
                rule={"tau0": tau0, "p_min": max(args.p_cand, P_MIN), "top_r": args.top_r})
    log.info("%s %s: %d of %d pairs kept (%.2f per S1 with candidates)", args.tag, args.split, len(out), len(sc),
             len(out) / max(n_s1, 1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
