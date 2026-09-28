#!/bin/bash
# RTX 5090: score the q7st 7B adapters 1 and 2 (Bakshi's score_pairs.py) on the pairs adapter 0 put below 0: the US/India
# holdout sample (train split) and the French + US/India final pairs (test split). Ends "Q7ENS DONE".
cd /workspace/grenuke && source env.sh
export HF_HOME=/workspace/grenuke/hf PYTHONPATH=/workspace/grenuke/repo/experiments/ameya/model-v1:/workspace/grenuke/repo/code/business_entity_resolution/src
until grep -q "DL DONE" q7ens/dl.log; do sleep 10; done
S="python3 repo/experiments/bakshi/box/score_pairs.py --batch 128"
for a in adapter_2 adapter_1; do
  for s in train test; do
    $S --adapter q7ens/$a --pairs q7ens/pairs_$s.parquet --split $s --out q7ens/${a}_$s.parquet > q7ens/${a}_$s.log 2>&1 \
      && echo "$(date +%H:%M:%S) $a $s done" >> q7ens/run.log || echo "$(date +%H:%M:%S) $a $s FAILED" >> q7ens/run.log
  done
done
echo "$(date +%H:%M:%S) Q7ENS DONE" >> q7ens/run.log
