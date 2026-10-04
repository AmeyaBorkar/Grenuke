# F14. Information theory and losses

**Summary**

- Information theory gives one currency, bits or nats, for surprise, uncertainty and loss. Entropy measures uncertainty, cross-entropy is the loss we train on, and KL divergence is the gap between belief and reality.
- Log loss and the Brier score are proper scoring rules: they reward honest probabilities. Our per-S1 decision step maximises expected F0.5, so it needs calibrated probabilities, not just a good ranking.
- Softmax, sigmoid, temperature, logit shifts, sample weights and perplexity are the same toolbox seen from different sides. We use logits everywhere, a +0.2 logit shift in the decision layer, and weight 3 on French pseudo-labelled rows.

## What you need first

- [F02 probability and statistics](F02-probability-and-statistics.md): expectation, conditional probability, logarithms.
- [F03 machine learning fundamentals](F03-machine-learning-fundamentals.md): a loss function and training.
- [F04 classification metrics](F04-classification-metrics.md): precision, recall and AUC, for contrast with the losses here.

---

## 1. Surprise and entropy

**Intuition.** Rare events are more surprising. Learning that a fair coin landed heads is mild news; learning that a 1-in-1024 event happened is big news.

**Definition.** The **surprise** of an event with probability $p$ is $-\log p$. In base 2 the unit is the **bit**; in base $e$ it is the **nat**. One nat is 1.4427 bits. The **entropy** of a distribution is the expected surprise:

$$H(p)=-\sum_i p_i\log p_i .$$

For a yes/no event with probability $p$: $H(p)=-p\log p-(1-p)\log(1-p)$. It is 0 when the outcome is certain and largest at $p=0.5$ (1 bit, 0.693 nats).

| $p$ | 0.01 | 0.05 | 0.1 | 0.3 | 0.5 |
|---|---|---|---|---|---|
| bits | 0.081 | 0.286 | 0.469 | 0.881 | 1.000 |
| nats | 0.056 | 0.199 | 0.325 | 0.611 | 0.693 |

**Worked example from our data.** An S1 has 3.46 true copies on average, and retrieval returns about 34 candidates per S1. So roughly one retrieved pair in ten is a true copy (a derived estimate: $3.46/34$). The entropy of that base rate is 0.469 bits, or 0.325 nats. A model must beat a log loss of 0.325 nats to know anything beyond the base rate. In the final candidate file there are 3.70 candidates per S1 against 3.46 true copies, so most candidates are true, and the prior is much less uncertain.

## 2. Cross-entropy and log loss

**Intuition.** Suppose reality follows distribution $p$ but your model believes $q$. The cross-entropy is the average surprise you actually feel.

**Definition.** $H(p,q)=-\sum_i p_i\log q_i$. For a binary label $y\in\{0,1\}$ and a predicted match probability $\hat p$, the loss of one example is

$$\ell(y,\hat p)=-\big[y\ln\hat p+(1-y)\ln(1-\hat p)\big],$$

and the **log loss** is its average over the data. Minimising it equals maximising the likelihood of the labels under the model.

**Worked example.**

| true label | predicted $\hat p$ | loss (nats) |
|---|---|---|
| 1 | 0.99 | 0.010 |
| 1 | 0.9 | 0.105 |
| 1 | 0.5 | 0.693 |
| 1 | 0.1 | 2.303 |
| 1 | 0.001 | 6.908 |
| 0 | 0.99 | 4.605 |

Being confidently wrong ($\hat p=0.99$ on a non-match) costs about 460 times what being confidently right costs. The loss punishes overconfidence hard. A log loss of 0.05 means the model puts on average $e^{-0.05}=0.95$ on the true label.

