# F03. Machine learning fundamentals, as used in this project

**Summary.**
- Supervised learning fits a function to labelled examples. The hard part is not the fitting but knowing whether the result will work on data it has not seen.
- This page covers train, validation and test, over- and underfitting, bias and variance, regularisation, log loss, gradient descent, out-of-fold predictions, leakage (and why we split by S1, not by pair), class imbalance and baselines.
- It ties back to one design rule of ours: train for probabilities, then decide for the metric.

Tier P1. About 2.5 hours in full, about 1.25 hours on the fast path (sections 2.6, 2.8, 2.9, 2.10 and 2.11). Prepares you for the advanced pages [05 evaluation][adv05], [06 boosting and stacking][adv06] and [07 calibration][adv07].

---

## 1. What you need first

[F01][f01] for the vocabulary (S1, copies, candidates) and [F02][f02] sections 2.1 to 2.3 (probability, odds, logit). A little numpy helps to run the code. Evidence levels: **M** measured, **E** estimated or derived, **R** reported. "Toy" means made-up numbers for practice.

---

## 2. The concepts from zero

### 2.1 Supervised learning and the pair classifier

**Intuition.** Show the computer many examples where the answer is known, let it find a rule, then use the rule where the answer is unknown.

**Definitions.** An **example** has **features** `x` (numbers that describe it) and a **label** `y` (the answer). A **model** `f` with **parameters** (weights) `θ` maps `x` to a prediction. A **loss** `L(y, f(x))` scores one mistake. **Training** chooses `θ` to minimise the average loss over the training examples. **Hyperparameters** are settings that we choose and the training loop does not learn: tree depth, learning rate, regularisation strength.

**In our project.** An example is a **candidate pair** (an S1 record and an S2/S3 record). The features are about 100 numbers: name similarities, house-number equality, ranks among rivals and more ([methodology 4][doc]). The label is 1 if the pair is in the ground truth. The model outputs the probability that the pair is a match. This turns "find the copies of S1" into "classify pairs". It is not the whole story, because the right answer for a pair depends on the other candidates, which is why later stages add context features and a per-S1 decision ([F11][f11]).

**Worked example (toy).** Four candidate pairs for S1 "Acme Robotics Inc, 500 Market St", with a hand-made model `z = 4 × name Jaccard + 2 × house number equal + 2 × street word equal − 3`, `p = sigmoid(z)` (Jaccard is the number of words the two names share divided by the number of distinct words in both):

| candidate | Jaccard | number | street | label | z | p |
|---|---|---|---|---|---|---|
| Acme Robotics Incorporated, 500 Market Street | 0.50 | 1 | 1 | 1 | 3.0 | 0.953 |
| Acme Robotics, Nr. City Hall | 0.67 | 0 | 0 | 1 | −0.3 | 0.421 |
| Acme Bakery, 500 Market St | 0.25 | 1 | 1 | 0 | 2.0 | 0.881 |
| Acme Robotix, 12 Elm Rd | 0.25 | 0 | 0 | 0 | −2.0 | 0.119 |

The mean log loss (section 2.6) is 0.792. The model trusts the address too much: the bakery gets 0.88 and the landmark copy only 0.42. Add a feature "the business word differs" (1 for the bakery and Robotix) with weight −6 and the bakery drops to 0.018 and the loss to 0.233. Better features, or better weights found by training, lower the loss.

### 2.2 Train, validation and test

Training error is optimistic: a model can memorise its training examples. So we hold data back.
- **Training set:** fits the parameters.
- **Validation set:** chooses hyperparameters and designs, and so is slowly "used up" by those choices.
- **Test set:** estimates final performance, ideally once.

**Our version** ([`ber.eval.splits`][splits], [CONTRACTS C2][contracts]):

| name | what it is | size |
|---|---|---|
| fold | `splitmix64(S1 id) mod 20`, a hash of the S1 ID, so identical on every machine | 20 buckets |
| holdout | S1 in folds 0 to 4, never trained on, with their matched records | 549,699 S1 (US 329,717; India 219,982) [M] |
| training | S1 in folds 5 to 19 | the rest of the labelled S1 |
| OOF groups | folds 5 to 9, 10 to 14, 15 to 19 (section 2.8) | three groups |
| test | no labels; includes France | 1,732,544 S1 |
| public / private LB | organisers score a subset / the rest of test | rankings only for private |

