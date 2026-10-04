# Evaluation methodology: holdout, leakage, paired bootstrap, leaderboards and an unlabelled country

**Summary.** We had labels only for US and India, a private leaderboard we could not see, and a third country with no labels at all. This page explains how we measured progress honestly: a fixed 25% holdout grouped by S1, out-of-fold training, the leakage traps specific to entity resolution, the paired bootstrap for differences of 10⁻⁵, multiple comparisons, leaderboard overfitting, label-free diagnostics for France, and why our local 0.9913 sits above the public 0.990879.

Related pages: [metrics and decisions](04-metrics-and-decisions.md), [boosting and stacking](06-gradient-boosting-and-stacking.md), [calibration](07-calibration.md), [self-training and domain shift](09-self-training-and-domain-shift.md), [glossary](glossary.md).

---

## 1. Intuition

Evaluation had three jobs:
1. **An honest stand-in for the private leaderboard**, for US and India: the holdout.
2. **Telling a real gain of a few 10⁻⁵ from noise**, because late changes were that small: the paired bootstrap.
3. **Measuring what the holdout cannot see**, which is France: label-free checks and leaderboard uploads designed as experiments.

And it had three enemies: **leakage** (the answer sneaks into training), **noise** (a difference that a re-draw would erase), and **adaptive overfitting** (deciding so many times on the same data that the data stops being a fair judge).

## 2. Formal definition

### 2.1 The holdout

- **Definition** ([CONTRACTS C2][contracts], [`splits.py`][splits]): fold(eid) = splitmix64(eid) mod 20. The holdout is every train S1 with fold 0–4: **549,699 S1** (US 329,717; India 219,982), 25% of train. Training uses folds 5–19.
- **Grouped by S1**: an S1, all its candidate pairs and all its true records sit on the same side.
- **A deterministic integer hash**: identical on every machine and library version, needs no shared file, and cannot be re-drawn by accident. Tests lock the values.
- **Realistic conditions**: blocking and features search the **full** record pool, as on test; competition features use the full candidate graph; ownership competes over **all** S1. An early run let holdout records compete only among holdout S1, which made ownership too easy; it was fixed before the G6 numbers ([G6 record][g6]).
- **Never fitted on the holdout**: anything supervised, such as dictionaries learned from pairs, word odds, calibration and model weights. Tuning one or two scalars there, such as a threshold or a shift, is allowed and is a small, known optimism.
- **Noise of the absolute level**: about ±0.001 on the full holdout and ±0.002 on fold 0 alone ([CONTRACTS C2][contracts]). Differences between two systems are far less noisy (§2.4).

### 2.2 Out-of-fold training

Training folds form three **out-of-fold (OOF) groups** (5–9, 10–14, 15–19). Each group is scored by a model trained on the other two; the holdout and test are scored by models trained on all training folds ([`splits.py`][splits]). Every stage therefore learns from **honest scores** of the stage before: a stage-2 model trained on in-sample stage-1 scores would learn to trust them too much, because in-sample scores are overconfident (Wolpert 1992; [06](06-gradient-boosting-and-stacking.md)).

Supervised encodings follow the same rule: the look-alike word odds of a training row are counted on the other groups, and the Indic dictionary uses folds 5–19 only ([RESEARCH_v5 §1][r5]).

The **final fit** made the holdout a fourth OOF group, so every model saw 75% of train and every train pair kept an honest out-of-fold score; as expected, the holdout read a tie: +0.00002 [−0.00003, +0.00007] [M] ([final-fit record][ops]).

### 2.3 Leakage traps in entity resolution

