# F11. Decision theory and optimisation: from probabilities to the set we submit

**Summary.**
- A decision is a choice between actions under uncertainty. The best one maximises expected utility, and with calibrated probabilities the costs of the two kinds of error give a threshold.
- F0.5 is a ratio of counts, not a sum over pairs. So the probability a pair needs before adding it helps depends on what the S1 already has: 0.50 for a first match, about 0.73 to 0.80 for later ones. One global threshold cannot be right for all S1, so for each S1 we pick the best prefix of its candidates by expected F0.5, with a dynamic programme.
- The gain was small. The whole decision layer gained +0.0000481 [0.0000071, 0.0000912] on the local holdout, and the dynamic programme alone (+33.2e-6 [−7.5, +75.0]) was not significant. 94.5% of our predictions are so confident that the decision is trivial.

About 3 hours with the exercises. Prepares you for [04 metrics and decisions][adv04] and [07 calibration][adv07].

---

## 1. What you need first

- [F02][f02]: expectation, independence, the Bernoulli variable, odds and log-odds.
- [F04][f04]: precision, recall, F0.5 and calibration (a probability of 0.9 should be right 90% of the time).
- [F09][f09]: the paired bootstrap and why a +0.00005 gain needs care. Evidence levels: **M** measured, **E** estimated, **R** reported (not re-checked here), **U** uncertain; "toy" is invented for practice. "Local holdout" is the fixed 25% of labelled US/India S1 (549,699 S1, no France).

---

## 2. The concepts from zero

### 2.1 Decisions under uncertainty

**Intuition.** You must act before you know the truth. You do not know whether a candidate pair is a match, but you can say how likely it is, and you know what each mistake costs. Choose the action with the best average outcome.

**Definition.** For an action a and an unknown state s, the **utility** U(a, s) says how good the outcome is. The **expected utility** of a is the average of U(a, s) over the probabilities of the states. The **Bayes-optimal** decision maximises it. For a single pair with match probability p, the two actions are "predict" and "do not predict". Let a false positive cost c_FP and a false negative cost c_FN, and let right answers cost nothing:

```
predict if   p x c_FN  >  (1 - p) x c_FP
      i.e.   p  >  c_FP / (c_FP + c_FN)
```

**Worked example.** If a wrong merge costs 2 and a missed copy costs 1, the threshold is 2 / 3 = 0.667. If a wrong merge costs 4 times a miss, it is 0.8. A threshold is just a cost ratio written as a probability. It only works if p is right: if the model says 0.8 and the truth is 0.6, a threshold of 0.667 accepts pairs it should reject. That is why calibration comes first ([07 calibration][adv07]). Our stage-2 probabilities were calibrated with isotonic regression and were reliable within about 0.01 to 0.03 [R].

**Two places to put the costs.** You can bake costs into training (a cost-sensitive loss that punishes false positives more) or keep training neutral, produce calibrated probabilities, and apply the costs in a separate decision step. We did the second. The same probabilities can then serve another metric or another cost by changing only the decision rule, and a calibrated probability can be checked against labels. The price is that the decision step is only as good as the calibration. With a ratio-of-counts metric like F0.5 there is no fixed cost ratio at all, which is the subject of the next two sections.

### 2.2 F0.5 in counts, and what one error costs

**Definition.** For one S1, let TP be the correct predictions, K the number predicted and m the true set size. Substituting precision TP / K and recall TP / m into F-beta gives a form with no ratio of ratios:

```
F_beta = (1 + beta^2) x TP / (beta^2 x m + K)          F0.5 = 1.25 x TP / (0.25 x m + K)
m = 0 (a singleton):   F = 1 if K = 0, else 0
```

K counts what we predict and m is fixed by the world. This single form drives everything below.

**Worked example.** An S1 has m = 4 true copies. We predict 4 records and 3 are right: F0.5 = 1.25 × 3 / (0.25 × 4 + 4) = 3.75 / 5 = 0.75.

**What one error costs.** Take an S1 with t true copies and an otherwise perfect answer. One miss gives TP = t − 1, K = t − 1. One false merge gives TP = t, K = t + 1.

| true copies t | one miss costs | one false merge costs | false merge divided by miss |
|---|---|---|---|
| 1 | 1.000 | 0.444 | 0.44 |
| 2 | 0.167 | 0.286 | 1.7 |
| 3 | 0.091 | 0.211 | 2.3 |
| 4 | 0.063 | 0.167 | 2.7 |
| 11 | 0.020 | 0.068 | 3.5 |
| very large | near 0 | near 0 | 4 |

