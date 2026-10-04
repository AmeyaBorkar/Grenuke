# F18. Tuning, ensembles and interpretability

**Summary**

- Tuning means choosing settings without fooling yourself. Search sensibly, stop early on a slice that scoring never touches, and remember that every look at a validation score spends some of its honesty.
- An ensemble beats its members when their errors differ. For France, diversity beat accuracy: a weaker model from another family lifted the mean more than a stronger sibling. We combined the cross-encoders by a z-scored mean of their logits.
- Interpretation tools generate suspects, not proofs. Error analysis (slices, loss ledgers, ablations) tells us where the score is lost and what a fix is worth.

## What you need first

- [F03 machine learning fundamentals](F03-machine-learning-fundamentals.md): validation, overfitting, bias and variance.
- [F05 trees and ensembles](F05-trees-and-ensembles.md): stacking, out-of-fold scores, SHAP basics.
- [F07 neural networks, transformers, LLMs](F07-neural-networks-transformers-llms.md): cross-encoders, logits, z-scoring.
- [F09 experiments and evidence](F09-experiments-and-evidence.md): the paired bootstrap and gates. [F14](F14-information-theory-and-losses.md): losses.

---

## 1. Hyperparameters and the validation problem

**Intuition.** Training sets the **parameters** (leaf values, network weights). We set the **hyperparameters** (depth, learning rate, LoRA rank, batch size, the decision layer's logit shift). Choosing them means trying settings and scoring each one, and every score is a noisy measurement.

**The winner's curse.** Suppose $K$ settings are truly equal, and each score has noise of size $\sigma$. The best-looking one is then above the truth by the expected maximum of $K$ standard normal draws, times $\sigma$:

| $K$ | 2 | 5 | 10 | 20 | 50 | 100 |
|---|---|---|---|---|---|---|
| expected maximum ($\sigma$ units) | 0.56 | 1.16 | 1.54 | 1.87 | 2.25 | 2.51 |

**Worked example.** The per-S1 decision beat the best global threshold by +0.000048 on the local holdout, with 95% interval [0.000007, 0.000091] ([method note](../../../experiments/ameya/final-zip/doc/Documentation_template.md)). The standard error is about $(0.000091-0.000007)/2/1.96=0.000021$. If we had tried 20 variants with no true gain, the best would still look about $1.87\times0.000021=+0.00004$ better, almost the whole claimed gain. So a gain of this size is only believable with controls. Ours were: confirm on both halves of the holdout, check random subsets, use paired bootstraps, and let ties go to the simpler option ([AGENTS.md](../../../AGENTS.md)). An out-of-sample check showed the optimism: the stacked decision rules gained +48.1e-6 on the holdout but +23.7e-6 under repeated 2-fold cross-validation, positive in 86% of 42 splits ([MODEL_CHOICE.md](../../../experiments/bakshi/final-package/MODEL_CHOICE.md)). About half the in-sample gain survived.

## 2. Search strategies

- **Grid search** tries every combination: $k$ values for each of $h$ settings is $k^h$ runs (3 values for 6 settings is 729). It wastes runs when only a few settings matter.
- **Random search** (Bergstra and Bengio 2012) draws each setting independently. With 9 trials you see 9 distinct values of each setting, while a 3 by 3 grid over two important settings shows 3 of each. When only two of six settings matter, random search covers them far better.
- **Bayesian optimisation** (Snoek et al. 2012) fits a cheap surrogate of score against settings (a Gaussian process, or tree-structured density estimators) and picks the next trial where improvement looks most likely. It pays when each trial is costly, such as a 7B fine-tune (about 2 hours on three H100s).
- **Successive halving and Hyperband** start many settings on a small budget, keep the better half, double the budget, and repeat.

Practical rules: search learning rates on a log scale; tune the few settings that matter first (learning rate, depth or rank, regularisation); keep seeds fixed inside one comparison. Our stage settings are listed in [F05](F05-trees-and-ensembles.md). The three decision-layer settings (a +0.2 logit shift, a further $-0.3$ for records that four or more S1 compete for, and 0.01 expected true matches outside the candidate set) were tuned on the local holdout, a small search that is exposed to the effect in section 1.

## 3. Early stopping and validation reuse

**Early stopping** picks the number of trees where validation loss stops improving (Prechelt 1998). That makes the validation score optimistic, because the set chose the stopping point. So our early-stopping rows are a 2% hash slice of S1 inside the training groups, never the group being scored and never the holdout. Calibration is fitted the same way, on training folds only.

Leakage hides in feature construction too. The look-alike word odds are counted from labels, so rows in a training fold use counts from the other two groups only; the holdout and test use all training folds ([FEATURES.md](../../../experiments/ameya/model-v1/FEATURES.md)). Any label-derived feature must be built out of fold, exactly like a stacked score.

The holdout itself is reused for many decisions. Each use leaks a little, which is why late rules had to win on both halves of it.

## 4. Ensembling theory

**Intuition.** Ask several people and average. If they err in different ways, errors cancel. If they all repeat the same mistake, averaging does nothing.

**Bias-variance-covariance.** For the average $\bar f$ of $M$ predictors (Ueda and Nakano 1996), with squared error:

$$E\big[(\bar f-y)^2\big]=\overline{\text{bias}}^{\,2}+\frac1M\,\overline{\text{var}}+\Big(1-\frac1M\Big)\overline{\text{cov}} ,$$

where the bars are averages over members and cov is the average pairwise covariance. As $M$ grows, the variance term vanishes. The floor is bias squared plus the covariance. Only more diverse members, with lower covariance, lower the floor. Worked example: bias 0.2, variance 1, pairwise correlation 0.5:

| members $M$ | 1 | 2 | 5 | 10 | infinite |
|---|---|---|---|---|---|
| error | 1.04 | 0.79 | 0.64 | 0.59 | 0.54 |

At correlation 0.9 the same members give 0.96 at $M=5$ and 0.94 at infinity: nearly no gain. A simulation confirms the formula.

**Ambiguity decomposition** (Krogh and Vedelsby 1995). For an average under squared error, ensemble error equals average member error minus average disagreement with the ensemble mean. Example: truth 1, members 0.6, 1.4, 1.0. Member errors average 0.107, disagreement averages 0.107, so the ensemble error is 0. If all three said 0.6, disagreement would be 0 and nothing would be gained. A member helps when it is accurate enough and also disagrees with the others.

**Voting shows the same thing.** Three classifiers, each right 80% of the time, vote. If their errors are independent, the majority is right with probability $3(0.8)^2(0.2)+0.8^3=0.896$. If they always err together, the majority is right 0.8 of the time: no gain.

**Sources of diversity**: different model families, data subsets (bagging), feature sets, seeds, training objectives and training domains.

## 5. Our finding: diversity beat accuracy for France

France has no labels. [RESEARCH_v6](../../../experiments/ameya/model-v1/RESEARCH_v6.md) section 6.13 measured cross-encoder logits on France's rule populations (53,290 band pairs whose labels come from our rules, since France has no ground truth), against the US/India holdout band AUC:

| cross-encoder input | French rule AUC | US/India band AUC |
|---|---|---|
| e5-base | 0.687 | 0.929 |
| bge-reranker-v2-m3 | 0.774 | 0.942 |
| e5-large, 2 epochs | 0.792 | 0.944 |
| e5-large, 1 epoch | 0.803 | 0.939 |
| mean of the two e5-large runs | 0.806 | 0.943 |
| mean of e5-large (two runs) and bge | 0.826 | 0.943 |
| mean of e5-large (1 epoch) and bge | 0.829 | |
| mean of e5-large (two runs), bge and e5-base | 0.813 | 0.942 |

Reading it: bge is weaker than either e5-large on France (0.774 against 0.792 and 0.803), yet adding it to the e5-large mean lifts France by 0.020 (0.806 to 0.826), because it is a different model family, so its French errors are decorrelated from e5's (the note's explanation). US/India is unchanged at 0.943: the models already agree there, so there is nothing to gain. Adding the weak e5-base lowers the mean (0.826 to 0.813): diversity needs competence. The second e5-large epoch specialised towards US/India (holdout up, France down). This is the ambiguity decomposition in action.

