# Team Grenuke: Business Entity Resolution (Amazon ML Challenge 2026)

**Best submission:** "Composite B", public leaderboard **0.990879** (27 Sep 2026). Files: `matching_results.tsv`
(sha256 `df4bccd785b3fa785b7edcf0532288bcddc0010e2e31ce6f358064529ecb62e8`), `candidate_pairs.tsv` (sha256
`58c824a3f61c184fe7da1a448a4ac94284f288feff9c351abfe16a3dfc0520e5`). Validator PASS; every match is a candidate; one
owner per S2/S3 record; no cross-country pairs.

## 1. Problem and approach

For each Source-1 (S1) business record (name, address, country), list the Source-2/3 records of the same business
(0–11, 3.46 on average). Train covers US and India; test adds France, which has no labels. The metric is macro F0.5
per S1, so a false pair costs about four times a missed one, and any prediction on a true singleton scores 0. The
pipeline is therefore precision-first: **candidate generation → learned pair scoring in three stages → an
expected-F0.5 decision per S1 → rule layers → an independent re-check of the confident predictions.** Only the
provided data was used; all models are MIT or Apache-2.0 and at most 8B parameters.

1. **Candidate generation (blocking v3).** Multi-key retrieval per S1: trimmed name tokens, name 3/4-grams, a
   domain-name key (`vop.com` → `vop`), address words and house numbers, plus an Indic→Latin transliteration
   dictionary learned on the training folds. 66.4M train / 58.4M test pairs; the submitted candidate file keeps 3.70
   per S1 (every tighter cut lost holdout F0.5).
2. **Pair features (fx5).** Name and address string similarities (rapidfuzz), legal-form bitmasks (LLC/Inc/Pvt Ltd/
   SARL…), numeric-address features (house-number substitutions, digit swaps, suffix), learned word tables
   (per-token log-odds from the training folds), and per-S1 context (number of candidates, rank).
3. **Stage 0/1: XGBoost (GPU)** on 4 out-of-fold groups gives `p1`; a stage-0 cut removes 80% of the pairs.
4. **Cross-encoders on the uncertain band** (`p1` in [0.02, 0.99], about 1.5M pairs): the text `name ; address` of
   both sides, fine-tuned as pair classifiers. The stage-2 feature is the mean of z-scored logits of the members:
   multilingual-e5-large (×2 seeds, one self-trained on France), bge-reranker-v2-m3, Qwen2.5-1.5B (LoRA,
   self-trained on France) and **Qwen2.5-7B (LoRA, self-trained on France, counted twice)**; an e5-small model is
   a separate feature group. **Self-training** labels France (no labels) from the best model's final decisions
   (pc ≥ 0.9 or rule-added → 1, not predicted with pc ≤ 0.05 → 0, guarded, cross-fitted by S1 group so no French
   pair is scored by a model that saw its own label).
5. **Stage 2/3: XGBoost** with cluster features and the French pseudo-labelled rows, isotonic calibration (`pc`),
   then a stage-3 re-scoring with per-S1 context.
6. **Decision.** Per S1, the prediction set that maximises expected F0.5 under the calibrated `pc` (logit shift
   +0.2, crowd shift −0.3 for records contested by ≥4 S1, phantom 0.01), then rules: acronym join, a per-source
   cap, and for France an address "copy" rule (same normalised name at the exact address, 99.99% true on US/India),
   a cross-commune drop, and a look-alike word-swap drop.
7. **Independent re-check of the confident predictions.** 94.5% of final predictions have `p1` > 0.99 and were
   never read by a cross-encoder. The 7B scores them; a pair is dropped when its logit is below −6 (1,150 pairs).
8. **Composition per country.** US/India from the pipeline with the 7B in the mix (`g1w`); France from the
   round-2 self-trained French model (`v7sq7wg`); the 7B re-check applied to all three.

## 2. Models used

| model | licence | params | role |
|---|---|---|---|
| XGBoost 3.2 | Apache-2.0 | — | stages 0/1/2/3 |
| intfloat/multilingual-e5-small / -large | MIT | 118M / 560M | band cross-encoders (large ×2, one self-trained) |
| BAAI/bge-reranker-v2-m3 | Apache-2.0 | 568M | band cross-encoder |
| Qwen/Qwen2.5-1.5B (LoRA r16) | Apache-2.0 | 1.5B | band cross-encoder, self-trained on France |
| Qwen/Qwen2.5-7B (LoRA r16, bf16) | Apache-2.0 | 7.6B | band cross-encoder (×2 weight) and re-check of confident predictions |

## 3. Experiments (shared US/India holdout, 25% of train S1, macro F0.5; leaderboard where stated)

| step | holdout | leaderboard |
|---|---|---|
| stage 1 → stage 2 with e5-small and the band mix; rules v3; stage 3 | 0.99119 | v7nst 0.990179 |
| + expected-F0.5 decision per S1 and the French copy/city rules ("-dpc") | +48e-6 [+7, +91], paired bootstrap | 0.990264 |
| + Qwen2.5-1.5B and self-trained e5-large in the mix (v7sq) | 0.991246 | **0.990545** (+0.000281) |
| + round-2 French self-training ×3, look-alike drop, French expected-F0.5 decision (mixmdp) | — (France) | **0.990699** (+0.000154) |
| + Qwen2.5-7B ×2 in the mix for US/India (g1w) | **0.991323** (+62e-6; India +66e-6, P 0.998) | |
| + 7B re-check drop at logit < −6 (out of band) | +33e-6, both holdout halves positive | **0.990879** (+0.000180) |

Diagnostics that shaped the design: on the holdout the pipeline's predictions are 99.9% precise and 69% of the
remaining loss is partially-missed S1s; the missed true pairs are mostly empty-address name variants and never
become candidates (16.5k) or are rejected at `pc` ≈ 0 (15.2k). Every recall rule tried (empty-address name match,
alias-at-address, top-candidate rescue, 7B additions) was 17–71% true, below the ~75% an F0.5 addition needs, so none
was used. The French 7B drops are generic-name decoys (same name, same house number, different street): on the
labelled holdout that pattern is 0.5% true where the model rejects it (7B median −9.9) and 99.7% true where it
predicts it (median +7.9). Model scale alone did not help: the 7B's band AUC (0.9436) equals e5-large's (0.9439);
its value was diversity in the mix and the independent re-check. Self-training helped for two rounds (leaderboard
+0.000281, +0.000154) and hurt at round 3 (0.990819); a blend of all six cross-encoder logits raised band AUC to
0.9575 but lost 0.001 as a decision score, because stage 3's per-S1 context matters more than pair ranking.

## 4. Conclusion

A precision-first pipeline with calibrated per-S1 decisions reaches 0.9913 on the labelled countries and, through
guarded self-training plus an independent large-model re-check, about 0.9886 on the unlabelled one (public
leaderboard 0.990879). The remaining loss is recall on look-alike records that name and address alone cannot
separate; closing it needs better candidate generation and cluster-level evidence (S2↔S3 consistency), not larger
pair models. Source code: the `ber` package (blocking, features, evaluation), `experiments/ameya/model-v1` (stages,
cross-encoders, decision and rules), `experiments/bakshi/box` (7B training, re-check, composition).
