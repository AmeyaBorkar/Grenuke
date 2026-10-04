# Lessons: what worked, what did not, and what we would do differently

**Summary.** Thirty-seven numbered lessons from the Grenuke build, in six groups: strategy; data and evaluation; modelling; France and unlabelled data; compute and process; teamwork.
Each says what worked, what did not or what we would do differently, gives the evidence with numbers and sources, and gives a line to say to the jury.
The events behind them are in [`failures.md`](failures.md) (IDs like [F-EVL-01](failures.md#f-evl-01)).

## How to read this page

- **Tags.** Each lesson is tagged **worked**, **did not work** or **do differently**. A lesson can carry two tags when it did both.
- **Say it** is spoken English, one or two sentences, meant to be said as written. **Hindsight:** is what we would change now; it is kept apart from what we knew then.
- **Evidence tags** follow numbers: [M] measured, [E] estimated, [R] reported and not re-checked, [U] uncertain. "Holdout" is the local holdout (the fixed 25% of labelled US/India S1, 549,699 S1, no France). "LB" is the public leaderboard. A number after either is macro F0.5. 1e-6 means one millionth.
- **The private result.** The organisers publish only rankings for the private leaderboard. Grenuke is 2nd of the Top 10 [memory:ameya]. We never quote or estimate a private score.

## Terms used on this page

| term | meaning |
|---|---|
| S1 | A business in the reference source. For each S1 we must find its copies in sources S2 and S3. |
| decoy, look-alike | A record that resembles an S1 business but is not a copy. |
| op-B | A generator edit that swaps one name word for another real word at the S1's own address. 0.6% true on the US/India holdout. |
| pc | The calibrated match probability from stage 2 or 3. |
| cross-encoder | A transformer that reads both records together and scores the match: e5, bge, Qwen. |
| 7B | Qwen2.5-7B with a LoRA adapter, trained by Bakshi. g1w is the stage-2 mix that counts it twice. |
| self-training | Training on our own confident decisions as pseudo-labels. |
| LOCO | Leave-one-country-out: train on one labelled country and score another, to imitate France. |
| Composite B | The team's best upload (LB 0.990879): g1w for US/India, mixmdp's France, both minus the 7B's rejects. |

More terms are in [`theory/glossary.md`](theory/glossary.md).

## If you remember five

1. The metric rewards being right when we speak and silent when unsure (L-01).
2. A holdout without the unseen country is blind to it, and every French number we have is an estimate (L-07, L-23).
3. Estimates built from our own probabilities were biased on decoys (L-09).
4. A different model family and a second reader of the confident predictions beat a more accurate copy of the same (L-14, L-18).
5. Verify the artifact, not the source it came from (L-28).

## Strategy

### L-01 · Build for the metric, not for the model (worked)
- **Evidence:** The metric is macro F0.5 per S1. An S1 with no copies (5.6% of S1) scores 1.0 for an empty list and 0 for anything else, and a wrong merge costs about twice a missed copy [Documentation §2.1][doc]. Adding a pair pays only above about 72 to 75% precision: a false add costs about 0.18, a miss about 0.07 [decision rules-v3-and-stage3][d-rules3]. Holdout precision is 99.9%, recall 97.5% [Documentation Table 4][doc].
- **Say it:** "The metric scores each business separately and punishes a wrong merge about twice as hard as a missed copy. So every stage is built to speak only when it is right, and our held-out precision is 99.9%."

### L-02 · Write the gates and the tie rule down on day one (worked)
- **Evidence:** [FINAL_PLAN][plan] set gates G1 to G13, a paired bootstrap over S1 (1,000 resamples) and "ties go to the simpler option". The rule kept out v7ensall2 (expected LB 0.990299 against 0.990295 [E], and seven stage-2 runs to reproduce) [MODEL_CHOICE][b-choice], and Sachi's name-uniqueness features (+0.00054 [+0.00001, +0.00107]) [d-uniq]. Gate G6 kept the threshold until stage 2 supplied calibrated rivals (+0.00027) [d-g6].
- **Say it:** "Every component had to beat a simpler one on a paired bootstrap, and a tie went to the simpler one. That kept a seven-model ensemble out of the final, because it only tied a single model and could not be reproduced."
- **Hindsight:** The +0.002 bar did not survive the unseen country ([F-EVL-08](failures.md#f-evl-08)). We should have written the replacement rule down when we changed it.

### L-03 · Settle plan disputes with data (worked)
- **Evidence:** On 25 Sep full-data checks showed test has 5.75 S2/S3 records per S1 against 4.68 in train, with the same true matches per S1, so the extras are look-alikes. Look-alikes keep the first house number 12.4% of the time (true pairs 84.8%) and add a business word 76.5% (true pairs 23.3%). Postcodes appear in at most 0.5% of records [M, crude normalisation] [handover 25 Sep 14:14][h0925-1414]. Plan A became the base, with Plan B's gates grafted on. The rubric (3.9 against 3.1) was scored by Plan A's author, so the data decided ([F-PRB-04](failures.md#f-prb-04)).
- **Say it:** "Two plans disagreed about what the extra test records were. We measured instead of arguing: they are look-alikes of the same matches, not extra matches."

### L-04 · Spend effort where the model is unsure (worked)
- **Evidence:** XGBoost scores all 58.4M retrieved test pairs. The cross-encoders read only the 1.49M pairs with 0.02 ≤ p1 ≤ 0.99. The 7B reads the predictions no cross-encoder saw: 94.5% of final predictions have p1 above 0.99. Scoring all 58M pairs with the 7B at about 600 pairs per second would take about 27 GPU-hours [E] [Documentation §2.2][doc].
- **Say it:** "Cheap models see everything, bigger models see the doubtful pairs, and the biggest is a second opinion on what the others were sure about. Running the 7B on every pair would have taken about 27 GPU-hours."

### L-05 · Use leaderboard uploads as controlled experiments (worked, with misses)
- **Evidence:** v7nst-dpc against v7sq-dpc split one gain into +0.000085 for the stacked rules and +0.000281 for the French model change [LB 2026-09-27 #01][lb-0927-01]; [LB 2026-09-27 #02][lb-0927-02]. Composite B isolated the 7B parts (+180e-6, +149e-6 predicted); mixf7 and mixf2 isolated round-3 France (−46e-6) and g1w's US (+14e-6) [M] ([F-SUB-01](failures.md#f-sub-01)). The same uploads exposed the estimator bias (L-09).
- **Say it:** "We used the leaderboard as an instrument. Each late upload changed one thing, so the score difference was the answer."
- **Hindsight:** We skipped the cheapest control, a France-emptied upload ([F-SUB-05](failures.md#f-sub-05)), and left a control as the live upload for hours ([F-SUB-02](failures.md#f-sub-02)).

### L-06 · Confirm the rules of the arena in writing on day one (do differently)
- **Evidence:** We planned to a 21:00 deadline while the plan said 23:59, and uploads at about 21:55 and 23:40 were accepted ([F-SUB-03](failures.md#f-sub-03)). We still do not know whether the best or the last upload counts ([F-SUB-02](failures.md#f-sub-02)), or how the portal counted the daily limit ([F-SUB-04](failures.md#f-sub-04)). The candidate file became a ranking criterion on 26 Sep ([F-BLK-02](failures.md#f-blk-02)), and our first candidate file was the wrong set ([F-BLK-01](failures.md#f-blk-01)).
- **Say it:** "We learned on day two that the candidate file was a ranking criterion, and on the last day we still did not know whether the best or the last upload counts. We would read the portal rules on day one and put them in the repository."

## Data and evaluation

### L-07 · A holdout without the shifted country is blind to it (did not work)
- **Evidence:** v2 scored holdout 0.98436 and LB 0.976081; v3 0.98882 and 0.979606. The gap grew from −0.0083 to −0.0092, and France was about 0.93 [E] ([F-EVL-01](failures.md#f-evl-01)). The holdout preferred v7n, the LB preferred v7nst by +0.000458 ([F-EVL-02](failures.md#f-evl-02)).
- **Say it:** "Our local validation had no French records, because France has no labels. It said 0.989 while the leaderboard said 0.980, and the whole difference was France."
- **Hindsight:** We would build the stand-in country (leave-one-country-out) and per-country label-free diagnostics before the first upload. We built them after the gap appeared ([F-FRA-04](failures.md#f-fra-04)).

### L-08 · Label-free invariants find problems fast but cannot size them (worked)
- **Evidence:** The sum of pc per S1 equals the truth on US/India (3.43) and was 3.55 in France against a generator limit of 3.46. France broke the cap of 5 S2 copies 10 times as often. Every tenth of the ID range is 15% France [RESEARCH_v6 §2.2, §2.3, §6.15][r6]. They located the French problem within hours; none sized a fix ([F-EVL-04](failures.md#f-evl-04)).
- **Say it:** "Without labels we could still check what the generator guarantees, like how many copies one business can have. Those checks found the French problem within hours, but they could not say how much a fix was worth."

### L-09 · Estimates built on your own probabilities are biased on decoys (did not work)
- **Evidence:** Round-3 France was forecast at +69e-6 and measured −46e-6 ([F-EVL-05](failures.md#f-evl-05)). fhs saw 7% of the v7sq gain, per-category rates 30%, the pc-band method 82%; the offline forecast for v7sq-dpc was a third of the gain ([F-EVL-04](failures.md#f-evl-04)). Forecasts for US/India held to ±0.00004; French forecasts missed by 0.0001 to 0.0003, once in sign ([F-EVL-06](failures.md#f-evl-06)) [M, E].
- **Say it:** "Everything we estimated from our own model's probabilities was too optimistic about putting decoys back. One-change uploads told us: we forecast plus 69 millionths and the leaderboard gave minus 46."
- **Hindsight:** Calibrate with an independent model (the 7B) from the start. Use estimates to rank, and spend an upload when the sign matters.

### L-10 · Measure a population over all its candidates, and include every competitor (worked, after four slips)
- **Evidence:** Ownership was computed over holdout S1 only twice. Filtering to pc at least 0.3 made same-address swaps look 99.9% true when over all candidates they are 0.3 to 2.9%. On stage-2 candidates op-B pairs looked 12 to 43% true in US/India ([F-EVL-09](failures.md#f-evl-09)) [M].
- **Say it:** "Whenever a statistic is about competition between businesses, it has to include every business. We got that wrong four times and caught each one before it changed a decision."

### L-11 · Report an out-of-sample number next to every tuned one (worked)
- **Evidence:** Tuning the flat threshold by repeated 2-fold cross-validation gives −18.8e-6 out of sample, while the per-business rule gives +23.7e-6, positive in 86% of 42 splits. The final all-of-train fit uses the holdout as a fold, so it is not untouched ([F-EVL-08](failures.md#f-evl-08)) [M].
- **Say it:** "Tuning the threshold on the holdout made things worse out of sample. The per-business rule stayed positive in 86% of 42 repeated splits, which is why we kept it."

## Modelling

### L-12 · Read the errors; the largest US/India gains came from error analysis (worked)
- **Evidence:** Legal forms had been invisible to the features: +0.00271 [0.00260, 0.00283] ([F-FEA-01](failures.md#f-fea-01)). An Indic dictionary and look-alike word odds took India from 0.9561 (baseline v0) to 0.9838 (model v2) [h0925-1958]. Blocking recall rose from 0.9752 to 0.9857, 0.9899 and 0.99135 over v0 to v3. The holdout path was 0.9683, 0.9801, 0.98436, 0.98882, 0.990788, 0.991323 [M].
- **Say it:** "Each big step came from reading the errors of the previous model: legal forms, Indic names, blocking misses. We looked before we tuned."

### L-13 · Cross-encoders read only the doubtful pairs, and give stage 2 one consensus input (worked)
- **Evidence:** e5-large reaches band AUC 0.9391 against 0.9297 for p1 on the same pairs; v7ce3 gained +0.000311 [+0.000258, +0.000362] on the holdout and v7n +0.001112 on the LB [M]. The cross-encoders disagree in sign on 12.0% of French band pairs against 3.1% (US) and 2.7% (India) [RESEARCH_v6 §6.6][r6], so stage 2 gets their z-scored mean. That tied separate logits on the holdout and scored better on the French check (0.8776 against 0.8741).
- **Say it:** "The cross-encoders only read the 1.49 million pairs we were unsure about. They disagree four times as often on France, so we gave stage 2 their average instead of each opinion separately."

### L-14 · Diversity beats accuracy in the mix (worked, found by accident)
- **Evidence:** bge is the weakest single model on France (0.774) yet lifted the French mean by +0.020; a second e5-large epoch raised US/India and lowered France; the 7B ties e5-large (0.9436 against 0.9439) yet g1w gained +0.000062 on the holdout, India +66.1e-6 at P 0.998 ([F-CE-01](failures.md#f-ce-01)) [M].
- **Say it:** "The best model for the mix was not the most accurate one. A weaker model from another family fixed errors the others shared, and our 7B tied the best encoder on accuracy and still improved the system."
- **Hindsight:** We found this because a lost machine forced v7n. We would plan model families for diversity from the start.

### L-15 · Stop tuning the learner when the information is saturated (did not work)
- **Evidence:** Seed bagging −0.00004; depth 8 and a lower learning rate no gain; a 4-model stage-3 bag +5e-6 [−11, +21]. US/India converged at holdout 0.991297 to 0.991307 ([F-MDL-01](failures.md#f-mdl-01)) [M].
- **Say it:** "US and India converged near 0.9913 on our holdout and nothing we changed in the learner moved it. What moved the score was new information: cross-encoders, the 7B and a better decision rule."

### L-16 · Decide the way the metric scores, with calibrated probabilities that know about rivals (worked)
- **Evidence:** The per-S1 expected-F0.5 choice lost on stage-1 probabilities (−0.00029) and won on stage 2 (+0.00027). With a logit shift, a phantom term and a crowd shift it gained +48.1e-6 [+7.1, +91.2] ([F-DEC-01](failures.md#f-dec-01), [F-DEC-02](failures.md#f-dec-02)) [M].
- **Say it:** "For each business we pick the set of records with the highest expected F-score. It lost with raw scores and won once the probabilities knew about competing businesses."
- **Hindsight:** We called the rule "already optimised" after testing only its plain variant. Record exactly which variant a verdict covers.

### L-17 · Recall rules cannot beat a 75% break-even, and the rest of the loss is a data limit (did not work)
- **Evidence:** No recall rule was more than 71% precise ([F-RUL-05](failures.md#f-rul-05)). About 22k holdout pairs, empty-address copies of businesses that share a name, are 95 to 100% missed. Of the true pairs we miss, about 16.5k never become candidates and about 15.2k score near zero [M] [handover 25 Sep 21:47][h0925-2147]; [Documentation §5][doc].
- **Say it:** "Adding a wrong match costs about two and a half times what a missed one does, so a rule must be about 75% right to help. We tried many; the best was 71%. So we abstain, and our recall is 97.5%."

### L-18 · A second, independent reader for the predictions the model was sure about (worked)
- **Evidence:** 94.5% of final predictions have p1 above 0.99 and no cross-encoder saw them. The 7B's logit −6 rule gained +33e-6 on the holdout (halves +22e-6 and +43e-6) and rejected French predictions at 25 times the US/India rate. About 78% were the same name and house number on a different street, a pattern that is 99.7% true when the model accepts it and 0.5% true when it rejects it. Composite B gained +180e-6 on the LB over mixmdp, +149e-6 predicted ([F-LLM-03](failures.md#f-llm-03)) [M].
- **Say it:** "Almost all our predictions were so confident that no neural model had checked them. A second model that reads them again removed 840 French decoys and added 0.00018 on the public leaderboard."

## France and unlabelled data

### L-19 · A feature value never seen in training acts as a country feature (did not work, fixed)
- **Evidence:** French legal-form codes (values of 4096 and up) occur in 0.08% of train rows and 6 to 8% of test rows. French look-alikes scored 0.456 at stage 1, against 0.027 with the bits zeroed. Words unseen in training cost 0.961 → 0.882 in leave-one-country-out. The "no statistics" value differed between train and test, and a classifier told them apart with AUC 0.95 ([F-FEA-02](failures.md#f-fea-02), [F-FEA-03](failures.md#f-fea-03)) [M].
- **Say it:** "A feature can carry a country signal even when the model has no country column. French legal-form codes sat in a range the model never saw, so our own legal-form gain turned into a French loss."
- **Hindsight:** Run the train-versus-test classifier before the first upload.

### L-20 · Learn the generator on labelled countries and apply it to France as rules (worked)
- **Evidence:** Op-B edits are 0.6% true (5,364 US/India holdout pairs) and op-A edits 97 to 99.8% true. The v4 model predicted 17,088 op-B pairs in France. Applying the rules cost the holdout −0.000003. France went from about 0.93 (v3) to 0.971 to 0.976 (v5all with rules) [E] with the v4 fixes and the rules together; no upload isolated the rules ([F-RUL-01](failures.md#f-rul-01)) [M].
- **Say it:** "The data comes from a generator that applies the same few edits in every country. We learned the edits on US and India, where we have labels, and applied them to France as rules."
- **Hindsight:** Hand-review raw examples before trusting a rule's key. Our first address test missed 1,291 French look-alikes.

### L-21 · Self-training works on an unlabelled country, with guards (worked, after a wrong rejection)
- **Evidence:** In the unseen-words stand-in each round made it worse (0.88235 → 0.85120 → 0.83075). With label-free word odds restored, v7nst gained +0.000458 on the LB, France +0.0031. The guards were: rules win, empty-address records keep their first-round labels, and cross-fitting by S1 group ([F-FRA-01](failures.md#f-fra-01)) [M].
- **Say it:** "Self-training can teach the model a country it has no labels for, if the model is not confidently wrong to begin with and if you stop it from confirming its own mistakes. One round added 0.00046."
- **Hindsight:** We rejected it in the wrong regime and kept writing "rejected". Record the regime with every rejection.

### L-22 · Do not iterate pseudo-labels beyond the guarded rounds (did not work)
- **Evidence:** Round 2 on the model's own decisions dropped clear copies (fhs −1.54). Round-2 labels on the cross-encoder were negative under every valuation (s1 −6, own −13, s2 −53). Rule labels cost −0.0034 on the India stand-in. Synthetic cross-encoders reverted 1,182 and 1,576 LB-confirmed moves ([F-FRA-02](failures.md#f-fra-02), [F-CE-02](failures.md#f-ce-02), [F-FRA-05](failures.md#f-fra-05), [F-CE-04](failures.md#f-ce-04)) [M, E].
- **Say it:** "Self-training helped for one cross-encoder round and two guarded stage-2 rounds. Beyond that it only amplified the model's own near-threshold mistakes."

### L-23 · Measure the unlabelled country directly (do differently)
- **Evidence:** Every French level is derived from the leaderboard formula and the assumption that US/India on test score like the holdout. If they sat 0.002 lower, France for v5all would be 0.987, not 0.971 [E]. A France-emptied probe was packaged at least three times and never uploaded ([F-EVL-07](failures.md#f-evl-07), [F-SUB-05](failures.md#f-sub-05)).
- **Say it:** "We never measured France directly. Every French number we quote comes from the leaderboard formula and an assumption about US and India on test. One upload on day one would have replaced the assumption."

### L-24 · The unlabelled country can differ in the opposite direction from the naive reading (surprise)
- **Evidence:** French acronyms ran 11 times the rate that name shapes predict, which looked like planted decoys. A label-free size-bias test gave a false share of 0.00 [0.00, 0.01], so they were kept. "SNC" is a look-alike legal form in France, but "Incorporated" in the US is a vendor spelling (86% true). French true copies rarely move the house number (6 digit drops per 1000 S1 against 96 in the US) ([F-FRA-06](failures.md#f-fra-06)) [M].
- **Say it:** "French acronyms ran eleven times the US rate, which looked like planted decoys. A test that needed no labels showed they were real copies, so we kept them."

## Compute and process

### L-25 · Use on-demand machines for anything that must finish, and copy outputs back as they land (did not work)
- **Evidence:** The interruptible box was taken away at about 21:40 on 26 Sep with a non-persistent disk. We lost the bge logits and the self-trained e5-large, and v7m (French rule-population AUC 0.878) never shipped. Bakshi's interruptible 4×H100 box was taken away on 27 Sep, and his 5-minute backups to Drive let the 7B resume ([F-ORG-03](failures.md#f-org-03)) [M, R].
- **Say it:** "Twice a cheap interruptible machine was taken away mid-job. The first time we lost our best French model. The second time, backups every five minutes saved the run."

### L-26 · Make every job resumable and every write atomic (worked)
- **Evidence:** The laptop froze at 03:35 on 27 Sep with stage 2 running, and we lost about 15 minutes, not the run. Writes go to a temporary file and then `os.replace`, and chains resume from step markers. The memory reaper killed shell wrappers at least six times but not the scripts ([F-ORG-01](failures.md#f-org-01), [F-ORG-02](failures.md#f-org-02)) [R].
- **Say it:** "Our laptop froze on the last night and we lost 15 minutes, not the run, because every file write was atomic and every chain resumed from step markers."
- **Hindsight:** Add the memory guard and a per-agent memory budget on the first day, and give the agent standing permission to resume idempotent jobs. We lost 4.7 hours of compute waiting for a go-ahead.

### L-27 · Guard training against non-finite values (did not work)
- **Evidence:** One non-finite gradient at step 305 poisoned two cross-encoder runs that kept printing normal progress and logged NaN from step 1000. About 35 minutes of H100 time was lost ([F-ORG-04](failures.md#f-org-04)) [R].
- **Say it:** "A single bad gradient poisoned two training runs that kept printing normal progress. We now skip non-finite steps and log the first one."

### L-28 · Verify the artifact, not the source it came from (worked and did not work)
- **Evidence:** A filter named `*token*` dropped `tokens.py`, so five ZIP builds could not run while reported as validated for about 8 hours. The organisers' validator prints PASS with only warnings when the candidate file is missing or matches fall outside it. The fixes: the builder unpacks the archive, imports all 34 submodules and runs the shipped tests from inside it, a strict audit exits non-zero, files are identified by hash, and the last composition step was rebuilt byte-identical ([F-PKG-01](failures.md#f-pkg-01), [F-PKG-02](failures.md#f-pkg-02), [F-PKG-03](failures.md#f-pkg-03)) [M].
- **Say it:** "Our first ZIPs passed every check and could not run, because a filter had dropped a file called tokens. We now unpack the archive and run its tests from inside it."

### L-29 · Put the scripts in the repository before the upload, and run the package end to end once (do differently)
- **Evidence:** Recipes for three variants were never written down. The production stage-2 driver existed only in a temporary scratchpad until 29 Sep 01:08, when 134 files were rescued. `reproduce.sh` was never executed end to end, because every rented GPU machine was destroyed by 01:05 on 29 Sep. Stage 3 and GPU training are not bit-identical, so a rerun lands within about 0.0001 ([F-PKG-04](failures.md#f-pkg-04), [F-PKG-05](failures.md#f-pkg-05), [F-PKG-06](failures.md#f-pkg-06)) [M].
- **Say it:** "We can reproduce our result to about 0.0001, not byte for byte. The full pipeline was not rerun end to end, because the GPU machines were gone before the package was finished, and our document says so."

## Teamwork

### L-30 · One writer per file, pull requests only, and written handovers and decision records (worked)
- **Evidence:** The repo holds 24 handovers, 16 decision records and 11 submission records. Eight of the 16 decision records state a "Right if" and a "Wrong if" test in advance: v7n was "right if it beats v6all by more than +0.0003", and it gained +0.001112. Ten pull requests merged on 26 Sep (#22 to #32) [R] [AGENTS.md][agents]; [decision model-v7n][d-v7n].
- **Say it:** "Three people and many agents worked in parallel without overwriting each other, because every file had one writer and every change went through a pull request. Our decision records say in advance what result would prove them wrong."

### L-31 · Parallel stages need an integration owner and a shared artifact store (did not work)
- **Evidence:** Bakshi was blocked three times for files that lived on the integration laptop ([F-ORG-06](failures.md#f-org-06)). His normalisation and string-feature stages and Sachi's `ber.model` were not read by the final chain ([F-ORG-07](failures.md#f-org-07)). A team drive link was an open blocker in the 25 Sep 14:14 handover. The 27 Sep rebuild on rented boxes with Drive backups reproduced v7sq-dpc (holdout 0.991261 against 0.991246) [M].
- **Say it:** "Some of our teammates' stages did not end up in the final pipeline, partly because the model chain ran on one laptop and the files could not follow. We would set up shared storage and an integration owner on day one."

### L-32 · Review and audit by a teammate, with written corrections (worked)
- **Evidence:** Bakshi found the broken ZIP ([F-PKG-01](failures.md#f-pkg-01)) and retracted his own circular argument, his frs2 ranking and his bge estimate ([F-SUB-07](failures.md#f-sub-07)). Ameya's correction of "same number, different street" made the 7B drops the day's best French finding. The frs2 withdrawal came from the review (fhs −3.86) ([F-FRA-03](failures.md#f-fra-03)).
- **Say it:** "We corrected each other in writing, including Bakshi retracting his own claims. That caught a broken ZIP and a circular argument before either reached the leaderboard."

### L-33 · Let a teammate run the bet when compute is free (worked)
- **Evidence:** At 13:18 on 27 Sep the agent for Ameya argued against a 7B model [R]. Bakshi independently trained one on three H100s (about 2 hours). It gave g1w (India +66.1e-6, P 0.998) and the re-check (+33e-6 holdout, +180e-6 LB in Composite B) ([F-LLM-03](failures.md#f-llm-03)) [M].
- **Say it:** "On the last afternoon our agent argued against training a 7-billion-parameter model. Bakshi was training one independently, and it gave the best additions of the last day."

### L-34 · Brief helper agents exactly and re-check their key claims (worked, with slips)
- **Evidence:** We used 26 helper agents as parallel analysts, read-only on the repo [ROADMAP 6.3][roadmap]. They found the decision-layer gain (+48.1e-6), the France-diff valuations and the SHAP biases. They also made slips: a brief with the wrong threshold (0.70 against 0.675), 5 of 21 acronym adds mislabelled, memory overruns. The parent session caught each ([F-ORG-16](failures.md#f-org-16), [F-DEC-03](failures.md#f-dec-03), [F-RUL-03](failures.md#f-rul-03)).
- **Say it:** "We used 26 helper agents as parallel analysts. They found real things and they made mistakes, so every key claim was re-checked by the main session before it reached an upload."

### L-35 · A "don't overstate" pass by someone who did not write the text (worked)
- **Evidence:** Three overstatements were caught by the agent and four by Bakshi's agent on 29 Sep, after the first "final" ZIP was built ([F-PKG-07](failures.md#f-pkg-07)). The methodology states what we did not do: no end-to-end rerun, and reruns land within about 0.0001 [Documentation App. A][doc].
- **Say it:** "Our methodology says what we did not do. We did not rerun the whole pipeline end to end, and a rerun lands within about 0.0001 of our result, not on the same bytes."

### L-36 · Agents advise and a human decides the upload (worked)
- **Evidence:** [AGENTS.md][agents] gives uploads and the final choice to humans. At 20:46 to 20:53 on 27 Sep the team replaced the agreed single upload (mixf2) with a probe of Bakshi's Composite B. B scored 0.990879 and mixf2 0.990819, a gap of 60e-6 ([F-SUB-01](failures.md#f-sub-01)) [M].
- **Say it:** "Our agents recommended and the team decided. On the last evening the team replaced the agreed single upload with a probe of Bakshi's composite, and that probe was our best score."

### L-37 · Pick components on labels where labels exist and on one-change uploads where they do not (worked)
- **Evidence:** Composite B combined parts gated on the labelled holdout for US/India (g1w P 0.998 on India, the 7B rule positive in both halves) with a France that was leaderboard-proven (mixmdp, +134e-6 over v7sq-dpc [E]). The mixes that looked better by estimate (mixf7, mixf2) scored lower ([F-SUB-01](failures.md#f-sub-01)) [M].
- **Say it:** "Where we have labels we gate on them. Where we do not, we trust a leaderboard difference from a one-change upload over any estimate of our own."

## If we started again on Friday morning

Hindsight, not what we knew then.

1. Read the portal rules on day one (deadline, daily limit, best or last, the candidate file) and write them into `AGENTS.md` (L-06).
2. Before the first upload, build a stand-in for the unseen country, a train-versus-test classifier and per-country label-free diagnostics (L-07, L-19).
3. Spend one upload on a France-emptied probe (L-23).
4. Set up shared artifact storage and name an integration owner (L-31).
5. Use on-demand machines for must-finish jobs and copy outputs back as they land (L-25).
6. Plan cross-encoder families for diversity from the start, and train the 7B family earlier (L-14, L-33).
7. Calibrate every estimate with an independent model and treat it as a ranker (L-09).
8. Put every upload script in the repository, and rerun the package end to end once (L-29).

What we would keep: the gates and the tie rule (L-02), label-free invariants (L-08), atomic writes and resumable chains (L-26), the strict audit and hash identification (L-28), and written corrections between teammates (L-32).

[agents]: ../AGENTS.md
[b-choice]: ../experiments/bakshi/final-package/MODEL_CHOICE.md
[d-rules3]: ../docs/decisions/2026-09-26_1557_rules-v3-and-stage3.md
[d-v7n]: ../docs/decisions/2026-09-26_2135_model-v7n.md
[doc]: ../experiments/ameya/final-zip/doc/Documentation_template.md
[h0925-1414]: ../docs/handover/2026-09-25_1414_ameya_final-plan.md
[h0925-2147]: ../docs/handover/2026-09-25_2147_ameya_analysis-v2-and-v3.md
[lb-0927-01]: ../submissions/records/2026-09-27_sub01.md
[lb-0927-02]: ../submissions/records/2026-09-27_sub02.md
[plan]: ../plans/FINAL_PLAN.md
[r6]: ../experiments/ameya/model-v1/RESEARCH_v6.md
[roadmap]: ../docs/ROADMAP.md
