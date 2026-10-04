# Gradient boosting, cascades and stacking

**Summary.** Our matcher is four XGBoost stages run as a cascade: a cheap filter (stage 0), a pair model that gives p1 (stage 1), a context model that also reads the cross-encoders and gives the calibrated pc (stage 2), and a re-scorer that weighs rivals (stage 3).
Every stage learns from out-of-fold scores of the stage before, so no stage is trained on numbers that were fitted on its own rows.
This page gives the maths of boosted trees and stacking, and the numbers that justify each stage.

Related pages: [entity resolution](01-entity-resolution.md), [blocking](02-blocking.md), [metrics and decisions](04-metrics-and-decisions.md), [evaluation methodology](05-evaluation-methodology.md), [calibration](07-calibration.md), [cross-encoders](08-transformers-and-cross-encoders.md), [glossary](glossary.md).

---

## 1. Intuition

- A **decision tree** asks a short series of yes/no questions about a pair ("is the house number equal?", "is the rarest unmatched word a look-alike word?") and gives each final box, a **leaf**, a score.
- One tree is crude. **Gradient boosting** adds hundreds of small trees one after another. Each new tree is fitted to what the current sum still gets wrong, and only a small step of it is added.
- **Stacking** feeds one model's score into the next model as a feature. The next model can then ask questions that only make sense once every pair has a score: "is this the best S1 for this record?", "how many confident copies does this S1 already have?"
- A **cascade** spends effort in proportion to doubt. Most of the 58.4M retrieved test pairs are obvious non-matches, so a 200-tree filter removes them, and the expensive stages see only what is left.

## 2. Formal definition

### 2.1 Trees

A tree with T leaves sends a feature vector x to a leaf q(x) and returns that leaf's weight: $f(x) = w_{q(x)}$. Trees grow greedily: at each node, every feature and threshold is tried, and the split that most reduces the loss is kept (CART).

### 2.2 Gradient boosting

The model is a sum of trees on the log-odds (margin) scale:

$$F_M(x) = F_0 + \eta \sum_{m=1}^{M} f_m(x), \qquad p(x) = \sigma\big(F_M(x)\big) = \frac{1}{1+e^{-F_M(x)}}$$

With the logistic loss $\ell(y,F) = -\big[y\log\sigma(F) + (1-y)\log(1-\sigma(F))\big]$, the derivatives with respect to the margin are

$$g = \frac{\partial \ell}{\partial F} = p - y, \qquad h = \frac{\partial^2 \ell}{\partial F^2} = p(1-p).$$

Friedman's gradient boosting fits each new tree to the negative gradient $y - p$, the **pseudo-residual**. It is gradient descent in function space: the tree is the step direction and the **shrinkage** η (the learning rate) is the step size.

### 2.3 XGBoost's regularised second-order objective

At round t, XGBoost minimises

$$\mathcal{L}^{(t)} = \sum_i \ell\big(y_i,\ \hat y_i^{(t-1)} + f_t(x_i)\big) + \gamma T + \tfrac12\lambda \sum_{j=1}^{T} w_j^2 .$$

A second-order Taylor expansion around the current prediction gives, for each leaf j with $G_j = \sum_{i \in I_j} g_i$ and $H_j = \sum_{i\in I_j} h_i$,

$$w_j^{\star} = -\frac{G_j}{H_j+\lambda}, \qquad \mathcal{L}^{\star} = -\frac12\sum_{j}\frac{G_j^2}{H_j+\lambda} + \gamma T ,$$

so splitting a node into a left and a right child is worth

$$\text{Gain} = \frac12\left[\frac{G_L^2}{H_L+\lambda} + \frac{G_R^2}{H_R+\lambda} - \frac{(G_L+G_R)^2}{H_L+H_R+\lambda}\right] - \gamma .$$

