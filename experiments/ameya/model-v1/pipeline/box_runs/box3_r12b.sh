#!/bin/bash
# grenuke-vast3: v7sqsyc = cmq9 (six round-1 French CEs) + synth3 cross-encoders cesy3 (local, box_s3) and cesy3b (5090,
# relayed into box/), stage 2 on the round-3 labels (guarded mixmdp) x3 (18:25 switch from the guarded v7sq labels). Waits for cesy3 (and cesy3b until 18:50 IST = 13:20 UTC).
R=/workspace/grenuke; B=$R/box
LEG=leg__rel,leg__n_s1,leg__n_r,leg__inter,leg__s1_only,leg__r_only
NX=nx__d1,nx__nudge,nx__digit_sub,nx__digit_swap,nx__suffix,nx__len_diff
source $R/env.sh; export OMP_NUM_THREADS=24 NUMBA_NUM_THREADS=24
until [ -s $R/box_s3/out_cesy3/ce_test.parquet ] && [ -s $R/box_s3/out_cesy3/config.json ]; do sleep 30; done
mkdir -p $B/out_cesy3 && cp $R/box_s3/out_cesy3/ce_train.parquet $R/box_s3/out_cesy3/ce_test.parquet $R/box_s3/out_cesy3/config.json $B/out_cesy3/
until [ -s $B/out_cesy3b/ce_test.parquet ] || [ "$(date -u +%H%M)" -ge 1320 ]; do sleep 30; done
M="$B/out_qst $B/out_e5ls $B/out_e5ls2 $B/out_bges $B/out_bges2 $B/out_e5ls3 $B/out_cesy3"
[ -s $B/out_cesy3b/ce_test.parquet ] && M="$M $B/out_cesy3b"
echo "$(date +%H:%M:%S) cmqsc from:$M"
cd $R/repo/experiments/ameya/model-v1
python $B/zmean_ce.py $B/out_cmqsc $M || { echo "$(date +%H:%M:%S) R12 v7sqsyc FAILED zmean"; exit 1; }
python ce_import.py --feats ameya-fx5 --src $B/out_cmqsc --group cmqsc --column cmqsc__logit > $R/logs/imp_cmqsc.log 2>&1 || { echo "$(date +%H:%M:%S) R12 v7sqsyc FAILED import"; exit 1; }
python s2w.py --feats ameya-fx5 --s1 ameya-s1-v6all --groups str,cx,lo0,lg,ce,cmqsc,nx --cluster --extra $LEG,ce__logit,cmqsc__logit,$NX --all \
  --tag ameya-s2-v7sqsyc --pseudo $B/pseudo_s2_fr_mixmdp_guard.parquet --pseudo-weight 3 > $R/logs/s2_v7sqsyc.log 2>&1 \
  && echo "$(date +%H:%M:%S) R12 v7sqsyc DONE" || echo "$(date +%H:%M:%S) R12 v7sqsyc FAILED s2"
