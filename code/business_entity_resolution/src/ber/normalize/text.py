"""Unicode cleaning and a compact, dependency-free Indic transliteration.

The transliteration is intentionally phonetic and lossy: its purpose is to give
fuzzy retrieval a Latin-script spelling, not to reproduce a person's preferred
romanization.  Unsupported signs are dropped while ``f_indic`` preserves that
the source contained Indic script.
"""
from __future__ import annotations

import re
import unicodedata

INDIC_BLOCKS = frozenset((0x0900, 0x0980, 0x0A00, 0x0A80, 0x0B00, 0x0B80, 0x0C00, 0x0C80, 0x0D00))

# The eight non-Tamil Brahmic blocks share most Devanagari character offsets.
VOWELS = {
    0x05: "a", 0x06: "aa", 0x07: "i", 0x08: "ee", 0x09: "u", 0x0A: "oo",
    0x0B: "ri", 0x0F: "e", 0x10: "ai", 0x13: "o", 0x14: "au",
}
CONSONANTS = {
    0x15: "k", 0x16: "kh", 0x17: "g", 0x18: "gh", 0x19: "ng",
    0x1A: "ch", 0x1B: "chh", 0x1C: "j", 0x1D: "jh", 0x1E: "ny",
    0x1F: "t", 0x20: "th", 0x21: "d", 0x22: "dh", 0x23: "n",
    0x24: "t", 0x25: "th", 0x26: "d", 0x27: "dh", 0x28: "n",
    0x2A: "p", 0x2B: "ph", 0x2C: "b", 0x2D: "bh", 0x2E: "m",
    0x2F: "y", 0x30: "r", 0x32: "l", 0x35: "v", 0x36: "sh",
    0x37: "sh", 0x38: "s", 0x39: "h",
}
SIGNS = {
    0x3E: "aa", 0x3F: "i", 0x40: "ee", 0x41: "u", 0x42: "oo",
    0x43: "ri", 0x47: "e", 0x48: "ai", 0x4B: "o", 0x4C: "au",
}
TAMIL = {
    "அ": "a", "ஆ": "aa", "இ": "i", "ஈ": "ee", "உ": "u", "ஊ": "oo",
    "எ": "e", "ஏ": "e", "ஐ": "ai", "ஒ": "o", "ஓ": "o", "ஔ": "au",
    "க": "k", "ங": "ng", "ச": "ch", "ஞ": "ny", "ட": "t", "ண": "n",
    "த": "t", "ந": "n", "ப": "p", "ம": "m", "ய": "y", "ர": "r",
    "ல": "l", "வ": "v", "ழ": "zh", "ள": "l", "ற": "r", "ன": "n",
    "ஜ": "j", "ஷ": "sh", "ஸ": "s", "ஹ": "h",
}
TAMIL_SIGNS = {
    "ா": "aa", "ி": "i", "ீ": "ee", "ு": "u", "ூ": "oo",
    "ெ": "e", "ே": "e", "ை": "ai", "ொ": "o", "ோ": "o", "ௌ": "au",
}
WORD = re.compile(r"[a-z0-9]+")


def has_indic(value: str) -> bool:
    return any((ord(ch) & ~0x7F) in INDIC_BLOCKS for ch in value)


def transliterate_indic(value: str) -> str:
    out: list[str] = []
    for ch in value:
        cp = ord(ch)
        block = cp & ~0x7F
        if block not in INDIC_BLOCKS:
            out.append(ch)
            continue
        if block == 0x0B80:
            if ch in TAMIL:
                stem = TAMIL[ch]
                out.append(stem + ("a" if ch not in "அஆஇஈஉஊஎஏஐஒஓஔ" else ""))
            elif ch in TAMIL_SIGNS:
                if out and out[-1].endswith("a"):
                    out[-1] = out[-1][:-1]
                out.append(TAMIL_SIGNS[ch])
            elif ch == "்" and out and out[-1].endswith("a"):
                out[-1] = out[-1][:-1]
            elif ch in "ஂஃ":
                out.append("m")
            continue
        offset = cp - block
        if offset in CONSONANTS:
            out.append(CONSONANTS[offset] + "a")
        elif offset in VOWELS:
            out.append(VOWELS[offset])
        elif offset in SIGNS:
            if out and out[-1].endswith("a"):
                out[-1] = out[-1][:-1]
            out.append(SIGNS[offset])
        elif offset == 0x4D:  # virama
            if out and out[-1].endswith("a"):
                out[-1] = out[-1][:-1]
        elif offset in (0x02, 0x03):  # anusvara / visarga
            out.append("m" if offset == 0x02 else "h")
        elif 0x66 <= offset <= 0x6F:
            out.append(str(offset - 0x66))
    return "".join(out)


def ascii_words(value: str) -> list[str]:
    value = unicodedata.normalize("NFKC", value)
    value = transliterate_indic(value)
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return WORD.findall(value.casefold().replace("&", " and ").replace("+", " and "))
