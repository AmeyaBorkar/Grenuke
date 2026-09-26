"""Name repairs for blocking: extra name tokens for records whose name is a domain/handle or carries OCR digits.

Two vendor habits hide a record's name words from the token index (holdout blocking misses, RESEARCH_v5.md §5):
- **domains and handles**: "BLUEGRILL.COM", "@LUCKYICE", "#physicaltherapy", "acnservicescom". The name is one
  long token, so it only meets its S1 through the joined-name key when every S1 word is present. A dynamic
  program segments the token into words of the same country's S1 name vocabulary. It is frequency-weighted,
  allows a few initials and a leading "www" or a trailing domain suffix (com/net/org/in/co/info/biz), and needs
  full coverage. The words found are added as extra name tokens ("bluegrill" -> "blue", "grill");
- **OCR digits** inside words: "capita1", "5UAREZ", "8ROKERAGE". Digits map to look-alike letters (0->o, 1->l or i,
  5->s, 8->b, 6->g, 3->e, 4->a). The repaired word is added only when it is in the country's S1 name vocabulary.
The original tokens always stay. Only S2/S3 records are repaired: S1 names are the clean reference. Vocabularies
are built per country label from the S1 names of the same pool, so an unseen country (France) gets its own.
The loops run over distinct tokens, never over records or pairs. The lexicons (domain affixes, the OCR map) are
hand-written; no external data.
"""
from __future__ import annotations

import math
import re

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc

from . import text

DOMAIN_SUFFIX = frozenset({"com", "net", "org", "in", "co", "info", "biz"})
DOMAIN_PREFIX = frozenset({"www"})
OCR = {"0": "o", "1": "li", "3": "e", "4": "a", "5": "s", "6": "g", "8": "b"}
MARKER = r"(\.(com|net|org|in|co|info|biz)\b|\bwww\b|[@#])"
SEG_MIN_LEN = 8        # one-token names this long are segmented (6 with a domain/handle marker)
SEG_MARKER_MIN_LEN = 6
MAX_WORD = 24
SEG_PENALTY = 3.0      # per segment: fewer, longer words win
AFFIX_COST = 2.0       # www / com ...
LEGAL_COST = 6.0
INITIAL_COST = 9.0     # per single letter
MAX_INITIALS = 2
MAX_WORDS = 4


def s1_vocabulary(tok: text.Tokens, is_s1: np.ndarray, country: np.ndarray) -> dict[str, dict[str, int]]:
    """Per country label: how many S1 names contain each name token."""
    m = is_s1[tok.rows]
    rows = tok.rows[m]
    d = pd.DataFrame({"c": country[rows], "r": rows,
                      "t": pc.filter(tok.values, pa.array(m)).to_numpy(zero_copy_only=False)})
    d = d.drop_duplicates(["r", "t"])
    out: dict[str, dict[str, int]] = {}
    for c, g in d.groupby("c", sort=False):
        out[str(c)] = g["t"].value_counts().to_dict()
    return out


def _allowed(word: str, count: int) -> bool:
    """Short words need more S1 support, so pseudo-words do not split into chance syllables."""
    return len(word) >= 3 and count >= (1 if len(word) >= 5 else 2 if len(word) == 4 else 20)


def segment(token: str, vocab: dict[str, int], total: int) -> list[str] | None:
    """The S1 words that cover ``token`` (plus initials and domain affixes), cheapest first; None if no cover
    with at least two pieces, one word of 3+ letters, <= MAX_INITIALS initials and <= MAX_WORDS words."""
    if vocab.get(token):  # the token is itself an S1 word: it already meets its S1
        return None
    n = len(token)
    best = [math.inf] * (n + 1)
    back = [-1] * (n + 1)
    best[0] = 0.0
    for i in range(1, n + 1):
        for j in range(max(0, i - MAX_WORD), i):
            if best[j] == math.inf:
                continue
            piece = token[j:i]
            cnt = vocab.get(piece, 0)
            if cnt and _allowed(piece, cnt):
                c = math.log(total / cnt) + SEG_PENALTY
            elif (piece in DOMAIN_SUFFIX and i == n and j > 0) or (piece in DOMAIN_PREFIX and j == 0 and i < n):
                c = AFFIX_COST
            elif piece in text.LEGAL and len(piece) >= 2:
                c = LEGAL_COST
            elif len(piece) == 1:
                c = INITIAL_COST
            else:
                continue
            if best[j] + c < best[i]:
                best[i], back[i] = best[j] + c, j
    if best[n] == math.inf:
        return None
    pieces, i = [], n
    while i > 0:
        pieces.append(token[back[i]:i])
        i = back[i]
    pieces.reverse()
    words = [p for p in pieces if len(p) >= 3 and p not in DOMAIN_SUFFIX | DOMAIN_PREFIX and p not in text.LEGAL]
    initials = sum(len(p) == 1 for p in pieces)
    if len(pieces) < 2 or not words or initials > MAX_INITIALS or len(words) > MAX_WORDS:
        return None
    return words


