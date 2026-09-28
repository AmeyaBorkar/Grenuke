#!/usr/bin/env bash
F=/workspace/grenuke/backup_loop.sh
for p in $(pgrep -f "bash $F"); do kill $p; done
for p in $(pgrep -f "rclone copy /workspace/grenuke/work"); do kill $p; done
sed -i 's#rclone copy /workspace/grenuke/work   $R/work --include "reports/\*\*" --include "stack/\*\*" --include "matches/\*\*" --max-size 500M#rclone copy /workspace/grenuke/work/reports $R/work/reports#' $F
echo "reports-only line present: $(grep -c 'work/reports $R/work/reports' $F)"
bash -n $F && (setsid nohup bash $F > /dev/null 2>&1 < /dev/null &)
sleep 1; echo "loops running: $(pgrep -f "bash $F" | wc -l)"
tail -1 /workspace/grenuke/logs/phaseB_g1.log; tail -1 /workspace/grenuke/logs/phaseB_g1w.log
