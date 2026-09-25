"""Token keys per record and per-country indexes for blocking (plans/FINAL_PLAN.md section 4.3).

Each record gets int64 token keys:
- base tokens: name tokens (+ the joined name), address words and address numbers, each in its own namespace;
- compound tokens, which stay rare where single tokens are common:
  (one of the first 2 numbers, one of the first 3 address words), (one of the first 2 numbers, one of the first 3
  name tokens) and unordered pairs among the first 4 name tokens.
Per country partition the keys are re-coded to a dense vocabulary with IDF weights (fitted on that partition's
S1 + S2 + S3 records, so an unseen country such as France gets its own statistics).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
from numba import njit, prange

from . import text

KIND_SHIFT = 61  # bits 61-62: compound kind (0 = base token)
A_SHIFT = 30     # bits 30-60: first code; bits 0-29: second code
MAX_CODE = 1 << 30
MAX_NAME_PAIR = 4
MAX_NUM_WORD = 3
MAX_NUM_NAME = 3
MAX_NUMS = 2


def _prefixed(values: pa.Array, prefix: str) -> pa.Array:
    values = values.cast(pa.large_string())
    return pc.binary_join_element_wise(pa.scalar(prefix, pa.large_string()), values, pa.scalar("", pa.large_string()))


@njit(cache=True)
def _group_by_row(rows, keys, n_rows):
    """Counting sort of (row, key) pairs by row -> CSR (indptr, keys)."""
    indptr = np.zeros(n_rows + 1, np.int64)
    for r in rows:
        indptr[r + 1] += 1
    for i in range(n_rows):
        indptr[i + 1] += indptr[i]
    pos = indptr[:-1].copy()
    out = np.empty(keys.size, np.int64)
    for j in range(keys.size):
        r = rows[j]
        out[pos[r]] = keys[j]
        pos[r] += 1
    return indptr, out


def _csr(rows: np.ndarray, codes: np.ndarray, n_rows: int) -> tuple[np.ndarray, np.ndarray]:
    """CSR arrays from (row, code) pairs whose rows ascend (original token order kept within a row)."""
    indptr = np.zeros(n_rows + 1, np.int64)
    np.cumsum(np.bincount(rows, minlength=n_rows), out=indptr[1:])
    return indptr, codes


@njit(cache=True)
def _count_compound(n_ptr, w_ptr, d_ptr, out):
    for i in range(out.size):
        nn = min(n_ptr[i + 1] - n_ptr[i], MAX_NAME_PAIR)
        c = nn * (nn - 1) // 2
        nd = min(d_ptr[i + 1] - d_ptr[i], MAX_NUMS)
        c += nd * (min(w_ptr[i + 1] - w_ptr[i], MAX_NUM_WORD) + min(n_ptr[i + 1] - n_ptr[i], MAX_NUM_NAME))
        out[i] = c


@njit(parallel=True, cache=True)
def _fill_compound(n_ptr, n_codes, w_ptr, w_codes, d_ptr, d_codes, c_ptr, out):
    for i in prange(c_ptr.size - 1):
        p = c_ptr[i]
        n0, nn = n_ptr[i], min(n_ptr[i + 1] - n_ptr[i], MAX_NAME_PAIR)
        for a in range(nn):
            for b in range(a + 1, nn):
                x, y = n_codes[n0 + a], n_codes[n0 + b]
                lo, hi = (x, y) if x < y else (y, x)
                out[p] = (np.int64(2) << KIND_SHIFT) | (np.int64(lo) << A_SHIFT) | np.int64(hi)
                p += 1
        for m in range(min(d_ptr[i + 1] - d_ptr[i], MAX_NUMS)):
            num = np.int64(d_codes[d_ptr[i] + m])
            for a in range(min(w_ptr[i + 1] - w_ptr[i], MAX_NUM_WORD)):
                out[p] = (np.int64(1) << KIND_SHIFT) | (num << A_SHIFT) | np.int64(w_codes[w_ptr[i] + a])
                p += 1
            for a in range(min(n_ptr[i + 1] - n_ptr[i], MAX_NUM_NAME)):
                out[p] = (np.int64(3) << KIND_SHIFT) | (num << A_SHIFT) | np.int64(n_codes[n0 + a])
                p += 1


def record_keys(names: pa.Array, addresses: pa.Array) -> tuple[np.ndarray, np.ndarray]:
    """Token keys of every record: CSR ``(indptr, keys)``, keys int64, possibly with duplicates inside a row."""
    n = len(names)
    nt = text.name_tokens(names)
    nc = text.name_concat(nt, n)
    aw = text.address_words(addresses)
    ad = text.address_numbers(addresses)
    parts = [_prefixed(nt.values, "n"), _prefixed(nc.values, "n"), _prefixed(aw.values, "a"), _prefixed(ad.values, "d")]
    enc = pc.dictionary_encode(pa.chunked_array(parts).combine_chunks())
    codes = enc.indices.to_numpy(zero_copy_only=False).astype(np.int64)
    if len(enc.dictionary) >= MAX_CODE:
        raise ValueError("token vocabulary too large for the compound-key layout")
    sizes = np.cumsum([0] + [len(p) for p in parts])
    c_nt, c_nc, c_aw, c_ad = (codes[sizes[k]:sizes[k + 1]] for k in range(4))

    n_ptr, _ = _csr(nt.rows, c_nt, n)
    w_ptr, _ = _csr(aw.rows, c_aw, n)
    d_ptr, _ = _csr(ad.rows, c_ad, n)
    counts = np.empty(n, np.int64)
    _count_compound(n_ptr, w_ptr, d_ptr, counts)
    c_ptr = np.zeros(n + 1, np.int64)
    np.cumsum(counts, out=c_ptr[1:])
    compound = np.empty(c_ptr[-1], np.int64)
    _fill_compound(n_ptr, c_nt, w_ptr, c_aw, d_ptr, c_ad, c_ptr, compound)

    rows = np.concatenate([nt.rows, nc.rows, aw.rows, ad.rows, np.repeat(np.arange(n, dtype=np.int64), counts)])
    keys = np.concatenate([c_nt, c_nc, c_aw, c_ad, compound])
    return _group_by_row(rows, keys, n)


@njit(parallel=True, cache=True)
def _sorted_unique_counts(indptr, codes, out):
    for i in prange(indptr.size - 1):
        seg = np.sort(codes[indptr[i]:indptr[i + 1]])
        c = 0
        for j in range(seg.size):
            if j == 0 or seg[j] != seg[j - 1]:
                c += 1
        out[i] = c


@njit(parallel=True, cache=True)
def _sorted_unique_fill(indptr, codes, new_ptr, out):
    for i in prange(indptr.size - 1):
        seg = np.sort(codes[indptr[i]:indptr[i + 1]])
        p = new_ptr[i]
        for j in range(seg.size):
            if j == 0 or seg[j] != seg[j - 1]:
                out[p] = seg[j]
                p += 1


def sort_unique_rows(indptr: np.ndarray, codes: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Sort each CSR row and drop duplicate codes."""
    counts = np.empty(indptr.size - 1, np.int64)
    _sorted_unique_counts(indptr, codes, counts)
    new_ptr = np.zeros(indptr.size, np.int64)
    np.cumsum(counts, out=new_ptr[1:])
    out = np.empty(new_ptr[-1], codes.dtype)
    _sorted_unique_fill(indptr, codes, new_ptr, out)
    return new_ptr, out


