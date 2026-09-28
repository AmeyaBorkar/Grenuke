"""Paired-bootstrap gates (ber.eval.gates.compare) on the full holdout and halves A/B for selected rules."""
import json
import os
import time

import numpy as np
import pandas as pd

from base import D, fmt_gate, gate, universe_and_truth
from feats import build
from rules import r_cap, r_mass, r_nsa, r_pop, r_rank, r_singleton, r_src_zero


def combo(d, base, pops):
    m = r_cap(d, base)
    m = m & r_nsa(d, base, 0.675, 0.75) | (m & ~base)  # drop part of nsa
    m = m | (r_rank(d, base, 0.6, 0.675) & ~base)
    m = r_pop(d, m, pops, ["acr"], ["same", "same_num_other_street", "other_street", "no_num", "other_num", "nudge+",
                                    "minus"], 0.1)
    return m


def main():
    t0 = time.time()
    d = build()
    uni, cty, th = universe_and_truth()
    base = d.pred.to_numpy()
    pops = pd.read_parquet(os.path.join(D, "pops.parquet"))
    acr_nr = ["same", "same_num_other_street", "other_street", "no_num", "other_num", "nudge+", "minus"]
    rules = {
        "i_cap_5_6_11": r_cap(d, base),
        "ii_src0_own_t0.6": r_src_zero(d, base, 0.6),
        "iv_single_u0.75": r_singleton(d, base, 0.75),
        "v_mass_all": r_mass(d, base, "psum_all"),
        "vi_nsa_drop_t4_0.75": r_nsa(d, base, 0.675, 0.75),
        "vi_nsa_drop_t4_0.80": r_nsa(d, base, 0.675, 0.80),
        "vi_nsa_t2_0.625_t4_0.75": r_nsa(d, base, 0.625, 0.75),
        "vi_rank0_add_t0_0.6": r_rank(d, base, 0.6, 0.675),
        "vi_acr_add": r_pop(d, base, pops, ["acr"], acr_nr, 0.1),
        "COMBO_cap+nsa_drop0.75+rank0_0.6+acr": combo(d, base, pops),
    }
    res = {}
    for k, m in rules.items():
        g = gate(d, uni, th, base, m)
        hb, hm = base & d.hold.to_numpy(), m & d.hold.to_numpy()
        g["changes"] = {"add": int((hm & ~hb).sum()), "drop": int((hb & ~hm).sum())}
        # per country delta on the full holdout
        from ber.eval.metric import per_entity_f05
        s1, r = d.s1.to_numpy(), d.r.to_numpy()
        fa = per_entity_f05(pd.DataFrame({"s1": s1[base], "r": r[base]}), th, uni)["f05"]
        fb = per_entity_f05(pd.DataFrame({"s1": s1[m], "r": r[m]}), th, uni)["f05"]
        g["by_country"] = {str(c): float(v) for c, v in (fb - fa).groupby(cty.reindex(fa.index).to_numpy()).mean().items()}
        res[k] = g
        print(f"{k:40s} {fmt_gate({x: g[x] for x in ('full', 'A', 'B')})} | {g['changes']} | {g['by_country']}",
              flush=True)
    json.dump(res, open(os.path.join(D, "gates.json"), "w"), indent=1)
    print("done", round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
