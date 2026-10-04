# F04. Classification metrics: how to read every number we report

**Summary.**
- A metric is a question you ask of a classifier. This page builds the confusion matrix, precision, recall, F1 and F-beta from scratch, derives why F0.5 favours precision and its count form (one false merge weighs as much as four missed copies), and shows how our per-S1 macro average treats singletons.
- It then covers thresholds, ROC and AUC (what the 0.944 means and does not), PR curves, calibration curves, blocking metrics and per-country breakdowns.
- The goal: for every number we report you can say what it measures, on which data, and what it does not tell you.

Tier P1. About 2.5 hours in full, about 1.25 hours on the fast path (sections 2.5 to 2.8, 2.11 and 2.12). Prepares you for the advanced pages [04 metrics and decisions][adv04], [07 calibration][adv07], [02 blocking][adv02], [08 cross-encoders][adv08] and [05 evaluation][adv05].

---

## 1. What you need first

[F01][f01] for the vocabulary, and [F02][f02] sections 2.1 (probability) and 2.3 (odds) for the calibration part. Evidence levels: **M** measured, **E** estimated or derived, **R** reported. "Local holdout" is the fixed 25% of labelled US/India S1 (549,699 S1); "public LB" is the leaderboard during the challenge. "Toy" means made-up numbers for practice.

---

## 2. The concepts from zero

### 2.1 The confusion matrix

For a yes/no decision there are four outcomes. Take "this pair is a match" as the positive class.

| | truth: match | truth: not a match |
|---|---|---|
| we say match | **TP** true positive (a correct merge) | **FP** false positive (a false merge) |
| we say no match | **FN** false negative (a missed copy) | **TN** true negative |

**Worked example.** S1 "Acme Robotics Inc" has two true copies, A and B. We predict A and C. Then TP = 1 (A), FP = 1 (C, a false merge), FN = 1 (B, a missed copy). TN is every other S2/S3 record that we correctly left alone: millions of them, which is why TN is useless for our metric. We count TP, FP and FN **per S1** and over the predicted set, not over all pairs.

### 2.2 Accuracy, and why it fails here

`accuracy = (TP + TN) / (all pairs)`. Because TN is enormous, accuracy is close to 1 for a system that does nothing. On the 58,437,794 retrieved test pairs, about 5.94 million are true [E], so "say no to everything" is 89.8% accurate. Over all within-country pairs (about 6.7e12 [E]) it is 99.99991% accurate. Both find zero copies. Use measures that do not contain TN.

### 2.3 Precision and recall

```
precision = TP / (TP + FP)        of what we predicted, how much is right
recall    = TP / (TP + FN)        of what exists, how much we found
```

Two companions: the **false positive rate** `FP / (FP + TN)` and the **specificity** `TN / (TN + FP)`. Precision is undefined when we predict nothing (0 / 0). In our metric an empty prediction is handled by explicit rules (section 2.6).

**Worked example.** The official statement's example: we predict S2-00047, S2-00193, S3-00812; the truth is S2-00047, S3-00812. TP = 2, FP = 1, FN = 0, so precision = 2/3 and recall = 1. The one false merge cost us a third of the precision.

### 2.4 F1 and the harmonic mean

We want one number that is high only when both precision P and recall R are high. The arithmetic mean fails: predicting everything gives R = 1 and a tiny P, yet a mean of about 0.5. The **harmonic mean** `2PR / (P + R)` is dominated by the smaller number. With P = 0.01 and R = 1: arithmetic mean 0.505, harmonic mean 0.0198. This is **F1**. In counts it is `2 TP / (2 TP + FP + FN)`.

### 2.5 F-beta, F0.5, and the count form

**Definition.** F-beta is a weighted harmonic mean:

```
F_beta = (1 + beta²) × P × R / (beta² × P + R)
equivalently  1 / F_beta = alpha / P + (1 - alpha) / R,   alpha = 1 / (1 + beta²)
```

For beta = 0.5, alpha = 0.8, so `1 / F = 0.8 / P + 0.2 / R`: precision gets weight 0.8 and recall 0.2. This is the formula in the [problem statement][task], `F0.5 = 1.25 × P × R / (0.25 × P + R)`.

**Derivation of the count form.** Substitute `P = TP / (TP + FP)` and `R = TP / (TP + FN)`:

