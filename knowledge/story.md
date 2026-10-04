# The story of our solution

**Summary.** This page tells the project in order: the problem, what we learned and how, the strategy that followed, how the public leaderboard score rose from 0.97608 to 0.990879, the final system, what failed, what we would change and who did what. It is the backbone of the deck. Times are IST; the competition ran 25–27 Sep 2026.

**Tags.** Each number carries an evidence level ([STANDARD] §3): [M] measured, [E] estimated or inferred, [R] reported and not re-checked, [U] uncertain. Brackets after a gain give its 95% paired-bootstrap interval. The "local holdout" is the fixed 25% of labelled US and India S1 (549,699 S1; no France). The "public LB" is the leaderboard during the challenge, on a subset of test. "e-6" means millionths of F0.5. Names such as v7nst or mixmdp tag our uploaded files; the table in section 4 says what each holds. The private leaderboard publishes rankings only, so this page quotes and estimates no private score.

## 1. The problem and what makes it hard

**The task.** Each Source-1 (S1) record is a business. For every S1 we list all Source-2 and Source-3 (S2/S3) records for the same business, using only name and address. An S1 has 0 to 11 matches, 3.46 on average [M] ([AGENTS]); about 5.6% have none [M] ([DOC] §2.1). Train is labelled (US and India). Test adds France, which has no labels and never appears in train.

**The metric.** Macro F0.5: each S1 gets its own F0.5 and we average. In count form F0.5 = 1.25·TP / (1.25·TP + 0.25·FN + FP), with TP right matches, FN missed copies and FP false merges. In this form one false merge weighs as much as four missed copies. Put the usual way, precision is weighted twice as heavily as recall. An S1 with no matches scores 1.0 if we predict nothing and 0 if we predict anything. Near our operating point a pair helps only if it is right about 75% of the time [E] ([DOC] §5).

**Six facts shaped the work.**

1. **Look-alike decoys.** About 26% of S2/S3 records belong to no S1; they carry a nudged house number and a changed business word [M] [chat:ameya/19e315ba 2026-09-25 12:15]. Test has 5.75 S2/S3 records per S1 against 4.68 in train, and the extra records are decoys, not extra matches [M] ([PLAN DECISION]). The first house number is equal in 12% of look-alike pairs against 85% of true pairs [M] ([PLAN DECISION]).
2. **Shared names.** 46–54% of S1 share their exact name with another S1 [M] ([PLAN DECISION]), so the address usually decides. In the US/India holdout, 62.5% of the records we lose sit between identically named S1 [M] ([RESEARCH_v5] §4).
3. **Noise and empty addresses.** Copies change case, accents, legal forms, word order, acronyms, spelling, street types and house numbers ([DOC] §2.1). 69% of the misses are empty-address records whose name several S1 share [M] ([RESEARCH_v5] TL;DR).
4. **France.** Unlabelled, and about 15% of any public subset of test [M] ([RESEARCH_v5] §1). Its names are generic: each French decoy we later removed shares its name with a median of 43 other S1 [M] ([RESEARCH_v6] §6.19). The public score is 0.38274·F_US + 0.46751·F_India + 0.14975·F_France, where F is a country's F0.5 [E] ([RESEARCH_v5] §1).
5. **Scale.** Comparing every S1 with every S2/S3 record is out of reach, so a cheap first search, called blocking, proposes candidates: 58.4M pairs on test [M] ([DOC] §3). A costly model can read only a small share.
6. **A local score that cannot see France.** France has no labels, so it cannot be in the holdout. Our local score (0.9913) always sat above the public LB (0.990879) [M]; the leaderboard was our only view of France.

## 2. The insights, in the order we found them

**2.1 The data is clean (25 Sep 11:00–12:15).** The agent for Ameya profiled all of train. Each S2/S3 record has at most one S1 owner: 0 violations in 7,638,365 true pairs [M]. True pairs with both a weak name and a weak address are almost absent (0.14%) [M] [chat:ameya/19e315ba 2026-09-25 12:15]. Distractors look the same in two unrelated towns (unmatched share 0.268 [M]), which suggested one generator for all countries [E] [chat:ameya/19e315ba 2026-09-25 11:55]. So: one decision per S1, precision first.

