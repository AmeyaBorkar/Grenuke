# F05. Trees and ensembles

**Summary**

- A decision tree is a list of yes/no questions about a pair of records. Boosting stacks hundreds of small trees, and each tree fixes what the earlier ones still get wrong.
- Our matcher is four XGBoost stages in a cascade. Each stage learns from honest (out-of-fold) scores of the stage before it, and SHAP showed us why France was scored less confidently.
- This page builds every idea from zero: splits, bagging, gradient boosting worked by hand, the XGBoost objective, stacking and cascades, and importance versus SHAP.

## What you need first

- [F03 machine learning fundamentals](F03-machine-learning-fundamentals.md): training, validation, overfitting.
- [F04 classification metrics](F04-classification-metrics.md): precision, recall, AUC, log loss.
- [F02 probability and statistics](F02-probability-and-statistics.md): expectation and variance.
- Helpful: [F14](F14-information-theory-and-losses.md) for log loss and entropy, [F13](F13-linear-algebra-and-optimisation.md) for gradients.
- The setting: blocking proposes candidate records for every S1 record. The matcher gives each (S1, record) pair a probability of being the same business. See [F01](F01-data-and-problem.md) and [01-entity-resolution](../01-entity-resolution.md).

---

## 1. Decision trees

### 1.1 What a tree is

**Intuition.** Think of twenty questions. For a pair of records you ask: "Does the S1 house number appear among the record's numbers?" If yes, ask the next question, and so on. After a few questions you land in a final box, called a **leaf**, and the leaf gives a score. In our v3 dev kit the question about the house number was the top feature by gain (`num__s1first_in_r`, see [FEATURES.md](../../../experiments/ameya/model-v1/FEATURES.md)).

**Definition.** A tree has internal nodes (each holds one feature and one threshold), branches (yes or no) and leaves. A tree cuts the feature space into boxes and returns one constant per box. If $q(x)$ is the leaf that pair $x$ falls into, the tree is $f(x) = w_{q(x)}$. The depth is the longest path from the root to a leaf. A tree of depth $d$ has at most $2^d$ leaves: depth 6 gives 64, depth 9 gives 512.

### 1.2 Choosing a split: Gini and entropy

**Intuition.** A node is pure if it holds one class only. A good question makes the two child nodes purer than the parent. We need a number that says how mixed a node is.

**Definition.** For a node where a fraction $p$ of the pairs are matches:

- Gini impurity: $G = 1 - p^2 - (1-p)^2 = 2p(1-p)$.
- Entropy: $H = -p\log_2 p - (1-p)\log_2(1-p)$, in bits.

Both are 0 for a pure node and largest at $p = 0.5$ (Gini 0.5, entropy 1 bit). The **gain** of a split is the parent's impurity minus the size-weighted impurity of the children. The tree picks the question with the largest gain.

**Worked example.** A node has 10 pairs: 6 matches, 4 non-matches. Question: "house number found in the record?" The yes branch gets 5 pairs, all matches. The no branch gets 5 pairs: 1 match and 4 non-matches.

| quantity | Gini | entropy (bits) |
|---|---|---|
| parent (6 of 10) | 0.48 | 0.971 |
| yes branch (5 of 5) | 0 | 0 |
| no branch (1 of 5) | 0.32 | 0.722 |
| weighted children, 0.5 and 0.5 | 0.16 | 0.361 |
| gain | 0.32 | 0.610 |

Entropy gain is the information gain: it equals the mutual information between the answer and the label ([F14](F14-information-theory-and-losses.md)). Gini and entropy usually pick the same split.

### 1.3 Growing a tree, and why depth matters

**How it grows.** For each feature, sort the pairs by its value and sweep a threshold from left to right, updating the class counts as you go. One sweep gives the impurity of every possible split of that feature. Do this for all features, take the best split, and repeat inside each child. This is greedy: each split is the best for now, not for the final tree.

