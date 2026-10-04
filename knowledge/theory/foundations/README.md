# Foundations track: the whole deal

**Summary.**
- Eighteen pages that teach, from zero, what sits under our pipeline: the data, probability and statistics, machine learning, metrics, trees, text and retrieval, neural networks, scale, evidence, domain shift, decisions, our results, linear algebra, information theory, graphs, limited labels, production and tuning.
- They sit below the eleven advanced pages of the [theory study guide](../README.md) (01 to 11). Each foundation page names the advanced page it prepares, and section 3 below lists, for each advanced page, what to read first.
- This file is the curriculum: the map, the prerequisite order, priority tiers with hours, a reading path for each Q&A topic, and about 100 "I can explain" statements to tick off.

The track is written for three of us who know machine learning and learn fast, and who want the whole picture and not a crash course. The finale runs on Wed 7 Oct 2026, 09:00 to 14:00 IST, and our slot is a 10-minute talk and 5 minutes of Q&A with senior Amazon scientists, who probe understanding, scale and production use ([finale brief](../../../finale/README.md)). Team Grenuke is 2nd of the Top 10. The organisers publish ranks only, so no private-leaderboard score exists.

---

## 1. How the track works

- **One shape for every page** ([STANDARD section 2.9](../../STANDARD.md)): a summary and "What you need first"; the concepts from zero, each with intuition, a precise definition and a worked example (ours where possible: Acme Robotics Inc and its copies and look-alikes); how it shows up in our project; how to read the numbers; common misconceptions; "Check yourself" (exercises with hidden answers); going deeper; where next.
- **Evidence levels.** Numbers about our project carry **M** measured, **E** estimated or derived, **R** reported and not re-checked. "Toy" marks numbers invented for practice. Every score names its evaluation: "local holdout" (the fixed 25% of labelled US/India S1, 549,699 S1, no France), "public LB", or "private LB" (rank only).
- **Numbers.** The [methodology document](../../../experiments/ameya/final-zip/doc/Documentation_template.md) is the source for most of them. When the curator's number sheet `knowledge/numbers.md` exists, it wins over any number in these pages.
- **Three ways to read a page.**
  - **Full read:** the whole page and all exercises.
  - **Fast path:** only the sections named in the table of section 4 (named for F01, F02, F03, F04 and F17).
  - **Pass (30 to 40 minutes):** the summary, "How to read the numbers", "Common misconceptions" and three exercises of your choice. Use it for any page you do not lead.
- **Time estimates** assume about 1 hour of reading per 20 to 25 thousand characters (with the worked examples), plus about 6 minutes per exercise. Adjust to your speed.
- **The talk comes first.** The deck, the script and the rehearsals ([finale brief](../../../finale/README.md)) come before reading. This track fills the gaps around them.

---

## 2. The map

