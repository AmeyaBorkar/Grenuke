# F02. Probability and statistics: how sure is the model, and how sure are we?

**Summary.**
- A model speaks in probabilities, and an evaluation is a number measured on a finite sample. This page gives you the tools for both: Bayes' rule, odds and log-odds, expectation, the Poisson-binomial distribution, standard errors, the bootstrap, effect size and multiple comparisons.
- Each tool is tied to a decision of ours: the logit shift in the decision layer, the per-S1 expected F0.5, the gates that decided every component, and how to read a 0.9913 or a +0.000037.
- The goal is that you can say not only what we measured but how far to trust it.

Tier P1. About 3 hours in full, about 1.5 hours on the fast path (sections 2.2, 2.3, 2.5, 2.6 and 2.9 to 2.12). Prepares you for the advanced pages [04 metrics and decisions][adv04], [05 evaluation][adv05] and [07 calibration][adv07].

---

## 1. What you need first

School algebra, the sum sign Σ, the natural logarithm `ln` and the exponential `exp`, and the idea of an average. The vocabulary of S1, copies and candidates is in [F01][f01]. Evidence levels are as in F01: **M** measured, **E** estimated or derived, **R** reported. "Toy" means made-up numbers for practice.

---

## 2. The concepts from zero

### 2.1 Probability, conditional probability and independence

**Intuition.** A probability is a number from 0 to 1 that says how likely something is. We read it as a long-run frequency: "of 100 pairs that look like this one, about 80 are true matches." A model is **calibrated** when this holds at every score it gives ([F04][f04], [calibration page][adv07]).

**Rules.**

```
P(not A)  = 1 - P(A)
P(A or B) = P(A) + P(B) - P(A and B)          (the last term is 0 if A and B cannot both happen)
P(at least one of several) = 1 - P(none)
P(A | B)  = P(A and B) / P(B)                 probability of A among the cases where B holds
A and B are independent when P(A and B) = P(A) × P(B), equivalently P(A | B) = P(A)
```

**Worked example (toy).** 1,000 candidate pairs: 800 true, 200 false. The house numbers are equal in 760 of the true pairs and in 40 of the false ones.

| | house number equal | not equal | total |
|---|---|---|---|
| true | 760 | 40 | 800 |
| false | 40 | 160 | 200 |
| total | 800 | 200 | 1,000 |

P(true) = 0.80, but P(true | equal) = 760 / 800 = 0.95. They differ, so the house number carries information and the two events are not independent. Product check: P(true and equal) = 0.76, while P(true) × P(equal) = 0.64. Also, draw two pairs at random and ask for the chance that at least one is false: if the draws were independent it is 1 − 0.8² = 0.36. "At least one" is almost always easiest as one minus "none".

### 2.2 Total probability and Bayes' rule

**Intuition.** Evidence moves a belief, and how far depends on where you started. Bayes' rule turns "how likely is this evidence if the pair is a match" into "how likely is a match given this evidence". Mixing up those two questions is the commonest error in the subject.

```
P(match | e) = P(e | match) × P(match) / P(e)
P(e)         = P(e | match) × P(match) + P(e | no match) × P(no match)      (total probability)
```

P(match) is the **prior**, P(e | match) the **likelihood**, P(match | e) the **posterior**.

**Worked example (toy).** A feature fires for 90% of true pairs and 10% of look-alikes. How sure are we once it fires? That depends on the prior, the share of true pairs among the candidates.

| prior P(match) | 0.92 | 0.50 | 0.10 | 0.01 |
|---|---|---|---|---|
| posterior after the feature fires | 0.990 | 0.900 | 0.500 | 0.083 |

The same evidence is decisive in a clean list and nearly worthless in a cluttered one: the **base-rate effect**. It matters here because the test set has about 1.9 times as many orphans per S1 as train ([F01][f01] section 2.6), so the prior that a retrieved pair is true is lower there. For US and India this needed no correction, because the extra test records sit below the candidate cut ([calibration page][adv07], [self-training page][adv09]). The principle stays: a score learned at one prior cannot be trusted at another without a check ([F03][f03] gives the correction formula).

