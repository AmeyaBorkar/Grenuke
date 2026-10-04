# F09. Experiments and evidence: how we knew a change helped

**Summary.**
- An experiment is a fair comparison: same data, same split, one change. This page is about keeping that comparison fair when the effects are tiny.
- Our late gains were 0.00002 to 0.0006 on a score of 0.991. That needed a fixed holdout split by business, paired comparisons, rules for noise and selection, and leaderboard uploads that changed one thing at a time.
- Every number we quote carries its scope (which evaluation) and its evidence level (measured, estimated, reported, uncertain). A number without both is not ready to be said aloud.

About 2.5 hours with the exercises. Prepares you for the advanced page [05 evaluation methodology][adv05] and for [F10][f10], [F11][f11] and [F12][f12].

---

## 1. What you need first

- [F01][f01]: what S1, S2/S3 records, candidates and the holdout are.
- [F02][f02]: mean, standard error, confidence interval, the bootstrap and multiple comparisons. This page applies them.
- [F04][f04]: precision, recall and F0.5.

One reminder of the metric. **Macro F0.5**: for each S1 we compare the predicted set with the true set, compute F0.5, then average over all S1. An S1 with no true match scores 1 for an empty prediction and 0 for any prediction.

Names we always use. **Local holdout**: the fixed 25% of labelled US/India S1 (549,699 S1) that we never trained on; it has no France. **Public LB**: the leaderboard during the challenge, scored on a subset of the test set. **Private LB**: the final ranking, scored on the rest of the test set. Never write a bare "F0.5 = ...".

Evidence levels. **M** measured (computed on labels, or scored by the leaderboard). **E** estimated (derived without labels, or inferred). **R** reported (stated in a team document and not re-checked by the author of this page). **U** uncertain. "Toy" marks numbers invented for practice.

---

## 2. The concepts from zero

### 2.1 Signal and noise

**Intuition.** When you compare two systems you never see the true difference. You see the true difference plus noise. Noise has three sources. Sampling: the evaluation set holds some businesses, not all of them. Training: seeds, hardware and data order change a model a little every time it is built. Selection: if you try many changes and keep the best, the kept one looks better than it is.

**Definition.**

```
observed difference = true effect + sampling noise + training noise + selection bias
```

Each tool in this page shrinks one of the last three terms or measures it.

**Worked example.** On 27 Sep Bakshi rebuilt an earlier model on other hardware (the "g0 reproduction gate"). The local holdout F0.5 moved from 0.991246 to 0.991261 [M], a change of +0.000015 with the same code and data ([methodology doc][doc], Appendix A). The gains we accepted that day were of the same order: the 7B drop rule +0.000037, the decision layer +0.000048, the 7B counted twice for India +0.000066 [M]. A plain rebuild moved the score by a quarter to two-fifths of the effects we were measuring, so none of the tools below is optional.

### 2.2 Baselines

**Intuition.** A baseline is the simplest complete system you can run end to end. It proves that the whole path works, gives you a floor, and shows how much room is left. A result without a baseline is a number with nothing to compare to.

**Definition.** A baseline is a simple method evaluated on the same split with the same metric as the final system, and cheap enough that you really run it.

**Worked example.** Ameya's first end-to-end baseline (25 Sep, blocking v0 and a first matcher) scored 0.9683 on the local holdout [M] ([handover 25 Sep 17:06][h-v0]). The final US/India matcher g1w scored 0.991323 [M] ([handover 27 Sep 20:14][h-final]). In score that is +0.0230. In error (1 minus the score) it is 0.0317 down to 0.0087, so we removed about 73% of the error that v0 left [E, arithmetic]. Near the top of a metric the error view is fairer: 0.990 to 0.991 looks like nothing, yet it cuts the error by 10%.

### 2.3 Ablations and one change at a time

**Intuition.** An **ablation** takes one part away (or adds one part), keeps everything else fixed, and measures the change. If two things change at once you cannot say which one did the work.

