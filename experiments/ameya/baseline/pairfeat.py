"""Fast pair signals for the baseline (Submission 1) and the dev features (Sachi's model development).

Not the team's feature stage (that is ber.features, issue #7/#12); a small, vectorized reference set:
- token overlap per field (name tokens, address words, address numbers): counts, IDF-weighted Jaccard, containment
  both ways, and the IDF mass of tokens only one side has (the look-alike "extra word" signal);
- house-number relation (equal / truncation / nudge <= 10 / other / missing) and log difference;
- rapidfuzz scores on folded strings (name token_sort, name partial, address token_set);
- retrieval metadata (score, ranks both ways) and context (candidates per S1 / per record, gap to the best score).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pyarrow.compute as pc
import pyarrow.parquet as pq
from numba import njit, prange

from ber.block import text
from ber.block.index import sort_unique_rows
from ber.paths import records_path

FIELDS = ("name", "word", "num")


def _field_csr(tok: text.Tokens, n: int):
    enc = pc.dictionary_encode(tok.values)
    codes = enc.indices.to_numpy(zero_copy_only=False).astype(np.int32)
    ptr = np.zeros(n + 1, np.int64)
    np.cumsum(np.bincount(tok.rows, minlength=n), out=ptr[1:])
    ptr, codes = sort_unique_rows(ptr, codes)
    df = np.bincount(codes, minlength=len(enc.dictionary))
    w = np.log(n / np.maximum(df, 1)).astype(np.float32)
    wsum = np.add.reduceat(np.concatenate([w[codes], [0]]), ptr[:-1]) * (np.diff(ptr) > 0)
    return ptr, codes, w, wsum.astype(np.float32), enc.dictionary


def load_records(split: str) -> dict:
    """Per-record token CSRs (sorted unique codes), IDF weights, first numbers and folded strings."""
    tbl = pq.read_table(records_path(split), columns=["eid", "source", "country", "name", "address"])
    n = tbl.num_rows
    names, addrs = tbl["name"].combine_chunks(), tbl["address"].combine_chunks()
    out = {"eid": tbl["eid"].to_numpy(), "source": tbl["source"].to_numpy(), "n": n}
    out["name"] = _field_csr(text.name_tokens(names), n)
    out["word"] = _field_csr(text.address_words(addrs), n)
    nums = text.address_numbers(addrs)
    out["num"] = _field_csr(nums, n)
    first = np.full(n, -1, np.int64)
    rows, idx = np.unique(nums.rows, return_index=True)
    vals = pc.utf8_slice_codeunits(pc.take(nums.values, idx), 0, 12).to_numpy(zero_copy_only=False)
    first[rows] = np.array([int(v) for v in vals], dtype=np.int64)
    out["num1"] = first
    out["fname"] = np.asarray(text.fold(names).to_numpy(zero_copy_only=False), dtype=object)
    out["faddr"] = np.asarray(text.fold(addrs).to_numpy(zero_copy_only=False), dtype=object)
    out["row_of"] = pd.Index(out["eid"])
    return out


@njit(parallel=True, cache=True)
def _overlap(ptr, codes, w, ii, jj):
    n = ii.size
    inter = np.empty(n, np.float32)
    winter = np.empty(n, np.float32)
    for k in prange(n):
        a, a1 = ptr[ii[k]], ptr[ii[k] + 1]
        b, b1 = ptr[jj[k]], ptr[jj[k] + 1]
        c = 0
        s = 0.0
        while a < a1 and b < b1:
            x, y = codes[a], codes[b]
            if x == y:
                c += 1
                s += w[x]
                a += 1
                b += 1
            elif x < y:
                a += 1
            else:
                b += 1
        inter[k] = c
        winter[k] = s
    return inter, winter


@njit(parallel=True, cache=True)
def _num_relation(x, y):
    """0 missing, 1 equal, 2 truncation/prefix (drop 1-3 trailing digits), 3 nudge (|d| <= 10), 4 other."""
    out = np.empty(x.size, np.int8)
    for k in prange(x.size):
        a, b = x[k], y[k]
        if a < 0 or b < 0:
            out[k] = 0
        elif a == b:
            out[k] = 1
        else:
            hi, lo = (a, b) if a > b else (b, a)
            rel = 4
            p = hi
            for _ in range(3):
                p //= 10
                if p == lo and p > 0:
                    rel = 2
                    break
            if rel == 4 and hi - lo <= 10:
                rel = 3
            out[k] = rel
    return out


def pair_features(rec: dict, pairs: pd.DataFrame, chunk: int = 5_000_000) -> pd.DataFrame:
    """Signals for candidate pairs (s1, r, score_tok, rank_s1_tok, rank_r_tok) of one split."""
    from rapidfuzz import fuzz, process

    ii = rec["row_of"].get_indexer(pairs["s1"].to_numpy())
    jj = rec["row_of"].get_indexer(pairs["r"].to_numpy())
    if (ii < 0).any() or (jj < 0).any():
        raise ValueError("pairs reference ids that are not in the records")
    cols: dict[str, np.ndarray] = {}
    for f in FIELDS:
        ptr, codes, w, wsum, _ = rec[f]
        inter, winter = _overlap(ptr, codes, w, ii, jj)
        la, lb = np.diff(ptr)[ii].astype(np.float32), np.diff(ptr)[jj].astype(np.float32)
        wa, wb = wsum[ii], wsum[jj]
        union = wa + wb - winter
        with np.errstate(divide="ignore", invalid="ignore"):
            cols[f"{f}__inter"] = inter
            cols[f"{f}__jac_w"] = np.where(union > 0, winter / union, np.nan).astype(np.float32)
            cols[f"{f}__cont_s1"] = np.where(la > 0, inter / la, np.nan).astype(np.float32)
            cols[f"{f}__cont_r"] = np.where(lb > 0, inter / lb, np.nan).astype(np.float32)
            cols[f"{f}__extra_r_w"] = (wb - winter).astype(np.float32)   # IDF mass only the record has
            cols[f"{f}__extra_s1_w"] = (wa - winter).astype(np.float32)  # IDF mass only S1 has
        cols[f"{f}__len_s1"], cols[f"{f}__len_r"] = la, lb
    n1, n2 = rec["num1"][ii], rec["num1"][jj]
    cols["num__rel1"] = _num_relation(n1, n2).astype(np.float32)
    cols["num__logdiff1"] = np.where((n1 >= 0) & (n2 >= 0), np.log1p(np.abs(n1 - n2).astype(np.float64)),
                                     np.nan).astype(np.float32)
    for name, field, scorer in (("name__tsort", "fname", fuzz.token_sort_ratio), ("name__partial", "fname", fuzz.partial_ratio),
                                ("addr__tset", "faddr", fuzz.token_set_ratio)):
        out = np.empty(len(pairs), np.float32)
        s = rec[field]
        for a in range(0, len(pairs), chunk):
            b = min(a + chunk, len(pairs))
            out[a:b] = process.cpdist(s[ii[a:b]], s[jj[a:b]], scorer=scorer, workers=-1, dtype=np.float32)
        cols[name] = out
    cols["ret__score"] = pairs["score_tok"].to_numpy(np.float32)
    cols["ret__rank_s1"] = np.where(pairs["rank_s1_tok"] >= 0, pairs["rank_s1_tok"], 99).astype(np.float32)
    cols["ret__rank_r"] = np.where(pairs["rank_r_tok"] >= 0, pairs["rank_r_tok"], 99).astype(np.float32)
    for c in CONTEXT:
        cols[c] = pairs[c].to_numpy(np.float32)
    cols["src__is_s3"] = (rec["source"][jj] == 3).astype(np.float32)
    return pd.DataFrame(cols)


CONTEXT = ("ctx__n_cand_s1", "ctx__n_cand_r", "ctx__gap_s1_best", "ctx__gap_r_best")


def add_context(pairs: pd.DataFrame) -> pd.DataFrame:
    """Candidate-set context, computed once on the whole candidate table (it needs every pair of an S1 / record)."""
    g1 = pairs.groupby("s1")["score_tok"]
    g2 = pairs.groupby("r")["score_tok"]
    pairs["ctx__n_cand_s1"] = g1.transform("size").astype(np.float32)
    pairs["ctx__n_cand_r"] = g2.transform("size").astype(np.float32)
    pairs["ctx__gap_s1_best"] = (g1.transform("max") - pairs["score_tok"]).astype(np.float32)
    pairs["ctx__gap_r_best"] = (g2.transform("max") - pairs["score_tok"]).astype(np.float32)
    return pairs
