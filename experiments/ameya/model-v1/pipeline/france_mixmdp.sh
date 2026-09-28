#!/usr/bin/env bash
# France block of Composite B: the French rows of mixmdp (public leaderboard 0.990699), rebuilt from the v7sq chain.
#
#   Called by Composite B's driver (src/box/compositeB.sh, step 7):   FR_DIR=<dir> bash "$M/pipeline/france_mixmdp.sh"
#   It can also run on its own from the package root once VARIANT=v7sq STACK=1 reproduce.sh has finished.
#
# What it builds (the 27 Sep run, in order):
#   F1  three more French-facing cross-encoders on the uncertain band, self-trained on the round-1 French labels:
#       e5ls2 (multilingual-e5-large, 2nd seed of e5ls), bges (bge-reranker-v2-m3), e5fr (France-heavy e5-large)
#   F2  cmq7 = z-scored mean of qst, e5ls, e5ls2, bges, e5fr, imported as one stage-2 feature group
#   F3  round-2 French stage-2 pseudo-labels from the finished v7sq-dpc (teacher; public 0.990545)
#   F4  the French rule populations (true-copy edits y=1, op-B look-alikes y=0; truth known from US/India)
#   F5  the guard: empty-address records keep their round-1 label, the rule populations override
#   F6  stage 2 of v7sq7wg: the guarded labels at sample weight 3 (pipeline/s2w.py)
#   F7  decide -> stage 3 -> decide -> France rules v3 -> acronym join   (run_local_full_w.sh, after its stage 2)
#   F8  the stacked rules (stack/stack.sh) -> v7sq7wg-dpc
#   F9  minus the look-alike word swaps (stack/apply_swapsim.py), plus the France expected-F0.5 decision (stack/dp_france.py)
#   F10 write $FR_DIR/matching_results.tsv + candidate_pairs.tsv. compose_tsv.py takes only their French rows.
#
# Inputs from the v7sq chain (reproduce.sh VARIANT=v7sq STACK=1, Composite B's step 1):
#   features ameya-fx5 (with the e5-small group ce), scores ameya-s1-v6all, candidates ameya-cands-v6all-c2;
#   $CE_BOX_DIR/band_{train,test}.parquet, out_qst/, out_e5ls/ (round-1 self-trained), pseudo_fr_v7ce3.parquet and
#   pseudo_s2_fr_v7ce3.parquet (round-1 labels, teacher v7ce3); the reports of ameya-model-v7ce3-c2 / -s3 (gate bases);
#   the teacher's tags ameya-model-v7sq-s3, -s3-ops3, -s3-ops3a-dpc and scores ameya-s3-v7sq.
#
# Knobs (environment): FR_DIR (output dir; default work/out_france_mixmdp), CE_GPU (GPU for the cross-encoders,
#   default 0), E5FR_PARALLEL (1 = e5fr's three out-of-fold groups side by side on one 80 GB card, as run; 0 = one after
#   another). Every step is skipped when its output exists, so a rerun resumes.
#
# Hardware and times of the 27 Sep run: cross-encoders on one H100 80 GB (e5ls2 ~2.0 h, bges ~1.3 h, e5fr ~20 min with
#   its three groups side by side, inferred from the launch times: its config.json was not kept); stage 2 on a 128-vCPU
#   box (33 min); F7-F9 on a 24-core laptop (~25 min).
#
# Models: intfloat/multilingual-e5-large (MIT, 560M), BAAI/bge-reranker-v2-m3 (Apache-2.0, 568M); qst reused from the
#   v7sq chain: Qwen/Qwen2.5-1.5B with LoRA (Apache-2.0).
#
# DEVIATIONS from the 27 Sep run:
#   1. Paths only: the box ran ce_box.py and zmean_ce.py from copies in its box dir and s2w.py from a copy in
#      model-v1; the laptop ran F7 from the research-v5 worktree (stage3/decide/post_ops/acr_join/common/cluster/
#      ce_import byte-identical to these files). Here: $M, $CE_BOX_DIR and $BER_WORK_DIR.
#   2. The cross-encoders train on this package's own band (as in compositeB.sh), not on the laptop band of 26 Sep.
#   3. Same code under its committed name: pseudo_labels.py for the streaming copy pl_lean.py (same rules, rows and
#      order); rule_pop.py for r7/rulepop.py (only a sys.path line differs); pseudo_guard.py for gpuplan/guard.py
#      (same logic; guard.py also wrote a band-level file nothing here reads); stack/stack.sh for stack_model.sh +
#      apply_combo.py + merge_dpc.py (all five stages identical on a test model: work/logs/repo_test.log "PORT OK").
#   4. F9 runs on v7sq7wg-dpc itself. The run first composed it with v7sq3's US/India (mixmc), then dropped a
#      precomputed look-alike list (apply_changes.py + novel/drop_swapsim_all.parquet), then ran dp_france.py. Both
#      steps touch only the countries without labels, and records never cross countries, so the French rows are the
#      same. Checked on 29 Sep with the 27 Sep artifacts: F9 on v7sq7wg-dpc gives mixmdp's French rows exactly
#      (871,147 pairs, 0 / 0 differ; 454 look-alikes, DP drops 224, adds 357 of 361). The US/India rows of $FR_DIR
#      are v7sq7wg's own; compose_tsv.py discards them.
#   5. Not rebuilt, since nothing downstream reads them: F7's intermediate package, the stack's h2pc package and
#      COPY/SWAP report, and the mixm / mixmdp packages.
#   6. bges's seed is not in its config.json (ce_box.py does not record seeds). 26 is used: ce_box.py's default and
#      the seed of the non-self-trained bge; the later bges2 was logged as "seed 27, second seed of bges".
set -euo pipefail