**Definition.** For a component C, effect(C) = score(with C) minus score(without C), on the same data, split and metric, ideally with the same seeds. A clean study changes one component per run.

**Worked example (clean).** Adding the legal-form features (SARL, LLC, Pvt Ltd and so on) to stage 2 gave +0.00271 [0.00260, 0.00283] on the full local holdout [M] ([decision][d-legal]). The only difference between the two runs was those features.

**Worked example (bundled).** Model v2 added three things at once: look-alike word odds (gate G3), cluster support (G9) and blocking v1. Together they gave +0.00431 [0.00418, 0.00445] over v1 [M] ([handover 25 Sep 19:58][h-v1]). We adopted the bundle. We cannot say what each part contributed, and the records do not explain why it was bundled (time pressure is the likely reason, U). **Hindsight:** three more runs would have given a three-row table. Our methodology document has no ablation table either; it has a leaderboard step figure (see [F12][f12]) and a "measured and dropped" list.

**Table 1. A ledger of measured changes** (local holdout, paired bootstrap, 95% interval; every row is [M]).

| change | gain in macro F0.5 | note | record |
|---|---|---|---|
| legal-form features | +0.00271 [0.00260, 0.00283] | clean ablation | [decision][d-legal] |
| blocking v3 repairs | +0.00063 [0.00057, 0.00070] | recall 0.98992 to 0.99135 | [decision][d-v6all] |
| e5-small cross-encoder on the uncertain band (G10) | +0.00140 [0.00131, 0.00148] | below the +0.003 bar, kept for France | [decision][d-v4] |
| three cross-encoder logits (v7ce3) | +0.000311 [0.000258, 0.000362] | | [decision][d-v7ce3] |
| stage 3 (joint re-scoring) | +0.000055 [0.000025, 0.000085] | on v6all | [decision][d-s3] |
| decision layer (expected F0.5 per S1 plus shifts) | +0.0000481 [0.0000071, 0.0000912] | on v7s | [decision][d-stack] |
| 7B counted twice in the mix: India / US | +0.0000661, P 0.998 / +0.0000262, P 0.906 | the US is not significant | [handover][h-final] |

Measured and dropped (also [M]): two tighter candidate cuts, −0.000106 and −0.000041; stage-2 seed bagging, −0.00004; a learned blend of the cross-encoder scores as the decision score, about 0.001 lower ([methodology doc][doc], Appendix B; [handover 26 Sep 20:49][h-sq]).

The rows do not add up to the total gain from v0. Each was measured on a different base model, some on the dev sample, and some overlap.

### 2.4 A fixed holdout split by entity

**Intuition.** The holdout plays the part of the unseen test set. The unit you split by must be the unit you want to generalise to. We want to generalise to new businesses, so we split by business (S1), not by pair and not by record.

**Definition.** `fold(eid) = splitmix64(eid) mod 20`. The local holdout is folds 0 to 4: 549,699 S1 (US 329,717; India 219,982), 25% of train [M]. Training uses folds 5 to 19, split into three out-of-fold groups (5 to 9, 10 to 14, 15 to 19) ([05 section 2.1][adv05]). The hash is deterministic, so every machine and every teammate gets the same split without a shared file. Everything about an S1 stays on one side: its candidate pairs, its true records and its rivals' scores.

**Worked example (the leak).** Split pairs at random and the S1 "X Ltd" has three true records. Two land in training and one in validation. The model learns X Ltd's name, its rare words and its address from two copies, and then finds the third copy easy. Validation flatters the model. Split by S1 and all of X Ltd's evidence sits on one side, as it does in the real test.

The holdout was kept realistic: blocking and ownership ran over the full record pool, because an early run that let holdout records compete only among holdout S1 made ownership too easy ([decision][d-g6]). Nothing supervised was fitted on it (dictionaries, word odds, calibration, weights). Tuning one or two scalars on it, such as a threshold or a shift, was allowed as a small known optimism. We measured that optimism for the decision layer: +48.1e-6 in sample became +23.7e-6 out of sample under repeated 2-fold cross-validation (42 splits, positive in 86%), while a flat threshold re-tuned the same way lost 18.8e-6 [M] ([decision][d-stack]).

