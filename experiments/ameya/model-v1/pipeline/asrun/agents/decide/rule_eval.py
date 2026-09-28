"""Holdout F0.5 of ONE model under the production combo rule, plus its own threshold rule for reference.

    python rule_eval.py <model>     # scores ameya-s3-<model>, holdout matches ameya-model-<model>-s3 (threshold check)

Combo rule (as apply_combo.py on test): cut = common.candidate_mask(s1, r, p1, 0.02, 2), pc outside the cut = 0,
argmax owner over all train S1; q = sigmoid(logit(pc) + 0.2 - 0.3 * [record has >= 4 S1 with p1 >= 0.02]); exact
expected-F0.5 prefix per S1 with phantom 0.01 (core.expected_f_select); then hunt apply_rules acr + cap (THR = 0, so every
DP prediction is a model prediction for cap). Only holdout S1 rows are needed: every prediction is an owned pair, so a
holdout S1's records can only be held by that S1.
Writes rule_<model>.npz (per-entity F0.5 on universe.parquet's sorted S1: f_combo, f_thr) and rule_<model>.json.
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

D = os.path.dirname(os.path.abspath(__file__))
HUNT = os.path.join(os.path.dirname(D), "hunt")
sys.path.insert(0, D)
sys.path.insert(1, HUNT)

import apply_hunt  # noqa: E402
from ber.paths import artifact_path  # noqa: E402
from common import argmax_owner, candidate_mask  # noqa: E402
from core import expected_f_select, to_q  # noqa: E402

K = 4_000_000_000


def main() -> int:
    t0 = time.time()
    model = sys.argv[1]
    tag, mtag = f"ameya-s3-{model}", f"ameya-model-{model}-s3"
    rep_path = os.path.join(os.environ["BER_WORK_DIR"], "reports", f"{mtag}.json")
    thr = float(json.load(open(rep_path))["rule"]["threshold"])
    u = pd.read_parquet(os.path.join(D, "universe.parquet"))
    U = u["s1"].to_numpy()
    th = pd.read_parquet(os.path.join(D, "truth_hold.parquet"))
    tkeys = np.sort(th["s1"].to_numpy() * K + th["r"].to_numpy())
    n_true = u["n_true"].to_numpy().astype(np.float64)

    def fast_f(pairs: pd.DataFrame) -> np.ndarray:
        s1 = pairs["s1"].to_numpy()
        m = np.isin(s1, U)
        s1, r = s1[m], pairs["r"].to_numpy()[m]
        idx = np.searchsorted(U, s1)
        hit = np.isin(s1 * K + r, tkeys).astype(np.float64)
        n_pred = np.bincount(idx, minlength=U.size)
        n_hit = np.bincount(idx, weights=hit, minlength=U.size)
        den = 0.25 * n_true + n_pred
        return np.where(den > 0, 1.25 * n_hit / np.where(den > 0, den, 1.0), 1.0)

    # 1. train rows with p1 >= 0.02
    f = pq.ParquetFile(artifact_path("scores", tag, "train"))
    parts = {c: [] for c in ("s1", "r", "p1", "pc")}
    for g in range(f.num_row_groups):
        t = f.read_row_group(g, columns=["s1", "r", "p1", "pc"])
        keep = t.column("p1").to_numpy() >= 0.02
        for c in parts:
            parts[c].append(t.column(c).to_numpy()[keep])
        del t
    s1, r, p1, pc = (np.concatenate(parts[c]) for c in ("s1", "r", "p1", "pc"))
    del parts
    # 2. cut, ownership over all S1, record crowding (S1 with p1 >= 0.02, before the cut)
    cut = candidate_mask(s1, r, p1, 0.02, 2)
    p = np.where(cut, pc, np.float32(0)).astype(np.float32)
    own = argmax_owner(s1, r, p)
    ur, inv, cnt = np.unique(r, return_inverse=True, return_counts=True)
    n_s1_all = cnt[inv].astype(np.int16)
    del ur, inv, cnt, p1, pc
    # 3. holdout S1 rows inside the cut with p > 0
    h = np.isin(s1, U) & (p > 0)
    s = pd.DataFrame({"s1": s1[h], "r": r[h], "pc": p[h], "own": own[h], "n_s1_all": n_s1_all[h]})
    del s1, r, p, own, n_s1_all, cut, h
    print(f"{model}: holdout cut rows {len(s):,}; thr {thr} ({time.time() - t0:.0f}s)", flush=True)

    # 4. threshold rule + check against the stored holdout matches
    thr_sel = s.own.to_numpy() & (s.pc.to_numpy() > thr)
    m_thr = s.loc[thr_sel, ["s1", "r"]]
    stored = pq.read_table(artifact_path("matches", mtag, "train"), columns=["s1", "r"]).to_pandas()
    stored = stored[np.isin(stored["s1"].to_numpy(), U)]
    ks, kt = np.sort(stored["s1"].to_numpy() * K + stored["r"].to_numpy()), np.sort(m_thr.s1.to_numpy() * K + m_thr.r.to_numpy())
    same = bool(ks.size == kt.size and (ks == kt).all())
    print(f"threshold rebuild == {mtag} holdout: {same} ({ks.size:,} vs {kt.size:,})", flush=True)
    f_thr = fast_f(m_thr)

    # 5. combo rule
    crowd = s.n_s1_all.to_numpy() >= 4
    q = to_q(s.pc.to_numpy().astype(np.float64), 0.2 - 0.3 * crowd)
    sel = expected_f_select(s.s1.to_numpy(), q, s.own.to_numpy(), lam=0.01)
    m_dp = s.loc[sel, ["s1", "r"]].reset_index(drop=True)
    pre = s.loc[s.own.to_numpy() & (s.pc.to_numpy() >= 0.1) & (s.pc.to_numpy() <= 0.95), ["s1", "r", "pc"]]
    pre = pre.reset_index(drop=True)
    orig_acr = apply_hunt.acr_pairs
    flag = orig_acr("train", pre)
    acr_keys = np.sort(pre.s1.to_numpy()[flag] * K + pre.r.to_numpy()[flag])
    pre_keys = np.sort(pre.s1.to_numpy() * K + pre.r.to_numpy())

    def cached_acr(split, pairs):
        k = pairs.s1.to_numpy() * K + pairs.r.to_numpy()
        out_ = np.isin(k, acr_keys)
        miss = ~np.isin(k, pre_keys)
        if miss.any():  # outside the cached pc range: ask the original function
            out_[miss] = orig_acr(split, pairs.loc[miss].reset_index(drop=True))
        return out_

    apply_hunt.acr_pairs = cached_acr
    apply_hunt.THR = 0.0
    cty = pd.Series(u["country"].to_numpy(), index=U)
    out, ch = apply_hunt.apply_rules(s[["s1", "r", "pc", "own", "n_s1_all"]], m_dp, cty, ["acr", "cap"], "", None,
                                     "train")
    f_combo = fast_f(out)
    f_dp = fast_f(m_dp)
    res = {"model": model, "thr": thr, "thr_rebuild_matches_stored": same, "rows": int(len(s)),
           "n_pred_thr": int(len(m_thr)), "n_pred_dp": int(len(m_dp)), "n_pred_combo": int(len(out)),
           "acr_adds": int(((ch.rule == "acr") & (ch.action == "add")).sum()) if len(ch) else 0,
           "cap_drops": int(((ch.rule == "cap") & (ch.action == "drop")).sum()) if len(ch) else 0,
           "f_thr": float(f_thr.mean()), "f_dp": float(f_dp.mean()), "f_combo": float(f_combo.mean())}
    for c in ("US", "India"):
        mc = u["country"].to_numpy() == c
        res[f"f_combo_{c}"] = float(f_combo[mc].mean())
        res[f"f_thr_{c}"] = float(f_thr[mc].mean())
    np.savez_compressed(os.path.join(D, f"rule_{model}.npz"), f_combo=f_combo.astype(np.float64),
                        f_thr=f_thr.astype(np.float64), f_dp=f_dp.astype(np.float64))
    res["runtime_s"] = round(time.time() - t0)
    json.dump(res, open(os.path.join(D, f"rule_{model}.json"), "w"), indent=1)
    print(json.dumps(res), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
