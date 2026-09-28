#!/usr/bin/env bash
# Ameya: 7B (q7st adapter_0, Bakshi's score_pairs.py) scoring of candidate pairs we did NOT predict (record unowned):
# the US/India holdout sample (labelled, for validating an "add" rule) on GPU 0, test on GPUs 1-3. Waits for Bakshi's jobs.
R=/workspace/grenuke; cd $R
export PATH="$HOME/.local/bin:$PATH"; . $R/.venv/bin/activate
export BER_DATA_DIR=$R/student_resource/dataset BER_WORK_DIR=$R/work BER_OUTPUT_DIR=$R/output CE_BOX_DIR=$R/box HF_HOME=$R/hf
export M=$R/repo/experiments/ameya/model-v1 B=$R/repo/experiments/bakshi
export PYTHONPATH="$M:$R/repo/code/business_entity_resolution/src"
A=$R/ameya_q7add; S="python $B/box/score_pairs.py --adapter $R/box/out_q7st/adapter_0"
while pgrep -f "score_pairs.py" > /dev/null; do sleep 15; done
echo "$(date -u +%T) start" >> $A/run.log
CUDA_VISIBLE_DEVICES=0 $S --pairs $A/hold_add_pairs.parquet --split train --out $A/hold_add_scored.parquet > $A/hold.log 2>&1 &
for i in 0 1 2; do CUDA_VISIBLE_DEVICES=$((i+1)) $S --pairs $A/test_add_pairs.parquet --split test --part $i/3 --out $A/test_add_scored_$i.parquet > $A/test$i.log 2>&1 & done
wait
echo "$(date -u +%T) ADD SCORING DONE" >> $A/run.log
