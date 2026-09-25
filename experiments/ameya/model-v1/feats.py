"""Pair features v1 (model-v1 experiments): string and number groups plus context, on the full candidate graph.

    python experiments/ameya/model-v1/feats.py --cands ameya-block-v0 --split train
    python experiments/ameya/model-v1/feats.py --cands ameya-block-v0 --split test

Writes, row-aligned with the candidates (same order), in row groups of CHUNK rows:
- work/features/<tag>-str/<split>.parquet: s1, r, fold, y (train) + groups name/word/num/addr (float32);
- work/features/<tag>-cx/<split>.parquet: groups ret/ctx/src (ber.features.context + record-side rivalry).

What v1 adds over the baseline signals (error analysis of 25 Sep: Indic-name S1 carry 29.5% of the loss, the largest
bucket is true pairs scored below the threshold, look-alikes swap or add a name word):
- Indic names are transliterated; on Indic-origin names the transliterated legal forms and honorifics are dropped and
  the tokens go through an Indic->Latin dictionary learned from true pairs of train folds 5-19 only (holdout excluded,
  C2); the test run reuses it (work/models/<tag>/indic_dict.parquet);
- typo-tolerant name matching (edit distance 1, or 2 from 6 letters): the IDF mass, count and maximum of the tokens
  left without a partner on each side and the number of substituted tokens (a swapped first name is not a typo);
- consonant-skeleton and skeleton-prefix overlaps (transliteration variants, vowel typos);
- number relations over the whole number sets, not only the first numbers;
- concatenated-name scores (domains and hashtags: 'onetechnologies.com');
- IDF is per country (France gets its own statistics); rapidfuzz scores are NaN when a side is empty;
- record-side rivalry: how many S1 share the record's name key or its (number, street) key (log counts).
"""
from __future__ import annotations

import argparse
import logging
import os
import time

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
from numba import get_num_threads, get_thread_id, njit, prange

from ber.artifacts import provenance, read_table
from ber.block import indic, text
from ber.block.index import sort_unique_rows
from ber.eval.splits import fold_of
from ber.features import context
from ber.paths import artifact_dir, artifact_path, records_path
from ber.records import load_truth

log = logging.getLogger("feats")
CHUNK = 4_000_000
INDIC_RE = r"[\x{0900}-\x{0d7f}]"
# Skeletons of the transliterated legal forms and honorifics among the most frequent Indic-name tokens of train:
# praaivet/praivet/piraivet (private) prvt, praaibhet prbt, praivarr prvr, praa + li (pra. li.) pr + l,
# limitet lmt, limirrad lmrd, limited lmtd, elaelapii (LLP) elp, shrii sr. Dropped on Indic-origin names only.
INDIC_DROP_SKEL = ("prvt", "prbt", "prvr", "pr", "l", "lmt", "lmtd", "lmrd", "elp", "sr")


# ----------------------------------------------------------------------------------------------- records

def _name_tokens(names: pa.Array) -> tuple[text.Tokens, np.ndarray]:
    is_ind = pc.match_substring_regex(names, INDIC_RE).to_numpy(zero_copy_only=False)
    tok = text.name_tokens(indic.transliterate_array(names))
    sk = indic.skeleton(tok.values)
    legal = pc.is_in(sk, value_set=pa.array(INDIC_DROP_SKEL, type=sk.type)).to_numpy(zero_copy_only=False)
    keep = ~(is_ind[tok.rows] & legal)
    return text.Tokens(pc.filter(tok.values, pa.array(keep)), tok.rows[keep]), is_ind


def learn_indic_dict(tok: text.Tokens, is_ind: np.ndarray, eid: np.ndarray, truth: pd.DataFrame,
                     min_count: int = 5, min_share: float = 0.5) -> pd.DataFrame:
    """Indic-name token t -> the S1 name token w it co-occurs with most in true pairs of train folds 5-19."""
    tr = truth[fold_of(truth["s1"].to_numpy()) >= 5]
    row_of = pd.Index(eid)
    si, ri = row_of.get_indexer(tr["s1"].to_numpy()), row_of.get_indexer(tr["r"].to_numpy())
    m = is_ind[ri]
    pairs = pd.DataFrame({"pair": np.arange(m.sum()), "s": si[m], "r": ri[m]})
    need = np.zeros(len(eid), bool)
    need[pairs["s"]] = need[pairs["r"]] = True
    sel = need[tok.rows]
    t = pd.DataFrame({"row": tok.rows[sel], "tok": pc.filter(tok.values, pa.array(sel)).to_numpy(zero_copy_only=False)})
    t = t.drop_duplicates()
    rt = pairs.merge(t.rename(columns={"row": "r", "tok": "t"}), on="r")[["pair", "t"]]
    st = pairs.merge(t.rename(columns={"row": "s", "tok": "w"}), on="s")[["pair", "w"]]
    n_t = rt.groupby("t")["pair"].nunique()
    co = rt.merge(st, on="pair").groupby(["t", "w"]).size().rename("count").reset_index()
    co = co.sort_values(["t", "count"], ascending=[True, False]).drop_duplicates("t")
    co["share"] = co["count"] / n_t.reindex(co["t"]).to_numpy()
    co = co[(co["count"] >= min_count) & (co["share"] >= min_share) & (co["t"] != co["w"])]
    return co.reset_index(drop=True)


