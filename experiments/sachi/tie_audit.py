"""France tie audit: is France's pc overconfident on shared records, and would per-record renormalisation help?
Laptop-sized (reads only the France kit + the needed record addresses).

    python experiments/sachi/tie_audit.py --kit work/kits/france-kit-v1

1. The §2.3 table on the kit: records whose candidate pc sums past 1 (a record has at most one owner).
2. Contested kept pairs: a predicted pair whose record has another candidate S1 with pc >= 0.3.
   US/India holdout: their true rate by renormalised pc' = pc / max(1, sum pc) (labels), and the exact macro-F0.5
   change of dropping kept pairs with pc' below a cut. France: how many there are, and their implied false share
   if they behave like US/India pairs at the same pc' (the team's `cal` idea).
3. Department check: learns department -> region from confident French pairs (data only) and counts kept French
   pairs whose record's department maps to a different region than the S1's.
The kit is an older model's output: read the results as "is the effect there and how big", not as final numbers.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

N_HOLD = 549_699


def f05(h, t, p):
    d = 0.25 * t + p
    return np.where(d > 0, 1.25 * h / np.where(d > 0, d, 1), 1.0)


def load(path, want):
    cols = pq.ParquetFile(path).schema_arrow.names
    print(f"{Path(path).name}: {len(cols)} columns: {', '.join(cols)}")
    miss = [c for c in want if c not in cols]
    if miss:
        raise SystemExit(f"missing {miss} in {path}: paste this output so the script can be adapted")
    return pd.read_parquet(path, columns=[c for c in want + ["pred", "pred_final", "pred_model", "added", "y", "country", "r_address", "s1_address"]
                                          if c in cols])


def rec_stats(df, n_s1):
    s = df.groupby("r").pc.sum()
    return {"records/1000 S1 with sum pc > 1.05": 1000 * (s > 1.05).sum() / n_s1,
            "excess mass/1000 S1": 1000 * np.maximum(0, s - 1).sum() / n_s1}


def contested(df):
    df = df.copy()
    tot = df.groupby("r").pc.transform("sum")
    df["pcn"] = df.pc / np.maximum(1.0, tot)
    srt = df[["r", "pc"]].sort_values(["r", "pc"], ascending=[True, False])
    rank = srt.groupby("r").cumcount()
    second = srt[rank == 1].set_index("r").pc
    mx = df.groupby("r").pc.transform("max")
    sec = df.r.map(second).fillna(0.0).to_numpy()
    df["rival"] = np.where(df.pc >= mx, sec, mx)
    df["contested"] = (df.pred == 1) & (df.rival >= 0.3)
    return df


def addr_parts(a):
    return [p.strip().lower() for p in str(a).split(",") if p.strip()] if isinstance(a, str) else []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kit", default="work/kits/france-kit-v1")
    ap.add_argument("--truth", default="work/records/truth.parquet")
    ap.add_argument("--records", default="work/records/test.parquet")
    a = ap.parse_args()
    pd.set_option("display.width", 200)
    ho = load(Path(a.kit) / "holdout_pairs.parquet", ["s1", "r", "pc"])
    fr = load(Path(a.kit) / "france_pairs.parquet", ["s1", "r", "pc"])
    if "pred" not in fr and "pred_model" in fr:
        fr = fr.rename(columns={"pred_model": "pred"})   # the MODEL's decision: rule adds excluded
    for d in (ho, fr):
        if "added" in d:
            d.drop(d.index[d["added"].fillna(0).astype(bool)], inplace=True)
        d.drop(d.index[d["pc"] < 0.5], inplace=True)       # genuine model ties only
    for d in (ho, fr):
        if "pred" not in d:
            raise SystemExit("no `pred` column: paste this output so the script can be adapted")
        d["pred"] = d["pred"].astype(int)
    n_fr = fr.s1.nunique()
    print(f"\nholdout pairs {len(ho):,} ({ho.s1.nunique():,} S1); France pairs {len(fr):,} ({n_fr:,} S1)")

    print("\n1. Records whose candidate pc sums past 1 (one owner per record):")
    rows = {"holdout US/India": rec_stats(ho, N_HOLD), "test France": rec_stats(fr, n_fr)}
    print(pd.DataFrame(rows).T.round(2).to_string())

    hc, fc = contested(ho), contested(fr)
    print("\n2. Kept pairs whose record has a rival S1 at pc >= 0.3:")
    print(f"   holdout: {1000 * hc.contested.sum() / N_HOLD:.1f} per 1000 S1, true rate {hc[hc.contested].y.mean():.3f}")
    print(f"   France : {1000 * fc.contested.sum() / n_fr:.1f} per 1000 S1")
    bins = [0, 0.4, 0.5, 0.6, 0.7, 0.76, 0.85, 0.95, 1.01]
    hb = hc[hc.pred == 1].groupby(pd.cut(hc[hc.pred == 1].pcn, bins), observed=False).y.agg(["size", "mean"])
    fb = fc[fc.pred == 1].groupby(pd.cut(fc[fc.pred == 1].pcn, bins), observed=False).size()
    tab = pd.DataFrame({"holdout kept": hb["size"], "holdout true rate": hb["mean"].round(3),
                        "France kept": fb, "France kept /1000 S1": (1000 * fb / n_fr).round(2)})
    print("\n   kept pairs by renormalised pc' = pc / max(1, sum pc of the record):")
    print(tab.to_string())

    truth = pd.read_parquet(a.truth, columns=["s1"])
    n_true = truth.groupby("s1").size()
    base = ho[ho.pred == 1].groupby("s1").agg(p=("y", "size"), h=("y", "sum"))
    base["t"] = n_true.reindex(base.index).fillna(0)
    print("\n   drop kept pairs with pc' below a cut:")
    for cut in (0.5, 0.6, 0.7, 0.76):
        dh = hc[(hc.pred == 1) & (hc.pcn < cut)]
        fd = fc[(fc.pred == 1) & (fc.pcn < cut)]
        d = dh.groupby("s1").agg(dp=("y", "size"), dy=("y", "sum"))
        bb = base.reindex(d.index)
        delta = (f05(bb.h - d.dy, bb.t, bb.p - d.dp) - f05(bb.h, bb.t, bb.p)).sum() / N_HOLD
        ok = hb["size"].to_numpy() >= 30
        rate = np.where(ok, hb["mean"].to_numpy(), np.nan)
        idx = np.clip(np.searchsorted(bins, fd.pcn.to_numpy(), side="right") - 1, 0, len(rate) - 1)
        imp = 1 - np.nanmean(rate[idx]) if len(fd) else np.nan
        print(f"   pc' < {cut:.2f}: holdout drops {len(dh):,} (true {dh.y.mean():.3f}), exact holdout dF {delta:+.6f} | "
              f"France drops {1000 * len(fd) / n_fr:.1f}/1000 S1, implied false share {imp:.2f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
