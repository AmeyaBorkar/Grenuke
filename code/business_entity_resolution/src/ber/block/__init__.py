"""Stage ``block`` (owner: Ameya, docs/TEAM.md). Plan: plans/FINAL_PLAN.md section 4.3. Contract: C4.

Views (bits in ``views``; docs/CONTRACTS.md C4):
- ``tok`` (64): IDF-weighted token-overlap search over names + addresses, in both directions, per exact country label,
  with its own crude tokenizer (``ber.block.text``) so blocking does not wait for the normalize stage;
- ``name_short`` (4): the same search over **names only**, between every S1 and the S2/S3 records whose address is
  empty or has at most 3 tokens (their address cannot carry the match; FINAL_PLAN section 4.3).
Per view: S1 -> S2/S3 top ``k_s1`` and S2/S3 -> S1 top ``k_r``; a pair is kept if the record is in the S1's top
``trim_s1`` or the S1 is in the record's top ``trim_r``. Views are merged on (s1, r) with per-view score and ranks
(NaN / -1 when a view did not retrieve the pair). The GPU TF-IDF views (V-both, V-addr) join the same way later.
This exact set becomes candidate_pairs.tsv.

Parameters (``--set key=value``): k_s1 (40), k_r (8), trim_s1 (30), trim_r (2), seed_cap_r (3000), seed_cap_s1 (1000),
verify_s1 (400), verify_r (200); name_short (1 = on), ns_k (10), ns_trim_s1 (5), ns_trim_r (5), ns_max_addr_tokens (3),
ns_ngrams (0: character n-grams of names in name_short); indic_dict (a models tag holding indic_dict.parquet: the
Indic -> Latin token dictionary learned on train folds 5-19); dev_tag (train only: also write the dev-sample subset).
Blocking always searches the full record pool of the split; partitions are exact country labels (open set).
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..config import RunConfig

log = logging.getLogger("ber.block")

VIEW_BITS = {"both": 1, "addr": 2, "name_short": 4, "key_numstreet": 8, "key_domain": 16, "key_dba": 32, "tok": 64}


@dataclass
class SearchParams:
    k_s1: int
    k_r: int
    trim_s1: int
    trim_r: int
    seed_cap_r: int
    seed_cap_s1: int
    verify_s1: int
    verify_r: int


def partitions(country: np.ndarray) -> list[tuple[str, np.ndarray]]:
    """Row indices per exact country label. Rows with an empty label join every partition (open set)."""
    labels = pd.Series(country, dtype=object).fillna("").astype(str).str.strip().to_numpy()
    empty = np.flatnonzero(labels == "")
    out = []
    for label in sorted(set(labels.tolist()) - {""}):
        rows = np.flatnonzero(labels == label)
        out.append((label, np.union1d(rows, empty) if empty.size else rows))
    if not out and empty.size:
        out.append(("", empty))
    return out


def union_trim(qa: np.ndarray, a_idx: np.ndarray, a_score: np.ndarray, b_idx: np.ndarray, b_score: np.ndarray,
               n_r: int, s1_kept: np.ndarray, trim_s1: int, trim_r: int) -> pd.DataFrame:
    """Union of both search directions with metadata, trimmed. Indices are partition-local.

    ``qa`` are the S1 rows that were queried (row j of ``a_idx``); ``s1_kept`` marks the S1 rows whose pairs we keep.
    Returns s1_local, r_local, score, rank_s1 (rank of r in the S1's list, -1 if absent) and rank_r.
    """
    ka, kb = a_idx.shape[1], b_idx.shape[1]
    va = a_idx >= 0
    a_s1 = np.broadcast_to(qa[:, None], a_idx.shape)[va].astype(np.int64)
    a_r = a_idx[va].astype(np.int64)
    a_rank = np.broadcast_to(np.arange(ka, dtype=np.int16), a_idx.shape)[va]
    a_sc = a_score[va]
    vb = b_idx >= 0
    b_r = np.broadcast_to(np.arange(b_idx.shape[0], dtype=np.int64)[:, None], b_idx.shape)[vb]
    b_s1 = b_idx[vb].astype(np.int64)
    b_rank = np.broadcast_to(np.arange(kb, dtype=np.int16), b_idx.shape)[vb]
    b_sc = b_score[vb]
    keep_b = s1_kept[b_s1]
    b_r, b_s1, b_rank, b_sc = b_r[keep_b], b_s1[keep_b], b_rank[keep_b], b_sc[keep_b]

    key_a = a_s1 * n_r + a_r
    key_b = b_s1 * n_r + b_r
    chosen = np.unique(np.concatenate([key_a[a_rank < trim_s1], key_b[b_rank < trim_r]]))

    def lookup(keys, values, fill):
        out = np.full(chosen.size, fill, dtype=values.dtype)
        if keys.size == 0:
            return out
        order = np.argsort(keys, kind="stable")
        ks = keys[order]
        pos = np.minimum(np.searchsorted(ks, chosen), ks.size - 1)
        hit = ks[pos] == chosen
        out[hit] = values[order][pos[hit]]
        return out

    rank_s1 = lookup(key_a, a_rank, np.int16(-1))
    rank_r = lookup(key_b, b_rank, np.int16(-1))
    score = np.fmax(lookup(key_a, a_sc, np.float32(np.nan)), lookup(key_b, b_sc, np.float32(np.nan)))
    return pd.DataFrame({"s1_local": chosen // n_r, "r_local": chosen % n_r, "score": score.astype(np.float32),
                         "rank_s1": rank_s1, "rank_r": rank_r})


def search_view(indptr: np.ndarray, keys: np.ndarray, s1_rows: np.ndarray, r_rows: np.ndarray, s1_kept: np.ndarray,
                p: SearchParams) -> tuple[pd.DataFrame, int]:
    """One view on one partition: both directions, union and trim. Returns local pairs and the vocabulary size."""
    from . import index, search

    part = index.Partition(indptr, keys, s1_rows, r_rows)
    qa = np.flatnonzero(s1_kept)
    qa_ptr, qa_codes = index.take_rows(part.q_ptr_s1, part.q_s1, qa)
    a_idx, a_sc = search.topk(qa_ptr, qa_codes, part.norm_s1[qa], part.post_r, (part.q_ptr_r, part.q_r),
                              part.norm_r, part.w, p.k_s1, p.seed_cap_r, p.verify_s1)
    b_idx, b_sc = search.topk(part.q_ptr_r, part.q_r, part.norm_r, part.post_s1, (part.q_ptr_s1, part.q_s1),
                              part.norm_s1, part.w, p.k_r, p.seed_cap_s1, p.verify_r)
    return union_trim(qa, a_idx, a_sc, b_idx, b_sc, part.n_r, s1_kept, p.trim_s1, p.trim_r), part.n_codes


def merge_views(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Outer-merge per-view pair frames (s1, r, score_<v>, rank_s1_<v>, rank_r_<v>) and OR their view bits."""
    out = None
    for name, f in frames.items():
        f = f.assign(views=np.int16(VIEW_BITS[name]))
        if out is None:
            out = f
            continue
        out = out.merge(f, on=["s1", "r"], how="outer", suffixes=("", "_other"))
        out["views"] = (out["views"].fillna(0).astype(np.int16) | out.pop("views_other").fillna(0).astype(np.int16))
    for name in frames:
        out[f"score_{name}"] = out[f"score_{name}"].astype(np.float32)
        for c in (f"rank_s1_{name}", f"rank_r_{name}"):
            out[c] = out[c].fillna(-1).astype(np.int16)
    cols = ["s1", "r", "views"] + [f"{m}_{name}" for name in frames for m in ("score", "rank_s1", "rank_r")]
    return out[cols]


def run(cfg: RunConfig) -> dict:
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.parquet as pq

    from ..artifacts import write_table
    from ..eval.splits import in_dev_sample, in_folds
    from ..paths import records_path
    from . import index

    tag = cfg.require_tag()
    tok = SearchParams(cfg.param("k_s1", 40, int), cfg.param("k_r", 8, int), cfg.param("trim_s1", 30, int),
                       cfg.param("trim_r", 2, int), cfg.param("seed_cap_r", 3000, int),
                       cfg.param("seed_cap_s1", 1000, int), cfg.param("verify_s1", 400, int),
                       cfg.param("verify_r", 200, int))
    use_ns = cfg.param("name_short", 1, int) == 1
    ns_k = cfg.param("ns_k", 10, int)
    ns = SearchParams(ns_k, ns_k, cfg.param("ns_trim_s1", 5, int), cfg.param("ns_trim_r", 5, int),
                      tok.seed_cap_r, tok.seed_cap_s1, 200, 200)
    ns_max_tokens = cfg.param("ns_max_addr_tokens", 3, int)
    ns_ngrams = cfg.param("ns_ngrams", 0, int)  # character n-grams of names in the name_short view (0 = off)
    dev_tag = cfg.param("dev_tag")
    indic_dict = cfg.param("indic_dict")  # a models tag holding indic_dict.parquet (learned on train folds 5-19)
    params = {"tok": vars(tok), "name_short": vars(ns) if use_ns else None, "ns_max_addr_tokens": ns_max_tokens,
              "ns_ngrams": ns_ngrams, "indic_dict": indic_dict}

    t0 = time.perf_counter()
    tbl = pq.read_table(records_path(cfg.split), columns=["eid", "source", "country", "name", "address"])
    eid = tbl["eid"].to_numpy()
    source = tbl["source"].to_numpy()
    country = tbl["country"].to_numpy()
    names, addresses = tbl["name"].combine_chunks(), tbl["address"].combine_chunks()
    del tbl
    name_map = None
    if indic_dict:
        from ..paths import artifact_dir
        from .indic import load_name_map
        name_map = load_name_map(artifact_dir("models", indic_dict) / "indic_dict.parquet")
    counts: dict = {}
    indptr, keys = index.record_keys(names, addresses, counts, name_map)
    n_addr = counts["address_tokens"]
    del addresses
    log.info("tokens: %d records, %.1f keys per record, %.0fs", eid.size, keys.size / eid.size, time.perf_counter() - t0)

    s1_mask = source == 1
    s1_query = s1_mask.copy()
    if cfg.split == "train" and cfg.folds:
        s1_query &= in_folds(eid, cfg.folds)
    if cfg.split == "train" and cfg.param("sample") == "dev":
        s1_query &= in_dev_sample(eid)

    parts = partitions(country)
    has_empty_country = sum(r.size for _, r in parts) > eid.size
    frames, report = [], {}
    for label, rows in parts:
        t1 = time.perf_counter()
        s1_rows = rows[s1_mask[rows]]
        r_rows = rows[~s1_mask[rows]]
        if s1_rows.size == 0 or r_rows.size == 0:
            continue
        kept = s1_query[s1_rows]
        views, info = {}, {"s1": int(s1_rows.size), "r": int(r_rows.size), "s1_queried": int(kept.sum())}
        pairs, info["vocab"] = search_view(indptr, keys, s1_rows, r_rows, kept, tok)
        views["tok"] = pairs.assign(s1=eid[s1_rows[pairs["s1_local"].to_numpy()]],
                                    r=eid[r_rows[pairs["r_local"].to_numpy()]])
        if use_ns:
            short = r_rows[n_addr[r_rows] <= ns_max_tokens]
            sub = np.concatenate([s1_rows, short])
            ns_ptr, ns_keys = index.record_keys(pc.take(names, pa.array(sub)),
                                                pa.array([""] * sub.size, type=names.type), name_map=name_map,
                                                name_ngrams=ns_ngrams)
            local_s1 = np.arange(s1_rows.size)
            local_r = np.arange(s1_rows.size, sub.size)
            if short.size:
                pairs_ns, _ = search_view(ns_ptr, ns_keys, local_s1, local_r, kept, ns)
                views["name_short"] = pairs_ns.assign(s1=eid[s1_rows[pairs_ns["s1_local"].to_numpy()]],
                                                      r=eid[short[pairs_ns["r_local"].to_numpy()]])
            info["short_r"] = int(short.size)
        for name, f in views.items():
            views[name] = f.rename(columns={"score": f"score_{name}", "rank_s1": f"rank_s1_{name}",
                                            "rank_r": f"rank_r_{name}"}).drop(columns=["s1_local", "r_local"])
        merged = merge_views(views)
        frames.append(merged)
        info.update({f"pairs_{name}": int(len(f)) for name, f in views.items()})
        info.update({"pairs": int(len(merged)),
                     "s1_without_candidates": int(kept.sum() - merged["s1"].nunique()),
                     "seconds": round(time.perf_counter() - t1, 1)})
        report[label] = info
        log.info("partition %s: %s", label, info)
        del views, merged

    cands = pd.concat(frames, ignore_index=True)
    view_names = [v for v in VIEW_BITS if f"score_{v}" in cands.columns]
    for name in view_names:  # partitions without a view leave NaN: give them the absent-view values
        cands[f"score_{name}"] = cands[f"score_{name}"].astype(np.float32)
        for c in (f"rank_s1_{name}", f"rank_r_{name}"):
            cands[c] = cands[c].fillna(-1).astype(np.int16)
    cands["views"] = cands["views"].astype(np.int16)
    cands = cands[["s1", "r", "views"] + [f"{m}_{v}" for v in view_names for m in ("score", "rank_s1", "rank_r")]]
    if has_empty_country and cands.duplicated(["s1", "r"]).any():  # empty-label records join several partitions
        cands = cands.sort_values("views", ascending=False).drop_duplicates(["s1", "r"]).reset_index(drop=True)
    order = np.lexsort((cands["r"].to_numpy(), cands["s1"].to_numpy()))  # by s1, then r (numpy: fast on 100M rows)
    cands = cands.take(order).reset_index(drop=True)
    meta = {"params": params, "partitions": report}
    write_table(cands, "candidates", tag, cfg.split, command=cfg.command, inputs={"records": cfg.split}, **meta)
    out = {"pairs": int(len(cands)), "s1_with_candidates": int(cands["s1"].nunique()),
           "pairs_per_s1_queried": round(len(cands) / max(int(s1_query.sum()), 1), 2),
           "seconds": round(time.perf_counter() - t0, 1), **meta}
    if dev_tag and cfg.split == "train":
        dev = cands[in_dev_sample(cands["s1"].to_numpy())].reset_index(drop=True)
        write_table(dev, "candidates", dev_tag, "train", command=cfg.command, inputs={"records": "train"},
                    subset="dev sample (ber.eval.splits.in_dev_sample)", **meta)
        out["dev_pairs"] = int(len(dev))
    return out