def _apply_dict(tok: text.Tokens, is_ind: np.ndarray, mapping: dict[str, str]) -> text.Tokens:
    mask = is_ind[tok.rows]
    if not mask.any() or not mapping:
        return tok
    sub = pc.filter(tok.values, pa.array(mask))
    mapped = text._map_values(sub, mapping)  # noqa: SLF001 (same package family, applied on unique values)
    return text.Tokens(pc.replace_with_mask(tok.values, pa.array(mask), mapped), tok.rows)


def _joined(tok: text.Tokens, n: int, sep: str) -> np.ndarray:
    counts = np.bincount(tok.rows, minlength=n)
    offsets = np.concatenate([[0], np.cumsum(counts)]).astype(np.int64)
    values = tok.values.cast(pa.large_string())
    lists = pa.LargeListArray.from_arrays(pa.array(offsets), values)
    return np.asarray(pc.binary_join(lists, pa.scalar(sep, pa.large_string())).to_numpy(zero_copy_only=False),
                      dtype=object)


def _field_csr(tok: text.Tokens, n: int, cid: np.ndarray) -> dict:
    """Sorted unique codes per row, per-entry IDF weights (per country), row weight sums, the first code per row and
    the dictionary as a flat byte buffer (for edit distances)."""
    enc = pc.dictionary_encode(tok.values.cast(pa.large_string()))
    codes = enc.indices.to_numpy(zero_copy_only=False).astype(np.int32)
    first = np.full(n, -1, np.int32)
    rows_u, idx = np.unique(tok.rows, return_index=True)
    first[rows_u] = codes[idx]
    ptr = np.zeros(n + 1, np.int64)
    np.cumsum(np.bincount(tok.rows, minlength=n), out=ptr[1:])
    ptr, codes = sort_unique_rows(ptr, codes)
    rows = np.repeat(np.arange(n, dtype=np.int64), np.diff(ptr))
    n_c = int(cid.max()) + 1
    key = cid[rows].astype(np.int64) * len(enc.dictionary) + codes
    _, inv, cnt = np.unique(key, return_inverse=True, return_counts=True)
    wt = np.log(np.bincount(cid, minlength=n_c)[cid[rows]] / cnt[inv]).astype(np.float32)
    wsum = np.bincount(rows, weights=wt, minlength=n).astype(np.float32)
    d = enc.dictionary
    off = np.frombuffer(d.buffers()[1], np.int64)[d.offset:d.offset + len(d) + 1]
    buf = np.frombuffer(d.buffers()[2], np.uint8)
    return {"ptr": ptr, "codes": codes, "wt": wt, "wsum": wsum, "first": first, "dict": d,
            "off": off.copy(), "buf": buf.copy()}