**Stopping.** Without limits, a tree keeps splitting until every leaf is pure and memorises the noise. That is **overfitting**: high variance, because a small change in the training data gives a very different tree. We stop with a maximum depth, a minimum amount of data per leaf, or a minimum gain.

**What trees can and cannot do.**
- Only the order of values matters, so scaling or taking logs of a feature changes nothing. Trees need no feature scaling.
- A tree is piecewise constant and cannot extrapolate beyond the range it saw.
- A tree of depth $d$ can express interactions of up to $d$ features, such as "house numbers equal AND rare name words match AND no rival S1". Pair features are full of such interactions.

---

## 2. Bagging and random forests

**Intuition.** One tree is unstable. Many trees trained on different random versions of the data, then averaged, are stable. Averaging cancels noise that is not shared between the trees.

**Bootstrap.** Draw $n$ rows with replacement from $n$ rows. A given row is missed with probability $(1-1/n)^n$, which tends to $1/e \approx 0.368$. So each bootstrap sample holds about 63.2% of the distinct rows (65.1% for $n=10$, 63.4% for $n=100$). The missed 36.8% are the **out-of-bag (OOB)** rows, a free validation set for that tree.

Bagging (Breiman 1996) trains $B$ trees on $B$ bootstrap samples and averages them. If each tree has variance $\sigma^2$ and any two trees have correlation $\rho$, the average has variance

$$\mathrm{Var}(\bar f) = \rho\,\sigma^2 + \frac{1-\rho}{B}\,\sigma^2 .$$

**Worked example.** Take $\sigma^2 = 1$ and $\rho = 0.3$. One tree: 1.0. Ten trees: $0.3 + 0.07 = 0.37$. One hundred trees: $0.3 + 0.007 = 0.307$. The floor is $\rho\sigma^2 = 0.3$. More trees stop helping once the second term vanishes, so the only lever left is a lower correlation $\rho$.

Random forest (Breiman 2001) lowers $\rho$ by letting each split look at only a random subset of the features (commonly $\sqrt{p}$ of $p$ features for classification). Trees become less alike, so the average is better. Forests reduce variance. They do not reduce bias: if each deep tree is wrong in the same direction, the average is wrong too.

This project's matcher uses boosting. This page does not claim a measured comparison with a forest.

---

## 3. Boosting from scratch

### 3.1 The idea

**Intuition.** Bagging trains trees in parallel and independently. Boosting trains them one after another. Each new tree looks at the mistakes of the current ensemble and learns to correct them. Many small corrections add up to a strong model. AdaBoost (Freund and Schapire 1997) did this by re-weighting the rows that were misclassified. Gradient boosting (Friedman 2001) generalises it to any loss. The trees are regression trees: their leaves hold numbers, and a leaf's number is a step on the score scale.

**Definition.** The model is an additive sum of trees on a score scale:

$$F_m(x) = F_{m-1}(x) + \eta\, f_m(x),$$

where $\eta$ is the learning rate (also called shrinkage), a small step size such as 0.05. For classification, $F$ is the **margin**, the log-odds of a match, and the probability is $p = 1/(1+e^{-F})$. With the log loss $\ell(y,F) = -[y\ln p + (1-y)\ln(1-p)]$, two derivatives with respect to the margin drive everything:

$$g = \frac{\partial \ell}{\partial F} = p - y, \qquad h = \frac{\partial^2 \ell}{\partial F^2} = p(1-p).$$

Here $g$ is the **gradient** (the direction of steepest increase in loss) and $h$ is the **hessian** (the curvature). The new tree is fitted to the negative gradient $y - p$, called the **pseudo-residual**. For squared error that is the ordinary residual $y - F$. For other losses it is not, so "boosting fits residuals" is only true for squared error. This is gradient descent in the space of functions ([F13](F13-linear-algebra-and-optimisation.md)).

### 3.2 Worked example: two rounds by hand

