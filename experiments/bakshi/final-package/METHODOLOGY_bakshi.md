# Methodology: Bakshi's part of Composite B (g1w + Qwen2.5-7B + the 7B re-check)

For issue #69. Written for completeness, not polish. Every number carries its source:
- **[holdout]**: a report in `work/reports/` on the shared holdout (549,699 US/India S1, folds 0–4, `ber.eval`), copied to Drive `grenuke-train-backup/pipeline/work/reports/`;
- **[log]**: a run log (Drive `grenuke-train-backup/logs/` and `pipeline/logs/`);
- **[LB]**: the public leaderboard;
- **[Ameya]**: from Ameya's analysis (RESEARCH_v6 §6.19, #62/#64);
- **[estimate]**: derived here, method stated.

The exact commands, in order: `REPRO_compositeB.sh` (this folder). Every script named below is on `main`, byte-identical to the copies the boxes ran (checked 29 Sep).

## 1. My part of Composite B

Composite B (**0.990879 [LB]**, the team's best) has three parts:
- **US/India** from `g1w`: Ameya's v7sq pipeline, rebuilt from the raw TSVs on my rented box, with my Qwen2.5-7B cross-encoder `q7st` added twice to the stage-2 cross-encoder mix;
- **France** from Ameya's `mixmdp` (0.990699 [LB]), unchanged;
- minus every confident prediction (stage-1 p1 > 0.99, never read by any cross-encoder) that `q7st` scores below logit −6. This covers all three countries: 840 French and 310 US/India pairs.

**From Ameya's side:**
- the band files every cross-encoder was trained on;
- the four cross-encoder outputs of the v7sq mix (e5l, qst, e5ls, bge);
- the French pseudo-label files;
- the stack scripts;
- the mixmdp submission.

**`compose_tsv.py`** joins the two submissions per S1 country and applies the drop lists.

## 2. Rebuilding the pipeline on my box (`phaseA.sh`)

Pipeline box: 2× RTX 4090 24 GB, 64 vCPU, 258 GB RAM, driver 565.77. Times are wall clock [log `phaseA.log`, UTC].

| step | command (in `phaseA.sh`) | time | result |
|---|---|---|---|
| records | `ber.pipeline --stage records` ×2 | 45 s | |
| Indic dictionary | `feats.py --dict-only` (learned on train folds 5–19) | 4.5 min | 693 entries [log] |
| blocking v3 | `ber.pipeline --stage block`, train and test in parallel | 11 / 15 min | 66,429,057 train / 58,437,794 test pairs [log], equal to the team's earlier ~66.4M / 58.4M |
| fx5 features | `feats.py`, `feats_nx.py`, `feats_lo.py`, `feats_legal.py`, `feats_lo_proxy.py`, `lo_mix.py` | 52 min | |
| stage 0+1 | `s1.py --feats ameya-fx5 --tag ameya-s1-v6all --groups str,cx,lo0,lg,nx --drop leg__r_only_bits,leg__s1_only_bits --all` | 8 min + 4 min test | see note |
| e5-small | `ce.py ... --model intfloat/multilingual-e5-small` (GPU 0) | 21 min | feature `ce` |
| band export, c2 candidates | `ce.band_pairs`, `cands_final.py --p-cand 0.02 --top-r 2` | 15 s, 9 s | `ameya-cands-v6all-c2` |
| band check | `remap_ce.py` of Ameya's e5l onto our band | 10 s | train 100.0000%, test 99.9999% of rows matched by (s1, r); **1** test pair missing [log] |

**Note on `s1.py`.** It crashed on its last, report-only line, which compares with `matches/ameya-baseline-v0`; that tag doesn't exist in a fresh work dir. The models and train scores were already written. `ops/run_chain3.sh` therefore:
1. writes an **empty placeholder** for that tag;
2. scores test with `s1.py ... --test-only`.

Consequence: every `gate_vs_baseline_v0` field in the rebuilt reports compares against an empty baseline and must be ignored.

**Reproduction gate `g0`** (the v7sq recipe on the rebuilt pipeline, Ameya's four cross-encoders remapped): `phaseB.sh g0 "e5l qst e5ls bge" pseudo_s2_fr_v7ce3.parquet`.
- Holdout macro F0.5: **0.991261** (US 0.991064, India 0.991558) [holdout `ameya-model-g0-s3`], against **0.991246** for v7sq's original [Ameya's package ledger].
- Output vs the uploaded v7sq-dpc file (`diff_candidates.py`, predictions changed per 1000 S1):

  | country | added | dropped | changed |
  |---|---|---|---|
  | France | 1.20 | 3.14 | **4.34** |
  | India | 0.48 | 0.65 | 1.13 |
  | US | 0.55 | 0.68 | 1.23 |

  [log `B_g0_diff_dpc.log`]
- Validator PASS, `audit_matching.py` PASS. Stage-3 decisions are not bit-reproducible across machines [Ameya], so a small difference is expected. The gate's purpose was to make sure nothing built on this box was silently different.

## 3. The Qwen2.5-7B cross-encoder `q7st`

**Model.** `Qwen/Qwen2.5-7B`, revision **`d149729398750b98c0af14eb82c78cfe92750796`** [log: HF resolve-cache, 46 lines], Apache-2.0, 7.6B parameters.

**Architecture** (`sachi/ce_llm.py build`, called through `ameya/model-v1/ce_llm_st.py` and `bakshi/box/llm_group.py`):
- `AutoModelForSequenceClassification`, 1 output logit (the `score` head, trained and saved with the adapter), bf16 base weights.
- LoRA: r 16, alpha 32, dropout 0.05, targets `q_proj k_proj v_proj o_proj gate_proj up_proj down_proj`. The trainable weights (LoRA + head) are kept in fp32.
- Pad token = EOS.

**Input.** For each side, `name ; address` (each truncated to 300 characters), with `" || "` before the record side. The pair is truncated to **96 tokens** (median 37 [log]).

**Training** (`llm_group.py` defaults, the `ce_llm_st.py` recipe):
- AdamW, lr 1e-4, weight decay 0; linear warm-up over the first 3% of steps, then linear decay.
- Batch 64 (batches bucketed by length), 1 epoch, bf16 autocast, gradient-norm clip 1.0, seed 26.
- Non-finite-gradient guard: a step with a non-finite gradient norm is skipped. **0 were skipped** [log].

**Rows.** The stage-1 uncertainty band, p1 ∈ [0.02, 0.99]: 1,568,554 train / 1,490,930 test pairs (Ameya's band files, sha256 `876987f0…` / `ec8d1db8…`).

**Out-of-fold groups (3).**
- Train rows of folds 5–19 are split into 3 groups by `oof_group(s1)`. Group *g* trains on a 50% sample (`--us-in-frac 0.5`) of the labelled rows of the other two groups, plus the French pseudo-labelled pairs whose S1 falls in the other two thirds (`fold_of(s1) % 3`).
- Model *g* scores:
  - its own group's train rows (out of fold);
  - all holdout rows (folds 0–4), averaged over the 3 models;
  - all US/India test rows, averaged over the 3 models;
  - **only its own third of the French test pairs**.

**Self-training labels.** `pseudo_fr_v7sq.parquet` (Ameya, `pseudo_labels.py`), teacher v7sq-dpc (`ameya-model-v7sq-s3-ops3a-dpc`, the best LB model at the time, 0.990545). 385,274 French band pairs:

| label | rule | pairs |
|---|---|---|
| 1 | in the teacher's final matches with pc ≥ 0.9, or added by the French rules / acronym join | 74,325 |
| 0 | not in the final with pc ≤ 0.05, or an op-B prediction the rules dropped | 273,160 |
| −1 | unlabelled | 37,789 |

[counted from the file]

**Cross-fitting.** Because model *g* never trains on the pseudo-labels of the French third it scores, no French pair is scored by a model that saw its own label, or the labels of other records of its S1.

**Rows per group** [log]:

| group | labelled | pseudo | OOF AUC |
|---|---|---|---|
| 0 | 392,391 | 226,027 | 0.9397 |
| 1 | 394,567 | 226,562 | 0.9393 |
| 2 | 391,928 | 242,381 | 0.9399 |

**Compute.**
- 3× H100 80 GB, one OOF group per GPU (`llm_group.py`, same rows and seeds as the sequential script; the RNG draws of earlier groups are replayed).
- Training: 9,663 / 9,706 / 9,912 steps.
- Box 1 (interruptible, driver 560.35, torch 2.11.0+cu126) ran at ~3.6 steps/s and was taken away mid-training (~09:35 UTC).
  - Checkpoints (trainable weights + optimiser + scheduler + step + RNG, every 600 s, written atomically) were backed up to Google Drive every 5 min.
  - The run resumed on an on-demand box (driver 595.71, torch 2.11.0+cu128) at steps 4,321 / 6,561 / 4,371, at ~2.3 steps/s.
- Scoring: ~2.0M pairs per group at ~600 pairs/s (~55 min).
- Total per group on the second box: 4,462–5,135 s [log].
- `llm_merge.py --name q7st` assembled the three parts exactly as the sequential script would, and refuses parts from different runs.

**Quality.** Band AUC on labelled pairs [each model's `config.json`]:

| cross-encoder | params | holdout | OOF |
|---|---|---|---|
| stage-1 p1 (same pairs) | — | 0.9297 | — |
| e5-large, 1 epoch (`e5l`) | 560M | 0.9391 | 0.9350 |
| e5-large, 2 epochs (`e5l2`) | 560M | 0.9441 | 0.9403 |
| e5-large, France self-trained (`e5ls`) | 560M | 0.9439 | 0.9403 |
| bge-reranker-v2-m3 (`bge`) | 568M | 0.9417 | 0.9382 |
| Qwen2.5-1.5B LoRA, France self-trained (`qst`) | 1.5B | 0.9381 | 0.9332 |
| **Qwen2.5-7B LoRA, France self-trained (`q7st`)** | 7.6B | **0.9436** | **0.9396** |
| Qwen3-4B-Base LoRA (`q34st`, not used) | 4.0B | 0.9411 | 0.9370 |

**Scale alone did not buy AUC:** the 7B ties e5-large. Its value was as a different model family in the mix (section 4) and as an independent reader of the confident predictions (section 5).

**`q34st`** (Qwen/Qwen3-4B-Base, Apache-2.0): same recipe. It merged at ~18:43 IST, too late for a stage-2 variant before the deadline, and its AUC is below the 7B's. Not used.

**Failed fillers:**
- `microsoft/mdeberta-v3-base`: 999 of its first 1,000 steps had non-finite gradients under bf16 (a known DeBERTa-v3 issue); killed.
- `Alibaba-NLP/gte-multilingual-reranker-base`: crashed with an index assert in its remote code under transformers 5.17.

## 4. `g1w`: stage 2 → final with the 7B in the mix (`phaseB.sh`)

**Remapping.** `remap_ce.py` moves each cross-encoder's logits from Ameya's band to ours by (s1, r), never by row number, because `ce_import.py` places logits positionally. It aborts below 99.5% coverage. All six inputs: train 100.0000%, test 99.9999% [log].

**The mix.** `zmean_ce.py`: the mean of the z-scored logits of e5l, qst, e5ls, bge, q7st and q7st (**the 7B counted twice**, so 2 of 6 votes). This is feature group `zg1w`, alongside e5-small's `ce`. The mean is used instead of separate logits for the reason in Ameya's §4.3: in France the models disagree 4× as often, and a stage 2 given separate logits extrapolates on those disagreements.

**Ablation** (same pipeline, only the mix changes; holdout macro F0.5 after stage 3 + decision) [holdout `ameya-model-<v>-s3`]:

| variant | mix | overall | US | India | vs g0 |
|---|---|---|---|---|---|
| g0 | e5l, qst, e5ls, bge | 0.991261 | 0.991064 | 0.991558 | — |
| g1 | + q7st ×1 | 0.991276 | 0.991076 | 0.991577 | +15e-6 |
| **g1w** | **+ q7st ×2** | **0.991323** | **0.991114** | **0.991635** | **+62e-6** |
| g1x3 | + q7st ×3 | 0.991322 | 0.991111 | 0.991639 | +61e-6 |
| g7only | q7st alone | 0.991286 | 0.991089 | 0.991581 | +25e-6 |
| gbag | mean of the g0, g1, g1w stage-2 scores | 0.991313 | 0.991096 | 0.991637 | +52e-6 |

- ×2 was the smallest weight at the plateau (×3 is flat), and the 7B alone is worse than the mix.
- Ameya's paired bootstrap against v7sq3: India **+66.1e-6, P 0.998**; US +26.2e-6, P 0.906 [Ameya].
- Paired against g1w on India: g1x3 −13.5e-6, g7only −70.3e-6 [Ameya].

**Downstream settings for g1w** (as run):

| step | command / settings | holdout macro F0.5 |
|---|---|---|
| stage 2 | `s2.py --feats ameya-fx5 --s1 ameya-s1-v6all --tag ameya-s2-g1w --groups str,cx,lo0,lg,ce,zg1w,nx --cluster --extra <leg__*, ce__logit, zg1w__logit, nx__*> --all --pseudo pseudo_s2_fr_v7ce3.parquet` (weight 1, top 30, 3,000 rounds). 10,065,671 stage-2 rows; best iterations 824 / 957 / 1,032 / 911; 20 min | pc @0.70: **0.991190** (US 0.990995, India 0.991482) [holdout `ameya-s2-g1w`] |
| decide (c2) | skipped: writes `ameya-model-g1w-c2`, which nothing downstream reads | — |
| stage 3 | `stage3.py --scores ameya-s2-g1w --p-cand 0.02 --top-r 2` | |
| decide (s3) | `decide.py --scores ameya-s3-g1w --col pc --p-cand 0.02 --top-r 2`; the rule it chose: expected-F0.5, threshold 0.675 | **0.991323** (US 0.991114, India 0.991635) |
| post_ops, acr_join | `--robust-addr`; France only | (France: no labels) |
| stack (`-dpc`) | `stack/stack.sh g1w` | labelled countries: Ameya's gate +48.1e-6 on v7s; not re-measured here |

For comparison, g0's stage 2: pc @0.725 0.991185, c2 decision 0.991179 [holdout].

## 5. The 7B re-check of confident predictions

**Why.** Most final predictions have p1 > 0.99: 95.6% of the holdout sample's predictions and 90.5% of the French ones [log `rescore_export`], 94.5% overall [Ameya]. The cross-encoders only ever scored the band, so for those pairs the final decision rests on stage 1–3 features alone. The 7B reads them as an independent second opinion.

**The pairs:**
- `rescore_export.py --final ameya-model-g0-s3-ops3a-dpcsf --s3 ameya-s3-g0 --pred ameya-model-g0-s3`:
  - 870,019 French final pairs;
  - a 34% random sample of holdout S1 (186,897 S1, 631,001 predictions, precision 0.99896) with truth.
- `analysis/export_usin.py`: 4,744,395 US/India final predictions of g1w-dpc with p1 > 0.99.
- `score_pairs.py --adapter out_q7st/adapter_0` (batch 512, max 96 tokens) on H100s, at 430–480 pairs/s per GPU with 2–4 jobs sharing the box [log].

**Truth rate by 7B logit** (holdout sample, predictions outside the band) [log `rescore_eval.py --out-band-only`]:

| 7B logit | holdout n | truly a match | French n (share of French predictions) |
|---|---|---|---|
| < −6 | 24 | 8.3% | 859 (0.10%) |
| [−6, −4) | 51 | 86.3% | 209 (0.02%) |
| [−4, −2) | 138 | 94.9% | 321 (0.04%) |
| [−2, 0) | 6,616 | 99.6% | 897 (0.10%) |
| [0, 2) | 16,893 | 99.8% | 4,461 (0.51%) |
| ≥ 2 | 579,440 | 100.0% | 780,629 (89.7%) |

**Drop rule "drop if 7B < t"**: change in holdout macro F0.5 (sample of 186,897 S1; halves fixed by `s1 // 7 % 2`) [log]:

| t | drops | truly matches | ΔF all | half A | half B | French drops |
|---|---|---|---|---|---|---|
| −8 | 7 | 0 | +11e-6 | +4e-6 | +19e-6 | 743 |
| **−6** | **24** | **2** | **+33e-6** | **+22e-6** | **+43e-6** | **859** |
| −5 | 36 | 12 | +26e-6 | +8e-6 | +43e-6 | 959 |
| −4 | 75 | 46 | +12e-6 | −3e-6 | +27e-6 | 1,068 |
| −3 | 121 | 88 | −4e-6 | −20e-6 | +11e-6 | 1,203 |
| −2 | 213 | 177 | −55e-6 | −67e-6 | −42e-6 | 1,389 |
| 0 | 6,829 | 6,768 | −3,168e-6 | −3,318e-6 | −3,018e-6 | 2,286 |

- **−6 is the loosest cut positive in both halves.**
- Ameya's check on the whole holdout (3× larger): −6 +37e-6 (halves +33 / +41), −5 +29e-6, −4 +17e-6 [Ameya].
- On 3,000 random 25% subsets of the holdout S1 the −6 gain is positive in **99.7%** (mean +32.8e-6, sd 16.7e-6) [estimate: resampling, 29 Sep].

**Leakage check.** Adapter 0 trained on the French pseudo-labels of S1 thirds 1–2 (band pairs only), yet it flags French pairs outside the band at the same rate in every third: 0.112% (unseen third 0), 0.108%, 0.107%, with median logit 9.6 in each [log, 27 Sep].

**On test.**
- 859 French rejects (0.10% of French predictions, **25× the US/India rate** of 0.004%) and 310 US/India rejects out of 4.74M.
- The French rejects are mostly **generic-name decoys**: the same generic name and the same house number on a different street [Ameya]. On the labelled holdout that pattern is 0.5% true where our model rejected it (7B median −9.9), and 99.7% true where it predicted it (median +7.9). 78% of the French rejects are this pattern; a bge detector with no self-training labels flags 82% of them [Ameya].

## 6. Composite B and B7

**`compose_tsv.py`:**
- For each test S1, both the matching row and the candidate row come from one source:
  - the labelled countries (read from the train S1 file, not hard-coded) from `--labelled` (g1w-dpcsfq; its US/India rows equal g1w-dpc's);
  - the other countries from `--unlabelled` (mixmdp).
- Then the drop lists (the 7B score files, filtered to q7 < −6 and p1 > 0.99) remove pairs by parsed eid.
- Ownership and matches ⊆ candidates hold by construction: records never cross countries, and each S1's rows come from one audited source. Both are re-checked by `audit_matching.py`.

**Composite B:**

| | value |
|---|---|
| inputs | g1w-dpcsfq (US/India); mixmdp (`00ec3d9b…` / `b55c2b1d…`); `fr_scored_*`, `usin_scored_*` |
| drops | drop list 1,169 pairs; 1,150 present and dropped: 840 France, 310 US/India |
| output | `matching_results.tsv` `df4bccd785b3fa785b7edcf0532288bcddc0010e2e31ce6f358064529ecb62e8`, `candidate_pairs.tsv` `58c824a3f61c184fe7da1a448a4ac94284f288feff9c351abfe16a3dfc0520e5` |
| checks | validator PASS, audit PASS |
| pairs | 5,851,832; 99,802 empty S1; 3.3776 per S1 |
| audit | 0 two-owner records, 0 cross-country pairs, 0 matches outside candidates |
| per country | France 870,307 pairs, India 2,734,227, US 2,247,298 |

**Leaderboard:** **0.990879**, +0.000180 over mixmdp (0.990699) [LB]. Split [estimate: holdout deltas × country share of test S1]:

| source | estimate |
|---|---|
| India g1w vs v7sq3 (+66.1e-6 × 0.467) | ≈ +31e-6 |
| US g1w vs v7sq3 (+26.2e-6 × 0.383, not significant) | ≈ +10e-6 |
| US/India 7B drops (+33e-6 × 0.850) | ≈ +28e-6 |
| **French 7B drops: the remainder, ≈ +111e-6** | **so the 840 French drops were nearly all false** |

**For comparison:**
- **mixf2** (India g1w, US v7sq3, France from round-3 self-training, the same 7B drops) scored **0.990819** [LB]. So round-3 French labels lost to round 2's, the pattern the LOCO self-training ladder predicted.
- **B7** (`fr_drop_ladder.py --stop B7`) extends the French drops below −6:
  - [−6, −4) everywhere;
  - [−4, 0) where Qwen3-4B also rejects (logit < −2);
  - the remaining out-of-band [−4, −2);
  - and restores 251 look-alike pairs the 7B accepts (> 2).

  France changed +251 / −1,699 vs B. It scored **0.990875** [LB], a tie: the labelled −6 cut-off was already right, and France's higher decoy density did not carry into the −6…−2 bands.

## 7. What did not work (measured)

| idea | measurement | source |
|---|---|---|
| Recall: empty-address records whose core name matches exactly one S1, unassigned | 24% true (holdout-only competitors); 17% true with all train S1 as competitors; break-even ~75% | [log `analysis/empty_addr*.py`, `empty_all.py`] |
| + sibling / same-source evidence | best slice 59% true (193 pairs) | [log] |
| Empty-S1 rescue (add the top free candidate) | negative at every pc threshold (−505e-6 at 0.2 … −4e-6 at 0.5) | [log `empty_s1.py`] |
| 7B additions (recall) | best holdout precision 71% | [Ameya] |
| 7B drop at −4 / −2 / 0 | +12e-6 (one half negative) / −55e-6 / −3,168e-6 | [log] |
| 7B ×3 / 7B alone in the mix | +61e-6 (flat) / +25e-6 | [holdout] |
| Bag of stage-2 variants | +52e-6, below g1w | [holdout] |
| Cross-fitted logistic blend of all six CE logits + p1 + pc | band AUC 0.9575 vs pc 0.9276, but **−0.001** as the decision score; +2…4e-6 as a drop/add edit | [log `meta_band.py`, `meta_edit.py`] |
| Drop mining (depth-5 tree on 7B, p1, pc, similarities, house number, name frequency) | one leaf < 70% true: half A +33e-6, held-out half B **−15e-6** (overfit) | [log `drop_mine.py`] |
| Same house number, different street as a drop rule by itself | 100% true among US/India predictions; only a decoy signal together with the 7B | [log `street_pattern.py`], [Ameya] |
| In-band two-model drop (7B [−4, 0) and 4B < −2) | +8e-6 (halves −7 / +24e-6) | [log] |
| French look-alike word-swap drop (`apply_swapsim`) | −25…−27e-6 by the calibrated estimator; B+ restored the pairs the 7B accepts | [Ameya] |
| mDeBERTa-v3 / gte-multilingual as extra encoders | non-finite bf16 gradients / remote-code crash | [log] |

**Where US/India loses** (g0 decisions, 549,699 holdout S1) [log `analysis/headroom.py`, `miss_anatomy.py`]:
- Predictions are 99.9% precise.
- Of 4,804 S1-equivalents of lost F0.5:

  | kind of S1 | S1 | loss |
  |---|---|---|
  | partially missed | 43,863 | 3,331 (69%) |
  | missed entirely | 964 | 964 (20%) |
  | false positive only | 1,655 | 386 (8%) |
  | wrong prediction on a singleton | 68 | 68 |
  | both a false positive and a miss | 174 | 55 |

- 48,509 true pairs are missed:
  - 16,455 were never candidates (blocking);
  - 237 went to another S1;
  - the rest were rejected, 15,152 of them at pc ≈ 0. These are mostly empty-address name variants.

## 8. Environment and reproduction

- **Pipeline box:** 2× RTX 4090 24 GB, driver 565.77 (CUDA 12.7), Python 3.12.3, torch 2.11.0+cu128 (the image's own; a bf16 CUDA matmul passed on this driver).
- **Training box:** 4× H100 80 GB SXM, Python 3.12 (uv venv), transformers 5.17.0, peft 0.21.0.
  - Box 1: driver 560.35, torch 2.11.0+cu126.
  - Box 2: driver 595.71, torch 2.11.0+cu128.
- **Package pins:** see `requirements_box.txt` (this folder). It is not a `pip freeze`, since the boxes were destroyed; it lists the pins of `box/setup.sh` and `box/train_jobs.sh` and the versions the logs printed.
- **Commands:** `REPRO_compositeB.sh` (this folder).
- **Non-determinism:** XGBoost with fixed seeds is deterministic on one machine; the cross-encoders are not bit-identical across GPUs, so a rerun moves a few pairs. The reference checks are:
  - g0 0.991261 and g1w 0.991323 [holdout];
  - the drop-rule table above.
- **Drive** (`grenuke-train-backup`):
  - `final_zip/output/`: Composite B's two TSVs, sha256 `df4bccd7…` / `58c824a3…` (verified in Drive, `SHA256SUMS.txt` beside them).
  - `final_zip/models/q7st/`: `adapter_{0,1,2}/` (`adapter_model.safetensors`, 161,547,632 bytes each; Drive md5 `1457b7c6…`, `89e51c9c…`, `56e33c6a…`) and the merged `config.json`.
  - `box/out_q7st/`: `ce_{train,test}.parquet` (the 7B band logits); `rescore/`: the 7B score files for France, the holdout sample and US/India.

## 9. Tables worth putting in the document

1. The cross-encoder AUC table (section 3): scale alone didn't help; diversity did.
2. The mix ablation (section 4), per country.
3. The 7B truth-rate buckets and the drop-rule table (section 5): the clearest evidence behind the re-check.
4. The leaderboard sequence v7sq-dpc 0.990545 → mixmdp 0.990699 → mixf2 0.990819 → **Composite B 0.990879**, with B7 0.990875 as the "went too far" control.
5. The US/India loss anatomy (section 7): why the remaining gap is recall on look-alikes, not precision.
