"""Stage ``normalize`` (owner: Member 3, docs/TEAM.md). Plan: plans/FINAL_PLAN.md section 4.2. Contract: C3.

Input:  ``ber.records.load_records(cfg.split)`` -> eid, source, country, name, address.
Output: ``ber.artifacts.write_table(df, "norm", cfg.require_tag(), cfg.split, command=cfg.command)`` with one row per
        record: eid, source, country and the v0 columns of docs/CONTRACTS.md C3 (n_*, a_*, f_*).

Suggested modules: ``text.py`` (Unicode, Indic->Latin table), ``name.py``, ``address.py``, ``lexicons.py``
(US/India/France street types, legal forms, states/regions/departments; hand-written and documented).
Rules: vectorize or use multiprocessing (guard entry points for Windows spawn); country is an open set;
anything learned from pairs (e.g. the Indic dictionary) is fitted on training folds only (C2).
"""
from __future__ import annotations

from ..config import RunConfig


def run(cfg: RunConfig) -> dict:
    raise NotImplementedError("normalize v0 is roadmap task 1.2 (plans/FINAL_PLAN.md section 4.2, contract C3)")
