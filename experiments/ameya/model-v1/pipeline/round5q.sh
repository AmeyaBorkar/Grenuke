#!/bin/bash
# 7B-corrected round-4 labels: pseudo_labels.py on mixf7 (France = v7sq6r3 minus the 7B rejects), pseudo_guard.py, then the
# 859 French pairs the 7B rejects forced to y = 0 (pseudo_labels leaves them unlabelled because their pc is high) ->
# grenuke-vast3 stage 2 v7sq6q4 / v7sq7q4 (box3_r15.sh). Ends "R5Q LABELS DONE" / "... FAILED".
SP=/c/Users/ameya/AppData/Local/Temp/claude/C--Users-ameya-Documents-GrenukeAmazon/19e315ba-0725-4d6f-ae6a-972e1c1f0aa9/scratchpad
SPW=C:/Users/ameya/AppData/Local/Temp/claude/C--Users-ameya-Documents-GrenukeAmazon/19e315ba-0725-4d6f-ae6a-972e1c1f0aa9/scratchpad
FS=C:/Users/ameya/Documents/GrenukeAmazon/.claude/worktrees/final-stack/experiments/ameya/model-v1
source $SP/env6.sh > /dev/null
cd /c/Users/ameya/Documents/GrenukeAmazon
python $FS/pseudo_labels.py ameya-model-v7sq6r3-s3 ameya-s3-v7sq6r3 ameya-model-v7sq6r3-s3-ops3 ameya-model-mixf7 s1:ameya-s1-v6all $SPW/box/pseudo_s2_fr_mixf7q.parquet \
  || { echo "$(date +%H:%M) R5Q LABELS FAILED pseudo_labels"; exit 1; }
python $FS/pseudo_guard.py $SPW/box/pseudo_s2_fr_v7ce3.parquet $SPW/box/pseudo_s2_fr_mixf7q.parquet $SPW/box/rulepop_fr.parquet $SPW/box/pseudo_s2_fr_mixf7q_guard.parquet \
  || { echo "$(date +%H:%M) R5Q LABELS FAILED guard"; exit 1; }
python - <<PY || { echo "$(date +%H:%M) R5Q LABELS FAILED force"; exit 1; }
import numpy as np, pandas as pd
K = 4_000_000_000
p = pd.read_parquet(r"$SPW/box/pseudo_s2_fr_mixf7q_guard.parquet")
q = pd.read_parquet(r"$SPW/q7drop/drop_q7_fr.parquet")
k = np.isin(p.s1.to_numpy(np.int64) * K + p.r.to_numpy(np.int64), q.s1.to_numpy(np.int64) * K + q.r.to_numpy(np.int64))
print("7B-rejected pairs in the label set:", int(k.sum()), "of", len(q), "; labels before:", p.y[k].value_counts().to_dict())
p.loc[k, "y"] = 0
p.to_parquet(r"$SPW/box/pseudo_s2_fr_mixf7q_guard.parquet", index=False)
r3 = pd.read_parquet(r"$SPW/box/pseudo_s2_fr_mixmdp_guard.parquet").merge(p, on=["s1", "r"], suffixes=("_r3", "_q4"))
print("round 3 -> 7B-corrected round 4: changed", int((r3.y_r3 != r3.y_q4).sum()), pd.crosstab(r3.y_r3, r3.y_q4).to_dict())
PY
scp -q $SP/box/pseudo_s2_fr_mixf7q_guard.parquet grenuke-vast3:/workspace/grenuke/box/ && scp -q $SP/box3_r15.sh grenuke-vast3:/workspace/grenuke/ || { echo "$(date +%H:%M) R5Q LABELS FAILED upload"; exit 1; }
ssh -n grenuke-vast3 'cd /workspace/grenuke; setsid nohup bash box3_r15.sh > logs/box3_r15.log 2>&1 < /dev/null &' 2>/dev/null
echo "$(date +%H:%M) R5Q LABELS DONE"