For quick runs we used a dev sample of 27,651 S1 (R). Adoption gates used the full holdout.

### 2.5 Gates

**Intuition.** A **gate** is a rule written before the run: "this change enters the pipeline only if ...". Writing it first stops us moving the goalposts after we see a number.

**Definition.** The plan's gates asked for a gain of at least +0.002 for a component and +0.003 for a heavy one, with the 95% interval above zero. In practice, for the late changes, the working rule was: the interval is above zero, the change is positive on both holdout halves (called A and B), and a tie goes to the simpler option. Overriding a bar needs a written reason in `docs/decisions/` (contract C10). A gate is re-run when the base model changes.

**Worked example (an override).** The first cross-encoder gained +0.00140 against a +0.003 bar [M]. We kept it for France, because it halved the number of French look-alikes the model accepted, and we wrote that down ([decision][d-v4]).

**Worked example (a gate that flipped).** Gate G6 compared the expected-F0.5 selection with one tuned threshold. On stage-1 probabilities the selection lost (−0.00029). On stage-2 probabilities it won (+0.00027). On the last models the gain had shrunk to +0.00003 to +0.00005 [M] ([decision][d-g6], [04 section 2.8][adv04]). The same question gave different answers on different models, so the gate was re-run on each one. [F11][f11] explains why.

**Worked example (a half-split).** The 7B drop rule gained +33e-6 on a 34% labelled sample, with +22e-6 on one half and +43e-6 on the other. On the whole holdout it gained +37e-6, with +33e-6 and +41e-6 on the halves [M] ([handover 27 Sep 20:06][h-push]).

**Why the bar had to move.** The +0.002 bar was 6% of v0's error (0.0317) but 23% of the final error (0.0087) [E, arithmetic]. At the end no single change could reach it. Our own note says it plainly: at 0.99 the useful gains were much smaller than the bar.

### 2.6 Paired comparisons and the paired bootstrap

**Intuition.** Two good models get nearly every S1 exactly right, and they get the same ones right. If you look at the difference S1 by S1, all the shared easy cases cancel and only the S1 where the models disagree remain. That is a **paired** comparison, and it is far less noisy than comparing two averages.

**Definition.**

```
d_s    = F_new(s) - F_base(s)          for each S1 s
Delta  = mean of d_s over all S1
Var(Delta) = [ Var(F_new) + Var(F_base) - 2 Cov(F_new, F_base) ] / n
```

The covariance is large when the models succeed and fail on the same S1, so the variance of the difference is small. The **bootstrap** then measures how much Delta would move if we had drawn a different set of S1:

1. Resample the n S1 with replacement to make a new set of the same size, and compute its mean d.
2. Repeat B times.
3. The 95% interval is the 2.5th and 97.5th percentiles of those means.
4. **P(better)** is the share of resamples whose mean d is above 0.

In `ber.eval.gates` each S1 gets a Poisson(1) weight in each resample, which is equivalent at this size, and B is 1,000 [R] ([05 section 2.4][adv05]).

**Worked example (toy, so you can run it).** Twelve S1. The new model changes three of them: +0.3, −0.1 and +0.2. The rest are 0.

```python
import numpy as np
d = np.array([0, 0, 0, 0, 0, 0, 0.3, 0, -0.1, 0, 0.2, 0])   # F_new - F_base per S1 (toy)
rng = np.random.default_rng(7)
boot = np.array([rng.choice(d, size=len(d), replace=True).mean() for _ in range(10_000)])
print(d.mean(), np.percentile(boot, [2.5, 97.5]), (boot > 0).mean())
# 0.0333  [-0.0167  0.1]  0.83
```

Delta is +0.0333, but the interval runs from −0.0167 to +0.1 and P(better) is 0.83. With twelve S1, two wins cannot beat chance. Repeat the same pattern over 1,200 S1 and the standard error shrinks by a factor of 10, so the same Delta would sit about 11 standard errors above zero. Sample size is what makes tiny gains measurable.

