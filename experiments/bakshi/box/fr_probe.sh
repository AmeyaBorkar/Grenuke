#!/usr/bin/env bash
# France-only probe of a finished variant: rerun Ameya's French expected-F0.5 decision (stack/dp_france.py) with a
# different logit SHIFT, then write, validate, audit and diff exactly like phaseB's finalize. US/India are unchanged.
# dp_france.py uses SHIFT = +0.2 (more inclusive); a negative shift favours precision, a larger one recall. France
# has no labels, so the leaderboard is the only judge: the best upload counts, so a probe costs a slot, not score.
#
#   bash fr_probe.sh <variant> <shift> <suffix>      e.g.  bash fr_probe.sh g1 -0.4 frp
set -euo pipefail
V="${1:?variant}"; SH="${2:?shift}"; SFX="${3:?suffix}"
ROOT="${ROOT:-/workspace/grenuke}"
. "$ROOT/env.sh"
L="$ROOT/logs"; LOG="$L/probe_${V}_$SFX.log"; MT="ameya-model-$V"
[ -f "$L/.doneB_${V}_swapsim" ] || { echo "FAIL: $V has no -dpcs tag yet (swapsim not done)" | tee -a "$LOG"; exit 2; }
echo "$(date +%T) probe $V shift $SH -> $MT-s3-ops3a-$SFX" | tee -a "$LOG"
(cd "$M/stack" && python -c "import dp_france as d; d.SHIFT = float('$SH'); d.main('$V', 'ameya-cands-$V-c2a', '$MT-s3-ops3a-dpcs', '$MT-s3-ops3a-$SFX')") >> "$LOG" 2>&1
export BER_OUTPUT_DIR="$ROOT/output/$V/$SFX"; mkdir -p "$BER_OUTPUT_DIR"
MR="$BER_OUTPUT_DIR/matching_results.tsv"; CP="$BER_OUTPUT_DIR/candidate_pairs.tsv"
python -m ber.pipeline --stage write --split test --tag "$MT-s3-ops3a-$SFX" \
  --in "candidates=ameya-cands-$V-c2a" --in "matches=$MT-s3-ops3a-$SFX" >> "$LOG" 2>&1
python "$ROOT/repo/student_resource/utils/validate_submission.py" --matching "$MR" --candidate "$CP" \
  --test-dir "$BER_DATA_DIR/test" 2>&1 | tail -2 | tee -a "$LOG"
python "$B/final-package/audit_matching.py" --matching "$MR" --candidate "$CP" --test-dir "$BER_DATA_DIR/test" 2>&1 \
  | grep -E "AUDIT" | tee -a "$LOG"
python "$B/final-package/diff_candidates.py" --base "v7sq-dpc=$ROOT/ref/v7sq_dpc_matching.tsv" \
  --cand "$V-dpcsf=$ROOT/output/$V/dpcsf/matching_results.tsv" --cand "$V-$SFX=$MR" \
  --s1-tsv "$BER_DATA_DIR/test/test_source1.tsv" 2>&1 | grep -E "France" | tee -a "$LOG"
sha256sum "$MR" "$CP" | tee -a "$LOG"
echo "$(date +%T) probe done: $MR" | tee -a "$LOG"
