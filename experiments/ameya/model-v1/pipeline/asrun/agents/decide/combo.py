"""Gates on the v7s US/India holdout, all against plain v7s (own & pc > 0.70): the DP winner combined with the hunt's
rules (hunt/apply_hunt.apply_rules, used read-only; hunt cache feats_all_v7s.parquet).

  V1  DP (shift 0.2, lam 0.01)
  V2  DP + acr + cap
  V3a DP + acr + cap + nsa (hunt band: pc in (0.70, 0.75], record with >= 4 S1 at p1 >= 0.02)
  V3b-d DP with nsa as calibration (q shift -delta for pairs of records with >= 4 S1; delta 0.15 / 0.3 / 0.45) + acr + cap
  V4  threshold 0.70 + acr + cap + nsa + rank0 (the hunt's best; cross-check of its +33.1)
  V5  threshold 0.70 + acr + cap + nsa (the hunt's recommended)
Per-entity F0.5 = ber.eval.metric.per_entity_f05, interval = ber.eval.gates.paired_bootstrap (as compare()).
Writes combo_v7s.json.
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
import pandas as pd
import pyarrow.compute as pc
import pyarrow.parquet as pq

D = os.path.dirname(os.path.abspath(__file__))
HUNT = os.path.join(os.path.dirname(D), "hunt")
sys.path.insert(0, D)
sys.path.insert(1, HUNT)
os.environ.setdefault("HUNT_SUFFIX", "_v7s")

import apply_hunt  # noqa: E402
from base import K, universe_and_truth  # noqa: E402
from ber.eval.gates import paired_bootstrap  # noqa: E402
from ber.eval.metric import per_entity_f05  # noqa: E402
from ber.eval.splits import splitmix64  # noqa: E402
from ber.paths import records_path  # noqa: E402
from core import expected_f_select, to_q  # noqa: E402
from feats import build  # noqa: E402

CROWD = 4
BASE_THR = float(os.environ.get("BASE_THR", "0.70"))
QUICK = os.environ.get("QUICK", "") == "1"
OUT = f"combo{os.environ.get('HUNT_SUFFIX', '_v7s') or '_v7nst'}.json"


def main() -> int:
    t0 = time.time()
    d = build()
    uni, cty, th = universe_and_truth()
    t = pq.read_table(records_path("train"), columns=["eid", "source", "country"])
    t = t.filter(pc.equal(t["source"], 1))
    cty_all = pd.Series(t["country"].to_numpy(zero_copy_only=False), index=t["eid"].to_numpy())
    del t
    s = d.loc[d.cand, ["s1", "r", "pc", "own", "n_s1_all"]].reset_index(drop=True)
    m_thr = d.loc[d.pred, ["s1", "r"]].reset_index(drop=True)
    fa = per_entity_f05(m_thr, th, uni)["f05"].to_numpy()
    half = (splitmix64(uni) % np.uint64(2)).astype(np.int8)
    c = cty.reindex(uni).to_numpy()
    print(f"base F0.5 {fa.mean():.6f}; rows {len(d):,}; cut rows {len(s):,} ({time.time() - t0:.0f}s)", flush=True)

    # cached acr flags (the hunt's acr_pairs reads the records file; compute once for every owned cut pair that any
    # variant could leave unpredicted: pc in [0.1, 0.95])
    orig_acr = apply_hunt.acr_pairs
    pre = s.loc[s.own.to_numpy() & (s.pc.to_numpy() >= 0.1) & (s.pc.to_numpy() <= 0.95), ["s1", "r", "pc"]]
    pre = pre.reset_index(drop=True)
    flag = orig_acr("train", pre)
    acr_keys = np.sort(pre.s1.to_numpy()[flag] * K + pre.r.to_numpy()[flag])
    pre_keys = np.sort(pre.s1.to_numpy() * K + pre.r.to_numpy())
    print(f"acr flags: {int(flag.sum())} of {len(pre):,} owned pairs ({time.time() - t0:.0f}s)", flush=True)

    def cached_acr(split, pairs):
        k = pairs.s1.to_numpy() * K + pairs.r.to_numpy()
        assert np.isin(k, pre_keys).all(), "acr candidate outside the cached range"
        return np.isin(k, acr_keys)

    apply_hunt.acr_pairs = cached_acr

    # DP on the holdout S1 (all their cut rows); other S1 keep the threshold predictions (they only matter for
    # "is the record already held")
    rows = d[d.hold.to_numpy() & d.cand.to_numpy() & (d.pc.to_numpy() > 0)].reset_index(drop=True)
    rs1, rr, rp, rown = rows.s1.to_numpy(), rows.r.to_numpy(), rows.pc.to_numpy().astype(np.float64), rows.own.to_numpy()
    crowd = rows.n_s1_all.to_numpy() >= CROWD
    others = d.loc[d.pred.to_numpy() & ~d.hold.to_numpy(), ["s1", "r"]]

    def dp_matches(delta: float) -> pd.DataFrame:
        sel = expected_f_select(rs1, to_q(rp, 0.2 - delta * crowd), rown, lam=0.01)
        return pd.concat([pd.DataFrame({"s1": rs1[sel], "r": rr[sel]}), others], ignore_index=True)

    def nsa_drop(m: pd.DataFrame, base_m: pd.DataFrame, lo: float, hi: float = 0.75) -> pd.DataFrame:
        """Drop pairs of the ORIGINAL decision (base_m; never rule adds) that are owned, pc in (lo, hi], crowded."""
        bad = s.own.to_numpy() & (s.pc.to_numpy() > lo) & (s.pc.to_numpy() <= hi) & (s.n_s1_all.to_numpy() >= CROWD)
        bk = s.s1.to_numpy()[bad] * K + s.r.to_numpy()[bad]
        bk = bk[np.isin(bk, base_m.s1.to_numpy() * K + base_m.r.to_numpy())]
        mk = m.s1.to_numpy() * K + m.r.to_numpy()
        return m[~np.isin(mk, bk)].reset_index(drop=True)

    def rules(m: pd.DataFrame, names, thr: float) -> pd.DataFrame:
        apply_hunt.THR = thr
        out, _ = apply_hunt.apply_rules(s, m, cty_all, names, "", None, "train")
        return out

    res = {"base_f05": float(fa.mean())}

    def gate(name: str, m: pd.DataFrame) -> None:
        fb = per_entity_f05(m, th, uni)["f05"].to_numpy()
        g = {}
        for part, sel in (("full", np.ones(uni.size, bool)), ("A", half == 0), ("B", half == 1),
                          ("US", c == "US"), ("India", c == "India")):
            b = paired_bootstrap(fa[sel], fb[sel])
            g[part] = {k: round(1e6 * b[k], 1) for k in ("delta", "ci_low", "ci_high")}
            g[part]["p_better"] = b["p_better"]
        mk = np.sort(m.s1.to_numpy() * K + m.r.to_numpy())
        bk = m_thr.s1.to_numpy() * K + m_thr.r.to_numpy()
        hold_new = mk[np.isin(mk // K, uni)]
        hold_old = bk[np.isin(bk // K, uni)]
        tk = th.s1.to_numpy() * K + th.r.to_numpy()
        add, rem = hold_new[~np.isin(hold_new, hold_old)], hold_old[~np.isin(hold_old, hold_new)]
        g["changes"] = {"added": int(add.size), "added_true": int(np.isin(add, tk).sum()),
                        "removed": int(rem.size), "removed_true": int(np.isin(rem, tk).sum())}
        g["new_f05"] = float(fb.mean())
        res[name] = g
        print(f"{name:34s} full {g['full']['delta']:+6.1f} [{g['full']['ci_low']:+6.1f}, {g['full']['ci_high']:+6.1f}]"
              f" p={g['full']['p_better']:.3f} | A {g['A']['delta']:+6.1f} [{g['A']['ci_low']:+6.1f}, "
              f"{g['A']['ci_high']:+6.1f}] | B {g['B']['delta']:+6.1f} [{g['B']['ci_low']:+6.1f}, "
              f"{g['B']['ci_high']:+6.1f}] | US {g['US']['delta']:+6.1f} India {g['India']['delta']:+6.1f} | "
              f"{g['changes']} ({time.time() - t0:.0f}s)", flush=True)
        json.dump(res, open(os.path.join(D, OUT), "w"), indent=1)

    if QUICK:  # second-model check: the winner, its pieces and the hunt's best
        gate("V1 DP", dp_matches(0.0))
        gate("V3 DP(crowd -0.3)+acr+cap", rules(dp_matches(0.3), ["acr", "cap"], 0.0))
        gate("V4 thr+acr+cap+nsa+rank0", rules(m_thr, ["acr", "cap", "nsa", "rank0"], BASE_THR))
        print(f"done {time.time() - t0:.0f}s")
        return 0
    m_dp = dp_matches(0.0)
    gate("V1 DP", m_dp)
    m2 = rules(m_dp, ["acr", "cap"], 0.0)
    gate("V2 DP+acr+cap", m2)
    gate("V3a DP+acr+cap+nsa(pc 0.70-0.75)", nsa_drop(m2, m_dp, BASE_THR))
    for delta in (0.15, 0.3, 0.45):
        md = dp_matches(delta)
        gate(f"V3 DP(crowd -{delta})+acr+cap", rules(md, ["acr", "cap"], 0.0))
    m4 = rules(m_thr, ["acr", "cap", "nsa", "rank0"], BASE_THR)
    gate("V4 thr+acr+cap+nsa+rank0", m4)
    m5 = rules(m_thr, ["acr", "cap", "nsa"], BASE_THR)
    gate("V5 thr+acr+cap+nsa", m5)
    print(f"done {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
