#!/usr/bin/env bash
# Laptop-side orchestration of the box work after 12:00 (runs in the background, logs to work/logs/box3_after.log):
#  Wg: when the box's v7sqwg stage 2 ends, fetch it and mark v7sqwg_state/s2.done (the queue then skips that stage 2).
#  R2: when both round-2 cross-encoders are done, ship e5l/bge/qst/e5ls outputs, run box3_r2_remote.sh on the box
#      (gates, cmq5g, stage 2 v7sq5g), then fetch it and mark v7sq5g_state/s2.done.  Ends "BOX3 AFTER DONE".
set -uo pipefail
H=grenuke-vast3; R=/workspace/grenuke
SP=/c/Users/ameya/AppData/Local/Temp/claude/C--Users-ameya-Documents-GrenukeAmazon/19e315ba-0725-4d6f-ae6a-972e1c1f0aa9/scratchpad
rsh() { ssh -n -o ConnectTimeout=20 $H "$@" 2>&1 | grep -vE "^Welcome|^Have fun|^AI agents"; }
echo "$(date +%H:%M:%S) start"
# R2 launch (as soon as both CEs are done), then Wg fetch, then R2 fetch
for n in e5lsr2g qstr2g; do
  until rsh "grep -qE 'done in|Traceback' $R/logs/ce_$n.log && echo y" | grep -q y; do sleep 60; done
  echo "$(date +%H:%M:%S) $n: $(rsh "grep -E 'done in|Traceback' $R/logs/ce_$n.log | tail -1")"
done
for s in e5l bge qst e5ls; do rsh "mkdir -p $R/box/out_$s" > /dev/null; scp -q $SP/box/out_$s/ce_train.parquet $SP/box/out_$s/ce_test.parquet $SP/box/out_$s/config.json $H:$R/box/out_$s/; done
scp -q $SP/box3_r2_remote.sh $H:$R/r2_remote.sh
rsh "cd $R && THREADS=96 nohup bash r2_remote.sh > $R/logs/r2_chain.log 2>&1 < /dev/null & sleep 5; cat $R/logs/r2_chain.log"
echo "$(date +%H:%M:%S) R2 chain launched on the box"
until rsh "pgrep -f 'ameya-s2-v7sqwg' > /dev/null || echo ended" | grep -q ended; do sleep 60; done
echo "$(date +%H:%M:%S) v7sqwg stage 2 ended on the box: $(rsh "tail -c 200 $R/logs/s2_v7sqwg.log | tail -1 | cut -c1-120")"
bash $SP/box3_fetch_s2.sh v7sqwg 2>&1 | tail -4
until rsh "grep -qE 'R2 S2 DONE|R2 FAILED' $R/logs/r2_chain.log && echo y" | grep -q y; do sleep 60; done
rsh "cat $R/logs/r2_chain.log | tail -6"
if rsh "grep -q 'R2 S2 DONE' $R/logs/r2_chain.log && echo y" | grep -q y; then bash $SP/box3_fetch_s2.sh v7sq5g 2>&1 | tail -4; fi
echo "$(date +%H:%M:%S) BOX3 AFTER DONE"
