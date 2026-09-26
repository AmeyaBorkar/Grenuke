"""Leaderboard probe: a lower decision threshold for the countries without training labels (France) only.

    python experiments/ameya/model-v1/fr_add.py --model ameya-model-v7ce3-s3 --scores ameya-s3-v7ce3 --lo 0.5 \
        --p-cand 0.02 --top-r 2 --tag ameya-model-v7ce3-s3-frlo

The counterpart of fr_threshold.py, one step earlier in the pipeline. For target-country S1 it adds to the model's
matches the owned pairs (the record's argmax S1 inside the final candidate set, as in decide.py) whose pc is above
--lo and that the decision left out. The rules (post_ops) and the acronym join then run on the result as usual, so
op-B look-alikes among the additions are dropped. France's stage-1 scores sit in the uncertain band 2-3x as often as
US/India's; the leaderboard difference to the candidate, 0.14975 x (France F0.5 change), says whether the band just
below the threshold is underconfident. Adding it pays when its precision is above about 0.72 (a false positive costs
about 0.18 F0.5, a miss about 0.07).
"""
from __future__ import annotations

import argparse
import logging

import numpy as np
import pandas as pd
import pyarrow.compute as pc
import pyarrow.parquet as pq

from ber.artifacts import read_table, write_table
from ber.paths import records_path
from common import argmax_owner, candidate_mask

log = logging.getLogger("fr_add")
K = 4_000_000_000


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="the model's matches before the rules (decide.py output)")
    ap.add_argument("--scores", required=True)
    ap.add_argument("--lo", type=float, required=True, help="add owned target-country pairs with pc above this")
    ap.add_argument("--p-cand", type=float, default=0.02)
    ap.add_argument("--top-r", type=int, default=2)
    ap.add_argument("--tag", required=True)
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    tr = pq.read_table(records_path("train"), columns=["country"])
    labelled = set(pc.unique(tr["country"]).to_pylist())
    t = pq.read_table(records_path("test"), columns=["eid", "source", "country"])
    t = t.filter(pc.equal(t["source"], 1))
    cty = np.asarray(t["country"].to_numpy(zero_copy_only=False), dtype=object)
    target = np.sort(t["eid"].to_numpy()[~np.isin(cty, list(labelled))])
    sc = read_table("scores", args.scores, "test", ["s1", "r", "pc", "p1"])
    s1, r = sc["s1"].to_numpy(), sc["r"].to_numpy()
    keep = candidate_mask(s1, r, sc["p1"].to_numpy(), args.p_cand, args.top_r)
    p = np.where(keep, sc["pc"].to_numpy(np.float32), np.float32(0))
    own = argmax_owner(s1, r, p)
    m = read_table("matches", args.model, "test")
    pred = np.isin(s1 * K + r, m.s1.to_numpy() * K + m.r.to_numpy())
    add = own & (p > args.lo) & ~pred & np.isin(s1, target)
    out = pd.concat([m[["s1", "r"]], pd.DataFrame({"s1": s1[add], "r": r[add]})], ignore_index=True)
    write_table(out, "matches", args.tag, "test",
                command=(f"python experiments/ameya/model-v1/fr_add.py --model {args.model} --scores {args.scores} "
                         f"--lo {args.lo} --p-cand {args.p_cand} --top-r {args.top_r} --tag {args.tag}"),
                inputs={"model": args.model, "scores": args.scores}, added=int(add.sum()))
    q = np.quantile(p[add], [0.1, 0.5, 0.9]) if add.any() else []
    log.info("%s: added %d target-country pairs with pc above %.3f (%.1f per 1000 target S1; pc deciles 10/50/90 %s); "
             "%d pairs", args.tag, int(add.sum()), args.lo, 1000 * add.sum() / target.size, np.round(q, 3), len(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
