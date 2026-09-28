#!/usr/bin/env bash
# Phase B on the pipeline box: one stage-2 variant from a set of cross-encoder runs, through the full chain
# to a validated, audited submission and its France footprint against v7sq-dpc.
#
#   CUDA_VISIBLE_DEVICES=0 bash phaseB.sh <variant> "<ce names>" <s2 pseudo parquet>
#   e.g. bash phaseB.sh g0 "e5l qst e5ls bge" /workspace/grenuke/box_ameya/pseudo_s2_fr_v7ce3.parquet   (= v7sq)
#
# Each CE name is a directory $ROOT/box_ameya/out_<name> (ce_train/ce_test.parquet + config.json) trained on
# Ameya's band. It is re-keyed by (s1, r) onto OUR band (remap_ce.py; aborts below 99.5% coverage), then the
# mix is the z-scored mean (zmean_ce.py), imported as feature group z<variant>, and stage 2 onwards follows
# final-package/reproduce.sh step 8-9b with the tag pattern stack.sh expects. Two variants can run side by
# side on the two GPUs: every tag, stack file and output directory is per variant.
set -euo pipefail
V="${1:?variant}"; CES="${2:?ce names}"; PSEUDO="${3:?s2 pseudo parquet}"
ROOT="${ROOT:-/workspace/grenuke}"
. "$ROOT/env.sh"
L="$ROOT/logs"; LOG="$L/phaseB_$V.log"
G="z$V"; COL="${G}__logit"
LEG=leg__rel,leg__n_s1,leg__n_r,leg__inter,leg__s1_only,leg__r_only
NX=nx__d1,nx__nudge,nx__digit_sub,nx__digit_swap,nx__suffix,nx__len_diff
export BER_OUTPUT_DIR="$ROOT/output/$V"
mkdir -p "$BER_OUTPUT_DIR" "$L"
[ -f "$PSEUDO" ] || { echo "FAIL: pseudo file $PSEUDO missing" | tee -a "$LOG"; exit 2; }

step () {
  local name="$1"; shift
  local t0=$(date +%s)
  if [ -f "$L/.doneB_${V}_$name" ]; then echo "$(date +%T) SKIP  $V/$name (done earlier)" | tee -a "$LOG"; return 0; fi
  echo "$(date +%T) START $V/$name" | tee -a "$LOG"
  if "$@" > "$L/B_${V}_$name.log" 2>&1; then
    touch "$L/.doneB_${V}_$name"
    echo "$(date +%T) DONE  $V/$name ($(( $(date +%s) - t0 ))s)" | tee -a "$LOG"
  else
    echo "$(date +%T) FAIL  $V/$name -- see $L/B_${V}_$name.log" | tee -a "$LOG"
    tail -20 "$L/B_${V}_$name.log" >> "$LOG"
    return 1
  fi
}
echo "$(date +%T) ===== variant $V: ces [$CES], pseudo $(basename "$PSEUDO"), gpu ${CUDA_VISIBLE_DEVICES:-all} =====" | tee -a "$LOG"

# ---- remap every CE onto our band (shared dirs, so locked and atomic; a finished remap is reused) ----
SRC=""
for n in $CES; do
  [ -d "$ROOT/box_ameya/out_$n" ] || { echo "FAIL: $ROOT/box_ameya/out_$n missing" | tee -a "$LOG"; exit 2; }
  (
    flock 9
    if [ ! -f "$CE_BOX_DIR/out_$n/.remapped" ]; then
      rm -rf "$CE_BOX_DIR/out_$n.tmp"
      step "remap_$n" python "$B/box/remap_ce.py" --src-band "$ROOT/box_ameya" --src-out "$ROOT/box_ameya/out_$n" \
        --dst-band "$CE_BOX_DIR" --out "$CE_BOX_DIR/out_$n.tmp"
      touch "$CE_BOX_DIR/out_$n.tmp/.remapped"
      rm -rf "$CE_BOX_DIR/out_$n"; mv "$CE_BOX_DIR/out_$n.tmp" "$CE_BOX_DIR/out_$n"
    fi
  ) 9>"$CE_BOX_DIR/.remap.lock"
  grep -h "coverage" "$L/B_"*"_remap_$n.log" 2>/dev/null | tail -2 | sed "s/^/   $n: /" | tee -a "$LOG" || true
  SRC="$SRC $CE_BOX_DIR/out_$n"
done

