# F10. Semi-supervised learning and domain shift: learning where you have no labels

**Summary.**
- Train and test data differ. The test set has more look-alike records, and France has no labels at all. "Shift" is the name for the gap between the data a model learned from and the data it is used on.
- We narrowed the French gap with label-free fixes (proxy word odds, counts instead of rates), self-training on our own guarded decisions (two rounds helped, a third did not) and an independent 7B reader for the confident mistakes that self-training cannot see.
- Any estimate built from the model's own probabilities shares the model's blind spots. Our round-3 forecast was +0.000069 and the leaderboard said −0.000046.

About 2.5 hours with the exercises. Prepares you for the advanced page [09 self-training and domain shift][adv09], and for [F11][f11], [F12][f12] and [F16][f16].

---

## 1. What you need first

- [F02][f02]: conditional probability, Bayes' rule, odds and log-odds.
- [F03][f03]: training, validation, overfitting. [F04][f04]: calibration (a probability of 0.9 should be right 90% of the time).
- [F09][f09]: the local holdout, controls and evidence levels. In short: **M** measured, **E** estimated, **R** reported (not re-checked here), **U** uncertain; "toy" is invented for practice. "Local holdout" is the fixed 25% of labelled US/India S1 (549,699 S1, no France); "public LB" is the leaderboard during the challenge.

---

## 2. The concepts from zero

### 2.1 Shift: three kinds and an unseen domain

**Intuition.** A model learns patterns from its training data and assumes the future looks the same. When it does not, the patterns can fail without any warning, because the model still reports confident probabilities.

**Definition.** Let x be everything we know about a pair of records and y be 1 for a match and 0 otherwise. Write P_S(x, y) for the source (training) data and P_T(x, y) for the target (test) data. Since P(x, y) = P(y | x) P(x) = P(x | y) P(y), three things can move:

| shift | what changes | our example | textbook fix |
|---|---|---|---|
| covariate | P(x), the inputs; P(y given x) stays | French words, legal forms (SARL, SAS), department names in 32% of French addresses, generic names [M] | importance weights P_T(x) / P_S(x); new features; adaptation |
| prior (label) | P(y), the base rate; P(x given y) stays | the test has 5.75 S2/S3 records per S1 against 4.68 in train (+23%), with the same true matches per S1 [M] | shift the log-odds by the log prior ratio |
| concept | P(y given x), the rule itself | "same name, same house number, different street" is 99.7% true among US/India predictions but mostly a decoy in France | needs target labels or an independent reader |
| unseen domain | no target labels at all | France | proxies, self-training, rules |

Sources: [09 section 2.1][adv09], [methodology doc][doc]. A concept shift can hide between two labelled countries too. The population of pairs whose house number is lower by 1 or 2 (one of the groups our French rules looked at) is a true match 97.6% of the time in the US and 78.2% in India [M] ([decision][d-rules2]).

**Worked example (prior shift, toy).** Say the share of true pairs among candidates falls from 10% to 8%. A pair that the model scores 0.50 should now score lower, because matches are rarer:

```
odds_T  = odds_S x [ 0.08 / 0.92 ] / [ 0.10 / 0.90 ]
        = 1.0 x 0.783 = 0.783   ->   probability 0.439
log-odds change = ln(0.783) = -0.245
```

In our data the extra records sit below stage-1 probability 0.02, so the candidate sets are not affected and the prior shift did not reach the decision [M] ([09][adv09]). The shifts our decision layer does use (+0.2, then −0.3 for crowded records) are tuned on the holdout. They are not derived from a prior ratio.

**Worked example (covariate shift: counts, not rates).** A name shared by 16 S1 is as ambiguous among France's 259k S1 as among the 1.32M US training S1. As rates (16 divided by the pool) the two differ by a factor of 5, and French rates would look unlike anything in training. As counts they match. So our rival features are counts, stored as log1p(count) ([09 section 2.5][adv09]). The fix for a covariate shift was often to choose features that do not move with the shift.

