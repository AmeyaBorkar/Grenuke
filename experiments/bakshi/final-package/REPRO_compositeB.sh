#!/usr/bin/env bash
# Composite B (public LB 0.990879): the exact command lines Bakshi's side ran on 27 Sep 2026, in order (issue #66 item B).
# A record of what ran, not an unattended driver. All times are wall clock; box clocks were UTC (IST = UTC + 5:30).
#
#   output files (identical to the upload):
#     matching_results.tsv  df4bccd785b3fa785b7edcf0532288bcddc0010e2e31ce6f358064529ecb62e8
#     candidate_pairs.tsv   58c824a3f61c184fe7da1a448a4ac94284f288feff9c351abfe16a3dfc0520e5
#
#   Composite B = US/India from g1w-dpc (this chain, with the Qwen2.5-7B cross-encoder counted twice in stage 2)
#               + France from mixmdp (Ameya's upload, 0.990699; its own recipe is on his side of #66)
#               - every predicted pair outside the CE band (stage-1 p1 > 0.99) that the 7B scores below logit -6.
#   Candidate rows are taken per S1 from the same source as its matches (France: mixmdp's candidate file; US/India:
#   ameya-cands-g1w-c2a), which is why a single-pipeline rebuild gives a different candidate hash.
#
# Every script below is on main, byte-identical to the copies the boxes ran (checked 29 Sep).
# Models: Qwen/Qwen2.5-7B, revision d149729398750b98c0af14eb82c78cfe92750796 (Apache-2.0, 7.6B); the other
# cross-encoders (e5-small/large MIT, bge-reranker-v2-m3 Apache-2.0, Qwen2.5-1.5B Apache-2.0) are Ameya's recipe.
set -euo pipefail
exit 0   # documentation: run the blocks by hand, on the machine named in each block

# =====================================================================================================================
# 0. Inputs taken from Ameya's side (all keyed by (s1, r); the band files are the ones every cross-encoder trained on)
# =====================================================================================================================
# box_ameya/band_train.parquet   876987f008c17901ff95ba6576657a479ee0992f184430401564edc06340080b  (1,568,554 rows)
# box_ameya/band_test.parquet    ec8d1db8dfe3e730bb2db006f2349ea2270691c4c3a8424409c5967ebd088355  (1,490,930 rows)
# box_ameya/out_{e5l,bge}/       ce_{train,test}.parquet + config.json (v7ens2 hand-off, 26 Sep)
# box_ameya/out_{qst,e5ls}/      ce_{train,test}.parquet + config.json (grenuke_must_have.zip 44d86ae0...d2ac)
# box_ameya/pseudo_s2_fr_v7ce3.parquet   stage-2 French pseudo-labels (round 1, teacher v7ce3)
# box/pseudo_fr_v7sq.parquet             band French pseudo-labels (teacher v7sq-dpc) -- trains q7st
# ref/v7sq_dpc_matching.tsv              for diffs only
# mixmdp pair (France source):   matching_results_mixmdp.tsv  00ec3d9be505df6158eb3f575258fc42f310c796403514157fb13709578f021b
#                                candidate_pairs_mixmdp.tsv   b55c2b1d01fa9699e55adbf44c16c10dfe3f69e28b199110fd283e68980b826a
# stack/{apply_swapsim,compose,dp_france}.py from ameya/final-stack d6c2e38 (now on main via #65)

# =====================================================================================================================
# 1. PIPELINE BOX: 2x RTX 4090 24 GB, 64 vCPU, 258 GB RAM, driver 565.77, the image's torch 2.11.0+cu128, Python 3.12
# =====================================================================================================================
ROOT=/workspace/grenuke
bash $ROOT/repo/experiments/bakshi/box/setup.sh main        # writes $ROOT/env.sh
. $ROOT/env.sh

# 1a. Phase A: records -> Indic dict -> blocking v3 -> fx5 features -> stage 0+1 -> e5-small -> band -> c2 candidates.
#     Ran through ops/run_chain2.sh (blocking train and test side by side), then ops/run_chain3.sh after the crash below.
bash $ROOT/run_chain2.sh
#     s1.py crashed at its last, report-only line: it compares with matches/ameya-baseline-v0, which a fresh work dir
#     lacks. The stage-1 models and train scores were already written, so ops/run_chain3.sh writes an EMPTY placeholder
#     for that tag and scores test with the saved models (s1.py ... --test-only), then resumes phaseA.sh (finished
#     steps are skipped by their markers) and runs g0.
bash $ROOT/run_chain3.sh
#     Times: records 45 s, dict 4.5 min, blocking train 11 min / test 15 min (in parallel), features 52 min (fx5 + nx + lo + legal + lo proxy + lo_mix),
#     s1 8 min + test scoring 4 min, e5-small (GPU 0) 21 min, band export 15 s, c2 candidates 9 s.
#     Blocking: 66,429,057 train / 58,437,794 test pairs.
#     Band check vs Ameya's band: train 100.0000%, test 99.9999% of rows matched by (s1, r) (1 pair missing).

