"""Task 2-3: candidate rules on the v7nst holdout, deltas on the full holdout and on halves A/B (splitmix64(s1) % 2)."""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
import pandas as pd

from base import D, THR, Eval, fmt_gate, gate, universe_and_truth
from feats import build, group_rank

CAP = {2: 5, 3: 6}
TOTAL_CAP = 11


def one_owner(d, m):
    """Keep, per record, only the predicted row with the highest pc (ties: lower s1)."""
    idx = np.flatnonzero(m)
    if idx.size == 0:
        return m
    r, p, s1 = d.r.to_numpy()[idx], d.pc.to_numpy()[idx], d.s1.to_numpy()[idx]
    rk = group_rank(r, p.astype(np.float64), s1)
    out = m.copy()
    out[idx[rk > 0]] = False
    return out


def per_s1_rank(d, m, extra_key=None):
    """rank (pc descending) of the predicted rows inside their S1 (and extra_key); -1 for unpredicted rows."""
    s1 = d.s1.to_numpy()
    key = s1 if extra_key is None else s1 * 4 + extra_key
    idx = np.flatnonzero(m)
    rk = np.full(len(d), -1, np.int64)
    rk[idx] = group_rank(key[idx], d.pc.to_numpy()[idx].astype(np.float64), d.r.to_numpy()[idx])
    return rk


def counts(d, m, key=None):
    s1 = d.s1.to_numpy()
    k = s1 if key is None else s1 * 4 + key
    return pd.Series(m.astype(np.int32)).groupby(k).transform("sum").to_numpy()


# ---------------------------------------------------------------- rules
def r_cap(d, base, s2cap=5, s3cap=6, tcap=11):
    src = d.src.to_numpy()
    rk = per_s1_rank(d, base, src)
    m = base & ~((src == 2) & (rk >= s2cap)) & ~((src == 3) & (rk >= s3cap))
    rk2 = per_s1_rank(d, m)
    return m & ~(rk2 >= tcap)


def r_soft_trim(d, base, kmin=8, x=0.9):
    """S1 with >= kmin predictions: drop predictions below pc x."""
    n = counts(d, base)
    return base & ~((n >= kmin) & (d.pc.to_numpy() < x))


def r_src_zero(d, base, tau=0.5, allow_nonown=False, need_other=True):
    """(ii) S1 with no predicted copy in source s (and >= 1 in the other): add its best candidate in s if pc >= tau."""
    src = d.src.to_numpy()
    n2 = counts(d, base & (src == 2))
    n3 = counts(d, base & (src == 3))
    n_s = np.where(src == 2, n2, n3)
    n_o = np.where(src == 2, n3, n2)
    pc_ = d.pc.to_numpy()
    rec_pred = pd.Series(base.astype(np.int8)).groupby(d.r.to_numpy()).transform("max").to_numpy() > 0
    elig = d.cand.to_numpy() & d.hold.to_numpy() & ~base & (n_s == 0) & (pc_ >= tau) & ~rec_pred
    elig &= (n_o >= 1) if need_other else True
    if not allow_nonown:
        elig &= d.own.to_numpy()
    # best one per (S1, source)
    idx = np.flatnonzero(elig)
    key = d.s1.to_numpy()[idx] * 4 + src[idx]
    rk = group_rank(key, pc_[idx].astype(np.float64), d.r.to_numpy()[idx])
    add = np.zeros(len(d), bool)
    add[idx[rk == 0]] = True
    return one_owner(d, base | add)


def r_singleton(d, base, u=0.8):
    """(iv) S1 whose only prediction has pc <= u: predict nothing."""
    n = counts(d, base)
    return base & ~((n == 1) & (d.pc.to_numpy() <= u))


def r_mass(d, base, col="psum_c", thr=THR):
    """(v) pc / max(1, record's pc sum) before the threshold (ownership unchanged: same scaling per record)."""
    p = d.pc.to_numpy() / np.maximum(1.0, d[col].to_numpy())
    return base & (p > thr)


def r_nsa(d, base, t2=0.675, t4=0.675, t3=None):
    """(vi-a) threshold by the number of S1 with p1 >= 0.02 for the record (before the top-2 cut)."""
    nsa = d.n_s1_all.to_numpy()
    t = np.where(nsa == 2, t2, np.where(nsa >= 4, t4, THR if t3 is None else np.where(nsa == 3, t3, THR)))
    return d.own.to_numpy() & d.cand.to_numpy() & (d.pc.to_numpy() > t)


def r_rank(d, base, t0=0.675, t5=0.675, kmin=5):
    """(vi-b) threshold by the pair's rank among its S1's owned candidates: rank 0 -> t0, rank >= kmin -> t5."""
    rk = d.rank_s1_own.to_numpy()
    t = np.where(rk == 0, t0, np.where(rk >= kmin, t5, THR))
    return d.own.to_numpy() & d.cand.to_numpy() & (d.pc.to_numpy() > t)


