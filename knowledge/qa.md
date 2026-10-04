# Jury Q&A bank

Deeper answers: the component pages in [`components/`](components/README.md) explain each part of the pipeline (how, why, alternatives, limits, scale).

The question bank for the 5-minute Q&A at the Grand Finale (Wed 7 Oct 2026, after the 10-minute talk): 100 questions in eight groups that follow the organisers' talk sections. Each entry has a spoken answer of at most three sentences, the evidence (numbers with their evidence level, and links) and likely follow-ups.
Numbers come from [`numbers.md`](numbers.md). Where our submitted methodology document is looser than the record, the answer follows the record ([`conflicts.md`](conflicts.md)) and the entry says so. Format: [`STANDARD.md`](STANDARD.md) §2.8.

Status: first full draft, 4 Oct 2026. Each member should read the entries on their own area; the open points are at the end.

## How to answer

> **How to answer (20 to 30 seconds per question)**
>
> 1. **Answer first.** The first sentence is the answer: yes, no, a number or a name. Reasons come after.
> 2. **One number, with its scope.** Say "public leaderboard", "local holdout (US and India)" or "test". Never a bare F0.5.
> 3. **Admit the limit in one clause.** "We never measured that." "That is an estimate." Do not defend what the record does not support.
> 4. **Offer depth, then stop.** "I can go into the cost arithmetic if useful." Let the jury choose.
>
> The jury values reasoning over results, honesty about limits, concrete numbers and scale. Credit people by role: Ameya (integration, model chain, France), Bakshi (7B, audit, package, Composite B), Sachi (Plan B gates, Qwen code, diagnostics).

