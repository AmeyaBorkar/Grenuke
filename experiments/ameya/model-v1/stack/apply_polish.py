"""Label-validated polish of a test matches tag, for countries without training labels (France).

    python apply_polish.py [matches_tag] [--cands TAG] [--scores TAG] [--rules copy]      (default rules: copy)

Rules (REPORT.md has the numbers):
- copy (recommended): add an unpredicted candidate pair when the names are equal up to legal forms, stop words
  ("&"/"et"/"and"), word order and the abbreviations Cie/Compagnie, Ets/Etablissements, St/Saint, Ste/Sainte; the
  address is the same (post_ops.same_address, and every street word of the shorter street matched up to a typo)
  with the same multiset of address numbers; the legal form is equal,
  dropped or added (not changed); the S1 is the record's best-scoring candidate S1 (pc); no S1 holds the record;
  no other candidate S1 of the record passes the same test; the cities do not mismatch (rule city's test).
- city (optional, not validated by labels): drop a predicted pair when the S1 and the record both name a city of the
  country's S1 city vocabulary (data-driven: frequent digit-free comma components of the country's S1 addresses,
  minus regions; sub-areas folded into their city: Lomme/Hellemmes -> Lille, Le Clion -> Pornic) and the two city
  sets are disjoint. "city_acr" drops only such pairs that are acronym records (the acr_join additions).
Writes <out-dir>/polished_<tag>.parquet (s1, r) and <out-dir>/changes_<tag>.parquet (s1, r, action, rule, country);
<out-dir> defaults to $STACK_OUT or <work dir>/stack. Countries with training labels are never changed. Peak memory
about 2 GB.
"""
from __future__ import annotations

import argparse
import logging
import os
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

D = Path(__file__).resolve().parent
sys.path[1:1] = [str(D), str(D.parent)]  # the stack modules, then model-v1 (common, post_ops)
from abbrlib import classify_names, tokens  # noqa: E402
from citylib import alone_counts, build_vocab, city_table, make_city_id, mismatch, s1_component_counts  # noqa: E402
from textlib import load_text  # noqa: E402

from ber.artifacts import exists, read_table  # noqa: E402
from ber.paths import artifact_path, records_path, work_dir  # noqa: E402
from common import argmax_owner  # noqa: E402
from post_ops import LEG, _close_word, addr_parts, name_edit, same_address  # noqa: E402

log = logging.getLogger("polish")
K = 4_000_000_000


def derive(tag: str, kind: str) -> str:
    """ameya-model-<X>-s3-ops3a -> ameya-cands-<X>-c2a / ameya-s3-<X>. Stops when that tag does not exist: adds
    must come from the submission's own candidate set, so never fall back to another model's tags."""
    m = re.search(r"ameya-model-(.+?)-s3", tag)
    if m:
        cand = f"ameya-cands-{m.group(1)}-c2a" if kind == "candidates" else f"ameya-s3-{m.group(1)}"
        if exists(kind, cand, "test"):
            return cand
    raise SystemExit(f"cannot derive the {kind} tag from {tag}: pass --{'cands' if kind == 'candidates' else 'scores'}")


def strict_street(a: str, b: str) -> bool:
    """Same first house number and every street word of the shorter street matched up to a typo (French streets
    share first names: "18 rue jean moulin" vs "18 allee jean anouilh" passes post_ops.same_address, not this)."""
    (na, sa), (nb, sb) = addr_parts(a or ""), addr_parts(b or "")
    if not (na and na == nb and sa and sb):
        return False
    small, big = (sa, sb) if len(sa) <= len(sb) else (sb, sa)
    return all(any(_close_word(x, y) for y in big) for x in small)


