"""Chunked C8 feature stage: string groups plus optional coordinator context.

IDF is unsupervised and fitted on a fixed-seed sample *per split and country*;
there is no country feature or fit on the match labels.  Candidate batches are
scored independently while the normalized record table is retained in memory.
"""
from __future__ import annotations

from collections import Counter
import importlib.util
import json
import os
import time

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq

from ..artifacts import provenance
from ..config import RunConfig
from ..eval.splits import fold_of, in_dev_sample
from ..paths import artifact_path, records_path
from ..records import load_truth
from .string import FEATURES, compute

NORM_COLUMNS = [
    "eid", "source", "country", "n_core", "n_concat", "n_legal", "f_domain",
    "f_hashtag", "f_indic", "a_norm", "a_street", "a_city", "a_state",
    "a_num1", "a_num1_sfx", "a_unit", "a_ntok", "f_addr_empty",
    "f_addr_short", "f_landmark", "f_pobox", "f_addr_null", "a_nums",
]


def _fit_idf(norm: pd.DataFrame, field: str, max_docs: int, seed: int) -> dict[str, dict[str, float]]:
    """Estimate document frequencies from records, not candidate repetitions."""
    country_values = norm["country"].astype(str).to_numpy()
    result: dict[str, dict[str, float]] = {}
    for country in pd.unique(country_values):
        positions = np.flatnonzero(country_values == country)
        rng = np.random.default_rng(seed)
        if len(positions) > max_docs:
            positions = rng.choice(positions, size=max_docs, replace=False)
        counts: Counter[str] = Counter()
        for value in norm[field].iloc[positions].fillna("").astype(str).to_numpy():
            counts.update(set(value.split()))
        total = len(positions)
        table = {word: float(np.log((total + 1) / (count + 1)) + 1)
                 for word, count in counts.items()}
        table["__default__"] = float(np.log(total + 1) + 1)
        result[str(country)] = table
    return result


def _candidate_mask(cands: pd.DataFrame, cfg: RunConfig) -> np.ndarray:
    mask = np.ones(len(cands), dtype=bool)
    if cfg.split == "train" and cfg.folds is not None:
        mask &= np.isin(fold_of(cands["s1"].to_numpy()), cfg.folds)
    if cfg.split == "train" and cfg.param("sample", "") == "dev":
        mask &= in_dev_sample(cands["s1"].to_numpy())
    return mask


