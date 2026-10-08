#!/usr/bin/env bash
# LAPTOP-side backup of the (interruptible) training box to Google Drive.
#
# The Drive credential never leaves the laptop: every pass pulls the files that changed on the box since the last
# successful pass (checkpoints, adapters, prediction sets, parts, merged outputs, logs) over ssh into a local mirror,
# then `rclone copy`s the mirror to gdrive:grenuke-train-backup with the laptop's own rclone config.
#
#   bash backup_pull.sh HOST PORT [SECONDS=300]        # loop; run it in the background
#   BACKUP_DIR=... RCLONE=... override the local mirror / rclone binary.
#
# A pass extracts into a staging directory and only moves files into the mirror when the whole stream arrived, so an
# interrupted transfer never leaves a truncated checkpoint in the mirror (or on Drive). The box-side marker only
# advances after a successful pass, so nothing changed in between is skipped.
set -uo pipefail
H="root@${1:?host}"; P="${2:?port}"; EVERY="${3:-300}"
KEY="$HOME/.ssh/vast_grenuke"
DST="${BACKUP_DIR:-$HOME/Downloads/New folder/train-backup}"
RCLONE="${RCLONE:-rclone}"
REMOTE="${REMOTE:-gdrive:grenuke-train-backup}"
R=/workspace/grenuke
SSH=(ssh -i "$KEY" -p "$P" -o BatchMode=yes -o ConnectTimeout=20 -o ServerAliveInterval=30 "$H")
mkdir -p "$DST"
LOG="$DST/backup.log"

while true; do
  STAGE="$DST.stage"; rm -rf "$STAGE"; mkdir -p "$STAGE"
  t0=$(date +%s)
  "${SSH[@]}" "cd $R && touch .bk_new && { [ -f .bk_marker ] && NEWER='-newer .bk_marker' || NEWER=''; \
      find box/out_* logs -type f ! -name '*.tmp' ! -name '*.tmp.npz' \$NEWER 2>/dev/null | tar -cf - -T - 2>/dev/null; }" \
    | tar -xf - -C "$STAGE"
  rc=("${PIPESTATUS[@]}")
  if [ "${rc[0]}" = 0 ] && [ "${rc[1]}" = 0 ]; then
    n=$(find "$STAGE" -type f | wc -l)
    cp -a "$STAGE/." "$DST/" && rm -rf "$STAGE"
    "${SSH[@]}" "cd $R && mv -f .bk_new .bk_marker" >/dev/null 2>&1
    if "$RCLONE" copy "$DST" "$REMOTE" --exclude "backup.log" --exclude "*.stage/**" >>"$LOG" 2>&1; then
      echo "$(date '+%H:%M:%S') pass OK: $n changed files pulled, Drive synced ($(( $(date +%s) - t0 ))s)" >> "$LOG"
    else
      echo "$(date '+%H:%M:%S') pulled $n files but the Drive copy FAILED (local mirror is intact)" >> "$LOG"
    fi
  else
    echo "$(date '+%H:%M:%S') pull FAILED (ssh/tar exit ${rc[*]}); box down or preempted? mirror unchanged" >> "$LOG"
  fi
  sleep "$EVERY"
done
