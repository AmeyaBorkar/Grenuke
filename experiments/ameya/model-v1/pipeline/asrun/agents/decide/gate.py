"""Paired-bootstrap gates (ber.eval.gates.compare) of the finalists vs the current predictions (matches BASE, train
split) on the full holdout, half A and half B. Writes gate_<tag>.json."""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

from ber.artifacts import read_table
from ber.eval.gates import compare
from core import D, Hold, expected_f_select, greedy_perfect, to_q

TAG = sys.argv[1] if len(sys.argv) > 1 else "ameya-s3-v7nst"
BASE = sys.argv[2] if len(sys.argv) > 2 else "ameya-model-v7nst-s3"


def variants(H: Hold) -> dict:
    return {
        "dp_s0.20_lam0.01": expected_f_select(H.s1, to_q(H.p, 0.2), H.own, lam=0.01),
        "dp_s0.20": expected_f_select(H.s1, to_q(H.p, 0.2), H.own),
        "dp_s0.00": expected_f_select(H.s1, to_q(H.p, 0.0), H.own),
        "greedy_s0.20": greedy_perfect(to_q(H.p, 0.2), H.own, H.own_rank),
        "thr_0.675": H.own & (H.p > 0.675),
    }


def main() -> int:
    H = Hold(TAG)
    truth = pd.read_parquet(os.path.join(D, "truth_hold.parquet"))
    base = read_table("matches", BASE, "train", ["s1", "r"])
    base = base[np.isin(base["s1"].to_numpy(), H.U)]
    country = pd.Series(H.country, index=H.U)
    out = {"tag": TAG, "base": BASE}
    V = variants(H)
    for name, sel in V.items():
        pred = pd.DataFrame({"s1": H.s1[sel], "r": H.r[sel]})
        res = {}
        for part, m in (("full", H.masks["full"]), ("A", H.masks["A"]), ("B", H.masks["B"])):
            g = compare(base, pred, truth, H.U[m], groups=country)
            res[part] = {k: g[k] for k in ("delta", "ci_low", "ci_high", "p_better", "base_f05", "new_f05",
                                            "delta_by_group")}
        # pair-level change counts on the holdout
        key_b = base["s1"].to_numpy() * 4_000_000_000 + base["r"].to_numpy()
        key_n = pred["s1"].to_numpy() * 4_000_000_000 + pred["r"].to_numpy()
        added = ~np.isin(key_n, key_b)
        removed = ~np.isin(key_b, key_n)
        kh = set((truth["s1"].to_numpy() * 4_000_000_000 + truth["r"].to_numpy()).tolist())
        res["changes"] = {"added": int(added.sum()), "added_true": int(sum(k in kh for k in key_n[added])),
                          "removed": int(removed.sum()), "removed_true": int(sum(k in kh for k in key_b[removed])),
                          "s1_changed": int(np.unique(np.r_[pred["s1"].to_numpy()[added],
                                                              base["s1"].to_numpy()[removed]]).size)}
        out[name] = res
        f = res["full"]
        print(f"{name:18s} full {1e6 * f['delta']:+.1f} [{1e6 * f['ci_low']:+.1f}, {1e6 * f['ci_high']:+.1f}] "
              f"p={f['p_better']:.3f} | A {1e6 * res['A']['delta']:+.1f} [{1e6 * res['A']['ci_low']:+.1f}, "
              f"{1e6 * res['A']['ci_high']:+.1f}] | B {1e6 * res['B']['delta']:+.1f} [{1e6 * res['B']['ci_low']:+.1f}, "
              f"{1e6 * res['B']['ci_high']:+.1f}] p={res['B']['p_better']:.3f} | {res['changes']}", flush=True)
    # winner vs the simpler greedy rule
    pa = pd.DataFrame({"s1": H.s1[V["greedy_s0.20"]], "r": H.r[V["greedy_s0.20"]]})
    pb = pd.DataFrame({"s1": H.s1[V["dp_s0.20_lam0.01"]], "r": H.r[V["dp_s0.20_lam0.01"]]})
    g = compare(pa, pb, truth, H.U, groups=country)
    out["dp_lam_vs_greedy"] = {k: g[k] for k in ("delta", "ci_low", "ci_high", "p_better")}
    print("dp_lam vs greedy:", out["dp_lam_vs_greedy"])
    json.dump(out, open(os.path.join(D, f"gate_{TAG}.json"), "w"), indent=1, default=str)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
