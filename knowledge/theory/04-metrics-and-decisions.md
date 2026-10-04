# Metrics and decisions: F0.5, expected-F optimisation and ownership

**Summary.** The competition scores F0.5 per S1 and averages it over all S1, singletons included. This page derives what that metric implies: why β = 0.5 favours precision, what a false merge costs against a miss, and the probability a candidate needs before adding it helps (the "75%" rule, with its assumptions). It then covers expected-F optimisation, our per-S1 dynamic programme (derivation, algorithm, complexity), ownership constraints, and why a tuned global threshold lost to the DP, and when it did not.

Related pages: [entity resolution](01-entity-resolution.md), [evaluation](05-evaluation-methodology.md), [calibration](07-calibration.md), [boosting and stage 3](06-gradient-boosting-and-stacking.md), [glossary](glossary.md).

---

## 1. Intuition

- **Per entity, then averaged (macro).** An S1 with one copy counts as much as one with eleven. A singleton (5.6% of S1) scores 1 for an empty list and 0 for anything else.
- **Precision first.** F0.5 punishes a wrong merge more than a missed copy, and the penalty grows with the size of the S1's true set.
- **Decide like the metric.** Given calibrated probabilities, each S1's best answer is the set that maximises its expected F0.5. A single threshold applies the same bar to every pair; the right bar depends on the S1's situation: how many confident copies it already has, whether it might be a singleton, and how much it is likely to be missing.

## 2. Formal definition

### 2.1 Precision, recall, F-beta

For one S1 with true set T, predicted set P and c = |P ∩ T| correct predictions:

```
precision = c/|P|      recall = c/|T|
F_β = (1 + β²)·P·R / (β²·P + R) = (1 + β²)·c / (β²·|T| + |P|)
F0.5 = 1.25·c / (0.25·|T| + |P|) = 1.25·c / (1.25·c + 0.25·FN + FP)
```

with the edge cases T = ∅: F = 1 if P = ∅, else 0; and T ≠ ∅, P = ∅: F = 0 ([`metric.py`][metric]). The README's example (P = 2/3, R = 1) gives 1.25 × 2 / (0.5 + 3) = 0.714 ([task][task]).

### 2.2 Why β = 0.5 favours precision

- F_β = 1 / (α/P + (1 − α)/R) with α = 1/(1 + β²): for β = 0.5, α = 0.8, a harmonic mean that puts weight 0.8 on precision (van Rijsbergen 1979).
- ∂F/∂P = ∂F/∂R exactly when R = βP: β is the recall-to-precision ratio at which a small gain in either is worth the same.
- In the counting form, a false positive has weight 1 in the denominator and a false negative 0.25.

**What one error costs**, for an S1 with t true copies and an otherwise perfect answer:

```
cost of one miss       = 0.25 / (1.25t − 1)
cost of one false merge = 1 / (1.25t + 1)
ratio                   = 4·(1.25t − 1) / (1.25t + 1)
```

| t | 1 | 2 | 3 | 4 | → ∞ |
|---|---|---|---|---|---|
| miss costs | 1.000 | 0.167 | 0.091 | 0.063 | → 0 |
| false merge costs | 0.444 | 0.286 | 0.211 | 0.167 | → 0 |
| false merge ÷ miss | 0.44 | 1.7 | 2.3 | 2.7 | 4 |

A false merge costs 2–3 times a miss at the typical sizes (mean |T| = 3.46), approaching 4 for large sets. Two exceptions matter: for **t = 1** a miss is worse (the S1 scores 0), and for a **singleton** any prediction costs the full 1.

### 2.3 Macro versus micro

Macro F = mean over S1 of F_s; micro F computes P and R from pooled counts. Example: S1 A has 10 copies, all found; S1 B has 1, missed. Micro F0.5 = 1.25 × 10 / (0.25 × 11 + 10) = 0.980; macro = (1 + 0)/2 = 0.5. Macro makes small entities expensive per pair and gives singletons 5.6% of the score. Its convenience: **given probabilities, the decision splits into one problem per S1**, coupled only through records that several S1 compete for (§2.7).

