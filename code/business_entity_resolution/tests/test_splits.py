import numpy as np

from ber.eval.splits import HOLDOUT_FOLDS, N_FOLDS, fold_of, is_holdout, splitmix64
from ber.ids import to_eid

_M = (1 << 64) - 1


def _splitmix64_reference(x: int) -> int:
    z = (x + 0x9E3779B97F4A7C15) & _M
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _M
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _M
    return z ^ (z >> 31)


def test_numpy_matches_pure_python_reference():
    xs = np.arange(1_000_000_000, 1_000_002_000, dtype=np.int64)
    assert [int(v) for v in splitmix64(xs)] == [_splitmix64_reference(int(x)) for x in xs]


def test_locked_fold_values():
    # If this fails, the shared holdout has changed. Every reported number would stop being comparable.
    expected = {"S1-965667": 7, "S1-55344266": 12, "S1-343815751": 17, "S1-925783039": 7, "S1-773889195": 17, "S1-377745466": 7}
    got = {k: int(fold_of([to_eid(k)])[0]) for k in expected}
    assert got == expected


def test_holdout_share_is_about_25_percent():
    xs = np.arange(1_000_000_000, 1_000_200_000, dtype=np.int64)
    share = float(is_holdout(xs).mean())
    assert abs(share - len(HOLDOUT_FOLDS) / N_FOLDS) < 0.005
    assert fold_of(xs).min() >= 0 and fold_of(xs).max() < N_FOLDS
