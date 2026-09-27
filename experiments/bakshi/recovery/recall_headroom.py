#!/usr/bin/env python3
"""Is there French RECALL headroom the pipeline left on the table, and can a rule find it at high precision?

Everything measured so far has been about precision on accepted pairs. Recall is the dimension nobody has
measured for France, because France has no labels. This closes that gap using the method the team already
trusts for France: **calibrate a structural criterion where labels exist (US/India train truth), then count
how many unpredicted French pairs it finds.**

For each criterion:
  * precision on US/India = of all TRAIN pairs meeting it, the share that are true. Computed over the
    generated candidate set, not over truth alone, so it is a real precision and not a recall figure.
  * French yield = pairs meeting it in the test set that the submitted model did NOT predict, and whose
    record is unowned (adding an owned record would mean stealing an owner; excluded here).

A criterion is worth acting on only if precision clears the F0.5 break-even AND the yield is large enough to
matter. Break-even: for an S1 with 3 of 4 true matches predicted, adding a true pair gains 0.0625 and adding
a false one costs 0.1875, so break-even precision is 75%. Closing +0.000455 at perfect precision needs about
12,600 recovered matches on distinct S1; at 90% precision, far more.

    python recall_headroom.py --records-train train.parquet --truth truth.parquet \
        --records-test test.parquet --matching <submitted matching_results.tsv>
"""

from __future__ import annotations

import argparse
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pyarrow import csv as pacsv

K = 4_000_000_000
NONWORD = re.compile(r"[^0-9a-z]+")
LEGAL = {"sarl", "sas", "sasu", "sa", "eurl", "snc", "sci", "scp", "selarl", "ltd", "limited", "llp", "llc",
         "inc", "corp", "corporation", "company", "co", "pvt", "private", "plc", "gmbh", "bv", "nv",
         "societe", "ste", "cie", "et", "and", "the", "de", "du", "des", "la", "le", "les"}