### 2.3 Odds, log-odds, logit and sigmoid

```
odds(p)    = p / (1 - p)               p = 0.75 gives odds 3 (three to one)
logit(p)   = ln( p / (1 - p) )         the log-odds, any real number
sigmoid(z) = 1 / (1 + exp(-z))         turns a log-odds back into a probability
```

`logit` and `sigmoid` are inverses. Logistic regression, neural networks and XGBoost with a logistic objective compute a log-odds `z` internally and return `sigmoid(z)`. The raw `z` is the **logit** or **margin**.

| p | 0.5 | 0.75 | 0.9 | 0.99 | 0.999 |
|---|---|---|---|---|---|
| odds | 1 | 3 | 9 | 99 | 999 |
| logit | 0 | 1.10 | 2.20 | 4.60 | 6.91 |

**Why log-odds.** Bayes' rule in odds form is a product, and a product becomes a sum in logs:

```
posterior odds     = prior odds × ratio of feature 1 × ratio of feature 2 × ...
log posterior odds = log prior odds + weight 1 + weight 2 + ...
```

This is the **Fellegi–Sunter** idea of record linkage ([entity resolution page 2.1][adv01]): each field adds a weight `ln(m / u)`, where m is the chance the field agrees for a match and u the chance it agrees for a non-match. It assumes the fields are independent given the class ("naive Bayes"). That is often false, and a learned model with interactions is the fix.

**Worked example (toy).** Prior: 10% of candidates are true, so odds 1 to 9. Name agrees (m = 0.9, u = 0.01): ratio 90. House number equal (m = 0.8, u = 0.05): ratio 16. Street word equal (m = 0.85, u = 0.10): ratio 8.5. Posterior odds = (1/9) × 90 × 16 × 8.5 = 1,360, so the probability is 1,360 / 1,361 = 0.9993. In logs: −2.20 + 4.50 + 2.77 + 2.14 = 7.21.

**Shifting a logit.** Adding `s` to the logit multiplies the odds by `exp(s)`. Our decision layer uses a shift of +0.2 (odds × 1.22) and a further −0.3 (odds × 0.74) for records that four or more S1 compete for ([methodology 4][doc]).

| p before | after +0.2 | after −0.3 | after both (net −0.1) |
|---|---|---|---|
| 0.50 | 0.550 | 0.426 | 0.475 |
| 0.75 | 0.786 | 0.690 | 0.731 |
| 0.90 | 0.917 | 0.870 | 0.891 |
| 0.99 | 0.992 | 0.987 | 0.989 |

A shift moves middle probabilities a lot and extreme ones very little, which is what you want when tuning a decision boundary.

**A raw logit is not a calibrated probability.** Read as log-odds, the 7B model's logit of −6 means `sigmoid(−6) = 0.0025`, a quarter of a percent. On labelled holdout data, 2 of the 24 confident predictions it rated at −6 or below (8.3%) were real matches [M] ([LLM page 4][adv10]). The flagged pairs are a selected group (only predictions whose stage-1 probability was above 0.99 are re-read), so the two numbers answer different questions. This is why the cut-off was fixed on labelled data and not read off a formula.

### 2.4 Random variables, expectation and variance

A **random variable** is a number that depends on chance, such as the number of true pairs in a list. Its **expectation** is the probability-weighted average of its values; its **variance** is the expected squared distance from that mean; the **standard deviation** (sd) is the square root of the variance. An **indicator** is 1 when an event happens and 0 otherwise; its expectation is the event's probability.

```
E[X] = Σ x × P(X = x)             Var(X) = E[(X - E[X])²]           sd = sqrt(Var)
E[X + Y] = E[X] + E[Y]            always, even when X and Y are dependent       (linearity)
Var(X + Y) = Var(X) + Var(Y)      only when X and Y are uncorrelated
```

**Worked example.** Three candidates for one S1 have probabilities 0.99, 0.95 and 0.60. The expected number of true ones is 0.99 + 0.95 + 0.60 = 2.54, by linearity, without knowing how the three relate. Our decision layer also allows 0.01 expected true copies outside the candidate set ([methodology 4][doc]): the summed probability of copies we never retrieved.