```
P × R             = TP² / ((TP + FP)(TP + FN))
beta² P + R       = TP × [ beta² (TP + FN) + (TP + FP) ] / ((TP + FP)(TP + FN))
F_beta            = (1 + beta²) × TP / ( (1 + beta²) × TP + beta² × FN + FP )
```

For beta = 0.5:

```
F0.5 = 1.25 × TP / (1.25 × TP + 0.25 × FN + FP)
```

Since `TP + FN = T` (the number of true copies) and `TP + FP = k` (the number we predicted), this is also `F0.5 = 1.25 × TP / (0.25 × T + k)`, the form used in [`ber.eval.metric`][metric].

**Reading it.** A false positive adds 1 to the denominator and a false negative adds 0.25. So in the count form **one false merge weighs as much as four missed copies**. You will also see "F0.5 weights precision twice as much as recall" (the official statement says so). That is shorthand. With beta = 0.5, a small gain in precision and a small gain in recall are worth the same at the point `R = 0.5 × P`, where precision counts twice as much as recall. The exchange rate in the error counts is 4 to 1, and at P = R a one-point gain in precision is worth about four points of recall: from P = R = 0.90, +0.01 precision raises F0.5 by 0.0080 and +0.01 recall by 0.0020.

**What an error really costs.** The weight 4 is for the error terms at a fixed number of hits. A real miss also removes a hit. For an S1 with t true copies that is otherwise perfect, directly from the formula:

```
cost of one miss        = 0.25 / (1.25 t - 1)
cost of one false merge = 1 / (1.25 t + 1)
ratio (false merge / miss) = 4 (1.25 t - 1) / (1.25 t + 1)
```

| t (true copies) | 1 | 2 | 3 | 4 | 5 | many |
|---|---|---|---|---|---|---|
| cost of a miss | 1.000 | 0.167 | 0.091 | 0.063 | 0.048 | to 0 |
| cost of a false merge | 0.444 | 0.286 | 0.211 | 0.167 | 0.138 | to 0 |
| ratio | 0.44 | 1.7 | 2.3 | 2.7 | 2.9 | to 4 |

At our mean of 3.46 copies the ratio is 2.5. So a false merge costs 2 to 3 times a miss at typical sizes and approaches 4 for large sets. Two exceptions matter: for t = 1 a miss costs more (the S1 scores 0), and for a singleton any prediction costs the full 1.0 ([metrics page 2.2][adv04]).

### 2.6 One S1, many S1: singletons, macro and micro

**Per S1.** With true set T, predicted set P and c = |P ∩ T| correct predictions ([`ber.eval.metric`][metric]):

```
F0.5 = 1.25 × c / (0.25 × |T| + |P|)
if T is empty:  F = 1 if P is empty, else 0          (singletons)
if P is empty and T is not:  F = 0
```

**Macro versus micro.** The competition score is the **macro** average: compute F0.5 per S1 and average over all S1, singletons included. **Micro** pools the counts of all S1 first. Macro gives every S1 the same weight, so a small S1 is worth as much as a large one and a singleton is worth 5.6% of the score in total.

**Worked example (toy).** Five S1:

| S1 | true copies | we predict | F0.5 |
|---|---|---|---|
| a | 2 | exactly the two | 1.000 |
| b | 1 | the true one plus one wrong | 1.25 / (0.25 + 2) = 0.556 |
| c | 0 (singleton) | nothing | 1.000 |
| d | 0 (singleton) | one record | 0.000 |
| e | 3 | one of the three | 1.25 / (0.75 + 1) = 0.714 |

Macro = (1 + 0.556 + 1 + 0 + 0.714) / 5 = 0.654. Micro pools TP = 4, T = 6, k = 6: 1.25 × 4 / (1.5 + 6) = 0.667. They differ because macro punishes the singleton failure d at full weight.

**Macro F is not F of the averages.** Our final local-holdout predictions have precision 99.9% and recall 97.5% [M] ([scaling page 2.1][adv11]). Putting those into the P-R formula gives 0.9941, but the macro F0.5 is 0.9913 [M]. Averaging F over S1 is not the same as averaging P and R first, and we cannot tell from the documents whether 99.9% and 97.5% are pooled or averaged per S1. Never recompute a macro score from P and R.

### 2.7 Thresholds and the precision–recall trade-off

A classifier gives a score; a **threshold** τ turns it into yes/no. Lowering τ adds predictions: recall can only rise, precision usually falls. Sweeping τ traces the trade-off.

