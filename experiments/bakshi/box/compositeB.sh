#!/usr/bin/env bash
# Composite B (public leaderboard 0.990879), end to end from the raw challenge TSVs.
#
#   From the unzipped package root:   VARIANT=compositeB bash code/business_entity_resolution/src/reproduce.sh
#   (reproduce.sh hands over to this script; it can also be run directly from the package root.)
#
# Composite B = US/India of g1w  (the v7sq recipe with the Qwen2.5-7B cross-encoder q7st counted twice in stage 2)
#             + France of mixmdp (Ameya's block, pipeline/france_mixmdp.sh)
#             - every predicted pair outside the cross-encoder band (stage-1 p1 > 0.99) that q7st scores below -6.
# The same scripts and arguments as the 27 Sep run (experiments/bakshi/final-package/REPRO_compositeB.sh); the
# deviations, all forced by running from one package instead of three machines, are listed at the end.
#
# Hardware: the cross-encoders need CUDA. q7st (7.6B, LoRA) wants 3x H100/A100 80 GB (one out-of-fold group per GPU,
# ~2 h); with fewer GPUs the groups run one after another (~6 h on one H100). XGBoost stages run on CPU or GPU.
#
# Knobs (environment):
#   Q7_MODEL      model id or local path for q7st (default: Qwen/Qwen2.5-7B at the pinned revision). A small model here
#                 is how a dev-sample dry-run fits on a 12 GB card; the result is then not Composite B.
#   Q7_GPUS       GPU ids for the three q7st groups (default "0 1 2"; fewer than three -> sequential on the first)
#   SCORE_BATCH   batch of score_pairs.py (default 512, as run; lower it on a card smaller than 40 GB)
#   FR_DIR        a finished France block output dir (matching_results.tsv + candidate_pairs.tsv); default: build it
#   CHECK_7B=1    also score the labelled holdout sample and print the drop-rule table (rescore_eval.py)
#   BER_OUTPUT_DIR  where Composite B is written (default output_rerun/, never the shipped output/)
set -euo pipefail

ROOT="$(pwd)"
BOX="${BOX_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
if [ -f "$BOX/../reproduce.sh" ]; then                     # inside the package: code/business_entity_resolution/src/box
  PKG="$(cd "$BOX/../.." && pwd)"; REPRO="$PKG/src/reproduce.sh"; M="${MODEL_DIR:-$PKG/src/model_v1}"
else                                                        # in the repository: experiments/bakshi/box
  PKG="$ROOT/code/business_entity_resolution"; REPRO="$BOX/../final-package/reproduce.sh"
  M="${MODEL_DIR:-$ROOT/experiments/ameya/model-v1}"
fi
export MODEL_DIR="$M"
export BER_DATA_DIR="${BER_DATA_DIR:-$ROOT/student_resource/dataset}"
export BER_WORK_DIR="${BER_WORK_DIR:-$ROOT/work}"
export CE_BOX_DIR="${CE_BOX_DIR:-$BER_WORK_DIR/box}"
export PYTHONPATH="$M:$ROOT/code/business_entity_resolution/src:${PYTHONPATH:-}"
OUT="${BER_OUTPUT_DIR:-$ROOT/output_rerun}"
AUDIT="${AUDIT:-$M/audit_matching.py}"
[ -f "$AUDIT" ] || AUDIT="$BOX/../final-package/audit_matching.py"
VALIDATOR="$ROOT/student_resource/utils/validate_submission.py"
LOGS="$BER_WORK_DIR/logs_compositeB"
mkdir -p "$CE_BOX_DIR" "$LOGS" "$OUT"
D="$CE_BOX_DIR/rescore"
mkdir -p "$D"

LEG=leg__rel,leg__n_s1,leg__n_r,leg__inter,leg__s1_only,leg__r_only
NX=nx__d1,nx__nudge,nx__digit_sub,nx__digit_swap,nx__suffix,nx__len_diff
Q7_REV=d149729398750b98c0af14eb82c78cfe92750796
read -r -a GPUS <<< "${Q7_GPUS:-0 1 2}"
say () { echo "$(date +%T) == $*"; }
have () { [ -d "$BER_WORK_DIR/$1" ]; }          # a finished artifact tag, e.g. matches/<tag>

