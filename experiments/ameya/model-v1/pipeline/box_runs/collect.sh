#!/bin/bash
# fetch each out-of-band detector when it finishes (config.json + ce_test.parquet), evaluate it (eval_det.py), log "DET READY".
SP=$SCRATCH
source $SP/env6.sh > /dev/null; K=~/.ssh/grenuke_vast2
declare -A SRC=( [cesyoob]="-i $K -P <port> root@<gpu-host>:/workspace/grenuke/box_oob/out_cesyoob"
                 [cesyoobg]="-i $K -P <port> root@<gpu-host>:/workspace/grenuke/box_oob/out_cesyoobg"
                 [cesyoobh]="grenuke-vast3:/workspace/grenuke/box_oob/out_cesyoobh"
                 [cesyoobL]="grenuke-vast3:/workspace/grenuke/box_oob/out_cesyoobL"
                 [cesyoobl]="-i $K -P <port> root@<gpu-host>:/workspace/grenuke/ameya_oob/box_l/out_cesyoobl"
                 [cesyoobb]="-i $K -P <port> root@<gpu-host>:/workspace/grenuke/ameya_oob/box_b/out_cesyoobb" )
todo="cesyoob cesyoobh cesyoobL cesyoobg cesyoobl cesyoobb"
while [ -n "$todo" ] && [ "$(date +%H%M)" -lt 2130 ]; do
  for n in $todo; do
    s=${SRC[$n]}; opts=${s% *}; [ "$opts" = "$s" ] && opts=""; loc=${s##* }; host=${loc%%:*}; dir=${loc#*:}
    port=$(echo "$opts" | sed -n 's/.*-P \([0-9]*\).*/\1/p')
    if [ -n "$port" ]; then chk="ssh -n -o ConnectTimeout=15 -i $K -p $port $host"; else chk="ssh -n -o ConnectTimeout=15 $host"; fi
    $chk "test -s $dir/config.json && test -s $dir/ce_test.parquet && echo yes" 2>/dev/null | grep -q yes || continue
    mkdir -p $SP/oob/out_$n
    scp -q $opts "$loc/ce_train.parquet" "$loc/ce_test.parquet" "$loc/config.json" $SP/oob/out_$n/ 2>/dev/null || continue
    echo "$(date +%H:%M) DET READY $n $(python -c "import json; print(json.load(open(r'$(cygpath -w $SP/oob/out_$n/config.json)')).get('auc'))")"
    (cd $REPO && python $SP/oob/eval_det.py "$(cygpath -m $SP/oob/out_$n)" 2>&1 | tail -14)
    todo=$(echo " $todo " | sed "s| $n | |; s|^ *||; s| *$||")
  done
  [ -n "$todo" ] && sleep 60
done
echo "$(date +%H:%M) DET COLLECT DONE (not collected: ${todo:-none})"
