"""Shared loaders and evaluation for the error hunt (holdout of train, v7nst stage-3)."""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from ber.eval.gates import compare
from ber.eval.splits import is_holdout, splitmix64
from ber.paths import records_path
from ber.records import load_truth

D = os.path.dirname(os.path.abspath(__file__))
K = 4_000_000_000
THR = 0.675


def load(cache="cache_train.parquet"):
    df = pd.read_parquet(os.path.join(D, cache))
    df["src"] = (df.r.to_numpy() // 1_000_000_000).astype(np.int8)
    return df


def universe_and_truth():
    t = pq.read_table(records_path("train"), columns=["eid", "source", "country"])
    t = t.filter(pc.equal(t["source"], 1))
    eid = t["eid"].to_numpy()
    cty = pd.Series(t["country"].to_numpy(zero_copy_only=False), index=eid)
    uni = np.sort(eid[is_holdout(eid)])
    truth = load_truth()
    th = truth[np.isin(truth.s1.to_numpy(), uni)].reset_index(drop=True)
    return uni, cty.reindex(uni), th


def empty_addr(split: str, ids: np.ndarray | None = None) -> pd.Series:
    """eid -> address empty (after trimming)."""
    f = pq.ParquetFile(records_path(split))
    out = []
    for g in range(f.num_row_groups):
        t = f.read_row_group(g, columns=["eid", "address"])
        if ids is not None:
            t = t.filter(pc.is_in(t["eid"], value_set=pa.array(ids)))
        a = t["address"]
        e = pc.or_(pc.is_null(a), pc.equal(pc.utf8_length(pc.utf8_trim_whitespace(a)), 0))
        out.append(pd.Series(e.to_numpy(zero_copy_only=False), index=t["eid"].to_numpy()))
    return pd.concat(out)


class Eval:
    """Per-entity F0.5 over the holdout universe from a bool mask over the cache rows (predicted pairs)."""

    def __init__(self, df, uni, th):
        self.uni = uni
        self.n_true = np.bincount(np.searchsorted(uni, th.s1.to_numpy()), minlength=uni.size).astype(np.float64)
        self.in_u = df.hold.to_numpy()
        self.idx = np.searchsorted(uni, df.s1.to_numpy()[self.in_u])
        self.hit = df.y.to_numpy()[self.in_u].astype(np.float64)
        h = splitmix64(uni) % np.uint64(2)
        self.half = h.astype(np.int8)  # 0 = A, 1 = B

    def per_entity(self, mask):
        m = mask[self.in_u]
        n_pred = np.bincount(self.idx[m], minlength=self.uni.size)
        n_hit = np.bincount(self.idx[m], weights=self.hit[m], minlength=self.uni.size)
        den = 0.25 * self.n_true + n_pred
        return np.where(den > 0, 1.25 * n_hit / np.where(den > 0, den, 1.0), 1.0)

    def score(self, mask):
        return float(self.per_entity(mask).mean())

    def delta(self, base, new):
        """(full, A, B) mean per-entity deltas (A/B are means within each half)."""
        d = self.per_entity(new) - self.per_entity(base)
        return float(d.mean()), float(d[self.half == 0].mean()), float(d[self.half == 1].mean())


def gate(df, uni, th, base_mask, new_mask, n_boot=1000):
    """ber.eval.gates.compare on full holdout and on the two halves (splitmix64(s1) % 2)."""
    s1, r = df.s1.to_numpy(), df.r.to_numpy()
    pb = pd.DataFrame({"s1": s1[base_mask], "r": r[base_mask]})
    pn = pd.DataFrame({"s1": s1[new_mask], "r": r[new_mask]})
    h = (splitmix64(uni) % np.uint64(2)).astype(np.int8)
    out = {}
    for name, u in (("full", uni), ("A", uni[h == 0]), ("B", uni[h == 1])):
        g = compare(pb, pn, th, u, n_boot=n_boot)
        out[name] = {k: g[k] for k in ("delta", "ci_low", "ci_high", "p_better", "base_f05", "new_f05", "n")}
    return out


def fmt_gate(g):
    return " | ".join(f"{k} {v['delta']:+.6f} [{v['ci_low']:+.6f}, {v['ci_high']:+.6f}]" for k, v in g.items())


def text_for(split: str, ids: np.ndarray) -> pd.DataFrame:
    """eid -> raw name/address, folded name, robust address parts, empty address (row-group-wise, low memory)."""
    from ber.block.text import fold
    from post_ops import addr_parts
    ids = np.unique(np.asarray(ids, np.int64))
    f = pq.ParquetFile(records_path(split))
    out = []
    va = pa.array(ids)
    for g in range(f.num_row_groups):
        t = f.read_row_group(g, columns=["eid", "name", "address"])
        t = t.filter(pc.is_in(t["eid"], value_set=va))
        if t.num_rows == 0:
            continue
        name = t["name"].combine_chunks()
        addr = t["address"].combine_chunks()
        fa = fold(pc.fill_null(addr, "")).to_numpy(zero_copy_only=False)
        out.append(pd.DataFrame({
            "eid": t["eid"].to_numpy(),
            "name": name.to_numpy(zero_copy_only=False),
            "address": pc.fill_null(addr, "").to_numpy(zero_copy_only=False),
            "fname": fold(pc.fill_null(name, "")).to_numpy(zero_copy_only=False),
            "parts": [addr_parts(a or "") for a in fa],
            "aempty": pc.equal(pc.utf8_length(pc.utf8_trim_whitespace(pc.fill_null(addr, ""))), 0).to_numpy(
                zero_copy_only=False),
        }))
    return pd.concat(out, ignore_index=True).set_index("eid")


def pair_text_feats(pairs: pd.DataFrame, txt: pd.DataFrame) -> pd.DataFrame:
    """name kind (post_ops.name_edit) and same address (post_ops.same_address) per (s1, r)."""
    from post_ops import name_edit, same_address
    sn = txt.fname.reindex(pairs.s1.to_numpy()).to_numpy()
    rn = txt.fname.reindex(pairs.r.to_numpy()).to_numpy()
    sp = txt.parts.reindex(pairs.s1.to_numpy()).to_numpy()
    rp = txt.parts.reindex(pairs.r.to_numpy()).to_numpy()
    ed = [name_edit(a or "", b or "") for a, b in zip(sn, rn)]
    same = [same_address(a, b) if isinstance(a, tuple) and isinstance(b, tuple) else False for a, b in zip(sp, rp)]
    return pairs.assign(kind=[e[0] for e in ed], npos=[e[1] for e in ed], added=[e[2] for e in ed],
                        dropped=[e[3] for e in ed], same_addr=same)
