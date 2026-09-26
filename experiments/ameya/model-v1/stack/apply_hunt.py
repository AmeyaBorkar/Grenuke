"""Apply the hunt's holdout-validated rules to a test final matches tag (read-only on work/).

    python apply_hunt.py --matches ameya-model-v7s-s3-ops3a --scores ameya-s3-v7s --cands ameya-cands-v7s-c2a \
        --thr 0.70 --rules acr,cap,nsa@US+India
    A rule without "@" applies to every country; "nsa@US+India" restricts it to S1 of those countries.
    --thr must be the model's decide.py threshold (v7nst 0.675, v7s 0.70: work/matches/<tag>/train.parquet "rule").

Rules (decisions use the stage-3 pc of --scores, the candidate cut p1 >= 0.02 and the record's top-2 S1 by p1, and
the argmax owner of the record inside the cut, exactly as decide.py):
- cap   : an S1 with more than 5 S2, 6 S3 or 11 predicted records keeps its highest-pc ones (generator caps);
          model predictions are trimmed before rule adds (pairs the model did not predict itself).
- nsa   : drop a model prediction (argmax owner, pc in (thr, NSA_HI = 0.75]) whose record has >= 4 S1 with
          p1 >= 0.02 (counted before the top-2 cut).
- rank0 : an S1 with no prediction gets its best owned candidate if pc in (RANK0_LO = 0.6, thr] and no S1 holds the
          record.
- acr   : add an owned, unheld candidate with pc >= 0.1 whose record name is the S1's initials (post_ops.name_edit
          "acr") and whose record address is not empty.
Adds are restricted to the candidate file (--cands) and to records no S1 holds, so there is one owner per record.
Writes OUT/<out>.parquet (s1, r int64; default out = hunted_<matches tag>) and OUT/<out>_changes.csv, where OUT is
$STACK_OUT or <work dir>/stack.
"""
from __future__ import annotations

import argparse
import os
import sys
import time

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

D = os.path.dirname(os.path.abspath(__file__))
sys.path[1:1] = [D, os.path.dirname(D)]  # the stack modules, then model-v1 (common, post_ops)

from ber.artifacts import read_table  # noqa: E402
from ber.paths import artifact_path, records_path, work_dir  # noqa: E402
from common import argmax_owner, candidate_mask  # noqa: E402

OUT = os.environ.get("STACK_OUT") or str(work_dir() / "stack")
K = 4_000_000_000
THR = 0.675
NSA_HI = 0.75
RANK0_LO = 0.6
ALL_RULES = ("cap", "nsa", "rank0", "acr")


def group_rank(key, score, tie):
    order = np.lexsort((tie, -score, key))
    k = key[order]
    start = np.r_[True, k[1:] != k[:-1]]
    first = np.maximum.accumulate(np.where(start, np.arange(k.size), 0))
    out = np.empty(key.size, np.int64)
    out[order] = np.arange(k.size) - first
    return out


def load_scores(tag: str, split: str = "test") -> pd.DataFrame:
    f = pq.ParquetFile(artifact_path("scores", tag, split))
    parts = []
    for g in range(f.num_row_groups):
        t = f.read_row_group(g, columns=["s1", "r", "p1", "pc"])
        t = t.filter(pc.greater_equal(t["p1"], 0.02))
        parts.append(t.to_pandas())
    s = pd.concat(parts, ignore_index=True)
    s1, r = s.s1.to_numpy(), s.r.to_numpy()
    cand = candidate_mask(s1, r, s.p1.to_numpy(), 0.02, 2)
    s["n_s1_all"] = s.groupby("r").s1.transform("size").astype(np.int16)
    s = s[cand].reset_index(drop=True)
    s["own"] = argmax_owner(s.s1.to_numpy(), s.r.to_numpy(), s.pc.to_numpy())
    return s


def s1_country(split: str = "test") -> pd.Series:
    t = pq.read_table(records_path(split), columns=["eid", "source", "country"])
    t = t.filter(pc.equal(t["source"], 1))
    return pd.Series(t["country"].to_numpy(zero_copy_only=False), index=t["eid"].to_numpy())


