#!/bin/bash
# grenuke-vast3 GPU queue after box3_r6.sh (bges2): round-1 self-trained seeds, two folds at a time (a stage-2 run may
# share the GPU), then the third, then merge. e5ls3 = e5-large seed 37 (2 epochs), bges3 = bge seed 38 (1 epoch).
R=/workspace/grenuke; B=$R/box
source $R/env.sh; export HF_HUB_OFFLINE=1
until grep -qE "BGES2 (DONE|FAILED)" $R/logs/box3_r6.log 2>/dev/null; do sleep 30; done
cd $B
job() {  # job <name> <args...>
  local n=$1; shift; rm -rf out_$n; echo "$(date +%H:%M:%S) start $n"
  for g in 0 1; do python ce_box.py --name $n "$@" --only-group $g > $R/logs/ce_${n}_g$g.log 2>&1 & done; wait
  python ce_box.py --name $n "$@" --only-group 2 > $R/logs/ce_${n}_g2.log 2>&1
  python ce_box.py --name $n "$@" --merge > $R/logs/ce_${n}_merge.log 2>&1 && echo "$(date +%H:%M:%S) $n DONE" || echo "$(date +%H:%M:%S) $n FAILED"
}
job e5ls3 --model intfloat/multilingual-e5-large --lr 2e-5 --batch 128 --epochs 2 --seed 37 --pseudo $B/pseudo_fr_v7ce3.parquet
job bges3 --model BAAI/bge-reranker-v2-m3 --lr 2e-5 --batch 128 --epochs 1 --seed 38 --pseudo $B/pseudo_fr_v7ce3.parquet
echo "$(date +%H:%M:%S) QUEUE DONE"
