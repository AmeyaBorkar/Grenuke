"""Leave-one-country-out on the dev kit (gate G13): how much does each feature group lose on an unseen country?

    python experiments/ameya/model-v1/loco.py --dev ameya-fx3-dev --train-country US --eval-country India

Stage-1-style XGBoost on the dev-sample pairs (work/features/<dev>/train.parquet, 87 features). The evaluation set is
the holdout folds (0-4) of --eval-country; the models train on folds 5-19:
- ``in``: both countries (the in-country reference);
- ``loco``: --train-country only;
- variants of ``loco``: without the lo__* group, without the legal-form bitmasks, and ``loco`` scored with the
  eval country's lo__* zeroed (its words unseen, like France).
Macro F0.5 with argmax ownership and the best global threshold (``common.FastEval``) on the eval-country holdout S1.
"""
from __future__ import annotations

import argparse
import json
import logging
import time

import numpy as np
import pandas as pd
import pyarrow.compute as pc
import pyarrow.parquet as pq
import xgboost as xgb

from ber.artifacts import write_report
from ber.paths import artifact_path, records_path
from ber.records import load_truth
from common import FastEval, argmax_owner

log = logging.getLogger("loco")
PARAMS = {"objective": "binary:logistic", "eval_metric": "logloss", "tree_method": "hist", "device": "cuda",
          "max_bin": 256, "subsample": 0.8, "max_depth": 9, "eta": 0.08, "colsample_bytree": 0.7,
          "min_child_weight": 10, "lambda": 2.0}
KEYS = ("s1", "r", "fold", "y")
BITS = ("leg__r_only_bits", "leg__s1_only_bits")


