"""France expected-F0.5 decision (RESEARCH_v6.md 6.18): the expected-F0.5 prefix per S1 that apply_combo.py uses for
US/India, applied to a model's French stage-3 pc instead of the stage-3 threshold.

    python dp_france.py <model, e.g. v7sq6> <candidates tag> <matches tag> <new matches tag>

- Rows: p1 >= 0.02 and each record's top-2 S1 (the candidate cut), owner = the record's argmax pc, French S1 only.
- q = sigmoid(logit(pc) + 0.2 - 0.3 * [record has >= 4 S1 with p1 >= 0.02]); phantom 0.01; core.expected_f_select.
- The model's rule layer is kept as it is: pairs the rules added (in <model>-s3-ops3a-dpc, not in <model>-s3) stay,
  pairs they dropped stay dropped; the look-alike word swaps (apply_swapsim.is_swapsim) are removed.
- A DP addition is not added when it is a one-word swap to a real word (at least REAL_MIN French S1 names, MIN_LEN
  letters, not a list word) that either resembles the S1's word (the look-alike swap) or sits at the S1's address in
  an op-B position (the op-B look-alike).
- The French part of <matches tag> must be <model>-s3-ops3a-dpc's minus its look-alike swaps (compose.py, then
  apply_swapsim.py). Drops are applied first; an addition is kept only if it is a candidate and its record has no
  other S1 after the drops. Other countries are not changed.

The error agent's valuation (holdout calibration of the pc bands, US/India): +0.00001 to +0.000016 LB on every French
base tried, positive under every valuation; the same DP against the threshold on the US/India holdout: +0.000027.
"""
from __future__ import annotations

import json
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
import post_ops as po  # noqa: E402
from apply_swapsim import is_swapsim  # noqa: E402
from core import expected_f_select, to_q  # noqa: E402
from textlib import load_text  # noqa: E402

from ber.artifacts import read_table, write_table  # noqa: E402
from ber.block.text import fold  # noqa: E402
from ber.paths import artifact_path, records_path, report_path  # noqa: E402

K = 4_000_000_000
SHIFT, CROWD, PHANTOM, P_CAND, TOP_R = 0.2, 0.3, 0.01, 0.02, 2
NORM = {"cie": "compagnie", "ets": "etablissements", "st": "saint", "ste": "sainte", "cte": "comite", "asso": "association"}


def sorted_isin(x: np.ndarray, sorted_set: np.ndarray) -> np.ndarray:
    if not sorted_set.size:
        return np.zeros(len(x), bool)
    j = np.searchsorted(sorted_set, x)
    j[j >= sorted_set.size] = 0
    return sorted_set[j] == x


def candidate_mask(s1, r, p1, p_min, top_r):
    keep = p1 >= p_min
    idx = np.flatnonzero(keep)
    order = idx[np.lexsort((s1[idx], -p1[idx], r[idx]))]
    rs = r[order]
    start = np.ones(rs.size, bool)
    start[1:] = rs[1:] != rs[:-1]
    first = np.maximum.accumulate(np.where(start, np.arange(rs.size), 0))
    keep = np.zeros(p1.size, bool)
    keep[order[np.arange(rs.size) - first < top_r]] = True
    return keep


def argmax_owner(s1, r, p):
    order = np.lexsort((s1, -p, r))
    rs = r[order]
    first = np.ones(rs.size, bool)
    first[1:] = rs[1:] != rs[:-1]
    out = np.zeros(p.size, bool)
    out[order[first]] = True
    return out


def cut_rows(tag: str, fr_s1: np.ndarray) -> pd.DataFrame:
    """The candidate cut of every S1 on the records that have a p1 >= 0.02 row of a French S1, with owners."""
    f = pq.ParquetFile(artifact_path("scores", tag, "test"))
    rs = []
    for i in range(f.num_row_groups):
        t = f.read_row_group(i, columns=["s1", "r", "p1"])
        s1, r, p1 = t["s1"].to_numpy(), t["r"].to_numpy(), t["p1"].to_numpy()
        rs.append(np.unique(r[(p1 >= P_CAND) & sorted_isin(s1, fr_s1)]))
    R = np.unique(np.concatenate(rs))
    parts = []
    for i in range(f.num_row_groups):
        t = f.read_row_group(i, columns=["s1", "r", "p1", "pc"])
        s1, r, p1 = t["s1"].to_numpy(), t["r"].to_numpy(), t["p1"].to_numpy()
        m = (p1 >= P_CAND) & sorted_isin(r, R)
        parts.append(pd.DataFrame({"s1": s1[m], "r": r[m], "p1": p1[m].astype(np.float32),
                                   "pc": t["pc"].to_numpy()[m].astype(np.float64)}))
    s = pd.concat(parts, ignore_index=True)
    s["n_s1_all"] = s.groupby("r").s1.transform("size").astype(np.int16)
    s = s[candidate_mask(s.s1.to_numpy(), s.r.to_numpy(), s.p1.to_numpy(), P_CAND, TOP_R)].reset_index(drop=True)
    s["own"] = argmax_owner(s.s1.to_numpy(), s.r.to_numpy(), s.pc.to_numpy())
    return s[sorted_isin(s.s1.to_numpy(), fr_s1)].reset_index(drop=True)


