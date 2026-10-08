#!/usr/bin/env bash
# Laptop-side orchestration of the box work (replaces box3_after.sh + box3_fetch_seeds.sh, 12:20), strictly in order:
#  1. Wg: when the box's v7sqwg stage 2 ends, fetch it and mark v7sqwg_state/s2.done (the queue then skips it).
#  2. Seeds: fetch v7sq-sd1..3 (members of the v7xbag seed bag).
#  3. R2: when e5lsr2g is done (qstr2g was stopped at 12:01 and marked failed), ship e5l/bge/qst/e5ls outputs, run
#     box3_r2_remote.sh on the box (gates, cmq5g, stage 2 v7sq5g), fetch it and mark v7sq5g_state/s2.done.
# Logs to work/logs/box3_after.log. Ends "BOX3 AFTER DONE".
set -uo pipefail
H=grenuke-vast3; R=/workspace/grenuke
SP=$SCRATCH
rsh() { ssh -n -o ConnectTimeout=20 $H "$@" 2>&1 | grep -vE "^Welcome|^Have fun|^AI agents"; }
ended() { rsh "pgrep -f '[t]ag ameya-s2-$1 ' > /dev/null || echo ended" | grep -q ended; }
echo "$(date +%H:%M:%S) start (after2)"
for t in v7sqwg v7sq-sd1 v7sq-sd2 v7sq-sd3; do
  until ended $t; do sleep 30; done
  echo "$(date +%H:%M:%S) $t stage 2 ended on the box: $(rsh "tail -c 160 $R/logs/s2_$t.log | tail -1 | cut -c1-110")"
  bash $SP/box3_fetch_s2.sh $t 2>&1 | tail -3
done
for n in e5lsr2g qstr2g; do
  until rsh "grep -qE 'done in|Traceback' $R/logs/ce_$n.log && echo y" | grep -q y; do sleep 60; done
  echo "$(date +%H:%M:%S) $n: $(rsh "grep -E 'done in|Traceback' $R/logs/ce_$n.log | tail -1 | cut -c1-120")"
done
for s in e5l bge qst e5ls; do rsh "mkdir -p $R/box/out_$s" > /dev/null; scp -q $SP/box/out_$s/ce_train.parquet $SP/box/out_$s/ce_test.parquet $SP/box/out_$s/config.json $H:$R/box/out_$s/; done
scp -q $SP/box3_r2_remote.sh $H:$R/r2_remote.sh
rsh "cd $R && THREADS=96 nohup bash r2_remote.sh > $R/logs/r2_chain.log 2>&1 < /dev/null & sleep 5; cat $R/logs/r2_chain.log"
echo "$(date +%H:%M:%S) R2 chain launched on the box"
until rsh "grep -qE 'R2 S2 DONE|R2 FAILED' $R/logs/r2_chain.log && echo y" | grep -q y; do sleep 60; done
rsh "tail -6 $R/logs/r2_chain.log"
if rsh "grep -q 'R2 S2 DONE' $R/logs/r2_chain.log && echo y" | grep -q y; then bash $SP/box3_fetch_s2.sh v7sq5g 2>&1 | tail -3; fi
echo "$(date +%H:%M:%S) BOX3 AFTER DONE"
