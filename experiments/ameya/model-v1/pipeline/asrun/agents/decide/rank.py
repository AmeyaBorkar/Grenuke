"""Rank the models by holdout F0.5 under the combo rule (rule_<model>.npz from rule_eval.py): full, US, India, A, B, and
the paired delta vs the reference model under the same rule (ber.eval.gates.paired_bootstrap, 1000 resamples, seed 0).

    python rank.py [reference=v7sq]
Writes rank.json and prints a markdown table.
"""
from __future__ import annotations

import glob
import json
import os
import sys

import numpy as np
import pandas as pd

from ber.eval.gates import paired_bootstrap

D = os.path.dirname(os.path.abspath(__file__))
REF = sys.argv[1] if len(sys.argv) > 1 else "v7sq"


def main() -> int:
    u = pd.read_parquet(os.path.join(D, "universe.parquet"))
    parts = {"full": np.ones(len(u), bool), "US": (u.country == "US").to_numpy(), "India": (u.country == "India").to_numpy(),
             "A": (u.half == 0).to_numpy(), "B": (u.half == 1).to_numpy()}
    models = sorted(os.path.basename(f)[5:-4] for f in glob.glob(os.path.join(D, "rule_*.npz")))
    F = {m: np.load(os.path.join(D, f"rule_{m}.npz")) for m in models}
    meta = {m: json.load(open(os.path.join(D, f"rule_{m}.json"))) for m in models}
    ref = F[REF]["f_combo"]
    rows = []
    for m in models:
        f, ft = F[m]["f_combo"], F[m]["f_thr"]
        row = {"model": m, "thr": meta[m]["thr"], "rebuild_ok": meta[m]["thr_rebuild_matches_stored"]}
        for k, sel in parts.items():
            row[k] = float(f[sel].mean())
        row["thr_full"] = float(ft.mean())
        row["gain_vs_own_thr"] = 1e6 * float((f - ft).mean())
        for k, sel in parts.items():
            if m == REF:
                row[f"d_{k}"] = (0.0, 0.0, 0.0, 0.0)
            else:
                b = paired_bootstrap(ref[sel], f[sel])
                row[f"d_{k}"] = (1e6 * b["delta"], 1e6 * b["ci_low"], 1e6 * b["ci_high"], b["p_better"])
        rows.append(row)
    rows.sort(key=lambda x: -x["full"])
    print(f"| rank | model | combo full | US | India | A | B | vs {REF} full [95% CI] (P better) | US | India | A | B |"
          f" own thr: full | combo gain vs own thr |")
    print("|---" * 14 + "|")
    for i, x in enumerate(rows, 1):
        d = lambda k: f"{x[f'd_{k}'][0]:+.1f}"
        print(f"| {i} | {x['model']} | {x['full']:.6f} | {x['US']:.6f} | {x['India']:.6f} | {x['A']:.6f} | {x['B']:.6f} | "
              f"{x['d_full'][0]:+.1f} [{x['d_full'][1]:+.1f}, {x['d_full'][2]:+.1f}] ({x['d_full'][3]:.3f}) | "
              f"{d('US')} [{x['d_US'][1]:+.1f}, {x['d_US'][2]:+.1f}] | {d('India')} [{x['d_India'][1]:+.1f}, "
              f"{x['d_India'][2]:+.1f}] | {d('A')} | {d('B')} | {x['thr_full']:.6f} (t {x['thr']}) | "
              f"{x['gain_vs_own_thr']:+.1f} |")
    # direct paired comparisons among the top 3 (by full)
    top = [x["model"] for x in rows[:3]]
    pairs = {}
    for i in range(len(top)):
        for j in range(i + 1, len(top)):
            a, b_ = top[i], top[j]
            for k in ("full", "US", "India", "A", "B"):
                bs = paired_bootstrap(F[b_]["f_combo"][parts[k]], F[a]["f_combo"][parts[k]])
                pairs[f"{a}-{b_}|{k}"] = (1e6 * bs["delta"], 1e6 * bs["ci_low"], 1e6 * bs["ci_high"], bs["p_better"])
                print(f"{a} - {b_} {k:5s}: {1e6 * bs['delta']:+.1f} [{1e6 * bs['ci_low']:+.1f}, {1e6 * bs['ci_high']:+.1f}]"
                      f" (P {a} better {bs['p_better']:.3f})", flush=True)
    best_us = max(rows, key=lambda x: x["US"])["model"]
    best_in = max(rows, key=lambda x: x["India"])["model"]
    print(f"best full: {rows[0]['model']}; best US: {best_us}; best India: {best_in}")
    json.dump({"rows": rows, "top_pairs": pairs}, open(os.path.join(D, "rank.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
