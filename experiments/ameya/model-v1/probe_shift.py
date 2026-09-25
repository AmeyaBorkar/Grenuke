"""Leaderboard probe: the same decision rule on test, with an extra logit shift for countries without training labels.

    python experiments/ameya/model-v1/probe_shift.py --scores ameya-s2-v4 --matches ameya-model-v4 --delta -1.0 --tag ameya-probe-v4fr-m10

France has no labels, so its calibration cannot be checked on the holdout, and the label-free diagnostics say the
model over-accepts there (predicted per S1 and the empty share are off the US/India values). A stricter rule for
France alone is one knob, tested with one upload (G8): every other country keeps the predictions of ``--matches``
exactly, so the leaderboard difference is France's alone. The rule (DP with shift, or threshold) is read from the
matches' metadata; France's probabilities get logit(p) + delta before it.
"""
from __future__ import annotations

import argparse
import json
import logging

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from ber.artifacts import read_table, write_table
from ber.paths import artifact_path
from common import argmax_owner
from decide import expected_f_select
from probe import s1_country

log = logging.getLogger("probe_shift")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores", required=True)
    ap.add_argument("--matches", required=True)
    ap.add_argument("--col", default="pc")
    ap.add_argument("--delta", type=float, required=True, help="logit shift for countries without training labels")
    ap.add_argument("--tag", required=True)
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    meta = json.loads(pq.read_schema(artifact_path("matches", args.matches, "test")).metadata[b"ber"])
    rule = meta["rule"]
    eid_tr, cty_tr = s1_country("train")
    eid, cty = s1_country("test")
    new = pd.Series(~pd.Series(cty).isin(set(cty_tr)).to_numpy(), index=eid)
    st = read_table("scores", args.scores, "test", ["s1", "r", args.col])
    s1, r = st["s1"].to_numpy(), st["r"].to_numpy()
    p = np.clip(st[args.col].to_numpy(np.float64), 1e-7, 1 - 1e-7)
    is_new = new.reindex(s1).fillna(False).to_numpy()
    z = np.log(p / (1 - p)) + np.where(is_new, args.delta, 0.0)
    q = 1 / (1 + np.exp(-z))
    own = argmax_owner(s1, r, q)
    if rule["method"] == "expected_f05":
        sel = expected_f_select(s1, q, own, rule["shift"])
    else:
        sel = own & (q > rule["threshold"])
    mt = st.loc[sel, ["s1", "r"]].reset_index(drop=True)
    base = read_table("matches", args.matches, "test")
    keep_old = ~new.reindex(base["s1"]).fillna(False).to_numpy()
    new_rows = new.reindex(mt["s1"]).fillna(False).to_numpy()
    out = pd.concat([base[keep_old], mt[new_rows]], ignore_index=True)
    n_new_s1 = int(new.sum())
    command = (f"python experiments/ameya/model-v1/probe_shift.py --scores {args.scores} --matches {args.matches} "
               f"--delta {args.delta} --tag {args.tag}")
    write_table(out[["s1", "r"]], "matches", args.tag, "test", command=command,
                inputs={"scores": args.scores, "matches": args.matches}, rule={**rule, "delta_new_countries": args.delta})
    log.info("%s: countries without labels %d S1; their predictions %d -> %d (%.3f -> %.3f per S1)", args.tag,
             n_new_s1, int((~keep_old).sum()), int(new_rows.sum()), (~keep_old).sum() / n_new_s1,
             new_rows.sum() / n_new_s1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