Eight pairs. The feature $x$ is the Jaccard overlap of the two names (see [F06](F06-text-strings-and-retrieval.md)). Pair c is a true copy whose name was garbled; pair d is a different business with some shared words.

| pair | a | b | c | d | e | f | g | h |
|---|---|---|---|---|---|---|---|---|
| x | 0.10 | 0.20 | 0.35 | 0.45 | 0.55 | 0.70 | 0.80 | 0.90 |
| y (1 = match) | 0 | 0 | 1 | 0 | 1 | 1 | 1 | 1 |

Settings: learning rate $\eta = 0.5$, penalty $\lambda = 1$ (section 4), trees with one split. Start at margin 0, so $p = 0.5$ for every pair. Then $g = p - y$ is $+0.5$ for the three non-matches (a, b, d) and $-0.5$ for the five matches, and every $h = 0.25$.

**Round 1.** The best split is $x < 0.50$. Left holds a, b, c, d: $G_L = 1.0$, $H_L = 1.0$. Right holds e, f, g, h: $G_R = -2.0$, $H_R = 1.0$. Each leaf takes the step $w = -G/(H+\lambda)$:

- left: $-1.0/(1.0+1) = -0.5$, times $\eta$ gives $-0.25$;
- right: $2.0/(1.0+1) = +1.0$, times $\eta$ gives $+0.50$.

**Round 2.** Now $p = 0.438$ for a, b, c, d and $p = 0.622$ for e, f, g, h. The best new split is $x < 0.275$: it separates a and b, the two lowest-overlap non-matches, from the rest. Leaf steps (after $\eta$): $-0.293$ for a, b and $+0.336$ for c to h.

| | margin | p | log loss |
|---|---|---|---|
| start | 0 for all | 0.50 | 0.693 |
| after round 1 | a-d: -0.25, e-h: +0.50 | 0.44 / 0.62 | 0.556 |
| after round 2 | a, b: -0.543; c, d: +0.086; e-h: +0.836 | 0.37 / 0.52 / 0.70 | 0.468 |

Running the same data through XGBoost (`max_depth=1`, `eta=0.5`, `lambda=1`, exact tree method) gives identical thresholds, leaf values and margins. Two lessons. First, loss falls a little with each tree, so we need many rounds. Second, with one feature the model cannot separate c from d, so it lifts both. Real models win by having many features that disagree in useful ways.

---

## 4. XGBoost specifics

### 4.1 The regularised objective

XGBoost (Chen and Guestrin 2016) adds a penalty on the size of each tree. At round $t$ it minimises

$$\mathcal{L}^{(t)} = \sum_i \ell\big(y_i,\ \hat y_i^{(t-1)} + f_t(x_i)\big) + \gamma\,T + \tfrac12 \lambda \sum_{j=1}^{T} w_j^2 ,$$

where $T$ is the number of leaves, $w_j$ the leaf values, $\gamma$ a price per leaf, and $\lambda$ an L2 penalty on leaf values. The loss is replaced by its second-order Taylor expansion around the current prediction. For leaf $j$ define $G_j = \sum g_i$ and $H_j = \sum h_i$ over the rows in it. The best leaf value and the value of a split are

$$w_j^{\star} = -\frac{G_j}{H_j + \lambda}, \qquad \text{Gain} = \tfrac12\left[\frac{G_L^2}{H_L+\lambda} + \frac{G_R^2}{H_R+\lambda} - \frac{(G_L+G_R)^2}{H_L+H_R+\lambda}\right] - \gamma .$$

A split is kept only if its gain is positive. This is a Newton step per leaf: the hessian sizes the step ([F13](F13-linear-algebra-and-optimisation.md), the section on second-order information).

**Worked example.** Round 1 above: $G_L = 1$, $H_L = 1$, $G_R = -2$, $H_R = 1$, $\lambda = 1$. The bracket is $1/2 + 4/2 - 1/3 = 2.1667$. Half of it is the gain, 1.0833. The XGBoost library reports the bracket without the one half (it printed 2.1667), so reported gains are twice the formula above. The ranking of splits is the same.

