"""Error analysis of a model on the full shared holdout: where the macro F0.5 is lost and on which kinds of data.

    python experiments/ameya/model-v1/analysis.py --scores ameya-s2-v2 --s1 ameya-s1-v2 --matches ameya-model-v2 \
        --feats ameya-fx2 --out ameya-analysis-v2 [--examples 40]

Writes work/analysis/<out>/{s1,pairs}.parquet (per holdout S1 / per holdout pair of interest) and prints:
- the loss by S1 outcome (singleton given a match, non-singleton left empty, all wrong, partial misses, extras);
- the counterfactual gain of fixing each pair bucket:
  - FP: fp_orphan (the record matches no S1), fp_owned_elsewhere (it belongs to another S1);
  - FN: fn_not_candidate (blocking), fn_stage0 (filtered by p0), fn_pmin (p1 < P_MIN), fn_lost (another S1 owns
    the record), fn_rejected (owned, not selected by the decision);
- the loss by slice (country, set size, scripts, empty addresses, name frequency, record source);
- the reliability of the calibrated probability per country and source;
- with --examples, random examples of every bucket to <work>/analysis/<out>/examples.txt.
Pair buckets are exclusive; the gains are counterfactual (fix only that bucket), so they do not add up exactly.
"""
from __future__ import annotations

import argparse
import json
import re

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from ber.artifacts import read_table
from ber.paths import artifact_dir, records_path, work_dir
from ber.records import load_truth
from common import argmax_owner, holdout_universe

INDIC = "[ऀ-෿]"
P_MIN = 0.002


def f05(hit: np.ndarray, n_pred: np.ndarray, n_true: np.ndarray) -> np.ndarray:
    denom = 0.25 * n_true + n_pred
    return np.where(denom > 0, 1.25 * hit / np.where(denom > 0, denom, 1.0), 1.0)


def name_key(s: pd.Series) -> pd.Series:
    return s.str.lower().str.replace(r"[^0-9a-zऀ-෿]+", " ", regex=True).str.strip()