**2.2 The extra test records are decoys (25 Sep 13:36–15:20).** Plans A and B disagreed on whether test resembles train, so Ameya's Claude sessions checked the full data. In India test's extra records sit as close to an S1 as train's do (31.8% against 31.7%), so they are look-alikes, not records whose owner is missing [M] [chat:ameya/19e315ba 2026-09-25 15:20]. Plan B's assumption failed.

**2.3 Where the loss is (25 Sep 17:30–21:31).** Missed true pairs were 81% of model v2's loss [M] ([ANALYSIS_v2]). The tokenizer had been dropping legal forms, which help separate a look-alike from a true copy. Legal-form features gave +0.00271 [0.00260, 0.00283] [M] ([decision legal-form features]), and with blocking v2 model v3 reached 0.98882 [M] ([decision model-v3]). Sachi's gate G6 asked whether the best set per S1 beats one global threshold. Stage 1 scores each pair alone and stage 2 also sees its rivals. The set choice lost on stage-1 probabilities (−0.00029) and won on stage-2 probabilities (+0.00027) [M] ([decision gate-g6]), as she had predicted. We re-ran it on every model.

**2.4 The leaderboard gap is France (25 Sep 23:45 → 26 Sep 00:33).** v2 scored 0.97608 on the public LB against 0.98436 on the holdout; v3 scored 0.97961 against 0.98882. The gap grew from −0.0083 to −0.0092 while the holdout improved [M] ([CHANGELOG]). US/India behaved like the holdout, while France predicted 3.54 matches per S1 against 3.46 in the generator [M] ([decision model-v4]). The leaderboard arithmetic put France at about 0.93 [E] ([RESEARCH_v5] §1).

