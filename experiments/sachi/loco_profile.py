"""Do generator edit-profile features make the model transfer to an unseen country? (RESEARCH_v6 §3, branch A)

    python experiments/sachi/loco_profile.py --dev ameya-fx2-dev --train-country US --eval-country India

RESEARCH_v6 §3: if France's remaining loss is confident, the next model-level idea is "stage-2 edit-profile features,
which let the model learn the generator's operations instead of word identities". This tests that idea where labels
exist: leave-one-country-out on the dev kit (train on US only, score India's dev holdout).
- Profile per pair: post_ops.classify (op B/A/APP/ACR/NUM/CODE, kind, pos, num_kind, same_num, ...) one-hot encoded,
  plus log1p(s1_group), the number of S1 sharing the S1's core name. All label-free.
- Fits: baseline vs baseline + profile, each (a) US only -> India (loco) and (b) US + India -> India (in-country).
- loco_fixed uses the threshold tuned on the US holdout (what France gets); loco_oracle tunes it on India.
Keep the idea if loco_fixed rises >= +0.003 and in-country does not drop (> -0.001). The profile is cached in
work/features/<dev>-prof/train.parquet.
"""
from __future__ import annotations

import argparse
import json
import time

import numpy as np
import pandas as pd
import pyarrow.compute as pc
import pyarrow.parquet as pq

from ber.paths import artifact_path, records_path
from ber.records import load_truth
from loco_groups import Eval, fit, KEYS

CATS = ("op", "kind", "pos", "num_kind")


def build_profile(df: pd.DataFrame, cty: np.ndarray) -> pd.DataFrame:
    from post_ops import classify, record_text, s1_vocab
    t0 = time.perf_counter()
    ids = np.unique(np.r_[df["s1"].to_numpy(), df["r"].to_numpy()])
    names, keys, parts = record_text("train", ids, True)
    _, vocab = s1_vocab("train", {"US", "India"})
    print(f"profile inputs ready ({time.perf_counter() - t0:.0f}s); classifying {len(df):,} pairs", flush=True)
    d = classify(df[["s1", "r"]].assign(cty=cty), names, keys, vocab, parts)
    out = pd.DataFrame(index=df.index)
    for c in CATS:
        v = d[c].fillna("").astype(str) if c in d else pd.Series("", index=d.index)
        for val in sorted(set(v) - {""}):
            out[f"prof__{c}_{val}"] = (v == val).to_numpy(np.float32)
    for c in ("same_num", "street_typo"):
        if c in d:
            out[f"prof__{c}"] = d[c].astype(str).str.lower().isin(["true", "1"]).to_numpy(np.float32)
    try:
        from gap_check import s1_groups
        g = s1_groups("train").set_index("s1").n_core
        out["prof__log_s1_group"] = np.log1p(g.reindex(df["s1"].to_numpy()).fillna(1).to_numpy()).astype(np.float32)
    except Exception as e:  # noqa: BLE001
        print("s1_group skipped:", e, flush=True)
    print(f"profile: {out.shape[1]} columns ({time.perf_counter() - t0:.0f}s)", flush=True)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev", default="ameya-fx2-dev")
    ap.add_argument("--train-country", default="US")
    ap.add_argument("--eval-country", default="India")
    ap.add_argument("--no-in", action="store_true")
    a = ap.parse_args()
    t0 = time.perf_counter()
    df = pq.read_table(artifact_path("features", a.dev, "train")).to_pandas()
    base = [c for c in df.columns if c not in KEYS]
    rec = pq.read_table(records_path("train"), columns=["eid", "source", "country"])
    rec = rec.filter(pc.equal(rec["source"], 1))
    cmap = pd.Series(np.asarray(rec["country"].to_numpy(zero_copy_only=False), dtype=object),
                     index=rec["eid"].to_numpy())
    cty = cmap.reindex(df["s1"].to_numpy()).to_numpy()

    cache = artifact_path("features", f"{a.dev}-prof", "train")
    if cache.exists():
        prof = pd.read_parquet(cache)
        print(f"profile loaded from {cache}", flush=True)
    else:
        prof = build_profile(df, cty)
        cache.parent.mkdir(parents=True, exist_ok=True)
        prof.to_parquet(cache, index=False)
    df = pd.concat([df, prof.reset_index(drop=True)], axis=1)
    pcols = list(prof.columns)

    fold, y = df["fold"].to_numpy(), df["y"].to_numpy()
    tr_all = fold >= 5
    tr_loco = tr_all & (cty == a.train_country)
    truth = load_truth()
    ev_tr = Eval(df.loc[(~tr_all) & (cty == a.train_country)], truth)
    ev = Eval(df.loc[(~tr_all) & (cty == a.eval_country)], truth)

    res = {}
    for name, cols in (("base", base), ("base+profile", base + pcols)):
        X = df[cols].to_numpy(np.float32)
        b = fit(X[tr_loco], y[tr_loco], cols)
        t_tr, _ = ev_tr.best(b.inplace_predict(X[ev_tr.idx]))
        p = b.inplace_predict(X[ev.idx])
        t_or, f_or = ev.best(p)
        r = {"loco_oracle": round(f_or, 5), "loco_fixed": round(ev.at(p, t_tr), 5), "t_train": t_tr, "t_oracle": t_or}
        if not a.no_in:
            b2 = fit(X[tr_all], y[tr_all], cols)
            r["in_oracle"] = round(ev.best(b2.inplace_predict(X[ev.idx]))[1], 5)
        res[name] = r
        print(name, r, f"({time.perf_counter() - t0:.0f}s)", flush=True)
    d_fixed = res["base+profile"]["loco_fixed"] - res["base"]["loco_fixed"]
    d_in = res["base+profile"].get("in_oracle", np.nan) - res["base"].get("in_oracle", np.nan)
    keep = d_fixed >= 0.003 and (np.isnan(d_in) or d_in > -0.001)
    print(f"\nprofile features: loco_fixed {d_fixed:+.5f}, in-country {d_in:+.5f} -> {'KEEP (propose)' if keep else 'discard'}")
    with open(f"loco_profile_{a.train_country}_{a.eval_country}.json", "w") as fh:
        json.dump(res, fh, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
