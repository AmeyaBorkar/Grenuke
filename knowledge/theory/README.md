# Theory study guide

**New to a topic? Start with the foundations track:** [`foundations/README.md`](foundations/README.md) has 18 pages from scratch (data, statistics, ML, metrics, trees, text and retrieval, neural networks and LLMs, scale, experiments, domain shift, decision theory, interpreting our results, linear algebra, information theory, clustering and graphs, limited labels, production ML, tuning and interpretability), a curriculum and a self-assessment checklist. The pages below are the advanced layer.

**Summary.** The theory behind every technique team Grenuke used in the Amazon ML Challenge 2026 (business entity resolution), written so that each of us can defend any part of the pipeline before senior Amazon scientists on 7 Oct 2026 (10-minute talk, 5 minutes of Q&A). Eleven pages and a glossary, each tied to our own numbers, plus a two-day study plan, a pair self-test drill and the ten things every member must be able to explain in one minute.

The jury values reasoning over results and probes scale and the candidate-pairs-per-entity ratio; finalists were ranked on the private leaderboard, blocking strategy and novelty (finer keys and compute-efficient methods scored higher) and candidate efficiency ([finale README][finale]). The guide is built for exactly those questions.

---

## How the pages work

Every page follows the theory format of [`knowledge/STANDARD.md`][standard] §2.7: **Intuition · Formal definition · Variants · Where we used it · Why it fits this problem · Pitfalls · Jury questions with answers · Self-test (answers hidden in `<details>`) · Further reading**.

- **Numbers carry a scope and an evidence level:** [M] measured, [E] estimated, [R] reported, [U] uncertain. "Local holdout" is the fixed 25% of labelled US/India S1 (549,699 S1); "public LB" is the leaderboard during the challenge; the private LB, which decides the ranking, we have not seen.
- **References** are classic sources cited by author, year and title, only where we are sure they exist.
- **Who did what** is stated on each page; credit goes to whoever had the idea.

## The pages

| # | page | what it covers | first learner | backup |
|---|---|---|---|---|
| 01 | [Entity resolution](01-entity-resolution.md) | the problem, the classic pipeline, Fellegi–Sunter, rules vs probabilities vs learning, one-to-many with exclusive ownership, clustering, active learning, deep ER, where we sit | everyone | |
| 02 | [Blocking](02-blocking.md) | quality measures (recall, reduction ratio, pairs quality, candidates per S1), the standard methods, our per-country two-direction retrieval and learned cut, city/state keys honestly compared | Ameya | Bakshi |
| 03 | [String similarity](03-string-similarity.md) | normalisation, edit distances, Jaro–Winkler, token and TF-IDF measures, q-grams, phonetic codes, transliteration, house numbers, look-alike word odds | Bakshi | Ameya |
| 04 | [Metrics and decisions](04-metrics-and-decisions.md) | F0.5, macro averaging, singletons, the break-even derivation, expected-F optimisation, our per-S1 DP, ownership, why a threshold lost | Ameya | Sachi |
| 05 | [Evaluation methodology](05-evaluation-methodology.md) | the grouped holdout, out-of-fold training, ER leakage, the paired bootstrap, multiple comparisons, leaderboard overfitting, label-free France checks, the holdout-vs-LB gap | Sachi | Ameya |
| 06 | [Gradient boosting and stacking](06-gradient-boosting-and-stacking.md) | XGBoost, the four-stage cascade, out-of-fold stacking, context features, SHAP | Sachi | Ameya |
| 07 | [Calibration](07-calibration.md) | reliability, isotonic regression, why the DP needs calibrated probabilities | Sachi | Ameya |
| 08 | [Transformers and cross-encoders](08-transformers-and-cross-encoders.md) | e5, bge and Qwen as pair classifiers, LoRA, the uncertain band, z-scored mixing | Sachi (Qwen 1.5B), Ameya (e5, bge) | Bakshi |
| 09 | [Self-training and domain shift](09-self-training-and-domain-shift.md) | France without labels: pseudo-labels, guards, cross-fitting, why rounds beyond two drift | Ameya (self-training, rules), Sachi (synthetic French, diagnostics) | Bakshi |
| 10 | [LLM verification and compute](10-llm-verification-and-compute.md) | Qwen2.5-7B in the mix and as a re-checker of confident predictions; GPU cost | Bakshi | Ameya |
| 11 | [Scaling to billions](11-scaling-to-billions.md) | cost per stage, the candidates-per-entity ratio as the cost driver, what we would change for production | Ameya | Bakshi |
| — | [Glossary](glossary.md) | every term, one line each | everyone | |

