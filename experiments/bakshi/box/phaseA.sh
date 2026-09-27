#!/usr/bin/env bash
# Phase A on the pipeline box: rebuild everything up to the cross-encoder band, exactly as
# final-package/reproduce.sh steps 0-5, plus the c2 candidate set every later stage reads.
#
#   bash phaseA.sh            # after setup.sh main; logs to $ROOT/logs/phaseA.log (+ one log per step)
#
# Parallel only where the code shows independence:
#   - records train / test (separate inputs, separate outputs);
#   - after feats.py: nx and legal (read records + <feats>-str only) run beside the lo chain
#     (feats_lo -> feats_lo_proxy --calib needs token_lo.parquet -> lo_proxy test -> lo_mix);
#   - band export and cands_final (both read only the stage-1 scores) run beside ce.py.
# Everything else keeps reproduce.sh order (a train run writes tables its test run reads).
set -euo pipefail
ROOT="${ROOT:-/workspace/grenuke}"
. "$ROOT/env.sh"
L="$ROOT/logs"
mkdir -p "$L" "$CE_BOX_DIR"
NJ="${NTHREADS:-64}"

step () {   # step <name> <command...>: timed, logged, fails the phase on error
  local name="$1"; shift
  local t0=$(date +%s)
  echo "$(date +%T) START $name" | tee -a "$L/phaseA.log"
  if "$@" > "$L/A_$name.log" 2>&1; then
    echo "$(date +%T) DONE  $name ($(( $(date +%s) - t0 ))s)" | tee -a "$L/phaseA.log"
  else
    echo "$(date +%T) FAIL  $name ($(( $(date +%s) - t0 ))s) -- see $L/A_$name.log" | tee -a "$L/phaseA.log"
    tail -20 "$L/A_$name.log" >> "$L/phaseA.log"
    return 1
  fi
}
par () {    # par <step-spec-fn>...: run shell functions in parallel, fail if any fails
  local pids=() rc=0
  for f in "$@"; do "$f" & pids+=($!); done
  for p in "${pids[@]}"; do wait "$p" || rc=1; done
  return $rc
}

cd "$ROOT/repo"
echo "$(date +%T) ===== phase A start =====" | tee -a "$L/phaseA.log"

# ---- 0. records (parallel) + the Indic->Latin dictionary ----
rec_tr () { step records_train python -m ber.pipeline --stage records --split train --n-jobs "$NJ"; }
rec_te () { step records_test  python -m ber.pipeline --stage records --split test  --n-jobs "$NJ"; }
par rec_tr rec_te
step dict python "$M/feats.py" --split train --tag ameya-fx1 --dict-only

# ---- 1. blocking v3 ----
BP="--set trim_s1=15 --set trim_r=4 --set indic_dict=ameya-fx1 --set ns_ngrams=4 --set ns_domain_len=8 --set nw_words=6"
step block_train python -m ber.pipeline --stage block --split train --tag ameya-block-v3 $BP --n-jobs "$NJ"
step block_test  python -m ber.pipeline --stage block --split test  --tag ameya-block-v3 $BP --n-jobs "$NJ"

cd "$M"
# ---- 2. pair features, bundle ameya-fx5 ----
step feats_train python feats.py --cands ameya-block-v3 --split train --tag ameya-fx5
step feats_test  python feats.py --cands ameya-block-v3 --split test  --tag ameya-fx5
nx_chain ()  { step nx_train python feats_nx.py --feats ameya-fx5 --split train && \
               step nx_test  python feats_nx.py --feats ameya-fx5 --split test; }
leg_chain () { step legal_train python feats_legal.py --feats ameya-fx5 --split train && \
               step legal_test  python feats_legal.py --feats ameya-fx5 --split test; }
lo_chain ()  { step lo_train python feats_lo.py --feats ameya-fx5 --split train && \
               step lo_test  python feats_lo.py --feats ameya-fx5 --split test && \
               step lop_train python feats_lo_proxy.py --feats ameya-fx5 --split train --calib && \
               step lop_test  python feats_lo_proxy.py --feats ameya-fx5 --split test; }
par nx_chain leg_chain lo_chain
step lo_mix python lo_mix.py --feats ameya-fx5

# ---- 3. stage 0 + 1 ----
step s1 python s1.py --feats ameya-fx5 --tag ameya-s1-v6all --groups str,cx,lo0,lg,nx \
  --drop leg__r_only_bits,leg__s1_only_bits --all

# ---- 4-5. e5-small feature (GPU) beside the band export and the c2 candidate set (CPU) ----
ce_small () { CUDA_VISIBLE_DEVICES=${CE_GPU:-0} step ce_small python ce.py --feats ameya-fx5 --s1 ameya-s1-v6all \
                --tag ameya-ce-v6 --model intfloat/multilingual-e5-small; }
band ()     { step band_export python -c "from ce import band_pairs; import os; d=os.environ['CE_BOX_DIR']; [band_pairs('ameya-s1-v6all', s)[['s1','r','row','p1'] + (['fold','y'] if s == 'train' else [])].to_parquet(f'{d}/band_{s}.parquet', index=False) for s in ('train','test')]"; }
cands ()    { step cands_c2 python cands_final.py --s1 ameya-s1-v6all --tag ameya-cands-v6all-c2 --p-cand 0.02 --top-r 2; }
par ce_small band cands

# ---- band check: does OUR band reproduce the one every cross-encoder was trained on? ----
step band_check python "$B/box/remap_ce.py" --src-band "$ROOT/box_ameya" --src-out "$ROOT/box_ameya/out_e5l" \
  --dst-band "$CE_BOX_DIR" --out "$CE_BOX_DIR/check_e5l" --min-coverage 0.0
grep -E "coverage|written" "$L/A_band_check.log" | tee -a "$L/phaseA.log"
echo "$(date +%T) ===== phase A done =====" | tee -a "$L/phaseA.log"
