"""Label-free look-alike odds of name tokens, per country, from the candidate pairs themselves (group ``lop``).

    python experiments/ameya/model-v1/feats_lo_proxy.py --feats ameya-fx3 --split train --calib  # the rate -> odds map
    python experiments/ameya/model-v1/feats_lo_proxy.py --feats ameya-fx3 --split train          # writes <feats>-lop
    python experiments/ameya/model-v1/feats_lo_proxy.py --feats ameya-fx3 --split test           # writes <feats>-lop

The ``lo`` group (feats_lo.py) looks up each extra/missing name token in a table of log-odds learned from training
labels. Test France never appears in train, so its words (groupe, holding, participations, culturelle...) get 0 and a
look-alike that adds one looks like a true record with a noise word; US/India odds of shared words (centre, club)
also do not transfer.

Look-alike records move the first house number (nudge or other; 88-98% of look-alikes), true records seldom do. So
the share of moved numbers among the close pairs where token t is an extra record token (or a missing S1 token),
counted within one country on unlabelled pairs, says how look-alike the token is. ``--calib`` maps that rate to the
label-based odds of token_lo with a decreasing isotonic fit over the US/India tokens (support-weighted); every other
run applies the map per country, with each token's rate shrunk toward the neutral rate (the one the map sends to 0)
and tokens below MIN_SUPPORT set to exactly 0 (which also removes the -1.9e-16 vs 0 mismatch of ``lo``). The rate is
a within-token share, so it does not depend on how many look-alikes a country has: France's saturated mixture prior
(an earlier version) cannot happen here. Features: the lo__* columns of feats_lo.py, so the models use ``lop``
in place of ``lo``, trained and scored on the same label-free statistic.

- ``--calib`` (train): the map (work/models/<feats>/lo_proxy_map.json), its per-country fit, and dev-sample features
  for the leave-one-country-out check (``loco.py --lop <feats>-lop-dev``).
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import time

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from ber.artifacts import provenance, write_report
from ber.paths import artifact_dir, artifact_path
from feats import load_records
from feats_lo import CLOSE_WORD_JAC, _counts, _summarize, unmatched_tokens

log = logging.getLogger("feats_lo_proxy")
MOVED = (3, 4)      # num__rel1: 0 missing, 1 equal, 2 truncation, 3 nudge (|d| <= 10), 4 other
SHRINK = 20.0       # pseudo-pairs pulling a token's moved rate toward the neutral rate
MIN_SUPPORT = 30    # close numbered pairs a token needs in its country; below it the feature is exactly 0
FIT_SUPPORT = 200   # token_lo support for the tokens the map is fitted on
SIDES = (("x", "lo_extra", "extra_r"), ("m", "lo_missing", "missing_s1"))


def _keys(feats: str, split: str) -> pd.DataFrame:
    cols = ["s1", "r", "word__jac_w", "name__fz_inter", "num__rel1"]
    return pq.read_table(artifact_path("features", f"{feats}-str", split), columns=cols).to_pandas()


def token_rates(codes: np.ndarray, close: np.ndarray, rel: np.ndarray, n_codes: int,
                neutral: float | None) -> tuple[np.ndarray, np.ndarray, float]:
    """Per token code: the moved-number share among its close numbered pairs (shrunk toward ``neutral``, or toward
    the pooled share when None), its numbered support, and the pooled share."""
    numbered = close & (rel > 0)
    moved = np.isin(rel, MOVED)
    n_num, n_mov = _counts(codes[numbered], moved[numbered].astype(np.int8), n_codes)
    m = numbered & (codes[:, 0] >= 0)
    r0 = float(moved[m].mean()) if m.any() else 0.0
    target = r0 if neutral is None else neutral
    return (n_mov + SHRINK * target) / (n_num + SHRINK), n_num, r0


def apply_map(rate: np.ndarray, support: np.ndarray, mp: dict) -> np.ndarray:
    """Proxy log-odds per token: the isotonic map of its rate; exactly 0 below MIN_SUPPORT."""
    x, y = np.asarray(mp["x"]), np.asarray(mp["y"])
    lo = np.interp(rate, x, y).astype(np.float32)
    return np.where(support >= MIN_SUPPORT, lo, 0.0).astype(np.float32)


def country_features(rec: dict, s1: np.ndarray, r: np.ndarray, close: np.ndarray, rel: np.ndarray, n_codes: int,
                     maps: dict, label: str, vocab: np.ndarray) -> tuple[dict, dict]:
    """lo__* columns for one country's pairs from that country's own token rates."""
    xr, xs = unmatched_tokens(rec, s1, r)
    out, info = {}, {}
    for (side, col, name), codes in zip(SIDES, (xr, xs)):
        mp = maps[col]
        rate, sup, r0 = token_rates(codes, close, rel, n_codes, mp["neutral"])
        lo = apply_map(rate, sup, mp)
        o = np.zeros((3, s1.size), np.float32)
        _summarize(codes, lo[None, :], np.zeros(s1.size, np.int64), o)
        out[f"lo__{name}_min"], out[f"lo__{name}_sum"], out[f"lo__{name}_nlow"] = o[0], o[1], o[2]
        big = sup >= 200
        order = np.argsort(np.where(big, lo, np.inf))[:25]
        log.info("%s %s: pooled moved share %.3f, %d tokens with support; most look-alike: %s", label, col, r0,
                 int((sup >= MIN_SUPPORT).sum()),
                 ", ".join(f"{vocab[i]} {lo[i]:.1f} ({rate[i]:.2f}, n {int(sup[i])})" for i in order))
        benign = np.argsort(np.where(big, -lo, np.inf))[:10]
        log.info("%s %s: most benign: %s", label, col,
                 ", ".join(f"{vocab[i]} {lo[i]:.1f} ({rate[i]:.2f}, n {int(sup[i])})" for i in benign))
        info[col] = {"pooled_moved_share": r0, "tokens": int((sup >= MIN_SUPPORT).sum()),
                     "top": [[str(vocab[i]), float(lo[i]), float(rate[i]), int(sup[i])] for i in order]}
    return out, info


def calibrate(rec: dict, keys: pd.DataFrame, cty: np.ndarray, labels: list, vocab: np.ndarray,
              table: pd.DataFrame, model_dir, command: str) -> dict:
    """Fit rate -> label odds on US/India tokens (rates from holdout pairs; labels only through token_lo)."""
    from sklearn.isotonic import IsotonicRegression

    from ber.eval.splits import is_holdout
    n_codes = len(vocab)
    tidx = pd.Index(table["token"]).get_indexer(vocab)
    s1 = keys["s1"].to_numpy()
    hold = np.flatnonzero(is_holdout(s1))
    kh = keys.iloc[hold]
    xr, xs = unmatched_tokens(rec, kh["s1"].to_numpy(), kh["r"].to_numpy())
    close = (kh["word__jac_w"].to_numpy() >= CLOSE_WORD_JAC) & (kh["name__fz_inter"].to_numpy() >= 1)
    rel = kh["num__rel1"].to_numpy()
    maps, report = {}, {}
    for (side, col, name), codes in zip(SIDES, (xr, xs)):
        lab = np.full(n_codes, np.nan)
        lab[tidx >= 0] = table[col].to_numpy()[tidx[tidx >= 0]]
        nlab = np.zeros(n_codes)
        nlab[tidx >= 0] = table["n"].to_numpy()[tidx[tidx >= 0]]
        xs_, ys_, ws_, per = [], [], [], {}
        for c in np.unique(cty[hold]):
            m = cty[hold] == c
            rate, sup, r0 = token_rates(codes[m], close[m], rel[m], n_codes, None)
            ok = (sup >= MIN_SUPPORT) & (nlab >= FIT_SUPPORT) & np.isfinite(lab)
            xs_.append(rate[ok]), ys_.append(lab[ok]), ws_.append(sup[ok])
            per[labels[c]] = (rate, sup, ok, r0)
        x, y, w = np.concatenate(xs_), np.concatenate(ys_), np.concatenate(ws_)
        iso = IsotonicRegression(increasing=False, out_of_bounds="clip").fit(x, y, sample_weight=np.sqrt(w))
        grid = np.linspace(0.0, 1.0, 201)
        gy = iso.predict(grid)
        neutral = float(grid[np.argmin(np.abs(gy))])
        maps[col] = {"x": grid.tolist(), "y": gy.round(4).tolist(), "neutral": neutral}
        rep = {"tokens": int(x.size), "neutral_rate": neutral}
        for lbl, (rate, sup, ok, r0) in per.items():
            pred = np.interp(rate[ok], grid, gy)
            rho = pd.Series(pred).corr(pd.Series(lab[ok]), method="spearman")
            r2 = 1 - np.sum((lab[ok] - pred) ** 2) / np.sum((lab[ok] - lab[ok].mean()) ** 2)
            rep[lbl] = {"tokens": int(ok.sum()), "pooled_moved_share": round(r0, 3), "spearman": round(float(rho), 3),
                        "r2": round(float(r2), 3)}
        log.info("%s map: %d tokens, neutral rate %.3f, g(0.05)=%.2f g(0.2)=%.2f g(0.5)=%.2f g(0.8)=%.2f g(0.95)=%.2f; "
                 "fit per country %s", col, x.size, neutral, *np.interp([0.05, 0.2, 0.5, 0.8, 0.95], grid, gy),
                 {k: v for k, v in rep.items() if isinstance(v, dict)})
        report[col] = rep
    (model_dir / "lo_proxy_map.json").write_text(json.dumps(maps))
    write_report("ameya-fx3-lop-calib", {"maps": report}, command=command, inputs={"features": "ameya-fx3-str"},
                 merge=False)
    return maps


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--feats", default="ameya-fx3")
    ap.add_argument("--split", required=True, choices=["train", "test"])
    ap.add_argument("--calib", action="store_true", help="train: fit the rate -> odds map, write dev-sample features")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    command = (f"python experiments/ameya/model-v1/feats_lo_proxy.py --feats {args.feats} --split {args.split}"
               + (" --calib" if args.calib else ""))
    t0 = time.perf_counter()
    model_dir = artifact_dir("models", args.feats)
    rec, _ = load_records(args.split, pd.read_parquet(model_dir / "indic_dict.parquet"), strings=False)
    labels = list(rec["labels"])
    keys = _keys(args.feats, args.split)
    s1 = keys["s1"].to_numpy()
    cty = rec["cid"][rec["row_of"].get_indexer(s1)]
    vocab = rec["name"]["dict"].to_numpy(zero_copy_only=False)
    n_codes = len(vocab)
    word_jac, fz_inter, rel_all, r_all = (keys[c].to_numpy() for c in ("word__jac_w", "name__fz_inter", "num__rel1", "r"))

    if args.calib:
        if args.split != "train":
            raise SystemExit("--calib needs --split train")
        maps = calibrate(rec, keys, cty, labels, vocab, pd.read_parquet(model_dir / "token_lo.parquet"), model_dir,
                         command)
    else:
        maps = json.loads((model_dir / "lo_proxy_map.json").read_text())
    del keys

    names = [f"lo__{name}_{s}" for _, _, name in SIDES for s in ("min", "sum", "nlow")]
    out = {c: np.zeros(s1.size, np.float32) for c in names}
    written = {}
    for c in np.unique(cty):
        rows = np.flatnonzero(cty == c)
        close = (word_jac[rows] >= CLOSE_WORD_JAC) & (fz_inter[rows] >= 1)
        f, info = country_features(rec, s1[rows], r_all[rows], close, rel_all[rows], n_codes, maps, labels[c], vocab)
        for k, v in f.items():
            out[k][rows] = v
        written[labels[c]] = info
        log.info("%s: %d pairs (%.0fs)", labels[c], rows.size, time.perf_counter() - t0)

    if args.calib:  # the dev-sample slice for loco.py --lop (every country from its own full-split rates)
        from ber.eval.splits import in_dev_sample
        dev = in_dev_sample(s1)
        dfd = pd.DataFrame({k: v[dev] for k, v in out.items()})
        path = artifact_path("features", f"{args.feats}-lop-dev", "train")
        path.parent.mkdir(parents=True, exist_ok=True)
        meta = provenance(command, {"features": f"{args.feats}-str"}, split="train", rows=len(dfd), kind="features",
                          tag=f"{args.feats}-lop-dev", subset="dev sample (ber.eval.splits.in_dev_sample)")
        pq.write_table(pa.Table.from_pandas(dfd, preserve_index=False).replace_schema_metadata(
            {b"ber": json.dumps(meta).encode()}), path, compression="zstd")
        log.info("dev-sample proxy lo: %d pairs -> %s", len(dfd), path)

    fl = pq.ParquetFile(artifact_path("features", f"{args.feats}-str", args.split))
    df = pd.DataFrame(out)
    path = artifact_path("features", f"{args.feats}-lop", args.split)
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = provenance(command, {"features": f"{args.feats}-str"}, split=args.split, rows=len(df), kind="features",
                      tag=f"{args.feats}-lop", proxy={"moved": list(MOVED), "shrink": SHRINK,
                                                      "min_support": MIN_SUPPORT, "tables": written})
    schema = pa.Schema.from_pandas(df, preserve_index=False).with_metadata({b"ber": json.dumps(meta).encode()})
    w = pq.ParquetWriter(str(path) + ".tmp", schema, compression="zstd")
    start = 0
    for g in range(fl.num_row_groups):
        n = fl.metadata.row_group(g).num_rows
        w.write_table(pa.Table.from_pandas(df.iloc[start:start + n], preserve_index=False), row_group_size=n)
        start += n
    w.close()
    os.replace(str(path) + ".tmp", path)
    log.info("done: %s in %.0fs", path, time.perf_counter() - t0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
