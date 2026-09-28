#!/bin/bash
# grenuke-vast3, 14:55 IST: bges2 = round-1 self-trained bge-reranker-v2-m3, seed 27 (second seed of bges), folds 0 and 1
# now, fold 2 when the v7sq7wg stage 2 has ended (GPU memory), then merge. Ends "BGES2 DONE" / "BGES2 FAILED".
R=/workspace/grenuke; B=$R/box
source $R/env.sh; export HF_HUB_OFFLINE=1
cd $B; rm -rf out_bges2
BG="--model BAAI/bge-reranker-v2-m3 --name bges2 --lr 2e-5 --batch 128 --epochs 1 --seed 27 --pseudo $B/pseudo_fr_v7ce3.parquet"
for g in 0 1; do python ce_box.py $BG --only-group $g > $R/logs/ce_bges2_g$g.log 2>&1 & done
sleep 60
while pgrep -f "s2w.py --feats ameya-fx5 --s1 ameya-s1-v6all --groups str,cx,lo0,lg,ce,cmq7" > /dev/null; do sleep 20; done
python ce_box.py $BG --only-group 2 > $R/logs/ce_bges2_g2.log 2>&1
wait
python ce_box.py $BG --merge > $R/logs/ce_bges2_merge.log 2>&1 && echo "$(date +%H:%M:%S) BGES2 DONE" || echo "$(date +%H:%M:%S) BGES2 FAILED"