def load_records(split: str, dictionary: pd.DataFrame | None, truth: pd.DataFrame | None = None,
                 strings: bool = True) -> tuple[dict, pd.DataFrame | None]:
    """Token CSRs (name, skel, skel4, word, num), numbers and, if ``strings``, the folded strings for rapidfuzz."""
    t0 = time.perf_counter()
    tbl = pq.read_table(records_path(split), columns=["eid", "source", "country", "name", "address"])
    n = tbl.num_rows
    names, addrs = tbl["name"].combine_chunks(), tbl["address"].combine_chunks()
    country = tbl["country"].to_numpy(zero_copy_only=False)
    labels, cid = np.unique(country.astype(str), return_inverse=True)
    rec = {"eid": tbl["eid"].to_numpy(), "source": tbl["source"].to_numpy(), "cid": cid.astype(np.int32), "n": n}
    tok, is_ind = _name_tokens(names)
    if dictionary is None:
        dictionary = learn_indic_dict(tok, is_ind, rec["eid"], truth)
        log.info("indic dictionary: %d entries", len(dictionary))
    tok = _apply_dict(tok, is_ind, dict(zip(dictionary["t"], dictionary["w"])))
    rec["name"] = _field_csr(tok, n, rec["cid"])
    sk = text.Tokens(indic.skeleton(tok.values), tok.rows)
    rec["skel"] = _field_csr(sk, n, rec["cid"])
    rec["skel4"] = _field_csr(text.Tokens(pc.utf8_slice_codeunits(sk.values, 0, 4), sk.rows), n, rec["cid"])
    if strings:
        rec["cname"] = _joined(tok, n, " ")
        rec["ccat"] = _joined(tok, n, "")
        rec["fname"] = np.asarray(text.fold(indic.transliterate_array(names)).to_numpy(zero_copy_only=False),
                                  dtype=object)
    words = text.address_words(addrs)
    rec["word"] = _field_csr(words, n, rec["cid"])
    nums = text.address_numbers(addrs)
    rec["num"] = _field_csr(nums, n, rec["cid"])
    nd = rec["num"]["dict"].to_numpy(zero_copy_only=False)
    rec["numval"] = np.array([int(v[:12]) for v in nd], dtype=np.int64)
    first = rec["num"]["first"]
    rec["num1"] = np.where(first >= 0, rec["numval"][np.maximum(first, 0)], -1)
    if strings:
        rec["faddr"] = np.asarray(text.fold(addrs).to_numpy(zero_copy_only=False), dtype=object)
    rec["row_of"] = pd.Index(rec["eid"])
    rec["labels"] = labels
    log.info("records %s: %d rows, %d Indic names, prepared in %.0fs", split, n, int(is_ind.sum()),
             time.perf_counter() - t0)
    return rec, dictionary


# ----------------------------------------------------------------------------------------------- kernels

@njit(parallel=True, cache=True)
def _overlap_w(ptr, codes, wt, ii, jj):
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
                s += wt[a]
                a += 1
                b += 1
            elif x < y:
                a += 1
            else:
                b += 1
        inter[k] = c
        winter[k] = s
    return inter, winter


@njit(cache=True)
def _lev(buf, s0, s1, t0, t1, row0, row1):
    m = min(s1 - s0, 63)
    n = min(t1 - t0, 63)
    for j in range(n + 1):
        row0[j] = j
    for i in range(1, m + 1):
        row1[0] = i
        ci = buf[s0 + i - 1]
        for j in range(1, n + 1):
            v = row0[j] + 1
            if row1[j - 1] + 1 < v:
                v = row1[j - 1] + 1
            c = row0[j - 1] + (0 if ci == buf[t0 + j - 1] else 1)
            if c < v:
                v = c
            row1[j] = v
        for j in range(n + 1):
            row0[j] = row1[j]
    return row0[n]


@njit(parallel=True, cache=True)
def _fuzzy(ptr, codes, wt, off, buf, ii, jj, scratch):
    """Exact, then typo-tolerant token matching between the S1 and record token sets (<= 62 tokens each)."""
    n = ii.size
    out = np.zeros((7, n), np.float32)
    for k in prange(n):
        tid = get_thread_id()
        r0 = scratch[tid, 0]
        r1 = scratch[tid, 1]
        a0 = ptr[ii[k]]
        b0 = ptr[jj[k]]
        la = min(ptr[ii[k] + 1] - a0, 62)
        lb = min(ptr[jj[k] + 1] - b0, 62)
        ma = np.int64(0)
        mb = np.int64(0)
        p = 0
        q = 0
        while p < la and q < lb:
            x, y = codes[a0 + p], codes[b0 + q]
            if x == y:
                ma |= np.int64(1) << p
                mb |= np.int64(1) << q
                p += 1
                q += 1
            elif x < y:
                p += 1
            else:
                q += 1
        for q in range(lb):
            if (mb >> q) & 1:
                continue
            cb = codes[b0 + q]
            tb0, tb1 = off[cb], off[cb + 1]
            lenb = tb1 - tb0
            for p in range(la):
                if (ma >> p) & 1:
                    continue
                ca = codes[a0 + p]
                ta0, ta1 = off[ca], off[ca + 1]
                lena = ta1 - ta0
                short = min(lena, lenb)
                if short < 3:
                    continue
                bound = 1 if short <= 5 else 2
                if abs(lena - lenb) > bound:
                    continue
                if _lev(buf, ta0, ta1, tb0, tb1, r0, r1) <= bound:
                    ma |= np.int64(1) << p
                    mb |= np.int64(1) << q
                    break
        xr = 0.0
        xs = 0.0
        xr_max = 0.0
        xs_max = 0.0
        nr = 0
        ns = 0
        for q in range(lb):
            if not (mb >> q) & 1:
                w = wt[b0 + q]
                xr += w
                nr += 1
                if w > xr_max:
                    xr_max = w
        for p in range(la):
            if not (ma >> p) & 1:
                w = wt[a0 + p]
                xs += w
                ns += 1
                if w > xs_max:
                    xs_max = w
        out[0, k] = lb - nr
        out[1, k] = xr
        out[2, k] = xs
        out[3, k] = xr_max
        out[4, k] = xs_max
        out[5, k] = min(nr, ns)
        out[6, k] = nr
    return out


