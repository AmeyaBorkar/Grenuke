"""Default locations with environment-variable overrides (no hard-coded personal paths).

Artifact layout (docs/CONTRACTS.md C0): ``work/<kind>/<tag>/<split>.parquet``.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

# src/ber/paths.py -> parents: ber, src, business_entity_resolution, code, <repo root>
REPO_ROOT = Path(__file__).resolve().parents[4]

_NAME = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def data_dir() -> Path:
    """Folder containing ``train/`` and ``test/`` TSVs (env ``BER_DATA_DIR``)."""
    return Path(os.environ.get("BER_DATA_DIR", REPO_ROOT / "student_resource" / "dataset"))


def work_dir() -> Path:
    """Intermediate artifacts, git-ignored (env ``BER_WORK_DIR``)."""
    return Path(os.environ.get("BER_WORK_DIR", REPO_ROOT / "work"))


def output_dir() -> Path:
    """Final TSV outputs (env ``BER_OUTPUT_DIR``)."""
    return Path(os.environ.get("BER_OUTPUT_DIR", REPO_ROOT / "output"))


def check_name(value: str, what: str = "tag") -> str:
    """Tags, kinds and splits are lowercase ``[a-z0-9._-]`` so they are safe as path parts."""
    if not isinstance(value, str) or not _NAME.match(value):
        raise ValueError(f"bad {what} {value!r}: use lowercase letters, digits, '.', '_' or '-'")
    return value


def artifact_dir(kind: str, tag: str) -> Path:
    """``work/<kind>/<tag>/``, e.g. ``work/candidates/ameya-block-v0/``."""
    return work_dir() / check_name(kind, "artifact kind") / check_name(tag)


def artifact_path(kind: str, tag: str, split: str, ext: str = "parquet") -> Path:
    """``work/<kind>/<tag>/<split>.<ext>``."""
    return artifact_dir(kind, tag) / f"{check_name(split, 'split')}.{ext}"


def records_path(split: str) -> Path:
    """Raw records cache (stage ``records``): ``work/records/<split>.parquet``."""
    return work_dir() / "records" / f"{check_name(split, 'split')}.parquet"


def truth_path() -> Path:
    """Unique true pairs of the train split: ``work/records/truth.parquet``."""
    return work_dir() / "records" / "truth.parquet"


def report_path(tag: str) -> Path:
    """Result report (C7): ``work/reports/<tag>.json``."""
    return work_dir() / "reports" / f"{check_name(tag)}.json"