| trap | what goes wrong | what we did |
|---|---|---|
| splitting by pair | the same S1 appears in training and validation through different pairs; the model learns entity-specific facts and validation flatters it | split by S1 |
| supervised statistics fitted with holdout labels | the holdout's answers shape its own features | dictionaries, word odds, calibration fitted without the holdout |
| in-sample stacking | the next stage over-trusts the previous score | OOF groups |
| a shrunken pool | fewer distractors make blocking and ownership easier | always the full record pool; ownership over all S1 |
| self-training without cross-fitting | a pseudo-labelled French pair is scored by a model that saw its own label | French S1 split into groups; each model scores only the group it did not train on ([09](09-self-training-and-domain-shift.md)) |
| IDs or row order | an accidental ordering signal | checked: correlation of S1 and record IDs over true pairs 0.0002 [M] ([RESEARCH_v5 §1][r5]) |

**Unsupervised statistics fitted on train plus test** (per-country IDF) are not leakage: they use no labels. Bakshi checked the 7B's cross-fitting directly: it rejected 0.112% of French predictions in the third of S1 its adapter never trained on, against 0.108% and 0.107% elsewhere [M] ([RESEARCH_v6 §6.19][r6]).

### 2.4 The paired bootstrap

For each holdout S1 s, let d_s = F_new(s) − F_base(s), and Δ = mean(d).
1. Resample the S1 with replacement B = 1,000 times and recompute Δ*_b each time.
2. The 95% interval is the 2.5% and 97.5% quantiles of the Δ*_b (percentile interval).
3. P(better) is the share of Δ*_b above 0.

Our implementation gives each S1 a Poisson(1) weight per resample and computes Σw·d / Σw, which at this size is equivalent to the classic bootstrap and runs 1,000 resamples over 550k S1 in seconds ([`gates.py`][gates]). The method is Efron's (Efron and Tibshirani 1993); Koehn (2004) made the paired version standard for comparing translation systems.

**Why paired.** Var(mean d) = [Var(F_new) + Var(F_base) − 2·Cov(F_new, F_base)] / n. Both systems get the same easy S1 right, so the covariance is large and most d_s are exactly 0. An unpaired comparison of two means would bury a 5 × 10⁻⁵ effect in the spread of the per-S1 scores.

**Reading the numbers.** The final decision rule gave +0.0000481 [+0.0000071, +0.0000912] ([stacked rules][stack]); the interval implies a standard error of about 2.1 × 10⁻⁵ and a per-S1 spread of d of about 0.016 (2.1 × 10⁻⁵ × √549,699) [E]. P(better) is not a p-value; under the bootstrap approximation it is roughly one minus the one-sided p-value.

**What the bootstrap does not cover.**
- **Training randomness**: an earlier model rebuilt on other hardware moved from 0.991246 to 0.991261 [M] ([methodology App. A][doc]); averaging in a second seed moved v7ce3 by −0.00004 [M]; stage 3 is not bit-reproducible across machines, with about 500 test decisions differing [M] ([RESEARCH_v6 §6.1, §6.18][r6]). Repeated runs measure this (Dietterich 1998; Bouthillier et al. 2021).
- **Distribution shift**: France and the different test pools.
- **Adaptive reuse** of the same holdout (§2.6).

### 2.5 Significance against practical size

A change of 10⁻⁵ in macro F0.5 is about 5.5 S1 flipping from wrong to right on the holdout, and about 17 on the full test. Effects of a few 10⁻⁵ can have an interval clear of zero and still sit inside training noise of 1.5–4 × 10⁻⁵. On the leaderboard, the team's estimate was that a gap below about 0.00005 between near-identical candidates is noise [E] ([RESEARCH_v6 §6.15][r6]).

The plan's gates (+0.002 for a component, +0.003 for a heavy one, interval above zero) suited the early, large components ([FINAL_PLAN §9][plan]). Late changes were 10 to 100 times smaller, so in practice a change had to have an interval above zero and be **positive on both holdout halves** (the fold-parity halves A and B), and ties went to the simpler option. Overriding a bar needed a written reason: the first cross-encoder gained +0.0014 against a +0.003 bar and was kept because it halved French look-alike acceptances [M] ([v4 record][v4]).

### 2.6 Multiple comparisons and the garden of forking paths

