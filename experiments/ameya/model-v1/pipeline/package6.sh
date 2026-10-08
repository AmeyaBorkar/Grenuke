#!/usr/bin/env bash
# Package a submission into its own folder: write both TSVs, validate, sha256. Code: research-v5 worktree (main).
# usage: package6.sh <matches tag> <candidates tag> <folder name under submissions/files>
set -euo pipefail
source $SCRATCH/env6.sh
TAG=$1; CANDS=$2; NAME=$3
DEST=$REPO/submissions/files/$NAME
mkdir -p "$DEST"
export BER_OUTPUT_DIR=$DEST
cd $REPO/.claude/worktrees/research-v5
python -m ber.pipeline --stage write --split test --tag "$TAG" --in candidates="$CANDS" --in matches="$TAG"
python $REPO/student_resource/utils/validate_submission.py \
  --matching "$DEST/matching_results.tsv" --candidate "$DEST/candidate_pairs.tsv" \
  --test-dir "$BER_DATA_DIR/test" --check-ids
sha256sum "$DEST/matching_results.tsv" "$DEST/candidate_pairs.tsv"
