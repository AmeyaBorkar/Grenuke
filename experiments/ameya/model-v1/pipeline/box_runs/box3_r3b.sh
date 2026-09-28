#!/bin/bash
# grenuke-vast3, after box3_r3.sh's bges2 merge: gate bges2 (holdout band AUC >= 0.93), cmq7 = zmean(qst, e5ls, e5ls2,
# bges, bges2), import, then stage 2 v7sq7wg (guarded v7sq labels x3). Ends "R3B DONE" or "R3B FAILED ...".
R=/workspace/grenuke; B=$R/box
LEG=leg__rel,leg__n_s1,leg__n_r,leg__inter,leg__s1_only,leg__r_only
NX=nx__d1,nx__nudge,nx__digit_sub,nx__digit_swap,nx__suffix,nx__len_diff
until grep -q "bges2 merge exit" $R/logs/box3_r3.log 2>/dev/null; do sleep 30; done
grep -q "bges2 merge exit 0" $R/logs/box3_r3.log || { echo "$(date +%H:%M:%S) R3B FAILED bges2"; exit 1; }
source $R/env.sh; export OMP_NUM_THREADS=32 NUMBA_NUM_THREADS=32
cd $R/repo/experiments/ameya/model-v1
python - <<PY || { echo "$(date +%H:%M:%S) R3B FAILED gate"; exit 1; }
import json; c = json.load(open("$B/out_bges2/config.json")); a = c["auc"]["holdout"]; print("bges2 holdout band AUC", a)
raise SystemExit(0 if a >= 0.93 else 1)
PY
python $B/zmean_ce.py $B/out_cmq7 $B/out_qst $B/out_e5ls $B/out_e5ls2 $B/out_bges $B/out_bges2 || { echo "$(date +%H:%M:%S) R3B FAILED zmean"; exit 1; }
python ce_import.py --feats ameya-fx5 --src $B/out_cmq7 --group cmq7 --column cmq7__logit || { echo "$(date +%H:%M:%S) R3B FAILED import"; exit 1; }
echo "$(date +%H:%M:%S) s2 v7sq7wg"
python s2w.py --feats ameya-fx5 --s1 ameya-s1-v6all --groups str,cx,lo0,lg,ce,cmq7,nx --cluster --extra $LEG,ce__logit,cmq7__logit,$NX --all \
  --tag ameya-s2-v7sq7wg --pseudo $B/pseudo_s2_fr_v7sq_guard.parquet --pseudo-weight 3 > $R/logs/s2_v7sq7wg.log 2>&1 \
  && echo "$(date +%H:%M:%S) R3B DONE" || echo "$(date +%H:%M:%S) R3B FAILED s2"
