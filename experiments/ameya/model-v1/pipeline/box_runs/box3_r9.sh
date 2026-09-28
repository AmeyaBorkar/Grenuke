#!/bin/bash
# grenuke-vast3: round-3 stage 2 on the guarded mixmdp labels x3: v7sq6r3 (cmq6) and v7sq7r3 (cmq7), in parallel.
R=/workspace/grenuke; B=$R/box
LEG=leg__rel,leg__n_s1,leg__n_r,leg__inter,leg__s1_only,leg__r_only
NX=nx__d1,nx__nudge,nx__digit_sub,nx__digit_swap,nx__suffix,nx__len_diff
source $R/env.sh; export OMP_NUM_THREADS=24 NUMBA_NUM_THREADS=24
cd $R/repo/experiments/ameya/model-v1
for x in "v7sq6r3 cmq6" "v7sq7r3 cmq7"; do set -- $x
  python s2w.py --feats ameya-fx5 --s1 ameya-s1-v6all --groups str,cx,lo0,lg,ce,$2,nx --cluster --extra $LEG,ce__logit,$2__logit,$NX --all \
    --tag ameya-s2-$1 --pseudo $B/pseudo_s2_fr_mixmdp_guard.parquet --pseudo-weight 3 > $R/logs/s2_$1.log 2>&1 \
    && echo "$(date +%H:%M:%S) R9 $1 DONE" || echo "$(date +%H:%M:%S) R9 $1 FAILED" &
done
wait
echo "$(date +%H:%M:%S) R9 DONE"
