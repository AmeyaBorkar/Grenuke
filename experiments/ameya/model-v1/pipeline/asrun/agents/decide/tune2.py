"""Families (d): rank-aware prefix thresholds, greedy break-even schedule, contested/uncontested thresholds,
DP with segment shifts (contested vs uncontested), DP with a phantom for blocking misses. Summary rows only.

Contested: the record's best rival S1 (other than this pair's S1) has p >= c0 (riv >= c0)."""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

from core import D, Hold, expected_f_select, greedy_perfect, rank_threshold, to_q

TAG = sys.argv[1] if len(sys.argv) > 1 else "ameya-s3-v7nst"
FAMS = sys.argv[2].split(",") if len(sys.argv) > 2 else ["rank", "greedy", "cont", "dpseg", "dplam"]


def main() -> int:
    t0 = time.perf_counter()
    H = Hold(TAG)
    rows = []
    path = os.path.join(D, f"res2_{TAG}_{'-'.join(FAMS)}.jsonl")
    fo = open(path, "a")

    def add(fam, params, sel):
        f = H.per_entity(sel)
        row = {"fam": fam, **params, **H.summary(f)}
        rows.append(row)
        fo.write(json.dumps(row) + "\n")

    n_u = H.U.size
    if "rank" in FAMS:
        for tf in np.round(np.arange(0.30, 0.801, 0.05), 3):
            for tr in np.round(np.arange(0.60, 0.8001, 0.01), 3):
                add("rank", {"t_first": float(tf), "t_rest": float(tr)},
                    rank_threshold(H.p, H.own, H.own_rank, H.idx, n_u, tf, tr))
        print(f"rank done {time.perf_counter() - t0:.0f}s", flush=True)
    if "greedy" in FAMS:
        for sh in np.round(np.arange(-1.0, 1.001, 0.1), 2):
            add("greedy", {"shift": float(sh)}, greedy_perfect(to_q(H.p, sh), H.own, H.own_rank))
        print(f"greedy done {time.perf_counter() - t0:.0f}s", flush=True)
    if "cont" in FAMS:
        for c0 in (0.001, 0.005, 0.01, 0.02, 0.05, 0.1):
            cont = H.riv >= c0
            for tu in np.round(np.arange(0.40, 0.8001, 0.025), 3):
                for tc in np.round(np.arange(0.60, 0.8501, 0.01), 3):
                    add("cont", {"c0": c0, "t_u": float(tu), "t_c": float(tc)},
                        H.own & (H.p > np.where(cont, tc, tu)))
            print(f"cont c0={c0} done {time.perf_counter() - t0:.0f}s", flush=True)
    if "dpseg" in FAMS:
        for c0 in (0.01,):
            cont = H.riv >= c0
            for sc in np.round(np.arange(-0.6, 0.401, 0.1), 2):
                for su in np.round(np.arange(-0.25, 1.501, 0.125), 3):
                    q = to_q(H.p, np.where(cont, sc, su))
                    add("dpseg", {"c0": c0, "s_c": float(sc), "s_u": float(su)}, expected_f_select(H.s1, q, H.own))
                print(f"dpseg s_c={sc} done {time.perf_counter() - t0:.0f}s", flush=True)
    if "dplam" in FAMS:
        for lam in (0.0, 0.002, 0.005, 0.01, 0.02, 0.05):
            for sh in (-0.2, 0.0, 0.2):
                add("dplam", {"lam": lam, "shift": sh}, expected_f_select(H.s1, to_q(H.p, sh), H.own, lam=lam))
        print(f"dplam done {time.perf_counter() - t0:.0f}s", flush=True)
    fo.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
