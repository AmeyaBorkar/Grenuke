# Review of the $100 plan against current GitHub

Snapshot: main `72a221fbd1bd488995efd0bd0b4c7b501d3f4660`, fetched 26 Sep late evening. Scope: current-state verification, PR30 package review and a corrected execution plan. No new rental, upload, model run or final package selection was performed.

## Confirmed current state

- v7n has a recorded **public score 0.989721, rank 8 at about 23:05 IST**. Rank is historical, not a guarantee of final placement. Holdout is 0.991211.
- Its local matching file `C:/Users/baksh/Downloads/New folder/matching_resultsv7n.tsv` has the recorded SHA256 `9b902971c72ada328bb9a23e1cdae3ec171c08239034114d5f9c60d9eaa92ae5`.
- Local v7nst `C:/Users/baksh/Downloads/New folder/matching_resultsv7nst.tsv` has SHA256 `659f5169cabbb2a3de2cb8580b614bbff718ea62d5b1fb4497243b50fcc34533`. It has no recorded public result yet.
- The paired v7n candidate file must have SHA256 `7246d9ec1ca32ea89bce1ec30f84a997af98bce7b33b7cfae3c21679ddcc31c3`. It was not found in the supplied download folders. The available v6 candidates (`cc3750d0...`) are a different package.
- Main's 23:15 status says **a replacement on-demand H100 already runs BGE and a France self-trained e5-large**. Reported alias `grenuke-vast`, key `grenuke_vast2`; account access is not available in this task. Avoid a duplicate rental. This status is not a live GPU health check.
- Latest issue #45 assigns uploads to Ameya and gives the current sequence. Do not spend slots separately or leave a diagnostic probe as the final upload.

