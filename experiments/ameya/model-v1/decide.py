"""Ownership + decision (FINAL_PLAN sections 2 and 4.7, gate G6): global threshold vs exact expected-F0.5 per S1.

    python experiments/ameya/model-v1/decide.py --scores ameya-s2-v1 --col pc --tag ameya-model-v1

- Ownership: each record stays only under its highest-p S1 (argmax, v0 rule).
- Threshold: one global threshold on p, tuned on the holdout.
- Expected F0.5 (DP): per S1, candidates sorted by q = sigmoid(logit(p) + shift). Under independence the best set
  is a prefix of the owned candidates; for every prefix length k the expected F0.5 is
      E[F_k] = sum_{i in top k} q_i * E[1.25 / (0.25 * (1 + S_-i) + k)],   E[F_0] = P(S = 0),
  where S_-i (Poisson binomial) counts the true matches among all the S1's other candidates (owned or not). One
  global shift is tuned on the holdout. Candidates with q < Q_MIN are ignored (at most MAX_C per S1).
- The paired bootstrap (ber.eval.gates) decides between the two; ties go to the threshold (G6 rule).
Writes C9 matches work/matches/<tag>/{train,test}.parquet and a report with per-country numbers and test diagnostics.
"""
from __future__ import annotations

import argparse
import json
import logging
import time

import numpy as np
import pandas as pd
from numba import get_num_threads, get_thread_id, njit, prange

from ber.artifacts import read_table, write_report, write_table
from ber.eval.gates import compare
from ber.eval.metric import per_entity_f05
from ber.records import load_truth
from common import FastEval, argmax_owner, holdout_report, holdout_universe

log = logging.getLogger("decide")
Q_MIN = 1e-3
MAX_C = 48
MAX_K = 16


@njit(parallel=True, cache=True)
def _expected_f(starts, order, q, own, scratch, sel, best_ef):
    """For each S1 group (``order`` sorted by q descending inside the group), mark the best prefix of owned pairs."""
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
        # E[F_0] = P(no true match among the candidates)
        p0 = 1.0
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
            # Poisson-binomial pmf of the other candidates
            for s in range(n + 1):
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


def expected_f_select(s1: np.ndarray, p: np.ndarray, own: np.ndarray, shift: float) -> np.ndarray:
    pc = np.clip(p.astype(np.float64), 1e-7, 1 - 1e-7)
    q = 1.0 / (1.0 + np.exp(-(np.log(pc / (1 - pc)) + shift)))
    order = np.lexsort((-q, s1))
    k = s1[order]
    starts = np.append(np.flatnonzero(np.r_[True, k[1:] != k[:-1]]), k.size).astype(np.int64)
    scratch = np.zeros((get_num_threads(), 3, MAX_C + 2), np.float64)
    sel = np.zeros(p.size, np.bool_)
    best_ef = np.zeros(starts.size - 1, np.float64)
    _expected_f(starts, order.astype(np.int64), q, own, scratch, sel, best_ef)
    return sel


