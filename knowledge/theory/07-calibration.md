# Calibration

**Summary.** A model is calibrated when its probabilities match frequencies: among pairs scored 0.8, about 80% are true.
Two parts of our pipeline read probabilities literally, the per-S1 expected-F0.5 decision and the self-training thresholds (≥ 0.9 positive, ≤ 0.05 negative), so calibration is not cosmetic for us.
On the labelled holdout our pc is calibrated within about 0.01 per bin; in France we proved without labels that it was overconfident (Σ pc per S1 3.55, where about 3.46 is the most possible).

Related pages: [metrics and decisions](04-metrics-and-decisions.md) (the F0.5 decision itself), [evaluation methodology](05-evaluation-methodology.md), [gradient boosting](06-gradient-boosting-and-stacking.md), [self-training and domain shift](09-self-training-and-domain-shift.md), [glossary](glossary.md).

---

## 1. Intuition

- A weather forecaster is calibrated if it rains on about 70% of the days she says "70%".
- **Ranking is not calibration.** A model can put every true pair above every false one (perfect AUC) and still say 0.6 for all true pairs. AUC only sees the order; calibration sees the numbers.
- We need the numbers because we compute expectations from them: the expected F0.5 of each candidate set, the expected false positives of a rule, and which pairs are safe to use as pseudo-labels.
- Calibration belongs to a distribution. A model calibrated on US/India can be overconfident on France, and nothing on the US/India holdout will show it.

## 2. Formal definition

### 2.1 What calibrated means, and how to measure it

A score $\hat p(x)$ is **calibrated** if $P(Y = 1 \mid \hat p(X) = p) = p$ for every p.

