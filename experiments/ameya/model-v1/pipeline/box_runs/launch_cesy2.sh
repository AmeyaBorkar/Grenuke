#!/bin/bash
# Bakshi's training box: the two synthetic-French cross-encoders (synth_fr2 data, ce_synth2) on the H100s his jobs leave
# free, never on a GPU his scheduler (sched_q34.sh) claims. A: the q7st GPU among 0-2 without a .q34_gpu<g> marker, after
# both q34st groups are assigned and that GPU is empty. B: GPU 3 after q34st group 0 has written part_0.npz and freed it.
R=/workspace/grenuke; A=$R/ameya; L=$A/logs/launch.log
cd $A && . ./env.sh
mem() { nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i $1 | tr -d ' '; }
run() {  # run <gpu> <name> <model> [extra]
  echo "$(date -u +%T) GPU$1 -> $2" >> $L
  CUDA_VISIBLE_DEVICES=$1 python ce_synth2.py --name $2 --model $3 --lr 2e-5 --batch 128 --epochs 1 --us-in-frac 0.5 \
    --target-only-test --hold-groups 0 ${4:-} > $A/logs/ce_$2.log 2>&1
  echo "$(date -u +%T) $2 exit $?" >> $L
}
(
  until [ "$(grep -c 'freed by q7st' $R/logs/sched_q34.log 2>/dev/null)" -ge 2 ]; do sleep 30; done
  g=""; for c in 0 1 2; do [ -f $R/logs/.q34_gpu$c ] || g=$c; done
  [ -z "$g" ] && { echo "$(date -u +%T) A: no unclaimed GPU" >> $L; exit 0; }
  until [ -f $R/box/out_q7st/part_$g.npz ] && [ "$(mem $g)" -lt 2000 ]; do sleep 30; done
  sleep 60; [ "$(mem $g)" -lt 2000 ] && run $g cesy2 intfloat/multilingual-e5-large || echo "$(date -u +%T) A: GPU$g busy again" >> $L
) &
(
  until [ -f $R/box/out_q34st/part_0.npz ] && [ "$(mem 3)" -lt 2000 ]; do sleep 30; done
  sleep 60; [ "$(mem 3)" -lt 2000 ] && run 3 cesy2b BAAI/bge-reranker-v2-m3 "--synth-weight 2" || echo "$(date -u +%T) B: GPU3 busy again" >> $L
) &
wait
echo "$(date -u +%T) LAUNCH DONE" >> $L
