#!/usr/bin/env bash
# Put a backed-up training run onto a FRESH box, so llm_group.py resumes (from its checkpoint, adapter, prediction
# sets or part -- whichever is newest for each group). Run on the LAPTOP.
#
#   bash restore.sh HOST PORT          # then on the box: train_jobs.sh setup; train_jobs.sh launch
#
# Source: the local mirror written by backup_pull.sh; if it is missing, it is first pulled back from Drive.
set -euo pipefail
H="root@${1:?host}"; P="${2:?port}"
KEY="$HOME/.ssh/vast_grenuke"
DST="${BACKUP_DIR:-/c/Users/baksh/Downloads/New folder/train-backup}"
RCLONE="${RCLONE:-rclone}"
REMOTE="${REMOTE:-gdrive:grenuke-train-backup}"
R=/workspace/grenuke
if [ ! -d "$DST/box" ]; then
  echo "no local mirror; pulling $REMOTE -> $DST"
  mkdir -p "$DST"
  "$RCLONE" copy "$REMOTE" "$DST"
fi
ssh -i "$KEY" -p "$P" -o StrictHostKeyChecking=accept-new "$H" "mkdir -p $R/box $R/logs"
# never restore a half-written temp file
tar -C "$DST" -cf - --exclude='*.tmp' --exclude='*.tmp.npz' box logs \
  | ssh -i "$KEY" -p "$P" "$H" "tar -xf - -C $R && ls -la $R/box/out_* | head -50"
echo "restored. Now on the box: bash $R/repo/experiments/bakshi/box/train_jobs.sh setup, then launch (finished groups are skipped, interrupted ones resume)."