# 1b. g0 = the v7sq recipe rebuilt (the reproduction gate; also the source of the French pairs the 7B re-scores).
CUDA_VISIBLE_DEVICES=0 bash $ROOT/repo/experiments/bakshi/box/phaseB.sh g0 "e5l qst e5ls bge" \
  $ROOT/box_ameya/pseudo_s2_fr_v7ce3.parquet
#     ~59 min (s2 22 min). Holdout macro F0.5 0.991261 (v7sq's own 0.991246); France vs v7sq-dpc 4.3 changes per
#     1000 S1, US/India ~1.2. Validator and audit_matching.py PASS.

# =====================================================================================================================
# 2. TRAINING BOX: 4x H100 80 GB SXM. The q7st run started on an interruptible box (driver 560.35, torch 2.11.0+cu126),
#    which was taken away at ~09:35 UTC; it resumed from the Drive checkpoints on an on-demand box (driver 595.71,
#    torch 2.11.0+cu128, transformers 5.17.0, peft 0.21.0, Python 3.12). Same seeds, same rows, same code.
# =====================================================================================================================
ROOT=/workspace/grenuke
bash $ROOT/repo/experiments/bakshi/box/train_jobs.sh setup     # venv, pinned stack, records, model prefetch
# band_{train,test}.parquet (Ameya's) and pseudo_fr_v7sq.parquet sit in $ROOT/box
bash $ROOT/repo/experiments/bakshi/box/train_jobs.sh launch    # = the three commands below + an auto-merge watcher
#   CUDA_VISIBLE_DEVICES=g python llm_group.py --model Qwen/Qwen2.5-7B --name q7st --group g \
#       --pseudo $ROOT/box/pseudo_fr_v7sq.parquet --infer-batch 512            # g = 0, 1, 2 on GPUs 0, 1, 2
#   defaults (llm_group.py): --sep " || " --us-in-frac 0.5 --lr 1e-4 --batch 64 --epochs 1 --max-len 96 --lora-r 16
#                            --seed 26 --ckpt-every 600 (LoRA alpha 32, dropout 0.05, all attention + MLP projections)
#   training: 9,663 / 9,706 / 9,912 steps per group at ~3.6 steps/s (first box) and ~2.3 steps/s (second box),
#             about 392k labelled + 226-242k French pseudo-labelled pairs per group; 0 non-finite steps skipped
#   scoring:  ~2.0M pairs per group at ~600 pairs/s (~55 min)
python $ROOT/repo/experiments/bakshi/box/llm_merge.py --name q7st
#   -> box/out_q7st/ce_{train,test}.parquet, config.json: band AUC holdout 0.9436, OOF 0.9396
#   LoRA adapters: box/out_q7st/adapter_{0,1,2} (Drive grenuke-train-backup/final_zip/models/q7st/)

# =====================================================================================================================
# 3. PIPELINE BOX: g1w = the g0 recipe with q7st added twice to the z-mean (2 of 6 votes)
# =====================================================================================================================
mkdir -p $ROOT/box_ameya/out_q7st      # ce_train.parquet, ce_test.parquet, config.json copied from the training box
touch $ROOT/logs/.doneB_g1w_decide_c2  # decide_c2 writes ameya-model-g1w-c2, which nothing downstream reads
CUDA_VISIBLE_DEVICES=0 bash $ROOT/repo/experiments/bakshi/box/phaseB.sh g1w "e5l qst e5ls bge q7st q7st" \
  $ROOT/box_ameya/pseudo_s2_fr_v7ce3.parquet
#     ~39 min (s2 20 min). Holdout macro F0.5 0.991323 (+0.000062 over g0; India +66.1e-6, P 0.998 by Ameya's
#     paired bootstrap). US/India of Composite B = output/g1w/dpc (the French-only layers leave US/India unchanged).

