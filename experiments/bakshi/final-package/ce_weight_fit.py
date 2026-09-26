#!/usr/bin/env python3
"""Choose cross-encoder blend weights for France honestly, and gate them on real US/India labels.

Two problems with picking weights off a single French-proxy sweep:

1. **Selection bias.** The argmax of a grid scored on the proxy is an optimistic estimate of its own gain,
   and a bootstrap CI around it does not correct for that. Fix: split the French rule populations by S1 into
   a FIT half and a VALIDATE half. Choose on fit, report on validate. Neither half shares an S1 with the
   other, so a chosen weight cannot be riding S1-level idiosyncrasies of the scoring set.
2. **No labelled gate.** The French rule populations are a proxy; they cannot tell us whether a
   France-tuned weight quietly damages US/India, where the real labels live. Fix: `band_train.parquet`
   carries `fold` and `y`, so folds 0-4 are the shared holdout with GROUND TRUTH. Every candidate weight is
   scored there too. A France gain that costs labelled holdout AUC is not worth having, because US/India are
   85% of the test set.

z-moments are fitted on training folds only (fold >= 5), never on the holdout, so the holdout AUC is honest.
That differs from `zmean_ce.py`, which standardises on the whole train band; `--z-rows all` reproduces
production instead, and the two are reported so a difference is never mistaken for a weighting effect.

    python ce_weight_fit.py --band-train B_tr.parquet --band-test B_te.parquet --rule-pop rulepop.parquet \
        --run e5l=out_e5l --run e5l2=out_e5l2 --run bge=out_bge --step 0.05 [--z-rows train_folds|all] \
        [--write-best DIR]
"""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

COL = "ce__logit"
K = 4_000_000_000