**Validation gets used up.** The contract allows tuning one or two scalars on the holdout; the three decision settings (+0.2, −0.3, 0.01) were tuned there ([methodology 4][doc]). So 0.9913 is, in principle, slightly optimistic. With three numbers and 549,699 S1 the effect is small, but we cannot quantify it from the documents. The contract also planned for holdout noise of about ±0.001; the bound in [F02][f02] section 2.7 shows sampling noise on the mean is at most ±0.00025.

### 2.3 Overfitting and underfitting

**Generalisation** is performance on data the model has not seen. **Overfitting** is fitting the noise of the training set so that test performance is worse than training performance. **Underfitting** is a model too simple to capture the pattern. Fit polynomials of degree 1, 3 and 9 to a noisy sine wave, with 10 and 100 training points and a fixed test set of 200 points:

```python
import numpy as np
truth = lambda x: np.sin(2 * np.pi * x)
rng = np.random.default_rng(3)
x_te = rng.uniform(0, 1, 200); y_te = truth(x_te) + rng.normal(0, 0.25, 200)   # fixed test set

for n in (10, 100):
    x = np.linspace(0, 1, n); y = truth(x) + rng.normal(0, 0.25, n)
    for degree in (1, 3, 9):
        c = np.polyfit(x, y, degree)
        print(n, degree, np.mean((np.polyval(c, x) - y) ** 2), np.mean((np.polyval(c, x_te) - y_te) ** 2))
```

| training points | degree | training error | test error |
|---|---|---|---|
| 10 | 1 | 0.325 | 0.309 |
| 10 | 3 | 0.025 | 0.060 |
| 10 | 9 | 0.000 | 0.110 |
| 100 | 1 | 0.249 | 0.237 |
| 100 | 3 | 0.055 | 0.062 |
| 100 | 9 | 0.045 | 0.065 |

The noise floor is 0.25² = 0.0625: no model can beat it on average. Degree 1 underfits (both errors high). Degree 9 on 10 points overfits (training error 0, test error close to double the floor). Degree 3 fits (test error at the floor). With 100 points even degree 9 behaves: more data cures overfitting. Numbers will differ a little with another numpy version; the pattern will not. Diagnosis: both errors high and close means underfit; training low and test high means overfit.

### 2.4 Bias and variance

For squared error, the expected test error splits into three parts:

```
expected error = bias² + variance + irreducible noise
```

**Bias** is error from a model too simple to follow the truth (degree 1). **Variance** is how much the fitted model changes with the particular training sample (degree 9). Simple models have high bias and low variance, flexible models the opposite. Our table shows both.

**Ensembles reduce variance.** Average n models whose predictions each have variance σ² and pairwise correlation ρ. The average has variance `σ² × [ρ + (1 − ρ) / n]`. For three models: ρ = 0 gives 0.33σ², ρ = 0.5 gives 0.67σ², ρ = 0.8 gives 0.87σ². The more alike the members, the less averaging helps, which is why diversity matters. The methodology says the 7B model, counted twice in the US/India mix, "adds diversity" even though it is no more accurate than a self-trained e5-large ([methodology 4][doc], [LLM page][adv10]).

### 2.5 Regularisation

**Regularisation** limits what a model can fit, to cut variance. Common forms: a **penalty** on the weights (L2, "ridge": add `λ × Σ w²`; L1, "lasso": add `λ × Σ |w|`, which also sets some weights to 0); **early stopping**; **limiting capacity** (tree depth, minimum child weight, learning rate, row and column subsampling in XGBoost, which also has L1/L2 penalties on leaf weights, [boosting page 2.3][adv06]); **dropout** and weight decay in neural networks; and restricting an update to a low-rank form, as LoRA does for the large language models ([transformers page 2.4][adv08]).

**Worked example.** One weight, data `x = (1, 2, 3)`, `y = (1.1, 1.9, 3.2)`. Ridge gives `w = Σxy / (Σx² + λ)` with Σxy = 14.5 and Σx² = 14:

| λ | 0 | 1 | 14 | 100 |
|---|---|---|---|---|
| w | 1.036 | 0.967 | 0.518 | 0.127 |

The penalty pulls the weight toward 0. A little shrinkage can improve test error; too much underfits (bias up, variance down).

