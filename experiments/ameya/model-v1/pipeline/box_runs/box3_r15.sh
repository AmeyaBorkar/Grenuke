#!/bin/bash
# grenuke-vast3: stage 2 on the 7B-corrected round-4 labels (mixf7's French decisions, guarded; the 859 French pairs the
# 7B rejects forced to y = 0) x3: v7sq6q4 (cmq6) and v7sq7q4 (cmq7), in parallel on the H100.
R=/workspace/grenuke; B=$R/box
LEG=leg__rel,leg__n_s1,leg__n_r,leg__inter,leg__s1_only,leg__r_only
NX=nx__d1,nx__nudge,nx__digit_sub,nx__digit_swap,nx__suffix,nx__len_diff
source $R/env.sh; export OMP_NUM_THREADS=24 NUMBA_NUM_THREADS=24
pkill -f "ce_synth2.py --name cesyoob" 2>/dev/null; sleep 5
cd $R/repo/experiments/ameya/model-v1
for x in "v7sq6q4 cmq6" "v7sq7q4 cmq7"; do set -- $x
  ( for a in 1 2 3; do
      python s2w.py --feats ameya-fx5 --s1 ameya-s1-v6all --groups str,cx,lo0,lg,ce,$2,nx --cluster --extra $LEG,ce__logit,$2__logit,$NX --all \
        --tag ameya-s2-$1 --pseudo $B/pseudo_s2_fr_mixf7q_guard.parquet --pseudo-weight 3 > $R/logs/s2_$1.log 2>&1 && { echo "$(date +%H:%M:%S) R15 $1 DONE"; exit 0; }
      grep -q "out of memory" $R/logs/s2_$1.log || break; sleep 120
    done; echo "$(date +%H:%M:%S) R15 $1 FAILED" ) &
  sleep 20
done
wait
echo "$(date +%H:%M:%S) R15 DONE"