def acr_pairs(split: str, pairs: pd.DataFrame) -> np.ndarray:
    """Bool per pair: record name = the S1's initials (post_ops.name_edit 'acr') and the record address not empty."""
    from ber.block.text import fold
    from post_ops import name_edit
    ids = pa.array(np.unique(np.r_[pairs.s1.to_numpy(), pairs.r.to_numpy()]))
    f = pq.ParquetFile(records_path(split))
    names, empty = [], []
    for g in range(f.num_row_groups):
        t = f.read_row_group(g, columns=["eid", "name", "address"])
        t = t.filter(pc.is_in(t["eid"], value_set=ids))
        if t.num_rows == 0:
            continue
        e = t["eid"].to_numpy()
        names.append(pd.Series(fold(pc.fill_null(t["name"], "").combine_chunks()).to_numpy(zero_copy_only=False), index=e))
        a = pc.fill_null(t["address"], "").combine_chunks()
        empty.append(pd.Series(pc.equal(pc.utf8_length(pc.utf8_trim_whitespace(a)), 0).to_numpy(zero_copy_only=False),
                               index=e))
    names, empty = pd.concat(names), pd.concat(empty)
    sn = names.reindex(pairs.s1.to_numpy()).fillna("").to_numpy()
    rn = names.reindex(pairs.r.to_numpy()).fillna("").to_numpy()
    short = np.array([len(b) <= 30 for b in rn])  # an acronym record name is short: skip the rest cheaply
    kind = np.array([name_edit(a, b)[0] if k else "" for a, b, k in zip(sn, rn, short)], object)
    return (kind == "acr") & ~empty.reindex(pairs.r.to_numpy()).fillna(True).to_numpy().astype(bool)


def parse_rules(tokens) -> dict:
    """["acr", "nsa@US+India"] -> {"acr": None, "nsa": {"US", "India"}} (None: every country)."""
    out = {}
    for tok in tokens:
        name, _, cs = tok.partition("@")
        assert name in ALL_RULES, name
        out[name] = set(cs.split("+")) if cs else None
    return out


def apply_rules(s: pd.DataFrame, m: pd.DataFrame, cty: pd.Series, rules, countries: str = "",
                cand_ok: np.ndarray | None = None, split: str = "test"):
    """s: the cut rows (s1, r, pc, own, n_s1_all); m: final matches (s1, r). Returns (new matches, change log)."""
    rules = rules if isinstance(rules, dict) else parse_rules(rules)
    glob = set(countries.split(",")) if countries else None
    m = m[["s1", "r"]].astype(np.int64).reset_index(drop=True)
    cand_ok = np.ones(len(s), bool) if cand_ok is None else cand_ok
    s_cty = cty.reindex(s.s1.to_numpy()).to_numpy()
    m_cty = cty.reindex(m.s1.to_numpy()).to_numpy()

    def ok(values, rule):
        o = np.ones(values.size, bool)
        for allowed in (glob, rules[rule]):
            if allowed:
                o &= np.isin(values, list(allowed))
        return o

    mk = m.s1.to_numpy() * K + m.r.to_numpy()
    sk = s.s1.to_numpy() * K + s.r.to_numpy()
    in_m = np.isin(sk, mk)
    pcs = pd.Series(s.pc.to_numpy(), index=sk)
    m["pc"] = pcs.reindex(mk).to_numpy()  # NaN for pairs outside the cut (rule adds): never trimmed first
    m["src"] = m.r // 1_000_000_000
    changes = []
    drop = np.zeros(len(m), bool)
    if "cap" in rules:
        # trim model predictions first (argmax owner, pc > thr): rule adds (low pc, 97-99.8% true edits) are kept
        model = np.isin(mk, sk[s.own.to_numpy() & (s.pc.to_numpy() > THR)])
        key_pc = np.where(model, m.pc.fillna(2.0).to_numpy(), 2.0)
        m_ok = ok(m_cty, "cap")
        rk = group_rank(m.s1.to_numpy() * 4 + m.src.to_numpy(), key_pc, m.r.to_numpy())
        over = m_ok & (((m.src == 2).to_numpy() & (rk >= 5)) | ((m.src == 3).to_numpy() & (rk >= 6)))
        rk2 = group_rank(np.where(over, -1, m.s1.to_numpy()), key_pc, m.r.to_numpy())
        over |= m_ok & ~over & (rk2 >= 11)
        changes.append(m.loc[over, ["s1", "r", "pc"]].assign(rule="cap", action="drop"))
        drop |= over
    if "nsa" in rules:
        bad = s.own.to_numpy() & in_m & (s.pc.to_numpy() > THR) & (s.pc.to_numpy() <= NSA_HI) & \
            (s.n_s1_all.to_numpy() >= 4) & ok(s_cty, "nsa")
        x = np.isin(mk, sk[bad]) & ~drop
        changes.append(m.loc[x, ["s1", "r", "pc"]].assign(rule="nsa", action="drop"))
        drop |= x
    rec_free = ~np.isin(s.r.to_numpy(), m.r.to_numpy())
    adds = []
    if "rank0" in rules:
        has = np.isin(s.s1.to_numpy(), m.s1.to_numpy())
        own = s.own.to_numpy()
        idx = np.flatnonzero(own)
        rk = np.full(len(s), -1)
        rk[idx] = group_rank(s.s1.to_numpy()[idx], s.pc.to_numpy()[idx].astype(np.float64), s.r.to_numpy()[idx])
        a = (rk == 0) & ~has & (s.pc.to_numpy() > RANK0_LO) & (s.pc.to_numpy() <= THR) & rec_free & cand_ok & \
            ok(s_cty, "rank0")
        adds.append(s.loc[a, ["s1", "r", "pc"]].assign(rule="rank0", action="add"))
    if "acr" in rules:
        c = s.own.to_numpy() & ~in_m & rec_free & cand_ok & ok(s_cty, "acr") & (s.pc.to_numpy() >= 0.1)
        sub = s.loc[c, ["s1", "r", "pc"]].reset_index(drop=True)
        if len(sub):
            ac = acr_pairs(split, sub)
            adds.append(sub.loc[ac].assign(rule="acr", action="add"))
    add = pd.concat(adds, ignore_index=True) if adds else pd.DataFrame(
        {"s1": np.empty(0, np.int64), "r": np.empty(0, np.int64), "pc": np.empty(0, np.float32),
         "rule": np.empty(0, object), "action": np.empty(0, object)})
    add = add.sort_values("pc", ascending=False).drop_duplicates("r")  # one owner per record
    assert not np.isin(add.r.to_numpy(), m.r.to_numpy()).any()
    out = pd.concat([m.loc[~drop, ["s1", "r"]], add[["s1", "r"]]], ignore_index=True).astype(np.int64)
    assert not out.r.duplicated().any(), "one owner per record"
    ch = pd.concat([c for c in changes + [add] if len(c)], ignore_index=True) if any(
        len(c) for c in changes + [add]) else add.copy()
    ch["country"] = cty.reindex(ch.s1.to_numpy()).to_numpy()
    return out, ch


