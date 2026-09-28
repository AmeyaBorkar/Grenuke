#!/bin/bash
# RTX 5090: synth3 data, then after bges4 the synth3 e5-base cross-encoder cesy3b (replaces the e5ls4 seed).
cd /workspace/grenuke && source env.sh
mkdir -p box_s3 && ln -sf /workspace/grenuke/box/band_train.parquet box_s3/band_train.parquet && ln -sf /workspace/grenuke/box/band_test.parquet box_s3/band_test.parquet
python3 box/synth_fr3.py --records /workspace/grenuke/work/records/test.parquet --out /workspace/grenuke/box_s3 2>&1 | head -1 >> logs/gpu_queue.log
while [ -n "$(ps -eo args | grep '^python3 ce_box.py --name bges4')" ]; do sleep 20; done
echo "$(date +%H:%M:%S) bges4 exit (e5ls4 replaced by cesy3b)" >> logs/gpu_queue.log
echo "$(date +%H:%M:%S) start cesy3b" >> logs/gpu_queue.log
CE_BOX_DIR=/workspace/grenuke/box_s3 python3 box/ce_synth2.py --name cesy3b --model intfloat/multilingual-e5-base --lr 3e-5 --batch 128 --epochs 1 \
  --us-in-frac 0.5 --target-only-test --hold-groups 0 > logs/ce_cesy3b.log 2>&1
echo "$(date +%H:%M:%S) cesy3b exit $?" >> logs/gpu_queue.log
echo "$(date +%H:%M:%S) QUEUE DONE" >> logs/gpu_queue.log
