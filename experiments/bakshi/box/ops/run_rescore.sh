#!/usr/bin/env bash
# 7B rescoring on the two GPUs the Qwen3-4B does not use (2 and 3). Inputs pulled from Drive; outputs pushed back.
R=/workspace/grenuke; cd $R
export PATH="$HOME/.local/bin:$PATH"; . $R/.venv/bin/activate
export BER_DATA_DIR=$R/student_resource/dataset BER_WORK_DIR=$R/work BER_OUTPUT_DIR=$R/output CE_BOX_DIR=$R/box HF_HOME=$R/hf
export M=$R/repo/experiments/ameya/model-v1 B=$R/repo/experiments/bakshi
export PYTHONPATH="$M:$R/repo/code/business_entity_resolution/src"
D=$R/box/rescore; mkdir -p $D; rclone copy gdrive:grenuke-train-backup/rescore $D
S="python $B/box/score_pairs.py --adapter $R/box/out_q7st/adapter_0"
( CUDA_VISIBLE_DEVICES=2 $S --pairs $D/hold_pred_pairs.parquet --split train --out $D/hold_scored.parquet > $R/logs/rescore_hold.log 2>&1
  CUDA_VISIBLE_DEVICES=2 $S --pairs $D/fr_final_pairs.parquet --split test --part 1/2 --out $D/fr_scored_1.parquet > $R/logs/rescore_fr1.log 2>&1 ) &
CUDA_VISIBLE_DEVICES=3 $S --pairs $D/fr_final_pairs.parquet --split test --part 0/2 --out $D/fr_scored_0.parquet > $R/logs/rescore_fr0.log 2>&1
wait
rclone copy $D gdrive:grenuke-train-backup/rescore --include "*_scored*.parquet"
echo "$(date -u +%T) rescore done" >> $R/logs/rescore.log