### 2.5 Bernoulli, binomial and Poisson-binomial

- **Bernoulli(p):** one yes/no trial, true with probability p; mean p, variance p(1 − p). A calibrated candidate pair is a Bernoulli trial.
- **Binomial(n, p):** successes in n independent trials with the same p. P(k) = C(n, k) p^k (1 − p)^(n−k); mean np, variance np(1 − p).
- **Poisson-binomial:** successes in n independent trials with different probabilities p1, ..., pn. This is our case, because every candidate has its own probability. Mean Σ pi, variance Σ pi(1 − pi), never larger than the binomial variance with the same mean.

Build the distribution one candidate at a time. Let `P_k(j)` be the probability of j successes among the first k candidates:

```
P_k(j) = P_(k-1)(j) × (1 - p_k)  +  P_(k-1)(j-1) × p_k
```

**Worked example.** Probabilities 0.9, 0.8 and 0.5.

| true pairs j | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| P(j) | 0.01 | 0.14 | 0.49 | 0.36 |

Check: j = 0 is 0.1 × 0.2 × 0.5 = 0.01; j = 3 is 0.9 × 0.8 × 0.5 = 0.36. The mean is 0.14 + 0.98 + 1.08 = 2.2 and the variance is 0.09 + 0.16 + 0.25 = 0.50, against 0.587 for a binomial with the same mean.

**Likelihood and log loss.** The probability the model gave to what happened is `p` when the label is 1 and `1 − p` when it is 0. **Maximum likelihood** picks the parameters that make the observed labels most probable; the negative average log of that probability is the **log loss** ([F03][f03], [F14][f14]).

### 2.6 Expected F0.5 of a chosen set

This is why the Poisson-binomial matters to us. For one S1, suppose we predict k candidates, of which TP are truly copies, and the S1 has T true copies in all:

```
F0.5 = 1.25 × TP / (0.25 × T + k)
       (F = 1 if T = 0 and k = 0;  F = 0 if T = 0 and k > 0, or if k = 0 and T > 0)
```

TP and T are random, so we choose the set with the highest **expected** F0.5. With independent candidates the distribution of TP comes from the recursion above, and T = TP plus the number of true copies we did not select.

**Worked example.** The candidates 0.9, 0.8 and 0.5, with no copies outside the list.

| set we predict | {0.9, 0.8} | {0.9, 0.8, 0.5} | {0.9} | {0.9, 0.5} | {0.8} | {0.8, 0.5} | {0.5} | {} |
|---|---|---|---|---|---|---|---|---|
| expected F0.5 | 0.8245 | 0.7638 | 0.7221 | 0.6728 | 0.6305 | 0.6201 | 0.3755 | 0.0100 |

Adding the 0.8 candidate to {0.9} helps (0.7221 to 0.8245). Adding the 0.5 candidate hurts (0.8245 to 0.7638). The empty set scores 1 only if nothing is true, a chance of 0.1 × 0.2 × 0.5 = 0.01. Two lessons. A candidate is worth adding only if its probability is high, about 0.75 to 0.80 (the break-even is derived in [F04][f04] section 2.7). And **the expectation of F is not F of the expectations**: plugging the expected counts (TP = 2.2, T = 2.2, k = 3) into the formula gives 0.7746 for the full set, not 0.7638. Allowing a 1% chance that one more true copy lies outside the list changes the best value only from 0.8245 to 0.8238.

The independence assumed here is an approximation: candidates of one S1 compete for the same records. Calibration cannot repair that ([calibration page][adv07]).

### 2.7 Samples, standard error, the law of large numbers and the CLT

**Intuition.** We cannot score every possible business, so we score a sample and hope it represents the rest. A sample mean is itself random: another sample would give a slightly different number.

- The **law of large numbers**: as the sample grows, the sample mean approaches the true mean.
- The **standard error** (SE) of a mean is the sd of the sample mean across repeated samples: SE = σ / √n, with σ the sd of one observation.
- The **central limit theorem** (CLT): for large n the sample mean is approximately normal with sd σ / √n, **even when single observations are not normal**.
- For a normal variable, about 68% of values lie within 1 sd of the mean, 95% within 1.96, 99.7% within 3.