**A gate for diversity.** Qwen entered only after a predeclared gate: band AUC above 0.93 (Qwen 1.5B: 0.9381) and correlation with e5-large at most 0.975 (observed 0.9433), so it had to be both accurate and diverse ([MODEL_CHOICE.md](../../../experiments/bakshi/final-package/MODEL_CHOICE.md)). The method note adds that the 7B is no more accurate than a self-trained e5-large (both 0.944), but counted twice in the US/India mix it gained +0.000066 on India (paired bootstrap P 0.998) and +0.000026 on the US (P 0.906, not significant).

**Why one z-scored mean.** We average each model's z-scored logits into a single stage-2 feature ([zmean_ce.py](../../../experiments/ameya/model-v1/zmean_ce.py), [F07](F07-neural-networks-transformers-llms.md)), not separate columns. With separate scores, stage 2 extrapolated on pairs where the models disagree, and they disagree about four times as often in France. A tree fitted on mostly-agreeing training pairs has seen few such combinations. One mean is dense in the data. A learned blend as the decision score was also 0.001 lower in F0.5 ([method note](../../../experiments/ameya/final-zip/doc/Documentation_template.md), appendix B).

## 6. Stacking, blending, averaging

| method | what is fitted | data it needs | main risk | where we used it |
|---|---|---|---|---|
| plain or z-scored average | nothing, or one mean and spread per model | none | weights not optimal | the cross-encoders |
| weighted average | one weight per model | a labelled validation set | overfits with many models | tried as a learned blend: worse |
| blending | a meta-model | a held-out set the base models never saw | wastes data | not used |
| stacking | a meta-model | out-of-fold predictions on all training data | leakage if folds are wrong | XGBoost stages 0 to 3 |

