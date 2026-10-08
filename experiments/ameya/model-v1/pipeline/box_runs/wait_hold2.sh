#!/bin/bash
SP=$SCRATCH
source $SP/env6.sh > /dev/null
until ssh -n -o ConnectTimeout=15 grenuke-vast3 "grep -qE 'HOLD2 (DONE|FAILED)' /workspace/grenuke/q7ens/run_hold2.log && echo yes" 2>/dev/null | grep -q yes; do sleep 20; done
ssh -n grenuke-vast3 "cat /workspace/grenuke/q7ens/run_hold2.log" 2>/dev/null | grep -vE "^Welcome|^Have fun|^AI agents"
scp -q grenuke-vast3:/workspace/grenuke/q7ens/hold2_scored.parquet $SP/q7ens/ && cd $REPO && python $SP/q7ens/eval_hold2.py 2>&1 | grep -v Warning | tail -12
echo "$(date +%H:%M) HOLD2 EVAL READY"
