"""Select on half A, confirm on half B: per family, global and per-country selection. Deltas vs the baseline in 1e-6."""
from __future__ import annotations

import glob
import json
import os
import sys

import pandas as pd

from core import D

TAG = sys.argv[1] if len(sys.argv) > 1 else "ameya-s3-v7nst"


def load() -> tuple[pd.DataFrame, dict, dict]:
    r1 = json.load(open(os.path.join(D, f"res1_{TAG}.json")))
    rows = list(r1["rows"])
    bad = 0
    for fn in glob.glob(os.path.join(D, f"res2_{TAG}*.jsonl")) + glob.glob(os.path.join(D, f"res3_{TAG}*.jsonl")):
        for line in open(fn):
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                bad += 1
    if bad:
        print(f"[warn] {bad} unparsable lines", file=sys.stderr)
    u = pd.read_parquet(os.path.join(D, "universe.parquet"))
    n = {"A_US": ((u.half == 0) & (u.country == "US")).sum(), "A_India": ((u.half == 0) & (u.country == "India")).sum(),
         "B_US": ((u.half == 1) & (u.country == "US")).sum(), "B_India": ((u.half == 1) & (u.country == "India")).sum()}
    df = pd.DataFrame(rows)
    return df, r1["base"], n


def params_of(row: pd.Series) -> str:
    keys = [k for k in row.index if k not in ("fam", "A", "B", "full", "US", "India", "A_US", "A_India", "B_US",
                                               "B_India") and pd.notna(row[k])]
    return ", ".join(f"{k}={row[k]:g}" for k in keys)


def main() -> int:
    df, base, n = load()
    df = df.drop_duplicates(subset=[c for c in df.columns if c not in ("A", "B", "full", "US", "India", "A_US",
                                                                        "A_India", "B_US", "B_India")])
    nA, nB = n["A_US"] + n["A_India"], n["B_US"] + n["B_India"]
    out = []
    for fam, g in df.groupby("fam", sort=False):
        g = g.reset_index(drop=True)
        a = g.loc[g["A"].idxmax()]
        f = g.loc[g["full"].idxmax()]
        b = g.loc[g["B"].idxmax()]
        # per-country selection on A
        au = g.loc[g["A_US"].idxmax()]
        ai = g.loc[g["A_India"].idxmax()]
        Bc = (au["B_US"] * n["B_US"] + ai["B_India"] * n["B_India"]) / nB
        Ac = (au["A_US"] * n["A_US"] + ai["A_India"] * n["A_India"]) / nA
        Fc = (au["US"] * (n["A_US"] + n["B_US"]) + ai["India"] * (n["A_India"] + n["B_India"])) / (nA + nB)
        d = lambda v, k: 1e6 * (v - base[k])
        # cross-fit: select on A -> score B; select on B -> score A; combine (honest full-holdout estimate)
        xf = (d(a["B"], "B") * nB + d(b["A"], "A") * nA) / (nA + nB)
        out.append({"family": fam, "n_grid": len(g),
                    "sel_on_A": params_of(a), "A": d(a["A"], "A"), "B": d(a["B"], "B"), "full": d(a["full"], "full"),
                    "B_US": d(a["B_US"], "B_US"), "B_India": d(a["B_India"], "B_India"),
                    "percountry_on_A": f"US[{params_of(au)}] India[{params_of(ai)}]",
                    "pc_A": d(Ac, "A"), "pc_B": d(Bc, "B"), "pc_full": d(Fc, "full"),
                    "best_full": params_of(f), "bf_full": d(f["full"], "full"), "bf_A": d(f["A"], "A"),
                    "bf_B": d(f["B"], "B"), "best_B": params_of(b), "bB_B": d(b["B"], "B"), "bB_A": d(b["A"], "A"), "xfit": xf})
    res = pd.DataFrame(out)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_colwidth", 80)
    for _, r in res.iterrows():
        print(f"== {r['family']} (grid {r['n_grid']})")
        print(f"  selected on A: {r['sel_on_A']}:  A {r['A']:+.1f}  B {r['B']:+.1f}  full {r['full']:+.1f}  "
              f"(B_US {r['B_US']:+.1f}, B_India {r['B_India']:+.1f})")
        print(f"  per-country on A: {r['percountry_on_A']}:  A {r['pc_A']:+.1f}  B {r['pc_B']:+.1f}  full {r['pc_full']:+.1f}")
        print(f"  [ref] best on full: {r['best_full']}: full {r['bf_full']:+.1f} (A {r['bf_A']:+.1f}, B {r['bf_B']:+.1f});"
              f" best on B: {r['best_B']}: B {r['bB_B']:+.1f} -> A {r['bB_A']:+.1f};  CROSS-FIT full {r['xfit']:+.1f}")
    res.to_csv(os.path.join(D, f"select_{TAG}.csv"), index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
