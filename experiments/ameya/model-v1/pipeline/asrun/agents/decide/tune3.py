"""(d6) Cross-fitted segment calibration + DP / break-even rules.

Isotonic y ~ p fitted on one half's rows per segment (owned & contested, owned & uncontested, not owned), applied to
the other half (2-fold cross-fit), then the expected-F0.5 DP (or the greedy break-even schedule) on calibrated q.
Every S1's decision uses a calibration fitted on the other half only, so the full-holdout number is honest.
Writes res3_<tag>.jsonl (summary rows) and arr3_<tag>.npz (per-entity F of each variant)."""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
from sklearn.isotonic import IsotonicRegression

from core import D, Hold, expected_f_select, greedy_perfect, to_q

TAG = sys.argv[1] if len(sys.argv) > 1 else "ameya-s3-v7nst"


def segments(H: Hold, c0: float) -> np.ndarray:
    """0 = owned uncontested, 1 = owned contested, 2 = not owned."""
    return np.where(~H.own, 2, np.where(H.riv >= c0, 1, 0)).astype(np.int8)


def crossfit_q(H: Hold, seg: np.ndarray, p_lo: float = 0.0) -> np.ndarray:
    """q for every row from an isotonic map fitted on the OTHER half (same segment)."""
    q = H.p.copy()
    for s in np.unique(seg):
        for h in (0, 1):
            fit = (seg == s) & (H.row_half != h) & (H.p >= p_lo)
            app = (seg == s) & (H.row_half == h) & (H.p >= p_lo)
            if fit.sum() < 100 or app.sum() == 0:
                continue
            iso = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip", increasing=True)
            iso.fit(H.p[fit], H.hit[fit])
            q[app] = iso.predict(H.p[app])
    return np.clip(q, 1e-6, 1 - 1e-6)


def main() -> int:
    t0 = time.perf_counter()
    H = Hold(TAG)
    fo = open(os.path.join(D, f"res3_{TAG}.jsonl"), "w")
    arrays = {}

    def add(fam, params, sel, keep=False):
        f = H.per_entity(sel)
        row = {"fam": fam, **params, **H.summary(f)}
        fo.write(json.dumps(row) + "\n")
        fo.flush()
        if keep:
            arrays[fam + "|" + ",".join(f"{k}={v}" for k, v in params.items())] = f.astype(np.float32)
        return row

    for c0 in (0.001, 0.01, 0.05):
        seg = segments(H, c0)
        for p_lo in (0.0, 0.02):
            q0 = crossfit_q(H, seg, p_lo)
            for sh in (-0.3, -0.15, 0.0, 0.15, 0.3):
                q = to_q(q0, sh)
                r = add("iso_dp", {"c0": c0, "p_lo": p_lo, "shift": sh}, expected_f_select(H.s1, q, H.own), keep=True)
                g = add("iso_greedy", {"c0": c0, "p_lo": p_lo, "shift": sh}, greedy_perfect(q, H.own, H.own_rank),
                        keep=True)
                print(f"c0={c0} p_lo={p_lo} sh={sh:+.2f}: dp A {r['A']:.6f} B {r['B']:.6f} full {r['full']:.6f} | "
                      f"greedy A {g['A']:.6f} B {g['B']:.6f} full {g['full']:.6f} ({time.perf_counter() - t0:.0f}s)",
                      flush=True)
    fo.close()
    np.savez_compressed(os.path.join(D, f"arr3_{TAG}.npz"), **arrays)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
