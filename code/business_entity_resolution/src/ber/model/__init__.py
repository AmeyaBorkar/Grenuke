"""Stages ``train``, ``predict``, ``decide`` (owner: Sachi, docs/TEAM.md). Plan: FINAL_PLAN sections 4.5-4.7.

train   (--split train): stage-1 XGBoost on C8 features of training folds (OOF groups from ``ber.eval.oof_group``),
        isotonic calibration fitted on OOF only; models -> work/models/<tag>/, OOF stage-1 scores -> C5 ``<tag>-s1``.
predict (both splits): calibrated ``p`` for every pair -> C5 ``<tag>``. Train: cross-fitted OOF ``p`` for training
        rows, full model for holdout (and unsampled) rows. Test: full model.
decide  (both splits): argmax ownership over ALL S1 candidates of each record (training folds included, as on
        test) + decision rule. Train: tunes the threshold on the holdout, runs gate G6 (expected-F DP vs threshold,
        paired bootstrap, ties -> threshold), saves the rule to work/models/<tag>/decide.json. Test: applies it.
        -> C9 ``<tag>`` (always a subset of C4).

    python -m ber.pipeline --stage train   --split train --tag sachi-model-v0 --in features=<feat> [--set sample_entities=400000]
    python -m ber.pipeline --stage predict --split train --tag sachi-model-v0 --in features=<feat>
    python -m ber.pipeline --stage decide  --split train --tag sachi-model-v0
    python -m ber.pipeline --stage predict --split test  --tag sachi-model-v0 --in features=<feat>
    python -m ber.pipeline --stage decide  --split test  --tag sachi-model-v0

Parameters (``--set``): sample_entities (train; default 0 = all), sample=dev (decide on train: evaluate dev-sample S1 only).
Calibration and model weights are never fitted on the holdout (C2); only the threshold / shift scalar is tuned on it.
The decision helpers live in ``decision.py``: a submodule named ``decide`` would shadow the ``decide`` stage function.
"""
from __future__ import annotations

import json
import pickle

import numpy as np
import pandas as pd

from ..config import RunConfig


# ------------------------------------------------------------------ helpers
def _in(cfg: RunConfig, kind: str) -> str:
    """Input tag for an artifact kind (``--in kind=tag``, default this run's tag)."""
    if hasattr(cfg, "input_tag"):
        return cfg.input_tag(kind)
    return (cfg.inputs or {}).get(kind, cfg.tag)


def _param(cfg: RunConfig, key: str, default=None):
    return (cfg.params or {}).get(key, default)


def _model_dir(tag: str):
    from ..paths import artifact_dir
    d = artifact_dir("models", tag)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _params(cfg: RunConfig) -> dict:
    from .stage1 import default_params
    p = default_params(None if cfg.device == "auto" else cfg.device)
    p["seed"] = cfg.seed
    if cfg.n_jobs and cfg.n_jobs > 0:
        p["nthread"] = cfg.n_jobs
    return p


def _load_features(cfg: RunConfig, split: str) -> pd.DataFrame:
    from ..artifacts import read_table
    df = read_table("features", _in(cfg, "features"), split)
    df = df.rename(columns={"s1": "s1_eid", "r": "r_eid", "y": "label"})
    for c in df.columns:
        if "__" in c:
            df[c] = df[c].astype(np.float32)
    return df


def _c5(df: pd.DataFrame, col: str, extra: tuple = ()) -> pd.DataFrame:
    out = {"s1": df["s1_eid"].astype(np.int64).to_numpy(), "r": df["r_eid"].astype(np.int64).to_numpy(),
           col: df[col].astype(np.float32).to_numpy()}
    for c in extra:
        out[c] = df[c].astype(np.int8).to_numpy()
    return pd.DataFrame(out)


def _split_train(df: pd.DataFrame, cfg: RunConfig):
    """Training-fold rows (optionally entity-sampled), holdout rows, unsampled training rows."""
    from ..eval import HOLDOUT_FOLDS
    hold_mask = np.isin(df["fold"].to_numpy(), list(HOLDOUT_FOLDS))
    train, hold = df[~hold_mask], df[hold_mask]
    rest = train.iloc[:0]
    n = int(_param(cfg, "sample_entities", 0) or 0)
    if n:
        ents = train["s1_eid"].drop_duplicates().sample(min(n, train["s1_eid"].nunique()), random_state=cfg.seed)
        pick = train["s1_eid"].isin(ents)
        train, rest = train[pick], train[~pick]
    return train.copy(), hold, rest


