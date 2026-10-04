# F12. Interpreting our results: a guided tour of every key number

**Summary.**
- Our public leaderboard score is 0.990879 (Composite B) and our local holdout score is 0.9913. They are different measurements. The gap of about 0.0004 comes mostly from France, which the holdout cannot contain, and from easier US/India test pools. Our final private rank is 2nd of the Top 10; the organisers publish ranks only, so there is no private score to quote.
- This page walks through the numbers one by one: per-country scores, the leaderboard staircase and the cause of each step, the implied France level, the candidate funnel, the band AUCs, the bootstrap intervals, the 7B re-check, and precision and recall. For each it says what the number is, how it was obtained and what it does not tell you.
- It closes with the ten numbers every member must say correctly, each with the sentence to say aloud.

About 3 hours with the exercises. Read it after [F09][f09], [F10][f10] and [F11][f11]. It prepares you for the jury questions in [05 evaluation methodology][adv05], [09][adv09] and [10][adv10].

---

## 1. What you need first

- [F09][f09]: evidence levels, the paired bootstrap, control uploads.
- [F04][f04]: precision, recall, F0.5, AUC. [F01][f01]: S1, S2/S3, candidates.
- Evidence levels: **M** measured (computed on labels, or scored by the leaderboard), **E** estimated (derived without labels, or inferred), **R** reported (stated in a team document and not re-checked here), **U** uncertain.
- The three names we always use: **local holdout** (the fixed 25% of labelled US/India S1, 549,699 S1, no France), **public LB** (the leaderboard during the challenge, on a subset of the test set), **private LB** (the final ranking, on the rest). Never write a bare "F0.5 = ...".

---

## 2. The tour

### 2.1 The scoreboard

