"""Artifact I/O with provenance (docs/CONTRACTS.md C0, C7).

Every Parquet artifact and report records the git commit, the command, the creation time (IST) and the input tags,
so any number can be traced back to the code and data that produced it.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from . import __version__
from .paths import REPO_ROOT, artifact_path, report_path

IST = dt.timezone(dt.timedelta(hours=5, minutes=30), "IST")
_META_KEY = b"ber"


def git_commit() -> str:
    """Short commit of the repo, with ``+dirty`` if tracked files have uncommitted changes; ``unknown`` outside git."""
    def git(*args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True, timeout=15
        ).stdout.strip()

    try:
        sha = git("rev-parse", "--short", "HEAD")
        dirty = git("status", "--porcelain", "--untracked-files=no")
        return sha + ("+dirty" if dirty else "")
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def provenance(command: str | None = None, inputs: dict[str, str] | None = None, **extra: Any) -> dict:
    """The metadata stored with every artifact and report."""
    return {
        "git_commit": git_commit(),
        "command": command or " ".join(["python", *sys.argv]),
        "created_ist": dt.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
        "ber_version": __version__,
        "inputs": dict(inputs or {}),
        **extra,
    }


def write_parquet(df: pd.DataFrame, path: str | Path, meta: dict) -> Path:
    """Write ``df`` (index dropped) with ``meta`` in the schema metadata. Atomic: a crash never leaves half a file."""
    path = Path(path)
    table = pa.Table.from_pandas(df, preserve_index=False)
    table = table.replace_schema_metadata({**(table.schema.metadata or {}), _META_KEY: json.dumps(meta, default=str).encode()})
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    pq.write_table(table, tmp, compression="zstd")
    os.replace(tmp, path)
    return path


def read_meta(path: str | Path) -> dict:
    """Provenance metadata of a Parquet artifact (empty dict if it has none)."""
    raw = (pq.read_schema(path).metadata or {}).get(_META_KEY)
    return json.loads(raw) if raw else {}


def write_table(df: pd.DataFrame, kind: str, tag: str, split: str, *, command: str | None = None,
                inputs: dict[str, str] | None = None, **extra: Any) -> Path:
    """Write the artifact ``work/<kind>/<tag>/<split>.parquet`` with provenance."""
    meta = provenance(command, inputs, kind=kind, tag=tag, split=split, rows=len(df), **extra)
    return write_parquet(df, artifact_path(kind, tag, split), meta)


def read_table(kind: str, tag: str, split: str, columns: list[str] | None = None) -> pd.DataFrame:
    """Read ``work/<kind>/<tag>/<split>.parquet``; a missing file raises with a hint."""
    path = artifact_path(kind, tag, split)
    if not path.exists():
        raise FileNotFoundError(f"{path} not found: produce it first, or point at another tag with --in {kind}=<tag>")
    return pd.read_parquet(path, columns=columns)


def exists(kind: str, tag: str, split: str) -> bool:
    return artifact_path(kind, tag, split).exists()


def write_report(tag: str, payload: dict, *, command: str | None = None, inputs: dict[str, str] | None = None,
                 merge: bool = True) -> Path:
    """Write ``work/reports/<tag>.json`` (C7). With ``merge``, keys of an existing report are kept unless replaced."""
    path = report_path(tag)
    body: dict = {}
    if merge and path.exists():
        body = json.loads(path.read_text(encoding="utf-8"))
    merged_inputs = {**body.get("inputs", {}), **(inputs or {})}
    body.update({"tag": tag, **provenance(command, merged_inputs), **payload})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    return path
