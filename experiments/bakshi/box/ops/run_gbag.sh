#!/usr/bin/env bash
# Bagged variant: mean of the stage-2 scores of g0, g1, g1w (bag_scores.py, as v7ens2 did), then the usual chain.
R=/workspace/grenuke; L=$R/logs
cd $R; . ./env.sh
until [ -f $L/.doneB_g1_s2 ] && [ -f $L/.doneB_g1w_s2 ]; do sleep 30; done
echo "$(date +%T) START gbag/bag" >> $L/phaseB_gbag.log
( cd $M && python bag_scores.py --scores ameya-s2-g0,ameya-s2-g1,ameya-s2-g1w --tag ameya-s2-gbag ) > $L/B_gbag_bag.log 2>&1 \
  || { echo "$(date +%T) FAIL gbag/bag" >> $L/phaseB_gbag.log; tail -20 $L/B_gbag_bag.log >> $L/phaseB_gbag.log; exit 1; }
echo "$(date +%T) DONE  gbag/bag" >> $L/phaseB_gbag.log
for s in zmean ce_import s2 decide_c2; do touch $L/.doneB_gbag_$s; done
CUDA_VISIBLE_DEVICES=1 bash repo/experiments/bakshi/box/phaseB.sh gbag "e5l" $R/box_ameya/pseudo_s2_fr_v7ce3.parquet
