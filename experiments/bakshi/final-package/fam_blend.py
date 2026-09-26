#!/usr/bin/env python3
"""Family-balanced consensus of cross-encoder logits (Track B), plus a label-free screener.

Why this exists. `zmean_ce.py` averages every run it is given with equal weight. The two
multilingual-e5-large fine-tunes correlate at 0.986 on the holdout band, so an equal three-way mean of
{e5l, e5l2, bge} gives the E5 *family* two votes and BGE one, even though the two E5 runs are close to
one source of evidence. On France the models disagree 4x as often as on the labelled countries
(RESEARCH_v6.md 6.6), so how much weight BGE gets is not a detail. This script averages within a family
first, then weights across families:

    E     = mean(z(e5l), z(e5l2))          # one vote for the E5 family
    blend = w_e5 * E + w_bge * z(bge)

Predeclared designs (do not sweep these against the leaderboard):
    reproduction of production :  --family e5=out_e5l,out_e5l2                       --weight e5=1
    existing equal-checkpoint  :  --family e5=out_e5l,out_e5l2 --family bge=out_bge  --weight e5=0.667 --weight bge=0.333
    main new family-balanced   :  ... --weight e5=0.5   --weight bge=0.5
    optional BGE-heavy         :  ... --weight e5=0.333 --weight bge=0.667

Guards, all hard failures rather than warnings:
  * every source must cover exactly the same `row` set as the band, in the same order;
  * no duplicate rows, no missing rows, no non-finite logits, no zero standard deviation;
  * z-moments are fitted on a declared row mask only, and the mask definition is saved;
  * source directories are never written to.

Standardisation rows (`--z-rows`). `train_folds` fits the mean/sd on training folds only (`fold >= 5`),
excluding the shared holdout, which is what a newly fitted transform should do. `all` fits on every train
band row, which is what `zmean_ce.py` does in production -- use it only for the reproduction arm, so a
difference is never silently attributed to family weighting when it is really the row population.

Subcommands::

    python fam_blend.py build  --band-train B_tr.parquet --band-test B_te.parquet \
        --family e5=out_e5l,out_e5l2 --family bge=out_bge --weight e5=0.5 --weight bge=0.5 \
        --out out_fam5050 [--z-rows train_folds|all] [--verify-against out_cem2]

    python fam_blend.py screen --band-test B_te.parquet --rule-pop rule_pop.parquet \
        out_e5l out_e5l2 out_bge out_cem2 out_fam5050
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

COL = "ce__logit"


def sha256(path: Path, chunk: int = 1 << 22) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def die(msg: str) -> None:
    print(f"FAIL: {msg}")
    raise SystemExit(1)


def load_run(d: Path, split: str, band_rows: np.ndarray) -> np.ndarray:
    """Read one run's logits for `split`, aligned to the band's row order. Fails on any irregularity."""
    p = d / f"ce_{split}.parquet"
    if not p.is_file():
        die(f"{p} not found")
    df = pd.read_parquet(p, columns=["row", COL])
    if df["row"].duplicated().any():
        die(f"{p}: duplicate row ids ({int(df['row'].duplicated().sum())})")
    s = pd.Series(df[COL].to_numpy(), index=df["row"].to_numpy())
    missing = np.setdiff1d(band_rows, s.index.to_numpy(), assume_unique=False)
    if missing.size:
        die(f"{p}: {missing.size} band rows absent, e.g. {missing[:5].tolist()}")
    # Keep the stored dtype (float32). zmean_ce.py does all of its arithmetic in float32, and the
    # submitted stage 2 was trained on float32-computed features, so float32 is the faithful path.
    # Promoting to float64 here is more accurate and differs by ~1 float32 ULP (2.4e-07), which is
    # enough to break a bit-for-bit reproduction check. See --compute-dtype.
    out = s.reindex(band_rows).to_numpy()
    if not np.isfinite(out).all():
        die(f"{p}: {int((~np.isfinite(out)).sum())} non-finite logits after alignment")
    extra = s.index.size - band_rows.size
    if extra:
        print(f"  note {d.name}/{split}: {extra} rows beyond the band, ignored")
    return out


def cmd_build(a: argparse.Namespace) -> int:
    families: dict[str, list[Path]] = {}
    for spec in a.family:
        name, _, dirs = spec.partition("=")
        if not dirs:
            die(f"--family needs name=dir[,dir]: got {spec!r}")
        families[name] = [Path(x) for x in dirs.split(",")]
    weights = {}
    for spec in a.weight:
        name, _, val = spec.partition("=")
        weights[name] = float(val)
    if set(weights) != set(families):
        die(f"--weight names {sorted(weights)} do not match --family names {sorted(families)}")
    total = sum(weights.values())
    if abs(total - 1.0) > 1e-9:
        print(f"  note: weights sum to {total:.6f}, normalising to 1")
        weights = {k: v / total for k, v in weights.items()}

    band_tr = pd.read_parquet(a.band_train)
    band_te = pd.read_parquet(a.band_test)
    for nm, b in (("band_train", band_tr), ("band_test", band_te)):
        if "row" not in b.columns:
            die(f"{nm} has no `row` column")
        if b["row"].duplicated().any():
            die(f"{nm}: duplicate row ids")
    rows_tr, rows_te = band_tr["row"].to_numpy(), band_te["row"].to_numpy()

    # ---- the declared standardisation mask -----------------------------
    if a.z_rows == "train_folds":
        if "fold" not in band_tr.columns:
            die("--z-rows train_folds needs a `fold` column in band_train (fold >= 5 = training folds)")
        mask = band_tr["fold"].to_numpy() >= 5
        mask_desc = "band_train fold >= 5 (training folds only; shared holdout folds 0-4 excluded)"
    else:
        mask = np.ones(rows_tr.size, bool)
        mask_desc = "all band_train rows (matches zmean_ce.py production behaviour, holdout included)"
    print(f"== standardisation rows: {mask.sum()} / {mask.size} -- {mask_desc}")
    if mask.sum() < 1000:
        die(f"only {mask.sum()} rows in the standardisation mask; refusing to fit on that")

    # ---- per-run z, then per-family mean -------------------------------
    moments, fam_tr, fam_te, src_hashes = {}, {}, {}, {}
    for fam, dirs in families.items():
        zt, ze = [], []
        for d in dirs:
            raw_tr = load_run(d, "train", rows_tr).astype(a.compute_dtype)
            raw_te = load_run(d, "test", rows_te).astype(a.compute_dtype)
            # Moments are taken from a pandas Series of the same dtype and with ddof=1, exactly as
            # zmean_ce.py does (`tr[s].ce__logit.mean()` / `.std()`), so the reproduction arm matches.
            mu = float(pd.Series(raw_tr[mask]).mean())
            sd = float(pd.Series(raw_tr[mask]).std())
            if not np.isfinite(sd) or sd <= 0:
                die(f"{d}: standard deviation {sd} on the mask; cannot standardise")
            moments[d.name] = {"mean": mu, "std": sd, "n_rows_fitted": int(mask.sum())}
            src_hashes[f"{d.name}/ce_train.parquet"] = sha256(d / "ce_train.parquet")
            src_hashes[f"{d.name}/ce_test.parquet"] = sha256(d / "ce_test.parquet")
            zt.append((raw_tr - mu) / sd)
            ze.append((raw_te - mu) / sd)
            print(f"  {fam}/{d.name}: mean {mu:+.6f} sd {sd:.6f}")
        fam_tr[fam] = np.mean(zt, axis=0)
        fam_te[fam] = np.mean(ze, axis=0)

    blend_tr = sum(weights[f] * fam_tr[f] for f in families).astype(np.float32)
    blend_te = sum(weights[f] * fam_te[f] for f in families).astype(np.float32)
    if not (np.isfinite(blend_tr).all() and np.isfinite(blend_te).all()):
        die("the blend contains non-finite values")

    # ---- correlations between families, per country if we can ----------
    if len(families) > 1:
        print("== family correlations on the test band ==")
        names = list(families)
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                r = float(np.corrcoef(fam_te[names[i]], fam_te[names[j]])[0, 1])
                print(f"  {names[i]} vs {names[j]}: {r:+.4f}")

    out = Path(a.out)
    if out.resolve() in {d.resolve() for ds in families.values() for d in ds}:
        die("--out is one of the source directories; refusing to overwrite a source")
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"row": rows_tr, COL: blend_tr}).to_parquet(out / "ce_train.parquet", index=False)
    pd.DataFrame({"row": rows_te, COL: blend_te}).to_parquet(out / "ce_test.parquet", index=False)
    cfg = {
        "model": "family-balanced consensus: " + "; ".join(
            f"{f}({','.join(d.name for d in ds)})*{weights[f]:.4f}" for f, ds in families.items()),
        "families": {f: [d.name for d in ds] for f, ds in families.items()},
        "weights": weights,
        "z_rows": a.z_rows,
        "z_mask": mask_desc,
        "compute_dtype": a.compute_dtype,
        "moments": moments,
        "source_sha256": src_hashes,
        "band_train": str(a.band_train), "band_test": str(a.band_test),
        "n_train": int(rows_tr.size), "n_test": int(rows_te.size),
        "built_by": "experiments/bakshi/final-package/fam_blend.py",
    }
    (out / "config.json").write_text(json.dumps(cfg, indent=1), encoding="utf-8")
    print(f"== written {out} ({rows_tr.size} train, {rows_te.size} test rows)")

    # ---- optional: prove we reproduce an existing production dir -------
    if a.verify_against:
        ref = Path(a.verify_against)
        print(f"== reproduction check against {ref.name} ==")
        okall = True
        for split, rows, mine in (("train", rows_tr, blend_tr), ("test", rows_te, blend_te)):
            theirs = load_run(ref, split, rows).astype(np.float32)
            same_bits = bool(np.array_equal(theirs, mine))
            dmax = float(np.max(np.abs(theirs.astype(np.float64) - mine.astype(np.float64))))
            print(f"  {split}: bit-identical={same_bits}  max|diff|={dmax:.3e}")
            okall &= same_bits
        if okall:
            print("  REPRODUCED EXACTLY -- these copies and this tooling match production.")
        else:
            print("  NOT bit-identical. Before trusting any new blend, find out why: check --z-rows "
                  "(production uses `all`), the family/weight spec, and that the source dirs are the "
                  "ones production actually consumed.")
    return 0


def tie_unaware_auc(y: np.ndarray, s: np.ndarray) -> float:
    """The repo's own AUC (ce_rule_auc.py): positional ranks, ties NOT averaged. Kept only for
    comparability with the numbers already circulated; it is biased for saturated or rounded scores."""
    o = np.argsort(s, kind="stable")
    r = np.empty(len(s))
    r[o] = np.arange(1, len(s) + 1)
    n1 = y.sum()
    n0 = len(y) - n1
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def cmd_screen(a: argparse.Namespace) -> int:
    from sklearn.metrics import roc_auc_score

    K = 4_000_000_000
    band = pd.read_parquet(a.band_test, columns=["s1", "r", "row"])
    pop = pd.read_parquet(a.rule_pop)
    lab = pd.Series(pop["y"].to_numpy(), index=pop["s1"].to_numpy() * K + pop["r"].to_numpy())
    lab = lab[~lab.index.duplicated()]
    band["y"] = lab.reindex(band["s1"].to_numpy() * K + band["r"].to_numpy()).to_numpy()
    band = band.dropna(subset=["y"])
    y_all = band["y"].to_numpy().astype(int)
    print(f"rule-population pairs in the band: {len(band)} (true-copy share {y_all.mean():.3f})")
    if y_all.min() == y_all.max():
        die("only one class present; AUC is undefined")

    # Common rows across every run, so the AUCs are comparable rather than each on its own subset.
    scores, common = {}, None
    for d in a.dirs:
        p = Path(d) / "ce_test.parquet"
        if not p.is_file():
            print(f"  skip {d}: no ce_test.parquet")
            continue
        ce = pd.read_parquet(p, columns=["row", COL])
        s = pd.Series(ce[COL].to_numpy(), index=ce["row"].to_numpy()).reindex(band["row"].to_numpy()).to_numpy()
        scores[Path(d).name] = s
        ok = np.isfinite(s)
        common = ok if common is None else (common & ok)
    if not scores:
        die("no readable run directories")
    n_common = int(common.sum())
    print(f"common finite rows across all {len(scores)} runs: {n_common} "
          f"({n_common / len(band):.1%} coverage; true-copy share {y_all[common].mean():.3f})")

    print(f"\n{'run':<16} {'AUC (sklearn)':>14} {'AUC (repo, ties unaveraged)':>29} {'own coverage':>13} {'ties':>8}")
    for name, s in scores.items():
        own = np.isfinite(s)
        y_c, s_c = y_all[common], s[common]
        ties = 1.0 - len(np.unique(s_c)) / len(s_c)
        print(f"{name:<16} {roc_auc_score(y_c, s_c):>14.4f} {tie_unaware_auc(y_c, s_c):>29.4f} "
              f"{own.sum() / len(band):>12.1%} {ties:>7.1%}")
    print("\nsklearn averages tied ranks and is the number to use. A large `ties` share is exactly when "
          "the repo's own AUC drifts from it.")
    print("Reminder: these are PROXY labels (post_ops operation families), not French ground truth, and a "
          "model self-trained on those populations cannot be ranked here at all.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build")
    b.add_argument("--band-train", type=Path, required=True)
    b.add_argument("--band-test", type=Path, required=True)
    b.add_argument("--family", action="append", required=True, help="name=dir[,dir]")
    b.add_argument("--weight", action="append", required=True, help="name=float")
    b.add_argument("--out", required=True)
    b.add_argument("--z-rows", choices=["train_folds", "all"], default="train_folds")
    b.add_argument("--compute-dtype", choices=["float32", "float64"], default="float32",
                   help="arithmetic precision. float32 (default) matches zmean_ce.py and the dtype the "
                        "submitted stage 2 was trained on, and is required for a bit-for-bit reproduction "
                        "check. float64 is marginally more accurate but differs by ~2.4e-07.")
    b.add_argument("--verify-against", default="", help="existing run dir to reproduce, e.g. out_cem2")
    b.set_defaults(fn=cmd_build)

    s = sub.add_parser("screen")
    s.add_argument("--band-test", type=Path, required=True)
    s.add_argument("--rule-pop", type=Path, required=True)
    s.add_argument("dirs", nargs="+")
    s.set_defaults(fn=cmd_screen)

    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
