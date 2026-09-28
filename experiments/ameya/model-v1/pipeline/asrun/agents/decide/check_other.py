"""Transfer check: the fixed winner rule (DP, shift 0.2, lam 0.01; params chosen on v7nst) on another model's stage-3
scores, vs that model's own threshold rule. Needs hold_<tag>.parquet (prep.py <tag>).

    python check_other.py <scores tag> <baseline threshold>
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

from ber.eval.gates import paired_bootstrap
from core import D, Hold, expected_f_select, greedy_perfect, to_q


def main() -> int:
    tag, thr = sys.argv[1], float(sys.argv[2])
    H = Hold(tag)
    fb = H.per_entity(H.own & (H.p > thr))
    out = {"tag": tag, "base_thr": thr, "base": H.summary(fb)}
    V = {
        "dp_s0.20_lam0.01": expected_f_select(H.s1, to_q(H.p, 0.2), H.own, lam=0.01),
        "dp_s0.20": expected_f_select(H.s1, to_q(H.p, 0.2), H.own),
        "greedy_s0.20": greedy_perfect(to_q(H.p, 0.2), H.own, H.own_rank),
    }
    for t in np.round(np.arange(0.60, 0.8001, 0.025), 3):
        V[f"thr_{t:.3f}"] = H.own & (H.p > t)
    for name, sel in V.items():
        f = H.per_entity(sel)
        s = H.summary(f)
        row = {k: round(1e6 * (s[k] - out["base"][k]), 1) for k in ("A", "B", "full", "US", "India")}
        if not name.startswith("thr"):
            bs = paired_bootstrap(fb, f)
            row.update({"ci_low": round(1e6 * bs["ci_low"], 1), "ci_high": round(1e6 * bs["ci_high"], 1),
                        "p_better": bs["p_better"]})
        out[name] = row
        print(f"{tag} {name:18s} {row}", flush=True)
    json.dump(out, open(os.path.join(D, f"check_{tag}.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