def build(args) -> tuple[pd.DataFrame, pd.DataFrame]:
    universe, country = holdout_universe()
    uni = np.sort(universe)
    truth = load_truth()
    th = truth[truth["s1"].isin(uni)].reset_index(drop=True)
    tau0 = json.loads((artifact_dir("models", args.s1) / "config.json").read_text())["tau0"]

    sc = read_table("scores", args.scores, "train", ["s1", "r", "y", "p1", "pc"])
    p0 = read_table("scores", args.s1, "train", ["s1", "p0"])
    if not (p0["s1"].to_numpy() == sc["s1"].to_numpy()).all():
        raise ValueError("stage-1 and stage-2 scores are not row-aligned")
    sc["p0"] = p0["p0"].to_numpy(np.float32)
    del p0
    s1, r, pc = sc["s1"].to_numpy(), sc["r"].to_numpy(), sc["pc"].to_numpy(np.float32)
    own = argmax_owner(s1, r, pc)
    # record side: best pc over all S1 and the S1 holding it (the owner), second best
    order = np.lexsort((s1, -pc, r))
    rs = r[order]
    first = np.r_[True, rs[1:] != rs[:-1]]
    best_s1 = pd.Series(s1[order][first], index=rs[first])
    best_p = pd.Series(pc[order][first], index=rs[first])
    n_c_r = pd.Series(np.diff(np.r_[np.flatnonzero(first), rs.size]), index=rs[first])
    # S1 side: rank of the pair by pc inside its S1
    order = np.lexsort((-pc, s1))
    ss = s1[order]
    start = np.flatnonzero(np.r_[True, ss[1:] != ss[:-1]])
    rank = np.empty(s1.size, np.int32)
    rank[order] = np.arange(s1.size) - np.repeat(start, np.diff(np.r_[start, ss.size]))
    n_c_s1 = pd.Series(np.diff(np.r_[start, ss.size]), index=ss[start])

    pred = read_table("matches", args.matches, "train")
    pred = pred[pred["s1"].isin(uni)]
    key_pred = pred["s1"].to_numpy() * 4_000_000_000 + pred["r"].to_numpy()
    hold = np.isin(s1, uni)
    key = s1 * 4_000_000_000 + r
    is_pred = np.zeros(s1.size, bool)
    is_pred[hold] = np.isin(key[hold], key_pred)
    keep = hold & ((sc["y"].to_numpy() == 1) | is_pred | (pc >= 0.01) | (rank < 3))
    pairs = sc.loc[keep, ["s1", "r", "y", "p0", "p1", "pc"]].reset_index(drop=True)
    pairs["own"], pairs["pred"], pairs["s_rank"] = own[keep], is_pred[keep], rank[keep]
    del sc, own, is_pred, rank, key, s1, r, pc, order, rs, ss
    pairs["r_best"] = best_p.reindex(pairs["r"]).to_numpy()
    pairs["r_best_s1"] = best_s1.reindex(pairs["r"]).to_numpy()
    pairs["n_cands_r"] = n_c_r.reindex(pairs["r"]).to_numpy()

    # true pairs that are not candidates
    kt = th["s1"].to_numpy() * 4_000_000_000 + th["r"].to_numpy()
    kp = pairs["s1"].to_numpy() * 4_000_000_000 + pairs["r"].to_numpy()
    miss = th[~np.isin(kt, kp)].copy()
    cand_all = read_table("scores", args.scores, "train", ["s1", "r"])
    ca = cand_all[cand_all["s1"].isin(uni)]
    kc = ca["s1"].to_numpy() * 4_000_000_000 + ca["r"].to_numpy()
    miss_nc = miss[~np.isin(miss["s1"].to_numpy() * 4_000_000_000 + miss["r"].to_numpy(), kc)]
    del cand_all, ca, kc
    if len(miss_nc) != len(miss):
        raise ValueError("a candidate true pair was dropped from the pair table")
    nc = miss_nc.assign(y=1, p0=np.nan, p1=np.nan, pc=np.nan, own=False, pred=False, s_rank=-1)
    nc["r_best"] = best_p.reindex(nc["r"]).to_numpy()
    nc["r_best_s1"] = best_s1.reindex(nc["r"]).to_numpy()
    nc["n_cands_r"] = n_c_r.reindex(nc["r"]).fillna(0).to_numpy()
    pairs = pd.concat([pairs, nc], ignore_index=True)

    owner = truth.set_index("r")["s1"]
    pairs["true_owner"] = owner.reindex(pairs["r"]).fillna(-1).astype(np.int64).to_numpy()
    y = pairs["y"].to_numpy() == 1
    pr = pairs["pred"].to_numpy()
    kind = np.full(len(pairs), "", object)
    kind[pr & ~y & (pairs["true_owner"].to_numpy() < 0)] = "fp_orphan"
    kind[pr & ~y & (pairs["true_owner"].to_numpy() >= 0)] = "fp_owned_elsewhere"
    fn = y & ~pr
    p0v, p1v = pairs["p0"].to_numpy(), pairs["p1"].to_numpy()
    kind[fn & np.isnan(p0v)] = "fn_not_candidate"
    kind[fn & ~np.isnan(p0v) & (p0v < tau0)] = "fn_stage0"
    kind[fn & (p0v >= tau0) & (p1v < P_MIN)] = "fn_pmin"
    kind[fn & (p0v >= tau0) & (p1v >= P_MIN) & ~pairs["own"].to_numpy()] = "fn_lost"
    kind[fn & (p0v >= tau0) & (p1v >= P_MIN) & pairs["own"].to_numpy()] = "fn_rejected"
    kind[y & pr] = "tp"
    pairs["kind"] = kind

    # per S1
    ent = pd.DataFrame(index=pd.Index(uni, name="s1"))
    ent["country"] = country.reindex(uni).to_numpy()
    ent["n_true"] = th.groupby("s1").size().reindex(uni).fillna(0).astype(int).to_numpy()
    ent["n_pred"] = pred.groupby("s1").size().reindex(uni).fillna(0).astype(int).to_numpy()
    ent["n_hit"] = pairs[pairs["kind"] == "tp"].groupby("s1").size().reindex(uni).fillna(0).astype(int).to_numpy()
    ent["f05"] = f05(ent["n_hit"].to_numpy(), ent["n_pred"].to_numpy(), ent["n_true"].to_numpy())
    ent["n_cands"] = n_c_s1.reindex(uni).fillna(0).astype(int).to_numpy()
    for k in ("fp_orphan", "fp_owned_elsewhere", "fn_not_candidate", "fn_stage0", "fn_pmin", "fn_lost", "fn_rejected"):
        ent[k] = pairs[pairs["kind"] == k].groupby("s1").size().reindex(uni).fillna(0).astype(int).to_numpy()

    # record attributes
    rec = pq.read_table(records_path("train"), columns=["eid", "source", "country", "name", "address"]).to_pandas()
    rec = rec.set_index("eid")
    s1rec = rec[rec["source"] == 1]
    nk = name_key(s1rec["name"])
    ent["s1_name_dup"] = nk.map(nk.value_counts()).reindex(uni).fillna(1).astype(int).to_numpy()
    nm, ad = rec["name"].reindex(uni), rec["address"].reindex(uni)
    ent["s1_indic_name"] = nm.str.contains(INDIC).fillna(False).to_numpy()
    ent["s1_indic_addr"] = ad.str.contains(INDIC).fillna(False).to_numpy()
    ent["s1_addr_empty"] = (ad.fillna("").str.strip() == "").to_numpy()
    ent["s1_addr_digit"] = ad.fillna("").str.contains("[0-9]").to_numpy()
    ent["s1_name_ntok"] = nm.fillna("").str.split().str.len().to_numpy()
    rr = pairs["r"]
    pairs["r_source"] = rec["source"].reindex(rr).to_numpy()
    pairs["r_indic_name"] = rec["name"].reindex(rr).str.contains(INDIC).fillna(False).to_numpy()
    pairs["r_addr_empty"] = (rec["address"].reindex(rr).fillna("").str.strip() == "").to_numpy()
    pairs["s1_indic_name"] = ent["s1_indic_name"].reindex(pairs["s1"]).to_numpy()
    pairs["country"] = ent["country"].reindex(pairs["s1"]).to_numpy()
    out = work_dir() / "analysis" / args.out
    out.mkdir(parents=True, exist_ok=True)
    ent.reset_index().to_parquet(out / "s1.parquet")
    pairs.to_parquet(out / "pairs.parquet")
    return ent, pairs