**Worked example: how precise is 0.9913?** The per-S1 F0.5 is far from normal: most S1 score exactly 1 and a few score less. But the holdout averages 549,699 of them, so the CLT applies to the mean. We do not know σ, but any variable between 0 and 1 with mean μ has variance at most μ(1 − μ). With μ = 0.9913:

```
σ ≤ sqrt(0.9913 × 0.0087) = 0.0929
SE ≤ 0.0929 / sqrt(549,699) = 0.000125            95% half-width ≤ 1.96 × 0.000125 = 0.000246
```

So the local holdout score 0.9913 [M] is known to within at most ±0.00025 from sampling alone [E]; the real σ is smaller. This says nothing about whether the holdout represents the test set (France is absent), only about sampling noise.

### 2.8 Confidence intervals

A 95% **confidence interval** is a range from a procedure that, over many repetitions of the experiment, covers the true value 95% of the time. The usual form is estimate ± 1.96 × SE. The honest reading is about the procedure. It is not "the true value is inside with probability 95%": the true value is fixed, and the interval is the random thing.

**Worked example.** Our final decision layer (expected-F0.5 selection plus its three tuned settings) beat the best tuned global threshold by +0.000048, 95% interval [0.000007, 0.000091] [M] ([methodology 2.2][doc], [stacked-rules record][stack]). The interval excludes 0, so the gain is distinguishable from noise. It is also tiny, and wide: its width (0.000084) is almost twice the estimate. The implied SE is the half-width over 1.96: 0.000042 / 1.96 = 0.000021. The selection on its own gained +0.0000332 with an interval of [−0.0000075, +0.0000750] [M]: it includes 0, so by itself it was not distinguishable from noise.

**Small samples need a better interval.** Of 24 holdout predictions that the 7B rated at −6 or lower, 2 were true [M] ([LLM page 4][adv10]): 8.3%. The textbook interval p ± 1.96 sqrt(p(1 − p) / n) gives −2.7% to 19.4%, a negative share, which is nonsense. The **Wilson interval** gives 2.3% to 25.8%: with 24 cases we know little, which is why the cut-off was also checked on two halves and on random subsets.

### 2.9 Hypothesis tests and p-values

A test starts from a **null hypothesis** H0, usually "no effect". The **p-value** is the probability, if H0 were true, of a result at least as extreme as the one observed. It is not the probability that H0 is true. A **type I error** rejects a true H0 (its rate is the significance level α, often 0.05); a **type II error** misses a real effect; **power** is the chance of detecting an effect of a given size, and it grows with the sample and the effect.

**Worked example: the sign test.** A new rule changes the answer for 25 S1: 18 better, 7 worse. S1 where nothing changed carry no information. Under H0 (the rule is neutral) each changed S1 is a fair coin. The chance of 18 or more in 25 is 0.022 one-sided, 0.043 two-sided: evidence for the rule. With 14 better and 11 worse the one-sided p is 0.35: no evidence. Ignoring ties between the two systems is the paired idea of the next section in its simplest form.

**P(better) is not a p-value.** Our gate tool reports `P(better)`, the share of bootstrap resamples with a positive gain. Under the bootstrap approximation it is roughly one minus the one-sided p-value ([evaluation page 2.4][adv05]). The 7B counted twice in the mix gave +0.0000661 on India with P(better) 0.998 (p about 0.002) and +0.0000262 on the US with P(better) 0.906 (p about 0.09) [M]. The US result "failed", yet a later leaderboard estimate put the US effect at +0.000014, so not significant did not mean no effect ([evaluation page 2.6][adv05]).

### 2.10 The bootstrap and the paired bootstrap

**Intuition.** We want to know how much an estimate would vary across new samples, but we have one. The **bootstrap** treats the sample as the population: draw many new samples from the sample with replacement, recompute the statistic each time, and look at the spread (Efron 1979). Take B = 1,000 resamples; the 2.5% and 97.5% quantiles of the B values form a 95% **percentile interval**.

