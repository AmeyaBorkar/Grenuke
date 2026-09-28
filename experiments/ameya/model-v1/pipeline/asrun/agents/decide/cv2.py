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
    halves = np.stack([H.half == 1] + [(splitmix64(H.U.astype(np.int64) ^ np.int64(s)) % np.uint64(2)).astype(bool)
                                        for s in salts])
    n1 = halves.sum(1)
    n0 = H.U.size - n1
    fams: dict[str, list] = {}

    def add(fam, params, sel):
        d = H.per_entity(sel) - fb
        s1 = halves @ d  # sum over half 1 per salt
        tot = d.sum()
        fams.setdefault(fam, []).append((params, (tot - s1) / n0, s1 / n1))

    # original A/B split as an extra halving (index 0 in the report)
    halves_orig = (H.half == 1)
    cont01 = H.riv >= 0.01
    cont02 = H.riv >= 0.02
    for sh in (0.1, 0.2, 0.3):
        q = to_q(H.p, sh)
        add("greedy", {"shift": sh}, greedy_perfect(q, H.own, H.own_rank))
        add("dplam", {"shift": sh, "lam": 0.01}, expected_f_select(H.s1, q, H.own, lam=0.01))
    for c0, cm in ((0.01, cont01), (0.02, cont02)):
        for tu in (0.5, 0.525, 0.55, 0.575, 0.6):
            for tc in (0.70, 0.71, 0.72, 0.73, 0.74, 0.75):
                add("cont_small", {"c0": c0, "t_u": tu, "t_c": tc}, H.own & (H.p > np.where(cm, tc, tu)))
    for sc in (0.0, 0.1, 0.2, 0.3):
        for su in (0.2, 0.4, 0.6, 0.8, 1.0):
            q = to_q(H.p, np.where(cont01, sc, su))
            add("greedy_seg", {"s_c": sc, "s_u": su}, greedy_perfect(q, H.own, H.own_rank))
    print(f"greedy_seg done {time.perf_counter() - t0:.0f}s", flush=True)
    for sc in (0.1, 0.2, 0.3):
        for su in (0.3, 0.5, 0.7, 0.9):
            q = to_q(H.p, np.where(cont01, sc, su))
            add("dplam_seg", {"s_c": sc, "s_u": su, "lam": 0.01}, expected_f_select(H.s1, q, H.own, lam=0.01))
    print(f"dplam_seg done {time.perf_counter() - t0:.0f}s", flush=True)
    for tf in (0.45, 0.5, 0.55, 0.6, 0.675):
        for tu in (0.525, 0.55, 0.575):
            for tc in (0.71, 0.72, 0.73, 0.74):
                t = np.where(cont02, tc, tu)
                first = H.own & (H.own_rank == 0) & (H.p > tf)
                ok = np.zeros(H.U.size, bool)
                ok[H.idx[first]] = True
                add("cont_first", {"t_first": tf, "t_u": tu, "t_c": tc, "c0": 0.02},
                    first | (H.own & (H.own_rank > 0) & (H.p > t) & ok[H.idx]))
    print(f"cont_first done {time.perf_counter() - t0:.0f}s", flush=True)

    out = {}
    for fam, rows in fams.items():
        g0 = np.stack([r[1] for r in rows])  # [variant, salt] mean gain on half 0
        g1 = np.stack([r[2] for r in rows])
        oos = []
        picks = []
        for s in range(N_SALT + 1):
            i = int(np.argmax(g0[:, s]))
            oos.append(g1[i, s]); picks.append(rows[i][0])
            j = int(np.argmax(g1[:, s]))
            oos.append(g0[j, s]); picks.append(rows[j][0])
        oos = 1e6 * np.array(oos)
        insample = 1e6 * np.array([max(g0[:, s].max(), 0) for s in range(N_SALT + 1)])
        orig = oos[:2]  # the prescribed A/B split: [select A -> score B, select B -> score A]
        out[fam] = {"n_grid": len(rows), "oos_mean": round(float(oos.mean()), 1), "oos_sd": round(float(oos.std()), 1),
                    "oos_pos_share": round(float((oos > 0).mean()), 2),
                    "orig_split_AtoB_BtoA": [round(float(x), 1) for x in orig], "in_sample_mean": round(float(insample.mean()), 1),
                    "picks": [json.dumps(p) for p in picks[:6]], "oos": [round(float(x), 2) for x in oos]}
        print(f"{fam:8s} grid {len(rows):5d}  out-of-sample mean {oos.mean():+6.1f} (sd {oos.std():5.1f}, >0 in "
              f"{(oos > 0).mean():.0%}) orig A->B {orig[0]:+.1f} B->A {orig[1]:+.1f}  in-sample best {insample.mean():+6.1f}  picks {picks[:4]}", flush=True)
    # fixed winner per halving
    fw = H.per_entity(expected_f_select(H.s1, to_q(H.p, 0.2), H.own, lam=0.01)) - fb
    w1 = 1e6 * (halves @ fw) / n1
    w0 = 1e6 * (fw.sum() - halves @ fw) / n0
    ww = np.r_[w0, w1]
    out["fixed_winner_dp_s0.2_lam0.01"] = {"mean": round(float(ww.mean()), 1), "min": round(float(ww.min()), 1),
                                           "max": round(float(ww.max()), 1), "pos_share": round(float((ww > 0).mean()), 2)}
    print("fixed winner per half:", out["fixed_winner_dp_s0.2_lam0.01"])
    json.dump(out, open(os.path.join(D, f"cv2_{TAG}.json"), "w"), indent=1)
    fam_list = [f for f in out if "oos" in out[f]]
    for a in fam_list:
        for b in fam_list:
            if a < b:
                d = np.array(out[a]["oos"]) - np.array(out[b]["oos"])
                print(f"paired {a} - {b}: mean {d.mean():+.1f}, {a} better in {(d > 0).mean():.0%} of {d.size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
