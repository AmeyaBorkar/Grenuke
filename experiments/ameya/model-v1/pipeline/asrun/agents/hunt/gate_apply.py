"""Paired-bootstrap gates of apply_hunt's rules on one model's holdout, using the deliverable implementation
(apply_hunt.apply_rules). Per-entity F0.5 is ber.eval.metric.per_entity_f05 and the interval is
ber.eval.gates.paired_bootstrap (1000 Poisson resamples, seed 0), which is exactly what ber.eval.gates.compare does.
Reported on the full holdout and halves A/B (splitmix64(s1) % 2), with mean deltas per country.

    python gate_apply.py 0.675 "cap nsa rank0 acr acr+cap acr+cap+nsa acr+cap+nsa+rank0"          # v7nst
    HUNT_SUFFIX=_v7s python gate_apply.py 0.70 "..."                                                   # v7s
A set "nsa|hi0.80" gates nsa with NSA_HI = 0.80 (sensitivity).
"""
import json
import os
import sys
import time

import numpy as np
import pandas as pd
import pyarrow.compute as pc
import pyarrow.parquet as pq

import apply_hunt
from base import D, K, universe_and_truth
from ber.eval.gates import paired_bootstrap
from ber.eval.metric import per_entity_f05
from ber.eval.splits import splitmix64
from ber.paths import records_path


def main():
    t0 = time.time()
    sfx = os.environ.get("HUNT_SUFFIX", "")
    thr = float(sys.argv[1])
    sets = (sys.argv[2] if len(sys.argv) > 2 else "cap nsa rank0 acr acr+cap acr+cap+nsa acr+cap+nsa+rank0").split()
    apply_hunt.THR = thr
    from feats import build
    d = build()
    uni, cty, th = universe_and_truth()
    t = pq.read_table(records_path("train"), columns=["eid", "source", "country"])
    t = t.filter(pc.equal(t["source"], 1))
    cty_all = pd.Series(t["country"].to_numpy(zero_copy_only=False), index=t["eid"].to_numpy())
    del t
    s = d.loc[d.cand, ["s1", "r", "pc", "own", "n_s1_all"]].reset_index(drop=True)
    m = d.loc[d.pred, ["s1", "r"]].reset_index(drop=True)
    yk = pd.Series(d.y.to_numpy(), index=d.s1.to_numpy() * K + d.r.to_numpy())
    yk = yk[~yk.index.duplicated()]
    del d
    fa = per_entity_f05(m, th, uni)["f05"].to_numpy()
    half = (splitmix64(uni) % np.uint64(2)).astype(np.int8)
    c = cty.reindex(uni).to_numpy()
    print(f"base holdout F0.5 {fa.mean():.6f}; thr {thr}; suffix '{sfx}'; A {int((half == 0).sum())} B "
          f"{int((half == 1).sum())} S1", flush=True)
    path = os.path.join(D, f"gates_apply{sfx}.json")
    res = json.load(open(path)) if os.path.exists(path) else {}
    res.update({"base_f05": float(fa.mean()), "thr": thr, "suffix": sfx})
    for token in sets:
        rs, _, opt = token.partition("|")
        apply_hunt.NSA_HI = float(opt[2:]) if opt.startswith("hi") else 0.75
        out, ch = apply_hunt.apply_rules(s, m, cty_all, rs.split("+"), "", None, "train")
        fb = per_entity_f05(out, th, uni)["f05"].to_numpy()
        g = {}
        for name, sel in (("full", np.ones(uni.size, bool)), ("A", half == 0), ("B", half == 1)):
            b = paired_bootstrap(fa[sel], fb[sel])
            g[name] = {k: b[k] for k in ("delta", "ci_low", "ci_high", "p_better", "n")}
            g[name]["by_country"] = {str(x): float((fb[sel & (c == x)] - fa[sel & (c == x)]).mean())
                                     for x in np.unique(c)}
        hch = ch[np.isin(ch.s1.to_numpy(), uni)]
        y = yk.reindex(hch.s1.to_numpy() * K + hch.r.to_numpy()).to_numpy()
        act = hch.action.to_numpy()
        g["changes"] = {a: int((act == a).sum()) for a in ("add", "drop")}
        g["changes_true"] = {a: int(np.nansum(y[act == a])) for a in ("add", "drop")}
        g["new_f05"] = float(fb.mean())
        res[token] = g
        f, a, b = g["full"], g["A"], g["B"]
        print(f"{token:24s} +{g['changes']['add']}({g['changes_true']['add']} true) -{g['changes']['drop']}"
              f"({g['changes_true']['drop']} true) | full {f['delta']:+.7f} [{f['ci_low']:+.7f}, {f['ci_high']:+.7f}]"
              f" | A {a['delta']:+.7f} [{a['ci_low']:+.7f}, {a['ci_high']:+.7f}]"
              f" | B {b['delta']:+.7f} [{b['ci_low']:+.7f}, {b['ci_high']:+.7f}]"
              f" | {', '.join(f'{k} {v:+.7f}' for k, v in f['by_country'].items())} ({time.time() - t0:.0f}s)",
              flush=True)
        json.dump(res, open(path, "w"), indent=1)
    print("done", round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