**Worked example (toy).** Eight S1 with per-S1 F0.5 of `1, 1, 1, 0.714, 0, 1, 0.833, 1` (mean 0.818). Three resamples, written as S1 numbers:

| resample | S1 drawn | scores | mean |
|---|---|---|---|
| 1 | 7, 3, 1, 3, 4, 7, 4, 1 | 0.833, 1, 1, 1, 0.714, 0.833, 0.714, 1 | 0.887 |
| 2 | 3, 5, 7, 6, 8, 2, 8, 1 | 1, 0, 0.833, 1, 1, 1, 1, 1 | 0.854 |
| 3 | 5, 3, 2, 6, 3, 5, 3, 2 | 0, 1, 1, 1, 1, 0, 1, 1 | 0.750 |

With 10,000 such resamples the means had an sd of 0.117 and a middle 95% from 0.55 to 0.98. With eight S1 we know very little, as the width says. **The unit of resampling is the S1**: pairs of one S1 are not independent, and the metric is a mean over S1.

**Paired.** To compare systems A and B on the same S1, form `d = F_B − F_A` per S1 and bootstrap the mean of `d`. Why this beats comparing two separate means:

```
Var(mean d) = [ Var(F_A) + Var(F_B) - 2 × Cov(F_A, F_B) ] / n
```

Both systems get the same easy S1 right, so the covariance is large and most `d` are exactly 0.

**Worked example with real numbers.** Our decision layer against the tuned threshold gained +0.0000481 with interval [+0.0000071, +0.0000912]: an SE of about 2.1e-5 and a spread of `d` of about 0.016 [E] ([evaluation page 2.4][adv05]). Unpaired, each mean has an SE of at most 0.000125 (section 2.7), so a difference of two independent means could have an SE of 0.000177, and the z-value would be at most 0.0000481 / 0.000177 = 0.27: invisible. Paired, it is 0.0000481 / 0.000021 = 2.3: visible. The observed spread of `d` implies a correlation of about 0.985 between the per-S1 scores of the two systems [E]. The SE belongs to the pair of systems compared: it is smaller when they differ on fewer S1.

**Our implementation.** `ber.eval.gates.paired_bootstrap` ([source][gates]) gives every S1 a random Poisson(1) weight in each resample. In a classic bootstrap an S1 appears Binomial(n, 1/n) times, which is almost Poisson(1) for large n. It then takes the weighted mean difference:

```python
def paired_bootstrap(d, n_boot=1000, seed=0):
    rng = np.random.default_rng(seed)
    w = rng.poisson(1.0, size=(n_boot, d.size))      # weight of every S1 in every resample
    boots = (w @ d) / w.sum(axis=1)                  # weighted mean of d per resample
    lo, hi = np.quantile(boots, [0.025, 0.975])      # 95% percentile interval
    return d.mean(), lo, hi, (boots > 0).mean()      # gain, interval, P(better)
```

The repository version works in batches of 50 resamples so that 1,000 resamples over 550k S1 need little memory. **The bootstrap does not cover** training randomness (rebuilding a model on other hardware moved the holdout from 0.991246 to 0.991261 [M]), distribution shift (France, different test pools), or repeated reuse of one holdout ([evaluation page 2.4][adv05]).

### 2.11 Effect size versus statistical significance

**Significance** says an effect is distinguishable from zero; **effect size** says how big it is. With a big sample a trivial effect can be significant. Report both.

**Translate effects into S1.** The holdout has 549,699 S1, so 1e-5 of macro F0.5 is about 5.5 S1 flipping from wrong to right; on the 1,732,544 test S1 it is about 17. The 7B re-check at −6 gained +0.000037 on the holdout [M]: about 20 holdout S1, or about 64 test S1 [E]. Real, small, and worth having because it was cheap and passed its gates.

