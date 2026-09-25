"""Shared evaluation: the official metric and the team-wide holdout (docs/CONTRACTS.md C2, C7)."""
from .metric import entity_f05, macro_f05, macro_f05_pairs, oracle_f05, pair_recall, per_entity_f05, report
from .splits import HOLDOUT_FOLDS, N_FOLDS, fold_of, is_holdout

__all__ = [
    "entity_f05",
    "macro_f05",
    "macro_f05_pairs",
    "oracle_f05",
    "pair_recall",
    "per_entity_f05",
    "report",
    "HOLDOUT_FOLDS",
    "N_FOLDS",
    "fold_of",
    "is_holdout",
]
