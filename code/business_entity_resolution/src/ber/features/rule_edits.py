"""Label-free address evidence and composed name edits for the v7 experiment.

These are diagnostic features, not acceptance rules. Parsing is done once per
distinct text; aligned-pair comparisons run in Numba/RapidFuzz. Unknown or
missing address components do not count as contradictions.
"""
from __future__ import annotations

import re
from functools import lru_cache

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
from numba import njit, prange

from ..block.text import DEPARTMENT_REGION, LEGAL, NAME_STOP, STREET, fold, ordinals_to_digits
from ..normalize.lexicons import STATE_CODES, STATE_NAMES
from .context import NUMSTREET, _SKIP

LIST_WORDS = frozenset("center services service partners fils cie associes groupe developpement france".split())
_LEGAL = LEGAL | frozenset("eirl scop selarl gie".split())
_STOP = NAME_STOP | frozenset(("et", "and"))
_MARKERS = set(STREET) | set(STREET.values()) | set(_SKIP.split("|"))
_REGIONS = set(STATE_NAMES) | set(STATE_CODES) | set(DEPARTMENT_REGION)
_REGIONS.update(d for deps in DEPARTMENT_REGION.values() for d in deps)
_ARTICLES = frozenset("de du des la le les d l et".split())


def _fold_texts(values):
    return np.asarray(fold(pa.array(values, type=pa.string())).to_numpy(zero_copy_only=False), object)


@lru_cache(maxsize=100_000)
def _address_parts(value: str) -> tuple[str, str]:
    """Street span and one unambiguous comma-delimited locality, or unknown."""
    segments = [re.sub(r"[^a-z0-9]+", " ", s).strip() for s in value.split(",")]
    segments = [s for s in segments if s]
    street_index, street = -1, ""
    for i, s in enumerate(segments):
        clean = re.sub(r"\b(?:" + _SKIP + r")\b", " ", s)
        match = re.search(NUMSTREET, clean)
        if match:
            # Keep every significant word after the primary number, not only its first word.
            words = re.findall(r"[a-z]+|[0-9]+", s)
            n = next((j for j, w in enumerate(words) if w.isdigit()), -1)
            street = " ".join(w for w in words[n + 1:] if w not in _MARKERS and w not in _ARTICLES)
            street_index = i
            break
    locality = []
    if street_index >= 0:
        for i, s in enumerate(segments):
            if i == street_index or s in _REGIONS or any(c.isdigit() for c in s):
                continue
            if not s or len(s.split()) > 5:
                continue
            locality.append(s)
    return street, locality[0] if len(locality) == 1 else ""


def address_evidence(left, right) -> pd.DataFrame:
    """Complete-street similarity plus positive evidence of locality conflict.

    Empty/ambiguous components remain unknown. A city mismatch is flagged only
    when both localities are confidently parsed and strongly dissimilar.
    """
    from rapidfuzz import fuzz, process
    from rapidfuzz.distance import Levenshtein

    values = np.r_[np.asarray(left, object), np.asarray(right, object)]
    unique, inv = np.unique(values.astype(str), return_inverse=True)
    folded = ordinals_to_digits(pa.array(_fold_texts(unique))).to_pylist()
    profiles = [_address_parts(s) for s in folded]
    street = np.array([p[0] for p in profiles], object)[inv]
    city = np.array([p[1] for p in profiles], object)[inv]
    n = len(left)
    a, b, ca, cb = street[:n], street[n:], city[:n], city[n:]
    sim = process.cpdist(a, b, scorer=Levenshtein.normalized_similarity, dtype=np.float32, workers=-1)
    csim = process.cpdist(ca, cb, scorer=Levenshtein.normalized_similarity, dtype=np.float32, workers=-1)
    known = (a != "") & (b != "")
    city_known = (ca != "") & (cb != "")
    # Typo tolerance grows with span length; no implication that different means false.
    dist = process.cpdist(a, b, scorer=Levenshtein.distance, dtype=np.int32, workers=-1)
    tolerance = np.where(np.minimum(np.char.str_len(a.astype(str)), np.char.str_len(b.astype(str))) < 7, 1, 2)
    subset = process.cpdist(a, b, scorer=fuzz.token_set_ratio, dtype=np.float32, workers=-1) == 100
    close = known & ((dist <= tolerance) | subset)
    conflict = (known & ~close) | (city_known & (csim < 0.5))
    return pd.DataFrame({"street_known": known, "street_equal": known & (a == b),
        "street_close": close, "street_similarity": np.where(known, sim, np.nan),
        "city_known": city_known, "city_equal": city_known & (ca == cb),
        "city_conflict": city_known & (csim < 0.5),
        "address_conflict": conflict, "address_add_ok": close & ~(city_known & (csim < 0.5))})


