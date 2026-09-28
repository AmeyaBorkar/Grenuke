"""Core helpers: holdout tables, fast per-entity F0.5, decision rules (threshold, rank-aware, expected-F0.5 DP)."""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
from numba import get_num_threads, get_thread_id, njit, prange

D = os.path.dirname(os.path.abspath(__file__))
Q_MIN = 1e-3
MAX_C = 48
MAX_K = 16


# ----------------------------------------------------------------------------------------------------------------
# data
# ----------------------------------------------------------------------------------------------------------------
class Hold:
    """Holdout rows (p > 0, candidate cut applied, ownership over all train S1) + universe + fast evaluator."""

    def __init__(self, tag: str = "ameya-s3-v7nst"):
        h = pd.read_parquet(os.path.join(D, f"hold_{tag}.parquet"))
        u = pd.read_parquet(os.path.join(D, "universe.parquet"))
        th = pd.read_parquet(os.path.join(D, "truth_hold.parquet"))
        # sort rows by (s1, -p) once: every rule below works on S1 groups sorted by p descending
        order = np.lexsort((-h["p"].to_numpy(), h["s1"].to_numpy()))
        h = h.iloc[order].reset_index(drop=True)
        self.s1 = h["s1"].to_numpy()
        self.r = h["r"].to_numpy()
        self.p = h["p"].to_numpy().astype(np.float64)
        self.own = h["own"].to_numpy()
        self.riv = h["riv"].to_numpy().astype(np.float64)
        self.y = h["y"].to_numpy() if "y" in h else None
        self.u = u
        self.U = u["s1"].to_numpy()
        self.idx = np.searchsorted(self.U, self.s1)
        assert np.all(self.U[self.idx] == self.s1)
        key = self.s1 * 4_000_000_000 + self.r
        self.hit = np.isin(key, th["s1"].to_numpy() * 4_000_000_000 + th["r"].to_numpy()).astype(np.float64)
        self.n_true = u["n_true"].to_numpy().astype(np.float64)
        self.half = u["half"].to_numpy()
        self.country = u["country"].to_numpy()
        self.row_country = self.country[self.idx]
        self.row_half = self.half[self.idx]
        k = self.s1
        self.starts = np.append(np.flatnonzero(np.r_[True, k[1:] != k[:-1]]), k.size).astype(np.int64)
        # rank of each owned row among its S1's owned rows (0 = highest p)
        grp_start = np.repeat(self.starts[:-1], np.diff(self.starts))
        ocum = np.cumsum(self.own.astype(np.int64))
        base = np.where(grp_start > 0, ocum[grp_start - 1], 0)
        self.own_rank = np.where(self.own, ocum - base - 1, -1)
        self.masks = {"A": self.half == 0, "B": self.half == 1, "full": np.ones(self.U.size, bool)}
        for c in ("US", "India"):
            self.masks[c] = self.country == c
            self.masks[f"A_{c}"] = (self.half == 0) & (self.country == c)
            self.masks[f"B_{c}"] = (self.half == 1) & (self.country == c)

    def per_entity(self, sel: np.ndarray) -> np.ndarray:
        n_pred = np.bincount(self.idx[sel], minlength=self.U.size)
        n_hit = np.bincount(self.idx[sel], weights=self.hit[sel], minlength=self.U.size)
        denom = 0.25 * self.n_true + n_pred
        return np.where(denom > 0, 1.25 * n_hit / np.where(denom > 0, denom, 1.0), 1.0)

    def summary(self, f: np.ndarray) -> dict:
        return {k: float(f[m].mean()) for k, m in self.masks.items()}


