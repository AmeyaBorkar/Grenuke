"""Exact top-k token-overlap search (numba), used in both directions: S1 -> S2/S3 and S2/S3 -> S1.

score(q, d) = sum of idf over tokens shared by q and d / (norm(q) * norm(d)), where norm = sqrt(sum of idf of the
record's tokens): the cosine of binary token vectors with sqrt(idf) weights.
Candidates are seeded by the query's rarer tokens (posting list <= seed_cap), which keeps the work per query small.
The best ``n_verify`` seeded candidates (by partial score) are then re-scored exactly: the query's common tokens are
looked up in each candidate's sorted token list, so a shared "dental care" or "delhi" still counts in the ranking.
Queries that share no rare token with anything get no candidates.
"""
from __future__ import annotations

import numba
import numpy as np
from numba import njit, prange


@njit(cache=True)
def _heap_push(hs, hd, size, k, s, d):
    """Keep the ``k`` largest scores in a min-heap; returns the new size."""
    if size < k:
        pos = size
        size += 1
        while pos > 0:
            par = (pos - 1) >> 1
            if hs[par] <= s:
                break
            hs[pos] = hs[par]
            hd[pos] = hd[par]
            pos = par
        hs[pos] = s
        hd[pos] = d
    elif s > hs[0]:
        pos = 0
        while True:
            c = 2 * pos + 1
            if c >= k:
                break
            if c + 1 < k and hs[c + 1] < hs[c]:
                c += 1
            if hs[c] >= s:
                break
            hs[pos] = hs[c]
            hd[pos] = hd[c]
            pos = c
        hs[pos] = s
        hd[pos] = d
    return size


@njit(cache=True)
def _contains(codes, lo, hi, t):
    """Binary search for ``t`` in the sorted slice codes[lo:hi]."""
    while lo < hi:
        mid = (lo + hi) >> 1
        v = codes[mid]
        if v < t:
            lo = mid + 1
        elif v > t:
            hi = mid
        else:
            return True
    return False


@njit(parallel=True, cache=True)
def _topk(q_ptr, q_codes, q_norm, t_ptr, t_docs, d_ptr, d_codes, d_norm, w, k, seed_cap, n_verify, n_docs, n_blocks):
    nq = q_ptr.size - 1
    out_i = np.full((nq, k), -1, np.int32)
    out_s = np.zeros((nq, k), np.float32)
    block = (nq + n_blocks - 1) // n_blocks
    for b in prange(n_blocks):
        lo = b * block
        hi = min(nq, lo + block)
        if lo >= hi:
            continue
        acc = np.zeros(n_docs, np.float32)
        touched = np.empty(n_docs, np.int32)
        vs = np.empty(n_verify, np.float32)
        vd = np.empty(n_verify, np.int32)
        hs = np.empty(k, np.float32)
        hd = np.empty(k, np.int32)
        for q in range(lo, hi):
            nt = 0
            n_common = 0
            for p in range(q_ptr[q], q_ptr[q + 1]):
                t = q_codes[p]
                a, e = t_ptr[t], t_ptr[t + 1]
                if e - a > seed_cap:
                    n_common += 1
                    continue
                wt = w[t]
                for pp in range(a, e):
                    d = t_docs[pp]
                    if acc[d] == 0.0:
                        touched[nt] = d
                        nt += 1
                    acc[d] += wt
            # the best n_verify seeded candidates by partial score
            nv = 0
            for j in range(nt):
                d = touched[j]
                nv = _heap_push(vs, vd, nv, n_verify, acc[d] / d_norm[d], d)
            # exact score: add the common tokens the candidate also has
            size = 0
            inv = 1.0 / q_norm[q]
            for j in range(nv):
                d = vd[j]
                full = acc[d]
                if n_common > 0:
                    for p in range(q_ptr[q], q_ptr[q + 1]):
                        t = q_codes[p]
                        if t_ptr[t + 1] - t_ptr[t] > seed_cap and _contains(d_codes, d_ptr[d], d_ptr[d + 1], t):
                            full += w[t]
                size = _heap_push(hs, hd, size, k, full * inv / d_norm[d], d)
            for j in range(nt):
                acc[touched[j]] = 0.0
            order = np.argsort(-hs[:size], kind="mergesort")
            for r in range(size):
                out_i[q, r] = hd[order[r]]
                out_s[q, r] = hs[order[r]]
    return out_i, out_s


def topk(q_ptr: np.ndarray, q_codes: np.ndarray, q_norm: np.ndarray, postings: tuple[np.ndarray, np.ndarray],
         docs: tuple[np.ndarray, np.ndarray], d_norm: np.ndarray, w: np.ndarray, k: int, seed_cap: int,
         n_verify: int = 200) -> tuple[np.ndarray, np.ndarray]:
    """Top-``k`` documents per query row: (indices int32 with -1 padding, scores float32), best first.

    ``postings`` is the documents' inverted index; ``docs`` their CSR rows with sorted, unique token codes.
    """
    t_ptr, t_docs = postings
    d_ptr, d_codes = docs
    n_blocks = max(1, min(q_ptr.size - 1, numba.get_num_threads() * 16))
    return _topk(q_ptr, q_codes, q_norm.astype(np.float32), t_ptr, t_docs, d_ptr, d_codes,
                 d_norm.astype(np.float32), w.astype(np.float32), int(k), int(seed_cap), int(max(n_verify, k)),
                 int(d_norm.size), int(n_blocks))