M="${MODEL_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
if [ -d "$M/../ber" ]; then SRC="$(cd "$M/.." && pwd)"                               # package: src/{ber,model_v1}
else SRC="$(cd "$M/../../.." && pwd)/code/business_entity_resolution/src"; fi      # repo: experiments/ameya/model-v1
export BER_DATA_DIR="${BER_DATA_DIR:-$(pwd)/student_resource/dataset}"
export BER_WORK_DIR="${BER_WORK_DIR:-$(pwd)/work}"
export CE_BOX_DIR="${CE_BOX_DIR:-$BER_WORK_DIR/box}"
export PYTHONPATH="$M:$SRC:${PYTHONPATH:-}"
FR_DIR="${FR_DIR:-$BER_WORK_DIR/out_france_mixmdp}"
LOGS="$BER_WORK_DIR/logs_france"
mkdir -p "$FR_DIR" "$LOGS"

V=v7sq7wg; G=cmq7; MT=ameya-model-$V; CA=ameya-cands-$V-c2a
LEG=leg__rel,leg__n_s1,leg__n_r,leg__inter,leg__s1_only,leg__r_only
NX=nx__d1,nx__nudge,nx__digit_sub,nx__digit_swap,nx__suffix,nx__len_diff
say () { echo "$(date +%T) == france: $*"; }
done_file () { [ -f "$BER_WORK_DIR/$1" ]; }       # e.g. done_file matches/<tag>/test.parquet
need () { [ -e "$1" ] || { echo "FAIL: $1 is missing; run the v7sq chain first (VARIANT=v7sq STACK=1 reproduce.sh)" >&2; exit 1; }; }

need "$CE_BOX_DIR/band_train.parquet"; need "$CE_BOX_DIR/out_qst/ce_test.parquet"; need "$CE_BOX_DIR/out_e5ls/ce_test.parquet"
need "$CE_BOX_DIR/pseudo_fr_v7ce3.parquet"; need "$CE_BOX_DIR/pseudo_s2_fr_v7ce3.parquet"
need "$BER_WORK_DIR/matches/ameya-model-v7sq-s3-ops3a-dpc/test.parquet"
cd "$M"

