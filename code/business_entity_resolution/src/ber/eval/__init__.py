"""Shared evaluation: the official metric, the team-wide holdout and folds, and gates (docs/CONTRACTS.md C2, C7, C10)."""
from .gates import compare, paired_bootstrap
from .metric import entity_f05, macro_f05, macro_f05_pairs, oracle_f05, pair_recall, per_entity_f05, report
from .splits import DEV_FOLDS, HOLDOUT_FOLDS, N_FOLDS, N_OOF_GROUPS, TRAIN_FOLDS, fold_of, in_folds, is_holdout, oof_group

__all__ = [
    "entity_f05",
    "macro_f05",
    "macro_f05_pairs",
    "oracle_f05",
    "pair_recall",
    "per_entity_f05",
    "report",
    "compare",
    "paired_bootstrap",
    "DEV_FOLDS",
    "HOLDOUT_FOLDS",
    "N_FOLDS",
    "N_OOF_GROUPS",
    "TRAIN_FOLDS",
    "fold_of",
    "in_folds",
    "is_holdout",
    "oof_group",
]
