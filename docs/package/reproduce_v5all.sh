#!/usr/bin/env bash
# Final submission, fallback recipe: model v5all + France rules v2 + candidate cut (2026-09-26-v5all-ops2-c2,
# matching_results.tsv sha256 76fe7eff...). Use ONLY if v6all fails its gate.
# Code: commit 7568980 (main before the blocking v3 merge) plus PR #29's two small changes (decide.py --base
# optional, feats.py --dict-only). Current main cannot rebuild blocking v2 bit-for-bit (v3 repairs and ordinals).
#   git checkout 7568980 && git cherry-pick fddee7d
# Source of truth: experiments/ameya/model-v1/RECIPE.md. Hardware and runtimes as in reproduce_v6all.sh.
set -euo pipefail

ROOT="$(pwd)"
export BER_DATA_DIR="${BER_DATA_DIR:-$ROOT/student_resource/dataset}"
export BER_WORK_DIR="${BER_WORK_DIR:-$ROOT/work}"
export BER_OUTPUT_DIR="${BER_OUTPUT_DIR:-$ROOT/output}"
M="${MODEL_DIR:-$ROOT/experiments/ameya/model-v1}"
export PYTHONPATH="$M:$ROOT/code/business_entity_resolution/src:${PYTHONPATH:-}"

python -m ber.pipeline --stage records --split train
python -m ber.pipeline --stage records --split test
python "$M/feats.py" --split train --tag ameya-fx1 --dict-only

BP="--set trim_s1=15 --set trim_r=4 --set indic_dict=ameya-fx1 --set ns_ngrams=4 --set ns_domain_len=8 --set nw_words=6"
python -m ber.pipeline --stage block --split train --tag ameya-block-v2 $BP
python -m ber.pipeline --stage block --split test  --tag ameya-block-v2 $BP

cd "$M"
python feats.py --cands ameya-block-v2 --split train --tag ameya-fx4
python feats.py --cands ameya-block-v2 --split test  --tag ameya-fx4
python feats_lo.py --feats ameya-fx4 --split train
python feats_lo.py --feats ameya-fx4 --split test
python feats_legal.py --feats ameya-fx4 --split train
python feats_legal.py --feats ameya-fx4 --split test
python feats_lo_proxy.py --feats ameya-fx4 --split train --calib
python feats_lo_proxy.py --feats ameya-fx4 --split test
python lo_mix.py --feats ameya-fx4

python s1.py --feats ameya-fx4 --tag ameya-s1-v5all --groups str,cx,lo0,lg --drop leg__r_only_bits,leg__s1_only_bits --all
# The submitted v5all reused fx3's cross-encoder group (same candidates and row groups); this clean re-run computes
# it from its own stage 1, so a few pairs may differ from the submitted file.
python ce.py --feats ameya-fx4 --s1 ameya-s1-v5all --tag ameya-ce-v5 --model intfloat/multilingual-e5-small
LEG=leg__rel,leg__n_s1,leg__n_r,leg__inter,leg__s1_only,leg__r_only
python s2.py --feats ameya-fx4 --s1 ameya-s1-v5all --tag ameya-s2-v5all --groups str,cx,lo0,lg,ce --cluster \
  --extra $LEG,ce__logit --all
python decide.py --scores ameya-s2-v5all --col pc --tag ameya-model-v5all-c2 --p-cand 0.02 --top-r 2
python cands_final.py --s1 ameya-s1-v5all --tag ameya-cands-v5all-c2 --p-cand 0.02 --top-r 2
python post_ops.py --matches ameya-model-v5all-c2 --scores ameya-s2-v5all --cands ameya-cands-v5all-c2 \
  --feats ameya-fx4 --tag ameya-model-v5all-c2-ops2
cd "$ROOT"

python -m ber.pipeline --stage write --split test --tag ameya-model-v5all-c2-ops2 \
  --in candidates=ameya-cands-v5all-c2 --in matches=ameya-model-v5all-c2-ops2
python student_resource/utils/validate_submission.py --matching "$BER_OUTPUT_DIR/matching_results.tsv" \
  --candidate "$BER_OUTPUT_DIR/candidate_pairs.tsv" --test-dir "$BER_DATA_DIR/test"
shasum -a 256 "$BER_OUTPUT_DIR/matching_results.tsv" "$BER_OUTPUT_DIR/candidate_pairs.tsv"   # submitted: 76fe7eff...