# ------------------------------------------------------------------------------------------------------------------
# F1. Cross-encoders, round-1 French labels (teacher v7ce3), cross-fitted by S1 third like e5ls / qst.
#     27 Sep band AUC holdout / OOF: e5ls2 0.9440 / 0.9404, bges 0.9424 / 0.9389 (their config.json);
#     e5fr about 0.918 on the holdout by design (a quarter of the US/India band; gate 0.90, box3_r4b.sh).
# ------------------------------------------------------------------------------------------------------------------
P1="$CE_BOX_DIR/pseudo_fr_v7ce3.parquet"
ce () {  # ce <name> <ce_box.py args...>
  local n=$1; shift
  if [ -f "$CE_BOX_DIR/out_$n/ce_test.parquet" ]; then say "F1 $n exists, skipping"; return 0; fi
  say "F1 $n"
  CUDA_VISIBLE_DEVICES="${CE_GPU:-0}" python "$M/ce_box.py" --name "$n" "$@" > "$LOGS/ce_$n.log" 2>&1 \
    || { echo "FAIL: ce_box.py $n; see $LOGS/ce_$n.log" >&2; exit 1; }
}
ce e5ls2 --model intfloat/multilingual-e5-large --lr 2e-5 --batch 128 --epochs 2 --seed 11 --pseudo "$P1"   # box/run_e5ls2.sh
ce bges  --model BAAI/bge-reranker-v2-m3 --lr 2e-5 --batch 128 --epochs 1 --seed 26 --pseudo "$P1"         # deviation 6
if [ ! -f "$CE_BOX_DIR/out_e5fr/ce_test.parquet" ]; then                                                  # box3_r4.sh / r4b
  say "F1 e5fr (three out-of-fold groups, then merge)"
  A=(--model intfloat/multilingual-e5-large --name e5fr --lr 2e-5 --batch 128 --epochs 1 --seed 31 --pseudo "$P1"
     --us-in-frac 0.25 --target-only-test --hold-groups 0)
  run_g () { CUDA_VISIBLE_DEVICES="${CE_GPU:-0}" python "$M/ce_box.py" "${A[@]}" --only-group "$1" > "$LOGS/ce_e5fr_g$1.log" 2>&1; }
  if [ "${E5FR_PARALLEL:-1}" = 1 ]; then
    pids=(); for g in 0 1 2; do run_g "$g" & pids+=($!); done
    for p in "${pids[@]}"; do wait "$p" || { echo "FAIL: an e5fr group failed; see $LOGS/ce_e5fr_g*.log" >&2; exit 1; }; done
  else
    for g in 0 1 2; do run_g "$g" || { echo "FAIL: e5fr group $g; see $LOGS/ce_e5fr_g$g.log" >&2; exit 1; }; done
  fi
  CUDA_VISIBLE_DEVICES="${CE_GPU:-0}" python "$M/ce_box.py" "${A[@]}" --merge > "$LOGS/ce_e5fr_merge.log" 2>&1 \
    || { echo "FAIL: e5fr merge; see $LOGS/ce_e5fr_merge.log" >&2; exit 1; }
fi
python - "$CE_BOX_DIR" <<'PY'
import json, sys
box = sys.argv[1]
for n in ("qst", "e5ls", "e5ls2", "bges", "e5fr"):
    a = json.load(open(f"{box}/out_{n}/config.json"))["auc"]
    print(f"  {n:6s} band AUC holdout {a['holdout']:.4f}  OOF {a.get('oof', float('nan')):.4f}")
a = json.load(open(f"{box}/out_e5fr/config.json"))["auc"]["holdout"]
raise SystemExit(0 if a >= 0.90 else "FAIL: e5fr holdout band AUC below its gate 0.90 (box3_r4b.sh)")
PY