def fit(X: np.ndarray, y: np.ndarray, names: list[str], seed: int = 26) -> xgb.Booster:
    rng = np.random.default_rng(seed)
    es = rng.random(y.size) < 0.05
    dtr = xgb.QuantileDMatrix(X[~es], y[~es], feature_names=names)
    dva = xgb.QuantileDMatrix(X[es], y[es], feature_names=names, ref=dtr)
    return xgb.train(PARAMS, dtr, 3000, evals=[(dva, "es")], early_stopping_rounds=60, verbose_eval=False)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev", default="ameya-fx3-dev")
    ap.add_argument("--train-country", default="US")
    ap.add_argument("--eval-country", default="India")
    ap.add_argument("--lop", default="", help="dev-aligned proxy lo__* features (feats_lo_proxy.py --split train)")
    ap.add_argument("--only-proxy", action="store_true", help="train in/loco only and score the proxy variants")
    ap.add_argument("--self-train", type=int, default=0, help="rounds of self-training on the eval country (0: off)")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    t0 = time.perf_counter()
    df = pq.read_table(artifact_path("features", args.dev, "train")).to_pandas()
    feats = [c for c in df.columns if c not in KEYS]
    rec = pq.read_table(records_path("train"), columns=["eid", "source", "country"])
    rec = rec.filter(pc.equal(rec["source"], 1))
    cmap = pd.Series(np.asarray(rec["country"].to_numpy(zero_copy_only=False), dtype=object), index=rec["eid"].to_numpy())
    df["cty"] = cmap.reindex(df["s1"].to_numpy()).to_numpy()
    tr_all = df["fold"].to_numpy() >= 5
    ev = (~tr_all) & (df["cty"].to_numpy() == args.eval_country)
    tr_loco = tr_all & (df["cty"].to_numpy() == args.train_country)
    y = df["y"].to_numpy()
    universe = np.unique(df.loc[ev, "s1"].to_numpy())
    truth = load_truth()
    truth = truth[truth["s1"].isin(universe)]
    e = df.loc[ev].reset_index(drop=True)
    fe = FastEval(e["s1"].to_numpy(), e["r"].to_numpy(), truth, universe)
    log.info("eval %s holdout: %d S1, %d pairs; train rows in %d, loco %d", args.eval_country, universe.size, len(e),
             int(tr_all.sum()), int(tr_loco.sum()))

    lop = lop_full = None
    if args.lop:
        lop_full = pq.read_table(artifact_path("features", args.lop, "train")).to_pandas()
        if len(lop_full) != len(df):
            raise ValueError("the proxy file is not aligned with the dev features")
        lop = lop_full.loc[ev].reset_index(drop=True)

    def matrix(rows: np.ndarray, cols: list[str], mode: str) -> np.ndarray:
        """Features of ``rows`` with the lo__* group as is, zeroed (words unseen) or from the proxy table."""
        X = df.loc[rows, cols].to_numpy(np.float32).copy()
        for i, c in enumerate(cols):
            if not c.startswith("lo__"):
                continue
            if mode == "zero":
                X[:, i] = np.where(np.isfinite(X[:, i]), 0.0, X[:, i]) if c.endswith("_min") else 0.0
            elif mode == "proxy":
                X[:, i] = lop_full.loc[rows, c].to_numpy(np.float32)
        return X

    def score(b: xgb.Booster, cols: list[str], zero_lo: bool = False, proxy: bool = False) -> dict:
        X = e[cols].to_numpy(np.float32).copy()
        if proxy:  # the eval country's lo__* from its label-free proxy table
            for i, c in enumerate(cols):
                if c.startswith("lo__"):
                    X[:, i] = lop[c].to_numpy(np.float32)
        if zero_lo:  # every word unseen: the table lookup gives 0 (min stays NaN where a side has no word)
            for i, c in enumerate(cols):
                if c.startswith("lo__"):
                    X[:, i] = np.where(np.isfinite(X[:, i]), 0.0, X[:, i]) if c.endswith("_min") else 0.0
        p = b.inplace_predict(X, iteration_range=(0, b.best_iteration + 1))
        own = argmax_owner(e["s1"].to_numpy(), e["r"].to_numpy(), p)
        t, f, _ = fe.sweep(p, own)
        ll = float(-np.mean(np.where(e["y"].to_numpy() == 1, np.log(np.clip(p, 1e-7, 1)), np.log(np.clip(1 - p, 1e-7, 1)))))
        return {"f05": round(float(f), 5), "threshold": round(float(t), 3), "logloss": round(ll, 5)}

    res = {}
    variants = {"in": (tr_all, feats), "loco": (tr_loco, feats)} if args.only_proxy else {
        "in": (tr_all, feats),
        "loco": (tr_loco, feats),
        "loco_no_lo": (tr_loco, [c for c in feats if not c.startswith("lo__")]),
        "loco_no_bits": (tr_loco, [c for c in feats if c not in BITS]),
        "in_no_bits": (tr_all, [c for c in feats if c not in BITS]),
    }
    boosters = {}
    for name, (rows, cols) in variants.items():
        b = fit(df.loc[rows, cols].to_numpy(np.float32), y[rows], cols)
        boosters[name] = (b, cols)
        res[name] = score(b, cols)
        log.info("%-14s %s (%.0fs)", name, res[name], time.perf_counter() - t0)
    if lop is not None:
        # proxy lo as the model's own feature: (a) replacing lo everywhere; (b) next to lo, with lo blanked (NaN) on a
        # random half of the training rows so the model learns what to do when a country's words are unknown
        lo_cols = [c for c in feats if c.startswith("lo__")]
        rng = np.random.default_rng(7)
        for name, rows in (("loco", tr_loco), ("in", tr_all)):
            Xp = matrix(rows, feats, "proxy")
            b = fit(Xp, y[rows], feats)
            res[f"{name}_trained_on_proxy"] = score(b, feats, proxy=True)
            log.info("%-14s %s", f"{name}_trained_on_proxy", res[f"{name}_trained_on_proxy"])
            cols2 = feats + [c.replace("lo__", "lop__") for c in lo_cols]
            Xa = df.loc[rows, feats].to_numpy(np.float32)
            Xb = lop_full.loc[rows, lo_cols].to_numpy(np.float32)
            blank = rng.random(Xa.shape[0]) < 0.5
            for i, c in enumerate(feats):
                if c.startswith("lo__"):
                    Xa[blank, i] = np.nan
            b = fit(np.hstack([Xa, Xb]), y[rows], cols2)
            Xe = np.hstack([e[feats].to_numpy(np.float32), lop[lo_cols].to_numpy(np.float32)])
            for i, c in enumerate(feats):
                if c.startswith("lo__"):
                    Xe[:, i] = np.nan
            pe = b.inplace_predict(Xe, iteration_range=(0, b.best_iteration + 1))
            own = argmax_owner(e["s1"].to_numpy(), e["r"].to_numpy(), pe)
            t, f, _ = fe.sweep(pe, own)
            res[f"{name}_dropout_proxy"] = {"f05": round(float(f), 5), "threshold": round(float(t), 3)}
            log.info("%-14s %s", f"{name}_dropout_proxy", res[f"{name}_dropout_proxy"])
        for name in ("in", "loco"):
            b, cols = boosters[name]
            res[f"{name}_lo_proxy"] = score(b, cols, proxy=True)
            log.info("%-14s %s", f"{name}_lo_proxy", res[f"{name}_lo_proxy"])
    b, cols = boosters["loco"]
    res["loco_lo_zeroed"] = score(b, cols, zero_lo=True)
    log.info("%-14s %s", "loco_lo_zeroed", res["loco_lo_zeroed"])
    b, cols = boosters["in"]
    res["in_lo_zeroed"] = score(b, cols, zero_lo=True)
    log.info("%-14s %s", "in_lo_zeroed", res["in_lo_zeroed"])
    if args.self_train:
        # transductive self-training: pseudo-label the eval country's pairs (all folds; labels never read), retrain
        tgt = df["cty"].to_numpy() == args.eval_country
        s1_t, r_t = df.loc[tgt, "s1"].to_numpy(), df.loc[tgt, "r"].to_numpy()
        for mode in ["asis", "zero"] + (["proxy"] if lop_full is not None else []):
            b, cols = boosters["loco"]
            Xs = df.loc[tr_loco, cols].to_numpy(np.float32)
            Xt = matrix(tgt, cols, mode)
            for it in range(args.self_train):
                p = b.inplace_predict(Xt, iteration_range=(0, b.best_iteration + 1))
                own = argmax_owner(s1_t, r_t, p)
                pos, neg = (p >= 0.97) & own, p <= 0.03
                keep = pos | neg
                b = fit(np.vstack([Xs, Xt[keep]]), np.r_[y[tr_loco], pos[keep].astype(y.dtype)], cols)
                r_ = score(b, cols, zero_lo=(mode == "zero"), proxy=(mode == "proxy"))
                res[f"loco_st{it + 1}_{mode}"] = r_
                log.info("%-14s %s (pseudo +%d / -%d)", f"loco_st{it + 1}_{mode}", r_, int(pos.sum()), int(neg.sum()))
    command = f"python experiments/ameya/model-v1/loco.py --dev {args.dev} --train-country {args.train_country} --eval-country {args.eval_country}"
    write_report(f"ameya-loco-{args.train_country}-{args.eval_country}".lower(), {"results": res},
                 command=command, inputs={"features": args.dev})
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
