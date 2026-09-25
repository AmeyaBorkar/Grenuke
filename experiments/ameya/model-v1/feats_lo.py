"""Per-token distractor encoding (gate G3, FINAL_PLAN section 4.4 v1) for the model-v1 experiments.

    python experiments/ameya/model-v1/feats_lo.py --feats ameya-fx1 --split train
    python experiments/ameya/model-v1/feats_lo.py --feats ameya-fx1 --split test

Look-alikes add or swap one business-changing name word ("Exports", "Holdings", another first name) while true pairs
add noise words ("Center", "Services"). For every candidate pair this takes the name tokens left without a partner
after exact + typo-tolerant matching (up to K per side, highest IDF first) and looks up each token's log-odds of a
true match when it is extra on the record side, or missing from it:
- counted on "close" training pairs only (shared address words and at least one shared name token), where the
  word decides; smoothed toward the base rate (A_PRIOR pseudo-pairs);
- out of fold (C2): training pairs of stacking group g use counts from the other two groups; the holdout and test
  use every training fold. Tokens are keyed by their string, so test (France included) reuses train's statistics and
  unseen tokens get 0.
Features (group ``lo``): min and sum of the log-odds over the extra record tokens and over the missing S1 tokens,
and how many of them are below -1 (NaN min when a side has no such token).
Writes work/features/<feats>-lo/<split>.parquet, row-aligned with <feats>-str (same row groups);
the full-train tables go to work/models/<feats>/token_lo.parquet for the test run.
"""
from __future__ import annotations

import argparse
import logging
import os
import time

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from numba import get_num_threads, get_thread_id, njit, prange

from ber.artifacts import provenance
from ber.eval.splits import oof_group
from ber.paths import artifact_dir, artifact_path
from feats import _lev, load_records

log = logging.getLogger("feats_lo")
K = 3
A_PRIOR = 20.0
CLOSE_WORD_JAC = 0.3


@njit(parallel=True, cache=True)
def _unmatched(ptr, codes, wt, off, buf, ii, jj, scratch, xr, xs):
    """Up to K unmatched token codes per side (highest weight first; -1 = none) after exact + typo matching."""
    n = ii.size
    kk = xr.shape[1]
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
        # highest-weight unmatched tokens first (K small: repeated selection)
        taken = np.int64(0)
        for slot in range(kk):
            best = -1
            bw = -1.0
            for q in range(lb):
                if (mb >> q) & 1 or (taken >> q) & 1:
                    continue
                if wt[b0 + q] > bw:
                    bw = wt[b0 + q]
                    best = q
            if best < 0:
                break
            taken |= np.int64(1) << best
            xr[k, slot] = codes[b0 + best]
        taken = np.int64(0)
        for slot in range(kk):
            best = -1
            bw = -1.0
            for p in range(la):
                if (ma >> p) & 1 or (taken >> p) & 1:
                    continue
                if wt[a0 + p] > bw:
                    bw = wt[a0 + p]
                    best = p
            if best < 0:
                break
            taken |= np.int64(1) << best
            xs[k, slot] = codes[a0 + best]


def unmatched_tokens(rec: dict, s1: np.ndarray, r: np.ndarray, chunk: int = 4_000_000) -> tuple[np.ndarray, np.ndarray]:
    nm = rec["name"]
    n = s1.size
    xr = np.full((n, K), -1, np.int32)
    xs = np.full((n, K), -1, np.int32)
    scratch = np.empty((get_num_threads(), 2, 64), np.int32)
    for a in range(0, n, chunk):
        b = min(a + chunk, n)
        ii = rec["row_of"].get_indexer(s1[a:b]).astype(np.int64)
        jj = rec["row_of"].get_indexer(r[a:b]).astype(np.int64)
        _unmatched(nm["ptr"], nm["codes"], nm["wt"], nm["off"], nm["buf"], ii, jj, scratch, xr[a:b], xs[a:b])
    return xr, xs


def _counts(codes: np.ndarray, y: np.ndarray, n_codes: int) -> tuple[np.ndarray, np.ndarray]:
    """Per token: pairs where it appears in ``codes`` (rows x K, -1 = empty) and how many of them are true."""
    valid = codes >= 0
    rows = np.nonzero(valid)[0]
    c = codes[valid]
    return (np.bincount(c, minlength=n_codes).astype(np.float64),
            np.bincount(c, weights=y[rows].astype(np.float64), minlength=n_codes))


def _log_odds(n: np.ndarray, n1: np.ndarray, prior: float) -> np.ndarray:
    lo = np.log((n1 + A_PRIOR * prior) / (n - n1 + A_PRIOR * (1 - prior))) - np.log(prior / (1 - prior))
    return lo.astype(np.float32)


