#!/bin/bash
# relay cesy3g from the new RTX 5090 (<gpu-host>:42151) to grenuke-vast3 box/out_cesy3g via the laptop. Ends "READY-SYNTH cesy3g" or gives up at 19:45.
SP=$SCRATCH
K=~/.ssh/grenuke_vast2; H=root@<gpu-host>; d=/workspace/grenuke/box_s3/out_cesy3g
until ssh -n -o ConnectTimeout=15 -i $K -p <port> $H "test -s $d/config.json && test -s $d/ce_test.parquet && echo yes" 2>/dev/null | grep -q yes; do
  [ "$(date +%H%M)" -gt 1945 ] && { echo "$(date +%H:%M) cesy3g never arrived"; exit 0; }; sleep 60; done
mkdir -p $SP/synth_out/out_cesy3g
for f in ce_train.parquet ce_test.parquet config.json; do
  for t in 1 2 3; do scp -q -i $K -P <port> "$H:$d/$f" $SP/synth_out/out_cesy3g/ && break; sleep 10; done
done
ls $SP/synth_out/out_cesy3g/ | grep -c . | grep -q 3 || { echo "$(date +%H:%M) cesy3g fetch FAILED"; exit 1; }
ssh -n grenuke-vast3 "mkdir -p /workspace/grenuke/box/out_cesy3g.tmp" 2>/dev/null \
  && scp -q $SP/synth_out/out_cesy3g/* grenuke-vast3:/workspace/grenuke/box/out_cesy3g.tmp/ \
  && ssh -n grenuke-vast3 "rm -rf /workspace/grenuke/box/out_cesy3g && mv /workspace/grenuke/box/out_cesy3g.tmp /workspace/grenuke/box/out_cesy3g" \
  && echo "$(date +%H:%M) READY-SYNTH cesy3g $(python -c "import json; print(json.load(open(r'$(cygpath -w $SP/synth_out/out_cesy3g/config.json)')).get('auc'))")"