For the typical S1 (3.46 copies on average [M]) a wrong merge costs about twice a miss, which is the "twice as much" in our methodology document. The ratio tends to 4 for large sets, because a false positive counts 1 and a false negative counts 0.25 in the denominator. For t = 1 a miss is worse, since the S1 scores 0. For a singleton, any prediction costs the full 1.0 (an empty list scores 1, anything else 0). About 5.6% of S1 are singletons [M].

### 2.3 The break-even probability, and why one threshold fails

**Intuition.** Adding a pair is a bet. If it is right you gain a little recall. If it is wrong you lose precision. The bet is worth taking when the odds are good enough, and "good enough" depends on how many right answers you already have.

**Derivation.** An S1 has m predicted pairs, all certainly right, and no other true copy is missing. One more candidate x is true with probability p.
- If x is true: without x, F = 1.25m / (1.25m + 0.25); with x, F = 1. Gain G = 0.25 / (1.25m + 0.25).
- If x is false: without x, F = 1; with x, F = 1.25m / (1.25m + 1). Loss L = 1 / (1.25m + 1).

Add x when p × G > (1 − p) × L, that is

```
p  >  L / (G + L)  =  (5m + 1) / (6.25m + 2)
```

For the first match, m = 0. If x is true, predicting it gives F = 1 and staying silent gives 0. If x is false, predicting it gives 0 and staying silent gives 1, because the S1 is then a singleton. Gain and loss are both 1, so p > 0.5.

| pairs already in (m) | 0 | 1 | 2 | 3 | 4 | many |
|---|---|---|---|---|---|---|
| break-even p | 0.50 | 0.73 | 0.76 | 0.77 | 0.78 | 0.80 |

Check for m = 1: G = 0.25 / 1.5 = 0.167, L = 1 / 2.25 = 0.444, so p = 0.444 / 0.611 = 0.727. This is the "about 75%" in our methodology: the bar for a typical S1 with one to three copies already predicted. It is not universal. Copies already missed lower it, an uncertain earlier pick lowers it, and dependence between candidates moves it ([04 section 2.4][adv04]).

**Pooled F0.5.** If all pairs of all S1 sit in one pool, P (all true pairs) is fixed and F = 1.25 TP / (0.25 P + K). Adding one pair with probability p changes TP by p and K by 1, which helps exactly when p > TP / (0.25 P + K) = F / 1.25. At F near 0.99 that is 0.79: one global threshold is optimal for the pooled metric. Lipton, Elkan and Naryanaswamy (2014) prove the F1 version, a threshold of half the best F1.

**Worked example (why macro F0.5 differs).** Our metric averages F over S1, so every S1 faces its own bar. Take S1 A with one candidate at 0.60 and S1 B with candidates 0.97, 0.97 and 0.65. The exact expected F0.5 of each choice is:

| S1 | stop before the last candidate | include the last candidate | best choice |
|---|---|---|---|
| A (0.60) | 0.400 (predict nothing) | 0.600 | include |
| B (0.97, 0.97, 0.65) | 0.916 | 0.882 | drop the 0.65 |

A needs a threshold of at most 0.60 and B needs one above 0.65. No single threshold gets both right.

### 2.4 Dynamic programming from zero, and the expected F0.5 of a set

**Intuition.** **Dynamic programming** (DP) solves a big problem by building it from smaller ones and writing the small answers in a table so that nothing is computed twice. The classic first example: count the paths from the top-left to the bottom-right of a 3 × 3 grid, moving right or down. Each cell is the number of paths to the cell on its left plus the number to the cell above:

```
1 1 1
1 2 3        the answer is the last cell: 6 paths
1 3 6
```

**The Poisson-binomial.** Candidate i is true with probability q_i, independently. The number of true candidates is the **Poisson-binomial** distribution. Let pi_j(s) be the chance that exactly s of the first j candidates are true. Adding candidate j gives the recurrence

```
pi_j(s) = pi_{j-1}(s) x (1 - q_j)  +  pi_{j-1}(s - 1) x q_j
```

**Worked example.** Take q = (0.9, 0.7, 0.4).

