#!/bin/bash
SP=/c/Users/ameya/AppData/Local/Temp/claude/C--Users-ameya-Documents-GrenukeAmazon/19e315ba-0725-4d6f-ae6a-972e1c1f0aa9/scratchpad
source $SP/env6.sh > /dev/null; K=~/.ssh/grenuke_vast2; H="root@31.13.237.164"
until ssh -n -o ConnectTimeout=15 -i $K -p 42151 $H "grep -q 'Q7ENS DONE' /workspace/grenuke/q7ens/run.log && echo yes" 2>/dev/null | grep -q yes; do
  [ "$(date +%H%M)" -gt 2230 ] && { echo "$(date +%H:%M) ENS never finished"; exit 0; }; sleep 30; done
ssh -n -i $K -p 42151 $H "cat /workspace/grenuke/q7ens/run.log" 2>/dev/null | grep -vE "^Welcome|^Have fun|^AI agents"
for f in adapter_1_train adapter_1_test adapter_2_train adapter_2_test; do scp -q -i $K -P 42151 "$H:/workspace/grenuke/q7ens/$f.parquet" $SP/q7ens/ || echo "fetch $f FAILED"; done
cd /c/Users/ameya/Documents/GrenukeAmazon && python $SP/q7ens/eval_ens.py 2>&1 | grep -v Warning | tail -24
echo "$(date +%H:%M) ENS EVAL READY"
