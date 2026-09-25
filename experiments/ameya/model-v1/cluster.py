"""Cluster support (gate G9, FINAL_PLAN section 4.6) for stage 2: does the record resemble the S1's confident records?

For each stage-2 pair (s, r), over the S1's other candidates r' with p1(s, r') >= CONF: the best IDF-weighted
Jaccard between r and r' on name tokens and on address words, and the best p1(s, r') * mean(name, address).
An S2 record with an invented brand name, or an Indic name the dictionary misses, often sits next to a confident
sibling record of the same S1 that shares its exact address or name form.
"""
from __future__ import annotations

import numpy as np
from numba import njit, prange

CONF = 0.5
NAMES = ("s2__cs_name", "s2__cs_addr", "s2__cs_pw", "s2__cs_n")


@njit(cache=True)
def _jac(ptr, codes, wt, wsum, a, b):
    i, i1 = ptr[a], ptr[a + 1]
    j, j1 = ptr[b], ptr[b + 1]
    s = 0.0
    while i < i1 and j < j1:
        x, y = codes[i], codes[j]
        if x == y:
            s += wt[i]
            i += 1
            j += 1
        elif x < y:
            i += 1
        else:
            j += 1
    u = wsum[a] + wsum[b] - s
    return s / u if u > 0 else 0.0


@njit(parallel=True, cache=True)
def _support(q_row, q_grp, g_ptr, g_row, g_p, n_ptr, n_codes, n_wt, n_wsum, w_ptr, w_codes, w_wt, w_wsum, out):
    for k in prange(q_row.size):
        g = q_grp[k]
        if g < 0:
            continue
        r = q_row[k]
        bn = 0.0
        bw = 0.0
        bp = 0.0
        cnt = 0
        for t in range(g_ptr[g], g_ptr[g + 1]):
            r2 = g_row[t]
            if r2 == r:
                continue
            cnt += 1
            jn = _jac(n_ptr, n_codes, n_wt, n_wsum, r, r2)
            jw = _jac(w_ptr, w_codes, w_wt, w_wsum, r, r2)
            if jn > bn:
                bn = jn
            if jw > bw:
                bw = jw
            pw = g_p[t] * 0.5 * (jn + jw)
            if pw > bp:
                bp = pw
        out[0, k] = bn
        out[1, k] = bw
        out[2, k] = bp
        out[3, k] = cnt


def support(rec: dict, s1: np.ndarray, r: np.ndarray, p1: np.ndarray, rows: np.ndarray) -> dict[str, np.ndarray]:
    """Cluster-support features for the pairs where ``rows`` is True (in row order)."""
    conf = p1 >= CONF
    cs1, cr, cp = s1[conf], rec["row_of"].get_indexer(r[conf]).astype(np.int64), p1[conf].astype(np.float64)
    order = np.argsort(cs1, kind="stable")
    cs1, cr, cp = cs1[order], cr[order], cp[order]
    groups, g_start = np.unique(cs1, return_index=True)
    g_ptr = np.append(g_start, cs1.size).astype(np.int64)
    q_grp = np.searchsorted(groups, s1[rows])
    q_grp = np.where((q_grp < groups.size) & (groups[np.minimum(q_grp, groups.size - 1)] == s1[rows]), q_grp, -1)
    q_row = rec["row_of"].get_indexer(r[rows]).astype(np.int64)
    out = np.zeros((len(NAMES), q_row.size), np.float32)
    nm, wd = rec["name"], rec["word"]
    _support(q_row, q_grp.astype(np.int64), g_ptr, cr, cp, nm["ptr"], nm["codes"], nm["wt"], nm["wsum"],
             wd["ptr"], wd["codes"], wd["wt"], wd["wsum"], out)
    return {name: out[i] for i, name in enumerate(NAMES)}