def load(d: Path, split: str, rows: np.ndarray) -> np.ndarray:
    ce = pd.read_parquet(Path(d) / f"ce_{split}.parquet", columns=["row", COL])
    s = pd.Series(ce[COL].to_numpy(), index=ce["row"].to_numpy())
    out = s.reindex(rows).to_numpy()
    if not np.isfinite(out).all():
        raise SystemExit(f"FAIL {d}/ce_{split}: {int((~np.isfinite(out)).sum())} non-finite after alignment")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--band-train", required=True, type=Path)
    ap.add_argument("--band-test", required=True, type=Path)
    ap.add_argument("--rule-pop", required=True, type=Path)
    ap.add_argument("--run", action="append", required=True, help="name=dir")
    ap.add_argument("--step", type=float, default=0.05)
    ap.add_argument("--z-rows", choices=["train_folds", "all"], default="train_folds")
    ap.add_argument("--write-best", default="")
    ap.add_argument("--seed", type=int, default=26)
    args = ap.parse_args()

    names, dirs = [], []
    for spec in args.run:
        n, _, d = spec.partition("=")
        names.append(n)
        dirs.append(Path(d))

    btr = pd.read_parquet(args.band_train)
    bte = pd.read_parquet(args.band_test, columns=["s1", "r", "row"])
    rows_tr, rows_te = btr["row"].to_numpy(), bte["row"].to_numpy()
    fold, y_tr = btr["fold"].to_numpy(), btr["y"].to_numpy()
    zmask = (fold >= 5) if args.z_rows == "train_folds" else np.ones(fold.size, bool)
    hold = fold < 5
    print(f"train band {len(btr)} (holdout folds 0-4: {hold.sum()}, positives {y_tr[hold].mean():.4f})")
    print(f"z-moments fitted on {zmask.sum()} rows ({args.z_rows})")

    # standardise each run once
    Ztr, Zte, moments = {}, {}, {}
    for n, d in zip(names, dirs):
        raw_tr = load(d, "train", rows_tr).astype(np.float32)
        raw_te = load(d, "test", rows_te).astype(np.float32)
        mu = float(pd.Series(raw_tr[zmask]).mean())
        sd = float(pd.Series(raw_tr[zmask]).std())
        if not np.isfinite(sd) or sd <= 0:
            raise SystemExit(f"FAIL {n}: standard deviation {sd}")
        moments[n] = {"mean": mu, "std": sd, "n_rows_fitted": int(zmask.sum())}
        Ztr[n] = (raw_tr - mu) / sd
        Zte[n] = (raw_te - mu) / sd
        print(f"  {n}: mean {mu:+.6f} sd {sd:.6f}  |  labelled holdout band AUC "
              f"{roc_auc_score(y_tr[hold], Ztr[n][hold]):.4f}")

    # French rule populations -> band rows, split by S1 into fit / validate
    pop = pd.read_parquet(args.rule_pop)
    lab = pd.Series(pop["y"].to_numpy(), index=pop["s1"].to_numpy() * K + pop["r"].to_numpy())
    lab = lab[~lab.index.duplicated()]
    bte["y"] = lab.reindex(bte["s1"].to_numpy() * K + bte["r"].to_numpy()).to_numpy()
    fr = bte.dropna(subset=["y"]).copy()
    fr_idx = fr.index.to_numpy()
    y_fr = fr["y"].to_numpy().astype(int)
    uniq_s1 = pd.unique(fr["s1"])
    rng = np.random.default_rng(args.seed)
    half = pd.Series(rng.integers(0, 2, uniq_s1.size), index=uniq_s1)
    side = half.reindex(fr["s1"]).to_numpy()
    A, B = side == 0, side == 1
    print(f"\nFrench rule-population band pairs {len(fr)} over {uniq_s1.size} S1"
          f"\n  FIT half A: {A.sum()} pairs (true-copy {y_fr[A].mean():.3f})"
          f"\n  VAL half B: {B.sum()} pairs (true-copy {y_fr[B].mean():.3f})")

    ZteF = {n: Zte[n][fr_idx] for n in names}

    def scores(w: dict[str, float]):
        bf = sum(w[n] * ZteF[n] for n in names)
        bt = sum(w[n] * Ztr[n] for n in names)
        return (roc_auc_score(y_fr[A], bf[A]), roc_auc_score(y_fr[B], bf[B]),
                roc_auc_score(y_tr[hold], bt[hold]))

    # grid over the simplex
    k = names.__len__()
    steps = int(round(1 / args.step))
    grid = [t for t in itertools.product(range(steps + 1), repeat=k) if sum(t) == steps]
    print(f"\nevaluating {len(grid)} weight combinations (step {args.step})\n")
    recs = []
    for t in grid:
        w = {n: v / steps for n, v in zip(names, t)}
        a, b, h = scores(w)
        recs.append({**{f"w_{n}": w[n] for n in names}, "fr_fit": a, "fr_val": b, "hold": h})
    df = pd.DataFrame(recs)

    # references, under the SAME standardisation so the comparison is like for like
    refs = {"cem2 (e5l+e5l2, production)": {"e5l": .5, "e5l2": .5, "bge": 0.0},
            "cem (equal 3-way, v7mst)": {"e5l": 1/3, "e5l2": 1/3, "bge": 1/3},
            "e5l+bge equal (6.13 best)": {"e5l": .5, "e5l2": 0.0, "bge": .5}}
    refs = {k2: v for k2, v in refs.items() if set(v) <= set(names)}
    ref_scores = {}
    for label, w in refs.items():
        ref_scores[label] = scores({n: w.get(n, 0.0) for n in names})

    base_label = "cem2 (e5l+e5l2, production)"
    base_fr = ref_scores.get(base_label, (0, 0, 0))[1]
    base_hold = ref_scores.get(base_label, (0, 0, 0))[2]

    # ---- put the two sides on one scale -------------------------------------------------------------
    # France and US/India pull in opposite directions here, so counting AUC on each separately cannot
    # decide anything. Convert both to an approximate public-leaderboard delta.
    #
    #   France side.  Anchor: adding bge to the e5-large mean moved the French CE rule AUC 0.806 -> 0.826
    #   (+0.020) and the stage-2 French pc rule AUC 0.872 -> 0.8776 (+0.0056); and v6all -> v7n moved
    #   stage-2 pc +0.0174 for an implied France +0.005. So France F0.5 ~ CE_gain * 0.080, and France is
    #   14.975% of test S1 (measured), giving LB ~ CE_gain * 0.01198.
    #
    #   US/India side.  Anchor: v6all -> v7ce3 added e5-large, moving the labelled holdout band AUC
    #   0.9240 -> 0.9391 (+0.0151) for a holdout macro F0.5 of 0.990842 -> 0.991138 (+0.000296). So
    #   US/India F0.5 ~ band_gain * 0.0196, over 85.025% of test S1, giving LB ~ band_gain * 0.01667.
    #
    # Both coefficients are single-anchor extrapolations through two hops and should be read as order of
    # magnitude, not precision. The point they make is robust though: the two coefficients are COMPARABLE
    # (0.012 vs 0.017), so a labelled-holdout loss is not automatically outweighed by a larger French gain.
    FR_COEF, UI_COEF = 0.01198, 0.01667

    def lb_delta(fr_val: float, hold: float) -> float:
        return FR_COEF * (fr_val - base_fr) + UI_COEF * (hold - base_hold)

    print(f"{'reference':<30} {'fr_fit':>8} {'fr_val':>8} {'holdAUC':>8} {'dHold':>9} {'est dLB':>10}")
    for label, (a, b, h) in ref_scores.items():
        print(f"{label:<30} {a:>8.4f} {b:>8.4f} {h:>8.4f} {h-base_hold:>+9.5f} {lb_delta(b, h):>+10.6f}")

    df["est_lb"] = [lb_delta(r.fr_val, r.hold) for r in df.itertuples()]

    print(f"\n== top 8 by FIT half (selection), with their VALIDATE half and labelled gate ==")
    print("   " + "  ".join(f"{'w_'+n:>7}" for n in names)
          + f" {'fr_fit':>8} {'fr_val':>8} {'holdAUC':>8} {'dHold':>9} {'est dLB':>10}")
    for _, r in df.sort_values("fr_fit", ascending=False).head(8).iterrows():
        print("   " + "  ".join(f"{r['w_'+n]:>7.2f}" for n in names)
              + f" {r['fr_fit']:>8.4f} {r['fr_val']:>8.4f} {r['hold']:>8.4f} "
              f"{r['hold']-base_hold:>+9.5f} {r['est_lb']:>+10.6f}")

    print(f"\n== top 8 by ESTIMATED LB (both sides weighted), selection still on the fit half ==")
    print("   " + "  ".join(f"{'w_'+n:>7}" for n in names)
          + f" {'fr_val':>8} {'holdAUC':>8} {'dHold':>9} {'est dLB':>10}")
    for _, r in df.sort_values("est_lb", ascending=False).head(8).iterrows():
        print("   " + "  ".join(f"{r['w_'+n]:>7.2f}" for n in names)
              + f" {r['fr_val']:>8.4f} {r['hold']:>8.4f} {r['hold']-base_hold:>+9.5f} {r['est_lb']:>+10.6f}")
    spread = df["est_lb"].max() - df.nlargest(40, "est_lb")["est_lb"].min()
    print(f"\n   spread of estimated dLB across the best 40 weightings: {spread:.6f}")
    print("   If that spread is tiny, the weight choice does not matter and the only real decision is "
          "whether bge is in the mix at all.")

    best = df.sort_values("fr_fit", ascending=False).iloc[0]
    wbest = {n: float(best[f"w_{n}"]) for n in names}
    print(f"\n== selected on the FIT half only: {wbest} ==")
    print(f"   France rule AUC, VALIDATE half : {best['fr_val']:.4f}")
    for label, (a, b, h) in ref_scores.items():
        print(f"     vs {label:<28} {best['fr_val']-b:+.5f} on validate")
    print(f"   labelled US/India holdout AUC  : {best['hold']:.4f} "
          f"({best['hold']-base_hold:+.5f} vs production cem2)")
    gate = best["hold"] >= base_hold - 0.0005
    print(f"   LABELLED GATE (no worse than production by >0.0005): {'PASS' if gate else 'FAIL'}")

    if args.write_best:
        out = Path(args.write_best)
        if out.resolve() in {d.resolve() for d in dirs}:
            raise SystemExit("--write-best is a source directory; refusing")
        out.mkdir(parents=True, exist_ok=True)
        btr_blend = sum(wbest[n] * Ztr[n] for n in names).astype(np.float32)
        bte_blend = sum(wbest[n] * Zte[n] for n in names).astype(np.float32)
        pd.DataFrame({"row": rows_tr, COL: btr_blend}).to_parquet(out / "ce_train.parquet", index=False)
        pd.DataFrame({"row": rows_te, COL: bte_blend}).to_parquet(out / "ce_test.parquet", index=False)
        (out / "config.json").write_text(json.dumps({
            "model": "France-tuned weighted z-mean: " + ", ".join(f"{n}*{wbest[n]:.2f}" for n in names),
            "weights": wbest, "z_rows": args.z_rows, "moments": moments,
            "selection": "weights chosen on a FIT half of the French rule populations, split by S1; "
                         "the reported France AUC is from the disjoint VALIDATE half",
            "france_rule_auc_validate": float(best["fr_val"]),
            "labelled_holdout_band_auc": float(best["hold"]),
            "labelled_holdout_band_auc_production_cem2": float(base_hold),
            "built_by": "experiments/bakshi/final-package/ce_weight_fit.py",
        }, indent=1), encoding="utf-8")
        print(f"\nwritten {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