Try many variants on one holdout, keep the best, and the kept estimate is biased upward: the **winner's curse**. Gelman and Loken (2013) add that even without deliberate fishing, every data-dependent choice is an implicit comparison. Our own cases [M]:
- the stage-3 prototype was the best of three variants on the holdout (+0.00011); rebuilt as a pipeline step it gave +0.00005 ([RESEARCH_v5 §8.4][r5]);
- an India-only count prior scored +0.000016 [+0.000002, +0.000030] but was picked from about 160 variants and lowered the US on every model, so it was not used ([RESEARCH_v6 §6.18][r6]);
- the 7B counted twice in the mix: India +0.0000661 (P 0.998), US +0.0000262 (P 0.906, failing a multiple-testing correction); the leaderboard later put the US effect at +0.000014, so "not significant" did not mean "no effect" ([RESEARCH_v6 §6.19–6.20][r6]);
- the final decision rule: +0.000048 in sample, +0.0000237 under repeated 2-fold cross-validation ([stacked rules][stack]).

What we used against it: choose on half A and confirm on half B; repeated 2-fold CV for tuned parameters; gate rules written before the run in decision records; ties to the simpler option. What we could have added: a Holm (1979) or Benjamini–Hochberg (1995) correction across a day's comparisons, and a second untouched holdout reserved for the final choice.

### 2.7 Public and private leaderboards

The public board scores a subset of test S1; the private board, which decides the ranking, scores the disjoint rest ([task][task]). Choosing among many uploads by public score overfits the public subset (Blum and Hardt 2015; Dwork et al. 2015), although with large test sets the effect is often small (Roelofs et al. 2019).

Our policy, within a budget of 5 uploads a day ([FINAL_PLAN §5][plan]):
- **US and India decisions came from the holdout.** The leaderboard was used mainly for France, where nothing else could measure.
- **Each upload had a written hypothesis and a predicted score** ([submission records][subs]).
- **Most uploads changed one thing**, often France alone with US/India byte-identical, so the difference isolates the French effect.
- The test S1 file is shuffled: every tenth of it is 15% France, 47% India, 38% US, so any public subset is representative by country [M] ([RESEARCH_v5 §1][r5]).

Predictions against results [M]: v7n was forecast at 0.9894–0.9900 and scored 0.989721 ([sub 03][s03]); Composite B's 7B parts were forecast at +0.000149 and measured +0.000180; the round-3 France upload was forecast at +0.000069 and measured −0.000046, which taught us that estimators built on the model's own probabilities are biased on decoys ([RESEARCH_v6 §6.20][r6]).

### 2.8 Label-free diagnostics for France

| tool | what it measures | its limit |
|---|---|---|
| **leaderboard arithmetic** | LB = 0.38274·F_US + 0.46751·F_India + 0.14975·F_France (test S1 shares), so France = (LB − US/India part) / 0.14975 | needs the US/India part on test, taken from the re-weighted holdout |
| **country-isolating uploads** | France-only changes with US/India byte-identical | costs uploads; the France-emptied probe, which would have measured US/India on test, was packaged and never uploaded |
| **generator invariants** | Σ pc per record ≤ 1; Σ pc per S1 against 3.46 copies; counts and caps per S1. The US/India holdout matched its truth (3.4320 against 3.4323); France showed 3.5456, proof of overconfidence [M] ([RESEARCH_v6 §2.3][r6]) | finds excess mass, not which pairs are wrong |
| **rule-population AUC** | a model's AUC on French pairs of edit types with known US/India truth (copies 97–99.8% true, look-alikes 0–1.2%): 0.855 → 0.865 → 0.878 across our cross-encoder upgrades, tracking France's leaderboard gains [M] ([RESEARCH_v6 §6.8][r6]) | saturates (0.984) once a model trains on those populations |
| **size-bias test** | a true copy's S1 is drawn in proportion to its copy count, so its other copies follow the size-biased distribution; a mixture fit gives the false share: French acronyms 0.00 [0.00, 0.01] [M] ([RESEARCH_v6 §6.17][r6]) | weak for populations that take most of an S1's copies |
| **a stand-in country** | train on US only, score India as unlabelled: 0.96106 with known words, 0.88235 unseen, 0.95984 with proxy odds [M] ([v4 record][v4]) | India is not France |
| **the model's own expected F** | its forecast of itself | shares its blind spots: v3 forecast France at 0.970; the leaderboard implied 0.925–0.931 [M] ([RESEARCH_v5 §1][r5]) |