def fold(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return NONWORD.sub(" ", s.lower()).strip()


def core(s: str) -> str:
    """Folded name with legal forms and stopwords removed, tokens sorted -- order-insensitive identity."""
    return " ".join(sorted(t for t in fold(s).split() if t and t not in LEGAL))


def first_num(a: str) -> str:
    m = re.search(r"\d+", a or "")
    return m.group(0) if m else ""


def load(path: Path) -> pd.DataFrame:
    t = pq.read_table(path, columns=["eid", "source", "country", "name", "address"]).to_pandas()
    t["name"] = t["name"].fillna("")
    t["address"] = t["address"].fillna("")
    return t


def final_pairs(path: Path) -> tuple[np.ndarray, np.ndarray]:
    t = pacsv.read_csv(
        path, parse_options=pacsv.ParseOptions(delimiter="\t", quote_char=False),
        convert_options=pacsv.ConvertOptions(
            column_types={"source1_entity_id": pa.string(), "matched_entity_ids": pa.string()},
            strings_can_be_null=False, null_values=[])).to_pandas()
    t.columns = ["s1", "lists"]
    lists = t["lists"].fillna("")
    sp = lists.str.split(",")
    n = np.where(lists.str.len().to_numpy() == 0, 0, sp.str.len().to_numpy())
    flat = np.concatenate([np.asarray(x, dtype=object) for x in sp[n > 0]])
    def eid(a):
        s = pd.Series(a, dtype="string")
        return (s.str.slice(1, 2).astype("int64") * 1_000_000_000 + s.str.slice(3).astype("int64")).to_numpy()
    return eid(np.repeat(t["s1"].to_numpy(), n)), eid(flat)


def build_keys(df: pd.DataFrame) -> dict[str, dict]:
    """Per record: the identity keys the criteria below join on."""
    out = {}
    out["core"] = df["name"].map(core).to_numpy()
    out["addr"] = df["address"].map(fold).to_numpy()
    out["hnum"] = df["address"].map(first_num).to_numpy()
    return out


def candidates(s1: pd.DataFrame, rec: pd.DataFrame, key: str) -> pd.DataFrame:
    """Join S1 to records on an exact composite key. Returns (s1, r) pairs. Caps huge buckets."""
    a, b = s1.copy(), rec.copy()
    a["k"], b["k"] = a[key], b[key]
    a = a[a.k.astype(bool)]
    b = b[b.k.astype(bool)]
    size = b.groupby("k").size()
    keep = set(size[size <= 20].index)          # a key shared by >20 records is not identity evidence
    b = b[b.k.isin(keep)]
    j = a[["eid", "k"]].merge(b[["eid", "k"]], on="k", suffixes=("_s1", "_r"))
    return j.rename(columns={"eid_s1": "s1", "eid_r": "r"})[["s1", "r"]]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--records-train", required=True, type=Path)
    ap.add_argument("--truth", required=True, type=Path)
    ap.add_argument("--records-test", required=True, type=Path)
    ap.add_argument("--matching", required=True, type=Path)
    args = ap.parse_args()

    # ---------- calibrate on US/India, where truth exists ----------
    print("== calibrating on train (US/India) ==")
    tr = load(args.records_train)
    kt = build_keys(tr)
    tr["core"], tr["addr"], tr["hnum"] = kt["core"], kt["addr"], kt["hnum"]
    tr["ca"] = tr.core + "|" + tr.addr
    tr["cn"] = tr.core + "|" + tr.hnum
    truth = pq.read_table(args.truth).to_pandas()
    tkey = set(truth.s1.to_numpy() * K + truth.r.to_numpy())
    s1_tr = tr[tr.source == 1]
    r_tr = tr[tr.source != 1]
    print(f"  train S1 {len(s1_tr):,}  records {len(r_tr):,}  truth pairs {len(truth):,}")

    crit = {
        "core name + full address": "ca",
        "core name + house number": "cn",
        "core name alone": "core",
    }
    cal = {}
    for label, k in crit.items():
        j = candidates(s1_tr, r_tr, k)
        if not len(j):
            continue
        y = np.isin(j.s1.to_numpy() * K + j.r.to_numpy(), list(tkey))
        cal[label] = (len(j), float(y.mean()))
        print(f"  {label:<26} pairs {len(j):>9,}  precision on truth {y.mean():.4f}")

    del tr, s1_tr, r_tr, kt, tkey, truth

    # ---------- apply to France, count what the model did not predict ----------
    print("\n== applying to France (test) ==")
    te = load(args.records_test)
    lab = {"US", "India"}
    te = te[~te.country.isin(lab)].reset_index(drop=True)
    kk = build_keys(te)
    te["core"], te["addr"], te["hnum"] = kk["core"], kk["addr"], kk["hnum"]
    te["ca"] = te.core + "|" + te.addr
    te["cn"] = te.core + "|" + te.hnum
    s1_te = te[te.source == 1]
    r_te = te[te.source != 1]
    print(f"  French S1 {len(s1_te):,}  French records {len(r_te):,}")

    ps1, pr = final_pairs(args.matching)
    pred = set(ps1 * K + pr)
    owned = set(pr)
    print(f"  submitted pairs {len(ps1):,}; records already owned {len(owned):,}")

    print(f"\n{'criterion':<26} {'US/IN precision':>16} {'French pairs':>13} {'NOT predicted':>14} "
          f"{'record unowned':>15} {'distinct S1':>12}")
    results = []
    for label, k in crit.items():
        if label not in cal:
            continue
        j = candidates(s1_te, r_te, k)
        if not len(j):
            continue
        key = j.s1.to_numpy() * K + j.r.to_numpy()
        notpred = ~np.isin(key, list(pred))
        free = ~np.isin(j.r.to_numpy(), list(owned))
        add = j[notpred & free]
        results.append((label, cal[label][1], len(j), int(notpred.sum()), len(add), add.s1.nunique()))
        print(f"{label:<26} {cal[label][1]:>16.4f} {len(j):>13,} {int(notpred.sum()):>14,} "
              f"{len(add):>15,} {add.s1.nunique():>12,}")

    print("\n== verdict per criterion ==")
    print("!! The US/India precision above is UNCONDITIONAL and is the WRONG number to decide on. !!")
    print("The pairs we would add are ones the pipeline already had and CHOSE NOT TO PREDICT, having seen")
    print("them with far better features. The number that matters is precision CONDITIONAL on the pipeline")
    print("rejecting the pair, and rejection selects hard against true pairs. Estimating it from the data:")
    print()
    for label, prec, tot, np_, nfree, ns1 in results:
        pred_share = 1 - np_ / tot if tot else 0
        # The model's own precision on what it predicts is about 0.998. So of `tot` pairs, prec*tot are true
        # and the model already captured roughly 0.998 * (tot - np_) of them. What is left among the ones it
        # rejected is the residual, which is what a recovery rule would actually be adding.
        true_total = prec * tot
        true_predicted = 0.998 * (tot - np_)
        cond = max(0.0, min(1.0, (true_total - true_predicted) / np_)) if np_ else 0.0
        gain_u = ns1 * (prec * 0.0625 - (1 - prec) * 0.1875) / 1_732_544
        gain_c = ns1 * (cond * 0.0625 - (1 - cond) * 0.1875) / 1_732_544
        verdict = "ACT" if (cond >= 0.75 and gain_c >= 0.00005) else "REJECT"
        print(f"  {label}")
        print(f"    pipeline already predicts {pred_share:>6.1%} of these pairs")
        print(f"    unconditional precision {prec:.4f} -> est LB {gain_u:+.6f}   (MISLEADING)")
        print(f"    implied precision among the ones it REJECTED {cond:.4f} -> est LB {gain_c:+.6f}")
        print(f"    verdict: {verdict}")
    print()
    print("The `record unowned` filter makes this worse, not safer. Unowned means no S1 in the submitted")
    print("output claims the record, so that subset is enriched for genuine orphans -- and 26% of S2/S3")
    print("records match no S1 at all. The safety filter selects the least promising subpopulation.")
    print()
    print("To turn the conditional precision from an estimate into a measurement we need the pipeline's")
    print("TRAIN-side final matches. Then it is a direct count: of criterion pairs the pipeline rejected on")
    print("train, how many are in truth. Until then this stays a screen, not a gate.")
    print()
    print("Other caveats: US/India precision is a transfer assumption for France, not a measurement there;")
    print("the estimate uses the 3-of-4 state for every S1; and a pair the pipeline did not predict may have")
    print("been deliberately abstained on -- under F0.5 that is often correct.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