def report(ent: pd.DataFrame, pairs: pd.DataFrame) -> dict:
    res = {}
    n = len(ent)
    loss = 1 - ent["f05"]
    L = loss.sum()
    hit, npred, ntrue = ent["n_hit"].to_numpy(), ent["n_pred"].to_numpy(), ent["n_true"].to_numpy()
    res["macro_f05"] = round(float(ent["f05"].mean()), 5)
    res["loss_total"] = round(float(L / n), 5)
    res["precision"] = round(float(hit.sum() / max(npred.sum(), 1)), 4)
    res["recall"] = round(float(hit.sum() / max(ntrue.sum(), 1)), 4)
    fp = npred - hit
    fnn = ntrue - hit
    outcome = np.select(
        [(ntrue == 0) & (npred > 0), (ntrue > 0) & (npred == 0), (ntrue > 0) & (npred > 0) & (hit == 0),
         (fp == 0) & (fnn > 0), (fp > 0) & (fnn == 0), (fp > 0) & (fnn > 0)],
        ["singleton_given_matches", "nonsingleton_left_empty", "all_wrong", "misses_only", "extras_only",
         "misses_and_extras"], "perfect")
    ent = ent.assign(outcome=outcome, loss=loss)
    t = ent.groupby("outcome").agg(s1=("loss", "size"), loss=("loss", "sum"))
    t["share_of_s1"] = (t["s1"] / n).round(5)
    t["loss_share"] = (t["loss"] / L).round(4)
    t["macro_pts"] = (t["loss"] / n).round(5)
    res["by_outcome"] = t.drop(columns="loss").to_dict("index")
    # counterfactual bucket gains
    base = ent["f05"].mean()
    gains = {}
    for k in ("fp_orphan", "fp_owned_elsewhere"):
        gains[k] = (int(ent[k].sum()), round(float(f05(hit, npred - ent[k].to_numpy(), ntrue).mean() - base), 5))
    for k in ("fn_not_candidate", "fn_stage0", "fn_pmin", "fn_lost", "fn_rejected"):
        a = ent[k].to_numpy()
        gains[k] = (int(a.sum()), round(float(f05(hit + a, npred + a, ntrue).mean() - base), 5))
    a = sum(ent[k].to_numpy() for k in ("fn_not_candidate", "fn_stage0", "fn_pmin", "fn_lost", "fn_rejected"))
    gains["all_fn"] = (int(a.sum()), round(float(f05(hit + a, npred + a, ntrue).mean() - base), 5))
    b = ent["fp_orphan"].to_numpy() + ent["fp_owned_elsewhere"].to_numpy()
    gains["all_fp"] = (int(b.sum()), round(float(f05(hit, npred - b, ntrue).mean() - base), 5))
    res["bucket_gain_if_fixed"] = gains
    # loss by slice
    def sl(col, vals=None):
        g = ent.groupby(col if vals is None else vals)
        d = pd.DataFrame({"s1": g.size(), "f05": g["f05"].mean().round(4), "loss_share": (g["loss"].sum() / L).round(4)})
        return d.to_dict("index")
    res["by_country"] = sl("country")
    res["by_n_true"] = sl(None, ent["n_true"].clip(upper=8))
    res["by_s1_indic_name"] = sl(None, ent["country"] + "/" + np.where(ent["s1_indic_name"], "indic", "latin"))
    res["by_s1_addr_empty"] = sl("s1_addr_empty")
    res["by_s1_name_dup"] = sl(None, pd.cut(ent["s1_name_dup"], [0, 1, 2, 5, 20, 100, 10**7]).astype(str))
    res["by_n_cands"] = sl(None, pd.cut(ent["n_cands"], [-1, 0, 5, 15, 30, 60, 10**6]).astype(str))
    # pair buckets by record attributes
    bad = pairs[pairs["kind"].str.startswith("f")]
    res["pair_kind_by_country"] = pd.crosstab(bad["kind"], bad["country"]).to_dict("index")
    res["pair_kind_by_r_source"] = pd.crosstab(bad["kind"], bad["r_source"]).to_dict("index")
    tp_all = pairs[pairs["y"] == 1]
    res["true_pairs_by_kind_and_r_indic"] = pd.crosstab(tp_all["kind"], tp_all["r_indic_name"]).to_dict("index")
    res["true_pairs_by_kind_and_r_addr_empty"] = pd.crosstab(tp_all["kind"], tp_all["r_addr_empty"]).to_dict("index")
    rej = pairs[pairs["kind"] == "fn_rejected"]
    res["fn_rejected_pc_quantiles"] = rej["pc"].quantile([.1, .25, .5, .75, .9]).round(4).to_dict()
    res["fn_lost_owner_is_true"] = round(float((pairs.loc[pairs["kind"] == "fn_lost", "r_best_s1"]
                                               == pairs.loc[pairs["kind"] == "fn_lost", "true_owner"]).mean()), 4)
    fpp = pairs[pairs["kind"].str.startswith("fp")]
    res["fp_pc_quantiles"] = fpp["pc"].quantile([.1, .25, .5, .75, .9]).round(4).to_dict()
    # reliability of pc on the holdout pairs of interest, by country and source
    cand = pairs[pairs["pc"].notna() & (pairs["p1"] >= P_MIN)]
    cand = cand.assign(bin=np.clip((cand["pc"] * 10).astype(int), 0, 9))
    rel = cand.groupby(["country", "r_source", "bin"]).agg(p=("pc", "mean"), y=("y", "mean"), n=("y", "size"))
    res["reliability"] = {f"{c}/S{s}": g.droplevel([0, 1]).round(3).to_dict("index")
                          for (c, s), g in rel.groupby(level=[0, 1])}
    return res


