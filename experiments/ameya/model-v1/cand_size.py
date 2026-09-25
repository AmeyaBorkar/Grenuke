"""Candidate-set size vs matching F0.5: how small can the final candidate set (the stage-2 input) get?

    python experiments/ameya/model-v1/cand_size.py --s1 ameya-s1-v5all --matches ameya-model-v5all \
        --final ameya-model-v5all-ops

The organisers rank a smaller candidate set per S1 higher, beyond the leaderboard. The candidate set today is
the stage-2 input: p0 >= tau0 and p1 >= P_MIN (0.002). This tries tighter stage-1 cuts:
- p1 >= t;
- the S1's top k records by p1;
- the record's top m S1 by p1 (ownership is an argmax over S1, so a record's low-ranked S1 are almost never predicted);
- combinations of these.
For each cut:
- holdout: pairs per S1, the current predictions that fall outside the cut, the macro F0.5 of the predictions
  restricted to the kept pairs (no re-decision, so a slight underestimate), pair recall, and the kept set's
  oracle F0.5;
- test: pairs per S1 per country, and the final predictions per S1 that fall outside the cut.
"""
from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from ber.artifacts import read_table
from ber.paths import artifact_dir, artifact_path, records_path, truth_path
from common import holdout_universe

K = 4_000_000_000
CUTS = ([("p1>=0.002 (now)", lambda d: d.p1 >= 0.002)]
        + [(f"p1>={t}", (lambda t: lambda d: d.p1 >= t)(t)) for t in (0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3)]
        + [(f"top{k}/S1", (lambda k: lambda d: d.k_s1 <= k)(k)) for k in (3, 4, 5, 6, 8)]
        + [(f"top{m}/record", (lambda m: lambda d: d.k_r <= m)(m)) for m in (1, 2, 3)]
        + [("p1>=0.02 & top2/record", lambda d: (d.p1 >= 0.02) & (d.k_r <= 2)),
           ("p1>=0.05 & top2/record", lambda d: (d.p1 >= 0.05) & (d.k_r <= 2)),
           ("p1>=0.02 & top6/S1", lambda d: (d.p1 >= 0.02) & (d.k_s1 <= 6))])


def stage2_rows(s1_tag: str, split: str, tau0: float) -> pd.DataFrame:
    f = pq.ParquetFile(artifact_path("scores", s1_tag, split))
    parts = []
    for g in range(f.num_row_groups):
        t = f.read_row_group(g, columns=["s1", "r", "p0", "p1"]).to_pandas()
        parts.append(t.loc[(t.p0 >= tau0) & (t.p1 >= 0.002), ["s1", "r", "p1"]])
    d = pd.concat(parts, ignore_index=True)
    d = d.sort_values(["s1", "p1"], ascending=[True, False])
    d["k_s1"] = d.groupby("s1").cumcount() + 1
    d = d.sort_values(["r", "p1"], ascending=[True, False])
    d["k_r"] = d.groupby("r").cumcount() + 1
    return d.reset_index(drop=True)


def f05(h: np.ndarray, p: np.ndarray, t: np.ndarray) -> np.ndarray:
    den = 0.25 * t + p
    return np.where(den > 0, 1.25 * h / np.where(den > 0, den, 1), 1.0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--s1", default="ameya-s1-v5all", help="stage-1 scores tag (p0, p1)")
    ap.add_argument("--matches", default="ameya-model-v5all", help="predictions with a train split (holdout)")
    ap.add_argument("--final", default="ameya-model-v5all-ops", help="final test predictions")
    args = ap.parse_args()
    tau0 = json.loads((artifact_dir("models", args.s1) / "config.json").read_text())["tau0"]

    uni, _ = holdout_universe()
    d = stage2_rows(args.s1, "train", tau0)
    d = d[np.isin(d.s1.to_numpy(), uni)].reset_index(drop=True)
    truth = pq.read_table(truth_path()).to_pandas()
    truth = truth[truth.s1.isin(uni)]
    n_true = pd.Series(0, index=uni).add(truth.groupby("s1").size(), fill_value=0).to_numpy()
    pred = read_table("matches", args.matches, "train")
    pred = pred[pred.s1.isin(uni)]
    key = d.s1.to_numpy() * K + d.r.to_numpy()
    d["y"] = np.isin(key, truth.s1.to_numpy() * K + truth.r.to_numpy())
    d["pred"] = np.isin(key, pred.s1.to_numpy() * K + pred.r.to_numpy())
    print(f"holdout: {len(uni)} S1, stage-2 pairs {len(d) / len(uni):.3f} per S1, predictions {len(pred)} "
          f"({int(d.pred.sum())} inside the stage-2 set)")

    def count(s: pd.DataFrame) -> np.ndarray:
        return pd.Series(0, index=uni).add(s.groupby("s1").size(), fill_value=0).to_numpy()

    rows = []
    for name, fn in CUTS:
        keep = fn(d).to_numpy()
        s = d[keep]
        hits, n_pred, oracle = count(s[s.pred & s.y]), count(s[s.pred]), count(s[s.y])
        rows.append((name, keep.sum() / len(uni), int(d.pred.sum() - s.pred.sum()),
                     round(float(f05(hits, n_pred, n_true).mean()), 5), round(float(s.y.sum() / len(truth)), 5),
                     round(float(f05(oracle, oracle, n_true).mean()), 5)))
    print(pd.DataFrame(rows, columns=["cut", "pairs/S1", "predictions lost", "F0.5 restricted", "pair recall",
                                      "oracle F0.5"]).round(3).to_string(index=False))

    d = stage2_rows(args.s1, "test", tau0)
    rec = pq.read_table(records_path("test"), columns=["eid", "source", "country"]).to_pandas()
    rec = rec[rec.source == 1]
    d["c"] = pd.Series(rec.country.to_numpy(), index=rec.eid.to_numpy()).reindex(d.s1).to_numpy()
    n_c = rec.groupby("country").size()
    fin = read_table("matches", args.final, "test")
    d["pred"] = np.isin(d.s1.to_numpy() * K + d.r.to_numpy(), fin.s1.to_numpy() * K + fin.r.to_numpy())
    print(f"\ntest: stage-2 pairs {len(d) / len(rec):.3f} per S1; final predictions {len(fin)} ({int(d.pred.sum())} inside)")
    rows = []
    for name, fn in CUTS:
        keep = fn(d).to_numpy()
        per = d[keep].groupby("c").size() / n_c
        lost = d[d.pred & ~keep].groupby("c").size().reindex(n_c.index, fill_value=0) / n_c
        rows.append([name, keep.sum() / len(rec)] + [per.get(c, 0) for c in n_c.index] + [lost[c] for c in n_c.index])
    cols = ["cut", "pairs/S1"] + [f"{c}" for c in n_c.index] + [f"lost/S1 {c}" for c in n_c.index]
    print(pd.DataFrame(rows, columns=cols).round(4).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
