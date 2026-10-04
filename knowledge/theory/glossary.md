# Glossary

**Summary.** Every term used in our methodology document and in this study guide, one or two lines each, in alphabetical order, including our internal names (S1, p1, band, g1w, v7sq, mixmdp, Composite B and the rest).
Numbers carry their scope; the pages in [`theory/`](README.md) hold the detail, and the [methodology](../../experiments/ameya/final-zip/doc/Documentation_template.md) holds the submitted figures.

Jump to: [A](#a) · [B](#b) · [C](#c) · [D](#d) · [E](#e) · [F](#f) · [G](#g) · [H](#h) · [I](#i) · [J](#j) · [L](#l) · [M](#m) · [N](#n) · [O](#o) · [P](#p) · [Q](#q) · [R](#r) · [S](#s) · [T](#t) · [U](#u) · [V](#v) · [W](#w) · [Z](#z)

---

## A

- **A, APP, ACR**: generator operations that make true copies at the S1's own address: a list word swapped in after the legal form (A, also op-A), a list word appended (APP), the name cut to its initials (ACR). 97–99.8% true on the US/India holdout; the French rules add them.
- **Acronym join** (`acr_join.py`): pairs a record whose name is an S1's initials with that S1, on (country, house number, initials), confirmed by the robust address test. It added 3,872 French pairs on v6all.
- **Active learning**: choosing which examples a human should label next, usually where models are unsure or disagree. Our proposal for new countries in production.
- **AdamW**: the Adam optimiser with decoupled weight decay; used for every cross-encoder.
- **Adapter**: the small set of trained LoRA weights, saved apart from the frozen base model. Our 7B adapters are 161.5 MB each.
- **Adversarial validation**: train a classifier to tell training rows from test rows; a high AUC reveals a shift. Ours (AUC 0.95) exposed unseen words encoded as −1.94e-16 on train and 0.0 on test.
- **Ambiguity decomposition** (Krogh–Vedelsby): for an averaged ensemble under squared error, ensemble error = average member error − average disagreement. Why diverse members help.
- **ANN (approximate nearest neighbour)**: fast search for close vectors that may miss a few true neighbours (HNSW, IVF-PQ, ScaNN). Not used; proposed as an embedding view at scale.
- **Argmax ownership**: each record stays only under its highest-scoring S1, because a record has at most one owner.
- **Attention**: $\mathrm{softmax}(QK^\top/\sqrt{d})V$, the way a transformer lets each token mix in information from the others.
- **AUC (area under the ROC curve)**: the probability that a random true pair scores above a random false pair. Band AUC compared our cross-encoders.
- **`audit_matching.py`**: our strict output audit: one row per S1, no record with two owners, no cross-country pair, every match inside the candidate file.

## B

- **B7**: our last upload: Composite B with the French 7B drops extended toward logit −2 where Qwen3-4B agreed. Public LB 0.990875, a tie with Composite B.
- **Bagging**: averaging models trained on resampled data or different seeds. Seed-bagging stage 2 lost 0.00004 on the holdout.
- **Band (uncertain band)**: pairs with 0.02 ≤ p1 ≤ 0.99; 1,568,554 train and 1,490,930 test pairs. The only pairs the cross-encoders score.
- **BBSE, label-shift EM**: methods that estimate the target domain's class balance and correct the logits for it.
- **Beta calibration**: a three-parameter calibration family that contains the identity map.
- **bf16 (bfloat16)**: a 16-bit float with float32's range; used to train the transformers.
- **bge, bges**: bge-reranker-v2-m3 (568M parameters, Apache-2.0), a multilingual cross-encoder reranker, fine-tuned on our band (bge) or also on French pseudo-labels (bges).
- **Bi-encoder**: encodes each record separately into a vector; fast and reusable, but cannot align tokens across the pair.
- **Block purging**: ignoring oversized blocks or posting lists. Our seed cap does this.
- **Blocking**: generating candidate pairs cheaply, so the matcher never sees all pairs ([page 02](02-blocking.md)).
- **Blocking views**: separate searches whose candidates are merged: the token view (`tok`) and the names-only view (`name_short`), after the repairs.
- **Box**: a rented GPU machine (H100s) for the cross-encoders and the 7B.
- **Break-even probability**: the probability above which adding a pair raises expected F0.5: about 0.75 for an S1 holding 3 of 4 copies. A drop pays when a pair is more than about 20–25% likely to be false.
- **Brier score**: the mean squared error of probabilities; a proper scoring rule.

## C

- **c2 (the candidate cut)**: the candidate file's rule: p0 ≥ τ0, p1 ≥ 0.02 and the pair among its record's top 2 S1 by p1; acronym-join pairs are added to it. 3.70 pairs per test S1.
- **cal**: our estimator for a French change: the new model's pc, calibrated on the US/India holdout, applied to the French pairs that changed. It tracked the leaderboard best (correlation 0.98) but was biased on decoys.
- **Calibration**: probabilities that match frequencies ([page 07](07-calibration.md)).
- **Candidate file** (`candidate_pairs.tsv`): the pairs our matcher scores at inference; 6,410,308 pairs; part of the submission and the basis of the candidate-efficiency ranking.
- **Candidates per S1 (pairs per entity)**: 3.70 in our file, against 3.46 true matches per S1 and 3.38 predictions.
- **Cascade**: a chain of increasingly expensive models, each run only on what the previous one did not settle.
- **CatBoost, LightGBM**: other gradient-boosting libraries; not tried.
- **CE**: cross-encoder.
- **CE mean groups** (`cem2`, `cem`, `cms`, `cmq`, `zg1w`): stage-2 features holding the z-scored mean of several cross-encoders: e5l + e5l2 (cem2); plus bge (cem); e5l + e5ls + bge (cms); e5l + qst + e5ls + bge (cmq); cmq plus q7st twice (zg1w).
- **Character n-grams**: overlapping letter sequences; the names-only view matches names on 4-grams.
- **Cluster support**: stage-2 features: how similar a record is to the S1's confident records.
- **Co-training**: two models with different views of the data label examples for each other.
- **Collective (context) features**: features computed from competing pairs' scores: rank, margin to the best rival, how many confident copies the S1 already has.
- **Composite B**: our best submission: US/India from g1w, France from mixmdp, minus the confident predictions the 7B rejects (logit < −6, 1,150 pairs). Public LB 0.990879; 5,851,832 pairs.
- **Compound key**: a blocking key made of two tokens, such as (house number, street word) or (name token, address word); it stays rare where single tokens are common.
- **Concept shift**: P(y | x) changes between domains.
- **Confidence interval**: here, the 2.5–97.5% range of paired-bootstrap differences; a gate needs it above zero.
- **Confirmation bias**: in self-training, a model learning its own mistakes as truth.
- **Consonant skeleton**: a token with its vowels removed (marketing → mrktng), so transliterations still match.
- **Containment**: the share of one side's tokens found in the other side.
- **Contested record**: a record with two or more candidate S1 at pc ≥ 0.01; stage 3 re-scores them.
- **copy and city rules (polish)**: French-only rules: add same-name copies at the exact address (a population 99.99% true in US/India); drop pairs whose S1 and record name different communes.
- **COPY population**: French pairs with the same content words up to typos and the same or an empty address. True copies by US/India rates, and no rule decides them, so they stayed a usable label-free check (`fhs.py`).
- **Covariate shift**: P(x) changes between domains while P(y | x) does not.
- **Cross-encoder**: a transformer that reads both records together and outputs one logit for the pair ([page 08](08-transformers-and-cross-encoders.md)).
- **Cross-fitting**: training on some groups and scoring only the held-out group. Our French pseudo-labels are cross-fitted by S1 group, so no French pair is scored by a model that saw its label.
- **Crowd shift**: −0.3 added to the logit before the decision, for records with 4 or more candidate S1 at p1 ≥ 0.02.

## D

- **DANN (domain-adversarial training)**: an encoder trained so that a domain classifier cannot tell source from target (gradient reversal). Proposed for the cross-encoders.
- **Decision layer**: everything after scoring: argmax ownership, the expected-F0.5 selection per S1, then the rules and the 7B drops.
- **Decoder model**: a transformer with a causal mask, where each token sees only earlier ones (Qwen). As a classifier, it reads the last token.
- **Decoy (look-alike)**: a record that resembles an S1 but is a different business: a swapped business word, a nudged house number, or the same name elsewhere.
- **Dev sample, dev kit**: a quarter of the S1 in folds 0, 5, 10 and 15 (about 110k S1) with precomputed features, for teammates' smaller machines; its fold-0 part (27,651 S1) is the dev holdout.
- **Distillation**: training a small model to reproduce a large model's scores. Our production path for the cross-encoders and the 7B.
- **Diversity (ensemble)**: members that make different errors; it is what makes an average beat its best member.
- **Domain shift**: test data distributed differently from training data ([page 09](09-self-training-and-domain-shift.md)).
- **Double machine learning**: estimation that fits nuisance models on one fold and uses them on another; the origin of the term cross-fitting.
- **DP (expected-F0.5 dynamic programme)**: computes, for each S1, the expected F0.5 of every top-k set of its owned candidates (a Poisson-binomial calculation) and keeps the best.
- **`dp_france` (France DP)**: the expected-F0.5 decision applied to France's stage-3 pc, where look-alike swaps are never added.
- **-dpc (suffix)**: the stacked decision layer built by `stack/stack.sh`: the DP with the logit shift, phantom and crowd shift plus the acr and cap rules for US/India; the polish rules for France.

## E

- **e5 (multilingual-e5-small, -base, -large)**: multilingual encoders (118M, 278M, 560M parameters; MIT) pre-trained contrastively, used as cross-encoders. Our runs: e5-small (the `ce` feature), e5b (base), e5l (large, one epoch), e5l2 (two epochs), e5ls and e5ls2 (French self-trained, two seeds), e5fr (France-heavy, band AUC about 0.918).
- **Early stopping**: stop adding trees when the validation loss has not improved for a set number of rounds (60 for us).
- **ECE (expected calibration error)**: the average gap between mean score and true rate over bins, weighted by bin size.
- **eid**: our integer record id: source × 1,000,000,000 + number.
- **Empty-address record**: a record with no address. 4.41% of true copies have none, such a record is a true copy 97.7% of the time, and these records are the bulk of our misses.
- **Encoder model**: a transformer in which every token sees every other token (BERT, XLM-R, e5, bge).
- **Entity resolution**: deciding which records describe the same real-world entity; here, which S2/S3 records copy each S1 business ([page 01](01-entity-resolution.md)).
- **Error independence**: two models whose mistakes are unrelated; the more independent, the more a second opinion catches.
- **Expected F0.5**: the average F0.5 an S1 would get over the uncertainty in its candidates; the quantity our decision maximises.

## F

- **F-unit**: one S1's worth of F0.5, a change of 1 in the sum of per-S1 scores; about 5.8e-7 of the leaderboard score (1 / 1,732,544 test S1).
- **F0.5 (macro)**: per S1, 1.25·hits / (0.25·|true| + |predicted|), averaged over all S1. A singleton scores 1 only for an empty prediction. Precision counts about twice as much as recall ([page 04](04-metrics-and-decisions.md)).
- **`fhs.py`**: our label-free French check: the net change in COPY and SWAP pairs per 1000 French S1 against a reference model.
- **Fold, `fold_of`**: fold = splitmix64(eid) mod 20. Folds 0–4 are the holdout; folds 5–19 are training folds.
- **fr-<model>**: a France-only package: US/India byte-identical to a reference, France from another model, so the score change is French alone.
- **fr0, fr090, fr090r, frlo**: France probes: France emptied (fr0, packaged but never uploaded); French predictions below pc 0.9 dropped after (fr090) or before (fr090r) the rules; extra French pairs added (frlo).
- **France implied level**: (public LB − US/India part) / 0.14975. An estimate: it assumes US/India score on test as on the holdout, and that the public subset has the whole test's country mix.
- **frs2**: a withdrawn variant that took France's decision from stage 2 instead of stage 3.

## G

- **g0, g1, g1w, g1x3, g7only, gbag**: Bakshi's stage-2 mix ablation on his rebuild: g0 is v7sq's mix (local holdout 0.991261); g1 adds q7st once; **g1w** twice (0.991323, our final US/India model); g1x3 three times; g7only uses q7st alone; gbag bags stage-2 scores.
- **Gain**: the loss reduction from a split, in XGBoost's second-order form; gain importance sums it per feature.
- **Garble**: a word replaced by a typo of itself (Indel similarity ≥ 0.5 to the original); 95–99% of such pairs are true copies.
- **Gate (G1–G13)**: a pre-registered test a component had to pass before joining the pipeline, usually a paired bootstrap on the holdout; ties go to the simpler option. Examples: G4 stage 2, G6 DP against threshold, G10 cross-encoder, G13 leave-one-country-out.
- **GBDT**: gradient-boosted decision trees ([page 06](06-gradient-boosting-and-stacking.md)).
- **Generator**: the organisers' process that made the data. We reverse-engineered its operations: copy counts (3.46 per S1, caps of 5 S2 and 6 S3), dropped addresses, operations A, APP, ACR and op-B.
- **GPU-hour**: one GPU busy for one hour; our unit of transformer cost.
- **Gradient, hessian (g, h)**: first and second derivatives of the loss with respect to the model's output; for log-loss, g = p − y and h = p(1 − p).
- **Guard**: a pseudo-label protection: empty-address records keep their round-1 labels, and rule populations override the teacher.

## H

- **H100**: NVIDIA's 80 GB data-centre GPU, rented for the cross-encoders and the 7B.
- **Halves A and B**: two fixed halves of the holdout (by fold parity; for the 7B sample, by s1 // 7 mod 2). A setting chosen on one half had to hold on the other.
- **Histogram method**: XGBoost's split search on pre-binned features (256 bins).
- **HNSW**: a graph-based ANN index.
- **Holdout (local holdout)**: the fixed 25% of labelled US/India S1 (folds 0–4, 549,699 S1) behind every local comparison. It has no France.
- **House-number nudge**: a house number moved by a small amount (1–10); look-alikes do this, true copies seldom do.
- **Hunt rules (acr, cap, nsa)**: rules found by an analysis agent: add an owned, unheld pair whose record name is the S1's initials (acr); at most 5 S2, 6 S3 and 11 records per S1 (cap); drop weak predictions on records with 4 or more competing S1 (nsa, later replaced by the crowd shift).

## I

- **IDF (inverse document frequency)**: the log-scaled rarity of a token; rare tokens weigh more. Fitted per country.
- **Importance weighting**: re-weighting source rows by $P_T(x)/P_S(x)$ to correct a covariate shift. We re-weighted the holdout to the test's name-group sizes.
- **Incremental ER**: updating matches as records arrive, without recomputing everything.
- **Indel similarity**: a normalised insertion/deletion edit similarity (rapidfuzz); defines a garble.
- **Indic dictionary**: 693 Indic-to-Latin token mappings learned from training pairs (for example kanstrakshan → construction).
- **InfoNCE**: the contrastive loss used to pre-train e5.
- **Isotonic regression**: the best non-decreasing fit of labels to scores; our calibrator, solved by PAV.

## J

- **Jaccard similarity**: |A ∩ B| / |A ∪ B|; we use an IDF-weighted version on name tokens and address words.
- **Jaro-Winkler**: a character similarity that rewards matching prefixes; one of our name features ([page 03](03-string-similarity.md)).

## L

- **Label (prior) shift**: P(y) changes between domains while P(x | y) does not.
- **Label odds, proxy odds (`lo`, `lop`, `lo0`)**: per-word log-odds of a true match when the word is extra or missing. `lo` comes from US/India labels (out of fold); `lop` is the label-free proxy from a word's moved-house-number share; `lo0` mixes them (labels where they exist, the proxy for France, unseen words exactly 0).
- **LB (public and private leaderboard)**: public, the score on a subset of test during the challenge; private, the final ranking on the rest. Our best public score: 0.990879.
- **Learned cut**: see c2. Stage 0 and stage 1 prune the retrieved pairs to the candidate file, a supervised form of meta-blocking.
- **Learning to defer**: learning when to hand a case to a stronger decider.
- **Legal features (`lg`, `leg__*`)**: whether the legal forms of the two names agree, were dropped, added or changed.
- **Legal form**: SARL, SAS, LLC, Pvt Ltd and the like. True copies keep, reformat or drop them; look-alikes change or add them.
- **List words**: the generator's words appended to true copies (English: center, services, partners; French: fils, cie, services, associés, groupe, développement, france).
- **LLM**: large language model; ours are decoder models (Qwen2.5) fine-tuned as pair classifiers.
- **LOCO (leave-one-country-out)**: train on one country and test on another; India stood in for France.
- **Logit, logit shift**: the log-odds log(p / (1 − p)); adding b multiplies the odds by $e^b$. We add +0.2 before the decision.
- **Look-alike**: see decoy.
- **LoRA**: low-rank adaptation: freeze the model and learn ΔW = BA of rank r. Ours: r 16, alpha 32, on all attention and MLP projections.

## M

- **Macro F0.5**: see F0.5.
- **MapReduce, Spark**: frameworks that split work into map and reduce steps across many machines.
- **Margin**: a pair's score minus the best score of any other S1 for the same record.
- **Meta-blocking**: pruning the graph of candidate pairs by edge weights; our learned cut is a supervised version.
- **min_child_weight**: XGBoost's floor on the hessian sum in a leaf.
- **MinHash, LSH**: hashing schemes under which similar sets collide in the same bucket.
- **mixf2, mixf7**: uploads with round-3 French labels (v7sq6r3): 0.990819 and 0.990833.
- **mixmdp**: an upload: US/India from v7sq3; France from v7sq7wg (guarded round-2 self-training, weight 3) minus 454 look-alike swaps, plus the France DP. Public LB 0.990699; Composite B's France.
- **mixqc**: a composed package, not uploaded, whose French decisions gave the round-4 labels.

## N

- **name_short view**: names-only search (character 4-grams) for records with an empty or short address, and for one-token names such as domains.
- **nx group**: signed house-number features (difference, nudge, digit substitution or swap, suffix, length difference).

## O

- **OOF (out of fold)**: a score from a model that never trained on that row ([page 06](06-gradient-boosting-and-stacking.md)).
- **OOF group**: one of three S1 groups (folds 5–9, 10–14, 15–19); the holdout became a fourth in the final fit.
- **op-B**: the generator's look-alike operation: one S1 name word replaced by another real word at the same house number and street. 0.6% true on the US/India holdout; the French rules drop it.
- **Oracle F0.5**: the best F0.5 reachable with a candidate set if the matcher were perfect.
- **Orphan**: a source record with no owner (26% of records); almost never has an empty address (0.29%).
- **Ownership**: the rule that a record belongs to at most one S1.

## P

- **p0, p1, p2, pc**: the stage-0, stage-1 and stage-2 probabilities, and pc, the calibrated p2 (re-scored by stage 3 downstream).
- **P_MIN**: 0.002, the p1 cut for stage-2 rows.
- **Paired bootstrap**: resampling S1 with Poisson(1) weights to get a confidence interval for the difference between two systems scored on the same S1; also gives P(better).
- **PAV (pool-adjacent-violators)**: the linear-time algorithm for isotonic regression.
- **Phantom (λ)**: 0.01 expected true matches outside the candidate list, included in the decision.
- **Platt scaling**: calibration by a logistic regression on the score.
- **Poisson binomial**: the distribution of a sum of independent Bernoulli variables with different probabilities; the number of true matches among an S1's candidates.
- **Pool size**: how many S1 a country partition holds. Test US has half train US's S1 (663k against 1.32M); test France has 259,452.
- **`post_ops` (rules v2, v3)**: the French generator-operation rules: drop op-B predictions, add A/APP/ACR pairs where the S1 owns the record and no other S1 holds it. v3 reads addresses robustly (suffixed numbers, typo'd street types).
- **Posting list**: the list of records that contain a given token in an inverted index.
- **Precision, recall**: the share of predicted matches that are true; the share of true matches that are predicted.
- **Probe**: an upload meant to measure something rather than to win, such as fr0.
- **Product quantization (IVF-PQ)**: compressing vectors into short codes for memory-efficient nearest-neighbour search.
- **Proper scoring rule**: a loss minimised in expectation only by the true probability (log-loss, Brier score).
- **Pseudo-label**: a label taken from our own model's decision on unlabelled French data: 1 if kept at pc ≥ 0.9 or added by a rule, 0 if dropped at pc ≤ 0.05 or removed as op-B, otherwise unlabelled.
- **Pseudo-residual**: the negative gradient that each new boosted tree is fitted to; y − p for log-loss.
- **Public LB, private LB**: see LB.

## Q

- **q7st, qst, q34st**: LoRA cross-encoders self-trained on French pseudo-labels: Qwen2.5-7B (q7st, Bakshi; band AUC 0.9436), Qwen2.5-1.5B (qst, Sachi's LoRA classifier; 0.9381) and Qwen3-4B-Base (q34st; 0.9411, finished too late to use).
- **QuantileDMatrix**: XGBoost's memory-saving input that bins features directly.
- **Qwen2.5**: an Apache-2.0 decoder LLM family; the 0.5B, 1.5B and 7B models are Apache-2.0, the 3B is not.

## R

- **Random forest**: deep trees on bootstrap samples, averaged; lowers variance rather than bias. Not used.
- **Re-check (7B re-check)**: q7st re-reads predictions with p1 > 0.99; those below logit −6 are dropped (840 French and 310 US/India in Composite B).
- **Re-weighted holdout**: the holdout re-weighted to the test's mix of name-group sizes; the basis of the US/India part.
- **Recall (pair recall, pair completeness)**: the share of true pairs present in a candidate set. Retrieval keeps 99.135% of true holdout pairs.
- **Record linkage**: entity resolution across different sources.
- **Reduction ratio**: 1 − candidate pairs / all possible pairs.
- **Regularisation (λ, γ)**: XGBoost's L2 penalty on leaf weights and minimum gain per split.
- **Reject option**: a classifier's third action, abstain; see selective prediction.
- **Reliability diagram**: the true rate against the mean score, per score bin.
- **Repairs**: blocking fixes applied before matching: domain names split into words, OCR digits in names fixed, Indic names transliterated.
- **Repeated 2-fold CV**: splitting the holdout S1 in two many times, tuning on one half and scoring on the other; the DP with the phantom kept +23.7e-6 over 42 splits.
- **Rival S1**: another S1 competing for the same record.
- **Round (self-training)**: one cycle of labelling with the current best model and retraining: round 1 (v7ce3's decisions), round 2 (v7sq's, guarded), round 3 (mixmdp's), round 4 (mixqc's).
- **Rule-population AUC**: the AUC of a model's French pc on pairs whose truth rate is known from US/India (A/APP/ACR true, op-B false). A label-free French score, until self-training made it circular.

## S

- **S1, S2, S3**: Source 1 is the deduplicated reference list of businesses; Sources 2 and 3 are vendor files whose records may copy an S1 business. For each S1 we list its S2/S3 copies.
- **s3-ops3a (suffix)**: stage 3, then rules v3, then the acronym join.
- **ScaNN**: an ANN library based on anisotropic vector quantization.
- **Seed cap**: in our token search, only tokens whose posting list is short enough (1,000 or 3,000 records) seed candidates; a form of block purging.
- **Selective prediction**: a classifier that may abstain, judged by its risk (errors on what it keeps) against its coverage.
- **Self-training**: retraining a model on its own confident predictions ([page 09](09-self-training-and-domain-shift.md)).
- **SHAP**: Shapley-value attributions of a prediction to its features; we used it to explain France's lower confidence.
- **Shrinkage (eta)**: the learning rate that scales each new tree.
- **Similarity join**: finding all pairs above a similarity threshold, often with prefix filtering.
- **Singleton**: an S1 with no copies (about 5.6%); it scores 1.0 only if we predict nothing.
- **Size-bias test**: a label-free test of a predicted population: true copies attach to S1 in proportion to their copy count, extra records do not, so fitting the mixture gives the false share.
- **Skew**: uneven work across machines, caused by giant blocks or partitions.
- **Soft key**: a blocking key used as one of several passes, with fallbacks, so a record missing the key is still found.
- **Spot instance**: an interruptible rented machine; one took our bge logits with it on 26 Sep.
- **Stacking**: feeding one model's scores to another as features ([page 06](06-gradient-boosting-and-stacking.md)).
- **Stage 0, 1, 2, 3**: our XGBoost cascade: a cheap filter; the pair model (p1); the context model with cross-encoder features, calibrated (pc); re-scoring against rivals.
- **Star-shaped matching**: each record attaches to at most one deduplicated S1, so there are no chains of matches to close transitively.
- **Street type**: Rue, Avenue, R., Bd and the like; our address keys skip them.
- **swapsim** (`apply_swapsim.py`): the French look-alike word-swap drop (a word replaced by a similar real word at the S1's address); 454 pairs in mixmdp.
- **Synthetic French data**: labelled French pairs generated from real French S1 with the generator's operations (Sachi's `synth_fr.py`, Ameya's extensions); tried, not used in the final model.

## T

- **Target encoding**: a feature built from labels, such as a word's log-odds of a true match; it must be computed out of fold. Our `lo__*` features are one.
- **τ0 (tau0)**: stage 0's cut, set to keep 99.95% of the positives outside its training sample.
- **Teacher, student**: in self-training, the model whose decisions become labels, and the model trained on them.
- **Temperature scaling**: calibration by dividing a logit by one number T.
- **Test-time adaptation**: updating a trained model on the test stream itself (for example Tent); we adapted decisions, not weights, at test time.
- **Token view (`tok`)**: IDF-weighted token-overlap search on name and address, in both directions and per country, with compound keys: each S1's top 40 records and each record's top 8 S1, trimmed to the top 15 and top 4.
- **Transductive learning**: using the unlabelled test data during training, as our self-training does.
- **Transformer**: a neural network built from attention and MLP layers ([page 08](08-transformers-and-cross-encoders.md)).
- **Transitive closure**: merging chains of pairwise matches into clusters; not needed for star-shaped matching.

## U

- **Uncertain band**: see band.
- **Unseen domain**: a domain with no labels at all, like France.
- **US/India part**: 0.38274 F_US + 0.46751 F_India, the US and Indian shares of the leaderboard at the re-weighted holdout; the leaderboard minus it, divided by 0.14975, gives France's implied level.

## V

- **Validator**: the organisers' `validate_submission.py`. It still prints PASS when matches fall outside the candidates (only a warning) and never checks ownership or country consistency; our audit does.
- **vCPU-hour**: one virtual CPU busy for one hour.
- **Version names**:
  - **v0** (baseline, local holdout 0.9683), **v2** (0.98436), **v3** (0.98882), **v3ce** (the first cross-encoder, e5-small), **v4** (France fixes: proxy odds, no legal bitmasks);
  - **v5all**, **v6all** (final fits on all of train; v6all adds blocking v3, the nx features and the candidate cut);
  - **v7ce3** (e5-base and e5-large as features; the round-1 teacher), **v7c** (separate cross-encoder logits), **v7m**, **v7n** (one z-mean), **v7nst** (round-1 self-training), **v7nst2** (unguarded round 2);
  - **v7mst**, **v7s**, **v7sb**, **v7sq** (bge, then self-trained cross-encoders in the mean; v7sq adds qst), **v7sq3** (plus e5ls2), **v7sq6** (four round-1 self-trained cross-encoders), **v7sq6r3** (round-3 labels), **v7sqwg** and **v7sq7wg** (guarded labels at weight 3; v7sq7wg adds e5fr and is mixmdp's France);
  - **v7ensall**, **v7ensall2** (bags of five and seven models), **v7sqsyc**, **v7sqsyd** (with synthetic cross-encoders; not used).

## W

- **Weak supervision**: training labels from rules or heuristics with known accuracy; our French rules play that role.
- **wg**: "weighted, guarded": stage 2 trained on guarded pseudo-labels at weight 3.

## Z

- **z-mean, z-score**: a logit standardised by the mean and standard deviation of its train-band values; the z-mean averages several cross-encoders' z-scores into one stage-2 feature.