**Worked example (importance weighting, used once, to read the holdout).** To estimate how a model would score on the test, re-weight the holdout S1 so their mix matches the test's mix. If name groups of size 1, 2 and 3 or more are 50%, 30% and 20% of the holdout but 60%, 25% and 15% of the test (toy), the weights are 0.60 / 0.50 = 1.2, 0.25 / 0.30 = 0.83 and 0.15 / 0.20 = 0.75. We did this with the holdout's name-group sizes: it raised the US/India estimate by about +0.0004, because the US test pool is half the size of the train pool and fewer names collide [M] ([05 section 2.9][adv05]). Weighting changes how we read the holdout. It does not change the model.

### 2.2 Leave-one-country-out (LOCO): a stand-in for an unseen country

**Intuition.** We could not measure France, so we made a country unseen on purpose. Train on the US only, then score India as if it had no labels. India is not France, but the mistake is of the same kind.

**Definition.** Train on all labelled countries but one, score the held-out country, and compare with a model that saw it.

**Worked example.** The numbers are macro F0.5 on India's holdout [M] ([decision][d-v4]; [05][adv05]).

| model trained on the US only | India F0.5 |
|---|---|
| India's words known to the model (an upper bound) | 0.96106 |
| India's words unseen, as France's were | 0.88235 |
| unseen words plus label-free proxy odds | 0.95984 |
| trained on both countries | 0.98346 |

Unseen words cost 0.0787. The proxy recovered 0.0775 of it, 98.5% [E, arithmetic]. The remaining 0.0236 to the both-country model is the price of having no labels in the target. The **proxy odds** work like this: each word gets a look-alike score from how often it appears with a moved house number, counted on the unlabelled target pool. That needs no labels. On 26 Sep, before the next upload, this stand-in forecast France at about 0.97 [E]; the leaderboard arithmetic for that upload then gave 0.971 to 0.976 [E] ([F12][f12]).

### 2.3 Semi-supervised learning and self-training

**Intuition.** Unlabelled data is cheap. Semi-supervised methods use it to learn where the inputs live. **Self-training** is the simplest: a **teacher** model labels the unlabelled data, we keep only the labels it is confident about (the **pseudo-labels**), and a **student** model trains on real labels plus pseudo-labels. Then the student can become the next teacher.

**Definition.** With a teacher f and thresholds t_plus > t_minus:

```
pseudo-label(x) = 1            if f(x) >= t_plus
                  0            if f(x) <= t_minus
                  unlabelled   otherwise
student = train( labelled data + { (x, pseudo-label(x)) } )
```

It can work for two reasons. The student sees the target domain's inputs, such as French vocabulary, even if some labels are wrong. And confident labels pull the decision boundary into the low-density gap between clusters. It fails when confident labels are wrong in a systematic way (section 2.4).

**Other families.** Co-training uses two different views of the data that label for each other; our rules and our models are two such views. Consistency methods ask that a small change to an input does not change the prediction. Entropy minimisation pushes the model to be decisive on unlabelled data. Label propagation spreads labels along a similarity graph. All of them assume that close points share a label and that the boundary should fall in a sparse region. That assumption is false for look-alikes, which are close in text and different in label. There semi-supervised learning amplifies the mistake, and an outside reader is needed.

**Our version** ([09 section 2.2][adv09]):
- Labels follow the teacher's final decisions, not raw scores. Positive: the teacher kept the pair with calibrated probability pc of at least 0.9 (or a French rule or the acronym join added it). Negative: the teacher dropped it with pc of at most 0.05. Everything between stays unlabelled but is still scored.
- The thresholds are not symmetric, and the records give no reason or sweep for 0.9 against 0.05 (U). Do not invent one.
- Round 1 used 851,116 positive, 493,352 negative and 85,198 unlabelled French stage-2 rows [M]. The students were stage 2 and the cross-encoders (e5, bge, Qwen). That labelled 94% of the 1,429,666 rows (59.5% positive, 34.5% negative, 6.0% unlabelled) [E, arithmetic]. Most candidate pairs are far from both thresholds, so the thresholds were not very selective.

**Why calibration matters.** A threshold of 0.9 means "at most 10% of these labels are wrong" only if the probabilities are calibrated in the target domain. If the mean pc of 1,000 pseudo-positives is 0.95, the expected number of wrong labels is 50 (5%). In France the probabilities were overconfident: the expected number of copies per S1 summed to 3.55, while the truth is at most about 3.46 [M] ([05][adv05]; [07 calibration][adv07]). So the real noise was higher than the thresholds suggest.

