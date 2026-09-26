"""Stage 3: joint re-scoring across a record's S1 (A) and record-mass calibration of empty-address records (B).

    python experiments/ameya/model-v1/stage3.py --scores ameya-s2-v5all --tag ameya-s3-v5all --p-cand 0.02 --top-r 2
    python experiments/ameya/model-v1/decide.py --scores ameya-s3-v5all --col pc --tag ameya-model-v5all-s3 \
        --base ameya-model-v5all-c2 --p-cand 0.02 --top-r 2

Stage 2 sees the pair's own S1 (its confident copies per source) but not the rival S1 that competes for the same
record. The generator gives each S1 an S2 count and an S3 count drawn independently (RESEARCH_v5.md section 4), so
how many confident copies each rival already holds in the record's source says whose copy an ambiguous record is.
- A (contested records: >= 2 candidate S1 with pc >= P_CONTEST): a small XGBoost re-scores those rows from the
  pair's pc, its S1's confident copies per source (this record excluded), the best rival's pc and the rival S1's
  confident copies per source, the record's candidate count, empty address and source. Out of fold like stage 2
  (ber.eval.splits.oof_group): model g is trained on groups != g and scores group g; the holdout and test get the
  mean of the three models. Records with a holdout S1 among their candidates are never trained on, so no holdout
  label enters stage 3.
- B (empty-address records): a record with no address is a true copy 97.7% of the time (orphans almost always keep
  an address), but its total pc over its candidate S1 is compressed in the middle (0.3-0.9). An isotonic map from the
  record's total pc to "its owner is a candidate", fitted on training records only, scales that record's pcs up
  (never down). Records with an address are left alone (scaling them hurt).
Nothing is country-specific, so France gets the same treatment.

With --p-cand/--top-r, only the final candidate set (common.candidate_mask, as cands_final.py) is re-scored and every
pair outside it gets pc = 0, so decide.py with the same options keeps the matches inside the candidate file.
Writes work/scores/<tag>/{train,test}.parquet (the stage-2 columns with pc replaced), the models and the isotonic
map under work/models/<tag>/, and a report. Structure-thread prototype on the holdout: A +0.00006, A+B +0.00011;
in the pipeline with the candidate cut (ameya-model-v5all-s3 vs ameya-model-v5all-c2): +0.000051
[+0.000023, +0.000079] (A alone +0.000042), test predictions per S1 unchanged to 0.001 (RESEARCH_v5.md 8.4).
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
import pyarrow.compute as pc
import pyarrow.parquet as pq
import xgboost as xgb
from numba import njit
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import log_loss

from ber.artifacts import provenance, write_report
from ber.eval.splits import is_holdout, oof_group, splitmix64
from ber.paths import artifact_dir, artifact_path, records_path
from common import candidate_mask

log = logging.getLogger("stage3")
P_KEEP = 0.001  # rows below this (and outside the candidate set) never matter; they keep their pc
P_CONTEST = 0.01  # a record is contested when >= 2 of its S1 have pc >= P_CONTEST
CONF = 0.5  # an owned pair at pc >= CONF counts as one of its S1's confident copies
P_MAX = 0.999  # cap for pcs scaled up by B
PARAMS = {"objective": "binary:logistic", "eval_metric": "logloss", "tree_method": "hist", "max_depth": 6, "eta": 0.1,
          "subsample": 0.8, "min_child_weight": 20, "nthread": 8, "seed": 0}
NAMES = ["lpc", "k_same", "k_other", "k_none", "riv_lpc", "riv_k_same", "riv_k_other", "riv_k_none", "n_cands",
         "addr_empty", "is_s3"]


def empty_addresses(split: str) -> tuple[np.ndarray, np.ndarray]:
    """Sorted S2/S3 record eids and whether the record's address is empty."""
    f = pq.ParquetFile(records_path(split))
    eids, flags = [], []
    for b in f.iter_batches(batch_size=1_000_000, columns=["eid", "source", "address"]):
        m = b.column("source").to_numpy() > 1
        if not m.any():
            continue
        a = pc.filter(b.column("address"), pa.array(m))
        e = pc.equal(pc.utf8_length(pc.utf8_trim_whitespace(pc.fill_null(a, ""))), 0)
        eids.append(b.column("eid").to_numpy()[m])
        flags.append(e.to_numpy(zero_copy_only=False))
    eid, flag = np.concatenate(eids), np.concatenate(flags)
    order = np.argsort(eid)
    return eid[order], flag[order]