**Worked example (our numbers).** The decision layer gave +48.1e-6 with interval [7.1, 91.2] and P(better) 0.987 [M] ([decision][d-stack]). Read it backwards:

```
standard error  = (91.2 - 7.1) / (2 x 1.96)       = 21.5e-6
z               = 48.1 / 21.5                      = 2.24
normal cdf(2.24)                                   = 0.988   (recorded: 0.987)
per-S1 spread of d = 21.5e-6 x sqrt(549,699)       = 0.016   [E]
```

So P(better) is the bootstrap's way of reporting a z-score. The spread of 0.016 says that most d are exactly 0 and a few S1 move by a lot. Had we compared the two models' averages without pairing, the standard error would be about sqrt(2) x SD(F) / sqrt(n). A per-S1 SD of F between 0.07 and 0.093 (0.093 is the maximum possible at a mean of 0.9913) gives 1.3e-4 to 1.8e-4 [E]. That is 6 to 8 times larger and would hide a gain of 48e-6.

**What the bootstrap does not cover.** Training randomness (a rebuild moved a score by +0.000015; stage 3 is not bit-reproducible across machines, with about 500 test decisions differing [M]), the shift from the holdout to the test including France, and reuse of the same holdout for hundreds of questions (section 2.8).

### 2.7 Significance versus effect size

**Intuition.** "Significant" says an effect is probably not zero. "Large" says it matters. They are different questions, and with 549,699 S1 you can get a significant answer to a question nobody cares about.

**Definition.** Effect size is Delta in the metric's units, or as a share of the remaining error. Significance is how many standard errors Delta sits from zero, or P(better).

**Worked example (what a number is worth).** One S1 flipping from wrong to right adds 1/549,699 = 1.8e-6 to the holdout score. So +1e-5 is about 5.5 S1 on the holdout and 17 S1 on the full test (1,732,544 S1) [E, arithmetic]. The decision layer's +48.1e-6 is about 26 S1 on the holdout and 83 on the test. It is real, and it is small.

**Worked example (the smallest effect we could see).** The standard errors of our gates were about 13e-6 to 27e-6, and an interval excludes zero only when Delta exceeds about 1.96 times that, so effects below roughly 25e-6 to 50e-6 could rarely be confirmed one at a time [E]. Training noise adds 1.5 to 4e-5 ([05][adv05]). Below about 4e-5 we were refining, not proving, which is why ties went to the simpler option.

