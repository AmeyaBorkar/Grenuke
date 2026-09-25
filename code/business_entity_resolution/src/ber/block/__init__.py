"""Stage ``block`` (owner: Ameya, docs/TEAM.md). Plan: plans/FINAL_PLAN.md section 4.3. Contract: C4.

Input:  normalized records ``read_table("norm", cfg.input_tag("norm"), cfg.split)``.
Output: ``write_table(pairs, "candidates", cfg.require_tag(), cfg.split, ...)`` with s1, r, views (bitmask) and
        score_<view> / rank_s1_<view> / rank_r_<view>. This exact set becomes candidate_pairs.tsv.

View bits (v0): 1 V-both, 2 V-addr, 4 V-name-short, 8 key number+street, 16 key domain, 32 key DBA.
Suggested modules: ``vectorize.py`` (TF-IDF + SVD per country), ``knn.py`` (GPU tiled top-k both directions,
sparse CPU fallback), ``keys.py``, ``union.py`` (union, metadata, heuristic trim).
Blocking always searches the full record pool of the split; partitions are exact country labels (open set).
"""
from __future__ import annotations

from ..config import RunConfig

VIEW_BITS = {"both": 1, "addr": 2, "name_short": 4, "key_numstreet": 8, "key_domain": 16, "key_dba": 32}


def run(cfg: RunConfig) -> dict:
    raise NotImplementedError("block v0 is roadmap tasks 1.3a/1.3b (plans/FINAL_PLAN.md section 4.3, contract C4)")
