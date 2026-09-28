#!/bin/bash
# relay cesy3b from the RTX 5090 to grenuke-vast3 box/out_cesy3b via the laptop. Ends "READY-SYNTH cesy3b" or gives up at 19:00.
SP=/c/Users/ameya/AppData/Local/Temp/claude/C--Users-ameya-Documents-GrenukeAmazon/19e315ba-0725-4d6f-ae6a-972e1c1f0aa9/scratchpad
K=~/.ssh/grenuke_vast2; d=/workspace/grenuke/box_s3/out_cesy3b
until ssh -n -o ConnectTimeout=15 -i $K -p 28839 root@180.189.55.43 "test -s $d/config.json && test -s $d/ce_test.parquet && echo yes" 2>/dev/null | grep -q yes; do
  [ "$(date +%H%M)" -gt 1900 ] && { echo "$(date +%H:%M) cesy3b never arrived"; exit 0; }; sleep 60; done
mkdir -p $SP/synth_out/out_cesy3b && scp -q -i $K -P 28839 "root@180.189.55.43:$d/ce_train.parquet" "root@180.189.55.43:$d/ce_test.parquet" "root@180.189.55.43:$d/config.json" $SP/synth_out/out_cesy3b/ \
  && ssh -n grenuke-vast3 "mkdir -p /workspace/grenuke/box/out_cesy3b" 2>/dev/null && scp -q $SP/synth_out/out_cesy3b/* grenuke-vast3:/workspace/grenuke/box/out_cesy3b/ \
  && echo "$(date +%H:%M) READY-SYNTH cesy3b $(python -c "import json; print(json.load(open(r'$(cygpath -w $SP/synth_out/out_cesy3b/config.json)')).get('auc'))")"