### 4.2 What each knob does

| knob | meaning |
|---|---|
| `eta` | learning rate: how much of each tree to add |
| `max_depth` | longest path in a tree |
| `lambda`, `gamma` | penalty on leaf values; minimum gain for a split |
| `min_child_weight` | minimum sum of hessians in a child, not a row count |
| `subsample` | fraction of rows each tree sees |
| `colsample_bytree` | fraction of features each tree sees |
| `max_bin` | number of histogram bins per feature |

**`min_child_weight` in numbers.** For the log loss each pair adds $h = p(1-p)$. A pair at $p = 0.5$ adds 0.25, so a floor of 10 needs 40 such pairs. A pair at $p = 0.001$ adds 0.000999, so the same floor needs about 10,010 pairs. The rule therefore lets the trees spend splits where the model is unsure, and stops them from carving tiny leaves out of near-certain pairs.

**Sample weights.** A row with weight $w$ contributes $w\cdot g$ and $w\cdot h$, so it acts like $w$ copies of the row. Our French pseudo-labelled rows get weight 3 (option `--pseudo-weight` in [s2.py](../../../experiments/ameya/model-v1/s2.py)). They then count three times in every leaf sum, and also towards `min_child_weight`. A variant with weight 5 had the same estimated gain (+0.000167 against +0.000166 in leaderboard units, [RESEARCH_v6](../../../experiments/ameya/model-v1/RESEARCH_v6.md)), so the weight had saturated.

**Our settings.** All four stages use `binary:logistic` with `tree_method=hist`, `max_bin=256` and `subsample=0.8`.

| stage | depth | eta | min_child_weight | colsample_bytree | other |
|---|---|---|---|---|---|
| 0 | 6 | 0.2 | 5 | 0.8 | 200 rounds, 10% sample of training S1 |
| 1 | 9 | 0.06 | 10 | 0.7 | lambda 2; early stopping 60 rounds, at most 4000 |
| 2 | 7 | 0.05 | 10 | 0.8 | lambda 2; early stopping 60; only pairs with p1 at least 0.002 |
| 3 | 6 | 0.1 | 20 | (default) | early stopping 50 rounds, at most 2000 |

Source: [s1.py](../../../experiments/ameya/model-v1/s1.py), [s2.py](../../../experiments/ameya/model-v1/s2.py), [stage3.py](../../../experiments/ameya/model-v1/stage3.py). Deep trees are reasonable with millions of rows and many interacting features, and `lambda`, `min_child_weight`, shrinkage and early stopping guard against overfitting.

### 4.3 Histogram splits

The exact method scans every sorted feature value at every node. The histogram method cuts each feature once into at most 256 quantile bins. At a node it sums $g$ and $h$ per bin in one pass over the rows, then scans the bins from left to right to find the best threshold. A child's histogram is its parent's minus its sibling's, so only the smaller child needs a pass. Features are stored as small bin numbers instead of 4-byte floats, which cuts memory and bandwidth.

**Worked example.** Cut $x$ at 0.25, 0.50 and 0.75. Round 1 sums:

| bin | pairs | G | H |
|---|---|---|---|
| below 0.25 | a, b | +1.0 | 0.5 |
| 0.25 to 0.50 | c, d | 0.0 | 0.5 |
| 0.50 to 0.75 | e, f | -1.0 | 0.5 |
| above 0.75 | g, h | -1.0 | 0.5 |

Scanning gives $(G_L, H_L)$ = (1.0, 0.5), then (1.0, 1.0), then (0.0, 1.5). The middle one is the split at 0.50 with gain 1.0833, the same answer as the exact method.

### 4.4 Missing values

At each split XGBoost learns a default direction for NaN by trying both sides and keeping the better. So NaN is information, not a gap to fill. In our features NaN means "undefined", for example an empty address on one side.

### 4.5 Early stopping

