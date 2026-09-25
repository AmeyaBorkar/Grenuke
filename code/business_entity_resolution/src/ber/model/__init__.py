"""Stages ``train``, ``predict``, ``decide`` (owner: Sachi, docs/TEAM.md). Plan: FINAL_PLAN sections 4.5-4.7.

train   (--split train): fit stage 1 (XGBoost, OOF groups from ``ber.eval.splits.oof_group``) and, from v1, stage 2
        and calibration; save models under ``work/models/<tag>/`` and OOF stage-1 scores
        ``write_table(df, "scores", f"{tag}-s1", "train", ...)`` (C5).
predict (both splits): calibrated ``p`` -> ``write_table(df, "scores", tag, split, ...)`` (C5). Models are read from
        ``work/models/<cfg.input_tag("models")>/``.
decide  (both splits): ownership (argmax per record in v0) + decision rule (tuned threshold in v0; expected-F DP
        behind gate G6) -> ``write_table(pairs, "matches", tag, split, ...)`` (C9, always a subset of C4).

Suggested modules: ``stage1.py``, ``stage2.py``, ``calibrate.py``, ``decide.py``. Calibration and model weights
are never fitted on the holdout (C2); tuning one or two scalars on it is allowed. Gates: ``ber.eval.gates``.
"""
from __future__ import annotations

from ..config import RunConfig


def train(cfg: RunConfig) -> dict:
    raise NotImplementedError("model v0 is roadmap task 1.5 (plans/FINAL_PLAN.md section 4.5, contract C5)")


def predict(cfg: RunConfig) -> dict:
    raise NotImplementedError("model v0 is roadmap task 1.5 (plans/FINAL_PLAN.md section 4.5, contract C5)")


def decide(cfg: RunConfig) -> dict:
    raise NotImplementedError("decide v0 is roadmap task 1.6 (plans/FINAL_PLAN.md section 4.7, contract C9)")
