#!/bin/bash
# Round-3 stage-2 labels from the LB-measured final mixmdp (0.990699): pseudo_labels.py (French decisions of mixmdp,
# pc of v7sq7wg's stage 3) -> pseudo_guard.py (round-1 labels for empty-address records, rule populations override) ->
# grenuke-vast3: stage 2 v7sq6r3 (cmq6) and v7sq7r3 (cmq7), guarded x3. Ends "R3 LABELS DONE" / "... FAILED".
SP=$SCRATCH
SPW=$SCRATCH
FS=$REPO/.claude/worktrees/final-stack/experiments/ameya/model-v1
source $SP/env6.sh > /dev/null
while ps -ef | grep -q "[r]un_local_full"; do sleep 30; done
cd $REPO
python $FS/pseudo_labels.py ameya-model-v7sq7wg-s3 ameya-s3-v7sq7wg ameya-model-v7sq7wg-s3-ops3 ameya-model-mixmdp s1:ameya-s1-v6all $SPW/box/pseudo_s2_fr_mixmdp.parquet \
  || { echo "$(date +%H:%M) R3 LABELS FAILED pseudo_labels"; exit 1; }
python $FS/pseudo_guard.py $SPW/box/pseudo_s2_fr_v7ce3.parquet $SPW/box/pseudo_s2_fr_mixmdp.parquet $SPW/box/rulepop_fr.parquet $SPW/box/pseudo_s2_fr_mixmdp_guard.parquet \
  || { echo "$(date +%H:%M) R3 LABELS FAILED guard"; exit 1; }
scp -q $SP/box/pseudo_s2_fr_mixmdp_guard.parquet grenuke-vast3:/workspace/grenuke/box/ || { echo "$(date +%H:%M) R3 LABELS FAILED upload"; exit 1; }
ssh -n grenuke-vast3 'cd /workspace/grenuke; setsid nohup bash box3_r9.sh > logs/box3_r9.log 2>&1 < /dev/null &' 2>/dev/null
echo "$(date +%H:%M) R3 LABELS DONE"
