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


def files(feats: str, split: str) -> tuple[pq.ParquetFile, pq.ParquetFile]:
    fs = pq.ParquetFile(artifact_path("features", f"{feats}-str", split))
    fc = pq.ParquetFile(artifact_path("features", f"{feats}-cx", split))
    if fs.metadata.num_rows != fc.metadata.num_rows or fs.num_row_groups != fc.num_row_groups:
        raise ValueError(f"{feats}: the str and cx files of {split} are not row-aligned")
    return fs, fc


def feature_names(feats: str, split: str = "train") -> list[str]:
    fs, fc = files(feats, split)
    return [c for c in fs.schema_arrow.names if c not in KEYS] + list(fc.schema_arrow.names)


def load_keys(feats: str, split: str) -> pd.DataFrame:
    fs, _ = files(feats, split)
    cols = [c for c in KEYS if c in fs.schema_arrow.names]
    return fs.read(columns=cols).to_pandas()


def load_matrix(feats: str, split: str, features: list[str], rows: np.ndarray | None = None) -> np.ndarray:
    """float32 matrix of ``features`` for the rows where ``rows`` (bool mask over the split) is True."""
    fs, fc = files(feats, split)
    in_s = set(fs.schema_arrow.names)
    cs = [f for f in features if f in in_s]
    cc = [f for f in features if f not in in_s]
    n_out = int(rows.sum()) if rows is not None else fs.metadata.num_rows
    X = np.empty((n_out, len(features)), np.float32)
    pos = {f: i for i, f in enumerate(features)}
    start = out = 0
    for g in range(fs.num_row_groups):
        n = fs.metadata.row_group(g).num_rows
        sel = rows[start:start + n] if rows is not None else None
        k = int(sel.sum()) if sel is not None else n
        if k:
            for f, tbl in ((cs, fs), (cc, fc)):
                if not f:
                    continue
                t = tbl.read_row_group(g, columns=f)
                for name in f:
                    col = t.column(name).to_numpy()
                    X[out:out + k, pos[name]] = col[sel] if sel is not None else col
        start += n
        out += k
    return X


def iter_matrix(feats: str, split: str, features: list[str], rows: np.ndarray | None = None):
    """Yield (start, sel, X) per row group: X holds the rows of that group where ``rows`` is True (all if None)."""
    fs, fc = files(feats, split)
    in_s = set(fs.schema_arrow.names)
    cs = [f for f in features if f in in_s]
    cc = [f for f in features if f not in in_s]
    pos = {f: i for i, f in enumerate(features)}
    start = 0
    for g in range(fs.num_row_groups):
        n = fs.metadata.row_group(g).num_rows
        sel = rows[start:start + n] if rows is not None else np.ones(n, bool)
        k = int(sel.sum())
        if k:
            X = np.empty((k, len(features)), np.float32)
            for f, tbl in ((cs, fs), (cc, fc)):
                if f:
                    t = tbl.read_row_group(g, columns=f)
                    for name in f:
                        X[:, pos[name]] = t.column(name).to_numpy()[sel]
            yield start, sel, X
        start += n


def argmax_owner(s1: np.ndarray, r: np.ndarray, p: np.ndarray) -> np.ndarray:
    """True where the pair's S1 has the highest p among all candidate S1 of that record (ties: lower s1)."""
    order = np.lexsort((s1, -p, r))
    rs = r[order]
    first = np.ones(rs.size, bool)
    first[1:] = rs[1:] != rs[:-1]
    out = np.zeros(p.size, bool)
    out[order[first]] = True
    return out


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