def fr_keys(tag: str, fr_s1: np.ndarray) -> np.ndarray:
    m = read_table("matches", tag, "test", ["s1", "r"])
    s1, r = m.s1.to_numpy(np.int64), m.r.to_numpy(np.int64)
    f = sorted_isin(s1, fr_s1)
    return np.unique(s1[f] * K + r[f])


def norm_name(s: str) -> str:
    return " ".join(NORM.get(w, w) for w in po.tokens(s))


def main(model: str, cands: str, tag: str, out: str) -> None:
    t = pq.read_table(records_path("test"), columns=["eid", "source", "country", "name"], filters=[("source", "==", 1)])
    t = t.filter(pc.equal(t["country"], "France"))
    fr_s1 = np.sort(t["eid"].to_numpy())
    voc: Counter = Counter()
    for n in fold(t["name"].combine_chunks().fill_null("")).to_numpy(zero_copy_only=False):
        voc.update(set(po.tokens(n)))
    del t

    s = cut_rows(f"ameya-s3-{model}", fr_s1)
    KD = fr_keys(f"ameya-model-{model}-s3-ops3a-dpc", fr_s1)
    KR = fr_keys(f"ameya-model-{model}-s3", fr_s1)
    sk = s.s1.to_numpy(np.int64) * K + s.r.to_numpy(np.int64)
    thr = json.load(open(report_path(f"ameya-model-{model}-s3")))["rule"]["threshold"]
    raw = np.unique(sk[s.own.to_numpy() & (s.pc.to_numpy() > thr)])
    print(f"{model}: French cut rows {len(s)}; stage-3 threshold {thr} reproduced: {raw.size} vs {KR.size} "
          f"({np.setdiff1d(raw, KR).size} / {np.setdiff1d(KR, raw).size} differ)")

    def cont(n: str) -> tuple:
        return tuple(w for w in po.tokens(n) if w not in po.LEG and w not in po.STOP)

    txt = load_text("test", np.r_[KD // K, KD % K])
    flag = np.array([is_swapsim(cont(a), cont(b), voc) for a, b in
                     zip(txt.name.reindex(KD // K).fillna("").to_numpy(), txt.name.reindex(KD % K).fillna("").to_numpy())], bool)
    lk = KD[flag]
    KM = np.setdiff1d(KD, lk)
    radd, rdrop = np.setdiff1d(KD, KR), np.setdiff1d(KR, KD)

    q = to_q(s.pc.to_numpy(), SHIFT - CROWD * (s.n_s1_all.to_numpy() >= 4))
    sel = expected_f_select(s.s1.to_numpy(), q, s.own.to_numpy(), lam=PHANTOM)
    new = np.setdiff1d(np.union1d(np.unique(sk[sel]), radd), np.r_[rdrop, lk])

    a = np.setdiff1d(new, KD)  # the DP's additions: no look-alike or op-B swaps
    if a.size:
        txa = load_text("test", np.r_[a // K, a % K])
        sn, rn = txa.name.reindex(a // K).fillna("").to_numpy(), txa.name.reindex(a % K).fillna("").to_numpy()
        sa, ra = txa.address.reindex(a // K).fillna("").to_numpy(), txa.address.reindex(a % K).fillna("").to_numpy()
        bad = np.zeros(a.size, bool)
        for i in range(a.size):
            kind, pos, added, dropped = po.name_edit(norm_name(sn[i]), norm_name(rn[i]))
            if kind != "swap" or voc.get(added, 0) < po.REAL_MIN or added in po.LIST_A or len(added) < po.MIN_LEN:
                continue
            sim = Indel.normalized_similarity(added, dropped) if added and dropped else 0.0
            same = ra[i].strip() != "" and po.same_address(po.addr_parts(sa[i]), po.addr_parts(ra[i]))
            bad[i] = sim >= po.GARBLE_SIM or (same and pos in po.B_POS)
        new = np.setdiff1d(new, a[bad])
        print(f"DP additions {a.size}: {int(bad.sum())} look-alike or op-B swaps not added")

    m = read_table("matches", tag, "test", ["s1", "r"]).astype("int64")
    mk = m.s1.to_numpy() * K + m.r.to_numpy()
    fr = sorted_isin(m.s1.to_numpy(), fr_s1)
    if not np.array_equal(np.unique(mk[fr]), KM):
        raise SystemExit(f"the French part of {tag} ({int(fr.sum())} pairs) is not {model}-s3-ops3a-dpc minus its "
                         f"look-alike swaps ({KM.size})")
    drops, adds = np.setdiff1d(KM, new), np.setdiff1d(new, KM)
    m2 = m[~np.isin(mk, drops)]
    c = read_table("candidates", cands, "test", ["s1", "r"]).astype("int64")
    ck = np.sort(c.s1.to_numpy() * K + c.r.to_numpy())
    ad = pd.DataFrame({"s1": adds // K, "r": adds % K})
    ad = ad[sorted_isin(adds, ck) & ~ad.r.isin(m2.r).to_numpy()].drop_duplicates("r")
    res = pd.concat([m2, ad], ignore_index=True)
    if res.r.duplicated().any():
        raise SystemExit("a record has two owners")
    write_table(res, "matches", out, "test", command=f"dp_france.py {model} {cands} {tag} {out}")
    print(f"{out}: France look-alikes {lk.size}; DP drops {drops.size}, adds {len(ad)} of {adds.size}; "
          f"pairs {len(m)} -> {len(res)}")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit(__doc__)
    main(*sys.argv[1:5])
