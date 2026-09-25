from __future__ import annotations

import numpy as np
import pandas as pd
import xgboost as xgb

OOF_GROUPS = {0: range(5, 10), 1: range(10, 15), 2: range(15, 20)}
TRAIN_FOLDS = set(range(5, 20))
KEY_COLS = ("s1_eid", "r_eid")


def default_params(device: str | None = None) -> dict:
    if device is None:
        device = "cuda" if xgb.build_info().get("USE_CUDA") else "cpu"
    return {
        "objective": "binary:logistic",
        "eval_metric": ["logloss", "aucpr"],
        "tree_method": "hist",
        "device": device,
        "max_depth": 8,
        "min_child_weight": 5,
        "eta": 0.08,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "lambda": 1.0,
        "max_bin": 256,
        "seed": 17,
    }


def _cuda_available() -> bool:
    try:
        xgb.train({"device": "cuda", "tree_method": "hist"},
                  xgb.DMatrix(np.zeros((2, 1)), label=[0, 1]), num_boost_round=1)
        return True
    except Exception:
        return False


def feature_columns(df: pd.DataFrame) -> list[str]:
    cols = [c for c in df.columns if "__" in c and c not in KEY_COLS]
    bad = [c for c in cols if "country" in c.lower()]
    if bad:
        raise ValueError(f"country-like feature columns are not allowed: {bad}")
    return cols


def _dmatrix(df, cols, label=None):
    X = df[cols].to_numpy(dtype=np.float32, copy=False)
    return xgb.QuantileDMatrix(X, label=label, max_bin=256, feature_names=cols) \
        if label is not None else xgb.DMatrix(X, feature_names=cols)


def _es_split(train_df, frac=0.05, seed=17):
    ents = np.unique(train_df["s1_eid"].to_numpy())
    rng = np.random.default_rng(seed)
    es_ents = rng.choice(ents, size=max(1, int(len(ents) * frac)), replace=False)
    m = train_df["s1_eid"].isin(es_ents).to_numpy()
    return train_df[~m], train_df[m]


def fit_one(train_df, cols, params, max_rounds=2000, es_rounds=50, verbose=100):
    fit_df, es_df = _es_split(train_df)
    dtr = _dmatrix(fit_df, cols, fit_df["label"].to_numpy())
    des = xgb.DMatrix(es_df[cols].to_numpy(np.float32), label=es_df["label"].to_numpy(),
                      feature_names=cols)
    booster = xgb.train(params, dtr, num_boost_round=max_rounds,
                        evals=[(des, "es")], early_stopping_rounds=es_rounds,
                        verbose_eval=verbose)
    return booster, booster.best_iteration + 1


def predict(booster, df, cols, n_rounds=None):
    d = xgb.DMatrix(df[cols].to_numpy(np.float32), feature_names=cols)
    rng = (0, n_rounds) if n_rounds else (0, 0)
    return booster.predict(d, iteration_range=rng)


def train_oof_and_full(train_df, apply_dfs, params=None, verbose=100):
    params = params or default_params()
    cols = feature_columns(train_df)
    if not set(train_df["fold"].unique()) <= TRAIN_FOLDS:
        raise ValueError("train_df contains holdout folds (0-4). Never train on them.")

    if "oof_group" in train_df.columns:          # team assignment (ber.eval.oof_group)
        grp = train_df["oof_group"].to_numpy()
    else:
        group_of_fold = {f: g for g, fs in OOF_GROUPS.items() for f in fs}
        grp = train_df["fold"].map(group_of_fold).to_numpy()
    if (grp < 0).any():
        raise ValueError("training rows with oof_group < 0 (holdout?)")

    oof = np.full(len(train_df), np.nan, dtype=np.float32)
    best_iters = []
    for g in np.unique(grp):
        tr, te = train_df[grp != g], train_df[grp == g]
        booster, n = fit_one(tr, cols, params, verbose=verbose)
        best_iters.append(n)
        oof[grp == g] = predict(booster, te, cols, n)

    n_full = int(np.mean(best_iters) * 1.1)
    dfull = _dmatrix(train_df, cols, train_df["label"].to_numpy())
    full = xgb.train(params, dfull, num_boost_round=n_full, verbose_eval=False)

    applied = {}
    for name, df in apply_dfs.items():
        out = df[list(KEY_COLS)].copy()
        out["p1"] = predict(full, df, cols)
        applied[name] = out

    oof_df = train_df[list(KEY_COLS)].copy()
    oof_df["p1"] = oof
    oof_df["oof_group"] = grp
    info = {"best_iters": best_iters, "n_full": n_full, "n_features": len(cols),
            "importance_gain": full.get_score(importance_type="gain")}
    return oof_df, applied, info, full
