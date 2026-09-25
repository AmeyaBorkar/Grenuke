"""Default locations with environment-variable overrides (no hard-coded personal paths)."""
from __future__ import annotations

import os
from pathlib import Path

# src/ber/paths.py -> parents: ber, src, business_entity_resolution, code, <repo root>
REPO_ROOT = Path(__file__).resolve().parents[4]


def data_dir() -> Path:
    """Folder containing ``train/`` and ``test/`` TSVs (env ``BER_DATA_DIR``)."""
    return Path(os.environ.get("BER_DATA_DIR", REPO_ROOT / "student_resource" / "dataset"))


def work_dir() -> Path:
    """Intermediate artifacts, git-ignored (env ``BER_WORK_DIR``)."""
    return Path(os.environ.get("BER_WORK_DIR", REPO_ROOT / "work"))


def output_dir() -> Path:
    """Final TSV outputs (env ``BER_OUTPUT_DIR``)."""
    return Path(os.environ.get("BER_OUTPUT_DIR", REPO_ROOT / "output"))