**2.5 What France had never seen (26 Sep 00:12–03:37).** French legal forms sat in bitmask values (number codes) never seen in training. A French look-alike with a changed legal form and a moved house number scored 0.456 at stage 1, and 0.027 with the bits zeroed [M]. Look-alike words unseen in train got neutral odds. In a leave-one-country-out test (LOCO: hide India's labels, treat it as the unseen country) the score was 0.961 with India's words known and 0.882 unseen. Label-free proxy odds recovered 0.95984 [M] ([decision model-v4]). The candidate file we wrote was also the raw blocking output (34 per S1) [M] [chat:ameya/agent-a1f88e87 2026-09-26 00:40].

**2.6 The generator has a vocabulary of edits (26 Sep 02:30–04:17).** Reverse-engineering the training labels showed two families. In op B one name word is swapped in place at the S1's own address; only 0.6% are true copies in US/India. In op A a word is dropped and a list word appended; 98.3–99.9% are true [M] ([decision france-generator-ops]). Model v4 accepted about 17k op-B swaps in France. Rules learned from US/India labels carry over to a country without labels. They were forecast at +0.0027 on the LB for a holdout cost of −0.000003 [E].

**2.7 Smaller candidate files rank higher (26 Sep 05:10).** The organisers said the approach "that generates a smaller candidate set per Source 1 entity will be ranked higher in the final evaluation beyond the public/private leaderboard" ([decision candidate-set-cut]). We cut the file from 4.68 to 3.70 per test S1 at a holdout tie (−0.000003 [−0.000015, +0.000011]), giving up 0.7 points of pair recall in the set [M]. Tighter cuts cost more (−0.000106, −0.000041) [M] ([DOC] §3).

**2.8 US and India are near their floor (26 Sep 05:00–14:25).** Re-weighted to the test's name mix, the holdout gives US 0.9909 and India 0.9905, and nothing leaks [M] ([RESEARCH_v5] §1). We took only small verified gains there (blocking repairs with signed house numbers, +0.00063 [0.00057, 0.00070]; stage 3, +0.000055 [M]) ([decision model-v6all]) and put the effort into France.

**2.9 French confidence was too high and the cross-encoders disagreed (26 Sep 14:52–20:59).** A cross-encoder is a language model that reads both records as one text and returns a match score. French probabilities summed to 3.55 expected matches per S1, against at most 3.46 in the generator [M, label-free] ([RESEARCH_v6] §2.3). The large cross-encoders disagreed in sign on 12.0% of French band pairs against 3.1% in the US [M] ([RESEARCH_v6] §6.6). So stage 2 takes the mean of their standardised scores. We ranked French models by a label-free yardstick, the rule-population AUC (how well a model ranks true above false pairs of known type).

**2.10 Self-training works when guarded (26 Sep 21:17–23:35).** Self-training means training on our own confident decisions as if they were labels. We had rejected it: in LOCO each round lost ground (0.882 → 0.851 → 0.831) [M]. We revived it for three recorded reasons: the top seven had passed 0.99, US/India had about 0.0003 left, and France's weakness, disagreeing text models, is what target-domain training addresses ([RESEARCH_v6] §6.7). Confident pairs (calibrated probability ≥ 0.9 or ≤ 0.05) became labels, rules overrule labels, and labels are cross-fitted by S1 group. It gained +0.000458 on the public LB [M] ([LB 2026-09-26 #04]).

**2.11 Offline French checks under-sized the real gain (27 Sep 10:05–10:22).** Our label-free check had estimated +0.00012 for v7sq-dpc; the leaderboard gave +0.000366 over v7nst [M]. A control upload split it: rules +0.000085, model +0.000281 [M] ([LB 2026-09-27 #01]). The France-diff agent explained why: the French self-trained cross-encoders overruled the US-trained ones, mostly by dropping confident false pairs. The leaderboard became France's instrument, read through a back-tested estimator ("cal": scale 0.96, mean absolute error 42e-6 on five past moves) [M] [chat:ameya/19e315ba 2026-09-27 15:18].

**2.12 A second reader finds decoys that string features accept (27 Sep 18:09–20:11).** Bakshi's Qwen2.5-7B, a 7-billion-parameter language model, re-read the confident predictions that no cross-encoder sees. Dropping those it scores below logit −6 gained +0.000033 on a 34% holdout sample, positive in both halves [M] ([handover 2026-09-27_2006]). In France it rejected 25 times the US/India rate, and 78% were one pattern: the same generic name and house number on a different street [M] ([RESEARCH_v6] §6.19). In US/India that pattern is a real match 99.7% of the time when the feature model keeps it and 0.5% when it rejects it, and the 7B separates the two (Ameya's check). Sachi's street-swap check supported gating the drop on the 7B.

**2.13 The leaderboard exposed biased estimators (27 Sep 21:55).** Round-3 French labels scored 46e-6 below Composite B, though our estimator had forecast +69e-6 [M] ([LB 2026-09-27 #05]). Estimators built on the model's own probabilities overvalue putting back decoys. Decoy-aware, the France decision layer (+51e-6) carried mixmdp's France and the round-3 model itself was +24e-6 [E] ([RESEARCH_v6] §6.20).

## 3. The strategy that followed

Five ideas and one working rule came out of these insights.

**Spend compute where the uncertainty is.** XGBoost (gradient-boosted decision trees) is cheap and scores all 58.4M retrieved pairs. The costly cross-encoders read only the 1.49M pairs where XGBoost is unsure, 2.6% of the total [E]. The 7B reads the pairs XGBoost was sure about, where a second opinion pays most. Reading all 58.4M pairs with the 7B would take about 27 GPU-hours at the 600 pairs per second we measured on an H100 [E] ([DOC] §2.2).

**Decide the way the metric scores.** The metric scores each S1 alone, so the last layer picks a set of records per S1 from calibrated probabilities (made to match how often the model is right), not a threshold on pairs. Each record belongs to at most one S1.

**Precision first.** A false merge weighs four missed copies, so a rule that adds pairs must be right about 75% of the time. The best recall rule we tried was 71% precise [M] ([DOC] §5), so we shipped none. The exact-address copy rule we did ship is 99.99% precise in US/India ([DOC] §4).

**Per country.** Weights, neighbours and statistics are fitted per country, the model has no country feature, and country is an open set. The final package is composed per country: US/India from the model best on the labelled holdout, France from the model best on the leaderboard.

**France is the unknown, so make it measurable.** With no French labels we used a stand-in country (LOCO), label-free invariants, the leaderboard arithmetic, uploads that change only France, and an independent reader (the 7B). Self-training was guarded against confirming its own errors.

**How we judged every change.** One fixed holdout that nothing trains on; a paired bootstrap (resample S1 and see whether a gain exceeds noise); ties to the simpler option; late rules had to gain on both holdout halves ([FINAL_PLAN] §9). We wrote the expected score down before each upload.

## 4. How the solution evolved

**P0, plan (25 Sep 11:00–14:30).** Ameya's agent set up the repository. Plan A (Ameya, 13:02) was a full gradient-boosting pipeline with a compute budget. Plan B (Sachi, 13:31) tagged every claim measured, fact or hypothesis and made each complex part beat a simpler one. Plan C (Bakshi) was not submitted. At 14:15 Ameya chose Plan A as the base (his rubric scores 3.9 against 3.1 [R]) and grafted in Plan B's gates, paired bootstrap and tie rule ([PLAN DECISION]).

**P1, baseline to model v2 (25 Sep 14:30–21:30).** Tasks went out as GitHub issues #5–#13, sized to each laptop. Blocking v0 found 97.52% of true holdout pairs at 29 candidates per S1, and the baseline scored 0.9683 on the holdout [M] ([handover 2026-09-25_1706]). Models v1, v2 and the legal-form step followed (0.98006, 0.98436, 0.98708) [M] ([handover 2026-09-25_1958]). Sachi's model v0 and Bakshi's normalisation and string features arrived but were not used by the chain.

**P2, the France gap (25 Sep 21:30 → 26 Sep 11:00).** The v3 upload exposed the gap; by morning we had the causes, the generator rules, the candidate cut and the proof that US/India were near their floor (§§2.4–2.8).

**P3, cross-encoders and self-training (26 Sep 11:00 → 27 Sep 03:00).** Ameya asked for a rented instance so work could run in parallel [chat:ameya/19e315ba 2026-09-26 16:52]. On a rented H100 the first large cross-encoders lifted v7n by +0.001112, the biggest step after the first France fixes. Self-training followed (§2.10).

**P4, the last day (27 Sep 03:00–23:40).** Three sub-agents found the stacked decision layer overnight. Bakshi rebuilt the pipeline on rented GPUs, trained the 7B and found the re-check (§2.12). At 20:46–20:53 Ameya and Bakshi chose to upload Composite B first, as a probe, instead of the single upload we had agreed (mixf2, forecast 0.99091) [chat:ameya/19e315ba 2026-09-27 20:46]; the repo records do not name who decided. B scored 0.990879; mixf2, sent later, scored 0.990819 [M]. We had planned for a 21:00 close, though AGENTS.md said 23:59; uploads were accepted at 21:55 and about 23:40 [M].

**P5, the package (27 Sep 21:00 → 29 Sep 10:00).** Bakshi built a hash-gated ZIP builder, a runnable Composite B driver and an 8-item check. Ameya assembled the package; his agents wrote the France block and, over many rounds of his feedback ("don't overstate"), the 7-page methodology. A rerun lands within about 0.0001 of our numbers, not bit for bit [R].

**P6, the finale (3 Oct → 7 Oct).** On 3 Oct the organisers told us we are in the Top 10 of 32,000+ teams, 2nd on their list [R] ([FINALE]). The deck is due Tue 6 Oct 14:00; the talk is Wed 7 Oct, 10 minutes plus 5 of questions.

**Every public upload and what moved it.** Public LB and holdout values are [M]; France values are [E].

| upload | public LB | local holdout | public rank | what changed | why the score moved |
|---|---|---|---|---|---|
| v2, 25 Sep | 0.97608 | 0.98436 | – | blocking v1, look-alike odds, cluster support | first transfer test; gap −0.0083 ([CHANGELOG]) |
| v3, 25 Sep night | 0.97961 | 0.98882 | – | legal-form features, blocking v2 | +0.0035 on the LB, +0.0045 on the holdout; gap −0.0092 pointed to France (about 0.93) |
| v5all, 26 Sep ~14:38 [LB 2026-09-26 #01] | 0.98781 | 0.990156 | 15 | France fixes: proxy odds, no bitmasks, e5-small cross-encoder, rules v2; 3.70 cut | +0.0082; France 0.971–0.976 |
| v6all, 26 Sep evening [LB 2026-09-26 #02] | 0.988609 | 0.990842 | 15 | blocking repairs, signed numbers, stage 3, rules v3 | +0.000799; France about 0.973 |
| v7n, ~23:05 [LB 2026-09-26 #03] | 0.989721 | 0.991211 | 8 | mean of two large e5 cross-encoders | +0.001112; France about 0.978 |
| v7nst, ~23:35 [LB 2026-09-26 #04] | 0.990179 | 0.991194 | 7 | French self-training, round 1 | +0.000458, France alone; about 0.981 |
| v7nst-dpc, 27 Sep morning [LB 2026-09-27 #01] | 0.990264 | 0.991194 | – | stacked decision layer | +0.000085 (the control) |
| v7sq-dpc, ~10:05 [LB 2026-09-27 #02] | 0.990545 | 0.991246 | 7 | Qwen2.5-1.5B and self-trained e5-large in the mean; round 2 | +0.000281 over the control; France +0.0016 |
| mixmdp, ~16:40 [LB 2026-09-27 #03] | 0.990699 | US/India 0.991307 | 12 | guarded round-2 labels, 454 swaps dropped, France decision layer | +0.000154: US/India +20e-6, France +134e-6 |
| Composite B, ~20:55 [LB 2026-09-27 #04] | 0.990879 | g1w 0.991323 | 16 | g1w for US/India, mixmdp for France, 7B rejects dropped | +0.000180 (forecast +149e-6); final |
| mixf7, ~21:55 [LB 2026-09-27 #05] | 0.990833 | – | – | B with round-3 French labels | −46e-6 against B |
| mixf2, ~21:55 [LB 2026-09-27 #06] | 0.990819 | – | – | mixf7 with v7sq3 for the US | −14e-6: g1w's US is worth +14e-6 |
| B7, ~23:40 [LB 2026-09-27 #07] | 0.990875 | – | – | B plus deeper French 7B drops | −4e-6: a tie; the last upload |

Rank is the public rank at upload, as recorded; the private ranking uses other data. France is an estimate from the leaderboard arithmetic, with no recorded value after v7nst; the theory page puts Composite B at about 0.985 [E] ([theory 05] §2.9). The first two uploads (baseline 0.9683 and model v1 0.9801 on the holdout) have no recorded public score [U]. Forecasts held when we understood the change (v7n: forecast 0.9894–0.9900, scored 0.989721).

## 5. The final system on one page

Composite B writes one set of matches per test S1 from 6,410,308 candidate pairs. Eight steps ([DOC] §§2–4; code-level detail in [RECIPE]):

1. **Blocking, per country.** A token view (word overlap on name and address, both directions, rare words counting more), a names-only view (character 4-grams, for empty or short addresses) and repairs (domain names split into words, OCR digits fixed, a 693-entry Indic-to-Latin dictionary learned from training pairs). It retrieves 58.4M test pairs, about 34 per S1, holding 99.1% of the true holdout pairs [M].
2. **Stages 0 and 1** (XGBoost). Stage 0 cheaply removes more than 80% of pairs; stage 1 gives each pair a probability p1. A pair joins the candidate file when p1 ≥ 0.02 and it is among its record's two best S1, plus acronym-join pairs: 6,410,308 pairs, 3.70 per test S1, holding about 98.2–98.4% of the true holdout pairs [M].
3. **Cross-encoders on the uncertain band.** Only pairs with 0.02 ≤ p1 ≤ 0.99 are read: 1.49M test pairs [M]. Models: multilingual-e5-large (MIT), bge-reranker-v2-m3 (Apache-2.0), Qwen2.5-1.5B and 7B with LoRA (Apache-2.0; LoRA trains small add-on weights instead of the whole model), plus French self-trained versions. Their z-scored logits are averaged into one feature.
4. **Stages 2 and 3.** Stage 2 adds the cross-encoder mean, per-S1 and cluster features and French pseudo-labelled rows, and is calibrated with isotonic regression. Stage 3 re-scores each pair against the other candidates of its S1.
5. **The per-S1 decision.** A dynamic programme (an exact search) picks the set with the highest expected F0.5, using a logit shift of +0.2, a further −0.3 for records that four or more S1 compete for, and 0.01 expected true matches outside the candidates. Each record goes to its highest-scoring S1. The combined layer gained +48.1e-6 [+7.1, +91.2] on the holdout; the programme alone gained +33.2e-6 [−7.5, +75.0], not significant [M] ([decision stacked-rules]).
6. **Rules.** Acronym joins and per-source caps everywhere. France adds an exact-address copy rule (99.99% precise in US/India), a cross-commune drop, a look-alike word-swap drop and its own set selection.
7. **The 7B re-check.** Qwen2.5-7B (7.6B parameters) reads the 94.5% of final predictions with p1 > 0.99 and drops those it scores below logit −6, a cut-off fixed on labelled data first: 840 French and 310 US/India pairs [M].
8. **Composition per country.** US/India come from g1w (the 7B counted twice in the mean), France from mixmdp, both minus the 7B drops.

**Results.** Public LB 0.990879 [M]. Local holdout 0.9913 (US 0.9911, India 0.9916), precision 99.9%, recall 97.5% [M] ([DOC] §5). **Compute.** XGBoost needs 24 or more cores and 32 GB RAM; the cross-encoders ran on one 80 GB H100; Qwen2.5-7B trained on three 80 GB GPUs in about two hours [R] ([DOC] App. A). Only the provided data is used, and every model is MIT or Apache-2.0 with at most 8B parameters.

## 6. What did not work, and why

- **More rounds of self-training.** In LOCO each round lost ground (0.882 → 0.851 → 0.831 → 0.823) [M]; round-3 French labels scored 46e-6 below Composite B on the leaderboard [M]; retraining the cross-encoders on round-2 labels drifted. The model's own errors become labels. The guards slow this; they do not remove it.
- **Recall rules.** Scoring unowned candidates with the 7B peaked at 71% precision (69 adds, 49 true); an empty-address exact-name rule was 40% true; copy-count tie-breaking would lose 0.00057 [M] ([RESEARCH_v6] §6.19; [DOC] App. B). Under F0.5 a wrong add costs more than a right one gains.
- **Cleverer decision scores.** A learned blend of cross-encoder scores scored 0.001 lower F0.5; drops mined with a decision tree failed on the held-out half; renormalising French probabilities per record lost up to 0.000137 [M] ([DOC] App. B).
- **Quick language-model tests.** Zero-shot Qwen2.5-7B-Instruct reached AUC 0.537 and a quick LoRA run 0.720, against 0.898 for our probability on the uncertain pairs [M] [chat:ameya/19e315ba 2026-09-27 afternoon]. Bakshi's fully trained 7B worked as a second reader; as a pair scorer it only tied a self-trained e5-large (band AUC 0.9436 against 0.9439) [M].
- **Synthetic French pairs.** Cross-encoders trained on Sachi's generator (re-weighted as synth3) raised our estimator while reversing 1,182–1,576 leaderboard-confirmed moves; one lost 43e-6 on the US/India holdout [M] ([RESEARCH_v6] §6.19). Not used, though a bge trained on them flagged 82% of the 7B's French drops.
- **Bakshi's normalisation and string features, and Sachi's `ber.model`.** Delivered and tested, not used by the final chain, which ran on Ameya's tokenizer and feature scripts ([ROADMAP]). The reasons are not recorded; at first review the features looked largely redundant and `ber.model` could not yet run at full scale [R].
- **The gate bar.** The +0.002 bar was never met after v3. At 0.99 useful gains were +0.00002 to +0.0006, so we kept components on "interval above 0, both halves", with no decision record for the change [R] ([FINAL_PLAN] §9).
- **A drop we still ship.** mixmdp, and so Composite B's France, drops 454 look-alike swaps. A leaderboard-history test put that at about −27e-6; the later 7B-calibrated split found it about neutral [U].

## 7. What we would do differently

Hindsight: this section is what we know now, not what we knew then.

- **Measure France in absolute terms early.** Estimators that share the model's blind spots misled us on 27 Sep. A small hand-checked French sample, or the France-emptied upload we built and never sent, would have given an anchor on day 1.
- **Rent GPUs on day 1.** The 31 GB laptop was the bottleneck: it froze at 03:35 on 27 Sep and the agent tool's memory reaper killed background jobs several times [R]. The biggest late steps (v7n, the French self-trained cross-encoders, the 7B) came from rented GPUs, which began on the evening of 26 Sep.
- **Share one runnable pipeline.** Full-scale artifacts lived on one laptop, and two members' modules went unused. Agree one chain and give everyone a way to run it.
- **Settle the rules at once.** We planned around a 21:00 close, were unsure whether the best or the last upload counts, and the protocol said five uploads a day against seven on 27 Sep.
- **Start the independent reader sooner.** The 7B found the French decoys only on the last evening.

## 8. Who did what

Where an agent for Ameya relayed, ported or verified a teammate's work, the credit goes to the teammate. The research documents do not separate Ameya's own ideas from his agents'.

**Ameya** (captain, coordinator, integrator).
- Set up the repository, hooks, CI and the shared package; wrote Plan A and chose the final plan; issued tasks and built dev kits for teammates' small machines ([PLAN DECISION]).
- With his agents built the scoring chain: blocking v0–v3, features, XGBoost stages 0–3, calibration, the per-S1 decision, the France work (proxy odds, generator rules, acronym join, France decision layer), cross-encoders on rented GPUs, French self-training, the stacked rules, per-country composition and label-free checks such as the size-bias test.
- As captain: made all 15 uploads [R], ran the status threads (#45, #63, #64), rented the GPU boxes, reviewed teammates' PRs, assembled the ZIP.

**Sachi.**
- Plan B: evidence tags, the gate system, "ties go to the simpler option", LOCO, the France-vs-empty probe idea.
- Model v0 and decision v0 (PRs #16, #17), the ownership fix, the first gate records (G6, G4, name uniqueness) and the finding that empty-address losses are a data limit. PR #39: no feature group explains the unseen-country gap.
- `ce_llm.py` (PR #46), the Qwen LoRA classifier. She chose 1.5B because Qwen2.5-3B is not Apache-2.0. It is the training core of both Qwen models in the submission. Ameya's review flagged that the two texts were joined without a separator; his wrapper added one and the French self-training, making qst.
- Synthetic French pairs (§6); on issue #64 the street-swap evidence and the round-count risk that made Ameya drop mixf4; PR #68 diagnostics cited in the methodology.

**Bakshi.**
- Normalisation (PR #20) and string features (PR #21), with a Codex agent. France diagnostics (PR #34): every proposed rule failed its evidence check and stayed off.
- With Claude Code on 27 Sep: the strict output auditor, the hash-gated ZIP builder, the variant-driven `reproduce.sh`, the fix for the packaging bug that made earlier ZIPs unrunnable, the labelled gate for the cross-encoder mix, and measured negative results.
- The final push (PR #62): rebuilt the pipeline on rented GPUs (holdout 0.991261 against our 0.991246 [M]), trained the Qwen2.5-7B q7st (band AUC 0.9436 [M]), built g1w (best US/India, 0.991323; India +66.1e-6, P 0.998 [M]), originated and validated the 7B re-check, built Composite B and B7.
- On 29 Sep: the runnable `compositeB.sh` driver (PR #72) and, through his agent, the 8-item ZIP check (issue #75). Composite B is half his: its US/India model, its 7B member and the rule that removed 840 French decoys.

**Agents.**
- Agent for Ameya, three Claude Code sessions: the main one built and ran everything and directed 22 sub-agents; a research session settled the plan with data checks, wrote FINAL_PLAN v1.0, built the loss ledger and refuted two of Bakshi's claims by measurement; a short session searched for top-10 teams' public code and found none.
- Sub-agents (26 in all): hunt and polish found the acronym, cap, copy and city rules; decide built the combined decision rule; GPU-plan built the guarded labels; the error agent found the French acronym anomaly, which the size-bias test cleared; the France-diff agent explained v7sq's gain, designed the France decision layer, built `cal` and refereed late candidates; a fork wrote the ZIP's France block.
- Agents for Bakshi: Codex, Claude Code Opus sessions and a cloud session; for Sachi, an AI assistant [E]. Agents never uploaded or chose the final.

## Open items and conflicts

- **Which upload did the private ranking use?** Composite B (the ZIP's outputs, public 0.990879) or B7 (the last upload, public 0.990875, a tie). No source says [U].
- **Wording in the submitted methodology that this page corrects.** Its 99.1% recall is the retrieval stage (the 3.70-per-S1 file keeps about 98.2–98.4% [M]); a wrong merge costs four missed copies, not "twice as much"; the +0.000048 gain is the combined decision layer; and "p1 ≥ 0.02, plus the two best S1" reads as a union where the 3.70 count shows an intersection. The document stays as submitted.
- **French 7B rejects.** The 7B flags 859 French pairs on the test list ([RESEARCH_v6] §6.19); a package drops those it contains: 840 in Composite B, 832 in mixf2.
- **Origin of two pasted idea lists.** Ameya pasted idea lists on 26 Sep at 00:05 and 02:17 (candidate size may be ranked; self-training; owner pruning). One extract reads them as another team's plans, another found no origin [U]. Ameya to confirm.
- **Not in the record yet.** Sachi's own Qwen2.5-1.5B result, whether she ran the ZIP's clean-install check, and Bakshi's and Sachi's chat histories (issues #80, #81; see [sources]).

[STANDARD]: STANDARD.md
[sources]: sources.md
[theory 05]: theory/05-evaluation-methodology.md
[AGENTS]: ../AGENTS.md
[DOC]: ../experiments/ameya/final-zip/doc/Documentation_template.md
[PLAN DECISION]: ../plans/DECISION.md
[FINAL_PLAN]: ../plans/FINAL_PLAN.md
[FINALE]: ../finale/README.md
[ROADMAP]: ../docs/ROADMAP.md
[CHANGELOG]: ../CHANGELOG.md
[RECIPE]: ../experiments/ameya/model-v1/RECIPE.md
[ANALYSIS_v2]: ../experiments/ameya/model-v1/ANALYSIS_v2.md
[RESEARCH_v5]: ../experiments/ameya/model-v1/RESEARCH_v5.md
[RESEARCH_v6]: ../experiments/ameya/model-v1/RESEARCH_v6.md
[decision legal-form features]: ../docs/decisions/2026-09-25_2142_gate-legal-form-features.md
[decision gate-g6]: ../docs/decisions/2026-09-25_1731_gate-g6-dp-vs-threshold.md
[decision model-v3]: ../docs/decisions/2026-09-25_2328_model-v3-end-to-end.md
[decision model-v4]: ../docs/decisions/2026-09-26_0207_model-v4-france-and-cross-encoder.md
[decision france-generator-ops]: ../docs/decisions/2026-09-26_0417_france-generator-ops-and-final-fit.md
[decision candidate-set-cut]: ../docs/decisions/2026-09-26_0532_candidate-set-cut.md
[decision model-v6all]: ../docs/decisions/2026-09-26_1425_model-v6all-final.md
[decision stacked-rules]: ../docs/decisions/2026-09-27_0636_stacked-rules.md
[handover 2026-09-25_1706]: ../docs/handover/2026-09-25_1706_ameya_block-v0-baseline.md
[handover 2026-09-25_1958]: ../docs/handover/2026-09-25_1958_ameya_model-v1.md
[handover 2026-09-27_2006]: ../docs/handover/2026-09-27_2006_bakshi_final-push.md
[LB 2026-09-26 #01]: ../submissions/records/2026-09-26_sub01.md
[LB 2026-09-26 #02]: ../submissions/records/2026-09-26_sub02.md
[LB 2026-09-26 #03]: ../submissions/records/2026-09-26_sub03.md
[LB 2026-09-26 #04]: ../submissions/records/2026-09-26_sub04.md
[LB 2026-09-27 #01]: ../submissions/records/2026-09-27_sub01.md
[LB 2026-09-27 #02]: ../submissions/records/2026-09-27_sub02.md
[LB 2026-09-27 #03]: ../submissions/records/2026-09-27_sub03.md
[LB 2026-09-27 #04]: ../submissions/records/2026-09-27_sub04.md
[LB 2026-09-27 #05]: ../submissions/records/2026-09-27_sub05.md
[LB 2026-09-27 #06]: ../submissions/records/2026-09-27_sub06.md
[LB 2026-09-27 #07]: ../submissions/records/2026-09-27_sub07.md
