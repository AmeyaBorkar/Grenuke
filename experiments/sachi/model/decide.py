"""Ownership + decision (issue #9).

Metric per S1 (averaged over EVERY S1, singletons included):
    T empty: 1 if P empty else 0;  P empty & T non-empty: 0;
    else F = 1.25*|P&T| / (0.25*|T| + |P|)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

try:
    from numba import njit
except ImportError:
    def njit(*a, **k):
        return (lambda f: f) if not (a and callable(a[0])) else a[0]


def argmax_ownership(scores, p_col="p"):
    """Keep each record only under its highest-p S1."""
    s = scores.sort_values(["r_eid", p_col, "s1_eid"], ascending=[True, False, True])
    return s.drop_duplicates("r_eid", keep="first")


class EvalIndex:
    def __init__(self, s1_all, truth):
        self.s1_all = np.asarray(s1_all)
        self.pos = pd.Index(self.s1_all)
        t = truth[truth["s1_eid"].isin(self.pos)]
        self.T = np.bincount(self.pos.get_indexer(t["s1_eid"]),
                             minlength=len(self.s1_all)).astype(np.float64)
        self._truth = t[["s1_eid", "r_eid"]].drop_duplicates()

    def label(self, df):
        m = df[["s1_eid", "r_eid"]].merge(self._truth.assign(_y=True),
                                          on=["s1_eid", "r_eid"], how="left")
        return m["_y"].notna().to_numpy()

    def per_entity_f(self, s1_idx, keep, y):
        n = len(self.s1_all)
        npred = np.bincount(s1_idx[keep], minlength=n).astype(np.float64)
        c = np.bincount(s1_idx[keep & y], minlength=n).astype(np.float64)
        T = self.T
        f = np.where(T == 0, (npred == 0).astype(np.float64), 0.0)
        m = (T > 0) & (npred > 0)
        f[m] = 1.25 * c[m] / (0.25 * T[m] + npred[m])
        return f


def f_vector(pred, ev):
    idx = ev.pos.get_indexer(pred["s1_eid"])
    if (idx < 0).any():
        raise ValueError("prediction contains S1 ids outside the evaluated split")
    return ev.per_entity_f(idx, np.ones(len(pred), bool), ev.label(pred))


def tune_threshold(owned, ev, p_col="p", grid=np.round(np.arange(0.30, 0.96, 0.01), 2)):
    idx = ev.pos.get_indexer(owned["s1_eid"])
    y = ev.label(owned)
    p = owned[p_col].to_numpy()
    res = [(t, ev.per_entity_f(idx, p >= t, y).mean()) for t in grid]
    best_t, best_f = max(res, key=lambda r: r[1])
    return float(best_t), float(best_f), pd.DataFrame(res, columns=["t", "macro_f05"])


def apply_threshold(owned, t, p_col="p"):
    return owned[owned[p_col] >= t]


@njit(cache=True)
def _expected_f_best_k(p, beta2):
    n = p.shape[0]
    B = np.zeros((n + 1, n + 1))
    B[n, 0] = 1.0
    for k in range(n - 1, -1, -1):
        pk = p[k]
        for j in range(n - k + 1):
            v = B[k + 1, j] * (1.0 - pk)
            if j > 0:
                v += B[k + 1, j - 1] * pk
            B[k, j] = v
    A = np.zeros(n + 1)
    A[0] = 1.0
    best_k = 0
    best_v = B[0, 0]
    for k in range(1, n + 1):
        pk = p[k - 1]
        for a in range(k, 0, -1):
            A[a] = A[a] * (1.0 - pk) + A[a - 1] * pk
        A[0] = A[0] * (1.0 - pk)
        v = 0.0
        for a in range(1, k + 1):
            if A[a] == 0.0:
                continue
            s = 0.0
            for b in range(n - k + 1):
                s += B[k, b] * (1.0 + beta2) * a / (beta2 * (a + b) + k)
            v += A[a] * s
        if v > best_v:
            best_v = v
            best_k = k
    return best_k


@njit(cache=True)
def _dp_all(p_sorted, offsets, cap, beta2):
    keep = np.zeros(p_sorted.shape[0], dtype=np.bool_)
    for e in range(offsets.shape[0] - 1):
        lo, hi = offsets[e], offsets[e + 1]
        n = min(hi - lo, cap)
        if n == 0:
            continue
        k = _expected_f_best_k(p_sorted[lo:lo + n], beta2)
        for i in range(k):
            keep[lo + i] = True
    return keep


def _shift(p, b):
    if b == 0:
        return p
    z = np.log(np.clip(p, 1e-6, 1 - 1e-6) / np.clip(1 - p, 1e-6, 1))
    return 1.0 / (1.0 + np.exp(-(z + b)))


def dp_decide(owned, p_col="p", b=0.0, cap=30, beta2=0.25):
    s = owned.sort_values(["s1_eid", p_col], ascending=[True, False]).reset_index(drop=True)
    p = _shift(s[p_col].to_numpy(np.float64), b)
    ids = s["s1_eid"].to_numpy()
    starts = np.flatnonzero(np.r_[True, ids[1:] != ids[:-1]])
    offsets = np.r_[starts, len(s)].astype(np.int64)
    keep = _dp_all(p, offsets, cap, beta2)
    return s[keep]


def tune_shift(owned, ev, p_col="p", grid=np.round(np.arange(-1.5, 1.51, 0.25), 2)):
    res = [(b, f_vector(dp_decide(owned, p_col, b), ev).mean()) for b in grid]
    best_b, best_f = max(res, key=lambda r: r[1])
    return float(best_b), float(best_f), pd.DataFrame(res, columns=["b", "macro_f05"])


def paired_bootstrap(f_base, f_cand, n_boot=1000, seed=0, min_delta=0.002):
    f_base, f_cand = np.asarray(f_base), np.asarray(f_cand)
    d = f_cand - f_base
    rng = np.random.default_rng(seed)
    n = len(d)
    boots = np.array([d[rng.integers(0, n, n)].mean() for _ in range(n_boot)])
    lo, hi = np.percentile(boots, [2.5, 97.5])
    delta = float(d.mean())
    return {"delta": delta, "ci_low": float(lo), "ci_high": float(hi),
            "keep": bool(delta >= min_delta and lo > 0)}
