#!/bin/bash
# Bakshi's pipeline box, idle RTX 4090s: two more out-of-band detectors (synth3 CEs scoring the French final pairs and
# the US/India holdout predicted pairs): GPU 0 e5-large on synth seed 26, GPU 1 e5-base on synth seed 27. Ameya's dir only.
cd /workspace/grenuke && source env.sh >/dev/null 2>&1
export OMP_NUM_THREADS=8 NUMBA_NUM_THREADS=8 MKL_NUM_THREADS=8 RAYON_NUM_THREADS=8
A=/workspace/grenuke/ameya_oob
for d in l b; do mkdir -p $A/box_$d; ln -sf $A/band_train.parquet $A/box_$d/band_train.parquet; ln -sf $A/band_test.parquet $A/box_$d/band_test.parquet; done
cp $A/s26/*.parquet $A/box_l/; cp $A/s27/*.parquet $A/box_b/
CUDA_VISIBLE_DEVICES=0 CE_BOX_DIR=$A/box_l nice -n 5 python $A/ce_synth2.py --name cesyoobl --model intfloat/multilingual-e5-large --lr 2e-5 --batch 128 --epochs 1 \
  --us-in-frac 0.5 --target-only-test --hold-groups 0 > $A/ce_cesyoobl.log 2>&1 &
CUDA_VISIBLE_DEVICES=1 CE_BOX_DIR=$A/box_b nice -n 5 python $A/ce_synth2.py --name cesyoobb --model intfloat/multilingual-e5-base --lr 3e-5 --batch 128 --epochs 1 --seed 50 \
  --synth-weight 2 --us-in-frac 0.5 --target-only-test --hold-groups 0 > $A/ce_cesyoobb.log 2>&1 &
wait
