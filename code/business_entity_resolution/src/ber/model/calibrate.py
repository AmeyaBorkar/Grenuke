"""Isotonic calibration, cross-fitted on OOF scores (never on the holdout)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression


def _fit(p, y):
    iso = IsotonicRegression(y_min=1e-4, y_max=1 - 1e-4, out_of_bounds="clip")
    iso.fit(p, y)
    return iso


def crossfit_oof(oof_df, labels):
    p = oof_df["p1"].to_numpy()
    g = oof_df["oof_group"].to_numpy()
    out = np.empty_like(p)
    for grp in np.unique(g):
        m = g == grp
        out[m] = _fit(p[~m], labels[~m]).predict(p[m])
    return out


def fit_full(oof_df, labels):
    return _fit(oof_df["p1"].to_numpy(), labels)


def reliability_table(p, y, bins=15):
    edges = np.linspace(0, 1, bins + 1)
    idx = np.clip(np.digitize(p, edges) - 1, 0, bins - 1)
    df = pd.DataFrame({"bin": idx, "p": p, "y": y})
    t = df.groupby("bin").agg(n=("y", "size"), mean_p=("p", "mean"), rate=("y", "mean"))
    t.attrs["ece"] = float((t["n"] * (t["mean_p"] - t["rate"]).abs()).sum() / len(p))
    return t
