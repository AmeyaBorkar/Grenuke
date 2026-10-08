#!/bin/bash
# relay cesy3g from the new RTX 5090 to grenuke-vast3 box/out_cesy3g via the laptop. Ends "READY-SYNTH cesy3g" or gives up at 19:00.
SP=$SCRATCH
K=~/.ssh/grenuke_vast2; d=/workspace/grenuke/box_s3/out_cesy3g
until ssh -n -o ConnectTimeout=15 -i $K -p <port> root@<gpu-host> "test -s $d/config.json && test -s $d/ce_test.parquet && echo yes" 2>/dev/null | grep -q yes; do
  [ "$(date +%H%M)" -gt 1945 ] && { echo "$(date +%H:%M) cesy3g never arrived"; exit 0; }; sleep 60; done
mkdir -p $SP/synth_out/out_cesy3g && scp -q -i $K -P <port> "root@<gpu-host>:$d/ce_train.parquet" "root@<gpu-host>:$d/ce_test.parquet" "root@<gpu-host>:$d/config.json" $SP/synth_out/out_cesy3g/ \
  && ssh -n grenuke-vast3 "mkdir -p /workspace/grenuke/box/out_cesy3g" 2>/dev/null && scp -q $SP/synth_out/out_cesy3g/* grenuke-vast3:/workspace/grenuke/box/out_cesy3g/ \
  && echo "$(date +%H:%M) READY-SYNTH cesy3g $(python -c "import json; print(json.load(open(r'$(cygpath -w $SP/synth_out/out_cesy3g/config.json)')).get('auc'))")"
