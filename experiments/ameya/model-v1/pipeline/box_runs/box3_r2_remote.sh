#!/usr/bin/env bash
# Runs ON grenuke-vast3: gate the round-2 cross-encoders exactly as final_night15 does (holdout-band AUC >= 0.93, corr
# with e5l <= 0.995), build cmq5g = zmean(e5l, q, e, bge), import it, then stage 2 for v7sq5g with the P1 labels.
# Ends "R2 S2 DONE" or "R2 FAILED ...".
set -uo pipefail
R=/workspace/grenuke; B=$R/box
cd $R/repo/experiments/ameya/model-v1; source $R/env.sh
export OMP_NUM_THREADS=${THREADS:-64} NUMBA_NUM_THREADS=${THREADS:-64}
gate() {
python - "$1" <<'PY'
import sys, json, numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
B = "/workspace/grenuke/box"; name = sys.argv[1]
b = pd.read_parquet(f"{B}/band_train.parquet", columns=["fold", "y"]); h = b.fold.to_numpy() < 5; y = b.y.to_numpy()[h]
q = pd.read_parquet(f"{B}/out_{name}/ce_train.parquet").ce__logit.to_numpy()[h]
e = pd.read_parquet(f"{B}/out_e5l/ce_train.parquet").ce__logit.to_numpy()[h]
t = pd.read_parquet(f"{B}/out_{name}/ce_test.parquet").ce__logit.to_numpy()
auc = roc_auc_score(y, q); corr = np.corrcoef(q, e)[0, 1]
ok = bool(np.isfinite(q).all() and np.isfinite(t).all() and auc >= 0.93 and corr <= 0.995)
print(json.dumps({"name": name, "holdout_band_auc": round(float(auc), 4), "corr_with_e5l": round(float(corr), 4), "pass": ok}))
sys.exit(0 if ok else 1)
PY
}
echo "$(date +%H:%M:%S) start"
q=qst; gate qstr2g && q=qstr2g
e=e5ls; gate e5lsr2g && e=e5lsr2g
echo "chosen: e5l $q $e bge"
if [ $q = qst ] && [ $e = e5ls ]; then echo "R2 FAILED: both gates failed"; exit 1; fi
python zmean_ce.py $B/out_cmq5g $B/out_e5l $B/out_$q $B/out_$e $B/out_bge || { echo "R2 FAILED zmean"; exit 1; }
python ce_import.py --feats ameya-fx5 --src $B/out_cmq5g --group cmq5g --column cmq5g__logit || { echo "R2 FAILED import"; exit 1; }
LEG=leg__rel,leg__n_s1,leg__n_r,leg__inter,leg__s1_only,leg__r_only
NX=nx__d1,nx__nudge,nx__digit_sub,nx__digit_swap,nx__suffix,nx__len_diff
echo "$(date +%H:%M:%S) s2"
python s2.py --feats ameya-fx5 --s1 ameya-s1-v6all --tag ameya-s2-v7sq5g --groups str,cx,lo0,lg,ce,cmq5g,nx --cluster \
  --extra $LEG,ce__logit,cmq5g__logit,$NX --all --pseudo $B/pseudo_s2_fr_v7ce3.parquet > $R/logs/s2_v7sq5g.log 2>&1 \
  || { echo "R2 FAILED s2"; tail -5 $R/logs/s2_v7sq5g.log; exit 1; }
echo "$(date +%H:%M:%S) R2 S2 DONE"
