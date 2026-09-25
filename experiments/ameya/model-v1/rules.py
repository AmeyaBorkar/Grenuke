"""Decision rules beyond one global threshold, tuned on holdout folds 0-1 and scored on folds 2-4 (honest check).

    python experiments/ameya/model-v1/rules.py --scores ameya-s2-v1 --col pc

After argmax ownership:
- global: one threshold t;
- top/rest: t_top for each S1's best owned candidate, t_rest for the others (the metric's break-even is 0.5 for a
  lone candidate and rises to about 0.77 with set size; FINAL_PLAN section 2);
- by-size: t by the number of owned candidates above 0.5 in the S1 (1, 2, 3, 4+).
Prints the tuned parameters, the macro F0.5 on the tuning folds and on the untouched folds, and a paired bootstrap
of each rule against the global threshold on the untouched folds.
"""
from __future__ import annotations

import argparse
import itertools

import numpy as np
import pandas as pd

from ber.artifacts import read_table
from ber.eval.gates import paired_bootstrap
from ber.eval.splits import fold_of
from ber.records import load_truth
from common import FastEval, argmax_owner, holdout_universe

ap = argparse.ArgumentParser()
ap.add_argument("--scores", required=True)
ap.add_argument("--col", default="pc")
args = ap.parse_args()

sc = read_table("scores", args.scores, "train", ["s1", "r", args.col])
s1, r, p = sc["s1"].to_numpy(), sc["r"].to_numpy(), sc[args.col].to_numpy(np.float32)
truth = load_truth()
universe, _ = holdout_universe()
uf = fold_of(universe)
tune_u, test_u = universe[np.isin(uf, (0, 1))], universe[np.isin(uf, (2, 3, 4))]
own = argmax_owner(s1, r, p)
fe_tune, fe_test = FastEval(s1, r, truth, tune_u), FastEval(s1, r, truth, test_u)

# rank of each owned pair among its S1's owned pairs (0 = best) and the S1's count of owned pairs above 0.5
m = own & np.isin(s1, universe)
idx = np.flatnonzero(m)
d = pd.DataFrame({"s1": s1[idx], "p": p[idx], "i": idx})
d["rank"] = d.groupby("s1")["p"].rank(ascending=False, method="first") - 1
d["n05"] = d.assign(h=d["p"] > 0.5).groupby("s1")["h"].transform("sum")
rank = np.full(p.size, -1, np.int32)
rank[d["i"].to_numpy()] = d["rank"].to_numpy()
n05 = np.zeros(p.size, np.int32)
n05[d["i"].to_numpy()] = np.minimum(d["n05"].to_numpy(), 4)

grid = np.round(np.arange(0.40, 0.901, 0.025), 3)


def best(fe, make, space):
    res = [(params, fe.score(make(*params))) for params in space]
    return max(res, key=lambda x: x[1])


rules = {
    "global": (lambda t: own & (p > t), [(t,) for t in grid]),
    "top_rest": (lambda a, b: own & np.where(rank == 0, p > a, p > b), list(itertools.product(grid, grid))),
    "by_size": (lambda a, b, c, e: own & (p > np.select([n05 <= 1, n05 == 2, n05 == 3], [a, b, c], e)), None),
}
out = {}
for name, (make, space) in rules.items():
    if name == "by_size":  # coordinate descent from the global optimum (4 parameters)
        t0 = out["global"][0][0]
        params = [t0] * 4
        for _ in range(2):
            for k in range(4):
                cands = []
                for t in grid:
                    q = list(params)
                    q[k] = t
                    cands.append((tuple(q), fe_tune.score(make(*q))))
                params = list(max(cands, key=lambda x: x[1])[0])
        params = tuple(params)
        f_tune = fe_tune.score(make(*params))
    else:
        params, f_tune = best(fe_tune, make, space)
    out[name] = (params, f_tune, fe_test.score(make(*params)), fe_test.per_entity(make(*params)))
    print(f"{name:9s} params {params}  tune {f_tune:.5f}  untouched {out[name][2]:.5f}")
base = out["global"][3]
for name in ("top_rest", "by_size"):
    g = paired_bootstrap(base, out[name][3])
    print(f"{name} vs global on untouched folds: {g['delta']:+.5f} CI [{g['ci_low']:+.5f}, {g['ci_high']:+.5f}]")