# -------------------------------------------------------------------------------------------------------------------
# 1. The v7sq chain: records, blocking, features, stage 1, the band, its four cross-encoders (on THIS band), the v7ce3
#    teacher and its French pseudo-labels, stage 2, stage 3, rules, acronym join, stacked rules -> v7sq-dpc.
#    It is the teacher of q7st and of the France block, and it plays the role g0 had on the box.
# -------------------------------------------------------------------------------------------------------------------
if have matches/ameya-model-v7sq-s3-ops3a-dpc; then
  say "1. v7sq-dpc already built, skipping"
else
  say "1. v7sq chain (VARIANT=v7sq STACK=1 reproduce.sh)"
  VARIANT=v7sq STACK=1 BER_OUTPUT_DIR="$BER_WORK_DIR/out_v7sq" bash "$REPRO"
fi

cd "$M"

# -------------------------------------------------------------------------------------------------------------------
# 2. French band pseudo-labels from v7sq-dpc (the teacher of q7st): pseudo_labels.py, as reproduce.sh's pseudo_for.
# -------------------------------------------------------------------------------------------------------------------
if [ ! -f "$CE_BOX_DIR/pseudo_fr_v7sq.parquet" ]; then
  say "2. pseudo_fr_v7sq from v7sq-dpc"
  python pseudo_labels.py ameya-model-v7sq-s3 ameya-s3-v7sq ameya-model-v7sq-s3-ops3 ameya-model-v7sq-s3-ops3a-dpc \
    "$CE_BOX_DIR/band_test.parquet" "$CE_BOX_DIR/pseudo_fr_v7sq.parquet"
fi

# -------------------------------------------------------------------------------------------------------------------
# 3. q7st: Qwen2.5-7B LoRA sequence classifier, self-trained on France, one out-of-fold group per GPU, then merged.
#    llm_group.py defaults are the run's: --sep " || " --us-in-frac 0.5 --lr 1e-4 --batch 64 --epochs 1 --max-len 96
#    --lora-r 16 --seed 26 --ckpt-every 600. A killed group resumes from its checkpoint when rerun.
# -------------------------------------------------------------------------------------------------------------------
if [ -z "${Q7_MODEL:-}" ]; then
  Q7_MODEL="$(python -c "from huggingface_hub import snapshot_download as s; print(s('Qwen/Qwen2.5-7B', revision='$Q7_REV', allow_patterns=['*.json', '*.safetensors', '*.txt']))")"
fi
if [ ! -f "$CE_BOX_DIR/out_q7st/ce_test.parquet" ]; then
  say "3. q7st on GPUs ${GPUS[*]} (model $Q7_MODEL)"
  group () {  # group <g> <gpu>
    CUDA_VISIBLE_DEVICES="$2" python "$BOX/llm_group.py" --model "$Q7_MODEL" --name q7st --group "$1" \
      --pseudo "$CE_BOX_DIR/pseudo_fr_v7sq.parquet" --infer-batch 512 > "$LOGS/q7st_g$1.log" 2>&1
  }
  if [ "${#GPUS[@]}" -ge 3 ]; then
    pids=()
    for g in 0 1 2; do group "$g" "${GPUS[$g]}" & pids+=($!); done
    for p in "${pids[@]}"; do wait "$p" || { echo "FAIL: a q7st group failed; see $LOGS/q7st_g*.log" >&2; exit 1; }; done
  else
    for g in 0 1 2; do group "$g" "${GPUS[0]}"; done
  fi
  python "$BOX/llm_merge.py" --name q7st > "$LOGS/q7st_merge.log" 2>&1
  tail -1 "$LOGS/q7st_merge.log"            # run of 27 Sep: band AUC holdout 0.9436, OOF 0.9396
fi

# -------------------------------------------------------------------------------------------------------------------
# 4. v7sq-dpc -> -dpcsf: the look-alike word-swap drop, then the France expected-F0.5 decision (as phaseB.sh ran them on
#    g0). Its French final predictions are the ones the 7B re-checks. US/India are unchanged by both.
# -------------------------------------------------------------------------------------------------------------------
if ! have matches/ameya-model-v7sq-s3-ops3a-dpcsf; then
  say "4. v7sq-dpc -> -dpcs -> -dpcsf"
  (cd "$M/stack" && python apply_swapsim.py ameya-model-v7sq-s3-ops3a-dpc ameya-model-v7sq-s3-ops3a-dpcs)
  (cd "$M/stack" && python dp_france.py v7sq ameya-cands-v7sq-c2a ameya-model-v7sq-s3-ops3a-dpcs ameya-model-v7sq-s3-ops3a-dpcsf)
fi

