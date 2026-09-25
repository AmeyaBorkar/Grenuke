"""Issues #8 + #9 on the TEAM pipeline (contracts C2, C5, C8, C9, C10).

    python experiments/sachi/run_real.py --feat-tag <features tag> --tag m-v0
    python experiments/sachi/run_real.py --feat-tag <features tag> --tag m-v0 --sample-entities 400000

Reads : work/features/<feat-tag>/{train,test}.parquet   (C8: s1, r, fold, y, <group>__<name>)
        work/records/train.parquet, work/records/truth.parquet   (C3)
Writes: work/scores/<tag>-s1/{train,test}.parquet   (C5: s1, r, p1, oof_group)
        work/scores/<tag>/{train,test}.parquet      (C5: s1, r, p  calibrated)
        work/matches/<tag>/{train,test}.parquet     (C9: s1, r; train = holdout S1s)
        work/reports/<tag>-model.json
"""
from __future__ import annotations

import argparse, json, subprocess, sys, time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from model.stage1 import train_oof_and_full, default_params
from model.calibrate import crossfit_oof, fit_full, reliability_table
from model.decide import (argmax_ownership, EvalIndex, tune_threshold, apply_threshold,
                          dp_decide, tune_shift, f_vector)
import ber.eval as E

W = Path("work")


def check_team_splits():
    """Stop if the team's holdout/train folds differ from what this script assumes."""
    if set(E.HOLDOUT_FOLDS) != set(range(0, 5)) or set(E.TRAIN_FOLDS) != set(range(5, 20)):
        sys.exit(f"Team folds differ: HOLDOUT={E.HOLDOUT_FOLDS} TRAIN={E.TRAIN_FOLDS}. Paste this to Claude.")


def load_feats(tag, split):
    df = pd.read_parquet(W / "features" / tag / f"{split}.parquet")
    df = df.rename(columns={"s1": "s1_eid", "r": "r_eid", "y": "label"})
    for c in df.columns:
        if "__" in c:
            df[c] = df[c].astype(np.float32)
    return df


