"""Final ranking under the combo rule, reusing rank.json's paired CIs vs the reference (computed for the first 7 models)
and bootstrapping only what is new: models missing from rank.json vs the reference (full, US, India, A, B), and direct
paired comparisons among the top 3 by full F0.5 (full, US, India). ber.eval.gates.paired_bootstrap, 1000, seed 0.
Writes rank2.json and prints a markdown table."""
from __future__ import annotations

import glob
import json
import os
import sys

import numpy as np
import pandas as pd

from ber.eval.gates import paired_bootstrap

D = os.path.dirname(os.path.abspath(__file__))
REF = "v7sq"


def main() -> int:
    u = pd.read_parquet(os.path.join(D, "universe.parquet"))
    parts = {"full": np.ones(len(u), bool), "US": (u.country == "US").to_numpy(), "India": (u.country == "India").to_numpy(),
             "A": (u.half == 0).to_numpy(), "B": (u.half == 1).to_numpy()}
    models = sorted(os.path.basename(f)[5:-4] for f in glob.glob(os.path.join(D, "rule_*.npz")))
    F = {m: np.load(os.path.join(D, f"rule_{m}.npz"))["f_combo"] for m in models}
    FT = {m: np.load(os.path.join(D, f"rule_{m}.npz"))["f_thr"] for m in models}
    meta = {m: json.load(open(os.path.join(D, f"rule_{m}.json"))) for m in models}
    old = json.load(open(os.path.join(D, "rank.json")))
    old = {x["model"]: x for x in (old["rows"] if isinstance(old, dict) else old)}
    rows = []
    for m in models:
        row = {"model": m, "thr": meta[m]["thr"], "rebuild_ok": meta[m]["thr_rebuild_matches_stored"]}
        for k, sel in parts.items():
            row[k] = float(F[m][sel].mean())
        row["thr_full"] = float(FT[m].mean())
        row["gain_vs_own_thr"] = 1e6 * float((F[m] - FT[m]).mean())
        for k, sel in parts.items():
            if m == REF:
                row[f"d_{k}"] = [0.0, 0.0, 0.0, 0.0]
            elif m in old and f"d_{k}" in old[m]:
                row[f"d_{k}"] = old[m][f"d_{k}"]
            else:
                b = paired_bootstrap(F[REF][sel], F[m][sel])
                row[f"d_{k}"] = [1e6 * b["delta"], 1e6 * b["ci_low"], 1e6 * b["ci_high"], b["p_better"]]
                print(f"{m} vs {REF} {k}: {row[f'd_{k}'][0]:+.1f} [{row[f'd_{k}'][1]:+.1f}, {row[f'd_{k}'][2]:+.1f}]",
                      flush=True)
        rows.append(row)
    rows.sort(key=lambda x: -x["full"])
    print(f"| rank | model (thr) | combo full | US | India | A | B | vs {REF} full [95% CI] (P better) | US [CI] | "
          f"India [CI] | A | B | own-thr full | combo vs own thr |")
    print("|---" * 14 + "|")
    for i, x in enumerate(rows, 1):
        d = x
        print(f"| {i} | {x['model']} ({x['thr']}) | {x['full']:.6f} | {x['US']:.6f} | {x['India']:.6f} | {x['A']:.6f} | "
              f"{x['B']:.6f} | {d['d_full'][0]:+.1f} [{d['d_full'][1]:+.1f}, {d['d_full'][2]:+.1f}] ({d['d_full'][3]:.3f}) | "
              f"{d['d_US'][0]:+.1f} [{d['d_US'][1]:+.1f}, {d['d_US'][2]:+.1f}] | {d['d_India'][0]:+.1f} "
              f"[{d['d_India'][1]:+.1f}, {d['d_India'][2]:+.1f}] | {d['d_A'][0]:+.1f} | {d['d_B'][0]:+.1f} | "
              f"{x['thr_full']:.6f} | {x['gain_vs_own_thr']:+.1f} |", flush=True)
    top = [x["model"] for x in rows[:3]]
    pairs = {}
    for i in range(len(top)):
        for j in range(i + 1, len(top)):
            a, b_ = top[i], top[j]
            for k in ("full", "US", "India"):
                bs = paired_bootstrap(F[b_][parts[k]], F[a][parts[k]])
                pairs[f"{a}-{b_}|{k}"] = [1e6 * bs["delta"], 1e6 * bs["ci_low"], 1e6 * bs["ci_high"], bs["p_better"]]
                print(f"{a} - {b_} {k:5s}: {1e6 * bs['delta']:+.1f} [{1e6 * bs['ci_low']:+.1f}, {1e6 * bs['ci_high']:+.1f}]"
                      f" (P {a} better {bs['p_better']:.3f})", flush=True)
    best_us = max(rows, key=lambda x: x["US"])["model"]
    best_in = max(rows, key=lambda x: x["India"])["model"]
    print(f"best full: {rows[0]['model']}; best US: {best_us}; best India: {best_in}")
    json.dump({"rows": rows, "top_pairs": pairs}, open(os.path.join(D, "rank2.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