def take_rows(indptr: np.ndarray, values: np.ndarray, rows: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Sub-CSR with the given rows, in the given order."""
    starts, ends = indptr[rows], indptr[rows + 1]
    lens = ends - starts
    new_ptr = np.zeros(rows.size + 1, np.int64)
    np.cumsum(lens, out=new_ptr[1:])
    idx = np.repeat(starts - new_ptr[:-1], lens) + np.arange(new_ptr[-1], dtype=np.int64)
    return new_ptr, values[idx]


@njit(cache=True)
def build_postings(indptr, codes, n_codes):
    """Inverted index: for each code, the ascending rows that contain it (rows must hold unique codes)."""
    t_ptr = np.zeros(n_codes + 1, np.int64)
    for c in codes:
        t_ptr[c + 1] += 1
    for c in range(n_codes):
        t_ptr[c + 1] += t_ptr[c]
    pos = t_ptr[:-1].copy()
    docs = np.empty(codes.size, np.int32)
    for i in range(indptr.size - 1):
        for p in range(indptr[i], indptr[i + 1]):
            c = codes[p]
            docs[pos[c]] = i
            pos[c] += 1
    return t_ptr, docs


@njit(parallel=True, cache=True)
def row_norms(indptr, codes, w):
    """sqrt of the summed token weights of each row (the length of a vector with sqrt(idf) entries)."""
    out = np.empty(indptr.size - 1, np.float32)
    for i in prange(indptr.size - 1):
        s = 0.0
        for p in range(indptr[i], indptr[i + 1]):
            s += w[codes[p]]
        out[i] = np.sqrt(s) if s > 0 else 1.0
    return out


class Partition:
    """One country's S1 and S2/S3 records with a shared vocabulary, IDF weights and both inverted indexes."""

    def __init__(self, indptr: np.ndarray, keys: np.ndarray, s1_rows: np.ndarray, r_rows: np.ndarray):
        rows = np.concatenate([s1_rows, r_rows])
        ptr, sub = take_rows(indptr, keys, rows)
        local, uniq = pd.factorize(sub, sort=False)
        del sub
        ptr, local = sort_unique_rows(ptr, local.astype(np.int32))
        self.n_s1, self.n_r, self.n_codes = s1_rows.size, r_rows.size, uniq.size
        df = np.bincount(local, minlength=uniq.size)
        n_docs = self.n_s1 + self.n_r
        self.w = np.maximum(np.log(n_docs / np.maximum(df, 1)), 0.01).astype(np.float32)
        self.q_ptr_s1, self.q_s1 = ptr[: self.n_s1 + 1], local[: ptr[self.n_s1]]
        r_ptr = ptr[self.n_s1:] - ptr[self.n_s1]
        self.q_ptr_r, self.q_r = r_ptr, local[ptr[self.n_s1]:]
        self.norm_s1 = row_norms(self.q_ptr_s1, self.q_s1, self.w)
        self.norm_r = row_norms(self.q_ptr_r, self.q_r, self.w)
        self.post_r = build_postings(self.q_ptr_r, self.q_r, self.n_codes)
        self.post_s1 = build_postings(self.q_ptr_s1, self.q_s1, self.n_codes)