Stacking rules: split by S1, build every label-derived feature out of fold, and give the holdout and test the mean of the fold models ([F05](F05-trees-and-ensembles.md)).

## 7. Interpretability

**Kinds.** An **intrinsic** explanation comes from a simple model (a short tree, a linear model). A **post-hoc** one explains a complex model afterwards. A **global** explanation covers the whole model; a **local** one covers one prediction.

**Built-in importance** (gain, weight, cover) describes how the trees were built, favours features with many thresholds (Strobl et al. 2007), and splits credit between correlated features.

**Permutation importance** (Breiman 2001; Fisher, Rudin and Dominici 2019). Shuffle one feature in held-out data and measure how much the loss rises. Pitfalls: shuffling breaks correlations and creates impossible rows (house number equal but street different), and credit splits among duplicates. Worked example: $y=3x$, and two features $x_1=x_2=x$ with unit variance. Model A uses only $x_1$ (weights 3 and 0). Model B uses both (1.5 and 1.5). Their predictions are identical. Shuffling $x_1$ raises the squared error by 18 in A, but by 4.5 in B, where $x_2$ also scores 4.5. Importance belongs to the model, not to the data.

**SHAP** ([F05](F05-trees-and-ensembles.md)). Exact for trees, additive in log-odds, local. Cautions (Kumar et al. 2020): it depends on how hidden features are filled in, correlated features share credit, and it explains the model's output, not the world.

**LIME** (Ribeiro et al. 2016). Perturb one instance, ask the model about each perturbation, and fit a weighted linear model nearby. The coefficients explain that prediction locally. Results depend on the sampling and the neighbourhood width, so they can change from run to run.

**Partial dependence** (Friedman 2001) averages the prediction over the data while one feature is set to each value on a grid; **ICE** curves show the same per instance, revealing differences the average hides. With correlated features the grid visits unrealistic points. ALE plots reduce this.

**Pitfalls.** Explanations describe a model, not causes. Many different models fit equally well and explain differently (the Rashomon effect). An explanation that "makes sense" is easy to over-trust. Our practice with SHAP in France was to treat the output as suspects and test each by changing the input and re-scoring ([F05](F05-trees-and-ensembles.md) section 6.3).

## 8. Systematic error analysis

**Slice.** Break the score down by country, source (S2 or S3), error type, name length, empty address and generic names. Look for slices where loss per S1 is high and the slice is large. Many small slices raise the risk of a false alarm, so confirm suspicious ones on separate data.

