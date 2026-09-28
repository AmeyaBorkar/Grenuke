"""Repeated 2-fold cross-validation of each rule family over 20 random S1 halvings (salted splitmix64):
select the family's parameters on one half, score the other half, both directions. Reports the mean out-of-sample
gain vs the current predictions (x1e-6) and how often it is > 0. Also the fixed winner rule's gain per halving."""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

from ber.eval.splits import splitmix64
from core import D, Hold, expected_f_select, greedy_perfect, rank_threshold, to_q

TAG = sys.argv[1] if len(sys.argv) > 1 else "ameya-s3-v7nst"
N_SALT = 20


def main() -> int:
    t0 = time.perf_counter()
    H = Hold(TAG)
    fb = H.per_entity(H.own & (H.p > 0.675))
    rng = np.random.default_rng(12345)
    salts = rng.integers(1, 2**62, N_SALT)
    halves = np.stack([(splitmix64(H.U.astype(np.int64) ^ np.int64(s)) % np.uint64(2)).astype(bool) for s in salts])
    n1 = halves.sum(1)
    n0 = H.U.size - n1
    fams: dict[str, list] = {}

    def add(fam, params, sel):
        d = H.per_entity(sel) - fb
        s1 = halves @ d  # sum over half 1 per salt
        tot = d.sum()
        fams.setdefault(fam, []).append((params, (tot - s1) / n0, s1 / n1))

    for t in np.round(np.arange(0.60, 0.8501, 0.005), 3):
        add("thr", {"t": float(t)}, H.own & (H.p > t))
    for sh in np.round(np.arange(-0.5, 0.5001, 0.05), 2):
        q = to_q(H.p, sh)
        add("dp", {"shift": float(sh)}, expected_f_select(H.s1, q, H.own))
        add("greedy", {"shift": float(sh)}, greedy_perfect(q, H.own, H.own_rank))
        for lam in (0.005, 0.01, 0.02):
            add("dplam", {"shift": float(sh), "lam": lam}, expected_f_select(H.s1, q, H.own, lam=lam))
    fams["dplam"] = fams["dplam"] + [(dict(p, lam=0.0), a, b) for p, a, b in fams["dp"]]
    print(f"dp families done {time.perf_counter() - t0:.0f}s", flush=True)
    for tf in np.round(np.arange(0.30, 0.801, 0.05), 3):
        for tr in np.round(np.arange(0.60, 0.8001, 0.01), 3):
            add("rank", {"t_first": float(tf), "t_rest": float(tr)},
                rank_threshold(H.p, H.own, H.own_rank, H.idx, H.U.size, tf, tr))
    for c0 in (0.01, 0.02, 0.05):
        cont = H.riv >= c0
        for tu in np.round(np.arange(0.45, 0.7501, 0.025), 3):
            for tc in np.round(np.arange(0.62, 0.8001, 0.01), 3):
                add("cont", {"c0": c0, "t_u": float(tu), "t_c": float(tc)}, H.own & (H.p > np.where(cont, tc, tu)))
    print(f"grids done {time.perf_counter() - t0:.0f}s", flush=True)
    for sc in np.round(np.arange(-0.4, 0.401, 0.2), 2):
        for su in np.round(np.arange(-0.2, 1.001, 0.2), 2):
            q = to_q(H.p, np.where(H.riv >= 0.01, sc, su))
            add("dpseg", {"s_c": float(sc), "s_u": float(su)}, expected_f_select(H.s1, q, H.own))
    print(f"dpseg done {time.perf_counter() - t0:.0f}s", flush=True)

    out = {}
    for fam, rows in fams.items():
        g0 = np.stack([r[1] for r in rows])  # [variant, salt] mean gain on half 0
        g1 = np.stack([r[2] for r in rows])
        oos = []
        picks = []
        for s in range(N_SALT):
            i = int(np.argmax(g0[:, s]))
            oos.append(g1[i, s]); picks.append(rows[i][0])
            j = int(np.argmax(g1[:, s]))
            oos.append(g0[j, s]); picks.append(rows[j][0])
        oos = 1e6 * np.array(oos)
        insample = 1e6 * np.array([max(g0[:, s].max(), 0) for s in range(N_SALT)])
        out[fam] = {"n_grid": len(rows), "oos_mean": round(float(oos.mean()), 1), "oos_sd": round(float(oos.std()), 1),
                    "oos_pos_share": round(float((oos > 0).mean()), 2), "in_sample_mean": round(float(insample.mean()), 1),
                    "picks": [json.dumps(p) for p in picks[:6]]}
        print(f"{fam:8s} grid {len(rows):5d}  out-of-sample mean {oos.mean():+6.1f} (sd {oos.std():5.1f}, >0 in "
              f"{(oos > 0).mean():.0%})  in-sample best {insample.mean():+6.1f}  picks {picks[:4]}", flush=True)
    # fixed winner per halving
    fw = H.per_entity(expected_f_select(H.s1, to_q(H.p, 0.2), H.own, lam=0.01)) - fb
    w1 = 1e6 * (halves @ fw) / n1
    w0 = 1e6 * (fw.sum() - halves @ fw) / n0
    ww = np.r_[w0, w1]
    out["fixed_winner_dp_s0.2_lam0.01"] = {"mean": round(float(ww.mean()), 1), "min": round(float(ww.min()), 1),
                                           "max": round(float(ww.max()), 1), "pos_share": round(float((ww > 0).mean()), 2)}
    print("fixed winner per half:", out["fixed_winner_dp_s0.2_lam0.01"])
    json.dump(out, open(os.path.join(D, f"cv_{TAG}.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