Credit: the invariants and the rule-population AUC are Ameya's research; the size-bias test is the error agent's (agent for Ameya); Bakshi ran the 7B leakage check; Sachi's leave-one-country-out ladder showed further self-training rounds drifting (0.882 → 0.851 → 0.831 → 0.823) [M] ([RESEARCH_v6 §6.19][r6]).

### 2.9 The holdout-versus-leaderboard gap

| upload | holdout | public LB | gap | France implied |
|---|---|---|---|---|
| v2 / v3 (25 Sep) | 0.98436 / 0.98882 | 0.97608 / 0.97961 | −0.0083 / −0.0092 | about 0.93 |
| v5all (26 Sep) | 0.990156 | 0.98781 | −0.0024 | 0.971–0.976 |
| v7nst (26 Sep) | 0.991194 | 0.990179 | −0.0010 | about 0.981 |
| **Composite B** (27 Sep) | **0.9913** | **0.990879** | **−0.0004** | **about 0.985** [E] |

All holdout and LB values [M] ([CHANGELOG][changelog], [methodology §5][doc]); France values [E].

**Other causes ruled out** ([RESEARCH_v5 §1][r5], [RESEARCH_v6 §6.15][r6]): our scorer is the official formula and matched the leaderboard arithmetic at every upload; nothing leaks; and test's pools do not lower US/India. The 23% extra records per S1 are rejected at the holdout rate, and the US test pool is half of train's (663k against 1.32M S1), so fewer names collide and the US gets slightly **easier**: re-weighting the holdout to test's name-group mix adds about +0.0004 to the US/India part [M].

**The decomposition** [E]. The simple weighted holdout gives 0.38274 × 0.9911 + 0.46751 × 0.9916 = 0.8429; re-weighting brings the US/India part to about 0.8433, so France ≈ (0.990879 − 0.8433)/0.14975 ≈ 0.985. Had France scored like US/India, the leaderboard would read about 0.9918. The gap of −0.0004 is therefore about +0.0004 from easier US/India test pools minus about 0.0009 from France sitting 0.006 below US/India. The whole argument rests on US/India scoring on test like the re-weighted holdout; the France-emptied probe would have tested that directly.

## 3. Variants

- **k-fold cross-validation** instead of one holdout: lower variance, k times the cost; **grouped** folds keep entities together (Roberts et al. 2017).
- **Nested CV** for honest estimates after tuning (Varma and Simon 2006; Cawley and Talbot 2010).
- **Leave-one-group-out**, here leave-one-country-out, for transfer to an unseen group.
- **Other paired tests**: McNemar's test on paired decisions, approximate randomisation; Dietterich (1998) compares them for classifiers.

## 4. Where we used it

[`splits.py`][splits], [`gates.py`][gates], [`metric.py`][metric], `ber/eval/evaluate.py`, the gate records in `docs/decisions/` (e.g. [G6][g6]) and the [submission records][subs]. The holdout design and `ber.eval` are Ameya's repo setup of 25 Sep; the gate discipline (paired bootstrap, ties to the simpler option) is Plan B's (Sachi) ([FINAL_PLAN §14][plan]).

## 5. Why it fits this problem

The test labels were hidden, one country was unlabelled, uploads were rationed, and late gains were tiny. A grouped, realistic holdout with a paired test handles US/India; designed probes and label-free invariants handle France; split-half confirmation and simpler-wins ties limit adaptive overfitting.