**The loss ledger.** The macro score is an average over S1, so the total loss $1-F_{0.5}$ splits exactly into per-S1 losses, which can be grouped into non-overlapping categories. Toy ledger, 10 S1:

| category | S1 | loss | share of total |
|---|---|---|---|
| missed some copies, no false positives | 2 | 0.139 | 4.7% |
| missed everything | 1 | 1.000 | 34.1% |
| predicted something for an S1 with no copies | 1 | 1.000 | 34.1% |
| mixed false positives and misses | 2 | 0.796 | 27.1% |

The loss column adds per-S1 losses (total 2.934). Divided by 10 S1, the loss is 0.293 and the macro F0.5 is 0.707. Two S1 out of ten, one missed completely and one wrongly given a prediction, carry 68% of the loss.

**Our ledger** ([method note](../../../experiments/ameya/final-zip/doc/Documentation_template.md) section 5). On the local holdout precision is 99.9% and recall 97.5%, so the remaining loss is mostly recall: 69% of it from S1 where we found some copies but not all, 20% from S1 we missed completely. The missed copies are mostly empty-address records with a changed name: 16.5k never become candidates and 15.2k get a score near zero. In France the costliest false positives were generic-name decoys (same name and house number, different street): such a pair is a real match 0.5% of the time when our model rejects it and 99.7% when it accepts it.

**Error types named in the method note.** False positives: generic-name decoys in France (same name and house number, other street); a business word swapped at the same address ("antenne danse" against "antenne gaz"); very short names that differ by one letter ("osd" against "otd"); branches of one chain that share a name. False negatives: empty address plus a changed name; heavy garbles ("ehpad" typed as "ehpvd"). Each type suggests a different remedy: a second reader for the decoys, better keys for the garbles.

**Empty-address records** form their own slice. With no address, the name must carry the match. In the label-free French checks, pairs with the same content words up to typos and an empty record address were 97.7% true ([RESEARCH_v6](../../../experiments/ameya/model-v1/RESEARCH_v6.md) section 6.14), and stage 3 calibrates the total probability of such a record separately (about +0.00005 on the holdout together with a second change).

**By country.** On the local holdout the macro F0.5 is 0.9913: US 0.9911 and India 0.9916. France cannot be sliced this way, because it has no labels.

**What a fix is worth.** Gain $\approx$ (S1 affected) $\times$ (change in $F$ per S1) $\div$ (total S1). An added pair helps only if its chance of being right exceeds $F/(1+\beta^2)=0.8F$ for $\beta=0.5$, about 0.75 for an S1 at $F\approx0.94$. None of the recall rules we tried was more than 71% precise, so none was added. Fixes for one country convert through the leaderboard weights (US 0.38274, India 0.46751, France 0.14975, [RESEARCH_v6](../../../experiments/ameya/model-v1/RESEARCH_v6.md) section 3): a France-only gain of 0.0005 is worth $0.14975\times0.0005=+0.000075$.

## 9. Ablations

**Definition.** An **ablation** changes one component and keeps everything else fixed, then measures the difference on the same S1 with a paired comparison. Variants: remove one, add one, swap one, scale one.

**Rules.** Same data, seeds and hardware. Remember that GPU non-determinism alone moved one model from 0.991246 to 0.991261 on the holdout, so differences below about 0.0001 need paired intervals. Resample S1, not pairs. Predeclare gates. Redundant components show no effect when removed, which does not prove they are useless, only that something else covers them. Changing two things at once tells you nothing about either.

**Our ablation ledger** (all from the [method note](../../../experiments/ameya/final-zip/doc/Documentation_template.md) unless marked):

| change | result on the local holdout or leaderboard |
|---|---|
| per-S1 set selection instead of the best global threshold | +0.000048 [0.000007, 0.000091] |
| 7B re-check at logit $-6$ | +0.000037 on the whole holdout; +0.000033 on the 34% labelled sample, positive in both halves and in 99.7% of random 25% subsets |
| 7B counted twice in the mix | +0.000066 India (P 0.998), +0.000026 US (P 0.906) |
| tighter candidate cuts (best S1 per record; p1 at least 0.05) | -0.000106 and -0.000041 |
| learned blend of cross-encoders as decision score | 0.001 lower F0.5 |
| copy-count tie-breaking | -0.00057 |
| per-record renormalisation of French probabilities | up to -0.000137 |
| extra drops mined with a decision tree | failed on the held-out half |
| recall rules | at most 71% precise; none added |
| France-heavy cross-encoders (e5fr, bgefr) added to the mix | nothing measurable (RESEARCH_v6) |

