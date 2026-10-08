#!/bin/bash
SP=$SCRATCH
source $SP/env6.sh > /dev/null; K=~/.ssh/grenuke_vast2; H="root@<gpu-host>"
until ssh -n -o ConnectTimeout=15 -i $K -p <port> $H "grep -q 'Q7ENS DONE' /workspace/grenuke/q7ens/run.log && echo yes" 2>/dev/null | grep -q yes; do
  [ "$(date +%H%M)" -gt 2230 ] && { echo "$(date +%H:%M) ENS never finished"; exit 0; }; sleep 30; done
ssh -n -i $K -p <port> $H "cat /workspace/grenuke/q7ens/run.log" 2>/dev/null | grep -vE "^Welcome|^Have fun|^AI agents"
for f in adapter_1_train adapter_1_test adapter_2_train adapter_2_test; do scp -q -i $K -P <port> "$H:/workspace/grenuke/q7ens/$f.parquet" $SP/q7ens/ || echo "fetch $f FAILED"; done
cd $REPO && python $SP/q7ens/eval_ens.py 2>&1 | grep -v Warning | tail -24
echo "$(date +%H:%M) ENS EVAL READY"
