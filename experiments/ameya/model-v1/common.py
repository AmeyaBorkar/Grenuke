"""Shared helpers for the model-v1 experiments: feature loading, ownership, holdout evaluation."""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from ber.eval.metric import per_entity_f05, report
from ber.eval.splits import is_holdout, splitmix64
from ber.paths import artifact_path, records_path

log = logging.getLogger("model-v1")
KEYS = ("s1", "r", "fold", "y")


GROUPS = ["str", "cx"]  # feature files <feats>-<group>; s1.py --groups adds more (e.g. lo)


def files(feats: str, split: str) -> list[pq.ParquetFile]:
    out = [pq.ParquetFile(artifact_path("features", f"{feats}-{g}", split)) for g in GROUPS]
    for f, g in zip(out[1:], GROUPS[1:]):
        if f.metadata.num_rows != out[0].metadata.num_rows or f.num_row_groups != out[0].num_row_groups:
            raise ValueError(f"{feats}: the {g} and str files of {split} are not row-aligned")
    return out


def feature_names(feats: str, split: str = "train") -> list[str]:
    return [c for f in files(feats, split) for c in f.schema_arrow.names if c not in KEYS]


def load_keys(feats: str, split: str) -> pd.DataFrame:
    fs = files(feats, split)[0]
    cols = [c for c in KEYS if c in fs.schema_arrow.names]
    return fs.read(columns=cols).to_pandas()


def iter_matrix(feats: str, split: str, features: list[str], rows: np.ndarray | None = None):
    """Yield (start, sel, X) per row group: X holds the rows of that group where ``rows`` is True (all if None)."""
    fl = files(feats, split)
    owner = {}
    for f in fl:
        for c in f.schema_arrow.names:
            owner.setdefault(c, f)
    pos = {f: i for i, f in enumerate(features)}
    start = 0
    for g in range(fl[0].num_row_groups):
        n = fl[0].metadata.row_group(g).num_rows
        sel = rows[start:start + n] if rows is not None else np.ones(n, bool)
        k = int(sel.sum())
        if k:
            X = np.empty((k, len(features)), np.float32)
            for f in fl:
                cols = [c for c in features if owner[c] is f]
                if cols:
                    t = f.read_row_group(g, columns=cols)
                    for name in cols:
                        X[:, pos[name]] = t.column(name).to_numpy()[sel]
            yield start, sel, X
        start += n


def load_matrix(feats: str, split: str, features: list[str], rows: np.ndarray | None = None) -> np.ndarray:
    """float32 matrix of ``features`` for the rows where ``rows`` (bool mask over the split) is True."""
    n_out = int(rows.sum()) if rows is not None else files(feats, split)[0].metadata.num_rows
    X = np.empty((n_out, len(features)), np.float32)
    out = 0
    for _, _, Xg in iter_matrix(feats, split, features, rows):
        X[out:out + len(Xg)] = Xg
        out += len(Xg)
    return X


def argmax_owner(s1: np.ndarray, r: np.ndarray, p: np.ndarray) -> np.ndarray:
    """True where the pair's S1 has the highest p among all candidate S1 of that record (ties: lower s1)."""
    order = np.lexsort((s1, -p, r))
    rs = r[order]
    first = np.ones(rs.size, bool)
    first[1:] = rs[1:] != rs[:-1]
    out = np.zeros(p.size, bool)
    out[order[first]] = True
    return out


def candidate_mask(s1: np.ndarray, r: np.ndarray, p1: np.ndarray, p_min: float, top_r: int = 0) -> np.ndarray:
    """The final candidate set (the matching model's input): p1 >= p_min and, if top_r > 0, the pair is one of its
    record's top_r S1 by p1 (ties: lower s1 first). Ownership is an argmax over a record's S1, so the record's
    lower-ranked S1 are almost never predicted (cand_size.py)."""
    keep = p1 >= p_min
    if top_r > 0:
        idx = np.flatnonzero(keep)
        order = idx[np.lexsort((s1[idx], -p1[idx], r[idx]))]
        rs = r[order]
        start = np.ones(rs.size, bool)
        start[1:] = rs[1:] != rs[:-1]
        first = np.maximum.accumulate(np.where(start, np.arange(rs.size), 0))
        keep = np.zeros(p1.size, bool)
        keep[order[np.arange(rs.size) - first < top_r]] = True
    return keep