**What can this holdout resolve?** The SE of a paired difference is `SD(d) / sqrt(n)`. With `SD(d)` = 0.016 and n = 549,699 it is 2.2e-5, so effects below about 4e-5 cannot be separated from zero by this comparison alone. To resolve 1e-5 (z = 2) you need an SE of 5e-6, which takes (0.016 / 5e-6)² = 10 million S1, 19 times the holdout. The team's estimate is that leaderboard gaps below about 0.00005 between near-identical candidates are noise [E] ([evaluation page 2.5][adv05]). A change that touches few S1, like the re-check, has a much smaller `SD(d)`, so smaller effects can be seen.

### 2.12 Multiple comparisons and selection bias

Run enough tests and something looks significant by luck.

```
P(at least one false alarm among m independent tests at α = 0.05) = 1 - 0.95^m
m = 5: 23%     m = 10: 40%     m = 20: 64%     m = 50: 92%
```

**Corrections.** **Bonferroni** tests each at α / m. **Holm** is a step-down version that is never worse. **Benjamini–Hochberg** controls the false discovery rate, the expected share of false alarms among the declared discoveries.

**The winner's curse.** Pick the best of m variants and its estimate is biased upward. If all variants had no true effect and noise of 1 SE each, the best of 5, 10, 20, 50 and 100 would look 1.16, 1.54, 1.87, 2.25 and 2.51 SE better than zero on average. The "garden of forking paths" (Gelman and Loken 2013) adds that every data-dependent choice is an implicit comparison, even without deliberate fishing.

**What we did** ([evaluation page 2.6][adv05]): gate rules were written before the run, in decision records; the paired bootstrap interval had to sit above zero, and late changes also had to be positive on both halves of the holdout; ties went to the simpler option. A live example of the curse: the stage-3 prototype was the best of three variants (+0.00011 on the holdout) and gave +0.00005 once rebuilt as a pipeline step [M].

**The leaderboard.** We had 5 uploads a day, and choosing among many uploads by the public score overfits the public subset. The organisers publish only rankings for the private leaderboard, so **no private-leaderboard score exists** for us and we cannot compute the public-to-private gap. We relied on the labelled holdout for US and India decisions and used the leaderboard as an outside check.

---

## 3. How it shows up in our project

- **Logit shifts and the Poisson-binomial recursion:** the decision layer uses +0.2, −0.3 and 0.01 outside mass, and the per-S1 expected-F0.5 selection handles at most 48 candidates and 16 set sizes per S1 ([methodology 4][doc], [calibration page 2.4][adv07], [scaling page 2.2][adv11]).
- **Paired bootstrap:** every gate in [`ber.eval.gates`][gates]; keep a component when the mean gain is large enough and the 95% interval is above zero.
- **Halves and subsets:** the 7B re-check was checked on two halves and on 3,000 random 25% subsets and was positive in 99.7% of them [M] ([LLM page 4][adv10]).
- **Leaderboard arithmetic:** the public score is a weighted average of per-country scores, so France can be backed out ([F04][f04] section 2.12).
- **Selection bias:** the stage-3 prototype, and an India-only prior picked from about 160 variants that lowered the US on every model, so it was not used ([evaluation page 2.6][adv05]).

---

## 4. How to read the numbers

| number | scope and level | how to read it | what it does not tell you |
|---|---|---|---|
| 0.9913 | local holdout, 549,699 S1, macro F0.5 [M] | sampling noise at most ±0.00025 [E] | whether France behaves the same |
| +0.000048 [0.000007, 0.000091] | whole decision layer against a tuned threshold, holdout, paired bootstrap [M] | real but tiny, SE about 2.1e-5 [E]; the selection alone was +0.000033 [−0.000008, +0.000075] | training randomness, reuse of the holdout |
| P(better) 0.998 and 0.906 | 7B counted twice, India and US [M] | roughly one minus the one-sided p-value | effect size; that 0.906 means "no effect" |
| 8.3% | 2 of 24 holdout predictions below −6 [M] | Wilson interval 2.3% to 25.8% [E] | the true share |
| 99.7% of 3,000 random 25% subsets | re-check gain positive [M] | the gain is consistent | independence: the subsets overlap |
| 0.990879 | public LB, macro F0.5 on the public part of test [M] | one draw, no error bar given | the private score, which does not exist for us |

---

## 5. Common misconceptions

