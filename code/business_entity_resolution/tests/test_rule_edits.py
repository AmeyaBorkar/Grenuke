import numpy as np
import pytest

pytest.importorskip("rapidfuzz")
from ber.features.rule_edits import address_evidence, composed_edits


def test_first_street_word_does_not_prove_complete_address():
    d = address_evidence(["12 Rue Jean Moulin, Nantes"], ["12 Rue Jean Jaures, Bordeaux"])
    assert d.address_conflict.iloc[0]
    assert not d.address_add_ok.iloc[0]


def test_reordering_departments_typos_and_missing_city():
    d = address_evidence(
        ["Nantes, Pays de la Loire, 12 Rue Jean Moulin", "12 Rue Jean Moulin, Nantes", "64 Rue Bonnefin, Lille"],
        ["12 R. Jean Moulin, Nantes, Loire-Atlantique", "12 Rue Jean Moulin", "64 Rue Bonneuin, Lille"])
    assert d.address_add_ok.all()
    assert not d.address_conflict.any()


def test_truncated_street_is_not_a_contradiction():
    d = address_evidence(["12 Rue Jean Moulin, Nantes", "12 Rue Jean Moulin, Nantes"],
                         ["12 Rue Jean, Nantes", ""])
    assert d.street_close.iloc[0]
    assert not d.address_conflict.any()
    assert not d.address_add_ok.iloc[1]


def test_same_street_different_city_is_positive_conflict_evidence():
    d = address_evidence(["12 Rue Jean Moulin, Nantes"], ["12 Rue Jean Moulin, Lille"])
    assert d.city_conflict.iloc[0]
    assert not d.address_add_ok.iloc[0]


def test_composed_name_edits_are_diagnostics_not_implicit_acceptances():
    d = composed_edits(
        ["Nantes Club SAS", "Nantes Club SAS", "Nantes Club SAS", "Nantes Club SAS"],
        ["NANTES COMITE SAS FRANCE", "Nantes Club SAS France Services", "Nantes SAS France Services", "Nantes Club SAS France"])
    assert d.combination.tolist() == ["swap_list", "multi_append", "drop_multi_list", ""]
    assert d.dropped.tolist() == [1, 0, 1, 0]
    assert d.list_after_legal.tolist() == [1, 2, 2, 1]


def test_exact_alignment_before_fuzzy_and_duplicate_tokens():
    d = composed_edits(["AAAA AAAB SAS", "Club Club SAS"], ["AAAB France SAS", "Club Club SAS France Services"])
    assert d.dropped.tolist() == [1, 0]
    assert d.combination.tolist() == ["", "multi_append"]


def test_empty_names_and_permuted_pair_order():
    a, b = np.array(["", "Nantes Club SAS", "Nantes Club SAS"]), np.array(["", "Nantes Comite SAS France", "Nantes SAS France Services"])
    x = composed_edits(a, b)
    order = np.array([2, 0, 1])
    y = composed_edits(a[order], b[order])
    assert x.iloc[order].reset_index(drop=True).equals(y)
