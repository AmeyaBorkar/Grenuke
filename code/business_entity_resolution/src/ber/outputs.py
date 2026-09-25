"""Stage ``write``: the two submission TSVs from C4 candidates and C9 matches (docs/CONTRACTS.md C6).

Checks what the official validator checks before writing: one row per test S1 in file order, S2/S3 ids only,
matches a subset of candidates. Then run the validator itself (the command is printed).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import ids, io
from .artifacts import read_table
from .config import RunConfig
from .paths import output_dir
from .records import s1_order

VALIDATOR = ("python student_resource/utils/validate_submission.py --matching {m} --candidate {c} "
             "--test-dir student_resource/dataset/test")


def check_subset(matches: pd.DataFrame, candidates: pd.DataFrame) -> None:
    """Raise if any matched pair is not a candidate (the validator flags this as a pipeline bug)."""
    m = matches[["s1", "r"]].drop_duplicates()
    missing = m.merge(candidates[["s1", "r"]].drop_duplicates(), on=["s1", "r"], how="left", indicator=True)
    n_bad = int((missing["_merge"] == "left_only").sum())
    if n_bad:
        raise ValueError(f"{n_bad} matched pair(s) are not in the candidate set (C9 must be a subset of C4)")


def run(cfg: RunConfig) -> dict:
    if cfg.split != "test":
        raise ValueError("write produces the submission files: use --split test")
    order = s1_order("test")
    candidates = read_table("candidates", cfg.input_tag("candidates"), "test", ["s1", "r"])
    matches = read_table("matches", cfg.input_tag("matches"), "test", ["s1", "r"])
    check_subset(matches, candidates)
    for name, t in (("candidates", candidates), ("matches", matches)):
        if len(t) and not np.isin(ids.source_of(t["r"].to_numpy()), (2, 3)).all():
            raise ValueError(f"{name}: column r must hold S2/S3 eids only")
    out = output_dir()
    c_path = io.write_candidates(out / "candidate_pairs.tsv", order, candidates)
    m_path = io.write_matching(out / "matching_results.tsv", order, matches)
    n_s1 = len(order)
    return {
        "s1_rows": n_s1,
        "candidate_pairs": int(len(candidates)),
        "matched_pairs": int(len(matches)),
        "mean_pred_per_s1": float(len(matches) / n_s1) if n_s1 else 0.0,
        "files": [str(m_path), str(c_path)],
        "next": VALIDATOR.format(m=m_path.as_posix(), c=c_path.as_posix()),
    }
