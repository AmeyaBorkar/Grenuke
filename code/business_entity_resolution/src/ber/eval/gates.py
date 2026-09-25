"""Gate decisions (plans/FINAL_PLAN.md section 9, docs/CONTRACTS.md C10): paired bootstrap over S1 entities.

Both systems are scored on the same S1 universe, so per-entity F0.5 differences are paired. Resampling uses
Poisson(1) weights per entity (equivalent to the classic bootstrap at this scale) in batches, so 1,000 resamples
over ~550k holdout entities take seconds and little memory.

CLI (compares two C9 match artifacts on the holdout and prints a block to paste into the gate record):
    python -m ber.eval.gates --base sachi-model-v0 --new sachi-model-v1 [--folds 0] [--min-gain 0.002]
"""
from __future__ import annotations

import argparse
import json
import sys

import numpy as np
import pandas as pd

from .metric import per_entity_f05

MIN_GAIN = 0.002


def paired_bootstrap(f_base, f_new, n_boot: int = 1000, seed: int = 0, batch: int = 50) -> dict:
    """Mean per-entity difference ``f_new - f_base`` with a 95% bootstrap interval."""
    a = np.asarray(f_base, dtype=np.float64)
    b = np.asarray(f_new, dtype=np.float64)
    if a.shape != b.shape or a.ndim != 1 or a.size == 0:
        raise ValueError("f_base and f_new must be 1-D arrays of the same, non-zero length")
    d = b - a
    rng = np.random.default_rng(seed)
    boots = []
    for start in range(0, n_boot, batch):
        w = rng.poisson(1.0, size=(min(batch, n_boot - start), d.size)).astype(np.float64)
        boots.append((w @ d) / np.maximum(w.sum(axis=1), 1.0))
    boots = np.concatenate(boots)
    lo, hi = np.quantile(boots, [0.025, 0.975])
    return {
        "delta": float(d.mean()),
        "ci_low": float(lo),
        "ci_high": float(hi),
        "p_better": float((boots > 0).mean()),
        "n": int(d.size),
        "n_boot": int(n_boot),
    }


def compare(pred_base: pd.DataFrame, pred_new: pd.DataFrame, true_pairs: pd.DataFrame, s1_universe, *,
            groups=None, n_boot: int = 1000, seed: int = 0, min_gain: float = MIN_GAIN) -> dict:
    """Gate result for two prediction pair tables (``s1``, ``r``) on ``s1_universe``.

    ``keep`` is True when the mean gain is at least ``min_gain`` and the 95% interval is above zero.
    ``groups`` (S1 eid -> label, e.g. country) adds the mean difference per group.
    """
    fa = per_entity_f05(pred_base, true_pairs, s1_universe)["f05"]
    fb = per_entity_f05(pred_new, true_pairs, s1_universe)["f05"]
    out = paired_bootstrap(fa.to_numpy(), fb.to_numpy(), n_boot=n_boot, seed=seed)
    out.update({"base_f05": float(fa.mean()), "new_f05": float(fb.mean()), "min_gain": min_gain})
    if groups is not None:
        g = pd.Series(groups).reindex(fa.index)
        out["delta_by_group"] = {str(k): float(v) for k, v in (fb - fa).groupby(g).mean().items()}
    out["keep"] = bool(out["delta"] >= min_gain and out["ci_low"] > 0)
    return out


def _parse_folds(text: str | None):
    if not text:
        return None
    folds: list[int] = []
    for part in text.split(","):
        lo, _, hi = part.partition("-")
        folds.extend(range(int(lo), int(hi or lo) + 1))
    return tuple(folds)


def main(argv: list[str] | None = None) -> int:
    from ..artifacts import read_table
    from ..records import load_records, load_truth
    from .splits import in_folds, is_holdout

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", required=True, help="tag of the baseline matches (work/matches/<tag>/train.parquet)")
    ap.add_argument("--new", required=True, help="tag of the candidate matches")
    ap.add_argument("--folds", help="restrict to these folds, e.g. 0 or 0-4 (default: the shared holdout)")
    ap.add_argument("--min-gain", type=float, default=MIN_GAIN)
    ap.add_argument("--n-boot", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)

    rec = load_records("train", columns=["eid", "source", "country"])
    s1 = rec[rec["source"] == 1]
    folds = _parse_folds(args.folds)
    mask = is_holdout(s1["eid"]) if folds is None else in_folds(s1["eid"], folds)
    universe = s1["eid"].to_numpy()[mask]
    country = pd.Series(s1["country"].to_numpy(), index=s1["eid"].to_numpy())
    res = compare(read_table("matches", args.base, "train", ["s1", "r"]), read_table("matches", args.new, "train", ["s1", "r"]),
                  load_truth(), universe, groups=country, n_boot=args.n_boot, seed=args.seed, min_gain=args.min_gain)
    verdict = "KEEP" if res["keep"] else "DROP (or retry)"
    print(f"| baseline | `{args.base}` | macro F0.5 {res['base_f05']:.4f} |")
    print(f"| candidate | `{args.new}` | macro F0.5 {res['new_f05']:.4f} |")
    print(f"| delta (95% CI) | {res['delta']:+.4f} ({res['ci_low']:+.4f}, {res['ci_high']:+.4f}) | P(better) {res['p_better']:.3f} |")
    print(f"| per country | {', '.join(f'{k} {v:+.4f}' for k, v in res.get('delta_by_group', {}).items())} | n = {res['n']:,} |")
    print(f"| verdict | **{verdict}** | min gain {args.min_gain} |")
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
