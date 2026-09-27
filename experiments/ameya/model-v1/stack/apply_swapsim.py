"""Drop look-alike word swaps in the countries without training labels (France), RESEARCH_v6.md 6.17.

    python apply_swapsim.py <matches tag> <new matches tag>

A predicted pair is dropped when, after legal forms and stop words, the names differ by exactly one content word, the
record's word is a real word (in at least REAL_MIN S1 names of the country, at least MIN_LEN letters), is not a list
word (LIST_A), and resembles the S1's word (Indel similarity >= GARBLE_SIM): "college du marie" -> "ecole du marie",
"vgp amis sa" -> "vgp maison sa", "fraicheur agricole sarl" -> "fraicheur amicale sarl". This is the error agent's
swap_real_sim population: 592 French predictions of v7sq-dpc. France has 4,088 such candidates at the S1's address
against 172 in a same-size US/India holdout sample, so the population is the French look-alike trap; US/India base
rates allow about 130 true copies among the 484 predicted at the address, and the size-bias test fits a false share
of 0.83 [0.56, 1.10]. Countries with training labels are never changed (there these pairs are 99.3% true).
Other name categories (acronym, concatenation, typo, abbreviation, one word added or dropped, list-word swap, several
words) are recognised first and kept, exactly as the error agent's classifier did. Peak memory about 3 GB.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.compute as pc
import pyarrow.parquet as pq
from rapidfuzz.distance import Indel

D = Path(__file__).resolve().parent
sys.path[1:1] = [str(D), str(D.parent)]  # the stack modules, then model-v1 (post_ops)
from post_ops import GARBLE_SIM, LEG, LIST_A, MIN_LEN, REAL_MIN, STOP, close, tokens  # noqa: E402
from textlib import load_text  # noqa: E402

from ber.artifacts import read_table, write_table  # noqa: E402
from ber.block.text import fold  # noqa: E402
from ber.paths import records_path  # noqa: E402


def _abbr(a: str, b: str) -> bool:
    if len(a) > len(b):
        a, b = b, a
    if len(a) < 2 or len(a) >= len(b) or a[0] != b[0]:
        return False
    it = iter(b)
    return all(ch in it for ch in a)


def is_swapsim(sc: tuple, rc: tuple, vocab: Counter) -> bool:
    """True for the swap_real_sim category of the error agent's name classifier (content-word tuples)."""
    if not sc or not rc or sc == rc:
        return False
    if len(sc) >= 2 and len(rc) == 1 and 2 <= len(rc[0]) <= 5 and rc[0] == "".join(w[0] for w in sc):
        return False  # acronym
    sj, rj = "".join(sc), "".join(rc)
    if len(rc) < len(sc) and sj.startswith(rj) and len(rj) > len(sc[0]):
        return False  # concatenation
    used, miss = set(), []
    for w in sc:
        j = next((j for j, x in enumerate(rc) if j not in used and close(w, x)), None)
        if j is None:
            miss.append(w)
        else:
            used.add(j)
    add = [x for j, x in enumerate(rc) if j not in used]
    if not miss and not add:
        return False  # typo
    for w in list(miss):
        j = next((k for k, x in enumerate(add) if _abbr(w, x)), None)
        if j is not None:
            miss.remove(w)
            add.pop(j)
    if (not miss and not add) or len(miss) == len(sc) or len(miss) != 1 or len(add) != 1:
        return False  # abbreviation, disjoint, one word added or dropped, several words
    a, d = add[0], miss[0]
    if a in LIST_A:
        return False
    return vocab.get(a, 0) >= REAL_MIN and len(a) >= MIN_LEN and Indel.normalized_similarity(a, d) >= GARBLE_SIM


def main(tag: str, out: str) -> None:
    labelled = set(pc.unique(pq.read_table(records_path("train"), columns=["country"])["country"]).to_pylist())
    t = pq.read_table(records_path("test"), columns=["eid", "source", "country", "name"], filters=[("source", "==", 1)])
    s1 = pd.DataFrame({"eid": t["eid"].to_numpy(), "cty": t["country"].to_pandas().astype(str).to_numpy()})
    other = ~s1.cty.isin(labelled).to_numpy()
    names = fold(t["name"].combine_chunks().fill_null("")).to_numpy(zero_copy_only=False)
    del t
    vocab: dict[str, Counter] = {}
    for c in s1.cty[other].unique():
        cnt: Counter = Counter()
        for n in names[(s1.cty == c).to_numpy()]:
            cnt.update(set(tokens(n)))
        vocab[c] = cnt
    cty = s1.set_index("eid").cty
    m = read_table("matches", tag, "test", ["s1", "r"])
    mo = m[~cty.reindex(m.s1).isin(labelled).to_numpy()]
    txt = load_text("test", np.r_[mo.s1.to_numpy(), mo.r.to_numpy()])

    def cont(n: str) -> tuple:
        return tuple(w for w in tokens(n) if w not in LEG and w not in STOP)

    sc = [cont(n) for n in txt.name.reindex(mo.s1).fillna("").to_numpy()]
    rc = [cont(n) for n in txt.name.reindex(mo.r).fillna("").to_numpy()]
    cc = cty.reindex(mo.s1).to_numpy()
    flag = np.array([is_swapsim(a, b, vocab[c]) for a, b, c in zip(sc, rc, cc)], bool)
    drop = mo[flag]
    k = 4_000_000_000
    keep = ~np.isin(m.s1.to_numpy() * k + m.r.to_numpy(), drop.s1.to_numpy() * k + drop.r.to_numpy())
    write_table(m[keep].reset_index(drop=True), "matches", out, "test", command=f"apply_swapsim.py {tag} {out}")
    print(f"{out}: dropped {int(flag.sum())} look-alike swaps in {len(mo)} pairs of countries without labels; "
          f"pairs {len(m)} -> {int(keep.sum())}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