@njit(cache=True)
def _rel(a, b):
    """0 missing, 1 equal, 2 truncation/prefix (1-3 trailing digits dropped), 3 nudge (|d| <= 10), 4 other."""
    if a < 0 or b < 0:
        return 0
    if a == b:
        return 1
    hi, lo = (a, b) if a > b else (b, a)
    p = hi
    for _ in range(3):
        p //= 10
        if p == lo and p > 0:
            return 2
    if hi - lo <= 10:
        return 3
    return 4


@njit(parallel=True, cache=True)
def _numbers(ptr, codes, numval, num1, ii, jj):
    n = ii.size
    out = np.full((5, n), np.nan, np.float32)
    for k in prange(n):
        fa, fb = num1[ii[k]], num1[jj[k]]
        out[0, k] = _rel(fa, fb)
        if fa >= 0 and fb >= 0:
            out[1, k] = np.log1p(abs(fa - fb))
        a0, a1 = ptr[ii[k]], ptr[ii[k] + 1]
        b0, b1 = ptr[jj[k]], ptr[jj[k] + 1]
        if fa >= 0 and b1 > b0:
            best = 4
            for b in range(b0, b1):
                r = _rel(fa, numval[codes[b]])
                if r < best:
                    best = r
            out[2, k] = best  # best relation of the S1's first number to any record number
            out[3, k] = 1.0 if best == 1 else 0.0
        if fb >= 0 and a1 > a0:
            hit = 0.0
            for a in range(a0, a1):
                if numval[codes[a]] == fb:
                    hit = 1.0
            out[4, k] = hit  # the record's first number appears among the S1's numbers
    return out


@njit(parallel=True, cache=True)
def _row_hash(ptr, codes, cid):
    n = ptr.size - 1
    out = np.zeros(n, np.int64)
    for i in prange(n):
        if ptr[i + 1] == ptr[i]:
            continue
        h = np.uint64(1469598103934665603) ^ np.uint64(cid[i] + 1)
        for a in range(ptr[i], ptr[i + 1]):
            h = (h ^ np.uint64(codes[a] + 1)) * np.uint64(1099511628211)
        out[i] = np.int64(h >> np.uint64(1)) + 1
    return out


# ----------------------------------------------------------------------------------------------- features

def _set_group(cols: dict, f: str, fld: dict, ii, jj) -> None:
    inter, winter = _overlap_w(fld["ptr"], fld["codes"], fld["wt"], ii, jj)
    ptr = fld["ptr"]
    la, lb = (ptr[ii + 1] - ptr[ii]).astype(np.float32), (ptr[jj + 1] - ptr[jj]).astype(np.float32)
    wa, wb = fld["wsum"][ii], fld["wsum"][jj]
    union = wa + wb - winter
    with np.errstate(divide="ignore", invalid="ignore"):
        cols[f"{f}__inter"] = inter
        cols[f"{f}__jac_w"] = np.where(union > 0, winter / union, np.nan).astype(np.float32)
        cols[f"{f}__cont_s1"] = np.where(la > 0, inter / la, np.nan).astype(np.float32)
        cols[f"{f}__cont_r"] = np.where(lb > 0, inter / lb, np.nan).astype(np.float32)
        cols[f"{f}__extra_r_w"] = (wb - winter).astype(np.float32)
        cols[f"{f}__extra_s1_w"] = (wa - winter).astype(np.float32)
    cols[f"{f}__len_s1"], cols[f"{f}__len_r"] = la, lb