### 2.4 The break-even probability for adding one pair

**Setting.** An S1 has m predicted pairs, all certainly correct, and no other true copy is missing. One more candidate x is true with probability p, independently.
- If x is true: without x, F = 1.25m/(1.25m + 0.25); with x, F = 1. Gain G = 0.25/(1.25m + 0.25).
- If x is false: without x, F = 1; with x, F = 1.25m/(1.25m + 1). Loss L = 1/(1.25m + 1).

Add x when p·G > (1 − p)·L, that is

```
p > L / (G + L) = (5m + 1) / (6.25m + 2)
```

| m (certain pairs already in) | 0 | 1 | 2 | 3 | 4 | → ∞ |
|---|---|---|---|---|---|---|
| break-even p | 0.50 | 0.73 | 0.76 | 0.77 | 0.78 | 0.80 |

The m = 0 case is the lone candidate: right gives 1 either way round, so the bar is 0.5. These match the plan's table ([FINAL_PLAN §2][plan]). **The "about 75%" in our methodology is the bar for a typical S1 with one to three confident copies already predicted.** It is not universal:
- **Other copies already missed lower the bar.** With 2 correct predictions and 2 other true copies already missed, a third prediction needs only p > 0.65: recall is worth more when recall is low.
- **Uncertain earlier picks lower it too.** If the first candidate has p = 0.9 instead of 1, the second needs only 0.66, because it insures against the first being wrong (self-test 8).
- **The micro limit.** In one big pool, adding x helps iff p > TP/(β²|T| + |P|) = F/(1 + β²), so the bar is 0.8·F, about 0.79 at F = 0.99. Lipton, Elkan and Narayanaswamy (2014) prove the F1 version: the optimal threshold of a calibrated classifier is half the optimal F1.
- **Dependence** between candidates moves all of these numbers.

The same function prices drops: removing a predicted pair helps when its probability is below the bar. Evidence on the US/India holdout [M]: the best recall rule we found was 71% precise (49 of 69 pairs, the 7B on unowned candidates) and the empty-address exact-name rule 40%, so neither was added; pairs contested by 4 or more S1 with pc in (threshold, 0.75] were 65–68% true, so dropping them helped ([RESEARCH_v6 §6.16, §6.19][r6]).

### 2.5 Expected-F optimisation: two approaches

- **Plug-in thresholding** (empirical utility maximisation): estimate probabilities, then pick the threshold that maximises F on validation data.
- **Decision-theoretic** (Bayes-optimal set): for each test set, choose S maximising E_{y ~ p}[F(S, y)] under the model. Under macro F each S1 is its own small test set of 3–5 candidates.

Ye, Chai, Lee and Chieu (2012) show the two are asymptotically equivalent on large test sets; the plug-in rule is more robust when the model is misspecified, while the decision-theoretic one wins with a good model and on small sets. Jansche (2007) computes the expected F exactly under independence by dynamic programming. Dembczyński, Waegeman, Cheng and Hüllermeier (2011) drop independence: their General F-measure Maximizer needs only P(y_i = 1, Σy = s) for every i and s plus P(y = 0), and finds the exact optimum in cubic time.

**Top-k lemma.** Under independence the best set of each size k is the k most probable candidates (see e.g. Lewis 1995), so only n + 1 sets need checking. Sketch: E[F(S)] = 1.25 Σ_{i∈S} p_i·g_i with g_i = E[1/(0.25(1 + N_{−i}) + k)], where N_{−i} counts the true candidates other than i. If p_i > p_j, then N_{−i} contains Z_j where N_{−j} contains Z_i, so N_{−i} is stochastically smaller, g_i ≥ g_j, and swapping j out for i never lowers E[F].

### 2.6 Our per-S1 dynamic programme

**Model.** For one S1, candidate i is true with probability q_i, independently: Z_i ~ Bernoulli(q_i). A **phantom** Z_φ ~ Bernoulli(λ) stands for true copies outside the candidate list, which can never be predicted. N = Σ Z_i + Z_φ is the true set size.

