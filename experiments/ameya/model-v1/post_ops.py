"""Generator-operation rules for countries without training labels (France): drop in-slot word swaps, add list appends.

    python experiments/ameya/model-v1/post_ops.py --matches ameya-model-v5 --scores ameya-s2-v5 --cands ameya-cands-v5 \
        --feats ameya-fx4 --tag ameya-model-v5ops

The organisers' generator edits one S1 name word in two ways at the S1's own address (same house number and street
word), measured on the US/India holdout (ANALYSIS_v4.md):
- A, true-copy noise: one word dropped and a word from a short list appended after the legal form or at the end
  ("Crandall Enterprises Inc" -> "Crandall Inc Services"; France: "Champollion Sportive SARL" -> "Champollion SARL
  Groupe"). US/India: 98-99.8% true.
- B, look-alike: another real word in the dropped word's slot ("Arcot Motors Corp" -> "Arcot Solutions Corp";
  France: "Troupe Ecole SAS" -> "Troupe Centre SAS"). US/India holdout: 5,364 pairs, 0.6% true.
The trained models know this for US/India through the label word odds, but a country without labels only has the
label-free proxy odds, which flag look-alike words by moved house numbers, and op B keeps the number: v4 predicts
17k op-B records in France (65 per 1000 S1) and misses op-A records. For countries absent from the training labels
this script drops predicted op-B pairs and adds op-A pairs (owner, in the candidate set, record not predicted
elsewhere). Countries with labels keep the model's predictions.

A "real" word is used in >= 20 S1 names of the country; a garble (typo) has Indel similarity >= 0.5 to the dropped
word; list words are hand-written from the op-A signature counts (English: center, services, service, partners;
French: fils, cie, services, associes, groupe, developpement, france).
"""
from __future__ import annotations

import argparse
import logging
import re
from collections import Counter

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
from rapidfuzz.distance import Indel, Levenshtein

from ber.artifacts import read_table, write_table
from ber.block.text import LEGAL, NAME_STOP, fold
from ber.features.context import numstreet_keys
from ber.paths import artifact_path, records_path

log = logging.getLogger("post_ops")
LEG = set(LEGAL) | {"sarl", "sas", "sasu", "eurl", "sa", "sci", "snc", "ei", "eirl", "scop", "selarl", "gie"}
STOP = set(NAME_STOP) | {"et", "and"}
LIST_A = {"center", "services", "service", "partners", "fils", "cie", "associes", "groupe", "developpement", "france"}
REAL_MIN, GARBLE_SIM, MIN_LEN = 20, 0.5, 4
B_POS = {"before_legal", "after_legal", "end_same_slot", "inner"}
A_POS = {"after_legal", "end_moved", "end_same_slot"}


def tokens(s: str) -> list[str]:
    s = re.sub(r"(?<=\b[a-z])\.(?=[a-z]\b)", "", s)  # s.a.r.l -> sarl
    return re.findall(r"[a-z0-9]+", s.replace(".", " "))


def close(a: str, b: str) -> bool:
    if a == b:
        return True
    if len(a) >= 4 and len(b) >= 4:
        return Levenshtein.distance(a, b) <= (1 if min(len(a), len(b)) < 7 else 2)
    return False