def string_features(rec: dict, ii: np.ndarray, jj: np.ndarray, scratch: np.ndarray) -> dict[str, np.ndarray]:
    from rapidfuzz import fuzz
    from rapidfuzz.distance import JaroWinkler

    cols: dict[str, np.ndarray] = {}
    for f in ("name", "word", "num"):
        _set_group(cols, f, rec[f], ii, jj)
    cols["name__idf_s1"], cols["name__idf_r"] = rec["name"]["wsum"][ii], rec["name"]["wsum"][jj]
    for f in ("skel", "skel4"):
        tmp: dict[str, np.ndarray] = {}
        _set_group(tmp, f, rec[f], ii, jj)
        for c in ("jac_w", "cont_s1", "cont_r", "extra_r_w"):
            cols[f"name__{f}_{c}"] = tmp[f"{f}__{c}"]
    nm = rec["name"]
    fz = _fuzzy(nm["ptr"], nm["codes"], nm["wt"], nm["off"], nm["buf"], ii, jj, scratch)
    for i, c in enumerate(("fz_inter", "fz_extra_r_w", "fz_extra_s1_w", "fz_extra_r_max", "fz_extra_s1_max",
                           "fz_sub", "fz_n_extra_r")):
        cols[f"name__{c}"] = fz[i]
    nu = _numbers(rec["num"]["ptr"], rec["num"]["codes"], rec["numval"], rec["num1"], ii, jj)
    for i, c in enumerate(("rel1", "logdiff1", "rel_best", "s1first_in_r", "rfirst_in_s1")):
        cols[f"num__{c}"] = nu[i]

    def score(field: str, scorer, empty_nan: bool) -> np.ndarray:
        from rapidfuzz import process

        a, b = rec[field][ii], rec[field][jj]
        out = process.cpdist(a, b, scorer=scorer, workers=-1, dtype=np.float32)
        if empty_nan:
            la, lb = rec[f"{field}_len"][ii], rec[f"{field}_len"][jj]
            out[(la == 0) | (lb == 0)] = np.nan
        return out

    cols["name__tsort"] = score("fname", fuzz.token_sort_ratio, True)
    cols["name__partial"] = score("fname", fuzz.partial_ratio, True)
    cols["name__c_tset"] = score("cname", fuzz.token_set_ratio, True)
    cols["name__c_ratio"] = score("cname", fuzz.ratio, True)
    cols["name__c_jw"] = score("cname", JaroWinkler.normalized_similarity, True) * np.float32(100)
    cols["name__cat_ratio"] = score("ccat", fuzz.ratio, True)
    cols["name__cat_partial"] = score("ccat", fuzz.partial_ratio, True)
    cols["addr__tset"] = score("faddr", fuzz.token_set_ratio, True)
    cols["addr__tsort"] = score("faddr", fuzz.token_sort_ratio, True)
    return cols


def context_features(cands: pd.DataFrame, rec: dict, split: str) -> pd.DataFrame:
    """ber.features.context groups + record-side rivalry (log counts of S1 sharing the record's keys)."""
    s1_rec = pq.read_table(records_path(split), columns=["eid", "source", "country", "name", "address"]).to_pandas()
    s1_rec = s1_rec[s1_rec["source"] == 1].drop(columns="source")
    cx = context.compute(cands, s1_rec)
    del s1_rec
    is_s1 = rec["source"] == 1
    name_key = _row_hash(rec["name"]["ptr"], rec["name"]["codes"], rec["cid"])
    # (house number, street word) key of every record, the same definition as the S1 side (context.numstreet_keys)
    addrs = pq.read_table(records_path(split), columns=["address"])["address"].combine_chunks()
    ns = context.numstreet_keys(addrs)
    codes, _ = pd.factorize(ns)
    ns_key = np.where(ns != "", (codes.astype(np.int64) + 1) * 64 + rec["cid"] + 1, 0)
    del addrs, ns, codes
    ii = rec["row_of"].get_indexer(cands["s1"].to_numpy())
    jj = rec["row_of"].get_indexer(cands["r"].to_numpy())
    for name, key in (("rname", name_key), ("rnumstreet", ns_key)):
        vc = pd.Series(key[is_s1 & (key != 0)]).value_counts()
        cnt = vc.reindex(key[jj]).fillna(0).to_numpy(np.float32)
        cnt[key[jj] == 0] = 0
        cx[f"ctx__log_s1_same_{name}"] = np.log1p(cnt).astype(np.float32)
    cx["ctx__same_name_key"] = ((name_key[ii] == name_key[jj]) & (name_key[ii] != 0)).astype(np.float32)
    return cx