def legrel(a: str, b: str) -> str:
    la = sorted(w for w in tokens(a or "") if w in LEG)
    lb = sorted(w for w in tokens(b or "") if w in LEG)
    return "eq" if la == lb else "r_none" if not lb else "s_none" if not la else "changed"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("matches", nargs="?", default="ameya-model-v7nst-s3-ops3a",
                    help="a test matches tag, or a .parquet file (s1, r) such as a hunted_<tag>.parquet from the error analysis")
    ap.add_argument("--cands", default="", help="candidate tag (default: derived from the matches tag)")
    ap.add_argument("--scores", default="", help="stage-3 scores tag (default: derived from the matches tag)")
    ap.add_argument("--rules", default="copy", help="comma list of: copy, city, city_acr")
    ap.add_argument("--out-dir", default=os.environ.get("STACK_OUT") or str(work_dir() / "stack"))
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    t0 = time.time()
    rules = set(args.rules.split(","))
    is_file = args.matches.endswith(".parquet")
    name = Path(args.matches).stem if is_file else args.matches
    cands_tag = args.cands or derive(name, "candidates")
    scores_tag = args.scores or derive(name, "scores")
    log.info("matches %s, candidates %s, scores %s, rules %s", args.matches, cands_tag, scores_tag, sorted(rules))

    labelled = set(pc.unique(pq.read_table(records_path("train"), columns=["country"])["country"]).to_pylist())
    rec = pq.read_table(records_path("test"), columns=["eid", "source", "country"]).to_pandas()
    targets = set(rec.country.unique()) - labelled
    tgt_rec = rec.eid[rec.country.isin(targets)].to_numpy()
    s1_cty = pd.Series(rec.country[rec.source == 1].to_numpy(), index=rec.eid[rec.source == 1].to_numpy())
    del rec
    log.info("countries without training labels: %s", sorted(targets))

    m = pd.read_parquet(args.matches, columns=["s1", "r"]) if is_file else read_table("matches", args.matches, "test", ["s1", "r"])
    m = m.astype({"s1": "int64", "r": "int64"})
    n_in = len(m)
    changes = []

    cnt, co, n = s1_component_counts("test", countries=targets)
    cnt = {c: cnt[c] for c in targets if c in cnt}
    co = {c: co[c] for c in targets if c in co}
    n = {c: n[c] for c in targets if c in n}
    v0 = build_vocab(cnt, co, n)
    vocab = build_vocab(cnt, co, n, alone=alone_counts("test", {c: v0[c][1] for c in v0}))
    cid = make_city_id(vocab)
    for c in vocab:
        log.info("%s: %d cities %s; regions %s", c, len(vocab[c][0]), sorted(vocab[c][0])[:20], sorted(vocab[c][1]))

    if rules & {"city", "city_acr"}:
        mt = m[m.s1.isin(tgt_rec).to_numpy()]
        ct = city_table("test", np.r_[mt.s1.to_numpy(), mt.r.to_numpy()], vocab, cid).set_index("eid")
        cs = ct.reindex(mt.s1.to_numpy()).fillna(-1).to_numpy(np.int32)
        cr = ct.reindex(mt.r.to_numpy()).fillna(-1).to_numpy(np.int32)
        _, mis = mismatch(cs, cr)
        drop = mt[mis]
        if "city" not in rules:  # city_acr: only acronym-named records
            txt = load_text("test", np.r_[drop.s1.to_numpy(), drop.r.to_numpy()])
            acr = np.array([name_edit(a or "", b or "")[0] == "acr" for a, b in
                            zip(txt.name.reindex(drop.s1).to_numpy(), txt.name.reindex(drop.r).to_numpy())], bool)
            drop = drop[acr]
        rule = "city" if "city" in rules else "city_acr"
        changes.append(drop.assign(action="drop", rule=rule))
        m = m[~np.isin(m.s1.to_numpy() * K + m.r.to_numpy(), drop.s1.to_numpy() * K + drop.r.to_numpy())]
        log.info("%s: dropped %d predicted pairs (%d S1)", rule, len(drop), drop.s1.nunique())

    if "copy" in rules:
        c = read_table("candidates", cands_tag, "test", ["s1", "r"])
        c = c[c.r.isin(tgt_rec).to_numpy()].reset_index(drop=True)
        f = pq.ParquetFile(artifact_path("scores", scores_tag, "test"))
        vs = pa.array(np.unique(c.r.to_numpy()))
        parts = []
        for g in range(f.num_row_groups):
            t = f.read_row_group(g, columns=["s1", "r", "pc"])
            parts.append(t.filter(pc.is_in(t["r"], value_set=vs)))
        s = pa.concat_tables(parts).to_pandas()
        del parts
        c = c.merge(s, on=["s1", "r"], how="left")
        del s
        c["pc"] = c.pc.fillna(0.0)
        c["own"] = argmax_owner(c.s1.to_numpy(), c.r.to_numpy(), c.pc.to_numpy())
        mk = m.s1.to_numpy() * K + m.r.to_numpy()
        u = c[~np.isin(c.s1.to_numpy() * K + c.r.to_numpy(), mk) & ~c.r.isin(m.r).to_numpy()
              & c.s1.isin(s1_cty.index[s1_cty.isin(targets)]).to_numpy()].reset_index(drop=True)
        del c
        txt = load_text("test", np.r_[u.s1.to_numpy(), u.r.to_numpy()])
        ns, nr = txt.name.reindex(u.s1).to_numpy(), txt.name.reindex(u.r).to_numpy()
        a_s, a_r = txt.address.reindex(u.s1).to_numpy(), txt.address.reindex(u.r).to_numpy()
        u["nk"] = classify_names(ns, nr)
        k = (u.nk != "").to_numpy()
        u["same_addr"] = [same_address(addr_parts(a or ""), addr_parts(b or "")) and strict_street(a, b) if kk
                          else False for a, b, kk in zip(a_s, a_r, k)]
        u["nums_eq"] = [sorted(re.findall(r"[0-9]+", a or "")) == sorted(re.findall(r"[0-9]+", b or "")) if kk
                        else False for a, b, kk in zip(a_s, a_r, k)]
        u["leg"] = [legrel(a, b) if kk else "" for a, b, kk in zip(ns, nr, k)]
        ok = (u.nk != "") & u.same_addr & u.nums_eq & u.leg.isin(["eq", "r_none", "s_none"])
        n_ok_r = ok.groupby(u.r).transform("sum")  # another candidate S1 of the record passes too -> ambiguous, skip
        add = u[ok & u.own & (n_ok_r == 1)]
        ct = city_table("test", np.r_[add.s1.to_numpy(), add.r.to_numpy()], vocab, cid).set_index("eid")
        _, mis = mismatch(ct.reindex(add.s1.to_numpy()).fillna(-1).to_numpy(np.int32),
                          ct.reindex(add.r.to_numpy()).fillna(-1).to_numpy(np.int32))
        add = add[~mis].drop_duplicates("r").sort_values("pc", ascending=False)
        # generator caps (hunt rule "cap"): an S1 has at most 5 S2, 6 S3 and 11 records; skip adds that exceed them
        n_src = m.assign(src=m.r // 1_000_000_000).groupby(["s1", "src"]).size().to_dict()
        keep = []
        for s1_, r_ in zip(add.s1.to_numpy(), add.r.to_numpy()):
            src = int(r_ // 1_000_000_000)
            n2, n3 = n_src.get((s1_, 2), 0), n_src.get((s1_, 3), 0)
            fits = (n2 + (src == 2) <= 5) and (n3 + (src == 3) <= 6) and (n2 + n3 + 1 <= 11)
            keep.append(fits)
            if fits:
                n_src[(s1_, src)] = n_src.get((s1_, src), 0) + 1
        n_cap = len(add) - int(np.sum(keep))
        add = add[np.array(keep, bool)]
        log.info("copy: %d unpredicted pairs of free records; name-equal %d; + exact address %d; + legal ok %d; "
                 "+ best S1 and unique %d; after the city check and the caps %d (skipped by the caps %d) %s", len(u),
                 int(k.sum()), int((k & u.same_addr & u.nums_eq).sum()), int(ok.sum()),
                 int((ok & u.own & (n_ok_r == 1)).sum()), len(add), n_cap, add.groupby(["nk", "leg"]).size().to_dict())
        changes.append(add[["s1", "r"]].assign(action="add", rule=("copy_" + add.nk + "_" + add.leg).to_numpy()))
        m = pd.concat([m, add[["s1", "r"]]], ignore_index=True)

    m = m.astype({"s1": "int64", "r": "int64"}).reset_index(drop=True)
    assert not m.r.duplicated().any(), "a record has two owners"
    ch = pd.concat(changes, ignore_index=True) if changes else pd.DataFrame({"s1": [], "r": [], "action": [], "rule": []})
    ch = ch.astype({"s1": "int64", "r": "int64"})
    ch["country"] = s1_cty.reindex(ch.s1.to_numpy()).to_numpy()
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    m.to_parquet(out / f"polished_{name}.parquet", index=False)
    ch[["s1", "r", "action", "rule", "country"]].to_parquet(out / f"changes_{name}.parquet", index=False)
    log.info("%s: %d -> %d pairs; changes %s (%.0fs)", name, n_in, len(m),
             ch.groupby(["country", "action", "rule"]).size().to_dict(), time.time() - t0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
