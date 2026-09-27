#!/usr/bin/env bash
# GPU scheduler for the second wave on the 4x H100 training box (run via: train_jobs.sh after7b, under nohup).
#
# Measured on this box: GPU 3 is thermally throttled (86 C, "SW Thermal Slowdown", 345-1380 MHz vs 1980 on GPUs 0-2)
# and runs at about half speed. mDeBERTa (every step non-finite in bf16) and gte (remote code: index out of bounds
# under transformers 5.17) both failed on this stack and are dropped. So:
#   GPU 3 now                          q34st group 2 starts training (half speed)
#   first two GPUs the 7B frees        q34st group 0 (resumes from its step-981 checkpoint), q34st group 1
#   third GPU the 7B frees             group 2 moves there: at its next checkpoint the GPU-3 process is stopped and the
#                                      group resumes at full speed. If it has already finished training (adapter DONE)
#                                      it is left to finish on GPU 3: stopping it mid prediction-set is not safe.
# then q34st's parts are merged. The q7st merge watcher from `launch` is untouched.
set -uo pipefail
R=/workspace/grenuke
J="bash $R/repo/experiments/bakshi/box/train_jobs.sh"
LOGS=$R/logs
O=$R/box/out_q34st
Q34=Qwen/Qwen3-4B-Base
PAT2="llm_group.py --model $Q34 --name q34st --group 2"
log() { echo "$(date -u +%H:%M:%S) $*"; }

log "GPU3 -> q34st g2"
( $J run-group q34st $Q34 3 2 >> $LOGS/q34st_g2.log 2>&1; log "q34st g2 (GPU3) exit $?" ) &

free_gpu() {  # $1 = 7B group/GPU index: free once its part is written and its process is gone
  [ -f $R/box/out_q7st/part_$1.npz ] && ! pgrep -f "llm_group.py --model Qwen/Qwen2.5-7B --name q7st --group $1" >/dev/null
}

queue=(0 1 move2)
used=""
while [ ${#queue[@]} -gt 0 ]; do
  for g in 0 1 2; do
    [ ${#queue[@]} -gt 0 ] || break
    case " $used " in *" $g "*) continue ;; esac
    free_gpu $g || continue
    job=${queue[0]}
    queue=("${queue[@]:1}")
    used="$used $g"
    case $job in
      0|1)
        log "GPU$g free -> q34st g$job"
        ( $J run-group q34st $Q34 $g $job >> $LOGS/q34st_g$job.log 2>&1; log "q34st g$job exit $?" ) & ;;
      move2)
        if [ -f $O/part_2.npz ]; then
          log "GPU$g free; q34st g2 already finished on GPU3"
        elif [ -f $O/adapter_2/DONE ]; then
          log "GPU$g free; q34st g2 already trained, predicting on GPU3: left there"
        else
          ( t0=$(stat -c %Y $O/ckpt_2.pt 2>/dev/null || echo 0)
            log "GPU$g free -> moving q34st g2 at its next checkpoint (current ckpt mtime $t0)"
            while pgrep -f "$PAT2" >/dev/null && [ ! -f $O/adapter_2/DONE ] \
                  && [ "$(stat -c %Y $O/ckpt_2.pt 2>/dev/null || echo 0)" = "$t0" ]; do sleep 3; done
            if [ -f $O/adapter_2/DONE ]; then
              log "q34st g2 finished training on GPU3 before its checkpoint; left there"
            else
              pkill -f "$PAT2"
              while pgrep -f "$PAT2" >/dev/null; do sleep 1; done
              log "stopped q34st g2 on GPU3 right after its checkpoint; resuming on GPU$g"
              $J run-group q34st $Q34 $g 2 >> $LOGS/q34st_g2.log 2>&1
              log "q34st g2 (GPU$g) exit $?"
            fi ) &
        fi ;;
    esac
  done
  sleep 30
done
wait
log "all second-wave jobs ended; merging q34st"
$J merge q34st > $LOGS/q34st_merge.log 2>&1
log "q34st merge exit $?"
