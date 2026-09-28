#!/bin/bash
# grenuke-vast3: round-4 stage 2 on the guarded mixqc labels x3: v7sq6r4 (cmq6). r14 hit a GPU out-of-memory next to the
# two synthetic cross-encoders (78 GB), so this waits until no ce_synth2.py is training, then tries up to 3 times.
R=/workspace/grenuke; B=$R/box
LEG=leg__rel,leg__n_s1,leg__n_r,leg__inter,leg__s1_only,leg__r_only
NX=nx__d1,nx__nudge,nx__digit_sub,nx__digit_swap,nx__suffix,nx__len_diff
source $R/env.sh; export OMP_NUM_THREADS=24 NUMBA_NUM_THREADS=24
while ps -eo args | grep -q "^python ce_synth2.py"; do sleep 30; done
cd $R/repo/experiments/ameya/model-v1
for a in 1 2 3; do
  echo "$(date +%H:%M:%S) R14 v7sq6r4 attempt $a"
  python s2w.py --feats ameya-fx5 --s1 ameya-s1-v6all --groups str,cx,lo0,lg,ce,cmq6,nx --cluster --extra $LEG,ce__logit,cmq6__logit,$NX --all \
    --tag ameya-s2-v7sq6r4 --pseudo $B/pseudo_s2_fr_mixqc_guard.parquet --pseudo-weight 3 > $R/logs/s2_v7sq6r4.log 2>&1 \
    && { echo "$(date +%H:%M:%S) R14 v7sq6r4 DONE"; exit 0; }
  grep -q "out of memory" $R/logs/s2_v7sq6r4.log || break
  cp $R/logs/s2_v7sq6r4.log $R/logs/s2_v7sq6r4.oom$a.log; sleep 180
done
echo "$(date +%H:%M:%S) R14 v7sq6r4 FAILED"
