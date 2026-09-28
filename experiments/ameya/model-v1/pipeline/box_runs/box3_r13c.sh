#!/bin/bash
# grenuke-vast3: v7sqsyd = cmq9 + synth3 cross-encoders cesy3, cesy3b, cesy3h, cesy3g, cesy3w and cesy3x (5090s, relayed), stage 2 on the round-3 labels (guarded mixmdp) x3.

R=/workspace/grenuke; B=$R/box
LEG=leg__rel,leg__n_s1,leg__n_r,leg__inter,leg__s1_only,leg__r_only
NX=nx__d1,nx__nudge,nx__digit_sub,nx__digit_swap,nx__suffix,nx__len_diff
source $R/env.sh; export OMP_NUM_THREADS=24 NUMBA_NUM_THREADS=24
until [ -s $R/box_s3/out_cesy3/ce_test.parquet ] && [ -s $R/box_s3/out_cesy3/config.json ]; do sleep 30; done
mkdir -p $B/out_cesy3 && cp $R/box_s3/out_cesy3/ce_train.parquet $R/box_s3/out_cesy3/ce_test.parquet $R/box_s3/out_cesy3/config.json $B/out_cesy3/
until { [ -s $B/out_cesy3g/ce_test.parquet ] && [ -s $R/box_s3/out_cesy3h/config.json ] && [ -s $B/out_cesy3x/ce_test.parquet ]; } || [ "$(date -u +%H%M)" -ge 1350 ]; do sleep 30; done
M="$B/out_qst $B/out_e5ls $B/out_e5ls2 $B/out_bges $B/out_bges2 $B/out_e5ls3 $B/out_cesy3"
[ -s $R/box_s3/out_cesy3h/ce_test.parquet ] && [ -s $R/box_s3/out_cesy3h/config.json ] && mkdir -p $B/out_cesy3h && cp $R/box_s3/out_cesy3h/ce_train.parquet $R/box_s3/out_cesy3h/ce_test.parquet $R/box_s3/out_cesy3h/config.json $B/out_cesy3h/
for n in cesy3b cesy3h cesy3g cesy3w cesy3x; do [ -s $B/out_$n/ce_test.parquet ] && M="$M $B/out_$n"; done
echo "$(date +%H:%M:%S) cmqsd from:$M"
cd $R/repo/experiments/ameya/model-v1
python $B/zmean_ce.py $B/out_cmqsd $M || { echo "$(date +%H:%M:%S) R13 v7sqsyd FAILED zmean"; exit 1; }
python ce_import.py --feats ameya-fx5 --src $B/out_cmqsd --group cmqsd --column cmqsd__logit > $R/logs/imp_cmqsd.log 2>&1 || { echo "$(date +%H:%M:%S) R13 v7sqsyd FAILED import"; exit 1; }
python s2w.py --feats ameya-fx5 --s1 ameya-s1-v6all --groups str,cx,lo0,lg,ce,cmqsd,nx --cluster --extra $LEG,ce__logit,cmqsd__logit,$NX --all \
  --tag ameya-s2-v7sqsyd --pseudo $B/pseudo_s2_fr_mixmdp_guard.parquet --pseudo-weight 3 > $R/logs/s2_v7sqsyd.log 2>&1 \
  && echo "$(date +%H:%M:%S) R13 v7sqsyd DONE" || echo "$(date +%H:%M:%S) R13 v7sqsyd FAILED s2"