```
after 0.9 :  s=0: 0.100   s=1: 0.900
after 0.7 :  s=0: 0.030   s=1: 0.340   s=2: 0.630
after 0.4 :  s=0: 0.018   s=1: 0.216   s=2: 0.514   s=3: 0.252
```

Doing this by hand takes 3 rows. Listing all outcomes takes 2^n, which is 1,048,576 for n = 20. The DP takes about n squared (400).

**Expected F0.5 of a set.** Select the first k candidates by probability. Then TP is the number of true ones among them, and m is TP plus the true ones left out, including a **phantom**: one more unselectable Bernoulli with probability 0.01 for true copies outside the candidate list. The expected F averages F(TP, m, k) over all outcomes. The **prefix lemma** says the best set of each size k is the k most probable candidates. Swap a selected candidate j for a more probable one i that was left out. Only when exactly one of the two is true does the swap matter, the gain and the loss are the same size, and "i true, j false" is more likely than the reverse (an exchange argument, [04 section 2.5][adv04]). So only n + 1 sets need checking.

For q = (0.9, 0.7, 0.4), without the phantom:

| selected k | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| expected F0.5 | 0.018 | 0.747 | 0.788 | 0.702 |

The best is k = 2. The 0.7 candidate is kept although 0.7 is below the 0.727 bar, because the bar assumed the first pick is certain and here it fails 10% of the time, so a second pick still scores. The plug-in shortcut (F of the expected counts) gives 0, 0.750, 0.800 and 0.714: close, except at k = 0, where it misses the chance that the S1 is a singleton.

**Hand check of the exact method.** The repository uses a trick: F is zero unless a selected candidate i is true, and then the true set size is 1 plus the number N_i of the other true candidates. So E[F_k] = 1.25 × the sum over selected i of q_i × E[1 / (0.25 × (1 + N_i) + k)]. Take k = 1 and q = (0.9, 0.7, 0.4). The selected candidate is the 0.9. The other two give N = 0, 1 or 2 with probabilities 0.18, 0.54 and 0.28. The terms 1 / (0.25 × (1 + N) + 1) are 0.800, 0.667 and 0.571, so the expectation is 0.144 + 0.360 + 0.160 = 0.664, and E[F_1] = 1.25 × 0.9 × 0.664 = 0.747, the value in the table. The code builds each leave-one-out distribution with the same recurrence ([04 section 2.6][adv04]).

### 2.5 Our per-S1 set selection

For each S1 the decision layer does this ([04 section 2.6][adv04], [methodology doc][doc]):
1. Take the calibrated probability pc of each owned candidate. Move it to q = sigmoid(logit(pc) + 0.2). Subtract a further 0.3 on the logit scale when the record is wanted by four or more S1 (the crowd shift). Add a phantom of 0.01.
2. Sort by q, compute the expected F0.5 of every prefix with the DP, and keep the best prefix.
3. Then apply the rules (acronym joins, per-source caps) and, for France, its own rules and the same selection on French probabilities.

The shifts are tuned on the local holdout, not derived. Here is what they do to a few probabilities:

| pc | after +0.2 | after the crowd shift (−0.3 more) |
|---|---|---|
| 0.55 | 0.599 | 0.525 |
| 0.65 | 0.694 | 0.627 |
| 0.70 | 0.740 | 0.679 |
| 0.75 | 0.786 | 0.731 |
| 0.80 | 0.830 | 0.784 |

Near the bars of 0.73 to 0.80 the +0.2 shift adds about 0.03 to 0.05, and the crowd shift takes back about 0.05, so a crowded record at pc = 0.75 ends at 0.731, just under the bar for a second copy.

**Table 1. Expected-F0.5 selection against the best single threshold** (paired bootstrap on the local holdout, Δ in macro F0.5 [M]; [04 section 2.8][adv04], [decision][d-g6], [decision][d-stack]).

| probabilities | gain over the tuned threshold |
|---|---|
| stage 1, dev sample / full holdout | −0.00024 / −0.00029 |
| stage 2, models v1 / v2 / v3 | +0.00027 / +0.00018 / +0.00011 |
| v7ce3 | +0.00005 [+0.00001, +0.00009] |
| v7mst, plain DP | +0.00003 [−0.00002, +0.00007] (n.s.) |
| v7s, DP alone | +33.2e-6 [−7.5, +75.0] (n.s.) |
| v7s, final rule (DP + shifts + phantom + rules) | +48.1e-6 [+7.1, +91.2], P(better) 0.987 |

