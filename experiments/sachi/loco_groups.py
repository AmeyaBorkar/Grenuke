"""Which feature groups make the model fragile on an unseen country? (leave-one-country-out, dev kit)

    python experiments/sachi/loco_groups.py --dev ameya-fx2-dev --train-country US --eval-country India

Question (France): a model trained on one country loses ~0.03 F0.5 on another even when that country's words are known
("country conventions"). For each feature group, retrain WITHOUT it and measure, on the eval country's holdout:
  - f05_oracle : best threshold tuned on the eval country itself (what loco.py reports; optimistic);
  - f05_fixed  : threshold tuned on the TRAIN country's holdout, then applied (what France actually gets);
and, in-country (both countries' training rows), the holdout cost of dropping the group.
A group is a France-robustness candidate if dropping it raises loco f05_fixed by >= +0.003 while the in-country score
drops by < 0.001. Groups = feature-name prefix before "__", plus name sub-families (skel, fz, cat, c_).
"""
from __future__ import annotations

import argparse
import json
import time

import numpy as np
import pandas as pd
import pyarrow.compute as pc
import pyarrow.parquet as pq
import xgboost as xgb

from ber.paths import artifact_path, records_path
from ber.records import load_truth
from common import FastEval, argmax_owner

PARAMS = {"objective": "binary:logistic", "eval_metric": "logloss", "tree_method": "hist", "device": "cpu",
          "max_bin": 256, "subsample": 0.8, "max_depth": 9, "eta": 0.08, "colsample_bytree": 0.7,
          "min_child_weight": 10, "lambda": 2.0}
KEYS = ("s1", "r", "fold", "y")
GRID = np.round(np.arange(0.30, 0.9501, 0.025), 3)


def group_of(c: str) -> str:
    pre = c.split("__")[0]
    if pre == "name":
        rest = c.split("__", 1)[1]
        for sub in ("skel4", "skel", "fz", "cat", "c_"):
            if rest.startswith(sub):
                return f"name_{sub.rstrip('_')}"
    return pre


def fit(X, y, names, seed=26):
    rng = np.random.default_rng(seed)
    es = rng.random(y.size) < 0.05
    dtr = xgb.QuantileDMatrix(X[~es], y[~es], feature_names=names)
    dva = xgb.QuantileDMatrix(X[es], y[es], feature_names=names, ref=dtr)
    return xgb.train(PARAMS, dtr, 3000, evals=[(dva, "es")], early_stopping_rounds=60, verbose_eval=False)


class Eval:
    def __init__(self, part: pd.DataFrame, truth: pd.DataFrame):
        self.s1, self.r = part["s1"].to_numpy(), part["r"].to_numpy()
        self.fe = FastEval(self.s1, self.r, truth, np.unique(self.s1))
        self.idx = part.index.to_numpy()

    def best(self, p):
        own = argmax_owner(self.s1, self.r, p)
        t, f, _ = self.fe.sweep(p, own, GRID)
        return t, f

    def at(self, p, t):
        return self.fe.score(argmax_owner(self.s1, self.r, p) & (p > t))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev", default="ameya-fx2-dev")
    ap.add_argument("--train-country", default="US")
    ap.add_argument("--eval-country", default="India")
    ap.add_argument("--no-in", action="store_true", help="skip the in-country runs (half the time)")
    ap.add_argument("--groups", default="", help="comma-separated subset of groups to test (default: all)")
    a = ap.parse_args()
    t0 = time.perf_counter()
    df = pq.read_table(artifact_path("features", a.dev, "train")).to_pandas()
    feats = [c for c in df.columns if c not in KEYS]
    rec = pq.read_table(records_path("train"), columns=["eid", "source", "country"])
    rec = rec.filter(pc.equal(rec["source"], 1))
    cmap = pd.Series(np.asarray(rec["country"].to_numpy(zero_copy_only=False), dtype=object),
                     index=rec["eid"].to_numpy())
    cty = cmap.reindex(df["s1"].to_numpy()).to_numpy()
    fold, y = df["fold"].to_numpy(), df["y"].to_numpy()
    tr_all = fold >= 5
    tr_loco = tr_all & (cty == a.train_country)
    truth = load_truth()
    ev_tr = Eval(df.loc[(~tr_all) & (cty == a.train_country)], truth)   # threshold source for "fixed"
    ev = Eval(df.loc[(~tr_all) & (cty == a.eval_country)], truth)

    groups = sorted({group_of(c) for c in feats})
    if a.groups:
        groups = [g for g in groups if g in a.groups.split(",")]
    print(f"{len(feats)} features in {len(groups)} groups: {groups}", flush=True)

    def run(drop: str | None) -> dict:
        cols = [c for c in feats if drop is None or group_of(c) != drop]
        X = df[cols].to_numpy(np.float32)
        out = {"n_features": len(cols)}
        b = fit(X[tr_loco], y[tr_loco], cols)
        t_tr, _ = ev_tr.best(b.inplace_predict(X[ev_tr.idx]))
        p = b.inplace_predict(X[ev.idx])
        t_or, f_or = ev.best(p)
        out.update(loco_oracle=round(f_or, 5), loco_fixed=round(ev.at(p, t_tr), 5), t_train=t_tr, t_oracle=t_or)
        if not a.no_in:
            b2 = fit(X[tr_all], y[tr_all], cols)
            out["in_oracle"] = round(ev.best(b2.inplace_predict(X[ev.idx]))[1], 5)
        return out

    res = {"ALL": run(None)}
    print("ALL", res["ALL"], f"({time.perf_counter() - t0:.0f}s)", flush=True)
    for g in groups:
        res[g] = run(g)
        print(f"-{g}", res[g], f"({time.perf_counter() - t0:.0f}s)", flush=True)

    base = res["ALL"]
    rows = []
    for g in groups:
        r = res[g]
        d_fixed = r["loco_fixed"] - base["loco_fixed"]
        d_in = (r["in_oracle"] - base["in_oracle"]) if "in_oracle" in r else float("nan")
        verdict = "CANDIDATE" if d_fixed >= 0.003 and (np.isnan(d_in) or d_in > -0.001) else ""
        rows.append((g, r["n_features"], d_fixed, r["loco_oracle"] - base["loco_oracle"], d_in, verdict))
    tab = pd.DataFrame(rows, columns=["dropped group", "n_feat", "d_loco_fixed", "d_loco_oracle", "d_in", "verdict"])
    print("\nbaseline:", base)
    print(tab.sort_values("d_loco_fixed", ascending=False).round(5).to_string(index=False))
    with open(f"loco_groups_{a.train_country}_{a.eval_country}.json", "w") as fh:
        json.dump(res, fh, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
