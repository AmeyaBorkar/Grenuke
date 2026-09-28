#!/bin/bash
# grenuke-vast3 H100 (free after the stage-2 runs): the bge and e5-large out-of-band detectors, faster than the copies on
# 5090 #2 / Bakshi's 4090s. Same inputs: CE band + the US/India holdout predicted pairs (holdout rows), French final pairs as test.
cd /workspace/grenuke && source env.sh
mkdir -p box_oob; for f in band_synth records_synth; do ln -sf /workspace/grenuke/box_s3/$f.parquet box_oob/$f.parquet; done
cd /workspace/grenuke
CE_BOX_DIR=/workspace/grenuke/box_oob python ce_synth2.py --name cesyoobh --model BAAI/bge-reranker-v2-m3 --lr 2e-5 --batch 128 --epochs 1 --seed 47 \
  --us-in-frac 0.5 --target-only-test --hold-groups 0 > /workspace/grenuke/logs/ce_cesyoobh.log 2>&1 &
CE_BOX_DIR=/workspace/grenuke/box_oob python ce_synth2.py --name cesyoobL --model intfloat/multilingual-e5-large --lr 2e-5 --batch 128 --epochs 1 \
  --us-in-frac 0.5 --target-only-test --hold-groups 0 > /workspace/grenuke/logs/ce_cesyoobL.log 2>&1 &
wait