# ------------------------------------------------------------------ stage: train
def train(cfg: RunConfig) -> dict:
    from ..artifacts import write_table
    from ..eval import HOLDOUT_FOLDS, TRAIN_FOLDS, oof_group
    from .calibrate import fit_full, reliability_table
    from .stage1 import feature_columns, train_oof_and_full

    if set(HOLDOUT_FOLDS) != set(range(0, 5)) or set(TRAIN_FOLDS) != set(range(5, 20)):
        raise ValueError(f"unexpected folds HOLDOUT={HOLDOUT_FOLDS} TRAIN={TRAIN_FOLDS}")
    feats = _load_features(cfg, "train")
    train_df, hold, rest = _split_train(feats, cfg)
    if len(train_df) == 0:
        raise ValueError(f"no training-fold rows in features {_in(cfg, 'features')!r}")
    train_df["oof_group"] = np.asarray(oof_group(train_df["s1_eid"].to_numpy())).astype(np.int8)

    oof, _, info, booster = train_oof_and_full(train_df, {}, _params(cfg), verbose=200)
    y = train_df["label"].to_numpy()
    iso = fit_full(oof, y)

    d = _model_dir(cfg.tag)
    booster.save_model(str(d / "stage1_full.json"))
    with open(d / "isotonic.pkl", "wb") as fh:
        pickle.dump(iso, fh)
    meta = {"features": feature_columns(train_df), "best_iters": info["best_iters"], "n_full": info["n_full"],
            "features_tag": _in(cfg, "features"), "sample_entities": int(_param(cfg, "sample_entities", 0) or 0)}
    (d / "stage1.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")

    write_table(_c5(oof, "p1", ("oof_group",)), "scores", f"{cfg.tag}-s1", "train", command=cfg.command,
                inputs={"features": _in(cfg, "features")}, subset="training-fold rows, out-of-fold")
    ece = reliability_table(iso.predict(oof["p1"].to_numpy()), y).attrs["ece"]
    top = sorted(info["importance_gain"].items(), key=lambda kv: -kv[1])[:10]
    return {"train_pairs": len(train_df), "holdout_pairs": len(hold), "unsampled_pairs": len(rest),
            "best_iters": info["best_iters"], "n_full": info["n_full"], "ece_oof": round(ece, 5),
            "top_features": [k for k, _ in top]}


# ------------------------------------------------------------------ stage: predict
def predict(cfg: RunConfig) -> dict:
    import xgboost as xgb
    from ..artifacts import read_table, write_table
    from .calibrate import crossfit_oof
    from .stage1 import predict as xgb_predict

    mtag = _in(cfg, "models")
    d = _model_dir(mtag)
    booster = xgb.Booster()
    booster.load_model(str(d / "stage1_full.json"))
    with open(d / "isotonic.pkl", "rb") as fh:
        iso = pickle.load(fh)
    cols = json.loads((d / "stage1.json").read_text(encoding="utf-8"))["features"]

    feats = _load_features(cfg, cfg.split)
    missing = [c for c in cols if c not in feats.columns]
    if missing:
        raise ValueError(f"features {_in(cfg, 'features')!r} lack model columns: {missing[:5]}")

    if cfg.split == "train":
        oof = read_table("scores", f"{mtag}-s1", "train").rename(columns={"s1": "s1_eid", "r": "r_eid"})
        oof = oof.merge(feats[["s1_eid", "r_eid", "label"]], on=["s1_eid", "r_eid"], how="left")
        oof["p"] = crossfit_oof(oof, oof["label"].to_numpy())       # honest calibrated OOF
        key = feats["s1_eid"].to_numpy().astype(np.int64) * 4_000_000_000 + feats["r_eid"].to_numpy()
        okey = oof["s1_eid"].to_numpy().astype(np.int64) * 4_000_000_000 + oof["r_eid"].to_numpy()
        other = feats[~np.isin(key, okey)]                          # holdout + unsampled training rows
        other = other[["s1_eid", "r_eid"]].assign(p=iso.predict(xgb_predict(booster, other, cols)))
        out = pd.concat([oof[["s1_eid", "r_eid", "p"]], other], ignore_index=True)
        src = {"oof_rows": len(oof), "full_model_rows": len(other)}
    else:
        out = feats[["s1_eid", "r_eid"]].assign(p=iso.predict(xgb_predict(booster, feats, cols)))
        src = {"full_model_rows": len(out)}
    write_table(_c5(out, "p"), "scores", cfg.tag, cfg.split, command=cfg.command,
                inputs={"features": _in(cfg, "features"), "models": mtag})
    return {"pairs": len(out), **src, "mean_p": round(float(out["p"].mean()), 5)}


