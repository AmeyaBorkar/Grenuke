"""Stage ``features`` (owner: Member 3, docs/TEAM.md). Plan: plans/FINAL_PLAN.md section 4.4. Contract: C8.

Input:  candidates ``read_table("candidates", cfg.input_tag("candidates"), cfg.split)`` and normalized records
        ``read_table("norm", cfg.input_tag("norm"), cfg.split)``; truth via ``ber.records.load_truth()`` (train).
Output: ``write_table(df, "features", cfg.require_tag(), cfg.split, ...)``: s1, r, fold, y (train only) and float32
        columns named ``<group>__<name>`` (groups: name, extra, num, addr, ctx, ret, src, var, emb).

Rules: no country feature; frequency features as rates per split and country; supervised encodings out-of-fold
and holdout-free (C2); rapidfuzz cdist/cpdist, numba over token CSR arrays, chunked; never a Python loop over pairs.
Keep a one-line definition of every feature in this package (it feeds the methodology document).
"""
from __future__ import annotations

from ..config import RunConfig


def run(cfg: RunConfig) -> dict:
    raise NotImplementedError("features v0 is roadmap task 1.4 (plans/FINAL_PLAN.md section 4.4, contract C8)")
