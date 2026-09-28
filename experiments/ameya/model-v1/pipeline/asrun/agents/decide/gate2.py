"""Gate of the winner rule (DP, shift 0.2, lam 0.01; parameters fixed from v7nst half A) against a model's current
holdout predictions (matches <base>, train split), with ber.eval.gates.compare on the full holdout, halves A/B and
per country. Alternatives get the same paired bootstrap on fast per-entity arrays (same math, full/A/B only).

    python gate2.py <scores tag> <base matches tag> <base threshold>
Writes gate2_<scores tag>.json.
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
import pandas as pd

from ber.artifacts import read_table
from ber.eval.gates import compare, paired_bootstrap
from core import D, Hold, expected_f_select, greedy_perfect, to_q

TAG, BASE, THR = sys.argv[1], sys.argv[2], float(sys.argv[3])


def main() -> int:
    t0 = time.perf_counter()
    H = Hold(TAG)
    truth = pd.read_parquet(os.path.join(D, "truth_hold.parquet"))
    base = read_table("matches", BASE, "train", ["s1", "r"])
    base = base[np.isin(base["s1"].to_numpy(), H.U)].reset_index(drop=True)
    key = H.s1 * 4_000_000_000 + H.r
    in_base = np.isin(key, base["s1"].to_numpy() * 4_000_000_000 + base["r"].to_numpy())
    rep = H.own & (H.p > THR)
    out = {"tag": TAG, "base": BASE, "base_thr": THR, "base_pairs": len(base),
           "base_pairs_found": int(in_base.sum()), "base_vs_rule_diff_pairs": int((rep != in_base).sum())}
    print(f"base {BASE}: {len(base):,} pairs, found {int(in_base.sum()):,}, differs from own & p > {THR} on "
          f"{out['base_vs_rule_diff_pairs']} pairs", flush=True)
    fb = H.per_entity(in_base)
    country = pd.Series(H.country, index=H.U)

    win = expected_f_select(H.s1, to_q(H.p, 0.2), H.own, lam=0.01)
    pred = pd.DataFrame({"s1": H.s1[win], "r": H.r[win]})
    res = {}
    for part in ("full", "A", "B", "US", "India", "A_US", "A_India", "B_US", "B_India"):
        g = compare(base, pred, truth, H.U[H.masks[part]], groups=country)
        res[part] = {k: g[k] for k in ("delta", "ci_low", "ci_high", "p_better", "base_f05", "new_f05", "n")}
        print(f"winner {part:8s} {1e6 * g['delta']:+7.1f} [{1e6 * g['ci_low']:+7.1f}, {1e6 * g['ci_high']:+7.1f}] "
              f"p_better {g['p_better']:.3f}  base {g['base_f05']:.6f} -> {g['new_f05']:.6f}  n {g['n']:,} "
              f"({time.perf_counter() - t0:.0f}s)", flush=True)
    k_b = base["s1"].to_numpy() * 4_000_000_000 + base["r"].to_numpy()
    k_n = pred["s1"].to_numpy() * 4_000_000_000 + pred["r"].to_numpy()
    kt = truth["s1"].to_numpy() * 4_000_000_000 + truth["r"].to_numpy()
    add, rem = ~np.isin(k_n, k_b), ~np.isin(k_b, k_n)
    res["changes"] = {"added": int(add.sum()), "added_true": int(np.isin(k_n[add], kt).sum()),
                      "removed": int(rem.sum()), "removed_true": int(np.isin(k_b[rem], kt).sum()),
                      "s1_changed": int(np.unique(np.r_[pred["s1"].to_numpy()[add], base["s1"].to_numpy()[rem]]).size)}
    print("winner changes on the holdout:", res["changes"], flush=True)
    out["winner_dp_s0.20_lam0.01"] = res

    alts = {"dp_s0.20": expected_f_select(H.s1, to_q(H.p, 0.2), H.own),
            "dp_s0.00": expected_f_select(H.s1, to_q(H.p, 0.0), H.own),
            "greedy_s0.20": greedy_perfect(to_q(H.p, 0.2), H.own, H.own_rank)}
    for name, sel in alts.items():
        f = H.per_entity(sel)
        r = {}
        for part in ("full", "A", "B"):
            m = H.masks[part]
            bs = paired_bootstrap(fb[m], f[m])
            r[part] = {k: bs[k] for k in ("delta", "ci_low", "ci_high", "p_better")}
        r["by_country_full"] = {c: float((f - fb)[H.masks[c]].mean()) for c in ("US", "India")}
        out[name] = r
        print(f"{name:12s} " + "  ".join(f"{p} {1e6 * r[p]['delta']:+.1f} [{1e6 * r[p]['ci_low']:+.1f}, "
                                         f"{1e6 * r[p]['ci_high']:+.1f}]" for p in ("full", "A", "B")) +
              f"  US {1e6 * r['by_country_full']['US']:+.1f} India {1e6 * r['by_country_full']['India']:+.1f}", flush=True)
    json.dump(out, open(os.path.join(D, f"gate2_{TAG}.json"), "w"), indent=1, default=str)
    print(f"done {time.perf_counter() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
