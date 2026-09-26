"""Generator-operation rules for countries without training labels (France): drop look-alike edits, add true-copy
edits that the model misses.

    python experiments/ameya/model-v1/post_ops.py --matches ameya-model-v5all-c2 --scores ameya-s2-v5all \
        --cands ameya-cands-v5all-c2 --feats ameya-fx4 --tag ameya-model-v5all-c2-ops
    python experiments/ameya/model-v1/post_ops.py --measure --matches ameya-model-v5all --feats ameya-fx4

The organisers' generator edits S1 records in a small set of ways. At the S1's own address (same first house
number, street word equal or within a typo) the US/India holdout labels say (ANALYSIS_v4.md, RESEARCH_v5.md §6):
- B, look-alike: another real word in the slot of one S1 name word ("Arcot Motors Corp" -> "Arcot Solutions Corp";
  France: "Troupe Ecole SAS" -> "Troupe Centre SAS"): 0.6% true;
- A, true copy: one word dropped and a list word appended after the legal form or at the end ("Crandall Enterprises
  Inc" -> "Crandall Inc Services"; France: "Champollion Sportive SARL" -> "Champollion SARL Groupe"): 98-99.8% true;
- APP, true copy: a list word appended with nothing dropped ("Chasseurs & Fils SAS" -> "Chasseurs Fils SAS France");
- ACR, true copy: the name written as its initials ("Ets Motards SAS" -> "EM");
- NUM, true copy: the same name with the house number moved by -1/-2 or one digit edited, never a look-alike +d
  nudge (d in {1, 2, 3, 4, 5, 7, 9, 11, 13, 21});
- CODE, true copy: a 2-3 letter code with a typo ("YU Primaire SASU" -> "YYU Primaire SASU").
The trained models know this for US/India through the label word odds; a country without labels only has proxy odds,
so it accepts B (v4: 17k in France) and misses the true-copy edits. For countries absent from the training labels
this script drops predicted B pairs and adds the true-copy pairs that are in the candidate set, whose S1 is the
record's best-scoring S1 and whose record is not predicted elsewhere. Countries with labels keep the model's
predictions. ``--measure`` prints every population's truth rate and the model's acceptance on the US/India holdout.

A "real" word is used in >= 20 S1 names of the country; a garble has Indel similarity >= 0.5 to the dropped word;
list words are hand-written from the op-A signature counts (English: center, services, service, partners; French:
fils, cie, services, associes, groupe, developpement, france) and match the label-free derivation exactly.
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
from rapidfuzz.distance import Indel, Levenshtein, OSA

from ber.artifacts import read_table, write_table
from ber.block.text import LEGAL, NAME_STOP, fold
from ber.eval.splits import is_holdout
from ber.features.context import numstreet_keys
from ber.paths import artifact_path, records_path

log = logging.getLogger("post_ops")
LEG = set(LEGAL) | {"sarl", "sas", "sasu", "eurl", "sa", "sci", "snc", "ei", "eirl", "scop", "selarl", "gie"}
STOP = set(NAME_STOP) | {"et", "and"}
LIST_A = {"center", "services", "service", "partners", "fils", "cie", "associes", "groupe", "developpement", "france"}
NUDGE = {1, 2, 3, 4, 5, 7, 9, 11, 13, 21}
REAL_MIN, GARBLE_SIM, MIN_LEN = 20, 0.5, 4
B_POS = {"before_legal", "after_legal", "end_same_slot", "inner"}
A_POS = {"after_legal", "end_moved", "end_same_slot"}
APP_POS = {"after_legal", "end"}
ADD_OPS = ("A", "APP", "ACR", "NUM", "CODE")
NUM_KINDS = {"minus", "sub", "swap", "indel"}
K = 4_000_000_000


def tokens(s: str) -> list[str]:
    s = re.sub(r"(?<=\b[a-z])\.(?=[a-z]\b)", "", s)  # s.a.r.l -> sarl
    return re.findall(r"[a-z0-9]+", s.replace(".", " "))


def close(a: str, b: str) -> bool:
    if a == b:
        return True
    if len(a) >= 4 and len(b) >= 4:
        return Levenshtein.distance(a, b) <= (1 if min(len(a), len(b)) < 7 else 2)
    return False


def name_edit(sname: str, rname: str) -> tuple[str, str, str, str]:
    """(kind, position, added word, dropped word). kind: "swap" (one S1 content word replaced), "add" (one word
    added, none dropped), "same" (same content words up to typos), "acr" (the record is the S1's initials), "" else."""
    st, rt = tokens(sname), tokens(rname)
    s_cont = [(i, w) for i, w in enumerate(st) if w not in LEG and w not in STOP]
    r_cont = [(j, w) for j, w in enumerate(rt) if w not in LEG and w not in STOP]
    if len(s_cont) >= 2 and len(r_cont) == 1 and 2 <= len(r_cont[0][1]) <= 5 \
            and r_cont[0][1] == "".join(w[0] for _, w in s_cont):
        return "acr", "", r_cont[0][1], ""
    used, miss = set(), []
    for i, w in s_cont:
        j = next((j for j, x in r_cont if j not in used and close(w, x)), None)
        if j is None:
            miss.append((i, w))
        else:
            used.add(j)
    add = [(j, x) for j, x in r_cont if j not in used]
    if not s_cont:
        return "", "", "", ""
    if not miss and not add:
        return "same", "", "", ""
    r_leg = [j for j, w in enumerate(rt) if w in LEG]
    if not miss and len(add) == 1:
        rj, rw = add[0]
        pos = "after_legal" if r_leg and rj > min(r_leg) else "end" if rj == r_cont[-1][0] else "inner"
        return "add", pos, rw, ""
    if len(miss) != 1 or len(add) != 1 or len(s_cont) < 2:
        return "", "", "", ""
    (si, sw), (rj, rw) = miss[0], add[0]
    s_leg = [i for i, w in enumerate(st) if w in LEG]
    if s_leg and r_leg:
        pos = "after_legal" if rj > min(r_leg) else "before_legal"
    elif s_leg:
        pos = "legal_dropped"
    else:
        s_last, r_last = si == s_cont[-1][0], rj == r_cont[-1][0]
        pos = "end_moved" if r_last and not s_last else "end_same_slot" if r_last else "inner"
    return "swap", pos, rw, sw


# Robust "same address" (rules v3): the (number, first street word) key misses the same address when the house
# number carries a suffix ("8BIS", "129D", "51 TER"), the street type has a typo ("AVEUNE", "ASLEE", "Pace") or an
# abbreviation ("Q." for quai), or a short street name has a two-letter typo ("Arts"/"Arst"). Here the first house
# number is read without its suffix, and the street is the set of words after it (street types, typo'd street types,
# articles and suffixes skipped); two addresses match when the numbers are equal and the street sets share a word up
# to a typo.
TYPES = ("rue r avenue ave av boulevard bd blvd allee all impasse imp chemin ch che route rte place pl quai q cours crs "
         "faubourg fg passage pas psg square sq cite lotissement lot residence res voie sentier digue parvis promenade "
         "esplanade hameau street st road rd lane ln drive dr court ct circle cir highway hwy parkway pkwy terrace "
         "trail trl way no nr n numero").split()
TYPES_SET = set(TYPES)
TYPES_LONG = [t for t in TYPES if len(t) >= 5]
ARTICLES = set("de du des la le les l d a au aux en et the of".split())
SUFFIXES = set("bis ter quater a b c d e f o t q".split())
_NUM = re.compile(r"(?<![0-9])0*([0-9]{1,5})(bis|ter|quater|[a-z])?\b")


def _is_type(w: str) -> bool:
    if w in TYPES_SET:
        return True
    return len(w) >= 4 and any(abs(len(w) - len(t)) <= 1 and OSA.distance(w, t) <= (1 if len(t) < 7 else 2)
                               for t in TYPES_LONG)


def addr_parts(address: str) -> tuple[str, frozenset]:
    """(first house number without its suffix, street-name words after it) of a folded address; ("", ()) if none."""
    for seg in address.split(","):
        m = _NUM.search(seg)
        if not m:
            continue
        words = re.findall(r"[a-z]+", seg[m.end():])
        while words and words[0] in SUFFIXES:
            words = words[1:]
        street = frozenset(w for w in words if len(w) >= 3 and w not in ARTICLES and not _is_type(w))
        return m.group(1), street
    return "", frozenset()


def _close_word(a: str, b: str) -> bool:
    if a == b:
        return True
    if min(len(a), len(b)) < 4:
        return False
    return OSA.distance(a, b) <= (1 if min(len(a), len(b)) < 7 else 2)


def same_address(ps: tuple[str, frozenset], pr: tuple[str, frozenset]) -> bool:
    (ns, ss), (nr, sr) = ps, pr
    return bool(ns) and ns == nr and bool(ss) and bool(sr) and any(_close_word(a, b) for a in ss for b in sr)


def number_edit(ns: str, nr: str) -> str:
    """The kind of a true-copy house-number edit, "" if none: "minus" (-1/-2), "sub" (one digit substituted),
    "swap" (two adjacent digits swapped), "indel" (one digit inserted or deleted). A look-alike +d nudge is never an
    edit."""
    if ns == nr:
        return ""
    d = int(nr[:12]) - int(ns[:12])
    if d in NUDGE:
        return ""
    if d in (-1, -2):
        return "minus"
    if len(ns) == len(nr):
        return "sub" if Levenshtein.distance(ns, nr) == 1 else "swap" if OSA.distance(ns, nr) == 1 else ""
    return "indel" if Levenshtein.distance(ns, nr) == 1 else ""


def classify(d: pd.DataFrame, names: pd.Series, keys: pd.Series, vocab: dict[str, Counter],
             parts: pd.Series | None = None) -> pd.DataFrame:
    """Adds kind/pos/added/dropped, the address relation and the rule population ``op`` for each (s1, r) pair.
    ``parts`` (eid -> ``addr_parts``) adds the robust same-address match (rules v3) to the key match."""
    ks, kr = keys.reindex(d.s1).to_numpy(), keys.reindex(d.r).to_numpy()
    num_s = np.array([k.split("|")[0] if k else "" for k in ks], object)
    num_r = np.array([k.split("|")[0] if k else "" for k in kr], object)
    st_s = np.array([k.split("|")[1] if k else "" for k in ks], object)
    st_r = np.array([k.split("|")[1] if k else "" for k in kr], object)
    ok = (num_s != "") & (num_r != "")
    street = ok & np.array([a == b or close(a, b) for a, b in zip(st_s, st_r)])
    same_num = street & (num_s == num_r)
    if parts is not None:
        robust = np.array([same_address(a, b) for a, b in zip(parts.reindex(d.s1).to_numpy(),
                                                               parts.reindex(d.r).to_numpy())])
        d = d.assign(robust_only=robust & ~same_num)
        same_num = same_num | robust
    num_kind = np.array([number_edit(a, b) if o and a != b else "" for a, b, o in zip(num_s, num_r, street)], object)
    num_ed = np.isin(num_kind, list(NUM_KINDS))
    edits = [name_edit(a, b) for a, b in zip(names.reindex(d.s1).to_numpy(), names.reindex(d.r).to_numpy())]
    d = d.assign(kind=[e[0] for e in edits], pos=[e[1] for e in edits], added=[e[2] for e in edits],
                 dropped=[e[3] for e in edits], same_num=same_num, num_edit=num_ed, num_kind=num_kind,
                 street_typo=street & (st_s != st_r))
    real = np.array([vocab[c].get(w, 0) >= REAL_MIN if w else False for c, w in zip(d.cty, d.added)])
    garble = np.array([Indel.normalized_similarity(a, b) >= GARBLE_SIM if a and b else False
                       for a, b in zip(d.added, d.dropped)])
    lst = d.added.isin(LIST_A).to_numpy()
    kind, pos = d.kind.to_numpy(), d.pos.to_numpy()
    long_ = d.added.str.len().to_numpy() >= MIN_LEN
    code = np.array([0 < len(b) <= 3 and Levenshtein.distance(a, b) <= 1 if b else False
                     for a, b in zip(d.added, d.dropped)])
    op = np.full(len(d), "", object)
    sn = d.same_num.to_numpy()
    op[sn & (kind == "swap") & real & ~lst & ~garble & long_ & np.isin(pos, list(B_POS))] = "B"
    op[sn & (kind == "swap") & lst & ~garble & np.isin(pos, list(A_POS))] = "A"
    op[sn & (kind == "add") & lst & np.isin(pos, list(APP_POS))] = "APP"
    op[sn & (kind == "acr")] = "ACR"
    op[sn & (kind == "swap") & code & (op == "")] = "CODE"
    op[d.num_edit.to_numpy() & (kind == "same")] = "NUM"
    return d.assign(op=op)


def preselect(feats: str, split: str, s1_set: np.ndarray) -> pd.DataFrame:
    """Candidate pairs of the given S1 that can hold one of the edits (cheap str-feature filters)."""
    f = pq.ParquetFile(artifact_path("features", f"{feats}-str", split))
    cols = ["s1", "r", "num__rel1", "name__fz_inter", "name__fz_sub", "name__fz_n_extra_r", "name__len_r",
            "name__inter"] + (["y"] if split == "train" else [])
    parts = []
    for i in range(f.num_row_groups):
        a = f.read_row_group(i, columns=cols).to_pandas()
        j = np.searchsorted(s1_set, a.s1.to_numpy())
        j[j >= s1_set.size] = 0
        rel, fz_i, fz_s, fz_x = a.num__rel1, a.name__fz_inter, a.name__fz_sub, a.name__fz_n_extra_r
        sel = (s1_set[j] == a.s1.to_numpy()) & (
            ((rel == 1) & (fz_i >= 1) & (fz_x == 1))  # swaps, appends, code typos
            | ((rel == 1) & (a.name__len_r <= 2) & (a.name__inter == 0))  # acronyms
            | (rel.isin([2, 3, 4]) & (fz_x == 0) & (fz_s == 0)))  # same name, other number
        parts.append(a.loc[sel.to_numpy(), ["s1", "r"] + (["y"] if split == "train" else [])])
    return pd.concat(parts, ignore_index=True)


def record_text(split: str, ids: np.ndarray, robust: bool = False) -> tuple[pd.Series, pd.Series, pd.Series | None]:
    t = pq.read_table(records_path(split), columns=["eid", "name", "address"])
    t = t.filter(pc.is_in(t["eid"], value_set=pa.array(ids)))
    eid = t["eid"].to_numpy()
    names = pd.Series(fold(t["name"].combine_chunks()).to_numpy(zero_copy_only=False), index=eid)
    keys = pd.Series(numstreet_keys(t["address"].combine_chunks()), index=eid)
    parts = None
    if robust:
        addr = fold(t["address"].combine_chunks()).to_numpy(zero_copy_only=False)
        parts = pd.Series([addr_parts(a or "") for a in addr], index=eid)
    return names, keys, parts


def s1_vocab(split: str, countries: set) -> tuple[pd.Series, dict[str, Counter]]:
    """S1 country per eid and, per country, how many S1 names use each token."""
    rec = pq.read_table(records_path(split), columns=["eid", "source", "country", "name"])
    s1t = rec.filter(pc.equal(rec["source"], 1))
    cty = pd.Series(s1t["country"].to_numpy(zero_copy_only=False), index=s1t["eid"].to_numpy())
    names = fold(s1t["name"].combine_chunks()).to_numpy(zero_copy_only=False)
    vocab = {}
    for c in countries:
        cnt = Counter()
        for s in names[cty.to_numpy() == c]:
            cnt.update(set(re.findall(r"[a-z0-9]+", s)))
        vocab[c] = cnt
    return cty, vocab


def measure(args) -> int:
    """Truth rate and model acceptance of every rule population on the US/India holdout."""
    tr = pq.read_table(records_path("train"), columns=["source", "country"])
    cty, vocab = s1_vocab("train", set(pc.unique(tr["country"]).to_pylist()))
    hold = np.sort(cty.index.to_numpy()[is_holdout(cty.index.to_numpy())])
    d = preselect(args.feats, "train", hold)
    names, keys, parts = record_text("train", np.unique(np.r_[d.s1.to_numpy(), d.r.to_numpy()]), args.robust_addr)
    d = classify(d.assign(cty=cty.reindex(d.s1).to_numpy()), names, keys, vocab, parts)
    m = read_table("matches", args.matches, "train")
    d["pred"] = np.isin(d.s1.to_numpy() * K + d.r.to_numpy(), m.s1.to_numpy() * K + m.r.to_numpy())
    d = d[d.op != ""]
    by = ["op", "num_kind", "street_typo"] + (["robust_only"] if args.robust_addr else []) + ["cty"]
    t = d.groupby(by).agg(pairs=("y", "size"), true=("y", "mean"), predicted=("pred", "mean"))
    t["per_1000_s1"] = t.pairs / pd.Series(cty.reindex(hold).value_counts()).reindex(
        t.index.get_level_values("cty")).to_numpy() * 1000
    print(t.round(4).to_string())
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--matches", required=True)
    ap.add_argument("--scores")
    ap.add_argument("--cands")
    ap.add_argument("--feats", required=True, help="feature set whose <feats>-str/<split>.parquet preselects the pairs")
    ap.add_argument("--tag")
    ap.add_argument("--rules", default="B,A,APP,ACR", help="which populations to apply (NUM and CODE: see --measure)")
    ap.add_argument("--no-add", action="store_true")
    ap.add_argument("--no-drop", action="store_true")
    ap.add_argument("--measure", action="store_true", help="print truth rates on the US/India holdout and exit")
    ap.add_argument("--robust-addr", action="store_true",
                    help="rules v3: also match the S1's address with suffixed numbers and typo'd street types")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    if args.measure:
        return measure(args)
    rules = set(args.rules.split(","))

    tr = pq.read_table(records_path("train"), columns=["source", "country"])
    labelled = set(pc.unique(tr["country"]).to_pylist())
    del tr
    rec = pq.read_table(records_path("test"), columns=["source", "country"])
    targets = set(pc.unique(rec["country"]).to_pylist()) - labelled
    del rec
    cty, vocab = s1_vocab("test", targets)
    target = cty[cty.isin(targets)]
    log.info("countries without training labels: %s (%d S1)", sorted(targets), len(target))
    d = preselect(args.feats, "test", np.sort(target.index.to_numpy()))
    names, keys, parts = record_text("test", np.unique(np.r_[d.s1.to_numpy(), d.r.to_numpy()]), args.robust_addr)
    d = classify(d.assign(cty=target.reindex(d.s1).to_numpy()), names, keys, vocab, parts)
    d = d[d.op.isin(list(rules))].reset_index(drop=True)
    log.info("rule populations: %s", d.groupby("op").size().to_dict())
    if parts is not None:
        log.info("of which matched only by the robust address: %s", d[d.robust_only].groupby("op").size().to_dict())

    m = read_table("matches", args.matches, "test")
    mk = m.s1.to_numpy() * K + m.r.to_numpy()
    dk = d.s1.to_numpy() * K + d.r.to_numpy()
    pred = np.isin(dk, mk)
    out = m
    n_drop, n_add = 0, {}
    if not args.no_drop and "B" in rules:
        drop = dk[(d.op == "B").to_numpy() & pred]
        out = out[~np.isin(mk, drop)]
        n_drop = drop.size
    if not args.no_add:
        cand = read_table("candidates", args.cands, "test")
        ck = np.sort(cand.s1.to_numpy() * K + cand.r.to_numpy())
        del cand
        x = d[d.op.isin(ADD_OPS).to_numpy() & ~pred]
        xk = x.s1.to_numpy() * K + x.r.to_numpy()
        j = np.searchsorted(ck, xk)
        j[j >= ck.size] = 0
        inside = ck[j] == xk
        log.info("true-copy edits not predicted: %s; inside the candidate set: %s", x.groupby("op").size().to_dict(),
                 x[inside].groupby("op").size().to_dict())
        x = x[inside & ~x.r.isin(out.r).to_numpy()]
        sc = read_table("scores", args.scores, "test", ["s1", "r", "pc"])
        sc = sc[sc.r.isin(x.r)]
        owner = sc.loc[sc.groupby("r").pc.idxmax(), ["r", "s1"]].set_index("r").s1
        x = x[owner.reindex(x.r).to_numpy() == x.s1.to_numpy()].drop_duplicates("r")
        out = pd.concat([out, x[["s1", "r"]]], ignore_index=True)
        n_add = x.groupby("op").size().to_dict()
    command = (f"python experiments/ameya/model-v1/post_ops.py --matches {args.matches} --scores {args.scores} "
               f"--cands {args.cands} --feats {args.feats} --tag {args.tag} --rules {args.rules}"
               + (" --robust-addr" if args.robust_addr else "")
               + (" --no-add" if args.no_add else "") + (" --no-drop" if args.no_drop else ""))
    write_table(out[["s1", "r"]].reset_index(drop=True), "matches", args.tag, "test", command=command,
                inputs={"matches": args.matches, "scores": args.scores, "candidates": args.cands},
                dropped_op_b=int(n_drop), added={k: int(v) for k, v in n_add.items()})
    log.info("%s: %d pairs (%s: %d); dropped %d op-B predictions (%.1f per 1000 target S1); added %s", args.tag,
             len(out), args.matches, len(m), n_drop, 1000 * n_drop / len(target), n_add)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