@njit(parallel=True, cache=True)
def _summarize(codes, table, which, out):
    """min, sum and count(< -1) of table[which[k], code] over the valid codes of each row."""
    for k in prange(codes.shape[0]):
        mn = np.inf
        sm = 0.0
        low = 0
        cnt = 0
        for j in range(codes.shape[1]):
            c = codes[k, j]
            if c < 0:
                continue
            v = table[which[k], c]
            cnt += 1
            sm += v
            if v < mn:
                mn = v
            if v < -1.0:
                low += 1
        out[0, k] = mn if cnt > 0 else np.nan
        out[1, k] = sm
        out[2, k] = low


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--feats", default="ameya-fx1")
    ap.add_argument("--split", required=True, choices=["train", "test"])
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    command = f"python experiments/ameya/model-v1/feats_lo.py --feats {args.feats} --split {args.split}"
    t0 = time.perf_counter()
    model_dir = artifact_dir("models", args.feats)
    rec, _ = load_records(args.split, pd.read_parquet(model_dir / "indic_dict.parquet"), strings=False)
    fs = pq.ParquetFile(artifact_path("features", f"{args.feats}-str", args.split))
    cols = ["s1", "r"] + (["fold", "y", "word__jac_w", "name__fz_inter"] if args.split == "train" else [])
    keys = fs.read(columns=cols).to_pandas()
    s1, r = keys["s1"].to_numpy(), keys["r"].to_numpy()
    xr, xs = unmatched_tokens(rec, s1, r)
    vocab = rec["name"]["dict"].to_numpy(zero_copy_only=False)
    n_codes = len(vocab)
    log.info("%s: unmatched tokens for %d pairs (%.0fs)", args.split, s1.size, time.perf_counter() - t0)

    # tables[g] for g = 0, 1, 2 (training pairs of group g), 3 (holdout / test): lo per token code
    if args.split == "train":
        y = keys["y"].to_numpy()
        grp = oof_group(s1)
        close = (grp >= 0) & (keys["word__jac_w"].to_numpy() >= CLOSE_WORD_JAC) & (keys["name__fz_inter"].to_numpy() >= 1)
        prior = float(y[close].mean())
        per = {}
        for side, codes in (("x", xr), ("m", xs)):
            parts = [_counts(codes[close & (grp == g)], y[close & (grp == g)], n_codes) for g in range(3)]
            n_all = sum(p[0] for p in parts)
            n1_all = sum(p[1] for p in parts)
            per[side] = np.stack([_log_odds(n_all - parts[g][0], n1_all - parts[g][1], prior) for g in range(3)]
                                 + [_log_odds(n_all, n1_all, prior)])
            if side == "x":
                support = n_all
        which = np.where(grp >= 0, grp, 3).astype(np.int64)
        table = pd.DataFrame({"token": vocab, "lo_extra": per["x"][3], "lo_missing": per["m"][3], "n": support})
        table = table[table["n"] > 0]
        table.to_parquet(model_dir / "token_lo.parquet")
        top = table[table["n"] >= 200].sort_values("lo_extra")
        log.info("close pairs %d, prior %.3f; most distractor-like extra words: %s", int(close.sum()), prior,
                 ", ".join(f"{t} {v:.1f}" for t, v in zip(top["token"].head(25), top["lo_extra"].head(25))))
        log.info("most benign extra words: %s",
                 ", ".join(f"{t} {v:.1f}" for t, v in zip(top["token"].tail(15), top["lo_extra"].tail(15))))
    else:
        table = pd.read_parquet(model_dir / "token_lo.parquet")
        idx = pd.Index(table["token"]).get_indexer(vocab)
        per = {}
        for side, col in (("x", "lo_extra"), ("m", "lo_missing")):
            v = np.zeros(n_codes, np.float32)
            v[idx >= 0] = table[col].to_numpy(np.float32)[idx[idx >= 0]]
            per[side] = v[None, :]
        which = np.zeros(s1.size, np.int64)

    out: dict[str, np.ndarray] = {}
    for side, codes, name in (("x", xr, "extra_r"), ("m", xs, "missing_s1")):
        o = np.zeros((3, s1.size), np.float32)
        _summarize(codes, per[side], which, o)
        out[f"lo__{name}_min"], out[f"lo__{name}_sum"], out[f"lo__{name}_nlow"] = o[0], o[1], o[2]
    df = pd.DataFrame(out)

    path = artifact_path("features", f"{args.feats}-lo", args.split)
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = provenance(command, {"features": f"{args.feats}-str"}, split=args.split, rows=len(df), kind="features",
                      tag=f"{args.feats}-lo")
    schema = pa.Schema.from_pandas(df, preserve_index=False).with_metadata({b"ber": __import__("json").dumps(meta).encode()})
    w = pq.ParquetWriter(str(path) + ".tmp", schema, compression="zstd")
    start = 0
    for g in range(fs.num_row_groups):
        n = fs.metadata.row_group(g).num_rows
        w.write_table(pa.Table.from_pandas(df.iloc[start:start + n], preserve_index=False), row_group_size=n)
        start += n
    w.close()
    os.replace(str(path) + ".tmp", path)
    log.info("done: %s (%d columns) in %.0fs", path, df.shape[1], time.perf_counter() - t0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