**Expected F of a prefix.** For the set S_k of the k most probable selectable candidates, F = 1.25·C/(0.25·N + k) with C = Σ_{i∈S_k} Z_i. By linearity of expectation, and because Z_i/(0.25N + k) is zero unless Z_i = 1, in which case N = 1 + N_{−i}:

```
E[F_0] = P(N = 0) = (1 − λ) · Π_j (1 − q_j)
E[F_k] = 1.25 · Σ_{i in S_k} q_i · E[ 1 / (0.25·(1 + N_{−i}) + k) ]      (k ≥ 1)
```

N_{−i} is Poisson-binomial; its distribution is built by adding one Bernoulli at a time: π′(s) = π(s)(1 − q) + π(s − 1)·q.

**Algorithm** ([`decide.py`][decide]; the phantom version in [`stack/core.py`][core]):
1. q = σ(logit(p) + 0.2), with a further −0.3 when the pair's record has 4 or more S1 at p1 ≥ 0.02 (the **crowd shift**); λ = 0.01 ([methodology §4][doc]).
2. Per S1, sort candidates by q; keep q ≥ 0.001, at most 48.
3. Only candidates whose record this S1 **owns** (§2.7) can be selected, up to 16. Unowned candidates still count in N: if the record really is this S1's, giving it away is a miss.
4. For each selectable i, build the distribution of N_{−i} over all other candidates and the phantom, then add 1.25·q_i·Σ_s π(s)/(0.25(1 + s) + k) to E[F_k] for every prefix k that contains i.
5. Select the prefix with the largest E[F_k].

**Complexity.** O(k_max·n²) per S1 (n ≤ 48, k_max ≤ 16); with about 3.7 candidates per S1 that is a few hundred arithmetic operations. It is linear in the number of S1 and parallel across them (numba `prange`), so it never limits scale ([11](11-scaling-to-billions.md)). The leave-one-out distributions could be shared for O(n²) per S1; at our n it does not matter.

**Worked example** (λ = 0). Candidates q = 0.9 and 0.6: E[F_0] = 0.1 × 0.4 = 0.04; E[F_1] = 1.25 × 0.9 × (0.4 × 0.8 + 0.6 × 0.667) = 0.81; E[F_2] = 0.773. The DP keeps one. With 0.8 instead of 0.6: E[F_1] = 0.78 and E[F_2] = 0.864, so it keeps both.

### 2.7 Ownership: who gets a contested record

- **The constraint:** each record has at most one owner (0 violations in 7,638,365 true pairs) [M] ([FINAL_PLAN §1][plan]).
- **Argmax ownership:** each record stays only under its highest-probability S1. With additive pair scores and no binding capacity limits, this is the exact best many-to-one assignment. It must be computed over **all** S1, as on test; an early holdout run restricted the competition to holdout S1, and the bug was fixed before the G6 numbers ([G6 record][g6]).
- **Not Hungarian:** one-to-one assignment would give each S1 one record. Capacities (the generator never exceeds 5 S2, 6 S3 or 11 records per S1) make it a b-matching, solvable by min-cost flow; we enforced them with a cap rule instead (US −9, India −13 test pairs on v7s) [M] ([stacked-rules record][stack]).
- **F0.5 is not additive**, so "argmax, then the DP" is a two-step heuristic. A record contested by two S1 at p ≈ 0.49 each should go to neither: a false merge costs about 0.19 and a miss about 0.06 [M] ([RESEARCH_v5 §4][r5]).
- **Alternatives we measured:** a softmax over each record's S1 plus "none" (Plan B's G5) was dropped because records taken by the wrong S1 were only 0.26% of true pairs ([name-uniqueness record][uniq]); per-record renormalisation p/max(1, Σp) gave +0.000015 on v6all, nothing after stage 3, and up to −0.000137 on France; stage 3's joint re-scoring of contested records gave +0.00005 [M] ([RESEARCH_v5 §8.4][r5], [RESEARCH_v6 §2.3, §5.3][r6], [06](06-gradient-boosting-and-stacking.md)).

### 2.8 Why the global threshold lost, and when it won

Holdout paired bootstraps, DP against the best global threshold on the same probabilities [M]:

