#!/bin/bash
# relay cesy3x from the RTX 5090 #1 (180.189.55.43:28839) to grenuke-vast3 box/out_cesy3x via the laptop. Ends "READY-SYNTH cesy3x" or gives up at 19:25.
SP=/c/Users/ameya/AppData/Local/Temp/claude/C--Users-ameya-Documents-GrenukeAmazon/19e315ba-0725-4d6f-ae6a-972e1c1f0aa9/scratchpad
K=~/.ssh/grenuke_vast2; H=root@180.189.55.43; d=/workspace/grenuke/box_s3x/out_cesy3x
until ssh -n -o ConnectTimeout=15 -i $K -p 28839 $H "test -s $d/config.json && test -s $d/ce_test.parquet && echo yes" 2>/dev/null | grep -q yes; do
  [ "$(date +%H%M)" -gt 1925 ] && { echo "$(date +%H:%M) cesy3x never arrived"; exit 0; }; sleep 60; done
mkdir -p $SP/synth_out/out_cesy3x
for f in ce_train.parquet ce_test.parquet config.json; do
  for t in 1 2 3; do scp -q -i $K -P 28839 "$H:$d/$f" $SP/synth_out/out_cesy3x/ && break; sleep 10; done
done
ls $SP/synth_out/out_cesy3x/ | grep -c . | grep -q 3 || { echo "$(date +%H:%M) cesy3x fetch FAILED"; exit 1; }
ssh -n grenuke-vast3 "mkdir -p /workspace/grenuke/box/out_cesy3x.tmp" 2>/dev/null \
  && scp -q $SP/synth_out/out_cesy3x/* grenuke-vast3:/workspace/grenuke/box/out_cesy3x.tmp/ \
  && ssh -n grenuke-vast3 "rm -rf /workspace/grenuke/box/out_cesy3x && mv /workspace/grenuke/box/out_cesy3x.tmp /workspace/grenuke/box/out_cesy3x" \
  && echo "$(date +%H:%M) READY-SYNTH cesy3x $(python -c "import json; print(json.load(open(r'$(cygpath -w $SP/synth_out/out_cesy3x/config.json)')).get('auc'))")"
