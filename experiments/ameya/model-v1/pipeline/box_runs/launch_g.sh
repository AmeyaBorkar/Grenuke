#!/bin/bash
cd /workspace/grenuke && source env.sh
ln -sf /workspace/grenuke/box_s3/band_synth.parquet box_oob/band_synth.parquet
ln -sf /workspace/grenuke/box_s3/records_synth.parquet box_oob/records_synth.parquet
CE_BOX_DIR=/workspace/grenuke/box_oob python3 box/ce_synth2.py --name cesyoobg --model BAAI/bge-reranker-v2-m3 --lr 2e-5 --batch 128 --epochs 1 \
  --us-in-frac 0.5 --target-only-test --hold-groups 0 > logs/ce_cesyoobg.log 2>&1