### 2.6 Loss functions, and why the loss is not the metric

**Log loss** (binary cross-entropy) for one example with label `y` and predicted probability `p`:

```
L = -( y × ln p + (1 - y) × ln(1 - p) )          averaged over examples
```

| true label 1, predicted p | 0.99 | 0.9 | 0.5 | 0.1 | 0.01 |
|---|---|---|---|---|---|
| loss | 0.010 | 0.105 | 0.693 | 2.303 | 4.605 |

Confident mistakes are punished hard, which matters for confident decoys. The **Brier score** `(p − y)²` is a gentler alternative. Both are **proper scoring rules**: their expected value is lowest when `p` is the true probability, so training on them pushes toward calibrated probabilities ([F04][f04]). Log loss is the negative average log-likelihood ([F02][f02] section 2.5, [F14][f14]). Its gradient with respect to the logit is `p − y`, which keeps the maths simple.

**The metric is different.** Accuracy and F-measures are not smooth, and F0.5 is computed per S1 over a chosen set, not per pair. We cannot train directly on it. So we **train for probabilities and decide for the metric**: the classifier is trained with log loss, its output is calibrated, and a separate step picks the set per S1 that maximises expected F0.5 ([F02][f02] section 2.6, [metrics page][adv04]).

### 2.7 Gradient descent

To minimise a loss `L(θ)`, repeatedly step against the gradient: `θ ← θ − η × ∇L(θ)`. The **learning rate** `η` sets the step size.

**Worked example.** For `L(w) = (w − 3)²` the gradient is `2(w − 3)`. Starting at 0:

| η | step 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| 0.1 | 0 | 0.6 | 1.08 | 1.46 | 1.77 |
| 0.5 | 0 | 3.0 | 3.0 | 3.0 | 3.0 |
| 1.1 | 0 | 6.6 | −1.32 | 8.18 | −3.22 |

Small steps are slow, a perfect step lands at once, and a step above 1 diverges for this loss. For logistic regression on `x = (0, 1, 2, 3)`, `y = (0, 0, 1, 1)` with `η = 0.5`, a weight and a bias both starting at 0: the loss is 0.693 and the gradient for the weight is −0.5, so the weight becomes 0.25 and the loss 0.595; after four steps the loss is 0.509.

In practice, **mini-batch** versions use a random subset of examples per step, and **Adam** adapts the step size per parameter ([F13][f13]). Gradient boosting is gradient descent in function space: each new tree fits the negative gradient `y − p` of the log loss ([boosting page 2.2][adv06]).

### 2.8 Cross-validation, out-of-fold predictions and stacking

**k-fold cross-validation** splits the data into k parts, trains on k − 1 and scores the part left out, and rotates. Each example is then scored by a model that never saw it: an **out-of-fold (OOF) prediction**. **Group** cross-validation keeps related examples together.

**Why stacking needs OOF.** Stage 2 learns how far to trust the stage-1 score. If stage 1 had scored its own training examples, those scores would be too good (the model has seen the answers), and stage 2 would learn to over-trust them. At test time the stage-1 scores are honest and stage 2 misfires. With OOF scores, training and test scores have the same character.

**Our scheme** ([CONTRACTS C2][contracts]): the training S1 form three OOF groups (folds 5 to 9, 10 to 14, 15 to 19). Each group is scored by a model trained on the other two. The holdout and the test set are scored by a model trained on all training folds. The four XGBoost stages and the three cross-encoder models are built this way ([methodology 4][doc]).

**Worked example (toy).** Nine S1 in three groups.

| S1 | 1, 2, 3 | 4, 5, 6 | 7, 8, 9 | holdout S1 and test |
|---|---|---|---|---|
| group | 0 | 1 | 2 | none |
| scored by a model trained on | groups 1 and 2 | groups 0 and 2 | groups 0 and 1 | groups 0, 1 and 2 |

S1 number 5 is scored by a model that never saw S1 4 to 6. The French **cross-fitting** is the same trick for pseudo-labels: a French pair is never scored by a model trained on its own label ([F10][f10]).

### 2.9 Leakage