# ------------------------------------------------------------------------------------------------------------------
# F2. cmq7: one stage-2 feature, the mean of the five z-scored logits (zmean_ce.py), imported as group cmq7.
# ------------------------------------------------------------------------------------------------------------------
if ! done_file features/ameya-fx5-$G/test.parquet; then
  say "F2 $G = zmean(qst, e5ls, e5ls2, bges, e5fr)"
  python zmean_ce.py "$CE_BOX_DIR/out_$G" "$CE_BOX_DIR/out_qst" "$CE_BOX_DIR/out_e5ls" "$CE_BOX_DIR/out_e5ls2" \
    "$CE_BOX_DIR/out_bges" "$CE_BOX_DIR/out_e5fr"
  python ce_import.py --feats ameya-fx5 --src "$CE_BOX_DIR/out_$G" --group $G --column ${G}__logit
fi

# ------------------------------------------------------------------------------------------------------------------
# F3-F5. Guarded round-2 stage-2 labels (RESEARCH_v6.md 6.17). 27 Sep:
#   F3 "target band pairs 1429666: positive 861326 (rule adds 306, acr 363), negative 520104 (op-B drops 241),
#      unlabelled 48236"
#   F4 128,856 rule pairs: A 38,304 + ACR 14,884 + APP 11,652 true-copy (y=1), op-B 64,016 look-alikes (y=0)
#   F5 "pairs 1429666, empty record address 214288 (... changed vs new 16803), rule pairs 95350: positive 861340,
#      negative 516463, unlabelled 51863"
# ------------------------------------------------------------------------------------------------------------------
S2P="$CE_BOX_DIR/pseudo_s2_fr_v7sq.parquet"; POP="$CE_BOX_DIR/rulepop_fr.parquet"; GUARD="$CE_BOX_DIR/pseudo_s2_fr_v7sq_guard.parquet"
[ -f "$S2P" ] || { say "F3 round-2 labels from v7sq-dpc"
  python pseudo_labels.py ameya-model-v7sq-s3 ameya-s3-v7sq ameya-model-v7sq-s3-ops3 ameya-model-v7sq-s3-ops3a-dpc \
    s1:ameya-s1-v6all "$S2P"; }
[ -f "$POP" ] || { say "F4 French rule populations"; python rule_pop.py "$POP"; }
[ -f "$GUARD" ] || { say "F5 guard"; python pseudo_guard.py "$CE_BOX_DIR/pseudo_s2_fr_v7ce3.parquet" "$S2P" "$POP" "$GUARD"; }

# ------------------------------------------------------------------------------------------------------------------
# F6. Stage 2 of v7sq7wg (box3_r4b.sh). 27 Sep: "pseudo: 1429666 target stage-2 rows, 1377803 labelled (0.625
#     positive)"; 10,065,671 stage-2 rows, 65 features; holdout macro F0.5 of pc 0.991138 at 0.725.
# ------------------------------------------------------------------------------------------------------------------
if ! done_file scores/ameya-s2-$V/test.parquet; then
  say "F6 stage 2 $V (guarded labels x3)"
  python pipeline/s2w.py --feats ameya-fx5 --s1 ameya-s1-v6all --groups str,cx,lo0,lg,ce,$G,nx --cluster \
    --extra $LEG,ce__logit,${G}__logit,$NX --all --tag ameya-s2-$V --pseudo "$GUARD" --pseudo-weight 3 \
    > "$LOGS/s2_$V.log" 2>&1 || { echo "FAIL: stage 2 $V; see $LOGS/s2_$V.log" >&2; exit 1; }
fi

