"""Name keys equal up to abbreviations, legal forms, stop words and word order."""
import numpy as np, pandas as pd
from post_ops import tokens, LEG, STOP

# Hand-written abbreviation lexicon (documented in REPORT.md). French: Cie/Compagnie, Ets/Etablissements,
# St/Saint, Ste/Sainte ("&"/"et" vanish as stop words). English/India analogues are legal forms (LEG) or stop words
# (corp/corporation, inc/incorporated, pvt/private, ltd/limited, co/company, &/and), so they vanish too.
ABBR = {"cie": "compagnie", "ets": "etablissements", "etabl": "etablissements", "etab": "etablissements",
        "st": "saint", "ste": "sainte"}


def content(name: str) -> list[str]:
    return [w for w in tokens(name or "") if w not in LEG and w not in STOP]


def keys(name: str) -> tuple[tuple, tuple]:
    """(raw content key, abbreviation-normalized content key), both sorted."""
    c = content(name)
    return tuple(sorted(c)), tuple(sorted(ABBR.get(w, w) for w in c))


def classify_names(ns, nr):
    """per pair: 'same' (content words equal up to order), 'abbr' (equal only after the abbreviation map), ''."""
    out = []
    for a, b in zip(ns, nr):
        ra, na = keys(a)
        rb, nb = keys(b)
        if not na:
            out.append("")
        elif ra == rb:
            out.append("same")
        elif na == nb:
            out.append("abbr")
        else:
            out.append("")
    return np.array(out, object)


def raw_diff(ns, nr):
    """True when the raw folded names differ beyond case/spacing (i.e. the pair differs by legal forms/stop words/order/abbr)."""
    return np.array([" ".join(tokens(a or "")) != " ".join(tokens(b or "")) for a, b in zip(ns, nr)])
