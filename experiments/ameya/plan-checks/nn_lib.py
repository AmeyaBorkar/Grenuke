"""Shared helpers for the 25 Sep plan checks: crude normalisation and rare-token nearest-S1 retrieval.

Crude on purpose (ASCII fold, lowercase, alnum tokens): it tests the direction and rough size of plan claims.
"""
import os
import re
import time
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

# Parquet cache written by make_cache.py (default <repo>/data_cache, git-ignored).
DC = os.environ.get("BER_CACHE_DIR", str(Path(__file__).resolve().parents[3] / "data_cache"))
T0 = time.time()
_TOK = re.compile(r"[a-z0-9]+")
_NUM = re.compile(r"\d+")
LEGAL = set("inc llc ltd pvt private limited corp corporation co company lp llp pllc pc plc the sarl sas sasu eurl sa sci snc".split())


def log(*a):
    print(f"[{time.time() - T0:6.1f}s]", *a, flush=True)


def fold(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def core(s):
    return {t for t in _TOK.findall(fold(s)) if t not in LEGAL}


def addr(s):
    return [t for t in _TOK.findall(fold(s)) if t != "null"]


def jac(a, b):
    return len(a & b) / len(a | b) if (a or b) else np.nan


def nearest_s1(s1, q, cap=300):
    """Top-1 S1 row for every query row, scored by the summed IDF of shared rare tokens (same country)."""
    sets = [core(n) | set(addr(a)) for n, a in zip(s1.business_name, s1.business_address)]
    lens = np.fromiter((len(x) for x in sets), np.int64, len(sets))
    fi = np.repeat(np.arange(len(s1)), lens)
    fk = s1.country.to_numpy()[fi] + "|" + pd.Series([t for x in sets for t in x]).to_numpy(dtype=object)
    codes, uniq = pd.factorize(fk)
    dft = np.bincount(codes)
    nc = s1.country.value_counts().to_dict()
    idf = np.log(np.array([nc[u.split("|", 1)[0]] for u in uniq]) / dft)
    keep = dft[codes] <= cap
    index = pd.DataFrame({"code": codes[keep], "s1i": fi[keep]})
    qs = [core(n) | set(addr(a)) for n, a in zip(q.business_name, q.business_address)]
    ql = np.fromiter((len(x) for x in qs), np.int64, len(qs))
    qi = np.repeat(np.arange(len(q)), ql)
    qk = q.country.to_numpy()[qi] + "|" + pd.Series([t for x in qs for t in x]).to_numpy(dtype=object)
    qc = pd.Index(uniq).get_indexer(qk)
    ok = qc >= 0
    ok[ok] = dft[qc[ok]] <= cap
    j = pd.DataFrame({"qi": qi[ok], "code": qc[ok]}).merge(index, on="code")
    j["w"] = idf[j.code.to_numpy()]
    sc = j.groupby(["qi", "s1i"], sort=False)["w"].sum().reset_index()
    best = sc.loc[sc.groupby("qi")["w"].idxmax()].set_index("qi")
    return best.s1i.reindex(range(len(q))).to_numpy()


def bucket(s1, q, top):
    out = []
    for k, t in enumerate(top):
        if np.isnan(t):
            out.append("no S1 found")
            continue
        a = s1.iloc[int(t)]
        nj = jac(core(a.business_name), core(q.business_name.iat[k]))
        aw = {x for x in addr(a.business_address) if not x.isdigit() and len(x) > 1}
        bw = {x for x in addr(q.business_address.iat[k]) if not x.isdigit() and len(x) > 1}
        aj = jac(aw, bw)
        aj = 0.0 if np.isnan(aj) else aj
        if nj >= 0.5 and aj >= 0.5:
            out.append("close on name and address")
        elif nj >= 0.5:
            out.append("close on name only")
        elif aj >= 0.5:
            out.append("close on address only")
        else:
            out.append("no close S1")
    return out