### 2.4 Confirmation bias and guards

**Intuition.** If a student learns its teacher's mistakes as facts, and the next teacher is that student, mistakes grow. Random errors average out. Systematic errors, tied to a feature such as an unseen word, are learned as rules.

**Worked example (measured).** Sachi's LOCO ladder repeated self-training rounds on the India stand-in, with pseudo-labels at p of at least 0.97 and at most 0.03 [M] ([09 section 4][adv09]):

| India's words | no rounds | round 1 | round 2 | round 3 |
|---|---|---|---|---|
| known to the model | 0.96106 | 0.96370 | 0.96479 | |
| unseen, as France's were | 0.88235 | 0.85120 | 0.83075 | 0.82307 |

The same algorithm helped when the teacher knew the words (+0.00264, then +0.00109) and hurt when it did not (−0.03115, −0.02045, −0.00768). With unseen words the confident positives included look-alikes, and each round taught the model to accept more of them. We rejected self-training at the v4 decision. Later we fixed the blind spot first: with proxy odds the stand-in rose from 0.882 to 0.960, and self-training then gained +0.0009 on average over three seeds, small but consistent.

**Our guards for France.** From round 2 ([09][adv09]):
- Where our hand-written rules decided a population (look-alikes to drop, copies to keep), the rules override the teacher's label.
- Empty-address pairs keep their round-1 labels.
- Labels are cross-fitted (section 2.5).
- The 7B reader looks from outside the loop (see [10][adv10]).

What they prevented: an unguarded round 2 dropped clear copies ("Projet & Cie EURL" against "Projet & Compagnie EURL") and added word swaps at an S1's address, and it turned about 12.7k empty-address same-name pairs from unlabelled into confident negatives, which would have taught that such copies never match [M]. The records show what each guard prevented; why it works is an interpretation (E).

### 2.5 Cross-fitting by S1 group

**Intuition.** A student must not grade its own homework. If a model trained on a pair's pseudo-label also scores that pair, it only repeats itself.

**Definition.** Split the French S1 into k groups. For group g, train a model on the labelled US/India rows plus the pseudo-labels of the other groups, and use that model alone to score group g's pairs. We used three groups for the cross-encoders and four for stage 2.

**Worked example.** Groups A, B, C. The model that scores group B saw the labels of A and C and never those of B. Splitting by S1, not by pair, matters because the pairs of one S1 share names and addresses: a model that learned (S1 x, record 1) would recognise (S1 x, record 2). Bakshi checked the effect on the 7B reader: it rejected 0.112% of French predictions in the third of S1 its adapter never trained on, against 0.108% and 0.107% in the others [M]. Cross-fitting stops memorisation. It does not remove systematic teacher errors, because the same mistake sits in every group.

### 2.6 Why the gains stopped after two rounds

**Table 1. French self-training on the public LB** ([09][adv09], [CHANGELOG][changelog]; all [M] unless marked).

| round | what changed | public LB | note |
|---|---|---|---|
| 1 (v7nst) | stage 2 trained on 1.34M pseudo-labelled French rows | 0.989721 to 0.990179, +0.000458 | US/India part unchanged within 0.00002, so France about +0.0031 [E] |
| 2 (mixmdp) | guarded labels, weight ×3, plus the French decision layers | 0.990699, +0.000154 over v7sq-dpc | France +134e-6 |
| 3 (mixf7) | round-3 labels | 0.990833, −0.000046 against Composite B | forecast +0.000069; confounded, see below |
| 4 | next round of labels | not uploaded | changed 3,553 of 1.43M labels (0.25%) |

The reasons, from the records ([09][adv09]), with the interpretation marked (E):
- Each round's labels are the previous round's decisions. Once student and teacher agree almost everywhere, a new round carries little information (round 4: 0.25% changed).
- The labels that still change sit near the threshold, where the teacher is least reliable, so more rounds amplify near-threshold mistakes.
- Self-training fixes what the model is unsure about. It cannot fix what the model is sure about. Our worst French errors were confident decoys.

