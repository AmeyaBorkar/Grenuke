"""Integer entity keys (docs/CONTRACTS.md C1).

eid = source * 1_000_000_000 + number   e.g. "S2-681193310" -> 2_681_193_310

The mapping is lossless for this dataset: every id matches ``S[123]-[0-9]{1,9}`` with no
leading zeros (checked on all 23.7M records). The converters below reject anything else.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

SOURCE_BASE = 1_000_000_000
_ID_PATTERN = r"^S[123]-(?:0|[1-9][0-9]{0,8})$"


def to_eid(entity_id: str) -> int:
    """Convert one entity id string to its integer key."""
    if not isinstance(entity_id, str) or len(entity_id) < 4 or entity_id[0] != "S" or entity_id[2] != "-":
        raise ValueError(f"bad entity_id: {entity_id!r}")
    source, number = entity_id[1], entity_id[3:]
    if source not in "123" or not number.isdigit() or len(number) > 9 or (len(number) > 1 and number[0] == "0"):
        raise ValueError(f"bad entity_id: {entity_id!r}")
    return int(source) * SOURCE_BASE + int(number)


def to_eids(entity_ids) -> np.ndarray:
    """Vectorized ``to_eid`` for a Series/array/list of id strings -> int64 array."""
    s = pd.Series(entity_ids, copy=False).astype("string[pyarrow]")
    ok = s.str.match(_ID_PATTERN)
    if not bool(ok.all()):
        raise ValueError(f"bad entity_id(s), e.g. {s[~ok.fillna(False)].head(3).tolist()}")
    source = s.str.slice(1, 2).astype("int64")
    number = s.str.slice(3).astype("int64")
    return (source * SOURCE_BASE + number).to_numpy(dtype=np.int64)


def to_entity_id(eid: int) -> str:
    """Integer key -> original entity id string."""
    source, number = divmod(int(eid), SOURCE_BASE)
    if source not in (1, 2, 3):
        raise ValueError(f"bad eid: {eid}")
    return f"S{source}-{number}"


def to_entity_ids(eids) -> np.ndarray:
    """Vectorized ``to_entity_id`` -> object array of strings."""
    e = np.asarray(eids, dtype=np.int64)
    source = e // SOURCE_BASE
    if e.size and not np.isin(source, (1, 2, 3)).all():
        raise ValueError("bad eid(s): source digit must be 1, 2 or 3")
    number = e % SOURCE_BASE
    out = "S" + pd.Series(source).astype(str) + "-" + pd.Series(number).astype(str)
    return out.to_numpy(dtype=object)


def source_of(eids) -> np.ndarray:
    """Source digit (1, 2 or 3) of each eid."""
    return (np.asarray(eids, dtype=np.int64) // SOURCE_BASE).astype(np.int8)