**Leaderboard controls** act as ablations on the real test set. The method note reports two: the round-3 French model without the French decision layers scored 0.990833, and pushing the French 7B drops below $-6$ scored 0.990875, which it calls a tie. The final submission scored 0.990879.

---

## How it shows up in our project

- Decisions on evidence: [AGENTS.md](../../../AGENTS.md) section 3 (gates, paired bootstrap, ties to the simpler option); [F09](F09-experiments-and-evidence.md).
- Ensembling: [zmean_ce.py](../../../experiments/ameya/model-v1/zmean_ce.py), [MODEL_CHOICE.md](../../../experiments/bakshi/final-package/MODEL_CHOICE.md), RESEARCH_v6 section 6.13.
- Error analysis: method note section 5; [F12 interpreting our results](F12-interpreting-our-results.md).
- Advanced pages: [05 evaluation methodology](../05-evaluation-methodology.md), [06](../06-gradient-boosting-and-stacking.md).

## How to read the numbers

- **Gains of 1e-5 to 1e-4.** They are real only with an interval that excludes zero and a plan that did not pick them from many tries. Compare with the noise floor of about 0.0001 from hardware.
- **French rule AUC.** It measures agreement with rule-made labels, not truth, and the note itself calls it saturated for self-trained models. Use it for ranking inputs, not for absolute claims.
- **Shares in a ledger.** They are shares of loss, not of S1. A few S1 with $F=0$ can carry a third of the loss.

## Common misconceptions

1. "More models always help." Only if they are accurate enough and different enough.
2. "Tuning on the holdout is fine if it is a big holdout." Size reduces noise but not selection bias.
3. "The best of many trials is the true best." It is biased upwards.
4. "Permutation or SHAP importance reveals causes." They describe the model.
5. "If removing a component changes nothing, drop it without thought." It may be covered by another, or matter on a slice.
6. "A learned weighted blend is better than a plain average." With little or shifted data it can be worse (0.001 lower here).
7. "Early stopping on the validation set gives an unbiased score." The set chose the stopping point.

## Check yourself

Exercise 1. Five settings, four values each, as a full grid: how many runs? If only two settings matter, how many distinct values of an important setting does a random search of 30 trials try, and the grid?

<details><summary>Answer</summary>

$4^5=1024$ runs. Random search: 30 distinct values of each important setting. The grid: 4.

</details>

Exercise 2. Ten settings are truly equal; score noise is 0.00003. How much better does the best look?

<details><summary>Answer</summary>

Expected maximum of 10 normals is 1.54, so about $1.54\times0.00003=+0.000046$ better, by luck alone.

</details>

Exercise 3. Members have average bias 0.1, variance 0.5, covariance 0.2. Error of an average of $M=4$, and as $M\to\infty$?

<details><summary>Answer</summary>

$0.1^2+0.5/4+(3/4)(0.2)=0.01+0.125+0.15=0.285$. As $M\to\infty$: $0.01+0.2=0.21$.

</details>

Exercise 4. Truth 0. Two members predict $+1$ and $-1$. Compute average member error, ambiguity and ensemble error.

<details><summary>Answer</summary>

Member errors are 1 and 1, average 1. The mean is 0; each member is 1 away from it, so ambiguity is 1. Ensemble error $=0$, and $1-1=0$ checks out.

</details>

Exercise 5. Model A has AUC 0.95 and correlation 0.98 with the current mix. Model B has AUC 0.93 and correlation 0.90. Which is the better candidate, and what gate would you set?

<details><summary>Answer</summary>

B probably adds more: it disagrees more, and 0.93 may be competent enough. A is accurate but nearly a copy. Use a two-part gate like ours: AUC above a floor (0.93) and correlation below a ceiling (0.975), then test the mix on a paired comparison. Neither alone decides.

</details>

