#!/usr/bin/env bash
# Resume after the restart: block_train (pid 3470) survived the restart and keeps running; block_test runs
# beside it now; phase A then resumes (finished steps are skipped by their markers) and g0 follows.
# (Pipeline box, 27 Sep; recovered verbatim from the box for the record. run_chain3.sh took over after s1 crashed.)
cd /workspace/grenuke
. ./env.sh
L=logs
BP="--set trim_s1=15 --set trim_r=4 --set indic_dict=ameya-fx1 --set ns_ngrams=4 --set ns_domain_len=8 --set nw_words=6"
echo "$(date +%T) START block_test (beside the surviving block_train pid 3470)" >> $L/phaseA.log
( cd repo && python -m ber.pipeline --stage block --split test --tag ameya-block-v3 $BP --n-jobs 64 > ../$L/A_block_test.log 2>&1 \
  && touch ../$L/.doneA_block_test && echo "$(date +%T) DONE  block_test" >> ../$L/phaseA.log \
  || echo "$(date +%T) FAIL  block_test" >> ../$L/phaseA.log ) &
BT=$!
while kill -0 3470 2>/dev/null; do sleep 15; done
if grep -q "stage block: done" $L/A_block_train.log || tail -n 1 $L/A_block_train.log | grep -q "^}"; then
  touch $L/.doneA_block_train; echo "$(date +%T) DONE  block_train (surviving process)" >> $L/phaseA.log
else
  echo "$(date +%T) block_train did not finish cleanly -- phase A will rerun it" >> $L/phaseA.log
fi
wait $BT
bash repo/experiments/bakshi/box/phaseA.sh && CUDA_VISIBLE_DEVICES=0 bash repo/experiments/bakshi/box/phaseB.sh g0 "e5l qst e5ls bge" /workspace/grenuke/box_ameya/pseudo_s2_fr_v7ce3.parquet
echo "chain exit $?" >> $L/phaseA.log