Training stops when the validation loss has not improved for a set number of rounds (60 for stages 1 and 2). Our validation rows are a 2% hash slice of S1 taken from inside the training groups, never the group being scored. If we chose the stopping point with the scored group's own labels, those labels would leak into its scores ([F18](F18-tuning-ensembles-and-interpretability.md)).

LightGBM (Ke et al. 2017) grows trees leaf-wise instead of level-wise; CatBoost uses ordered statistics for categorical features. The boosting idea is the same.

---

## 5. Stacking and cascades

### 5.1 Stacking and why it needs out-of-fold scores

**Intuition.** Stacking (Wolpert 1992) feeds the score of one model into a second model as a feature. The second model can then ask questions that only make sense once every pair has a score: "Is this the best S1 for this record?", "How many confident copies does this S1 already have?"

**The leak.** A model's score on rows it was trained on is too good. If stage 2 learned from such scores it would learn to trust them too much, and fail on new data. So each stage is trained on **out-of-fold (OOF)** scores: scores for a row produced by a model that never saw that row.

**Our folds.** The fold of an S1 is `splitmix64(eid) mod 20`. Folds 0 to 4 (about 25% of train S1, 549,699 S1) are the holdout. Folds 5 to 19 form three OOF groups: 5-9, 10-14, 15-19. A model that scores group $g$ is trained on the other two groups only, and the holdout and test get the mean of the group models ([splits.py](../../../code/business_entity_resolution/src/ber/eval/splits.py)). We split by S1, not by pair, because all pairs of one S1 share its rivals and labels, and splitting them would leak.

### 5.2 The four stages

| stage | what it does |
|---|---|
| 0 | a cheap filter; drops about 80% of the retrieved pairs |
| 1 | the pair model; gives p1, which sets the candidate cut (p1 at least 0.02) and picks the pairs the cross-encoders read |
| 2 | adds context: per record, the best and second-best p1 among its S1, the margin to the best rival, its rank; per S1, counts of confident records; plus the cross-encoder score and French pseudo-labelled rows; the output is calibrated with isotonic regression |
| 3 | re-scores each pair against the other candidates of its S1 |

Stage 2 is collective: its group features are computed from stage-1 scores over the whole candidate graph, not from one pair ([s2.py](../../../experiments/ameya/model-v1/s2.py) docstring). Calibration (so that "0.9" means 90%) is the subject of [07-calibration](../07-calibration.md).

### 5.3 Cascades and the cost of looking closely

**Intuition.** A cascade spends effort in proportion to doubt. Most retrieved pairs are obvious non-matches, so a cheap model removes them and the expensive models see only what is left.

**Worked example (arithmetic on numbers from the method note).**

- Retrieval gives 58.4M test pairs. Stage 0 drops about 80%, so about 11.7M go to stage 1.
- The candidate file keeps 6,410,308 pairs, 11% of the retrieved ones.
- The cross-encoders read the band 0.02 to 0.99: 1.49M pairs, 2.55% of the retrieved ones.
- The 7B model scores about 600 pairs per second on an H100. All 58.4M pairs would take 97,333 s, about 27 GPU-hours. The 1.49M band takes 2,483 s, about 41 minutes.

The principle is in the [method note](../../../experiments/ameya/final-zip/doc/Documentation_template.md): spend effort where the uncertainty is. More in [F08](F08-computing-at-scale.md).

We used stacking for the XGBoost chain and a plain z-scored average for the cross-encoders (blending and averaging are compared in [F18](F18-tuning-ensembles-and-interpretability.md)).

---

## 6. Feature importance versus SHAP

### 6.1 Built-in importance

XGBoost can report, per feature, how often it was used in a split (`weight`), the average gain of those splits (`gain`) or the average amount of data they touched (`cover`). Our [s1.py](../../../experiments/ameya/model-v1/s1.py) records the top 25 by gain in its report. Pitfalls: the numbers describe how the trees were built, not how predictions depend on a feature; impurity-based importances favour features with many possible thresholds (Strobl et al. 2007); and when two features carry the same information, credit is split between them arbitrarily ([F18](F18-tuning-ensembles-and-interpretability.md)).