def ocr_repair(token: str, vocab: dict[str, int]) -> str | None:
    """The most frequent S1 word that ``token`` becomes when its digits are read as the letters they resemble."""
    if not re.search(r"[0-9]", token) or sum(ch.isalpha() for ch in token) < 2 or len(token) < 4:
        return None
    options = [OCR.get(ch, ch) if ch.isdigit() else ch for ch in token]
    if any(ch.isdigit() for ch in options) or sum(len(o) > 1 for o in options) > 4:
        return None  # an unmappable digit (2, 7, 9) or too many ambiguous ones
    best, best_n = None, 0
    for combo in _product(options):
        cnt = vocab.get(combo, 0)
        if cnt > best_n and combo not in text.LEGAL and combo not in text.NAME_STOP:
            best, best_n = combo, cnt
    return best


def _product(options: list[str]) -> list[str]:
    out = [""]
    for o in options:
        out = [p + ch for p in out for ch in o]
    return out


def _apply(idx: np.ndarray, tok_rows: np.ndarray, country: np.ndarray, vals: np.ndarray, fn) -> pd.DataFrame:
    """(row, word) pairs from ``fn(country, token)`` evaluated once per distinct (country, token)."""
    if idx.size == 0:
        return pd.DataFrame({"row": np.empty(0, np.int64), "w": np.empty(0, object)})
    d = pd.DataFrame({"row": tok_rows[idx], "c": country[tok_rows[idx]], "t": vals[idx]})
    u = d[["c", "t"]].drop_duplicates()
    u["w"] = [fn(str(c), t) for c, t in zip(u["c"], u["t"])]
    u = u[u["w"].notna()]
    d = d.merge(u, on=["c", "t"], how="inner")[["row", "w"]]
    return d.explode("w", ignore_index=True)


def extra_name_tokens(names: pa.Array, tok: text.Tokens, is_s1: np.ndarray, country: np.ndarray,
                      segment_domains: bool = True, repair_ocr: bool = True) -> text.Tokens:
    """Extra name tokens (rows ascending) for the S2/S3 rows: segments of domain/handle names and OCR repairs.

    ``tok`` are the name tokens of ``names`` (row = record), ``is_s1`` and ``country`` are per record."""
    n = len(names)
    country = np.asarray(country, dtype=object)
    vocab = s1_vocabulary(tok, is_s1, country)
    total = {c: max(int(np.sum(is_s1 & (country == c))), 1) for c in vocab}
    counts = np.bincount(tok.rows, minlength=n)
    vals = tok.values.to_numpy(zero_copy_only=False).astype(object)
    rec = ~is_s1[tok.rows]
    parts = []
    if segment_domains:
        marker = pc.fill_null(pc.match_substring_regex(text.fold(names), MARKER), False).to_numpy(zero_copy_only=False)
        lens = pc.utf8_length(tok.values).to_numpy(zero_copy_only=False)
        alpha = pc.match_substring_regex(tok.values, r"^[a-z]+$").to_numpy(zero_copy_only=False)
        elig = rec & alpha & (((counts[tok.rows] == 1) & (lens >= SEG_MIN_LEN))
                              | (marker[tok.rows] & (lens >= SEG_MARKER_MIN_LEN)))
        parts.append(_apply(np.flatnonzero(elig), tok.rows, country, vals,
                            lambda c, t: segment(t, vocab[c], total[c]) if c in vocab else None))
    if repair_ocr:
        digit = pc.match_substring_regex(tok.values, r"[0-9]").to_numpy(zero_copy_only=False)
        letter = pc.match_substring_regex(tok.values, r"[a-z]").to_numpy(zero_copy_only=False)
        parts.append(_apply(np.flatnonzero(rec & digit & letter), tok.rows, country, vals,
                            lambda c, t: ocr_repair(t, vocab[c]) if c in vocab else None))
    d = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame({"row": [], "w": []})
    d = d.sort_values("row", kind="stable")
    return text.Tokens(pa.array(d["w"].tolist(), type=tok.values.type), d["row"].to_numpy(np.int64))


def merge(tok: text.Tokens, extra: text.Tokens) -> text.Tokens:
    """``tok`` with ``extra`` appended after each row's own tokens (rows stay ascending)."""
    if extra.rows.size == 0:
        return tok
    rows = np.concatenate([tok.rows, extra.rows])
    order = np.argsort(rows, kind="stable")
    values = pa.concat_arrays([tok.values, extra.values.cast(tok.values.type)])
    return text.Tokens(pc.take(values, pa.array(order)), rows[order])
