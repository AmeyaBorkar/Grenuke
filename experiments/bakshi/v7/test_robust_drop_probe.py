import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from robust_drop_probe import repeated_word


def test_repetition_protects_word_already_in_source():
    assert repeated_word(["pinnacle asset group", "foot & ankle clinic"], ["asset", "ankle"]).tolist() == [True, True]


def test_new_business_word_and_substring_are_not_repetitions():
    assert repeated_word(["nantes club sas", "asset management corp"], ["comite", "ass"]).tolist() == [False, False]


def test_repetition_handles_punctuation_and_empty_batch():
    assert repeated_word(["pinedo, berny, cpa"], ["berny"]).tolist() == [True]
    assert repeated_word([], []).tolist() == []
