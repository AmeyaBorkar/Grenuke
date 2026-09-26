"""Regression checks for rule application, independent of large cached runs."""
import importlib.util
from pathlib import Path

import pandas as pd

spec = importlib.util.spec_from_file_location("v7_rules", Path(__file__).with_name("rules.py"))
rules = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rules)


def profiles():
    return pd.DataFrame({
        "s1": [1, 2, 3, 4, 5, 6, 7], "r": [11, 12, 13, 14, 15, 16, 17],
        "op": ["A", "APP", "ACR", "NUM", "CODE", "B", ""],
        "base_pred": [False, False, False, False, False, True, False],
        "eligible_add": [True, True, False, True, True, False, True],
        "address_conflict": [True, False, False, False, False, True, False],
        "address_add_ok": [False, True, True, True, True, False, True],
        "combination": ["", "", "", "", "", "", "multi_append"]})


def test_guard_checks_additions_and_keeps_disabled_number_rules_disabled():
    base = pd.DataFrame({"s1": [6, 8], "r": [16, 18]})
    policy = {"rules": [], "validation_passed": True, "address_guard_enabled": True}
    result = rules.apply_rules(base, profiles(), policy)
    assert list(result.itertuples(index=False, name=None)) == [(2, 12), (8, 18)]


def test_unvalidated_guard_preserves_baseline_additions():
    base = pd.DataFrame({"s1": [8], "r": [18]})
    result = rules.apply_rules(base, profiles(), {"rules": [], "address_guard_enabled": True})
    assert 11 in set(result.r)


def test_unvalidated_combinations_cannot_be_applied():
    base = pd.DataFrame({"s1": [8], "r": [18]})
    policy = {"rules": [{"family": "multi_append", "action": "add", "enabled": True}]}
    result = rules.apply_rules(base, profiles(), policy)
    assert 17 not in set(result.r)
    policy["validation_passed"] = True
    assert 17 in set(rules.apply_rules(base, profiles(), policy).r)
    assert 17 not in set(rules.apply_rules(base, profiles(), policy, enable_combined=False).r)


def test_fit_does_not_enable_rules_without_independent_validation():
    d = pd.DataFrame({"cty": ["country_a"] * 250, "combination": ["multi_append"] * 250,
                      "base_pred": [False] * 250, "eligible_add": [True] * 250,
                      "address_add_ok": [True] * 250, "y": [1] * 250})
    policy = rules.fit_policy(d)
    rule = next(r for r in policy["rules"] if r["family"] == "multi_append")
    assert rule["fit_passes"]
    assert not rule["enabled"]
    assert not policy["validation_passed"]
