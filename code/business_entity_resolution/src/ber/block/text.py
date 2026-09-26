"""Blocking tokenizer: crude, vectorized text keys for candidate retrieval (plans/FINAL_PLAN.md section 4.3).

Blocking does not wait for the normalize stage, so it has its own small normalizer:
- NFKD, combining marks removed, other non-ASCII characters (e.g. Indic scripts) become spaces, lowercase;
- name tokens without legal forms, honorifics and stop words (length >= 2);
- address words (letters only, length >= 2, markers, articles and number suffixes removed, street types
  canonicalized, the one-letter "R" read as "rue") and numbers (every digit run, leading zeros stripped);
- ordinal street words written out become numbers ("Twentieth Ave" -> "20 ave", "twenty first" -> "21"), as
  "20th" already does: one vendor spells them out ("200 15th Street" -> "FIFTEENTH STREET");
- French departments written as a whole address component become their region ("…, Lille, Nord" and "…, Lille,
  Hauts-de-France" give the same words): S1 addresses name the region, a third of S2/S3 name the department.
Everything runs on whole pyarrow columns; nothing loops over records in Python (ordinal words: only the few
rows that hold one).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc

LEGAL = frozenset("""
    inc incorporated llc ltd limited pvt private corp corporation co company cos lp llp pllc pc plc gmbh
    sarl sas sasu eurl sa sci snc ei
""".split())
# Honorific prefixes: shri/sri/smt never occur in train S1 names but the generator adds them to about 1.6k copies each;
# sree/shree/om/maa occur in S1 names and are dropped from 32-45% of their true copies (train, 26 Sep).
NAME_STOP = frozenset("""
    the and of a an de du des la le les et www com net org dba aka shri sri smt dr mr mrs ms
    sree shree shre om maa
""".split())
ADDR_STOP = frozenset("""
    null none na no nos h hno house plot door flat unit apt apartment suite ste floor fl bldg building
    near nr opp opposite behind beside po box pmb nd th
    de du des la le les sur en au aux bis ter quater cedex
""".split())
# One short form per street type (US, India, France); "saint" -> "st" on both sides (FINAL_PLAN section 4.2).
STREET = {
    "road": "rd", "street": "st", "str": "st", "saint": "st", "avenue": "ave", "av": "ave", "boulevard": "blvd",
    "bd": "blvd", "lane": "ln", "drive": "dr", "place": "pl", "court": "ct", "circle": "cir", "highway": "hwy",
    "parkway": "pkwy", "square": "sq", "terrace": "ter", "trail": "trl", "rue": "rue", "chemin": "ch",
    "impasse": "imp", "allee": "all", "route": "rte", "faubourg": "fg",
}
SHORT_STREET = {"r": "rue"}  # one-letter abbreviations, mapped before the length filter
# French departments -> their region (hand-written, the regions of the test data; applied to whole address components)
DEPARTMENT_REGION = {
    "hauts de france": ("aisne", "nord", "oise", "pas de calais", "somme"),
    "nouvelle aquitaine": ("charente", "charente maritime", "correze", "creuse", "dordogne", "gironde", "landes",
                           "lot et garonne", "pyrenees atlantiques", "deux sevres", "vienne", "haute vienne"),
    "pays de la loire": ("loire atlantique", "maine et loire", "mayenne", "sarthe", "vendee"),
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


_ORDINAL_UNITS = ("first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth")
_ORDINAL_TEENS = ("tenth", "eleventh", "twelfth", "thirteenth", "fourteenth", "fifteenth", "sixteenth",
                  "seventeenth", "eighteenth", "nineteenth")
# Hand-written: the ordinals 1-39 written out ("first" .. "thirty ninth"), the forms street names use.
ORDINALS = {w: str(i + 1) for i, w in enumerate(_ORDINAL_UNITS)}
ORDINALS.update({w: str(i + 10) for i, w in enumerate(_ORDINAL_TEENS)})
ORDINALS.update({"twentieth": "20", "thirtieth": "30"})
_ORDINAL_RE = re.compile(r"\b(?:(twenty|thirty)[ -]?)?(" + "|".join(ORDINALS) + r")\b")
_ORDINAL_ANY = r"\b(?:" + "|".join(ORDINALS) + r")\b"


def _ordinal(m: re.Match) -> str:
    tens, word = m.group(1), m.group(2)
    if tens and word in _ORDINAL_UNITS:
        return str((2 if tens == "twenty" else 3) * 10 + int(ORDINALS[word]))
    return (tens + " " if tens else "") + ORDINALS[word]


def ordinals_to_digits(folded: pa.Array) -> pa.Array:
    """Ordinal words -> digits in folded (lowercase ASCII) text: "twentieth ave" -> "20 ave", "twenty-first st" ->
    "21 st". Only the rows that contain one are rewritten (a few percent), so it stays cheap on whole columns."""
    mask = pc.fill_null(pc.match_substring_regex(folded, _ORDINAL_ANY), False)
    idx = np.flatnonzero(mask.to_numpy(zero_copy_only=False))
    if idx.size == 0:
        return folded
    sub = pc.take(folded, pa.array(idx)).to_pylist()
    fixed = pa.array([_ORDINAL_RE.sub(_ordinal, v) for v in sub], type=folded.type)
    return pc.replace_with_mask(folded, mask, fixed)


def _address_text(addresses: pa.Array) -> pa.Array:
    """Folded address without ordinal endings ('1st floor' -> '1 floor', '3rd' -> '3'): they are not street types.
    Ordinal words become digits too ("Twentieth Ave" -> "20 ave"). French departments written as a whole
    comma-separated component become their region."""
    a = pc.replace_substring_regex(ordinals_to_digits(fold(addresses)), r"([0-9])(st|nd|rd|th)\b", r"\1")
    for region, departments in DEPARTMENT_REGION.items():
        alt = "|".join(d.replace(" ", "[ -]+") for d in departments)
        a = pc.replace_substring_regex(a, r"(^|,)\s*(?:" + alt + r")\s*(,|$)", r"\1 " + region + r" \2")
    return a


def address_words(addresses: pa.Array) -> Tokens:
    """Address words (letters only), markers removed, street types canonicalized ("R" -> "rue" first)."""
    tok = _split(_address_text(addresses), r"[^a-z]+")
    tok = _drop(Tokens(_map_values(tok.values, SHORT_STREET), tok.rows), ADDR_STOP, 2)
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
