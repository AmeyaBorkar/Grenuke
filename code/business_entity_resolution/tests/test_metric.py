import numpy as np
import pandas as pd
import pytest

from ber.eval.metric import entity_f05, macro_f05, macro_f05_pairs, oracle_f05, pair_recall, per_entity_f05, report
from ber.ids import to_eid


def test_readme_example():
    # README: predict [S2-00047, S2-00193, S3-00812], truth [S2-00047, S3-00812] -> 0.714
    assert entity_f05({"a", "b", "c"}, {"a", "c"}) == pytest.approx(0.7142857, abs=1e-6)


def test_singleton_rules():
    assert entity_f05(set(), set()) == 1.0
    assert entity_f05({"x"}, set()) == 0.0
    assert entity_f05(set(), {"x"}) == 0.0


def test_perfect_and_partial():
    assert entity_f05({"a", "b"}, {"a", "b"}) == 1.0
    # c=1, |T|=2, |P|=1 -> 1.25 / (0.5 + 1) = 0.8333
    assert entity_f05({"a"}, {"a", "b"}) == pytest.approx(1.25 / 1.5)


def test_macro_counts_missing_keys_as_empty():
    truth = {"s1": {"a"}, "s2": set(), "s3": {"b", "c"}}
    pred = {"s1": {"a"}}  # s2 -> empty (correct singleton), s3 -> empty (0)
    assert macro_f05(pred, truth) == pytest.approx((1 + 1 + 0) / 3)


def _random_pairs(rng, n_s1=300):
    s1 = 1_000_000_000 + np.arange(n_s1)
    true_rows, pred_rows = [], []
    for s in s1:
        t = set(rng.choice(np.arange(2_000_000_000, 2_000_000_050), size=rng.integers(0, 5), replace=False).tolist())
        p = set(rng.choice(np.arange(2_000_000_000, 2_000_000_050), size=rng.integers(0, 5), replace=False).tolist())
        p |= set(list(t)[: rng.integers(0, len(t) + 1)])
        true_rows += [(s, r) for r in t]
        pred_rows += [(s, r) for r in p]
    return s1, pd.DataFrame(true_rows, columns=["s1", "r"]), pd.DataFrame(pred_rows, columns=["s1", "r"])


def test_vectorized_matches_reference():
    rng = np.random.default_rng(0)
    s1, true, pred = _random_pairs(rng)
    ref = macro_f05(pred.groupby("s1")["r"].apply(set).to_dict(), true.groupby("s1")["r"].apply(set).to_dict(), s1)
    assert macro_f05_pairs(pred, true, s1) == pytest.approx(ref, abs=1e-12)


def test_recall_and_oracle():
    a, b, c = to_eid("S1-1"), to_eid("S1-2"), to_eid("S1-3")  # c is a singleton
    x, y, z = to_eid("S2-10"), to_eid("S3-11"), to_eid("S2-12")
    true = pd.DataFrame({"s1": [a, a, b], "r": [x, y, z]})
    cand = pd.DataFrame({"s1": [a, b, c], "r": [x, y, z]})  # covers only (a, x)
    assert pair_recall(cand, true) == pytest.approx(1 / 3)
    # oracle: a -> {x} of {x,y}: 1.25/(0.5+1); b -> 0; c -> singleton 1
    assert oracle_f05(cand, true, [a, b, c]) == pytest.approx((1.25 / 1.5 + 0 + 1) / 3)


def test_report_groups_and_singletons():
    a, b = to_eid("S1-1"), to_eid("S1-2")
    true = pd.DataFrame({"s1": [a], "r": [to_eid("S2-5")]})
    pred = pd.DataFrame({"s1": [a], "r": [to_eid("S2-5")]})
    rep = report(pred, true, [a, b], groups={a: "US", b: "India"})
    assert rep["macro_f05"] == 1.0 and rep["singleton_share"] == 0.5
    assert rep["by_group"] == {"India": 1.0, "US": 1.0}
    assert per_entity_f05(pred, true, [a, b])["n_hit"].tolist() == [1, 0]