| page | what it teaches | prepares advanced pages | tier | hours (full / fast) |
|---|---|---|---|---|
| [F01 Data and the problem](F01-data-and-problem.md) | records, sources, matches, singletons, look-alikes; exploring a dataset; our data facts and what each forced; counts against rates; checking a claim | 01, 02, 11 | P1 | 2 / 1 |
| [F02 Probability and statistics](F02-probability-and-statistics.md) | Bayes, odds and logit, Poisson-binomial and expected F0.5, standard error, intervals, tests, bootstrap and paired bootstrap, effect size, multiple comparisons | 04, 05, 07 | P1 | 3 / 1.5 |
| [F03 Machine learning fundamentals](F03-machine-learning-fundamentals.md) | pair classification, our folds, over- and underfitting, bias and variance, regularisation, log loss, gradient descent, out-of-fold, leakage, imbalance, baselines | 05, 06, 07 | P1 | 2.5 / 1.25 |
| [F04 Classification metrics](F04-classification-metrics.md) | confusion matrix, F-beta and the count form of F0.5, per-S1 costs, macro and micro, thresholds and break-even, ROC and AUC (0.944), PR, calibration, blocking metrics, leaderboard arithmetic | 04, 07, 02, 08 | P1 | 2.5 / 1.25 |
| [F05 Trees and ensembles](F05-trees-and-ensembles.md) | decision trees, bagging, boosting by hand, the XGBoost objective and knobs, stacking and cascades, importance against SHAP | 06 | P2 | 3 |
| [F06 Text, strings and retrieval](F06-text-strings-and-retrieval.md) | Unicode, tokens, n-grams, edit distance, Jaro-Winkler, Jaccard, TF-IDF and cosine, the inverted index, top-k in both directions, transliteration | 02, 03 | P2 | 2.5 |
| [F07 Neural networks, transformers and LLMs](F07-neural-networks-transformers-llms.md) | backpropagation, tokens, attention, encoders and decoders, cross-encoders, LoRA, number formats, GPU memory, z-scoring logits | 08, 10 | P2 | 2.5 |
| [F08 Computing at scale](F08-computing-at-scale.md) | Big-O, hashing, sorting, partitioning, MapReduce and skew, nearest-neighbour search, memory, columnar files, throughput arithmetic | 11, 02, 10 | P2 | 2 |
| [F09 Experiments and evidence](F09-experiments-and-evidence.md) | signal and noise, baselines, ablations, the fixed holdout, gates, paired comparisons, leaderboards, control uploads, evidence levels | 05 | P1 | 2.5 |
| [F10 Semi-supervised learning and domain shift](F10-semi-supervised-and-domain-shift.md) | kinds of shift, leave-one-country-out, self-training, guards, cross-fitting, why gains stopped, label-free diagnostics | 09 | P1 | 2.5 |
| [F11 Decision theory and optimisation](F11-decision-theory-and-optimisation.md) | expected utility, F0.5 in counts, break-even, dynamic programming, per-S1 set selection, ownership, Bayes limits | 04, 07 | P2 | 3 |
| [F12 Interpreting our results](F12-interpreting-our-results.md) | a guided tour of every key number, and the ten numbers to say aloud | 05, 09, 10 | P1 | 3 |
| [F13 Linear algebra and optimisation](F13-linear-algebra-and-optimisation.md) | vectors, matrices, SVD and PCA, low rank and LoRA, gradients, SGD and Adam, second-order information | 08, 06 | P3 | 2.5 |
| [F14 Information theory and losses](F14-information-theory-and-losses.md) | entropy, cross-entropy, KL, proper scoring rules, softmax and temperature, logit shifts, weights | 07, 06, 08 | P3 | 2 |
| [F15 Clustering, graphs and ER variants](F15-clustering-graphs-and-er-variants.md) | shapes of ER, cardinality, graphs, transitive closure, correlation clustering, assignment, our ownership constraint | 01, 04 | P3 | 2.5 |
| [F16 Learning with limited labels](F16-learning-with-limited-labels.md) | the label budget, transfer learning and LoRA, multilingual models, zero- and few-shot LLMs, active learning, weak supervision, synthetic data, pseudo-labels | 09, 10 | P2 | 2.5 |
| [F17 Production ML and MLOps](F17-production-ml-and-mlops.md) | batch and incremental ER, candidate service, feature stores, cost and latency, monitoring, review queues, A/B tests, reproducibility, governance | 11, 10, 05, 09 | P1 | 2.5 / 1.25 |
| [F18 Tuning, ensembles and interpretability](F18-tuning-ensembles-and-interpretability.md) | hyperparameters and validation reuse, ensembling theory, diversity against accuracy, stacking, interpretability, error analysis, ablations | 06, 08, 05 | P2 | 2.5 |

---

## 3. From foundations to the advanced pages

