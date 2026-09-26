"""Probe strict complete-name/address rescue using only provided raw records."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
from rapidfuzz import fuzz, process

from ber.block.text import fold
from ber.eval.gates import compare
from ber.eval.splits import fold_of, in_dev_sample
from ber.paths import records_path, truth_path, work_dir
from ber.artifacts import write_report
from rules import argmax_owner, pair_keys, wilson

NORM_FIELDS = ["country", "n_full", "a_street", "a_city", "a_num1", "a_num1_sfx", "a_unit"]

def canonical(a):
    return pc.utf8_trim_whitespace(pc.replace_substring_regex(fold(a), r"[^a-z0-9]+", " "))


def keys(table):
    if "n_full" in table.schema.names:
        n, a, city = table["n_full"], table["a_street"], table["a_city"]
        ok = pc.and_(pc.match_substring_regex(n, r"[a-z].* [a-z]"),
                     pc.and_(pc.match_substring_regex(a, r"[a-z]+ [a-z]+"),
                             pc.and_(pc.greater_equal(table["a_num1"], 0), pc.not_equal(city, ""))))
        d = pa.table({f: table[f] for f in NORM_FIELDS}).to_pandas(types_mapper=pd.ArrowDtype)
        return pd.util.hash_pandas_object(d, index=False).to_numpy(np.uint64), ok.to_numpy(zero_copy_only=False)
    n, a = canonical(table["name"]), canonical(table["address"])
    # Retain legal forms, every street/locality token, and their order.
    # Require content-rich fields; name-only / absent-address matches are excluded.
    ok = pc.and_(pc.match_substring_regex(n, r"[a-z].* [a-z]"),
                 pc.and_(pc.match_substring_regex(a, r"[0-9]"),
                         pc.match_substring_regex(a, r"[a-z]+ [a-z]+")))
    d = pa.table({"country": table["country"], "name": n, "address": a}).to_pandas(types_mapper=pd.ArrowDtype)
    return pd.util.hash_pandas_object(d, index=False).to_numpy(np.uint64), ok.to_numpy(zero_copy_only=False)


def retrieve(split, target_s1=None, norm_file=None):
    data = ds.dataset(norm_file if norm_file else records_path(split))
    fields = NORM_FIELDS if norm_file else ["name", "address", "country"]
    t = data.to_table(columns=["eid"] + fields, filter=ds.field("source") == 1)
    hashed, ok = keys(t)
    owners = pd.DataFrame({"key": hashed[ok], "s1": t["eid"].to_numpy()[ok]})
    # Ambiguity is checked across all S1, including those outside a dev slice.
    owners = owners[~owners.key.duplicated(keep=False)]
    if target_s1 is not None:
        owners = owners[owners.s1.isin(target_s1)]
    del t, hashed, ok
    parts = []
    scanned = 0
    for number, batch in enumerate(data.scanner(columns=["eid"] + fields,
                              filter=ds.field("source") != 1, batch_size=250_000).to_batches()):
        h, valid = keys(batch)
        r = pd.DataFrame({"key": h[valid], "r": batch["eid"].to_numpy()[valid]})
        parts.append(r.merge(owners, on="key", how="inner", validate="many_to_one")[["s1", "r"]])
        scanned += len(batch)
        if number % 10 == 9:
            print(f"Scanned {scanned:,} records", flush=True)
    result = pd.concat(parts, ignore_index=True)
    # Verify text equality after the hash join; hash collisions never imply a match.
    ids = np.unique(np.r_[result.s1.to_numpy(), result.r.to_numpy()])
    text = data.to_table(columns=["eid"] + fields, filter=ds.field("eid").isin(ids))
    if norm_file:
        frame = text.to_pandas().set_index("eid")
    else:
        n, a = canonical(text["name"]), canonical(text["address"])
        frame = pa.table({"eid": text["eid"], "name": n, "address": a, "country": text["country"]}).to_pandas().set_index("eid")
    left, right = frame.reindex(result.s1), frame.reindex(result.r)
    exact = (left.to_numpy() == right.to_numpy()).all(axis=1)
    if not exact.all():
        raise ValueError("Hash candidate failed exact text verification")
    return result


def inspect_residuals(result, split):
    """Expose counterexamples to parsed keys; flags do not authorize edits."""
    if result.empty:
        return result.assign(numeric_sequence_equal=pd.Series(dtype=bool),
                             existing_owner_compatible=pd.Series(dtype=bool))
    old = result.existing_owner.to_numpy()
    ids = np.unique(np.r_[result.s1.to_numpy(), result.r.to_numpy(), old[old >= 0]])
    t = ds.dataset(records_path(split)).to_table(columns=["eid", "name", "address"],
                                                 filter=ds.field("eid").isin(ids))
    nums = pc.utf8_trim_whitespace(pc.replace_substring_regex(t["address"], r"[^0-9]+", " "))
    names, addresses = canonical(t["name"]), canonical(t["address"])
    frame = pa.table({"eid": t["eid"], "nums": nums, "name": names, "address": addresses}).to_pandas().set_index("eid")
    left, right = frame.reindex(result.s1), frame.reindex(result.r)
    result = result.copy()
    result["numeric_sequence_equal"] = left.nums.to_numpy() == right.nums.to_numpy()
    previous = frame.reindex(old).fillna("")
    address_subset = process.cpdist(previous.address.to_numpy(), right.address.to_numpy(),
                                    scorer=fuzz.token_set_ratio, workers=-1) == 100
    result["existing_owner_compatible"] = (old >= 0) & address_subset & (previous.name.to_numpy() == right.name.to_numpy())
    return result


def main(args):
    out = work_dir() / "v7" / args.tag
    out.mkdir(parents=True, exist_ok=True)
    if args.split == "train":
        t = ds.dataset(records_path("train")).to_table(columns=["eid", "country"], filter=ds.field("source") == 1)
        all_ids = t["eid"].to_numpy()
        ids = all_ids[in_dev_sample(all_ids)]
        countries = pd.Series(t["country"].to_numpy(zero_copy_only=False), index=all_ids)
        pred = pd.read_parquet(args.scores, columns=["s1", "r", "pc"])
        mask = argmax_owner(pred.s1.to_numpy(), pred.r.to_numpy(), pred.pc.to_numpy()) & (pred.pc > 0.70)
        base = pred.loc[mask, ["s1", "r"]]
        del pred, t
        print("Retrieving strict pairs for train dev entities", flush=True)
        rescued = retrieve("train", ids, args.norm_file)
        rescued.to_parquet(out / "train_exact_pairs.parquet", index=False)
        assigned = pd.Series(base.s1.to_numpy(), index=base.r)
        rescued["existing_owner"] = assigned.reindex(rescued.r).fillna(-1).to_numpy(np.int64)
        rescued = rescued[rescued.existing_owner != rescued.s1].reset_index(drop=True)
        rescued["operation"] = np.where(rescued.existing_owner == -1, "add", "transfer")
        truth = ds.dataset(truth_path()).to_table(filter=ds.field("s1").isin(ids)).to_pandas()
        rescued["y"] = np.isin(pair_keys(rescued), pair_keys(truth))
        rescued["fold"] = fold_of(rescued.s1.to_numpy())
        rows = []
        for (country, holdout, operation), p in rescued.assign(country=countries.reindex(rescued.s1).to_numpy(),
                                                    holdout=rescued.fold < 5).groupby(["country", "holdout", "operation"]):
            lo, hi = wilson(p.y)
            rows.append({"country": str(country), "holdout": bool(holdout), "operation": str(operation), "n": len(p),
                         "true": int(p.y.sum()), "precision": float(p.y.mean()), "wilson_low": lo, "wilson_high": hi})
        new = pd.concat([base[~base.r.isin(rescued.r)], rescued[["s1", "r"]]], ignore_index=True)
        hold = ids[fold_of(ids) < 5]
        gate = compare(base, new, truth, hold, groups=countries, min_gain=0.0)
        report = {"split": "train", "residuals": rows, "gate": gate,
                  "note": "v3 dev baseline with sample-graph ownership; not a full v5/v6 gate", "enable": False}
    else:
        base = pd.read_parquet(args.base_pairs, columns=["s1", "r"])
        print("Retrieving strict pairs for full test", flush=True)
        rescued = retrieve("test", norm_file=args.norm_file)
        rescued.to_parquet(out / "test_exact_pairs.parquet", index=False)
        assigned = pd.Series(base.s1.to_numpy(), index=base.r)
        rescued["existing_owner"] = assigned.reindex(rescued.r).fillna(-1).to_numpy(np.int64)
        rescued = rescued[rescued.existing_owner != rescued.s1].reset_index(drop=True)
        rescued["operation"] = np.where(rescued.existing_owner == -1, "add", "transfer")
        report = {"split": "test", "strict_residual_pairs": len(rescued),
                  "operations": {str(k): int(v) for k, v in rescued.operation.value_counts().items()},
                  "note": "Candidates for validation, not a score claim or submission", "enable": False}
    report["norm_file"] = args.norm_file
    rescued = inspect_residuals(rescued, args.split)
    report["numeric_sequence_mismatches"] = int((~rescued.numeric_sequence_equal).sum())
    report["compatible_existing_owners"] = int(rescued.existing_owner_compatible.sum())
    rescued.to_parquet(out / (args.split + "_exact_residuals.parquet"), index=False)
    (out / (args.split + "_exact_report.json")).write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_report(args.tag + "-" + args.split, {"diagnostic": report}, command="v7 probe_exact", inputs={
        "scores": args.scores, "matches": args.base_pairs, "norm": args.norm_file})
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--split", choices=["train", "test"], required=True)
    ap.add_argument("--scores", help="v3 dev score parquet for train")
    ap.add_argument("--base-pairs", help="imported v5 test pairs parquet")
    ap.add_argument("--norm-file", help="optional existing normalized cache for complete street/city keys")
    ap.add_argument("--tag", default="bakshi-exact-rescue-v7")
    args = ap.parse_args()
    if args.split == "train" and not args.scores or args.split == "test" and not args.base_pairs:
        ap.error("train needs --scores; test needs --base-pairs")
    main(args)
