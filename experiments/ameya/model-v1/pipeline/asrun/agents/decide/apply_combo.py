"""Winner on test: DP (shift 0.2, lam 0.01, crowd shift -0.3) + the hunt's acr + cap for US/India; France (and any
unlabelled country) taken from the hunt's output (final tag + the hunt's France acr/cap changes).

    python apply_combo.py --scores ameya-s3-v7s --final ameya-model-v7s-s3-ops3a --cands ameya-cands-v7s-c2a \
        --hunted ../hunt/hunted_ameya-model-v7s-s3-ops3a.parquet --base-thr 0.7 --out decided_combo_ameya-s3-v7s

US/India S1: cut rows (p1 >= 0.02 and the record's top-2 S1 by p1), argmax owner, q = sigmoid(logit(pc) + 0.2 - 0.3 *
[record has >= 4 S1 with p1 >= 0.02]), exact expected-F0.5 prefix per S1 with a 0.01 phantom (core.expected_f_select),
then hunt/apply_hunt.apply_rules with acr and cap restricted to US+India (cap trims the lowest-pc predictions first).
Checks: base threshold reproduces the final tag's US/India pairs; one S1 per record; all pairs inside --cands;
France identical to the hunted file. Writes <out>.parquet (s1, r int64) and <out>.json.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np
import pandas as pd

D = os.path.dirname(os.path.abspath(__file__))
HUNT = os.path.join(os.path.dirname(D), "hunt")
sys.path.insert(0, D)
sys.path.insert(1, HUNT)

import apply_hunt  # noqa: E402
from ber.artifacts import read_table  # noqa: E402
from core import expected_f_select, to_q  # noqa: E402

K = 4_000_000_000
LABELLED = ("US", "India")


def keys(df: pd.DataFrame) -> np.ndarray:
    return df.s1.to_numpy().astype(np.int64) * K + df.r.to_numpy().astype(np.int64)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores", default="ameya-s3-v7s")
    ap.add_argument("--final", default="ameya-model-v7s-s3-ops3a")
    ap.add_argument("--cands", default="ameya-cands-v7s-c2a")
    ap.add_argument("--hunted", default=os.path.join(HUNT, "hunted_ameya-model-v7s-s3-ops3a.parquet"))
    ap.add_argument("--base-thr", type=float, default=0.7)
    ap.add_argument("--shift", type=float, default=0.2)
    ap.add_argument("--lam", type=float, default=0.01)
    ap.add_argument("--crowd", type=int, default=4)
    ap.add_argument("--delta", type=float, default=0.3)
    ap.add_argument("--rules", default="acr,cap", help="hunt rules applied to US/India after the DP ('' for none)")
    ap.add_argument("--out", default="decided_combo_ameya-s3-v7s")
    args = ap.parse_args()
    t0 = time.time()
    cty = apply_hunt.s1_country("test")
    s = apply_hunt.load_scores(args.scores, "test")  # cut rows: s1, r, p1, pc, n_s1_all, own
    fin = read_table("matches", args.final, "test", ["s1", "r"]).astype(np.int64)
    s_c = cty.reindex(s.s1.to_numpy()).to_numpy()
    f_c = cty.reindex(fin.s1.to_numpy()).to_numpy()
    lab = np.isin(s_c, LABELLED) & (s.pc.to_numpy() > 0)
    print(f"cut rows {len(s):,}; labelled rows {int(lab.sum()):,}; final {len(fin):,} ({time.time() - t0:.0f}s)", flush=True)
    rep = {"args": vars(args)}

    # base reproduction on US/India
    b = s.own.to_numpy() & lab & (s.pc.to_numpy() > args.base_thr)
    kb, kf = keys(s[b]), keys(fin[np.isin(f_c, LABELLED)])
    rep["base_reproduction"] = {"final_labelled": int(kf.size), "rule": int(kb.size),
                                "in_final_not_rule": int((~np.isin(kf, kb)).sum()),
                                "in_rule_not_final": int((~np.isin(kb, kf)).sum())}
    print("base reproduction:", rep["base_reproduction"], flush=True)

    # DP on US/India
    sl = s[lab].reset_index(drop=True)
    crowd = sl.n_s1_all.to_numpy() >= args.crowd
    q = to_q(sl.pc.to_numpy().astype(np.float64), args.shift - args.delta * crowd)
    sel = expected_f_select(sl.s1.to_numpy(), q, sl.own.to_numpy(), lam=args.lam)
    m_lab = sl.loc[sel, ["s1", "r"]].astype(np.int64)
    m_in = pd.concat([m_lab, fin[~np.isin(f_c, LABELLED)]], ignore_index=True)
    print(f"DP pairs US/India {len(m_lab):,} ({time.time() - t0:.0f}s)", flush=True)

    # hunt rules (acr, cap) on US/India; THR = 0 so every DP prediction counts as a model prediction for cap
    cd = read_table("candidates", args.cands, "test", ["s1", "r"])
    ck = np.sort(keys(cd))
    del cd
    sk = keys(s)
    j = np.minimum(np.searchsorted(ck, sk), ck.size - 1)
    cand_ok = ck[j] == sk
    names = [x for x in args.rules.split(",") if x]
    if names:
        apply_hunt.THR = 0.0
        out, ch = apply_hunt.apply_rules(s, m_in, cty, {n: set(LABELLED) for n in names}, "", cand_ok, "test")
        rep["hunt_rule_changes"] = {f"{r_}/{a_}/{c_}": int(v) for (r_, a_, c_), v in
                                    ch.groupby(["rule", "action", "country"]).size().items()} if len(ch) else {}
        print("hunt rule changes (US/India):", rep["hunt_rule_changes"], flush=True)
    else:
        out = m_in
    o_c = cty.reindex(out.s1.to_numpy()).to_numpy()
    out = out[np.isin(o_c, LABELLED)]

    # France / other countries from the hunted file
    hu = pd.read_parquet(args.hunted, columns=["s1", "r"]).astype(np.int64)
    h_c = cty.reindex(hu.s1.to_numpy()).to_numpy()
    out = pd.concat([out, hu[~np.isin(h_c, LABELLED)]], ignore_index=True).astype(np.int64)
    o_c = cty.reindex(out.s1.to_numpy()).to_numpy()

    # checks
    dup = out.r.duplicated(keep=False)
    rep["records_with_2_owners"] = int(dup.sum())
    if dup.any():  # keep the France (hunted) row, drop the US/India one
        drop = dup.to_numpy() & np.isin(o_c, LABELLED)
        out, o_c = out[~drop].reset_index(drop=True), o_c[~drop]
        rep["clash_dropped"] = int(drop.sum())
    ko = keys(out)
    j = np.minimum(np.searchsorted(ck, ko), ck.size - 1)
    rep["outside_candidates"] = int((ck[j] != ko).sum())
    kl = ko[np.isin(o_c, LABELLED)]
    rep["labelled_outside_cut_or_not_owned"] = int((~np.isin(kl, sk[s.own.to_numpy()])).sum())
    fr_new, fr_h = np.sort(ko[~np.isin(o_c, LABELLED)]), np.sort(keys(hu[~np.isin(h_c, LABELLED)]))
    rep["non_labelled_identical_to_hunted"] = bool(fr_new.size == fr_h.size and (fr_new == fr_h).all())
    kfin, khu = keys(fin), keys(hu)
    n_s1 = cty.value_counts()
    ch_c = {}
    for c in sorted(n_s1.index):
        mo, mf, mh = o_c == c, f_c == c, h_c == c
        a_, r_ = ~np.isin(ko[mo], kfin[mf]), ~np.isin(kfin[mf], ko[mo])
        ch_c[str(c)] = {"n_s1": int(n_s1[c]), "pairs_final": int(mf.sum()), "pairs_new": int(mo.sum()),
                        "added_vs_final": int(a_.sum()), "removed_vs_final": int(r_.sum()),
                        "s1_changed_vs_final": int(np.unique(np.r_[out.s1.to_numpy()[mo][a_],
                                                                   fin.s1.to_numpy()[mf][r_]]).size),
                        "added_vs_hunted": int((~np.isin(ko[mo], khu[mh])).sum()),
                        "removed_vs_hunted": int((~np.isin(khu[mh], ko[mo])).sum()),
                        "pred_per_s1": round(float(mo.sum() / n_s1[c]), 4)}
    rep["changes_by_country"] = ch_c
    rep["n_pairs"] = int(len(out))
    path = os.path.join(D, args.out + ".parquet")
    out[["s1", "r"]].astype(np.int64).to_parquet(path, index=False)
    rep["path"] = path
    rep["runtime_s"] = round(time.time() - t0)
    json.dump(rep, open(os.path.join(D, args.out + ".json"), "w"), indent=1, default=str)
    print(json.dumps({k: rep[k] for k in rep if k != "args"}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
