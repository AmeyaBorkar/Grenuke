"""Check apply_hunt.apply_rules against the holdout: same deltas as rules.py / gates.py (holdout cache, train split)."""
import numpy as np
import pandas as pd

from apply_hunt import apply_rules
from base import Eval, universe_and_truth
from ber.eval.metric import per_entity_f05
from ber.eval.splits import splitmix64


def main():
    import sys
    import apply_hunt
    if len(sys.argv) > 1:  # the model's threshold, if not 0.675
        apply_hunt.THR = float(sys.argv[1])
    from feats import build
    d = build()
    uni, cty, th = universe_and_truth()
    s = d.loc[d.cand, ["s1", "r", "pc", "own", "n_s1_all"]].reset_index(drop=True)
    m = d.loc[d.pred, ["s1", "r"]].reset_index(drop=True)
    import pyarrow.parquet as pq, pyarrow.compute as pc
    from ber.paths import records_path
    t = pq.read_table(records_path("train"), columns=["eid", "source", "country"])
    t = t.filter(pc.equal(t["source"], 1))
    cty_all = pd.Series(t["country"].to_numpy(zero_copy_only=False), index=t["eid"].to_numpy())
    fa = per_entity_f05(m, th, uni)["f05"].to_numpy()
    half = (splitmix64(uni) % np.uint64(2)).astype(int)
    for rules in (["cap"], ["nsa"], ["rank0"], ["acr"], ["cap", "nsa", "rank0", "acr"]):
        out, ch = apply_rules(s, m, cty_all, rules, "", None, "train")
        fb = per_entity_f05(out, th, uni)["f05"].to_numpy()
        dd = fb - fa
        hch = ch[np.isin(ch.s1.to_numpy(), uni)]
        print(f"{'+'.join(rules):22s} holdout changes {hch.groupby('action').size().to_dict()}  full {dd.mean():+.7f}"
              f"  A {dd[half == 0].mean():+.7f}  B {dd[half == 1].mean():+.7f}", flush=True)


if __name__ == "__main__":
    main()
