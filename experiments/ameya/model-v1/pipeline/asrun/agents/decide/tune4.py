"""(d/e) finer grids around the robust families: DP shift x phantom lam; greedy break-even schedule with a separate
first-pair q-threshold; greedy with lam-adjusted schedule."""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

from core import D, Hold, expected_f_select, greedy_perfect, to_q

TAG = sys.argv[1] if len(sys.argv) > 1 else "ameya-s3-v7nst"


def greedy_first(q, own, own_rank, idx, n_u, t1):
    """Break-even schedule for ranks >= 2 (0.727, 0.759, ...); the first owned pair needs q > t1 (prefix rule)."""
    k = np.maximum(own_rank, 0).astype(np.float64)
    t = np.where(own_rank == 0, t1, (5 * k + 1) / (6.25 * k + 2))
    ok_first = own & (own_rank == 0) & (q > t)
    ok = np.zeros(n_u, bool)
    ok[idx[ok_first]] = True
    return ok_first | (own & (own_rank > 0) & (q > t) & ok[idx])


def main() -> int:
    t0 = time.perf_counter()
    H = Hold(TAG)
    fo = open(os.path.join(D, f"res2_{TAG}_fine.jsonl"), "w")

    def add(fam, params, sel):
        f = H.per_entity(sel)
        row = {"fam": fam, **params, **H.summary(f)}
        fo.write(json.dumps(row) + "\n")
        fo.flush()

    for sh in np.round(np.arange(0.0, 0.401, 0.05), 2):
        q = to_q(H.p, sh)
        for lam in (0.0, 0.005, 0.01, 0.015, 0.02, 0.03):
            add("dplam2", {"shift": float(sh), "lam": lam}, expected_f_select(H.s1, q, H.own, lam=lam))
        for t1 in (0.35, 0.40, 0.45, 0.50, 0.55, 0.60):
            add("greedy_t1", {"shift": float(sh), "t1": t1}, greedy_first(q, H.own, H.own_rank, H.idx, H.U.size, t1))
        print(f"shift {sh} done {time.perf_counter() - t0:.0f}s", flush=True)
    fo.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