# ------------------------------------------------------------------------------------------------------------------
# F7. run_local_full_w.sh after its stage 2. 27 Sep holdout macro F0.5: c2 decision 0.991186 (rule expected_f05),
#     stage-3 decision 0.991223 (rule threshold 0.725).
# ------------------------------------------------------------------------------------------------------------------
if ! done_file matches/$MT-s3-ops3a/test.parquet; then
  say "F7 decide -> stage 3 -> decide -> rules v3 -> acronym join"
  python decide.py --scores ameya-s2-$V --col pc --tag $MT-c2 --base ameya-model-v7ce3-c2 --p-cand 0.02 --top-r 2
  python stage3.py --scores ameya-s2-$V --tag ameya-s3-$V --p-cand 0.02 --top-r 2
  python decide.py --scores ameya-s3-$V --col pc --tag $MT-s3 --base ameya-model-v7ce3-s3 --p-cand 0.02 --top-r 2
  python post_ops.py --matches $MT-s3 --scores ameya-s3-$V --cands ameya-cands-v6all-c2 --feats ameya-fx5 \
    --tag $MT-s3-ops3 --robust-addr
  python acr_join.py --split test --matches $MT-s3-ops3 --cands ameya-cands-v6all-c2 --tag $MT-s3-ops3a --cands-tag $CA
fi

# ------------------------------------------------------------------------------------------------------------------
# F8. The stacked rules. 27 Sep (threshold 0.725): France +375 same-name copies at the exact address, -76 cross-commune
#     pairs; -dpc 5,814,539 pairs (US/India 4,943,071 from the expected-F0.5 decision, France 871,468).
# ------------------------------------------------------------------------------------------------------------------
if ! done_file matches/$MT-s3-ops3a-dpc/test.parquet; then
  say "F8 stack $V"
  STACK_OUT="$BER_WORK_DIR/stack_$V" bash "$M/stack/stack.sh" $V
fi

# ------------------------------------------------------------------------------------------------------------------
# F9. The look-alike word-swap drop, then the France expected-F0.5 decision. 27 Sep: "France look-alikes 454";
#     "stage-3 threshold 0.725 reproduced: 867059 vs 867059"; "DP additions 382: 21 look-alike or op-B swaps not
#     added"; "DP drops 224, adds 357 of 361". France 871,468 - 454 - 224 + 357 = 871,147 pairs.
# ------------------------------------------------------------------------------------------------------------------
if ! done_file matches/$MT-s3-ops3a-dpcs/test.parquet; then
  say "F9 look-alike drop"
  (cd "$M/stack" && python apply_swapsim.py $MT-s3-ops3a-dpc $MT-s3-ops3a-dpcs)
fi
if ! done_file matches/$MT-s3-ops3a-dpcsf/test.parquet; then
  say "F9 France expected-F0.5 decision"
  (cd "$M/stack" && python dp_france.py $V $CA $MT-s3-ops3a-dpcs $MT-s3-ops3a-dpcsf)
fi

# ------------------------------------------------------------------------------------------------------------------
# F10. The organiser TSVs of the France block, and its French pair count (27 Sep: 871,147).
# ------------------------------------------------------------------------------------------------------------------
say "F10 write -> $FR_DIR"
BER_OUTPUT_DIR="$FR_DIR" python -m ber.pipeline --stage write --split test --tag $MT-s3-ops3a-dpcsf \
  --in "candidates=$CA" --in "matches=$MT-s3-ops3a-dpcsf"
python - "$MT-s3-ops3a-dpcsf" <<'PY'
import sys
import pyarrow.compute as pc, pyarrow.parquet as pq
from ber.artifacts import read_table
from ber.paths import records_path
tr = set(pc.unique(pq.read_table(records_path("train"), columns=["country"])["country"]).to_pylist())
t = pq.read_table(records_path("test"), columns=["eid", "source", "country"]).to_pandas()
s1 = t[t.source == 1].set_index("eid").country
m = read_table("matches", sys.argv[1], "test", ["s1", "r"])
fr = ~s1.reindex(m.s1).isin(tr).to_numpy()
print(f"  France block: {int(fr.sum()):,} pairs on {m.s1[fr].nunique():,} S1 of countries without labels "
      f"(27 Sep: 871,147); {int((~fr).sum()):,} US/India pairs, discarded by compose_tsv.py")
PY
say "done: $FR_DIR"