def examples(pairs: pd.DataFrame, k: int, path) -> None:
    rec = pq.read_table(records_path("train"), columns=["eid", "name", "address"]).to_pandas().set_index("eid")
    lines = []
    for kind in ("fn_not_candidate", "fn_rejected", "fn_lost", "fn_pmin", "fn_stage0", "fp_orphan",
                 "fp_owned_elsewhere"):
        sub = pairs[pairs["kind"] == kind]
        lines.append(f"\n=== {kind}: {len(sub)} pairs")
        for _, x in sub.sample(min(k, len(sub)), random_state=0).iterrows():
            s, r = int(x["s1"]), int(x["r"])
            lines.append(f"[{x['country']}] pc={x['pc']:.3f} p1={x['p1']:.3f} rank={x['s_rank']} r_best={x['r_best']:.3f}")
            lines.append(f"   S1 : {rec.at[s, 'name'][:60]:60s} | {rec.at[s, 'address'][:90]}")
            lines.append(f"   R{r // 10**9} : {rec.at[r, 'name'][:60]:60s} | {rec.at[r, 'address'][:90]}")
            o = int(x["true_owner"])
            if o >= 0 and o != s:
                lines.append(f"   own: {rec.at[o, 'name'][:60]:60s} | {rec.at[o, 'address'][:90]}")
            b = x["r_best_s1"]
            if not np.isnan(b) and int(b) not in (s, o):
                b = int(b)
                lines.append(f"   top: {rec.at[b, 'name'][:60]:60s} | {rec.at[b, 'address'][:90]}  (pc {x['r_best']:.3f})")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores", default="ameya-s2-v2")
    ap.add_argument("--s1", default="ameya-s1-v2")
    ap.add_argument("--matches", default="ameya-model-v2")
    ap.add_argument("--out", default="ameya-analysis-v2")
    ap.add_argument("--examples", type=int, default=0)
    ap.add_argument("--reuse", action="store_true", help="read the tables written by an earlier run")
    args = ap.parse_args()
    out = work_dir() / "analysis" / args.out
    if args.reuse:
        ent, pairs = pd.read_parquet(out / "s1.parquet").set_index("s1"), pd.read_parquet(out / "pairs.parquet")
    else:
        ent, pairs = build(args)
    res = report(ent, pairs)
    (out / "report.json").write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    print(json.dumps(res, indent=1, default=str))
    if args.examples:
        examples(pairs, args.examples, out / "examples.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