def r_pop(d, base, pops, kinds, numrels, lo=0.1, mode="add", hi=1.0):
    """(vi-c) add (or drop) owned pairs of a text population (kind x number relation) with pc in [lo, hi)."""
    x = d[["s1", "r"]].merge(pops, on=["s1", "r"], how="left")
    kind = x.kind.fillna("").to_numpy()
    nr = np.where(d.r_empty.to_numpy(), "r_empty", x.numrel.fillna("").to_numpy())
    sel = np.isin(kind, kinds) & np.isin(nr, numrels) & (d.pc.to_numpy() >= lo) & (d.pc.to_numpy() < hi)
    sel &= d.own.to_numpy() & d.cand.to_numpy()
    return (base | sel) if mode == "add" else (base & ~sel)


def main():
    t0 = time.time()
    d = build()
    uni, cty, th = universe_and_truth()
    ev = Eval(d, uni, th)
    base = d.pred.to_numpy()
    print("base", round(ev.score(base), 6))
    pops = pd.read_parquet(os.path.join(D, "pops.parquet"))
    rows = []

    def run(name, m, desc=""):
        assert not (m & ~d.cand.to_numpy()).any(), name
        chk = pd.Series(m.astype(np.int8)).groupby(d.r.to_numpy()).sum().max()
        assert chk <= 1, (name, "one owner per record")
        hm = m & d.hold.to_numpy()
        hb = base & d.hold.to_numpy()
        n_add, n_drop = int((hm & ~hb).sum()), int((hb & ~hm).sum())
        f, a, b = ev.delta(base, m)
        rows.append(dict(rule=name, desc=desc, add=n_add, drop=n_drop,
                         add_true=int((hm & ~hb & (d.y.to_numpy() == 1)).sum()),
                         drop_true=int((hb & ~hm & (d.y.to_numpy() == 1)).sum()), full=f, A=a, B=b))
        print(f"{name:32s} +{n_add:5d} -{n_drop:5d}  full {f:+.7f}  A {a:+.7f}  B {b:+.7f}", flush=True)

    # (i) caps and soft trims
    run("i_cap_5_6_11", r_cap(d, base), "trim S2>5, S3>6, total>11 by lowest pc")
    for kmin in (7, 8, 9):
        for x in (0.8, 0.9, 0.95):
            run(f"i_trim_k{kmin}_x{x}", r_soft_trim(d, base, kmin, x), f"S1 with >= {kmin} preds: drop pc < {x}")
    # (ii) per-source zero count
    for tau in (0.3, 0.4, 0.5, 0.6):
        run(f"ii_src0_own_t{tau}", r_src_zero(d, base, tau), "no pred in source s, >=1 in other: add best owned cand")
        run(f"ii_src0_any_t{tau}", r_src_zero(d, base, tau, allow_nonown=True), "same, non-owned records allowed")
    # (iii) ownership conflicts
    own_viol = int((base & (d.p_other.to_numpy() > d.pc.to_numpy())).sum())
    print("iii: predicted records with a higher-pc rival S1:", own_viol)
    # (iv) singleton protection
    for u in (0.75, 0.8, 0.9, 0.95):
        run(f"iv_single_u{u}", r_singleton(d, base, u), f"S1 whose only prediction has pc <= {u}: empty")
    # (v) record mass
    run("v_mass_cut", r_mass(d, base, "psum_c"), "pc / max(1, record pc sum over the cut)")
    run("v_mass_all", r_mass(d, base, "psum_all"), "pc / max(1, record pc sum over p1>=0.02)")
    # (vi-a) n S1 per record
    for t2 in (0.6, 0.625, 0.65, 0.675):
        for t4 in (0.675, 0.7, 0.75, 0.8):
            if t2 == 0.675 and t4 == 0.675:
                continue
            run(f"vi_nsa_t2{t2}_t4{t4}", r_nsa(d, base, t2, t4), "threshold t2 if 2 S1 with p1>=.02, t4 if >=4")
    # (vi-b) rank thresholds
    for t0_ in (0.5, 0.55, 0.6, 0.675):
        for t5 in (0.6, 0.625, 0.65, 0.675):
            if t0_ == 0.675 and t5 == 0.675:
                continue
            run(f"vi_rank_t0{t0_}_t5{t5}", r_rank(d, base, t0_, t5), "threshold t0 for S1's top owned pair, t5 rank>=5")
    # (vi-c) text populations
    run("vi_acr_add_lo0.1", r_pop(d, base, pops, ["acr"], ["same", "same_num_other_street", "other_street", "no_num",
                                                           "other_num", "nudge+", "minus"], 0.1), "add owned acronym pairs pc>=0.1")
    run("vi_nudge_drop_hi0.85", r_pop(d, base, pops, ["same", "swap", "add", ""], ["nudge+"], 0.675, "drop", 0.85),
        "drop predicted same-street +d nudges with pc < 0.85")
    run("vi_same_num_other_street_add_0.6",
        r_pop(d, base, pops, ["same"], ["same_num_other_street", "same"], 0.6, "add", THR),
        "add same-name same-number pairs pc 0.6-0.675")
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(D, "rules_grid.csv"), index=False)
    print("done", round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
