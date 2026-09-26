"""Made-up brand-name copies at an address with a single S1 (rules v3 companion; measure first).

    python experiments/ameya/model-v1/brand_join.py --split train                    # measure on the holdout
    python experiments/ameya/model-v1/brand_join.py --split test --matches <tag> --cands <tag> --tag <new> \
        --cands-tag <new> [--min-truth 0.9]

The generator writes some copies under an invented brand ("Nylabelo", "Korzeph") at the S1's own address. Such a
record is a copy of some S1 at that address almost always (RESEARCH_v5.md), so where exactly one S1 sits at that
address (same first house number, a shared street word up to a typo: post_ops.same_address) the record should be
that S1's copy. Brand-like record: one alphabetic token of 5-15 letters that no S1 name of its country uses and that
is not a domain or an acronym. On train the script prints the holdout truth rate of the rule (all pairs, and those
whose record no S1 holds in --matches); on test it adds the pairs for countries without labels, only for records no
S1 holds, to the matches and the candidate set.
"""
from __future__ import annotations

import argparse
import logging
import re
from collections import Counter

import numpy as np
import pandas as pd
import pyarrow.compute as pc
import pyarrow.parquet as pq

from ber.artifacts import read_table, write_table
from ber.block.text import fold
from ber.eval.splits import is_holdout
from ber.paths import records_path
from post_ops import K, addr_parts, same_address

log = logging.getLogger("brand_join")


def pairs(split: str, countries: set | None = None, s1_filter=None) -> pd.DataFrame:
    t = pq.read_table(records_path(split), columns=["eid", "source", "country", "name", "address"])
    name = np.asarray(fold(t["name"].combine_chunks()).to_numpy(zero_copy_only=False), dtype=object)
    addr = np.asarray(fold(t["address"].combine_chunks()).to_numpy(zero_copy_only=False), dtype=object)
    src = t["source"].to_numpy()
    cty = np.asarray(t["country"].to_numpy(zero_copy_only=False), dtype=object)
    eid = t["eid"].to_numpy()
    del t
    in_c = np.isin(cty, list(countries)) if countries else np.ones(eid.size, bool)
    vocab: dict[str, Counter] = {}
    for c in np.unique(cty[(src == 1) & in_c]):
        cnt = Counter()
        for n in name[(src == 1) & (cty == c)]:
            cnt.update(set(re.findall(r"[a-z0-9]+", n or "")))
        vocab[c] = cnt
    s_idx = np.flatnonzero((src == 1) & in_c)
    r_idx = np.flatnonzero((src != 1) & in_c)
    brand = []
    for i in r_idx:
        n = (name[i] or "").strip()
        if not re.fullmatch(r"[a-z]{5,15}", n) or vocab.get(cty[i], Counter()).get(n, 0) > 0:
            continue
        brand.append(i)
    brand = np.array(brand, np.int64)
    log.info("%s: %d brand-like records", split, brand.size)
    # join on (country, house number); confirm with same_address; count S1 per address
    sp = {i: addr_parts(addr[i] or "") for i in s_idx}
    rp = {i: addr_parts(addr[i] or "") for i in brand}
    s_df = pd.DataFrame({"cty": cty[s_idx], "num": [sp[i][0] for i in s_idx], "si": s_idx})
    r_df = pd.DataFrame({"cty": cty[brand], "num": [rp[i][0] for i in brand], "ri": brand})
    s_df, r_df = s_df[s_df.num != ""], r_df[r_df.num != ""]
    j = s_df.merge(r_df, on=["cty", "num"])
    ok = np.array([same_address(sp[a], rp[b]) for a, b in zip(j.si.to_numpy(), j.ri.to_numpy())], bool)
    j = j[ok]
    n_s1 = j.groupby("ri").si.transform("size").to_numpy()
    j = j[n_s1 == 1]
    if s1_filter is not None:
        j = j[s1_filter(eid[j.si.to_numpy()])]
    return pd.DataFrame({"s1": eid[j.si.to_numpy()], "r": eid[j.ri.to_numpy()], "cty": cty[j.si.to_numpy()]})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True, choices=["train", "test"])
    ap.add_argument("--matches", default="ameya-model-v6all-s3")
    ap.add_argument("--cands", default="")
    ap.add_argument("--tag", default="")
    ap.add_argument("--cands-tag", default="")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    m = read_table("matches", args.matches, args.split)
    if args.split == "train":
        d = pairs("train", s1_filter=is_holdout)
        truth = pq.read_table(records_path("train").parent / "truth.parquet").to_pandas()
        d["y"] = np.isin(d.s1.to_numpy() * K + d.r.to_numpy(), np.sort(truth.s1.to_numpy() * K + truth.r.to_numpy()))
        d["free"] = ~d.r.isin(m.r).to_numpy()
        d["pred"] = np.isin(d.s1.to_numpy() * K + d.r.to_numpy(), m.s1.to_numpy() * K + m.r.to_numpy())
        g = d.groupby(["cty", "free"]).agg(pairs=("y", "size"), truth=("y", "mean"), predicted=("pred", "mean"))
        print(g.round(4).to_string())
        return 0
    tr = pq.read_table(records_path("train"), columns=["country"])
    labelled = set(pc.unique(tr["country"]).to_pylist())
    targets = set(pc.unique(pq.read_table(records_path("test"), columns=["country"])["country"]).to_pylist()) - labelled
    d = pairs("test", countries=targets)
    add = d[~d.r.isin(m.r).to_numpy()]
    c = read_table("candidates", args.cands, "test")
    ck = np.sort(c.s1.to_numpy() * K + c.r.to_numpy())
    in_c = np.isin(add.s1.to_numpy() * K + add.r.to_numpy(), ck)
    log.info("brand pairs at single-S1 addresses (countries without labels): %d; records free: %d (already candidates %d)",
             len(d), len(add), int(in_c.sum()))
    out = pd.concat([m[["s1", "r"]], add[["s1", "r"]]], ignore_index=True)
    cands = pd.concat([c, add.loc[~in_c, ["s1", "r"]].reindex(columns=c.columns)], ignore_index=True)
    command = (f"python experiments/ameya/model-v1/brand_join.py --split test --matches {args.matches} --cands {args.cands} "
               f"--tag {args.tag} --cands-tag {args.cands_tag}")
    write_table(out.reset_index(drop=True), "matches", args.tag, "test", command=command,
                inputs={"matches": args.matches, "candidates": args.cands}, added=int(len(add)))
    write_table(cands.reset_index(drop=True), "candidates", args.cands_tag, "test", command=command,
                inputs={"candidates": args.cands}, added=int((~in_c).sum()))
    log.info("%s: %d pairs (+%d)", args.tag, len(out), len(add))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
