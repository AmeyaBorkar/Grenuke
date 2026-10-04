# Decisions: MDL (XGBoost stages 0–3, calibration, out-of-fold training)

**Summary.**
- The matching model is a cascade of four XGBoost stages (XGBoost is a gradient-boosted tree learner). Stage 0 cheaply filters pairs; stage 1 scores each pair (p1); stage 2 adds competition, cluster and cross-encoder features and is calibrated into pc, a probability that can be read literally; stage 3 re-scores contested records. Every stage is trained out of fold (OOF): each training pair is scored by a model that never saw its S1, the Source-1 reference business.
- Sixteen decisions, in time order: the learner, the staging and the OOF design, the final fit on all of train, stage 3, the bundles chosen as upload candidates (v3, v6all, v7sq3, g1w), and the tuning, bagging and France-only variants we rejected.
- Scope: unless marked LB (public leaderboard), F0.5 means macro F0.5 on the local holdout (549,699 labelled US/India S1, no France). US/India part is the US/India share of the weighted LB score (LB = US/India part + 0.14975 × France F0.5). Evidence levels: [M] measured, [E] estimated, [R] reported, [U] uncertain. Times are IST. 1e-6 means 0.000001 of F0.5.

## Index

| ID | decision | when (IST) | status |
|---|---|---|---|
| D-MDL-01 | XGBoost on the GPU, not LightGBM | 2026-09-25 12:13 | adopted |
| D-MDL-02 | The v0 baseline: XGBoost stage 1, argmax ownership, one tuned threshold | 2026-09-25 14:15 | adopted for Submission 1; superseded by model v1 |
| D-MDL-03 | Stage 2: a collective model over the full candidate graph, isotonic-calibrated, with cluster support | 2026-09-25 14:15 | adopted |
| D-MDL-04 | Owner-removed training examples and the other Saturday extras deferred | 2026-09-25 14:15 | deferred (never built) |
| D-MDL-05 | A stage-0 cascade filter before stage 1 | 2026-09-25 17:50 | adopted |
| D-MDL-06 | Out-of-fold stage 1 over three S1 groups; holdout and test get the mean of the three models | 2026-09-25 17:50 | adopted |
| D-MDL-07 | Run the model chain from Ameya's experiment folder, not from `ber.model` | 2026-09-25 18:21 | adopted |
| D-MDL-08 | Gate G4: keep the collective stage 2 (Sachi) | 2026-09-25 21:03 | adopted |
| D-MDL-09 | Model v3 (full rebuild) as the next upload candidate | 2026-09-25 23:28 | adopted |
| D-MDL-10 | Final fit on all of train (`--all`): the holdout becomes a fourth OOF group | 2026-09-26 03:37 | adopted |
| D-MDL-11 | Stage 3: joint re-scoring of contested records | 2026-09-26 05:30 | adopted (parked, then revived) |
| D-MDL-12 | v6all as the candidate bundle, with a plain threshold | 2026-09-26 14:22 | adopted; superseded by the v7 models |
| D-MDL-13 | No stage-2 tuning: seed bagging, depth 8 and learning rate 0.03 dropped | 2026-09-26 19:49 | rejected |
| D-MDL-14 | France decided from stage 2 instead of stage 3 (`frs2`) | 2026-09-26 21:39 | rejected (planned, built, withdrawn) |
| D-MDL-15 | US/India has converged: v7sq3 is the source, no bagging, keep 3.70 candidates | 2026-09-27 11:38 | adopted; superseded for the finals by D-MDL-16 |
| D-MDL-16 | India, then the US, from Bakshi's g1w | 2026-09-27 18:52 | adopted |

Related records: the features each stage reads are in area FEA; the cross-encoder inputs to stage 2 are in area CE; the decision layer that reads pc is in area DEC; French self-training of stage 2 is D-FRA-13 and D-FRA-16; the final fit on all of train also appears as D-NRM-04; the candidate cut is D-BLK-10 and D-BLK-16; the gate exceptions are D-EVL-03 and D-EVL-04; the uploads built on these models are D-SUB-13 to D-SUB-24; packaging of the chain is D-PKG-01 and D-PKG-08; memory limits are D-ORG-12 and D-ORG-19.

## Records

