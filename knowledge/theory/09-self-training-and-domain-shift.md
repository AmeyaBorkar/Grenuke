# Self-training and domain shift

**Summary.** France appears only in the test set, so for our models it is an unseen domain: no labels, a new language, new legal forms and more generic names.
We adapted by self-training on our own French decisions, with guards and cross-fitting by S1 group to limit confirmation bias. The first round added +0.00046 on the public leaderboard, and the second, with the French decision layers, another +0.00015; a third did not help.
The same self-training had failed in our first test, until the model's blind spot for unseen words was fixed; that failure is the most instructive part of the story.

Related pages: [evaluation methodology](05-evaluation-methodology.md), [gradient boosting and stacking](06-gradient-boosting-and-stacking.md) (OOF), [calibration](07-calibration.md) (France's overconfidence), [cross-encoders](08-transformers-and-cross-encoders.md), [glossary](glossary.md).

---

## 1. Intuition

- **Domain shift** means the test data differ from the training data. A model can be excellent on its holdout and still fail where the inputs, the class balance or the rules change.
- **Self-training** lets a model label the unlabelled domain where it is confident, then retrains on those **pseudo-labels**. It works when the confident labels are mostly right and teach something new, such as the target's vocabulary.
- **Confirmation bias** is the failure mode: the model learns its own mistakes as truth, and each round can make them worse.
- Our protection had three parts: fix the known blind spot before self-training, let trusted rules override the pseudo-labels where they know better, and never let a model score a French pair whose label it learned from.

## 2. Formal definition

### 2.1 A taxonomy of shift

Write the source (train) distribution as $P_S(x, y)$ and the target (test) as $P_T(x, y)$.

| shift | what changes | textbook correction | in our data |
|---|---|---|---|
| **covariate** | $P_T(x) \ne P_S(x)$, same $P(y\mid x)$ | importance weights $w(x) = P_T(x)/P_S(x)$ | French language, legal forms (SARL, SAS, EURL) and address formats; the US test pool is half the train pool, so rival counts change |
| **label (prior)** | $P_T(y) \ne P_S(y)$, same $P(x\mid y)$ | shift the logits by the log prior ratio (EM, BBSE) | test has 5.75 S2/S3 records per S1 against 4.68 in train (+23%) with the same true matches per S1; the extras sit below p1 0.02, so the candidates are not affected |
| **concept** | $P_T(y\mid x) \ne P_S(y\mid x)$ | needs target labels | "same name, same house number, different street" is 99.7% true among US/India predictions, but in France, where a generic name is shared by a median of 43 S1, it is mostly a decoy |
| **unseen domain** | no target labels at all | domain generalisation, self-training, proxies | France |

### 2.2 Self-training

With a teacher model f, labelled source data L and an unlabelled target pool U, one round is:

$$\hat y(x) = \begin{cases} 1 & f(x) \ge \tau_+ \\ 0 & f(x) \le \tau_- \\ \text{unlabelled} & \text{otherwise} \end{cases} \qquad\Rightarrow\qquad f_{\text{new}} = \text{train}\big(L \cup \{(x, \hat y(x)) : x \in U\}\big),$$

repeated with $f_{\text{new}}$ as the next teacher (Scudder 1965; Yarowsky 1995; Lee 2013).

**Our version** ([`pseudo_labels.py`](../../experiments/ameya/model-v1/pseudo_labels.py), [`pseudo_guard.py`](../../experiments/ameya/model-v1/pseudo_guard.py)):
- **Labels follow decisions, not raw scores.** y = 1 if the teacher's final submission kept the pair with pc ≥ 0.9, or the French rules or the acronym join added it. y = 0 if the final dropped it with pc ≤ 0.05, or it was an op-B look-alike the rules removed. Everything else stays unlabelled but is still scored.
- **Guards** (from round 2): pairs whose record has an empty address keep their round-1 label, and the French rule populations override the teacher.
- **Cross-fitting by S1 group:** French S1 are split by `fold_of(s1) % n` (three groups for the cross-encoders, four for stage 2). Model g trains on the labelled US/India rows plus the pseudo-labels of the other groups, and alone scores group g's French pairs.
- **Students:** stage 2 (`s2.py --pseudo`, weight 1, later 3) and the cross-encoders (e5ls, qst, bges, q7st). Early stopping and calibration use labelled rows only.

### 2.3 Confirmation bias

Suppose the teacher's confident labels carry an error rate ε. If the errors were random, the student would average them away. If they are **systematic**, tied to features (an unseen word, a generic name), the student learns them as a rule and becomes confident exactly where the teacher was wrong. The next round's labels then contain the same errors with more confidence (Arazo et al. 2020). Nothing inside the loop can detect this, because the loop only sees its own outputs.

### 2.4 Cross-fitting

In double machine learning (Chernozhukov et al. 2018), nuisance models are fitted on one fold and used on another, so an observation never helps fit the model that is applied to it. Our analogue: no French pair is scored by a model that saw its own pseudo-label, or the labels of its S1's other pairs. That stops a student from simply reproducing the teacher on the rows it memorised.

Cross-fitting does **not** remove systematic teacher errors: the same kind of mistake sits in every group. Against those we had the guards, the rules, and checks from outside the loop.

### 2.5 Counts, not rates, under a pool-size shift

A context feature can be a **rate** (how many S1 share this name, divided by the pool) or a **count** (how many S1 share it). What makes a record ambiguous is the count: the number of S1 it could belong to. A name shared by 16 S1 is as ambiguous among France's 259k S1 as among the 1.32M US training S1, but as rates the two differ by a factor of 5, and French rates would look 3–4 times more common than anything in train ([`ber.features.context`](../../code/business_entity_resolution/src/ber/features/context.py)). So our rival features are counts, stored as `log1p(count)`.
- For trees, the log is cosmetic (any monotone transform gives the same splits); the real choice is counts over rates.
- Counts still move with pool size, but in the right direction: in the half-size US test pool fewer S1 share each name, records really are less ambiguous, and the extra US predictions were mostly correct ([RESEARCH_v6 §1](../../experiments/ameya/model-v1/RESEARCH_v6.md)).

### 2.6 Train-time against test-time adaptation

- **Train-time (transductive) adaptation** uses unlabelled target data while training: our self-training, per-country IDF fitted on test records, and look-alike odds counted on French test pairs.
- **Test-time adaptation** updates a trained model on the test stream itself, for example by minimising prediction entropy (Tent). We changed no weights at test time; our France-only rules, French decision and 7B drops adapt the decision instead. Both use only provided, unlabelled data.

## 3. Variants

| method | idea | for us |
|---|---|---|
| Pseudo-labelling, Noisy Student, FixMatch | confident predictions as labels; noise on the student | ours is the plain version, plus guards |
| Co-training | two views label data for each other | text models and feature models are such views |
| Importance weighting | re-weight source rows by $P_T(x)/P_S(x)$ | re-weighted the holdout to the test's name-group sizes |
| Label-shift EM / BBSE | estimate the target prior, shift the logits | not needed: the extra test records sit below p1 0.02 |
| Domain-adversarial training (DANN) | an encoder that cannot tell the domains apart | possible for cross-encoders; risky under label shift |
| Weak supervision (Snorkel) | labelling functions with known accuracies | our French rules play that role |
| Active learning | a human labels the most useful pairs | the production answer; not allowed on test data here |

## 4. Where we used it

**The failed first attempt** (25–26 Sep; [ANALYSIS_v3 §3](../../experiments/ameya/model-v1/ANALYSIS_v3.md)). India stood in for France (leave-one-country-out, LOCO): a stage-1 model trained on the US, scored on India's holdout, with pseudo-labels at p ≥ 0.97 (and the record's argmax) and p ≤ 0.03.