# -------------------------------------------------------------------------------------------------------------------
# 5. g1w: stage 2 with the z-mean of e5l, qst, e5ls, bge, q7st, q7st, then stage 3 -> the stacked rules (-dpc).
#    Composite B takes its US/India rows. Run of 27 Sep: holdout macro F0.5 0.991323 (US 0.991114, India 0.991635).
# -------------------------------------------------------------------------------------------------------------------
V=g1w; G=zg1w; COL=zg1w__logit; MT=ameya-model-g1w
if ! have matches/$MT-s3-ops3a-dpc; then
  say "5. g1w"
  python zmean_ce.py "$CE_BOX_DIR/out_$G" "$CE_BOX_DIR/out_e5l" "$CE_BOX_DIR/out_qst" "$CE_BOX_DIR/out_e5ls" \
    "$CE_BOX_DIR/out_bge" "$CE_BOX_DIR/out_q7st" "$CE_BOX_DIR/out_q7st"
  python ce_import.py --feats ameya-fx5 --src "$CE_BOX_DIR/out_$G" --group "$G" --column "$COL"
  python s2.py --feats ameya-fx5 --s1 ameya-s1-v6all --tag "ameya-s2-$V" \
    --groups "str,cx,lo0,lg,ce,$G,nx" --cluster --extra "$LEG,ce__logit,$COL,$NX" --all \
    --pseudo "$CE_BOX_DIR/pseudo_s2_fr_v7ce3.parquet"
  python stage3.py --scores "ameya-s2-$V" --tag "ameya-s3-$V" --p-cand 0.02 --top-r 2
  python decide.py --scores "ameya-s3-$V" --col pc --tag "$MT-s3" --p-cand 0.02 --top-r 2
  python post_ops.py --matches "$MT-s3" --scores "ameya-s3-$V" --cands ameya-cands-v6all-c2 \
    --feats ameya-fx5 --tag "$MT-s3-ops3" --robust-addr
  python acr_join.py --split test --matches "$MT-s3-ops3" --cands ameya-cands-v6all-c2 \
    --tag "$MT-s3-ops3a" --cands-tag "ameya-cands-$V-c2a"
  STACK_OUT="$BER_WORK_DIR/stack_$V" bash "$M/stack/stack.sh" "$V"
fi
G1W_DIR="$BER_WORK_DIR/out_g1w"
if [ ! -f "$G1W_DIR/matching_results.tsv" ]; then
  mkdir -p "$G1W_DIR"
  (cd "$ROOT" && BER_OUTPUT_DIR="$G1W_DIR" python -m ber.pipeline --stage write --split test --tag "$MT-s3-ops3a-dpc" \
    --in "candidates=ameya-cands-$V-c2a" --in "matches=$MT-s3-ops3a-dpc")
fi

# -------------------------------------------------------------------------------------------------------------------
# 6. The 7B re-check: score the confident final predictions with q7st's adapter_0.
#    France: v7sq-dpcsf's French predictions (870,019 on 27 Sep). US/India: g1w-dpc's with p1 > 0.99 (4,744,395).
# -------------------------------------------------------------------------------------------------------------------
say "6. 7B re-check"
[ -f "$D/fr_final_pairs.parquet" ] || python "$BOX/rescore_export.py" --final ameya-model-v7sq-s3-ops3a-dpcsf \
  --s3 ameya-s3-v7sq --pred ameya-model-v7sq-s3 --out "$D"
[ -f "$D/usin_final_pairs.parquet" ] || python "$BOX/analysis/export_usin.py" --matches "$MT-s3-ops3a-dpc" \
  --out "$D/usin_final_pairs.parquet"
