"""Vectorized v0 name, look-alike, number and address features (C8).

String scorers use aligned ``rapidfuzz.process.cpdist``.  Set comparisons use
compiled kernels in ``tokens`` and ``numbers``; no Python pair loop is used.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .numbers import number_features
from .tokens import token_features

FEATURES = {
    "name__ratio": "Character similarity of normalized core names.",
    "name__token_sort": "Core-name similarity after token sorting.",
    "name__token_set": "Core-name similarity after token-set normalization.",
    "name__partial": "Best substring similarity of the core names.",
    "name__jw": "Jaro-Winkler similarity of the core names.",
    "name__token_jaccard": "Exact core-name token intersection over union.",
    "name__contain_s1": "Fraction of S1 core-name tokens present in the candidate.",
    "name__contain_r": "Fraction of candidate core-name tokens present in S1.",
    "name__idf_cosine": "IDF-weighted token cosine of core names, fit per split and country.",
    "name__first_equal": "First core-name token agrees.",
    "name__last_equal": "Last core-name token agrees.",
    "name__token_count_diff": "Absolute difference in distinct core-name token counts.",
    "name__legal_equal": "Both legal-form codes are present and equal.",
    "name__legal_compatible": "Legal forms differ but belong to the same broad family.",
    "name__legal_conflict": "Both legal forms are present and incompatible.",
    "name__legal_missing": "At least one side has no legal-form code.",
    "name__concat_domain": "Space-free core-name similarity when a domain or hashtag is present.",
    "name__indic_mismatch": "Only one side contained Indic script.",
    "extra__s1_count": "S1 core-name tokens not explained by candidate tokens or short edits.",
    "extra__s1_idf_sum": "IDF sum of unexplained S1 name tokens.",
    "extra__s1_idf_max": "Largest IDF of an unexplained S1 name token.",
    "extra__r_count": "Candidate core-name tokens not explained by S1 tokens or short edits.",
    "extra__r_idf_sum": "IDF sum of unexplained candidate name tokens.",
    "extra__r_idf_max": "Largest IDF of an unexplained candidate name token.",
    "extra__substitution": "An unmatched name-token pair differs by at most two edits.",
    "num__equal": "Primary house numbers are present and equal.",
    "num__truncation": "A primary number is a decimal truncation of the other.",
    "num__suffix": "A primary number is a decimal suffix of the other.",
    "num__letter_suffix_equal": "The same nonempty house-number letter or bis/ter suffix appears.",
    "num__nudge": "Primary house numbers differ by one to ten.",
    "num__missing": "At least one primary house number is absent.",
    "num__abs_diff": "Absolute difference of known primary numbers.",
    "num__relative_diff": "Primary-number difference divided by the larger number.",
    "num__digit_edit": "Levenshtein distance of the decimal primary-number strings.",
    "num__same_length": "Known primary numbers have the same digit length.",
    "num__set_jaccard": "Jaccard of all address numbers, ignoring duplicates.",
    "num__s1_only": "Count of address numbers appearing only on S1.",
    "num__r_only": "Count of address numbers appearing only on the candidate.",
    "num__every_r_compatible": "Each candidate address number is equal or within ten of an S1 number.",
    "num__unit_equal": "Both numeric unit identifiers are present and equal.",
    "addr__street_jaccard": "Exact street-token intersection over union.",
    "addr__street_idf_overlap": "IDF-weighted street-token intersection over union.",
    "addr__street_jw": "Jaro-Winkler similarity of street text.",
    "addr__city_equal": "Both parsed cities are present and equal.",
    "addr__city_jw": "Jaro-Winkler similarity of parsed cities.",
    "addr__state_equal": "Both parsed state/region codes are present and equal.",
    "addr__token_set": "Token-set similarity of whole normalized addresses.",
    "addr__char_cosine": "Hashing character 3-gram cosine of whole addresses.",
    "addr__either_empty": "Either normalized address is empty.",
    "addr__either_short": "Either normalized address has at most three tokens.",
    "addr__either_landmark": "Either address has a landmark marker.",
    "addr__either_pobox": "Either address has a PO-box marker.",
    "addr__either_null": "Either raw address contained a null marker.",
    "addr__ntok_s1": "Number of normalized address tokens on S1.",
    "addr__ntok_r": "Number of normalized address tokens on the candidate.",
    "addr__ntok_diff": "Absolute normalized-address token-count difference.",
}


def _strings(frame: pd.DataFrame, column: str) -> np.ndarray:
    return frame[column].fillna("").astype(str).to_numpy(dtype=object)


def compute(left: pd.DataFrame, right: pd.DataFrame, countries: np.ndarray,
            name_idf: dict[str, dict[str, float]] | None = None,
            street_idf: dict[str, dict[str, float]] | None = None,
            number_csr: tuple[np.ndarray, np.ndarray] | None = None,
            left_rows: np.ndarray | None = None,
            right_rows: np.ndarray | None = None) -> pd.DataFrame:
    """Aligned candidate pairs to float32 feature columns, preserving pair order."""
    from rapidfuzz import fuzz, process
    from rapidfuzz.distance import JaroWinkler, Levenshtein
    from sklearn.feature_extraction.text import HashingVectorizer

    n = len(left)
    if len(right) != n or len(countries) != n:
        raise ValueError("pair sides and country labels must align")
    name_l, name_r = _strings(left, "n_core"), _strings(right, "n_core")
    street_l, street_r = _strings(left, "a_street"), _strings(right, "a_street")
    city_l, city_r = _strings(left, "a_city"), _strings(right, "a_city")
    addr_l, addr_r = _strings(left, "a_norm"), _strings(right, "a_norm")
    result: dict[str, np.ndarray] = {}

    def fuzzy(a, b, scorer, *, scale=100.0):
        return process.cpdist(a.tolist(), b.tolist(), scorer=scorer,
                              workers=-1, dtype=np.float32) / scale

    result["name__ratio"] = fuzzy(name_l, name_r, fuzz.ratio)
    result["name__token_sort"] = fuzzy(name_l, name_r, fuzz.token_sort_ratio)
    result["name__token_set"] = fuzzy(name_l, name_r, fuzz.token_set_ratio)
    result["name__partial"] = fuzzy(name_l, name_r, fuzz.partial_ratio)
    result["name__jw"] = fuzzy(name_l, name_r, JaroWinkler.normalized_similarity, scale=1)
    name_tokens = np.full((n, 12), np.nan, dtype=np.float32)
    street_tokens = np.full((n, 12), np.nan, dtype=np.float32)
    for country in pd.unique(countries):  # country groups, never individual pairs
        positions = np.flatnonzero(countries == country)
        lookup_name = (name_idf or {}).get(str(country))
        lookup_street = (street_idf or {}).get(str(country))
        name_tokens[positions] = token_features(
            name_l[positions].tolist(), name_r[positions].tolist(), lookup_name,
            absorb_typos=True,
        )
        street_tokens[positions] = token_features(
            street_l[positions].tolist(), street_r[positions].tolist(), lookup_street,
        )
    result["name__token_jaccard"] = name_tokens[:, 0]
    result["name__contain_s1"] = name_tokens[:, 1]
    result["name__contain_r"] = name_tokens[:, 2]
    result["name__idf_cosine"] = name_tokens[:, 3]
    first_l = pd.Series(name_l).str.extract(r"^(\S+)", expand=False).fillna("").to_numpy()
    first_r = pd.Series(name_r).str.extract(r"^(\S+)", expand=False).fillna("").to_numpy()
    last_l = pd.Series(name_l).str.extract(r"(\S+)$", expand=False).fillna("").to_numpy()
    last_r = pd.Series(name_r).str.extract(r"(\S+)$", expand=False).fillna("").to_numpy()
    result["name__first_equal"] = (first_l == first_r) & (first_l != "")
    result["name__last_equal"] = (last_l == last_r) & (last_l != "")
    result["name__token_count_diff"] = np.abs(
        pd.Series(name_l).str.count(" ").to_numpy() - pd.Series(name_r).str.count(" ").to_numpy()
    )
    legal_l, legal_r = _strings(left, "n_legal"), _strings(right, "n_legal")
    both_legal = (legal_l != "") & (legal_r != "")
    same_legal = both_legal & (legal_l == legal_r)
    corporation = np.array(["inc", "corp"])
    limited = np.array(["ltd", "pvt_ltd"])
    compatible = both_legal & ~same_legal & (
        (np.isin(legal_l, corporation) & np.isin(legal_r, corporation))
        | (np.isin(legal_l, limited) & np.isin(legal_r, limited))
    )
    result["name__legal_equal"] = same_legal
    result["name__legal_compatible"] = compatible
    result["name__legal_conflict"] = both_legal & ~same_legal & ~compatible
    result["name__legal_missing"] = ~both_legal
    concat_l, concat_r = _strings(left, "n_concat"), _strings(right, "n_concat")
    domain = (left["f_domain"].to_numpy(dtype=bool) | right["f_domain"].to_numpy(dtype=bool)
              | left["f_hashtag"].to_numpy(dtype=bool) | right["f_hashtag"].to_numpy(dtype=bool))
    result["name__concat_domain"] = np.where(domain, fuzzy(concat_l, concat_r, fuzz.ratio), np.nan)
    result["name__indic_mismatch"] = (left["f_indic"].to_numpy(dtype=bool)
                                      ^ right["f_indic"].to_numpy(dtype=bool))
    for label, index in (("s1_count", 5), ("s1_idf_sum", 6), ("s1_idf_max", 7),
                         ("r_count", 8), ("r_idf_sum", 9), ("r_idf_max", 10),
                         ("substitution", 11)):
        result[f"extra__{label}"] = name_tokens[:, index]

    number_l = left["a_num1"].to_numpy(dtype=np.int64)
    number_r = right["a_num1"].to_numpy(dtype=np.int64)
    known = (number_l >= 0) & (number_r >= 0)
    diff = np.abs(number_l.astype(np.float64) - number_r.astype(np.float64))
    equal = known & (number_l == number_r)
    truncation = known & ~equal & (((number_l // 10 == number_r) | (number_r // 10 == number_l))
                                   | (number_l // 100 == number_r) | (number_r // 100 == number_l))
    suffix = known & ~equal & (((number_l % 10 == number_r) | (number_r % 10 == number_l))
                               | (number_l % 100 == number_r) | (number_r % 100 == number_l))
    result["num__equal"] = equal
    result["num__truncation"] = truncation
    result["num__suffix"] = suffix
    sfx_l, sfx_r = _strings(left, "a_num1_sfx"), _strings(right, "a_num1_sfx")
    result["num__letter_suffix_equal"] = known & (sfx_l != "") & (sfx_l == sfx_r)
    result["num__nudge"] = known & (diff > 0) & (diff <= 10)
    result["num__missing"] = ~known
    result["num__abs_diff"] = np.where(known, diff, np.nan)
    result["num__relative_diff"] = np.where(known, diff / np.maximum.reduce(
        [number_l.astype(np.float64), number_r.astype(np.float64), np.ones(n)]), np.nan)
    number_str_l = pd.Series(number_l).astype(str).to_numpy(dtype=object)
    number_str_r = pd.Series(number_r).astype(str).to_numpy(dtype=object)
    result["num__digit_edit"] = np.where(known, fuzzy(number_str_l, number_str_r,
                                                       Levenshtein.distance, scale=1), np.nan)
    result["num__same_length"] = known & (pd.Series(number_str_l).str.len().to_numpy()
                                           == pd.Series(number_str_r).str.len().to_numpy())
    if number_csr is not None and left_rows is not None and right_rows is not None:
        numeric_sets = number_features(*number_csr, left_rows, right_rows)
        for label, index in (("set_jaccard", 0), ("s1_only", 1),
                             ("r_only", 2), ("every_r_compatible", 3)):
            result[f"num__{label}"] = numeric_sets[:, index]
    else:
        for label in ("set_jaccard", "s1_only", "r_only", "every_r_compatible"):
            result[f"num__{label}"] = np.full(n, np.nan, dtype=np.float32)
    unit_l, unit_r = left["a_unit"].to_numpy(dtype=np.int64), right["a_unit"].to_numpy(dtype=np.int64)
    result["num__unit_equal"] = (unit_l >= 0) & (unit_r >= 0) & (unit_l == unit_r)

    result["addr__street_jaccard"] = street_tokens[:, 0]
    result["addr__street_idf_overlap"] = street_tokens[:, 4]
    result["addr__street_jw"] = fuzzy(street_l, street_r, JaroWinkler.normalized_similarity, scale=1)
    state_l, state_r = _strings(left, "a_state"), _strings(right, "a_state")
    result["addr__city_equal"] = np.where((city_l != "") & (city_r != ""), city_l == city_r, np.nan)
    result["addr__city_jw"] = np.where((city_l != "") & (city_r != ""),
                                       fuzzy(city_l, city_r, JaroWinkler.normalized_similarity, scale=1), np.nan)
    result["addr__state_equal"] = np.where((state_l != "") & (state_r != ""),
                                            state_l == state_r, np.nan)
    result["addr__token_set"] = fuzzy(addr_l, addr_r, fuzz.token_set_ratio)
    hasher = HashingVectorizer(analyzer="char", ngram_range=(3, 3), n_features=2**18,
                               alternate_sign=False, norm="l2", dtype=np.float32)
    char_l = hasher.transform(addr_l)
    char_r = hasher.transform(addr_r)
    result["addr__char_cosine"] = np.asarray(char_l.multiply(char_r).sum(axis=1)).ravel()
    for label, field in (("empty", "f_addr_empty"), ("short", "f_addr_short"),
                         ("landmark", "f_landmark"), ("pobox", "f_pobox"),
                         ("null", "f_addr_null")):
        result[f"addr__either_{label}"] = (left[field].to_numpy(dtype=bool)
                                           | right[field].to_numpy(dtype=bool))
    ntok_l = left["a_ntok"].to_numpy(dtype=np.int16)
    ntok_r = right["a_ntok"].to_numpy(dtype=np.int16)
    result["addr__ntok_s1"] = ntok_l
    result["addr__ntok_r"] = ntok_r
    result["addr__ntok_diff"] = np.abs(ntok_l.astype(np.int32) - ntok_r.astype(np.int32))
    if set(result) != set(FEATURES):
        raise AssertionError(f"feature definitions differ from output: {set(result) ^ set(FEATURES)}")
    return pd.DataFrame({name: np.asarray(result[name], dtype=np.float32) for name in FEATURES})