- **Reliability diagram:** bin the pairs by $\hat p$ and plot each bin's true rate $\bar y_b$ against its mean score $\bar p_b$. A calibrated model lies on the diagonal.
- **Expected calibration error:** $\mathrm{ECE} = \sum_b \frac{n_b}{N}\,\lvert \bar y_b - \bar p_b \rvert$; the maximum calibration error is $\max_b \lvert \bar y_b - \bar p_b\rvert$.
- **Proper scoring rules.** The log-loss $-\frac1N\sum_i [y_i\log p_i + (1-y_i)\log(1-p_i)]$ and the Brier score $\frac1N \sum_i (p_i - y_i)^2$ are minimised in expectation only by the true probability, so training on them pushes toward calibration. The Brier score splits into reliability (miscalibration) − resolution (how much the scores separate cases) + uncertainty (the base rate's variance).

### 2.2 Three ways to recalibrate a score

All three are fitted on held-out (for us, out-of-fold) scores, never on the rows the model trained on.

- **Platt scaling:** $p = \sigma(a\,s + b)$, a logistic regression on the score s. Two parameters; it assumes the distortion is sigmoid-shaped.
- **Temperature scaling:** $p = \sigma(z/T)$ on a logit z. One parameter; strictly monotone, so the ranking and the AUC never change. It is the standard fix for overconfident neural networks.
- **Isotonic regression:** find the non-decreasing function m that minimises $\sum_i w_i\,(y_i - m(s_i))^2$. It assumes only that a higher score never means a lower true rate.

**The pool-adjacent-violators (PAV) algorithm** solves isotonic regression exactly. Sort by score. Walk left to right, keeping blocks with their weighted mean. Whenever a block's mean is below the previous block's, merge the two and re-check backwards. After sorting it is linear in n. The result is a step function; scikit-learn interpolates linearly between the steps, and we saved the steps and applied them with `np.interp` on test.

Example: labels in score order 0, 1, 0, 0, 1, 1. The third label breaks the order, so {1, 0} merges to 0.5; the fourth breaks it again, so {1, 0, 0} merges to 1/3. Result: 0, 1/3, 1/3, 1/3, 1, 1.

Isotonic has flat steps, so it can tie scores that were distinct and change the AUC slightly. Temperature scaling cannot.

### 2.3 Why calibration drives our decision

For one S1 with candidates sorted by probability $q_1 \ge q_2 \ge \dots$ (only the record's owner may predict it; see [page 04](04-metrics-and-decisions.md)), predicting the top k gives, if the candidates are independent,

$$\mathbb{E}[F_k] = \sum_{i \le k} 1.25\, q_i\; \mathbb{E}\!\left[\frac{1}{0.25\,(1 + S_{-i}) + k}\right], \qquad \mathbb{E}[F_0] = (1-\lambda)\prod_j (1 - q_j),$$

where $S_{-i}$, the number of true matches among the S1's other candidates, follows a Poisson binomial distribution, and λ is the **phantom**: the expected true matches outside the candidate list (we used 0.01). The DP in [`decide.py`](../../experiments/ameya/model-v1/decide.py) and [`stack/core.py`](../../experiments/ameya/model-v1/stack/core.py) computes every $\mathbb{E}[F_k]$ exactly and keeps the best k. Under independence the best set is always a top-k prefix (the classical result for expected F-measures; Lewis 1995, Jansche 2007).

Every $q_i$ enters the expectation directly. If q is too high, the DP predicts too many pairs; if too low, too few. A tuned global threshold only needs the order to be right near one cut-off; the DP needs the numbers to be right everywhere.

**Break-even probability.** Take an S1 with t true copies and k predictions, all correct, so $F = 1.25k/(0.25t + k)$, and one more candidate that is true with probability q. If t does not depend on the candidate (a copy is missing, and this candidate may or may not be it), predicting it raises the expected F0.5 only if

$$q > \frac{k}{0.25\,t + k} = \frac{F}{1.25}.$$

With t = 4 and k = 3 the bar is 0.75. If instead the candidate decides t (true: it is the 4th copy; false: the S1 has only 3), predicting it gives F 1.0 or 0.789, against 0.9375 or 1.0 without it, so it pays only if 0.0625 q > 0.211 (1 − q), that is q > 0.77. The same arithmetic decides drops: removing a prediction pays when it is more than about 20–25% likely to be false. That is where "a recall rule must be 75% precise" and "a drop pays at 20–25% false" come from, and near those values a few points of miscalibration flip decisions.

### 2.4 Logit shifts as decision tuning

We pass the calibrated pc through $q = \sigma(\operatorname{logit}(pc) + b)$ before the DP. A shift b multiplies the odds by $e^b$: +0.2 is ×1.22, −0.3 is ×0.74.

A constant logit shift is exactly a prior correction. By Bayes, if a model fitted where the positive rate is π is used where it is π′, the corrected log-odds are

$$\operatorname{logit} p' = \operatorname{logit} p + \operatorname{logit}\pi' - \operatorname{logit}\pi$$

(Saerens et al. 2002). We did not need that correction on test: the extra test records (+23% per S1) all sit below p1 0.02, outside the candidates. Our shifts instead correct what calibration cannot fix: the DP's independence assumption, and a group of pairs whose pc was too high.

## 3. Variants

| method | idea | when to use |
|---|---|---|
| Histogram binning | the score becomes its bin's true rate | simple; coarse |
| Bayesian binning (BBQ) | averages over many binnings | small data |
| Beta calibration | a three-parameter family that contains the identity | scores already in [0, 1], non-sigmoid distortion |
| Platt / temperature | one or two parameters on the logit | little data, sigmoid-shaped distortion, neural networks |
| Isotonic | any monotone map | lots of data; what we used (about 10M stage-2 rows) |
| Label-shift EM / BBSE | re-estimate the target's base rate, shift the logits | when only the prior changes |
| Conformal prediction | sets with guaranteed coverage | a different goal: coverage, not probabilities |

## 4. Where we used it

| where | what | evidence |
|---|---|---|
| stage 2 ([`s2.py`](../../experiments/ameya/model-v1/s2.py)) | isotonic map p2 → pc, fitted on out-of-fold p2 (in the final fit, on all four groups' OOF scores) | holdout reliability within about 0.01 per bin on v3 [M] ([FEATURES](../../experiments/ameya/model-v1/FEATURES.md)); v6all train OOF: bin 0.70–0.75 is 73% true, bin 0.95–0.98 is 97% [M] |
| stage 3, part B ([`stage3.py`](../../experiments/ameya/model-v1/stage3.py)) | isotonic map from an empty-address record's total pc to P(its owner is a candidate); scales pcs up, never down | an empty-address record is a true copy 97.7% of the time, yet its total pc sat at 0.3–0.9 |
| label-free proxy odds ([`feats_lo_proxy.py`](../../experiments/ameya/model-v1/feats_lo_proxy.py)) | a decreasing isotonic map from a word's moved-house-number share to the label-odds scale, fitted on US/India words, applied to French words | share 0.05 → +2.2, 0.45 → 0, 0.8 → −4.8 [M] |
| the decision ([`stack/apply_combo.py`](../../experiments/ameya/model-v1/stack/apply_combo.py)) | logit shift +0.2; a further −0.3 when 4 or more S1 have p1 ≥ 0.02 for the record; phantom 0.01 | +48.1e-6 [+7.1, +91.2] over the threshold on v7s [M] |
| pseudo-labels ([`pseudo_labels.py`](../../experiments/ameya/model-v1/pseudo_labels.py)) | y = 1 at pc ≥ 0.9 and kept; y = 0 at pc ≤ 0.05 and not kept; rule decisions override; the rest unlabelled | 74,325 / 273,160 / 37,789 French band pairs for the v7sq labels [M] |
| the 7B re-check | the 7B logit read through truth rates per logit bucket on labelled holdout pairs | below −6: 8.3% true (24 pairs); −6 to −4: 86.3% (51) [M] ([page 10](10-llm-verification-and-compute.md)) |

**The DP needs probabilities that are calibrated and aware of competition.** On stage-1 probabilities it lost to a tuned threshold (−0.00029 on the full holdout; −0.00024 on the dev kit even after isotonic calibration). On stage-2 pc, which already accounts for rivals, it won by +0.00011 [+0.00005, +0.00017] ([FEATURES](../../experiments/ameya/model-v1/FEATURES.md); Sachi's [G6 record](../../docs/decisions/2026-09-25_1731_gate-g6-dp-vs-threshold.md)). Calibration alone was not enough: stage-1 scores treat two S1 that compete for one record as independent.

**The crowd shift corrects a local miscalibration.** Predictions with pc between the threshold and 0.75 whose record had 4 or more competing S1 were only 65–68% true on the holdout, below the 72–77% break-even (the hunt agent's `nsa` finding, [RESEARCH_v6 §6.16](../../experiments/ameya/model-v1/RESEARCH_v6.md)). A one-number shift for exactly those records replaced a hand rule.

**Guarding against tuning on the holdout** ([stacked-rules record](../../docs/decisions/2026-09-27_0636_stacked-rules.md)):
- the shift and the phantom were chosen on half A of the holdout and confirmed on half B (+45.5e-6);
- the crowd shift was chosen from {0.15, 0.3, 0.45} on half A and confirmed on half B;
- in repeated 2-fold CV (42 splits) the DP with the phantom kept +23.7e-6 out of sample, positive in 86% of splits, while a flat threshold tuned the same way lost 18.8e-6.

**France: overconfidence proved without labels** ([RESEARCH_v6 §2.3](../../experiments/ameya/model-v1/RESEARCH_v6.md), v6all). Two invariants of the generator hold whatever the country: a record has at most one owner, so its pc summed over S1 should not exceed 1; and an S1 has 3.46 true copies on average (US and India alike), so Σ pc per S1 should not exceed that.

| label-free check | holdout US | holdout India | test US | test India | **test France** |
|---|---|---|---|---|---|
| Σ pc per S1 (truth inside candidates) | 3.4320 (3.4323) | 3.4243 (3.4235) | 3.4419 | 3.4256 | **3.5456** |
| records with Σ pc > 1.05, per 1000 S1 | 1.9 | 1.9 | 12.1 | 15.5 | **52.4** |
| excess mass Σ max(0, Σ pc − 1), per 1000 S1 | 0.39 | 0.49 | 2.44 | 3.45 | **29.2** |

On the holdout, Σ pc equals the truth to the third decimal. In France the model believed in 0.085–0.12 more true records per S1 than the generator allows. About 0.075 per S1 was op-B look-alike mass that the French rules drop anyway; the rest was mostly identical-name ties. What we did about it:
- **per-record renormalisation** (p / max(1, Σ p)): +0.000015 on the holdout, then nothing once stage 3 existed, and our French valuations put it as low as −0.000137 [E]. Not used;
- **self-training** brought French Σ pc from 3.52 to 3.41 in its first round (v7nst, [page 09](09-self-training-and-domain-shift.md));
- the **7B re-check** removed confident French decoys that no probability had flagged.

**Hindsight:** probability-based estimates share the model's blind spots. Label-free, France's calibrated expectation was about 0.985 [E] while the leaderboard implied about 0.971 [E] at the time (RESEARCH_v6 §3). Late on 27 Sep the `cal` estimator (US/India-calibrated pc applied to French changes) predicted +69e-6 for the round-3 France model, and the leaderboard said −46e-6. Part of the miss: pc valued putting the 7B-rejected decoys back as a gain of +49 to +65e-6 (§6.20).

## 5. Why it fits this problem

- The metric is F0.5 per S1, singletons included. Choosing a set per S1 by expected F0.5 needs probabilities, not ranks.
- Under F0.5 the break-even is 75–80%, exactly where most of our uncertain pairs sit.
- Self-training thresholds are probabilities; calibrated scores make "≥ 0.9" mean roughly "at most 10% wrong" on the source distribution.
- The generator's structure (one owner per record, 3.46 copies per S1) gives invariants that test calibration without labels, which is the only kind of check France allowed.

## 6. Pitfalls

1. **Fitting the calibrator on in-sample scores** makes it learn the training optimism. Ours were fitted on out-of-fold scores.
2. **Isotonic with little data** overfits a staircase. Stage 2 had about 10M rows; stage 3's part B, fewer, so it only scales up.
3. **Calibration does not transfer.** Our pc was calibrated on US/India and overconfident on France.
4. **Global calibration hides local errors.** Crowded records were overconfident by several points. French list-word copies, a population 97–99.8% true in US/India, reached pc ≥ 0.999 only 58–63% of the time (89–98% in US/India).
5. **AUC cannot see calibration, and ECE cannot see ranking.** Report both.
6. **ECE depends on the bins.** With most mass near 0 and 1, equal-width bins look perfect; look at the middle band, or use equal-mass bins.
7. **Independence is false for competing pairs.** Two S1 cannot both own one record; argmax ownership and the crowd shift handle most of it.
8. **Self-assessment under shift is optimistic.** The model's expected F0.5 for France was too high, and pc-based valuations were biased on decoys.

## 7. Jury questions with answers

**Q1. Why do you need calibrated probabilities if you only pick the best candidates?**
Because we pick a set per S1 by expected F0.5, and each probability enters that expectation. Near the 75–80% break-even, a few points of miscalibration change which pairs we predict.

**Q2. Why isotonic, not Platt or temperature scaling?**
Isotonic assumes only monotonicity, and boosted-tree distortions are not sigmoid-shaped. With about 10M out-of-fold rows it has plenty of data. Temperature scaling is the right tool for a single neural logit with little data.

**Q3. How do you know pc is calibrated?**
On the holdout each reliability bin is within about 0.01 of its true rate, and Σ pc per S1 equals the true count inside the candidates: 3.4320 against 3.4323 for the US.

**Q4. How did you find France's overconfidence without labels?**
With the generator's invariants. French Σ pc per S1 was 3.5456 where about 3.46 is the most possible, and 52.4 records per 1000 S1 had Σ pc above 1.05 against 1.9 on the holdout.

**Q5. Why expected F0.5 per S1 and not a tuned threshold?**
The best set depends on the S1: a singleton should stay empty, an S1 with many uncertain candidates should predict fewer. The DP computes the exact expectation, empty set included. The gain is small but measured: +48.1e-6 [+7.1, +91.2], checked on held-out halves.

**Q6. Isn't the +0.2 shift just overfitting the holdout?**
It was chosen on one half and confirmed on the other, and in repeated 2-fold CV the rule kept +23.7e-6 out of sample. A flat threshold tuned the same way lost 18.8e-6. The shift corrects the DP's assumptions, not noise.

**Q7. Why 0.9 and 0.05 for pseudo-labels?**
Both require roughly 90–95% confidence on the source distribution, and the middle stays unlabelled. Positives must also be in the final matches and negatives outside them, so labels follow decisions. Under shift those numbers are less trustworthy, which is why guards and rules override known populations.

**Q8. What is the break-even probability for adding a match?**
F / 1.25 for the S1's current F0.5: 0.75 for an S1 holding 3 of 4 copies. None of our recall rules reached it; the best was 71% precise.

## 8. Self-test

1. Run PAV on the labels 0, 1, 1, 0, 0, 1 (already sorted by score).
<details><summary>Answer</summary>

The fourth label (0) is below the block [1] before it: merge to 0.5. That block is below the earlier [1]: merge to {1, 1, 0} = 2/3. The fifth label (0) is below 2/3: merge to {1, 1, 0, 0} = 0.5, which is above the first block's 0, so stop. The sixth label (1) is fine. Result: 0, 0.5, 0.5, 0.5, 0.5, 1.

</details>

2. Two bins: 900 pairs with mean score 0.02 and true rate 0.01; 100 pairs with mean score 0.80 and true rate 0.70. Compute the ECE.
<details><summary>Answer</summary>

0.9 × |0.01 − 0.02| + 0.1 × |0.70 − 0.80| = 0.009 + 0.010 = 0.019. Most of it comes from the small middle bin, which is why averages over all pairs hide the band that matters.

</details>

3. What do p = 0.5 and p = 0.7 become after a logit shift of +0.2?
<details><summary>Answer</summary>

σ(0 + 0.2) = 0.550; logit 0.7 = 0.847, σ(1.047) = 0.740. A shift moves middle probabilities most and leaves 0.001 or 0.999 almost unchanged.

</details>

4. An S1 has two owned candidates, q = 0.9 and 0.6, no phantom. Which set has the highest expected F0.5?
<details><summary>Answer</summary>

E[F₀] = 0.1 × 0.4 = 0.04. E[F₁] = 0.54 × 1.25/1.5 + 0.36 × 1 = 0.81. E[F₂] = 0.54 × 1 + 0.36 × 0.556 + 0.06 × 0.556 = 0.773. Predict only the first: 0.6 is below this S1's break-even.

</details>

5. A model trained where 10% of pairs are true says 0.5 for a pair in a population where 5% are true. What is the corrected probability, if only the prior changed?
<details><summary>Answer</summary>

Odds 1 × (0.05/0.95) / (0.10/0.90) = 0.474, so p = 0.474/1.474 = 0.32.

</details>

6. Why does temperature scaling never change AUC, while isotonic regression can?
<details><summary>Answer</summary>

z/T is strictly increasing, so the order is kept exactly. Isotonic is only non-decreasing: its flat steps can tie pairs that had different scores, and ties change the AUC slightly.

</details>

7. French Σ pc per S1 is 3.55 and the generator's mean is 3.46. What does that prove, and what does it not?
<details><summary>Answer</summary>

It proves that, on average, the French probabilities are too high: they expect more true records than can exist. It does not say which pairs are wrong. The excess could sit in look-alikes, ties or confident decoys, and later we found all three.

</details>

## 9. Further reading

- Brier (1950). Verification of forecasts expressed in terms of probability.
- Murphy (1973). A new vector partition of the probability score.
- DeGroot and Fienberg (1983). The comparison and evaluation of forecasters.
- Ayer, Brunk, Ewing, Reid and Silverman (1955). An empirical distribution function for sampling with incomplete information.
- Platt (1999). Probabilistic outputs for support vector machines and comparisons to regularized likelihood methods.
- Zadrozny and Elkan (2002). Transforming classifier scores into accurate multiclass probability estimates.
- Niculescu-Mizil and Caruana (2005). Predicting good probabilities with supervised learning.
- Gneiting and Raftery (2007). Strictly proper scoring rules, prediction, and estimation.
- Naeini, Cooper and Hauskrecht (2015). Obtaining well calibrated probabilities using Bayesian binning.
- Guo, Pleiss, Sun and Weinberger (2017). On calibration of modern neural networks.
- Kull, Silva Filho and Flach (2017). Beta calibration: a well-founded and easily implemented improvement on logistic calibration for binary classifiers.
- Saerens, Latinne and Decaestecker (2002). Adjusting the outputs of a classifier to new a priori probabilities: a simple procedure.
- Ovadia et al. (2019). Can you trust your model's uncertainty? Evaluating predictive uncertainty under dataset shift.
- Lewis (1995). Evaluating and optimizing autonomous text classification systems.
- Jansche (2007). A maximum expected utility framework for binary sequence labeling.
- Ye, Chai, Lee and Chieu (2012). Optimizing F-measures: a tale of two approaches.