score () {  # score <gpu> <pairs> <split> <part> <out>
  [ -f "$5" ] || CUDA_VISIBLE_DEVICES="$1" python "$BOX/score_pairs.py" --model "$Q7_MODEL" \
    --adapter "$CE_BOX_DIR/out_q7st/adapter_0" --batch "${SCORE_BATCH:-512}" --pairs "$2" --split "$3" --part "$4" \
    --out "$5" > "$5.log" 2>&1
}
n=${#GPUS[@]}
score_parts () {  # score_parts <pairs> <split> <nparts> <out prefix>: at most one job per GPU at a time
  local i pids=()
  for ((i = 0; i < $3; i++)); do
    score "${GPUS[$((i % n))]}" "$1" "$2" "$i/$3" "$4$i.parquet" & pids+=($!)
    if [ "${#pids[@]}" -ge "$n" ]; then for p in "${pids[@]}"; do wait "$p"; done; pids=(); fi
  done
  for p in ${pids[@]+"${pids[@]}"}; do wait "$p"; done
}
score_parts "$D/fr_final_pairs.parquet" test 2 "$D/fr_scored_"       # 27 Sep: 2 x 15 min on H100
score_parts "$D/usin_final_pairs.parquet" test 4 "$D/usin_scored_"   # 27 Sep: 4 x 46 min on H100
for f in "$D"/fr_scored_0.parquet "$D"/fr_scored_1.parquet "$D"/usin_scored_{0,1,2,3}.parquet; do
  [ -f "$f" ] || { echo "FAIL: $f missing; see $f.log" >&2; exit 1; }
done
if [ "${CHECK_7B:-0}" = 1 ]; then
  score "${GPUS[0]}" "$D/hold_pred_pairs.parquet" train 0/1 "$D/hold_scored.parquet"
  python "$BOX/rescore_eval.py" --dir "$D" --out-band-only   # 27 Sep: t = -6 -> +0.000033, both halves positive
fi

# -------------------------------------------------------------------------------------------------------------------
# 7. France: mixmdp (Ameya's block). Only its French rows enter Composite B.
# -------------------------------------------------------------------------------------------------------------------
FR_DIR="${FR_DIR:-$BER_WORK_DIR/out_france_mixmdp}"
if [ ! -f "$FR_DIR/matching_results.tsv" ]; then
  say "7. France block (pipeline/france_mixmdp.sh -> $FR_DIR)"
  [ -f "$M/pipeline/france_mixmdp.sh" ] || { echo "FAIL: $M/pipeline/france_mixmdp.sh is missing" >&2; exit 1; }
  FR_DIR="$FR_DIR" bash "$M/pipeline/france_mixmdp.sh"
fi

# -------------------------------------------------------------------------------------------------------------------
# 8. Composite B: per S1 country from one source (labelled countries from g1w, the others from the France block), minus
#    the 7B rejects (q7 < -6, p1 > 0.99); then the organiser validator, the strict audit and the hashes.
# -------------------------------------------------------------------------------------------------------------------
say "8. compose -> $OUT"
cd "$ROOT"
python "$BOX/compose_tsv.py" --labelled "$G1W_DIR" --unlabelled "$FR_DIR" \
  --s1-tsv "$BER_DATA_DIR/test/test_source1.tsv" --train-s1-tsv "$BER_DATA_DIR/train/train_source1.tsv" \
  --drop "$D/fr_scored_*.parquet" "$D/usin_scored_*.parquet" --drop-logit -6 --out "$OUT"
python "$VALIDATOR" --matching "$OUT/matching_results.tsv" --candidate "$OUT/candidate_pairs.tsv" \
  --test-dir "$BER_DATA_DIR/test"
python "$AUDIT" --matching "$OUT/matching_results.tsv" --candidate "$OUT/candidate_pairs.tsv" \
  --test-dir "$BER_DATA_DIR/test"
sha256sum "$OUT/matching_results.tsv" "$OUT/candidate_pairs.tsv" 2>/dev/null \
  || shasum -a 256 "$OUT/matching_results.tsv" "$OUT/candidate_pairs.tsv"
cat <<'EOF'

Submitted Composite B (public leaderboard 0.990879), shipped verbatim in output/:
  matching_results.tsv  df4bccd785b3fa785b7edcf0532288bcddc0010e2e31ce6f358064529ecb62e8
  candidate_pairs.tsv   58c824a3f61c184fe7da1a448a4ac94284f288feff9c351abfe16a3dfc0520e5
A rerun is not byte-identical: the cross-encoders are not bit-reproducible across GPUs, and stage 3 moves ~500
decisions across machines. Check instead: blocking 66.4M / 58.4M pairs; holdout macro F0.5 of v7sq-s3 ~0.99125 and
g1w-s3 ~0.99132 (work/reports/); q7st band AUC ~0.944; ~1,150 7B drops (about 840 French, 310 US/India).

Deviations from the 27 Sep run (REPRO_compositeB.sh), all from running in one package instead of on three machines:
  - the cross-encoders are trained on this package's own band, so there is no remap onto another machine's band;
  - v7sq's own chain plays g0's role (g0 was the v7sq recipe rebuilt on the pipeline box);
  - compose takes g1w-dpc directly (the run took g1w-dpcsfq, whose US/India rows are g1w-dpc's);
  - export_usin.py takes its tag and output path as arguments and reads the labelled countries from the train records.
EOF