## 6. Pitfalls

- **Evaluating on an easier world**: ownership or blocking restricted to the evaluated subset.
- **Re-tuning on the holdout**: the flat threshold re-tuned under 2-fold CV lost −0.0000188 out of sample ([stacked rules][stack]).
- **Reading P(better) as a p-value**, or "not significant" as "no effect".
- **Trusting a model's forecast of itself**, or a diagnostic it has trained on.
- **Ignoring training noise** when effects are a few 10⁻⁵, and **chasing the public board** with near-identical uploads.

## 7. Jury questions with answers

**Q1. Why is your local score, 0.9913, above the leaderboard's 0.990879?**
The holdout cannot contain France, which has no labels. The leaderboard is a weighted sum of three countries; with US/India at their re-weighted holdout level, France comes out at about 0.985 against about 0.992 for US/India, which explains the gap. Early in the competition the same arithmetic put France near 0.93, and most of our later work went there.

**Q2. How do you know a 10⁻⁵ improvement is real?**
A paired bootstrap over 549,699 S1, positive on both holdout halves, and for tuned parameters repeated 2-fold CV. We also know its limits: hardware and seed changes move scores by 1.5–4 × 10⁻⁵, so a gain that small is a refinement we accept only when it is free and consistent.

**Q3. How did you avoid overfitting the public leaderboard?**
US/India decisions came from the holdout. Uploads were experiments with a written hypothesis and forecast, usually changing France alone. The one forecast that missed badly taught us that our French estimators were biased on decoys.

**Q4. How did you validate France without labels?**
Leaderboard arithmetic and France-only uploads, generator invariants (probability mass per record and per S1, counts, caps), the rule-population AUC, a size-bias test, and India as a stand-in unseen country. Each has a stated limit (§2.8).

**Q5. How did you prevent leakage in stacking and encodings?**
Three OOF groups by S1: every stage trains on scores from models that never saw those rows. Dictionaries, word odds and calibration were fitted without the holdout; French self-training was cross-fitted by S1 group, and Bakshi checked that the 7B's reject rate was the same on the third it never trained on.

**Q6. You made hundreds of decisions on one holdout. Isn't it overfit?**
Some optimism is certain, and we measured it where it mattered: the decision rule's in-sample +0.000048 became +0.0000237 out of sample, and the stage-3 prototype's +0.00011 became +0.00005. We confirmed on half B what we chose on half A, and refused a +0.000016 rule picked from about 160 variants.

**Q7. Will your public score carry to the private leaderboard?**
The split is random over shuffled S1, every slice has the same country mix, and with several hundred thousand S1 per part the level should carry within about 10⁻⁴ [E]. Rank order among teams separated by less than that is not guaranteed.

**Q8. Why one fixed holdout, not k-fold cross-validation?**
Compute and comparability. Each full pipeline run took hours, and a fixed holdout let three people and many agents compare every result on identical S1 with a paired test. We used repeated 2-fold CV where tuning made it necessary.

**Q9. What would you change in evaluation?**
Spend one upload early on the France-emptied probe, to measure US/India on test instead of assuming it; keep a second untouched holdout for the final choice; run seed repeats for the late, small decisions; and apply a multiple-testing correction to each day's comparisons.

## 8. Self-test

1. Why split by S1 rather than by pair? Give a concrete leak.
<details><summary>Answer</summary>With a pair split, (S1, R1) can be in training and (S1, R2) in validation; the model learns that S1's name rarity, rivals and typical copies, and validation flatters it. Splitting by S1 keeps an entity's evidence on one side, as on test.</details>

2. A change gives Δ = +0.00003 [−0.00001, +0.00007], P(better) 0.93. Keep it?
<details><summary>Answer</summary>Not under our rules: the interval includes 0, and ties go to the simpler option. Check both halves and, if it is a tuned parameter, cross-validate it.</details>

