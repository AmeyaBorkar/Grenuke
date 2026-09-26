"""Measure the published robust-address B rule on cached profiles before writing a probe."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
from rapidfuzz import process
from rapidfuzz.distance import Indel

from ber.block.text import fold
from ber.eval.gates import compare
from ber.eval.splits import fold_of, in_dev_sample
from ber.paths import check_name, records_path, truth_path, work_dir
from ber.io import read_tsv, write_matching
from ber.ids import to_eids
from ber.artifacts import write_report
from rules import argmax_owner, pair_keys, s1_vocab, text_for_pairs


def repeated_word(names, added):
    """Whole-token membership; repetition is not insertion of a new vocabulary word."""
    text = pd.Series(names).str.replace(r"[^a-z0-9]+", " ", regex=True).str.strip()
    return np.char.find((" " + text + " ").to_numpy(dtype=str),
                        (" " + pd.Series(added).reset_index(drop=True) + " ").to_numpy(dtype=str)) >= 0


def select_drops(profile, module, split):
    # Prefilter only by name edits. The new rule specifically repairs the old address key.
    p = pd.read_parquet(profile)
    p = p[(p.kind == "swap") & p.pos.isin(module.B_POS) & ~p.added.isin(module.LIST_A)
          & (p.added.str.len() >= module.MIN_LEN) & ~p.same_num].copy()
    if split == "train":
        p = p[p.base_pred].copy()
    similarity = process.cpdist(p.added.to_numpy(), p.dropped.to_numpy(),
                                scorer=Indel.normalized_similarity, workers=-1)
    p = p[similarity < module.GARBLE_SIM].copy()
    if p.empty:
        return p
    cty, vocab = s1_vocab(split, set(p.cty.unique()))
    real = pd.concat([p.loc[p.cty == country, "added"].map(counts) for country, counts in vocab.items()])
    p = p[real.reindex(p.index).fillna(0) >= module.REAL_MIN].reset_index(drop=True)
    print(f"Inspecting {len(p):,} possible additional op-B predictions in {split}", flush=True)
    if p.empty:
        return p
    raw, names, keys = text_for_pairs(p, split)
    addresses = fold(pa.array(raw.address.to_numpy())).to_numpy(zero_copy_only=False)
    unique, inverse = np.unique(addresses, return_inverse=True)
    parts = pd.Series([module.addr_parts(a) for a in unique], dtype=object).iloc[inverse]
    parts.index = raw.index
    cols = ["s1", "r", "cty"] + (["y", "fold"] if split == "train" else [])
    classified = module.classify(p[cols].copy(), names, keys, vocab, parts)
    classified["repeated_word"] = repeated_word(names.reindex(classified.s1).to_numpy(), classified.added.to_numpy())
    return classified[(classified.op == "B") & classified.robust_only].reset_index(drop=True)


def main(args):
    module_path = Path(args.rules_module)
    spec = importlib.util.spec_from_file_location("published_rules_v3", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    out = work_dir() / "v7" / args.tag
    out.mkdir(parents=True, exist_ok=True)
    d = select_drops(Path(args.profiles), module, args.split)
    d.to_parquet(out / (args.split + "_drops.parquet"), index=False)
    repeats = d[d.repeated_word] if len(d) else d
    d = d[~d.repeated_word] if len(d) else d
    report = {"split": args.split, "proposed_drops": len(d), "repetition_protected": len(repeats),
              "source_module_sha256": hashlib.sha256(module_path.read_bytes()).hexdigest(),
              "source_branch": "ameya/research-v6", "enable": False,
              "note": "Only newly matched op-B drops; no address-conflict veto, additions or ownership transfers."}
    if args.split == "train":
        report["protected_true_pairs"] = int(repeats.y.sum())
        report["protected_holdout_pairs"] = int((repeats.fold < 5).sum())
    if args.split == "train":
        report["residuals"] = [{"country": str(c), "holdout": bool(h), "n": len(p), "true": int(p.y.sum())}
                               for (c, h), p in d.assign(holdout=d.fold < 5).groupby(["cty", "holdout"])]
        scores = pd.read_parquet(args.scores, columns=["s1", "r", "pc"])
        own = argmax_owner(scores.s1.to_numpy(), scores.r.to_numpy(), scores.pc.to_numpy())
        base = scores.loc[own & (scores.pc > 0.70), ["s1", "r"]]
        new = base[~np.isin(pair_keys(base), pair_keys(d))]
        t = ds.dataset(records_path("train")).to_table(columns=["eid", "country"], filter=ds.field("source") == 1)
        ids = t["eid"].to_numpy()
        hold = ids[in_dev_sample(ids) & (fold_of(ids) < 5)]
        cty = pd.Series(t["country"].to_numpy(zero_copy_only=False), index=ids)
        truth = ds.dataset(truth_path()).to_table(filter=ds.field("s1").isin(hold)).to_pandas()
        report["gate"] = compare(base, new, truth, hold, groups=cty, min_gain=0.0)
        report["note"] += " Diagnostic v3 sample baseline; not a full v5/v6 gate."
    if args.write_experimental:
        if args.split != "test" or not args.base_pairs or not args.source_tsv:
            raise ValueError("Writing a test probe needs --base-pairs and --source-tsv")
        train_cty = ds.dataset(records_path("train")).to_table(columns=["country"])
        known = set(pc.unique(train_cty["country"]).to_pylist())
        if d.cty.isin(known).any():
            raise ValueError("Probe would change a labeled country")
        base = pd.read_parquet(args.base_pairs, columns=["s1", "r"])
        if not np.isin(pair_keys(d), pair_keys(base)).all():
            raise ValueError("Proposed drops absent from the verified baseline")
        result = base[~np.isin(pair_keys(base), pair_keys(d))].reset_index(drop=True)
        if result.r.duplicated().any() or len(base) - len(result) != len(d):
            raise ValueError("Ownership or pair-count invariant failed")
        source = read_tsv(args.source_tsv)
        order = source.source1_entity_id.astype(str).tolist()
        expected = ds.dataset(records_path("test")).to_table(columns=["eid"], filter=ds.field("source") == 1)["eid"].to_numpy()
        if not np.array_equal(np.sort(to_eids(order)), np.sort(expected)):
            raise ValueError("Source TSV does not cover exactly the test S1 universe")
        path = Path(args.write_experimental)
        if path.exists():
            raise FileExistsError("Refusing to overwrite an existing probe")
        write_matching(path, order, result)
        report.update({"experimental_file": str(path.resolve()), "base_pairs": len(base),
                       "new_pairs": len(result), "affected_s1": int(d.s1.nunique()),
                       "status": "EXPERIMENTAL: France score unmeasured; not selected as final submission"})
        with path.open("rb") as fh:
            report["output_sha256"] = hashlib.file_digest(fh, "sha256").hexdigest()
    (out / (args.split + "_report.json")).write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_report(args.tag + "-" + args.split, {"diagnostic": report}, command="v7 robust_drop_probe")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--split", choices=["train", "test"], required=True)
    ap.add_argument("--profiles", required=True)
    ap.add_argument("--rules-module", required=True)
    ap.add_argument("--scores", help="v3 dev scores for train diagnostic")
    ap.add_argument("--tag", type=check_name, default="bakshi-robust-drop-v7")
    ap.add_argument("--base-pairs", help="verified imported v5 pair cache")
    ap.add_argument("--source-tsv", help="verified v5 source TSV for S1 order")
    ap.add_argument("--write-experimental", help="optional path for an isolated France-drop leaderboard probe")
    args = ap.parse_args()
    if args.split == "train" and not args.scores:
        ap.error("--scores required for train")
    main(args)