The sign changed with model quality. On stage-1 probabilities the DP computed the exact expectation of the wrong model: stage 1 sees no per-S1 context, and candidates of one S1 are correlated. As the models sharpened, fewer candidates sat in the contested band and the gain shrank from +0.00027 to about +0.00003 to +0.00005. The final rule's parameters were chosen on one holdout half and confirmed on the other. Repeated 2-fold cross-validation gave +23.7e-6 out of sample (positive in 86% of 42 splits), while a re-tuned flat threshold lost 18.8e-6.

**What +48.1e-6 means.** It is 0.0000481 × 549,699 ≈ 26 S1 flipping from wrong to right, out of 549,699. The reason it is small: 94.5% of our final predictions have a stage-1 probability above 0.99 [M], so the decisions the DP can change sit in a thin band of S1, those with a candidate near the bars of 0.5 to 0.8 (an interpretation, E).

### 2.6 Ownership: who gets a contested record

**Definition.** Every S2/S3 record belongs to at most one S1: there are 0 violations in 7,638,365 true train pairs [M] ([04 section 2.7][adv04]). **Argmax ownership** keeps each record only under its highest-probability S1. When pair scores add up and nothing else binds, this is the exact best many-to-one assignment: each record chooses independently. Only owned candidates are selectable in the DP. Unowned candidates still count in m, because if the record really belongs to this S1, giving it away is a miss.

**Worked example.** Record r has p = 0.80 with S1 a and 0.60 with S1 b. It belongs to a. S1 b cannot select r, but r stays in b's count of possible true copies. If they were 0.49 and 0.49, the record should go to neither: a false merge costs about 0.19 and a miss about 0.06 for a typical S1, and the bet is worse than the break-even [M] ([04][adv04]).

**Capacities.** The generator never gives an S1 more than 5 S2 records, 6 S3 records or 11 records in total [M]. Respecting that exactly turns the assignment into a b-matching (each S1 has a capacity), which a min-cost flow solves. We used a cap rule instead, which removed 9 US and 13 India test pairs on v7s [M] ([04 section 2.7][adv04]).

**Why not something fancier.** F0.5 is not additive, so "argmax, then DP" is a two-step heuristic. A softmax over S1 plus "none" (gate G5) was dropped because records taken by the wrong S1 were only 0.26% of true pairs, which bounds the possible gain. Stage 3 re-scores contested records and gained +0.000055 [0.000025, 0.000085] ([F15][f15], [decision][d-s3]).

### 2.7 Bayes limits, abstaining and the 7B drop

**Bayes limit.** Some errors cannot be removed by any model. If two S1 have the same name and a record has that name and no address, the record is a 50/50 case, and whatever we do is right half the time. Our research notes call identical-name ties a Bayes limit and record that we accepted the loss [R].

**Abstaining is an action.** Dropping a pair is the same bet in reverse: drop it if its probability of being true is below the break-even for keeping it, about 0.75 to 0.80. The 7B re-check dropped confident predictions with a logit below −6. On a 34% labelled sample, 8.3% of those were real (2 of 24 pairs; Wilson 95% interval 2.3% to 25.8% [E]). The next bucket, −6 to −4, was 86.3% real, above the bar. So the drop is a good bet, with a margin, and the neighbouring bucket is a good keep ([10][adv10]).

**Value of a second opinion.** Running a reader B on a pair pays when P(B changes the decision) × (gain when it does) is larger than B's cost. For the 7B re-check the first factor is tiny: 1,150 drops among 5,614,414 re-checked predictions, 0.02% [M]. But each correct drop is worth about +0.19 F0.5 to the S1 concerned [R] ([10 section 2.1][adv10]). That is the decision-theory reason to spend about 3.6 GPU-hours on a re-check and not about 27 on every retrieved pair.

### 2.8 Choosing the knobs, and what the computation costs

The three tuned settings (shift +0.2, crowd shift −0.3, phantom 0.01) are three knobs. Tuning knobs on the holdout is an optimisation problem with a trap: the more knobs and the finer the grid, the more the tuned values fit the holdout's noise. We limited the damage. We chose on one half and confirmed on the other, then ran repeated 2-fold cross-validation, which cut the gain roughly in half (48.1e-6 in sample, 23.7e-6 out of sample), and a flat threshold tuned the same way lost. The computation is cheap. With about 3.7 candidates per S1 (6,410,308 pairs for 1,732,544 S1) the DP costs a few hundred operations per S1, is linear in the number of S1, and runs in parallel ([04][adv04]). Cost is not the constraint. Calibration is.