# =====================================================================================================================
# 4. The 7B re-check of the confident predictions (94.5% of final predictions have p1 > 0.99 and no CE ever read them)
# =====================================================================================================================
# 4a. PIPELINE BOX: the pairs to score.
cd $M && python $B/box/rescore_export.py --final ameya-model-g0-s3-ops3a-dpcsf --s3 ameya-s3-g0 \
  --pred ameya-model-g0-s3 --out $ROOT/box/rescore
#     -> fr_final_pairs.parquet (870,019 French predicted pairs), hold_pred_pairs.parquet + hold_truth.parquet
#        (631,001 predictions of 186,897 labelled holdout S1)
cd $M && python $B/box/analysis/export_usin.py
#     -> usin_final_pairs.parquet (4,744,395 US/India predictions of g1w-s3-ops3a-dpc with p1 > 0.99)

# 4b. TRAINING BOX: score them with adapter_0 (ops/run_rescore.sh, ops/run_rescore_usin.sh).
D=$ROOT/box/rescore
S="python $B/box/score_pairs.py --adapter $ROOT/box/out_q7st/adapter_0"          # --batch 512 --max-len 96 default
CUDA_VISIBLE_DEVICES=2 $S --pairs $D/hold_pred_pairs.parquet --split train --out $D/hold_scored.parquet      # 23 min
CUDA_VISIBLE_DEVICES=3 $S --pairs $D/fr_final_pairs.parquet --split test --part 0/2 --out $D/fr_scored_0.parquet  # 15 min
CUDA_VISIBLE_DEVICES=2 $S --pairs $D/fr_final_pairs.parquet --split test --part 1/2 --out $D/fr_scored_1.parquet  # 15 min
for i in 0 1 2 3; do   # 46 min each, in parallel on GPUs 0-3
  CUDA_VISIBLE_DEVICES=$i $S --pairs $D/usin_final_pairs.parquet --split test --part $i/4 --out $D/usin_scored_$i.parquet
done

# 4c. The rule, checked on the labelled holdout before use: drop when q7 logit < -6 and p1 > 0.99.
cd $M && python $B/box/rescore_eval.py --dir $ROOT/box/rescore --out-band-only
#     t = -6: +0.000033 macro F0.5 (fixed halves +0.000022 / +0.000043); that bucket is 8% true.
#     -6 has the largest gain; -5 gains less (+26e-6, both halves positive), -4 has a negative half (+12e-6 overall),
#     -3 and looser lose. On 3,000 random 25% subsets of the holdout S1 the -6 gain is positive in 99.7%
#     (analysis/resample_drop.py).

# =====================================================================================================================
# 5. LAPTOP (CPU): the composition that produced Composite B (both output files)
# =====================================================================================================================
#   g1w_dpcsfq/ = output/g1w/dpcsfq from ops/build_q7drop.sh (g1w-dpcsf minus the French 7B drops); only its US/India
#                 rows are used here, and those equal g1w-dpc's.
#   mixmdp/     = matching_results.tsv + candidate_pairs.tsv of mixmdp (hashes above)
python experiments/bakshi/box/compose_tsv.py --labelled g1w_dpcsfq --unlabelled mixmdp \
  --s1-tsv student_resource/dataset/test/test_source1.tsv --train-s1-tsv student_resource/dataset/train/train_source1.tsv \
  --drop "rescore/fr_scored_*.parquet" "rescore/usin_scored_*.parquet" --drop-logit -6 --out compB
#     drop list 1,169 pairs; 1,150 present -> dropped (840 France, 310 US/India). Rows: 259,452 France from mixmdp.
python student_resource/utils/validate_submission.py --matching compB/matching_results.tsv \
  --candidate compB/candidate_pairs.tsv --test-dir student_resource/dataset/test          # PASS
python experiments/bakshi/final-package/audit_matching.py --matching compB/matching_results.tsv \
  --candidate compB/candidate_pairs.tsv --test-dir student_resource/dataset/test          # AUDIT PASS
sha256sum compB/matching_results.tsv compB/candidate_pairs.tsv   # df4bccd7... / 58c824a3...
#     5,851,832 pairs, 99,802 empty S1, 3.3776 per S1; 0 records with two owners; 0 cross-country; 0 matches outside
#     the candidates. France 870,307 pairs, India 2,734,227, US 2,247,298.

# Non-determinism: XGBoost with fixed seeds is deterministic on one machine; the cross-encoders are not bit-identical
# across GPUs (TF32 / cuDNN kernel choice), so a rerun moves a few pairs. The reference check is the holdout macro F0.5
# (g0 0.991261, g1w 0.991323) and the drop-rule gain, not the file hash; the submitted bytes ship verbatim.
