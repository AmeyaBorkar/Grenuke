#!/usr/bin/env bash
# Stack the validated rules on a packaged model: stack_model.sh <model> (e.g. v7s)
#   1. hunt rules at the model's decide threshold: acr + cap + nsa@US+India (agents/hunt/apply_hunt.py)
#   2. France narrowed (stack/make_h2.py): only number-dropped acronym adds, no cap drops -> tag ...-h2
#   3. polish for countries without labels: copy + city (agents/polish/apply_polish.py) -> tag ...-h2pc, packaged
#   4. French COPY/SWAP check (fhs.py) vs v7nst and vs the model
# Each python step waits while agents/PAUSE exists or less than 8 GB is available.
set -euo pipefail
SP=/c/Users/ameya/AppData/Local/Temp/claude/C--Users-ameya-Documents-GrenukeAmazon/19e315ba-0725-4d6f-ae6a-972e1c1f0aa9/scratchpad
SPW=C:/Users/ameya/AppData/Local/Temp/claude/C--Users-ameya-Documents-GrenukeAmazon/19e315ba-0725-4d6f-ae6a-972e1c1f0aa9/scratchpad
source $SP/env6.sh > /dev/null
M=$1
FIN=ameya-model-$M-s3-ops3a; SC=ameya-s3-$M; CA=ameya-cands-$M-c2a
wait_ok() {
  while true; do
    [ -f $SP/agents/PAUSE ] && { sleep 30; continue; }
    a=$(powershell -NoProfile -Command "(Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory).AvailableMBytes" | tr -d '\r')
    [ "${a:-0}" -ge 8000 ] && return 0; sleep 30
  done
}
THR=$(python -c "import json; print(json.load(open('C:/Users/ameya/Documents/GrenukeAmazon/work/reports/ameya-model-$M-s3.json'))['rule']['threshold'])")
echo "$(date +%H:%M:%S) $M: threshold $THR"
wait_ok; (cd $SP/agents/hunt && python -W ignore apply_hunt.py --matches $FIN --scores $SC --cands $CA --thr $THR --rules acr,cap,nsa@US+India --out hunted_$M 2>&1 | tail -2)
wait_ok; python $SP/stack/make_h2.py $FIN $SPW/agents/hunt/hunted_$M.parquet $SPW/agents/hunt/hunted_${M}_changes.csv $SPW/stack/${M}_h2.parquet | head -1
wait_ok; python - $SPW/stack/${M}_h2.parquet $FIN-h2 $CA <<'PY'
import sys, numpy as np, pandas as pd
from ber.artifacts import read_table, write_table
pq_, tag, cands = sys.argv[1:4]
m = pd.read_parquet(pq_)[["s1", "r"]].astype("int64")
assert not m.r.duplicated().any()
c = read_table("candidates", cands, "test", ["s1", "r"]); K = 4_000_000_000
assert np.isin(m.s1.to_numpy() * K + m.r.to_numpy(), c.s1.to_numpy() * K + c.r.to_numpy()).all()
write_table(m, "matches", tag, "test", command=f"stack_model.sh import {pq_}")
print(f"imported {len(m)} pairs as matches/{tag}")
PY
mkdir -p $SP/stack/${M}_pc
wait_ok; (cd $SP/agents/polish && python apply_polish.py $FIN-h2 --cands $CA --scores $SC --rules copy,city --out-dir $SPW/stack/${M}_pc 2>&1 | grep -E "changes|dropped" | tail -2)
wait_ok; bash $SP/stack_pkg.sh $SPW/stack/${M}_pc/polished_$FIN-h2.parquet $FIN-h2pc $CA 2026-09-27-$M-s3-ops3a-h2pc-c2 2>&1 | grep -E "imported|PASS|FAIL|Error|matching_results.tsv$"
wait_ok; (cd /c/Users/ameya/Documents/GrenukeAmazon/.claude/worktrees/final-night && python experiments/ameya/model-v1/fhs.py ameya-model-v7nst-s3-ops3a $FIN $FIN-h2pc 2>&1 | tail -3)
echo "$(date +%H:%M:%S) STACK DONE $M"