**Worked example (toy).** Seven pairs for one S1 with scores: true pairs 0.95, 0.80, 0.60 (so T = 3) and false pairs 0.90, 0.40, 0.30, 0.20.

| τ | predicted k | TP | FP | FN | P | R | F1 | F0.5 |
|---|---|---|---|---|---|---|---|---|
| 0.95 | 1 | 1 | 0 | 2 | 1.00 | 0.33 | 0.50 | 0.714 |
| 0.90 | 2 | 1 | 1 | 2 | 0.50 | 0.33 | 0.40 | 0.455 |
| 0.80 | 3 | 2 | 1 | 1 | 0.67 | 0.67 | 0.67 | 0.667 |
| 0.60 | 4 | 3 | 1 | 0 | 0.75 | 1.00 | 0.86 | **0.789** |
| 0.40 | 5 | 3 | 2 | 0 | 0.60 | 1.00 | 0.75 | 0.652 |

The best τ for F0.5 is 0.60. Note how the score is not monotone in τ.

**When is adding a candidate worth it?** Add a candidate of probability p to a set. Expected hits rise by p and the predicted count by 1. F0.5 = 1.25 TP / (0.25 T + k) improves when `(TP + p) / (0.25 T + k + 1) > TP / (0.25 T + k)`, which simplifies to

```
p > TP / (0.25 T + k) = F0.5 / 1.25 = 0.8 × F0.5       (break-even probability)
```

For F0.5 near 0.94 this is 0.75, which is the "75%" in our methodology; for F0.5 = 0.9913 it is 0.793. For an S1 that already has m sure pairs and nothing else missing, the exact figure is `p* = (1.25 m + 0.25) / (1.5625 m + 0.5)`:

| sure pairs already in the set, m | 0 | 1 | 2 | 3 | 10 | many |
|---|---|---|---|---|---|---|
| break-even p* | 0.50 | 0.73 | 0.76 | 0.77 | 0.79 | 0.80 |

So the first candidate for an S1 needs only 0.5: with nothing predicted yet, an empty answer scores 0 if the candidate is a true copy and 1 if it is not, so the gain and the loss are equal. Later candidates need about 0.75 to 0.80. The threshold depends on the S1, which is why a single global threshold lost to the per-S1 set selection ([metrics page 2.8][adv04], [F11][f11]). It is also why none of the recall rules we tried (at most 71% precise) was added.

### 2.8 ROC curve and AUC

The **ROC curve** plots the true positive rate (recall) against the false positive rate as τ sweeps. The **AUC** (area under the curve) has a direct meaning:

```
AUC = P( score of a random true pair > score of a random false pair )      (ties count half)
```

0.5 is chance, 1.0 is a perfect ranking. In the toy above, the true scores 0.95, 0.80, 0.60 against the false scores 0.90, 0.40, 0.30, 0.20 give 10 of 12 ordered pairs correct: **AUC = 0.833**.

**Properties.** AUC needs no threshold. It uses only the ranking, so it is unchanged by any monotone rescaling and says nothing about calibration. Each rate is normalised within its own class, so it ignores class balance, and a model can have a high AUC and poor precision when positives are rare.

**What 0.944 means.** We compare cross-encoders by **band AUC**: the AUC on labelled holdout pairs whose stage-1 probability lies in the uncertain band 0.02 to 0.99. The 7B model and a self-trained e5-large both reach 0.944 [M]; bge 0.942, Qwen2.5-1.5B 0.938, e5-large 0.939, and the stage-1 probability alone 0.930 on the same pairs ([methodology 4][doc], Table 3). Read it as: pick a random true pair and a random false pair from the band; the 7B gives the true one the higher score 94.4% of the time. It does not mean:
- 94.4% accuracy, or a probability of anything;
- a number comparable to an AUC over all candidates, where easy pairs dominate and the value is much higher;
- anything about per-S1 decisions or the operating point;
- that 0.944 against 0.939 is a real difference: no interval is attached, and gaps of a few thousandths are small;
- that the models' errors are independent (a high AUC does not tell you whether a second model adds information).

"The 7B is no more accurate than a self-trained e5-large" is precisely the statement that both score 0.944 on the band.

### 2.9 Precision–recall curves and average precision