| probabilities | Δ macro F0.5 [95% CI] | source |
|---|---|---|
| stage 1, dev sample (25 Sep, Sachi) | −0.00024 [−0.00091, +0.00049] | [G6 record][g6] |
| stage 1, full holdout | −0.00029 [−0.00040, −0.00018] | [model-v1 handover][m1] |
| stage 2, models v1 / v2 / v3 | +0.00027 / +0.00018 / +0.00011, all CIs above 0 | [m1][m1], [FEATURES.md][feat] |
| v7ce3 | +0.00005 [+0.00001, +0.00009] | [RESEARCH_v6 §5.1][r6] |
| v7mst stage 3, plain DP | +0.00003 [−0.00002, +0.00007]: threshold kept | [RESEARCH_v6 §6.15][r6] |
| **final rule** on v7s (shift, phantom, crowd shift; + acronym and cap rules) | **+0.000048 [+0.000007, +0.000091]**, P(better) 0.987 | [stacked rules][stack] |

The final rule's parameters were chosen on one holdout half and confirmed on the other; repeated 2-fold cross-validation (42 splits) gave +0.0000237 out of sample, positive in 86% of splits, while re-tuning the flat threshold the same way gave −0.0000188 ([stacked rules][stack]). The honest size of the gain is a few times 10⁻⁵.

**Why the DP wins.**
1. **A set-size-aware bar**: about 0.5 for an S1's first candidate, 0.73–0.8 for later ones. On untouched holdout folds 2–4, a two-threshold rule (0.45 for the first candidate, 0.725 for the rest) gained +0.00024 [0.00012, 0.00036] over one threshold, the same as the DP [M] ([model-v1 handover][m1]). The theory's bars, recovered empirically.
2. It weighs each S1's singleton chance and expected recall.
3. Context enters as a calibrated shift (the crowd shift replaced a hard drop band).
4. It lands on the same prediction density from any model: 3.389 (US) and 3.376 (India) per S1 on three different models [M] ([RESEARCH_v6 §6.16][r6]).

**Why it sometimes lost.** On stage-1 probabilities it computed the exact expectation of the wrong model: stage 1 sees no per-S1 context, and candidates of one S1 are correlated. That is Ye et al.'s point that plug-in rules are more robust to misspecification. And as the models sharpened, fewer candidates sat in the contested band, so the gap shrank from +0.00027 to +0.00003.

Credit: Plan A (Ameya) proposed the DP; Plan B (Sachi) made it beat a tuned threshold first, with ties going to the threshold; Sachi ran the first G6; the phantom and crowd shift came from analysis agents for Ameya on 27 Sep; the France version is the error agent's design (agent for Ameya), worth about +0.000051 on the leaderboard by the 7B's calibration [E] ([RESEARCH_v6 §6.20][r6]).

## 3. Variants

- **Position thresholds** (first candidate vs the rest): a cheap approximation of the DP.
- **Dependence-aware maximisers** such as the General F-measure Maximizer.
- **Training for expected F** directly (Jansche 2005) instead of log-loss.
- **Segment-specific calibration shifts**, such as our French DP on France's own probabilities ([`dp_france.py`][dpfr]).
- **Joint decoding across S1** for contested records (stage 3).

## 4. Where we used it

[`metric.py`][metric] (the official formula), [`decide.py`][decide] (ownership, threshold, DP, G6), [`stack/core.py`][core] (phantom, crowd shift), [`stack/dp_france.py`][dpfr] (France), [stacked-rules record][stack].

## 5. Why it fits this problem

The metric is per entity and precision-heavy, each S1 has only a handful of candidates, the stage-2 and stage-3 probabilities are calibrated ([07](07-calibration.md)), and exclusivity gives a clean ownership rule. Those are the conditions under which the decision-theoretic approach beats a plug-in threshold.

## 6. Pitfalls

