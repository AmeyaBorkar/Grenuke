#!/bin/bash
# copy each finished synthetic-French cross-encoder to grenuke-vast3:/workspace/grenuke/box/out_<name>/ via the laptop.
SP=/c/Users/ameya/AppData/Local/Temp/claude/C--Users-ameya-Documents-GrenukeAmazon/19e315ba-0725-4d6f-ae6a-972e1c1f0aa9/scratchpad
K=~/.ssh/grenuke_vast2; mkdir -p $SP/synth_out
declare -A HOST=( [cesy2]="202.122.49.242 28860 /workspace/grenuke/ameya/box_cesy2" [cesy2b]="202.122.49.242 28860 /workspace/grenuke/ameya/box_cesy2" [cesyb]="216.144.178.146 48742 /workspace/grenuke/box_cesy" )
todo="cesy2 cesy2b cesyb"
while [ -n "$todo" ]; do
  for n in $todo; do
    set -- ${HOST[$n]}; h=$1; p=$2; d=$3
    if ssh -n -o ConnectTimeout=15 -i $K -p $p root@$h "test -s $d/out_$n/config.json && test -s $d/out_$n/ce_test.parquet && echo yes" 2>/dev/null | grep -q yes; then
      mkdir -p $SP/synth_out/out_$n && scp -q -i $K -P $p "root@$h:$d/out_$n/ce_train.parquet" "root@$h:$d/out_$n/ce_test.parquet" "root@$h:$d/out_$n/config.json" $SP/synth_out/out_$n/ \
        && ssh -n grenuke-vast3 "mkdir -p /workspace/grenuke/box/out_$n" 2>/dev/null && scp -q $SP/synth_out/out_$n/* grenuke-vast3:/workspace/grenuke/box/out_$n/ \
        && echo "$(date +%H:%M) READY-SYNTH $n $(python -c "import json; c=json.load(open(r'$(cygpath -w $SP/synth_out/out_$n/config.json)')); print(c.get('auc'))")" \
        && todo=$(echo " $todo " | sed "s/ $n / /" | xargs)
    fi
  done
  [ "$(date +%H%M)" -gt 1930 ] && { echo "$(date +%H:%M) RELAY GAVE UP on: $todo"; break; }
  sleep 60
done
echo "$(date +%H:%M) FINAL25 DONE"