The round-3 comparison is confounded: Composite B's France also had the French decision layers and mixf7's did not. So −46e-6 is not round 3 alone. The honest summary: two rounds helped, a third did not add to them.

### 2.7 Label-free diagnostics and their limits

**Intuition.** Without labels you can still ask whether the model behaves as the world must. The risk is that the judge is the model itself.

**Table 2. Label-free checks we used** ([05 section 2.8][adv05], [09 section 4][adv09]).

| check | what it showed | its limit |
|---|---|---|
| expected copies per S1 (sum of pc) | US/India holdout 3.4320 against truth 3.4323; France 3.5456, so overconfident [M] | finds excess mass, not which pairs are wrong |
| adversarial validation (train a classifier to tell train from test records) | AUC 0.95 exposed an encoding bug: unseen words were −1.94e-16 in train and 0.0 in test | finds shift in x, not in P(y given x) |
| France-only uploads | US/India identical, so the change is French alone | few uploads per day |
| reject rate by third (7B) | 0.112% against 0.108% and 0.107% | shows no memorisation, not correctness |
| independent detector (bge on US/India labels plus synthetic French, no self-training labels) | flagged 708 of the 859 French 7B rejects, 82% [M] | agreement, not proof |
| the model's own expected F | v3 forecast France at 0.970; the leaderboard implied 0.925 to 0.931 [M] | shares the model's blind spots |
| rule-population AUC | rose 0.855 to 0.865 with the leaderboard, then saturated at 0.984 to 0.986 after self-training | circular: the pseudo-labels contained those populations |

**The limit in one example.** Before the round-3 upload our `cal` estimator, built from the model's calibrated probabilities, forecast +69e-6. The leaderboard measured −46e-6. The error was 115e-6, and the sign was wrong. The estimator and the labels came from the same model, so it could not see the decoys the model accepted. By contrast, the forecast for the 7B parts of Composite B (+149e-6 against +180e-6 measured) was close. Those parts rested on a different kind of reader, the 7B, and on rules fixed on labelled data first (an interpretation, E). The lesson is independence: a check is only as good as how differently it errs.

**Why the sum of probabilities is a good check.** If probabilities are calibrated, the sum over an S1's candidates estimates its number of true copies, and the probabilities of one record across S1 sum to at most 1 (a record has at most one owner). On the US/India holdout the sum matched the truth to four digits. On France it was 2.5% too high, (3.5456 − 3.46) / 3.46, where 3.46 is the train average that we assume holds in France [E, arithmetic]. That says the French probabilities are inflated on average. It does not say which pairs.

**An experiment we planned and never ran.** Upload the same file with every French prediction removed (the France-emptied probe). An empty prediction scores 1 on a French S1 with no copies (about 5.59% of them) and 0 on all others, so the leaderboard would read about 0.8433 + 0.14975 × 0.0559 = 0.8517 if US/India score as we assume [E] ([05, self-test 5][adv05]). A different reading would measure US/India on the test directly, and the real upload would then give France. We packaged this probe several times and never uploaded it; label-free checks and leaderboard arithmetic stood in.

**Unlabelled test data without labels.** Per-country IDF weights are fitted on train and test text together. They use no labels, so they are not leakage. We never updated model weights at test time; the French rules, the French decision layer and the 7B drops adapt the decision instead ([09 section 2.6][adv09]).

---

## 3. How it shows up in our project

