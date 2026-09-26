"""Acronym copies at the S1's own address, found by a join instead of blocking (rules v3 companion).

    python experiments/ameya/model-v1/acr_join.py --split train                      # measure on the holdout
    python experiments/ameya/model-v1/acr_join.py --split test --matches <tag> --cands <tag> --tag <new matches tag> \
        --cands-tag <new candidates tag>                                             # add for countries without labels

A record whose name is the initials of the S1's content words ("PU" for "Passion Union", "CF" for "Cynegetique & Fils
SASU") at the same address (same first house number, a shared street word up to a typo: post_ops.same_address) is a
true copy 99.8-99.9% of the time in US/India over all blocking candidates (post_ops --measure, op ACR). Such records
match their S1 only through the address, so blocking can miss them when many S1 share the street: blocking v3 lost
about 950 French ones that v2 had. The join pairs S1 and records sharing (country, house number, street word); the
acronym test is post_ops.name_edit. On test, a pair is added (to the matches and to the candidate set) only for
countries without training labels, when no S1 holds the record yet and the record has exactly one such S1.
"""
from __future__ import annotations

import argparse
import logging
import re

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from ber.artifacts import read_table, write_table
from ber.block.text import fold
from ber.eval.splits import is_holdout
from ber.paths import records_path
from post_ops import K, LEG, STOP, addr_parts, name_edit, same_address, tokens

log = logging.getLogger("acr_join")


def _content(n: str) -> list[str]:
    return [w for w in tokens(n) if w not in LEG and w not in STOP]


def pairs(split: str, s1_filter=None, countries: set | None = None) -> pd.DataFrame:
    """S1-record pairs at the same address whose record name is the S1's initials (joined on country, house
    number and the initials; then post_ops.same_address and post_ops.name_edit confirm)."""
    t = pq.read_table(records_path(split), columns=["eid", "source", "country", "name", "address"])
    name = np.asarray(fold(t["name"].combine_chunks()).to_numpy(zero_copy_only=False), dtype=object)
    addr = np.asarray(fold(t["address"].combine_chunks()).to_numpy(zero_copy_only=False), dtype=object)
    src = t["source"].to_numpy()
    cty = np.asarray(t["country"].to_numpy(zero_copy_only=False), dtype=object)
    eid = t["eid"].to_numpy()
    del t
    in_c = np.isin(cty, list(countries)) if countries else np.ones(eid.size, bool)
    s_idx = np.flatnonzero((src == 1) & in_c)
    if s1_filter is not None:
        s_idx = s_idx[s1_filter(eid[s_idx])]
    r_idx = np.flatnonzero((src != 1) & in_c)
    s_rows, r_rows = [], []
    for i in s_idx:
        c = _content(name[i] or "")
        if 2 <= len(c) <= 5:
            s_rows.append((cty[i], "".join(w[0] for w in c), eid[i], i))
    for i in r_idx:
        c = _content(name[i] or "")
        if len(c) == 1 and 2 <= len(c[0]) <= 5:
            r_rows.append((cty[i], c[0], eid[i], i))
    s = pd.DataFrame(s_rows, columns=["cty", "ini", "s1", "si"])
    r = pd.DataFrame(r_rows, columns=["cty", "ini", "r", "ri"])
    j = s.merge(r, on=["cty", "ini"])
    log.info("%s: %d S1 with 2-5 content words, %d short-name records, %d initials matches", split, len(s), len(r), len(j))
    cache = {i: addr_parts(addr[i] or "") for i in np.unique(np.r_[j.si.to_numpy(), j.ri.to_numpy()])}
    ok = np.array([same_address(cache[a], cache[b]) for a, b in zip(j.si.to_numpy(), j.ri.to_numpy())], bool)
    j = j[ok]
    acr = np.array([name_edit(name[a] or "", name[b] or "")[0] == "acr" for a, b in zip(j.si.to_numpy(), j.ri.to_numpy())], bool)
    return j[acr][["s1", "r", "cty"]].reset_index(drop=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True, choices=["train", "test"])
    ap.add_argument("--matches", default="", help="test: final matches to extend")
    ap.add_argument("--cands", default="", help="test: the candidate set to extend")
    ap.add_argument("--tag", default="", help="test: new matches tag")
    ap.add_argument("--cands-tag", default="", help="test: new candidates tag")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    if args.split == "train":
        d = pairs("train", s1_filter=is_holdout)
        truth = pq.read_table(records_path("train").parent / "truth.parquet").to_pandas()
        tk = np.sort(truth.s1.to_numpy() * K + truth.r.to_numpy())
        d["y"] = np.isin(d.s1.to_numpy() * K + d.r.to_numpy(), tk)
        n_rec = d.groupby("r").s1.transform("size")
        log.info("holdout acronym pairs at the S1's address: %d, truth %.4f; records with one such S1: truth %.4f (%d)",
                 len(d), d.y.mean(), d.y[n_rec == 1].mean(), int((n_rec == 1).sum()))
        print(d.groupby("cty").y.agg(["size", "mean"]).round(4).to_string())
        return 0
    tr = pq.read_table(records_path("train"), columns=["country"])
    labelled = set(pc.unique(tr["country"]).to_pylist())
    targets = set(pc.unique(pq.read_table(records_path("test"), columns=["country"])["country"]).to_pylist()) - labelled
    d = pairs("test", countries=targets)
    m = read_table("matches", args.matches, "test")
    c = read_table("candidates", args.cands, "test")
    ck = np.sort(c.s1.to_numpy() * K + c.r.to_numpy())
    dk = d.s1.to_numpy() * K + d.r.to_numpy()
    n_rec = d.groupby("r").s1.transform("size").to_numpy()
    add = d[(n_rec == 1) & ~d.r.isin(m.r).to_numpy()]
    in_c = np.isin(add.s1.to_numpy() * K + add.r.to_numpy(), ck)
    log.info("acronym pairs at the address (countries without labels): %d; records free and single: %d "
             "(already candidates %d)", len(d), len(add), int(in_c.sum()))
    out = pd.concat([m[["s1", "r"]], add[["s1", "r"]]], ignore_index=True)
    new_c = add.loc[~in_c, ["s1", "r"]]
    cands = pd.concat([c, new_c.reindex(columns=c.columns)], ignore_index=True)
    command = (f"python experiments/ameya/model-v1/acr_join.py --split test --matches {args.matches} --cands {args.cands} "
               f"--tag {args.tag} --cands-tag {args.cands_tag}")
    write_table(out.reset_index(drop=True), "matches", args.tag, "test", command=command,
                inputs={"matches": args.matches, "candidates": args.cands}, added=int(len(add)))
    write_table(cands.reset_index(drop=True), "candidates", args.cands_tag, "test", command=command,
                inputs={"candidates": args.cands}, added=int(len(new_c)))
    log.info("%s: %d pairs (+%d); %s: %d pairs (+%d)", args.tag, len(out), len(add), args.cands_tag, len(cands), len(new_c))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