The **PR curve** plots precision against recall as τ sweeps. It focuses on the positive class, so it is more informative than ROC when positives are rare (Saito and Rehmsmeier 2015). **Average precision** (AP) averages the precision at the rank of each true pair. In the toy, true pairs sit at ranks 1, 3 and 4, with precisions 1, 2/3 and 3/4, so AP = 0.806. A random ranking has AP equal to the share of positives. The F0.5 values in the table of section 2.7 are the PR curve seen through the metric we care about.

### 2.10 Calibration curves

A model is **calibrated** if, among pairs given probability p, about p are true. A **reliability diagram** bins the predictions and plots the mean predicted probability against the observed share of true pairs in each bin; the diagonal is perfect. The **expected calibration error** is `ECE = Σ over bins (n_b / n) × |observed_b − predicted_b|`.

**Worked example (toy).** Three bins: predicted 0.05 with 400 pairs, observed 0.04; predicted 0.50 with 100 pairs, observed 0.40; predicted 0.95 with 500 pairs, observed 0.90. ECE = 0.4 × 0.01 + 0.1 × 0.10 + 0.5 × 0.05 = 0.039. The model is overconfident in the middle and at the top.

Calibration matters here for two reasons. Ranking metrics (AUC) cannot see it, and our decision layer treats probabilities as probabilities when it maximises expected F0.5. That is why stage 2 is calibrated with **isotonic regression**, a monotone step function fitted on training data and never on the holdout ([calibration page][adv07], [CONTRACTS C2][contracts]). With no labels (France) we check a sum instead: the probabilities of an S1's candidates should add up to about its expected number of copies. On the US/India holdout the sum per S1 was 3.4320 against a truth of 3.4323; on France it was 3.5456, evidence of overconfidence [M] ([evaluation page 2.8][adv05]).

### 2.11 Blocking metrics

Blocking is judged on what it keeps and what it costs. With candidate set C, true pairs T and all possible pairs A ([blocking page][adv02]):
- **pair completeness (recall)** `|C ∩ T| / |T|`;
- **reduction ratio** `1 − |C| / |A|`;
- **pairs per entity** `|C| / (number of S1)`, the cost driver;
- **oracle ceiling**: the macro F0.5 of a perfect classifier restricted to C (reported by `ber.eval.metric`).

| stage (test set) | pairs | per S1 | recall on the holdout |
|---|---|---|---|
| all within-country pairs | about 6.7e12 [E] | about 3.9M | 1 |
| retrieval | 58,437,794 | 33.7 | **99.1%** [M] |
| candidate file | 6,410,308 | 3.70 | about 98.2 to 98.4% [M] |
| predictions | 5,851,832 | 3.38 | precision 99.9%, recall 97.5% [M] |
| truth | | 3.46 | |

The 99.1% belongs to retrieval at 33.7 pairs per S1, not to the 3.70-per-S1 file ([scaling page 2.1][adv11]). A useful derived figure [E]: of 3.70 candidates per S1, about 3.46 × 0.983 = 3.40 are true copies, so about 92% of the candidate file is true and only about 0.30 false candidates per S1 remain for the later stages to remove.

**Recall is not the score ceiling.** On an earlier model chain (v5all), a recall of 98.20% had a measured oracle F0.5 of 0.99452, and a recall of 98.93% had 0.99676 [M] ([scaling page 2.1][adv11]). The pooled formula with recall 98.20% and precision 1 would suggest 0.9964. The macro score depends on how the missing pairs are spread over S1, so measure the ceiling; do not compute it from recall.

### 2.12 Breakdowns and the leaderboard arithmetic

Report every metric per group: per country, and per bucket such as empty address or number of rival S1. An overall average can hide a bad group, and it can move for a reason that is only a change of mix (a group with lower scores growing in share lowers the overall even if every group is unchanged).

**Local numbers.** Macro F0.5 on the local holdout: 0.9913 overall, US 0.9911, India 0.9916 [M]. France has no local number.

**The public leaderboard is a weighted average.** The test S1 are 38.274% US, 46.751% India and 14.975% France, and the public subset is representative by country [M] ([evaluation page 2.7 and 2.8][adv05]):

```
LB = 0.38274 × F_US + 0.46751 × F_India + 0.14975 × F_France
```

