#!/bin/bash
# grenuke-vast3, 27 Sep ~14:00 IST: v7sq6wg stage 2 (cmq6 = qst, e5ls, e5ls2, bges; guarded v7sq labels x3) on the GPU,
# with the round-1 bge second seed (bges2) folds 0 and 1 alongside; fold 2 starts when stage 2 is done, then merge.
R=/workspace/grenuke; B=$R/box
LEG=leg__rel,leg__n_s1,leg__n_r,leg__inter,leg__s1_only,leg__r_only
NX=nx__d1,nx__nudge,nx__digit_sub,nx__digit_swap,nx__suffix,nx__len_diff
source $R/env.sh; export HF_HUB_OFFLINE=1 OMP_NUM_THREADS=32 NUMBA_NUM_THREADS=32
cd $R/repo/experiments/ameya/model-v1
python s2w.py --feats ameya-fx5 --s1 ameya-s1-v6all --groups str,cx,lo0,lg,ce,cmq6,nx --cluster --extra $LEG,ce__logit,cmq6__logit,$NX --all \
  --tag ameya-s2-v7sq6wg --pseudo $B/pseudo_s2_fr_v7sq_guard.parquet --pseudo-weight 3 > $R/logs/s2_v7sq6wg.log 2>&1 &
S2=$!
cd $B
BG="--model BAAI/bge-reranker-v2-m3 --name bges2 --lr 2e-5 --batch 128 --epochs 1 --seed 27 --pseudo $B/pseudo_fr_v7ce3.parquet"
for g in 0 1; do python ce_box.py $BG --only-group $g > $R/logs/ce_bges2_g$g.log 2>&1 & done
wait $S2; echo "$(date +%H:%M:%S) S2 v7sq6wg exit $?"
python ce_box.py $BG --only-group 2 > $R/logs/ce_bges2_g2.log 2>&1
echo "$(date +%H:%M:%S) bges2 fold 2 exit $?"
wait
python ce_box.py $BG --merge > $R/logs/ce_bges2_merge.log 2>&1; echo "$(date +%H:%M:%S) bges2 merge exit $?"