- **A DP on miscalibrated probabilities** loses to a threshold (stage 1: −0.00029).
- **Independence:** forced singletons make all of an S1's candidates false together, so the model underestimates P(N = 0); the shift and the phantom absorb part of this.
- **Tuning on the same holdout:** use halves and repeated CV ([05](05-evaluation-methodology.md)).
- **Optimising micro F** when the metric is macro.
- **Leaving unowned candidates out of N**, which forgets the recall cost.
- **Quoting "75%" as a law.** It is 0.50–0.80 by situation.
- **F is not a perfect linkage metric:** Hand and Christen (2018) show its implied precision/recall trade-off depends on the number of predicted matches. The organisers fixed the metric; we optimised it as given.

## 7. Jury questions with answers

**Q1. What does β = 0.5 mean in plain words?**
Precision weighs four times as much as recall in the harmonic mean (0.8 against 0.2). Per S1, a wrong merge costs 2–3 times a missed copy at our typical sizes, and a singleton loses everything with one wrong pair.

**Q2. Where does "an added pair must be right 75% of the time" come from?**
For an S1 with m certain correct pairs and nothing missing, adding a candidate helps if p > (5m + 1)/(6.25m + 2): 0.73, 0.76 and 0.77 for one to three pairs, rising to 0.80. It assumes calibrated, independent probabilities and complete recall elsewhere; with copies already missing the bar is lower, which our DP computes per S1.

**Q3. Why not one global threshold?**
The right bar changes with the S1: 0.5 for its first candidate, about 0.75 for later ones, and it depends on singleton risk and missing recall. The DP beat the best threshold by +0.000048 [+0.000007, +0.000091] on the holdout, and a two-threshold rule recovered the same effect, which shows where the gain comes from.

**Q4. The DP assumes independence. Isn't that wrong?**
Yes, candidates of one S1 are correlated. Two things keep it useful: stage 2 and stage 3 already condition each probability on the S1's other candidates, so much of the dependence is inside q; and one global logit shift plus the phantom, chosen on a holdout half and confirmed on the other, absorb the rest. A dependence-aware maximiser would be the next step.

**Q5. What does it cost at a billion entities?**
O(k·n²) per S1 with n ≈ 4 candidates: a few hundred operations, linear in entities and parallel. It is the cheapest stage of the pipeline.

**Q6. How do you handle singletons?**
E[F_0] = P(no true copy) competes with every non-empty set, so a singleton-looking S1 (all candidates weak) gets an empty answer. Our test predictions leave 5.8% of S1 empty against a 5.6% singleton share in train [M] ([RESEARCH_v6 §6.15][r6]).

**Q7. Why argmax ownership, not Hungarian or a softmax?**
Records have at most one owner but S1 have many records, so the problem is many-to-one, and argmax is its exact solution for additive scores. Hungarian enforces one-to-one, which is wrong here. A softmax with "none" was gated and dropped: records taken by the wrong S1 were only 0.26% of true pairs [M].

**Q8. You tuned a shift, a phantom and a crowd shift on the holdout. Overfitting?**
Three scalars on 549,699 S1, chosen on one half and confirmed on the other; repeated 2-fold CV still gave +0.0000237, positive in 86% of 42 splits, while a re-tuned flat threshold lost out of sample. Some optimism remains: the honest gain is about half the in-sample +0.000048.

**Q9. A gain of 5 × 10⁻⁵: worth it?**
It is free at run time, it is the metric's own logic rather than a heuristic, and it is consistent across models. At the top of the leaderboard, gaps between neighbours were of this order. But it is a refinement; the big gains came from features, cross-encoders and France.

**Q10. How would decisions change under micro F0.5?**
The bar would become one global value, about 0.8 × F, roughly 0.79, and singletons would stop mattering separately. The per-S1 DP exists because the metric is macro.

## 8. Self-test

1. Compute F0.5 for T = {a, b, c, d} and P = {a, b, x}.
<details><summary>Answer</summary>c = 2: 1.25 × 2 / (0.25 × 4 + 3) = 2.5 / 4 = 0.625.</details>

2. Show that a false positive weighs 1 and a false negative 0.25 in F0.5's denominator.
<details><summary>Answer</summary>|T| = c + FN and |P| = c + FP, so 0.25|T| + |P| = 1.25c + 0.25·FN + FP.</details>