1. **"A p-value is the probability that the null hypothesis is true."** It is the probability of data this extreme if the null were true.
2. **"A 95% interval contains the true value with 95% probability."** The 95% describes the procedure over repeated samples.
3. **"Not significant means no effect."** It means the data could not rule out zero. The 7B in the mix had P = 0.906 on the US and a later estimate of +0.000014.
4. **"Significant means important."** With 549,699 S1, effects of 1e-5 can be significant and are worth about 5 S1.
5. **"Uncorrelated means independent."** Independence is stronger: a variable and its square can be uncorrelated yet fully dependent.
6. **"The model's probability is the truth."** Only if calibrated, and even then candidates of one S1 are not independent.
7. **"Test many variants, keep the best: each test is valid, so the result is fine."** Each test is valid, but the winner is selected, so its estimate is biased upward.

---

## 6. Check yourself

**1.** A feature fires for 90% of true pairs and 10% of look-alikes. If 50% of candidates are true, what is P(true | fired)? What if 1% are true?

<details><summary>Answer</summary>

0.9 × 0.5 / (0.9 × 0.5 + 0.1 × 0.5) = 0.45 / 0.50 = 0.90. At a prior of 0.01: 0.009 / (0.009 + 0.099) = 0.083. The same evidence gives 90% in one pool and 8% in a pool where true pairs are rare. A score learned at one prior needs checking at another.

</details>

**2.** Convert p = 0.9 to odds and logit. Apply the +0.2 shift, then the further −0.3, and convert back.

<details><summary>Answer</summary>

Odds 9; logit ln 9 = 2.197. After +0.2: 2.397, probability 1 / (1 + e^−2.397) = 0.917. After a further −0.3: 2.097, probability 0.891. The net change is small because 0.9 is near the flat part of the sigmoid; the same net −0.1 applied to 0.5 gives 0.475.

</details>

**3.** What probability does a logit of −6 correspond to, and why did we not rely on that reading for the 7B re-check?

<details><summary>Answer</summary>

sigmoid(−6) = 1 / (1 + e^6) = 0.0025. On labelled holdout data, 2 of 24 pairs rated at −6 or below (8.3%, Wilson interval about 2% to 26%) were true. A raw model score is not a calibrated probability, and the flagged pairs are a selected group. So the cut-off was fixed on labelled data, not read off the formula.

</details>

**4.** Candidates have probabilities 0.9, 0.7 and 0.4. What is the probability that exactly two are true, and the expected number of true ones?

<details><summary>Answer</summary>

Exactly two: 0.9 × 0.7 × 0.6 + 0.9 × 0.3 × 0.4 + 0.1 × 0.7 × 0.4 = 0.378 + 0.108 + 0.028 = 0.514. Expected number: 0.9 + 0.7 + 0.4 = 2.0 (the sum of the probabilities, by linearity).

</details>

**5.** Using the table in section 2.6, which set maximises expected F0.5, and which candidate would you remove from the three-candidate set?

<details><summary>Answer</summary>

{0.9, 0.8} with 0.8245. Removing the 0.5 candidate raises the expectation from 0.7638 to 0.8245. A 0.5 candidate is below the break-even of about 0.75 to 0.80, so its expected harm (a false merge costs 2 to 3 times a miss at typical set sizes, see [F04][f04]) exceeds its expected gain.

</details>

**6.** The holdout has 549,699 S1 and macro F0.5 0.9913. Give an upper bound for the standard error from sampling alone.

<details><summary>Answer</summary>

A variable on [0, 1] with mean μ has sd at most sqrt(μ(1 − μ)) = sqrt(0.9913 × 0.0087) = 0.0929. So SE ≤ 0.0929 / sqrt(549,699) = 0.000125, and the 95% half-width is at most 0.000246. The true sd is smaller because most S1 score exactly 1.

</details>

**7.** Why is the paired bootstrap interval for +0.000048 so much narrower than an unpaired comparison would give?

<details><summary>Answer</summary>