| advanced page | read first (foundations) |
|---|---|
| [01 Entity resolution](../01-entity-resolution.md) | F01; F02 sections 2.2 and 2.3 (Fellegi-Sunter); F15 |
| [02 Blocking](../02-blocking.md) | F01; F06 sections 7 to 9; F08; F04 section 2.11 |
| [03 String similarity](../03-string-similarity.md) | F06; F13 section 1 (cosine) |
| [04 Metrics and decisions](../04-metrics-and-decisions.md) | F04; F02 sections 2.5 and 2.6; F11; F15 sections 2.6 to 2.8 |
| [05 Evaluation methodology](../05-evaluation-methodology.md) | F09; F02 sections 2.7 to 2.12; F03 sections 2.2, 2.8 and 2.9 |
| [06 Gradient boosting and stacking](../06-gradient-boosting-and-stacking.md) | F05; F03 sections 2.6 to 2.8; F13 section 11; F18 section 7 |
| [07 Calibration](../07-calibration.md) | F04 section 2.10; F14 sections 6 and 7; F02 section 2.3; F11 |
| [08 Transformers and cross-encoders](../08-transformers-and-cross-encoders.md) | F07; F13 sections 7 and 10; F14 sections 2 and 7; F04 section 2.8; F18 sections 4 to 6 |
| [09 Self-training and domain shift](../09-self-training-and-domain-shift.md) | F10; F16; F03 section 2.8 |
| [10 LLM verification and compute](../10-llm-verification-and-compute.md) | F07 sections 8 to 12; F08 section 9; F17 section 2.5; F11 section 2.7 |
| [11 Scaling to billions](../11-scaling-to-billions.md) | F08; F17; F06 sections 8 and 9; F01 sections 2.3 and 2.9 |

The glossary ([glossary](../glossary.md)) has one line for every term.

---

## 4. Prerequisites

**The order in text.** Read left to right; "+" means all of them are needed first.

```
Core line        F01 --> F02 --> F03 --> F04 --> F09 --+--> F10 --> F12
                                                       +--> F11 --> F12
Model line       F03 --> F05 --> F18
Network line     F03 --> F13 --+
                 F03 --> F14 --+--> F07 --> F18          (F07 also needs F06)
Text and scale   F01 --> F06 --> F08 --> F17             (F17 also needs F03 and F04)
Branches         F11 --> F15            F10 --> F16          (F16 also needs F03, F04 and F07)
```

