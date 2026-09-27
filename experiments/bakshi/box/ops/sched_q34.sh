#!/usr/bin/env bash
# Qwen3-4B (q34st) on every GPU the 7B does not need: group 0 on GPU 3 now (resumes from its checkpoint), groups 1
# and 2 on the first two GPUs that q7st frees (q7st group g runs on GPU g; it is free once part_g.npz exists), then merge.
R=/workspace/grenuke; J=$R/repo/experiments/bakshi/box/train_jobs.sh; L=$R/logs/sched_q34.log; B=$R/box
cd $R
echo "$(date -u +%T) GPU3 -> q34st g0" >> $L
setsid nohup bash $J run-group q34st Qwen/Qwen3-4B-Base 3 0 > $R/logs/q34st_g0.log 2>&1 < /dev/null &
todo=(1 2)
while [ ${#todo[@]} -gt 0 ]; do
  for gpu in 0 1 2; do
    [ ${#todo[@]} -eq 0 ] && break
    if [ -f $B/out_q7st/part_$gpu.npz ] && [ ! -f $R/logs/.q34_gpu$gpu ] && ! pgrep -f "q7st --group $gpu" >/dev/null; then
      g=${todo[0]}; todo=("${todo[@]:1}"); touch $R/logs/.q34_gpu$gpu
      echo "$(date -u +%T) GPU$gpu freed by q7st -> q34st g$g" >> $L
      setsid nohup bash $J run-group q34st Qwen/Qwen3-4B-Base $gpu $g > $R/logs/q34st_g$g.log 2>&1 < /dev/null &
    fi
  done
  sleep 30
done
until [ -f $B/out_q34st/part_0.npz ] && [ -f $B/out_q34st/part_1.npz ] && [ -f $B/out_q34st/part_2.npz ]; do sleep 60; done
echo "$(date -u +%T) all q34st parts -> merge" >> $L
bash $J merge q34st >> $R/logs/q34st_merge.log 2>&1
echo "$(date -u +%T) q34st merge exit $?" >> $L
