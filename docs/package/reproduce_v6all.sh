#!/usr/bin/env bash
# Final submission, primary recipe: model v6all (2026-09-26-v6all-ops-c2), code = current main.
# Source of truth: experiments/ameya/model-v1/RECIPE.md. Run from the repository (or unzipped package) root.
#
# Hardware used: RTX 5070 Ti 12 GB, 24 cores, 31 GB RAM. ce.py needs a CUDA GPU. Stages 1/2 peak at ~18-19 GB RAM,
# so run nothing else heavy alongside them. Total about 3 h (blocking ~25 min, features ~1 h, stage 1 ~30 min,
# cross-encoder ~40 min, stage 2 ~25 min, decision + rules a few min).
set -euo pipefail

ROOT="$(pwd)"
export BER_DATA_DIR="${BER_DATA_DIR:-$ROOT/student_resource/dataset}"   # absolute: the model scripts run from their folder
export BER_WORK_DIR="${BER_WORK_DIR:-$ROOT/work}"
export BER_OUTPUT_DIR="${BER_OUTPUT_DIR:-$ROOT/output}"
M="${MODEL_DIR:-$ROOT/experiments/ameya/model-v1}"                     # in the zip: code/business_entity_resolution/src/model_v1
export PYTHONPATH="$M:$ROOT/code/business_entity_resolution/src:${PYTHONPATH:-}"

# 0. records and the Indic -> Latin dictionary (learned on train folds 5-19 only)
python -m ber.pipeline --stage records --split train
python -m ber.pipeline --stage records --split test
python "$M/feats.py" --split train --tag ameya-fx1 --dict-only

# 1. blocking v3 (domain/OCR repairs on by default, ordinal words converted); about 13 + 10 min
BP="--set trim_s1=15 --set trim_r=4 --set indic_dict=ameya-fx1 --set ns_ngrams=4 --set ns_domain_len=8 --set nw_words=6"
python -m ber.pipeline --stage block --split train --tag ameya-block-v3 $BP
python -m ber.pipeline --stage block --split test  --tag ameya-block-v3 $BP

cd "$M"
# 2. features (about 1 h). Each train run writes a table its test run reads, so keep the order.
python feats.py --cands ameya-block-v3 --split train --tag ameya-fx5
python feats.py --cands ameya-block-v3 --split test  --tag ameya-fx5
python feats_nx.py --feats ameya-fx5 --split train
python feats_nx.py --feats ameya-fx5 --split test
python feats_lo.py --feats ameya-fx5 --split train
python feats_lo.py --feats ameya-fx5 --split test
python feats_legal.py --feats ameya-fx5 --split train
python feats_legal.py --feats ameya-fx5 --split test
python feats_lo_proxy.py --feats ameya-fx5 --split train --calib
python feats_lo_proxy.py --feats ameya-fx5 --split test
python lo_mix.py --feats ameya-fx5

# 3. stage 0 + 1 on all of train (4 out-of-fold groups; about 30 min, 18 GB)
python s1.py --feats ameya-fx5 --tag ameya-s1-v6all --groups str,cx,lo0,lg,nx --drop leg__r_only_bits,leg__s1_only_bits --all

# 4. cross-encoder feature on the uncertain band (multilingual-e5-small, MIT, 118M; GPU about 40 min)
#    The first run downloads the model weights; afterwards HF_HUB_OFFLINE=1 works.
python ce.py --feats ameya-fx5 --s1 ameya-s1-v6all --tag ameya-ce-v6 --model intfloat/multilingual-e5-small

# 5. stage 2 on all of train (about 25 min, about 19 GB)
LEG=leg__rel,leg__n_s1,leg__n_r,leg__inter,leg__s1_only,leg__r_only
NX=nx__d1,nx__nudge,nx__digit_sub,nx__digit_swap,nx__suffix,nx__len_diff
python s2.py --feats ameya-fx5 --s1 ameya-s1-v6all --tag ameya-s2-v6all --groups str,cx,lo0,lg,ce,nx --cluster \
  --extra $LEG,ce__logit,$NX --all

# 6. decision inside the final candidate set, the candidate set itself, France rules v2
python decide.py --scores ameya-s2-v6all --col pc --tag ameya-model-v6all-c2 --p-cand 0.02 --top-r 2
python cands_final.py --s1 ameya-s1-v6all --tag ameya-cands-v6all-c2 --p-cand 0.02 --top-r 2
python post_ops.py --matches ameya-model-v6all-c2 --scores ameya-s2-v6all --cands ameya-cands-v6all-c2 \
  --feats ameya-fx5 --tag ameya-model-v6all-c2-ops
cd "$ROOT"

# 7. write the organiser TSVs and validate
python -m ber.pipeline --stage write --split test --tag ameya-model-v6all-c2-ops \
  --in candidates=ameya-cands-v6all-c2 --in matches=ameya-model-v6all-c2-ops
python student_resource/utils/validate_submission.py --matching "$BER_OUTPUT_DIR/matching_results.tsv" \
  --candidate "$BER_OUTPUT_DIR/candidate_pairs.tsv" --test-dir "$BER_DATA_DIR/test"
shasum -a 256 "$BER_OUTPUT_DIR/matching_results.tsv" "$BER_OUTPUT_DIR/candidate_pairs.tsv"
# Compare with submissions/files/2026-09-26-v6all-ops-c2/ (TODO: add the sha256 once packaged). GPU nondeterminism
# can change a few pairs; the reference check is then the holdout macro F0.5 in work/reports/ameya-model-v6all-c2.json.