**Worked example [E].** The US/India part from the holdout is 0.38274 × 0.9911 + 0.46751 × 0.9916 = 0.8429; re-weighting the holdout to the test set's name-group mix moves it to about 0.8433. For Composite B, France ≈ (0.990879 − 0.8433) / 0.14975 ≈ 0.985. For model v3 (holdout 0.98882, public LB 0.97961) the same arithmetic gives about 0.93: (0.97961 − 0.85025 × 0.98882) / 0.14975 = 0.927. This is how we learned France was the gap. Two cautions. The method assumes US and India score on test as they do on the holdout. And dividing by 0.14975 multiplies errors by 6.7: a 0.0004 error in the US/India part becomes 0.0027 in France (0.9881 with 0.8429 instead of 0.9855 with 0.8433).

---

## 3. How it shows up in our project

- **The official scorer** is implemented in [`ber.eval.metric`][metric] (`entity_f05`, `macro_f05`, `per_entity_f05`) and was matched against the leaderboard at every upload ([evaluation page 2.9][adv05]).
- **Gates** compare macro F0.5 per S1 with a paired bootstrap ([F02][f02], [`ber.eval.gates`][gates]).
- **The decision layer** picks the set per S1 with the highest expected F0.5; the break-even rule explains why recall rules at 71% precision were not added ([metrics page][adv04]).
- **Band AUC** compares cross-encoders ([transformers page 2.8][adv08]).
- **Blocking measures** are reported at every change: recall, pairs per S1, and the oracle ceiling ([blocking page][adv02]).
- **Calibration** is checked by reliability, by the sum rule and by country ([calibration page][adv07]).
- **Per-country breakdown and the leaderboard formula** exposed France ([evaluation page][adv05]).

---

## 4. How to read the numbers

| number | what it is | what it tells you | what it does not tell you |
|---|---|---|---|
| 0.990879 | public LB, macro F0.5, US + India + France, the public subset of test [M] | our official standing during the challenge | the private score; **no private-leaderboard scores exist, only rankings** |
| 0.9913 | local holdout, macro F0.5, 549,699 US/India S1 (US 0.9911, India 0.9916) [M] | performance where labels exist | France; slightly optimistic because three decision settings were tuned on it |
| precision 99.9%, recall 97.5% | holdout predictions [M] | most of the remaining loss is recall | the macro score (section 2.6) |
| 99.1% / about 98.2 to 98.4% | recall of retrieval / of the 3.70-per-S1 file [M] | what blocking keeps | the score ceiling (section 2.11) |
| 0.944 | band AUC of the 7B and a self-trained e5-large [M] | ranking quality on the uncertain band | accuracy, calibration or operating point |
| 3.4320 vs 3.4323 | summed probability per S1 against truth, US/India holdout [M] | calibration of the totals | which pairs are wrong |
| 0.056 | the "predict nothing" macro score = singleton share [E] | the floor | |
| 0.985 / 0.93 | France implied by the leaderboard arithmetic for Composite B / v3 [E] | where the gap was | an exact value; it inherits the US/India assumption |

---

## 5. Common misconceptions

1. **"F0.5 weights precision twice as much as recall."** That is the shorthand for beta = 0.5. In error counts the weights are 1 for a false merge and 0.25 for a miss (4 to 1), and the realised cost ratio is 2 to 3 at typical set sizes.
2. **"Accuracy is a fine summary."** True negatives swamp everything. "Predict nothing" is 89.8% accurate at the retrieval stage.
3. **"AUC 0.944 means 94.4% correct."** It is a probability about rankings of one true and one false pair on a selected band.
4. **"A higher AUC means better decisions."** Decisions need calibrated probabilities and a threshold; AUC ignores both.
5. **"Macro F equals F of the average precision and recall."** It does not (0.9913 against 0.9941).
6. **"Recall of 99.1% caps the score at 99.1%."** The ceiling is a macro quantity and must be measured.
7. **"Country scores average to the overall."** They are weighted by S1 share: 38.3%, 46.8%, 15.0%.
8. **"Calibrated means accurate."** A model that says 0.5 for everything can be calibrated and useless.
9. **"The local number should equal the leaderboard."** Different populations: France is only in the second.

---

## 6. Check yourself

**1.** S1 has three true copies {a, b, c}. Compute F0.5 for the predictions {a, b} and {a, b, c, d}. Which error was more expensive?

<details><summary>Answer</summary>

