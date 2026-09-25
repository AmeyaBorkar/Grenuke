"""Team-wide shared holdout, training folds and stacking groups (docs/CONTRACTS.md C2).

fold(eid) = splitmix64(eid) mod 20. Holdout = train S1 entities with fold in {0, 1, 2, 3, 4} (~25%).
Training folds are 5-19; out-of-fold stacking uses three groups: folds 5-9, 10-14, 15-19.
Pure integer arithmetic: identical on every machine, OS, and numpy/pandas version.
Tests lock the values for known ids.
"""
from __future__ import annotations

import numpy as np

N_FOLDS = 20
HOLDOUT_FOLDS = (0, 1, 2, 3, 4)
TRAIN_FOLDS = tuple(range(5, 20))
N_OOF_GROUPS = 3
DEV_FOLDS = (0,)  # quick iterations only; PR numbers use the full holdout
# Dev sample for small machines: 1/4 of the S1 in folds 0, 5, 10 and 15 (~110k S1, ~5% of train S1).
# Its fold-0 part (~27k S1) is a dev holdout; folds 5/10/15 give one fold per OOF group for training.
DEV_SAMPLE_FOLDS = (0, 5, 10, 15)
DEV_SAMPLE_MOD = 4

_C0 = np.uint64(0x9E3779B97F4A7C15)
_C1 = np.uint64(0xBF58476D1CE4E5B9)
_C2 = np.uint64(0x94D049BB133111EB)


def splitmix64(x) -> np.ndarray:
    """SplitMix64 finalizer applied element-wise (uint64 arithmetic wraps mod 2**64)."""
    z = np.atleast_1d(np.asarray(x)).astype(np.uint64)
    with np.errstate(over="ignore"):
        z = z + _C0
        z = (z ^ (z >> np.uint64(30))) * _C1
        z = (z ^ (z >> np.uint64(27))) * _C2
        z = z ^ (z >> np.uint64(31))
    return z


def fold_of(eids) -> np.ndarray:
    """Fold id in [0, N_FOLDS) for each eid (int64 array-like)."""
    return (splitmix64(np.asarray(eids, dtype=np.int64)) % np.uint64(N_FOLDS)).astype(np.int8)


def is_holdout(eids) -> np.ndarray:
    """Boolean mask: True for S1 eids in the shared holdout."""
    return np.isin(fold_of(eids), HOLDOUT_FOLDS)


def in_folds(eids, folds) -> np.ndarray:
    """Boolean mask: True for eids whose fold is in ``folds`` (e.g. ``DEV_FOLDS`` for quick runs)."""
    return np.isin(fold_of(eids), np.asarray(tuple(folds), dtype=np.int8))


def in_dev_sample(eids) -> np.ndarray:
    """Boolean mask: True for S1 eids in the dev sample (DEV_SAMPLE_FOLDS, then 1 in DEV_SAMPLE_MOD by a second hash digit)."""
    h = splitmix64(np.asarray(eids, dtype=np.int64))
    fold = (h % np.uint64(N_FOLDS)).astype(np.int64)
    keep = (h // np.uint64(N_FOLDS)) % np.uint64(DEV_SAMPLE_MOD) == 0
    return np.isin(fold, DEV_SAMPLE_FOLDS) & keep


def oof_group(eids) -> np.ndarray:
    """Stacking group per S1: folds 5-9 -> 0, 10-14 -> 1, 15-19 -> 2, holdout -> -1.

    A model scoring group g must be trained on the other training groups only (docs/CONTRACTS.md C2).
    """
    f = fold_of(eids).astype(np.int16)
    return np.where(f >= TRAIN_FOLDS[0], (f - TRAIN_FOLDS[0]) // 5, -1).astype(np.int8)