**Leakage** is any way information from outside the training set, usually the answer, reaches the model or the evaluation, so the measured score is better than the real one. Common kinds:
- **target leakage:** a feature that encodes the label;
- **contamination:** the same example, or a near copy, on both sides of the split;
- **group leakage:** related examples split between train and validation;
- **preprocessing leakage:** statistics that use labels fitted on data that includes the validation part;
- **selection leakage:** choosing a model or threshold on the data used to report.

**Why we split by S1, not by pair.** Take S1 "Acme Robotics Inc" with three copies A, B and C. A random split of pairs may put (S1, A) in training and (S1, B) in validation. The model has seen the S1's name and a near-twin of B, so B looks easy, and the validation score is inflated. In real use the system meets S1 it has never seen. Splitting by S1 keeps all pairs of one S1 on one side. The metric is per S1, so the unit of the split matches the unit of the score. The same logic is why every supervised encoding, such as word-level look-alike odds, is built out-of-fold and never on the holdout ([CONTRACTS C2 and C8][contracts]).

**What is allowed.** Fitting label-free statistics, such as word rarity (IDF) per country, on train plus test records is fine: it uses no labels ([D-PRB-01][prb]). Search runs over the full pool, not a pool shrunk to the holdout.

**A leak we caught.** Our first gate run for ownership took the argmax over holdout S1 only, which removed the rival S1 of the training folds and made ownership too easy. It was found and fixed before the gate numbers were recorded ([D-PRB-02][prb]). The lesson: leaks hide in how the evaluation set is built, not only in the features.

### 2.10 Class imbalance and prior shift

**Class imbalance** means one class is far rarer. The share of true pairs depends on where in the pipeline you look. These figures are derived [E] from 3.46 copies per S1, the 1,732,544 test S1 and the holdout recalls of 99.1% (retrieval) and about 98.3% (candidate file):

| set of pairs | pairs | true share |
|---|---|---|
| all within-country pairs | about 6.7e12 [E] | about 1 in 1.1 million |
| retrieved | 58,437,794 [M] | about 10% |
| candidate file | 6,410,308 [M] | about 92% |

**The accuracy trap.** Saying "no" to every retrieved pair is 89.8% accurate, and over all pairs 99.99991% accurate, and finds nothing. Use precision, recall and F-measures, which ignore true negatives ([F04][f04]).

**Remedies.** Class weights or resampling change the prior the model sees, so the probabilities must be re-calibrated. If a model trained at positive share `π_train` is used where the share is `π_new`, correct the odds (Saerens et al. 2002):

```
odds_new = odds_model × [π_new / (1 - π_new)] / [π_train / (1 - π_train)]
```

**Worked example.** A score of 0.9 from a model trained at 50% positives is odds 9. Used where only 10% are positive, the odds become 9 × (1/9) / 1 = 1, so p = 0.5. At 1% positives it is 0.083. The methodology does not mention class weights or resampling; probabilities are calibrated after the fact (stage 2, isotonic regression), and the extra test records did not need a prior correction on US and India ([calibration page][adv07]).

### 2.11 Baselines, ablations and gates

A **baseline** is the simplest reasonable method. It sets a floor and catches bugs. An **ablation** removes one component and measures the loss. A **gate** is a rule that admits a component only if it passes a test. Ours is a paired bootstrap on the holdout; the component stays only if the interval is above zero, and ties go to the simpler option ([AGENTS.md][agents] section 3, [F02][f02] section 2.10).

**Worked example.** The baseline "predict nothing for every S1" scores 1 on each singleton and 0 elsewhere: macro F0.5 = the singleton share = 0.056 [E] ([F01][f01]). Any model must beat that by a lot; most of our work lay between the 0.984 of the first versions and 0.9913, where each 0.001 is about 550 holdout S1. More baselines: the best candidate by name alone; exact equality of the normalised name and address; logistic regression on a handful of features; the previous version.

---

## 3. How it shows up in our project

- **Pair classification:** about 100 features per pair, four XGBoost stages ([boosting page][adv06]).
- **Folds and OOF:** hash folds, three OOF groups, a holdout that is never trained on ([`ber.eval.splits`][splits]).
- **Train for probabilities, decide for the metric:** isotonic calibration, then expected-F0.5 set selection ([calibration page][adv07], [metrics page][adv04]).
- **Leakage rules:** supervised encodings out-of-fold; pools stay full ([CONTRACTS C2][contracts]).
- **Cross-fitting** for the French pseudo-labels ([self-training page][adv09]).
- **Gates:** a component is admitted after a paired bootstrap ([`ber.eval.gates`][gates], [evaluation page][adv05]).