---

## 3. How it shows up in our project

| step | rule | number |
|---|---|---|
| cost of errors | wrong merge about twice a miss | 1.7 to 2.7 for 2 to 4 copies |
| first match | predict if p > 0.5 | the singleton rule, 5.6% of S1 |
| further matches | bar 0.73 to 0.80 | recall rules at most 71% precise were not added ([10][adv10]) |
| selection | best prefix by expected F0.5 | +48.1e-6 for the whole layer |
| ownership | argmax over all S1 | 0 violations in 7,638,365 pairs |
| drop | 7B logit below −6 | +37e-6 on the whole holdout [M] |

Credit ([04][adv04]): Ameya's plan proposed the DP, Sachi made it beat a tuned threshold first and ran the first G6, and the phantom and crowd shift came from analysis agents for Ameya on 27 Sep.

---

## 4. How to read the numbers

- A gain of +0.000048 is about 26 S1 on the holdout and about 83 on the test (1,732,544 S1) [E].
- "n.s." means the 95% interval includes zero. It is not a proof of no effect ([F09][f09]).
- The thresholds 0.5 and 0.8 are about one S1's current state. Do not call 0.75 "the threshold".
- The DP sees q, which is pc after the shifts, not pc itself.

---

## 5. Common misconceptions

1. **"The best threshold for F-measures is 0.5."** It is 0.5 only for the first match of an S1. For the pooled F0.5 it is F / 1.25, near 0.79.
2. **"F0.5 treats every pair the same."** One S1 is one unit; a pair on a singleton costs 1.0 and on an S1 with 11 copies costs 0.07.
3. **"The DP finds the best set."** The best set under its assumptions: independence and calibration. Duplicates share their fate, which the DP cannot see.
4. **"Expected F is the F of the expected counts."** It is not; the singleton term is the difference.
5. **"Precision first means never add below 0.9."** The first match needs only 0.5.
6. **"The gain proves the DP is good."** It is a small gain from a thin band; the model's probabilities carry the result.
7. **"A higher AUC means a higher F0.5."** AUC scores the ranking at every threshold. F0.5 scores one set per S1, after calibration, ownership and the bars above. Models with band AUCs of 0.938 and 0.944 are not 0.006 apart in F0.5 ([F12][f12]).

---

## 6. Check yourself

**1.** A wrong merge costs 3 and a miss costs 1. What is the threshold?

<details><summary>Answer</summary>

p > 3 / (3 + 1) = 0.75.

</details>

**2.** An S1 has m = 5 true copies. We predict 5 records, 4 right. Compute F0.5, and the cost of a miss for t = 5.

<details><summary>Answer</summary>

F0.5 = 1.25 × 4 / (0.25 × 5 + 5) = 5 / 6.25 = 0.80. A miss with t = 5 costs 1 − 1.25 × 4 / (1.25 + 4) = 1 − 0.952 = 0.048.

</details>

**3.** Find the break-even for adding a fifth pair (m = 4 already in).

<details><summary>Answer</summary>

(5 × 4 + 1) / (6.25 × 4 + 2) = 21 / 27 = 0.778. Check: G = 0.25 / 5.25 = 0.0476, L = 1 / 6 = 0.1667, L / (G + L) = 0.778.

</details>

**4.** Compute the Poisson-binomial for q = (0.8, 0.5) and the best prefix.

<details><summary>Answer</summary>

After 0.8: (0.2, 0.8). After 0.5: s = 0: 0.1, s = 1: 0.2 × 0.5 + 0.8 × 0.5 = 0.5, s = 2: 0.4. Expected F0.5: k = 0: 0.1; k = 1: 0.8 × (0.5 × 1 + 0.5 × 0.833) = 0.733; k = 2: 0.4 × 1 + 0.5 × 0.556 = 0.678. Best: k = 1. The 0.5 candidate is dropped.

</details>

**5.** For q = (0.9, 0.7, 0.4) we kept the 0.7 candidate although 0.7 < 0.727. Why is that right?

<details><summary>Answer</summary>

