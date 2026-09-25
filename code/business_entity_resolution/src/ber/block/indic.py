"""Crude Indic -> Latin transliteration and consonant skeletons for blocking (plans/FINAL_PLAN.md section 4.2).

The nine Indic Unicode blocks (Devanagari, Bengali, Gurmukhi, Gujarati, Oriya, Tamil, Telugu, Kannada, Malayalam)
share the ISCII-derived layout, so one table of offsets covers all of them: consonants carry an inherent "a" that a
vowel sign or the virama replaces, and the word-final inherent vowel is dropped ("राम" -> "ram").
The skeleton (first letter + consonants, with a few phonetic merges) lets "मार्केटिंग" -> "maarketing" -> "mrktng" meet
"marketing" -> "mrktng". Hand-written; no external data (the normalize stage owns the full transliteration, G12).
"""
from __future__ import annotations

import re

import pyarrow as pa
import pyarrow.compute as pc

BLOCKS = (0x0900, 0x0980, 0x0A00, 0x0A80, 0x0B00, 0x0B80, 0x0C00, 0x0C80, 0x0D00)
_INHERENT, _KILL = "\u0001", "\u0002"  # placeholders: inherent vowel, and "remove the preceding inherent vowel"

_VOWELS = {0x05: "a", 0x06: "aa", 0x07: "i", 0x08: "ii", 0x09: "u", 0x0A: "uu", 0x0B: "ri", 0x0C: "li", 0x0D: "e",
           0x0E: "e", 0x0F: "e", 0x10: "ai", 0x11: "o", 0x12: "o", 0x13: "o", 0x14: "au"}
_CONSONANTS = ["k", "kh", "g", "gh", "ng", "ch", "chh", "j", "jh", "ny", "t", "th", "d", "dh", "n", "t", "th", "d", "dh",
               "n", "n", "p", "ph", "b", "bh", "m", "y", "r", "r", "l", "l", "zh", "v", "sh", "sh", "s", "h"]  # 0x15-0x39
_SIGNS = {0x3E: "aa", 0x3F: "i", 0x40: "ii", 0x41: "u", 0x42: "uu", 0x43: "ri", 0x44: "ri", 0x45: "e", 0x46: "e",
          0x47: "e", 0x48: "ai", 0x49: "o", 0x4A: "o", 0x4B: "o", 0x4C: "au", 0x62: "li", 0x63: "li"}


def _table() -> dict[int, str]:
    t: dict[int, str] = {}
    for base in BLOCKS:
        t[base + 0x01] = "n"
        t[base + 0x02] = "n"
        t[base + 0x03] = "h"
        for off, v in _VOWELS.items():
            t[base + off] = v
        for i, c in enumerate(_CONSONANTS):
            t[base + 0x15 + i] = c + _INHERENT
        for off, v in _SIGNS.items():
            t[base + off] = _KILL + v
        t[base + 0x4D] = _KILL  # virama
        t[base + 0x3C] = ""     # nukta
        for d in range(10):
            t[base + 0x66 + d] = str(d)
    t[0x0BCD] = _KILL  # Tamil pulli (virama)
    t[0x0D4D] = _KILL  # Malayalam virama
    t[0x200C] = ""     # zero-width non-joiner
    t[0x200D] = ""     # zero-width joiner
    return t


TABLE = _table()
_INDIC = re.compile("[ऀ-ൿ]")
# inherent+kill -> nothing; stray kill -> nothing; word-final inherent vowel -> nothing (schwa deletion); else "a"
_CLEAN = [(re.compile(_INHERENT + _KILL), ""), (re.compile(_KILL), ""),
          (re.compile(_INHERENT + "(?=[^a-z]|$)"), ""), (re.compile(_INHERENT), "a")]


def transliterate(s: str) -> str:
    """Indic letters -> Latin (other characters unchanged)."""
    if not _INDIC.search(s):
        return s
    out = s.translate(TABLE)
    for pattern, repl in _CLEAN:
        out = pattern.sub(repl, out)
    return out


def transliterate_array(arr: pa.Array) -> pa.Array:
    """Transliterate the strings that contain Indic letters; the others pass through untouched."""
    mask = pc.match_substring_regex(arr, r"[\x{0900}-\x{0d7f}]").to_numpy(zero_copy_only=False)
    if not mask.any():
        return arr
    values = arr.to_pylist()
    for i in mask.nonzero()[0]:
        values[i] = transliterate(values[i])
    return pa.array(values, type=arr.type)


def skeleton(tokens: pa.Array) -> pa.Array:
    """Consonant skeleton of lowercase ASCII tokens: phonetic merges, then the first letter + non-vowels, no runs.

    Computed on the unique values only, so it is cheap on tens of millions of tokens.
    """
    enc = pc.dictionary_encode(tokens)
    return pc.take(_skeleton_unique(enc.dictionary), enc.indices)


def _skeleton_unique(tokens: pa.Array) -> pa.Array:
    a = tokens
    for pat, rep in (("ph", "f"), ("bh", "b"), ("dh", "d"), ("th", "t"), ("kh", "k"), ("gh", "g"), ("sh", "s"),
                     ("ch", "c"), ("ck", "k"), ("q", "k"), ("c", "k"), ("w", "v"), ("z", "j"), ("x", "ks")):
        a = pc.replace_substring(a, pat, rep)
    first = pc.utf8_slice_codeunits(a, 0, 1)
    rest = pc.replace_substring_regex(pc.utf8_slice_codeunits(a, 1), "[aeiouyh]", "")
    a = pc.binary_join_element_wise(first, rest, pa.scalar("", a.type))
    for letter in "bdfgjklmnprstv":  # RE2 has no backreferences: collapse runs letter by letter
        a = pc.replace_substring_regex(a, letter + "{2,}", letter)
    return a