| when | what happened | where to read more |
|---|---|---|
| 25 Sep | first leaderboard checks: v2 at 0.97608 against 0.98436 on the holdout; v3 at 0.97961 against 0.98882; France implied at about 0.93 [E] | [F12][f12] |
| 26 Sep | LOCO anatomy; proxy odds; French legal-form bitmasks dropped; first self-training attempt rejected | [decision v4][d-v4] |
| 26 Sep, late | round 1 works: +0.000458 on the leaderboard | [LB 26 Sep #04][lb-s04] |
| 27 Sep | guards; round 2; round 3 fails; the 7B re-check removes 840 French predictions | [09][adv09], [10][adv10] |
| 29 Sep | methodology: "self-training helped for two rounds" | [methodology doc][doc] |

**Hindsight, from the advanced page.** With more time we would measure France directly with an early France-emptied upload, add multi-teacher labels (label a French pair only when the feature models and the 7B agree), and use active learning where the cross-encoders disagree. Hand-labelling test data was not allowed in the challenge ([09][adv09]; see [F16][f16]).

---

## 4. How to read the numbers

| you see | read it as |
|---|---|
| 0.88235 to 0.82307 over three rounds | a loss of 0.0593 in India-as-France: confirmation bias, measured |
| +0.00264 then +0.00109 | gains that shrink every round even when self-training helps |
| +0.000458 on the LB | mostly France: 0.000458 / 0.14975 = +0.0031 on the French score if US/India did not move |
| 3.55 copies per S1 | the model's probabilities sum to more than the world allows (about 3.46) |
| forecast +69e-6, measured −46e-6 | a label-free estimator that shared the model's blind spots |

On the public LB a French change counts for 0.14975 of itself: +0.001 on France is +0.00015.

---

## 5. Common misconceptions

1. **"Self-training adds information."** It adds no new labels. It spreads the teacher's knowledge to inputs the teacher had not seen, which helps only if the teacher is mostly right.
2. **"More rounds are better."** Our ladder fell with each round, and the good France rounds saturated after two.
3. **"A confident prediction is a correct one."** Only if calibrated in that domain. In France, confident decoys sat above 0.99.
4. **"If the holdout is fine the test is fine."** The holdout cannot contain a country that has no labels.
5. **"A domain classifier with AUC 0.5 proves no shift."** It checks inputs only. A concept shift leaves P(x) alone.
6. **"Check the student with the pseudo-labels."** That is circular: the rule-population AUC saturated for exactly this reason.
7. **"Shift means the model is bad."** It means the data moved. A good model on moved data still needs a check.

---

## 6. Check yourself

**1.** Name the shift: (a) French names carry SARL and SAS; (b) the test has 23% more records per S1 with the same true matches; (c) the same kind of pair (house number lower by 1 or 2) is 97.6% true in the US and 78.2% in India; (d) a new country has no labels.

<details><summary>Answer</summary>

(a) covariate. (b) prior (label) shift in the pool; here the extras sit below p1 0.02, so candidates were unaffected. (c) concept shift between two labelled countries. (d) an unseen domain.

</details>

**2.** The share of true pairs falls from 10% to 8%. A model says 0.9 for a pair. What is the corrected probability?

<details><summary>Answer</summary>

Odds 9 × 0.783 = 7.05, probability 7.05 / 8.05 = 0.876. The correction is small at 0.9 and larger near 0.5 (0.50 becomes 0.439).

</details>

**3.** Using the LOCO table, compute the loss from unseen words, the share the proxy recovered, and the gap that remains.

<details><summary>Answer</summary>

Loss 0.96106 − 0.88235 = 0.0787. Recovered 0.95984 − 0.88235 = 0.0775, which is 98.5%. Remaining gap to the both-country model: 0.98346 − 0.95984 = 0.0236.

</details>

**4.** In the ladder, why did the same algorithm gain with known words and lose with unseen words?

<details><summary>Answer</summary>

With known words the teacher's confident labels are mostly right, so the student learns real structure of the target (+0.00264, +0.00109). With unseen words the teacher cannot tell look-alikes from copies, so its confident positives include look-alikes. The student learns to accept them, and the next teacher is more sure of the wrong thing (−0.03115, −0.02045, −0.00768).

</details>

**5.** 1,000 pseudo-positives average pc = 0.95, and 1,000 pseudo-negatives average pc = 0.02. How many labels are wrong if pc is calibrated? And if the positives are really 85% right and the negatives 95% right?

<details><summary>Answer</summary>

Calibrated: 50 + 20 = 70 of 2,000, which is 3.5%. Overconfident: 150 + 50 = 200, which is 10%. The thresholds only bound the noise when the probabilities are calibrated in the target domain, which France was not.

</details>

**6.** Three groups A, B, C. Which labels does the model that scores group B train on? Why group by S1?

<details><summary>Answer</summary>

The labelled US/India rows plus the pseudo-labels of A and C. By S1 because the pairs of one S1 share names and addresses; a model that had seen (S1 x, record 1) would recognise (S1 x, record 2) and look better than it is.

</details>

**7.** Round 3 was forecast at +69e-6 and measured −46e-6. Give the error and two reasons the comparison is unreliable.

<details><summary>Answer</summary>

Error −46 − 69 = −115e-6, and the sign is wrong. First, the estimator uses the model's own probabilities and shares its blind spots on decoys. Second, mixf7 differs from Composite B in two ways: the round-3 labels, and the absence of the French decision layers. So the −46e-6 is not round 3 alone.

</details>

**8.** Match each guard to the failure it addresses: rules override the teacher; empty-address pairs keep their round-1 labels; cross-fitting by S1 group; the 7B re-check.

<details><summary>Answer</summary>

Rules override: the teacher's systematic errors on populations whose truth rate we know. Empty-address pairs: confident negatives for copies that really do match (about 12.7k pairs). Cross-fitting: a model scoring its own labels and memorising them. The 7B re-check: confident decoys that every feature model accepts, which self-training cannot see because the loop only sees its own outputs.

</details>

**9.** Round 1 moved France by about +0.0031 and left US/India unchanged. By how much did the LB move?

<details><summary>Answer</summary>

0.14975 × 0.0031 = +0.000464. The upload showed +0.000458 [M], so the French estimate is consistent.

</details>

**10.** Why does the rule-population AUC stop being useful once a model is self-trained? Suggest a check that stays independent.

<details><summary>Answer</summary>

The populations are part of the pseudo-labels, so the model is scored on what it learned from, and the AUC saturates (0.984 to 0.986). An independent check must differ from the model: the 7B reader's rejection rate, a detector trained on other data, the sum of probabilities against the truth, or a leaderboard upload that changes France alone.

</details>

---

## 7. Going deeper

- [09 self-training and domain shift][adv09]: the full story, with the guard failures and the jury questions. [05 evaluation][adv05] section 2.8 for the label-free checks. [07 calibration][adv07] for France's overconfidence. [10 LLM verification][adv10] for the independent reader.
- Quiñonero-Candela, Sugiyama, Schwaighofer and Lawrence (2009), "Dataset Shift in Machine Learning", MIT Press.
- Shimodaira (2000), "Improving predictive inference under covariate shift by weighting the log-likelihood function", Journal of Statistical Planning and Inference. Saerens, Latinne and Decaestecker (2002), "Adjusting the outputs of a classifier to new a priori probabilities", Neural Computation. Lipton, Wang and Smola (2018), "Detecting and correcting for label shift with black box predictors", ICML.
- Ben-David et al. (2010), "A theory of learning from different domains", Machine Learning.
- Lee (2013), "Pseudo-Label: the simple and efficient semi-supervised learning method for deep neural networks", ICML workshop. Arazo et al. (2020), "Pseudo-labeling and confirmation bias in deep semi-supervised learning", IJCNN. Chapelle, Schölkopf and Zien (2006), "Semi-Supervised Learning", MIT Press.

## 8. Where next

- [F11 Decision theory and optimisation][f11]: what to do with the probabilities once you have them.
- [F12 Interpreting our results][f12]: the France levels, step by step.
- [F16 Learning with limited labels][f16]: transfer, zero-shot, active learning, weak supervision and synthetic data.
- The track map: [foundations README](README.md).

[doc]: ../../../experiments/ameya/final-zip/doc/Documentation_template.md
[changelog]: ../../../CHANGELOG.md
[adv05]: ../05-evaluation-methodology.md
[adv07]: ../07-calibration.md
[adv09]: ../09-self-training-and-domain-shift.md
[adv10]: ../10-llm-verification-and-compute.md
[f02]: F02-probability-and-statistics.md
[f03]: F03-machine-learning-fundamentals.md
[f04]: F04-classification-metrics.md
[f09]: F09-experiments-and-evidence.md
[f11]: F11-decision-theory-and-optimisation.md
[f12]: F12-interpreting-our-results.md
[f16]: F16-learning-with-limited-labels.md
[d-v4]: ../../../docs/decisions/2026-09-26_0207_model-v4-france-and-cross-encoder.md
[d-rules2]: ../../../docs/decisions/2026-09-26_0626_france-rules-v2.md
[lb-s04]: ../../../submissions/records/2026-09-26_sub04.md
