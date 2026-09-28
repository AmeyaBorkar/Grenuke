"""Context calibration near the threshold: truth rate vs mean pc of owned holdout candidate pairs."""
import numpy as np
import pandas as pd

from feats import build

pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 500)


def main():
    d = build()
    d = d[d.hold & d.own & (d.pc >= 0.3) & (d.pc < 0.99)].copy()
    d["band"] = pd.cut(d.pc, [0.3, 0.5, 0.6, 0.675, 0.75, 0.85, 0.95, 0.99], right=False).astype(str)
    pr = d.pred.to_numpy().astype(int)
    d["k_other"] = d.np_all - pr  # S1's other predictions
    d["k_src_other"] = np.where(d.src == 2, d.np_2, d.np_3) - pr
    d["k_osrc"] = np.where(d.src == 2, d.np_3, d.np_2)
    d["kcat"] = pd.cut(d.k_other, [-1, 0, 1, 2, 3, 4, 5, 99]).astype(str)
    d["zero_src"] = np.where(d.k_src_other == 0, np.where(d.k_osrc > 0, "src0_other>0", "src0_other0"), "src>0")
    d["rk"] = d.rank_s1_own.clip(upper=4)
    d["nsa"] = d.n_s1_all.clip(upper=4)
    d["mass"] = pd.cut(d.psum_c, [0, 0.9, 1.0, 1.05, 1.2, 9]).astype(str)
    d["srccap"] = np.where((d.src == 2) & (d.k_src_other >= 5) | (d.src == 3) & (d.k_src_other >= 6), "at_cap", "")
    for ctx in (["kcat"], ["rk"], ["zero_src", "src"], ["r_empty", "nsa"], ["mass"], ["srccap"], ["s1_empty"]):
        t = d.groupby(ctx + ["band"]).agg(n=("y", "size"), pc=("pc", "mean"), y=("y", "mean"))
        t["gap"] = t.y - t.pc
        print(f"\n== {ctx}\n", t.round(3).to_string())


if __name__ == "__main__":
    main()
