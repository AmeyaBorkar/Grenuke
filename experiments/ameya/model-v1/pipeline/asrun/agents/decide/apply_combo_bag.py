"""Test predictions of a BAG of stage-3 scores under the combo rule (US/India), France from the hunted v7sq3 file.

    python apply_combo_bag.py --bag bag4    (or bag5; members in bag_eval.BAGS)
Same steps as apply_combo.py: bag pc = mean logit(pc) of the members (rows aligned, checked), cut (p1 >= 0.02 and top-2 S1
per record), argmax owner on the cut, q = sigmoid(logit(pc) + 0.2 - 0.3 * [record has >= 4 S1 with p1 >= 0.02]), exact
expected-F0.5 prefix with phantom 0.01, hunt acr + cap for US/India (THR = 0), France and other countries copied from
--hunted. Checks: one S1 per record, all pairs inside --cands, US/India pairs owned and in the cut, France identical to
the hunted file. Change counts vs --final and vs --ref (the v7sq3 combo file).
Writes <out>.parquet (s1, r int64) and <out>.json.
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
from bag_eval import BAGS, bag_pc, load_members  # noqa: E402
from ber.artifacts import read_table  # noqa: E402
from common import argmax_owner, candidate_mask  # noqa: E402
from core import expected_f_select, to_q  # noqa: E402

K = 4_000_000_000
LABELLED = ("US", "India")


def keys(df: pd.DataFrame) -> np.ndarray:
    return df.s1.to_numpy().astype(np.int64) * K + df.r.to_numpy().astype(np.int64)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bag", default="bag4", choices=sorted(BAGS))
    ap.add_argument("--final", default="ameya-model-v7sq3-s3-ops3a")
    ap.add_argument("--cands", default="ameya-cands-v7sq3-c2a")
    ap.add_argument("--hunted", default=os.path.join(HUNT, "hunted_v7sq3.parquet"))
    ap.add_argument("--ref", default=os.path.join(D, "decided_combo_ameya-s3-v7sq3.parquet"))
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    out_stem = args.out or f"decided_combo_{args.bag}"
    t0 = time.time()
    cty = apply_hunt.s1_country("test")
    members = BAGS[args.bag]
    s1, r, p1, pcs, aligned = load_members(members, "test")
    print(f"test rows p1>=0.02 {s1.size:,}; members {members}; row-aligned {aligned} ({time.time() - t0:.0f}s)", flush=True)
    pc = bag_pc(pcs)
    del pcs
    s = pd.DataFrame({"s1": s1, "r": r, "p1": p1, "pc": pc})
    del s1, r, p1, pc
    s["n_s1_all"] = s.groupby("r").s1.transform("size").astype(np.int16)
    cut = candidate_mask(s.s1.to_numpy(), s.r.to_numpy(), s.p1.to_numpy(), 0.02, 2)
    s = s[cut].reset_index(drop=True)
    s["own"] = argmax_owner(s.s1.to_numpy(), s.r.to_numpy(), s.pc.to_numpy())
    fin = read_table("matches", args.final, "test", ["s1", "r"]).astype(np.int64)
    s_c = cty.reindex(s.s1.to_numpy()).to_numpy()
    f_c = cty.reindex(fin.s1.to_numpy()).to_numpy()
    lab = np.isin(s_c, LABELLED) & (s.pc.to_numpy() > 0)
    rep = {"args": vars(args), "members": members, "row_aligned": aligned}

    sl = s[lab].reset_index(drop=True)
    crowd = sl.n_s1_all.to_numpy() >= 4
    q = to_q(sl.pc.to_numpy().astype(np.float64), 0.2 - 0.3 * crowd)
    sel = expected_f_select(sl.s1.to_numpy(), q, sl.own.to_numpy(), lam=0.01)
    m_lab = sl.loc[sel, ["s1", "r"]].astype(np.int64)
    m_in = pd.concat([m_lab, fin[~np.isin(f_c, LABELLED)]], ignore_index=True)
    print(f"DP pairs US/India {len(m_lab):,} ({time.time() - t0:.0f}s)", flush=True)

    cd = read_table("candidates", args.cands, "test", ["s1", "r"])
    ck = np.sort(keys(cd))
    del cd
    sk = keys(s)
    j = np.minimum(np.searchsorted(ck, sk), ck.size - 1)
    cand_ok = ck[j] == sk
    apply_hunt.THR = 0.0
    out, ch = apply_hunt.apply_rules(s, m_in, cty, {n: set(LABELLED) for n in ("acr", "cap")}, "", cand_ok, "test")
    rep["hunt_rule_changes"] = {f"{a}/{b}/{c}": int(v) for (a, b, c), v in
                                ch.groupby(["rule", "action", "country"]).size().items()} if len(ch) else {}
    o_c = cty.reindex(out.s1.to_numpy()).to_numpy()
    out = out[np.isin(o_c, LABELLED)]
    hu = pd.read_parquet(args.hunted, columns=["s1", "r"]).astype(np.int64)
    h_c = cty.reindex(hu.s1.to_numpy()).to_numpy()
    out = pd.concat([out, hu[~np.isin(h_c, LABELLED)]], ignore_index=True).astype(np.int64)
    o_c = cty.reindex(out.s1.to_numpy()).to_numpy()

    dup = out.r.duplicated(keep=False)
    rep["records_with_2_owners"] = int(dup.sum())
    if dup.any():
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
    ref = pd.read_parquet(args.ref, columns=["s1", "r"]).astype(np.int64)
    r_c = cty.reindex(ref.s1.to_numpy()).to_numpy()
    kfin, kref = keys(fin), keys(ref)
    n_s1 = cty.value_counts()
    ch_c = {}
    for c in sorted(n_s1.index):
        mo, mf, mr = o_c == c, f_c == c, r_c == c
        ch_c[str(c)] = {"n_s1": int(n_s1[c]), "pairs_new": int(mo.sum()),
                        "added_vs_final": int((~np.isin(ko[mo], kfin[mf])).sum()),
                        "removed_vs_final": int((~np.isin(kfin[mf], ko[mo])).sum()),
                        "added_vs_v7sq3_combo": int((~np.isin(ko[mo], kref[mr])).sum()),
                        "removed_vs_v7sq3_combo": int((~np.isin(kref[mr], ko[mo])).sum()),
                        "s1_changed_vs_v7sq3_combo": int(np.unique(np.r_[out.s1.to_numpy()[mo][~np.isin(ko[mo], kref[mr])],
                                                                         ref.s1.to_numpy()[mr][~np.isin(kref[mr], ko[mo])]]).size),
                        "pred_per_s1": round(float(mo.sum() / n_s1[c]), 4)}
    rep["changes_by_country"] = ch_c
    rep["n_pairs"] = int(len(out))
    path = os.path.join(D, out_stem + ".parquet")
    out[["s1", "r"]].astype(np.int64).to_parquet(path, index=False)
    rep["path"] = path
    rep["runtime_s"] = round(time.time() - t0)
    json.dump(rep, open(os.path.join(D, out_stem + ".json"), "w"), indent=1, default=str)
    print(json.dumps({k: rep[k] for k in rep if k != "args"}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
