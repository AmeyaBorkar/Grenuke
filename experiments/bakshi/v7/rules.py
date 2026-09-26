"""Audit v7 rule populations, then apply measured rules to a cached model run.

Example audit (released dev kit; not a full-v6 metric):
  python experiments/bakshi/v7/rules.py audit --features-file ... --scores-file ...

No rule addition is enabled from its name alone. Fit the policy on folds 5-19,
inspect its held-out residual precision, and use the same policy on unseen-label
countries. Full output generation requires cached pre-rule matches and scores.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
import pyarrow.parquet as pq

MODEL_DIR = Path(__file__).resolve().parents[2] / "ameya" / "model-v1"
sys.path.insert(0, str(MODEL_DIR))
from post_ops import classify, s1_vocab
from common import argmax_owner, candidate_mask
from ber.artifacts import read_table, write_report, write_table
from ber.eval.splits import fold_of
from ber.features.context import numstreet_keys
from ber.features.rule_edits import address_evidence, composed_edits
from ber.paths import artifact_path, records_path, work_dir
from ber.block.text import fold

K = 4_000_000_000
BASE_ADD_OPS = ("A", "APP", "ACR")  # NUM/CODE are disabled in the current submission recipe.


def pair_keys(d):
    return d.s1.to_numpy(np.int64) * K + d.r.to_numpy(np.int64)


def preselect(path: Path, target: np.ndarray | None = None) -> pd.DataFrame:
    cols = ["s1", "r", "num__rel1", "name__fz_inter", "name__fz_n_extra_r", "name__len_r", "name__inter"]
    f = pq.ParquetFile(path)
    if "y" in f.schema.names:
        cols.append("y")
    parts = []
    for b in f.iter_batches(batch_size=250_000, columns=cols):
        d = b.to_pandas()
        # Broader than v2: composite edits can have more than one unmatched record word.
        sel = (d.num__rel1 == 1) & ((d.name__fz_inter >= 1) | ((d.name__len_r <= 3) & (d.name__inter == 0)))
        if target is not None:
            sel &= d.s1.isin(target)
        parts.append(d.loc[sel, ["s1", "r"] + (["y"] if "y" in cols else [])])
    return pd.concat(parts, ignore_index=True)


def text_for_pairs(d, split):
    ids = np.unique(np.r_[d.s1.to_numpy(), d.r.to_numpy()])
    t = ds.dataset(records_path(split)).to_table(columns=["eid", "name", "address"],
                                                filter=ds.field("eid").isin(ids))
    frame = t.to_pandas().set_index("eid")
    if not pd.Index(ids).isin(frame.index).all():
        raise ValueError("Raw records are missing pair IDs")
    names = pd.Series(fold(t["name"].combine_chunks()).to_numpy(zero_copy_only=False), index=t["eid"].to_numpy())
    keys = pd.Series(numstreet_keys(t["address"].combine_chunks()), index=t["eid"].to_numpy())
    return frame, names, keys


def profiles(d, split, cty, vocab):
    if d.empty:
        return pd.DataFrame(columns=["s1", "r", "op", "combination", "address_add_ok", "address_conflict"])
    raw, names, keys = text_for_pairs(d, split)
    # Baseline classification stays byte-compatible with current main.
    base = classify(d.assign(cty=cty.reindex(d.s1).to_numpy()), names, keys, vocab)
    addresses = address_evidence(raw.address.reindex(d.s1).to_numpy(), raw.address.reindex(d.r).to_numpy())
    edits = composed_edits(raw.name.reindex(d.s1).to_numpy(), raw.name.reindex(d.r).to_numpy())
    edits = edits.rename(columns={c: "edit__" + c for c in edits.columns if c != "combination"})
    return pd.concat([base.reset_index(drop=True), addresses, edits], axis=1)


def wilson(y, z=1.96):
    n = len(y)
    if not n:
        return None, None
    p = float(np.mean(y))
    center = (p + z*z/(2*n))/(1 + z*z/n)
    half = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n))/(1 + z*z/n)
    return float(center-half), float(center+half)


def population_table(d):
    rows = []
    for (country, family, selected), a in d.groupby(["cty", "family", "base_pred"], sort=True):
        lo, hi = wilson(a.y)
        rows.append({"country": str(country), "family": str(family), "base_predicted": bool(selected),
                     "pairs": len(a), "truth_rate": float(a.y.mean()), "wilson_low": lo, "wilson_high": hi,
                     "eligible_adds": int(a.eligible_add.sum()), "address_conflicts": int(a.address_conflict.sum())})
    return rows


def fit_policy(d, min_support=100, precision_floor=0.98):
    """Conservative shared rules; each labeled country must independently support them."""
    proposals = []
    for family in ("swap_list", "multi_append", "drop_multi_list"):
        action = "drop" if family == "swap_list" else "add"
        eligible = d.base_pred if action == "drop" else d.eligible_add
        a = d[(d.combination == family) & d.address_add_ok & eligible]
        countries = sorted(d.cty.unique())
        evidence, accepted = [], bool(countries)
        for c in countries:
            b = a[a.cty == c]
            lo, hi = wilson(b.y)
            keep = len(b) >= min_support and (hi <= 1 - precision_floor if action == "drop" else lo >= precision_floor)
            accepted &= keep
            evidence.append({"country": str(c), "n": len(b), "truth_rate": float(b.y.mean()) if len(b) else None,
                             "wilson_low": lo, "wilson_high": hi, "passes": bool(keep)})
        proposals.append({"family": family, "action": action, "enabled": False,
                          "fit_passes": bool(accepted), "evidence": evidence})
    return {"version": 7, "min_support": min_support, "precision_floor": precision_floor,
            "fit_folds": "5-19", "validation_passed": False,
            "address_guard_enabled": False, "rules": proposals}


def eligible_profiles(d, scores, base, candidates):
    base_keys = pair_keys(base)
    d = d.merge(scores[["s1", "r", "p1", "pc"]], on=["s1", "r"], how="left", validate="one_to_one")
    keys = pair_keys(d)
    if d.pc.isna().any():
        raise ValueError("Some selected feature pairs have no score row")
    d["base_pred"] = np.isin(keys, base_keys)
    d["in_cands"] = np.isin(keys, pair_keys(candidates))
    owner = scores.loc[argmax_owner(scores.s1.to_numpy(), scores.r.to_numpy(), scores.pc.to_numpy()), ["s1", "r"]]
    owner_keys = pair_keys(owner)
    d["owned"] = np.isin(keys, owner_keys)
    d["eligible_add"] = d.in_cands & d.owned & ~d.base_pred & ~d.r.isin(base.r)
    d["family"] = np.where(d.combination != "", "combo:" + d.combination.astype(str), d.op)
    return d


def apply_rules(base, p, policy, enable_combined=True):
    """Pure pair-table transform; caller verifies candidate subset and country scope."""
    keys = pair_keys(base)
    drops = p.loc[(p.op == "B") & p.base_pred]
    add_mask = p.op.isin(BASE_ADD_OPS) & p.eligible_add
    if policy.get("address_guard_enabled", False) and policy.get("validation_passed", False):
        add_mask &= ~p.address_conflict
    adds = p.loc[add_mask]
    if enable_combined and policy.get("validation_passed", False):
        for rule in policy["rules"]:
            if not rule["enabled"]:
                continue
            sel = (p.combination == rule["family"]) & p.address_add_ok
            if rule["action"] == "drop":
                drops = pd.concat([drops, p.loc[sel & p.base_pred]])
            else:
                adds = pd.concat([adds, p.loc[sel & p.eligible_add]])
    out = pd.concat([base.loc[~np.isin(keys, pair_keys(drops)), ["s1", "r"]], adds[["s1", "r"]]], ignore_index=True)
    out = out.drop_duplicates(["s1", "r"]).sort_values(["s1", "r"], kind="stable").reset_index(drop=True)
    if out.r.duplicated().any():
        raise ValueError("v7 produced conflicting owners")
    return out


def audit(args):
    fpath, spath = Path(args.features_file), Path(args.scores_file)
    d = preselect(fpath)
    print(f"Selected {len(d):,} numbered/name-edit candidates", flush=True)
    rec = ds.dataset(records_path("train")).to_table(columns=["country"])
    countries = set(pc.unique(rec["country"]).to_pylist())
    del rec
    cty, vocab = s1_vocab("train", countries)
    d = profiles(d, "train", cty, vocab)
    scores = pd.read_parquet(spath, columns=["s1", "r", "p1", "pc"])
    own = argmax_owner(scores.s1.to_numpy(), scores.r.to_numpy(), scores.pc.to_numpy())
    base = scores.loc[own & (scores.pc > args.threshold), ["s1", "r"]]
    keep = candidate_mask(scores.s1.to_numpy(), scores.r.to_numpy(), scores.p1.to_numpy(), 0.02, 2)
    candidates = scores.loc[keep, ["s1", "r"]]
    d = eligible_profiles(d, scores, base, candidates)
    d["fold"] = fold_of(d.s1.to_numpy())
    fit, hold = d[d.fold >= 5], d[d.fold < 5]
    policy = fit_policy(fit, args.min_support, args.precision_floor)
    veto = d[d.op.isin(BASE_ADD_OPS) & d.eligible_add & d.address_conflict]
    policy["address_guard_evidence"] = [{"country": str(c), "fold": int(f), "vetoed": len(a),
        "true_vetoed": int(a.y.sum())} for (c, f), a in veto.groupby(["cty", "fold"])]
    out = work_dir() / "v7" / args.tag
    out.mkdir(parents=True, exist_ok=True)
    d.to_parquet(out / "profiles.parquet", index=False)
    (out / "policy.json").write_text(json.dumps(policy, indent=2), encoding="utf-8")
    report = {"features_file": str(fpath), "scores_file": str(spath), "threshold": args.threshold,
        "population_fit": population_table(fit), "population_holdout": population_table(hold), "policy": policy,
        "note": "Released dev-v3 diagnostic; inferred ownership is on the sliced graph. Not a full-v6 gain."}
    (out / "audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"output_dir": str(out), "policy": policy}, indent=2), flush=True)
    return 0


def apply(args):
    needed = [artifact_path("matches", args.base, "test"), artifact_path("scores", args.scores, "test"),
              artifact_path("candidates", args.cands, "test"), artifact_path("features", args.feats + "-str", "test")]
    missing = [str(p) for p in needed if not p.exists()]
    if missing:
        raise FileNotFoundError("Required full-run artifacts are missing:\n" + "\n".join(missing))
    policy = json.loads(Path(args.policy).read_text(encoding="utf-8"))
    tr = ds.dataset(records_path("train")).to_table(columns=["country"])
    te = ds.dataset(records_path("test")).to_table(columns=["country"])
    targets = set(pc.unique(te["country"]).to_pylist()) - set(pc.unique(tr["country"]).to_pylist())
    del tr, te
    cty, vocab = s1_vocab("test", targets)
    target_ids = cty.index[cty.isin(targets)].to_numpy()
    d = profiles(preselect(needed[-1], target_ids), "test", cty, vocab)
    base = read_table("matches", args.base, "test")
    scores = read_table("scores", args.scores, "test", ["s1", "r", "p1", "pc"])
    cands = read_table("candidates", args.cands, "test", ["s1", "r"])
    p = eligible_profiles(d, scores, base, cands)
    out = apply_rules(base, p, policy, not args.no_combined)
    if not np.isin(pair_keys(out), pair_keys(cands)).all():
        raise ValueError("Matches outside final candidate set")
    untouched = ~base.s1.isin(target_ids)
    if not np.array_equal(np.sort(pair_keys(base[untouched])), np.sort(pair_keys(out[~out.s1.isin(target_ids)]))):
        raise ValueError("Labeled-country predictions changed")
    inputs = {"matches": args.base, "scores": args.scores, "candidates": args.cands, "features": args.feats}
    write_table(out, "matches", args.tag, "test", command="v7 rules apply", inputs=inputs, policy=policy)
    write_report(args.tag, {"base_pairs": len(base), "new_pairs": len(out),
                           "targets": sorted(targets), "policy": policy}, inputs=inputs)
    print(f"v7 wrote {len(out):,} pairs; candidate inclusion, ownership and labeled-country invariance verified.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    a = sub.add_parser("audit")
    a.add_argument("--features-file", required=True)
    a.add_argument("--scores-file", required=True)
    a.add_argument("--tag", default="bakshi-rules-v7-dev")
    a.add_argument("--threshold", type=float, default=0.70)
    a.add_argument("--min-support", type=int, default=100)
    a.add_argument("--precision-floor", type=float, default=0.98)
    b = sub.add_parser("apply")
    b.add_argument("--base", required=True, help="pre-France-rule matches, e.g. ameya-model-v6all-c2")
    b.add_argument("--scores", default="ameya-s2-v6all")
    b.add_argument("--cands", default="ameya-cands-v6all-c2")
    b.add_argument("--feats", default="ameya-fx5")
    b.add_argument("--policy", required=True)
    b.add_argument("--tag", default="bakshi-model-v7")
    b.add_argument("--no-combined", action="store_true")
    args = ap.parse_args()
    return audit(args) if args.command == "audit" else apply(args)


if __name__ == "__main__":
    raise SystemExit(main())