# ----------------------------------------------------------------------------------------------------------------
# expected-F0.5 DP (copy of decide.py's _expected_f with an extra 'phantom' term: lam = expected true matches outside
# the candidate list, modelled as one extra never-predictable candidate with probability lam)
# ----------------------------------------------------------------------------------------------------------------
@njit(parallel=True, cache=False)
def _expected_f(starts, order, q, own, scratch, sel, best_ef, lam):
    for g in prange(starts.size - 1):
        a, b = starts[g], starts[g + 1]
        tid = get_thread_id()
        qs = scratch[tid, 0]
        pmf = scratch[tid, 1]
        ef = scratch[tid, 2]
        n = 0
        for k in range(a, b):
            v = q[order[k]]
            if v < Q_MIN or n >= MAX_C:
                break
            qs[n] = v
            n += 1
        p0 = 1.0 - lam
        for j in range(n):
            p0 *= 1.0 - qs[j]
        n_el = 0
        for k in range(n):
            if own[order[a + k]]:
                n_el += 1
        kmax = min(n_el, MAX_K)
        for k in range(kmax + 1):
            ef[k] = 0.0
        ef[0] = p0
        rank = 0
        for k in range(n):
            if rank >= kmax:
                break
            if not own[order[a + k]]:
                continue
            for s in range(n + 2):
                pmf[s] = 0.0
            pmf[0] = 1.0
            m = 0
            for j in range(n):
                if j == k:
                    continue
                qj = qs[j]
                for s in range(m + 1, 0, -1):
                    pmf[s] = pmf[s] * (1.0 - qj) + pmf[s - 1] * qj
                pmf[0] *= 1.0 - qj
                m += 1
            if lam > 0.0:
                for s in range(m + 1, 0, -1):
                    pmf[s] = pmf[s] * (1.0 - lam) + pmf[s - 1] * lam
                pmf[0] *= 1.0 - lam
                m += 1
            for kk in range(rank + 1, kmax + 1):
                e = 0.0
                for s in range(m + 1):
                    e += pmf[s] / (0.25 * (1.0 + s) + kk)
                ef[kk] += 1.25 * qs[k] * e
            rank += 1
        best_k = 0
        for kk in range(1, kmax + 1):
            if ef[kk] > ef[best_k]:
                best_k = kk
        best_ef[g] = ef[best_k]
        rank = 0
        for k in range(n):
            if rank >= best_k:
                break
            if own[order[a + k]]:
                sel[order[a + k]] = True
                rank += 1


def to_q(p: np.ndarray, shift) -> np.ndarray:
    pc = np.clip(p.astype(np.float64), 1e-7, 1 - 1e-7)
    return 1.0 / (1.0 + np.exp(-(np.log(pc / (1 - pc)) + shift)))


def expected_f_select(s1: np.ndarray, q: np.ndarray, own: np.ndarray, lam: float = 0.0, with_ef: bool = False):
    """Rows must be grouped by s1; q = calibrated probabilities (already shifted)."""
    order = np.lexsort((-q, s1))
    k = s1[order]
    starts = np.append(np.flatnonzero(np.r_[True, k[1:] != k[:-1]]), k.size).astype(np.int64)
    scratch = np.zeros((get_num_threads(), 3, MAX_C + 3), np.float64)
    sel = np.zeros(q.size, np.bool_)
    best_ef = np.zeros(starts.size - 1, np.float64)
    _expected_f(starts, order.astype(np.int64), q, own, scratch, sel, best_ef, float(lam))
    if with_ef:
        return sel, pd.Series(best_ef, index=k[starts[:-1]])
    return sel


# ----------------------------------------------------------------------------------------------------------------
# simple rules
# ----------------------------------------------------------------------------------------------------------------
def rank_threshold(p: np.ndarray, own: np.ndarray, own_rank: np.ndarray, idx: np.ndarray, n_u: int,
                   t_first: float, t_rest: float) -> np.ndarray:
    """Prefix rule on owned pairs sorted by p: the S1's best owned pair needs p > t_first; the others need
    p > t_rest and the best one selected. (rows sorted by p desc inside S1, own_rank 0 = best owned)."""
    first = own & (own_rank == 0) & (p > t_first)
    ok = np.zeros(n_u, bool)
    ok[idx[first]] = True
    return first | (own & (own_rank > 0) & (p > t_rest) & ok[idx])


def greedy_perfect(q: np.ndarray, own: np.ndarray, own_rank: np.ndarray, off: float = 0.0) -> np.ndarray:
    """Add the k-th owned pair (k = own_rank + 1) iff q > (5(k-1)+1)/(6.25(k-1)+2) (+ off): the exact break-even
    when the pairs already chosen are certain and no other true match exists (0.5, 0.727, 0.759, ... -> 0.8)."""
    k = np.maximum(own_rank, 0).astype(np.float64)
    t = (5 * k + 1) / (6.25 * k + 2) + off
    return own & (q > t)