The derivation assumed the first pick is certain. It is true only 90% of the time. When it fails, a second pick can still make the S1's F positive, so the second pick is worth more than in the certain case. The exact expectation (0.788 against 0.747) shows it.

</details>

**6.** Apply the +0.2 shift and then the crowd shift of −0.3 to pc = 0.65.

<details><summary>Answer</summary>

logit(0.65) = 0.619. Plus 0.2 gives 0.819, probability 0.694. A further −0.3 gives 0.519, probability 0.627.

</details>

**7.** A recall rule is 71% precise and adds a second copy to S1 that already have one. Add it? What if it only adds to S1 that otherwise predict nothing?

<details><summary>Answer</summary>

For a second copy the bar is 0.73 (m = 1), so 71% loses: do not add. For an S1 with no prediction the bar is nearer 0.5, so 71% would win there. But 69% of the recall loss sits in S1 where other copies were found, so the 0.73 bar applies to most missed copies, and only about 20% sit in S1 we missed completely, where true singletons also exist. The sources do not record a test of an empty-S1-only rule (U).

</details>

**8.** The 7B drops pairs below −6, where 2 of 24 labelled pairs were real. The bar for keeping is about 0.75. Is the drop right, and how sure are we?

<details><summary>Answer</summary>

Yes. 8.3% is far below 75%. With so few pairs the Wilson 95% interval is 2.3% to 25.8%, still far below the bar. The next bucket (−6 to −4) is 86.3% real, above the bar, so a looser cut would lose, as the holdout confirmed.

</details>

**9.** Record r has 0.8 with S1 a and 0.6 with S1 b. Who owns it, and what does S1 b lose?

<details><summary>Answer</summary>

a owns it. S1 b cannot select r, so its set shrinks. If r truly belongs to b, that is a miss, which is why r still counts in b's possible true copies. If the scores were both 0.49, giving r to neither is better.

</details>

**10.** Name a case where the DP's independence assumption breaks, and what it changes.

<details><summary>Answer</summary>

Exact duplicates: they share an S1 in all 43,910 of 43,910 groups in train [M]. Take two duplicates at q = 0.6 each. Under independence the chance that both are false is 0.16, but for duplicates it is 0.40. The expected F0.5 of predicting nothing is 0.16 under independence and 0.40 for duplicates. The first-match bar lives in that singleton term, so dependence moves it.

</details>

---

## 7. Going deeper

- [04 metrics and decisions][adv04]: the break-even derivation with its caveats, the exact algorithm and complexity, ownership and the full G6 table. [07 calibration][adv07] for why the DP needs calibrated inputs. [10 LLM verification][adv10] for the drop rule.
- Lipton, Elkan and Naryanaswamy (2014), "Optimal Thresholding of Classifiers to Maximize F1 Measure", ECML PKDD.
- Ye, Chai, Lee and Chieu (2012), "Optimizing F-measures: a tale of two approaches", ICML. Jansche (2007), "A maximum expected utility framework for binary sequence labeling", ACL.
- Bellman (1957), "Dynamic Programming", Princeton University Press.
- Berger (1985), "Statistical Decision Theory and Bayesian Analysis", Springer.

## 8. Where next

- [F12 Interpreting our results][f12]: where these gains sit among all the numbers.
- [F15 Clustering, graphs and ER variants][f15]: ownership, assignment and collective matching.
- [F10 Semi-supervised learning and domain shift][f10]: calibration problems in a country with no labels.
- The track map: [foundations README](README.md).

[doc]: ../../../experiments/ameya/final-zip/doc/Documentation_template.md
[adv04]: ../04-metrics-and-decisions.md
[adv07]: ../07-calibration.md
[adv10]: ../10-llm-verification-and-compute.md
[f02]: F02-probability-and-statistics.md
[f04]: F04-classification-metrics.md
[f09]: F09-experiments-and-evidence.md
[f10]: F10-semi-supervised-and-domain-shift.md
[f12]: F12-interpreting-our-results.md
[f15]: F15-clustering-graphs-and-er-variants.md
[d-g6]: ../../../docs/decisions/2026-09-25_1731_gate-g6-dp-vs-threshold.md
[d-s3]: ../../../docs/decisions/2026-09-26_1557_rules-v3-and-stage3.md
[d-stack]: ../../../docs/decisions/2026-09-27_0636_stacked-rules.md