Sources: [submission 03](https://github.com/AmeyaBorkar/Grenuke/blob/72a221fbd1bd488995efd0bd0b4c7b501d3f4660/submissions/records/2026-09-26_sub03.md), [latest status at this snapshot](https://github.com/AmeyaBorkar/Grenuke/blob/72a221fbd1bd488995efd0bd0b4c7b501d3f4660/docs/status/ameya.md), [issue #45](https://github.com/AmeyaBorkar/Grenuke/issues/45).

## Corrections before spending or interpreting results

1. **Targets:** 0.99 - 0.989721 = **0.000279** leaderboard gain. If all of it comes from France (weight 0.14975), the needed French gain is **0.0018631**. A +0.0069 France target instead corresponds to about +0.0010333 overall, a different ranking target. Keep first-place ambitions separate from the 0.99 threshold.
2. **fr0 identifies two quantities, not three country scores:** subtracting the France-empty baseline isolates France's contribution; the remaining US/India contribution is combined. One such probe cannot separate US and India. Do not use an inferred intercept as independent evidence for its own assumptions.
3. **Mass mismatch is a diagnostic, not proof of bad decisions:** sum(pc) 3.5456 versus expected copy count 3.46 does not identify which individual predictions are false. The expected generator mean must also fit the exact country, subset and candidate population. A model can match the count with wrong owners. Treat this as a secondary check, not a shipping gate.
4. **AUC is not linearly convertible to F0.5 or leaderboard points.** The 0.872/0.878 figures use rule-derived pseudo-labels, not a representative labeled France holdout. Their ranking is useful evidence, but deriving +0.00027 LB by a proportional rule is not a measured forecast.
5. **No calibrated success probability exists here.** Remove the 20–25% / 40–45% numbers and guaranteed top-10 language. Historical rank and a few runs do not justify them.
6. **A stronger model cannot be declared unmeasurable everywhere:** evaluate its labeled-country OOF/holdout contribution first, then its French proxy diagnostics. France's true effect still needs a same-baseline public comparison. Specify the exact Qwen checkpoint, license, parameter count, input format and measured throughput before adding a run; the plan currently has no Qwen training/inference slot that produces its assumed logits.
7. **Joint copy-count assignment is a separate high-risk hypothesis.** The plan first rules out assignment engines, then makes one central. A count prior must be soft, tolerate unmatched records and omitted candidates, and optimize expected macro F0.5 rather than merely likelihood or total match count. No reason yet to place it on the critical path. At most run a bounded offline gate after the existing model experiments finish; do not force records into owners to hit 3.46.
8. **Budget is a cap, not an exact price quote.** Vast charges compute, storage and bandwidth; storage can continue while an instance is stopped. The $42/$24/$34 allocation is meaningful only if all these charges fit inside those buckets. Verify current offer and account usage, preserve contingency, and avoid paying for a duplicate instance. [Official pricing](https://github.com/vast-ai/docs/blob/main/guides/pricing.mdx).
9. **Persistence:** an instance-local 200 GB disk is not an independent backup. Save checkpoints and completed logit chunks outside the disposable instance and verify the copy before destruction. A failed spot job does not establish a general statistical failure rate from three attempts.
10. **Gate semantics:** paired holdout CI > 0 is useful for changes affecting US/India. A France-only transform may leave that holdout exactly unchanged and cannot establish France gain there. Define separate transfer/no-regression checks and a human-controlled France probe; do not call a null known-country result a positive gate.

BAAI/bge-reranker-v2-m3 is Apache-2.0 per its [official model repository](https://huggingface.co/BAAI/bge-reranker-v2-m3/tree/main). The useful BGE experiment is already underway upstream. Runtime figures in the pasted plan remain estimates until benchmarked on the actual instance and input lengths.

## PR30 package: concrete gaps

PR30 is merged commit `161dad99c94d5e4648072422f8c4369b06d45c42`. Its exact diff is exported locally to `C:/Users/baksh/Documents/Codex/2026-09-25/in/outputs/PR30_packaging.diff` and is [available on GitHub](https://github.com/AmeyaBorkar/Grenuke/pull/30/files).

| component | current draft | required for v7n |
|---|---|---|
| reproduce script | reproduce_v6all.sh trains e5-small and v6 stage 2 | two e5-large runs (one epoch seed 26; two epochs seed 7), train-band z-mean, cem2 import, v7n stage 2, stage 3, robust rules, acronym join, matching candidate output |
| README | claims v6 primary, final hashes/metrics TODO | v7n exact hashes, holdout 0.991211, public 0.989721, complete ensemble and true runtime |
| methodology | calls v6 final; says bigger model was not the fix; inferred France presented too strongly | v7n consensus design, actual measured score table, France estimate explicitly conditional, no universal gate claim |
| environment | torch and transformers unpinned | exact producing machine's Python/CUDA/torch/transformers/tokenizers/safetensors versions; do not invent pins from laptop |
| model list | e5-small + XGBoost only | include two fine-tuned e5-large runs and their MIT license; distinguish BGE evaluated from models actually in final variant |
| artifacts | latest matching files locally, old candidate file | obtain matching candidate TSV and producing run manifest; validate both together |
| clean rerun | recipe estimates about 3 h for an older model | fresh work directory, correct v7n chain, actual successful log and output checks; laptop RAM 16 GB is below recorded 18–19 GB stage peaks |

The documentation is owned/staged under `docs/package/`; its current gaps make an assertion of a guaranteed complete, reproducible package premature. A valid TSV alone does not prove the code can reproduce it. No final ZIP was built with mismatched candidate files or a stale v6 script.

## Useful exact source paths

Fresh isolated checkout: `C:/Users/baksh/Documents/Codex/2026-09-25/in/work/GrenukeFinalPlan`, branch `bakshi/final-plan-review`.

- `C:/Users/baksh/Documents/Codex/2026-09-25/in/work/GrenukeFinalPlan/docs/package/README.md`
- `C:/Users/baksh/Documents/Codex/2026-09-25/in/work/GrenukeFinalPlan/docs/package/Documentation_template.md`
- `C:/Users/baksh/Documents/Codex/2026-09-25/in/work/GrenukeFinalPlan/docs/package/reproduce_v6all.sh`
- `C:/Users/baksh/Documents/Codex/2026-09-25/in/work/GrenukeFinalPlan/docs/package/requirements.txt`
- `C:/Users/baksh/Documents/Codex/2026-09-25/in/work/GrenukeFinalPlan/experiments/ameya/model-v1/RECIPE.md` (currently detailed through v7ce3; v7n continuation is in the handover below).
- `C:/Users/baksh/Documents/Codex/2026-09-25/in/work/GrenukeFinalPlan/docs/handover/2026-09-26_2049_ameya_squeeze-v7n.md`
- `C:/Users/baksh/Documents/Codex/2026-09-25/in/work/GrenukeFinalPlan/docs/decisions/2026-09-26_2135_model-v7n.md`
- `C:/Users/baksh/Documents/Codex/2026-09-25/in/work/GrenukeFinalPlan/experiments/ameya/model-v1/zmean_ce.py`
- `C:/Users/baksh/Documents/Codex/2026-09-25/in/work/GrenukeFinalPlan/experiments/ameya/model-v1/ce_box.py`
- `C:/Users/baksh/Documents/Codex/2026-09-25/in/work/GrenukeFinalPlan/experiments/ameya/model-v1/ce_import.py`
- `C:/Users/baksh/Documents/Codex/2026-09-25/in/work/GrenukeFinalPlan/experiments/ameya/model-v1/stage3.py`
- `C:/Users/baksh/Documents/Codex/2026-09-25/in/work/GrenukeFinalPlan/experiments/ameya/model-v1/acr_join.py`
- `C:/Users/baksh/Documents/Codex/2026-09-25/in/work/GrenukeFinalPlan/student_resource/utils/validate_submission.py`

Older local v8 untracked files in `C:/Users/baksh/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/bakshi/v8/` belong to another session and were not edited or executed.

## Corrected next actions

1. Use the existing H100 experiment and await its measured results. Obtain account/instance access before assuming control of it; no new spending occurred in this review.
2. Bring the package up to the final selected model using the PR30 scaffold and the v7n handover. Obtain exact candidate TSV and producing environment/run manifest first. A request for its path is pending with the user.
3. With a suitable machine and an independent working directory, run the complete selected-model recipe from raw TSVs. Record real completion, runtime, hashes and validator output. A clean v6 rerun is not a clean v7n rerun.
4. Compare the existing BGE/self-training candidates and same-baseline fr090r probe under the captain's slot budget. Use fr0 only if its information is worth displacing one of the five slots; it is not automatically free.
5. Freeze and package the actually best validated variant, preserving v7n as the observed fallback. Keep the final upload as the chosen best. Do not add speculative assignment machinery or Qwen merely because budget remains.

GPU access, current account spend, the correct candidate TSV and producing environment versions remain required to finish the paid-run/final-package request. This review and PR30 diff are complete; paid execution and clean reproduction are not claimed.
