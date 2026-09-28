#!/bin/bash
# grenuke-vast3: synthetic-French variants. v7sqsya = cmq9 (qst, e5ls, e5ls2, bges, bges2, e5ls3) + cesyb, as soon as cesyb
# arrives; v7sqsyb = cmq9 + cesyb + cesy2 + cesy2b (whichever arrived by 18:25 IST = 12:55 UTC). Stage 2 on the guarded v7sq
# labels x3 (the LB-tested recipe). Logs "R10 v7sqsy<x> DONE/FAILED".
R=/workspace/grenuke; B=$R/box
LEG=leg__rel,leg__n_s1,leg__n_r,leg__inter,leg__s1_only,leg__r_only
NX=nx__d1,nx__nudge,nx__digit_sub,nx__digit_swap,nx__suffix,nx__len_diff
source $R/env.sh; export OMP_NUM_THREADS=24 NUMBA_NUM_THREADS=24
M9="$B/out_qst $B/out_e5ls $B/out_e5ls2 $B/out_bges $B/out_bges2 $B/out_e5ls3"
s2() {  # s2 <tag> <group>
  cd $R/repo/experiments/ameya/model-v1
  python ce_import.py --feats ameya-fx5 --src $B/out_$2 --group $2 --column $2__logit > $R/logs/imp_$2.log 2>&1 || { echo "$(date +%H:%M:%S) R10 $1 FAILED import"; return 1; }
  python s2w.py --feats ameya-fx5 --s1 ameya-s1-v6all --groups str,cx,lo0,lg,ce,$2,nx --cluster --extra $LEG,ce__logit,$2__logit,$NX --all \
    --tag ameya-s2-$1 --pseudo $B/pseudo_s2_fr_v7sq_guard.parquet --pseudo-weight 3 > $R/logs/s2_$1.log 2>&1 \
    && echo "$(date +%H:%M:%S) R10 $1 DONE" || echo "$(date +%H:%M:%S) R10 $1 FAILED s2"
}
(
  until [ -s $B/out_cesyb/ce_test.parquet ]; do sleep 30; done
  python $B/zmean_ce.py $B/out_cmqsa $M9 $B/out_cesyb && s2 v7sqsya cmqsa
) &
(
  until { [ -s $B/out_cesy2/ce_test.parquet ] && [ -s $B/out_cesy2b/ce_test.parquet ]; } || [ "$(date -u +%H%M)" -ge 1255 ]; do sleep 30; done
  M="$M9"; for n in cesyb cesy2 cesy2b; do [ -s $B/out_$n/ce_test.parquet ] && M="$M $B/out_$n"; done
  echo "$(date +%H:%M:%S) cmqsb from:$M"
  python $B/zmean_ce.py $B/out_cmqsb $M && s2 v7sqsyb cmqsb
) &
wait
echo "$(date +%H:%M:%S) R10 ALL DONE"