def read_rows(tag: str, split: str, p_cand: float) -> tuple[dict, int]:
    """Pass 1: the rows that can matter (pc >= P_KEEP, or p1 >= p_cand when cutting), in file order."""
    f = pq.ParquetFile(artifact_path("scores", tag, split))
    train = split == "train"
    cols = ["s1", "r", "p1", "pc"] + (["y"] if train else [])
    parts, start = [], 0
    for g in range(f.num_row_groups):
        t = f.read_row_group(g, columns=cols)
        s1, r = t.column("s1").to_numpy(), t.column("r").to_numpy()
        p1, pcv = t.column("p1").to_numpy(), t.column("pc").to_numpy()
        keep = pcv >= P_KEEP
        if p_cand > 0:
            keep |= p1 >= p_cand
        idx = np.flatnonzero(keep)
        part = {"row": start + idx.astype(np.int64), "s1": s1[idx], "r": r[idx], "p1": p1[idx].astype(np.float32),
                "pc": pcv[idx].astype(np.float32)}
        if train:
            part["y"] = t.column("y").to_numpy()[idx].astype(np.int8)
        parts.append(part)
        start += len(s1)
    rows = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
    return rows, start


@njit(cache=True)
def _owners(S, R, P, nR):
    best = np.full(nR, -1.0, np.float32)
    bs = np.full(nR, 2**31 - 1, np.int32)
    for i in range(S.size):
        r = R[i]
        if P[i] > best[r] or (P[i] == best[r] and S[i] < bs[r]):
            best[r] = P[i]
            bs[r] = S[i]
    return bs


@njit(cache=True)
def _rival(rows, S, R, P, k2, k3, src, nR):
    """Per contested row: the best other candidate's pc and that S1's confident copies (same / other source)."""
    b1 = np.full(nR, -1.0)
    b1s = np.full(nR, -1, np.int64)
    b2 = np.full(nR, -1.0)
    b2s = np.full(nR, -1, np.int64)
    for i in rows:
        r = R[i]
        p = P[i]
        if p > b1[r]:
            b2[r] = b1[r]
            b2s[r] = b1s[r]
            b1[r] = p
            b1s[r] = S[i]
        elif p > b2[r]:
            b2[r] = p
            b2s[r] = S[i]
    m = rows.size
    rp = np.empty(m)
    rks = np.empty(m)
    rko = np.empty(m)
    for j in range(m):
        i = rows[j]
        r = R[i]
        if b1s[r] == S[i]:
            p, s = b2[r], b2s[r]
        else:
            p, s = b1[r], b1s[r]
        rp[j] = p
        if src[i] == 2:
            rks[j] = k2[s]
            rko[j] = k3[s]
        else:
            rks[j] = k3[s]
            rko[j] = k2[s]
    return rp, rks, rko


def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