| India's words | US only | + 1 round | + 2 rounds | + 3 rounds |
|---|---|---|---|---|
| known to the model | 0.96106 | 0.96370 | 0.96479 | |
| unseen, as France's were | 0.88235 | 0.85120 | 0.83075 | 0.82307 |

With India's words unseen, the confident pseudo-positives included look-alikes, and every round taught the model to accept more of them: confirmation bias, measured. We rejected self-training at the v4 decision ([record](../../docs/decisions/2026-09-26_0207_model-v4-france-and-cross-encoder.md)). Sachi's ladder of these rounds kept us cautious to the end.

**Fix the blind spot, then self-train.** The label-free proxy odds give each French word a look-alike score from how often it comes with a moved house number. They lifted the India stand-in from 0.882 to 0.960 (with India's real word odds: 0.961) [M]. With the proxy in place, self-training on the stand-in gained +0.0009 on average over three seeds, small but consistent ([RESEARCH_v6 §4](../../experiments/ameya/model-v1/RESEARCH_v6.md)).

**On France** (Ameya; leaderboard records in [`CHANGELOG.md`](../../CHANGELOG.md)):

| step | what changed | public LB |
|---|---|---|
| round 1, v7nst | stage 2 trained with 1.34M pseudo-labelled French rows from v7ce3's decisions | 0.989721 → **0.990179** (+0.000458); US/India part unchanged within 0.00002, so France about +0.0031 [M]/[E] |
| self-trained cross-encoders, v7sq | e5ls and qst (French pseudo-labels, cross-fitted) in the mix | v7sq-dpc 0.990545; the model change was about +0.00028, mostly confident false French pairs dropped [M]/[E] |
| round 2, guarded and weighted ×3 (mixmdp) | v7sq's decisions as labels, guards, plus the French decision layers | **0.990699**, +0.000154 over v7sq-dpc (France +134e-6) [M] |
| round 3 (mixf7) | mixmdp's decisions as labels | 0.990833, −46e-6 against Composite B; confounded, since B's France also had the French decision layers [M] |
| round 4 | mixqc's decisions as labels | changed 3,553 of 1.43M labels; no gain; not uploaded |

Pseudo-label sizes [M]: round 1 gave 851,116 positive, 493,352 negative and 85,198 unlabelled French stage-2 rows; the v7sq labels on the band gave 74,325 / 273,160 / 37,789.

**What the guards prevented.**
- An unguarded round 2 (v7nst2) dropped clear copies ("Projet & Cie EURL" → "Projet & Compagnie EURL") and added word swaps at the S1's address ("GY Amicale SARL" → "GY Agricole SARL"). It was taken out of the ensemble.
- The round-2 teacher turned about 12.7k empty-address same-name pairs (median 12 S1 per record) from unlabelled into confident negatives, which would have taught that such copies never match. The empty-address guard keeps their round-1 labels.
- Round-2 labels for the cross-encoders drifted (v7sq5g was negative under every valuation); guarded stage-2 labels did not.

**What self-training changed** (v7n → v7nst, RESEARCH_v6 §6.12): it removed 5,484 French predictions, 68% of them one-word swaps at the S1's address, look-alikes just outside op-B's definition; and added 5,955, 31% with an empty record address. French Σ pc per S1 fell from 3.52 to 3.41 ([page 07](07-calibration.md)).

**Why the gains stopped after round 2.**
- Each round's labels are the previous round's decisions. Once the student agrees with its teacher almost everywhere, a new round carries little information: round 4 changed 0.25% of the labels.
- The pairs that still change sit near the threshold, where the teacher is least reliable, so further rounds mainly amplify near-threshold mistakes, which is what the unguarded round 2 did.
- The out-of-distribution ladder above falls with every round.

**Label-free validation.** Each check measures consistency with truths transferred from US/India, not French accuracy itself:

| check | what it showed |
|---|---|
| probability invariants | French Σ pc per S1 3.55 against at most about 3.46: overconfidence ([page 07](07-calibration.md)) |
| rule populations: op-A/APP/ACR 97–99.8% true, op-B 0–1.2% true in US/India | French pc's AUC on them rose 0.855 → 0.865 → 0.872 with the leaderboard; after self-training it saturated at 0.984–0.986, because the pseudo-labels contained those populations: circular |
| the COPY population (`fhs.py`) | true copies (same content words, same or empty address) that no rule decides: still usable after self-training |
| the size-bias test | French acronyms: false share 0.00 [0.00, 0.01], kept; real-word swaps at the address: 0.83 [0.56, 1.10] ([RESEARCH_v6 §6.17](../../experiments/ameya/model-v1/RESEARCH_v6.md)) |
| France-only leaderboard packages | US/India byte-identical, so the score change is the French effect alone |
| adversarial validation | AUC 0.95 exposed unseen words encoded as −1.94e-16 on train but 0.0 on test |
| leakage by third | the 7B adapter trained on two French thirds flags French pairs at the same rate in the third it never saw (0.112% against 0.108% and 0.107%) |

**Hindsight: what we would do with more time.**
1. **Measure France's level directly.** The France-emptied probe (`fr0`) was packaged but never uploaded; every French level we quote is inferred from the leaderboard formula, under the assumption that US/India score on test as on the holdout. For v7sq-dpc (public LB 0.990545), Bakshi showed that this only bounds France to 0.9813–0.9898 [E], while the French gap to the leader, about 0.0087, does not depend on the assumption ([CONFIDENT_SUBSTITUTIONS](../../experiments/bakshi/final-package/CONFIDENT_SUBSTITUTIONS.md)).
2. **In production, a small French labelled sample**, chosen by active learning where the cross-encoders disagree (hand-labelling test data was not an option in the challenge).
3. **Better synthetic French data.** We tried it (Sachi's `synth_fr.py`, Ameya's extensions): the synthetic cross-encoders raised our estimators by reverting leaderboard-confirmed moves; only a bge-based detector proved useful, agreeing with 82% of the French 7B drops. The generator must match France's real operation mix, checked on India-as-France first.
4. **Domain-adversarial cross-encoders**, with care: aligning two domains' inputs can hurt when their class balance differs.
5. **Multi-teacher pseudo-labels:** label a French pair only when the feature models and the 7B agree.

## 5. Why it fits this problem

- France had no labels but plenty of unlabelled pairs (1.43M French stage-2 rows) and a teacher that was right most of the time (France at about 0.97–0.98 by the leaderboard when we started).
- The generator is shared across countries, so the truth rates of its operations transfer, and rules built on them give trusted labels on known populations.
- France's remaining errors were systematic (vocabulary, generic names), the kind that target-domain training can fix once confident errors are kept out of the labels.

## 6. Pitfalls

1. **Confirmation bias**, measured in LOCO (0.882 → 0.823 in three rounds) and seen in the unguarded round 2.
2. **Circular validation:** after self-training, any check built from the pseudo-labels' own populations saturates.
3. **Estimators built from the model's own probabilities share its blind spots** (the `cal` estimator predicted +69e-6 for round 3; the leaderboard said −46e-6).
4. **Too easy pseudo-labels teach nothing, or the wrong thing:** on the India stand-in, rule-labelled positives alone lowered F0.5 by 0.0034, because certain copies taught the model to accept too much.
5. **The holdout cannot see France:** gates only check that US/India do not move, so French decisions rested on a few leaderboard uploads (5 a day) with noise of about ±0.00004 between near-identical candidates.
6. **Pool-size-dependent and unseen features:** rates instead of counts, unseen codes (French legal-form bits), encoding differences between train and test.

## 7. Jury questions with answers

**Q1. How do you know self-training did not reinforce its own mistakes?**
Three defences and an outside check. Rules that are 97–99.8% (or 0–1.2%) true in US/India override the pseudo-labels, empty-address records keep their first-round labels, and no French pair is scored by a model that saw its label. The outside check is the leaderboard: round 1 gave +0.00046 with US/India unchanged, so the gain was French.

**Q2. Self-training failed in your first test and later worked. Why?**
In the first test the model was blind to unseen words, so its confident labels included look-alikes and each round accepted more of them (0.882 → 0.831). The label-free proxy odds fixed that blind spot first (0.882 → 0.960); after that, self-training added a small consistent gain on the stand-in and +0.00046 on France.

**Q3. Why stop after two rounds?**
Round 3 did not beat round 2 on the leaderboard, and round 4 changed only 0.25% of the labels. Later rounds mostly re-learn near-threshold decisions, where the teacher is least reliable, and the out-of-distribution ladder fell with every round.

**Q4. What is cross-fitting, and why by S1?**
French S1 are split into groups; each model learns from the other groups' pseudo-labels and scores only its own group. By S1, so that a model never scores a French pair after learning the labels of that S1's other pairs, the same reason our folds are by S1.

**Q5. What kind of shift is France?**
Mostly covariate shift (new language, legal forms, address formats) with a concept-shift part: patterns that mean "copy" in US/India, like the same name and number on another street, mean "decoy" in France, where names are generic. The test's extra records are a prior shift, but they sit below p1 0.02, outside the candidates.

**Q6. How did you validate France without labels?**
With invariants of the generator (Σ pc per S1, at most one owner per record), populations whose truth rate transfers from US/India, a size-bias test, and leaderboard uploads that changed France alone. We are explicit that these check consistency, not French accuracy.

**Q7. Why counts rather than rates for rivalry features?**
Ambiguity depends on how many S1 a record could belong to, not on the pool size. As rates, France's smaller pool would make its names look 3–4 times more common than anything in train; as counts they mean the same in every country.

**Q8. Isn't training on the test set cheating?**
We used the test records without labels. They are provided data, used the same way as when we fit IDF weights on them. The pseudo-labels are our own predictions; no external data or human labels were used.

**Q9. With more time, what would you do?**
Upload the France-emptied probe to measure France directly; build better synthetic French data; and in production, label a small French sample by active learning where the models disagree.

## 8. Self-test

1. Classify each shift: (a) test has 23% more records per S1 with the same true matches; (b) French legal forms never seen in train; (c) "same name, same number, different street" is a copy in US/India and a decoy in France.
<details><summary>Answer</summary>

(a) Label (prior) shift at the pair level. (b) Covariate shift, with unseen values. (c) Concept shift: P(y | x) differs for the same features.

</details>

2. Why does cross-fitting not protect against a teacher that systematically accepts one kind of look-alike?
<details><summary>Answer</summary>

The same kind of wrong label appears in every group, so each student learns it from the other groups and applies it to its own. Cross-fitting stops memorising specific pairs, not learning a wrong rule. The rules and guards address known wrong rules.

</details>

3. A name is shared by 16 S1 in a pool of 259k, and another by 16 in a pool of 1.32M. Compare the rates and the counts. Which matches the ambiguity a record faces?
<details><summary>Answer</summary>

Rates 6.2e-5 against 1.2e-5, five times apart; counts 16 and 16. A record with that name could belong to 16 S1 in either case, so the count matches its ambiguity.

</details>

4. In the LOCO table, why did self-training help with India's words known but hurt with them unseen?
<details><summary>Answer</summary>

With words known, confident labels were mostly right and taught India's style: small gains. With words unseen, the model was confidently wrong on look-alikes, those errors became labels, and each round made them worse.

</details>

5. Why did the French rule-population AUC stop being useful after self-training?
<details><summary>Answer</summary>

The pseudo-labels included those same populations (the rules' decisions), so a self-trained model scores them well by construction: 0.984–0.986 for every candidate. A usable label-free check needs a population with a transferred truth rate that no rule or label decides.

</details>

6. The size-bias test: if a record is a true copy of S1 x, why are x's other copies size-biased?
<details><summary>Answer</summary>

An S1 with n copies is n times as likely to be the owner of a randomly picked true copy, so the owners of true copies are drawn in proportion to n, and their other copies follow n − 1 under that weighting. An extra (false) record attaches to an S1 regardless of its copy count, so that S1's other copies follow the plain distribution, singletons included. Fitting the mixture gives the false share.

</details>

7. Which of our steps were train-time adaptation, and which adapted only the decision?
<details><summary>Answer</summary>

Train-time: self-training of stage 2 and the cross-encoders, per-country IDF, the proxy odds counted on French pairs. Decision only: the French rules, the French expected-F0.5 decision, the 7B drops.

</details>

## 9. Further reading

- Scudder (1965). Probability of error of some adaptive pattern-recognition machines.
- Yarowsky (1995). Unsupervised word sense disambiguation rivaling supervised methods.
- Blum and Mitchell (1998). Combining labeled and unlabeled data with co-training.
- Lee (2013). Pseudo-label: the simple and efficient semi-supervised learning method for deep neural networks.
- Arazo, Ortego, Albert, O'Connor and McGuinness (2020). Pseudo-labeling and confirmation bias in deep semi-supervised learning.
- Xie, Luong, Hovy and Le (2020). Self-training with Noisy Student improves ImageNet classification.
- Sohn et al. (2020). FixMatch: simplifying semi-supervised learning with consistency and confidence.
- Chernozhukov et al. (2018). Double/debiased machine learning for treatment and structural parameters.
- Shimodaira (2000). Improving predictive inference under covariate shift by weighting the log-likelihood function.
- Saerens, Latinne and Decaestecker (2002). Adjusting the outputs of a classifier to new a priori probabilities: a simple procedure.
- Lipton, Wang and Smola (2018). Detecting and correcting for label shift with black box predictors.
- Quiñonero-Candela, Sugiyama, Schwaighofer and Lawrence (2009). Dataset Shift in Machine Learning.
- Moreno-Torres et al. (2012). A unifying view on dataset shift in classification.
- Ganin et al. (2016). Domain-adversarial training of neural networks.
- Ratner et al. (2017). Snorkel: rapid training data creation with weak supervision.
- Wang et al. (2021). Tent: fully test-time adaptation by entropy minimization.
- Garg et al. (2022). Leveraging unlabeled data to predict out-of-distribution performance.
- Settles (2009). Active learning literature survey.