---

## 4. How to read the numbers

| number | scope and level | how to read it | what it does not tell you |
|---|---|---|---|
| 549,699 holdout S1 | 25% of labelled US/India S1 [M] | the evaluation set for all comparisons | anything about France |
| 0.9913 | macro F0.5 on the holdout [M] | slightly optimistic, because three decision settings were tuned on it | the test score |
| train 0.000 / test 0.110 | toy polynomial, degree 9, 10 points | the signature of overfitting | project performance |
| 0.056 | all-empty baseline, singleton share [E] | the floor | how hard the last points are |
| about 10% / 92% true | retrieved pairs / candidate file, test, derived [E] | class balance depends on the stage | exact values |

---

## 5. Common misconceptions

1. **"A high training score means a good model."** It may mean memorisation. Only data the model never saw tells you.
2. **"More complex models are better."** They fit more, and also vary more. The best complexity depends on the amount of data.
3. **"Cross-validation gives the final score."** It guides choices. A final claim needs data that was not used to make any choice.
4. **"Leakage means copying the label into a feature."** Most leaks are quieter: related examples across a split, or an evaluation set built in a favourable way.
5. **"Accuracy is fine when classes are balanced."** The classes are never balanced across a whole pipeline, and the metric is per S1 anyway.
6. **"Optimise the metric directly."** F0.5 on sets cannot be trained on directly; we train a probability model and decide separately.
7. **"Resampling to balance classes is free."** It changes the prior, so the probabilities must be corrected.

---

## 6. Check yourself

**1.** In our task, what are an example, the features, the label, the model output and the loss?

<details><summary>Answer</summary>

Example: a candidate pair (S1, S2/S3 record). Features: about 100 numbers (name and address similarities, house-number equality, ranks among rivals). Label: 1 if the pair is in the ground truth. Output: the probability of a match. Loss: log loss, averaged over training pairs.

</details>

**2.** Diagnose each (training error, validation error): (0.30, 0.31), (0.01, 0.20), (0.05, 0.06). The noise floor is 0.05.

<details><summary>Answer</summary>

(0.30, 0.31): underfit; both are high and close, well above the floor. (0.01, 0.20): overfit; training is below the floor (fitting noise) and validation is far above. (0.05, 0.06): good; both at the floor.

</details>

**3.** Compute the log loss of predictions 0.9, 0.5 and 0.01 for pairs whose true labels are 1, 1 and 0. Which dominates?

<details><summary>Answer</summary>

0.9 with y = 1: 0.105. 0.5 with y = 1: 0.693. 0.01 with y = 0: −ln(0.99) = 0.010. The mean is 0.269. The undecided 0.5 dominates here; a confident mistake would dominate more (p = 0.01 for a true pair costs 4.605).

</details>

**4.** Three models have equal variance and pairwise correlation 0.8. What is the variance of their average, as a share of one model's? What helps more than adding a fourth similar model?

<details><summary>Answer</summary>

0.8 + 0.2 / 3 = 0.867. A fourth similar model gives 0.8 + 0.2 / 4 = 0.85, a small gain. Lowering the correlation helps more: a different model family or different inputs (for example raw text rather than hand features).

</details>

**5.** Nine S1 in three OOF groups (1 to 3, 4 to 6, 7 to 9). Which model scores S1 5, and what would go wrong if stage 2 used stage-1 scores that came from a model trained on S1 5 itself?

<details><summary>Answer</summary>

S1 5 is in group 1, so it is scored by a model trained on groups 0 and 2. If stage 2 used in-sample stage-1 scores, they would look better than real, stage 2 would learn to over-trust stage 1, and at test time, when stage-1 scores are honest, stage 2 would be over-confident.

</details>

**6.** A teammate randomly splits candidate pairs 75/25 and reports a score of 0.997 (toy). Why is that number suspect, and what do we do instead?

<details><summary>Answer</summary>

Pairs of one S1 land on both sides, so the model has seen the S1's name and near-twin copies; validation is easier than real use. We split by S1 using a hash of the S1 ID, keep the holdout out of all supervised fitting, and score per S1.

</details>

**7.** A model trained with 50% positives says 0.9. At deployment 10% are positive. What is the corrected probability?