# ------------------------------------------------------------------ stage: decide
def _holdout_universe(cfg: RunConfig) -> np.ndarray:
    from ..eval import in_dev_sample, in_folds, is_holdout
    from ..records import load_records
    rec = load_records("train", columns=["eid", "source"])
    s1 = rec.loc[rec["source"] == 1, "eid"].to_numpy()
    s1 = s1[is_holdout(s1)]
    if cfg.folds:
        s1 = s1[in_folds(s1, cfg.folds)]
    if _param(cfg, "sample") == "dev":
        s1 = s1[in_dev_sample(s1)]
    return s1


def decide(cfg: RunConfig) -> dict:
    from ..artifacts import read_table, write_table
    from .decision import (EvalIndex, apply_threshold, argmax_ownership, dp_decide, f_vector, tune_shift,
                           tune_threshold)

    stag, mtag = _in(cfg, "scores"), _in(cfg, "models")
    scores = read_table("scores", stag, cfg.split).rename(columns={"s1": "s1_eid", "r": "r_eid"})
    owned = argmax_ownership(scores)            # every S1 of the split competes for each record
    rule_path = _model_dir(mtag) / "decide.json"

    if cfg.split == "train":
        from ..eval import paired_bootstrap
        from ..records import load_truth
        universe = _holdout_universe(cfg)
        truth = load_truth().rename(columns={"s1": "s1_eid", "r": "r_eid"})
        ev = EvalIndex(universe, truth)
        oh = owned[owned["s1_eid"].isin(universe)]
        t, _, _ = tune_threshold(oh, ev)
        f_thr = f_vector(apply_threshold(oh, t), ev)
        b, _, _ = tune_shift(oh, ev)
        f_dp = f_vector(dp_decide(oh, b=b), ev)
        g = paired_bootstrap(f_thr, f_dp)
        rule = "dp" if (g["delta"] >= 0.002 and g["ci_low"] > 0) else "threshold"   # G6; ties -> threshold
        spec = {"rule": rule, "threshold": t, "shift_b": b, "scores_tag": stag,
                "gate_G6": {k: (float(v) if isinstance(v, (int, float, np.floating)) else v) for k, v in g.items()},
                "holdout_f05": {"threshold": round(float(f_thr.mean()), 5), "dp": round(float(f_dp.mean()), 5)},
                "n_holdout_s1": int(len(universe))}
        rule_path.write_text(json.dumps(spec, indent=1), encoding="utf-8")
    else:
        if not rule_path.exists():
            raise FileNotFoundError(f"{rule_path} missing: run --stage decide --split train first")
        spec = json.loads(rule_path.read_text(encoding="utf-8"))

    matches = dp_decide(owned, b=spec["shift_b"]) if spec["rule"] == "dp" else apply_threshold(owned, spec["threshold"])
    out = pd.DataFrame({"s1": matches["s1_eid"].astype(np.int64).to_numpy(),
                        "r": matches["r_eid"].astype(np.int64).to_numpy()})
    write_table(out, "matches", cfg.tag, cfg.split, command=cfg.command,
                inputs={"scores": stag, "models": mtag}, rule=spec["rule"], threshold=spec["threshold"])
    res = {"matches": len(out), "owned_pairs": len(owned), "rule": spec["rule"], "threshold": spec["threshold"]}
    if cfg.split == "train":
        res.update(holdout_f05=spec["holdout_f05"], gate_G6=spec["gate_G6"], n_holdout_s1=spec["n_holdout_s1"])
    return res