Each leaf takes a Newton step. What the settings mean, with ours ([`s1.py`](../../experiments/ameya/model-v1/s1.py), [`s2.py`](../../experiments/ameya/model-v1/s2.py), [`stage3.py`](../../experiments/ameya/model-v1/stage3.py)):
- **λ** is an L2 penalty on leaf weights (2.0 in stages 1 and 2). **γ** is a minimum gain per split (we left it at 0).
- **min_child_weight** is a floor on H in each child. Since h = p(1−p), a pair already scored at p = 0.001 adds only 0.001. With our stage-1 value of 10, a leaf of near-certain non-matches needs about 10,000 pairs, while a leaf of uncertain pairs (h ≈ 0.25) needs 40. The trees spend their splits where the model is unsure.
- **Shrinkage η** scales each tree before it is added: 0.2 in stage 0, 0.06 in stage 1, 0.05 in stage 2, 0.1 in stage 3. Small steps, many trees and early stopping generalise better than a few big steps.
- **Row and column subsampling** (subsample 0.8; colsample_bytree 0.7–0.8): each tree sees 80% of the rows and 70–80% of the features. This decorrelates the trees and regularises (stochastic gradient boosting).
- **Histogram method** (`tree_method hist`, `max_bin 256`): each feature is cut once into at most 256 quantile bins. At a node, g and h are summed per bin and the bins are scanned for the best threshold, with no sorting; a child's histogram is its parent's minus its sibling's. We trained on the GPU with bins built straight from the data (`QuantileDMatrix`), which kept about 10M stage-2 rows inside a 31 GB laptop's memory.
- **Missing values**: at every split, XGBoost learns a default direction for NaN by trying both sides.
- **Early stopping**: training stops when the validation log-loss has not improved for 60 rounds. Our validation rows are a 2% hash slice of S1 inside the training groups, so early stopping never sees the group being scored.

### 2.4 Stacking with out-of-fold scores

A model that scores its own training rows is too confident on them, because it has partly memorised them. A second model trained on such scores learns to over-trust them, then meets less confident scores on test (Wolpert 1992).

The fix is **out-of-fold (OOF)** scoring. Split the training S1 into K groups; for each group k, train on the other groups and score group k:

$$s^{\text{oof}}(x_i) = f^{(-k(i))}(x_i),$$

where k(i) is the group of pair i's S1. Every training pair then has a score from a model that never saw it, distributed like a test score. The holdout and the test get the mean of the K models.

Our groups come from a hash of the S1 id ([`ber.eval.splits`](../../code/business_entity_resolution/src/ber/eval/splits.py)): fold = splitmix64(eid) mod 20; folds 0–4 are the local holdout (549,699 S1); folds 5–9, 10–14 and 15–19 are OOF groups 0, 1 and 2. With three groups, each model trains on half of all training S1. The final fit (`--all`) makes the holdout a fourth group, so each model trains on three quarters, and every holdout pair is still scored by a model that never saw it.

**Why group by S1, not by pair.** Pairs of one S1 share its text and its rivals. Split across folds, a model could learn an S1's answer from its other pairs. Grouping by S1 also matches the metric, which averages over S1.

### 2.5 Collective (context) features

A pair model judges one pair at a time, but the truth is collective: each record belongs to at most one S1, and an S1 has 3.46 copies on average. Stage 2 therefore computes, from p1 over the whole candidate graph ([`s2.py`](../../experiments/ameya/model-v1/s2.py)):
- **per record**: this pair's rank among the record's S1; the best and second-best p1; the **margin** $m(s,r) = p_1(s,r) - \max_{s' \ne s} p_1(s',r)$; how many S1 are above 0.5; this pair's share of the record's total p1;
- **per S1**: this record's rank; the max and sum of p1 (an expected cluster size); counts above 0.5, 0.8 and 0.95; the gaps to neighbouring ranks; the confident copies from the same source, without this pair;
- **cluster support** ([`cluster.py`](../../experiments/ameya/model-v1/cluster.py)): how similar the record is to the S1's confident records.

Stage 3 goes further for **contested records**, those with two or more candidate S1 at pc ≥ 0.01. It adds the best rival's pc and how many confident copies each rival already holds per source. The generator draws each S1's S2 and S3 copy counts separately (capped at 5 and 6), so a rival that already holds several S2 copies is less likely to own one more.

### 2.6 SHAP

SHAP shares one prediction among the features. For a value function v(S), the expected output when only the features in S are known, the Shapley value of feature j is

$$\phi_j = \sum_{S\subseteq F\setminus\{j\}} \frac{|S|!\,(|F|-|S|-1)!}{|F|!}\big[v(S\cup\{j\}) - v(S)\big].$$

The shares add up: $f(x) = \phi_0 + \sum_j \phi_j$, where for XGBoost f(x) is the log-odds. TreeSHAP computes exact values for tree ensembles in polynomial time. Additivity is what makes SHAP useful for comparing groups: the logit gap between France and US/India inside one edit family splits exactly into per-feature gaps.

### 2.7 A cascade as a compute budget

If a share $\pi_k$ of the pairs reaches stage k and costs $c_k$ there, the cost per retrieved pair is

$$C = \sum_k \pi_k\, c_k .$$

A cascade pays when the early stages are cheap and remove most pairs. Recall multiplies: a true pair must survive every stage, so each filter is set by the positives it keeps, not by the negatives it removes.

## 3. Variants

