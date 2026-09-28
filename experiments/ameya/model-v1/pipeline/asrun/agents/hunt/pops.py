"""Edit-population scan on the holdout: predicted precision and unpredicted truth rate per (name kind, number relation,
empty record address) cell, for owned candidate pairs in the uncertain region (pc 0.1-0.999)."""
import os

import numpy as np
import pandas as pd

from base import D, pair_text_feats, text_for
from feats import build
from post_ops import NUDGE

pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 500)


def numrel(sp, rp):
    (ns, ss), (nr, sr) = sp, rp
    if not ns or not nr:
        return "no_num"
    from post_ops import _close_word
    street = bool(ss) and bool(sr) and any(_close_word(a, b) for a in ss for b in sr)
    d = int(nr[:9]) - int(ns[:9])
    if not street:
        return "same_num_other_street" if d == 0 else "other_street"
    if d == 0:
        return "same"
    if d in NUDGE:
        return "nudge+"
    if d in (-1, -2):
        return "minus"
    return "other_num"


def main():
    path = os.path.join(D, "pops.parquet")
    d = build()
    d = d[d.hold & d.own & (d.pc >= 0.1) & (d.pc < 0.999)].copy()
    if os.path.exists(path):
        x = pd.read_parquet(path)
    else:
        txt = text_for("train", np.r_[d.s1.to_numpy(), d.r.to_numpy()])
        x = pair_text_feats(d[["s1", "r"]], txt)
        sp = txt.parts.reindex(x.s1.to_numpy()).to_numpy()
        rp = txt.parts.reindex(x.r.to_numpy()).to_numpy()
        x["numrel"] = [numrel(a, b) if isinstance(a, tuple) and isinstance(b, tuple) else "no_num" for a, b in zip(sp, rp)]
        x[["s1", "r", "kind", "npos", "added", "dropped", "same_addr", "numrel"]].to_parquet(path, index=False)
    d = d.merge(x[["s1", "r", "kind", "numrel", "same_addr"]], on=["s1", "r"])
    d["numrel"] = np.where(d.r_empty, "r_empty", d.numrel)
    g = d.groupby(["kind", "numrel"])
    t = pd.DataFrame({
        "pred_n": g.pred.sum(),
        "pred_prec": g.apply(lambda z: z.y[z.pred].mean() if z.pred.any() else np.nan, include_groups=False),
        "pred_pc": g.apply(lambda z: z.pc[z.pred].mean() if z.pred.any() else np.nan, include_groups=False),
        "unp_n(pc>=.3)": g.apply(lambda z: int((~z.pred & (z.pc >= 0.3)).sum()), include_groups=False),
        "unp_rate": g.apply(lambda z: z.y[~z.pred & (z.pc >= 0.3)].mean(), include_groups=False),
        "unp_pc": g.apply(lambda z: z.pc[~z.pred & (z.pc >= 0.3)].mean(), include_groups=False),
    })
    print(t.round(3).to_string())
    # predicted pairs by band within each kind/numrel for the lowest-precision cells
    d["band"] = pd.cut(d.pc, [0.1, 0.3, 0.5, 0.6, 0.675, 0.75, 0.85, 0.95, 0.99, 0.999]).astype(str)
    t2 = d.groupby(["numrel", "band"]).agg(n=("y", "size"), pc=("pc", "mean"), y=("y", "mean"))
    print(t2.round(3).to_string())


if __name__ == "__main__":
    main()
