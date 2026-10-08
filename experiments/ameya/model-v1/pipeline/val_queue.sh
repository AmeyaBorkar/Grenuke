#!/bin/bash
# my valuation queue (the France agent is stopped): per model, when stacked, evalv (table vs v7sq-dpc), bt_cal (cal,
# the estimator that tracked the LB best), dpfr3 (France DP). One line per model into final_night29.log ("READY-VAL").
F=$SCRATCH/agents/fdiff
FB=$SCRATCH/agents/fdiff
L=$REPO/work/logs
for m in "$@"; do
  until grep -qE "(STACKED|READY) $m\b" $L/final_night*.log 2>/dev/null; do
    [ "$(date +%H%M)" -gt 2000 ] && { echo "$(date +%H:%M) VAL $m never stacked"; continue 2; }; sleep 30; done
  bash $FB/run.sh $F/evalv.py $F/ev_$m.log $m
  bash $FB/run.sh $F/bt_cal.py $F/bt_cal_$m.log $m
  bash $FB/run.sh $F/dpfr3.py $F/dpfr_$m.run.log $m auto
  c=$(tail -n +2 $FB/bt_cal_$m.csv 2>/dev/null | head -1)
  echo "$(date +%H:%M) READY-VAL $m | cal csv: $c | dp: $(cat $FB/dpfr_$m.log 2>/dev/null | cut -c1-200)"
done
echo "$(date +%H:%M) VALQ DONE"
