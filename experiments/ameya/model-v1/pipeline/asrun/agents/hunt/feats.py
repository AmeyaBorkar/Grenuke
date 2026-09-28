"""Row context features for the hunt (holdout cache): shared by calib.py and rules.py."""
from __future__ import annotations

import os

import numpy as np
import pandas as pd

from base import D, empty_addr, load


def group_rank(key, score, tie=None):
    """0-based rank of each row inside its key group by score descending (ties: lower tie first)."""
    tie = np.zeros(key.size, np.int64) if tie is None else tie
    order = np.lexsort((tie, -score, key))
    k = key[order]
    start = np.r_[True, k[1:] != k[:-1]]
    first = np.maximum.accumulate(np.where(start, np.arange(k.size), 0))
    out = np.empty(key.size, np.int64)
    out[order] = np.arange(k.size) - first
    return out


def build():
    sfx = os.environ.get("HUNT_SUFFIX", "")
    path = os.path.join(D, f"feats_all{sfx}.parquet")
    if os.path.exists(path):
        return pd.read_parquet(path)
    df = load(f"cache_all{sfx}.parquet")
    emp = empty_addr("train", np.unique(np.r_[df.r.to_numpy(), df.s1.to_numpy()]))
    emp = emp[~emp.index.duplicated()]
    df["r_empty"] = emp.reindex(df.r.to_numpy()).fillna(False).to_numpy().astype(bool)
    df["s1_empty"] = emp.reindex(df.s1.to_numpy()).fillna(False).to_numpy().astype(bool)
    s1, r, p = df.s1.to_numpy(), df.r.to_numpy(), df.pc.to_numpy().astype(np.float64)
    cand = df.cand.to_numpy()
    g = df.groupby("r")
    df["n_s1_all"] = g.s1.transform("size").astype(np.int16)  # S1 with p1 >= 0.02 (before the top-2 cut)
    df["psum_all"] = g.pc.transform("sum").astype(np.float32)
    pcc = np.where(cand, p, 0.0)
    df["psum_c"] = pd.Series(pcc).groupby(r).transform("sum").to_numpy().astype(np.float32)
    df["n03_c"] = pd.Series((pcc >= 0.3).astype(np.int8)).groupby(r).transform("sum").to_numpy().astype(np.int8)
    # the best other candidate S1's pc for the record (within the cut)
    rk = group_rank(r, pcc, s1)
    top = pd.Series(np.where(rk == 0, pcc, -1.0)).groupby(r).transform("max").to_numpy()
    sec = pd.Series(np.where(rk == 1, pcc, 0.0)).groupby(r).transform("max").to_numpy()
    df["p_other"] = np.where(rk == 0, sec, top).astype(np.float32)
    df["rank_r"] = rk.astype(np.int8)
    # rank of the pair among its S1's owned candidate pairs (pc descending)
    own = df.own.to_numpy()
    key = np.where(own, s1, -1)
    rs = group_rank(key, p, r)
    df["rank_s1_own"] = np.where(own, rs, -1).astype(np.int16)
    pred = df.pred.to_numpy()
    src = df.src.to_numpy()
    for name, m in (("np_all", pred), ("np_2", pred & (src == 2)), ("np_3", pred & (src == 3))):
        df[name] = pd.Series(m.astype(np.int16)).groupby(s1).transform("sum").to_numpy().astype(np.int16)
    df.to_parquet(path, index=False)
    return df


if __name__ == "__main__":
    d = build()
    print(d.shape, d.dtypes.to_dict())
