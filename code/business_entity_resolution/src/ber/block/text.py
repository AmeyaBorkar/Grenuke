"""Blocking tokenizer: crude, vectorized text keys for candidate retrieval (plans/FINAL_PLAN.md section 4.3).

Blocking does not wait for the normalize stage, so it has its own small normalizer:
- NFKD, combining marks removed, other non-ASCII characters (e.g. Indic scripts) become spaces, lowercase;
- name tokens without legal forms, honorifics and stop words (length >= 2);
- address words (letters only, length >= 2, markers removed, street types canonicalized) and numbers (every digit
  run, leading zeros stripped).
Everything runs on whole pyarrow columns; nothing loops over records in Python.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc

LEGAL = frozenset("""
    inc incorporated llc ltd limited pvt private corp corporation co company cos lp llp pllc pc plc gmbh
    sarl sas sasu eurl sa sci snc ei
""".split())
NAME_STOP = frozenset("""
    the and of a an de du des la le les et www com net org dba aka shri sri smt dr mr mrs ms
""".split())
ADDR_STOP = frozenset("""
    null none na no nos h hno house plot door flat unit apt apartment suite ste floor fl bldg building
    near nr opp opposite behind beside po box pmb nd th
""".split())
# One short form per street type (US, India, France); "saint" -> "st" on both sides (FINAL_PLAN section 4.2).
STREET = {
    "road": "rd", "street": "st", "str": "st", "saint": "st", "avenue": "ave", "av": "ave", "boulevard": "blvd",
    "bd": "blvd", "lane": "ln", "drive": "dr", "place": "pl", "court": "ct", "circle": "cir", "highway": "hwy",
    "parkway": "pkwy", "square": "sq", "terrace": "ter", "trail": "trl", "rue": "r", "chemin": "ch",
    "impasse": "imp", "allee": "all", "route": "rte", "faubourg": "fg",
}


def fold(arr: pa.Array) -> pa.Array:
    """NFKD, combining marks removed, remaining non-ASCII -> space, lowercase."""
    a = pc.utf8_normalize(arr, "NFKD")
    a = pc.replace_substring_regex(a, r"[\x{0300}-\x{036f}]", "")
    a = pc.replace_substring_regex(a, r"[^\x00-\x7f]", " ")
    return pc.ascii_lower(a)


@dataclass
class Tokens:
    """Flat tokens of one text field: ``values[i]`` belongs to row ``rows[i]``; rows ascend, original order kept."""

    values: pa.Array
    rows: np.ndarray


def _split(arr: pa.Array, pattern: str) -> Tokens:
    """Split every string on ``pattern`` and keep the non-empty pieces with their row index."""
    lists = pc.split_pattern_regex(arr, pattern)
    flat = pc.list_flatten(lists)
    rows = pc.list_parent_indices(lists).to_numpy(zero_copy_only=False).astype(np.int64)
    keep = pc.greater(pc.utf8_length(flat), 0)
    return Tokens(pc.filter(flat, keep), rows[keep.to_numpy(zero_copy_only=False)])


def _drop(tok: Tokens, stop: frozenset, min_len: int) -> Tokens:
    stop_values = pa.array(sorted(stop), type=tok.values.type)
    keep = pc.and_(pc.greater_equal(pc.utf8_length(tok.values), min_len),
                   pc.invert(pc.is_in(tok.values, value_set=stop_values)))
    return Tokens(pc.filter(tok.values, keep), tok.rows[keep.to_numpy(zero_copy_only=False)])


def _map_values(values: pa.Array, mapping: dict[str, str]) -> pa.Array:
    """Replace whole tokens through ``mapping``, applied to the dictionary of unique values (cheap)."""
    enc = pc.dictionary_encode(values)
    mapped = pa.array([mapping.get(v, v) for v in enc.dictionary.to_pylist()], type=values.type)
    return pc.take(mapped, enc.indices)


def name_tokens(names: pa.Array) -> Tokens:
    """Name tokens (letters and digits) without legal forms, honorifics and stop words."""
    return _drop(_split(fold(names), r"[^a-z0-9]+"), LEGAL | NAME_STOP, 2)


def _address_text(addresses: pa.Array) -> pa.Array:
    """Folded address without ordinal endings ('1st floor' -> '1 floor', '3rd' -> '3'): they are not street types."""
    return pc.replace_substring_regex(fold(addresses), r"([0-9])(st|nd|rd|th)\b", r"\1")


def address_words(addresses: pa.Array) -> Tokens:
    """Address words (letters only), markers removed, street types canonicalized."""
    tok = _drop(_split(_address_text(addresses), r"[^a-z]+"), ADDR_STOP, 2)
    return Tokens(_map_values(tok.values, STREET), tok.rows)


def address_numbers(addresses: pa.Array) -> Tokens:
    """Every digit run of the address, leading zeros stripped ('0054' -> '54', '8444b' -> '8444')."""
    tok = _split(_address_text(addresses), r"[^0-9]+")
    return Tokens(pc.replace_substring_regex(tok.values, r"^0+([0-9])", r"\1"), tok.rows)


def name_concat(tok: Tokens, n_rows: int) -> Tokens:
    """Name tokens joined without spaces ('abc exports' -> 'abcexports') for rows with two or more tokens.

    It shares the name namespace, so it matches a one-token domain or hashtag form ('abcexports.com').
    """
    counts = np.bincount(tok.rows, minlength=n_rows)
    offsets = np.concatenate([[0], np.cumsum(counts)]).astype(np.int32)
    joined = pc.binary_join(pa.ListArray.from_arrays(pa.array(offsets), tok.values), pa.scalar("", tok.values.type))
    rows = np.flatnonzero(counts >= 2)
    return Tokens(pc.take(joined, pa.array(rows)), rows.astype(np.int64))
