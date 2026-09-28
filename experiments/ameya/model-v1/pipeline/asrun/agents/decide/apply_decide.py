"""Apply the winning decision rule to test: US/India from the stage-3 scores, every other country (France) copied
from the final matches tag.

    python apply_decide.py --scores ameya-s3-v7s --final ameya-model-v7s-s3-ops3a --cands ameya-cands-v7s-c2a         --base-thr 0.7 [--rule dp --shift 0.2 --lam 0.01]

Rule (winner, see REPORT.md): candidate cut (p1 >= 0.02 and the record's top-2 S1 by p1), p = pc inside the cut,
argmax ownership over ALL test S1 (each record under its highest-p S1), then per S1 the exact expected-F0.5 set
(prefix of its owned pairs by p) with q = sigmoid(logit(p) + 0.2) and a phantom candidate of probability 0.01 for true
matches outside the candidate list. Only S1 of the labelled countries (US, India) get the new rule; other countries
keep the final tag's predictions unchanged (their pc calibration is not validated).

Checks: one S1 per record in the output, US/India predictions inside the cut and owned, every output pair inside the
candidates file (--cands), and (--base-thr) that the model's own threshold rule reproduces the final tag's US/India
predictions exactly (so the change counts are the rule's effect only). Reports change counts by country vs the final
tag. Writes <this dir>/decided_<scores>.parquet (s1, r int64) and decided_<scores>.json.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)

from ber.artifacts import read_table  # noqa: E402
from ber.paths import artifact_path, records_path  # noqa: E402
from common import argmax_owner, candidate_mask  # noqa: E402
from core import expected_f_select, greedy_perfect, to_q  # noqa: E402

LABELLED = ("US", "India")  # countries with training labels: the rule was validated on these only


def load_test(tag: str) -> pd.DataFrame:
    f = pq.ParquetFile(artifact_path("scores", tag, "test"))
    parts = []
    for g in range(f.num_row_groups):
        t = f.read_row_group(g, columns=["s1", "r", "p1", "pc"])
        m = t.column("p1").to_numpy() >= 0.02
        parts.append(pd.DataFrame({c: t.column(c).to_numpy()[m] for c in ("s1", "r", "p1", "pc")}))
    return pd.concat(parts, ignore_index=True)


def s1_country(split: str = "test") -> pd.Series:
    t = pq.read_table(records_path(split), columns=["eid", "country"], filters=[("source", "=", 1)])
    return pd.Series(t.column("country").to_numpy(zero_copy_only=False), index=t.column("eid").to_numpy())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores", default="ameya-s3-v7s")
    ap.add_argument("--final", default="ameya-model-v7s-s3-ops3a")
    ap.add_argument("--rule", default="dp", choices=("dp", "greedy", "thr"))
    ap.add_argument("--shift", type=float, default=0.2)
    ap.add_argument("--lam", type=float, default=0.01)
    ap.add_argument("--thr", type=float, default=0.675)
    ap.add_argument("--out", default="")
    ap.add_argument("--cands", default="ameya-cands-v7s-c2a", help="candidates tag: check every output pair is in its test file")
    ap.add_argument("--base-thr", type=float, default=0.7,
                    help="the model's own threshold: check it reproduces the final tag's US/India predictions")
    args = ap.parse_args()
    t0 = time.perf_counter()

    sc = load_test(args.scores)
    s1, r = sc["s1"].to_numpy(), sc["r"].to_numpy()
    cut = candidate_mask(s1, r, sc["p1"].to_numpy(), 0.02, 2)
    p = np.where(cut, sc["pc"].to_numpy(), np.float32(0)).astype(np.float64)
    own = argmax_owner(s1, r, p)
    country = s1_country("test")
    cs = country.reindex(s1).to_numpy()
    lab = np.isin(cs, LABELLED) & (p > 0)
    print(f"test rows p1>=0.02 {s1.size:,}; in cut {int(cut.sum()):,}; labelled rows with p>0 {int(lab.sum()):,} "
          f"({time.perf_counter() - t0:.0f}s)", flush=True)

    ls1, lr, lp, lown = s1[lab], r[lab], p[lab], own[lab]
    if args.rule == "dp":
        sel = expected_f_select(ls1, to_q(lp, args.shift), lown, lam=args.lam)
    elif args.rule == "greedy":
        order = np.lexsort((-lp, ls1))
        inv = np.empty_like(order)
        inv[order] = np.arange(order.size)
        ks, ko = ls1[order], lown[order]
        start = np.r_[True, ks[1:] != ks[:-1]]
        grp = np.maximum.accumulate(np.where(start, np.arange(ks.size), 0))
        oc = np.cumsum(ko.astype(np.int64))
        base_c = np.where(grp > 0, oc[grp - 1], 0)
        rank_sorted = np.where(ko, oc - base_c - 1, -1)
        sel = greedy_perfect(to_q(lp, args.shift), lown, rank_sorted[inv])
    else:
        sel = lown & (lp > args.thr)
    new_lab = pd.DataFrame({"s1": ls1[sel], "r": lr[sel]})

    fin = read_table("matches", args.final, "test", ["s1", "r"])
    fc = country.reindex(fin["s1"].to_numpy()).to_numpy()
    base_check = {}
    if args.base_thr > 0:
        bsel = lown & (lp > args.base_thr)
        kb = ls1[bsel] * 4_000_000_000 + lr[bsel]
        fl = fin[np.isin(fc, LABELLED)]
        kf = fl["s1"].to_numpy() * 4_000_000_000 + fl["r"].to_numpy()
        base_check = {"base_thr": args.base_thr, "final_labelled_pairs": int(kf.size),
                      "rule_pairs": int(kb.size), "in_final_not_rule": int((~np.isin(kf, kb)).sum()),
                      "in_rule_not_final": int((~np.isin(kb, kf)).sum())}
        print("base reproduction:", base_check, flush=True)
    keep_final = fin[~np.isin(fc, LABELLED)]
    out = pd.concat([new_lab, keep_final], ignore_index=True).astype({"s1": np.int64, "r": np.int64})

    # checks
    dup_r = out["r"].duplicated(keep=False)
    rep = {"scores": args.scores, "final": args.final, "rule": vars(args), "n_pred": len(out),
           "records_with_2_owners": int(dup_r.sum())}
    if dup_r.any():  # a labelled-country prediction collides with a kept (France) one: keep the kept one
        clash = out[dup_r]
        print(f"[warn] {int(dup_r.sum())} rows share a record; dropping the new labelled-country rows", flush=True)
        drop = dup_r & np.isin(country.reindex(out["s1"].to_numpy()).to_numpy(), LABELLED)
        out = out[~drop].reset_index(drop=True)
        rep["clash_dropped"] = int(drop.sum())
        rep["clash_examples"] = clash.head(10).to_dict("records")
    key_cut = s1[cut] * 4_000_000_000 + r[cut]
    key_own = s1[own & (p > 0)] * 4_000_000_000 + r[own & (p > 0)]
    oc_ = country.reindex(out["s1"].to_numpy()).to_numpy()
    k_lab = out.loc[np.isin(oc_, LABELLED), "s1"].to_numpy() * 4_000_000_000 + out.loc[np.isin(oc_, LABELLED), "r"].to_numpy()
    rep["labelled_outside_cut"] = int((~np.isin(k_lab, key_cut)).sum())
    rep["labelled_not_owned"] = int((~np.isin(k_lab, key_own)).sum())
    rep["records_with_2_owners_after"] = int(out["r"].duplicated().sum())
    rep["base_reproduction"] = base_check
    if args.cands:
        cd = read_table("candidates", args.cands, "test", ["s1", "r"])
        kc = np.sort(cd["s1"].to_numpy() * 4_000_000_000 + cd["r"].to_numpy())
        del cd
        ko = out["s1"].to_numpy() * 4_000_000_000 + out["r"].to_numpy()
        pos = np.minimum(np.searchsorted(kc, ko), kc.size - 1)
        rep["outside_candidates"] = int((kc[pos] != ko).sum())
        rep["candidates_pairs"] = int(kc.size)
        del kc
        print(f"pairs outside candidates {args.cands}: {rep['outside_candidates']}", flush=True)

    # change counts by country vs the final tag
    k_out = out["s1"].to_numpy() * 4_000_000_000 + out["r"].to_numpy()
    k_fin = fin["s1"].to_numpy() * 4_000_000_000 + fin["r"].to_numpy()
    add = ~np.isin(k_out, k_fin)
    rem = ~np.isin(k_fin, k_out)
    n_s1 = country.value_counts()
    ch = {}
    for c in sorted(set(country.unique())):
        a_ = add & (oc_ == c)
        r_ = rem & (fc == c)
        ch[str(c)] = {"n_s1": int(n_s1.get(c, 0)), "pred_final": int((fc == c).sum()), "pred_new": int((oc_ == c).sum()),
                      "added": int(a_.sum()), "removed": int(r_.sum()),
                      "s1_changed": int(np.unique(np.r_[out["s1"].to_numpy()[a_], fin["s1"].to_numpy()[r_]]).size),
                      "pred_per_s1_new": round(float((oc_ == c).sum() / max(n_s1.get(c, 1), 1)), 4),
                      "empty_share_new": round(1 - out.loc[oc_ == c, "s1"].nunique() / max(n_s1.get(c, 1), 1), 4)}
    rep["changes_by_country"] = ch
    path = args.out or os.path.join(D, f"decided_{args.scores}.parquet")
    out.to_parquet(path, index=False)
    rep["path"] = path
    rep["runtime_s"] = round(time.perf_counter() - t0)
    json.dump(rep, open(os.path.splitext(path)[0] + ".json", "w"), indent=1, default=str)
    print(json.dumps(rep, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