**The exact lists** (from each page's own "What you need first").

| page | needs first | also helps | fast path (sections) |
|---|---|---|---|
| F01 | nothing | | 2.2, 2.5, 2.6, 2.9, 2.10 |
| F02 | F01 | | 2.2, 2.3, 2.5, 2.6, 2.9 to 2.12 |
| F03 | F01, F02 (2.1 to 2.3) | | 2.6, 2.8 to 2.11 |
| F04 | F01, F02 (2.1, 2.3) | F03 | 2.5 to 2.8, 2.11, 2.12 |
| F05 | F02, F03, F04 | F13, F14 | |
| F06 | F01, F02 | F13 section 1 | |
| F07 | F03, F06, F13, F14 | | |
| F08 | F01, F06 | F07, F13 | |
| F09 | F01, F02, F04 | F03 | |
| F10 | F02, F03, F04, F09 | | |
| F11 | F02, F04, F09 | F10 | |
| F12 | F01, F04, F09; later sections need F10 and F11 | | |
| F13 | F03 and school calculus | F05, F06 | |
| F14 | F02, F03, F04 | | |
| F15 | F01, F04, F11 | F06 | |
| F16 | F03, F04, F07, F10 | F14 | |
| F17 | F01, F03, F04 | F08, F09, F10 | 2.2, 2.5, 2.6, 2.8, 2.9, 2.11 |
| F18 | F03, F05, F07, F09 | F14 | |

F07 needs only a few sections of F13 (matrices, the chain rule) and F14 (cross-entropy, softmax); read those sections and not the whole pages.

---

## 5. Priority tiers

| tier | meaning | pages | hours |
|---|---|---|---|
| **P1** | must-know before the finale on Wed 7 Oct | F01, F02, F03, F04, F09, F10, F12, F17 | 20.5 in full, about 14 with the fast paths of F01 to F04 and F17 |
| **P2** | complete understanding of the pipeline | F05, F06, F07, F08, F11, F16, F18 | 18 |
| **P3** | depth: the mathematics and the variants | F13, F14, F15 | 7 |

The whole track is about 45 hours. Nobody reads everything before Wednesday, and the plan does not need that.

**Why these are P1.** The jury asks for reasons and numbers: what the metric rewards (F04), how we know a change helped (F09, F02, F03), what happened with France (F10), what every number means (F12), what the data looked like (F01), and what this costs and how it would run for real (F17).

**The common core for everyone before Wednesday: about 8 hours.**

| piece | hours |
|---|---|
| F12 sections 2.1 to 2.6 and 2.12 (the scoreboard, holdout against LB, per-country scores, the staircase, the France level, the ten numbers) | 1.5 |
| F04 fast path | 1.25 |
| F09 sections 2.4 to 2.10 (the fixed holdout, gates, paired comparisons, effect size, many comparisons, leaderboards, control uploads) | 1.25 |
| F10 sections 2.1 and 2.3 to 2.7 (shift, self-training, guards, cross-fitting, why gains stopped, label-free checks) | 1.5 |
| F01 fast path | 1 |
| F17 fast path | 1.25 |

**On top of the core**, follow the paths of the topics you lead (section 6); pages already in the core are not read twice. A member who leads many topics should take them in the order of the likely jury questions: framing, the decision layer, France, blocking and scale, cross-encoders. The backup covers the rest in the first pass.

**Promotion.** A lead promotes the P2 and P3 pages of their topic to P1 for themselves. F07 also needs a few sections of F13 and F14.

**If you have one evening:** the F04 fast path (1.25 hours), a pass on F09 (0.5 hours), then F12 sections 2.1 to 2.6 and 2.12 (1.5 hours). That covers the metric, the evidence rules and the numbers.

---

## 6. Paths for the nine Q&A topics

The leads and backups are the proposals in [docs/TEAM.md](../../../docs/TEAM.md) ("Finale roles"; confirm in the team call). "Pass" means 30 to 40 minutes. A member who leads several topics follows the union and reads shared pages once. Section numbers refer to the pages as written on 4 Oct. "Ready when" lists checklist items from section 8.

**1. Problem framing, data analysis, overall strategy.** Lead Ameya, backup Sachi.
1. F01 in full (2 h). 2. F04 fast path (1.25 h). 3. F12 in full (3 h). 4. F09 pass (0.5 h).
Then advanced 01, 04, 05. About 7 hours. Ready when: F01.1 to F01.6, F04.1 to F04.5, F12.1 to F12.6.

**2. Blocking and candidate generation; the candidates-per-entity ratio; scale.** Lead Ameya, backup Bakshi.
1. F01 fast path (1 h). 2. F06 sections 7 to 9 and 11 (TF-IDF and cosine, the inverted index, top-k both ways, why exact keys fail) (1.25 h). 3. F08 in full (2 h). 4. F17 fast path (1.25 h). 5. F04 section 2.11 (0.25 h).
Then advanced 02, 11. About 6 hours. Ready when: F01.3, F06.5, F08.1 to F08.6, F17.2, F17.4, F04.8.

**3. Normalisation, lexicons, string features.** Lead Bakshi, backup Ameya.
1. F01 sections 2.4 and 2.5 (0.5 h). 2. F06 in full (2.5 h). 3. F13 section 1 (0.5 h). 4. F05 pass (0.5 h).
Then advanced 03 (and the string views of 02). About 4 hours. Ready when: F01.4, F06.1 to F06.6.

**4. XGBoost stages, calibration, gates and bootstrap, ablations.** Lead Sachi, backup Ameya.
1. F03 fast path (1.25 h). 2. F05 in full (3 h). 3. F14 sections 2, 6 and 7 (0.75 h). 4. F04 sections 2.7 and 2.10 (0.75 h). 5. F02 fast path (1.5 h). 6. F09 in full (2.5 h). 7. F18 sections 1 to 3 and 9 (1 h).
Then advanced 06, 07, 05. About 10.75 hours. Ready when: F03.6 to F03.8, F05.1 to F05.5, F02.7, F02.8, F09.1 to F09.6, F14.3.

**5. Cross-encoders: e5, bge, Qwen2.5-1.5B with LoRA.** Leads Sachi (Qwen 1.5B) and Ameya (e5, bge), backup Bakshi.
1. F03 fast path (1.25 h). 2. F13 sections 7 and 10 (0.75 h). 3. F14 sections 2 and 7 (0.5 h). 4. F07 in full (2.5 h). 5. F04 section 2.8 (0.4 h). 6. F18 sections 4 to 6 (1 h).
Then advanced 08. About 6.5 hours. Ready when: F07.1 to F07.6, F04.6, F18.2, F18.3.

**6. Qwen2.5-7B in the mix and the re-check of confident predictions; Composite B.** Lead Bakshi, backup Ameya.
1. F07 in full, with sections 8 to 12 closely (2.5 h). 2. F08 section 9 (0.4 h). 3. F11 section 2.7 (0.4 h). 4. F17 sections 2.5 and 2.6 (0.75 h). 5. F04 fast path (1.25 h). 6. F12 sections 2.8 to 2.10 (1 h).
Then advanced 10, 08. About 6.5 hours. Ready when: F07.4 to F07.6, F17.4, F17.5, F04.6, F12.5, F12.6.

**7. France: self-training, rules, probes, synthetic French.** Leads Ameya (self-training, rules) and Sachi (synthetic French, diagnostics), backup Bakshi.
1. F02 fast path (1.5 h). 2. F10 in full (2.5 h). 3. F16 in full (2.5 h). 4. F09 sections 2.9 and 2.10 (0.75 h). 5. F12 sections 2.5 and 2.6 (1 h). 6. F04 section 2.12 (0.3 h).
Then advanced 09, plus 05 section 2.8 and 10 section 4. About 8.5 hours. Ready when: F10.1 to F10.6, F16.1 to F16.4, F12.3, F12.4, F04.9.

**8. The decision layer: expected-F0.5 set selection and ownership.** Lead Ameya, backup Sachi.
1. F02 sections 2.3, 2.5 and 2.6 (1 h). 2. F04 fast path (1.25 h). 3. F11 in full (3 h). 4. F15 sections 2.6 to 2.8 and 2.10 (1 h).
Then advanced 04, and 07 sections 2.3 and 2.4. About 6.25 hours. Ready when: F02.2, F02.4, F02.5, F04.2 to F04.5, F11.1 to F11.5, F15.3.

**9. Reproducibility, the package, compliance.** Lead Bakshi, backup Ameya.
1. F17 in full, with sections 2.9 and 2.10 closely (2.5 h). 2. F09 sections 2.11 and 2.12 (0.5 h). 3. F07 section 10 (0.4 h). 4. F08 pass (0.5 h).
Then advanced 05 section 2.4 and 11 section 6, [AGENTS.md](../../../AGENTS.md) and the package README. About 4 hours. Ready when: F17.7, F17.8, F09.6, F07.5.

---

## 7. A fit with the days before the finale

The advanced track has its own two-day plan ([theory README](../README.md)); these slots go around it and around the rehearsals. Adjust the clock, keep the order.

| when (IST) | what |
|---|---|
| Sun 4 Oct, evening | common core, part one: the F04 fast path; F12 sections 2.1 to 2.6 and 2.12; F09 sections 2.4 to 2.10 |
| Mon 5 Oct | common core, part two: F10, F01 and F17 as above. Then the first pages of your topic paths (section 6) |
| Tue 6 Oct | the rest of your topic paths. Teach one page to the other two in 12 minutes. The "Check yourself" drill in pairs. Say the ten numbers of F12 aloud |
| Wed 7 Oct, before your slot | re-read the "How to read the numbers" tables of F04 and F12; no new material |
| after the finale | P2, then P3, in the order of the map |

---

## 8. Self-assessment: about 100 things you can explain

Tick an item when you can say it in about 60 seconds, with the number and its scope, without looking. If you cannot, re-read the section in brackets. The statements for F05 to F16 and F18, which other authors wrote, were drafted from those pages as they stood on 4 Oct; adjust them if a page changes.

### F01 Data and the problem
- [ ] F01.1 I can explain the difference between a record, an entity and a source, and why there is no shared key. (2.1)
- [ ] F01.2 I can explain matches, copies, singletons and ownership, with 3.46 copies per S1 and 5.6% singletons. (2.2)
- [ ] F01.3 I can walk through the pipeline from records to predicted set with our test sizes: 58.4M, 6.41M and 5.85M pairs. (2.3)
- [ ] F01.4 I can give three kinds of look-alike from our data and say why agreeing on one field is not enough. (2.5)
- [ ] F01.5 I can explain why 23% more records per S1 does not mean more matches, using counts and rates. (2.6)
- [ ] F01.6 I can list the steps for exploring a dataset and sanity-check a claim such as "46 to 54% of S1 share a name". (2.7, 2.10)

### F02 Probability and statistics
- [ ] F02.1 I can use Bayes' rule with a prior and explain the base-rate effect. (2.2)
- [ ] F02.2 I can convert between probability, odds and logit and say what a +0.2 logit shift does. (2.3)
- [ ] F02.3 I can explain why a raw 7B logit of −6 is not a 0.25% probability. (2.3)
- [ ] F02.4 I can compute a Poisson-binomial distribution for three candidates and say why the decision layer needs it. (2.5, 2.6)
- [ ] F02.5 I can explain why expected F0.5 is not F0.5 at the expected counts. (2.6)
- [ ] F02.6 I can bound the standard error of 0.9913 on 549,699 S1. (2.7)
- [ ] F02.7 I can read a 95% interval correctly, including a Wilson interval for 2 true out of 24. (2.8)
- [ ] F02.8 I can explain the paired bootstrap, why it resamples S1, and why P(better) is not a p-value. (2.9, 2.10)
- [ ] F02.9 I can explain effect size against significance, multiple comparisons and the winner's curse, and why no private score exists. (2.11, 2.12)

### F03 Machine learning fundamentals
- [ ] F03.1 I can name the example, features, label, output and loss of our pair classifier. (2.1)
- [ ] F03.2 I can describe our folds: a hash of the S1 ID, 20 buckets, a holdout of 549,699 S1, three OOF groups. (2.2)
- [ ] F03.3 I can diagnose over- and underfitting from training and test error. (2.3)
- [ ] F03.4 I can explain bias and variance, and why averaging correlated models gains little. (2.4)
- [ ] F03.5 I can explain regularisation with the ridge example. (2.5)
- [ ] F03.6 I can explain log loss and why we train for probabilities and decide for the metric. (2.6)
- [ ] F03.7 I can explain out-of-fold predictions and why stage 2 needs them. (2.8)
- [ ] F03.8 I can explain leakage, why we split by S1 and not by pair, and a leak we caught. (2.9)
- [ ] F03.9 I can explain the accuracy trap, the prior-shift correction, and the 0.056 baseline. (2.10, 2.11)

### F04 Classification metrics
- [ ] F04.1 I can draw the confusion matrix for one S1 and explain why accuracy fails. (2.1, 2.2)
- [ ] F04.2 I can derive the count form of F0.5 and say what "one false merge weighs as much as four missed copies" does and does not mean. (2.5)
- [ ] F04.3 I can give the cost of a miss and of a false merge for an S1 with t true copies, and the singleton rules. (2.5, 2.6)
- [ ] F04.4 I can explain macro against micro, and why a macro score cannot be rebuilt from precision and recall. (2.6)
- [ ] F04.5 I can derive the break-even probability 0.8 × F0.5 and explain why one global threshold fails. (2.7)
- [ ] F04.6 I can explain AUC and say what a band AUC of 0.944 does and does not mean. (2.8)
- [ ] F04.7 I can read a PR curve and a reliability diagram and compute an ECE. (2.9, 2.10)
- [ ] F04.8 I can define blocking recall, reduction ratio, pairs per entity and oracle ceiling, and quote 99.1% and 98.2 to 98.4% correctly. (2.11)
- [ ] F04.9 I can use the leaderboard formula to back out France and state its assumptions. (2.12)

### F05 Trees and ensembles
- [ ] F05.1 I can explain how a tree chooses a split and why depth matters. (1)
- [ ] F05.2 I can explain bagging and run two boosting rounds by hand. (2, 3)
- [ ] F05.3 I can explain the XGBoost objective and what the main knobs do. (4)
- [ ] F05.4 I can explain stacking, why it needs out-of-fold scores, and our four stages as a cascade. (5)
- [ ] F05.5 I can explain importance against SHAP and the two France biases SHAP showed. (6)

### F06 Text, strings and retrieval
- [ ] F06.1 I can explain Unicode normalisation, tokenisation and character n-grams, and what each fixes. (1 to 3)
- [ ] F06.2 I can compute an edit distance and say when Jaro-Winkler is the better choice. (4, 5)
- [ ] F06.3 I can compare Jaccard, containment and Dice for a dropped or added word. (6)
- [ ] F06.4 I can compute a TF-IDF cosine and explain why rare words carry the evidence. (7)
- [ ] F06.5 I can explain the inverted index and top-k retrieval in both directions. (8, 9)
- [ ] F06.6 I can explain transliteration and why exact keys fail on noisy data. (10, 11)

### F07 Neural networks, transformers and LLMs
- [ ] F07.1 I can explain backpropagation as the chain rule applied layer by layer. (1, 2)
- [ ] F07.2 I can explain tokens, embeddings and attention. (3, 4)
- [ ] F07.3 I can explain encoders, decoders, bi-encoders and cross-encoders. (5 to 7)
- [ ] F07.4 I can explain how a decoder LLM works as a pair classifier and what LoRA changes. (8, 9)
- [ ] F07.5 I can explain number formats, why GPU runs are not bit-identical, and the memory arithmetic for a 7.6B model. (10, 11)
- [ ] F07.6 I can explain why we z-score logits before averaging. (12)

### F08 Computing at scale
- [ ] F08.1 I can explain why all-pairs is impossible and what Big-O says about our stages. (1)
- [ ] F08.2 I can explain hashing and sorting as ways to group records without comparing all pairs. (2, 3)
- [ ] F08.3 I can explain partitioning by country, and skew with hot keys. (4, 5)
- [ ] F08.4 I can explain LSH, HNSW and FAISS and the recall trade-off. (6)
- [ ] F08.5 I can explain why memory and file layout decide what fits. (7, 8)
- [ ] F08.6 I can do the throughput arithmetic: pairs times cost per pair, and the 27 GPU-hour example. (9)

### F09 Experiments and evidence
- [ ] F09.1 I can tell signal from noise and say why baselines and one-change ablations are needed. (2.1 to 2.3)
- [ ] F09.2 I can explain why the holdout is fixed and split by entity. (2.4)
- [ ] F09.3 I can state our gate rule and why ties go to the simpler option. (2.5)
- [ ] F09.4 I can explain paired comparisons, significance against effect size, and the winner's curse. (2.6 to 2.8)
- [ ] F09.5 I can explain public and private leaderboards and control uploads. (2.9, 2.10)
- [ ] F09.6 I can attach scope and evidence level to any number I quote, and say what reproducible means for us. (2.11, 2.12)

### F10 Semi-supervised learning and domain shift
- [ ] F10.1 I can name the kinds of shift and say which applied to the extra test records and which to France. (2.1)
- [ ] F10.2 I can explain leave-one-country-out as a stand-in for an unseen country. (2.2)
- [ ] F10.3 I can explain self-training, pseudo-labels and our thresholds of 0.9 and 0.05. (2.3)
- [ ] F10.4 I can explain confirmation bias and our guards. (2.4)
- [ ] F10.5 I can explain cross-fitting by S1 group. (2.5)
- [ ] F10.6 I can explain why gains stopped after two rounds and what label-free diagnostics can and cannot show. (2.6, 2.7)

### F11 Decision theory and optimisation
- [ ] F11.1 I can explain expected utility and a cost-based threshold. (2.1)
- [ ] F11.2 I can explain F0.5 in counts and what one error costs. (2.2)
- [ ] F11.3 I can explain why the break-even depends on what the S1 already has, from 0.50 to about 0.80. (2.3)
- [ ] F11.4 I can explain the dynamic programme for the expected F0.5 of a prefix of candidates. (2.4)
- [ ] F11.5 I can explain our per-S1 set selection, ownership, Bayes limits, and why the gain was small. (2.5 to 2.8)

### F12 Interpreting our results
- [ ] F12.1 I can explain why 0.9913 and 0.990879 differ. (2.2)
- [ ] F12.2 I can say what we know about the private leaderboard (rank only) and what we do not. (2.3)
- [ ] F12.3 I can walk through the leaderboard staircase and the cause of each step. (2.5)
- [ ] F12.4 I can explain the implied France level and its assumptions. (2.6)
- [ ] F12.5 I can explain the candidate funnel, the band AUCs and the bootstrap intervals. (2.7 to 2.9)
- [ ] F12.6 I can say the ten key numbers correctly, with scope and evidence level. (2.12)

### F13 Linear algebra and optimisation
- [ ] F13.1 I can explain dot product, norm and cosine, and why TF-IDF cosine works. (1)
- [ ] F13.2 I can explain SVD, PCA and low-rank approximation, and how LoRA uses them. (5 to 7)
- [ ] F13.3 I can explain gradients and the chain rule. (8)
- [ ] F13.4 I can explain SGD, momentum and Adam, and why XGBoost uses second-order information. (10, 11)

### F14 Information theory and losses
- [ ] F14.1 I can explain entropy, cross-entropy and KL divergence, and why log loss is the training loss for probabilities. (1 to 3)
- [ ] F14.2 I can explain proper scoring rules and why they reward honest probabilities. (6)
- [ ] F14.3 I can explain sigmoid, softmax, temperature and logit shifts. (7)
- [ ] F14.4 I can explain class and sample weights, including the weight 3 on French pseudo-labelled rows. (8)

### F15 Clustering, graphs and ER variants
- [ ] F15.1 I can name the three shapes of ER, say which one ours is, and explain what one-to-many with a single owner means for our task. (2.1, 2.2)
- [ ] F15.2 I can explain transitive closure, correlation clustering and the Hungarian algorithm. (2.4 to 2.6)
- [ ] F15.3 I can explain our ownership constraint, rivalry and cluster-support features, and why our structure removed the need for clustering. (2.7, 2.8, 2.10)
- [ ] F15.4 I can explain pairwise against cluster metrics and why ours is macro F0.5. (2.9)

### F16 Learning with limited labels
- [ ] F16.1 I can explain the label budget: about 7.6M labelled true pairs for US and India and none for France, and what each tool costs in labels. (2.1)
- [ ] F16.2 I can explain transfer learning, LoRA, multilingual models and zero- and few-shot LLMs, and why pretraining gives a start while labels teach the task (7B band AUC 0.537 zero-shot, 0.720 after a quick LoRA, 0.944 properly trained). (2.2 to 2.4)
- [ ] F16.3 I can explain active learning and weak supervision, and say which tools we used and which we did not. (2.5, 2.6)
- [ ] F16.4 I can explain augmentation, synthetic data and pseudo-labels, and what we would do with 500 French labels. (2.7, 2.8)

### F17 Production ML and MLOps
- [ ] F17.1 I can compare batch, incremental and streaming ER and say what ownership adds to the problem. (2.2)
- [ ] F17.2 I can explain candidate generation as a service and why candidates per entity drives cost. (2.3)
- [ ] F17.3 I can explain feature stores and training-serving skew, with our context features as the example. (2.4)
- [ ] F17.4 I can give the cost of each stage and show why a cascade saves a factor of 39 (27 GPU-hours against 41 minutes). (2.5)
- [ ] F17.5 I can name label-free monitors for a new market and the France signals that worked. (2.6)
- [ ] F17.6 I can design a review queue, an audit sample and an entity-level A/B test. (2.7, 2.8)
- [ ] F17.7 I can explain our reproducibility practice, its limits on GPUs, and the licence and privacy rules. (2.9, 2.10)
- [ ] F17.8 I can list what we would change to run the pipeline in production, and what we did not measure. (2.11)

### F18 Tuning, ensembles and interpretability
- [ ] F18.1 I can explain why validation gets used up and how to search settings without fooling yourself. (1 to 3)
- [ ] F18.2 I can explain why an ensemble helps only when errors differ, and why diversity beat accuracy for France. (4, 5)
- [ ] F18.3 I can explain stacking, blending and averaging, and our z-scored mean. (6)
- [ ] F18.4 I can explain what interpretability tools can and cannot prove. (7)
- [ ] F18.5 I can do a systematic error analysis and an ablation. (8, 9)

---

## 9. Notes for whoever maintains the track

- Section numbers in sections 3, 4, 6 and 8 refer to the pages as written on 4 Oct 2026. If a page is renumbered, fix them here.
- If a number changes (a score, a count), change it on the page, in this file and in the glossary, and then check the curator's `knowledge/numbers.md`.
- Keep the shape of the pages ([STANDARD section 2.9](../../STANDARD.md)): plain English, short sentences, each term explained when first used, key words in bold sparingly, no italics, answers hidden in `<details>`.
- Do not add a claim without a source. Mark derived numbers E and made-up numbers "toy".