def one_word_edit(sname: str, rname: str) -> tuple[str, str, str]:
    """(position, added word, dropped word) when exactly one S1 content word is replaced; ("", "", "") otherwise."""
    st, rt = tokens(sname), tokens(rname)
    s_cont = [(i, w) for i, w in enumerate(st) if w not in LEG and w not in STOP]
    r_cont = [(j, w) for j, w in enumerate(rt) if w not in LEG and w not in STOP]
    used, miss = set(), []
    for i, w in s_cont:
        j = next((j for j, x in r_cont if j not in used and close(w, x)), None)
        if j is None:
            miss.append((i, w))
        else:
            used.add(j)
    add = [(j, x) for j, x in r_cont if j not in used]
    if len(miss) != 1 or len(add) != 1 or len(s_cont) < 2:
        return "", "", ""
    (si, sw), (rj, rw) = miss[0], add[0]
    s_leg = [i for i, w in enumerate(st) if w in LEG]
    r_leg = [j for j, w in enumerate(rt) if w in LEG]
    if s_leg and r_leg:
        pos = "after_legal" if rj > min(r_leg) else "before_legal"
    elif s_leg:
        pos = "legal_dropped"
    else:
        s_last, r_last = si == s_cont[-1][0], rj == r_cont[-1][0]
        pos = "end_moved" if r_last and not s_last else "end_same_slot" if r_last else "inner"
    return pos, rw, sw


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--matches", required=True)
    ap.add_argument("--scores", required=True)
    ap.add_argument("--cands", required=True)
    ap.add_argument("--feats", required=True, help="feature set whose <feats>-str/test.parquet preselects the pairs")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--no-add", action="store_true")
    ap.add_argument("--no-drop", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")

    tr = pq.read_table(records_path("train"), columns=["source", "country"])
    labelled = set(pc.unique(tr["country"]).to_pylist())
    del tr
    rec = pq.read_table(records_path("test"), columns=["eid", "source", "country", "name"])
    s1t = rec.filter(pc.equal(rec["source"], 1))
    s1_cty = pd.Series(s1t["country"].to_numpy(zero_copy_only=False), index=s1t["eid"].to_numpy())
    target = s1_cty[~s1_cty.isin(labelled)]
    log.info("countries without training labels: %s (%d S1)", sorted(set(target)), len(target))
    # S1 name vocabulary per country (how many S1 names use each token)
    vocab: dict[str, Counter] = {}
    names = fold(s1t["name"].combine_chunks()).to_numpy(zero_copy_only=False)
    cty = s1t["country"].to_numpy(zero_copy_only=False)
    for c in set(target):
        cnt = Counter()
        for s in names[cty == c]:
            cnt.update(set(re.findall(r"[a-z0-9]+", s)))
        vocab[c] = cnt
    del rec, s1t, names

    # preselect: equal first number, a shared name token, one unmatched record token, >= 1 unmatched S1 token
    t_sorted = np.sort(target.index.to_numpy())
    fs = pq.ParquetFile(artifact_path("features", f"{args.feats}-str", "test"))
    parts = []
    for i in range(fs.num_row_groups):
        a = fs.read_row_group(i, columns=["s1", "r", "num__rel1", "name__fz_inter", "name__fz_sub",
                                          "name__fz_n_extra_r"]).to_pandas()
        j = np.searchsorted(t_sorted, a.s1.to_numpy())
        j[j >= t_sorted.size] = 0
        sel = ((t_sorted[j] == a.s1.to_numpy()) & (a.num__rel1 == 1) & (a.name__fz_inter >= 1)
               & (a.name__fz_sub >= 1) & (a.name__fz_n_extra_r == 1)).to_numpy()
        parts.append(a.loc[sel, ["s1", "r"]])
    d = pd.concat(parts, ignore_index=True)
    ids = pa.array(np.unique(np.r_[d.s1.to_numpy(), d.r.to_numpy()]))
    t = pq.read_table(records_path("test"), columns=["eid", "name", "address"])
    t = t.filter(pc.is_in(t["eid"], value_set=ids))
    eid = t["eid"].to_numpy()
    nm = pd.Series(fold(t["name"].combine_chunks()).to_numpy(zero_copy_only=False), index=eid)
    ns = pd.Series(numstreet_keys(t["address"].combine_chunks()), index=eid)
    ks = ns.reindex(d.s1).to_numpy()
    d = d[(ks != "") & (ks == ns.reindex(d.r).to_numpy())].reset_index(drop=True)
    edits = [one_word_edit(a, b) for a, b in zip(nm.reindex(d.s1).to_numpy(), nm.reindex(d.r).to_numpy())]
    d["pos"] = [e[0] for e in edits]
    d["added"] = [e[1] for e in edits]
    d["dropped"] = [e[2] for e in edits]
    d = d[d.pos != ""].reset_index(drop=True)
    d["cty"] = target.reindex(d.s1).to_numpy()
    d["real"] = [vocab[c].get(w, 0) >= REAL_MIN for c, w in zip(d.cty, d.added)]
    d["garble"] = [Indel.normalized_similarity(a, b) >= GARBLE_SIM for a, b in zip(d.added, d.dropped)]
    d["list"] = d.added.isin(LIST_A)
    op_b = d.real & ~d.list & ~d.garble & (d.added.str.len() >= MIN_LEN) & d.pos.isin(B_POS)
    op_a = d.list & ~d.garble & d.pos.isin(A_POS)
    log.info("one-word edits at the S1's address: %d pairs (op B %d, op A %d)", len(d), int(op_b.sum()), int(op_a.sum()))

    m = read_table("matches", args.matches, "test")
    mk = m.s1.to_numpy() * 4_000_000_000 + m.r.to_numpy()
    dk = d.s1.to_numpy() * 4_000_000_000 + d.r.to_numpy()
    pred = np.isin(dk, mk)
    out = m
    n_drop = n_add = 0
    if not args.no_drop:
        drop = dk[op_b.to_numpy() & pred]
        out = out[~np.isin(mk, drop)]
        n_drop = drop.size
    if not args.no_add:
        cand = read_table("candidates", args.cands, "test")
        ck = np.sort(cand.s1.to_numpy() * 4_000_000_000 + cand.r.to_numpy())
        del cand
        x = d[op_a.to_numpy() & ~pred]
        xk = x.s1.to_numpy() * 4_000_000_000 + x.r.to_numpy()
        j = np.searchsorted(ck, xk)
        j[j >= ck.size] = 0
        x = x[(ck[j] == xk) & ~x.r.isin(out.r).to_numpy()]
        sc = read_table("scores", args.scores, "test", ["s1", "r", "pc"])
        sc = sc[sc.r.isin(x.r)]
        owner = sc.loc[sc.groupby("r").pc.idxmax(), ["r", "s1"]].set_index("r").s1
        x = x[owner.reindex(x.r).to_numpy() == x.s1.to_numpy()]
        out = pd.concat([out, x[["s1", "r"]]], ignore_index=True)
        n_add = len(x)
    command = (f"python experiments/ameya/model-v1/post_ops.py --matches {args.matches} --scores {args.scores} "
               f"--cands {args.cands} --feats {args.feats} --tag {args.tag}"
               + (" --no-add" if args.no_add else "") + (" --no-drop" if args.no_drop else ""))
    write_table(out[["s1", "r"]].reset_index(drop=True), "matches", args.tag, "test", command=command,
                inputs={"matches": args.matches, "scores": args.scores, "candidates": args.cands},
                dropped_op_b=int(n_drop), added_op_a=int(n_add))
    log.info("%s: %d pairs (%s: %d); dropped %d op-B predictions, added %d op-A pairs (per 1000 target S1: %.1f / %.1f)",
             args.tag, len(out), args.matches, len(m), n_drop, n_add, 1000 * n_drop / len(target),
             1000 * n_add / len(target))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