@njit(cache=True)
def _near(a, b):
    if a == b:
        return True
    if min(len(a), len(b)) < 4:
        return False
    limit = 1 if min(len(a), len(b)) < 7 else 2
    if abs(len(a) - len(b)) > limit:
        return False
    prev = np.arange(len(b) + 1, dtype=np.int32)
    for i in range(len(a)):
        cur = np.empty(len(b) + 1, np.int32)
        cur[0] = i + 1
        for j in range(len(b)):
            cur[j + 1] = min(cur[j] + 1, prev[j + 1] + 1, prev[j] + (a[i] != b[j]))
        prev = cur
    return prev[-1] <= limit


@njit(parallel=True, cache=True)
def _edits(left, right, ptr, codes, pos, legpos, vocab, is_list, out):
    for p in prange(left.size):
        s, r = left[p], right[p]
        sa, sb, ra, rb = ptr[s], ptr[s + 1], ptr[r], ptr[r + 1]
        if sb - sa > 32 or rb - ra > 32:
            out[p, 0] = -1
            continue
        used = np.zeros(rb - ra, np.bool_)
        matched = np.zeros(sb - sa, np.bool_)
        # Exact matches first so a fuzzy match cannot consume another token's exact copy.
        for fuzzy in range(2):
            for i in range(sa, sb):
                if matched[i - sa]:
                    continue
                for j in range(ra, rb):
                    if used[j - ra]:
                        continue
                    a, b = codes[i], codes[j]
                    ok = a == b if fuzzy == 0 else _near(vocab[a], vocab[b])
                    if ok:
                        matched[i - sa], used[j - ra] = True, True
                        break
        dropped = int((~matched).sum())
        added, list_added, other_added, after_legal = 0, 0, 0, 0
        for j in range(ra, rb):
            if not used[j - ra]:
                added += 1
                if is_list[codes[j]]:
                    list_added += 1
                    if legpos[r] >= 0 and pos[j] > legpos[r]:
                        after_legal += 1
                else:
                    other_added += 1
        out[p, 0], out[p, 1] = dropped, added
        out[p, 2], out[p, 3], out[p, 4] = list_added, other_added, after_legal


def composed_edits(left, right) -> pd.DataFrame:
    """Count aligned changes and label diagnostic combinations (no match decision)."""
    values = np.r_[np.asarray(left, object), np.asarray(right, object)]
    unique, inv = np.unique(values.astype(str), return_inverse=True)
    folded = _fold_texts(unique)
    seq, positions, legal_position = [], [], []
    for name in folded:  # once per distinct record text, never once per candidate pair
        name = re.sub(r"(?<=\b[a-z])\.(?=[a-z]\b)", "", name)
        words = re.findall(r"[a-z0-9]+", name)
        keep = [(i, w) for i, w in enumerate(words) if w not in _LEGAL and w not in _STOP]
        seq.append([w for _, w in keep])
        positions.extend(i for i, _ in keep)
        legal_position.append(next((i for i, w in enumerate(words) if w in _LEGAL), -1))
    flat = [w for words in seq for w in words]
    vocab, codes = np.unique(np.asarray(flat, dtype=str), return_inverse=True)
    ptr = np.r_[0, np.cumsum([len(w) for w in seq])].astype(np.int64)
    n = len(left)
    out = np.zeros((n, 5), np.int16)
    _edits(inv[:n].astype(np.int64), inv[n:].astype(np.int64), ptr, codes.astype(np.int32),
           np.asarray(positions, np.int16), np.asarray(legal_position, np.int16), vocab,
           np.isin(vocab, list(LIST_WORDS)), out)
    d = pd.DataFrame(out, columns=["dropped", "added", "list_added", "other_added", "list_after_legal"])
    family = np.full(n, "", object)
    family[(out[:, 0] == 1) & (out[:, 2] >= 1) & (out[:, 3] == 1)] = "swap_list"
    family[(out[:, 0] == 0) & (out[:, 1] >= 2) & (out[:, 1] == out[:, 2])] = "multi_append"
    family[(out[:, 0] == 1) & (out[:, 1] >= 2) & (out[:, 1] == out[:, 2])] = "drop_multi_list"
    return d.assign(combination=family)