def run(cfg: RunConfig) -> dict:
    started = time.perf_counter()
    norm_tag = cfg.input_tag("norm")
    candidate_tag = cfg.input_tag("candidates")
    norm_path = artifact_path("norm", norm_tag, cfg.split)
    candidates_path = artifact_path("candidates", candidate_tag, cfg.split)
    if not norm_path.exists() or not candidates_path.exists():
        raise FileNotFoundError(f"need {norm_path} and {candidates_path} before features")
    norm_table = pq.read_table(norm_path, columns=NORM_COLUMNS)
    number_list = norm_table["a_nums"].combine_chunks()
    number_csr = (number_list.offsets.to_numpy(zero_copy_only=False),
                  number_list.values.to_numpy(zero_copy_only=False))
    norm = norm_table.drop(["a_nums"]).to_pandas(types_mapper=pd.ArrowDtype)
    del norm_table, number_list
    if norm["eid"].duplicated().any():
        raise ValueError("normalized records contain duplicate eids")
    eid_index = pd.Index(norm["eid"].to_numpy(dtype=np.int64))
    max_docs = cfg.param("idf_docs", 200_000, int)
    if max_docs <= 0:
        raise ValueError("idf_docs must be positive")
    name_idf = _fit_idf(norm, "n_core", max_docs, cfg.seed)
    street_idf = _fit_idf(norm, "a_street", max_docs, cfg.seed)
    truth_index = None
    if cfg.split == "train":
        truth_index = pd.MultiIndex.from_frame(load_truth()[["s1", "r"]])
    input_file = pq.ParquetFile(candidates_path)
    batch_size = cfg.param("batch_size", 100_000, int)
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    # Context depends on *all* candidates for exact rivalry and group counts.
    # Compute it once when requested; per-batch context would silently change
    # those values at batch boundaries. The string-only mode remains streaming.
    context_features = None
    context_option = str(cfg.param("include_context", "auto")).lower()
    if context_option not in {"auto", "true", "1", "yes", "false", "0", "no"}:
        raise ValueError("include_context must be auto, true or false")
    context_available = importlib.util.find_spec("ber.features.context") is not None
    include_context = (context_available if context_option == "auto"
                       else context_option in {"true", "1", "yes"})
    if include_context:
        if not context_available:
            raise ImportError("ber.features.context is required for include_context")
        from . import context
        s1_records = ds.dataset(records_path(cfg.split), format="parquet").to_table(
            columns=["eid", "country", "name", "address"],
            filter=ds.field("source") == 1,
        ).to_pandas()
        all_candidates = pq.read_table(candidates_path).to_pandas()
        context_features = context.compute(all_candidates, s1_records)
        if len(context_features) != len(all_candidates):
            raise ValueError("context features are not row-aligned with candidates")
        del all_candidates, s1_records
    output = artifact_path("features", cfg.require_tag(), cfg.split)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    rows = 0
    candidate_offset = 0
    writer = None
    meta = provenance(cfg.command, {"norm": norm_tag, "candidates": candidate_tag},
                      kind="features", tag=cfg.require_tag(), split=cfg.split,
                      idf_docs=max_docs, rows="filtered" if cfg.folds or cfg.param("sample", "") else input_file.metadata.num_rows)
    try:
        for batch in input_file.iter_batches(batch_size=batch_size):
            candidates = batch.to_pandas()
            mask = _candidate_mask(candidates, cfg)
            batch_context = None
            if context_features is not None:
                batch_context = context_features.iloc[
                    candidate_offset:candidate_offset + len(candidates)
                ].loc[mask].reset_index(drop=True)
            candidate_offset += len(candidates)
            candidates = candidates.loc[mask].reset_index(drop=True)
            if candidates.empty:
                continue
            left_rows = eid_index.get_indexer(candidates["s1"].to_numpy(dtype=np.int64))
            right_rows = eid_index.get_indexer(candidates["r"].to_numpy(dtype=np.int64))
            if (left_rows < 0).any() or (right_rows < 0).any():
                raise ValueError("candidate references an eid absent from normalized records")
            left = norm.iloc[left_rows].reset_index(drop=True)
            right = norm.iloc[right_rows].reset_index(drop=True)
            countries = left["country"].astype(str).to_numpy()
            if not np.array_equal(countries, right["country"].astype(str).to_numpy()):
                raise ValueError("candidate pair crosses country partitions")
            features = compute(left, right, countries, name_idf, street_idf,
                               number_csr, left_rows, right_rows)
            base = candidates[["s1", "r"]].astype("int64")
            base["fold"] = (fold_of(base["s1"].to_numpy()) if cfg.split == "train"
                            else np.full(len(base), -1, dtype=np.int8))
            if truth_index is not None:
                base["y"] = pd.MultiIndex.from_frame(base[["s1", "r"]]).isin(truth_index).astype(np.int8)
            result = pd.concat([base, features], axis=1)
            if batch_context is not None:
                result = pd.concat([result, batch_context], axis=1)
            table = pa.Table.from_pandas(result, preserve_index=False)
            if writer is None:
                writer = pq.ParquetWriter(temporary,
                    table.schema.with_metadata({b"ber": json.dumps(meta, default=str).encode()}),
                    compression="zstd")
            writer.write_table(table)
            rows += len(result)
        if writer is None:
            empty = pd.DataFrame({"s1": pd.Series(dtype="int64"), "r": pd.Series(dtype="int64"),
                                  "fold": pd.Series(dtype="int8")})
            if cfg.split == "train":
                empty["y"] = pd.Series(dtype="int8")
            for name in FEATURES:
                empty[name] = pd.Series(dtype="float32")
            table = pa.Table.from_pandas(empty, preserve_index=False)
            writer = pq.ParquetWriter(temporary,
                table.schema.with_metadata({b"ber": json.dumps(meta, default=str).encode()}),
                compression="zstd")
            writer.write_table(table)
        writer.close()
        writer = None
        os.replace(temporary, output)
    finally:
        if writer is not None:
            writer.close()
        if temporary.exists():
            temporary.unlink()
    return {"pairs": rows, "features": len(FEATURES),
            "seconds": round(time.perf_counter() - started, 1), "path": str(output)}
