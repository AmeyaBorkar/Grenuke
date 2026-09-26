"""Leaderboard probe matches: one country's test predictions from another tag, or emptied (gate G7).

    python experiments/ameya/model-v1/probe.py --base ameya-model-v3 --country France --from ameya-model-v4 --tag ameya-probe-v3fr4
    python experiments/ameya/model-v1/probe.py --base ameya-model-v3 --country France --empty --tag ameya-probe-v3fr0

The probe keeps every other country's predictions of ``--base``, so the leaderboard difference to ``--base`` is
w_country * (F0.5 of the new country predictions - F0.5 of the old ones), with the same S1 set on both sides.
Writes work/matches/<tag>/test.parquet; package it with the write stage (candidates must contain the new pairs).
"""
from __future__ import annotations

import argparse
import logging

import numpy as np
import pyarrow.compute as pc
import pyarrow.parquet as pq

from ber.artifacts import read_table, write_table
from ber.paths import records_path

log = logging.getLogger("probe")


def s1_country(split: str) -> tuple[np.ndarray, np.ndarray]:
    """(S1 eids, country labels) of a split."""
    t = pq.read_table(records_path(split), columns=["eid", "source", "country"])
    t = t.filter(pc.equal(t["source"], 1))
    return t["eid"].to_numpy(), np.asarray(t["country"].to_numpy(zero_copy_only=False), dtype=object)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--country", required=True)
    ap.add_argument("--from", dest="src", default="")
    ap.add_argument("--empty", action="store_true")
    ap.add_argument("--tag", required=True)
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    if bool(args.src) == args.empty:
        raise SystemExit("give exactly one of --from and --empty")
    eid, cty = s1_country("test")
    target = set(eid[cty == args.country].tolist())
    if not target:
        raise SystemExit(f"no test S1 with country {args.country!r}")
    base = read_table("matches", args.base, "test")
    keep = ~base["s1"].isin(target)
    parts = [base[keep]]
    if args.src:
        new = read_table("matches", args.src, "test")
        parts.append(new[new["s1"].isin(target)])
    out = parts[0] if len(parts) == 1 else __import__("pandas").concat(parts, ignore_index=True)
    command = (f"python experiments/ameya/model-v1/probe.py --base {args.base} --country {args.country} "
               + (f"--from {args.src}" if args.src else "--empty") + f" --tag {args.tag}")
    write_table(out[["s1", "r"]].reset_index(drop=True), "matches", args.tag, "test", command=command,
                inputs={"base": args.base, **({"from": args.src} if args.src else {})}, country=args.country)
    log.info("%s: %d pairs (%d from the base outside %s, %d for %s)", args.tag, len(out), int(keep.sum()),
             args.country, len(out) - int(keep.sum()), args.country)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
