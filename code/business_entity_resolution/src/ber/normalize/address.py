"""Address parsing with explicit number relations and conservative city/state fields."""
from __future__ import annotations

import re

from .lexicons import STATE_CODES, STATE_NAMES, STREET_TYPES
from .text import ascii_words

NUMBER = re.compile(r"\d+")
SUFFIX = re.compile(r"(?<!\d)(\d+)\s*(bis|ter|[a-z])\b")
UNIT = re.compile(r"\b(?:flat|unit|apt|apartment|suite|ste|room|rm)\s*(?:no\s*)?(\d+)\b")
NULL = re.compile(r"(?i)\b(?:null|none|n\s*/\s*a|not\s+available)\b|<\s*null\s*>")
POBOX = re.compile(r"(?i)\b(?:p\s*\.?\s*o\s*\.?\s*box|pmb|post\s+office\s+box)\b")
LANDMARK = re.compile(r"(?i)\b(?:near|nr|opp|opposite|behind|beside|landmark|pres|face)\b")
ARRONDISSEMENT = re.compile(r"(?i)\b\d{1,2}(?:e|er|eme)\b")
ORDINAL = re.compile(r"^(\d+)(?:st|nd|rd|th)$")
SPELLED_ORDINALS = {"first": "1", "second": "2", "third": "3", "fourth": "4", "fifth": "5", "sixth": "6", "seventh": "7", "eighth": "8", "ninth": "9", "tenth": "10"}
UNIT_PART = re.compile(r"(?i)\b(?:unit|apt|apartment|suite|ste|flat)\s*(?:no\s*)?[a-z0-9]+\b")
MARKERS = {"h", "n", "no", "door", "plot", "flat", "site", "sf", "sy", "unit", "apt", "apartment", "suite", "ste", "pmb", "box", "cedex", "bis", "ter"}


def _state(component: str) -> str:
    words = [word for word in ascii_words(component) if not word.isdigit()]
    if not words:
        return ""
    for n in range(min(5, len(words)), 0, -1):
        name = " ".join(words[-n:])
        if name in STATE_NAMES:
            return STATE_NAMES[name]
    return words[-1] if words[-1] in STATE_CODES else ""


def _city_score(part: str) -> int:
    words = ascii_words(part)
    if not words:
        return -100
    score = 1 + (2 if len(words) <= 4 else 0)
    if any(any(ch.isdigit() for ch in word) for word in words):
        score -= 4
    if any(word in STREET_TYPES and word not in {"saint", "st"} for word in words):
        score -= 3
    if any(word in MARKERS for word in words):
        score -= 3
    return score


def _ordinal(word: str) -> str:
    match = ORDINAL.fullmatch(word)
    return match.group(1) if match else SPELLED_ORDINALS.get(word, word)


def parse_address(raw: str | None) -> tuple[str, str, str, str, int, str, list[int], int, int, bool, bool, bool, bool, bool, bool, bool]:
    raw = raw or ""
    had_null = bool(NULL.search(raw))
    cleaned = NULL.sub(" ", raw)
    parts = [part.strip() for part in cleaned.split(",") if part.strip()]
    states = [(i, _state(part)) for i, part in enumerate(parts)]
    states = [(i, state) for i, state in states if state]
    state_index, state = states[-1] if states else (-1, "")
    candidates = [(i, _city_score(part)) for i, part in enumerate(parts) if i != state_index]
    # Tie-breaking towards the later component handles "Haveli, Pune, Shed No …";
    # with a state, the nearest plausible component usually names the city.
    city_index = -1
    if candidates:
        city_index, best = max(candidates, key=lambda item: (item[1],
            -abs(item[0] - state_index) if state_index >= 0 else item[0]))
        if best < 0:
            city_index = -1
    city = ""
    if city_index >= 0:
        city = " ".join(STREET_TYPES.get(word, word) for word in ascii_words(parts[city_index]))
    street_parts = [part for i, part in enumerate(parts) if i not in (state_index, city_index)]
    street_text = UNIT_PART.sub(" ", ", ".join(street_parts))
    raw_words = ascii_words(cleaned)
    words = [STREET_TYPES.get(_ordinal(word), _ordinal(word)) for word in raw_words if word != "cedex"]
    norm = " ".join(words)
    numbers = [int(match.group()) for match in NUMBER.finditer(" ".join(raw_words))]
    street_number = NUMBER.search(" ".join(ascii_words(street_text)))
    first = int(street_number.group()) if street_number else (numbers[0] if numbers else -1)
    suffix = ""
    if first >= 0:
        match = SUFFIX.search(" ".join(ascii_words(street_text)))
        if match and int(match.group(1)) == first:
            suffix = match.group(2)
    unit_match = UNIT.search(" ".join(ascii_words(cleaned)))
    unit = int(unit_match.group(1)) if unit_match else -1
    street_words = ascii_words(street_text)
    street = " ".join(
        STREET_TYPES.get(_ordinal(word), _ordinal(word))
        for word in street_words
        if word not in MARKERS and (ORDINAL.fullmatch(word) or word in SPELLED_ORDINALS
                                    or not NUMBER.search(word))
    )
    empty = not words
    short = len(words) <= 3
    landmark = bool(LANDMARK.search(cleaned))
    pobox = bool(POBOX.search(cleaned))
    fragment = not empty and first < 0 and len(words) <= 4
    arrondissement = bool(ARRONDISSEMENT.search(cleaned))
    return (
        norm, street, city, state, first, suffix, numbers, unit, len(words),
        empty, short, landmark, pobox, fragment, had_null, arrondissement,
    )
