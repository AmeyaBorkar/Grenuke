"""Test concrete hypotheses about France's unexplained uncertain band on the France kit.

    python experiments/sachi/france_hypotheses.py --kit work/kits/france-kit-v1 [--examples 6]

france_discover.py showed the known operations (A, APP, ACR, B) are already aligned with the US/India truth after the
rules; the residual is in pairs with NO operation (46k in pc 0.3-0.9, 179 per 1000 French S1, only 20% predicted).
Each hypothesis below is a population defined identically in France and in the US/India holdout. We measure its truth
rate on the holdout (y) and France's predicted share, and estimate the value of making France follow that truth.
Caveat: both files are the stage-2 set (p1 >= 0.002). US/India stage 1 removes false pairs better than France's, so
holdout truth can be optimistic for France; hypotheses whose false pairs are structurally rare (e.g. empty address
+ unique exact name: orphans almost never lack an address) are the least exposed to that bias.
"""
from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

LEGAL = set("sarl sas sasu eurl sa sci snc ei llc inc ltd pvt private limited co corp corporation company llp lp pllc "
            "pc plc the".split())
LIST = {"France": {"fils", "cie", "services", "associes", "groupe", "developpement", "france", "et", "freres"},
        "US": {"center", "services", "service", "partners"},
        "India": {"center", "services", "service", "partners"}}
TOK = re.compile(r"[a-z0-9]+")
W_ADD, W_DROP = 0.06, 0.19


def fold(s) -> str:
    s = "" if s is None or (isinstance(s, float) and np.isnan(s)) else str(s)
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def toks(s) -> frozenset:
    return frozenset(t for t in TOK.findall(fold(s)) if t not in LEGAL)


def enrich(d: pd.DataFrame, country: np.ndarray) -> pd.DataFrame:
    a = d["r_address"].map(fold).str.strip()
    d = d.assign(country=country)
    d["empty_addr"] = a.isin(["", "null", "<null>", "none", "nan"]).to_numpy()
    s_t, r_t = d["s1_name"].map(toks), d["r_name"].map(toks)
    d["same_name"] = [x == y and len(x) > 0 for x, y in zip(s_t, r_t)]
    d["shared"] = [len(x & y) for x, y in zip(s_t, r_t)]
    extra = [y - x for x, y in zip(s_t, r_t)]
    missing = [x - y for x, y in zip(s_t, r_t)]
    lst = [LIST.get(c, set()) for c in d["country"]]
    d["list_extra"] = [len(e) > 0 and e <= L for e, L in zip(extra, lst)]
    d["pure_append"] = [len(e) > 0 and e <= L and len(m) == 0 for e, m, L in zip(extra, missing, lst)]
    d["brand1"] = [len(y) == 1 and len(next(iter(y))) >= 5 and len(x & y) == 0 for x, y in zip(s_t, r_t)]
    sn = d["same_num"]
    d["same_num_b"] = sn.astype(str).str.lower().isin(["true", "1"]).to_numpy()
    d["op"] = d["op"].fillna("").astype(str)
    return d


HYP = {
    "H1 empty addr + same name + unique name (s1_group=1)": lambda d: d.empty_addr & d.same_name & (d.s1_group == 1),
    "H1b empty addr + same name + 2 S1 share it": lambda d: d.empty_addr & d.same_name & (d.s1_group == 2),
    "H1c empty addr + same name + 3+ S1 share it": lambda d: d.empty_addr & d.same_name & (d.s1_group >= 3),
    "H2 one-word brand name at the S1's number, no shared word": lambda d: ~d.empty_addr & d.brand1 & d.same_num_b,
    "H3 no op, extra words all list words (+ maybe drops)": lambda d: (d.op == "") & d.list_extra & ~d.empty_addr,
    "H3b no op, pure list append (nothing dropped)": lambda d: (d.op == "") & d.pure_append & ~d.empty_addr,
    "H4 no op, same name, address present, same number": lambda d: (d.op == "") & d.same_name & ~d.empty_addr & d.same_num_b,
    "H4b no op, same name, address present, number differs": lambda d: (d.op == "") & d.same_name & ~d.empty_addr & ~d.same_num_b,
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kit", default="work/kits/france-kit-v1")
    ap.add_argument("--examples", type=int, default=6)
    a = ap.parse_args()
    kit = Path(a.kit)
    pd.set_option("display.width", 220, "display.max_colwidth", 70)
    cols = ["s1", "r", "pc", "op", "same_num", "s1_group", "s1_name", "s1_address", "r_name", "r_address"]
    fr = pd.read_parquet(kit / "france_pairs.parquet", columns=cols + ["pred_final"])
    ho = pd.read_parquet(kit / "holdout_pairs.parquet", columns=cols + ["y", "pred", "country"])
    n_fr_s1 = fr["s1"].nunique()
    fr = enrich(fr, np.array(["France"] * len(fr)))
    ho = enrich(ho, ho["country"].to_numpy())
    print(f"France {len(fr):,} stage-2 pairs, {n_fr_s1:,} S1; holdout {len(ho):,} pairs\n")

    rows = []
    for name, f in HYP.items():
        mf, mh = f(fr).to_numpy(), f(ho).to_numpy()
        h = ho[mh]
        t = h.groupby("country")["y"].agg(["size", "mean"])
        tr_us = t["mean"].get("US", np.nan)
        tr_in = t["mean"].get("India", np.nan)
        fp = fr[mf]
        pred = fp["pred_final"].mean() if len(fp) else np.nan
        truth_lo = np.nanmin([tr_us, tr_in]) if len(h) else np.nan
        truth_hi = np.nanmax([tr_us, tr_in]) if len(h) else np.nan
        if truth_lo >= 0.9:
            gain = len(fp) * max(truth_lo - pred, 0) * W_ADD / n_fr_s1
        elif truth_hi <= 0.1:
            gain = len(fp) * max(pred - truth_hi, 0) * W_DROP / n_fr_s1
        else:
            gain = 0.0
        rows.append({"hypothesis": name, "hold_n": len(h), "truth_US": tr_us, "truth_India": tr_in,
                     "hold_pred": h["pred"].mean() if len(h) else np.nan, "fr_n": len(fp),
                     "fr_per_1000": 1000 * len(fp) / n_fr_s1, "fr_pred": pred,
                     "fr_pc_med": fp["pc"].median() if len(fp) else np.nan,
                     "est_france_f05": gain, "est_lb": 0.15 * gain})
    tab = pd.DataFrame(rows)
    print(tab.round(4).to_string(index=False))
    print("\nest_* only where US/India truth is clear (>= 0.9 add, <= 0.1 drop); it assumes France follows it.")

    for name, f in HYP.items():
        fp = fr[f(fr).to_numpy() & (fr["pred_final"].to_numpy() == 0)]
        if not len(fp):
            continue
        print(f"\n=== {name}: France pairs NOT predicted ({len(fp):,})")
        for _, x in fp.sample(min(a.examples, len(fp)), random_state=0).iterrows():
            print(f"  pc={x.pc:.3f} g={x.s1_group}  S1: {str(x.s1_name)[:36]:36s} | {str(x.s1_address)[:48]}")
            print(f"                    R : {str(x.r_name)[:36]:36s} | {str(x.r_address)[:48]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