| number | what it is (scope) | level | source |
|---|---|---|---|
| 0.990879 | Composite B, public LB, macro F0.5 | M | [LB 27 Sep #04][lb-27-04] |
| 0.9913 | same pipeline, local holdout, US and India (g1w: 0.991323) | M | [methodology doc][doc], [CHANGELOG][changelog] |
| US 0.9911, India 0.9916 | local holdout by country | M | [methodology doc][doc] |
| precision 99.9%, recall 97.5% | local holdout | M | [methodology doc][doc] |
| 2nd of the Top 10 | private ranking, rank only | R | organisers |
| France about 0.985 | implied by the LB formula, never measured | E | section 2.6 |
| 58.4M pairs, 99.1% | retrieval on the test; recall of true holdout pairs | M | [methodology doc][doc] |
| 6,410,308 pairs, 3.70 per S1, about 98.2% to 98.4% | the candidate file; recall of true holdout pairs | M | section 2.7 |
| 840 French and 310 US/India drops | the 7B re-check on the test | M | [10][adv10] |

### 2.2 The local holdout against the public LB

**What each one is.** The local holdout is 549,699 labelled US and India S1 that we never trained on. It has no France. The public LB scores a subset of the test. The test, and any slice of it, is 38% US, 47% India and 15% France [M]. The public score is a weighted average of the three country scores:

```
LB = 0.38274 x F_US + 0.46751 x F_India + 0.14975 x F_France
```

The weights sum to 1 and are the country shares of the scored S1 (the test file is shuffled, so any slice has the same mix).

**The gap.** 0.9913 − 0.990879 = 0.0004 (0.00044 against the unrounded g1w value 0.991323). Three things explain it [E]:

| piece | effect on LB | why |
|---|---|---|
| the holdout has no France | about −0.0009 | France scores about 0.006 below US/India |
| US/India test pools are easier | about +0.0004 | the US test pool is half the size of the train pool (663k against 1.32M S1), so fewer names collide; re-weighting the holdout to the test's name-group mix adds about 0.0004 [M] |
| rounding and sampling | the remainder | per-S1 noise of the average is at most about 1.3e-4 [E] |

**One equation, two unknowns.** The LB is one number. The US/India test level and the France level are both unknown. If you assume US/India score on the test as on the holdout, France comes out at 0.988. If you assume the re-weighted level (US/India part 0.8433), France comes out at 0.985. Bakshi showed that for an earlier upload (v7sq-dpc, public LB 0.990545) the assumption only bounds France to 0.9813 to 0.9898 [E]. That is why we say France is never measured.

**The early gap.** On 25 Sep the gap was large: v2 had 0.98436 on the holdout and 0.97608 on the public LB (gap 0.0083); v3 had 0.98882 and 0.97961 (gap 0.0092). The same arithmetic put France at about 0.93 [E] (0.925 to 0.931). The model's own forecast for France had been 0.970 [M], 0.04 too high ([05][adv05]). Most of our later work went into closing that gap.

### 2.3 The private leaderboard and public ranks

The organisers publish rankings only. Our final private rank is 2nd of the Top 10 [R]. Say that and nothing more. Do not compute, estimate or guess a private score, and do not say that the public score "is" the private score.

The changelog records our public rank at upload, not at the end: 15 (0.98781), 8 (0.989721), 7 (0.990179), 7 (0.990545), 12 (0.990699), 16 (0.990879) [M]. Rank at upload moves with other teams' progress. Our score only rose, and our rank at upload fell from 7 to 16, so the crowd was improving faster than we were. It is not a measurement of the private result. Why the private ranking is kinder than the public rank at upload is not something our data can explain (U).

### 2.4 Per-country holdout scores

US 0.9911 and India 0.9916 on the local holdout [M]. The holdout is 60% US (329,717 S1) and 40% India (219,982 S1), so 0.6 × 0.9911 + 0.4 × 0.9916 = 0.9913. The test's US/India mix is 45% to 55% (0.38274 and 0.46751 out of 0.85025), so a test-weighted US/India level from the same two numbers is 0.99137, about 0.00007 higher. France has no entry, because no French pair has a label.

### 2.5 The leaderboard staircase and the cause of each step

The staircase below shows the public score after each upload. One # is 0.00033 above 0.975.

```
v2           0.97608  ###
v3           0.97961  ##############
26 Sep #01   0.98781  ######################################
26 Sep #02   0.98861  #########################################
26 Sep #03   0.98972  ############################################
26 Sep #04   0.99018  ##############################################
27 Sep #01   0.99026  ##############################################
27 Sep #02   0.99055  ###############################################
27 Sep #03   0.99070  ###############################################
27 Sep #04   0.99088  ################################################   Composite B
```

From v2 to Composite B the score rose by 0.014799. That removed 62% of v2's remaining error (0.02392 to 0.00912) [E]. 79% of the rise came in the two steps after v2. After that every step is small, which is the shape of a score near its ceiling.

**Table 1. The cause of each step** (public LB [M]; "France part" is the step minus 0.85025 times the US/India holdout change [E]; records: [CHANGELOG][changelog]).

| upload | public LB | step | what changed | France part of the step |
|---|---|---|---|---|
| v2 (25 Sep) | 0.97608 | | look-alike word odds, cluster support, blocking v1 (holdout 0.98436) | |
| v3 (25 Sep) | 0.97961 | +0.00353 | legal-form features, blocking v2, key fix (holdout 0.98882) | −0.00026: France did not gain |
| 26 Sep #01 | 0.98781 | +0.00820 | the French work since v3: proxy odds, French legal-form bitmask drop, e5-small cross-encoder, French normalisation, France rules v2, candidates cut to 3.70 per S1 | +0.00706 (86% of the step) |
| 26 Sep #02 | 0.988609 | +0.000799 | blocking v3 repairs (+0.00063 on the holdout), stage 3, rules v3, acronym join | +0.00022 |
| 26 Sep #03 | 0.989721 | +0.001112 | stronger cross-encoders: e5-small plus a mean of two e5-large (v7n) | +0.00080 |
| 26 Sep #04 | 0.990179 | +0.000458 | French self-training, round 1 (v7nst) | +0.00047 |
| 27 Sep #01 | 0.990264 | +0.000085 | the stacked decision layer only (a control) | |
| 27 Sep #02 | 0.990545 | +0.000281 | Qwen2.5-1.5B and a self-trained e5-large in the mix, round-2 French labels (v7sq) | France score +0.0016 |
| 27 Sep #03 | 0.990699 | +0.000154 | US/India v7sq3; France with guarded round 2, 454 swaps dropped, France DP (mixmdp) | US/India +20e-6, France +134e-6 |
| 27 Sep #04 | 0.990879 | +0.000180 | Composite B: g1w (7B counted twice) plus 7B re-check drops | India +31e-6, US +10e-6, US/India drops +28e-6, French drops +111e-6 |

Entries are in LB units unless they say "France score".

Reading it:
- v3 gained +0.00446 on the holdout but only +0.00353 on the leaderboard. The audit that followed found French legal-form bitmasks outside the range seen in training and an encoding mismatch for unseen tokens [R]; both were fixed for v4 ([decision][d-v4]).
- 26 Sep #01 is the biggest step. The holdout moved +0.0013, the leaderboard +0.0082, because the work was aimed at France.
- 27 Sep #01 is a control. Its +0.000085 is the decision layer alone; the next upload added the new models for +0.000281 ([F09][f09]).
- Composite B was forecast at +0.000149 and measured +0.000180. The French drops are about 62% of its gain.
- Shares of the total rise of 0.014799: the v3 step 24%, the first French package 55%, blocking repairs and stage 3 5%, stronger cross-encoders 8%, self-training round 1 3%, the decision layer 0.6%, the 1.5B and self-trained e5 models 1.9%, guarded round 2 and France DP 1.0%, the 7B 1.2% [E, arithmetic].
- After B: 27 Sep #05 (B with round-3 France) 0.990833, #06 0.990819 and #07 (extra French drops) 0.990875 were controls. None beat B.

**Gap by upload.** The gap between the holdout and the public LB shrinks as France improves (one # is 0.0002):

```
v2           0.0083  ##########################################
v3           0.0092  ###############################################
26 Sep #01   0.0023  ############
26 Sep #02   0.0022  ###########
26 Sep #03   0.0015  ########
26 Sep #04   0.0010  #####
27 Sep #02   0.0007  ####
27 Sep #04   0.0004  ##
```

### 2.6 The implied France level

France has no labels, so every French level is inferred from the LB formula:

```
F_France = ( LB - 0.85025 x F_US/India_on_test ) / 0.14975
```

**Worked example (v3).** (0.97961 − 0.85025 × 0.98882) / 0.14975 = 0.927. **Composite B.** With the re-weighted US/India part 0.8433, (0.990879 − 0.8433) / 0.14975 = 0.985.

**Table 2. Implied France** (all [E]; notes of 26 to 27 Sep and [05 section 2.9][adv05]).

| upload | holdout | public LB | implied France |
|---|---|---|---|
| v3 | 0.98882 | 0.97961 | about 0.93 (0.925 to 0.931) |
| 26 Sep #01 | 0.990156 | 0.98781 | 0.971 to 0.976 |
| 26 Sep #02 | 0.990842 | 0.988609 | 0.973 |
| 26 Sep #03 | 0.991211 | 0.989721 | 0.978 |
| 26 Sep #04 | 0.991194 | 0.990179 | 0.981 |
| Composite B | 0.9913 | 0.990879 | about 0.985 |

So France moved from about 0.93 to about 0.985, and ends about 0.006 below US/India. Four numbers show why it is harder [M] ([methodology doc][doc]): each French decoy we removed shares its name with a median of 43 other S1; 11% of French S1 share their exact address with another S1; 32% of French addresses carry a department or region name; and about 23% of French copies drop or rewrite the legal form. It is the weakest country by a clear margin. State it as an estimate with its assumption: "near 0.985, plausibly anywhere from 0.98 to 0.99". The France-emptied probe, which would have pinned US/India on the test, was packaged several times and never uploaded; algebra stood in ([F10][f10]).

### 2.7 The candidate funnel

**What it is.** Blocking proposes candidates; models then cut them to a short list per S1. The test has 1,732,544 S1 and 9,969,589 S2/S3 records [M].

| stage | pairs | per test S1 | recall of true holdout pairs |
|---|---|---|---|
| all pairs | about 1.7 × 10^13 | | 100% |
| retrieval (token view and names-only view, per country, both directions) | 58.4M | about 34 | 99.1% [M] |
| after stage 0 (a cheap filter: 15.4% of pairs remain and keep 99.95% of true pairs [R]) | about 9.0M | | 99.95% of the retrieved true pairs |
| the kept candidate file (p1 at least 0.02, plus each record's best two S1, plus acronym joins) | 6,410,308 | 3.70 | about 98.2% to 98.4% [M] |
| the uncertain band for the cross-encoders (0.02 to 0.99) | 1,490,930 | 0.86 | |
| final predictions | | | 97.5% [M] |

**Cross-check.** The holdout has about 1.9M true pairs (549,699 × 3.46). It misses 16.5k at retrieval and about 15.2k more get a score near zero: 31.7k, which is 1.67% of 1.9M. That puts the kept file at about 98.3%, inside the 98.2% to 98.4% we quote [E, consistency check, not an independent measurement]. Never say 99.1% for the kept file.

**Efficiency.** 3.70 candidates per S1 against 3.46 true copies per S1 is a ratio of 1.07 [E]: the file carries only 0.24 extra pairs per S1. The cut from 4.68 to 3.70 per S1 changed F0.5 by −0.000003 [−0.000015, +0.000011], a tie, and the organisers' size rule favours the smaller file ([decision][d-cut]). Two tighter cuts lost −0.000106 and −0.000041.

### 2.8 Band AUCs

**What it is.** AUC is the chance that a random true pair scores above a random false pair; 0.5 is a coin flip. The **band** is the pairs with p1 between 0.02 and 0.99, where stage 1 hesitates. Band AUCs are measured on labelled holdout pairs in that band, so they are on hard pairs only [M] ([methodology doc][doc]).

| reader | band AUC | share of (true, false) pairs in the wrong order (1 − AUC) [E] |
|---|---|---|
| stage-1 score p1 | 0.930 | 7.0% |
| Qwen2.5-1.5B (LoRA) | 0.938 | 6.2% |
| e5-large | 0.939 | 6.1% |
| bge-reranker-v2-m3 | 0.942 | 5.8% |
| e5-large, French self-trained | 0.944 | 5.6% |
| Qwen2.5-7B (LoRA) | 0.944 (0.9436) | 5.6% |

All five readers sit within 0.006 of each other and 0.008 to 0.014 above p1. The 7B is **not** more accurate than a self-trained e5-large. It earns its place by adding diversity in the mix (counted twice) and by giving an independent reading of confident pairs. For comparison, the same 7B scored 0.537 untrained and 0.720 after a quick LoRA [R] ([F16][f16]).

### 2.9 Bootstrap intervals and P values

Each row is a paired bootstrap on the local holdout (Δ in macro F0.5; P is the share of resamples where the change helped) [M] ([F09][f09]).

| claim | Δ | 95% interval | P | verdict |
|---|---|---|---|---|
| 7B counted twice in the mix, India | +66.1e-6 | | 0.998 | real |
| the same, US | +26.2e-6 | | 0.906 | not significant; LB later +14e-6 |
| the whole decision layer | +48.1e-6 | [7.1, 91.2] | 0.987 | adopted |
| the dynamic programme alone | +33.2e-6 | [−7.5, +75.0] | | not significant |
| stage 3 | +55e-6 | [25, 85] | | adopted |
| 7B drop rule at −6 | +37e-6 whole holdout (+33e-6 on a 34% sample) | | | positive in both halves and in 99.7% of 3,000 random 25% subsets |

For the two g1w rows no interval is recorded. The P values imply standard errors of about 23e-6 and 20e-6, so rough intervals of [21, 111]e-6 for India and [−13, +65]e-6 for the US [E]. The honest sentence: "India is clear, the US is small and unproven, and the leaderboard agreed with its sign."

### 2.10 The 7B re-check

**Why.** 94.5% of our final predictions have p1 above 0.99, so no cross-encoder had read them. A LoRA-tuned Qwen2.5-7B (Bakshi) re-read 5,614,414 of them (870,019 French, 4,744,395 US/India) and we dropped those it rejected with a logit below −6, a cut-off fixed on labelled data before France was touched.

**Truth by 7B logit, labelled 34% sample** (186,897 S1, 631,001 predictions) [M] ([10][adv10]):

| 7B logit | predictions | truly a match |
|---|---|---|
| below −6 | 24 | 8.3% (2 pairs) |
| −6 to −4 | 51 | 86.3% |
| −4 to −2 | 138 | 94.9% |
| −2 to 0 | 6,616 | 99.6% |
| 0 or above | 596,333 | 99.8% to 100% |

The 8.3% is two pairs out of 24. A Wilson 95% interval is 2.3% to 25.8%, still far below the 75% to 80% a pair needs to be worth keeping ([F11][f11]). The cut-off −6 gained +33e-6 on the sample (halves +22e-6 and +43e-6) and +37e-6 on the whole holdout.

**On the test.** Composite B dropped 1,150 pairs: 840 French and 310 US/India. That is about 0.10% of French predictions against 0.0065% of US/India ones. 78% of the French rejects are the same generic name and house number on a different street, a pattern that is 99.7% real when our model accepts it and 0.5% real when it rejects it in US/India labels. In France the feature models accepted these decoys with confidence and the 7B did not. Bakshi's split of the public gain: India +31e-6, US +10e-6, US/India drops +28e-6 and French drops +111e-6, so the 840 French drops were worth about +0.00011 of the +0.00018 [E].

**Checks from outside.** The reject rate was the same in each third of French S1 (0.112% against 0.108% and 0.107%), including the third the adapter never saw. An independent bge detector trained on US/India labels and synthetic French flagged 708 of the 859 French rejects, 82% [M]. A looser French cut (toward −2 where Qwen3-4B agreed) scored 0.990875, a tie with B, so −6 was right.

### 2.11 Precision 99.9% and recall 97.5%

**What they are.** On the local holdout, almost everything we predict is right (precision 99.9%) and we find 97.5% of the true pairs [M] ([methodology doc][doc]). Our loss is recall.

**Why they do not combine to 0.9913.** The pooled formula gives 1.25 × 0.999 × 0.975 / (0.25 × 0.999 + 0.975) = 0.994 [E, arithmetic]. The benchmark averages F over S1, so an error in a small S1 costs far more than the pooled counts suggest (a miss on an S1 with one copy costs 1.0; [F11][f11]). The sources do not say how the 99.9% and 97.5% were pooled (U).

**Where recall is lost** [R]. 69% of the recall loss comes from S1 where we found some copies but not all, and 20% from S1 we missed completely. The missed copies are mostly records with an empty address and a changed name, which never become candidates (16.5k) or get a score near zero (15.2k). Heavy garbles, such as "EHPAD" typed as "ehpvd", account for more. None of the recall rules we tried was more than 71% precise, and an added pair must be right about 75% of the time to help, so we added none.

### 2.12 Claims we can make, and claims we must not

| topic | we can say | we must not say |
|---|---|---|
| score | public LB 0.990879 [M]; local holdout 0.9913 without France [M] | "our score is 0.9913", or any private score |
| France | near 0.985 [E], with the assumption about US/India on the test | "France scores 0.985" as if measured |
| candidates | retrieval 99.1%; kept file about 98.2% to 98.4% | 99.1% for the kept file |
| self-training | two rounds helped (+0.00046, +0.00015 on the public score); a third did not add | "round 3 hurt", without the confound (B's France had the decision layers) |
| the 7B | an independent re-check; about +0.00011 of the +0.00018, estimated | "the 7B is our best model" |
| decision layer | +0.000048 [0.000007, 0.000091] on the holdout | "the DP is significant" (alone it was not) |
| reproducibility | a rerun lands within about 0.0001 [R] | "bit-identical" |
| rank | 2nd of the Top 10, private ranking | anything about a private score |

### 2.13 Ten numbers every member must say correctly

Say the number with its scope. The sentence is a model; use your own words, but keep the scope and the level.

| # | number | say aloud |
|---|---|---|
| 1 | 0.990879 | "Our submission, Composite B, scored 0.990879 macro F0.5 on the public leaderboard, which includes France." |
| 2 | 0.9913 | "On our own labelled holdout of 549,699 US and India businesses the same pipeline scores 0.9913, US 0.9911 and India 0.9916. It has no France, because France has no labels." |
| 3 | 2nd of the Top 10 | "We finished second among the top ten on the private ranking. The organisers publish ranks, not private scores, so I can't give you a number." |
| 4 | France about 0.985 | "We never measured France directly. Backed out of the leaderboard formula it is near 0.985, about 0.006 below US and India, and that is an estimate: plausibly anywhere from 0.98 to 0.99." |
| 5 | 58.4M to 6,410,308 | "We retrieve 58.4 million pairs, about 34 per business, holding 99.1% of the true holdout pairs. We keep 6,410,308, 3.70 per business, holding about 98.2% to 98.4%." |
| 6 | 99.9% and 97.5% | "On the holdout, precision is 99.9% and recall 97.5%. What we lose is recall, mostly copies with an empty address and a changed name." |
| 7 | +0.00046, +0.00015 | "We self-trained on our own confident French decisions, positives at calibrated probability 0.9 or more and negatives at 0.05 or less, cross-fitted by business group. Round 1 added +0.00046 on the public score, round 2 with the French decision layers +0.00015. Round 3 did not help: forecast +0.000069, measured −0.000046." |
| 8 | +0.000048 | "For each business we choose the set with the highest expected F0.5 instead of one threshold. On the holdout the whole layer gained +0.000048, interval 0.000007 to 0.000091. The dynamic programme alone, +0.000033, was not significant." |
| 9 | 840 + 310 | "A Qwen2.5-7B re-read the 5.6 million predictions no cross-encoder had seen. We dropped those below a logit of −6: 840 French and 310 US/India pairs. On labelled data only 8.3% of such rejects are real, 2 of 24, and the French drops were worth an estimated +0.00011 of the final +0.00018." |
| 10 | 0.944 | "The 7B is not more accurate than a self-trained e5-large; both have a band AUC of 0.944. Counted twice in the mix it gained +0.000066 on India (P 0.998) and +0.000026 on the US (P 0.906, not significant). Its main value was the independent re-check." |

Bonus: "A control upload split a jump of +0.000366 into the decision layer, +0.000085, and the new models, +0.000281."

---

## 3. How it shows up in our project

| number | derived in | credit |
|---|---|---|
| holdout, bootstrap, controls | [F09][f09] | Ameya (`ber.eval`), Sachi (gate discipline) |
| self-training thresholds, rounds, France levels | [F10][f10] | Ameya (guards, rounds), Sachi (LOCO ladder) |
| break-even 0.5 to 0.8, expected-F0.5 set | [F11][f11] | Ameya (plan), Sachi (G6) |
| 7B re-check, g1w, Composite B | [10][adv10] | Bakshi (q7st, g1w, `compose_tsv.py`); Ameya (decoy analysis, captain of every upload) |
| Qwen2.5-1.5B cross-encoder | [08][adv08] | Sachi |

The jury probes the ratio of candidate pairs to entities ([README][readme]), so number 5 is the one to know by heart.

---

## 4. How to read the numbers

1. Ask three questions of any number: which evaluation (local holdout, public LB, private LB)? Which countries? Which evidence level?
2. In e-6 units, 1e-6 = 0.000001. On the LB a US change counts 0.38274 times, India 0.46751 and France 0.14975. A holdout gain of +66.1e-6 on India is +31e-6 on the LB.
3. One S1 flipping from wrong to right is 1.8e-6 on the holdout and 0.58e-6 on the test (1 / 1,732,544).
4. A P of 0.9 to 0.99 is a lean, not a proof. An interval across zero means "not shown", not "zero".
5. A France number is always [E]. Say the assumption.
6. A gap below about 5e-5 between near-identical uploads is noise [E].

---

## 5. Common misconceptions

1. **"0.9913 is our score."** It is the local holdout, US and India only.
2. **"The gap proves France is bad."** One equation, two unknowns: the US/India level on the test is also unknown.
3. **"99.1% is the recall of the candidate file."** It is the recall of the 58.4M retrieval. The kept file is about 98.2% to 98.4%.
4. **"Rank 16 at upload was our rank."** It was our rank at one moment of the public board. Our final private rank is 2nd of the Top 10.
5. **"P = 0.998 means 99.8% sure."** It is the share of bootstrap resamples that favoured the change.
6. **"The 7B is our most accurate model."** It ties a self-trained e5-large in the band.
7. **"Precision 99.9% and recall 97.5% give F0.5 0.994."** The metric is a mean of per-S1 values, 0.9913.
8. **"8.3% of the rejects are real" is a measurement for France.** It is 2 pairs of 24 on US/India labels.

---

## 6. Check yourself

**1.** Compute the LB if F_US = 0.9911, F_India = 0.9916 and F_France = 0.985. Compare with 0.990879 and say what it implies.

<details><summary>Answer</summary>

0.38274 × 0.9911 + 0.46751 × 0.9916 + 0.14975 × 0.985 = 0.379334 + 0.463583 + 0.147504 = 0.990421. The real score is 0.000458 higher. So either France is better than 0.985 or US/India score higher on the test than on the holdout (by 0.000458 / 0.85025 = 0.0005). The re-weighted holdout does give about +0.0004, which is why 0.985 is our estimate.

</details>

**2.** From a US/India part of 0.8433, find France for LB = 0.990879. What changes if the part is 0.8429?

<details><summary>Answer</summary>

(0.990879 − 0.8433) / 0.14975 = 0.9855. With 0.8429: (0.990879 − 0.8429) / 0.14975 = 0.9882. A difference of 0.0004 in the US/India part moves France by 0.0004 / 0.14975 = 0.0027, because dividing by 0.14975 magnifies errors about 6.7 times.

</details>

**3.** What share of the total rise from v2 to Composite B came from the two steps right after v2?

<details><summary>Answer</summary>

(0.00353 + 0.00820) / 0.014799 = 0.01173 / 0.014799 = 79%.

</details>

**4.** v3 gained +0.00446 on the holdout and +0.00353 on the LB. What does that say about France?

<details><summary>Answer</summary>

The US/India part should have moved by about 0.85025 × 0.00446 = +0.00379. The LB moved +0.00353, so the France part is −0.00026: France did not gain. The audit then found French legal-form bitmasks out of range and an encoding mismatch for unseen tokens.

</details>

**5.** Check the candidate arithmetic: pairs per S1 at retrieval and at the kept file, and the ratio to true copies.

<details><summary>Answer</summary>

58.4M / 1,732,544 = 33.7. 6,410,308 / 1,732,544 = 3.70. 3.70 / 3.46 = 1.07.

</details>

**6.** The holdout has about 1.9M true pairs. Retrieval misses 16.5k and 15.2k more score near zero. What recall ceiling does that give the kept file?

<details><summary>Answer</summary>

(16.5k + 15.2k) / 1.9M = 1.67%, so about 98.3%, inside 98.2% to 98.4%. Final recall is 97.5%, so the decisions lose about another 0.8 points (about 15k pairs) [E].

</details>

**7.** The 7B dropped 840 of 870,019 French and 310 of 4,744,395 US/India predictions. Compute both rates and their ratio.

<details><summary>Answer</summary>

840 / 870,019 = 0.097%. 310 / 4,744,395 = 0.0065%. Ratio 15. France is 15 times the US/India test rate, which fits decoys that are specific to France.

</details>

**8.** The India g1w row has P = 0.998. Estimate its standard error and a rough interval.

<details><summary>Answer</summary>

P = 0.998 means z = 2.88. SE = 66.1e-6 / 2.88 = 23e-6. Interval 66.1 ± 1.96 × 23 = [21, 111]e-6 [E]. The same method for the US (P = 0.906, z = 1.32, SE 20e-6) gives [−13, +65]e-6, which includes zero.

</details>

**9.** US holdout gain of the 7B mix is +26.2e-6. The LB moved +14e-6. Are these consistent?

<details><summary>Answer</summary>

On the LB the US counts 0.38274, so +26.2e-6 on the holdout predicts +10.0e-6. The LB showed +14e-6. The gap of 4e-6 is inside the noise of near-identical uploads (about 5e-5). Yes, consistent.

</details>

**10.** Someone asks, "What was your private score?" Give a one-sentence answer.

<details><summary>Answer</summary>

"The organisers publish only the ranking, and we finished 2nd of the Top 10; our public score was 0.990879, which includes France, and our local validation was 0.9913 without it." Do not estimate a private score.

</details>

**11.** Label each as M, E, R or U: (a) 0.990879; (b) France about 0.985; (c) the 7B trained in about 2 hours on three H100s; (d) why our private rank beat our public rank at upload.

<details><summary>Answer</summary>

(a) M. (b) E, backed out of the formula under an assumption. (c) R, stated in the methodology and not re-timed. (d) U, our data cannot say.

</details>

---

## 7. Going deeper

- [05 evaluation methodology][adv05], sections 2.8 and 2.9: the label-free checks and the holdout-versus-leaderboard gap, with the jury answers. [10 LLM verification][adv10]: the re-check tables. [04 metrics and decisions][adv04]: why F0.5 is not the pooled formula.
- The methodology document ([doc][doc]) is the source of the headline numbers.
- Blum and Hardt (2015), "The Ladder: A Reliable Leaderboard for Machine Learning Competitions", ICML, on why leaderboard scores deserve caution. Roelofs et al. (2019), "A meta-analysis of overfitting in machine learning", NeurIPS.

## 8. Where next

- [F09][f09], [F10][f10] and [F11][f11] explain how the numbers were obtained.
- [F15][f15] and [F16][f16] cover the structure of the problem and learning without labels.
- The track map: [foundations README](README.md).

[doc]: ../../../experiments/ameya/final-zip/doc/Documentation_template.md
[changelog]: ../../../CHANGELOG.md
[readme]: ../README.md
[adv04]: ../04-metrics-and-decisions.md
[adv05]: ../05-evaluation-methodology.md
[adv08]: ../08-transformers-and-cross-encoders.md
[adv09]: ../09-self-training-and-domain-shift.md
[adv10]: ../10-llm-verification-and-compute.md
[f01]: F01-data-and-problem.md
[f04]: F04-classification-metrics.md
[f09]: F09-experiments-and-evidence.md
[f10]: F10-semi-supervised-and-domain-shift.md
[f11]: F11-decision-theory-and-optimisation.md
[f15]: F15-clustering-graphs-and-er-variants.md
[f16]: F16-learning-with-limited-labels.md
[d-v4]: ../../../docs/decisions/2026-09-26_0207_model-v4-france-and-cross-encoder.md
[d-cut]: ../../../docs/decisions/2026-09-26_0532_candidate-set-cut.md
[lb-27-04]: ../../../submissions/records/2026-09-27_sub04.md
