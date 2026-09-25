"""Safe readers and exact-format writers for the challenge TSVs (docs/CONTRACTS.md C6).

Reading:
- tab separator, **quote handling disabled** (business names contain ' and ");
- every column is read as a string; empty fields become "" (never NaN).

Writing: exactly the organizer format:
- the header line;
- one row per S1 in the given order;
- comma-joined ids with no spaces or quotes;
- empty lists allowed, duplicates removed, S2/S3 ids only.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.csv as pv

from . import ids as _ids
from .paths import data_dir

SOURCE_COLUMNS = ["entity_id", "business_name", "business_address", "country"]
TRUTH_COLUMNS = ["source1_entity_id", "matched_entity_ids"]
MATCHING_HEADER = ("source1_entity_id", "matched_entity_ids")
CANDIDATE_HEADER = ("source1_entity_id", "candidate_entity_ids")

_STRING_DTYPE = pd.StringDtype("pyarrow")


def read_tsv(path: str | Path) -> pd.DataFrame:
    """Read any challenge TSV with quoting disabled; all columns are pyarrow-backed strings."""
    path = Path(path)
    with open(path, encoding="utf-8") as fh:
        header = fh.readline().rstrip("\r\n").split("\t")
    table = pv.read_csv(
        path,
        read_options=pv.ReadOptions(block_size=1 << 26),
        parse_options=pv.ParseOptions(delimiter="\t", quote_char=False, escape_char=False, newlines_in_values=False),
        convert_options=pv.ConvertOptions(column_types={c: pa.string() for c in header}, strings_can_be_null=False),
    )
    return table.to_pandas(types_mapper={pa.string(): _STRING_DTYPE}.get)


def read_source(path: str | Path) -> pd.DataFrame:
    """Read a ``*_source{1,2,3}.tsv`` file and check its columns."""
    df = read_tsv(path)
    if list(df.columns) != SOURCE_COLUMNS:
        raise ValueError(f"{path}: unexpected columns {list(df.columns)}")
    return df


def load_split(split: str, root: str | Path | None = None) -> dict[str, pd.DataFrame]:
    """Load ``train`` or ``test``: keys ``s1, s2, s3`` (+ ``truth`` for train)."""
    if split not in ("train", "test"):
        raise ValueError("split must be 'train' or 'test'")
    folder = (Path(root) if root else data_dir()) / split
    out = {f"s{k}": read_source(folder / f"{split}_source{k}.tsv") for k in (1, 2, 3)}
    if split == "train":
        out["truth"] = read_tsv(folder / "train_ground_truth.tsv")
    return out


def truth_pairs(truth: pd.DataFrame) -> pd.DataFrame:
    """Ground-truth table -> unique int64 pairs ``(s1, r)``. Singletons produce no rows."""
    t = truth.loc[truth["matched_entity_ids"] != "", TRUTH_COLUMNS].astype(object)
    ex = t.assign(r=t["matched_entity_ids"].str.split(",")).explode("r")
    ex = ex[ex["r"].astype(str) != ""]
    return pd.DataFrame(
        {"s1": _ids.to_eids(ex["source1_entity_id"]), "r": _ids.to_eids(ex["r"])}
    ).drop_duplicates(ignore_index=True)


def read_id_lists(path: str | Path) -> tuple[list[str], pd.DataFrame]:
    """Read a matching/candidate output (or the ground truth) -> (S1 order, int64 pairs ``(s1, r)``)."""
    df = read_tsv(path)
    s1_col, list_col = df.columns[0], df.columns[1]
    renamed = df.rename(columns={s1_col: "source1_entity_id", list_col: "matched_entity_ids"})
    return df[s1_col].astype(str).tolist(), truth_pairs(renamed)


def _id_lists(s1_order: list[str], pairs: pd.DataFrame | None) -> list[str]:
    """One comma-joined, de-duplicated, sorted S2/S3 id list per S1 in ``s1_order``."""
    s1_eids = _ids.to_eids(s1_order)
    if pairs is None or len(pairs) == 0:
        return [""] * len(s1_order)
    p = pd.DataFrame(
        {"s1": np.asarray(pairs["s1"], dtype=np.int64), "r": np.asarray(pairs["r"], dtype=np.int64)}
    ).drop_duplicates()
    if not np.isin(_ids.source_of(p["r"].to_numpy()), (2, 3)).all():
        raise ValueError("column 'r' must contain only S2/S3 eids")
    unknown = ~p["s1"].isin(s1_eids)
    if unknown.any():
        raise ValueError(f"{int(unknown.sum())} pair(s) reference S1 ids not in s1_order")
    p = p.sort_values(["s1", "r"], kind="stable")
    p["rid"] = _ids.to_entity_ids(p["r"].to_numpy())
    joined = p.groupby("s1", sort=False)["rid"].agg(",".join)
    return joined.reindex(s1_eids, fill_value="").tolist()


def _write(path: str | Path, header: tuple[str, str], s1_order: Iterable[str], pairs: pd.DataFrame | None) -> Path:
    s1_list = [str(s) for s in s1_order]
    if len(set(s1_list)) != len(s1_list):
        raise ValueError("s1_order contains duplicate ids")
    lists = _id_lists(s1_list, pairs)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\t".join(header) + "\n")
        fh.writelines(f"{s}\t{lst}\n" for s, lst in zip(s1_list, lists))
    return path


def write_matching(path: str | Path, s1_order: Iterable[str], pairs: pd.DataFrame | None) -> Path:
    """Write ``matching_results.tsv``. ``s1_order``: test_source1 ids in file order; ``pairs``: int64 (s1, r)."""
    return _write(path, MATCHING_HEADER, s1_order, pairs)


def write_candidates(path: str | Path, s1_order: Iterable[str], pairs: pd.DataFrame | None) -> Path:
    """Write ``candidate_pairs.tsv`` (the exact set the matcher scored). Same arguments as ``write_matching``."""
    return _write(path, CANDIDATE_HEADER, s1_order, pairs)