# ----------------------------------------------------------------------------------------------- main

def _writer(path, schema, meta):
    path.parent.mkdir(parents=True, exist_ok=True)
    schema = schema.with_metadata({b"ber": __import__("json").dumps(meta, default=str).encode()})
    return pq.ParquetWriter(str(path) + ".tmp", schema, compression="zstd")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cands", required=True)
    ap.add_argument("--split", required=True, choices=["train", "test"])
    ap.add_argument("--tag", default="ameya-fx1")
    ap.add_argument("--limit", type=int, default=0, help="only the first N candidate rows (smoke test)")
    ap.add_argument("--out-suffix", default="")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    command = "python experiments/ameya/model-v1/feats.py " + " ".join(f"--{k.replace('_', '-')} {v}" for k, v in vars(args).items())
    t0 = time.perf_counter()

    model_dir = artifact_dir("models", args.tag)
    dict_path = model_dir / "indic_dict.parquet"
    if args.split == "train":
        rec, dictionary = load_records("train", None, load_truth())
        model_dir.mkdir(parents=True, exist_ok=True)
        dictionary.to_parquet(dict_path)
    else:
        rec, _ = load_records("test", pd.read_parquet(dict_path))
    for f in ("fname", "cname", "ccat", "faddr"):
        rec[f"{f}_len"] = np.fromiter((len(s) for s in rec[f]), np.int32, len(rec[f]))

    cands = read_table("candidates", args.cands, args.split)
    if args.limit:
        cands = cands.iloc[:args.limit].reset_index(drop=True)
    n = len(cands)
    log.info("%s: %d candidate pairs", args.split, n)
    tag_str, tag_cx = f"{args.tag}-str{args.out_suffix}", f"{args.tag}-cx{args.out_suffix}"
    meta = provenance(command, {"candidates": args.cands}, split=args.split, rows=n, chunk=CHUNK)

    # context group (needs the whole candidate table)
    cx = context_features(cands, rec, args.split)
    path = artifact_path("features", tag_cx, args.split)
    table = pa.Table.from_pandas(cx.iloc[:1], preserve_index=False)
    w = _writer(path, table.schema, {**meta, "kind": "features", "tag": tag_cx})
    for a in range(0, n, CHUNK):
        w.write_table(pa.Table.from_pandas(cx.iloc[a:a + CHUNK], preserve_index=False), row_group_size=CHUNK)
    w.close()
    os.replace(str(path) + ".tmp", path)
    log.info("context: %d columns written (%.0fs)", cx.shape[1], time.perf_counter() - t0)
    del cx

    s1 = cands["s1"].to_numpy()
    r = cands["r"].to_numpy()
    del cands
    y = None
    if args.split == "train":
        truth = load_truth()
        key = s1 * 4_000_000_000 + r
        y = np.isin(key, truth["s1"].to_numpy() * 4_000_000_000 + truth["r"].to_numpy()).astype(np.int8)
        del key
    fold = fold_of(s1).astype(np.int8)
    scratch = np.empty((get_num_threads(), 2, 64), np.int32)
    path = artifact_path("features", tag_str, args.split)
    w = None
    for a in range(0, n, CHUNK):
        b = min(a + CHUNK, n)
        ii = rec["row_of"].get_indexer(s1[a:b])
        jj = rec["row_of"].get_indexer(r[a:b])
        if (ii < 0).any() or (jj < 0).any():
            raise ValueError("candidate ids not found in the records")
        cols = {"s1": s1[a:b], "r": r[a:b], "fold": fold[a:b]}
        if y is not None:
            cols["y"] = y[a:b]
        cols.update(string_features(rec, ii.astype(np.int64), jj.astype(np.int64), scratch))
        table = pa.Table.from_pydict(cols)
        if w is None:
            w = _writer(path, table.schema, {**meta, "kind": "features", "tag": tag_str})
        w.write_table(table, row_group_size=CHUNK)
        log.info("string features: %d / %d (%.0fs)", b, n, time.perf_counter() - t0)
    w.close()
    os.replace(str(path) + ".tmp", path)
    log.info("done: %s and %s (%d string columns) in %.0fs", tag_str, tag_cx, len(cols) - 3 - (y is not None),
             time.perf_counter() - t0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