First learners follow the proposed Q&A leads in [`docs/TEAM.md`][team]; everyone must still be able to answer on every page.

## Two-day study plan

Day 1 starts after the deck is submitted (planned Mon 5 Oct 14:00 IST); Day 2 is Tue 6 Oct, the day before the finale ([finale README][finale]). Adjust the clock, keep the order.

**Day 1 (Mon 5 Oct, 15:00–21:30): own your pages**

| time | Ameya | Sachi | Bakshi |
|---|---|---|---|
| 15:00–15:45 | all three together: this page, the ten things below, start a shared misses log | | |
| 15:45–17:15 | 02 blocking | 05 evaluation | 03 string similarity |
| 17:30–19:00 | 04 decisions, then 11 scale | 06 boosting, then 07 calibration | 10 LLM verification, then the 7B parts of 08 |
| 19:45–21:15 | pair drill, round 1, on lead pages: Ameya examines Sachi (05, 06), Sachi examines Bakshi (03, 10), Bakshi examines Ameya (02, 04); 30 minutes each | | |
| 21:15–21:30 | write every missed question into the log with the page to re-read | | |

While reading a lead page, write your own one-minute answer to each jury question, and mark any number you cannot trace to its source.

**Day 2 (Tue 6 Oct, 09:00–18:30): learn everyone else's**

| time | what | who |
|---|---|---|
| 09:00–10:30 | teach-back: each first learner teaches a page in 12 minutes plus 3 of questions (02, 03, 04, 05, 06, 09) | lead teaches, two listen |
| 10:30–12:00 | rotation reading. Everyone masters 01, 02, 04 and 05, the jury's core (problem, blocking, decision, evaluation); then sections 1, 5 and 7 of the pages you did not lead | solo |
| 13:00–14:30 | pair drill, round 2, on non-lead pages; the page's first learner examines | pairs rotate |
| 14:30–15:30 | rehearsal 2 of the talk (timed) | all |
| 15:30–16:30 | hot seat: random jury questions from every page, 60-second answers, the other two grade; weight it to scale, candidates per entity, city/state keys, France and the 7B | all |
| 16:30–17:00 | re-test everything in the misses log | pairs |
| 17:00–18:00 | rehearsal 3 with a mock 5-minute Q&A, interruptions allowed | all |
| 18:00–18:30 | each member explains all ten things in ten minutes; then stop studying | all |

## How to self-test in pairs

One **examiner**, one **candidate**, 20–30 minutes, then swap. Rotate pairs every round so that everyone hears everyone.

1. **Draw** a question from a page's section 7 or 8, or from the ten things.
2. **One-minute answer**, timed, no notes. Lead with at most three sentences, the way you would say it aloud.
3. **Why-chain:** the examiner asks "why?" twice.
4. **Number check:** every number needs its scope (local holdout, public LB, private LB) and whether it was measured or estimated. A right number with the wrong scope is a miss.
5. **Hostile follow-up:** "what breaks at 100× the data?", "what if that number is wrong?", "what did you not measure?".
6. **Score** 0–2 on each of: correct, concise, numbers with scope, honest about limits. Below 6 of 8 goes into the misses log (question, what went wrong, page to re-read, when to re-test).

House rules:
- "We did not measure that; here is how we would" beats a confident guess. Never invent a number.
- Quote numbers only from these pages or `knowledge/numbers.md`, so that all three of us say the same thing.
- Say who did what, and give credit to the person who had the idea.

## The ten things every member must explain in one minute