**Say it this way.** These ten statements are the ones most likely to go wrong ([numbers: not to quote](numbers.md#numbers-not-to-quote-and-why)).

| topic | say | do not say |
|---|---|---|
| candidates | Retrieval keeps 99.1% of true holdout pairs at about 34 per S1; the cut to 3.70 per S1 keeps 98.35% | "3.70 per S1 at 99.1% recall" |
| scores | 0.990879 on the public leaderboard; 0.9913 on the US and India holdout, which has no France | a bare "0.99" or "our F0.5 is 0.9913" |
| ranking | 2nd of the Top 10; the organisers publish rankings only | any private score or estimate; "rank 16" |
| cost of an error | F0.5 weights precision twice as much as recall; in counts one false merge equals four missed copies, about 2.7 times one miss for a typical S1 | "a wrong merge costs twice a miss" |
| decision layer | the whole layer gained 0.000048 [0.000007, 0.000091] over the best flat threshold; the set selection alone was not significant | "the set selection beat a threshold by 0.000048" |
| holdout | holdout predictions are out of fold; the final test models also saw its rows, so it is a comparison set | "we never trained on the holdout" |
| France | France cannot be validated locally; from the public score we estimate it rose from about 0.93 to about 0.98 | any single French F0.5 as if measured |
| the 7B | it ties a well-trained e5-large (0.944); its value is diversity and an independent reading of confident pairs; 20% of its strong rejects are true on the whole holdout | "the 7B is more accurate"; "only 8% are true" |
| records | about 24 million records | "23.7M" |
| stage 0 | removes about 85% of pairs and keeps 99.95% of true ones | "about 80%" |

## Top 15 most likely questions

1. [Q7](#q7) What is your solution strategy in 30 seconds, and what is new in it?
2. [Q10](#q10) Why no city or state blocking keys? (The organisers rated finer-grained keys higher.)
3. [Q11](#q11) 3.70 candidates per S1: with what recall?
4. [Q12](#q12) What recall do you get with fewer candidates, say two per S1?
5. [Q26](#q26) Why do the cross-encoders only read the uncertain band?
6. [Q35](#q35) How do you handle singletons?
7. [Q51](#q51) Your local score is 0.9913 and the leaderboard 0.990879. Why the gap, and how did you find out?
8. [Q52](#q52) How can you validate anything on France with no labels?
9. [Q87](#q87) How do you know self-training did not just reinforce its own mistakes?
10. [Q88](#q88) Is the 7B re-check just luck?
11. [Q34](#q34) Why choose a set per S1 instead of a threshold, and did it always win?
12. [Q63](#q63) What would this cost on a billion records?
13. [Q85](#q85) Haven't you overfit the holdout, given how many things you tuned on it?
14. [Q73](#q73) What would you do differently?
15. [Q91](#q91) Are all your models within the rules?

Also likely: [Q54](#q54), [Q55](#q55), [Q92](#q92), [Q72](#q72), [Q37](#q37), [Q38](#q38).

## Contents

- [1. Problem understanding](#1-problem-understanding): Q1 to Q8 (8 questions)
- [2. Blocking and candidate generation](#2-blocking-and-candidate-generation): Q9 to Q19 (11 questions)
- [3. Matching model and features](#3-matching-model-and-features): Q20 to Q34 (15 questions)
- [4. Edge cases: singletons, the unseen country, noisy names and addresses](#4-edge-cases-singletons-the-unseen-country-noisy-names-and-addresses): Q35 to Q49 (15 questions)
- [5. Results and evaluation](#5-results-and-evaluation): Q50 to Q62 (13 questions)
- [6. Scalability and efficiency](#6-scalability-and-efficiency): Q63 to Q71 (9 questions)
- [7. Learnings and honesty](#7-learnings-and-honesty): Q72 to Q84 (13 questions)
- [8. Hard and hostile questions](#8-hard-and-hostile-questions): Q85 to Q100 (16 questions)

Suggested leads, from who built what (confirm in the team call): blocking, model chain, France, evaluation and leaderboard: Ameya; the 7B re-check, packaging, audit and reproducibility: Bakshi; gates, the Qwen code, diagnostics and the French patterns: Sachi.

---

## 1. Problem understanding

Slide 2 of the talk. The jury checks that we understood the task, the metric and the data before they look at the method.

<a id="q1"></a>
**Q1. What is the problem, in one minute, and what makes it hard?**

- **Say this:** For every Source-1 business we list all the Source-2 and Source-3 records that describe the same business, from zero to eleven of them and 3.46 on average. The score is a macro F0.5 per Source-1 entity, so a false merge costs more than a miss, and an empty list for a business with no match scores a perfect 1.0. The hard parts are look-alike decoys, noisy names and addresses, and France, a test country that never appears in training.
- **Evidence:** 24,229,173 records (12,527,040 train, 11,702,133 test) [M]; 0 to 11 matches per S1, mean 3.46 (S2 1.67, S3 1.79), 5.6% of S1 with none [M, train truth]; test has 1,732,544 S1, of which France 259,452 (14.975%) [M]; [numbers §1](numbers.md#1-data-facts), [theory 01](theory/01-entity-resolution.md), components/data-and-problem.md.
- **Follow-ups:**
  - [Q3](#q3) What is a look-alike decoy, and why does it dominate the errors?
  - [Q2](#q2) Why does F0.5 matter for the design, and how much does a wrong merge cost?
  - [Q38](#q38) How did you handle France, a country never seen in training?

<a id="q2"></a>
**Q2. Why does F0.5 matter for the design, and how much does a wrong merge cost?**

- **Say this:** F0.5 weights precision twice as much as recall. In counts, one false merge costs as much as four missed copies, and for a typical business with four true copies it costs about 2.7 times one missed copy. So we add a record only when it is more likely true than about three in four, except the first one, which needs just over one in two.
- **Evidence:** F0.5 = 1.25·TP / (1.25·TP + 0.25·FN + FP) [analytic]; for an S1 with 4 true copies and a perfect list, a wrong addition costs 0.167 and a missed copy 0.0625 (ratio 2.7) [E]; a pair pays above p = 0.500 (1st), 0.727 (2nd), 0.759 (3rd), 0.771 (4th), tending to 0.8 [E]; the methodology says "twice as much as a missed copy" and the records say "about 3" and "about 4", so use the wording above ([CF-15](conflicts.md)); [numbers §4.1](numbers.md#41-set-selection-and-break-even), [numbers: not to quote](numbers.md#numbers-not-to-quote-and-why) #3, [theory 04](theory/04-metrics-and-decisions.md).
- **Follow-ups:**
  - [Q34](#q34) Why choose a set per S1 instead of a threshold, and did it always win?
  - [Q59](#q59) What do precision and recall look like, and how does F0.5 trade them?
  - [Q78](#q78) Your document says a wrong merge costs twice a miss and that the set selection gained 0.000048. Is that exact?

<a id="q3"></a>
**Q3. What is a look-alike decoy, and why does it dominate the errors?**

- **Say this:** A look-alike is a record of a different business that imitates a real one: same street, a nudged house number, often one extra business word such as "group" or "holdings". A true copy keeps the first house number in 85% of cases, a look-alike in only 12%. Telling those apart, more than finding copies, is where the model earns its score.
- **Evidence:** first house number equal 12.4% (look-alikes) vs 84.8% (true pairs); at least one extra name word 76.5% vs 23.3% [M, train, weak proxy]; the look-alike number is the S1 number plus d, d in {1, 2, 3, 4, 5, 7, 9, 11, 13, 21}, and 99.5% of US nudges go up [M]; restoring legal-form signal (look-alikes change it) gave +0.00271 [0.00260, 0.00283] [M]; in France the look-alike is a swapped descriptor at the same address (op B), 0.6% true in US/India [M]; [numbers §1](numbers.md#1-data-facts), [decision legal-form-features](../docs/decisions/2026-09-25_2142_gate-legal-form-features.md), [decision france-generator-ops](../docs/decisions/2026-09-26_0417_france-generator-ops-and-final-fit.md).
- **Follow-ups:**
  - [Q4](#q4) Test has 23% more records per S1 than train. Are they decoys or owners you cannot find?
  - [Q40](#q40) What is an "op-B" look-alike, and how did you handle it?
  - [Q22](#q22) Which features matter for noisy records?

<a id="q4"></a>
**Q4. Test has 23% more records per S1 than train. Are they decoys or owners you cannot find?**

- **Say this:** Decoys. The number of true matches per S1 stayed flat, and only the "same name, different house number" pattern grew, so a test S1 carries about 3.5 true copies and roughly twice the look-alikes. We checked this on India, where train and test pools match in size, and later on the predictions per S1.
- **Evidence:** 5.75 vs 4.68 S2/S3 records per S1 (+23%) [M]; about 3.5 true copies and 2.3 look-alikes per test S1, against 1.2 look-alikes in train [E]; closeness profile India 31.7% test vs 31.8% train, whereas removing owners would give about 26% and 53% [M, crude proxy]; test US/India predictions per S1 within about 0.04 of the holdout [M]; "true matches per S1 not higher" is an inference from label-free predictions [E]; [numbers §1](numbers.md#1-data-facts), [D-EVL-02](decisions/EVL.md#d-evl-02--test-shift-by-diagnostics-not-test--train-and-not-a-drop-s1-stress-test).
- **Follow-ups:**
  - [Q3](#q3) What is a look-alike decoy, and why does it dominate the errors?
  - [Q51](#q51) Your local score is 0.9913 and the leaderboard 0.990879. Why the gap, and how did you find out?

<a id="q5"></a>
**Q5. What did your first data checks change in the plan?**

- **Say this:** They overturned three assumptions: postcodes are almost absent, house numbers are equal in only 83% of true pairs, and 46 to 54% of S1 share a name with another S1. So we dropped the postcode feature, made house-number relations and extra-word features core, and replaced "test looks like train" with diagnostics.
- **Evidence:** postcodes on at most 0.5% of addresses [M]; first house number equal in 83.3% of true pairs [M]; name collisions 46.2% US, 53.6% India [M]; test +23% records per S1 [M]; [D-NRM-01](decisions/NRM.md#d-nrm-01--no-postcode-field-or-feature), [D-FEA-01](decisions/FEA.md#d-fea-01--keep-the-look-alike-word-features-plan-bs-cut-reversed), [D-EVL-02](decisions/EVL.md#d-evl-02--test-shift-by-diagnostics-not-test--train-and-not-a-drop-s1-stress-test), [numbers §1](numbers.md#1-data-facts).
- **Follow-ups:**
  - [Q6](#q6) Why is name matching not enough on its own?
  - [Q7](#q7) What is your solution strategy in 30 seconds, and what is new in it?

<a id="q6"></a>
**Q6. Why is name matching not enough on its own?**

- **Say this:** Almost half of the S1 share an exact name with another S1, and a name alone cannot say which of them owns a record. The address, the house number and the competition between S1 for the same record separate them, because each S2 or S3 record has at most one owner. Where the address is empty nothing separates them, and that is our largest remaining loss.
- **Evidence:** 46.2% of US and 53.6% of India S1 share an exact core name; other keys give other shares, for example 34% of French S1 for a folded name ([CF-39](conflicts.md)) [M]; 0 one-owner violations in 7,638,365 true pairs [M]; stage 2 over stage 1 +0.001995 [0.00189, 0.00210] on the holdout [M]; empty-address records of shared names are 69% of misses at v5all [M]; [D-PRB-02](decisions/PRB.md#d-prb-02--each-s2s3-record-has-at-most-one-owner-argmax-ownership-plus-rivalry-features), [D-PRB-03](decisions/PRB.md#d-prb-03--do-not-chase-empty-address-misses-whose-name-several-s1-share-bayes-limit), [D-MDL-03](decisions/MDL.md#d-mdl-03--stage-2-a-collective-model-over-the-full-candidate-graph-isotonic-calibrated-with-cluster-support), [numbers §3.5](numbers.md#35-where-the-remaining-loss-is).
- **Follow-ups:**
  - [Q37](#q37) Where is the remaining loss on US and India, and is it fixable?
  - [Q15](#q15) Why a union of name-driven and address-driven retrieval?

<a id="q7"></a>
**Q7. What is your solution strategy in 30 seconds, and what is new in it?**

- **Say this:** Spend compute where the uncertainty is, and decide the way the metric scores. Cheap per-country retrieval and a learned cut leave 3.70 candidates per S1, boosted trees score them all, and heavier models read only the uncertain pairs. New for us: guarded self-training for the unlabelled country, a per-S1 choice of the list with the best expected F0.5, and a 7B re-check of confident predictions.
- **Evidence:** pairs per test S1: retrieval 33.73, stage 0 4.77, the cut 3.70, final matches 3.378 [M]; cross-encoders read 1.49M of 58.4M pairs (2.6%) and 94.5% of final predictions were never read by one [M]; sizes, stated honestly: self-training round 1 +0.000458 on the public LB, the decision layer +0.000048 on the holdout, Composite B (with the 7B re-check) +0.000180 on the public LB, roughly +0.0001 of it from the French drops [E] ([Q88](#q88)); [numbers §2](numbers.md#2-blocking-and-candidates), [numbers §4.3](numbers.md#43-the-7b-re-check-of-confident-predictions), components/model-stages.md, [theory 11](theory/11-scaling-to-billions.md).
- **Follow-ups:**
  - [Q43](#q43) How does your self-training work?
  - [Q34](#q34) Why choose a set per S1 instead of a threshold, and did it always win?
  - [Q30](#q30) The 7B is no more accurate than e5-large. Why use it?

<a id="q8"></a>
**Q8. Is this classification, ranking or clustering, and why not graph clustering?**

- **Say this:** We treat it as pairwise classification with a collective step on top: each record has one owner, so S1 compete for records, and each S1 then gets the list with the best expected F0.5. The owner constraint and a cluster-support feature in stage 2 covered the transitive evidence we needed. We did not build or measure a graph-clustering alternative.
- **Evidence:** stage 2 is a "collective model over the full candidate graph, isotonic-calibrated, with cluster support" ([D-MDL-03](decisions/MDL.md#d-mdl-03--stage-2-a-collective-model-over-the-full-candidate-graph-isotonic-calibrated-with-cluster-support)); graph clustering, an LLM judge and a singleton model were left out of the plan ([D-CE-01](decisions/CE.md#d-ce-01--cross-encoders-only-as-a-gated-extra-no-llm-judge-graph-clustering-or-singleton-model)); no clustering run exists in the record, so this is absence of evidence, not a measured negative [U]; [D-PRB-02](decisions/PRB.md#d-prb-02--each-s2s3-record-has-at-most-one-owner-argmax-ownership-plus-rivalry-features), [D-DEC-01](decisions/DEC.md#d-dec-01--per-s1-expected-f05-set-selection-gated-against-a-tuned-threshold-g6), [theory 01](theory/01-entity-resolution.md), [theory 04](theory/04-metrics-and-decisions.md).
- **Follow-ups:**
  - [Q34](#q34) Why choose a set per S1 instead of a threshold, and did it always win?
  - [Q24](#q24) What does stage 2 add over stage 1?

## 2. Blocking and candidate generation

Slide 4, and the organisers' own ranking criteria (blocking strategy, candidate efficiency). Know the three numbers: 33.73 per S1 at 99.1% before the cut, 3.70 per S1 at 98.35% after it.

<a id="q9"></a>
**Q9. How does your blocking work, and how long does it take?**

- **Say this:** Per country, we index IDF-weighted name and address tokens, take each S1's top records and each record's top S1, and keep a pair if it is in the S1's top 15 or the record's top 4. A second view on character four-grams covers short or empty addresses, and repairs handle domain names, OCR digits and ordinals. On test this returns 58.4M pairs, 33.73 per S1, in about 16 minutes on one laptop.
- **Evidence:** 58,437,794 pairs on test (33.73 per S1) [M]; token view: each S1's top 40 records and each record's top 8 S1, then the 15/4 trim [M]; run time 938 s (test) and 952 s (train) on a 24-core laptop [M]; retrieval recall v0 0.9752, v1 0.9857, v2 0.9899, v3 0.99135 [M]; [numbers §2](numbers.md#2-blocking-and-candidates), [D-BLK-01](decisions/BLK.md#d-blk-01--retrieve-by-name-and-by-address-separately-and-take-the-union-name-only-search-only-for-empty-or-short-addresses), [D-BLK-03](decisions/BLK.md#d-blk-03--heuristic-trim-top-15-per-s1-or-top-4-per-record-no-learned-pre-ranker-in-v0), [D-BLK-05](decisions/BLK.md#d-blk-05--engine-exact-idf-weighted-token-overlap-on-the-cpu-instead-of-tf-idf--svd--gpu-top-k), components/blocking.md, [theory 02](theory/02-blocking.md).
- **Follow-ups:**
  - [Q16](#q16) Why exact token overlap, not embeddings or approximate nearest neighbours?
  - [Q10](#q10) Why no city or state blocking keys? (The organisers rated finer-grained keys higher.)
  - [Q66](#q66) How does blocking scale?

<a id="q10"></a>
**Q10. Why no city or state blocking keys? (The organisers rated finer-grained keys higher.)**

- **Say this:** We partition by exact country only, because a hard state or city key can silently drop a true pair when the field is missing, abbreviated or in a regional script. City and state words still count as ordinary address tokens in retrieval, where a rare city name weighs a lot and a common state name almost nothing, so they work as a soft key. We never measured the recall of a hard city or state key, so I cannot give you that number; it is the first thing we would test.
- **Evidence:** 0 cross-country matches in 7.64M true pairs, so the country partition loses nothing [M]; the case against state partitions is Plan B's argument and is reasoned, not measured on a state key [R]; the record says so plainly: "we use city and state as features, not as keys, and no test of keys on them is recorded" ([D-BLK-02](decisions/BLK.md#d-blk-02--partition-the-search-by-the-exact-country-label-never-by-state), hindsight); the final model has no dedicated city or state feature, although the methodology's Table 2 lists them ([CF-24](conflicts.md)); without any such key, retrieval recall is 99.135% at 33.73 per S1 and the learned cut gives 98.35% at 3.70 [M]; after normalisation, state spellings, native script and city aliases cost no matches, only OCR, ordinals and domains did [M, [RESEARCH_v5 §5](../experiments/ameya/model-v1/RESEARCH_v5.md)]; [Q81](#q81) for the Table 2 wording.
- **Follow-ups:**
  - [Q12](#q12) What recall do you get with fewer candidates, say two per S1?
  - [Q11](#q11) 3.70 candidates per S1: with what recall?
  - [Q73](#q73) What would you do differently?

<a id="q11"></a>
**Q11. 3.70 candidates per S1: with what recall?**

- **Say this:** Retrieval keeps 99.1% of the true holdout pairs at about 34 candidates per S1. The learned cut shrinks that to 3.70 per S1 and keeps 98.35%, so the cut costs about 0.8 points of pair recall for about nine times fewer pairs. On the holdout it cost nothing measurable in F0.5.
- **Evidence:** retrieval recall 0.99135 (16,455 of 1,901,267 true holdout pairs never retrieved) at 33.73 per S1 [M]; candidate-file recall 0.98354 (31,304 outside the file) at 3.70 per test S1 and 3.588 per holdout S1 [M]; F0.5 effect of the cut −0.000003 [−0.000015, +0.000011] at v5all [M]; holdout oracle F0.5 0.99743 before the cut, 0.99499 after [M]; the methodology puts 99.1% next to the 3.70 file, which is the pre-cut figure ([CF-13](conflicts.md), [numbers: not to quote](numbers.md#numbers-not-to-quote-and-why) #1); [numbers §2](numbers.md#2-blocking-and-candidates), [decision candidate-set-cut](../docs/decisions/2026-09-26_0532_candidate-set-cut.md), [D-BLK-10](decisions/BLK.md#d-blk-10--cut-the-candidate-file-to-p1--002-and-each-records-top-2-s1-370-per-s1).
- **Follow-ups:**
  - [Q12](#q12) What recall do you get with fewer candidates, say two per S1?
  - [Q77](#q77) Your methodology document puts 99.1% next to 3.70 per S1. Which is it?
  - [Q14](#q14) Isn't the cut a way to look efficient on the candidate criterion?

<a id="q12"></a>
**Q12. What recall do you get with fewer candidates, say two per S1?**

- **Say this:** Two per S1 cannot work: a business has 3.46 true matches on average, so a hard top-2 cap could recall at most about 53% of true pairs even with a perfect ranking. Of the cuts we did measure, every tighter one lost score: keeping only each record's best S1 cost 0.000106 of F0.5 and a stricter probability cut cost 0.000041. We sit at 3.70 per test S1, within about 7% of the average number of true matches.
- **Evidence:** ceiling of a hard top-k cap = E[min(n, k)] / E[n]: about 0.53 for k = 2 and 0.74 for k = 3, from the train distribution of matches per S1 (0: 5.6%, 1: 5.4%, 2: 17%, 3: 24%, 4: 22%, 5: 14.6%, 6: 7.5%, 7 or more: 4%) [E, derived for this page]; tighter cuts on the final rule: top 1 per record −106e-6 [−129, −83] at 3.589 per S1; p1 ≥ 0.05 −41e-6 [−52, −30] at 3.608; p1 ≥ 0.1 −105e-6; p1 ≥ 0.2 −279e-6 [M]; a per-S1 top-6 cut lost 0.0014 [M]; the recall of those tighter cuts was not recorded; a 2.8% smaller file (stage 3 gated on stage-2 pc ≥ 2e-4) needed a full rebuild and was not built [M]; [numbers §2](numbers.md#2-blocking-and-candidates), [D-BLK-16](decisions/BLK.md#d-blk-16--keep-the-candidate-file-at-370-per-s1-against-tighter-cuts), [D-BLK-10](decisions/BLK.md#d-blk-10--cut-the-candidate-file-to-p1--002-and-each-records-top-2-s1-370-per-s1).
- **Follow-ups:**
  - [Q13](#q13) Why cut per record and not top-k per S1?
  - [Q14](#q14) Isn't the cut a way to look efficient on the candidate criterion?
  - [Q19](#q19) Is 3.70 per S1 efficient, and what do you get if "per record" means per S2 or S3 record?

<a id="q13"></a>
**Q13. Why cut per record and not top-k per S1?**

- **Say this:** A record belongs to only one S1, so only its best-scoring S1 can claim it, and its lower-ranked S1 are almost never predicted. True sets reach 11 records, so a per-S1 top-k throws away real matches: top-6 lost 0.0014. A per-record rule removes the rivals' pairs instead.
- **Evidence:** the cut keeps a pair if stage 0 keeps it, p1 ≥ 0.02 and it is among the record's top 2 S1 by p1 (an intersection; the methodology's "plus" is loose, [CF-14](conflicts.md)) [M]; 4.68 → 3.70 per test S1 (−21%), file 8.11M → 6.41M pairs, 127 MB → 105 MB [M]; train truth never exceeds 5 S2 and 6 S3 per S1 [M]; [decision candidate-set-cut](../docs/decisions/2026-09-26_0532_candidate-set-cut.md), [D-BLK-10](decisions/BLK.md#d-blk-10--cut-the-candidate-file-to-p1--002-and-each-records-top-2-s1-370-per-s1).
- **Follow-ups:**
  - [Q12](#q12) What recall do you get with fewer candidates, say two per S1?
  - [Q77](#q77) Your methodology document puts 99.1% next to 3.70 per S1. Which is it?

<a id="q14"></a>
**Q14. Isn't the cut a way to look efficient on the candidate criterion?**

- **Say this:** No: it is a real filter in front of our own second-stage model, so the candidate file is the set the matcher goes on to score. We rejected cutting the file down to the final decisions, because that would turn the file into an output, not an input. On the holdout the cut was a tie in F0.5.
- **Evidence:** F0.5 −0.000003 [−0.000015, +0.000011] at v5all [M]; cutting to the decision boundary was proposed and rejected ([D-BLK-13](decisions/BLK.md#d-blk-13--cut-the-candidates-to-the-decision-boundary-bakshis-proposal)); final audit: 0 matches outside the candidates, validator PASS [M]; 75,361 S1 have no candidate [M]; [D-BLK-09](decisions/BLK.md#d-blk-09--the-candidate-file-is-the-set-the-model-scores-stage-2-input-not-the-raw-blocking-output), [D-SUB-06](decisions/SUB.md#d-sub-06--the-candidate-file-is-the-set-the-matcher-actually-scores), [D-BLK-10](decisions/BLK.md#d-blk-10--cut-the-candidate-file-to-p1--002-and-each-records-top-2-s1-370-per-s1).
- **Follow-ups:**
  - [Q12](#q12) What recall do you get with fewer candidates, say two per S1?
  - [Q97](#q97) Why should we trust a validator PASS?

<a id="q15"></a>
**Q15. Why a union of name-driven and address-driven retrieval?**

- **Say this:** Name and address fail independently: 16% of true pairs have a weak name, 5% a weak address, and only 0.1% are weak on both. So the union of the two views recovers almost everything, where a combined-only retriever cannot. The name-only view runs only for empty or short addresses, because about half of the S1 names collide.
- **Evidence:** weak name 15.9% (India 26.1%, US 9.0%); weak address 4.7%; both 0.09% (200k train true pairs) [M] (other samples: 15.75 / 5.24 / 0.14, [CF-43](conflicts.md)); name-only view for addresses of 3 tokens or fewer and one-token names of 8 letters or more [M]; [D-BLK-01](decisions/BLK.md#d-blk-01--retrieve-by-name-and-by-address-separately-and-take-the-union-name-only-search-only-for-empty-or-short-addresses), [theory 02](theory/02-blocking.md).
- **Follow-ups:**
  - [Q16](#q16) Why exact token overlap, not embeddings or approximate nearest neighbours?
  - [Q17](#q17) Where does retrieval still miss, and why not reach the planned 99.5%?

<a id="q16"></a>
**Q16. Why exact token overlap, not embeddings or approximate nearest neighbours?**

- **Say this:** We needed an exact, fast, testable retriever on day one, and exact IDF-weighted token search on 24 cores did each split in about 16 minutes. Targeted keys then closed each measured miss type faster than a dense view would have. We never ran a dense-retrieval comparison, so we cannot say it would be worse; the planned gate for it, G2, was never run.
- **Evidence:** blocking v0 19 and 15 min, final 938 s and 952 s [M]; recall 0.9752 → 0.9857 → 0.9899 → 0.99135 across v0 to v3 [M]; the plan had TF-IDF → SVD-256 → GPU views with gate G2, which never ran ([CF-53](conflicts.md)); [D-BLK-05](decisions/BLK.md#d-blk-05--engine-exact-idf-weighted-token-overlap-on-the-cpu-instead-of-tf-idf--svd--gpu-top-k), [D-BLK-04](decisions/BLK.md#d-blk-04--blocking-uses-its-own-tokenizer-instead-of-waiting-for-the-normalise-stage), [theory 02](theory/02-blocking.md), components/blocking.md.
- **Follow-ups:**
  - [Q66](#q66) How does blocking scale?
  - [Q17](#q17) Where does retrieval still miss, and why not reach the planned 99.5%?

<a id="q17"></a>
**Q17. Where does retrieval still miss, and why not reach the planned 99.5%?**

- **Say this:** Retrieval misses 0.87% of true pairs, and over half of those are empty-address records whose name was also changed. Nothing in such a record points to its owner, and unowned records of that kind are only 37 to 40% true, so adding them would lose score. We reached 99.1% and never the 99.5% stretch bar.
- **Evidence:** misses v2 19,163 → v3 16,455 of 1,901,267 true pairs [M]; 54% are empty-address records with a changed name (66.8% have an empty record address in any case, [CF-42](conflicts.md)) [M]; the "G1 met" statement holds only for the v0 bar ([CF-52d](conflicts.md)); the alias bridge reaches about 30 French pairs and was closed ([D-BLK-15](decisions/BLK.md#d-blk-15--close-the-alias-bridge-recall-route)); v3 repairs (domains, OCR digits, ordinals) lifted recall from 0.98992 to 0.99135 ([decision blocking-v3-repairs](../docs/decisions/2026-09-26_1122_blocking-v3-repairs.md), [D-BLK-11](decisions/BLK.md#d-blk-11--blocking-v3-repairs-domains-ocr-digits-ordinals-honorific-stop-words-reverted)) [M]; [D-BLK-12](decisions/BLK.md#d-blk-12--exact-address-blocking-view-for-the-v3-regression-not-built).
- **Follow-ups:**
  - [Q37](#q37) Where is the remaining loss on US and India, and is it fixable?
  - [Q46](#q46) How did you handle Indic scripts without external data?

<a id="q18"></a>
**Q18. Why partition by country, and does it stay open to a new country?**

- **Say this:** There are no cross-country matches in 7.6M true pairs, so partitioning by the exact country label loses nothing and keeps word statistics local to each country. France ran as its own partition with its own statistics, and a record with an unseen or empty label would be searched against every partition. No model uses country as a feature.
- **Evidence:** 0 cross-country pairs in 7,638,365 true pairs [M]; France: 259,452 S1 against 1,434,993 S2/S3 records in test [M]; a few late rule scripts do name France ([CF-26](conflicts.md)) [M]; [D-BLK-02](decisions/BLK.md#d-blk-02--partition-the-search-by-the-exact-country-label-never-by-state), [D-PRB-01](decisions/PRB.md#d-prb-01--country-is-an-open-set-no-country-feature-statistics-per-exact-country-label).
- **Follow-ups:**
  - [Q49](#q49) Is the country handling really open-set?
  - [Q10](#q10) Why no city or state blocking keys? (The organisers rated finer-grained keys higher.)

<a id="q19"></a>
**Q19. Is 3.70 per S1 efficient, and what do you get if "per record" means per S2 or S3 record?**

- **Say this:** Our 3.70 candidates per S1 is within about 7% of the average of 3.46 true matches per S1, so there is little left to remove without losing true pairs. On the holdout about 95% of the candidate pairs are true pairs. If the organisers count per S2 or S3 record instead, 6.41M pairs over about 10M such records is about 0.64.
- **Evidence:** 6,410,308 pairs / 1,732,544 S1 = 3.70 (US 3.640, India 3.617, France 4.111) [M]; holdout: 1,901,267 − 31,304 = 1,869,963 true pairs inside a file of about 3.588 × 549,699 = 1.97M pairs, so about 95% [E, derived]; test S2 4,887,273 + S3 5,082,316 = 9,969,589 records, 6,410,308 / 9,969,589 = 0.64 [E, derived]; France is higher because it has roughly 2 to 2.5 times the uncertain pairs per S1 ([CF-47](conflicts.md)) [M]; [numbers §1](numbers.md#1-data-facts), [numbers §2](numbers.md#2-blocking-and-candidates).
- **Follow-ups:**
  - [Q12](#q12) What recall do you get with fewer candidates, say two per S1?
  - [Q14](#q14) Isn't the cut a way to look efficient on the candidate criterion?

## 3. Matching model and features

Slides 5 and 3. The jury will probe why each part exists, what it cost and whether it was gated.

<a id="q20"></a>
**Q20. What is the model architecture, end to end?**

- **Say this:** A cascade of four gradient-boosted stages, with transformers only where they are needed. Stage 0 is a cheap filter, stage 1 scores each pair, stage 2 adds context and cross-encoder scores for the uncertain band, and stage 3 re-scores records that two S1 contest. A per-S1 decision then picks the list with the best expected F0.5, and a 7B model re-checks confident predictions.
- **Evidence:** stage 0 drops about 85% of pairs (33.73 → 4.77 per test S1) and keeps 99.95% of true ones [M]; band 0.02 ≤ p1 ≤ 0.99 holds 1,490,930 test pairs [M]; cross-encoders: e5-small, -base, -large, bge-reranker-v2-m3, Qwen2.5-1.5B and 7B [M]; stage 2 reads 10,065,671 rows (g1w) [M]; the methodology's "four stages, each out of fold over three groups" is exact only for stage 3 and the cross-encoders ([CF-22](conflicts.md)); [numbers §3.6](numbers.md#36-model-shape-and-the-transfer-tests), [numbers §3.3](numbers.md#33-cross-encoder-band-aucs), components/model-stages.md, components/cross-encoders.md, [theory 06](theory/06-gradient-boosting-and-stacking.md).
- **Follow-ups:**
  - [Q21](#q21) Why XGBoost and not a neural matcher or LightGBM?
  - [Q26](#q26) Why do the cross-encoders only read the uncertain band?
  - [Q34](#q34) Why choose a set per S1 instead of a threshold, and did it always win?

<a id="q21"></a>
**Q21. Why XGBoost and not a neural matcher or LightGBM?**

- **Say this:** With about 80 hand-built features for names, addresses and house numbers, the features mattered more than the learner, and XGBoost trained two million rows by 100 features for 200 rounds in 4.6 seconds on a laptop GPU. That made iteration fast on one laptop. Neural cross-encoders came later and only on the uncertain band, where they add information the trees lack.
- **Evidence:** 2M × 100 features, 200 rounds in 4.6 s on an RTX 5070 Ti [M]; features 37 (v0) → 79 (v2) → 87 (v3) [M]; XGBoost is Apache-2.0; LightGBM stayed a gated blend option and was never needed [R]; the e5-small cross-encoder added +0.00140 [0.00131, 0.00148] [M]; [D-MDL-01](decisions/MDL.md#d-mdl-01--xgboost-on-the-gpu-not-lightgbm), [theory 06](theory/06-gradient-boosting-and-stacking.md).
- **Follow-ups:**
  - [Q22](#q22) Which features matter for noisy records?
  - [Q26](#q26) Why do the cross-encoders only read the uncertain band?

<a id="q22"></a>
**Q22. Which features matter for noisy records?**

- **Say this:** Five families: name similarity with typo tolerance and an Indic transliteration, address and house-number relations, legal-form agreement, learned look-alike word odds, and context about the competing S1. The biggest single discovery was legal forms, which our tokenizer had thrown away although look-alikes change them. Restoring them gave plus 0.0027 on the holdout.
- **Evidence:** legal-form features +0.00271 [0.00260, 0.00283], log-loss −20% [M]; signed house-number features +0.00021 [0.00016, 0.00025] [M]; learned word odds: "holdings" −9.8, "group" −9.7 [M]; counts, not rates, for frequency features ([D-FEA-03](decisions/FEA.md#d-fea-03--counts-not-rates-for-name-frequency-and-rivalry-features)); left out on purpose: country, postcode, embedding cosines ([D-FEA-02](decisions/FEA.md#d-fea-02--left-out-on-purpose-no-country-no-postcode-no-embedding-cosines)); [decision legal-form-features](../docs/decisions/2026-09-25_2142_gate-legal-form-features.md), [D-FEA-04](decisions/FEA.md#d-fea-04--features-v1-learned-indic-dictionary-typo-tolerant-names-number-set-relations-per-country-idf), [D-FEA-05](decisions/FEA.md#d-fea-05--look-alike-word-odds-learned-out-of-fold-g3-and-cluster-support-g9), [D-FEA-09](decisions/FEA.md#d-fea-09--legal-form-relation-features-lg), components/features.md, [theory 03](theory/03-string-similarity.md).
- **Follow-ups:**
  - [Q23](#q23) What are the look-alike word odds, and what did you do for words never seen in training?
  - [Q24](#q24) What does stage 2 add over stage 1?
  - [Q81](#q81) Where else is the methodology document looser than the code?

<a id="q23"></a>
**Q23. What are the look-alike word odds, and what did you do for words never seen in training?**

- **Say this:** A look-alike moves the house number and a true copy rarely does, so the share of close pairs with a moved number in which a word appears tells how look-alike that word is. For countries without labels we count that share in the country itself and map it onto the supervised scale with an isotonic fit learned on US and India. On a US-to-India test with India's words unseen, that lifted the model from 0.882 to 0.960.
- **Evidence:** leave-one-country-out on India: US-only model 0.96106 with India's words known, 0.88235 with them unseen, 0.95984 unseen with the label-free proxy, 0.94180 without look-alike odds [M]; supervised odds are out of fold ([D-FEA-05](decisions/FEA.md#d-fea-05--look-alike-word-odds-learned-out-of-fold-g3-and-cluster-support-g9)); label-free proxy odds `lop`/`lo0` ([D-FEA-11](decisions/FEA.md#d-fea-11--label-free-proxy-look-alike-odds-for-countries-without-labels-lop-lo0), [D-FRA-03](decisions/FRA.md#d-fra-03--label-free-look-alike-odds-for-words-never-seen-in-training-v4)); dual-use French words ("groupe", "france") are over-penalised and a cap on them was never decided ([D-FEA-15](decisions/FEA.md#d-fea-15--cap-the-dual-use-french-proxy-words)); [ANALYSIS_v3 §4](../experiments/ameya/model-v1/ANALYSIS_v3.md), [theory 09](theory/09-self-training-and-domain-shift.md).
- **Follow-ups:**
  - [Q39](#q39) Why was France so much worse at first?
  - [Q41](#q41) Aren't hand-written French rules overfitting?

<a id="q24"></a>
**Q24. What does stage 2 add over stage 1?**

- **Say this:** Context: how strongly other S1 claim the record, how many confident matches the S1 already has, source balance, and similarity to the S1's other confident records. It added about 0.002 on the holdout at model v1 and it is what makes the per-S1 decision work. Its output is isotonic-calibrated, which the decision layer needs.
- **Evidence:** model v1 over stage 1 with a threshold +0.001995 [0.00189, 0.00210] [M]; v2 over v1 +0.00431 [0.00418, 0.00445], which bundles blocking v1, word odds and cluster support [M]; ECE 0.00046, band ECE 0.00434 [M]; [D-MDL-03](decisions/MDL.md#d-mdl-03--stage-2-a-collective-model-over-the-full-candidate-graph-isotonic-calibrated-with-cluster-support), [D-MDL-08](decisions/MDL.md#d-mdl-08--gate-g4-keep-the-collective-stage-2-sachi), [decision gate-g4](../docs/decisions/2026-09-25_2103_gate-g4-stage2.md), [numbers §3.2](numbers.md#32-gains-that-passed-a-gate).
- **Follow-ups:**
  - [Q25](#q25) What does stage 3 do?
  - [Q34](#q34) Why choose a set per S1 instead of a threshold, and did it always win?

<a id="q25"></a>
**Q25. What does stage 3 do?**

- **Say this:** Stage 3 re-scores only the contested records, those that two or more S1 claim, using the rival S1 and both S1's confident-copy counts, and it calibrates the mass of empty-address records. It adds a small gain, about 0.00005 on the holdout. The methodology says it re-scores each pair against the other candidates of its S1, which is looser than the code.
- **Evidence:** contested = 2 or more S1 at pc ≥ 0.01; +0.000051 [0.000023, 0.000079] at v5all-c2, +0.000055 [0.000025, 0.000085] at v6all, 72 s and 1.71 GB [M]; not bit-reproducible: about 500 decisions differ across machines [M]; [CF-23](conflicts.md), [D-MDL-11](decisions/MDL.md#d-mdl-11--stage-3-joint-re-scoring-of-contested-records), [decision rules-v3-and-stage3](../docs/decisions/2026-09-26_1557_rules-v3-and-stage3.md).
- **Follow-ups:**
  - [Q96](#q96) How reproducible is your submission?
  - [Q81](#q81) Where else is the methodology document looser than the code?

<a id="q26"></a>
**Q26. Why do the cross-encoders only read the uncertain band?**

- **Say this:** Stage 1 is already almost always right outside the band: below 0.002 only 0.03 to 0.06% of pairs are true, and above 0.99, 99.98% are. So a second reader can only change decisions inside the band, which holds 1.49M of the 58.4M test pairs, about 2.6%. That fits on one H100 at about 925 pairs per second for e5-large.
- **Evidence:** band 0.02 ≤ p1 ≤ 0.99: train 1,568,554 pairs (27.2% positive), test 1,490,930, labelled holdout 389,668 [M]; e5-large about 925 pairs/s on an H100 [M]; band AUCs: p1 alone 0.9297, e5-large 0.9441, bge 0.9417, Qwen2.5-7B 0.9436 [M]; France has roughly 2 to 2.5 times the band per S1 (about 1,040 against 405 to 421 per 1000 S1, before self-training; [CF-47](conflicts.md)), so the cross-encoders decide a larger share of French pairs [M]; [D-CE-02](decisions/CE.md#d-ce-02--read-only-the-uncertain-band-with-a-cross-encoder), [numbers §3.3](numbers.md#33-cross-encoder-band-aucs), components/cross-encoders.md, [theory 08](theory/08-transformers-and-cross-encoders.md).
- **Follow-ups:**
  - [Q27](#q27) Why average the cross-encoders into one feature instead of giving each its own?
  - [Q32](#q32) Why not run the 7B on every pair?

<a id="q27"></a>
**Q27. Why average the cross-encoders into one feature instead of giving each its own?**

- **Say this:** On US and India the models agree, but on France they disagree in sign four times as often, 12% against 3%. A second stage fed separate logits learns splits where they agree and extrapolates on the French disagreements, so we give it one z-scored mean. The mean tied on the holdout and was better at separating French copies from look-alikes.
- **Evidence:** sign disagreement 12.0% France vs 3.1% US and 2.7% India; correlation 0.91 vs 0.98 [M]; holdout v7m 0.991149 vs v7c 0.991170 (a tie) [M]; French copy-vs-look-alike AUC 0.878 vs 0.874 [E]; the mix with larger cross-encoders gave +0.001112 on the public LB at v7n, our largest step [M]; e5-small's logit stays a separate stage-2 feature ([CF-35](conflicts.md)); [D-CE-11](decisions/CE.md#d-ce-11--one-z-scored-consensus-mean-instead-of-separate-logits-v7m-then-v7n), [D-CE-14](decisions/CE.md#d-ce-14--equal-z-mean-of-diverse-families-no-weight-tuning), [decision model-v7n](../docs/decisions/2026-09-26_2135_model-v7n.md).
- **Follow-ups:**
  - [Q28](#q28) Why does a weaker model like bge help the mix?
  - [Q29](#q29) You kept the e5-small cross-encoder although it failed its gate. Why?

<a id="q28"></a>
**Q28. Why does a weaker model like bge help the mix?**

- **Say this:** Its French errors are decorrelated from e5's, so it is the weakest alone on France but lifts the mean the most. Diversity beat raw strength, and we kept a labelled US and India gate so that diversity could not hide a loss elsewhere. For the same reason the 7B counts twice in the final mix.
- **Evidence:** French rule-population AUC alone: bge 0.774 vs e5-large about 0.79 to 0.80; the mix of e5-large and bge 0.829 [E]; holdout band AUC bge 0.9417 [M]; the 7B in the mix against g0: once +15e-6, twice +62e-6, three times +61e-6 (point estimates) [M]; [D-CE-09](decisions/CE.md#d-ce-09--add-bge-reranker-v2-m3-after-a-licence-check), [D-CE-14](decisions/CE.md#d-ce-14--equal-z-mean-of-diverse-families-no-weight-tuning), [D-CE-15](decisions/CE.md#d-ce-15--gate-every-new-cross-encoder-on-labelled-usindia-data-and-on-decorrelation), [D-CE-23](decisions/CE.md#d-ce-23--count-the-7b-twice-in-the-stage-2-mix-g1w).
- **Follow-ups:**
  - [Q30](#q30) The 7B is no more accurate than e5-large. Why use it?
  - [Q29](#q29) You kept the e5-small cross-encoder although it failed its gate. Why?

<a id="q29"></a>
**Q29. You kept the e5-small cross-encoder although it failed its gate. Why?**

- **Say this:** On the holdout it added plus 0.0014 against a bar of plus 0.003, but it halved French look-alike acceptances and raised singleton F0.5 from 0.991 to 0.997, and the holdout cannot see France. We recorded the exception and its reason. The larger cross-encoders later gave our biggest leaderboard step.
- **Evidence:** +0.00140 [0.00131, 0.00148]; singletons 0.99126 → 0.99742 [M]; larger e5 cross-encoders v6all → v7n +0.001112 on the public LB [M]; [D-CE-05](decisions/CE.md#d-ce-05--keep-the-e5-small-cross-encoder-although-it-missed-the-gate-bar), [decision model-v4](../docs/decisions/2026-09-26_0207_model-v4-france-and-cross-encoder.md), [D-EVL-03](decisions/EVL.md#d-evl-03--gates-every-component-must-beat-a-simpler-one-in-a-paired-bootstrap-g1g13).
- **Follow-ups:**
  - [Q58](#q58) Your gate bar was +0.002. Did anything pass it, and did you keep the bar?
  - [Q27](#q27) Why average the cross-encoders into one feature instead of giving each its own?

<a id="q30"></a>
**Q30. The 7B is no more accurate than e5-large. Why use it?**

- **Say this:** Correct, it is not: its uncertain-band AUC is 0.9436 against 0.9439 for a self-trained e5-large. Its value is independence, as a different model family in the mix and as a second reader of the 94.5% of predictions that no cross-encoder sees. Counted twice in the mix it added 62 millionths on the holdout.
- **Evidence:** band AUC 0.9436 holdout, 0.9396 out of fold [M]; 7B twice in the mix +62e-6 against g0 (point estimate); India +66.1e-6 [+19.4, +112.9], P 0.998 [M]; 94.5% of final predictions have p1 above 0.99 [M]; [D-CE-19](decisions/CE.md#d-ce-19--pull-the-model-scale-lever-qwen25-7b-on-rented-boxes-gated-by-a-reproduction-check-bakshi), [D-CE-23](decisions/CE.md#d-ce-23--count-the-7b-twice-in-the-stage-2-mix-g1w), [D-LLM-04](decisions/LLM.md#d-llm-04--train-a-7b-properly-bakshis-q7st-instead-of-prompting-one), components/llm-recheck.md, [theory 10](theory/10-llm-verification-and-compute.md).
- **Follow-ups:**
  - [Q88](#q88) Is the 7B re-check just luck?
  - [Q31](#q31) Why not just prompt an LLM?

<a id="q31"></a>
**Q31. Why not just prompt an LLM?**

- **Say this:** We tried: zero-shot Qwen2.5-7B-Instruct reached an AUC of 0.537 on the uncertain pairs against 0.898 for our own probability, and a quick fine-tune only 0.720. What worked was a properly trained, cross-fitted 7B used as a cross-encoder, which reached 0.9436. Prompting is also slow, at about 150 pairs per second.
- **Evidence:** AUC 0.537 vs 0.898, quick LoRA 0.720 [M, uncertain holdout pairs]; trained q7st 0.9436 [M]; zero-shot 145 to 170 pairs/s [M]; [D-LLM-02](decisions/LLM.md#d-llm-02--zero-shot-qwen25-7b-instruct-on-the-uncertain-pairs), [D-LLM-03](decisions/LLM.md#d-llm-03--a-quick-lora-fine-tune-of-qwen25-7b-instruct-as-a-re-scorer), [D-LLM-04](decisions/LLM.md#d-llm-04--train-a-7b-properly-bakshis-q7st-instead-of-prompting-one), [theory 10](theory/10-llm-verification-and-compute.md).
- **Follow-ups:**
  - [Q32](#q32) Why not run the 7B on every pair?
  - [Q30](#q30) The 7B is no more accurate than e5-large. Why use it?

<a id="q32"></a>
**Q32. Why not run the 7B on every pair?**

- **Say this:** At about 600 pairs per second, the 58.4M test pairs would take about 27 GPU-hours before any training. So the 7B reads only where a second opinion pays: the cross-encoder mix on the uncertain band, and the re-check of confident predictions. The 27-hour figure is an estimate; we did not run the comparison.
- **Evidence:** 58.44M / 600 per s ≈ 27 GPU-hours [E]; 7B scoring about 530 to 600 pairs/s on an H100 [M]; re-check runs: France 2 × 15 min, US/India 4 × 46 min on H100 [R]; [numbers §7](numbers.md#7-compute-runtimes-and-costs), [D-CE-19](decisions/CE.md#d-ce-19--pull-the-model-scale-lever-qwen25-7b-on-rented-boxes-gated-by-a-reproduction-check-bakshi), components/llm-recheck.md.
- **Follow-ups:**
  - [Q63](#q63) What would this cost on a billion records?
  - [Q65](#q65) How many GPU-hours did you use, and what did it cost in money?

<a id="q33"></a>
**Q33. How do you avoid leakage inside the learned features?**

- **Say this:** Every learned statistic is out of fold: a pair is scored by a model that never saw its S1 group. The Indic dictionary and the look-alike word odds come from training folds only, calibration uses out-of-fold scores, and the holdout is split by S1, not by pair. IDs and row order carry no signal.
- **Evidence:** the holdout is 25% of train S1 (549,699), chosen by a splitmix64 hash of the id ([D-EVL-01](decisions/EVL.md#d-evl-01--a-shared-deterministic-holdout-25-of-train-s1-out-of-fold-groups-a-dev-sample)) [M]; Indic dictionary of 693 entries learned on training folds only [M]; ID and row-order correlation with ownership 0.0002 and 0.0014 [M]; in the final fit the holdout later became a fourth fold, see [Q86](#q86); [RESEARCH_v5 §1](../experiments/ameya/model-v1/RESEARCH_v5.md), [theory 05](theory/05-evaluation-methodology.md).
- **Follow-ups:**
  - [Q86](#q86) Your final fit used the holdout as a fourth out-of-fold group. Isn't that training on your test set?
  - [Q85](#q85) Haven't you overfit the holdout, given how many things you tuned on it?

<a id="q34"></a>
**Q34. Why choose a set per S1 instead of a threshold, and did it always win?**

- **Say this:** The metric is F0.5 per S1, and the bar to add a record rises with the size of the list, which one flat threshold cannot express. It did not always win: on stage-1 probabilities it lost, on calibrated stage-2 probabilities it won, and in the final stack its edge is small. The decision layer as a whole gained 0.000048 over the best flat threshold on the holdout.
- **Evidence:** by model: stage 1 −0.00029; stage 2 v1 +0.00027, v2 +0.00018, v3 +0.00011, v6all +0.00004 (not significant) [M]; final layer +48.1e-6 [+7.1, +91.2], P 0.987 (set selection + crowd shift + `acr` + `cap`); set selection alone +33.2e-6 [−7.5, +75.0] [M]; out of sample +23.7e-6 (positive in 86% of splits) vs −18.8e-6 for re-tuning the threshold [M]; [CF-16](conflicts.md), [numbers §4.1](numbers.md#41-set-selection-and-break-even), [decision stacked-rules](../docs/decisions/2026-09-27_0636_stacked-rules.md), [D-DEC-01](decisions/DEC.md#d-dec-01--per-s1-expected-f05-set-selection-gated-against-a-tuned-threshold-g6), [D-DEC-08](decisions/DEC.md#d-dec-08--g6-applied-model-by-model-the-gate-picks-the-dp-or-the-threshold), [D-DEC-15](decisions/DEC.md#d-dec-15--the-stacked-decision-layer--dpc-expected-f05-with-logit-shift-crowd-shift-and-phantom-plus-acronym-adds-and-caps), [theory 04](theory/04-metrics-and-decisions.md).
- **Follow-ups:**
  - [Q78](#q78) Your document says a wrong merge costs twice a miss and that the set selection gained 0.000048. Is that exact?
  - [Q98](#q98) Your late gains are tiny, 0.00005 here and 0.0001 there. Was the complexity worth it?
  - [Q85](#q85) Haven't you overfit the holdout, given how many things you tuned on it?

## 4. Edge cases: singletons, the unseen country, noisy names and addresses

Slide 6. France is the centre of the jury's attention here: be exact about what was estimated and what was measured.

<a id="q35"></a>
**Q35. How do you handle singletons?**

- **Say this:** A business with no match scores 1.0 only if we predict nothing, so the decision layer may return an empty set, and it does when no candidate clears the expected-F0.5 bar. About 5.6% of S1 are singletons, and our output leaves 5.76% empty, close to the truth. The cross-encoder helped here: singleton F0.5 rose from 0.991 to 0.997.
- **Evidence:** truth 5.58% of S1 (holdout 30,677 of 549,699); an all-empty prediction scores 0.0558 on the holdout [M]; Composite B leaves 99,802 of 1,732,544 test S1 empty (5.76%) [M]; singletons 0.99126 → 0.99742 with the e5-small cross-encoder [M]; [D-DEC-01](decisions/DEC.md#d-dec-01--per-s1-expected-f05-set-selection-gated-against-a-tuned-threshold-g6), [D-DEC-13](decisions/DEC.md#d-dec-13--no-empty-s1-rescue), [numbers §3.4](numbers.md#34-what-the-final-model-predicts-on-test).
- **Follow-ups:**
  - [Q36](#q36) Did you try to rescue empty predictions or add recall rules?
  - [Q2](#q2) Why does F0.5 matter for the design, and how much does a wrong merge cost?

<a id="q36"></a>
**Q36. Did you try to rescue empty predictions or add recall rules?**

- **Say this:** Yes, and everything lost or tied. Under F0.5 a rule that adds pairs needs about 75% precision; the best we found was 71% and the rest ran from 17 to 59%. So we shipped no recall rules.
- **Evidence:** 31,574 empty S1 at v7n-s3, of which 30,606 are true singletons; best rescue rule +0.000021 [−0.000008, +0.000049]; adding the top free candidate is negative at every threshold (−505e-6 at pc 0.2 … −4e-6 at 0.5) [M]; tie rule −10 to −29e-6, singleton protection −33.7e-6 [M]; empty-address exact-name rule 24% true, best sibling slice 59%, 7B additions 71.4% at best (42 adds, 30 true) [M]; [D-DEC-13](decisions/DEC.md#d-dec-13--no-empty-s1-rescue), [D-RUL-17](decisions/RUL.md#d-rul-17--no-recall-add-rules), [D-LLM-08](decisions/LLM.md#d-llm-08--no-7b-driven-additions), [numbers §3.5](numbers.md#35-where-the-remaining-loss-is).
- **Follow-ups:**
  - [Q37](#q37) Where is the remaining loss on US and India, and is it fixable?
  - [Q72](#q72) What did not work?

<a id="q37"></a>
**Q37. Where is the remaining loss on US and India, and is it fixable?**

- **Say this:** About 89% of the remaining loss is missed copies, and most of those are records with an empty address whose name several S1 share. Nothing in the data says which of those S1 owns the record, so two S1 at probability 0.49 are both better left empty. That is close to the Bayes limit, and all structural priors together added only about 0.0001.
- **Evidence:** v5all loss 0.00984, misses 89%; false negatives with an empty record address 69% (37,774 of 54,573); recall 0.993 / 0.988 (US / India) with an address vs 0.54 / 0.57 without [M]; perfect ownership would give 0.99351 (+0.00335) on the holdout, and structure recovers about +0.00008 of it [M]; about 22k empty-address pairs of shared names are 95 to 100% missed [M]; final model: 97.47% of true pairs predicted, 99.9% precision [M]; [D-PRB-03](decisions/PRB.md#d-prb-03--do-not-chase-empty-address-misses-whose-name-several-s1-share-bayes-limit), [D-FEA-08](decisions/FEA.md#d-fea-08--name-uniqueness-features-rejected-empty-address-losses-are-a-data-limit), [numbers §3.5](numbers.md#35-where-the-remaining-loss-is).
- **Follow-ups:**
  - [Q36](#q36) Did you try to rescue empty predictions or add recall rules?
  - [Q73](#q73) What would you do differently?

<a id="q38"></a>
**Q38. How did you handle France, a country never seen in training?**

- **Say this:** We kept the pipeline open-set: no model uses country, and every word statistic is computed per country from the data itself. Where France had no labels we used label-free look-alike odds, rules whose truth rates we measured on US and India, stronger cross-encoders and, finally, guarded self-training. The cost was real: France was worth about 0.93 on our first models and about 0.98 by the end, estimated from the public score.
- **Evidence:** LB = 0.38274·F_US + 0.46751·F_India + 0.14975·F_France [E]; implied France ≈ 0.93 (v2, v3) → 0.971 to 0.976 (v5all) → 0.978 (v7n) → 0.984 (mixmdp) [E, public-LB algebra]; France was never measured directly ([CF-09](conflicts.md)); [D-PRB-01](decisions/PRB.md#d-prb-01--country-is-an-open-set-no-country-feature-statistics-per-exact-country-label), [D-FRA-01](decisions/FRA.md#d-fra-01--france-at-the-first-model-stage-country-agnostic-features-and-test-fitted-statistics-only), [numbers §5](numbers.md#5-france-estimates), components/france.md, [theory 09](theory/09-self-training-and-domain-shift.md).
- **Follow-ups:**
  - [Q39](#q39) Why was France so much worse at first?
  - [Q52](#q52) How can you validate anything on France with no labels?
  - [Q43](#q43) How does your self-training work?

<a id="q39"></a>
**Q39. Why was France so much worse at first?**

- **Say this:** Two feature bugs on unseen data. The legal-form bitmask took values never seen in training, so French look-alikes scored 0.456 and only 0.027 with the bits zeroed, and French look-alike words had no odds, so they looked harmless. A US-only model scores India at 0.961, and at 0.882 when India's words are unseen.
- **Evidence:** stage-1 p1 on 30,518 French pairs: 0.456 as is → 0.027 with the bits zeroed [M]; leave-one-country-out US → India: 0.96106 words known, 0.88235 unseen, 0.95984 with the label-free proxy [M]; LB 0.97961 (v3) → 0.98781 (v5all with rules) [M]; [ANALYSIS_v3 §2](../experiments/ameya/model-v1/ANALYSIS_v3.md), [ANALYSIS_v3 §3](../experiments/ameya/model-v1/ANALYSIS_v3.md), [D-FEA-10](decisions/FEA.md#d-fea-10--drop-the-legal-form-bitmasks-from-stages-02-v4), [D-FRA-03](decisions/FRA.md#d-fra-03--label-free-look-alike-odds-for-words-never-seen-in-training-v4).
- **Follow-ups:**
  - [Q23](#q23) What are the look-alike word odds, and what did you do for words never seen in training?
  - [Q40](#q40) What is an "op-B" look-alike, and how did you handle it?

<a id="q40"></a>
**Q40. What is an "op-B" look-alike, and how did you handle it?**

- **Say this:** The generator swaps one word of the S1 name for another real word at the same address and number, for example "Troupe Ecole SAS" becomes "Troupe Centre SAS". In US and India that pattern is true only 0.6% of the time, but our French statistics only caught decoys that move the number, and France accepted about 17,000 of them. A rule learned on US and India labels drops them, at a holdout cost of 0.000003.
- **Evidence:** 5,364 holdout pairs of this kind, 0.6% true; v4 France: 17,088 dropped by `post_ops` (16,971 by the probe count) [M]; truth by operation, US / India: A 99.7 / 98.3%, APP 98.9 / 99.6%, ACR 99.9 / 99.8%, B 3.1 / 0.6%, NUM 97.6 / 78.2%, CODE 42.6 / 44.0% [M]; the rules run only for countries without labels ([CF-25](conflicts.md)); [ANALYSIS_v4 §3](../experiments/ameya/model-v1/ANALYSIS_v4.md), [D-RUL-01](decisions/RUL.md#d-rul-01--france-rules-from-the-generator-drop-op-b-add-op-a-postopspy-v1-unlabelled-countries-only), [decision france-generator-ops](../docs/decisions/2026-09-26_0417_france-generator-ops-and-final-fit.md).
- **Follow-ups:**
  - [Q41](#q41) Aren't hand-written French rules overfitting?
  - [Q94](#q94) Isn't reverse-engineering the data generator a kind of leakage?

<a id="q41"></a>
**Q41. Aren't hand-written French rules overfitting?**

- **Say this:** Each rule targets a population whose truth rate we first measured on labelled US and India data with the same code: drops only below about 5% true, adds only above 98%. Rules that failed that bar, such as number edits at 70 to 98% and code typos at 43%, were not applied. The whole decision-layer stack, rules included, added about 0.000085 on the public score.
- **Evidence:** the rule lists derived without labels matched the hand lists exactly ([ANALYSIS_v4 §3](../experiments/ameya/model-v1/ANALYSIS_v4.md)); French true copies change commune in 3 of 546,465 pairs; exact-address same-name copies are 99.99% true [M]; +0.000085 public LB (v7nst 0.990179 → v7nst-dpc 0.990264) [M]; [decision france-rules-v2](../docs/decisions/2026-09-26_0626_france-rules-v2.md), [D-RUL-02](decisions/RUL.md#d-rul-02--france-rules-v2-add-app-and-acr-reject-num-and-code), [D-RUL-03](decisions/RUL.md#d-rul-03--france-rules-v3-a-robust-same-address-test), [D-RUL-14](decisions/RUL.md#d-rul-14--drop-french-look-alike-word-swaps-at-the-s1s-address-applyswapsimpy), [numbers §4.2](numbers.md#42-rules).
- **Follow-ups:**
  - [Q94](#q94) Isn't reverse-engineering the data generator a kind of leakage?
  - [Q42](#q42) French acronym matches ran at about 11 times the US/India rate. Why keep them?

<a id="q42"></a>
**Q42. French acronym matches ran at about 11 times the US/India rate. Why keep them?**

- **Say this:** A label-free size-bias test showed that S1 holding an acronym match look exactly like S1 holding true copies: the fitted false share was 0% with an interval of 0 to 1%. An independent count agreed by 14 standard errors, and dropping them would have cost about 0.0003. The rate is a trait of the French vendor data.
- **Evidence:** false share 0.00 [0.00, 0.01]; S1 holding French acronyms have 4.20 predictions against 4.36 if the acronyms were extras (14 SE); cost of dropping about −0.0003 on the LB [E]; the size-bias test, validated on the holdout (true populations score about 0, false look-alikes 0.47 at the same address), under-states the false share, so we stopped using it to value change sets [E]; 18,707 French acronym pairs (72 per 1000 S1); some notes say 14 times, the base rate differs ([CF-45](conflicts.md)); [D-FRA-19](decisions/FRA.md#d-fra-19--keep-the-french-acronym-matches-no-noacr-upload-the-size-bias-test), [D-RUL-06](decisions/RUL.md#d-rul-06--french-acronym-join-unlabelled-countries-only).
- **Follow-ups:**
  - [Q52](#q52) How can you validate anything on France with no labels?
  - [Q76](#q76) How reliable were your label-free estimators for France?

<a id="q43"></a>
**Q43. How does your self-training work?**

- **Say this:** We label only confident French decisions (probability at least 0.9 or at most 0.05), abstain in between, and let the rules override the labels. The models are cross-fitted by S1 group, so no French pair is scored by a model that saw its label, and calibration and early stopping use only US and India labels. We stopped after two rounds, because an unguarded second round drifted and a third lost on the leaderboard.
- **Evidence:** round 1: v7n → v7nst +0.000458 on the public LB with the US/India part unchanged to 0.00002, so France about +0.0031 [M]; round 2 with French decision layers: mixmdp +0.000154 (US/India +20e-6, France +134e-6) [M]; round 3 (mixf7) −46e-6 against Composite B [M]; the final used several runs with different label sets ([CF-28](conflicts.md)); labels from 1.43M French stage-2 rows [M]; [D-FRA-13](decisions/FRA.md#d-fra-13--self-train-on-france-with-cross-fitted-pseudo-labels-v7nst), [D-FRA-16](decisions/FRA.md#d-fra-16--stop-unguarded-self-training-at-round-1-withdraw-frs2), [D-FRA-18](decisions/FRA.md#d-fra-18--guarded-round-2-stage-2-labels-at-weight-3), [D-FRA-22](decisions/FRA.md#d-fra-22--no-round-2-self-training-of-the-cross-encoders), [D-FRA-24](decisions/FRA.md#d-fra-24--round-3-as-a-candidate-round-4-not-used), components/france.md, [theory 09](theory/09-self-training-and-domain-shift.md).
- **Follow-ups:**
  - [Q44](#q44) You rejected self-training, then made it a core part. Why?
  - [Q87](#q87) How do you know self-training did not just reinforce its own mistakes?
  - [Q45](#q45) Why did self-training stop after two rounds?

<a id="q44"></a>
**Q44. You rejected self-training, then made it a core part. Why?**

- **Say this:** The first test, on a US-to-India stand-in with India's words unseen, lost: 0.882 fell to 0.831 as the model learned its own confident mistakes. By the next evening we had label-free look-alike odds, rules and stronger cross-encoders, the labels came from cross-fitted decisions, and the leaderboard showed a gain of 0.000458. The verdict changed with the evidence, and we do not claim it always worked.
- **Evidence:** leave-one-out ladder, words unseen: 0.88235 → 0.8512 → 0.83075 → 0.823; words known: 0.96106 → 0.9637 → 0.96479 → 0.96498 [M]; re-test on the current model +0.0009 (3 seeds), judged too small at the time [M]; round 1 +0.000458 on the public LB [M]; no decision record covers the reversal, and the holdout could not gate it ([CF-50](conflicts.md)); [D-FRA-02](decisions/FRA.md#d-fra-02--self-training-on-france-first-rejection-confirmation-bias-in-the-loco-test), [D-FRA-11](decisions/FRA.md#d-fra-11--second-rejection-of-self-training-retrain-judged-too-small), [D-FRA-13](decisions/FRA.md#d-fra-13--self-train-on-france-with-cross-fitted-pseudo-labels-v7nst), [ANALYSIS_v3 §3](../experiments/ameya/model-v1/ANALYSIS_v3.md).
- **Follow-ups:**
  - [Q45](#q45) Why did self-training stop after two rounds?
  - [Q87](#q87) How do you know self-training did not just reinforce its own mistakes?

<a id="q45"></a>
**Q45. Why did self-training stop after two rounds?**

- **Say this:** Each round recycles our own decisions: the French gain roughly halved every round, an unguarded second round drifted by dropping clear copies, and round three lost 0.000046 on the leaderboard. More gain needs information from outside the model. Retraining the cross-encoders on round-2 labels also made France worse.
- **Evidence:** French part of each LB step 780 → 470 → 240 → 130 (e-6) [E]; unguarded round 2: copies lost −1.54 per 1000 French S1, holdout flat (0.991187 vs 0.991194) [M]; round 3 mixf7 0.990833 vs Composite B 0.990879, while `cal` had predicted +69e-6 [M]; raising the pseudo-label weight from ×3 to ×5 changed nothing [M]; [D-FRA-16](decisions/FRA.md#d-fra-16--stop-unguarded-self-training-at-round-1-withdraw-frs2), [D-FRA-22](decisions/FRA.md#d-fra-22--no-round-2-self-training-of-the-cross-encoders), [D-FRA-24](decisions/FRA.md#d-fra-24--round-3-as-a-candidate-round-4-not-used), [LB 2026-09-27 #05](../submissions/records/2026-09-27_sub05.md).
- **Follow-ups:**
  - [Q76](#q76) How reliable were your label-free estimators for France?
  - [Q73](#q73) What would you do differently?

<a id="q46"></a>
**Q46. How did you handle Indic scripts without external data?**

- **Say this:** With our own transliteration: one table of code-point offsets for nine scripts, consonant skeletons, and a 693-word dictionary learned from training pairs. Indic-name S1 went from 0.923 to parity with Latin names. We considered IndicXlit, saw that it was trained on external data, and did not use it.
- **Evidence:** dictionary learned on train folds 5 to 19 only; 752,869 Indic names transliterated in 3.8 s [M]; Indic scripts in 18.3% of India true pairs [M]; India retrieval recall v0 0.9590 → v1 0.9836 [M]; [D-NRM-02](decisions/NRM.md#d-nrm-02--our-own-indic-transliteration-skeletons-and-learned-dictionary-no-external-transliterator), [D-BLK-07](decisions/BLK.md#d-blk-07--blocking-v1-learned-indic-dictionary-in-the-name-keys-character-4-grams-in-the-name-only-view), components/normalisation.md.
- **Follow-ups:**
  - [Q92](#q92) Did you use any external data, geocoders or web lookups?
  - [Q17](#q17) Where does retrieval still miss, and why not reach the planned 99.5%?

<a id="q47"></a>
**Q47. What were the French decoys that the 7B caught?**

- **Say this:** Same generic name, same house number, different street. On US and India our feature model already rejects that pattern; in France the names are shared by a median of 43 S1, so the pairs passed stage 1 at high probability. The 7B scores them like the US and India decoys.
- **Evidence:** where our model predicted the pattern it was 99.7% true (n = 380); where it rejected it, 0.5% true (n = 218, 202 of 218 below −6) [M]; about 78% of the French rejects follow the pattern; 747 of 859 rejected S1 have generic names [M]; [D-LLM-06](decisions/LLM.md#d-llm-06--gate-the-drop-on-the-7b-not-on-the-pattern-same-name--same-number--different-street), [numbers §4.3](numbers.md#43-the-7b-re-check-of-confident-predictions).
- **Follow-ups:**
  - [Q88](#q88) Is the 7B re-check just luck?
  - [Q48](#q48) What is France's weakness, concretely?

<a id="q48"></a>
**Q48. What is France's weakness, concretely?**

- **Say this:** Not the counts: France's share of empty predictions, copies per S1 and source split look like US and India. It is which records we pick: generic association names, such as clubs, schools and amicales, at shared addresses. About 11% of French S1 share an exact address with another S1, against 4 to 6% in US and India.
- **Evidence:** French predictions 3.354 per S1, empty share 5.81% against a holdout truth of 5.54 to 5.60% [M]; S1 sharing an exact address: France 11.1% (largest group 101) vs US 5.62%, India 4.84% [M] (other measurements 10.7% and 8.5%, [CF-40](conflicts.md)); morning of 27 Sep: a leader at 0.991483 implied France about 0.990 if its US/India matched ours, against our 0.981 to 0.982 [E]; [D-FRA-07](decisions/FRA.md#d-fra-07--no-fix-for-weak-address-and-unrelated-name-families-the-first-france-estimate-withdrawn), [numbers §5](numbers.md#5-france-estimates).
- **Follow-ups:**
  - [Q47](#q47) What were the French decoys that the 7B caught?
  - [Q62](#q62) What was the gap to the top, and why?

<a id="q49"></a>
**Q49. Is the country handling really open-set?**

- **Say this:** No model uses country as a feature, and the package reads the labelled countries from the training records and treats every other country as unlabelled. A few late rule scripts do name France, the one unlabelled country in test. So the models are open-set; the last-day rule scripts are not fully.
- **Evidence:** `stk/dp_france.py`, `box/rescore_export.py`, `box/fr_drop_ladder.py` and `mv1/fhs.py` filter on country == "France"; the as-run `apply_combo.py` hard-coded ("US", "India") ([CF-26](conflicts.md)) [M]; test has exactly US, India and France [M]; [D-PRB-01](decisions/PRB.md#d-prb-01--country-is-an-open-set-no-country-feature-statistics-per-exact-country-label), [D-BLK-02](decisions/BLK.md#d-blk-02--partition-the-search-by-the-exact-country-label-never-by-state).
- **Follow-ups:**
  - [Q18](#q18) Why partition by country, and does it stay open to a new country?
  - [Q92](#q92) Did you use any external data, geocoders or web lookups?

## 5. Results and evaluation

Slide 7. Always name the evaluation: local holdout (US and India, no France), public LB, or private LB. Never quote a private score: none exists.

<a id="q50"></a>
**Q50. What are your key results?**

- **Say this:** Our submission, Composite B, scored 0.990879 on the public leaderboard, and its model scores 0.9913 on our US and India holdout, which has no France. We placed 2nd of the Top 10 finalists out of more than 32,000 teams, and the organisers publish rankings only, so we have no private score to quote. On the public board we climbed from 0.97608 on our first recorded upload to 0.990879.
- **Evidence:** public LB 0.990879 (Composite B, 27 Sep #04) [M]; holdout g1w 0.991323 (US 0.991114, India 0.991635), precision 99.9%, recall 97.5% [M]; Top 10 of 32,000+ teams, 2nd on the list [R, organisers' e-mail]; +0.014799 over 13 scored uploads [M]; [LB 2026-09-27 #04](../submissions/records/2026-09-27_sub04.md), [numbers §6](numbers.md#6-leaderboard-history), [numbers §3.1](numbers.md#31-local-holdout-version-by-version).
- **Follow-ups:**
  - [Q51](#q51) Your local score is 0.9913 and the leaderboard 0.990879. Why the gap, and how did you find out?
  - [Q54](#q54) What was your private leaderboard score, and where did you rank?
  - [Q60](#q60) Walk us through the leaderboard steps. Which changes mattered?

<a id="q51"></a>
**Q51. Your local score is 0.9913 and the leaderboard 0.990879. Why the gap, and how did you find out?**

- **Say this:** The holdout is US and India only, France has no labels so it cannot be in it, and most of the gap is France. Our first models scored 0.989 locally and 0.980 on the board; US and India behaved like the holdout on every label-free check, so back-solving the weighted score put France near 0.93. Fixing France brought it to about 0.98.
- **Evidence:** v2 0.98436 vs 0.97608 (−0.0083), v3 0.98882 vs 0.97961 (−0.0092), v5all −0.0024 [M]; weights US 0.38274, India 0.46751, France 0.14975 [M]; implied France about 0.93 (v3), 0.978 (v7n), 0.984 (mixmdp) [E, assumes US/India score like the re-weighted holdout]; other suspects measured negligible: US pool size (+0.02 predictions per S1, correct reassignments), crowding (−0.00009), the file path (rescoring from raw strings gave the same 0.98882) [M]; [CF-09](conflicts.md), [RESEARCH_v5 §1](../experiments/ameya/model-v1/RESEARCH_v5.md), [RESEARCH_v6 §1](../experiments/ameya/model-v1/RESEARCH_v6.md), [D-EVL-07](decisions/EVL.md#d-evl-07--attribute-the-leaderboard-gap-to-france), [D-EVL-08](decisions/EVL.md#d-evl-08--estimate-france-by-leaderboard-arithmetic), [D-EVL-17](decisions/EVL.md#d-evl-17--lead-with-the-public-leaderboard-score-label-09913-as-local-validation).
- **Follow-ups:**
  - [Q52](#q52) How can you validate anything on France with no labels?
  - [Q79](#q79) Is 0.9913 the score of what you submitted, and did you "never train on the holdout"?
  - [Q53](#q53) You never measured France. Why should we believe 0.98?

<a id="q52"></a>
**Q52. How can you validate anything on France with no labels?**

- **Say this:** Three ways: a labelled stand-in (train on US, test on India with India's words hidden), label-free tests built from the generator's invariants, and leaderboard uploads that change France alone, read through the weighted-score arithmetic. The labelled holdout judged everything else. We state the limit plainly: France was never measured directly.
- **Evidence:** LB ≈ 0.8423 + 0.14975 × F_France with US/India at the holdout level [E]; France-only packages keep US/India byte-identical, so the LB difference is France alone [M]; label-free checks: sum of pc per S1 near 3.46, one owner per record, rule-population AUC (0.855 → 0.872 matched France 0.973 → 0.978) and the size-bias test [E]; a forecast that hit: v7n was predicted at 0.9894 to 0.9900 and scored 0.989721 [M]; the France-emptied probe was packaged five times and never uploaded ([D-EVL-06](decisions/EVL.md#d-evl-06--the-france-emptied-probe-fr0-and-its-relatives-packaged-never-uploaded), [D-FRA-12](decisions/FRA.md#d-fra-12--france-probes-empty-france-threshold-cuts-lower-threshold-built-never-uploaded)); [D-EVL-05](decisions/EVL.md#d-evl-05--label-free-france-forecasts-are-diagnostics-not-measurements), [D-EVL-11](decisions/EVL.md#d-evl-11--the-rule-population-auc-as-the-label-free-yardstick-for-france), [D-EVL-12](decisions/EVL.md#d-evl-12--fhspy-replaces-the-saturated-rule-population-auc), [D-EVL-15](decisions/EVL.md#d-evl-15--trust-the-leaderboard-over-our-estimators), [numbers §5](numbers.md#5-france-estimates).
- **Follow-ups:**
  - [Q76](#q76) How reliable were your label-free estimators for France?
  - [Q53](#q53) You never measured France. Why should we believe 0.98?
  - [Q89](#q89) Did you overfit the public leaderboard?

<a id="q53"></a>
**Q53. You never measured France. Why should we believe 0.98?**

- **Say this:** Treat it as an estimate. It rests on two assumptions, that US and India score on test like the re-weighted holdout and that the public subset has the test's country mix, and it moved the right way with every France-only change. A France-emptied probe would have measured it directly; we built it but spent the upload slots on improvements.
- **Evidence:** sensitivity: v5all France ≈ 0.971 if US/India score like the holdout, ≈ 0.987 if they sit 0.002 below [E]; one teammate's "about 0.9886" for Composite B is not quotable [E]; [CF-09](conflicts.md), [numbers: not to quote](numbers.md#numbers-not-to-quote-and-why) #11, [numbers §5](numbers.md#5-france-estimates).
- **Follow-ups:**
  - [Q73](#q73) What would you do differently?
  - [Q76](#q76) How reliable were your label-free estimators for France?

<a id="q54"></a>
**Q54. What was your private leaderboard score, and where did you rank?**

- **Say this:** The organisers publish rankings only, so we have no private score and will not estimate one. We were ranked 2nd among the Top 10 finalists. Our public score, 0.990879, is the number we can stand behind.
- **Evidence:** final standing: Top 10 of 32,000+ teams, 2nd on the list [R] ([numbers §6](numbers.md#6-leaderboard-history)); never estimate a private score ([numbers: not to quote](numbers.md#numbers-not-to-quote-and-why) #4); public rank at upload was 15, 8, 7, 12 and 16, and fell to the high teens as others improved (7th to 20th on the evening of 27 Sep); what lifted us to 2nd is not documented ([CF-10](conflicts.md)).
- **Follow-ups:**
  - [Q55](#q55) Which of your uploads was ranked on the private board?
  - [Q50](#q50) What are your key results?

<a id="q55"></a>
**Q55. Which of your uploads was ranked on the private board?**

- **Say this:** We do not know, and it is not ours to settle: the portal text can be read as the last upload or the best one. Our package is Composite B at 0.990879; the last portal upload was B7, a French-only variant at 0.990875, which tied it on the public board. The two differ by 0.000004, inside the noise.
- **Evidence:** [CF-01](conflicts.md), [CF-03](conflicts.md); B 0.990879 (#04, about 20:55), B7 0.990875 (#07, about 23:40) [M]; B7 differs from B only in France (+251 / −1,699 pairs) [M]; public noise about ±0.00004 to 0.00005 between near-identical candidates [E]; [LB 2026-09-27 #07](../submissions/records/2026-09-27_sub07.md), [LB 2026-09-27 #04](../submissions/records/2026-09-27_sub04.md), [D-SUB-25](decisions/SUB.md#d-sub-25--the-last-hours-no-switch-away-from-composite-b), [D-SUB-26](decisions/SUB.md#d-sub-26--the-last-slot-b-or-b7).
- **Follow-ups:**
  - [Q89](#q89) Did you overfit the public leaderboard?
  - [Q54](#q54) What was your private leaderboard score, and where did you rank?

<a id="q56"></a>
**Q56. How is your holdout designed, and why?**

- **Say this:** It is a fixed 25% of the labelled US and India S1, chosen by a hash of the S1 id, so every machine gets the same split with no file sharing. We split entities, not pairs, because the metric and the stage-2 features are per S1. At 549,699 S1, paired differences have 95% intervals of about plus or minus 0.0001.
- **Evidence:** 549,699 S1 (US 329,717, India 219,982) and 1,901,267 true pairs [M]; splitmix64 hash of the S1 id ([D-EVL-01](decisions/EVL.md#d-evl-01--a-shared-deterministic-holdout-25-of-train-s1-out-of-fold-groups-a-dev-sample)) [R]; scores are reported per country as well; the holdout has no France, and thresholds and shifts were tuned on it ([Q85](#q85)); [theory 05](theory/05-evaluation-methodology.md), components/evaluation.md.
- **Follow-ups:**
  - [Q57](#q57) How does the paired bootstrap work, and why do you trust it?
  - [Q86](#q86) Your final fit used the holdout as a fourth out-of-fold group. Isn't that training on your test set?

<a id="q57"></a>
**Q57. How does the paired bootstrap work, and why do you trust it?**

- **Say this:** We resample S1 with replacement and compute the difference in F0.5 between two systems on the same resamples, so shared noise cancels and a small gain can still have a tight interval. A gain was kept only when its interval was above zero and, for late rules, positive on both fixed halves. Where the interval touched zero we said so, as for the set selection alone.
- **Evidence:** stage 2 over stage 1 +0.001995 [0.00189, 0.00210]; legal forms +0.00271 [0.00260, 0.00283] [M]; final layer +48.1e-6 [+7.1, +91.2], half A +7.7, half B +108.7, parameters picked on one half and confirmed on the other [M]; set selection alone +33.2e-6 [−7.5, +75.0] [M]; `ber.eval.gates` ([D-EVL-03](decisions/EVL.md#d-evl-03--gates-every-component-must-beat-a-simpler-one-in-a-paired-bootstrap-g1g13)); [theory 05](theory/05-evaluation-methodology.md).
- **Follow-ups:**
  - [Q58](#q58) Your gate bar was +0.002. Did anything pass it, and did you keep the bar?
  - [Q85](#q85) Haven't you overfit the holdout, given how many things you tuned on it?

<a id="q58"></a>
**Q58. Your gate bar was +0.002. Did anything pass it, and did you keep the bar?**

- **Say this:** Early components cleared it, such as legal forms at plus 0.0027. At 0.99 the remaining gains were 10 to 100 times smaller than the bar, so in practice we required a positive interval and, for late rules, positive on both halves, with ties going to the simpler option. We did not write that change of rule down as a decision record at the time.
- **Evidence:** bar MIN_GAIN = 0.002 (0.003 for heavy parts) in `ber/eval/gates.py`; model v1 printed `keep: False` at +0.001995 yet was used; later accepted gains ran from +0.00005 to +0.0006 with CI above zero [M]; [CF-36](conflicts.md), [D-EVL-03](decisions/EVL.md#d-evl-03--gates-every-component-must-beat-a-simpler-one-in-a-paired-bootstrap-g1g13), [D-EVL-04](decisions/EVL.md#d-evl-04--model-v1-for-submission-2-although-the-gate-printed-keep-false), [D-CE-05](decisions/CE.md#d-ce-05--keep-the-e5-small-cross-encoder-although-it-missed-the-gate-bar).
- **Follow-ups:**
  - [Q29](#q29) You kept the e5-small cross-encoder although it failed its gate. Why?
  - [Q85](#q85) Haven't you overfit the holdout, given how many things you tuned on it?

<a id="q59"></a>
**Q59. What do precision and recall look like, and how does F0.5 trade them?**

- **Say this:** On the holdout our predictions are 99.9% precise and recall 97.5% of true pairs, which is the right shape for F0.5: a false merge is expensive, a miss is cheap. Precision rose from 0.990 at the baseline to 0.999 while recall rose from 0.935 to 0.974, so both moved. The remaining loss is recall, and most of it is unreachable ownership ties.
- **Evidence:** baseline v0 0.9683 (precision 0.9898, recall 0.9347); v3 0.98882 (0.99833, 0.96893); v6all 0.990788 (0.9987, 0.9738); v7ce3 (0.9991, 0.9735) [M]; final recall 97.47% of 1,901,267 true pairs [M]; one recovered missed pair is worth +1.6e-7, one removed false pair +4.7e-7 [M]; [numbers §3.1](numbers.md#31-local-holdout-version-by-version), [numbers §3.5](numbers.md#35-where-the-remaining-loss-is), [numbers §4.1](numbers.md#41-set-selection-and-break-even).
- **Follow-ups:**
  - [Q2](#q2) Why does F0.5 matter for the design, and how much does a wrong merge cost?
  - [Q37](#q37) Where is the remaining loss on US and India, and is it fixable?

<a id="q60"></a>
**Q60. Walk us through the leaderboard steps. Which changes mattered?**

- **Say this:** The biggest steps were the larger cross-encoders (plus 0.001112), the day-two bundle of blocking repairs, stage 3 and rules v3 (plus 0.000799), and French self-training (plus 0.000458). The last three were small: the model mix plus 0.000281, Composite B plus 0.000180 and the French decision layers plus 0.000154. Only the self-training step is clean; the others bundle several changes.
- **Evidence:** public LB: 0.97608 (v2) → 0.97961 (v3) → 0.98781 (v5all) → 0.988609 (v6all) → 0.989721 (v7n) → 0.990179 (v7nst) → 0.990264 (decision stack) → 0.990545 (v7sq-dpc) → 0.990699 (mixmdp) → 0.990879 (Composite B) [M]; steps bundle changes ([CF-29](conflicts.md), [numbers: not to quote](numbers.md#numbers-not-to-quote-and-why) #12 and #13); [numbers §6](numbers.md#6-leaderboard-history).
- **Follow-ups:**
  - [Q43](#q43) How does your self-training work?
  - [Q61](#q61) How noisy is the public leaderboard, and how did you handle it?

<a id="q61"></a>
**Q61. How noisy is the public leaderboard, and how did you handle it?**

- **Say this:** Noise between near-identical candidates is about plus or minus 0.00004, and a simulated 25% public split has a standard deviation of 0.000164, larger than most of our late gains. So we preferred one-change uploads and labelled holdout checks, and treated gaps under about 0.00005 as ties.
- **Evidence:** ±0.00004 to 0.00005; sd 0.000164 for a 25% split, simulated on the local holdout [E]; uploads were designed to isolate one change, with a written prediction first [M]; [RESEARCH_v6 §6.15](../experiments/ameya/model-v1/RESEARCH_v6.md), [D-SUB-12](decisions/SUB.md#d-sub-12--27-sep-upload-discipline-no-pure-probes-one-change-per-upload-the-best-last), [D-SUB-15](decisions/SUB.md#d-sub-15--spend-upload-2-on-v7nst-dpc-as-a-controlled-comparison).
- **Follow-ups:**
  - [Q89](#q89) Did you overfit the public leaderboard?
  - [Q55](#q55) Which of your uploads was ranked on the private board?

<a id="q62"></a>
**Q62. What was the gap to the top, and why?**

- **Say this:** On the afternoon of 27 September the leader at 0.991829 was about 0.0011 above our best then, 0.990699. By our estimate that is roughly what France at parity with US and India would be worth, so the leaders had largely solved France and our US and India were not the gap. We cannot verify that, because France cannot be measured.
- **Evidence:** leader 0.991829 at about 16:40 on 27 Sep [R]; if the leaders' US/India matched ours, their France was about 0.990 against our 0.981 to 0.982 [E]; after checking for hidden levers we told the captain 0.993 and 0.992 were out of reach ([D-SUB-19](decisions/SUB.md#d-sub-19--check-for-hidden-levers-then-say-0993-and-0992-are-out-of-reach)); [numbers §5](numbers.md#5-france-estimates), [numbers §6](numbers.md#6-leaderboard-history).
- **Follow-ups:**
  - [Q37](#q37) Where is the remaining loss on US and India, and is it fixable?
  - [Q95](#q95) Did you find any leak, such as IDs, row order or hidden fields?

## 6. Scalability and efficiency

Slide 8. Most of this is design reasoning: we ran 24M records, not a billion. Say that first, then give the measured per-stage numbers.

<a id="q63"></a>
**Q63. What would this cost on a billion records?**

- **Say this:** We did not run it, so this is design reasoning: the expensive parts only touch a shrinking share of pairs. Retrieval is an inverted-index search per country, gradient boosting scores the few pairs per S1 that survive, cross-encoders read about 2.6% of them, and the 7B only where a second opinion pays. Every statistic is per country and every decision is per S1, so the work splits by country and by S1 group.
- **Evidence:** measured funnel per test S1: 33.73 → 4.77 → 3.70 pairs [M]; running the 7B on every pair would take about 27 GPU-hours at our scale [E]; at 100 times the data the design is untested ("not measured here"); what would need work: rarer compound keys and a learned pre-ranker in front of stage 0, pool-size-aware features, a large-memory machine for stage 2 [design reasoning, U]; [numbers §2](numbers.md#2-blocking-and-candidates), [numbers §7](numbers.md#7-compute-runtimes-and-costs), components/model-stages.md, components/process-and-infra.md, [theory 11](theory/11-scaling-to-billions.md).
- **Follow-ups:**
  - [Q64](#q64) What does each stage cost?
  - [Q66](#q66) How does blocking scale?
  - [Q70](#q70) What breaks first if the data grows 100 times?

<a id="q64"></a>
**Q64. What does each stage cost?**

- **Say this:** On one 24-core laptop with a 12 GB GPU, blocking takes about 16 minutes per split, features about an hour, stage 1 about 16 minutes and stage 2 about 24. The e5-small cross-encoder took about 35 minutes on the laptop and e5-large about an hour on an H100. The whole v6all pipeline ran in about three hours.
- **Evidence:** v6all end to end about 3 h (blocking 2 × 16 min, features 60, stage 1 16, cross-encoder 35, stage 2 24) [M]; stage 3 72 s and 1.71 GB [M]; e5-large about 61 min on a shared H100; 7B about 2 h on 3 H100 [R]; France block of the package about 4.5 h; a clean end-to-end run of the final chain estimated at 6 to 7 h [R]; memory peaks 18 to 19 GB [M]; [numbers §7](numbers.md#7-compute-runtimes-and-costs), components/process-and-infra.md.
- **Follow-ups:**
  - [Q65](#q65) How many GPU-hours did you use, and what did it cost in money?
  - [Q67](#q67) What are the memory and hardware limits?

<a id="q65"></a>
**Q65. How many GPU-hours did you use, and what did it cost in money?**

- **Say this:** The 7B adapters took about 2 hours on 3 H100s, e5-large about an hour on an H100, and the 7B re-check about 15 minutes for France and 46 minutes per US-and-India chunk. We rented H100 and RTX 5090 boxes by the hour, at single-digit dollars per session by our estimate, but we do not have the exact total. Everything else ran on one laptop.
- **Evidence:** estimates: on-demand H100 session about $5 to 8, A100 job about $3.5 to 4, RTX 4090 about $0.30 to 0.50 per hour [E]; the total spend is not recorded ([CF-12](conflicts.md)); 7B re-check: France 2 × 15 min, US/India 4 × 46 min on H100 [R]; two interruptible boxes were lost on 26 Sep ([Q84](#q84)); [numbers §7](numbers.md#7-compute-runtimes-and-costs).
- **Follow-ups:**
  - [Q32](#q32) Why not run the 7B on every pair?
  - [Q84](#q84) What happened when a GPU box died?

<a id="q66"></a>
**Q66. How does blocking scale?**

- **Say this:** It is an inverted index per country, so cost grows with the number of postings, not with the square of the records, and countries run independently. For us the whole test set took about 16 minutes on a laptop. At a billion records we would add rarer compound keys and a learned pre-ranker in front of stage 0, and shard by country; we have not measured those.
- **Evidence:** 938 s test, 952 s train; Bakshi's box 11 and 15 min [M]; 24 to 31% of S1 lists hit the cap of 15 on test [M]; Plan A's learned pre-ranker was deferred ([D-BLK-03](decisions/BLK.md#d-blk-03--heuristic-trim-top-15-per-s1-or-top-4-per-record-no-learned-pre-ranker-in-v0)); the scale-up steps are design reasoning, not measured [U]; [theory 02](theory/02-blocking.md), [theory 11](theory/11-scaling-to-billions.md).
- **Follow-ups:**
  - [Q10](#q10) Why no city or state blocking keys? (The organisers rated finer-grained keys higher.)
  - [Q63](#q63) What would this cost on a billion records?

<a id="q67"></a>
**Q67. What are the memory and hardware limits?**

- **Say this:** Stage 2 peaks at 16 to 19 GB, the full feature table is about 19 GB, and we ran the tabular pipeline at full scale on one 31 GB laptop with a 12 GB GPU. Teammates with 8 to 16 GB machines worked on a 110k-S1 dev sample, so code moved and data stayed put. The laptop froze once on the last day from memory exhaustion, and after that we ran one heavy job at a time behind a memory guard.
- **Evidence:** stage 2 16.5 to 19 GB, stages 1 to 3 peak 18 to 19 GB [M]; devkit-v0 180 MB and devkit-v2 384 MB [M]; the freeze was at 03:35 in the logs (03:21 in the Windows event log, [CF-49](conflicts.md)); atomic writes meant nothing was lost [M]; [D-ORG-04](decisions/ORG.md#d-org-04--roles-machines-and-tasks-as-issues-code-moves-data-doesnt), [D-ORG-07](decisions/ORG.md#d-org-07--run-heavy-jobs-one-at-a-time-add-a-lean-test-only-scoring-mode), [D-ORG-19](decisions/ORG.md#d-org-19--after-the-crash-one-heavy-job-at-a-time-a-15-gb-memory-guard-a-pause-flag).
- **Follow-ups:**
  - [Q68](#q68) What parallelises and what does not?
  - [Q70](#q70) What breaks first if the data grows 100 times?

<a id="q68"></a>
**Q68. What parallelises and what does not?**

- **Say this:** Statistics are per country and decisions are per S1, so retrieval, scoring and the decision layer split naturally by country and S1 group. What did not parallelise for us was stage 2: its features are about 12 GB and a rented box took data at about 3 MB per second, so it stayed on the laptop. The 7B trained one out-of-fold group per GPU.
- **Evidence:** 7B: one out-of-fold group per GPU, about 2 h on 3 H100 [R]; a later box took about 3 MB/s, so slim band-only records (119 MB instead of 1.08 GB) were sent; traffic cap 30 GB [R]; [D-ORG-15](decisions/ORG.md#d-org-15--rent-gpus-for-larger-cross-encoders-upload-only-records-and-band-pairs-stage-2-stays-local), [D-ORG-20](decisions/ORG.md#d-org-20--stop-the-rented-h100-once-every-output-is-safe-keep-stage-2-on-the-laptop), [numbers §7](numbers.md#7-compute-runtimes-and-costs).
- **Follow-ups:**
  - [Q74](#q74) What would you do with more compute or more time?
  - [Q67](#q67) What are the memory and hardware limits?

<a id="q69"></a>
**Q69. What hardware does it take to rerun your pipeline?**

- **Say this:** The CPU stages need 24 or more cores and 32 GB of RAM, and in the code the XGBoost stages use a CUDA device, so the whole chain needs a CUDA GPU. The cross-encoders need one 80 GB H100 and the 7B three 80 GB GPUs. A rerun lands within about plus or minus 0.0001 and is not byte-identical.
- **Evidence:** peak 18 to 19 GB; clean end-to-end run estimated at 6 to 7 h [R]; 15 packages pinned [M]; the package README says CPU or GPU, the code says CUDA ([CF-37](conflicts.md)); [numbers §8](numbers.md#8-package-and-reproducibility), components/packaging.md.
- **Follow-ups:**
  - [Q96](#q96) How reproducible is your submission?
  - [Q63](#q63) What would this cost on a billion records?

<a id="q70"></a>
**Q70. What breaks first if the data grows 100 times?**

- **Say this:** Three things, in this order: count-based features, stage-2 memory and the per-S1 candidate volume. We saw the first in miniature: the US test pool was half the size of train's, which moved name-rarity counts and gave 0.02 extra predictions per S1, traced to correct reassignments that are no longer ties. At 100 times the pool we would normalise by pool size and move stage 2 to a large-memory machine.
- **Evidence:** US test pool about half of train's; unique-name S1 share 53.6% vs 61.3%; +0.020 predictions per S1 on US test vs the holdout [M counts, E cause]; counts chosen over rates for stability ([D-FEA-03](decisions/FEA.md#d-fea-03--counts-not-rates-for-name-frequency-and-rivalry-features)); pool-size features left as they are ([D-FEA-12](decisions/FEA.md#d-fea-12--pool-size-dependent-rarity-and-rival-features-left-as-they-are)); stage 2 features 12 to 19 GB [M]; not measured at 100 times; [RESEARCH_v6 §1](../experiments/ameya/model-v1/RESEARCH_v6.md), [theory 11](theory/11-scaling-to-billions.md).
- **Follow-ups:**
  - [Q63](#q63) What would this cost on a billion records?
  - [Q67](#q67) What are the memory and hardware limits?

<a id="q71"></a>
**Q71. Where did extra compute pay, and where not?**

- **Say this:** The first rented GPUs paid most: the larger e5 cross-encoders were our single biggest leaderboard step, plus 0.001112. The 7B stage added about 0.00018 in the final package, roughly 0.0001 of it from French drops by our estimate. Beyond that GPUs were not the bottleneck, our serial laptop chain and the upload slots were, so we rented more only when a concrete job existed.
- **Evidence:** v6all → v7n +0.001112 (about +0.00033 US/India by the holdout, the rest France) [M]; Composite B +0.000180 over mixmdp [M], of which French drops about +0.00011 (Bakshi's split) or +0.00014 (record) [E] ([CF-30](conflicts.md)); a 4×H100 7B run was estimated at +0.00003 to +0.0001 [E]; about 4.7 h idle on 26 Sep waiting for approval [M]; [D-ORG-22](decisions/ORG.md#d-org-22--decline-extra-gpu-instances-until-a-concrete-job-existed), [D-ORG-15](decisions/ORG.md#d-org-15--rent-gpus-for-larger-cross-encoders-upload-only-records-and-band-pairs-stage-2-stays-local), [D-CE-06](decisions/CE.md#d-ce-06--rent-gpus-for-stronger-more-diverse-cross-encoders-on-demand-not-spot).
- **Follow-ups:**
  - [Q88](#q88) Is the 7B re-check just luck?
  - [Q74](#q74) What would you do with more compute or more time?

## 7. Learnings and honesty

Slide 9. The jury values honesty about limits. The imprecisions in our methodology document are collected here (Q "imp_*" entries) with the wording to correct them without drama: state the exact figure, say which one the document gave, move on.

<a id="q72"></a>
**Q72. What did not work?**

- **Say this:** Self-training with unseen words, rule-labelled French training pairs (about minus 0.004 on the India stand-in), seed bagging, brand-name joins, an unguarded second round and a third round, and every recall rule. Also synthetic French cross-encoders, which reverted leaderboard-confirmed moves, and disagreement-based drops, whose intervals all spanned zero. We list them because the dead ends narrowed the final design.
- **Evidence:** recall rules 17 to 71% precise against a 75% break-even [M]; copy-count tie-breaking −0.00057; tie renormalisation −0.000007 to −0.000137; drop mining overfit (half A +33e-6, half B −15e-6); six-logit blend −0.001 as a decision score; consensus editing (candidates agree on 99.92 to 99.97% of predictions); extending the 7B drop past −6 tied (B7) [M]; [numbers §4.4](numbers.md#44-measured-and-dropped-in-the-decision-layer), [D-RUL-12](decisions/RUL.md#d-rul-12--drop-rule-from-cross-encoder-disagreement-bge-below-0-while-e5-above-0), [D-RUL-17](decisions/RUL.md#d-rul-17--no-recall-add-rules), [D-RUL-07](decisions/RUL.md#d-rul-07--brand-name-join-rejected-brandjoinpy-kept-not-applied), [D-MDL-13](decisions/MDL.md#d-mdl-13--no-stage-2-tuning-seed-bagging-depth-8-and-learning-rate-003-dropped), [D-FRA-10](decisions/FRA.md#d-fra-10--rule-labelled-french-training-pairs-rejected-after-the-india-stand-in), [D-FRA-23](decisions/FRA.md#d-fra-23--synthetic-french-supervision-run-it-as-a-priority-correct-the-generator-do-not-upload), [D-SUB-17](decisions/SUB.md#d-sub-17--reject-consensus-editing-screen-candidates-by-change-footprint), [D-LLM-10](decisions/LLM.md#d-llm-10--no-three-adapter-7b-ensemble-and-no-in-band-extension-of-the-drop).
- **Follow-ups:**
  - [Q73](#q73) What would you do differently?
  - [Q75](#q75) What did you get wrong?

<a id="q73"></a>
**Q73. What would you do differently?**

- **Say this:** Upload one France-emptied probe early, to measure France instead of inferring it; build an independent check like the 7B much earlier, instead of trusting estimates made from our own probabilities; and settle the deadline and the best-versus-last upload rule on day one. On blocking, we would test city and state keys as a soft extra view. We would also write every ensemble recipe down at build time.
- **Evidence:** [handover 2026-09-27_2014](../docs/handover/2026-09-27_2014_ameya_final-upload.md) and [RESEARCH_v6 §6.20](../experiments/ameya/model-v1/RESEARCH_v6.md) list the same lessons; also: share artifacts as hash-identified pairs from day one, stop French self-training after round 2, keep production scripts in git from the start ([D-PKG-13](decisions/PKG.md#d-pkg-13--rescue-the-production-drivers-from-the-session-scratchpad-into-git)), check early for information the tokenizer threw away such as legal forms ([D-BLK-04](decisions/BLK.md#d-blk-04--blocking-uses-its-own-tokenizer-instead-of-waiting-for-the-normalise-stage)), and do not tune thresholds on the reporting holdout [M]; the record notes "no test of keys on city and state is recorded" ([D-BLK-02](decisions/BLK.md#d-blk-02--partition-the-search-by-the-exact-country-label-never-by-state)); [D-SUB-12](decisions/SUB.md#d-sub-12--27-sep-upload-discipline-no-pure-probes-one-change-per-upload-the-best-last).
- **Follow-ups:**
  - [Q74](#q74) What would you do with more compute or more time?
  - [Q10](#q10) Why no city or state blocking keys? (The organisers rated finer-grained keys higher.)

<a id="q74"></a>
**Q74. What would you do with more compute or more time?**

- **Say this:** Train a genuinely better French model, since the candidate family has converged; use cluster-level S2-to-S3 evidence and better candidate generation for empty-address variants; and run stage 2 in parallel on a large-memory box. With more uploads we would spend them on France-only composites, and we would measure before sizing, because our offline French proxies ranked well but under-sized gains.
- **Evidence:** `fhs` estimated v7sq-dpc at +0.00012 and the board measured +0.000366 [M]; five validated candidates agree with v7sq-dpc on 99.92 to 99.97% of predictions (commit c7f95b3) [M]; stage 2 was not parallelised: 12 GB of features at 3 MB/s [R]; [D-SUB-17](decisions/SUB.md#d-sub-17--reject-consensus-editing-screen-candidates-by-change-footprint), [D-BLK-15](decisions/BLK.md#d-blk-15--close-the-alias-bridge-recall-route), [D-FRA-17](decisions/FRA.md#d-fra-17--after-0990545-push-the-french-encoder-direction-a-second-h100-for-gpu-work-only).
- **Follow-ups:**
  - [Q73](#q73) What would you do differently?
  - [Q68](#q68) What parallelises and what does not?

<a id="q75"></a>
**Q75. What did you get wrong?**

- **Say this:** Two things in particular. We added the French look-alike word-swap drop on label-free evidence, then leaderboard history said it probably hurts; it stayed in, and later analysis calls it about neutral. And we trusted estimates built on our own probabilities, which are biased on decoys: for round three they said plus 0.000069 and the board measured minus 0.000046.
- **Evidence:** word-swap drop (454 pairs in mixmdp) valued between −31e-6 and +58e-6 by different methods ([CF-27](conflicts.md)) [E]; `cal` missed round 3 by about 115e-6 ([CF-51](conflicts.md)) [E]; a share-shift estimate (France 0.959) rested on counting artifacts [E]; our first word-odds method silently gave every French word 0, and a sanity print caught it [M]; [D-FRA-26](decisions/FRA.md#d-fra-26--after-the-verdicts-distrust-pc-based-french-estimators), [D-EVL-14](decisions/EVL.md#d-evl-14--value-french-changes-with-cal), [D-EVL-15](decisions/EVL.md#d-evl-15--trust-the-leaderboard-over-our-estimators), [D-RUL-14](decisions/RUL.md#d-rul-14--drop-french-look-alike-word-swaps-at-the-s1s-address-applyswapsimpy), [D-RUL-16](decisions/RUL.md#d-rul-16--build-later-candidates-without-the-look-alike-drop).
- **Follow-ups:**
  - [Q76](#q76) How reliable were your label-free estimators for France?
  - [Q89](#q89) Did you overfit the public leaderboard?

<a id="q76"></a>
**Q76. How reliable were your label-free estimators for France?**

- **Say this:** Good for ranking and poor for sizing. The `cal` estimator reached a scale of 0.96 and a mean error of 42 millionths on past uploads, but it missed round three by about 115 millionths because it was biased on decoys. After that we trusted one-change leaderboard measurements and a 7B-calibrated estimate over our own probabilities.
- **Evidence:** backtest over 5 to 6 past LB pairs: scale 0.96, mean absolute error 42e-6, correlation 0.98 ([CF-51](conflicts.md)) [E]; `fhs` under-sized v7sq-dpc by about 3 times (+0.00012 against +0.000366) [M]; the rule-population AUC saturated after self-training (0.984 to 0.986) [E]; "within ±0.00005" did not hold ([numbers: not to quote](numbers.md#numbers-not-to-quote-and-why) #16); [D-EVL-14](decisions/EVL.md#d-evl-14--value-french-changes-with-cal), [D-EVL-15](decisions/EVL.md#d-evl-15--trust-the-leaderboard-over-our-estimators), [D-FRA-26](decisions/FRA.md#d-fra-26--after-the-verdicts-distrust-pc-based-french-estimators), [RESEARCH_v6 §6.18](../experiments/ameya/model-v1/RESEARCH_v6.md).
- **Follow-ups:**
  - [Q75](#q75) What did you get wrong?
  - [Q89](#q89) Did you overfit the public leaderboard?

<a id="q77"></a>
**Q77. Your methodology document puts 99.1% next to 3.70 per S1. Which is it?**

- **Say this:** That sentence joins two numbers. Retrieval keeps 99.1% of true holdout pairs at about 34 per S1, and the file after the learned cut keeps 98.35% at 3.70 per S1; the document gave the retrieval figure. The cut is also the intersection of the probability filter and the record's top two S1, not a union as one sentence reads.
- **Evidence:** 0.99135 vs 0.98354 [M]; an independent count finds 31,304 true pairs outside the file [M]; 0.98198 is the same cut on an older model and is superseded [M]; [CF-13](conflicts.md), [CF-14](conflicts.md), [numbers: not to quote](numbers.md#numbers-not-to-quote-and-why) #1.
- **Follow-ups:**
  - [Q11](#q11) 3.70 candidates per S1: with what recall?
  - [Q78](#q78) Your document says a wrong merge costs twice a miss and that the set selection gained 0.000048. Is that exact?

<a id="q78"></a>
**Q78. Your document says a wrong merge costs twice a miss and that the set selection gained 0.000048. Is that exact?**

- **Say this:** Both are loose. Twice is the F0.5 weighting; in counts one false merge equals four missed copies, and for a typical S1 about 2.7. The 0.000048 belongs to the whole decision layer, while the set selection alone was 0.000033 and not significant, and the out-of-sample figure is 0.000024 against minus 0.000019 for re-tuning a threshold.
- **Evidence:** [CF-15](conflicts.md), [CF-16](conflicts.md); costs 0.167 vs 0.0625 for a typical S1 [E]; +48.1e-6 [+7.1, +91.2] for the layer, +33.2e-6 [−7.5, +75.0] for set selection alone, +23.7e-6 vs −18.8e-6 out of sample [M]; [numbers: not to quote](numbers.md#numbers-not-to-quote-and-why) #2 and #3.
- **Follow-ups:**
  - [Q34](#q34) Why choose a set per S1 instead of a threshold, and did it always win?
  - [Q2](#q2) Why does F0.5 matter for the design, and how much does a wrong merge cost?

<a id="q79"></a>
**Q79. Is 0.9913 the score of what you submitted, and did you "never train on the holdout"?**

- **Say this:** 0.9913 is the holdout score of the model behind Composite B's US and India rows with the stage-3 decision; the final rule layer was not re-measured on it, and on earlier models it added about 0.00005. The holdout predictions are out of fold, but in the final fit the holdout rows also trained the models that score test, so we treat it as a comparison set, not an untouched test. France is not in it.
- **Evidence:** 0.991323 for g1w; the combination on v7sq3 added +57e-6 (0.991250 → 0.991307) [M]; [CF-17](conflicts.md), [CF-18](conflicts.md), [numbers: not to quote](numbers.md#numbers-not-to-quote-and-why) #5 and #6; [Q86](#q86).
- **Follow-ups:**
  - [Q86](#q86) Your final fit used the holdout as a fourth out-of-fold group. Isn't that training on your test set?
  - [Q85](#q85) Haven't you overfit the holdout, given how many things you tuned on it?

<a id="q80"></a>
**Q80. The document says only 8% of the 7B's strong rejects are real matches. Is that right?**

- **Say this:** It is right for the sample the document uses and understated for the whole holdout: 2 of 24 on a 34% sample, and 16 of 80, which is 20%, on the whole holdout. Either way it is far below the 75% at which a drop stops paying. We dropped 840 French and 310 US and India pairs, and the French reject rate is 15 to 25 times the US and India rate.
- **Evidence:** [CF-19](conflicts.md), [CF-20](conflicts.md); gain at −6: sample +33e-6, whole holdout +37e-6 [M]; 859 French pairs are flagged and 840 were present in the final France ([M]); [numbers §4.3](numbers.md#43-the-7b-re-check-of-confident-predictions), [numbers: not to quote](numbers.md#numbers-not-to-quote-and-why) #7, #8 and #18.
- **Follow-ups:**
  - [Q88](#q88) Is the 7B re-check just luck?
  - [Q30](#q30) The 7B is no more accurate than e5-large. Why use it?

<a id="q81"></a>
**Q81. Where else is the methodology document looser than the code?**

- **Say this:** Four places. Stage 0 removes about 85% of pairs, not 80%; stage 3 re-scores contested records, not every pair; the feature table lists city, state and PO-box flags that are not in the final model; and "four stages, each out of fold over three groups" is exact only for stage 3 and the cross-encoders. None changes a number, and we answer from the code and the record.
- **Evidence:** [CF-22](conflicts.md), [CF-23](conflicts.md), [CF-24](conflicts.md), [CF-25](conflicts.md), [CF-35](conflicts.md); also 0.944 for the 7B and 0.939 for e5-large are different training lengths ([CF-35](conflicts.md)); the full list is in [CF-38](conflicts.md) (trivial items, none changes a number).
- **Follow-ups:**
  - [Q10](#q10) Why no city or state blocking keys? (The organisers rated finer-grained keys higher.)
  - [Q86](#q86) Your final fit used the holdout as a fourth out-of-fold group. Isn't that training on your test set?

<a id="q82"></a>
**Q82. How did three people coordinate in 72 hours?**

- **Say this:** One-writer files, a captain who alone uploaded, work split into issues with specs and due times, and gates recorded as files. Code moved and data did not: full-scale runs of the chain happened on one integration laptop, and teammates on 8 to 16 GB machines worked on a 110k-S1 dev sample. The limits were real: teammates waited for files, and we lost about 4.7 hours of machine time on 26 Sep waiting for an approval.
- **Evidence:** 9 first-day issues (#5 to #13) with due times; 115 unit tests; 229 commits on main and pull requests up to #77 [M]; by role: Ameya (integration, model chain, France), Bakshi (7B, audit, package, Composite B), Sachi (plan and gates from Plan B, Qwen code, diagnostics) ([CF-52o](conflicts.md)); one breach, a push to another member's branch, handled with a normal commit, no rewrite ([D-ORG-21](decisions/ORG.md#d-org-21--handle-sachis-push-to-ameyas-pr-branch-with-a-normal-commit-not-a-force-push)); [D-ORG-01](decisions/ORG.md#d-org-01--one-writer-files-member-branches-rebase-merge-only-hooks-no-attribution-lines), [D-ORG-04](decisions/ORG.md#d-org-04--roles-machines-and-tasks-as-issues-code-moves-data-doesnt), [D-ORG-12](decisions/ORG.md#d-org-12--do-not-restart-reaped-jobs-without-the-human-then-resumable-memory-aware-chains), [D-ORG-18](decisions/ORG.md#d-org-18--coordinate-on-issue-45-merge-on-ameyas-orders-only-the-captain-uploads).
- **Follow-ups:**
  - [Q83](#q83) How did you use AI agents, and what stayed human?
  - [Q84](#q84) What happened when a GPU box died?

<a id="q83"></a>
**Q83. How did you use AI agents, and what stayed human?**

- **Say this:** Agents ran analysis, built rules and wrote code under fixed protocols: read-only runs, disjoint A and B halves, paired bootstrap and memory caps. Humans chose every upload and the final, and the coordinator declined weakly supported agent findings. No agent finding reached a decision until it held on two disjoint halves of the holdout.
- **Evidence:** 26 sub-agents researched, diagnosed and built rules [R]; only the captain uploaded, agents never chose the final ([D-ORG-18](decisions/ORG.md#d-org-18--coordinate-on-issue-45-merge-on-ameyas-orders-only-the-captain-uploads)); strict audit on every package ([D-PKG-04](decisions/PKG.md#d-pkg-04--a-strict-output-audit-on-top-of-the-official-validator)); declined findings: the India count prior, the bag of four, the SHAP fixes ([D-DEC-19](decisions/DEC.md#d-dec-19--no-india-only-count-prior), [D-MDL-15](decisions/MDL.md#d-mdl-15--usindia-has-converged-v7sq3-is-the-source-no-bagging-keep-370-candidates), [D-FRA-09](decisions/FRA.md#d-fra-09--two-france-biases-found-by-shap-neither-fixed)); [D-EVL-13](decisions/EVL.md#d-evl-13--three-memory-capped-analysis-sub-agents-gains-must-hold-on-two-disjoint-halves), [D-ORG-29](decisions/ORG.md#d-org-29--knowledge-capture-redacted-transcript-digests-and-a-common-standard).
- **Follow-ups:**
  - [Q82](#q82) How did three people coordinate in 72 hours?
  - [Q97](#q97) Why should we trust a validator PASS?

<a id="q84"></a>
**Q84. What happened when a GPU box died?**

- **Say this:** An interruptible H100 was taken from us at 21:40 on 26 September, and with it the variant that had the best French check, v7m. We rebuilt its design locally as v7n, which scored plus 0.001112 on the leaderboard, and from then on we used only on-demand boxes. A later on-demand box hit NaN losses from a non-finite gradient, which we fixed by skipping such steps.
- **Evidence:** French rule-population AUC v7m 0.878, v7n 0.872 [E]; v7n +0.001112 on the public LB [M]; the bge logits were lost with the first box and retrained later ([CF-52p](conflicts.md)); [D-ORG-16](decisions/ORG.md#d-org-16--after-the-spot-box-died-rebuild-v7ms-design-locally-as-v7n), [D-ORG-17](decisions/ORG.md#d-org-17--box-policy-one-on-demand-80-gb-gpu-the-traffic-cap-lifted), [D-CE-13](decisions/CE.md#d-ce-13--skip-optimizer-steps-with-non-finite-gradients).
- **Follow-ups:**
  - [Q68](#q68) What parallelises and what does not?
  - [Q71](#q71) Where did extra compute pay, and where not?

## 8. Hard and hostile questions

Expect at least two of these. Keep the tone level: concede what is true, give the number, say what was not measured.

<a id="q85"></a>
**Q85. Haven't you overfit the holdout, given how many things you tuned on it?**

- **Say this:** Partly, in the absolute level, much less in the comparisons. Thresholds, shifts and the 7B cut-off were tuned on the holdout, so its absolute score may be a little optimistic, but paired differences between versions are unaffected, and the decision-rule comparison used untouched folds. The only independent test, the public board, agreed where we could isolate it: g1w's US gain was about plus 10 millionths on the holdout and plus 14 on the board.
- **Evidence:** out-of-sample check by repeated 2-fold CV (42 splits): set selection +23.7e-6 vs −18.8e-6 for re-tuning the threshold [M]; parameters picked on half A, confirmed on half B [M]; US g1w gain +10e-6 (holdout), +14e-6 (LB) ([CF-46](conflicts.md)) [M]; tuning thresholds on the reporting holdout is a stated mistake ([Q73](#q73)); [CF-18](conflicts.md), [D-DEC-06](decisions/DEC.md#d-dec-06--no-richer-tuned-rules-toprest-thresholds-thresholds-by-set-size), [D-EVL-03](decisions/EVL.md#d-evl-03--gates-every-component-must-beat-a-simpler-one-in-a-paired-bootstrap-g1g13).
- **Follow-ups:**
  - [Q86](#q86) Your final fit used the holdout as a fourth out-of-fold group. Isn't that training on your test set?
  - [Q89](#q89) Did you overfit the public leaderboard?

<a id="q86"></a>
**Q86. Your final fit used the holdout as a fourth out-of-fold group. Isn't that training on your test set?**

- **Say this:** It is training on the holdout rows for the models that score test and the other groups, which is why we call the holdout a comparison set and not an untouched test. Its own predictions stay out of fold: no holdout pair is scored by a model that saw its S1. Switching to the four-group fit left the holdout unchanged (plus 0.00002), as expected, and each model now sees 75% of train instead of 50%.
- **Evidence:** holdout rows train the stage-1 and stage-2 models of the other groups and of test, enter the other groups' stage-2 inputs through p1, and are in the isotonic fit; the cross-encoders and stage 3 never train on them [M, code] ([CF-18](conflicts.md)); thresholds, shifts and the baseline cut-off were tuned on it; Bakshi's draft calls it "a fit-quality reference and not an untouched test set"; [D-NRM-04](decisions/NRM.md#d-nrm-04--final-fit-on-all-of-train---all-the-holdout-becomes-a-fourth-out-of-fold-group), [D-MDL-10](decisions/MDL.md#d-mdl-10--final-fit-on-all-of-train---all-the-holdout-becomes-a-fourth-oof-group), [numbers: not to quote](numbers.md#numbers-not-to-quote-and-why) #6, [ANALYSIS_v4 §7](../experiments/ameya/model-v1/ANALYSIS_v4.md).
- **Follow-ups:**
  - [Q85](#q85) Haven't you overfit the holdout, given how many things you tuned on it?
  - [Q79](#q79) Is 0.9913 the score of what you submitted, and did you "never train on the holdout"?

<a id="q87"></a>
**Q87. How do you know self-training did not just reinforce its own mistakes?**

- **Say this:** We cannot prove it for France, which has no labels, so we looked wherever it could show. On a labelled stand-in it did hurt when words were unseen, so we added guards, cross-fitting by S1 and a two-round limit. With those, the US and India holdout stayed level, and the leaderboard paid for rounds one and two and charged us for round three.
- **Evidence:** stand-in ladder 0.882 → 0.851 → 0.831 → 0.823 [M]; holdout v7n 0.991211 vs v7nst 0.991194 [M]; unguarded round 2 dropped clear copies ("& Cie" → "& Compagnie") and added word-swap look-alikes [M]; public LB: round 1 +0.000458, round 2 with decision layers +0.000154, round 3 −0.000046 [M]; 7B leak check: same reject rate in every S1 third (0.1118 / 0.1082 / 0.1070%) [M]; honest limit: estimators built on pc over-value self-trained models ([CF-51](conflicts.md)); [D-FRA-13](decisions/FRA.md#d-fra-13--self-train-on-france-with-cross-fitted-pseudo-labels-v7nst), [D-FRA-16](decisions/FRA.md#d-fra-16--stop-unguarded-self-training-at-round-1-withdraw-frs2), [D-FRA-18](decisions/FRA.md#d-fra-18--guarded-round-2-stage-2-labels-at-weight-3), [D-FRA-24](decisions/FRA.md#d-fra-24--round-3-as-a-candidate-round-4-not-used).
- **Follow-ups:**
  - [Q45](#q45) Why did self-training stop after two rounds?
  - [Q76](#q76) How reliable were your label-free estimators for France?

<a id="q88"></a>
**Q88. Is the 7B re-check just luck?**

- **Say this:** The cut-off was fixed on labelled US and India data before it touched France: minus 6 had the largest gain, positive in both halves and in 99.7% of random subsamples, and looser cuts were worse. In France the drops follow one visible decoy pattern, a model that never saw our French labels flags 82% of the same pairs, and the leaderboard gained 0.00018 when the drops went in. The size is small, roughly 0.0001 from the French drops by our estimate, and we do not claim more.
- **Evidence:** gain at −6: whole holdout +37e-6 (halves +33 / +41; US +18, India +18); −7 +27e-6, −5 +29e-6, −4 +17e-6, −3 +3e-6 [M]; positive in 99.7% of 3,000 random 25% subsets (mean +32.8e-6, sd 16.7e-6) [M]; 20% of strong rejects are true (16 of 80) [M]; French rejects: 78% follow the decoy pattern, 747 of 859 S1 have generic names, the bge detector without self-training labels flags 708 of 859 (82%) [M]; B7, with looser French drops, tied at 0.990875 [M]; 840 French and 310 US/India pairs dropped; split of the +0.000180 is an estimate ([CF-30](conflicts.md)); [D-LLM-05](decisions/LLM.md#d-llm-05--the-7b-re-check-drop-confident-out-of-band-predictions-below-logit-6), [D-LLM-06](decisions/LLM.md#d-llm-06--gate-the-drop-on-the-7b-not-on-the-pattern-same-name--same-number--different-street), [D-LLM-07](decisions/LLM.md#d-llm-07--apply-the-same-drop-to-usindia), [D-EVL-16](decisions/EVL.md#d-evl-16--keep-the-6-threshold-reject-looser-usindia-thresholds-mixbp5-mixbp4), [numbers §4.3](numbers.md#43-the-7b-re-check-of-confident-predictions).
- **Follow-ups:**
  - [Q80](#q80) The document says only 8% of the 7B's strong rejects are real matches. Is that right?
  - [Q76](#q76) How reliable were your label-free estimators for France?

<a id="q89"></a>
**Q89. Did you overfit the public leaderboard?**

- **Say this:** For US and India we gated every change on the holdout and used the board mainly for France, with one change per upload where possible and a written prediction first. The honest caveat is the last step: the final choice among near-equal composites was made on the public board, where the gaps were inside the noise. We do not claim the last decimals as signal.
- **Evidence:** 13 scored uploads (2 + 4 + 7) ([CF-05](conflicts.md)) [M]; no pure probes on 27 Sep, the best last ([D-SUB-12](decisions/SUB.md#d-sub-12--27-sep-upload-discipline-no-pure-probes-one-change-per-upload-the-best-last)); Composite B 0.990879, mixf7 0.990833, mixf2 0.990819, B7 0.990875 [M]; noise sd 0.000164 for a 25% split [E]; [D-SUB-01](decisions/SUB.md#d-sub-01--leaderboard-policy-and-upload-budget), [D-SUB-11](decisions/SUB.md#d-sub-11--upload-v7n-safe-first-then-v7nst-the-bet-the-last-slot-before-midnight-is-not-a-probe), [D-SUB-14](decisions/SUB.md#d-sub-14--default-final-v7sq-dpc-over-the-bag-of-seven), [D-SUB-24](decisions/SUB.md#d-sub-24--after-b-a-one-change-follow-up-mixf7-and-always-upload-the-best-expected-model).
- **Follow-ups:**
  - [Q61](#q61) How noisy is the public leaderboard, and how did you handle it?
  - [Q55](#q55) Which of your uploads was ranked on the private board?

<a id="q90"></a>
**Q90. Why was your best upload a teammate's composite and not the model your estimator ranked first?**

- **Say this:** We used Composite B as a one-change probe from a measured baseline, and it scored 0.990879, plus 0.000180 against a predicted plus 0.000149. The two packages our estimator preferred scored lower, which showed the estimator was biased on decoys, so we trusted the board's one-change measurements over the estimate. Bakshi built Composite B and Ameya chose the order of uploads.
- **Evidence:** [CF-06](conflicts.md); mixf7 0.990833 and mixf2 0.990819 [M]; the variant with the highest French estimate lost 6 of 8 corroborating checks and was not used [M]; a pre-set threshold (+0.000015) governed any switch away from the measured best [R]; [D-SUB-21](decisions/SUB.md#d-sub-21--us-and-india-from-bakshis-g1w-in-composite-b), [D-SUB-23](decisions/SUB.md#d-sub-23--upload-composite-b-first-as-a-probe-with-a-pre-set-rule), [D-SUB-24](decisions/SUB.md#d-sub-24--after-b-a-one-change-follow-up-mixf7-and-always-upload-the-best-expected-model), [LB 2026-09-27 #04](../submissions/records/2026-09-27_sub04.md).
- **Follow-ups:**
  - [Q76](#q76) How reliable were your label-free estimators for France?
  - [Q55](#q55) Which of your uploads was ranked on the private board?

<a id="q91"></a>
**Q91. Are all your models within the rules?**

- **Say this:** Yes: every model in the final pipeline is MIT or Apache-2.0 and at most 8B parameters. The largest is Qwen2.5-7B at 7.6B, and we rejected Qwen2.5-3B, whose licence is not Apache, and jina-reranker-v2, which is non-commercial. We checked licences through the Hugging Face API before downloading and pinned the exact revisions.
- **Evidence:** XGBoost (Apache-2.0); multilingual-e5-small 118M, -base 278M, -large 560M (MIT); bge-reranker-v2-m3 568M (Apache-2.0); Qwen2.5-1.5B and Qwen2.5-7B, 7.6B, revision d149729398750b98c0af14eb82c78cfe92750796 (Apache-2.0); Qwen3-4B-Base (Apache-2.0, used in the B7 variant only) [M]; [numbers §8](numbers.md#8-package-and-reproducibility), [D-CE-03](decisions/CE.md#d-ce-03--licence-screen-mit-or-apache-20-at-most-8b-parameters-no-external-data-models), [D-CE-08](decisions/CE.md#d-ce-08--qwen25-15b-not-3b-with-lora-as-an-extra-cross-encoder-sachi), [D-CE-09](decisions/CE.md#d-ce-09--add-bge-reranker-v2-m3-after-a-licence-check), [theory 10](theory/10-llm-verification-and-compute.md).
- **Follow-ups:**
  - [Q92](#q92) Did you use any external data, geocoders or web lookups?
  - [Q30](#q30) The 7B is no more accurate than e5-large. Why use it?

<a id="q92"></a>
**Q92. Did you use any external data, geocoders or web lookups?**

- **Say this:** No. We used only the provided files; our lexicons are hand-written and documented (legal forms, street types, US and Indian states, French departments, an OCR digit map, ordinals), and the Indic dictionary is learned from training folds. We considered IndicXlit, noted that it was trained on external data, and did not use it.
- **Evidence:** [numbers §8](numbers.md#8-package-and-reproducibility) ("Rules followed"); own-data augmentation only ([D-FRA-04](decisions/FRA.md#d-fra-04--no-external-data-only-own-data-augmentation)); synthetic French pairs were generated from our own data and were not used in the final ([D-FRA-23](decisions/FRA.md#d-fra-23--synthetic-french-supervision-run-it-as-a-priority-correct-the-generator-do-not-upload)); [D-NRM-02](decisions/NRM.md#d-nrm-02--our-own-indic-transliteration-skeletons-and-learned-dictionary-no-external-transliterator), [D-CE-03](decisions/CE.md#d-ce-03--licence-screen-mit-or-apache-20-at-most-8b-parameters-no-external-data-models).
- **Follow-ups:**
  - [Q93](#q93) Isn't pseudo-labelling the test records against "only the provided training data"?
  - [Q91](#q91) Are all your models within the rules?

<a id="q93"></a>
**Q93. Isn't pseudo-labelling the test records against "only the provided training data"?**

- **Say this:** We use only the provided files: for France we pseudo-label our own predictions on the unlabelled test records, with guards, and retrain, with no external data and no test labels. This is transductive learning on unlabelled inputs. How the organisers read that rule is not something we can speak for.
- **Evidence:** [CF-11](conflicts.md) (status: open; one agreed sentence is still needed); on 25 Sep an agent called test pseudo-labelling "risky" under the rule; the final method self-trains on French test decisions [M]; [D-FRA-13](decisions/FRA.md#d-fra-13--self-train-on-france-with-cross-fitted-pseudo-labels-v7nst), [D-FRA-04](decisions/FRA.md#d-fra-04--no-external-data-only-own-data-augmentation).
- **Follow-ups:**
  - [Q92](#q92) Did you use any external data, geocoders or web lookups?
  - [Q87](#q87) How do you know self-training did not just reinforce its own mistakes?

<a id="q94"></a>
**Q94. Isn't reverse-engineering the data generator a kind of leakage?**

- **Say this:** Everything came from the provided train labels and label-free counts on the test files, with no external data. The rule lists were derived without labels and matched our hand lists exactly, and each rule applies only to a country without labels, where its truth rate was measured on US and India. We treat the generator's operations as properties of the vendor data, not as test labels.
- **Evidence:** [ANALYSIS_v4 §3](../experiments/ameya/model-v1/ANALYSIS_v4.md), [RESEARCH_v5 §6](../experiments/ameya/model-v1/RESEARCH_v5.md); truth by operation, see [Q40](#q40); rules apply to unlabelled countries only ([CF-25](conflicts.md)); [D-RUL-01](decisions/RUL.md#d-rul-01--france-rules-from-the-generator-drop-op-b-add-op-a-postopspy-v1-unlabelled-countries-only), [D-RUL-14](decisions/RUL.md#d-rul-14--drop-french-look-alike-word-swaps-at-the-s1s-address-applyswapsimpy).
- **Follow-ups:**
  - [Q41](#q41) Aren't hand-written French rules overfitting?
  - [Q95](#q95) Did you find any leak, such as IDs, row order or hidden fields?

<a id="q95"></a>
**Q95. Did you find any leak, such as IDs, row order or hidden fields?**

- **Say this:** We looked and found none: IDs and file order carry no entity signal, with correlations of 0.0002 and 0.0014 over true pairs and no local clustering. When we were asked to reach 0.993 we checked for hidden levers first, then told the captain the target was out of reach, rather than chase a shortcut.
- **Evidence:** test IDs spread evenly (each decile about 15.1% France, 46.8% India, 38.1% US) [M]; correlation about −0.0008 on the final-day check [M]; [numbers §1](numbers.md#1-data-facts), [D-SUB-19](decisions/SUB.md#d-sub-19--check-for-hidden-levers-then-say-0993-and-0992-are-out-of-reach), [RESEARCH_v5 §1](../experiments/ameya/model-v1/RESEARCH_v5.md).
- **Follow-ups:**
  - [Q94](#q94) Isn't reverse-engineering the data generator a kind of leakage?
  - [Q62](#q62) What was the gap to the top, and why?

<a id="q96"></a>
**Q96. How reproducible is your submission?**

- **Say this:** The output files are the exact uploaded bytes, and our recomposition of the final step is byte-identical. A full rerun is not bit-identical, because GPU training differs across machines and stage 3 moves about 500 decisions, so we state it lands within about plus or minus 0.0001. We verified the one-driver rerun statically and did not re-run it end to end, because the GPU boxes were gone.
- **Evidence:** v7sq rebuilt on other hardware 0.991261 vs 0.991246; France block reproduced 871,147 French pairs with 0 differences; cross-encoder band matched at 100.0000% (train) and 99.9999% (test, 1 pair missing); 5,853,353 pairs identical and equal sha256 in the stacked-rules rerun; ZIP sha256 60b601522ca8…, 115 unit tests pass [M]; clean end-to-end run estimated at 6 to 7 h [R]; [CF-37](conflicts.md), [D-PKG-07](decisions/PKG.md#d-pkg-07--no-clean-end-to-end-rerun-on-the-final-day), [D-PKG-17](decisions/PKG.md#d-pkg-17--the-packages-france-block-reproduces-mixmdp-as-it-ran), [D-PKG-18](decisions/PKG.md#d-pkg-18--how-to-claim-reproducibility-no-gpu-rerun-within-about-00001-not-bit-identical), [numbers §8](numbers.md#8-package-and-reproducibility), components/packaging.md.
- **Follow-ups:**
  - [Q69](#q69) What hardware does it take to rerun your pipeline?
  - [Q97](#q97) Why should we trust a validator PASS?

<a id="q97"></a>
**Q97. Why should we trust a validator PASS?**

- **Say this:** We did not: the official validator only warns about matches outside the candidates and never checks that each record has one owner or that countries are consistent. So a strict audit ran on every package and on the final bytes. The final audit found no record with two owners, no cross-country pair and no match outside the candidates.
- **Evidence:** Composite B audit: 0 records with two owners, 0 cross-country pairs, 0 matches outside the candidates, validator PASS [M]; 12 of 12 audits passed on the final candidates [M]; [D-PKG-04](decisions/PKG.md#d-pkg-04--a-strict-output-audit-on-top-of-the-official-validator), [D-PKG-05](decisions/PKG.md#d-pkg-05--hash-gate-the-package-never-substitute-a-candidate-file), [PR #50].
- **Follow-ups:**
  - [Q96](#q96) How reproducible is your submission?
  - [Q14](#q14) Isn't the cut a way to look efficient on the candidate criterion?

<a id="q98"></a>
**Q98. Your late gains are tiny, 0.00005 here and 0.0001 there. Was the complexity worth it?**

- **Say this:** Late in the project each step was small by necessity, because US and India sat at this model family's ceiling at 0.991 and France was limited by decoys. The big gains came earlier, from structural choices: stage 2 and look-alike features, legal forms, larger cross-encoders and France self-training. We kept late components only when their interval was above zero and they were simple to reproduce, and we dropped a seven-model bag that tied.
- **Evidence:** holdout path 0.9683 (v0) → 0.98006 (v1) → 0.98436 (v2) → 0.98882 (v3) → 0.990156 (v5all) → 0.991211 (v7n) → 0.991323 (g1w) [M]; the bag of seven: expected LB tie (0.990299 vs 0.990295), 7 GPU trainings, inputs not recorded, so v7sq won ([D-SUB-14](decisions/SUB.md#d-sub-14--default-final-v7sq-dpc-over-the-bag-of-seven)) [E]; [numbers §3.1](numbers.md#31-local-holdout-version-by-version), [numbers §3.2](numbers.md#32-gains-that-passed-a-gate).
- **Follow-ups:**
  - [Q34](#q34) Why choose a set per S1 instead of a threshold, and did it always win?
  - [Q60](#q60) Walk us through the leaderboard steps. Which changes mattered?

<a id="q99"></a>
**Q99. Is this just XGBoost with extra steps? What is the novelty?**

- **Say this:** The novelty is in how the pieces are arranged around the metric and the unlabelled country: a compute cascade that spends transformers only where the trees are unsure, a per-S1 expected-F0.5 choice of the list, guarded cross-fitted self-training for France, and a 7B used as an independent reader of confident predictions. Each has a measured size and none is large alone. Together they took the holdout from 0.9683 for a baseline to 0.9913.
- **Evidence:** baseline v0 0.9683 → g1w 0.991323 [M]; sizes: decision layer +48.1e-6 (holdout), round 1 +0.000458 (LB), larger cross-encoders +0.001112 (LB), 7B re-check roughly +0.0001 (LB, estimated) [M/E]; the novelty claim is ours and has not been assessed independently; [D-DEC-01](decisions/DEC.md#d-dec-01--per-s1-expected-f05-set-selection-gated-against-a-tuned-threshold-g6), [D-FRA-13](decisions/FRA.md#d-fra-13--self-train-on-france-with-cross-fitted-pseudo-labels-v7nst), [D-LLM-05](decisions/LLM.md#d-llm-05--the-7b-re-check-drop-confident-out-of-band-predictions-below-logit-6), [Q7](#q7).
- **Follow-ups:**
  - [Q98](#q98) Your late gains are tiny, 0.00005 here and 0.0001 there. Was the complexity worth it?
  - [Q7](#q7) What is your solution strategy in 30 seconds, and what is new in it?

<a id="q100"></a>
**Q100. Did you use other teams' work?**

- **Say this:** We read pasted planning documents from another team and took three ideas, candidate size, French self-training and owner pruning. We searched for top teams' public solutions and found none, and we reused no code from a live competition. Everything in the pipeline is ours and built on the provided data.
- **Evidence:** ideas only, no code reuse ([D-ORG-13](decisions/ORG.md#d-org-13--competitors-public-work-ideas-only-no-code-reuse), [D-SUB-04](decisions/SUB.md#d-sub-04--take-three-ideas-from-another-teams-plans)) [R]; the three ideas and where the documents came from are in [D-SUB-04](decisions/SUB.md#d-sub-04--take-three-ideas-from-another-teams-plans).
- **Follow-ups:**
  - [Q92](#q92) Did you use any external data, geocoders or web lookups?
  - [Q91](#q91) Are all your models within the rules?

---

## Open items before 7 Oct

1. **City and state keys ([Q10](#q10)).** No measured result exists. A quick test on train labels would settle it: the share of true pairs whose state tokens agree, and the recall of a state-keyed retrieval. Until then, use the "reasoned, not measured" wording.
2. **Self-training on unlabelled test records ([Q93](#q93)).** [CF-11](conflicts.md) is open: the team needs one agreed sentence.
3. **Which upload was ranked ([Q55](#q55)).** Unknown ([CF-01](conflicts.md), [CF-03](conflicts.md)). Use the agreed wording and do not guess. Name who clicked upload for B7 only after Ameya and Bakshi agree ([CF-07](conflicts.md)).
4. **Total rented-compute spend ([Q65](#q65)).** Not recorded ([CF-12](conflicts.md)). Check the rental account.
5. **France is an estimate ([Q53](#q53)).** Never say a French F0.5 as a measured value ([CF-09](conflicts.md)).
6. **Figures derived for this page (level E).** The ceiling of a hard top-k cap (53% for k = 2, 74% for k = 3), the 95% candidate precision on the holdout, and 0.64 pairs per S2 or S3 record are computed here from numbers in [`numbers.md`](numbers.md). Recompute them before they go on a slide.
7. **Wording drift.** [`finale/README.md`](../finale/README.md) hedges the candidate recall at "98.2 to 98.4%" and "about 98.3%"; this page uses 98.35% ([CF-13](conflicts.md)).
8. **Component pages.** Links to `components/` point to pages that were being written in parallel; check that they exist.
