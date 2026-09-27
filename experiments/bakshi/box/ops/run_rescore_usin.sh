#!/usr/bin/env bash
# 7B scoring of the US/India final predictions outside the band: parts 0-2 on the idle GPUs 1-3 now, part 3 on GPU 0
# once the Qwen3-4B has released it. Then push to Drive.
R=/workspace/grenuke; cd $R
export PATH="$HOME/.local/bin:$PATH"; . $R/.venv/bin/activate
export BER_DATA_DIR=$R/student_resource/dataset BER_WORK_DIR=$R/work BER_OUTPUT_DIR=$R/output CE_BOX_DIR=$R/box HF_HOME=$R/hf
export M=$R/repo/experiments/ameya/model-v1 B=$R/repo/experiments/bakshi
export PYTHONPATH="$M:$R/repo/code/business_entity_resolution/src"
D=$R/box/rescore; rclone copy gdrive:grenuke-train-backup/rescore/usin_final_pairs.parquet $D
S="python $B/box/score_pairs.py --adapter $R/box/out_q7st/adapter_0 --pairs $D/usin_final_pairs.parquet --split test"
for i in 0 1 2; do CUDA_VISIBLE_DEVICES=$((i+1)) $S --part $i/4 --out $D/usin_scored_$i.parquet > $R/logs/rescore_usin$i.log 2>&1 & done
until [ -f $R/box/out_q34st/part_2.npz ]; do sleep 30; done
CUDA_VISIBLE_DEVICES=0 $S --part 3/4 --out $D/usin_scored_3.parquet > $R/logs/rescore_usin3.log 2>&1
wait
rclone copy $D gdrive:grenuke-train-backup/rescore --include "usin_scored_*.parquet"
echo "$(date -u +%T) usin rescore done" >> $R/logs/rescore.log