1. **The task and the metric.** For each S1, find its 0–11 copies in S2/S3. F0.5 per S1, averaged over all S1: a wrong merge costs 2–3 times a miss at our typical sizes, and a singleton (5.6% of S1) scores 1 only for an empty answer. [04](04-metrics-and-decisions.md)
2. **Why it is hard.** 23.7M records; half of all S1 share their name with another S1; the test adds look-alike decoys at the true address (23% more records per S1, same number of true copies); France appears only in test. [01](01-entity-resolution.md)
3. **Blocking and the candidate ratio.** Per-country IDF token retrieval in both directions, a names-only view and repairs: 58.4M retrieved pairs keep 99.1% of true holdout pairs. A learned cut leaves 6.41M, **3.70 per S1, against 3.46 true copies per S1**; when measured, the cut kept 98.2% of true pairs and did not change F0.5. Why fine keys are weights in our search, not hard city/state partitions. [02](02-blocking.md)
4. **Copies against decoys.** House-number relations (the top feature), typo-tolerant token matching, learned look-alike word odds, legal forms, transliteration with a 693-entry learned dictionary. [03](03-string-similarity.md)
5. **The model cascade.** Four XGBoost stages trained out of fold, isotonic calibration, and cross-encoders only on the 1.49M uncertain test pairs (band AUC 0.930 for stage 1, up to 0.944 for Qwen2.5-7B). Spend compute where the uncertainty is. [06](06-gradient-boosting-and-stacking.md), [07](07-calibration.md), [08](08-transformers-and-cross-encoders.md)
6. **The decision layer.** For each S1, the set with the highest expected F0.5 under calibrated probabilities (a small DP, linear in entities); each record goes only to its best S1, which is exact for many-to-one ownership and why Hungarian is wrong here. +0.000048 [+0.000007, +0.000091] over the best global threshold on the local holdout, about half that out of sample. [04](04-metrics-and-decisions.md)
7. **France without labels.** Self-training on our own guarded decisions (positives at pc ≥ 0.9, negatives at ≤ 0.05, rules win, cross-fitted by S1 group): +0.00046 public LB in round 1; two rounds helped, a third did not. [09](09-self-training-and-domain-shift.md)
8. **The 7B re-check.** 94.5% of final predictions were never read by a cross-encoder; a LoRA-tuned Qwen2.5-7B re-reads them and we drop those below logit −6, a cut-off fixed on labelled data first. It removed 840 French decoys; only 8% of predictions rejected that strongly on labelled data are real matches. [10](10-llm-verification-and-compute.md)
9. **How we measured.** A fixed, S1-grouped 25% holdout, out-of-fold stacking, paired bootstraps, confirmation on both holdout halves, and leaderboard uploads designed as experiments. Local 0.9913 against public 0.990879 because France cannot be in the holdout; France comes out near 0.985 [E]. [05](05-evaluation-methodology.md)
10. **Scale.** Every stage after blocking costs in proportion to pairs, so candidates per entity is the cost driver; the 7B at about 600 pairs per second would need about 27 GPU-hours for all 58M retrieved test pairs, which is why it runs only where it pays. [11](11-scaling-to-billions.md), [02](02-blocking.md)

## Numbers never to misquote

| say | not | why |
|---|---|---|
| retrieval keeps **99.1%** of true holdout pairs (about 34 per S1); the **3.70-per-S1** file kept **98.2%** when measured | "3.70 per S1 at 99.1% recall" | two different sets ([02](02-blocking.md) §2) |
| **local holdout 0.9913**; **public LB 0.990879** | "our F0.5 is 0.99" without a scope | name the evaluation, always |
| private LB: **not seen** | any private number | we do not know it |
| France **about 0.93** early, **about 0.985** at the end, both estimated | "France scored …" | backed out of the LB formula |
| the DP gained **+0.000048** in sample, about **+0.000024** out of sample | "the DP gained a lot" | it is a refinement |

**Corrections found while writing this part** (for the curator's `knowledge/conflicts.md`):
- Our methodology ([§1][doc]) and the [finale README][finale] say the cut to 3.70 per S1 keeps 99.1% of true pairs. In the records 99.1% (0.99135) is the retrieval recall of blocking v3; the cut file kept 0.98198 when last measured (model v5all, blocking v2) and was not re-measured on the final model ([candidate-cut record][cut], [blocking v3 record][blk3]).
- [FINAL_PLAN §4.2][plan] says the Indic dictionary needs at least 2 supporting pairs and a 60% share; the code that ran (`feats.learn_indic_dict`) uses at least 5 pairs and a 50% share ([`feats.py`][feats]). Page 03 follows the code.

[finale]: ../../finale/README.md
[standard]: ../STANDARD.md
[team]: ../../docs/TEAM.md
[doc]: ../../experiments/ameya/final-zip/doc/Documentation_template.md
[cut]: ../../docs/decisions/2026-09-26_0532_candidate-set-cut.md
[blk3]: ../../docs/decisions/2026-09-26_1122_blocking-v3-repairs.md
[plan]: ../../plans/FINAL_PLAN.md
[feats]: ../../experiments/ameya/model-v1/feats.py