### 6.2 SHAP

**Intuition.** Features work together, so how do we share the credit for one prediction? Game theory has an answer: Shapley values (Shapley 1953). Treat the features as players in a team and the prediction as the team's payoff. A feature's credit is its average marginal contribution over all orders in which the team could be assembled.

**Definition.** For a set of features $N$ and a value function $v(S)$ (the model's output when only the features in $S$ are known):

$$\phi_i = \sum_{S \subseteq N\setminus\{i\}} \frac{|S|!\,(|N|-|S|-1)!}{|N|!}\,\big[v(S\cup\{i\}) - v(S)\big].$$

SHAP (Lundberg and Lee 2017) applies this to model predictions. Its key property is **local accuracy**: the contributions add up exactly to the prediction minus a base value. TreeSHAP (Lundberg et al. 2020) computes the exact values for tree ensembles quickly. For XGBoost they are in margin (log-odds) units, with a bias column, and each row sums to the margin. This holds on the toy model of section 3.2 (checked).

**Worked example.** Two features, name overlap and house number. Model output in log-odds: nothing known, -3; name only, -1; number only, -2; both, +3.

- Name credit: average of "name added first" $(-1)-(-3) = 2$ and "name added after number" $3-(-2) = 5$, which is $3.5$.
- Number credit: average of $(-2)-(-3) = 1$ and $3-(-1) = 4$, which is $2.5$.
- Sum: $3.5 + 2.5 = 6 = 3 - (-3)$. The credits add up. The interaction (together they are worth more than apart) is shared fairly.

### 6.3 How we used SHAP: two France biases

France was scored less confidently than the US and India. [RESEARCH_v6](../../../experiments/ameya/model-v1/RESEARCH_v6.md) section 2.9 used SHAP to find out why. The stage-1 attributions reproduced p1 exactly, the stage-2 matrix was rebuilt exactly per country, and France was compared with the US and India inside the same kind of edit (for example word swaps, acronyms). Exact copies were fine. True-copy families lost 1 to 5 logits, from two causes:

| cause | cost | what was tried |
|---|---|---|
| France has no labels, so its look-alike word odds are a label-free proxy: the share of close pairs where the house number moved when the word was extra. "groupe", "france" and "developpement" each sit in about 6,500 same-address pairs (true copies) and about 26k nudged pairs (look-alikes), so the proxy gave them -4.84, the value of "holding" | -5 to -6 logits on about 75 pairs per 1000 French S1 | cap the proxy at -1.25 (the US label odds of "partners"); estimated at about +0.0004 France F0.5; not packaged when the note was written |
| French house numbers are small and shared, so a rival S1 on the same street scores almost as high, which depresses the retrieval margin | -0.4 to -2.8 logits | recompute the margin among rivals at the same number; mixed, small effect; not adopted |

Good practice here: SHAP found the suspects, and then each suspect was tested by changing the input and re-scoring, not just by reading plots. The estimate for the first fix is an estimate, because France has no labels.

---

## How it shows up in our project

- The four stages: [s1.py](../../../experiments/ameya/model-v1/s1.py) (stages 0 and 1), [s2.py](../../../experiments/ameya/model-v1/s2.py) (stage 2, isotonic calibration, self-training), [stage3.py](../../../experiments/ameya/model-v1/stage3.py).
- Folds and groups: [splits.py](../../../code/business_entity_resolution/src/ber/eval/splits.py). Features: [FEATURES.md](../../../experiments/ameya/model-v1/FEATURES.md). Method and numbers: [method note](../../../experiments/ameya/final-zip/doc/Documentation_template.md), section 4.
- Advanced pages: [06](../06-gradient-boosting-and-stacking.md), [07](../07-calibration.md), [09](../09-self-training-and-domain-shift.md).

## How to read the numbers

- **Training logs.** `best iteration 1599` means 1,600 trees are used (iterations start at 0, and the code uses `best + 1`). The `es logloss` is the log loss on the early-stopping slice.
- **Logit units.** A deficit of 5 logits multiplies the odds by $e^{-5} = 0.0067$. A pair at $p = 0.9959$ (logit 5.5) falls to logit 0.5, so $p = 0.62$. That is how a "small" bias crosses a decision threshold.
- **Tiny gains.** On the v6all model, stage 3 added +0.000055 holdout F0.5 with 95% interval [+0.000025, +0.000085] (RESEARCH_v6). Both ends are above zero, so it is real on the holdout, but it is small. Judge a gain by its interval, not its size ([F09](F09-experiments-and-evidence.md), [F12](F12-interpreting-our-results.md)).

## Common misconceptions

1. "Deeper trees are better." Deep trees overfit unless data is large and guards are in place.
2. "Boosting fits the residuals." Only for squared error. In general it fits gradients, with hessians.
3. "Forests and boosting reduce error the same way." Forests mostly cut variance by averaging independent deep trees, and plateau. Boosting mostly cuts bias by sequential correction, and can overfit if run too long, so it needs early stopping.
4. "`min_child_weight` is a row count." It is a sum of hessians, and equals a row count only when every $h = 1$.
5. "Feature importance shows what causes matches." It describes the model, and correlated features split credit.
6. "SHAP values are probabilities." For XGBoost they are in log-odds by default.
7. "Stacking on in-sample scores is fine." It leaks. Use out-of-fold scores, grouped by S1.

## Check yourself

Exercise 1. A node has 8 pairs: 3 matches and 5 non-matches. A question sends 4 pairs left (3 matches, 1 non-match) and 4 right (0 matches). Compute the Gini gain.

<details><summary>Answer</summary>

Parent Gini: $1 - (3/8)^2 - (5/8)^2 = 1 - 0.1406 - 0.3906 = 0.46875$. Left: $1 - 0.75^2 - 0.25^2 = 0.375$. Right: pure, 0. Weighted children: $0.5\times 0.375 + 0.5\times 0 = 0.1875$. Gain $= 0.46875 - 0.1875 = 0.28125$.

</details>

Exercise 2. In a bootstrap sample of size 5, what is the chance that row 1 is never drawn? What does it tend to for large $n$?

<details><summary>Answer</summary>

Each draw misses row 1 with probability $4/5$, so $(4/5)^5 = 0.32768$. For large $n$, $(1-1/n)^n \to 1/e = 0.368$.

</details>

Exercise 3. Trees have $\sigma^2 = 4$ and pairwise correlation $\rho = 0.5$. Compute the variance of an average of $B = 16$ trees, and the floor as $B \to \infty$. How does a random forest try to lower the floor?

<details><summary>Answer</summary>

$\rho\sigma^2 + (1-\rho)\sigma^2/B = 2 + 0.5\times 4/16 = 2.125$. The floor is $\rho\sigma^2 = 2$. A random forest picks a random subset of features at each split, which makes the trees less correlated, so $\rho$ falls.

</details>

Exercise 4. Two rows both have $p = 0.8$, one with $y=0$ and one with $y=1$. Find $g$ and $h$ for each, and the leaf value if both fall in one leaf with $\lambda = 1$.

<details><summary>Answer</summary>

Row with $y=0$: $g = 0.8$, $h = 0.16$. Row with $y=1$: $g = -0.2$, $h = 0.16$. $G = 0.6$, $H = 0.32$. Leaf value $-G/(H+\lambda) = -0.6/1.32 = -0.4545$. The leaf lowers the margin because only 1 of its 2 pairs is a match, below the predicted 0.8.

</details>

Exercise 5. A split has $G_L = 3$, $H_L = 4$, $G_R = -2$, $H_R = 3$, $\lambda = 1$, $\gamma = 0.5$. Is the split kept?

<details><summary>Answer</summary>

Bracket: $9/5 + 4/4 - 1^2/8 = 1.8 + 1 - 0.125 = 2.675$. Gain $= \tfrac12\times 2.675 - 0.5 = 0.8375 > 0$, so it is kept.

</details>

Exercise 6. With `min_child_weight` = 10, how many pairs at $p = 0.02$ does a leaf need? What if each pair has weight 3?

<details><summary>Answer</summary>

$h = 0.02\times 0.98 = 0.0196$. $10/0.0196 = 510$ pairs. With weight 3 each pair adds $0.0588$, so $10/0.0588 = 170$ pairs.

</details>

Exercise 7. Why must stage 2 be trained on stage-1 scores that are out of fold?

<details><summary>Answer</summary>

Stage 1 scores its own training rows too well (positives near 1). If stage 2 trained on those, it would learn to trust p1 more than it deserves, and on test data, where p1 is honest and noisier, it would be overconfident. OOF scores have the same noise level on training rows as on new rows.

</details>

Exercise 8. Why do we split into OOF groups by S1 and not by pair?

<details><summary>Answer</summary>

Pairs of the same S1 share its rivals, its labels and its context features. If one pair were in training and another in validation, the model would see information about the validation pair's S1, and scores would be too optimistic. Splitting by S1 keeps each S1's pairs together.

</details>

Exercise 9. Two features have Shapley credits 3.5 and 2.5 on a pair, and the base value is -3. What is the margin and the probability?

<details><summary>Answer</summary>

Margin $= -3 + 3.5 + 2.5 = 3.0$. $p = 1/(1+e^{-3}) = 0.9526$.

</details>

Exercise 10. SHAP says a word-odds feature pushes French pairs down by 5 logits. A pair would score $p = 0.999$ without that push. What is its probability with it? Why does this matter for the per-S1 decision?

<details><summary>Answer</summary>

$\text{logit}(0.999) = 6.907$. Subtract 5: 1.907, so $p = 0.871$. The per-S1 decision maximises expected F0.5 from calibrated probabilities. A pair that should be at 0.999 but sits at 0.871 is more likely to be left out when its S1 has a rival, which costs recall ([F11](F11-decision-theory-and-optimisation.md)).

</details>

## Going deeper

- Breiman, Friedman, Olshen and Stone (1984). Classification and Regression Trees.
- Breiman (1996). Bagging predictors. Breiman (2001). Random forests.
- Freund and Schapire (1997). A decision-theoretic generalization of on-line learning and an application to boosting.
- Friedman (2001). Greedy function approximation: a gradient boosting machine.
- Chen and Guestrin (2016). XGBoost: a scalable tree boosting system. Ke et al. (2017). LightGBM: a highly efficient gradient boosting decision tree.
- Wolpert (1992). Stacked generalization.
- Shapley (1953). A value for n-person games. Lundberg and Lee (2017). A unified approach to interpreting model predictions. Lundberg et al. (2020). From local explanations to global understanding with explainable AI for trees.
- Strobl, Boulesteix, Zeileis and Hothorn (2007). Bias in random forest variable importance measures.
- Hastie, Tibshirani and Friedman (2009). The Elements of Statistical Learning, chapters 9, 10 and 15.
- XGBoost documentation: "Introduction to Boosted Trees".

## Where next

- [F18 tuning, ensembles and interpretability](F18-tuning-ensembles-and-interpretability.md): permutation importance, LIME, why diversity beat accuracy.
- [F14 information theory and losses](F14-information-theory-and-losses.md): log loss, entropy, proper scoring.
- [F13 linear algebra and optimisation](F13-linear-algebra-and-optimisation.md): the Newton step in detail.
- [06 gradient boosting and stacking](../06-gradient-boosting-and-stacking.md) and [07 calibration](../07-calibration.md) for the advanced treatment.