def save(df, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    print(f"  wrote {path}  ({len(df):,} rows)")


def c5_s1(df):
    return pd.DataFrame({"s1": df.s1_eid.astype(np.int64), "r": df.r_eid.astype(np.int64),
                         "p1": df.p1.astype(np.float32), "oof_group": df.oof_group.astype(np.int8)})


def c5_p(df):
    return pd.DataFrame({"s1": df.s1_eid.astype(np.int64), "r": df.r_eid.astype(np.int64),
                         "p": df.p.astype(np.float32)})


def c9(df):
    return pd.DataFrame({"s1": df.s1_eid.astype(np.int64), "r": df.r_eid.astype(np.int64)})


def git_sha():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True,
                                       stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "unknown"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feat-tag", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--sample-entities", type=int, default=0,
                    help="train on N sampled S1 entities (each keeps ALL its candidates); 0 = all")
    ap.add_argument("--device", default=None, help="cuda / cpu (default: auto)")
    ap.add_argument("--dev", action="store_true",
                    help="practice run: score only the holdout S1s that appear in the feature file")
    a = ap.parse_args()
    t0 = time.time()
    check_team_splits()

    # ---------------- load (C8)
    print("loading features ...")
    tr = load_feats(a.feat_tag, "train")
    hold_mask = np.isin(tr["fold"].to_numpy(), list(E.HOLDOUT_FOLDS))
    train, hold = tr[~hold_mask].copy(), tr[hold_mask]
    if len(hold) == 0 or len(train) == 0:
        sys.exit(f"Need both training and holdout rows. Folds present: {sorted(tr['fold'].unique())}")
    train["oof_group"] = np.asarray(E.oof_group(train["s1_eid"].to_numpy())).astype(np.int8)
    print("  OOF groups (team):", train["oof_group"].value_counts().sort_index().to_dict())
    rest = train.iloc[:0]
    if a.sample_entities:
        ents = train["s1_eid"].drop_duplicates().sample(
            min(a.sample_entities, train["s1_eid"].nunique()), random_state=17)
        pick = train["s1_eid"].isin(ents)
        train, rest = train[pick], train[~pick]
    test_path = W / "features" / a.feat_tag / "test.parquet"
    apply = {"holdout": hold}
    if len(rest):
        apply["rest"] = rest            # unsampled training-fold rows: scored, never trained on
    if test_path.exists():
        apply["test"] = load_feats(a.feat_tag, "test")
    print(f"  train pairs {len(train):,} | holdout pairs {len(hold):,} | test pairs "
          f"{len(apply['test']) if 'test' in apply else 0:,}")

    # ---------------- issue #8: stage 1 + calibration (C5)
    print("training (3 OOF models + full model) ...")
    oof, applied, info, booster = train_oof_and_full(train, apply, default_params(a.device), verbose=200)
    y = train["label"].to_numpy()
    oof["p"] = crossfit_oof(oof, y)
    iso = fit_full(oof, y)
    for d in applied.values():
        d["p"] = iso.predict(d["p1"].to_numpy())
        d["oof_group"] = -1

    h = applied["holdout"]
    # every train-split pair: OOF p for training rows, full-model p for holdout (+ unsampled) rows
    s1_train = pd.concat([oof, h] + ([applied["rest"]] if "rest" in applied else []), ignore_index=True)
    save(c5_s1(s1_train), W / "scores" / f"{a.tag}-s1" / "train.parquet")
    save(c5_p(s1_train), W / "scores" / a.tag / "train.parquet")
    if "test" in applied:
        save(c5_s1(applied["test"]), W / "scores" / f"{a.tag}-s1" / "test.parquet")
        save(c5_p(applied["test"]), W / "scores" / a.tag / "test.parquet")
    (W / "models" / a.tag).mkdir(parents=True, exist_ok=True)
    booster.save_model(W / "models" / a.tag / "stage1_full.json")

    ece_oof = reliability_table(oof["p"].to_numpy(), y).attrs["ece"]
    ece_h = reliability_table(h["p"].to_numpy(), hold["label"].to_numpy()).attrs["ece"]

    # ---------------- issue #9: ownership + decision (C9)
    print("deciding ...")
    rec = pd.read_parquet(W / "records" / "train.parquet", columns=["eid", "source", "country"])
    s1 = rec[rec["source"] == 1]
    s1_fold = np.asarray(E.fold_of(s1["eid"].to_numpy()))
    hold_s1 = s1[np.isin(s1_fold, list(E.HOLDOUT_FOLDS))]
    if a.dev:
        hold_s1 = hold_s1[hold_s1["eid"].isin(tr["s1_eid"].unique())]
    truth = pd.read_parquet(W / "records" / "truth.parquet").rename(columns={"s1": "s1_eid", "r": "r_eid"})
    ev = EvalIndex(hold_s1["eid"].to_numpy(), truth)

    # Ownership over ALL S1 candidates of each record (training folds included), exactly as on test,
    # then keep the pairs owned by holdout S1s for evaluation.
    owned_all = argmax_ownership(s1_train)
    owned = owned_all[owned_all["s1_eid"].isin(hold_s1["eid"])]
    print(f"  ownership: {len(s1_train):,} pairs -> {len(owned_all):,} owned; {len(owned):,} owned by holdout S1")
    t, _, _ = tune_threshold(owned, ev)
    f_thr = f_vector(apply_threshold(owned, t), ev)
    b, _, _ = tune_shift(owned, ev)
    f_dp = f_vector(dp_decide(owned, b=b), ev)
    g = E.paired_bootstrap(f_thr, f_dp)                    # team gate function (C10)
    keep_dp = g["delta"] >= 0.002 and g["ci_low"] > 0      # plan rule; ties go to the threshold
    rule = "dp" if keep_dp else "threshold"
    print(f"  threshold {t}: F0.5 {f_thr.mean():.4f} | DP (b={b}): {f_dp.mean():.4f} | chosen: {rule}")

    decide = (lambda o: dp_decide(o, b=b)) if keep_dp else (lambda o: apply_threshold(o, t))
    save(c9(decide(owned)), W / "matches" / a.tag / "train.parquet")
    if "test" in applied:
        save(c9(decide(argmax_ownership(applied["test"]))), W / "matches" / a.tag / "test.parquet")

    ctry = hold_s1["country"].to_numpy()
    rep = {
        "tag": a.tag, "feat_tag": a.feat_tag, "git": git_sha(),
        "minutes": round((time.time() - t0) / 60, 1),
        "n_train_pairs": len(train), "n_holdout_pairs": len(hold), "n_holdout_S1": len(hold_s1),
        "best_iters": info["best_iters"], "n_full": info["n_full"],
        "ece_oof": round(ece_oof, 4), "ece_holdout": round(ece_h, 4),
        "threshold": t, "F05_threshold": round(float(f_thr.mean()), 4),
        "shift_b": b, "F05_dp": round(float(f_dp.mean()), 4),
        "gate_G6": {k: (float(v) if isinstance(v, (int, float, np.floating)) else v) for k, v in g.items()},
        "chosen": rule,
        "per_country_F05": {c: round(float(f_thr[ctry == c].mean()), 4) for c in np.unique(ctry)},
        "singleton_F05": round(float(f_thr[ev.T == 0].mean()), 4),
        "mean_pred_per_S1_holdout": round(len(decide(owned)) / len(hold_s1), 3),
        "top_features": [k for k, _ in sorted(info["importance_gain"].items(), key=lambda kv: -kv[1])[:15]],
    }
    out = W / "reports" / f"{a.tag}-model.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    json.dump(rep, open(out, "w"), indent=2, default=str)
    print(json.dumps(rep, indent=2, default=str))


if __name__ == "__main__":
    main()
