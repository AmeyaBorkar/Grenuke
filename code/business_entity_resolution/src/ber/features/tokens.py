"""Aligned token-set features using CSR arrays and a compiled pair kernel.

Vocabulary construction loops over unique tokens, never over candidate pairs.
The kernel absorbs short spelling edits when counting extra business words.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np
import pandas as pd


@lru_cache(maxsize=1)
def _kernel():
    from numba import njit, prange

    @njit
    def near(a, b, letters, lengths):
        na, nb = lengths[a], lengths[b]
        if na == 0 or nb == 0 or abs(na - nb) > 2:
            return False
        previous = np.arange(nb + 1, dtype=np.int16)
        current = np.empty(nb + 1, dtype=np.int16)
        for i in range(1, na + 1):
            current[0] = i
            row_min = current[0]
            for j in range(1, nb + 1):
                cost = 0 if letters[a, i - 1] == letters[b, j - 1] else 1
                current[j] = min(previous[j] + 1, current[j - 1] + 1,
                                 previous[j - 1] + cost)
                row_min = min(row_min, current[j])
            if row_min > 2:
                return False
            previous, current = current, previous
        return previous[nb] <= 2

    @njit(parallel=True)
    def calculate(indptr, indices, idf, letters, lengths, n, absorb):
        out = np.zeros((n, 12), dtype=np.float32)
        for pair in prange(n):
            ls, le = indptr[pair], indptr[pair + 1]
            rs, re = indptr[pair + n], indptr[pair + n + 1]
            nl, nr = le - ls, re - rs
            common = 0
            common_w = 0.0
            common_w2 = 0.0
            wl, wr, wl2, wr2 = 0.0, 0.0, 0.0, 0.0
            for i in range(ls, le):
                a = indices[i]
                wl += idf[a]
                wl2 += idf[a] * idf[a]
                exact = False
                close = False
                for j in range(rs, re):
                    b = indices[j]
                    if a == b:
                        exact = True
                        break
                    if absorb and not close and near(a, b, letters, lengths):
                        close = True
                if exact:
                    common += 1
                    common_w += idf[a]
                    common_w2 += idf[a] * idf[a]
                elif close:
                    out[pair, 11] = 1.0
                else:
                    out[pair, 5] += 1.0
                    out[pair, 6] += idf[a]
                    out[pair, 7] = max(out[pair, 7], idf[a])
            for j in range(rs, re):
                b = indices[j]
                wr += idf[b]
                wr2 += idf[b] * idf[b]
                exact = False
                close = False
                for i in range(ls, le):
                    a = indices[i]
                    if a == b:
                        exact = True
                        break
                    if absorb and not close and near(a, b, letters, lengths):
                        close = True
                if not exact and not close:
                    out[pair, 8] += 1.0
                    out[pair, 9] += idf[b]
                    out[pair, 10] = max(out[pair, 10], idf[b])
            union = nl + nr - common
            out[pair, 0] = common / union if union else np.nan
            out[pair, 1] = common / nl if nl else np.nan
            out[pair, 2] = common / nr if nr else np.nan
            out[pair, 3] = common_w2 / np.sqrt(wl2 * wr2) if wl2 and wr2 else np.nan
            out[pair, 4] = common_w / (wl + wr - common_w) if wl + wr > common_w else np.nan
        return out

    return calculate


def token_features(left: list[str], right: list[str], idf_lookup: dict[str, float] | None = None,
                   *, absorb_typos: bool = False) -> np.ndarray:
    """Return jaccard, containment, IDF overlap and extra-token stats per pair."""
    from sklearn.feature_extraction.text import CountVectorizer

    n = len(left)
    if n == 0:
        return np.empty((0, 12), dtype=np.float32)
    vectorizer = CountVectorizer(binary=True, lowercase=False,
                                 token_pattern=r"(?u)\b[a-z0-9]+\b", dtype=np.int8)
    corpus = np.concatenate([np.asarray(left, dtype=object), np.asarray(right, dtype=object)])
    codes, unique_text = pd.factorize(corpus, sort=False)
    try:
        # A candidate list repeats S1 text across its neighbors. Tokenize each
        # distinct text once and gather the aligned pair rows from sparse CSR.
        matrix = vectorizer.fit_transform(unique_text)[codes]
    except ValueError as exc:
        if "empty vocabulary" not in str(exc):
            raise
        result = np.full((n, 12), np.nan, dtype=np.float32)
        result[:, 5:12] = 0
        return result
    words = vectorizer.get_feature_names_out()
    fallback = np.float32(
        idf_lookup.get("__default__", np.log1p(2 * n)) if idf_lookup is not None
        else np.log1p(2 * n)
    )
    if idf_lookup is None:
        document_frequency = np.asarray((matrix > 0).sum(axis=0)).ravel()
        idf = np.log((2 * n + 1) / (document_frequency + 1)).astype(np.float32) + 1
    else:
        idf = np.fromiter((idf_lookup.get(word, fallback) for word in words),
                          dtype=np.float32, count=len(words))
    letters = np.zeros((len(words), 40), dtype=np.uint8)
    lengths = np.zeros(len(words), dtype=np.int16)
    if absorb_typos:
        for i, word in enumerate(words):  # unique vocabulary words, not pairs
            encoded = word.encode("ascii", "ignore")[:40]
            letters[i, :len(encoded)] = np.frombuffer(encoded, dtype=np.uint8)
            lengths[i] = len(encoded)
    return _kernel()(matrix.indptr.astype(np.int64, copy=False),
                     matrix.indices.astype(np.int32, copy=False),
                     idf, letters, lengths, n, absorb_typos)