### D-MDL-01 · XGBoost on the GPU, not LightGBM
- **When (IST):** 2026-09-25 12:13 (speed measured) · 14:15 (FINAL_PLAN §4.5) · 16:41 (first use) · **Phase:** P0–P1 · **Area:** MDL
- **Decided by:** Ameya (Plan A's choice, kept in FINAL_PLAN). Plan B, Sachi's plan, had proposed LightGBM.
- **Status:** adopted. LightGBM was never tested, even as a blend.
- **Problem:** A tabular classifier was needed for 64M training pairs and 37–79 features, trainable in minutes on a laptop GPU, with a licence that fits the rules.
- **Options considered:**
  1. XGBoost 3.2 `hist` with `device=cuda`, and CPU `hist` as the fallback for teammates (Plan A; Apache-2.0).
  2. LightGBM with isotonic calibration (Plan B; MIT): "the right workhorse for short structured strings at this scale".
  3. Neural matchers, later and only as gated extras (area CE).
- **Choice and why:** Option 1. It trained 2M rows × 100 features × 200 rounds in 4.6 s on the laptop GPU, "so full-size training will take minutes, not hours". The blog takeaway that "feature engineering beats the choice of algorithm" made the learner a secondary choice, so LightGBM stayed a blend candidate (gate G10).
- **Evidence:** speed [M] [chat:ameya/19e315ba 2026-09-25 12:13]. Stage-1 v1 had 2,085–2,359 trees at depth 9 and eta 0.06; stage 2 had 923–1,401 trees at depth 7 and eta 0.05 [M]. No source holds a LightGBM run for gate G10.
- **Outcome:** Every model is XGBoost. The final pipeline has four XGBoost stages (0–3).
- **Hindsight:** none recorded.
- **Links:** [FINAL_PLAN §4.5, §9](../../plans/FINAL_PLAN.md) · [Plan A](../../plans/ameya/PLAN.md) · [Plan B](../../plans/sachi/PLAN.md) · [theory: boosting and stacking](../theory/06-gradient-boosting-and-stacking.md)

### D-MDL-02 · The v0 baseline: XGBoost stage 1, argmax ownership, one tuned threshold
- **When (IST):** 2026-09-25 14:15 (scope) · 17:06 (Submission 1 packaged) · **Phase:** P0–P1 · **Area:** MDL / DEC
- **Decided by:** Ameya (proposed and built by: agent for Ameya)
- **Status:** adopted for Submission 1; superseded by model v1 and v2
- **Problem:** A valid first submission was needed before Friday 23:30.
- **Options considered:** not recorded. The scope the plan set was "v0 = normalise v0 + block v0 + about 40 features + XGBoost stage 1 + argmax + a tuned threshold".
- **Choice and why:** That minimal scope. The plan made Friday a v0 baseline and every later step an increment that had to pass a gate. As built:
  - 37 features; XGBoost `hist`, max_depth 8, eta 0.08, subsample and colsample 0.8, min_child_weight 5, 800 rounds (it never stopped early; the log-loss was still falling);
  - trained on folds 5–16 (a 30% sample of S1), early stopping on folds 17–19;
  - each record goes to its argmax S1 (the S1 with the highest score) and one threshold, 0.675, tuned on the holdout decides;
  - the strongest feature was `ret__rank_r`, the S1's rank in the record's list, "because every record has at most one owner".
- **Evidence:** holdout 0.9683 (US 0.9765, India 0.9561, singletons 0.9587); micro precision 0.9898, recall 0.9347 [M]. Packaged as Submission 1 (validator PASS, 105,648 empty rows). Its LB score is not recorded in the sources.
- **Outcome:** Submission 1. Argmax ownership lasted to the end (D-DEC-02).
- **Hindsight:** none recorded.
- **Links:** [handover 2026-09-25_1706](../../docs/handover/2026-09-25_1706_ameya_block-v0-baseline.md) · [baseline features](../../experiments/ameya/baseline/FEATURES.md) · [FINAL_PLAN §0, §8](../../plans/FINAL_PLAN.md) · D-DEC-02

### D-MDL-03 · Stage 2: a collective model over the full candidate graph, isotonic-calibrated, with cluster support
- **When (IST):** 2026-09-25 14:15 (plan) · 17:52 (coded) · 18:31 (v1 measured) · 19:37 (v2) · **Phase:** P0–P1 · **Area:** MDL
- **Decided by:** Ameya (the full-graph rule in the plan); built by agent for Ameya (FINAL_PLAN §4.6, gates G4 and G9)
- **Status:** adopted
- **Problem:** Pair scores ignore the competition around each pair: the record's other S1 and the S1's other candidates. Plan B had trained and scored on a sampled "world" of about 200k entities.
- **Options considered:**
  1. Stage 1 only.
  2. Stage 2 on a sampled world (Plan B).
  3. Stage 2 on the full candidate graph, sampling only the training rows (chosen).
- **Choice and why:** Option 3: competition features need every real rival, so sampling is fine only for training rows.
  - Per record: best and second-best p1, margin, rank, claims above 0.5, sum and share.
  - Per S1: rank, max, sum (the expected cluster size), counts above 0.5, 0.8 and 0.95, neighbour gaps, source balance.
  - Plus p1, its logit and the top-30 stage-1 features, trained OOF over the same groups.
  - Calibration: isotonic regression (a monotone step function that turns scores into probabilities) fitted on the OOF p2 (stage 2's raw score) of training folds only, never on the holdout; the calibrated result is pc.
  - Cluster support (gate G9) joined in v2 (D-FEA-05).
- **Evidence:**
  - v1: p2 0.9798 against p1 0.9781 at the same threshold (+0.0017). v2: 0.9842 against 0.9820 (+0.0022). Stage-2 early-stopping log-loss 0.0507–0.0510 (v2) against 0.0514–0.0528 (v1) [M].
  - Calibration bins within about 0.015; isotonic pc is reliable within about 0.03 per decile in every country × source cell [M] ([ANALYSIS_v2 §2](../../experiments/ameya/model-v1/ANALYSIS_v2.md)).
  - Gate G4 for model v1: +0.00199 [0.00189, 0.00210], a hair under the +0.002 bar; for v2 the stage-2 step adds +0.0022 [M].
  - The dev kits were built on the integration machine over the full graph (65.2M train pairs for v2, 66.8M for v3) and then sliced to the dev sample, because "a dev-only recomputation would differ" [R].
- **Outcome:** Kept in every model. The final pipeline gives stage 2 the cross-encoder scores and the French pseudo-labels, and adds stage 3 (D-MDL-11). A per-stratum calibration (by country, shared-name size, address present and source) was measured and skipped: holdout gaps were at most 0.05, mostly +0.01 to +0.04, the argmax selection effect ([ANALYSIS_v4 §1](../../experiments/ameya/model-v1/ANALYSIS_v4.md); D-PRB-05, D-FRA-06).
- **Hindsight:** Audit finding 6 said the stage-2 cluster features "amplify accepted look-alikes" in France; the later SHAP review found the effect of cluster support on French confidence about zero ([RESEARCH_v6 §2.9](../../experiments/ameya/model-v1/RESEARCH_v6.md)).
- **Links:** [handover 2026-09-25_1958](../../docs/handover/2026-09-25_1958_ameya_model-v1.md) · [FINAL_PLAN §4.6](../../plans/FINAL_PLAN.md) · [ANALYSIS_v3 §7](../../experiments/ameya/model-v1/ANALYSIS_v3.md) · D-MDL-08 · [theory: calibration](../theory/07-calibration.md)

### D-MDL-04 · Owner-removed training examples and the other Saturday extras deferred
- **When (IST):** 2026-09-25 14:15 (planned for Saturday) · **Phase:** P0 · **Area:** MDL / EVL / FRA
- **Decided by:** the schedule (FINAL_PLAN milestones M4–M6), set by Ameya in the final plan
- **Status:** deferred. Owner-removed examples and softmax ownership were never built; leave-one-country-out ran on 26 Sep; the France probes were packaged and never uploaded.
- **Problem:** Plan B's graft: copies of training record groups with the true owner removed and labelled "no owner", to teach stage 2 what a missed owner looks like, "the most dangerous failure (a confident wrong merge)". Also planned for Saturday: softmax ownership with a "none" class (G5), leave-one-country-out (G13), and the France-versus-empty probe (G7).
- **Options considered:**
  1. Build the owner-removed examples into stage 2 now.
  2. Defer them (chosen).
- **Choice and why:** The Friday scope was cut to v0 plus measured increments.
- **Evidence:** FINAL_PLAN §4.6, §8, §9 [R]. No result for G5 or for owner-removed training exists in any source. Sachi's analysis later showed "taken by another S1" is only 0.26% of true pairs, which made the softmax idea low value (D-FEA-08).
- **Outcome:** Owner-removed training and G5 were never built; stage 3 (D-MDL-11) took over the contested-record problem. Leave-one-country-out was run on 26 Sep and became the stand-in for France (areas EVL, FRA). The G7 probes were packaged and never uploaded (D-FRA-12).
- **Hindsight:** The methodology mentions none of these, but the work they stood for moved elsewhere: France was handled by label-free proxy odds, rules, self-training and leaderboard arithmetic.
- **Links:** [FINAL_PLAN §4.6, §9](../../plans/FINAL_PLAN.md) · D-DEC-02 · D-FEA-08

### D-MDL-05 · A stage-0 cascade filter before stage 1
- **When (IST):** 2026-09-25 17:50 (designed) · 18:03 (measured) · **Phase:** P1 · **Area:** MDL
- **Decided by:** agent for Ameya
- **Status:** adopted
- **Problem:** 64M training pairs with 0.116 positive. Training three OOF models on about 32M rows each is slow and memory-heavy.
- **Options considered:**
  1. Sample training rows.
  2. A cheap 200-tree filter trained on 10% of training S1, keeping every pair with p0 ≥ τ0, where τ0 is chosen to keep 99.95% of the positives (chosen).
- **Choice and why:** Option 2. The filter keeps about 17.9% of pairs, so each stage-1 model trains on about 5.7M rows instead of 32M ("about 5× faster"). Test keeps the same share (17.9%), so the filter transfers.
- **Evidence:** τ0 0.00347 (v1) and 0.00345 (v2); kept 0.1785 and 0.1760 of pairs at 0.99950 of the positives; in v3 it kept 15.4% (v2: 17.6%) [M]. The stage-0 bucket cost only +0.00021 (1,071 true pairs) in model v2 [M].
- **Outcome:** The methodology: "Stage 0 removes about 80% of pairs cheaply." It also took the role of the learned pre-ranker the plan had gated (G11).
- **Hindsight:** none recorded.
- **Links:** [`s1.py`](../../experiments/ameya/model-v1/s1.py) · [FINAL_PLAN §9 (G11)](../../plans/FINAL_PLAN.md) · [handover 2026-09-25_1958](../../docs/handover/2026-09-25_1958_ameya_model-v1.md)

### D-MDL-06 · Out-of-fold stage 1 over three S1 groups; holdout and test get the mean of the three models
- **When (IST):** 2026-09-25 17:50 · **Phase:** P1 · **Area:** MDL
- **Decided by:** agent for Ameya. FINAL_PLAN §4.5 had said the holdout and test are "scored by the model trained on all of folds 5–19", so the averaging deviates from the plan.
- **Status:** adopted
- **Problem:** Stage 2 needs honest (out-of-sample) p1 on the training rows.
- **Options considered:**
  1. OOF scores for training rows plus a separate full model for the holdout and test (the plan).
  2. OOF scores, and the average of the three OOF models for the holdout and test (built).
- **Choice and why:** Option 2. Every training pair is scored by a model that never saw its S1, and averaging saves a fourth training run. Early stopping uses a 2% hash slice of S1.
- **Evidence:** stage-1 probabilities "already well calibrated on the holdout (bins within about 0.01)" [M]. The v3 audit checked the protocol: holdout and test both use the mean of the three group models ([ANALYSIS_v3 §7](../../experiments/ameya/model-v1/ANALYSIS_v3.md)).
- **Outcome:** Kept. `--all` later made it a bag of four (D-MDL-10). The methodology: each stage is "trained out-of-fold over three S1 groups, so every stage learns from honest scores of the one before it".
- **Hindsight:** none recorded.
- **Links:** [`s1.py`](../../experiments/ameya/model-v1/s1.py) · [FINAL_PLAN §4.5](../../plans/FINAL_PLAN.md) · [theory: boosting and stacking](../theory/06-gradient-boosting-and-stacking.md)

### D-MDL-07 · Run the model chain from Ameya's experiment folder, not from `ber.model`
- **When (IST):** 2026-09-25 18:21 (decided) · 19:58 (handover) · **Phase:** P1 · **Area:** MDL / ORG
- **Decided by:** agent for Ameya (reported to Ameya). It was not recorded as a decision; the handover notes it as a fact.
- **Status:** adopted for 25 Sep, and in practice to the end. Porting stage 0, stage 2 and the DP into `ber.model` became Sachi's follow-up; no record shows it happening.
- **Problem:** Sachi's merged `ber.model` ([PR #17]) loads the whole C8 feature table into pandas: about 19 GB at 64M × 73, more than the roughly 20 GB usable on the integration machine. Only that machine could run at full scale.
- **Options considered:**
  1. Run `ber.model` at full scale, or port stage 0 and stage 2 into it first (the "integration task").
  2. Keep iterating in `experiments/ameya/model-v1`, with its stage-0 filter and streamed row groups (chosen).
- **Choice and why:** Option 2: memory, and speed on the only machine that fits the data. It was also already measured to be ahead (0.9781 at stage 1).
- **Evidence:** [chat:ameya/19e315ba 2026-09-25 18:21]; the handover's "Known bugs and caveats" [R]. Submissions 2 and 3 came from this folder.
- **Outcome:** The chain stayed there and was later packaged as `src/model_v1` (methodology Appendix A). The experiment pipeline became the product.
- **Hindsight:** Fast, but it concentrated the pipeline knowledge and the artifacts on one machine. Teammates could not reproduce v6 and v7 locally (Bakshi on 26 Sep 15:45 and 27 Sep 01:11).
- **Links:** [handover 2026-09-25_1958](../../docs/handover/2026-09-25_1958_ameya_model-v1.md) · [handover 2026-09-26_1545](../../docs/handover/2026-09-26_1545_bakshi_v7-france.md) · [handover 2026-09-27_0111](../../docs/handover/2026-09-27_0111_bakshi_final-package.md) · [methodology Appendix A](../../experiments/ameya/final-zip/doc/Documentation_template.md) · D-PKG-01

### D-MDL-08 · Gate G4: keep the collective stage 2 (Sachi)
- **When (IST):** 2026-09-25 21:03 · **Phase:** P1 · **Area:** MDL
- **Decided by:** Sachi
- **Status:** adopted
- **Problem:** Does the stage-2 collective model beat stage 1 alone on the same 79 features?
- **Options considered:**
  1. Stage 1 only (`sachi-s1-fx2-dev`, threshold 0.68): 0.97745.
  2. Stage 1 plus stage 2 (`ameya-s2-v2-dev`, threshold 0.67): 0.98438.
- **Choice and why:** Keep stage 2: +0.00692 [+0.00622, +0.00772], p_better 1.000, above the +0.002 bar. Singleton F0.5 rose 0.968 to 0.985 and recall 0.949 to 0.963.
- **Evidence:** [M, dev fold 0, 27,651 S1]. Of v2's gain over v0 (0.9652 to 0.9844), "about two-thirds comes from the 79 features and one-third from stage 2". Ameya's full-scale numbers are smaller: +0.0022 for v2 and +0.0017 for v3 (stage 1 alone 0.9871 against 0.98882 for the full model) [M]. The dev-scale gain is larger probably because the dev-scale stage 1 was weaker (0.97745 against 0.9820 at full scale) [E].
- **Outcome:** Stage 2 stayed in every later model. The remaining loss is mainly recall on records with an empty address.
- **Hindsight:** none recorded.
- **Links:** [decision gate-g4](../../docs/decisions/2026-09-25_2103_gate-g4-stage2.md) · [PR #27] · [error_analysis_v2.py](../../experiments/sachi/error_analysis_v2.py) · D-MDL-03

### D-MDL-09 · Model v3 (full rebuild) as the next upload candidate
- **When (IST):** 2026-09-25 23:28 · **Phase:** P2 · **Area:** MDL / DEC / SUB
- **Decided by:** Ameya (proposed by: agent for Ameya; the captain uploads)
- **Status:** adopted; uploaded (LB 0.97961)
- **Problem:** Three separately gated changes were ready (legal-form features, blocking v2, the (number, street) key fix of [PR #18]) and v2 plus legal features alone (v2lg, 0.98708) existed.
- **Options considered:**
  1. v2lg.
  2. A full rebuild, v3: blocking v2, then features fx3 (str, cx, lo, lg), stages 0–2, and the expected-F0.5 DP.
- **Choice and why:** v3 wins the paired gate by a wide margin. The G6 re-check gave the DP +0.00011 [0.00005, 0.00017] over the best threshold (0.650), so the DP was kept with shift 0 (D-DEC-08).
- **Evidence:**
  - Holdout 0.98882 (US 0.98891, India 0.98868; precision 0.99833, recall 0.96893; singletons 0.99126) against v2's 0.98436: +0.00445 [0.00431, 0.00459] [M]. Stage 0 kept 15.4% of pairs (v2: 17.6%); stage 1 0.9871; stage 2 0.9887.
  - The model's own forecast was 0.99139, 0.0026 optimistic because it cannot see blocking misses. Test forecast: US 0.99141, India 0.99157, France 0.97001 [E].
  - LB: 0.97961, against 0.97608 for v2, so the LB gained +0.0035 against the holdout's +0.0045, and the holdout-to-LB gap grew to −0.0092 [M] ([CHANGELOG](../../CHANGELOG.md), [ANALYSIS_v3](../../experiments/ameya/model-v1/ANALYSIS_v3.md)).
- **Outcome:** The gap was France: 0.97961 = 0.85 × 0.9888 + 0.15 × F_France gives F_France about 0.93 [E]. The decision record had warned "France is the main risk. Its forecast is 0.02 below US/India, which argues for the G7 probe."
- **Hindsight:** The France probe was not run before uploading, so the France problem surfaced a few hours later than it could have.
- **Links:** [decision model-v3-end-to-end](../../docs/decisions/2026-09-25_2328_model-v3-end-to-end.md) · [status ameya](../../docs/status/ameya.md) · [chat:ameya/19e315ba 2026-09-25 23:28] · D-FEA-09 · D-FEA-10

### D-MDL-10 · Final fit on all of train (`--all`): the holdout becomes a fourth OOF group
- **When (IST):** 2026-09-26 03:37 (coded) · 04:17 (decision record) · **Phase:** P2 · **Area:** MDL
- **Decided by:** agent for Ameya, from item 2 of Ameya's 02:17 list ("train the final model on all training data"); Ameya accepted it in the decision record
- **Status:** adopted (v5all, v6all and every later model)
- **Problem:** The stage models trained on only 50% of train (two of three groups) while 25% sat in the holdout.
- **Options considered:**
  1. Refit on 100% with no holdout. The threshold would then have to come from earlier runs.
  2. A fourth OOF group: every model sees 75% of train, every train pair keeps an honest OOF score, and test gets the mean of four models (chosen).
- **Choice and why:** Option 2. The decision layer and the gates still have honest holdout scores.
- **Evidence:** v5 to v5all: stage 1 0.98693 to 0.98695; the DP 0.99013 to 0.99016, +0.00002 [−0.00003, +0.00007] [M]. The tie is expected: "the holdout compares one 75% model with a bag of three 50% models and cannot see the test-time bag of four". Stage-2 early-stopping log-loss 0.0386–0.0388 to 0.0379–0.0387; stage-1 peak memory 18.4 GB [M]. The `--all` isotonic fit also sees the holdout's own OOF p2, "negligible" [R].
- **Outcome:** Every later model used it. One source dates this to about 04:30; the chat shows the code at 03:37 and the decision record is dated 04:17.
- **Hindsight:** Its value is invisible on the holdout by construction and stays unmeasured except through the LB. It was adopted on reasoning, not on a measured gain; by the tie rule it would have lost.
- **Links:** [decision france-generator-ops-and-final-fit](../../docs/decisions/2026-09-26_0417_france-generator-ops-and-final-fit.md) · [ANALYSIS_v4 §7](../../experiments/ameya/model-v1/ANALYSIS_v4.md) · [commit 5f2abaa] · [chat:ameya/19e315ba 2026-09-26 03:37] · D-NRM-04

### D-MDL-11 · Stage 3: joint re-scoring of contested records
- **When (IST):** 2026-09-26 05:30 (design) · 06:27 (built, parked as optional) · 11:24 (measured again, still optional) · 15:38–15:44 (run on v6all, adopted) · **Phase:** P2–P3 · **Area:** MDL
- **Decided by:** Ameya (proposed by: structure agent a9638892; built by agent a2066847; run on v6all by agent for Ameya)
- **Status:** adopted (parked at 06:27 as optional; adopted at 15:44 after it gained on v6all)
- **Problem:** Most US/India loss is records "lost to another S1" or "rejected". Stage 2 cannot see the state of the rival S1 of a contested record. Could decoding all S1 jointly fix it?
- **Options considered:**
  1. A: a small XGBoost on contested records (two or more candidate S1 at pc ≥ 0.01) using the pair's pc, the S1's confident copies per source (this record excluded), the best rival's pc and counts, the candidate count, the empty-address flag and the source.
  2. B: an isotonic map from a record's total pc to "its owner is a candidate", scaling up only, for empty-address records.
  3. Other ideas: a count prior (the hazard P(T = n+1)/P(T = n)), a source-balance prior, hard caps (5 S2, 6 S3), a single-owner rule.
  4. Skip the stage.
- **Choice and why:** A and B only, trained OOF with the stage-2 groups, with no country features. Stage 2's per-S1 features already capture the count prior; the one thing they cannot see is the rival S1's state. The caps bind for only 4 holdout S1. It was parked at 06:27 and 11:24 as "+0.00004 LB for one more stage", and because the prototype was the best of three variants picked on the same holdout (optimistic). It was revived at 15:38 when a French example ("WLK SAS & Associés", stage-2 pc 0.954 falling to 0.525) looked like what stage 3 should fix. It is cheap (72 s, peak 1.7 GB), and the gate decides.
- **Evidence:**
  - Prototype: A +0.00006 [+0.00002, +0.00009]; B +0.00007 [+0.00004, +0.00009]; A and B +0.00011 [+0.00007, +0.00015] (India +0.00006, US +0.00014); A with the true copy counts (an oracle) +0.00008 [M].
  - As a pipeline step with the candidate cut, on v5all: +0.000051 [+0.000023, +0.000079] (A only +0.000042), holdout 0.990207 against 0.990156 [M].
  - On v6all: 0.990788 to 0.990842, +0.000055 [+0.000025, +0.000085], p_better 1.0, positive in both countries (US +0.000052, India +0.000059) [M].
- **Outcome:** In every package from `v6all-s3` on. The methodology credits "blocking repairs together with stage 3" with +0.0008 on the LB (v5all 0.98781 to 0.988609 [LB 2026-09-26 #02](../../submissions/records/2026-09-26_sub02.md)). Concerns that came later: it lowers the French rule-population AUC (a label-free French check) by about 0.005 and moves three times as many French decisions (D-MDL-14); it is not bit-reproducible across machines (232k test pc differ, about 500 decisions) [M] ([RESEARCH_v6 §6.18](../../experiments/ameya/model-v1/RESEARCH_v6.md)).
- **Hindsight:** The module agent warned that the prototype's +0.00011 was the best of three variants picked on the same holdout; the real gain was half. The caps came back later through the hunt agent as a rule at about +0.4e-6 [R] (D-DEC-15). Stage 3 was gated on US/India only.
- **Links:** [decision rules-v3-and-stage3](../../docs/decisions/2026-09-26_1557_rules-v3-and-stage3.md) · [RESEARCH_v5 §8.4](../../experiments/ameya/model-v1/RESEARCH_v5.md) · [`stage3.py`](../../experiments/ameya/model-v1/stage3.py) · [PR #28] · [chat:ameya/agent-a9638892 2026-09-26 05:30] · [chat:ameya/19e315ba 2026-09-26 15:44]

### D-MDL-12 · v6all as the candidate bundle, with a plain threshold
- **When (IST):** 2026-09-26 14:22–14:25 · **Phase:** P3 · **Area:** MDL / DEC
- **Decided by:** Ameya (proposed by: agent for Ameya, who accepted it on the gate; the captain uploads)
- **Status:** adopted as the final candidate on 26 Sep afternoon; superseded by the v7 models
- **Problem:** Bundle the round-1 solutions into one rebuilt candidate: blocking v3, signed numbers (`nx`), a new cross-encoder, `--all`, the candidate cut, rules v2.
- **Options considered:**
  1. Keep `v5all-ops2-c2` (0.990156).
  2. v6all, rebuilt end to end in about 3 h, decided by the DP or by a threshold.
- **Choice and why:** v6all. The gate for the decision rule (G6) picked a plain threshold, 0.70: the DP's gain was +0.00004 [−0.00001, +0.00008], which includes zero, and ties go to the threshold. After stage 3 the threshold moved to 0.675 and the DP was again a tie (D-DEC-08).
- **Evidence:** holdout 0.990788 (US 0.99065, India 0.99100) against 0.990156: +0.00063 [+0.00057, +0.00070], p_better 1.0 (US +0.00068, India +0.00056); recall 0.9713 to 0.9738, precision 0.9988 to 0.9987; blocking pair recall 0.98992 to 0.99135; cross-encoder OOF band AUC 0.919; final predictions per test S1: US 3.390, India 3.376, France 3.360 [M]. Expected LB gain +0.0005 (0.85 × 0.00063) [E].
- **Outcome:** With stage 3, rules v3 and the acronym join, v6all scored 0.988609 on the LB (+0.0008 over v5all's 0.98781; France implied about 0.973) [M] ([LB 2026-09-26 #02](../../submissions/records/2026-09-26_sub02.md)).
- **Hindsight:** The final methodology uses the DP again (+0.000048 on a later model), so the G6 verdict depended on the model (D-DEC-08, D-DEC-15).
- **Links:** [decision model-v6all-final](../../docs/decisions/2026-09-26_1425_model-v6all-final.md) · [handover 2026-09-26_1428](../../docs/handover/2026-09-26_1428_ameya_model-v6all-final.md) · [chat:ameya/19e315ba 2026-09-26 14:25] · D-FEA-13

### D-MDL-13 · No stage-2 tuning: seed bagging, depth 8 and learning rate 0.03 dropped
- **When (IST):** 2026-09-26 19:49–20:57 · **Phase:** P3 · **Area:** MDL
- **Decided by:** agent for Ameya (Ameya had asked to "milk anything from anywhere")
- **Status:** rejected
- **Problem:** Squeeze more out of stage 2.
- **Options considered:** seed bagging (retrain with seed 1 and average pc); `max_depth` 8; learning rate 0.03. Each was gated on the holdout.
- **Choice and why:** Stop all three. Bagging lost; the others showed no better early-stopping loss.
- **Evidence:** bagging, v7ce3 plus a seed-1 retrain with pc averaged: 0.991099 to 0.991061 (−0.00004) [M]. Depth 8: early-stopping log-loss per group 0.03686, 0.03651, 0.03625, 0.03684 against 0.03684, 0.03665, 0.03622, 0.03681, no gain, not scored [M]. Learning rate 0.03: group-0 log-loss 0.03688, stopped [M] ([RESEARCH_v6 §6.1](../../experiments/ameya/model-v1/RESEARCH_v6.md)).
- **Outcome:** No stage-2 parameter changes. The remaining effort went to cross-encoders and France. On 27 Sep Bakshi's weight variants of the 7B in the mix (×3, 7B alone) were also negative against g1w (D-CE-23).
- **Hindsight:** none recorded.
- **Links:** [handover 2026-09-26_2049](../../docs/handover/2026-09-26_2049_ameya_squeeze-v7n.md) · [handover 2026-09-27_2006](../../docs/handover/2026-09-27_2006_bakshi_final-push.md) · [handover 2026-09-27_2014](../../docs/handover/2026-09-27_2014_ameya_final-upload.md)

### D-MDL-14 · France decided from stage 2 instead of stage 3 (`frs2`)
- **When (IST):** 2026-09-26 21:39 (a no-stage-3 fallback planned) · 2026-09-27 01:03–01:13 (built) · 02:10 (withdrawn) · 02:15 (queued builds disabled) · **Phase:** P3 · **Area:** MDL / DEC / FRA
- **Decided by:** Ameya (the withdrawal; the 02:10 analysis was by agent for Ameya). Proposed by: agent for Ameya (the 21:39 fallback and the build) and Bakshi (who put the `frs2` variants ahead of a threshold probe, then retracted his recommendation on [issue #45], "agreeing that the rule-AUC drop was circularity").
- **Status:** rejected (withdrawn)
- **Problem:** Stage 3 was gated on US/India. In France it lowered the label-free rule-population AUC (the AUC of pc on French pairs whose truth is known from US/India rules): v7nst 0.9844 to 0.9791, v7nst2 0.9857 to 0.9792, and v7c 0.874 to 0.869 before self-training. It also moved three times as many French decisions: crossings at 0.675 +2.5 and −6.5 per 1000 French S1 against about 1 each way in US/India, and pc changes above 0.05 on 330 against about 100 per 1000 S1 [E]; stage 2 to stage 3 added 12.6 and dropped 3.5 French pairs per 1000 S1.
- **Options considered:**
  1. `frs2`: take the stage-2 decision for countries without labels and stage 3 elsewhere. It is cheap (about 5 minutes, no retraining), changes France only, leans to precision, "the direction that has paid".
  2. Keep stage 3 everywhere.
- **Choice and why:** The `frs2` variants were built (the 02:01 memo called it "a clean France-only bet"), then withdrawn:
  - A hand reading of 50 French pairs where stages 2 and 3 disagree found the drops and adds roughly balanced (60–65% true copies either way).
  - 35.4% of the 3,029 French pairs it drops have an empty record address, against a 2.7% base rate. It would discard about 1,070 likely-true copies. Stage 3's part B (record-mass calibration of empty-address records, which are true copies 97.7% of the time in US/India) is exactly what lifts these pairs.
  - The AUC drop was circular: stage 2 had trained on pseudo-labels that include the rule populations, and stage 3 had not.
  - On the label-free copy check (`fhs.py`) `frs2` lost 3.86 net true copies per 1000 French S1, the worst measured.
- **Evidence:** counts [M]; proxy AUCs [E]; copy check [M, proxy] ([RESEARCH_v6 §6.12, §6.14](../../experiments/ameya/model-v1/RESEARCH_v6.md)) [chat:ameya/19e315ba 2026-09-26 21:39] [chat:ameya/19e315ba 2026-09-27 02:09] [chat:ameya/19e315ba 2026-09-27 02:10].
- **Outcome:** `make_frs2.sh` became a no-op (the original kept as `make_frs2.orig.sh`) and the `frs2` step was removed from `final_night4.sh`. Stage 3 stayed everywhere.
- **Hindsight:** Right. The lasting lesson: after self-training, a label-free French AUC is circular and cannot judge a stage that did not see the pseudo-labels. Bakshi: "I'd flagged that circularity risk for self-trained model ranking and then walked straight into it for a stage comparison."
- **Links:** [PR #55] · [issue #45] · [fhs.py](../../experiments/ameya/model-v1/fhs.py) · D-MDL-11 · D-FRA-16 · D-EVL-12

### D-MDL-15 · US/India has converged: v7sq3 is the source, no bagging, keep 3.70 candidates
- **When (IST):** 2026-09-27 11:38 and 11:49 (chosen) · 14:58 and 15:03 (confirmed) · **Phase:** P4 · **Area:** MDL / BLK
- **Decided by:** agent for Ameya (proposed by: the decide agent's ranking, with a squeeze sub-agent); Ameya uploaded the composites that use it
- **Status:** adopted for every composite up to mixmdp; superseded by D-MDL-16 for the finals
- **Problem:** Choose which model's US/India decisions go into every final, and whether bagging (averaging several models) adds anything.
- **Options considered** (holdout F0.5 under the combo rule, the stacked decision layer of D-DEC-15):

  | model | combo holdout |
  |---|---|
  | v7sq | 0.991280 |
  | v7sq3 (v7sq plus a second seed of the French self-trained e5-large) | 0.991307 |
  | bag4 (v7sq3, v7qbag, v7sq2, v7sq4) | 0.991312 |
  | v7xbag | 0.991297 |
  | v7sq6wg | 0.991306 (best India, 0.991622) |

- **Choice and why:** v7sq3. It was the only model to beat v7sq with an interval above zero: +27.3e-6 [+2.2, +52.6]. bag4 against v7sq3 was +4.6e-6 [−10.6, +21.1] (P 0.714), and its halves disagreed (A −8.6, B +24.4): a tie, so the simpler option. v7sq6wg's memo figure of 0.991320 did not reproduce; under the combo rule it is 0.991306, a tie. US/India bagging "had already hit its ceiling". For France, bags "only damped the French changes": v7xbag (the stage-2 mean of v7sqsd, v7sq3, v7sq4, v7sq6 and v7sqwg) scored +0.000021 on the calibrated French estimator (+0.000039 with the DP) against +0.000166 for v7sq6wg, so it was kept only as a variant. The candidate file stayed at 3.70 pairs per S1 because every tighter cut lost holdout F0.5 (the record's top 1 only −106e-6; p1 ≥ 0.05 −41e-6) [M].
- **Evidence:**
  - The table above [M] ([RESEARCH_v6 §6.18](../../experiments/ameya/model-v1/RESEARCH_v6.md)). The squeeze agent's India-only count prior was declined (D-DEC-19).
  - Candidate recall: about 99.1% of true holdout pairs at retrieval (about 34 candidates per S1), and about 98.2–98.4% in the 3.70-per-S1 file (0.98198 for v5all when the cut was made) [M] ([decision candidate-set-cut](../../docs/decisions/2026-09-26_0532_candidate-set-cut.md)). A stage-2 pc gate at 2e-4 would cut another 2.8% at no loss but needs a pipeline rebuild. Stage 3 is not bit-reproducible across machines.
- **Outcome:** Every composite up to mixmdp uses v7sq3 for US/India; expected LB effect +0.00002 over v7sq's US/India [E]. mixmdp scored 0.990699 on the LB [LB 2026-09-27 #03](../../submissions/records/2026-09-27_sub03.md).
- **Hindsight:** Composite B took US/India from Bakshi's g1w, which beat v7sq3 on India by +66.1e-6 (P 0.998) (D-MDL-16).
- **Links:** [RESEARCH_v6 §6.18](../../experiments/ameya/model-v1/RESEARCH_v6.md) · [chat:ameya/19e315ba 2026-09-27 14:58] · [chat:ameya/19e315ba 2026-09-27 15:03] · D-BLK-16 · D-DEC-19 · D-SUB-18

### D-MDL-16 · India, then the US, from Bakshi's g1w
- **When (IST):** 2026-09-27 18:52 (India) · 20:53 (US, by uploading Composite B) · **Phase:** P4 · **Area:** MDL
- **Decided by:** agent for Ameya for India (proposed by: the France-diff agent's side finding and significance check; Ameya accepted it); the team for the US, when Ameya uploaded Composite B
- **Status:** adopted
- **Problem:** g1w, Bakshi's rebuild with the 7B counted twice in the stage-2 cross-encoder mix (D-CE-23), looked better than our v7sq3 on the India holdout.
- **Options considered:**
  1. Keep v7sq3 for both countries.
  2. g1w for India only.
  3. g1w for both.
  4. A hybrid: only the positive half of g1w's changes, or g1w plus gbag's extra additions.
- **Choice and why:** India from g1w at 18:52: +66.1e-6 on the holdout with P 0.998 [M], about +31e-6 on the LB [E]. Bakshi's own g1w India file matched our decision code within about 25 pairs. The US stayed on v7sq3 in the plan (mixf2) because its gain, +26e-6 at P 0.906, was not significant after a multiple-testing correction. Composite B, uploaded first (about 20:55), took the US from g1w too; the next two uploads, mixf7 and mixf2, then isolated g1w's US gain on the LB.
- **Evidence:**
  - Hybrid tests: g1w's India gain comes mostly from its drops (+0.000055 of +0.000066); the best US near-miss, g1w plus gbag's additions, was +0.000009 at P 0.77; g1w and v7sq3 never disagree on which S1 owns a record [M] [chat:ameya/19e315ba 2026-09-27 21:09]. g1x3 was slightly worse than g1w for India and g7only clearly worse [chat:ameya/19e315ba 2026-09-27 19:43].
  - The LB measured g1w's US at +0.000014 over ours (mixf2 0.990819 against mixf7 0.990833), where the holdout implied about +10e-6 [M] ([LB 2026-09-27 #06](../../submissions/records/2026-09-27_sub06.md)).
- **Outcome:** Composite B (g1w US/India plus mixmdp's France, minus the 7B rejects) scored 0.990879 on the LB [M] ([LB 2026-09-27 #04](../../submissions/records/2026-09-27_sub04.md)).
- **Hindsight:** Right for both countries; the holdout under-sold the US gain.
- **Links:** [FINAL_PUSH_RESULTS §2](../../experiments/bakshi/box/FINAL_PUSH_RESULTS.md) · [issue #64] · [RESEARCH_v6 §6.19, §6.20](../../experiments/ameya/model-v1/RESEARCH_v6.md) · D-CE-23 · D-MDL-15 · D-LLM-09 · D-SUB-21 · D-SUB-24
