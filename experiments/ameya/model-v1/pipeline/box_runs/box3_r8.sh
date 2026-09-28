#!/bin/bash
# grenuke-vast3, 15:05 IST: v7sq6w5 = cmq6 (qst, e5ls, e5ls2, bges) + guarded v7sq labels x5 at stage 2 (v7sq6wg used x3).
R=/workspace/grenuke; B=$R/box
LEG=leg__rel,leg__n_s1,leg__n_r,leg__inter,leg__s1_only,leg__r_only
NX=nx__d1,nx__nudge,nx__digit_sub,nx__digit_swap,nx__suffix,nx__len_diff
source $R/env.sh; export OMP_NUM_THREADS=24 NUMBA_NUM_THREADS=24
cd $R/repo/experiments/ameya/model-v1
echo "$(date +%H:%M:%S) s2 v7sq6w5"
python s2w.py --feats ameya-fx5 --s1 ameya-s1-v6all --groups str,cx,lo0,lg,ce,cmq6,nx --cluster --extra $LEG,ce__logit,cmq6__logit,$NX --all \
  --tag ameya-s2-v7sq6w5 --pseudo $B/pseudo_s2_fr_v7sq_guard.parquet --pseudo-weight 5 > $R/logs/s2_v7sq6w5.log 2>&1 \
  && echo "$(date +%H:%M:%S) R8 DONE" || echo "$(date +%H:%M:%S) R8 FAILED s2"