Exercise 6. Why is one z-scored mean fed to stage 2 instead of three separate cross-encoder scores?

<details><summary>Answer</summary>

Separate scores let the trees split on combinations in which the models disagree. Such combinations are rare in training and about four times more common in France, so the model extrapolates. One mean is dense in the data and carries the consensus. A learned blend was also 0.001 lower in F0.5.

</details>

Exercise 7. $y=3x$ with duplicate features $x_1=x_2=x$, $\sigma^2=1$. Model weights $(3,0)$ and $(1.5,1.5)$. Permutation importance of $x_1$ in each?

<details><summary>Answer</summary>

Shuffling $x_1$ replaces it by an independent copy $x'$. For $(3,0)$: error $=3(x-x')$, mean square $9\times2=18$. For $(1.5,1.5)$: error $=1.5(x-x')$, mean square $2.25\times2=4.5$. Same predictions, different importance.

</details>

Exercise 8. Four S1 score $F_{0.5}=1,\,0.9,\,0,\,0.75$. Macro score, total loss and the share of loss from the third S1?

<details><summary>Answer</summary>

Macro $=2.65/4=0.6625$. Loss $=0.3375$. Per-S1 losses are 0, 0.1, 1, 0.25, summing to 1.35. The third S1 carries $1/1.35=74\%$.

</details>

Exercise 9. A rule would add one pair to 100 S1 that sit at $F\approx0.94$, and the pair is right 70% of the time. Add it?

<details><summary>Answer</summary>

Break-even precision is $0.94/1.25=0.752$. At 70% the rule lowers the expected score, so do not add it.

</details>

Exercise 10. A France-only change gains 0.0012 French F0.5. Leaderboard effect?

<details><summary>Answer</summary>

$0.14975\times0.0012=+0.00018$.

</details>

Exercise 11. Two perfectly correlated features are used equally by a model. What does SHAP do, and what if the model uses only the first?

<details><summary>Answer</summary>

By symmetry it splits their joint credit equally. If the model uses only the first, that one gets all of it. Predictions are identical but attributions differ, so read attributions with the model's structure in mind.

</details>

Exercise 12. You change a feature set and a learning rate together and F0.5 rises by 0.0002. What do you conclude?

<details><summary>Answer</summary>

Nothing about either change alone, and perhaps nothing at all, since hardware noise is near 0.0001. Re-run each change separately with a paired comparison on the same S1 and report intervals.

</details>

## Going deeper

- Bergstra and Bengio (2012). Random search for hyper-parameter optimization. Snoek, Larochelle and Adams (2012). Practical Bayesian optimization of machine learning algorithms.
- Prechelt (1998). Early stopping, but when? Cawley and Talbot (2010). On over-fitting in model selection and subsequent selection bias in performance evaluation.
- Dietterich (2000). Ensemble methods in machine learning. Zhou (2012). Ensemble Methods: Foundations and Algorithms.
- Krogh and Vedelsby (1995). Neural network ensembles, cross validation, and active learning. Ueda and Nakano (1996). Generalization error of ensemble estimators. Brown, Wyatt, Harris and Yao (2005). Diversity creation methods.
- Wolpert (1992). Stacked generalization. Caruana et al. (2004). Ensemble selection from libraries of models.
- Breiman (2001). Random forests. Fisher, Rudin and Dominici (2019). All models are wrong, but many are useful. Strobl et al. (2007). Bias in random forest variable importance measures.
- Lundberg and Lee (2017). A unified approach to interpreting model predictions. Kumar et al. (2020). Problems with Shapley-value-based explanations as feature importance measures. Ribeiro, Singh and Guestrin (2016). Why should I trust you?
- Molnar. Interpretable Machine Learning (online book).

## Where next

- [F09 experiments and evidence](F09-experiments-and-evidence.md): paired bootstrap, gates, multiple comparisons.
- [F12 interpreting our results](F12-interpreting-our-results.md): what our numbers do and do not show.
- [F16 learning with limited labels](F16-learning-with-limited-labels.md): France without labels.
- [06 gradient boosting and stacking](../06-gradient-boosting-and-stacking.md) and [05 evaluation methodology](../05-evaluation-methodology.md).
