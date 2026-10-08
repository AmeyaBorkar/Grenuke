#!/bin/bash
# Round-4 stage-2 labels from mixqc (v7sq3 US/India + v7sq6r3 France, no look-alike drop; the cal leader): pseudo_labels.py
# (French decisions of mixqc, pc of v7sq6r3's stage 3) -> pseudo_guard.py (round-1 labels for empty-address records, rule
# populations override) -> grenuke-vast3: stage 2 v7sq6r4 (cmq6), guarded x3 (box3_r14.sh). Ends "R4 LABELS DONE" / "... FAILED".
SP=$SCRATCH
SPW=$SCRATCH
FS=$REPO/.claude/worktrees/final-stack/experiments/ameya/model-v1
source $SP/env6.sh > /dev/null
cd $REPO
echo "$(date +%H:%M) round-4 labels start"
python $FS/pseudo_labels.py ameya-model-v7sq6r3-s3 ameya-s3-v7sq6r3 ameya-model-v7sq6r3-s3-ops3 ameya-model-mixqc s1:ameya-s1-v6all $SPW/box/pseudo_s2_fr_mixqc.parquet \
  || { echo "$(date +%H:%M) R4 LABELS FAILED pseudo_labels"; exit 1; }
python $FS/pseudo_guard.py $SPW/box/pseudo_s2_fr_v7ce3.parquet $SPW/box/pseudo_s2_fr_mixqc.parquet $SPW/box/rulepop_fr.parquet $SPW/box/pseudo_s2_fr_mixqc_guard.parquet \
  || { echo "$(date +%H:%M) R4 LABELS FAILED guard"; exit 1; }
python -c "
import pandas as pd
a = pd.read_parquet(r'$SPW/box/pseudo_s2_fr_mixmdp_guard.parquet'); b = pd.read_parquet(r'$SPW/box/pseudo_s2_fr_mixqc_guard.parquet')
m = a.merge(b, on=['s1', 'r'], suffixes=('_r3', '_r4'))
print('round 3 -> 4 labels:', len(a), len(b), 'changed', int((m.y_r3 != m.y_r4).sum()), pd.crosstab(m.y_r3, m.y_r4).to_dict())
"
scp -q $SP/box/pseudo_s2_fr_mixqc_guard.parquet $SP/box3_r14.sh grenuke-vast3:/workspace/grenuke/box/ || { echo "$(date +%H:%M) R4 LABELS FAILED upload"; exit 1; }
ssh -n grenuke-vast3 'cd /workspace/grenuke; mv box/box3_r14.sh . && setsid nohup bash box3_r14.sh > logs/box3_r14.log 2>&1 < /dev/null &' 2>/dev/null
echo "$(date +%H:%M) R4 LABELS DONE"
