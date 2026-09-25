"""Does the test's different make-up lower US/India below the holdout? Re-weight the holdout to the test's ratios.

    python experiments/ameya/model-v1/gap_check.py --tags ameya-model-v3,ameya-model-v5all

The test pool differs from train: test US has half as many S1 as train US, so fewer S1 share a name. Group
S1 by the size of their same-core-name group in their own split and country (legal forms and stop words removed).
Then compare, per country and group size:
- holdout macro F0.5 per group, re-weighted to the test's group-size mix;
- predicted records per S1: the re-weighted holdout vs the test's actual count. The test has the same true matches
  per S1 as train, so an excess on test would be false positives.
Also prints the share of test S1 left empty per country (5.59% of S1 are true singletons in every country).
Label-free on the test side; the holdout side uses the shared holdout (ber.eval.splits.is_holdout).
"""
from __future__ import annotations

import argparse
import re

import numpy as np
import pandas as pd
import pyarrow.compute as pc
import pyarrow.parquet as pq

from ber.artifacts import exists, read_table
from ber.block.text import LEGAL, NAME_STOP, fold
from ber.eval.splits import is_holdout
from ber.paths import records_path, truth_path

LEG = set(LEGAL) | {"sarl", "sas", "sasu", "eurl", "sa", "sci", "snc", "ei", "eirl", "scop", "selarl", "gie"}
STOP = set(NAME_STOP) | {"et", "and"}
BINS, LABELS = [0, 1, 2, 4, 9, 29, 99, 10**9], ["1", "2", "3-4", "5-9", "10-29", "30-99", "100+"]
K = 4_000_000_000


def s1_groups(split: str) -> pd.DataFrame:
    t = pq.read_table(records_path(split), columns=["eid", "source", "country", "name"])
    t = t.filter(pc.equal(t["source"], 1))
    names = fold(t["name"].combine_chunks()).to_numpy(zero_copy_only=False)
    d = pd.DataFrame({"s1": t["eid"].to_numpy(), "country": t["country"].to_numpy(zero_copy_only=False)})
    d["core"] = [" ".join(w for w in re.findall(r"[a-z0-9]+", s) if w not in LEG and w not in STOP) for s in names]
    d["n_core"] = d.groupby(["country", "core"]).s1.transform("size")
    d["g"] = pd.cut(d.n_core, bins=BINS, labels=LABELS)
    return d.drop(columns="core")


def per_s1(universe: pd.DataFrame, pred: pd.DataFrame, truth: pd.DataFrame | None) -> pd.DataFrame:
    d = universe.copy()
    d["P"] = d.s1.map(pred.groupby("s1").size()).fillna(0).to_numpy()
    if truth is not None:
        hit = pred[np.isin(pred.s1.to_numpy() * K + pred.r.to_numpy(), truth.s1.to_numpy() * K + truth.r.to_numpy())]
        d["T"] = d.s1.map(truth.groupby("s1").size()).fillna(0).to_numpy()
        d["H"] = d.s1.map(hit.groupby("s1").size()).fillna(0).to_numpy()
        den = 0.25 * d["T"] + d["P"]
        d["F"] = np.where(den > 0, 1.25 * d["H"] / np.where(den > 0, den, 1), 1.0)
    return d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tags", default="ameya-model-v5all", help="comma-separated matches tags (train and test)")
    args = ap.parse_args()
    tr, te = s1_groups("train"), s1_groups("test")
    hold = tr[is_holdout(tr.s1.to_numpy())].reset_index(drop=True)
    truth = pq.read_table(truth_path()).to_pandas()
    truth = truth[truth.s1.isin(hold.s1)]
    for split, d in (("train", tr), ("test", te)):
        u = d.groupby("country").agg(s1=("s1", "size"), mean_group=("n_core", "mean"),
                                     unique_name=("n_core", lambda x: (x == 1).mean()))
        print(f"{split} S1 same-core-name groups:\n{u.round(3).to_string()}\n")
    for tag in args.tags.split(","):
        t = per_s1(te, read_table("matches", tag, "test"), None)
        h = per_s1(hold, read_table("matches", tag, "train"), truth) if exists("matches", tag, "train") else None
        print(f"== {tag}: holdout macro F0.5 " + (f"{h.F.mean():.5f}" if h is not None else "n/a (test only)"))
        for c in sorted(set(te.country)):
            share_t = t[t.country == c].groupby("g", observed=False).size()
            share_t = share_t / share_t.sum()
            p_test, empty = t[t.country == c].P.mean(), (t[t.country == c].P == 0).mean()
            if h is None or c not in set(h.country):
                print(f"  {c}: predicted/S1 {p_test:.4f}, empty {100 * empty:.2f}%")
                continue
            a = h[h.country == c].groupby("g", observed=False).agg(F=("F", "mean"), P=("P", "mean"))
            print(f"  {c}: holdout F0.5 {h[h.country == c].F.mean():.5f}, re-weighted to the test mix "
                  f"{np.nansum(a.F * share_t):.5f}; predicted/S1 holdout re-weighted {np.nansum(a.P * share_t):.4f}, "
                  f"test {p_test:.4f}; test empty {100 * empty:.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
