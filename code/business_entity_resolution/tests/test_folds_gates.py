import numpy as np
import pandas as pd
import pytest

from ber.eval import compare, fold_of, in_dev_sample, in_folds, is_holdout, oof_group, paired_bootstrap
from ber.eval.splits import DEV_SAMPLE_FOLDS, N_OOF_GROUPS, TRAIN_FOLDS


def test_oof_group_follows_folds():
    eids = np.arange(1_000_000_000, 1_000_020_000, dtype=np.int64)
    folds, groups = fold_of(eids), oof_group(eids)
    assert set(np.unique(groups)) == {-1, 0, 1, 2}
    assert (groups[is_holdout(eids)] == -1).all()
    train = ~is_holdout(eids)
    assert np.array_equal(groups[train], (folds[train] - TRAIN_FOLDS[0]) // 5)
    shares = np.bincount(groups[train], minlength=N_OOF_GROUPS) / train.sum()
    assert np.allclose(shares, 1 / 3, atol=0.03)


def test_in_folds():
    eids = np.arange(1_000_000_000, 1_000_005_000, dtype=np.int64)
    assert np.array_equal(in_folds(eids, range(5)), is_holdout(eids))
    assert np.array_equal(in_folds(eids, (0,)), fold_of(eids) == 0)


def test_bootstrap_identical_is_zero():
    f = np.random.default_rng(1).random(5000)
    res = paired_bootstrap(f, f, n_boot=200)
    assert res["delta"] == 0 and res["ci_low"] == 0 and res["ci_high"] == 0 and res["p_better"] == 0


def test_bootstrap_detects_gain_and_is_deterministic():
    rng = np.random.default_rng(2)
    base = rng.random(20000)
    new = np.clip(base + rng.normal(0.01, 0.05, base.size), 0, 1)
    a, b = paired_bootstrap(base, new, n_boot=300, seed=7), paired_bootstrap(base, new, n_boot=300, seed=7)
    assert a == b
    assert a["ci_low"] > 0 and a["ci_low"] <= a["delta"] <= a["ci_high"]


def test_bootstrap_rejects_mismatched_inputs():
    with pytest.raises(ValueError):
        paired_bootstrap(np.zeros(3), np.zeros(4))


def test_compare_keep_rule():
    truth = pd.DataFrame({"s1": [1, 1, 2, 3], "r": [10, 11, 20, 30]})
    universe = [1, 2, 3, 4]  # 4 is a singleton
    base = pd.DataFrame({"s1": [1, 4], "r": [10, 40]})          # misses, and a false merge on the singleton
    new = pd.DataFrame({"s1": [1, 1, 2, 3], "r": [10, 11, 20, 30]})  # perfect
    res = compare(base, new, truth, universe, groups={1: "US", 2: "US", 3: "India", 4: "India"}, n_boot=200)
    assert res["new_f05"] == 1.0 and res["delta"] > 0 and res["keep"]
    assert set(res["delta_by_group"]) == {"US", "India"}
    assert not compare(new, new, truth, universe, n_boot=50)["keep"]


def test_dev_sample_spans_holdout_and_every_oof_group():
    eids = np.arange(1_000_000_000, 1_000_400_000, dtype=np.int64)
    dev = in_dev_sample(eids)
    assert abs(dev.mean() - len(DEV_SAMPLE_FOLDS) / 20 / 4) < 0.002  # ~5% of S1
    assert set(np.unique(fold_of(eids[dev]))) == set(DEV_SAMPLE_FOLDS)
    assert set(np.unique(oof_group(eids[dev]))) == {-1, 0, 1, 2}
    # within each chosen fold, about a quarter of the entities are kept
    for f in DEV_SAMPLE_FOLDS:
        in_f = fold_of(eids) == f
        assert abs(dev[in_f].mean() - 0.25) < 0.02