class Graph:
    """The kept rows of one split as a compact S1 x record graph."""

    def __init__(self, rows: dict, rec_eid: np.ndarray, rec_empty: np.ndarray, p_cand: float, top_r: int):
        self.rows = rows
        pc0 = rows["pc"].copy()
        self.cand = np.ones(pc0.size, bool)
        if p_cand > 0 or top_r > 0:  # the final candidate set: everything else is out (pc = 0)
            self.cand = candidate_mask(rows["s1"], rows["r"], rows["p1"], p_cand, top_r)
            pc0[~self.cand] = 0
        self.pc0 = pc0
        self.s_u, self.S = np.unique(rows["s1"], return_inverse=True)
        self.r_u, self.R = np.unique(rows["r"], return_inverse=True)
        self.S, self.R = self.S.astype(np.int32), self.R.astype(np.int32)
        self.nS, self.nR = self.s_u.size, self.r_u.size
        j = np.searchsorted(rec_eid, self.r_u)
        if not (rec_eid[np.minimum(j, rec_eid.size - 1)] == self.r_u).all():
            raise ValueError("candidate records missing from the records table")
        self.r_empty = rec_empty[j]
        self.src = (rows["r"] // 1_000_000_000).astype(np.int8)
        self.ae = self.r_empty[self.R]
        # records with a holdout S1 among their candidates: never trained on (train split)
        self.touch = np.zeros(self.nR, bool)
        if "y" in rows:
            self.touch[self.R[self.cand & is_holdout(rows["s1"])]] = True

    def contested(self) -> np.ndarray:
        c = self.pc0 >= P_CONTEST
        n_c = np.bincount(self.R[c], minlength=self.nR)
        self.n_c = n_c
        return np.flatnonzero(c & (n_c >= 2)[self.R])

    def features(self, idx: np.ndarray) -> np.ndarray:
        S, R, P, src = self.S, self.R, self.pc0, self.src
        own = _owners(S, R, P, self.nR)[R] == S
        conf = own & (P >= CONF)
        k2 = np.bincount(S[conf & (src == 2)], minlength=self.nS).astype(np.float64)
        k3 = np.bincount(S[conf & (src == 3)], minlength=self.nS).astype(np.float64)
        s, a = src[idx], S[idx]
        ks = np.where(s == 2, k2[a], k3[a]) - conf[idx]
        ko = np.where(s == 2, k3[a], k2[a])
        rp, rks, rko = _rival(idx, S, R, P, k2, k3, src, self.nR)
        rks = rks - ((rp >= CONF) & ~own[idx])  # the rival's count includes this record when it holds it
        return np.column_stack([_logit(P[idx]), ks, ko, ks + ko == 0, _logit(np.maximum(rp, 1e-6)), rks, rko,
                                rks + rko == 0, self.n_c[R[idx]], self.ae[idx], s == 3]).astype(np.float32)

    def mass(self, p: np.ndarray) -> np.ndarray:
        return np.bincount(self.R, weights=p.astype(np.float64), minlength=self.nR)


def fit_a(g: Graph, idx: np.ndarray, X: np.ndarray) -> tuple[list, np.ndarray, dict]:
    """Three out-of-fold models; returns them, the OOF stage-3 scores of the contested rows and diagnostics."""
    y = g.rows["y"][idx]
    grp = oof_group(g.rows["s1"][idx])
    touched = g.touch[g.R[idx]]
    val = (splitmix64(g.rows["r"][idx]) % np.uint64(10)) == 0
    out = np.full(idx.size, np.nan, np.float32)
    models, info = [], {}
    for k in range(3):
        fit = (grp >= 0) & (grp != k) & ~touched
        dfit = xgb.DMatrix(X[fit & ~val], label=y[fit & ~val], feature_names=NAMES)
        dval = xgb.DMatrix(X[fit & val], label=y[fit & val], feature_names=NAMES)
        b = xgb.train(PARAMS, dfit, 2000, evals=[(dval, "val")], early_stopping_rounds=50, verbose_eval=False)
        models.append(b)
        sel = grp == k
        out[sel] = b.predict(xgb.DMatrix(X[sel], feature_names=NAMES), iteration_range=(0, b.best_iteration + 1))
        info[f"model_{k}"] = {"rows": int(fit.sum()), "trees": int(b.best_iteration + 1), "val_logloss": float(b.best_score)}
        log.info("A model %d: %d rows, %d trees, val log-loss %.5f", k, int(fit.sum()), b.best_iteration + 1, b.best_score)
    hold = grp < 0
    out[hold] = predict_a(models, X[hold])
    ev = hold | touched  # rows that no model trained on: holdout-side diagnostics
    info["holdout_side_rows"] = int(ev.sum())
    info["holdout_side_logloss_pc"] = float(log_loss(y[ev], np.clip(g.pc0[idx][ev], 1e-6, 1 - 1e-6), labels=[0, 1]))
    info["holdout_side_logloss_s3"] = float(log_loss(y[ev], np.clip(out[ev], 1e-6, 1 - 1e-6), labels=[0, 1]))
    gain = models[0].get_score(importance_type="gain")
    info["gain_model_0"] = {k: round(v, 2) for k, v in sorted(gain.items(), key=lambda x: -x[1])}
    return models, out, info


def predict_a(models: list, X: np.ndarray) -> np.ndarray:
    d = xgb.DMatrix(X, feature_names=NAMES)
    return np.mean([b.predict(d, iteration_range=(0, b.best_iteration + 1)) for b in models], axis=0).astype(np.float32)


def fit_b(g: Graph, p: np.ndarray) -> tuple[IsotonicRegression, dict]:
    """Isotonic map of an empty-address record's total pc to P(its owner is a candidate), on training records only."""
    mass = g.mass(p)
    owner_cand = np.zeros(g.nR, bool)
    owner_cand[g.R[(g.rows["y"] == 1) & (g.pc0 > 0)]] = True
    fit = g.r_empty & ~g.touch & (mass > 0)
    iso = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip").fit(mass[fit], owner_cand[fit])
    ev = g.r_empty & g.touch & (mass > 0)
    bins = pd.cut(mass[ev], [0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.1, 100])
    tab = pd.DataFrame({"b": bins, "y": owner_cand[ev], "m": mass[ev], "g": iso.predict(mass[ev])}).groupby(
        "b", observed=True).agg(n=("y", "size"), mass=("m", "mean"), calibrated=("g", "mean"), actual=("y", "mean"))
    log.info("B: fitted on %d empty-address training records; holdout-side table:\n%s", int(fit.sum()),
             tab.round(3).to_string())
    return iso, {"records_fitted": int(fit.sum()),
                 "holdout_side_table": {str(k): v for k, v in tab.round(4).to_dict(orient="index").items()}}


def apply_b(g: Graph, p: np.ndarray, iso: IsotonicRegression) -> np.ndarray:
    mass = g.mass(p)
    scale = np.ones(g.nR)
    m = g.r_empty & (mass > 0)
    gm = iso.predict(mass[m])
    scale[m] = np.where(gm > mass[m], gm / mass[m], 1.0)
    up = scale[g.R] > 1
    out = p.copy()
    out[up] = np.minimum(p[up] * scale[g.R][up], P_MAX).astype(np.float32)
    return out


def write_scores(tag: str, split: str, src_tag: str, row: np.ndarray, pc_new: np.ndarray, cut: bool, command: str,
                 **extra) -> None:
    """Pass 2: copy the stage-2 scores row group by row group with pc replaced (streamed; same metadata as write_table)."""
    f = pq.ParquetFile(artifact_path("scores", src_tag, split))
    path = artifact_path("scores", tag, split)
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = provenance(command, {"scores": src_tag}, kind="scores", tag=tag, split=split, rows=f.metadata.num_rows, **extra)
    schema = f.schema_arrow.remove_metadata().with_metadata({b"ber": json.dumps(meta, default=str).encode()})
    w = pq.ParquetWriter(str(path) + ".tmp", schema, compression="zstd")
    start = 0
    for gi in range(f.num_row_groups):
        t = f.read_row_group(gi)
        n = t.num_rows
        pcv = t.column("pc").to_numpy().astype(np.float32)
        if cut:
            pcv[:] = 0  # outside the candidate set; the kept candidate rows are written back below
        lo, hi = np.searchsorted(row, [start, start + n])
        pcv[row[lo:hi] - start] = pc_new[lo:hi]
        t = t.set_column(t.schema.get_field_index("pc"), "pc", pa.array(pcv, pa.float32()))
        w.write_table(t.replace_schema_metadata(schema.metadata), row_group_size=n)
        start += n
    w.close()
    os.replace(str(path) + ".tmp", path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores", required=True, help="stage-2 scores tag")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--p-cand", type=float, default=0.0, help="re-score only the final candidate set (cands_final.py)")
    ap.add_argument("--top-r", type=int, default=0)
    ap.add_argument("--no-a", action="store_true", help="skip the contested-record model")
    ap.add_argument("--no-b", action="store_true", help="skip the empty-address mass calibration")
    ap.add_argument("--no-test", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    command = (f"python experiments/ameya/model-v1/stage3.py --scores {args.scores} --tag {args.tag}"
               f" --p-cand {args.p_cand} --top-r {args.top_r}" + (" --no-a" if args.no_a else "")
               + (" --no-b" if args.no_b else "") + (" --no-test" if args.no_test else ""))
    t0 = time.perf_counter()
    cut = args.p_cand > 0 or args.top_r > 0
    rule = {"p_cand": args.p_cand, "top_r": args.top_r, "p_contest": P_CONTEST, "conf": CONF, "a": not args.no_a,
            "b": not args.no_b}
    report = {"rule": rule}

    rows, n_rows = read_rows(args.scores, "train", args.p_cand)
    rec_eid, rec_empty = empty_addresses("train")
    g = Graph(rows, rec_eid, rec_empty, args.p_cand, args.top_r)
    del rec_eid, rec_empty
    log.info("train: %d of %d rows kept, %d S1, %d records, %d with a holdout S1 among their candidates (%.0fs)",
             g.pc0.size, n_rows, g.nS, g.nR, int(g.touch.sum()), time.perf_counter() - t0)
    p = g.pc0.copy()
    models, iso = [], None
    if not args.no_a:
        idx = g.contested()
        X = g.features(idx)
        log.info("A: %d contested records, %d rows", int((g.n_c >= 2).sum()), idx.size)
        models, p3, report["a"] = fit_a(g, idx, X)
        p[idx] = p3
        del X
    if not args.no_b:
        iso, report["b"] = fit_b(g, p)
        p = apply_b(g, p, iso)
    mdir = artifact_dir("models", args.tag)
    mdir.mkdir(parents=True, exist_ok=True)
    for k, b in enumerate(models):
        b.save_model(str(mdir / f"stage3_a_{k}.json"))
    if iso is not None:
        pd.DataFrame({"x": iso.X_thresholds_, "y": iso.y_thresholds_}).to_parquet(mdir / "stage3_b_isotonic.parquet")
    (mdir / "config.json").write_text(json.dumps({"rule": rule, "names": NAMES, "params": PARAMS}, indent=1))
    changed = np.abs(p - g.pc0) > 1e-6
    report["train"] = {"rows_kept": int(g.pc0.size), "rows_changed": int(changed.sum())}
    write_scores(args.tag, "train", args.scores, rows["row"], p, cut, command, rule=rule)
    log.info("train written: %d pcs changed (%.0fs)", int(changed.sum()), time.perf_counter() - t0)
    del g, rows, p

    if not args.no_test:
        rows, n_rows = read_rows(args.scores, "test", args.p_cand)
        rec_eid, rec_empty = empty_addresses("test")
        g = Graph(rows, rec_eid, rec_empty, args.p_cand, args.top_r)
        del rec_eid, rec_empty
        p = g.pc0.copy()
        if models:
            idx = g.contested()
            p[idx] = predict_a(models, g.features(idx))
            report["test_contested_rows"] = int(idx.size)
        if iso is not None:
            p = apply_b(g, p, iso)
        changed = np.abs(p - g.pc0) > 1e-6
        report["test"] = {"rows_kept": int(g.pc0.size), "rows_changed": int(changed.sum())}
        write_scores(args.tag, "test", args.scores, rows["row"], p, cut, command, rule=rule)
        log.info("test written: %d of %d rows kept, %d pcs changed (%.0fs)", g.pc0.size, n_rows, int(changed.sum()),
                 time.perf_counter() - t0)
    report["runtime_s"] = round(time.perf_counter() - t0)
    write_report(args.tag, report, command=command, inputs={"scores": args.scores})
    print(json.dumps(report, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
