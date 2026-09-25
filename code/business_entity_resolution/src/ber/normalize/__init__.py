"""Streaming v0 normalizer (docs/CONTRACTS.md C3).

The input is read in batches and the final Parquet is written incrementally, so
the stage does not materialize all 12M records of a split on a 16 GB laptop.
``--n-jobs`` controls the process count (default: at most eight).
"""
from __future__ import annotations

from collections import deque
from concurrent.futures import ProcessPoolExecutor
import json
import os
import time

import pyarrow as pa
import pyarrow.parquet as pq

from ..artifacts import provenance
from ..config import RunConfig
from ..paths import artifact_path, records_path
from .address import parse_address
from .name import parse_name

SCHEMA = pa.schema([
    ("eid", pa.int64()), ("source", pa.int8()), ("country", pa.string()),
    ("n_full", pa.string()), ("n_core", pa.string()),
    ("n_concat", pa.string()), ("n_legal", pa.string()),
    ("f_domain", pa.bool_()), ("f_hashtag", pa.bool_()),
    ("f_phone", pa.bool_()), ("f_dba", pa.bool_()),
    ("f_indic", pa.bool_()), ("f_honorific", pa.bool_()),
    ("a_norm", pa.string()), ("a_street", pa.string()),
    ("a_city", pa.string()), ("a_state", pa.string()),
    ("a_num1", pa.int64()), ("a_num1_sfx", pa.string()),
    ("a_nums", pa.list_(pa.int64())), ("a_unit", pa.int64()),
    ("a_ntok", pa.int16()), ("f_addr_empty", pa.bool_()),
    ("f_addr_short", pa.bool_()), ("f_landmark", pa.bool_()),
    ("f_pobox", pa.bool_()), ("f_fragment", pa.bool_()),
    ("f_addr_null", pa.bool_()), ("f_arrondissement", pa.bool_()),
])
NAME_COLUMNS = ("n_full", "n_core", "n_concat", "n_legal", "f_domain",
                "f_hashtag", "f_phone", "f_dba", "f_indic", "f_honorific")
ADDRESS_COLUMNS = ("a_norm", "a_street", "a_city", "a_state", "a_num1",
                   "a_num1_sfx", "a_nums", "a_unit", "a_ntok", "f_addr_empty",
                   "f_addr_short", "f_landmark", "f_pobox", "f_fragment",
                   "f_addr_null", "f_arrondissement")


def normalize_batch(batch: pa.RecordBatch) -> pa.Table:
    """Top-level worker: one output row per input row, retaining input order."""
    source = {name: batch.column(batch.schema.get_field_index(name)).to_pylist()
              for name in ("eid", "source", "country", "name", "address")}
    result: dict[str, list] = {field.name: [] for field in SCHEMA}
    for eid, src, country, name, address in zip(*(source[key] for key in source)):
        result["eid"].append(eid)
        result["source"].append(src)
        result["country"].append(country or "")
        for key, value in zip(NAME_COLUMNS, parse_name(name)):
            result[key].append(value)
        for key, value in zip(ADDRESS_COLUMNS, parse_address(address)):
            result[key].append(value)
    return pa.Table.from_pydict(result, schema=SCHEMA)


def run(cfg: RunConfig) -> dict:
    source = records_path(cfg.split)
    if not source.exists():
        raise FileNotFoundError(f"{source} not found: run the records stage first")
    input_file = pq.ParquetFile(source)
    total = input_file.metadata.num_rows
    jobs = max(1, min(8, os.cpu_count() or 1)) if cfg.n_jobs < 0 else max(1, cfg.n_jobs)
    if total < 50_000:
        jobs = 1
    batch_size = cfg.param("batch_size", 100_000, int)
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    output = artifact_path("norm", cfg.require_tag(), cfg.split)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    meta = provenance(cfg.command, {"records": cfg.split}, kind="norm",
                      tag=cfg.require_tag(), split=cfg.split, rows=total)
    schema = SCHEMA.with_metadata({b"ber": json.dumps(meta, default=str).encode()})
    started = time.perf_counter()
    rows = 0
    try:
        with pq.ParquetWriter(temporary, schema, compression="zstd") as writer:
            batches = iter(input_file.iter_batches(
                batch_size=batch_size,
                columns=["eid", "source", "country", "name", "address"],
            ))
            if jobs == 1:
                for batch in batches:
                    table = normalize_batch(batch)
                    writer.write_table(table)
                    rows += table.num_rows
            else:
                with ProcessPoolExecutor(max_workers=jobs) as pool:
                    pending = deque()
                    for _ in range(jobs * 2):
                        batch = next(batches, None)
                        if batch is None:
                            break
                        pending.append(pool.submit(normalize_batch, batch))
                    while pending:
                        table = pending.popleft().result()
                        writer.write_table(table)
                        rows += table.num_rows
                        batch = next(batches, None)
                        if batch is not None:
                            pending.append(pool.submit(normalize_batch, batch))
        if rows != total:
            raise RuntimeError(f"normalized {rows} records, expected {total}")
        os.replace(temporary, output)
    finally:
        if temporary.exists():
            temporary.unlink()
    return {"records": rows, "workers": jobs,
            "seconds": round(time.perf_counter() - started, 1), "path": str(output)}
