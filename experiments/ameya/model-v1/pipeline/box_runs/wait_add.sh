#!/bin/bash
SP=/c/Users/ameya/AppData/Local/Temp/claude/C--Users-ameya-Documents-GrenukeAmazon/19e315ba-0725-4d6f-ae6a-972e1c1f0aa9/scratchpad
source $SP/env6.sh > /dev/null; K=~/.ssh/grenuke_vast2; A=/workspace/grenuke/ameya_q7add
until ssh -n -o ConnectTimeout=15 -i $K -p 28860 root@202.122.49.242 "grep -q 'ADD SCORING DONE' $A/run.log && echo yes" 2>/dev/null | grep -q yes; do
  [ "$(date +%H%M)" -gt 2045 ] && { echo "$(date +%H:%M) ADD scoring never finished"; exit 0; }; sleep 45; done
scp -q -i $K -P 28860 "root@202.122.49.242:$A/hold_add_scored.parquet" "root@202.122.49.242:$A/test_add_scored_*.parquet" $SP/q7add/ || { echo "ADD fetch FAILED"; exit 1; }
cd /c/Users/ameya/Documents/GrenukeAmazon && python $SP/q7add/eval_add.py 2>&1 | tail -22
echo "$(date +%H:%M) ADD EVAL READY"
