"""Name parsing; legal forms and honorifics are removed only from ``n_core``."""
from __future__ import annotations

import re

from .lexicons import HONORIFICS, LEGAL_FORMS, NAME_JUNK
from .text import ascii_words, has_indic

DOMAIN = re.compile(r"(?i)(?:^|\W)[a-z0-9-]+\.(?:com|in|net|org|co|fr|io)\b")
HASHTAG = re.compile(r"(?:^|\s)#[\w]+")
PHONE = re.compile(r"(?<!\d)(?:\+?\d[\s().-]*){9,}(?!\d)")
DBA = re.compile(r"(?i)\b(?:d\s*\.?\s*b\s*\.?\s*a\.?|doing\s+business\s+as)\b")
LEGAL_MAX_WORDS = max(len(form.split()) for form in LEGAL_FORMS)


def parse_name(raw: str | None) -> tuple[str, str, str, str, bool, bool, bool, bool, bool, bool]:
    raw = raw or ""
    words = ascii_words(raw)
    full = " ".join(words)
    legal = ""
    kept: list[str] = []
    honorific = False
    i = 0
    while i < len(words):
        matched = False
        for n in range(min(LEGAL_MAX_WORDS, len(words) - i), 0, -1):
            form = " ".join(words[i:i + n])
            if form in LEGAL_FORMS:
                if not legal:
                    legal = LEGAL_FORMS[form]
                i += n
                matched = True
                break
        if matched:
            continue
        word = words[i]
        if word in HONORIFICS:
            honorific = True
        elif word not in NAME_JUNK:
            kept.append(word)
        i += 1
    core = " ".join(kept) or full
    return (
        full, core, core.replace(" ", ""), legal,
        bool(DOMAIN.search(raw)), bool(HASHTAG.search(raw)),
        bool(PHONE.search(raw)), bool(DBA.search(raw)),
        has_indic(raw), honorific,
    )
