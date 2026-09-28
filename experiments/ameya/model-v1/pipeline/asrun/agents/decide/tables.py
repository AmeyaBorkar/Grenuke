"""Markdown tables for REPORT.md from the result files (deltas vs the current predictions, x1e-6)."""
from __future__ import annotations

import os
import sys

import pandas as pd

from analyze import load
from core import D

TAG = sys.argv[1] if len(sys.argv) > 1 else "ameya-s3-v7nst"
KEYS = ["A", "B", "full", "A_US", "A_India", "B_US", "B_India"]


def main() -> int:
    df, base, n = load()
    meta = [c for c in df.columns if c not in KEYS + ["US", "India", "fam"]]
    df = df.drop_duplicates(subset=["fam"] + meta)
    for k in KEYS:
        df[k] = 1e6 * (df[k] - base[k])
    lines = []

    def fmt(g: pd.DataFrame, cols) -> str:
        head = "| " + " | ".join(cols + KEYS) + " |\n|" + "---|" * (len(cols) + len(KEYS)) + "\n"
        body = "".join("| " + " | ".join([f"{r[c]:g}" for c in cols] + [f"{r[k]:+.1f}" for k in KEYS]) + " |\n"
                       for _, r in g.iterrows())
        return head + body

    for fam, cols in (("thr", ["t"]), ("dp", ["shift"]), ("greedy", ["shift"]), ("dplam2", ["shift", "lam"]),
                      ("greedy_t1", ["shift", "t1"]), ("iso_dp", ["c0", "p_lo", "shift"]),
                      ("iso_greedy", ["c0", "p_lo", "shift"])):
        g = df[df["fam"] == fam]
        if fam in ("iso_dp", "iso_greedy"):
            g = g[g["p_lo"] == 0.0]
        lines.append(f"\n#### {fam} (full grid, {len(g)} points)\n\n" + fmt(g, cols))
    for fam, cols in (("rank", ["t_first", "t_rest"]), ("cont", ["c0", "t_u", "t_c"]), ("dpseg", ["c0", "s_c", "s_u"])):
        g = df[df["fam"] == fam].sort_values("A", ascending=False).head(8)
        lines.append(f"\n#### {fam} (top 8 of {int((df['fam'] == fam).sum())} by A)\n\n" + fmt(g, cols))
    open(os.path.join(D, f"tables_{TAG}.md"), "w").write("".join(lines))
    print("".join(lines)[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
