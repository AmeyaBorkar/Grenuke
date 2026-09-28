"""Runner-up check: contested/uncontested thresholds with a first-pair threshold (cont_first). Params chosen on the
full v7nst holdout, then applied unchanged to other models (vs each model's own threshold) next to the DP winner."""
from __future__ import annotations

import json
import os

import numpy as np

from ber.eval.gates import paired_bootstrap
from core import D, Hold, expected_f_select, to_q


def cont_first(H: Hold, tf, tu, tc, c0=0.02):
    t = np.where(H.riv >= c0, tc, tu)
    first = H.own & (H.own_rank == 0) & (H.p > tf)
    ok = np.zeros(H.U.size, bool)
    ok[H.idx[first]] = True
    return first | (H.own & (H.own_rank > 0) & (H.p > t) & ok[H.idx])


def main() -> int:
    H = Hold("ameya-s3-v7nst")
    fb = H.per_entity(H.own & (H.p > 0.675))
    best = None
    mA = H.masks["A"]
    for tf in (0.45, 0.5, 0.55, 0.6, 0.675):
        for tu in (0.5, 0.525, 0.55, 0.575, 0.6):
            for tc in (0.70, 0.71, 0.72, 0.73, 0.74, 0.75):
                f = H.per_entity(cont_first(H, tf, tu, tc))[mA].mean()
                if best is None or f > best[0]:
                    best = (f, tf, tu, tc)
    _, tf, tu, tc = best
    print(f"cont_first selected on v7nst half A: t_first={tf} t_u={tu} t_c={tc} (c0=0.02): A "
          f"{1e6 * (best[0] - fb[mA].mean()):+.1f}", flush=True)
    out = {"params_selected_on_A": {"t_first": tf, "t_u": tu, "t_c": tc, "c0": 0.02}}
    del H
    for tag, thr in (("ameya-s3-v7nst", 0.675), ("ameya-s3-v7nst2", 0.7), ("ameya-s3-v7mst", 0.7),
                     ("ameya-s3-v7ens2", 0.675), ("ameya-s3-v7s", 0.7)):
        H = Hold(tag)
        fb = H.per_entity(H.own & (H.p > thr))
        res = {}
        for name, sel in (("cont_first", cont_first(H, tf, tu, tc)),
                          ("dp_s0.20_lam0.01", expected_f_select(H.s1, to_q(H.p, 0.2), H.own, lam=0.01))):
            f = H.per_entity(sel)
            d = f - fb
            bs = paired_bootstrap(fb, f)
            res[name] = {k: round(1e6 * float(d[H.masks[k]].mean()), 1) for k in ("A", "B", "full", "US", "India")}
            res[name].update({"ci_low": round(1e6 * bs["ci_low"], 1), "ci_high": round(1e6 * bs["ci_high"], 1),
                              "p_better": bs["p_better"]})
            print(f"{tag} (base thr {thr}) {name:18s} {res[name]}", flush=True)
        out[tag] = res
        del H
    json.dump(out, open(os.path.join(D, "check_cont.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