The two systems agree on nearly all S1, so the per-S1 difference is 0 for most. Var(mean d) = [Var(A) + Var(B) − 2 Cov(A, B)] / n and the covariance is almost as large as the variances, so the difference has tiny variance. The observed spread of d (about 0.016) implies a correlation of about 0.985. Unpaired, the effect is buried in the spread of the scores themselves (SE up to 0.000177 against 0.000021 paired).

</details>

**8.** A new rule changes 25 S1: 18 better, 7 worse. Is it better? What if 14 better and 11 worse? What does the sign test ignore?

<details><summary>Answer</summary>

Sign test with H0 "each changed S1 is a fair coin": 18 of 25 gives one-sided p = 0.022 (two-sided 0.043), evidence for the rule; 14 of 25 gives p = 0.35, no evidence. The sign test uses only direction, not size: 18 tiny gains and 7 large losses could still be a net loss. The paired bootstrap uses the sizes too.

</details>

**9.** You run 20 independent comparisons and keep each with p below 0.05. If all 20 true effects are zero, what is the chance of at least one false discovery, and what is the Bonferroni threshold?

<details><summary>Answer</summary>

1 − 0.95^20 = 0.64. Bonferroni tests each at 0.05 / 20 = 0.0025. The best of 20 null estimates also looks about 1.87 SE better than zero on average: the winner's curse.

</details>

**10.** Why do we resample S1 and not pairs in the bootstrap?

<details><summary>Answer</summary>

Pairs of one S1 share the S1 and compete for the same records, so they are not independent, and the metric is a mean over S1. Resampling pairs would treat about 3.7 related pairs per S1 as independent observations and make the interval too narrow. Resampling whole S1 mirrors the metric.

</details>

---

## 7. Going deeper

- Wasserman (2004), "All of Statistics", Springer; Blitzstein and Hwang (2019), "Introduction to Probability", 2nd edition, CRC Press.
- Efron (1979), "Bootstrap methods: another look at the jackknife", Annals of Statistics; Efron and Tibshirani (1993), "An Introduction to the Bootstrap", Chapman & Hall.
- Wasserstein and Lazar (2016), "The ASA statement on p-values: context, process, and purpose", The American Statistician.
- Brown, Cai and DasGupta (2001), "Interval estimation for a binomial proportion", Statistical Science; Benjamini and Hochberg (1995), "Controlling the false discovery rate", JRSS B; Holm (1979), "A simple sequentially rejective multiple test procedure", Scandinavian Journal of Statistics.
- Gelman and Loken (2013), "The garden of forking paths", working paper; Blum and Hardt (2015), "The Ladder: a reliable leaderboard for machine learning competitions", ICML; Dwork et al. (2015), "The reusable holdout: preserving validity in adaptive data analysis", Science.
- Koehn (2004), "Statistical significance tests for machine translation evaluation", EMNLP. The paired bootstrap for comparing systems.

## 8. Where next

- [F03 Machine learning fundamentals][f03]: log loss, out-of-fold predictions and leakage.
- [F04 Classification metrics][f04]: F0.5 from the count form, thresholds, calibration curves.
- [F09 Experiments and evidence][f09]: designing the comparisons whose numbers you can now read.
- Advanced pages [05 evaluation][adv05], [04 metrics and decisions][adv04], [07 calibration][adv07].
- The track map: [foundations README](README.md).

[doc]: ../../../experiments/ameya/final-zip/doc/Documentation_template.md
[gates]: ../../../code/business_entity_resolution/src/ber/eval/gates.py
[stack]: ../../../docs/decisions/2026-09-27_0636_stacked-rules.md
[adv01]: ../01-entity-resolution.md
[adv04]: ../04-metrics-and-decisions.md
[adv05]: ../05-evaluation-methodology.md
[adv07]: ../07-calibration.md
[adv09]: ../09-self-training-and-domain-shift.md
[adv10]: ../10-llm-verification-and-compute.md
[adv11]: ../11-scaling-to-billions.md
[f01]: F01-data-and-problem.md
[f03]: F03-machine-learning-fundamentals.md
[f04]: F04-classification-metrics.md
[f09]: F09-experiments-and-evidence.md
[f14]: F14-information-theory-and-losses.md
