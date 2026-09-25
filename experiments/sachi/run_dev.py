"""Issues #8 + #9 end to end on the dev features.

    python experiments/sachi/run_dev.py
"""
from __future__ import annotations

import json, sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from model.stage1 import train_oof_and_full, default_params
from model.calibrate import crossfit_oof, fit_full, reliability_table
from model.decide import (argmax_ownership, EvalIndex, tune_threshold, apply_threshold,
                          dp_decide, tune_shift, f_vector, paired_bootstrap)
from make_dev_features import dev_fold

W = Path(__file__).parent / "work"


def main():
    feats = pd.read_parquet(W / "features_dev.parquet")
    truth = pd.read_parquet(W / "truth_dev.parquet")
    s1 = pd.read_parquet(W / "s1_dev.parquet")
    s1["fold"] = s1.s1_eid.map(dev_fold)

    feats["label"] = feats.merge(truth.assign(_y=1), on=["s1_eid", "r_eid"], how="left")["_y"] \
        .fillna(0).astype(int).to_numpy()
    train, hold = feats[feats.fold >= 5], feats[feats.fold < 5]

    # issue #8: model + calibration
    oof, applied, info, booster = train_oof_and_full(train, {"holdout": hold}, default_params(), verbose=False)
    y = train.label.to_numpy()
    oof["p"] = crossfit_oof(oof, y)
    iso = fit_full(oof, y)
    h = applied["holdout"]; h["p"] = iso.predict(h.p1.to_numpy())
    ece_oof = reliability_table(oof.p.to_numpy(), y).attrs["ece"]
    ece_h = reliability_table(h.p.to_numpy(), hold.label.to_numpy()).attrs["ece"]

    # issue #9: ownership + decision
    hold_s1 = s1[s1.fold < 5]
    ev = EvalIndex(hold_s1.s1_eid.to_numpy(), truth)
    owned = argmax_ownership(h)
    t, _, _ = tune_threshold(owned, ev)
    f_thr = f_vector(apply_threshold(owned, t), ev)
    b, _, _ = tune_shift(owned, ev)
    f_dp = f_vector(dp_decide(owned, b=b), ev)
    gate = paired_bootstrap(f_thr, f_dp)

    ctry = hold_s1.country.to_numpy()
    rep = {
        "n_train_pairs": len(train), "n_holdout_S1": len(hold_s1),
        "best_iters": info["best_iters"], "ece_oof": round(ece_oof, 4), "ece_holdout": round(ece_h, 4),
        "threshold": t, "F05_threshold": round(f_thr.mean(), 4),
        "shift_b": b, "F05_dp": round(f_dp.mean(), 4), "gate_G6": gate,
        "chosen": "dp" if gate["keep"] else "threshold",
        "per_country_threshold": {c: round(f_thr[ctry == c].mean(), 4) for c in np.unique(ctry)},
        "singleton_F05": round(f_thr[ev.T == 0].mean(), 4),
        "top_features": [k for k, _ in sorted(info["importance_gain"].items(), key=lambda kv: -kv[1])[:8]],
    }
    print(json.dumps(rep, indent=2, default=float))
    json.dump(rep, open(W / "report_dev.json", "w"), indent=2, default=float)
    owned.to_parquet(W / "scores_holdout_dev.parquet", index=False)


if __name__ == "__main__":
    main()
