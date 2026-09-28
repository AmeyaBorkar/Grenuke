"""Bagged stage-3 scores under the combo rule on the US/India holdout.

    python bag_eval.py
Bags (mean of logit(pc), pc clipped to [1e-7, 1 - 1e-7]; rows where every member has pc = 0, i.e. outside the cut, stay 0):
  bag4 = v7sq3, v7qbag, v7sq2, v7sq4;  bag5 = bag4 + v7sq.
Rows of the members' train files must be the same (s1, r) in the same order: checked per row group (fallback: key sort).
Then exactly rule_eval.py's pipeline (cut, argmax owner over all S1, crowd, DP shift 0.2 / lam 0.01 / crowd 4 delta 0.3,
hunt acr + cap) and paired bootstraps (ber.eval.gates.paired_bootstrap, 1000, seed 0) vs v7sq3's and v7sq's combo
(rule_<m>.npz) on full / US / India / A / B. Writes rule_bag4.npz / rule_bag5.npz (+ .json) and bag_eval.json.
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
from ber.eval.gates import paired_bootstrap  # noqa: E402
from ber.paths import artifact_path  # noqa: E402
from common import argmax_owner, candidate_mask  # noqa: E402
from core import expected_f_select, to_q  # noqa: E402

K = 4_000_000_000
BAGS = {"bag4": ["v7sq3", "v7qbag", "v7sq2", "v7sq4"], "bag5": ["v7sq3", "v7qbag", "v7sq2", "v7sq4", "v7sq"]}
BASE_THR = 0.70  # v7sq3's decide threshold (reference only: the combo rule does not use it)


def load_members(models: list[str], split: str):
    """Rows with p1 >= 0.02 (p1 is the shared stage-1 score): s1, r, p1 and one pc column per member, aligned."""
    files = [pq.ParquetFile(artifact_path("scores", f"ameya-s3-{m}", split)) for m in models]
    n = {f.metadata.num_rows for f in files}
    ng = {f.num_row_groups for f in files}
    aligned = len(n) == 1 and len(ng) == 1
    s1s, rs, p1s, pcs = [], [], [], [[] for _ in models]
    if aligned:
        for g in range(files[0].num_row_groups):
            t0 = files[0].read_row_group(g, columns=["s1", "r", "p1", "pc"])
            s1, r, p1 = (t0.column(c).to_numpy() for c in ("s1", "r", "p1"))
            keep = p1 >= 0.02
            pcs[0].append(t0.column("pc").to_numpy()[keep])
            for i, f in enumerate(files[1:], 1):
                t = f.read_row_group(g, columns=["s1", "r", "pc"])
                if not (np.array_equal(t.column("s1").to_numpy(), s1) and np.array_equal(t.column("r").to_numpy(), r)):
                    aligned = False
                    break
                pcs[i].append(t.column("pc").to_numpy()[keep])
            if not aligned:
                break
            s1s.append(s1[keep]); rs.append(r[keep]); p1s.append(p1[keep])
    if aligned:
        return (np.concatenate(s1s), np.concatenate(rs), np.concatenate(p1s), [np.concatenate(x) for x in pcs], True)
    # fallback: align on (s1, r) keys
    print(f"[{split}] row order differs between members: aligning on keys", flush=True)
    base = None
    out_pcs = []
    for m in models:
        f = pq.ParquetFile(artifact_path("scores", f"ameya-s3-{m}", split))
        parts = {c: [] for c in ("s1", "r", "p1", "pc")}
        for g in range(f.num_row_groups):
            t = f.read_row_group(g, columns=["s1", "r", "p1", "pc"])
            keep = t.column("p1").to_numpy() >= 0.02
            for c in parts:
                parts[c].append(t.column(c).to_numpy()[keep])
        s1, r, p1, pc = (np.concatenate(parts[c]) for c in ("s1", "r", "p1", "pc"))
        key = s1 * K + r
        o = np.argsort(key, kind="stable")
        if base is None:
            base = (key[o], s1[o], r[o], p1[o])
        elif not np.array_equal(key[o], base[0]):
            raise ValueError(f"{m}: different (s1, r) rows in {split}")
        out_pcs.append(pc[o])
    return base[1], base[2], base[3], out_pcs, False


def bag_pc(pcs: list[np.ndarray]) -> np.ndarray:
    lg = np.zeros(pcs[0].size, np.float64)
    anypos = np.zeros(pcs[0].size, bool)
    for pc in pcs:
        x = np.clip(pc.astype(np.float64), 1e-7, 1 - 1e-7)
        lg += np.log(x / (1 - x))
        anypos |= pc > 0
    lg /= len(pcs)
    return np.where(anypos, 1.0 / (1.0 + np.exp(-lg)), 0.0).astype(np.float32)


def main() -> int:
    t0 = time.time()
    u = pd.read_parquet(os.path.join(D, "universe.parquet"))
    U = u["s1"].to_numpy()
    th = pd.read_parquet(os.path.join(D, "truth_hold.parquet"))
    tkeys = np.sort(th["s1"].to_numpy() * K + th["r"].to_numpy())
    n_true = u["n_true"].to_numpy().astype(np.float64)
    cty = pd.Series(u["country"].to_numpy(), index=U)
    parts = {"full": np.ones(len(u), bool), "US": (u.country == "US").to_numpy(), "India": (u.country == "India").to_numpy(),
             "A": (u.half == 0).to_numpy(), "B": (u.half == 1).to_numpy()}

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

    members = BAGS["bag5"]
    s1, r, p1, pcs, aligned = load_members(members, "train")
    print(f"train rows p1>=0.02 {s1.size:,}; members {members}; row-aligned {aligned} ({time.time() - t0:.0f}s)", flush=True)
    cut = candidate_mask(s1, r, p1, 0.02, 2)
    ur, inv, cnt = np.unique(r, return_inverse=True, return_counts=True)
    n_s1_all = cnt[inv].astype(np.int16)
    del ur, inv, cnt
    hold_all = np.isin(s1, U)
    refs = {m: np.load(os.path.join(D, f"rule_{m}.npz"))["f_combo"] for m in ("v7sq3", "v7sq")}
    summary = {"aligned": aligned, "members": BAGS}
    for name, mem in BAGS.items():
        pc = bag_pc([pcs[members.index(m)] for m in mem])
        p = np.where(cut, pc, np.float32(0)).astype(np.float32)
        own = argmax_owner(s1, r, p)
        h = hold_all & (p > 0)
        s = pd.DataFrame({"s1": s1[h], "r": r[h], "pc": p[h], "own": own[h], "n_s1_all": n_s1_all[h]})
        del pc, p, own
        m_thr = s.loc[s.own.to_numpy() & (s.pc.to_numpy() > BASE_THR), ["s1", "r"]]
        f_thr = fast_f(m_thr)
        crowd = s.n_s1_all.to_numpy() >= 4
        q = to_q(s.pc.to_numpy().astype(np.float64), 0.2 - 0.3 * crowd)
        sel = expected_f_select(s.s1.to_numpy(), q, s.own.to_numpy(), lam=0.01)
        m_dp = s.loc[sel, ["s1", "r"]].reset_index(drop=True)
        pre = s.loc[s.own.to_numpy() & (s.pc.to_numpy() >= 0.1) & (s.pc.to_numpy() <= 0.95), ["s1", "r", "pc"]]
        pre = pre.reset_index(drop=True)
        orig_acr = apply_hunt.acr_pairs if not hasattr(apply_hunt, "_orig_acr") else apply_hunt._orig_acr
        apply_hunt._orig_acr = orig_acr
        flag = orig_acr("train", pre)
        acr_keys = np.sort(pre.s1.to_numpy()[flag] * K + pre.r.to_numpy()[flag])
        pre_keys = np.sort(pre.s1.to_numpy() * K + pre.r.to_numpy())

        def cached_acr(split, pairs, acr_keys=acr_keys, pre_keys=pre_keys, orig_acr=orig_acr):
            k = pairs.s1.to_numpy() * K + pairs.r.to_numpy()
            out_ = np.isin(k, acr_keys)
            miss = ~np.isin(k, pre_keys)
            if miss.any():
                out_[miss] = orig_acr(split, pairs.loc[miss].reset_index(drop=True))
            return out_

        apply_hunt.acr_pairs = cached_acr
        apply_hunt.THR = 0.0
        out, ch = apply_hunt.apply_rules(s, m_dp, cty, ["acr", "cap"], "", None, "train")
        f_combo = fast_f(out)
        res = {"model": name, "thr": BASE_THR, "thr_rebuild_matches_stored": None, "rows": int(len(s)),
               "n_pred_thr": int(len(m_thr)), "n_pred_dp": int(len(m_dp)), "n_pred_combo": int(len(out)),
               "f_thr": float(f_thr.mean()), "f_combo": float(f_combo.mean())}
        for c in ("US", "India"):
            res[f"f_combo_{c}"] = float(f_combo[parts[c]].mean())
        for ref, fr in refs.items():
            for k, selm in parts.items():
                b = paired_bootstrap(fr[selm], f_combo[selm])
                res[f"vs_{ref}_{k}"] = [1e6 * b["delta"], 1e6 * b["ci_low"], 1e6 * b["ci_high"], b["p_better"]]
        np.savez_compressed(os.path.join(D, f"rule_{name}.npz"), f_combo=f_combo, f_thr=f_thr, f_dp=fast_f(m_dp))
        json.dump(res, open(os.path.join(D, f"rule_{name}.json"), "w"), indent=1)
        summary[name] = res
        print(f"{name}: combo F0.5 {res['f_combo']:.6f} (US {res['f_combo_US']:.6f}, India {res['f_combo_India']:.6f});"
              f" own-thr {res['f_thr']:.6f} ({time.time() - t0:.0f}s)", flush=True)
        for ref in refs:
            print("   vs " + ref + ": " + "  ".join(
                f"{k} {res[f'vs_{ref}_{k}'][0]:+.1f} [{res[f'vs_{ref}_{k}'][1]:+.1f}, {res[f'vs_{ref}_{k}'][2]:+.1f}]"
                for k in parts), flush=True)
        json.dump(summary, open(os.path.join(D, "bag_eval.json"), "w"), indent=1)
    ref_full = float(refs["v7sq3"].mean())
    best = max(BAGS, key=lambda b: summary[b]["f_combo"])
    winner = best if summary[best]["f_combo"] > ref_full else "none"
    with open(os.path.join(D, "bag_winner.txt"), "w") as fh:
        print(winner, file=fh)
    print(f"v7sq3 combo {ref_full:.6f}; best bag {best} {summary[best]['f_combo']:.6f} -> winner: {winner}", flush=True)
    print(f"done {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
