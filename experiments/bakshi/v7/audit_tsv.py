"""Import existing submission TSVs and inspect their predicted pairs without scores."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds

from ber.ids import to_eids
from ber.io import MATCHING_HEADER, read_tsv
from ber.paths import check_name, records_path, work_dir
from ber.artifacts import write_report
from rules import pair_keys, profiles, s1_vocab


def import_matching(path):
    """Use the standard TSV reader and Arrow flattening to avoid object explode."""
    frame = read_tsv(path)
    if tuple(frame.columns) != MATCHING_HEADER:
        raise ValueError(f"Incorrect header: {path}")
    s1 = to_eids(frame.iloc[:, 0])
    if len(np.unique(s1)) != len(s1):
        raise ValueError(f"Duplicate S1 rows: {path}")
    if not (s1 // 1_000_000_000 == 1).all():
        raise ValueError(f"Non-S1 row: {path}")
    lists = pc.split_pattern(pa.array(frame.iloc[:, 1]), pattern=",")
    flat = pc.list_flatten(lists)
    parent = pc.list_parent_indices(lists).to_numpy()
    keep = pc.not_equal(flat, "")
    pairs = pd.DataFrame({"s1": s1[parent[keep.to_numpy(zero_copy_only=False)]],
                          "r": to_eids(flat.filter(keep).to_numpy(zero_copy_only=False))})
    if not np.isin(pairs.r.to_numpy() // 1_000_000_000, [2, 3]).all():
        raise ValueError(f"Non-S2/S3 target: {path}")
    if pairs.duplicated().any():
        raise ValueError(f"Duplicate pair: {path}")
    with open(path, "rb") as fh:
        digest = hashlib.file_digest(fh, "sha256").hexdigest()
    return s1, pairs, digest


def audit(args):
    out = work_dir() / "v7" / args.tag
    out.mkdir(parents=True, exist_ok=True)
    rec = ds.dataset(records_path("test")).to_table(columns=["eid", "source", "country"])
    s1t = rec.filter(pc.equal(rec["source"], 1))
    cty = pd.Series(s1t["country"].to_numpy(zero_copy_only=False), index=s1t["eid"].to_numpy())
    train = ds.dataset(records_path("train")).to_table(columns=["country"])
    targets = set(pc.unique(rec["country"]).to_pylist()) - set(pc.unique(train["country"]).to_pylist())
    # Keep the ID/country index only until integrity checks are done.
    rcty = pd.Series(rec["country"].to_numpy(zero_copy_only=False), index=rec["eid"].to_numpy())
    del rec, s1t, train
    order, base, sha = import_matching(Path(args.base))
    if not np.array_equal(np.sort(order), np.sort(cty.index.to_numpy())):
        raise ValueError("Submission does not contain exactly the test S1 universe")
    rc = rcty.reindex(base.r)
    if rc.isna().any():
        raise ValueError("Submission references IDs absent from test records")
    if not np.array_equal(cty.reindex(base.s1).to_numpy(), rc.to_numpy()):
        raise ValueError("Submission contains cross-country matches")
    ownership_conflicts = int(base.r.duplicated().sum())
    del rcty, rc
    base.to_parquet(out / "base_pairs.parquet", index=False)
    countries = []
    for country, ids in cty.groupby(cty):
        p = base[base.s1.isin(ids.index)]
        counts = p.groupby("s1").size().reindex(ids.index, fill_value=0)
        countries.append({"country": str(country), "entities": len(ids), "pairs": len(p),
                          "empty_entities": int((counts == 0).sum()), "mean_matches": float(counts.mean())})
    report = {"base_file": str(Path(args.base).resolve()), "sha256": sha,
              "rows": len(order), "pairs": len(base), "ownership_conflicts": ownership_conflicts,
              "integrity": "S1 coverage, valid target IDs, unique pairs and same-country matches checked",
              "countries": countries, "unseen_label_countries": sorted(targets), "comparisons": [],
              "score_claim": "None: test labels and full model scores are unavailable"}
    print(json.dumps(report, indent=2), flush=True)
    base_keys = pair_keys(base)
    for path in args.compare:
        other_order, other, digest = import_matching(Path(path))
        if not np.array_equal(np.sort(order), np.sort(other_order)):
            raise ValueError(f"S1 coverage differs: {path}")
        other_keys = pair_keys(other)
        newer = base[~np.isin(base_keys, other_keys)]
        older = other[~np.isin(other_keys, base_keys)]
        rows = []
        for country, ids in cty.groupby(cty):
            a = newer[newer.s1.isin(ids.index)]
            b = older[older.s1.isin(ids.index)]
            rows.append({"country": str(country), "base_only_pairs": len(a), "older_only_pairs": len(b),
                         "changed_entities": len(np.unique(np.r_[a.s1.to_numpy(), b.s1.to_numpy()]))})
        comparison = {"file": str(Path(path).resolve()), "sha256": digest, "pairs": len(other), "countries": rows}
        report["comparisons"].append(comparison)
        print(json.dumps(comparison, indent=2), flush=True)
        del other, newer, older, other_keys
    del base_keys
    (out / "summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if args.profiles:
        unseen = base[cty.reindex(base.s1).isin(targets).to_numpy()].reset_index(drop=True)
        print(f"Profiling {len(unseen):,} predicted pairs in unseen-label countries", flush=True)
        _, vocab = s1_vocab("test", targets)
        p = profiles(unseen, "test", cty, vocab)
        p.to_parquet(out / "unseen_profiles.parquet", index=False)
        report["unseen_diagnostics"] = {
            "pairs": len(p), "address_conflicts": int(p.address_conflict.sum()),
            "street_conflicts": int((p.street_known & ~p.street_close).sum()),
            "city_conflicts": int(p.city_conflict.sum()),
            "combined_edits": {str(k): int(v) for k, v in p.combination.value_counts().items()},
            "warning": "Flags are not labels; do not automatically delete or add these pairs."}
        (out / "summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report["unseen_diagnostics"], indent=2), flush=True)
    print(f"Audit saved to {out}; source TSVs unchanged.", flush=True)
    write_report(args.tag, {"test_diagnostics": report}, command="v7 audit_tsv", inputs={"matches": str(Path(args.base).resolve())})


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", required=True)
    ap.add_argument("--compare", action="append", default=[])
    ap.add_argument("--tag", type=check_name, default="bakshi-tsv-v5-audit")
    ap.add_argument("--profiles", action="store_true")
    audit(ap.parse_args())