<details><summary>Answer</summary>

Odds 9 × (0.1 / 0.9) / (0.5 / 0.5) = 1, so p = 0.5. The same evidence is much weaker when positives are rare.

</details>

**8.** What is the accuracy of "no match" on the 58,437,794 retrieved test pairs, given about 5.94 million are true? And the macro F0.5 of "predict nothing" for every S1?

<details><summary>Answer</summary>

1 − 5.94M / 58.44M = 0.898, which looks respectable and finds nothing. "Predict nothing" scores 1 on the 5.6% singletons and 0 elsewhere: 0.056.

</details>

**9.** For `L(w) = (w − 3)²` and start `w = 0`, compute one gradient-descent step with `η = 0.1` and with `η = 1.1`. What happens with the second?

<details><summary>Answer</summary>

Gradient at 0 is −6. With η = 0.1: w = 0 + 0.6 = 0.6. With η = 1.1: w = 6.6, past the minimum by more than it started from. The next step goes to −1.32, then 8.18: it diverges because each step overshoots by more than it corrects.

</details>

**10.** Ridge with `Σxy = 14.5`, `Σx² = 14` and `λ = 14`: what is `w`? What happens as `λ` grows?

<details><summary>Answer</summary>

w = 14.5 / (14 + 14) = 0.518. As λ grows, w goes to 0: more bias, less variance.

</details>

---

## 7. Going deeper

- Hastie, Tibshirani and Friedman (2009), "The Elements of Statistical Learning", 2nd edition, Springer. Chapters on the bias-variance trade-off, model assessment and regularisation.
- James, Witten, Hastie and Tibshirani, "An Introduction to Statistical Learning", Springer. A gentler start.
- Bishop (2006), "Pattern Recognition and Machine Learning", Springer.
- Domingos (2012), "A few useful things to know about machine learning", Communications of the ACM. Short and practical.
- Kaufman, Rosset, Perlich and Stitelman (2012), "Leakage in data mining: formulation, detection, and avoidance", ACM TKDD.
- Wolpert (1992), "Stacked generalization", Neural Networks.
- Cawley and Talbot (2010), "On over-fitting in model selection and subsequent selection bias in performance evaluation", JMLR.
- Saerens, Latinne and Decaestecker (2002), "Adjusting the outputs of a classifier to new a priori probabilities: a simple procedure", Neural Computation.

## 8. Where next

- [F04 Classification metrics][f04]: the metrics that go with these models.
- [F05 Trees and ensembles][f05]: the model family behind our four stages.
- [F09 Experiments and evidence][f09]: gates, ablations and holdouts in practice.
- [F10 Semi-supervised learning and domain shift][f10]: pseudo-labels and cross-fitting.
- [F14 Information theory and losses][f14] and [F13 Linear algebra and optimisation][f13]: the maths behind log loss and gradient descent.
- Advanced pages [05 evaluation][adv05], [06 boosting and stacking][adv06], [07 calibration][adv07].
- The track map: [foundations README](README.md).

[doc]: ../../../experiments/ameya/final-zip/doc/Documentation_template.md
[agents]: ../../../AGENTS.md
[contracts]: ../../../docs/CONTRACTS.md
[splits]: ../../../code/business_entity_resolution/src/ber/eval/splits.py
[gates]: ../../../code/business_entity_resolution/src/ber/eval/gates.py
[prb]: ../../decisions/PRB.md
[adv04]: ../04-metrics-and-decisions.md
[adv05]: ../05-evaluation-methodology.md
[adv06]: ../06-gradient-boosting-and-stacking.md
[adv07]: ../07-calibration.md
[adv08]: ../08-transformers-and-cross-encoders.md
[adv09]: ../09-self-training-and-domain-shift.md
[adv10]: ../10-llm-verification-and-compute.md
[f01]: F01-data-and-problem.md
[f02]: F02-probability-and-statistics.md
[f04]: F04-classification-metrics.md
[f05]: F05-trees-and-ensembles.md
[f09]: F09-experiments-and-evidence.md
[f10]: F10-semi-supervised-and-domain-shift.md
[f11]: F11-decision-theory-and-optimisation.md
[f13]: F13-linear-algebra-and-optimisation.md
[f14]: F14-information-theory-and-losses.md
