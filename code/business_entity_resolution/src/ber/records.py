"""Stage ``records``: cache the raw TSVs as Parquet with integer ids (docs/CONTRACTS.md C3).

- ``work/records/<split>.parquet``: ``eid, source, country, name, address``, one row per S1/S2/S3 record,
  S1 first, each source in file order (so the test S1 rows are in ``test_source1.tsv`` order);
- ``work/records/truth.parquet`` (train only): unique true pairs ``s1, r``.

Every later stage reads these instead of the TSVs (about 1 minute to build, seconds to load).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import ids, io
from .artifacts import provenance, write_parquet
from .config import RunConfig
from .paths import data_dir, records_path, truth_path


def build_records(split: str, root: str | Path | None = None) -> pd.DataFrame:
    """Read ``<split>_source{1,2,3}.tsv`` into one table with int64 eids."""
    folder = (Path(root) if root else data_dir()) / split
    parts = []
    for k in (1, 2, 3):
        df = io.read_source(folder / f"{split}_source{k}.tsv")
        eid = ids.to_eids(df["entity_id"])
        source = ids.source_of(eid)
        if not (source == k).all():
            raise ValueError(f"{split}_source{k}.tsv contains ids of another source")
        # keep the pyarrow-backed strings from ber.io (no Python string objects for ~10M rows)
        part = df.rename(columns={"business_name": "name", "business_address": "address"})
        part = part[["country", "name", "address"]].reset_index(drop=True)
        part.insert(0, "source", source.astype(np.int8))
        part.insert(0, "eid", eid)
        parts.append(part)
    out = pd.concat(parts, ignore_index=True)
    if out["eid"].duplicated().any():
        raise ValueError(f"duplicate entity ids in {split}")
    return out


def build_truth(root: str | Path | None = None) -> pd.DataFrame:
    """Unique int64 true pairs ``s1, r`` from ``train_ground_truth.tsv``."""
    folder = (Path(root) if root else data_dir()) / "train"
    return io.truth_pairs(io.read_tsv(folder / "train_ground_truth.tsv"))


def load_records(split: str, columns: list[str] | None = None) -> pd.DataFrame:
    """Cached records of a split (run ``--stage records`` first)."""
    path = records_path(split)
    if not path.exists():
        raise FileNotFoundError(f"{path} not found: run `python -m ber.pipeline --stage records --split {split}`")
    return pd.read_parquet(path, columns=columns)


def load_truth() -> pd.DataFrame:
    """Cached true pairs of the train split."""
    path = truth_path()
    if not path.exists():
        raise FileNotFoundError(f"{path} not found: run `python -m ber.pipeline --stage records --split train`")
    return pd.read_parquet(path)


def s1_order(split: str = "test") -> list[str]:
    """S1 entity ids in source-file order (the row order the output TSVs must follow)."""
    rec = load_records(split, columns=["eid", "source"])
    return ids.to_entity_ids(rec.loc[rec["source"] == 1, "eid"].to_numpy()).tolist()


def run(cfg: RunConfig) -> dict:
    rec = build_records(cfg.split)
    write_parquet(rec, records_path(cfg.split), provenance(cfg.command, kind="records", split=cfg.split, rows=len(rec)))
    summary = {
        "records": len(rec),
        "by_source": {int(k): int(v) for k, v in rec["source"].value_counts().sort_index().items()},
        "s1_by_country": {str(k): int(v) for k, v in rec.loc[rec["source"] == 1, "country"].value_counts().items()},
    }
    if cfg.split == "train":
        truth = build_truth()
        write_parquet(truth, truth_path(), provenance(cfg.command, kind="truth", split="train", rows=len(truth)))
        summary["true_pairs"] = len(truth)
    return summary