3. LB = 0.990879 and the US/India part is 0.8433. What is France?
<details><summary>Answer</summary>(0.990879 − 0.8433)/0.14975 ≈ 0.985.</details>

4. Why does pairing shrink the variance of the difference?
<details><summary>Answer</summary>Var(d̄) = [Var(F_new) + Var(F_base) − 2Cov]/n. The systems succeed and fail on mostly the same S1, so the covariance is large; most per-S1 differences are exactly zero.</details>

5. What would the France-emptied probe have scored if the US/India part were 0.8433?
<details><summary>Answer</summary>An empty France scores 1 on its singletons only (about 5.59% of French S1), so LB ≈ 0.8433 + 0.14975 × 0.0559 ≈ 0.8517. The difference from the real upload, divided by 0.14975, gives France directly.</details>

6. The best of 160 variants shows +0.000016 [+0.000002, +0.000030]. What do you do?
<details><summary>Answer</summary>Distrust it: under the winner's curse the best of 160 noisy estimates is biased upward, and an interval barely above zero is what chance alone often produces among 160 tries. Confirm on fresh data or a held-back half, correct for the number of tests, or drop it. We dropped it.</details>

7. Why can the rule-population AUC not rank self-trained French models?
<details><summary>Answer</summary>The rule populations are part of their pseudo-labels, so they are scored on data they learned from; the AUC saturates (0.984) and no longer measures French competence.</details>

## 9. Further reading

- Efron and Tibshirani (1993), "An Introduction to the Bootstrap", Chapman & Hall.
- Koehn (2004), "Statistical Significance Tests for Machine Translation Evaluation", EMNLP.
- Dietterich (1998), "Approximate Statistical Tests for Comparing Supervised Classification Learning Algorithms", Neural Computation.
- Wolpert (1992), "Stacked Generalization", Neural Networks.
- Kaufman, Rosset, Perlich and Stitelman (2012), "Leakage in Data Mining: Formulation, Detection, and Avoidance", ACM TKDD.
- Roberts et al. (2017), "Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure", Ecography.
- Cawley and Talbot (2010), "On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation", JMLR.
- Gelman and Loken (2013), "The garden of forking paths: Why multiple comparisons can be a problem, even when there is no 'fishing expedition' or 'p-hacking'", working paper.
- Holm (1979), "A Simple Sequentially Rejective Multiple Test Procedure", Scandinavian Journal of Statistics.
- Benjamini and Hochberg (1995), "Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing", JRSS B.
- Blum and Hardt (2015), "The Ladder: A Reliable Leaderboard for Machine Learning Competitions", ICML.
- Dwork et al. (2015), "The reusable holdout: Preserving validity in adaptive data analysis", Science.
- Bouthillier et al. (2021), "Accounting for Variance in Machine Learning Benchmarks", MLSys.

[contracts]: ../../docs/CONTRACTS.md
[splits]: ../../code/business_entity_resolution/src/ber/eval/splits.py
[gates]: ../../code/business_entity_resolution/src/ber/eval/gates.py
[metric]: ../../code/business_entity_resolution/src/ber/eval/metric.py
[g6]: ../../docs/decisions/2026-09-25_1731_gate-g6-dp-vs-threshold.md
[r5]: ../../experiments/ameya/model-v1/RESEARCH_v5.md
[r6]: ../../experiments/ameya/model-v1/RESEARCH_v6.md
[ops]: ../../docs/decisions/2026-09-26_0417_france-generator-ops-and-final-fit.md
[stack]: ../../docs/decisions/2026-09-27_0636_stacked-rules.md
[doc]: ../../experiments/ameya/final-zip/doc/Documentation_template.md
[plan]: ../../plans/FINAL_PLAN.md
[v4]: ../../docs/decisions/2026-09-26_0207_model-v4-france-and-cross-encoder.md
[task]: ../../student_resource/README.md
[subs]: ../../submissions/records/
[s03]: ../../submissions/records/2026-09-26_sub03.md
[changelog]: ../../CHANGELOG.md
