"""French pattern discovery on the France kit (france_kit.py output): where does France's prediction rate disagree
with the US/India truth rate of the same generator edit profile?

    python experiments/sachi/france_discover.py --kit work/kits/france-kit-v1 [--min-n 100] [--examples 8]

Method (the op-A/op-B method of post_ops.py, extended to every profile cell):
1. Cells = op x kind x pos x num_kind x street_typo x same_num (the post_ops.classify edit profile).
2. Truth rate per cell from the US/India holdout over ALL blocking candidates (holdout_rule_pairs, unbiased), per
   country; France's share predicted before (pred_model) and after (pred_final) the rules, over all candidates.
3. Flag a cell when France's predicted share is far from what the US/India truth implies, with enough pairs:
   - DROP candidate: US and India truth <= 10% but France predicts >= 20% (look-alikes accepted);
   - ADD candidate: US and India truth >= 90% but France predicts <= 70% (true copies missed).
4. Rough value: flipping a false merge on a typical French S1 (3.4 true records) is worth about +0.19 F0.5 on that S1,
   adding a missed true copy about +0.06; leaderboard ~= 0.15 x mean France gain.
5. Print examples of each flagged cell to read, and the uncertain band of France pairs with no op (pc 0.3-0.9),
   grouped by cell, as hypotheses for new operations (stage-2 set: biased, reading only).
No test labels exist or are used: truth comes only from US/India.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

CELL = ["op", "kind", "pos", "num_kind", "street_typo", "same_num"]
W_DROP, W_ADD = 0.19, 0.06


def load(kit: Path, name: str) -> pd.DataFrame:
    d = pd.read_parquet(kit / f"{name}.parquet")
    for c in CELL:
        if c in d:
            d[c] = d[c].fillna("").astype(str)
    return d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kit", default="work/kits/france-kit-v1")
    ap.add_argument("--min-n", type=int, default=100)
    ap.add_argument("--examples", type=int, default=8)
    a = ap.parse_args()
    kit = Path(a.kit)
    pd.set_option("display.width", 220, "display.max_colwidth", 48, "display.max_rows", 200)

    hr, fr = load(kit, "holdout_rule_pairs"), load(kit, "france_rule_pairs")
    fp = load(kit, "france_pairs")
    n_fr_s1 = fp["s1"].nunique()
    cell = [c for c in CELL if c in hr and c in fr]

    t = hr.groupby(cell + ["country"]).agg(n=("y", "size"), truth=("y", "mean"), pred=("pred", "mean")).unstack("country")
    t.columns = [f"{m}_{c}" for m, c in t.columns]
    f = fr.groupby(cell).agg(n_fr=("r", "size"), fr_model=("pred_model", "mean"), fr_final=("pred_final", "mean"))
    tab = f.join(t, how="left").reset_index()
    tcols = [c for c in tab if c.startswith("truth_")]
    tab["truth_min"], tab["truth_max"] = tab[tcols].min(axis=1), tab[tcols].max(axis=1)
    ncols = [c for c in tab if c.startswith("n_") and c != "n_fr"]
    tab["n_hold"] = tab[ncols].sum(axis=1)
    enough = (tab.n_fr >= a.min_n) & (tab.n_hold >= a.min_n)
    drop = enough & (tab.truth_max <= 0.10) & (tab.fr_final >= 0.20)
    add = enough & (tab.truth_min >= 0.90) & (tab.fr_final <= 0.70)
    tab["flag"] = np.select([drop, add], ["DROP?", "ADD?"], "")
    tab["pairs_to_flip"] = np.where(drop, tab.n_fr * (tab.fr_final - tab.truth_max),
                                    np.where(add, tab.n_fr * (tab.truth_min - tab.fr_final), 0.0))
    tab["est_france_f05"] = np.where(drop, tab.pairs_to_flip * W_DROP, tab.pairs_to_flip * W_ADD) / n_fr_s1
    tab["est_lb"] = 0.15 * tab.est_france_f05
    show = ["flag"] + cell + ["n_fr", "fr_model", "fr_final", "n_hold"] + tcols + ["est_france_f05", "est_lb"]
    print(f"France: {n_fr_s1:,} S1 with stage-2 pairs; rule-population cells with >= {a.min_n} pairs on both sides\n")
    print(tab[enough][show].sort_values("est_lb", ascending=False).round(4).to_string(index=False))

    flagged = tab[tab.flag != ""].sort_values("est_lb", ascending=False)
    print(f"\n{len(flagged)} flagged cells, total est. leaderboard gain {flagged.est_lb.sum():+.5f} "
          "(upper bound: assumes France follows US/India truth in each cell)")
    for _, row in flagged.iterrows():
        m = np.ones(len(fr), bool)
        for c in cell:
            m &= fr[c].to_numpy() == row[c]
        pick = fr[m & (fr.pred_final.to_numpy() if row.flag == "DROP?" else ~fr.pred_final.to_numpy())]
        print(f"\n=== {row.flag} {dict(row[cell])}  France n={row.n_fr}, predicted {row.fr_final:.2f}, "
              f"US/India truth {row.truth_min:.2f}-{row.truth_max:.2f}")
        for _, x in pick.sample(min(a.examples, len(pick)), random_state=0).iterrows():
            print(f"  pc={x.pc:.3f}  S1: {str(x.s1_name)[:40]:40s} | {str(x.s1_address)[:55]}")
            print(f"           R : {str(x.r_name)[:40]:40s} | {str(x.r_address)[:55]}")

    u = fp[(fp.op == "") & fp.pc.between(0.3, 0.9)]
    gcols = [c for c in ["kind", "pos", "num_kind", "same_num", "street_typo"] if c in u]
    print(f"\nFrance uncertain band with no op (pc 0.3-0.9): {len(u):,} pairs "
          f"({len(u) / n_fr_s1 * 1000:.1f} per 1000 S1); predicted {u.pred_final.mean():.2f}")
    top = u.groupby(gcols).agg(n=("r", "size"), pred=("pred_final", "mean"), pc=("pc", "median"))
    print(top.sort_values("n", ascending=False).head(15).round(3).to_string())
    for _, x in u.sample(min(3 * a.examples, len(u)), random_state=1).iterrows():
        print(f"  pc={x.pc:.3f} pred={int(x.pred_final)}  S1: {str(x.s1_name)[:38]:38s} | {str(x.s1_address)[:50]}")
        print(f"                     R : {str(x.r_name)[:38]:38s} | {str(x.r_address)[:50]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
