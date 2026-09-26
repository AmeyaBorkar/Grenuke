"""Token keys per record and per-country indexes for blocking (plans/FINAL_PLAN.md section 4.3).

Each record gets int64 token keys:
- base tokens: name tokens (+ the joined name and consonant skeletons), address words and address numbers, each
  in its own namespace (Indic-script names are transliterated first, ber.block.indic). With ``repair``, S2/S3 names
  that are domains/handles or carry OCR digits add the S1 words they hide (ber.block.repair);
- compound tokens, which stay rare where single tokens are common:
  (one of the first 2 numbers, one of the first 3 address words), (one of the first 2 numbers, one of the first 3
  name tokens) and unordered pairs among the first 4 name tokens;
- optional name-word compounds (``name_words`` > 0): (one of the first 2 name tokens, one of the first
  ``name_words`` address words of 4+ letters). They keep a typo'd or shortened name with a number-less address
  findable ("Dynamic Nnsaq P.C. | DURHAM DR, ANDOVER" -> dynamic x durham, dynamic x andover).
Per country partition the keys are re-coded to a dense vocabulary with IDF weights (fitted on that partition's
S1 + S2 + S3 records, so an unseen country such as France gets its own statistics).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
from numba import njit, prange

from . import indic, text

KIND_SHIFT = 61  # bits 61-62: compound kind (0 = base token)
A_SHIFT = 30     # bits 30-60: first code; bits 0-29: second code
MAX_CODE = 1 << 30
MAX_NAME_PAIR = 4
MAX_NUM_WORD = 3
MAX_NUM_NAME = 3
MAX_NUMS = 2
MAX_NW_NAMES = 2
NW_MIN_LEN = 4


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


@njit(cache=True)
def _count_name_word(n_ptr, q_ptr, n_words, out):
    for i in range(out.size):
        out[i] = min(n_ptr[i + 1] - n_ptr[i], MAX_NW_NAMES) * min(q_ptr[i + 1] - q_ptr[i], n_words)


@njit(parallel=True, cache=True)
def _fill_name_word(n_ptr, n_codes, q_ptr, q_codes, n_words, c_ptr, out):
    """Kind-0 compounds: (name code + 1) in bits 30-60, so they never equal a base token (bits 30-60 zero)."""
    for i in prange(c_ptr.size - 1):
        p = c_ptr[i]
        for a in range(min(n_ptr[i + 1] - n_ptr[i], MAX_NW_NAMES)):
            x = np.int64(n_codes[n_ptr[i] + a]) + 1
            for b in range(min(q_ptr[i + 1] - q_ptr[i], n_words)):
                out[p] = (x << A_SHIFT) | np.int64(q_codes[q_ptr[i] + b])
                p += 1


def char_ngrams(tok: text.Tokens, n_rows: int, n: int) -> tuple[np.ndarray, np.ndarray]:
    """Character ``n``-grams (n <= 7) of each row's name tokens joined without spaces, as negative int64 keys (they
    never collide with token codes or compound keys, which are non-negative). "stormy cbmpbell 8rokerage" still
    shares most 4-grams with "stormy campbell brokerage"."""
    counts = np.bincount(tok.rows, minlength=n_rows)
    offsets = np.concatenate([[0], np.cumsum(counts)]).astype(np.int64)
    joined = pc.binary_join(pa.LargeListArray.from_arrays(pa.array(offsets), tok.values.cast(pa.large_string())),
                            pa.scalar("", pa.large_string()))
    off = np.frombuffer(joined.buffers()[1], np.int64)[joined.offset:joined.offset + len(joined) + 1]
    buf = np.frombuffer(joined.buffers()[2], np.uint8)
    cnt = np.maximum(np.diff(off) - n + 1, 0)
    rows = np.repeat(np.arange(n_rows, dtype=np.int64), cnt)
    first = np.cumsum(cnt) - cnt
    starts = np.repeat(off[:-1], cnt) + (np.arange(int(cnt.sum()), dtype=np.int64) - np.repeat(first, cnt))
    packed = np.zeros(starts.size, np.int64)
    for j in range(n):
        packed = packed * 256 + buf[starts + j]
    return rows, -(packed + 1)


def record_keys(names: pa.Array, addresses: pa.Array, counts_out: dict | None = None,
                name_map: dict[str, str] | None = None, name_ngrams: int = 0,
                name_words: int = 0, repair: dict | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Token keys of every record: CSR ``(indptr, keys)``, keys int64, possibly with duplicates inside a row.

    Indic-script names are transliterated first (``indic.name_tokens``: legal forms dropped, ``name_map`` applied);
    every name token of 3+ letters also adds its consonant skeleton (namespace "k"), so "मार्केटिंग" and "marketing"
    share a key. ``name_ngrams`` > 0 adds character n-grams of the name (typos; used by the name-only view).
    ``name_words`` > 0 adds the name-word compounds. ``counts_out`` receives per-record address token counts, name
    token counts and the longest name token's length (of the record's own tokens).
    ``repair`` = {"is_s1": bool per record, "country": label per record, "segment": bool, "ocr": bool} adds the
    S2/S3 name repairs of ``ber.block.repair`` (domain/handle segments, OCR-repaired words) as extra name tokens:
    they get name keys, skeletons and compounds; the joined name and the character n-grams keep the own tokens.
    """
    n = len(names)
    own, _ = indic.name_tokens(names, name_map)
    nc = text.name_concat(own, n)
    nt = own
    if repair and (repair.get("segment") or repair.get("ocr")):
        from . import repair as rp

        extra = rp.extra_name_tokens(names, own, np.asarray(repair["is_s1"], bool), np.asarray(repair["country"]),
                                     bool(repair.get("segment")), bool(repair.get("ocr")))
        nt = rp.merge(own, extra)
        if counts_out is not None:
            counts_out["repaired_tokens"] = int(extra.rows.size)
    aw = text.address_words(addresses)
    ad = text.address_numbers(addresses)
    if counts_out is not None:  # per-record counts (the name_short view needs them)
        counts_out["address_tokens"] = np.bincount(aw.rows, minlength=n) + np.bincount(ad.rows, minlength=n)
        counts_out["name_tokens"] = np.bincount(own.rows, minlength=n)
        lens = pc.utf8_length(own.values).to_numpy(zero_copy_only=False).astype(np.int64)
        maxlen = np.zeros(n, np.int64)
        np.maximum.at(maxlen, own.rows, lens)
        counts_out["name_maxlen"] = maxlen
    long = pc.greater_equal(pc.utf8_length(nt.values), 3)
    sk_values = indic.skeleton(pc.filter(nt.values, long))
    sk_rows = nt.rows[long.to_numpy(zero_copy_only=False)]
    parts = [_prefixed(nt.values, "n"), _prefixed(nc.values, "n"), _prefixed(aw.values, "a"), _prefixed(ad.values, "d"),
             _prefixed(sk_values, "k")]
    enc = pc.dictionary_encode(pa.chunked_array(parts).combine_chunks())
    codes = enc.indices.to_numpy(zero_copy_only=False).astype(np.int64)
    if len(enc.dictionary) >= MAX_CODE:
        raise ValueError("token vocabulary too large for the compound-key layout")
    sizes = np.cumsum([0] + [len(p) for p in parts])
    c_nt, c_nc, c_aw, c_ad, c_sk = (codes[sizes[k]:sizes[k + 1]] for k in range(5))

    n_ptr, _ = _csr(nt.rows, c_nt, n)
    w_ptr, _ = _csr(aw.rows, c_aw, n)
    d_ptr, _ = _csr(ad.rows, c_ad, n)
    counts = np.empty(n, np.int64)
    _count_compound(n_ptr, w_ptr, d_ptr, counts)
    c_ptr = np.zeros(n + 1, np.int64)
    np.cumsum(counts, out=c_ptr[1:])
    compound = np.empty(c_ptr[-1], np.int64)
    _fill_compound(n_ptr, c_nt, w_ptr, c_aw, d_ptr, c_ad, c_ptr, compound)

    rows = [nt.rows, nc.rows, aw.rows, ad.rows, sk_rows, np.repeat(np.arange(n, dtype=np.int64), counts)]
    keys = [c_nt, c_nc, c_aw, c_ad, c_sk, compound]
    if name_words:
        street = pa.array(sorted(set(text.STREET.values())), type=aw.values.type)
        ok = pc.and_(pc.greater_equal(pc.utf8_length(aw.values), NW_MIN_LEN),
                     pc.invert(pc.is_in(aw.values, value_set=street))).to_numpy(zero_copy_only=False)
        q_ptr, _ = _csr(aw.rows[ok], c_aw[ok], n)
        q_codes = c_aw[ok]
        nw_counts = np.empty(n, np.int64)
        _count_name_word(n_ptr, q_ptr, name_words, nw_counts)
        nw_ptr = np.zeros(n + 1, np.int64)
        np.cumsum(nw_counts, out=nw_ptr[1:])
        nw = np.empty(nw_ptr[-1], np.int64)
        _fill_name_word(n_ptr, c_nt, q_ptr, q_codes, name_words, nw_ptr, nw)
        rows.append(np.repeat(np.arange(n, dtype=np.int64), nw_counts))
        keys.append(nw)
    if name_ngrams:
        g_rows, g_keys = char_ngrams(own, n, name_ngrams)
        rows.append(g_rows)
        keys.append(g_keys)
    return _group_by_row(np.concatenate(rows), np.concatenate(keys), n)


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