3. Compute the break-even probability for a third pair when two certain pairs are already predicted.
<details><summary>Answer</summary>m = 2: (5 × 2 + 1)/(6.25 × 2 + 2) = 11/14.5 ≈ 0.76.</details>

4. Why is E[F_0] = P(N = 0), and what does the phantom do to it?
<details><summary>Answer</summary>An empty answer scores 1 only when the S1 has no true copy. The phantom multiplies P(N = 0) by (1 − λ): it admits that a copy may exist outside the candidates, which makes empty answers slightly less attractive.</details>

5. Verify E[F_1] = 0.81 for q = (0.9, 0.6) by enumerating the four outcomes.
<details><summary>Answer</summary>Predict {1}. Both true (0.54): 1.25/(0.5 + 1) = 0.833. Only 1 true (0.36): 1. Only 2 true (0.06): 0. Neither (0.04): 0. Sum 0.45 + 0.36 = 0.81.</details>

6. Sketch why the best set of size k is the top k by probability.
<details><summary>Answer</summary>E[F] = 1.25 Σ_{i∈S} p_i·g_i with g_i = E[1/(0.25(1 + N_{−i}) + k)]. A higher p_i means N_{−i} is stochastically smaller (it holds the other, less likely candidate), so g_i is larger too. Swapping a lower-probability member for a higher one never lowers E[F].</details>

7. Give a two-S1 example where micro and macro F0.5 differ sharply.
<details><summary>Answer</summary>A: 10 copies, all found; B: 1 copy, missed. Micro = 12.5/12.75 ≈ 0.98; macro = (1 + 0)/2 = 0.5.</details>

8. With q1 = 0.9, the second candidate needs only about 0.66, not 0.73. Why?
<details><summary>Answer</summary>E[F_1] = 0.9 − 0.15p and E[F_2] = 0.5 + 0.456p cross at p ≈ 0.66. If the first is wrong (10%), a right second candidate lifts F from 0 to 0.56, so it carries insurance value that a certain first candidate removes.</details>

## 9. Further reading

- van Rijsbergen (1979), "Information Retrieval", 2nd edition, Butterworths.
- Lewis (1995), "Evaluating and Optimizing Autonomous Text Classification Systems", SIGIR.
- Jansche (2005), "Maximum Expected F-Measure Training of Logistic Regression Models", HLT/EMNLP.
- Jansche (2007), "A Maximum Expected Utility Framework for Binary Sequence Labeling", ACL.
- Ye, Chai, Lee and Chieu (2012), "Optimizing F-measures: A Tale of Two Approaches", ICML.
- Lipton, Elkan and Narayanaswamy (2014), "Optimal Thresholding of Classifiers to Maximize F1 Measure", ECML PKDD.
- Dembczyński, Waegeman, Cheng and Hüllermeier (2011), "An Exact Algorithm for F-Measure Maximization", NIPS.
- Hand and Christen (2018), "A note on using the F-measure for evaluating record linkage algorithms", Statistics and Computing.
- Kuhn (1955), "The Hungarian Method for the Assignment Problem", Naval Research Logistics Quarterly.

[metric]: ../../code/business_entity_resolution/src/ber/eval/metric.py
[task]: ../../student_resource/README.md
[plan]: ../../plans/FINAL_PLAN.md
[r5]: ../../experiments/ameya/model-v1/RESEARCH_v5.md
[r6]: ../../experiments/ameya/model-v1/RESEARCH_v6.md
[decide]: ../../experiments/ameya/model-v1/decide.py
[core]: ../../experiments/ameya/model-v1/stack/core.py
[dpfr]: ../../experiments/ameya/model-v1/stack/dp_france.py
[doc]: ../../experiments/ameya/final-zip/doc/Documentation_template.md
[g6]: ../../docs/decisions/2026-09-25_1731_gate-g6-dp-vs-threshold.md
[stack]: ../../docs/decisions/2026-09-27_0636_stacked-rules.md
[uniq]: ../../docs/decisions/2026-09-25_2111_gate-name-uniqueness.md
[m1]: ../../docs/handover/2026-09-25_1958_ameya_model-v1.md
[feat]: ../../experiments/ameya/model-v1/FEATURES.md