cd "$M"
step zmean     python zmean_ce.py "$CE_BOX_DIR/out_$G" $SRC
step ce_import python ce_import.py --feats ameya-fx5 --src "$CE_BOX_DIR/out_$G" --group "$G" --column "$COL"
step s2 python s2.py --feats ameya-fx5 --s1 ameya-s1-v6all --tag "ameya-s2-$V" \
  --groups "str,cx,lo0,lg,ce,$G,nx" --cluster --extra "$LEG,ce__logit,$COL,$NX" --all --pseudo "$PSEUDO"

MT="ameya-model-$V"
step decide_c2 python decide.py --scores "ameya-s2-$V" --col pc --tag "$MT-c2" --p-cand 0.02 --top-r 2
step stage3    python stage3.py --scores "ameya-s2-$V" --tag "ameya-s3-$V" --p-cand 0.02 --top-r 2
step decide_s3 python decide.py --scores "ameya-s3-$V" --col pc --tag "$MT-s3" --p-cand 0.02 --top-r 2
step post_ops  python post_ops.py --matches "$MT-s3" --scores "ameya-s3-$V" --cands ameya-cands-v6all-c2 \
  --feats ameya-fx5 --tag "$MT-s3-ops3" --robust-addr
step acr_join  python acr_join.py --split test --matches "$MT-s3-ops3" --cands ameya-cands-v6all-c2 \
  --tag "$MT-s3-ops3a" --cands-tag "ameya-cands-$V-c2a"
export STACK_OUT="$BER_WORK_DIR/stack_$V"
step stack bash "$M/stack/stack.sh" "$V"
# France-only additions from ameya/final-stack d6c2e38 (RESEARCH_v6.md 6.17-6.18), run from the stack dir as
# stack.sh runs its own scripts: drop the look-alike word swaps (-dpcs), then the French expected-F0.5 decision
# (-dpcsf). dp_france expects exactly that input: the -dpc minus its look-alike swaps. US/India are unchanged.
(cd "$M/stack" && step swapsim python apply_swapsim.py "$MT-s3-ops3a-dpc" "$MT-s3-ops3a-dpcs")
(cd "$M/stack" && step dp_france python dp_france.py "$V" "ameya-cands-$V-c2a" "$MT-s3-ops3a-dpcs" "$MT-s3-ops3a-dpcsf")

finalize () {   # finalize <suffix> <matches tag>: write, validate, audit, diff vs v7sq-dpc
  local sfx="$1" tag="$2"
  export BER_OUTPUT_DIR="$ROOT/output/$V/$sfx"; mkdir -p "$BER_OUTPUT_DIR"
  local MR="$BER_OUTPUT_DIR/matching_results.tsv" CP="$BER_OUTPUT_DIR/candidate_pairs.tsv"
  step "write_$sfx" python -m ber.pipeline --stage write --split test --tag "$tag" \
    --in "candidates=ameya-cands-$V-c2a" --in "matches=$tag"
  step "validate_$sfx" python "$ROOT/repo/student_resource/utils/validate_submission.py" --matching "$MR" \
    --candidate "$CP" --test-dir "$BER_DATA_DIR/test"
  step "audit_$sfx" python "$B/final-package/audit_matching.py" --matching "$MR" --candidate "$CP" \
    --test-dir "$BER_DATA_DIR/test"
  step "diff_$sfx" python "$B/final-package/diff_candidates.py" --base "v7sq-dpc=$ROOT/ref/v7sq_dpc_matching.tsv" \
    --cand "$V-$sfx=$MR" --s1-tsv "$BER_DATA_DIR/test/test_source1.tsv"
  echo "   --- $V-$sfx ($tag) ---" | tee -a "$LOG"
  tail -2 "$L/B_${V}_validate_$sfx.log" | tee -a "$LOG"
  grep -E "AUDIT" "$L/B_${V}_audit_$sfx.log" | tee -a "$LOG"
  grep -E "^$V-$sfx " "$L/B_${V}_diff_$sfx.log" | tee -a "$LOG"
  sha256sum "$MR" "$CP" | tee -a "$LOG"
}
finalize dpc   "$MT-s3-ops3a-dpc"
finalize dpcsf "$MT-s3-ops3a-dpcsf"
python - "$V" <<'EOF' | tee -a "$LOG"
import json, sys
from ber.paths import report_path
v = sys.argv[1]
for t in (f"ameya-model-{v}-s3",):
    try:
        r = json.load(open(report_path(t)))
        print(f"   holdout report {t}: " + json.dumps({k: r[k] for k in r if k in ("f05", "holdout", "rule", "per_country")})[:400])
    except Exception as e:
        print(f"   (no holdout report for {t}: {e})")
EOF
echo "$(date +%T) ===== variant $V done: $ROOT/output/$V/{dpc,dpcsf}/ =====" | tee -a "$LOG"
