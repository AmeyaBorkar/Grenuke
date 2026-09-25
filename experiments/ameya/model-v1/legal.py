"""Legal forms of business names as bitmasks, and the legal-form relation of a pair (features v3).

The blocking tokenizer drops legal forms (``ber.block.text.LEGAL``), so the v1/v2 name features never see them. The
look-alike records of the data add or change the legal form ("Bright Voya LP" -> "Bright Voya Corp", "High Agro LLP"
-> "ஹை அக்ரோ லிமிடெட்" = limited) while true records keep it, reformat it ("((LLC))", "L.L.C.") or drop it. On
the v2 holdout, pairs scored 0.8-0.9 are true 94% of the time when the legal form is the same, 18% when it changed.

- Latin names: folded, dots removed ("l.l.c." -> "llc"), whole tokens looked up in ``WORDS`` with single-character
  OCR variants (c0rp, lnc, 1td).
- Indic-script names: transliterated (``ber.block.indic``); a token's consonant skeleton maps to a legal form
  (praaivet/piraivet -> prvt -> pvt, limited/limitet -> lmtd/lmt -> ltd, elaelapii -> elp -> llp, "pra. li." -> pvt,
  ltd).
- French legal forms get their own bits (the test adds France): the relation features stay the same. "EI"
  (entreprise individuelle, 4.2k French test S1 and 16.4k records) is a form too, so EI -> SARL is a change, not an
  addition.
"""
from __future__ import annotations

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc

from ber.block import indic, text

FORMS = ("pvt", "ltd", "llc", "inc", "corp", "co", "llp", "lp", "pllc", "pc", "plc", "opc", "sas", "sarl", "sa",
         "sasu", "eurl", "sci", "snc", "gmbh", "ei")
BIT = {f: 1 << i for i, f in enumerate(FORMS)}
_BASE = {"pvt": "pvt", "private": "pvt", "prvt": "pvt", "ltd": "ltd", "limited": "ltd", "llc": "llc", "inc": "inc",
         "incorporated": "inc", "corp": "corp", "corporation": "corp", "co": "co", "company": "co", "cos": "co",
         "llp": "llp", "lp": "lp", "pllc": "pllc", "pc": "pc", "plc": "plc", "opc": "opc", "sas": "sas",
         "sarl": "sarl", "sa": "sa", "sasu": "sasu", "eurl": "eurl", "sci": "sci", "snc": "snc", "gmbh": "gmbh",
         "ei": "ei", "eirl": "ei"}
_OCR = {"o": "0", "l": "1i", "i": "l1"}
# consonant skeletons of transliterated Indic legal words (see ber.block.indic.LEGAL_SKELETONS)
_SKELETON = {"prvt": "pvt", "prbt": "pvt", "prvr": "pvt", "lmt": "ltd", "lmtd": "ltd", "lmrd": "ltd", "elp": "llp"}


def _words() -> dict[str, int]:
    out = {w: BIT[f] for w, f in _BASE.items()}
    for w, f in _BASE.items():
        if len(w) < 3:
            continue
        for i, ch in enumerate(w):
            for alt in _OCR.get(ch, ""):
                out.setdefault(w[:i] + alt + w[i + 1:], BIT[f])
    out["pvtltd"] = BIT["pvt"] | BIT["ltd"]
    out["privatelimited"] = BIT["pvt"] | BIT["ltd"]
    return out


WORDS = _words()


def legal_bits(names: pa.Array) -> np.ndarray:
    """int64 bitmask of the legal forms in each name (bits: ``FORMS``)."""
    n = len(names)
    names = pc.fill_null(names, "")
    is_indic = pc.match_substring_regex(names, indic.INDIC_PATTERN).to_numpy(zero_copy_only=False)
    s = text.fold(indic.transliterate_array(names))
    s = pc.replace_substring(s, ".", "")
    tok = text._split(s, r"[^a-z0-9]+")  # noqa: SLF001
    out = np.zeros(n, np.int64)
    if len(tok.values) == 0:
        return out
    enc = pc.dictionary_encode(tok.values)
    uniq = enc.dictionary.to_pylist()
    idx = enc.indices.to_numpy(zero_copy_only=False)
    m_word = np.array([WORDS.get(u, 0) for u in uniq], np.int64)
    sk = indic.skeleton(enc.dictionary).to_pylist()
    m_sk = np.array([BIT[_SKELETON[k]] if k in _SKELETON else
                     (BIT["pvt"] if k == "pr" and len(u) <= 5 else (BIT["ltd"] if k == "l" and len(u) <= 3 else 0))
                     for k, u in zip(sk, uniq)], np.int64)
    bits = m_word[idx] | np.where(is_indic[tok.rows], m_sk[idx], 0)
    rows = tok.rows
    starts = np.flatnonzero(np.r_[True, rows[1:] != rows[:-1]])
    out[rows[starts]] = np.bitwise_or.reduceat(bits, starts)
    return out


REL = ("none", "same", "dropped", "added", "subset", "superset", "changed")


def relation(b_s1: np.ndarray, b_r: np.ndarray) -> np.ndarray:
    """Relation code per pair (index into ``REL``)."""
    inter = b_s1 & b_r
    return np.select([(b_s1 == 0) & (b_r == 0), b_s1 == b_r, b_r == 0, b_s1 == 0, inter == b_r, inter == b_s1],
                     [0, 1, 2, 3, 4, 5], 6).astype(np.int8)


def pair_features(b_s1: np.ndarray, b_r: np.ndarray) -> dict[str, np.ndarray]:
    """leg__* features of pairs from the two bitmasks."""
    bc = np.bitwise_count
    return {
        "leg__rel": relation(b_s1, b_r).astype(np.float32),
        "leg__n_s1": bc(b_s1).astype(np.float32),
        "leg__n_r": bc(b_r).astype(np.float32),
        "leg__inter": bc(b_s1 & b_r).astype(np.float32),
        "leg__s1_only": bc(b_s1 & ~b_r).astype(np.float32),
        "leg__r_only": bc(b_r & ~b_s1).astype(np.float32),
    }
