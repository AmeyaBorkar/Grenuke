"""Leaderboard probe: a stricter decision threshold for the countries without training labels (France) only.

    python experiments/ameya/model-v1/fr_threshold.py --final ameya-model-v6all-c2-ops --model ameya-model-v6all-c2 \
        --scores ameya-s2-v6all --thr 0.9 --tag ameya-probe-v6all-fr090

Keeps every other country's predictions and the rule additions (pairs in --final but not in --model), and drops the
model's predictions for target-country S1 whose pc is below --thr. The leaderboard difference to --final is
0.14975 x (France F0.5 change), which prices France's uncertain band (pc in [0.70, thr)) directly: it is worth
dropping when its precision is below about 0.72 (a false positive costs about 0.18 F0.5, a miss about 0.07).
"""
from __future__ import annotations

import argparse
import logging

import numpy as np
import pyarrow.compute as pc
import pyarrow.parquet as pq

from ber.artifacts import read_table, write_table
from ber.paths import records_path

log = logging.getLogger("fr_threshold")
K = 4_000_000_000


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--final", required=True, help="matches after the rules")
    ap.add_argument("--model", required=True, help="the model's matches before the rules")
    ap.add_argument("--scores", required=True)
    ap.add_argument("--thr", type=float, required=True)
    ap.add_argument("--tag", required=True)
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    tr = pq.read_table(records_path("train"), columns=["country"])
    labelled = set(pc.unique(tr["country"]).to_pylist())
    t = pq.read_table(records_path("test"), columns=["eid", "source", "country"])
    t = t.filter(pc.equal(t["source"], 1))
    cty = np.asarray(t["country"].to_numpy(zero_copy_only=False), dtype=object)
    target = np.sort(t["eid"].to_numpy()[~np.isin(cty, list(labelled))])
    final = read_table("matches", args.final, "test")
    model = read_table("matches", args.model, "test")
    sc = read_table("scores", args.scores, "test", ["s1", "r", "pc"])
    sc = sc[sc.s1.isin(target)]
    fk = final.s1.to_numpy() * K + final.r.to_numpy()
    by_model = np.isin(fk, model.s1.to_numpy() * K + model.r.to_numpy())
    in_target = np.isin(final.s1.to_numpy(), target)
    pcs = sc.set_index(sc.s1.to_numpy() * K + sc.r.to_numpy()).pc
    p = pcs.reindex(fk).fillna(0).to_numpy()
    drop = in_target & by_model & (p < args.thr)
    out = final[~drop]
    write_table(out[["s1", "r"]].reset_index(drop=True), "matches", args.tag, "test",
                command=(f"python experiments/ameya/model-v1/fr_threshold.py --final {args.final} --model {args.model} "
                         f"--scores {args.scores} --thr {args.thr} --tag {args.tag}"),
                inputs={"final": args.final, "model": args.model, "scores": args.scores}, dropped=int(drop.sum()))
    log.info("%s: dropped %d target-country predictions with pc < %.3f (%.1f per 1000 target S1); %d pairs left",
             args.tag, int(drop.sum()), args.thr, 1000 * drop.sum() / target.size, len(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