def main() -> int:
    global THR, NSA_HI, RANK0_LO
    ap = argparse.ArgumentParser()
    ap.add_argument("--matches", required=True, help="test final matches tag")
    ap.add_argument("--scores", required=True, help="its stage-3 scores tag")
    ap.add_argument("--cands", default="", help="candidate tag of the package (adds must be inside it)")
    ap.add_argument("--rules", default="acr,cap,nsa@US+India", help="comma list; rule@C1+C2 restricts a rule")
    ap.add_argument("--countries", default="", help="apply only to S1 of these countries (default: all)")
    ap.add_argument("--split", default="test")
    ap.add_argument("--thr", type=float, required=True, help="the model's decide.py threshold (v7nst 0.675, v7s 0.70)")
    ap.add_argument("--nsa-hi", type=float, default=NSA_HI)
    ap.add_argument("--rank0-lo", type=float, default=RANK0_LO)
    ap.add_argument("--out", default="", help="output stem in OUT (default hunted_<matches>)")
    args = ap.parse_args()
    THR, NSA_HI, RANK0_LO = args.thr, args.nsa_hi, args.rank0_lo
    t0 = time.time()
    rules = parse_rules([x for x in args.rules.split(",") if x])
    cty = s1_country(args.split)
    m = read_table("matches", args.matches, args.split)[["s1", "r"]].astype(np.int64)
    s = load_scores(args.scores, args.split)
    print(f"{args.matches}: {len(m)} pairs; cut rows {len(s)}; thr {THR}; rules {rules} ({time.time() - t0:.0f}s)",
          flush=True)
    sk = s.s1.to_numpy() * K + s.r.to_numpy()
    cand_ok = np.ones(len(s), bool)
    if args.cands:
        ck = read_table("candidates", args.cands, args.split, ["s1", "r"])
        ck = np.sort(ck.s1.to_numpy() * K + ck.r.to_numpy())
        j = np.searchsorted(ck, sk)
        j[j >= ck.size] = 0
        cand_ok = ck[j] == sk
        mk = np.sort(m.s1.to_numpy() * K + m.r.to_numpy())
        jm = np.searchsorted(ck, mk)
        jm[jm >= ck.size] = 0
        print(f"cut rows inside {args.cands}: {cand_ok.mean():.6f}; final matches inside it: {(ck[jm] == mk).mean():.6f}",
              flush=True)
        del ck, mk
    out, ch = apply_rules(s, m, cty, rules, args.countries, cand_ok, args.split)
    os.makedirs(OUT, exist_ok=True)
    base = os.path.join(OUT, args.out or f"hunted_{args.matches}")
    out.to_parquet(base + ".parquet", index=False)
    ch.to_csv(base + "_changes.csv", index=False)
    n_s1 = cty.value_counts()
    print(f"wrote {base}.parquet: {len(out)} pairs ({len(out) - len(m):+d})")
    if len(ch):
        t = ch.groupby(["rule", "action", "country"]).size().unstack(fill_value=0)
        print(t.to_string())
        print("per 1000 S1:\n", (t / n_s1.reindex(t.columns).to_numpy() * 1000).round(3).to_string())
    print(f"done {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
