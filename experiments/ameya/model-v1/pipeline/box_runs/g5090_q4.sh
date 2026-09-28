#!/bin/bash
# RTX 5090 #1: after cesy3w, a second synth3 draw (seed 27, 60k French S1) and its e5-base cross-encoder cesy3x (synth weight 2).
cd /workspace/grenuke && source env.sh
mkdir -p box_s3x && ln -sf /workspace/grenuke/box/band_train.parquet box_s3x/band_train.parquet && ln -sf /workspace/grenuke/box/band_test.parquet box_s3x/band_test.parquet
python3 box/synth_fr3.py --records /workspace/grenuke/work/records/test.parquet --out /workspace/grenuke/box_s3x --seed 27 --n-s1 60000 2>&1 | head -1 | sed "s/^/$(date +%H:%M:%S) synth3 seed 27: /" >> logs/gpu_queue.log
while [ -n "$(ps -eo args | grep '^python3 box/ce_synth2.py --name cesy3w')" ]; do sleep 20; done
echo "$(date +%H:%M:%S) start cesy3x" >> logs/gpu_queue.log
CE_BOX_DIR=/workspace/grenuke/box_s3x python3 box/ce_synth2.py --name cesy3x --model intfloat/multilingual-e5-base --lr 3e-5 --batch 128 --epochs 1 --seed 49 \
  --synth-weight 2 --us-in-frac 0.5 --target-only-test --hold-groups 0 > logs/ce_cesy3x.log 2>&1
echo "$(date +%H:%M:%S) cesy3x exit $?" >> logs/gpu_queue.log
echo "$(date +%H:%M:%S) QUEUE DONE" >> logs/gpu_queue.log
