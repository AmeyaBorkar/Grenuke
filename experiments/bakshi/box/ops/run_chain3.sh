#!/usr/bin/env bash
# Resume after s1.py crashed on its optional baseline comparison (matches/ameya-baseline-v0 does not exist here).
# The stage-1 models and TRAIN scores were saved before the crash; only the test scoring is missing.
cd /workspace/grenuke
. ./env.sh
L=logs
cd repo/experiments/ameya/model-v1
python - <<'PY' >> ../../../../$L/phaseA.log 2>&1
import pandas as pd
from ber.artifacts import write_table
write_table(pd.DataFrame({"s1": pd.Series([], dtype="int64"), "r": pd.Series([], dtype="int64")}), "matches",
            "ameya-baseline-v0", "train",
            command="PLACEHOLDER (Bakshi box): EMPTY baseline so s1.py/s2.py gate reports run. Ignore gate_vs_baseline.",
            inputs={})
print("placeholder ameya-baseline-v0 written (empty; report comparisons only)")
PY
echo "$(date +%T) START s1_test (test-only from saved models)" >> ../../../../$L/phaseA.log
if python s1.py --feats ameya-fx5 --tag ameya-s1-v6all --groups str,cx,lo0,lg,nx --drop leg__r_only_bits,leg__s1_only_bits \
     --all --test-only > ../../../../$L/A_s1_test.log 2>&1; then
  touch ../../../../$L/.doneA_s1; echo "$(date +%T) DONE  s1 (train from run 1, test from --test-only)" >> ../../../../$L/phaseA.log
else
  echo "$(date +%T) FAIL  s1_test" >> ../../../../$L/phaseA.log; exit 1
fi
cd /workspace/grenuke
bash repo/experiments/bakshi/box/phaseA.sh && CUDA_VISIBLE_DEVICES=0 bash repo/experiments/bakshi/box/phaseB.sh g0 "e5l qst e5ls bge" /workspace/grenuke/box_ameya/pseudo_s2_fr_v7ce3.parquet
echo "chain3 exit $?" >> $L/phaseA.log