**Gradient with respect to the logit.** Let $z$ be the logit and $\hat p=\sigma(z)$. Because $\sigma'(z)=\hat p(1-\hat p)$, the loss has the simple slope $\partial\ell/\partial z=\hat p-y$ and curvature $\partial^2\ell/\partial z^2=\hat p(1-\hat p)$. These are the $g$ and $h$ that XGBoost uses ([F05](F05-trees-and-ensembles.md)), and the slope that backpropagation starts from ([F07](F07-neural-networks-transformers-llms.md)).

**Where we use it.** XGBoost runs with `binary:logistic` and `eval_metric` logloss; early stopping watches it. The cross-encoders use binary cross-entropy on one logit (`BCEWithLogitsLoss`). It computes the loss straight from $z$ as $\max(z,0)-zy+\ln(1+e^{-|z|})$, which never overflows, instead of first forming $\hat p$ and then its log.

## 3. KL divergence

**Definition.** The **Kullback-Leibler divergence** is

$$D_{KL}(p\Vert q)=\sum_i p_i\log\frac{p_i}{q_i}=H(p,q)-H(p)\ \ge 0 ,$$

and it is 0 only when $p=q$. It is not symmetric. Since $H(p)$ is fixed by reality, minimising cross-entropy over $q$ is the same as minimising $D_{KL}(p\Vert q)$.

**Worked example.** Let $p$ be a coin with 0.1 and $q$ a coin with 0.5. $D_{KL}(p\Vert q)=0.1\ln0.2+0.9\ln1.8=0.368$ nats, and the other direction is 0.511. Check: $H(p)+D_{KL}=0.325+0.368=0.693=H(p,q)$, which is just $\ln2$ because $q$ is a fair coin.

