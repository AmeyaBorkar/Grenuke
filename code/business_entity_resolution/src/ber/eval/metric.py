"""Official metric (student_resource/README.md) and blocking diagnostics.

For each Source-1 entity with true set T, predicted set P, and c = |P ∩ T|:

    F0.5 = 1.25·Prec·Rec / (0.25·Prec + Rec) = 1.25·c / (0.25·|T| + |P|)
    if T is empty: 1.0 when P is empty, else 0.0   (singletons)

The leaderboard score is the **mean over all Source-1 entities**, singletons included.
Pair inputs are DataFrames with int64 columns ``s1`` and ``r`` (eids, see ``ber.ids``).
"""
from __future__ import annotations

from typing import Collection, Hashable, Iterable, Mapping

import numpy as np
import pandas as pd

BETA2 = 0.25


def entity_f05(pred: Collection, true: Collection) -> float:
    """F0.5 of one Source-1 entity (reference implementation)."""
    p, t = set(pred), set(true)
    if not t:
        return 1.0 if not p else 0.0
    if not p:
        return 0.0
    c = len(p & t)
    return (1.0 + BETA2) * c / (BETA2 * len(t) + len(p))


def macro_f05(
    pred: Mapping[Hashable, Collection],
    truth: Mapping[Hashable, Collection],
    s1_ids: Iterable[Hashable] | None = None,
) -> float:
    """Macro F0.5 over ``s1_ids`` (default: all keys of ``truth``). Missing keys count as empty sets."""
    ids = list(truth.keys()) if s1_ids is None else list(s1_ids)
    if not ids:
        return float("nan")
    return float(sum(entity_f05(pred.get(s, ()), truth.get(s, ())) for s in ids) / len(ids))


def _pairs(pairs: pd.DataFrame | None) -> pd.DataFrame:
    if pairs is None or len(pairs) == 0:
        return pd.DataFrame({"s1": np.empty(0, np.int64), "r": np.empty(0, np.int64)})
    return pd.DataFrame(
        {"s1": np.asarray(pairs["s1"], dtype=np.int64), "r": np.asarray(pairs["r"], dtype=np.int64)}
    ).drop_duplicates()


def per_entity_f05(pred_pairs: pd.DataFrame | None, true_pairs: pd.DataFrame | None, s1_universe) -> pd.DataFrame:
    """Vectorized per-entity table indexed by S1 eid: ``n_true, n_pred, n_hit, f05``.

    ``s1_universe`` is the set of evaluated S1 eids. Every entity counts, including those with no pairs.
    Pairs whose ``s1`` is outside the universe are ignored.
    """
    idx = pd.Index(np.unique(np.asarray(s1_universe, dtype=np.int64)), name="s1")
    pred, true = _pairs(pred_pairs), _pairs(true_pairs)
    pred = pred[pred["s1"].isin(idx)]
    true = true[true["s1"].isin(idx)]
    n_pred = pred.groupby("s1").size().reindex(idx, fill_value=0).to_numpy(np.float64)
    n_true = true.groupby("s1").size().reindex(idx, fill_value=0).to_numpy(np.float64)
    n_hit = pred.merge(true, on=["s1", "r"]).groupby("s1").size().reindex(idx, fill_value=0).to_numpy(np.float64)
    denom = BETA2 * n_true + n_pred  # == 0 only when both sets are empty -> score 1.0
    f05 = np.where(denom > 0, (1.0 + BETA2) * n_hit / np.where(denom > 0, denom, 1.0), 1.0)
    return pd.DataFrame(
        {"n_true": n_true.astype(np.int32), "n_pred": n_pred.astype(np.int32), "n_hit": n_hit.astype(np.int32), "f05": f05},
        index=idx,
    )


def macro_f05_pairs(pred_pairs: pd.DataFrame | None, true_pairs: pd.DataFrame | None, s1_universe) -> float:
    """Macro F0.5 from pair tables (fast path for millions of entities)."""
    return float(per_entity_f05(pred_pairs, true_pairs, s1_universe)["f05"].mean())


def pair_recall(cand_pairs: pd.DataFrame | None, true_pairs: pd.DataFrame | None, s1_universe=None) -> float:
    """Share of true (s1, r) pairs present in the candidates, i.e. the pair-level recall ceiling of blocking."""
    cand, true = _pairs(cand_pairs), _pairs(true_pairs)
    if s1_universe is not None:
        u = np.asarray(s1_universe, dtype=np.int64)
        cand, true = cand[cand["s1"].isin(u)], true[true["s1"].isin(u)]
    if len(true) == 0:
        return float("nan")
    return float(len(true.merge(cand, on=["s1", "r"])) / len(true))


def oracle_f05(cand_pairs: pd.DataFrame | None, true_pairs: pd.DataFrame | None, s1_universe) -> float:
    """Best macro F0.5 reachable with these candidates: a perfect matcher predicts exactly T ∩ C."""
    reachable = _pairs(cand_pairs).merge(_pairs(true_pairs), on=["s1", "r"])
    return macro_f05_pairs(reachable, true_pairs, s1_universe)


def report(
    pred_pairs: pd.DataFrame | None,
    true_pairs: pd.DataFrame | None,
    s1_universe,
    groups: pd.Series | Mapping | None = None,
) -> dict:
    """Headline numbers for docs/CONTRACTS.md C7.

    ``groups`` maps S1 eid to a label (e.g. country) and adds a ``by_group`` breakdown.
    """
    t = per_entity_f05(pred_pairs, true_pairs, s1_universe)
    single = t["n_true"] == 0
    hits, n_pred, n_true = int(t["n_hit"].sum()), int(t["n_pred"].sum()), int(t["n_true"].sum())
    out = {
        "macro_f05": float(t["f05"].mean()),
        "n_entities": int(len(t)),
        "singleton_share": float(single.mean()),
        "singleton_f05": float(t.loc[single, "f05"].mean()) if single.any() else None,
        "non_singleton_f05": float(t.loc[~single, "f05"].mean()) if (~single).any() else None,
        "micro_precision": hits / n_pred if n_pred else None,
        "micro_recall": hits / n_true if n_true else None,
        "mean_pred_per_s1": n_pred / len(t) if len(t) else None,
    }
    if groups is not None:
        g = pd.Series(groups).reindex(t.index)
        out["by_group"] = {str(k): float(v) for k, v in t["f05"].groupby(g).mean().items()}
    return out
