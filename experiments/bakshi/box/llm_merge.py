#!/usr/bin/env python3
"""Join the three llm_group.py parts of one run into the files ce_llm_st.py writes.

Assembly is ce_llm_st.main's, in the same order: each group's own OOF rows; the holdout as the mean of the three
groups (summed in group order 0, 1, 2); the non-target test pairs as the mean of the three; each target (France)
test pair from the one group that did not see its third. Before writing, every part is checked against a fresh
layout() -- same pseudo-label file, same rows, same config -- so parts from different runs cannot be mixed, and the
result must be finite on every train and test row.

    python llm_merge.py --name q7st [--smoke]

Writes $CE_BOX_DIR/out_<name>/ce_{train,test}.parquet (row, ce__logit) + config.json, as ce_llm_st.py does, for
remap_ce.py / zmean_ce.py / ce_import.py.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from llm_group import GROUPS, layout, out_dir, own_rows  # noqa: E402

SAME = ("model", "name", "pseudo", "sep", "us_in_frac", "lora_r", "lr", "batch", "epochs", "max_len", "seed", "smoke")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    out = out_dir(a.name, a.smoke)
    parts = {}
    for g in GROUPS:
        f = f"{out}/part_{g}.npz"
        if not os.path.exists(f):
            raise SystemExit(f"FAIL: {f} missing -- group {g} has not finished")
        z = np.load(f)
        parts[g] = {k: z[k] for k in z.files}
        parts[g]["meta"] = json.loads(str(z["meta"]))
    m0 = parts[0]["meta"]
    for g in GROUPS:
        diff = {k: (m0.get(k), parts[g]["meta"].get(k)) for k in SAME if parts[g]["meta"].get(k) != m0.get(k)}
        if diff:
            raise SystemExit(f"FAIL: part {g} was not produced by the same run as part 0: {diff}")

    L = layout(m0["pseudo"], m0["smoke"])
    tr, te, y, hold, rest_t, tgt = L["tr"], L["te"], L["y"], L["hold"], L["rest_t"], L["tgt"]
    train_rows = L["train_rows"]
    logit = np.full(len(tr), np.nan, np.float32)
    hold_sum = np.zeros(hold.size, np.float32)
    test_sum = np.zeros(len(te), np.float32)
    tgt_logit = np.full(len(te), np.nan, np.float32)
    for g in GROUPS:
        p = parts[g]
        own, mine = own_rows(L, g)
        if not (np.array_equal(p["own"], own) and np.array_equal(p["mine"], mine)
                and p["hold_l"].size == hold.size and p["rest_l"].size == rest_t.size):
            raise SystemExit(f"FAIL: part {g} does not match the layout recomputed from {m0['pseudo']}")
        logit[own] = p["own_l"]
        hold_sum += p["hold_l"]
        test_sum[rest_t] += p["rest_l"]
        tgt_logit[mine] = p["mine_l"]
    n = len(GROUPS)
    auc = {"holdout": float(roc_auc_score(y[hold], hold_sum / n))}
    logit[hold] = hold_sum / n
    auc["oof"] = float(roc_auc_score(y[train_rows], logit[train_rows]))
    if "p1" in tr:
        auc["holdout_p1"] = float(roc_auc_score(y[hold], tr["p1"].to_numpy()[hold]))
    test_logit = test_sum / n
    test_logit[tgt] = tgt_logit[tgt]
    bad_tr, bad_te = int((~np.isfinite(logit)).sum()), int((~np.isfinite(test_logit)).sum())
    if bad_tr or bad_te:
        raise SystemExit(f"FAIL: non-finite logits on {bad_tr} train and {bad_te} test rows")

    pd.DataFrame({"row": tr["row"].to_numpy(), "ce__logit": logit}).to_parquet(f"{out}/ce_train.parquet", index=False)
    pd.DataFrame({"row": te["row"].to_numpy(), "ce__logit": test_logit}).to_parquet(f"{out}/ce_test.parquet", index=False)
    cfg = {k: m0[k] for k in ("model", "pseudo", "sep", "us_in_frac", "lora_r", "lr", "batch", "epochs", "max_len", "smoke")}
    cfg.update({"auc": auc, "seconds": max(parts[g]["meta"]["seconds"] for g in GROUPS), "parallel_groups": True,
                "infer_batch": m0["infer_batch"], "train_band": len(tr), "test_band": len(te),
                "groups": {g: {k: parts[g]["meta"][k] for k in ("fit", "pseudo_rows", "train_seconds", "seconds", "auc_own")}
                           for g in GROUPS}})
    with open(f"{out}/config.json", "w") as f:
        json.dump(cfg, f, indent=1)
    print(f"written {out}: AUC {auc}; train {len(tr):,} rows, test {len(te):,} rows (target {tgt.size:,})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