Uses: distillation (a student matches a teacher's output distribution), drift measures (compare feature distributions in France with those in the US and India, [F10](F10-semi-supervised-and-domain-shift.md)), and the tie between loss and likelihood above.

## 4. Mutual information

**Definition.** $I(X;Y)=H(Y)-H(Y\mid X)=D_{KL}\big(p(x,y)\,\Vert\,p(x)p(y)\big)$. It is how many bits knowing $X$ saves about $Y$. It is zero when $X$ and $Y$ are independent.

**Worked example.** In [F05](F05-trees-and-ensembles.md) a split on "house number found in the record" took a node from 0.971 bits of label entropy to 0.361 bits. The information gain of 0.610 bits is the mutual information between that answer and the label at the node: it removes $0.610/0.971=63\%$ of the uncertainty.

**Caution.** Mutual information is hard to estimate for continuous variables, and a feature that carries information may add nothing once other features are known (redundancy).

## 5. Gini versus entropy

Both measure how mixed a node is. For a node with match share $p$: Gini $=2p(1-p)$ and entropy as above.

| $p$ | 0.01 | 0.1 | 0.3 | 0.5 |
|---|---|---|---|---|
| Gini | 0.020 | 0.180 | 0.420 | 0.500 |
| entropy (bits) | 0.081 | 0.469 | 0.881 | 1.000 |
| Gini as share of its maximum | 4% | 36% | 84% | 100% |
| entropy as share of its maximum | 8% | 47% | 88% | 100% |

Both are concave with the same peak. Entropy is steeper near the pure ends: it treats a 10% node as 47% of maximally impure, Gini as 36%. Gini avoids the logarithm, so it is cheaper. In practice they usually choose the same split.

XGBoost uses neither directly. But the hessian of the log loss is $h=p(1-p)$, which is exactly half the Gini impurity of a Bernoulli($p$). So `min_child_weight`, a sum of hessians, is a sum of half-Gini values: a leaf of near-certain pairs adds almost nothing to it.

## 6. Proper scoring rules and calibration

**Definition.** A **scoring rule** $S(\hat p,y)$ grades a probability forecast. It is **proper** if the expected score is best when you report your true belief $q$, and **strictly proper** if only then. Log loss and the **Brier score** $(\hat p-y)^2$ are strictly proper (Brier 1950; Gneiting and Raftery 2007). Accuracy at a threshold is not, and AUC is not a score of probabilities at all: it depends only on the ranking.

**Worked example.** Suppose the true match probability for a kind of pair is $q=0.7$. Expected loss if you report $r$:

| report $r$ | 0.5 | 0.6 | 0.7 | 0.8 | 0.9 |
|---|---|---|---|---|---|
| expected log loss | 0.693 | 0.633 | 0.611 | 0.639 | 0.765 |
| expected Brier | 0.250 | 0.220 | 0.210 | 0.220 | 0.250 |

Both are lowest at the honest report 0.7. Optimising a proper score therefore pushes a model towards **calibration**: among pairs given probability 0.8, about 80% should be true matches.

**Ranking is not calibration.** Ten pairs, four true. Scores for the true ones: 0.95, 0.9, 0.8, 0.4. Scores for the others: 0.6, 0.3, 0.2, 0.1, 0.05, 0.02. The AUC is 0.958, log loss 0.297, Brier 0.092. Cube the scores ($p^3$, a monotone change): AUC is still 0.958, but log loss rises to 0.417 and Brier to 0.126. With $\sqrt p$: 0.431 and 0.142. A model can rank well and still give poor probabilities.

**Measuring calibration.** A **reliability table** groups predictions into bins and compares the mean prediction with the observed share of true pairs. The **expected calibration error** is $\sum_b \frac{n_b}{n}\,\lvert\text{observed}_b-\text{predicted}_b\rvert$. Toy example: 100 pairs predicted about 0.10 with 8% true, 50 pairs at 0.50 with 60% true, 150 pairs at 0.95 with 93% true. The error is $(100\times0.02+50\times0.10+150\times0.02)/300=0.033$. In the v3 dev kit our calibrated stage-2 probability was reliable to within about 0.01 per bin on the holdout ([FEATURES.md](../../../experiments/ameya/model-v1/FEATURES.md)).

**How isotonic regression works.** Sort the pairs by score and take their labels in that order. Wherever the running average goes down, pool the offending neighbours and replace them by their mean (the pool adjacent violators algorithm). Example: labels 0, 1, 0, 0, 1, 1. The pair (1, 0) is out of order, so pool to 0.5, 0.5. Then 0.5 exceeds the next 0, so pool the three into 0.33, 0.33, 0.33. The result 0, 0.33, 0.33, 0.33, 1, 1 is a non-decreasing staircase, the closest one to the labels in squared error. Applied to scores, it is the calibration map.

**Why our decision step needs it.** For each S1 a small dynamic programme picks the set of records with the highest expected F0.5 given each record's probability ([04 metrics and decisions](../04-metrics-and-decisions.md)). Expected F is computed from the probabilities, so mis-scaled ones give wrong sets. The record shows it: in the v3 dev kit the rule gained +0.00011 over the best global threshold on calibrated stage-2 probabilities, and lost 0.00029 on stage-1 probabilities ([FEATURES.md](../../../experiments/ameya/model-v1/FEATURES.md)). Calibration is done with isotonic regression, a monotone step function fitted on out-of-fold predictions from training folds, never on the holdout ([s2.py](../../../experiments/ameya/model-v1/s2.py), [07 calibration](../07-calibration.md)).

## 7. Sigmoid, softmax, temperature, logit shifts

**Definitions.** The **logit** of $p$ is $\ln\frac{p}{1-p}$ (log-odds). The **sigmoid** $\sigma(z)=1/(1+e^{-z})$ is its inverse. For several classes, **softmax** turns scores $z_i$ into probabilities $e^{z_i}/\sum_j e^{z_j}$. The sigmoid is a softmax over $(z,0)$. Dividing the scores by a **temperature** $T$ before softmax sharpens ($T<1$) or flattens ($T>1$) the result.

**Worked example.** Scores $(2,1,0)$:

| $T$ | probabilities |
|---|---|
| 0.5 | 0.867, 0.117, 0.016 |
| 1 | 0.665, 0.245, 0.090 |
| 2 | 0.507, 0.307, 0.186 |

Stability: the naive softmax of $(1000,1001)$ overflows to NaN; subtracting the maximum first gives $(0.269,0.731)$. Temperature scaling (Guo et al. 2017) fits one $T$ on validation data to calibrate a network's logits. It keeps the ranking, so AUC is unchanged.

**Logit shifts.** Adding $c$ to a logit multiplies the odds by $e^{c}$. Our decision layer has a logit shift of +0.2 (odds $\times1.22$) and a further $-0.3$ (odds $\times0.74$) for records that four or more S1 compete for, both tuned on the local holdout ([method note](../../../experiments/ameya/final-zip/doc/Documentation_template.md)).

| $p$ | after +0.2 | after $-0.3$ |
|---|---|---|
| 0.5 | 0.550 | 0.426 |
| 0.7 | 0.740 | 0.634 |
| 0.9 | 0.917 | 0.870 |
| 0.99 | 0.992 | 0.987 |

The nudges matter near the middle and almost vanish near the ends.

**Evidence adds in logit space.** If pieces of evidence are independent, posterior odds equal prior odds times the likelihood ratio of each piece, so in logits the evidence simply adds. This is the idea behind Fellegi-Sunter weights ([01 entity resolution](../01-entity-resolution.md)). Toy example with made-up ratios: prior 10% (odds 0.111, logit $-2.20$). Equal house number: $\times50$. A shared rare name word: $\times20$. Odds become 111, so $p=0.991$. Now add an extra look-alike word with ratio $\times0.0001$: odds 0.0111, $p=0.011$. One strong piece of negative evidence flips the verdict. Our look-alike word table stores this kind of number: the log-odds of a true match when a word is extra in the record is $-9.8$ for "holdings" and $-9.7$ for "group" ([FEATURES.md](../../../experiments/ameya/model-v1/FEATURES.md)). That is also why the French "groupe" bias in [F05](F05-trees-and-ensembles.md) was so costly: a wrong value of $-4.84$ on a word that is common in true names subtracts several logits at once.

## 8. Class weights and sample weights

**Definition.** A weighted loss is $\sum_i w_i\,\ell_i\big/\sum_i w_i$.

**Class weights shift the prior.** Give positives weight $w$. For a pair with true probability $p$, minimising $p\,w\,(-\ln q)+(1-p)(-\ln(1-q))$ gives $q^\star=wp/(wp+1-p)$, so the model's odds are $w$ times the true odds: a logit shift of $\ln w$ (1.10 for $w=3$, 1.61 for $w=5$). With $w=4$, a pair truly at 0.2 is reported at 0.5. This is why class weights hurt calibration, and why we calibrate afterwards.

**Sample weights count rows more.** Our French pseudo-labelled rows get weight 3 for positives and negatives alike (option `--pseudo-weight` in [s2.py](../../../experiments/ameya/model-v1/s2.py)). Equal weights on both classes do not shift the prior. They make each French row count as three in the loss, as if it appeared three times, so the French domain has more say next to the labelled US and India rows. The cost is a smaller **effective sample size** (Kish): $n_\text{eff}=(\sum w)^2/\sum w^2$. For 10 rows of weight 1 and 5 rows of weight 3: $625/55=11.4$ of 15. Raising the weight to 5 gave the same estimated gain as 3 (+0.000167 against +0.000166, [RESEARCH_v6](../../../experiments/ameya/model-v1/RESEARCH_v6.md)), so more weight added nothing.

**Undoing a prior.** The same arithmetic runs backwards. If the share of true pairs among candidates changes between training and test, calibrated odds should be multiplied by the ratio of the new prior odds to the old (Saerens et al. 2002). Hypothetical numbers: the share falls from 10% to 8%. Prior odds go from $0.1/0.9=0.111$ to $0.08/0.92=0.087$, a ratio of 0.78, which is a logit shift of $-0.245$. This is the same kind of correction as the logit shifts above, but ours were tuned empirically on the holdout, not derived from a prior.

Importance weights $p_\text{target}(x)/p_\text{source}(x)$ correct covariate shift ([F10](F10-semi-supervised-and-domain-shift.md)).

## 9. Perplexity

**Definition.** For a language model, $\text{PPL}=\exp\!\big(-\tfrac1N\sum_t\ln p(x_t\mid x_{<t})\big)$: the exponential of the cross-entropy in nats, or $2^{\text{bits per token}}$. Read it as the number of equally likely choices the model is torn between at each step.

**Worked example.** A model gives three tokens probabilities 0.2, 0.5 and 0.1. The mean loss is 1.535 nats, so PPL $=e^{1.535}=4.64$, which is also the geometric mean of $5,2,10$. A model that spreads probability evenly over 4 options has PPL 4 (2 bits per token).

Qwen was pre-trained by minimising this next-token cross-entropy ([F07](F07-neural-networks-transformers-llms.md)). Our fine-tuning swaps it for a binary cross-entropy on one logit. We never use perplexity operationally. Compare it only between models with the same tokeniser and text, since "per token" changes with the tokeniser.

---

## How it shows up in our project

- Training and stopping on log loss: [s1.py](../../../experiments/ameya/model-v1/s1.py), [s2.py](../../../experiments/ameya/model-v1/s2.py), [ce.py](../../../experiments/ameya/model-v1/ce.py).
- Calibration and the decision rule: [07 calibration](../07-calibration.md), [04 metrics and decisions](../04-metrics-and-decisions.md), `decide.py` in [model-v1](../../../experiments/ameya/model-v1/).
- Weights: `--pseudo-weight` in [s2.py](../../../experiments/ameya/model-v1/s2.py). Logit arithmetic: [zmean_ce.py](../../../experiments/ameya/model-v1/zmean_ce.py).

## How to read the numbers

- **Log loss 0.325 nats** is what you get by always predicting a 10% base rate. Lower is a real skill.
- **Nats and bits.** Divide nats by 0.693 to get bits.
- **Brier 0.092** (ten-pair example) is the mean squared gap between probability and outcome; always predicting 0.5 scores 0.25.
- **AUC and log loss answer different questions.** AUC: does it rank well? Log loss: are the probabilities honest?
- **A +0.2 logit shift** is small: at most about 0.05 in probability.

## Common misconceptions

1. "Entropy measures information content of a message." It measures uncertainty about the outcome, averaged.
2. "KL divergence is a distance." It is not symmetric and fails the triangle inequality.
3. "High AUC means calibrated." AUC ignores scale.
4. "Accuracy is a fine score for probabilities." It is not proper, and ignores confidence.
5. "Class weights fix imbalance for free." They shift the odds and break calibration unless corrected.
6. "Temperature changes which class wins." For a single softmax it does not; it changes confidence.
7. "Lower perplexity always means a better model." Only for the same tokeniser and data.

## Check yourself

Exercise 1. What is the entropy of a coin with $p=0.25$, in bits?

<details><summary>Answer</summary>

$-(0.25\log_2 0.25+0.75\log_2 0.75)=0.5+0.311=0.811$ bits.

</details>

Exercise 2. Two predictions of 0.8: one on a true match, one on a non-match. Mean log loss?

<details><summary>Answer</summary>

$-\ln0.8=0.223$ and $-\ln0.2=1.609$. Mean $=0.916$.

</details>

Exercise 3. Compute $D_{KL}(\text{Bern}(0.2)\Vert\text{Bern}(0.5))$ in nats.

<details><summary>Answer</summary>

$0.2\ln(0.2/0.5)+0.8\ln(0.8/0.5)=0.2(-0.916)+0.8(0.470)=-0.183+0.376=0.193$.

</details>

Exercise 4. The true probability is 0.9. Expected Brier score when reporting 0.9 and when reporting 1.0?

<details><summary>Answer</summary>

Reporting 0.9: $0.9(0.1)^2+0.1(0.9)^2=0.009+0.081=0.090$. Reporting 1.0: $0.9\cdot0+0.1\cdot1=0.100$. The honest report is better.

</details>

Exercise 5. For $p=0.3$, compare the Gini impurity with the log-loss hessian $h=p(1-p)$.

<details><summary>Answer</summary>

Gini $=2(0.3)(0.7)=0.42$. $h=0.21$, exactly half.

</details>

Exercise 6. A pair has $p=0.8$. Apply the +0.2 shift, then the extra $-0.3$. New probabilities?

<details><summary>Answer</summary>

$\text{logit}(0.8)=1.386$. After +0.2: 1.586, $p=0.830$. After a further $-0.3$: 1.286, $p=0.7835$.

</details>

Exercise 7. Positives get weight 4. A group of pairs is truly 20% matches. What probability does the weighted model report?

<details><summary>Answer</summary>

Odds $0.2/0.8=0.25$, times 4 is 1, so $p=0.5$. A shift of $\ln4=1.39$ logits.

</details>

Exercise 8. Ten rows have weight 1 and five have weight 3. Effective sample size?

<details><summary>Answer</summary>

$\sum w=25$, $\sum w^2=10+45=55$, $n_\text{eff}=625/55=11.4$ of 15 rows.

</details>

Exercise 9. A language model gives probabilities 0.2, 0.5, 0.1 to three tokens. Perplexity?

<details><summary>Answer</summary>

Mean $-\ln p=(1.609+0.693+2.303)/3=1.535$; PPL $=e^{1.535}=4.64$.

</details>

Exercise 10. A model has AUC 0.99 but outputs only values between 0.4 and 0.6. Is it useful for our decision step?

<details><summary>Answer</summary>

It ranks well, but the expected-F0.5 step needs probabilities. Values in 0.4 to 0.6 would say "unsure" about everything and lead to wrong sets. Calibration (for example isotonic regression) can stretch them into honest probabilities without changing the ranking.

</details>

Exercise 11. Softmax of scores $(3,1)$ at $T=1$ and $T=2$?

<details><summary>Answer</summary>

$T=1$: $(0.881,0.119)$. $T=2$ (scores become $(1.5,0.5)$): $(0.731,0.269)$. Higher temperature, less confidence; the winner is unchanged.

</details>

## Going deeper

- Shannon (1948). A mathematical theory of communication.
- Kullback and Leibler (1951). On information and sufficiency.
- Cover and Thomas (2006). Elements of Information Theory. MacKay (2003). Information Theory, Inference, and Learning Algorithms.
- Brier (1950). Verification of forecasts expressed in terms of probability. Gneiting and Raftery (2007). Strictly proper scoring rules, prediction, and estimation.
- Guo et al. (2017). On calibration of modern neural networks.
- Niculescu-Mizil and Caruana (2005). Predicting good probabilities with supervised learning.
- Hinton, Vinyals and Dean (2015). Distilling the knowledge in a neural network.
- Elkan (2001). The foundations of cost-sensitive learning. Saerens, Latinne and Decaestecker (2002). Adjusting the outputs of a classifier to new a priori probabilities: a simple procedure.
- Jelinek, Mercer, Bahl and Baker (1977). Perplexity: a measure of the difficulty of speech recognition tasks.

## Where next

- [F11 decision theory and optimisation](F11-decision-theory-and-optimisation.md): from probabilities to decisions.
- [F18 tuning, ensembles and interpretability](F18-tuning-ensembles-and-interpretability.md): averaging logits across models.
- [07 calibration](../07-calibration.md) and [04 metrics and decisions](../04-metrics-and-decisions.md).