{a, b}: TP = 2, k = 2, T = 3, so F0.5 = 2.5 / (0.75 + 2) = 0.909; the miss cost 0.091. {a, b, c, d}: TP = 3, k = 4, so F0.5 = 3.75 / (0.75 + 4) = 0.789; the false merge cost 0.211. The false merge cost 2.3 times the miss, matching the table for t = 3.

</details>

**2.** Derive `F0.5 = 1.25 TP / (1.25 TP + 0.25 FN + FP)` from `F0.5 = 1.25 P R / (0.25 P + R)`.

<details><summary>Answer</summary>

Put P = TP/(TP + FP) and R = TP/(TP + FN) over the common denominator (TP + FP)(TP + FN). The numerator of F is 1.25 TP². The denominator is TP × [0.25 (TP + FN) + (TP + FP)]. Cancel TP: F = 1.25 TP / (0.25 TP + 0.25 FN + TP + FP) = 1.25 TP / (1.25 TP + 0.25 FN + FP).

</details>

**3.** Five S1 score 1, 0.556, 1, 0 and 0.714 (the toy of section 2.6, where the true set sizes are 2, 1, 0, 0, 3 and the predicted set sizes 2, 2, 0, 1, 1). What is the macro F0.5? Does micro give the same?

<details><summary>Answer</summary>

Macro = (1 + 0.556 + 1 + 0 + 0.714) / 5 = 0.654. Micro pools the counts first: TP = 2 + 1 + 0 + 0 + 1 = 4, T = 6, k = 6, so F0.5 = 1.25 × 4 / (1.5 + 6) = 0.667. They differ because macro gives every S1 the same weight, so the failing singleton costs a full fifth of the score, while micro lets it disappear among the pooled counts.

</details>

**4.** For t = 1 and t = 3, what does one miss cost and what does one false merge cost? Why is the t = 1 ratio below 1?

<details><summary>Answer</summary>

t = 1: a miss costs 0.25 / 0.25 = 1.0 (the S1 scores 0), a false merge 1 / 2.25 = 0.444. t = 3: a miss 0.25 / 2.75 = 0.091, a false merge 1 / 4.75 = 0.211. With a single true copy, a miss wipes out the whole score, so it outweighs a false merge.

</details>

**5.** Scores: true pairs 0.95, 0.80, 0.60; false pairs 0.90, 0.40, 0.30, 0.20. Compute the AUC and the best threshold for F0.5.

<details><summary>Answer</summary>

Ordered pairs with the true pair higher: 0.95 beats all four false (4), 0.80 beats three (3), 0.60 beats three (3): 10 of 12, AUC = 0.833. F0.5 at τ = 0.60 is 3.75 / (0.75 + 4) = 0.789, higher than at 0.95 (0.714), 0.80 (0.667) and 0.40 (0.652). The best threshold is 0.60.

</details>

**6.** An S1 already has two sure pairs. A third candidate has p = 0.74. Add it? What if the S1's F0.5 is 0.9913 and you use the simple rule?

<details><summary>Answer</summary>

With m = 2 the break-even is (2.5 + 0.25) / (3.125 + 0.5) = 0.759, so 0.74 is just below it: do not add. The simple rule p > 0.8 × F0.5 gives 0.793 for F0.5 = 0.9913, which also says no. A candidate must be right roughly three times in four to help.

</details>

**7.** Bins: predicted 0.10 with 200 pairs, observed 0.20; predicted 0.90 with 800 pairs, observed 0.85. Compute the ECE and say in which direction the model errs.

<details><summary>Answer</summary>

ECE = 0.2 × |0.20 − 0.10| + 0.8 × |0.85 − 0.90| = 0.02 + 0.04 = 0.06. The model is under-confident at the low end (true rate higher than predicted) and over-confident at the high end (true rate lower than predicted).

</details>

**8.** The stage-1 probability alone has band AUC 0.930 and the 7B has 0.944. A juror asks, "So the 7B is 1.4% better?" What do you answer?

<details><summary>Answer</summary>

It is 0.014 in AUC, not a percentage of accuracy. AUC is the chance that a random true pair outranks a random false pair on the uncertain band, so the 7B ranks about 1.4 points more such pairs correctly. This is a ranking measure on a selected band, with no interval attached; the value of the cross-encoder to the final score was measured separately, on the macro F0.5 with a paired bootstrap.

</details>