| variant | idea | relation to ours |
|---|---|---|
| AdaBoost | re-weight misclassified rows (exponential loss) | the first boosting; we boost log-loss |
| Random forest | deep trees on bootstrap samples, averaged | cuts variance, not bias; not used |
| LightGBM | histograms, leaf-wise growth, gradient-based row sampling | same family; not tried (time) |
| CatBoost | ordered target statistics against target leakage | the worry that made our look-alike odds out of fold |
| Blending | one holdout split instead of K folds | wastes data; OOF uses all of it |
| Cross-fitting | OOF applied to unlabelled target rows | our France self-training ([page 09](09-self-training-and-domain-shift.md)) |
| Cascades | cheap detector first, costly one on survivors | stage 0 → 1 → cross-encoders → 7B ([page 10](10-llm-verification-and-compute.md)) |
| Importance | gain, permutation, SHAP | gain chose stage 2's top 30 stage-1 features; SHAP explained France |

## 4. Where we used it

| stage | code | rows | model | output |
|---|---|---|---|---|
| 0 | [`s1.py`](../../experiments/ameya/model-v1/s1.py) | all 58.4M retrieved test pairs | 200 trees, depth 6, η 0.2, fitted on a 10% S1 sample | p0. The cut τ0 keeps 99.95% of the positives outside that sample and stops about 80–85% of pairs [M] |
| 1 | `s1.py` | pairs with p0 ≥ τ0 | depth 9, η 0.06, up to 4,000 trees (about 1,600 used in v3), 4 OOF models | p1. It sets the candidate file (p1 ≥ 0.02 and the record's top 2 S1, plus acronym joins: 6,410,308 pairs, 3.70 per S1) and the cross-encoder band (0.02 ≤ p1 ≤ 0.99: 1,490,930 test pairs) [M] |
| 2 | [`s2.py`](../../experiments/ameya/model-v1/s2.py) | p1 ≥ 0.002: 10,065,671 training rows for g1w [M] | depth 7, η 0.05, 4 OOF models (best iterations 824–1,032) | p2, then isotonic calibration to pc ([page 07](07-calibration.md)) |
| 3 | [`stage3.py`](../../experiments/ameya/model-v1/stage3.py) | contested records inside the candidate file | depth 6, η 0.1, min_child_weight 20, 11 features | pc re-scored; empty-address records' total pc calibrated (part B) |

**What each stage bought** (local holdout unless stated; [M]):
- **Stage 2 over stage 1** (gate G4, Sachi, dev holdout of 27,651 S1): macro F0.5 0.97745 → 0.98438, Δ +0.00692 [+0.00622, +0.00772]; singleton F0.5 0.968 → 0.985 ([decision record](../../docs/decisions/2026-09-25_2103_gate-g4-stage2.md)). On v6all over the full holdout: stage 1 alone 0.9878 at its best threshold, stage 2 0.9908 ([v6all record](../../docs/decisions/2026-09-26_1425_model-v6all-final.md)).
- **The cross-encoder as a stage-2 feature** (v3 → v3ce): +0.00140 [+0.00131, +0.00148] ([v4 record](../../docs/decisions/2026-09-26_0207_model-v4-france-and-cross-encoder.md)).
- **Stage 3** on v6all: +0.000055 [+0.000025, +0.000085] ([RESEARCH_v6 §2.8](../../experiments/ameya/model-v1/RESEARCH_v6.md)).
- **Tuning did not help**: a seed-bagged stage 2 lost 0.00004, and depth 8 left the early-stopping loss unchanged (RESEARCH_v6 §6.1).

**SHAP on France** (agent for Ameya, RESEARCH_v6 §2.9). Stage-1 SHAP values of French pairs were compared with US/India pairs of the same edit family. Exact copies were fine (99.57% at pc ≥ 0.999, against 99.73–99.83%). True copies with a swapped or appended list word lost 1–5 logits, from two France-specific biases:
- the label-free proxy odds treated dual-use words ("groupe", "france", "developpement") as pure look-alike words, at −4.84, the value of "holding";
- French house numbers are small and shared, so a rival S1 on the same street depressed the retrieval margin by 0.4–2.8 logits.

Fixing either moved only 1–2% of French predictions (about +0.0004 and ±0.001 France F0.5, estimated). **Hindsight:** SHAP told us where France lost, and also that these feature fixes were not where the big gain was. The gain came from cross-encoders and self-training.

## 5. Why it fits this problem

- **Tabular, mixed features.** About 87 features per pair in v3: fuzzy ratios from 0 to 100, ranks, counts, codes such as `num__rel1` (0–4), and NaN for empty sides. Trees need no scaling and ignore monotone transforms.
- **Sharp interactions.** "Same house number and a look-alike word swapped" is a decoy; "same house number and a list word swapped" is a copy. A tree needs two splits for that; a linear model needs a hand-made product.
- **Scale.** Stages 0 and 1 score the 58.4M test pairs in about 4 minutes on a 64-vCPU box with two RTX 4090s [R], and a stage-2 fit takes about 20 minutes [R] (Bakshi's [methodology](../../experiments/bakshi/final-package/METHODOLOGY_bakshi.md) §2, §4).
- **Probabilities.** Log-loss boosting plus isotonic calibration gives the probabilities the expected-F0.5 decision needs.
- **The weak spot is text** (abbreviations, transliterations, brand names). That is why the cross-encoders read the uncertain band and feed stage 2.

## 6. Pitfalls

1. **Leakage through in-sample scores.** We kept every learned input out of fold: p1, the cross-encoder logits, pc's calibration, stage 3, and the look-alike word odds `lo__*`, which are a target encoding (each word's log-odds of a true match) and use counts from the other OOF groups only.
2. **Single-model OOF scores on train, averaged scores on test.** The mean of K models is smoother than one model's score. Our holdout is scored the same way as test, so holdout numbers include this mismatch.
3. **Reusing the holdout.** The decision settings were tuned on it, the final isotonic map included its OOF scores, and we iterated against it for days. The absolute 0.9913 is mildly optimistic; paired comparisons, half-splits and repeated 2-fold checks guard the decisions ([page 05](05-evaluation-methodology.md)).
4. **Values never seen in training.** Unseen words were −1.94e-16 on train and exactly 0.0 on test, so a split at 0 sent them different ways; adversarial validation (AUC 0.95) found it. French legal-form bits (≥ 4096) never occurred in train; with the bits zeroed, French look-alike pairs fell from p1 0.456 to 0.027, so we dropped the bitmasks ([ANALYSIS_v3 §7](../../experiments/ameya/model-v1/ANALYSIS_v3.md)).
5. **Context features that depend on pool size.** Counts of rival S1 change when the pool changes (test US has half train US's S1). We used log-counts, not rates ([page 09](09-self-training-and-domain-shift.md)).
6. **Gain importance is biased** toward continuous, many-valued features. We used it only to pick the top 30 stage-1 features for stage 2.
7. **Cascade losses compound and cannot be undone.** In the v6all loss anatomy, stage 0 filtered 1,063 true holdout pairs, worth +0.00019 if recovered [M].
8. **A stage gated on US/India can act differently on France.** Stage 3 changed pc by more than 0.05 on 330 per 1000 French S1, against about 100 for US/India (RESEARCH_v6 §6.8).

## 7. Jury questions with answers

**Q1. Why XGBoost and not an end-to-end neural network?**
Our pair features are tabular, with sharp interactions and missing values, and there are 58.4M test pairs. Trees score them in minutes on CPU and GPU; a 7B model would need about 27 GPU-hours just to read them. We use neural models where they pay: cross-encoders on the 1.49M uncertain pairs, as a stage-2 feature (+0.00140 local holdout from the first one).

**Q2. Why four stages?**
Each one answers a question the one before cannot. Stage 0 removes about 80–85% of pairs while keeping 99.95% of positives. Stage 1 judges a pair. Stage 2 judges it against its rivals and reads the cross-encoders (+0.0069 over stage 1 on the dev holdout). Stage 3 resolves contested records with the rivals' copy counts (+0.000055).

**Q3. How did you prevent leakage between stages?**
Folds come from a hash of the S1 id, and every stage is trained on out-of-fold scores of the stage before, in three S1 groups. Early stopping uses a separate hash slice, calibration is fitted on OOF scores, and stage 3 never trains on records that touch a holdout S1.

**Q4. What does stage 2 know that stage 1 does not?**
The neighbourhood: whether this is the record's best S1, the margin to the best rival, how many confident copies the S1 already has, and whether the record looks like those copies. That matters because a record has at most one owner and 46–54% of S1 share their name with another S1. Singleton F0.5 rose from 0.968 to 0.985 with stage 2.

**Q5. The final fit used the holdout as a fourth group. Is 0.9913 still honest?**
Each holdout pair is still scored by a model that never saw it. But we tuned decision settings on the holdout and iterated against it, so the absolute number is mildly optimistic. We guarded the choices with fixed half-splits and repeated 2-fold CV (the decision rule kept +23.7e-6 out of sample, positive in 86% of 42 splits), and the public leaderboard, which includes France, is the independent check: 0.990879.

**Q6. Why three OOF groups and not five or ten?**
Cost: every group means another model per stage, and another cross-encoder per family; three 7B models already took about 6 GPU-hours. With millions of rows, going from 50% to 80% of the data per model changes little, and the final fit used four groups (75%).

**Q7. How did SHAP help you on France?**
It showed that French true copies lost 1–5 logits from two causes: dual-use words scored as look-alike words, and a retrieval margin depressed by shared house numbers. It also showed that fixing them moved only 1–2% of French predictions, so we put the effort into cross-encoders and self-training instead.

**Q8. What does the cascade lose?**
By design 0.05% of positives at stage 0; on the holdout, 1,063 true pairs worth +0.00019. That is the price of not running stage 1's 1,600 deep trees on every pair.

## 8. Self-test

1. Derive g and h for the logistic loss on the margin. Why does h matter for confident pairs?
<details><summary>Answer</summary>

With $p = \sigma(F)$, $\partial\ell/\partial F = p - y$ and $\partial^2\ell/\partial F^2 = p(1-p)$. For a confident pair, h is near 0, so it barely counts toward H. Leaves of confident pairs need many rows to pass min_child_weight, and their Newton steps $-G/(H+\lambda)$ are damped by λ.

</details>

2. A node splits into L and R with $G_L = -30$, $H_L = 20$, $G_R = 10$, $H_R = 40$, λ = 2, γ = 0. Compute the gain and the two leaf weights.
<details><summary>Answer</summary>

$G_L^2/(H_L+\lambda) = 900/22 = 40.91$; $G_R^2/(H_R+\lambda) = 100/42 = 2.38$; parent $(-20)^2/62 = 6.45$. Gain = ½ (40.91 + 2.38 − 6.45) = **18.42**. Weights: $w_L = 30/22 = +1.36$, $w_R = -10/42 = -0.24$ (in logits).

</details>

3. Why would training stage 2 on in-sample p1 hurt on test?
<details><summary>Answer</summary>

In-sample p1 is sharper than test p1, because stage 1 partly memorised its training rows. Stage 2 would learn that p1 is very reliable, then over-trust a noisier p1 on test: overconfident probabilities and worse decisions.

</details>

4. A cascade has stage 0 at cost 1 per pair, keeping 18% of pairs, and stage 1 at cost 20 per pair. What does it cost per retrieved pair, against stage 1 alone?
<details><summary>Answer</summary>

C = 1 + 0.18 × 20 = 4.6, against 20: about 4.3 times cheaper. The price is the positives stage 0 drops (0.05% for us).

</details>

5. Which of our features is a target encoding, and how was it kept honest?
<details><summary>Answer</summary>

The look-alike word odds `lo__*`: each word's log-odds of a true match, counted on labelled pairs. Training-fold rows use counts from the other two OOF groups only; the holdout and test use all training folds. Words never seen get exactly 0.

</details>

6. In stage 2, what does a missing cross-encoder logit mean, and why is that safe?
<details><summary>Answer</summary>

The cross-encoders only score the band 0.02 ≤ p1 ≤ 0.99, so NaN means p1 was below 0.02 or above 0.99. The same rule selects the band on train and test, so the default direction XGBoost learns for NaN carries over exactly.

</details>

7. Why are the folds a hash of the S1 id rather than random pairs?
<details><summary>Answer</summary>

So all pairs of one S1 fall in one fold: no S1 is partly seen in training, the split matches the per-S1 metric, and splitmix64 gives the same folds on every machine.

</details>

## 9. Further reading

- Breiman, Friedman, Olshen and Stone (1984). Classification and Regression Trees.
- Freund and Schapire (1997). A decision-theoretic generalization of on-line learning and an application to boosting.
- Friedman (2001). Greedy function approximation: a gradient boosting machine.
- Friedman (2002). Stochastic gradient boosting.
- Chen and Guestrin (2016). XGBoost: a scalable tree boosting system.
- Ke et al. (2017). LightGBM: a highly efficient gradient boosting decision tree.
- Prokhorenkova et al. (2018). CatBoost: unbiased boosting with categorical features.
- Wolpert (1992). Stacked generalization.
- Breiman (1996). Stacked regressions.
- Viola and Jones (2001). Rapid object detection using a boosted cascade of simple features.
- Shapley (1953). A value for n-person games.
- Lundberg and Lee (2017). A unified approach to interpreting model predictions.
- Lundberg et al. (2020). From local explanations to global understanding with explainable AI for trees.
- Bhattacharya and Getoor (2007). Collective entity resolution in relational data.
- Grinsztajn, Oyallon and Varoquaux (2022). Why do tree-based models still outperform deep learning on typical tabular data?