def s1_hash_slice(s1: np.ndarray, salt: int, mod: int) -> np.ndarray:
    """Deterministic S1 slice independent of the folds: hash(s1 ^ salt) % mod == 0."""
    return (splitmix64(np.asarray(s1, np.int64) ^ np.int64(salt)) % np.uint64(mod)) == 0


def holdout_universe(split: str = "train") -> tuple[np.ndarray, pd.Series]:
    t = pq.read_table(records_path(split), columns=["eid", "source", "country"]).to_pandas()
    s1 = t.loc[t["source"] == 1]
    country = pd.Series(s1["country"].to_numpy(), index=s1["eid"].to_numpy())
    eids = s1["eid"].to_numpy()
    return eids[is_holdout(eids)], country


def sweep(pairs: pd.DataFrame, p: np.ndarray, own: np.ndarray, truth: pd.DataFrame, universe: np.ndarray,
          grid=None) -> tuple[float, float, list]:
    """Best global threshold on the holdout (argmax ownership)."""
    grid = np.round(np.arange(0.30, 0.951, 0.025), 3) if grid is None else grid
    hold = np.isin(pairs["s1"].to_numpy(), universe)
    th = truth[truth["s1"].isin(universe)]
    res = []
    for t in grid:
        m = pairs.loc[hold & own & (p > t), ["s1", "r"]]
        res.append((float(t), float(per_entity_f05(m, th, universe)["f05"].mean())))
    best = max(res, key=lambda x: x[1])
    return best[0], best[1], res


def holdout_report(pred: pd.DataFrame, truth: pd.DataFrame, universe: np.ndarray, country: pd.Series) -> dict:
    rep = report(pred[pred["s1"].isin(universe)], truth[truth["s1"].isin(universe)], universe, groups=country)
    rep["by_country"] = rep.pop("by_group")
    return rep


class FastEval:
    """Macro F0.5 on a fixed S1 universe for many candidate selections (same numbers as ber.eval.metric).

    Build once from the scored pairs; ``score(mask)`` takes a bool mask over those pairs (the predicted ones).
    """

    def __init__(self, s1: np.ndarray, r: np.ndarray, truth: pd.DataFrame, universe: np.ndarray):
        self.universe = np.unique(np.asarray(universe, np.int64))
        th = truth[truth["s1"].isin(self.universe)]
        self.n_true = np.bincount(np.searchsorted(self.universe, th["s1"].to_numpy()),
                                  minlength=self.universe.size).astype(np.float64)
        self.in_u = np.isin(s1, self.universe)
        self.idx = np.searchsorted(self.universe, s1[self.in_u])
        key = s1[self.in_u] * 4_000_000_000 + r[self.in_u]
        self.hit = np.isin(key, th["s1"].to_numpy() * 4_000_000_000 + th["r"].to_numpy()).astype(np.float64)

    def per_entity(self, mask: np.ndarray) -> np.ndarray:
        m = mask[self.in_u]
        n_pred = np.bincount(self.idx[m], minlength=self.universe.size)
        n_hit = np.bincount(self.idx[m], weights=self.hit[m], minlength=self.universe.size)
        denom = 0.25 * self.n_true + n_pred
        return np.where(denom > 0, 1.25 * n_hit / np.where(denom > 0, denom, 1.0), 1.0)

    def score(self, mask: np.ndarray) -> float:
        return float(self.per_entity(mask).mean())

    def sweep(self, p: np.ndarray, own: np.ndarray, grid=None) -> tuple[float, float, list]:
        grid = np.round(np.arange(0.30, 0.951, 0.025), 3) if grid is None else grid
        res = [(float(t), self.score(own & (p > t))) for t in grid]
        best = max(res, key=lambda x: x[1])
        return best[0], best[1], res