def diagnostics(pred: pd.DataFrame, s1: np.ndarray, p: np.ndarray, own: np.ndarray, country: pd.Series,
                universe: np.ndarray) -> dict:
    """Per country (G8): predicted matches per S1, share of S1 left empty, share of owned pairs above 0.5 and 0.9
    per S1, mean owned p per S1 (sum of p over owned pairs / S1)."""
    uni = pd.Index(universe)
    c_of = country.reindex(uni)
    n_s1 = c_of.value_counts()
    pr = pred[pred["s1"].isin(uni)]
    pc_ = country.reindex(pr["s1"]).to_numpy()
    m = own & np.isin(s1, universe)
    cp = country.reindex(s1[m]).to_numpy()
    out = {}
    for c in n_s1.index:
        sel = cp == c
        out[str(c)] = {
            "pred_per_s1": round(float((pc_ == c).sum() / n_s1[c]), 4),
            "empty_share": round(1 - pr.loc[pc_ == c, "s1"].nunique() / n_s1[c], 4),
            "owned_p50_per_s1": round(float((p[m][sel] > 0.5).sum() / n_s1[c]), 4),
            "owned_p90_per_s1": round(float((p[m][sel] > 0.9).sum() / n_s1[c]), 4),
            "owned_psum_per_s1": round(float(p[m][sel].sum() / n_s1[c]), 4),
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores", default="ameya-s2-v1")
    ap.add_argument("--col", default="pc")
    ap.add_argument("--tag", default="ameya-model-v1")
    ap.add_argument("--base", default="ameya-baseline-v0")
    ap.add_argument("--no-test", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    command = "python experiments/ameya/model-v1/decide.py " + " ".join(f"--{k.replace('_', '-')} {v}" for k, v in vars(args).items())
    t0 = time.perf_counter()

    sc = read_table("scores", args.scores, "train", ["s1", "r", args.col])
    s1, r, p = sc["s1"].to_numpy(), sc["r"].to_numpy(), sc[args.col].to_numpy(np.float32)
    truth = load_truth()
    universe, country = holdout_universe()
    th = truth[truth["s1"].isin(universe)]
    hold = np.isin(s1, universe)
    own = argmax_owner(s1, r, p)

    fe = FastEval(s1, r, truth, universe)
    f05 = fe.score

    thr = [(float(t), f05(own & (p > t))) for t in np.round(np.arange(0.30, 0.951, 0.025), 3)]
    t_best, f_thr = max(thr, key=lambda x: x[1])
    log.info("threshold %.3f -> %.5f (%.0fs)", t_best, f_thr, time.perf_counter() - t0)
    hs1, hp, hown = s1[hold], p[hold], own[hold]
    dp = []
    for shift in (-1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0):
        sel = np.zeros(p.size, bool)
        sel[hold] = expected_f_select(hs1, hp, hown, shift)
        dp.append((shift, f05(sel)))
        log.info("expected-F0.5 shift %+.2f -> %.5f", *dp[-1])
    s_best, f_dp = max(dp, key=lambda x: x[1])

    pred_thr = sc.loc[own & (p > t_best), ["s1", "r"]]
    pred_dp = sc.loc[expected_f_select(s1, p, own, s_best), ["s1", "r"]]
    gate = compare(pred_thr, pred_dp, th, universe, groups=country)
    use_dp = gate["delta"] > 0 and gate["ci_low"] > 0
    pred = pred_dp if use_dp else pred_thr
    rule = {"method": "expected_f05" if use_dp else "threshold", "threshold": t_best, "shift": s_best}
    log.info("G6 expected-F0.5 vs threshold: %+.5f CI [%.5f, %.5f] -> %s", gate["delta"], gate["ci_low"],
             gate["ci_high"], rule["method"])
    base = read_table("matches", args.base, "train")
    gate_base = compare(base, pred, th, universe, groups=country)
    rep = holdout_report(pred, truth, universe, country)
    write_table(pred.reset_index(drop=True), "matches", args.tag, "train", command=command,
                inputs={"scores": args.scores}, rule=rule)
    payload = {"rule": rule, "holdout": rep, "threshold_grid": thr, "dp_grid": dp, "g6_dp_vs_threshold": gate,
               "gate_vs_base": gate_base}
    payload["diagnostics"] = {"holdout": diagnostics(pred, s1, p, own, country, universe)}

    if not args.no_test:
        st = read_table("scores", args.scores, "test", ["s1", "r", args.col])
        s1t, rt, pt = st["s1"].to_numpy(), st["r"].to_numpy(), st[args.col].to_numpy(np.float32)
        own_t = argmax_owner(s1t, rt, pt)
        sel_t = expected_f_select(s1t, pt, own_t, s_best) if use_dp else own_t & (pt > t_best)
        mt = st.loc[sel_t, ["s1", "r"]].reset_index(drop=True)
        write_table(mt, "matches", args.tag, "test", command=command, inputs={"scores": args.scores}, rule=rule)
        _, ct = holdout_universe("test")
        payload["diagnostics"]["test"] = diagnostics(mt, s1t, pt, own_t, ct, ct.index.to_numpy())
        log.info("diagnostics: %s", json.dumps(payload["diagnostics"], default=str))
    payload["runtime_s"] = round(time.perf_counter() - t0)
    write_report(args.tag, payload, command=command, inputs={"scores": args.scores})
    print(json.dumps({k: payload[k] for k in payload if k not in ("threshold_grid",)}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
