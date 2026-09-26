#!/usr/bin/env python3
"""Score a submission's FINAL French decisions against the rule populations, label-free.

Why this is different from `ce_rule_auc.py` / `rule_auc.py`. Those score a model's *logits* or *pc* on
France's rule populations. This scores what the package actually submits: the final matched pairs, after
stage 3, the rules and the acronym join. Two candidate packages can share a cross-encoder ranking and still
disagree on output, and it is the output that is graded.

The populations (`rule_pop.py`) are French candidate pairs whose truth rate is known from US/India:
  A / APP / ACR -- list-word and acronym true-copy edits, 97-99.8% true  -> treat as y=1
  B             -- look-alike word substitutions,           0-1.2% true  -> treat as y=0

So on these pairs a good package predicts nearly all of the y=1 and almost none of the y=0.

**Read the caveat.** `post_ops.py` deliberately *forces* decisions on exactly these populations: it adds
A/APP/ACR copies and drops op-B predictions. So the absolute numbers below measure the rules as much as the
model, and a package scoring well here is not thereby a good package. What IS meaningful is a **difference
between two packages**, because both run the same rules -- any gap is the model's, in the pairs the rules did
not force. Also: a package whose model was self-trained on pseudo-labels derived from these populations
cannot be compared here at all, and every current candidate from v7nst onward is in that category relative to
the v7ce3 teacher. Use this to compare, with that stated, not to rank absolutely.

    python rulepop_decisions.py --rule-pop rulepop_fr.parquet \
        --package v7nst=path/to/matching.tsv --package v7ens2=path/to/other.tsv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
from pyarrow import csv as pacsv

K = 4_000_000_000


def eid(ids: np.ndarray) -> np.ndarray:
    """"S2-123" -> 2_000_000_123, matching ber.ids (source * 1_000_000_000 + number)."""
    s = pd.Series(ids, dtype="string")
    src = s.str.slice(1, 2).astype("int64")
    num = s.str.slice(3).astype("int64")
    return (src * 1_000_000_000 + num).to_numpy()


def final_pairs(path: Path) -> np.ndarray:
    """Return the set of (s1*K + r) keys predicted by a matching TSV."""
    t = pacsv.read_csv(
        path,
        parse_options=pacsv.ParseOptions(delimiter="\t", quote_char=False),
        convert_options=pacsv.ConvertOptions(
            column_types={"source1_entity_id": pa.string(), "matched_entity_ids": pa.string()},
            strings_can_be_null=False, null_values=[]),
    )
    df = t.to_pandas()
    df.columns = ["s1", "lists"]
    lists = df["lists"].fillna("")
    split = lists.str.split(",")
    n = np.where(lists.str.len().to_numpy() == 0, 0, split.str.len().to_numpy())
    if not (n > 0).any():
        return np.array([], dtype=np.int64)
    flat = np.concatenate([np.asarray(x, dtype=object) for x in split[n > 0]])
    s1_rep = np.repeat(df["s1"].to_numpy(), n)
    return eid(s1_rep) * K + eid(flat)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rule-pop", required=True, type=Path)
    ap.add_argument("--package", action="append", required=True, help="name=path/to/matching_results.tsv")
    args = ap.parse_args()

    pop = pd.read_parquet(args.rule_pop)
    pop["key"] = pop["s1"].to_numpy() * K + pop["r"].to_numpy()
    pop = pop.drop_duplicates("key")
    y = pop["y"].to_numpy().astype(int)
    print(f"rule populations: {len(pop)} French pairs "
          f"({int((y == 1).sum())} true-copy, {int((y == 0).sum())} look-alike)")
    print(pop.groupby("op").size().to_dict())
    print()

    rows, preds = [], {}
    for spec in args.package:
        name, _, path = spec.partition("=")
        keys = final_pairs(Path(path))
        pred = np.isin(pop["key"].to_numpy(), np.sort(keys))
        preds[name] = pred
        tp = int((pred & (y == 1)).sum())
        fp = int((pred & (y == 0)).sum())
        fn = int((~pred & (y == 1)).sum())
        rec = tp / max(1, (y == 1).sum())
        fpr = fp / max(1, (y == 0).sum())
        prec = tp / max(1, tp + fp)
        f05 = (1.25 * prec * rec / (0.25 * prec + rec)) if (prec + rec) else 0.0
        rows.append((name, len(keys), tp, fn, fp, rec, fpr, prec, f05))
        print(f"{name:<12} final pairs {len(keys):>9} | on the populations: "
              f"kept {tp}/{int((y==1).sum())} true-copy ({rec:.4f}), "
              f"predicted {fp}/{int((y==0).sum())} look-alike ({fpr:.4f})")
        print(f"{'':<12} precision {prec:.4f}  F0.5 {f05:.4f}")

    if len(preds) >= 2:
        names = list(preds)
        print("\n== pairwise disagreement on the populations (the meaningful part) ==")
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = names[i], names[j]
                only_a = preds[a] & ~preds[b]
                only_b = preds[b] & ~preds[a]
                print(f"\n{a} vs {b}: {int(only_a.sum()) + int(only_b.sum())} disagreements")
                for lbl, m in ((f"only {a}", only_a), (f"only {b}", only_b)):
                    n1 = int((m & (y == 1)).sum())
                    n0 = int((m & (y == 0)).sum())
                    tot = n1 + n0
                    print(f"  {lbl:<16} {tot:>6}  true-copy {n1:>6}  look-alike {n0:>6}"
                          + (f"  ({n1/tot:.1%} true)" if tot else ""))
                # Under F0.5 a wrongly kept look-alike costs about 0.18 and a wrongly dropped true copy
                # about 0.07, so weight the exchange rather than counting pairs.
                def score(m: np.ndarray) -> float:
                    return (m & (y == 1)).sum() * 0.07 - (m & (y == 0)).sum() * 0.18

                print(f"  weighted exchange on these pairs: {a} {score(only_a):+.1f} vs "
                      f"{b} {score(only_b):+.1f} "
                      f"(true kept x0.07, look-alike kept x-0.18; sign only, not an F0.5 delta)")
                n_dis = int(only_a.sum()) + int(only_b.sum())
                if n_dis < 500:
                    print(f"  NOT SEPARABLE: {n_dis} disagreements out of {len(pop)} population pairs is far "
                          f"too few to rank these packages. This diagnostic is saturated at the decision "
                          f"level; use it on cross-encoder logits, not on finals.")
    print("\nCAVEAT: post_ops forces decisions on these populations, so absolute numbers measure the rules "
          "as much as the model. Only the between-package differences are model-driven, and none of this is "
          "French ground truth.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
