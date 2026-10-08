#!/bin/bash
SP=$SCRATCH
source $SP/env6.sh > /dev/null; K=~/.ssh/grenuke_vast2; A=/workspace/grenuke/ameya_q7add
until ssh -n -o ConnectTimeout=15 -i $K -p <port> root@<gpu-host> "grep -q 'ADD SCORING DONE' $A/run.log && echo yes" 2>/dev/null | grep -q yes; do
  [ "$(date +%H%M)" -gt 2045 ] && { echo "$(date +%H:%M) ADD scoring never finished"; exit 0; }; sleep 45; done
scp -q -i $K -P <port> "root@<gpu-host>:$A/hold_add_scored.parquet" "root@<gpu-host>:$A/test_add_scored_*.parquet" $SP/q7add/ || { echo "ADD fetch FAILED"; exit 1; }
cd $REPO && python $SP/q7add/eval_add.py 2>&1 | tail -22
echo "$(date +%H:%M) ADD EVAL READY"