**9.** Use LB = 0.38274 F_US + 0.46751 F_India + 0.14975 F_France with a US/India part of 0.8433 and LB = 0.990879 to find France. What happens if the part is 0.8429?

<details><summary>Answer</summary>

France = (0.990879 − 0.8433) / 0.14975 = 0.9855. With 0.8429: 0.9881. A 0.0004 change in the US/India part moves France by 0.0027, because the division magnifies errors by 1 / 0.14975 = 6.7. The estimate is only as good as the assumption that US and India score on test as on the holdout.

</details>

**10.** Precision is 99.9% and recall is 97.5%. Compute F0.5 from them. The reported macro F0.5 is 0.9913. Why do they differ?

<details><summary>Answer</summary>

1.25 × 0.999 × 0.975 / (0.25 × 0.999 + 0.975) = 0.9941. Macro F averages the per-S1 F0.5; plugging averaged P and R into the formula is a different calculation (the harmonic-mean-like function is concave, so the average of the F values is at most the F of the averages), and we also do not know whether the 99.9% and 97.5% are pooled or per S1. Never recompute a macro score from P and R.

</details>

**11.** The candidate file has recall 98.20% in one measurement, yet its oracle F0.5 was 0.99452. Why can't you get the oracle from the recall?

<details><summary>Answer</summary>

The pooled formula with recall 0.982 and precision 1 gives 0.9964. The oracle is a macro score: S1 with missed copies lose a share of their own F0.5 (and some lose everything), singletons are unaffected, and the average depends on how the missing pairs are distributed across S1. So the ceiling has to be measured on the per-S1 scores.

</details>

---

## 7. Going deeper

- van Rijsbergen (1979), "Information Retrieval", 2nd edition, Butterworths. Where F-beta comes from.
- Manning, Raghavan and Schütze (2008), "Introduction to Information Retrieval", Cambridge University Press. The evaluation chapter covers precision, recall, F and ranking measures.
- Hand and Christen (2018), "A note on using the F-measure for evaluating record linkage algorithms", Statistics and Computing. A critique specific to our setting.
- Lipton, Elkan and Narayanaswamy (2014), "Optimal thresholding of classifiers to maximize F1 measure", ECML PKDD; Ye, Chai, Lee and Chieu (2012), "Optimizing F-measures: a tale of two approaches", ICML.
- Fawcett (2006), "An introduction to ROC analysis", Pattern Recognition Letters; Hanley and McNeil (1982), "The meaning and use of the area under a receiver operating characteristic (ROC) curve", Radiology.
- Davis and Goadrich (2006), "The relationship between Precision-Recall and ROC curves", ICML; Saito and Rehmsmeier (2015), "The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets", PLoS ONE.
- Niculescu-Mizil and Caruana (2005), "Predicting good probabilities with supervised learning", ICML; Guo, Pleiss, Sun and Weinberger (2017), "On calibration of modern neural networks", ICML.
- Christen and Goiser (2007), "Quality and complexity measures for data linkage and deduplication", in Quality Measures in Data Mining, Springer. The blocking measures.

## 8. Where next

- [F11 Decision theory and optimisation][f11]: from these metrics to the per-S1 expected-F0.5 decision.
- [F12 Interpreting our results][f12]: reading our full set of numbers as a jury would.
- [F09 Experiments and evidence][f09]: how we decided that a change in these metrics was real.
- Advanced pages [04 metrics and decisions][adv04], [07 calibration][adv07], [02 blocking][adv02], [08 cross-encoders][adv08].
- The track map: [foundations README](README.md).

[doc]: ../../../experiments/ameya/final-zip/doc/Documentation_template.md
[task]: ../../../student_resource/README.md
[contracts]: ../../../docs/CONTRACTS.md
[metric]: ../../../code/business_entity_resolution/src/ber/eval/metric.py
[gates]: ../../../code/business_entity_resolution/src/ber/eval/gates.py
[adv02]: ../02-blocking.md
[adv04]: ../04-metrics-and-decisions.md
[adv05]: ../05-evaluation-methodology.md
[adv07]: ../07-calibration.md
[adv08]: ../08-transformers-and-cross-encoders.md
[adv11]: ../11-scaling-to-billions.md
[f01]: F01-data-and-problem.md
[f02]: F02-probability-and-statistics.md
[f09]: F09-experiments-and-evidence.md
[f11]: F11-decision-theory-and-optimisation.md
[f12]: F12-interpreting-our-results.md