Note that "not significant" is not "zero": the US effect of the 7B counted twice had P(better) 0.906 and was later seen at +14e-6 on the leaderboard ([LB 27 Sep #06][lb-06]).

### 2.8 Many comparisons and the winner's curse

**Intuition.** Try 20 changes that do nothing and one of them will look good at the 5% level. Keep that one and you have kept noise. This is the **winner's curse**: the best of many noisy estimates is biased upward.

**Definition.** If each of m independent tests has false-positive rate alpha, the chance of at least one false positive is 1 − (1 − alpha)^m. **Bonferroni** keeps that chance at alpha by testing each comparison at alpha / m.

```
m =  1   ->  5%        m = 13  ->  49%
m =  5   ->  23%       m = 20  ->  64%
m = 10   ->  40%       m = 40  ->  87%
```

**Worked example (our counts).** We had 13 numbered gates (G1 to G13), about 40 more packages that were built and validated but never uploaded, and 13 uploads with a recorded public score. We did not apply a formal correction, and our evaluation page says we could have (Holm or Benjamini and Hochberg, a second untouched holdout) ([05 section 2.6][adv05]). Here is what one would have done to the decision layer, as a what-if [E]. With m = 13 the critical z is 2.89, so the half-width becomes 62e-6 and the interval becomes [−13.9, +110.1]e-6. It would no longer exclude zero.

**What protected us instead.** Ties go to the simpler option, both halves must agree, tuned parameters are cross-validated, and the leaderboard is an outside check. The curse was real [M]: the stage-3 prototype, the best of three variants, gained +0.00011 and gained only +0.00005 once rebuilt as a pipeline step; an India-only count prior scored +0.000016 but was picked from about 160 variants and lowered the US, so we did not use it.

### 2.9 Public and private leaderboards

**Intuition.** The public leaderboard is a second test set. It is also small, shared by every team, and queried again and again. Each upload tells you a little about the labels behind it, and choosing the best of many uploads fits those labels a little.

**Definition.** The public board scores a subset of the test S1. The private board, which decides the ranking, scores the disjoint rest. Our test S1 file is shuffled, so any slice has the same country mix: about 15% France, 47% India, 38% US [M] ([05 section 2.7][adv05]). Choosing among many uploads by public score overfits the public subset (Blum and Hardt, 2015). With large test sets the effect is often small.

**What we did.** US and India decisions came from the labelled holdout. The leaderboard was used mainly for France, where nothing else could measure. Each upload had a written hypothesis and a predicted score ([records][lb-04]), and most uploads changed one thing (section 2.10).

**Forecasts against results** [M] ([05][adv05]): v7n was forecast at 0.9894 to 0.9900 and scored 0.989721; the 7B parts of Composite B were forecast at +0.000149 and measured +0.000180; the round-3 French upload was forecast at +0.000069 and measured −0.000046. That miss taught us that estimators built on a model's own probabilities are biased on decoys ([F10][f10]).

**The private result.** The organisers publish rankings only. Our final private rank is 2nd of the Top 10 [R]. There is no private score to quote, and you must not infer one from the public score. **Hindsight:** our public rank at upload went from 7 (0.990545) to 12 (0.990699) to 16 (0.990879) as our score rose (the changelog records the rank at upload only). Other teams were improving faster. Public rank measures the crowd at that hour, not our private result. Whether the public board misled anyone is unknowable from our data (U).

### 2.10 Control uploads

**Intuition.** An upload that changes one thing is an experiment. An upload that changes five is a lottery ticket. Because the score of a fixed file is exact, two uploads that differ in one component give that component's effect on the public subset, with no training noise at all.

**Definition.** A control is an upload identical to an earlier one except for one component. Its score difference is the effect of that component on the public subset. We often changed France alone and kept the US and India lines of the file identical.

**Worked example.** Table 2 shows how one control split a jump we would otherwise have credited to a new model.

**Table 2. Control uploads** (public LB, all [M]; [CHANGELOG][changelog]).

| upload | what differs from the one above it | public LB | difference |
|---|---|---|---|
| v7nst (26 Sep #04) | baseline: French self-training round 1 | 0.990179 | |
| v7nst-dpc (27 Sep #01) | adds the stacked decision layer only | 0.990264 | +0.000085 (the rules) |
| v7sq-dpc (27 Sep #02) | new models in the mix (Qwen2.5-1.5B, self-trained e5-large) and round-2 French labels | 0.990545 | +0.000281 (the model) |
| mixf7 (27 Sep #05) | Composite B (0.990879, team best) with the round-3 French model | 0.990833 | −0.000046 vs B |
| B7 (27 Sep #07) | B plus extra French 7B drops where Qwen3-4B agrees | 0.990875 | −0.000004 vs B: a tie |

From v7nst to v7sq-dpc the score rose by 0.000366. The control shows 0.000085 of it came from rules and 0.000281 from the model. Without v7nst-dpc we would have credited all 0.000366 to the model.

### 2.11 Evidence levels

**Intuition.** A number without its source is a rumour. We tag every number with how we know it, so a reader can tell a score from a guess.

**Definition.**

| level | meaning | example from our project |
|---|---|---|
| M measured | computed on labels, or scored by the leaderboard | public LB 0.990879; local holdout 0.9913 |
| E estimated | derived without labels, or inferred | France about 0.985, backed out of the leaderboard formula |
| R reported | stated in a document or chat and not re-checked | "the 7B model trained in about 2 hours on three H100s" |
| U uncertain | sources conflict, or it is unverified | why the private rank differs from the public rank at upload |

**Worked example (scope).** The same digits can describe different objects. 99.1% is the recall of the 58.4M retrieved pairs on the holdout [M]. The final 6,410,308-pair candidate file has about 98.2% to 98.4% [M]. Quoting 99.1% for the cut file is the commonest slip; the scope must travel with the number.

### 2.12 Reproducibility

**Intuition.** If others cannot rerun your work and land near your number, they cannot trust it. Computers do not always repeat themselves.

**Definition.** Reproducible means the same code, data, seeds and environment give the same output. In practice, floating-point addition is not associative, and GPUs add numbers in orders that vary between runs and between cards:

```python
(0.1 + 0.2) + 0.3     # 0.6000000000000001
0.1 + (0.2 + 0.3)     # 0.6
```

A training run is millions of such sums, so tiny differences compound.

**What we did.** Seeds fixed; every artifact records its command and git commit; versions pinned in `requirements.txt`; a hash-gated, self-verifying ZIP builder by Bakshi; and the `output/` folder holds the exact bytes we submitted ([methodology doc][doc], Appendix A). The g0 gate rebuilt a model on other hardware: 0.991261 against 0.991246 [M]. We tell readers that a rerun should land within about 0.0001 [R].

---

## 3. How it shows up in our project

| practice | where we used it | where to read more |
|---|---|---|
| baseline first | v0 at 0.9683, then 15 rows in the upload register (13 with a recorded public score) | [CHANGELOG][changelog] |
| fixed holdout split by S1 | `ber.eval.splits`, 549,699 S1, three out-of-fold groups | [05][adv05] |
| gates and decision records | 16 records in `docs/decisions/`, from G1 to the stacked rules | [decisions README][dec-readme] |
| control uploads | France-only compositions, the dpc split, mixf7 and B7 | [F12][f12], [LB records][lb-04] |

**Hindsight, from our own evaluation page.** We would add an early France-emptied upload to measure US/India on the test, a second untouched holdout for the final choice, seed repeats for the small late decisions, and a multiple-testing correction for each day's comparisons ([05, question 9][adv05]).

---

## 4. How to read the numbers

| you see | read it as | it does not tell you |
|---|---|---|
| +48.1e-6 | +0.0000481 on the local holdout; about 26 S1 | that it will carry to the test unchanged |
| [7.1, 91.2] and P(better) 0.987 | sampling noise alone puts the true gain plausibly in that range; 98.7% of resamples favoured the new model | training randomness, reuse of the holdout, or the chance that the model is truly better |
| 0.9913 local, 0.990879 public | two different sets of S1 and two different country mixes; do not subtract them without the reasons in [F12][f12] | which of the two is "right" |

Units: 1e-6 = 0.000001. On the public LB a change in one country moves the score by its weight times the country's change: US 0.38274, India 0.46751, France 0.14975. Sampling noise of an average over several hundred thousand S1 is at most about 1.3e-4 [E] (contract C2 quotes a more cautious plus or minus 0.001 [R]); differences between paired systems are far less noisy.

---

## 5. Common misconceptions

1. **"A higher number means a better model."** Only if the gap exceeds the noise. A rebuild alone moved our score by +0.000015.
2. **"Not significant means no effect."** It means we could not rule out zero. The US effect of the 7B had P = 0.906 and was later seen at +14e-6 on the leaderboard.
3. **"P(better) 0.998 means a 99.8% chance the model is better."** It is the share of bootstrap resamples with a positive mean. It is not a posterior probability.
4. **"A narrow interval means the result will replicate on the test."** The interval covers which S1 were drawn. It does not cover training noise, reuse of the holdout, or the shift to France.
5. **"The public leaderboard is the truth."** It is a subset of the test, shared with every team, and rank at upload moves with other teams.
6. **"An ablation drop equals importance."** Two redundant components each show a small drop when removed alone.
7. **"One change at a time is always possible."** Sometimes you bundle to save time. Then say that you bundled, and do not claim to know the parts.
8. **"A fixed seed makes a GPU run identical."** Not across machines, and often not on one machine.

---

## 6. Check yourself

**1.** A record says "+48.1e-6 [+7.1, +91.2], P 0.987". Write the gain as a decimal, estimate the standard error, and say how many S1 the gain is worth on the holdout.

<details><summary>Answer</summary>

+0.0000481. Standard error = (91.2 − 7.1) / 3.92 = 21.5e-6. On the holdout 0.0000481 × 549,699 = 26.4, so about 26 S1 flipping from wrong to right. z = 2.24 and the normal cdf at 2.24 is 0.988, which matches the recorded 0.987 within rounding.

</details>

**2.** v7nst scored 0.990179. v7nst-dpc scored 0.990264. v7sq-dpc scored 0.990545. Split the jump from v7nst to v7sq-dpc between rules and model, and say what would have gone wrong without the middle upload.

<details><summary>Answer</summary>

Rules: 0.990264 − 0.990179 = +0.000085. Model: 0.990545 − 0.990264 = +0.000281. Total: +0.000366. Without v7nst-dpc we would have credited all 0.000366 to the new models and overrated them by about 30%.

</details>

**3.** Apply a Bonferroni correction for 13 comparisons to the decision layer (+48.1e-6, standard error 21.5e-6). Is it still significant? Why did we adopt it anyway?

<details><summary>Answer</summary>

alpha / m = 0.05 / 13 = 0.00385, so the two-sided critical z is 2.89. Half-width = 2.89 × 21.5e-6 = 62e-6, interval [−13.9, +110.1]e-6. It includes zero, so it would not be significant. We adopted it because the comparison had a stated reason (the structure of the metric), its parameters were chosen on one half and confirmed on the other, repeated 2-fold cross-validation stayed positive (+23.7e-6 out of sample), and the leaderboard confirmed the stack (+85e-6 for the dpc upload). The correction is a what-if; we did not apply one.

</details>

**4.** Run the toy bootstrap with 12 S1 (section 2.6). Why does the interval include zero? What happens to the standard error if the same pattern holds on 1,200 S1?

<details><summary>Answer</summary>

Delta = (0.3 − 0.1 + 0.2) / 12 = +0.0333. Only three S1 differ and one of them is a loss, so resamples often drop the wins or double the loss, and many have a mean at or below 0 (P(better) = 0.83). With 1,200 S1 the standard error falls by a factor of sqrt(100) = 10, from about 0.031 to 0.0031, so z rises from about 1.1 to about 11.

</details>

**5.** Design a control upload to test whether one French rule helps. What stays fixed, what changes, and what would you conclude from a change of −3e-6?

<details><summary>Answer</summary>

Keep the US and India lines byte-identical, keep the French candidate pairs and every French probability identical, and change only the rule. The score difference is then the rule's effect on the public subset. A change of −3e-6 is far below the rule of thumb for noise (about 5e-5 between near-identical candidates), so it is a tie, and ties go to the simpler option: leave the rule out unless it was free.

</details>

**6.** Give the evidence level of each statement: (a) public LB 0.990879; (b) France about 0.985; (c) the 7B trained for about 2 hours on three H100s; (d) "the candidate file holds 99.1% of the true pairs".

<details><summary>Answer</summary>

(a) M, scored by the leaderboard. (b) E, backed out of the leaderboard formula under an assumption about US/India on the test. (c) R, stated in the methodology document and not re-timed here. (d) wrong scope: 99.1% is [M] for the 58.4M retrieved pairs; the 6.41M-pair file has about 98.2% to 98.4% [M]. Always write the scope.

</details>

**7.** Composite B was rank 16 on the public board at upload; our final private rank is 2nd of the Top 10. A colleague says the public board misled us. What do you answer?

<details><summary>Answer</summary>

Public rank at upload depends on what other teams had uploaded by then, so it went from 7 to 16 even as our score rose. Our US/India decisions came from the labelled holdout, and the public board served as a measuring instrument for France through controlled uploads. We have no private score and cannot explain every move in rank (U). Say that rank is relative and that the organisers publish ranks only.

</details>

**8.** Which of these splits leak? (a) random pairs; (b) a hash of the S1 id; (c) random records; (d) word odds counted using holdout labels; (e) IDF computed on train and test text.

<details><summary>Answer</summary>

(a) leaks: one S1 appears on both sides. (b) is correct. (c) leaks for the same reason as (a). (d) leaks: the holdout's answers shape its own features. (e) does not leak, because IDF uses no labels; per-country IDF fitted on train plus test is allowed.

</details>

---

## 7. Going deeper

- [05 evaluation methodology][adv05]: the holdout, leakage traps, the paired bootstrap, multiple comparisons, leaderboards, label-free diagnostics and the holdout-versus-leaderboard gap.
- [04 metrics and decisions][adv04] for the gates on the decision layer; [07 calibration][adv07] for why a P(better) is not a probability of truth.
- Efron and Tibshirani (1993), "An Introduction to the Bootstrap", Chapman & Hall.
- Koehn (2004), "Statistical Significance Tests for Machine Translation Evaluation", EMNLP. The paired bootstrap for comparing systems.
- Blum and Hardt (2015), "The Ladder: A Reliable Leaderboard for Machine Learning Competitions", ICML; Dwork et al. (2015), "The reusable holdout: Preserving validity in adaptive data analysis", Science.
- Gelman and Loken (2013), "The garden of forking paths", working paper; Holm (1979) and Benjamini and Hochberg (1995) on multiple testing.
- Bouthillier et al. (2021), "Accounting for Variance in Machine Learning Benchmarks", MLSys.

## 8. Where next

- [F10 Semi-supervised learning and domain shift][f10]: experiments when you have no labels at all, and the forecast that missed.
- [F11 Decision theory and optimisation][f11]: the decision layer whose gain we measured here.
- [F12 Interpreting our results][f12]: every key number of the project, with the sentence to say aloud.
- The track map: [foundations README](README.md).

[doc]: ../../../experiments/ameya/final-zip/doc/Documentation_template.md
[changelog]: ../../../CHANGELOG.md
[adv04]: ../04-metrics-and-decisions.md
[adv05]: ../05-evaluation-methodology.md
[adv07]: ../07-calibration.md
[f01]: F01-data-and-problem.md
[f02]: F02-probability-and-statistics.md
[f04]: F04-classification-metrics.md
[f10]: F10-semi-supervised-and-domain-shift.md
[f11]: F11-decision-theory-and-optimisation.md
[f12]: F12-interpreting-our-results.md
[dec-readme]: ../../../docs/decisions/README.md
[d-g6]: ../../../docs/decisions/2026-09-25_1731_gate-g6-dp-vs-threshold.md
[d-legal]: ../../../docs/decisions/2026-09-25_2142_gate-legal-form-features.md
[d-v4]: ../../../docs/decisions/2026-09-26_0207_model-v4-france-and-cross-encoder.md
[d-v6all]: ../../../docs/decisions/2026-09-26_1425_model-v6all-final.md
[d-s3]: ../../../docs/decisions/2026-09-26_1557_rules-v3-and-stage3.md
[d-v7ce3]: ../../../docs/decisions/2026-09-26_1933_model-v7ce3.md
[d-stack]: ../../../docs/decisions/2026-09-27_0636_stacked-rules.md
[h-v0]: ../../../docs/handover/2026-09-25_1706_ameya_block-v0-baseline.md
[h-v1]: ../../../docs/handover/2026-09-25_1958_ameya_model-v1.md
[h-sq]: ../../../docs/handover/2026-09-26_2049_ameya_squeeze-v7n.md
[h-push]: ../../../docs/handover/2026-09-27_2006_bakshi_final-push.md
[h-final]: ../../../docs/handover/2026-09-27_2014_ameya_final-upload.md
[lb-04]: ../../../submissions/records/2026-09-27_sub04.md
[lb-06]: ../../../submissions/records/2026-09-27_sub06.md
