#!/usr/bin/env bash
# Every 5 min: copy training state (checkpoints, adapters, parts, merged outputs, logs) to Google Drive. copy, never sync.
mkdir -p /workspace/grenuke/logs
LOG=/workspace/grenuke/logs/backup.log
while true; do
  t0=$(date +%s)
  rclone copy /workspace/grenuke/box gdrive:grenuke-train-backup/box --exclude "*.tmp/**" --exclude "*.tmp" \
    --exclude "__pycache__/**" --exclude "*.partial" --transfers 8 --checkers 16 --drive-chunk-size 64M >> $LOG.err 2>&1; rc1=$?
  rclone copy /workspace/grenuke/logs gdrive:grenuke-train-backup/logs --exclude "backup.log*" >> $LOG.err 2>&1; rc2=$?
  echo "$(date -u +%H:%M:%S)Z pass rc=$rc1/$rc2 in $(( $(date +%s) - t0 ))s" >> $LOG
  sleep 300
done
