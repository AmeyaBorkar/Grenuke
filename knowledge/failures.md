# Failures: dead ends, bugs and surprises

**Summary.** What went wrong while we built the Grenuke pipeline, how each problem was found, what it cost and what we learned, grouped by area code ([STANDARD §4](STANDARD.md)).
The largest items are France (the unlabelled country that our holdout could not see), label-free estimators that were biased on decoys, lost compute, and packaging mistakes caught late.
[`lessons.md`](lessons.md) turns these into lessons. The facts our sources disagree on are listed at the end, for [`conflicts.md`](conflicts.md).

## How to read this page

- **IDs.** `F-<AREA>-<NN>`. The standard defines no ID for failures, so these IDs belong to this page, and [`lessons.md`](lessons.md) cites them. Each entry has one type: bug, dead end, surprise, compute, estimator, packaging or process.
- **Fields.** What happened, how it was Found, what it Cost, what we Learned, and the Source. Our own later reading is kept apart under **Hindsight:**. Smaller items sit in a table at the end of their area and put the same facts in one cell.
- **Evidence tags** follow numbers: [M] measured, [E] estimated, [R] reported in a chat or document and not re-checked, [U] uncertain.
- **Names of evaluations.** "Holdout" is the local holdout: a fixed 25% of the labelled US/India S1 (549,699 S1), with no France. "LB" is the public leaderboard, scored on a subset of the test S1. A number after either word is macro F0.5. The sign 1e-6 means one millionth, so +51e-6 is +0.000051.
- **Sources.** Repo files are linked. Chats use `[chat:ameya/<session> date time]`. Times are IST.

## Terms used on this page

| term | meaning |
|---|---|
| S1, S2, S3 | The three record sources. S1 is the reference list. For each S1 business we must find its copies in S2 and S3. |
| decoy, look-alike | A record that resembles an S1 business but is not a copy of it. The test set has about 23% more S2/S3 records per S1 than train, and the extras are look-alikes. |
| op-A, op-B | The data generator's edits at an S1's own address. Op-A drops a word and appends a list word (97 to 99.8% true copies in US/India). APP appends a list word and drops none. ACR shortens the name to initials. Op-B puts another real word in the dropped word's place (0.6% true). |
| p1, pc | The stage-1 match probability, and the calibrated stage-2 or stage-3 probability. |
| stage 0 to 3 | The XGBoost stages. Stage 2 adds cross-encoder scores and rivalry between S1. Stage 3 re-scores contested records jointly. |
| band | Pairs with 0.02 ≤ p1 ≤ 0.99. Only these go to the cross-encoders (1.49M pairs on test). |
| cross-encoder | A transformer that reads both records together and outputs a match score: e5, bge, or Qwen with LoRA (a small trained adapter). |
| 7B, q7st, g1w | Qwen2.5-7B with a LoRA adapter, trained by Bakshi. g1w is the stage-2 mix with the 7B counted twice. |
| DP, combo rule | The per-S1 choice of the set with the highest expected F0.5, with a logit shift, a phantom term and a crowd shift. |
| dpc | The stacked decision layer put on a model: the combo rule plus acronym, cap and France rules. |
| self-training | Training on our own confident decisions as pseudo-labels. |
| LOCO | Leave-one-country-out: train on one labelled country, score another, to imitate France. |
| proxy odds | Label-free look-alike word odds for a country with no labels. |
| rule-population AUC | The AUC of pc on French pairs whose type is known from US/India labels (op-A, APP, ACR true; op-B false). A label-free check. |
| fhs | Our count of true French copies gained or lost against a reference model. |
| cal, own, s1, s2 | Label-free estimates of how a French change moves the LB, built from pc. |
| mixmdp | The upload before Composite B (LB 0.990699): US/India from v7sq3, France from round-2 guarded self-training minus 454 look-alike swaps plus the France decision layer. |
| mixf7, mixf2, B7, Composite B | The last evening's uploads, explained in F-SUB-01. Composite B is the team's best upload (LB 0.990879). |

## The twelve that mattered most

| ID | one line |
|---|---|
| [F-EVL-01](#f-evl-01) | The holdout had no France, so a gap of 0.008 to 0.009 showed up only on the leaderboard. |
| [F-FEA-02](#f-fea-02), [F-FEA-03](#f-fea-03) | Feature values unseen in training acted as a country feature. |
| [F-FRA-01](#f-fra-01) | Self-training was rejected at 02:07 and shipped at about 23:35 the same day, for +0.000458 on the LB. |
| [F-EVL-04](#f-evl-04), [F-EVL-05](#f-evl-05) | Offline French estimators could rank but not size, and were biased on decoys (round 3: +69e-6 forecast, −46e-6 measured). |
| [F-ORG-03](#f-org-03) | Interruptible machines were taken away twice, and v7m never shipped. |
| [F-ORG-01](#f-org-01), [F-ORG-02](#f-org-02) | The laptop's memory: a freeze at 03:35 and 4.7 hours of idle compute. |
| [F-ORG-06](#f-org-06) | Full-scale artifacts did not travel to Bakshi, three times. |
| [F-PKG-01](#f-pkg-01), [F-PKG-02](#f-pkg-02) | A secret-filename filter dropped `tokens.py` from every ZIP for about 8 hours, and the official validator only warns. |
| [F-SUB-01](#f-sub-01), [F-SUB-02](#f-sub-02) | The agreed final lost to the fallback, the last upload was not the best, and we do not know which one counts. |
| [F-SUB-03](#f-sub-03), [F-SUB-05](#f-sub-05) | Deadline confusion (21:00 or 23:59), and the France probes were never uploaded. |
| [F-RUL-04](#f-rul-04) | A look-alike drop was adopted, reversed and shipped anyway; its sign was never settled. |
| [F-LLM-01](#f-llm-01), [F-LLM-03](#f-llm-03) | A zero-shot LLM was useless (AUC 0.537). A trained 7B gave the last day's best additions. |

## Find by theme

| theme | entries |
|---|---|
| Compute and machines | [F-ORG-01](#f-org-01) to [F-ORG-04](#f-org-04); small items [F-ORG-08](#f-org-08) to [F-ORG-11](#f-org-11), [F-BLK-05](#f-blk-05), [F-CE-05](#f-ce-05) |
| Estimator failures (label-free estimates that misled us) | [F-EVL-03](#f-evl-03) to [F-EVL-07](#f-evl-07), [F-ORG-05](#f-org-05), [F-FRA-03](#f-fra-03), [F-RUL-04](#f-rul-04), [F-FEA-06](#f-fea-06) |
| Packaging and reproducibility | [F-PKG-01](#f-pkg-01) to [F-PKG-08](#f-pkg-08), [F-BLK-01](#f-blk-01), [F-ORG-15](#f-org-15) |
| Process (deadline, uploads against the plan, teamwork) | [F-EVL-08](#f-evl-08), [F-DEC-02](#f-dec-02), [F-ORG-05](#f-org-05) to [F-ORG-07](#f-org-07), [F-ORG-14](#f-org-14), [F-ORG-16](#f-org-16), [F-SUB-02](#f-sub-02) to [F-SUB-05](#f-sub-05), [F-SUB-07](#f-sub-07), [F-PRB-04](#f-prb-04) |
| Modelling dead ends | [F-PRB-01](#f-prb-01), [F-NRM-02](#f-nrm-02), [F-BLK-04](#f-blk-04), [F-FEA-05](#f-fea-05), [F-MDL-01](#f-mdl-01), [F-CE-02](#f-ce-02) to [F-CE-04](#f-ce-04), [F-DEC-03](#f-dec-03), [F-RUL-05](#f-rul-05), [F-FRA-02](#f-fra-02), [F-FRA-03](#f-fra-03), [F-FRA-05](#f-fra-05), [F-LLM-01](#f-llm-01), [F-LLM-02](#f-llm-02) |
| Bugs | [F-EVL-09](#f-evl-09), [F-NRM-01](#f-nrm-01), [F-BLK-01](#f-blk-01), [F-BLK-03](#f-blk-03), [F-FEA-01](#f-fea-01) to [F-FEA-04](#f-fea-04), [F-MDL-02](#f-mdl-02), [F-RUL-01](#f-rul-01) to [F-RUL-03](#f-rul-03), [F-FRA-04](#f-fra-04) |
| Surprises | [F-EVL-01](#f-evl-01), [F-EVL-02](#f-evl-02), [F-BLK-02](#f-blk-02), [F-CE-01](#f-ce-01), [F-DEC-01](#f-dec-01), [F-FRA-01](#f-fra-01), [F-FRA-06](#f-fra-06), [F-LLM-03](#f-llm-03), [F-SUB-01](#f-sub-01), [F-SUB-06](#f-sub-06) |

## PRB: problem framing and data analysis

<a id="f-prb-01"></a>
### F-PRB-01 · Hunts for a hidden lever found nothing (dead end)
- **What:** On 27 Sep Ameya asked for 0.993, then 0.992. The agent for Ameya looked for a hidden gain of about 0.0015 and found none: no ID or file-order leak, no US/India shift on test (pairs per 1000 S1 within 1 to 3% of the holdout in every stage-3 pc band), and France has US/India's count structure (3.36 matches per S1 against 3.38) [M].
- **Found:** Direct checks on the finished candidates, 27 Sep 13:12 to 16:37.
- **Cost:** Agent time and no upload slot [R].
- **Learned:** The agent told Ameya the realistic target was 0.9907 to 0.9908. Composite B scored 0.990879 on the public LB [M]. A clean negative result ends the search for tricks.
- **Source:** [RESEARCH_v6 §6.18][r6]; [chat:ameya/19e315ba 2026-09-27 16:37].

**Smaller items in PRB**

| ID | what happened, how it was found, what it cost, what we learned | source |
|---|---|---|
| <a id="f-prb-02"></a>F-PRB-02 | The record total was quoted as 23.7M in AGENTS.md, `docs/DEVELOPMENT.md` and the plans. The measured count is 24,229,173 (train 12,527,040 plus test 11,702,133) [M]. Quote 24.2M. | [handover 25 Sep 14:25][h0925-1425]; [AGENTS.md][agents] |
| <a id="f-prb-03"></a>F-PRB-03 | The AWS blog from the problem statement is a client-rendered page and came back empty. A crawler user agent returned pre-rendered text with nothing on entity resolution. About 5 minutes [R]. | [chat:ameya/19e315ba 2026-09-25 11:05] |
| <a id="f-prb-04"></a>F-PRB-04 | The plan rubric (Plan A 3.9, Plan B 3.1) was scored by the coordinator, who wrote Plan A, and teammates' scores were left "half-done". The disputes between the plans were settled by full-data checks, not by the rubric. Stated here so the choice is described accurately. | [DECISION][plan-decision]; [handover 25 Sep 14:14][h0925-1414] |

## EVL: metric, holdout, gates, bootstrap, leaderboard probes

<a id="f-evl-01"></a>
### F-EVL-01 · The holdout had no France, so it hid a gap of 0.008 to 0.009 (surprise)
- **What:** v2 scored holdout 0.98436 and public LB 0.976081. v3 scored holdout 0.98882 and LB 0.979606. The gap grew from −0.0083 to −0.0092 [M]. Predicted matches per French S1 rose 3.31, 3.48, 3.54 against about 3.46 true [M]. The model's own France forecast (0.970) was far above the 0.93 the LB implied [E].
- **Found:** By comparing v2 and v3 test predictions per country (France gained 36k look-alike-signature pairs), by label-free checks that US/India on test behave like the holdout, and, once Ameya reported the scores (about 23:53), by solving LB = 0.85 × US/India + 0.15 × F_France.
- **Cost:** It redirected all of 26 Sep to France (F-FEA-02, F-FEA-03, F-RUL-01, F-FRA-01).
- **Learned:** A validation set that lacks a country in the test set cannot warn you about that country. We needed per-country label-free diagnostics from the first upload and a stand-in country. We built the stand-in (leave-one-country-out) only after the gap appeared (F-FRA-04).
- **Source:** [CHANGELOG][chg]; [ANALYSIS_v3][a3]; [handover 26 Sep 02:07][h0926-0207].

<a id="f-evl-02"></a>
### F-EVL-02 · Holdout and leaderboard ranked models differently whenever only France changed (surprise)
- **What:** v7n and v7nst have US/India levels within 0.00002 of each other (holdout 0.991211 and 0.991194), so the holdout prefers v7n. The LB preferred v7nst: 0.990179 against 0.989721 [M]. On 27 Sep the best holdout model (v7ensall2, 0.991256) again was not the best French model.
- **Found:** Bakshi's methodology draft recorded the reversal at 01:39 on 27 Sep; the morning candidates confirmed it.
- **Cost:** For France-only changes the holdout gate proved only that US/India had not moved. French choices rested on label-free checks and uploads.
- **Learned:** Gate US/India changes on the holdout and French changes on the LB, and write down which gate each change used.
- **Source:** [RESEARCH_v6 §6.7, §6.10][r6]; [LB 2026-09-26 #03][lb-0926-03]; [LB 2026-09-26 #04][lb-0926-04].

<a id="f-evl-03"></a>
### F-EVL-03 · The first label-free reads of the gap were wrong (estimator)
- **What:**
  - A parallel research session split the gap into France, a US pool-size effect (up to −0.0015) and blocking crowding (−0.0003 to −0.001) [E]. Re-measured on v6all, the extra US predictions are mostly correct (the half-size US test pool resolves more same-name ties) and crowding costs at most −0.00009 [M].
  - Two helper agents estimated France's level without labels. Transferring US/India truth rates per edit profile failed (France 0.80 to 0.85 against about 0.93 implied). A share-shift estimator matched v2/v3 (0.936 and 0.930 against 0.929 and 0.927) by coincidence: about 120 per 1000 French S1 counted as false positives were profiling artifacts (French domains with accents dropped, empty-address records). It forecast an LB of about 0.985 for v5all with rules; the LB was 0.98781 [M].
- **Found:** By re-measuring family by family (26 Sep 16:16), and by a second agent within 15 minutes (06:06).
- **Cost:** Hours of attention on two non-problems, and about one hour of a wrong forecast, corrected before any upload decision [R].
- **Learned:** Measure a mechanism before sizing it. Levels from label-free profiles were unreliable; differences between versions held up better.
- **Source:** [RESEARCH_v6 §1, §2.6][r6]; [RESEARCH_v5 §6, §8.2][r5]; [chat:ameya/agent-a000fd3b 2026-09-26 06:06].

<a id="f-evl-04"></a>
### F-EVL-04 · Offline French proxies could rank candidates but not size them (estimator)
- **What:** After self-training, the rule-population AUC saturated (0.9844, 0.9857 and 0.9846 for v7nst, v7nst2, v7mst), because the pseudo-labels contain those very populations. Its replacement, fhs, under-predicted the v7sq gain about 15 times (+30 units against +441 implied): it covered 1,516 of the 5,323 changed pairs and weighted all pairs equally, though under F0.5 a correct drop is worth 0.21 to 1.0 and a correct add 0.06 to 1.0. The offline forecast for v7sq-dpc was about 0.9903; the upload scored 0.990545, three times the forecast gain over v7nst [M].
- **Found:** In the overnight checks of 27 Sep, and by the France-diff agent after the 10:05 upload.
- **Cost:** Caution the data did not support. Bakshi had called 0.991 "unlikely" [R], and at 09:44 the agent told Ameya the gap was France and out of reach that day (F-SUB-07).
- **Learned:** Three methods on one gain: fhs saw 7% of it, per-category rates 30%, and the pc-band method (US/India truth by the new model's pc band, carried to France) 82%. Rank with a proxy; do not size with it.
- **Source:** [RESEARCH_v6 §6.14, §6.16, §6.17][r6]; [MODEL_CHOICE][b-choice]; [chat:ameya/agent-a2762d22 2026-09-27 11:34].

<a id="f-evl-05"></a>
### F-EVL-05 · Estimators built on our own probabilities were biased on decoys (estimator)
- **What:** The label-free French estimators (cal, own, s1) start from our model's probabilities. They valued round-3 France at +69e-6 over mixmdp's France; the LB gave −46e-6 (mixf7 against Composite B) [M]. They valued the look-alike drop at −20 to −31e-6 and the France decision layer at +15e-6; with the 7B's calibration the drop is neutral to mildly positive and the layer about +51e-6 [E]. Stage-3 pc is overconfident on the generic-name decoys the 7B rejects, so every pc-based estimator rewards putting them back.
- **Found:** Through the one-change uploads mixf7 and mixf2, about 21:55 on 27 Sep.
- **Cost:** Two of the last four uploads. For the round-3 family the estimators were 53 to 98e-6 too optimistic.
- **Learned:** Before the decoys appeared, cal had tracked past moves well (scale 0.96, mean absolute error 42e-6). An estimate built from the model's own probabilities needs an independent check, because it shares the model's blind spots.
- **Hindsight:** mixf7's France differs from Composite B's in the labels and model group, the look-alike drop and the decision layer. The 7B-calibrated split (+24e-6 for the round-3 model, +51e-6 for B's layer, the drop neutral) gives −27e-6, not the measured −46e-6. How the −46e-6 divides is not known (F-FRA-02).
- **Source:** [LB 2026-09-27 #05][lb-0927-05]; [RESEARCH_v6 §6.18, §6.20][r6]; [chat:ameya/19e315ba 2026-09-27 22:01].

<a id="f-evl-06"></a>
### F-EVL-06 · Forecast scoreboard: our forecasts missed in both directions (estimator)
Forecasts are [E]; scores are public LB [M].

| upload | forecast | measured | miss | source |
|---|---|---|---|---|
| v5all with France rules v2 | structural estimator about 0.985; leave-one-country-out route 0.990 to 0.992 (v4 at 0.987 to 0.989 plus 0.0027 for the rules) | 0.98781 | low by 0.003 and high by 0.002 to 0.004. v4 was never uploaded, so base and rules cannot be separated | [RESEARCH_v5 §6][r5]; [ANALYSIS_v4 §4][a4] |
| v7n | 0.9894 at France 0.976, 0.9900 at 0.980 | 0.989721 | on target | [LB 2026-09-26 #03][lb-0926-03] |
| v7sq-dpc | about 0.9903 | 0.990545 | low by 0.00025 | F-EVL-04 |
| mixmdp | about 0.99078 | 0.990699 | high by 0.00008 (look-alike drop valued at +57.8e-6 by one estimator, −26.7e-6 by another) | [LB 2026-09-27 #03][lb-0927-03] |
| Composite B | +149e-6 over mixmdp | +180e-6 | low by 31e-6 | [LB 2026-09-27 #04][lb-0927-04] |
| mixf7 | +69e-6 over B | −46e-6 | high by 115e-6 | [LB 2026-09-27 #05][lb-0927-05] |
| mixf2 (the agreed upload) | about 0.99091 | 0.990819 | high by 91e-6 | [LB 2026-09-27 #06][lb-0927-06] |

- **Learned:** Forecasts for changes the labels can see (US/India) held to about ±0.00004. For French changes they missed by 0.0001 to 0.0003, once in sign.

<a id="f-evl-07"></a>
### F-EVL-07 · The France level was never measured, so every French number is an estimate (process)
- **What:** No France-emptied probe was uploaded (F-SUB-05). Every France level in our records (about 0.93 for v2/v3; 0.971 to 0.976 for v5all; 0.973, 0.978, 0.981; about 0.983 and 0.984 for v7sq-dpc and mixmdp) comes from LB = 0.38274·F_US + 0.46751·F_India + 0.14975·F_France, with US/India set to the holdout re-weighted to the test's name-group mix [E]. If US/India on test sat 0.002 below the holdout, France for v5all would be 0.987, not 0.971 [E]. The formula also assumes the public subset has the test set's country mix (France is 14.9752% of test S1 [M]). An ID-range check supports that; we never verified it for the actual subset [U].
- **Found:** Stated in RESEARCH_v6 on 26 Sep; Bakshi tested the sensitivity on 27 Sep.
- **Cost:** Unknown. The levels were enough to rank variants but cannot be quoted as measurements.
- **Learned:** Quote France as "implied by the leaderboard formula, assuming the holdout level for US/India". Bakshi's "invariant gap" table does not remove this uncertainty (F-SUB-07).
- **Source:** [RESEARCH_v6 TL;DR, §3, §6.15][r6]; [handover 27 Sep 01:11][h0927-0111]; [CONFIDENT_SUBSTITUTIONS][b-conf].

<a id="f-evl-08"></a>
### F-EVL-08 · The evidence rules bent: holdout-tuned thresholds, and a gain bar nobody restated (process)
- **What:**
  - The baseline threshold, stage 1 and the threshold arm of gate G6 were tuned on the holdout they were scored on. The final all-of-train fit also uses the holdout as a fourth out-of-fold group, so it is no longer untouched (Bakshi's point). Out of sample, tuning the flat threshold gives −18.8e-6, while the expected-F0.5 rule gives +23.7e-6, positive in 86% of 42 splits [M].
  - The plan's keep rule was at least +0.002 with a 95% interval above 0 (+0.003 for heavy components). After v3 almost nothing met it. The cross-encoder gate passed at +0.0014 and was kept "for France"; later components were kept on a positive interval and positive halves (stage 3 +0.000051, v7n +0.000072, the decision rule +48.1e-6) [M].
- **Found:** Recognised on 25 Sep (rules tuned on folds 0 and 1, scored on 2 to 4); the bar by reading the gate records against the plan.
- **Cost:** No measured cost. A looser bar admits noise; halves A/B, repeated cross-validation and the tie rule (v7ensall2 withdrawn) limited it.
- **Learned:** Report an out-of-sample number beside every tuned one. When the validation set stops seeing the main risk, write the replacement bar down. In the records we read, the new bar is applied case by case and never stated once as a rule.
- **Source:** [FINAL_PLAN §5, §9][plan]; [decision model-v4][d-v4]; [decision stacked-rules][d-stack]; [CONFIDENT_SUBSTITUTIONS][b-conf].

<a id="f-evl-09"></a>
### F-EVL-09 · Competition statistics were computed on the wrong population, four times (bug)
- **What:** Ownership was taken over holdout S1 only in Sachi's first v0 run (the G6 decision and `run_real.py`), so rivals from the training folds were ignored, and again in our v6all loss ledger (187 records "owned by another S1" against 834). Two selection traps: on stage-2 candidates op-B pairs (one name word swapped in place at the S1's address) look 12 to 43% true in US/India, because stage 1 had removed most false ones (26 Sep 12:17); and restricting to pc at least 0.3 made same-address swaps look 99.9% true, when over all candidates they are 0.3 to 2.9% true (27 Sep 02:29).
- **Found:** The first in review of PR #16 at 17:43 on 25 Sep, fixed in PR #17 (Sachi's decision record says it was fixed before the recorded numbers, so sources differ on who caught it first). The others by the agents before any conclusion.
- **Cost:** Minutes each. The dev number moved from 0.9648 to 0.9652 after the first fix [R].
- **Learned:** Any per-record competition statistic must see every S1, as on test. Measure a population over all its candidates, never over the part the model already filtered.
- **Source:** [decision gate-g6][d-g6]; [RESEARCH_v6 §6.14][r6]; [chat:ameya/a2a1b62a 2026-09-25 17:43].

**Smaller items in EVL**

| ID | what happened, how it was found, what it cost, what we learned | source |
|---|---|---|
| <a id="f-evl-10"></a>F-EVL-10 | The pandas threshold sweep (27 `per_entity_f05` calls over 550k S1) was too slow. Replaced by FastEval (bincount) with identical results. | [chat:ameya/19e315ba 2026-09-25 18:14] |
| <a id="f-evl-11"></a>F-EVL-11 | A false alarm. A helper flagged that `ce_rule_auc.py` does not average tied scores. Bakshi measured it: it agrees with scikit-learn to four decimals even with 77.5% tied logits. Closed. | [TRACK_B_FINDINGS §3][b-trackb] |
| <a id="f-evl-12"></a>F-EVL-12 | Analysis-script slips caught before any conclusion. `unrel.py` returned empty tables twice (`name__len_r` counts tokens, not characters; `addr__tset` is on 0 to 100, not 0 to 1). A pair-key helper assumed 23 or 24-bit IDs while eids span 30 bits. `eval_hold2.py` failed on a duplicated label column. `fhs.py` crashed on an empty change list (`pa.array([])` has a null type) and on a candidate identical to its reference. Tag names must be lowercase (`mixA` became `mixa`). Minutes each. | [chat:ameya/19e315ba 2026-09-27 02:35]; [chat:ameya/19e315ba 2026-09-26 15:10]; [chat:ameya/19e315ba 2026-09-27 05:13] |

## ORG: team, process, repo, compute, GPU boxes, tooling

<a id="f-org-01"></a>
### F-ORG-01 · The integration laptop's memory limited the whole project (compute)
- **What:** The laptop (31 GB, about 20 GB usable) ran stages 1 and 2 at peaks of 16.5 to 20 GB. The v2 chain passed 18 GB (25 Sep, about 19:40). A diagnostic reached 25 GB (26 Sep 15:09). The first French acronym join left 0.9 GB free (18:49), and free memory fell to 102 MB during v7nst (22:54). A runaway alias test reached 21.8 GB (27 Sep 10:18). Helper agents also broke their budgets (10.2 GB; 12.7 GB with the main job). At 03:35 on 27 Sep the screen went black and the machine rebooted at 03:40, with an unclean-shutdown log and no crash dump. Stage 2 (16.5 GB), the acronym join (6 GB) and three analysis scripts (7 to 8 GB) had run together on a 42.6 GB commit limit with about 23 GB already committed at idle.
- **Found:** Ameya reported the blank screen at 03:44; the logs fit memory exhaustion.
- **Cost:** About 15 minutes. Nothing was lost, because artifact writes are atomic (temp file, then `os.replace`) and chains resume from step markers [R]. The 15 GB guard added afterwards stalled the queue at 13:03, 13:56 and 17:18, and the serial laptop chain was the afternoon's bottleneck [R].
- **Learned:** One heavy job at a time. A memory guard before stage 2, a PAUSE flag that keeps analysis scripts off during pipeline steps, 8,000 MB free before any agent launch, `s2.py --test-only`, and one sequential queue (27 Sep 18:24).
- **Source:** [handover 25 Sep 19:58][h0925-1958]; [RESEARCH_v6 §6.16][r6]; [chat:ameya/19e315ba 2026-09-27 03:44]; [chat:ameya/19e315ba 2026-09-26 22:54].

<a id="f-org-02"></a>
### F-ORG-02 · The tool's memory reaper stopped our background jobs and left the machine idle (compute)
- **What:** Claude Code's low-memory reaper stopped background shell wrappers on 25 Sep (about 19:40), 26 Sep (06:30, 12:02, five shells at 21:44) and 27 Sep (04:46, ten wrappers; 06:30). Only the wrappers died. The Python scripts under them kept running.
- **Found:** By the agent's own job checks after each event.
- **Cost:** The 06:30 event on 26 Sep cost about 4.7 hours of idle compute (06:37 to 11:19). Under the standing rule nothing was restarted without Ameya's go-ahead, and he was away. The v6nx result sat in a report from 06:38 [R].
- **Learned:** Run long jobs detached with a done marker per step (`run_v6all.sh` became resumable). Give the agent standing permission to resume idempotent chains.
- **Source:** [handover 26 Sep 11:23][h0926-1123]; [chat:ameya/19e315ba 2026-09-26 06:31]; [chat:ameya/19e315ba 2026-09-27 04:48].

<a id="f-org-03"></a>
### F-ORG-03 · Interruptible rented machines were taken away twice (compute)
- **What:** About 21:40 on 26 Sep the rented spot box stopped answering, and its disk was not persistent. Lost: the bge logits, the v7c, v7m and v7mst stage-2 scores and the running self-trained e5-large. A second box went down at about 23:10 [R]. About 15:05 on 27 Sep Bakshi's interruptible 4×H100 box was taken away during the 7B run.
- **Found:** An `scp` "connection reset" while downloading v7m's scores; the second box disappeared.
- **Cost:** v7m, with the best French rule-population AUC (0.878), was never shipped; v7n without bge (0.872) went instead [M]. bge was retrained that night on an on-demand H100. The 7B resumed from Drive checkpoints (steps 4,321, 6,561, 4,371) on a slower box (2.3 against 3.6 steps per second) and was merged at about 17:10 [R].
- **Learned:** Use on-demand machines for anything that must finish. Copy outputs back as they land and checkpoint to off-box storage every few minutes (Bakshi's ran every 5). The file we missed most, bge's logits, was 20 MB.
- **Source:** [RESEARCH_v6 §6.9][r6]; [decision model-v7n][d-v7n]; [HANDOFF][b-handoff]; [chat:ameya/19e315ba 2026-09-26 21:41].

<a id="f-org-04"></a>
### F-ORG-04 · One non-finite gradient poisoned the cross-encoder runs on the new boxes (compute)
- **What:** Both runs on the two new boxes (PyTorch 2.11, CUDA 12.8, transformers 5.17) printed normal progress but logged NaN loss from step 1000. One non-finite gradient at step 305 had poisoned the weights. On Bakshi's boxes mDeBERTa-v3 (bf16, non-finite gradients) and gte-multilingual (an index assertion under transformers 5.17) failed that day for related reasons.
- **Found:** By the agent while the runs were going (23:59), traced to step 305 by 00:16. The sources do not say what first showed it.
- **Cost:** About 35 minutes of H100 time plus debugging [R]. The fix skips non-finite steps (0.7% of batches skipped early on); throughput fell to 394 pairs per second, about half of box 1.
- **Learned:** Guard every training loop against non-finite gradients, log the step of the first one, and show loss finiteness in the progress line.
- **Source:** [chat:ameya/19e315ba 2026-09-26 23:59]; [chat:ameya/19e315ba 2026-09-27 00:16]; [HANDOFF][b-handoff].

<a id="f-org-05"></a>
### F-ORG-05 · Track B was closed on missing files, then reopened (process)
- **What:** Track B was Bakshi's plan to rebalance the cross-encoder mix by model family. At about 02:00 on 27 Sep `out_bge` did not exist (lost with the spot box), only two e5-large runs correlated at +0.9757 remained [M], and he closed Track B. When bge arrived, round 2 (about 02:30) found a better French mix and round 3 added a labelled US/India gate and recommended the equal three-way mix v7mst already used. His first estimate for adding bge, +0.000256 LB, was probably too high: v7mst moved only 8 French final predictions per 1000 S1 against v7nst, where v7n to v7nst moved 31 [M].
- **Found:** By Bakshi's own rounds. Ameya's review corrected the estimate (issue #45, PR #54).
- **Cost:** None.
- **Learned:** In Bakshi's words, round 1 was "right about the artifacts then in hand and wrong as a conclusion about the hypothesis". Say "untested", not "no headroom", when an artifact is missing. Gains measured at the cross-encoder level shrink once stage 2 is self-trained.
- **Source:** [TRACK_B_FINDINGS][b-trackb]; [ledger][b-ledger]; [RESEARCH_v6 §6.14][r6].

<a id="f-org-06"></a>
### F-ORG-06 · Full-scale artifacts did not travel to the teammates who needed them (process)
- **What:** Scores, features, candidates and matches lived on the integration laptop. Bakshi was blocked three times: 26 Sep 15:45 (the v6 files were "absent locally and in checked GitHub locations", so he audited the v3 dev kit only and claimed no gain); 27 Sep 01:11 (the v7nst candidate file, so no valid package until Ameya delivered it at 01:50); 27 Sep 11:00 to 12:00 (the v7sq-dpc candidate file). His laptop could not run the chain anyway: no torch, a 4 GB GPU, 16 GB of RAM against stage peaks of 18 to 19 GB.
- **Found:** By Bakshi's agent, repeatedly, through `ARTIFACT_REQUEST` lists.
- **Cost:** A valid package for the best model waited on file transfers, and Track B's downstream fit and a clean rerun could not run locally.
- **Learned:** "Code moves, data doesn't" breaks once a member must audit full-scale outputs. A team drive link was already an open blocker in the 25 Sep 14:14 handover. On 27 Sep Bakshi rebuilt the whole pipeline on rented boxes instead (it reproduced v7sq-dpc: holdout 0.991261 against 0.991246, band coverage 99.9999% [M]) with 5-minute backups to a shared Drive folder.
- **Source:** [handover 26 Sep 15:45][h0926-1545]; [handover 27 Sep 01:11][h0927-0111]; [ARTIFACT_REQUEST][b-art]; [handover 27 Sep 20:06][h0927-2006]; [handover 25 Sep 14:14][h0925-1414].

<a id="f-org-07"></a>
### F-ORG-07 · Work that did not reach the submission (process)
- **What:** Bakshi's normalisation stage (PR #20, about 3 hours late, with parsing bugs found in review, F-NRM-01) and string-feature stage (56 features, 73 s per 100k pairs or about 13 hours per split, first tested only on true matches, later 3.6 minutes per 3.2M pairs, value never gated) were not read by the final chain. It ran on `experiments/ameya/model-v1`. Sachi's `ber.model` path stayed at v0; PR #27's text promised a full v3 port that is in no branch we checked [U]. Her own Qwen2.5-1.5B run (`out_q15`) never reached the integration machine, so it has no recorded result, though her LoRA code is the core of both Qwen cross-encoders in the final. Plan C was never submitted. The repo rule that anything the final pipeline needs must live in `src/ber/` was not followed: the model chain stayed in `experiments/` and shipped in the ZIP as `src/model_v1`.
- **Found:** By comparing the final chain with the plan and the GitHub timestamps.
- **Cost:** Effort. No score effect was measured. The chain moved faster than the shared package could follow, and `ber.model` loads about 19 GB at full scale.
- **Learned:** Parallel stages need an integration owner and a test that the next stage reads their output. Define "done" as "used by the chain".
- **Source:** [handover 25 Sep 16:58][h0925-1658]; [handover 25 Sep 20:56][h0925-2056]; [TRACK_B_FINDINGS][b-trackb]; [experiments README][exp-readme]; [issue #6]; [issue #7].

**Smaller items in ORG**

| ID | what happened, how it was found, what it cost, what we learned | source |
|---|---|---|
| <a id="f-org-08"></a>F-ORG-08 | Orphans and over-broad kills. `TaskStop` on Windows stops only the wrapper shell, so orphan scripts kept running: a stale duplicate chain would have built v7sq twice (found 02:20 on 27 Sep), and the box round-2 chain was launched twice (13:08). A `taskkill` on 26 Sep (20:56) ended every `python.exe` on the laptop; nothing else of ours was running. The laptop also started v7sq5g's stage 2 first, so the box's finished copy was declined as "TOO LATE" (13:04). Fix: kill by verified process ID only. | [chat:ameya/19e315ba 2026-09-27 02:20]; [chat:ameya/19e315ba 2026-09-26 20:56]; [chat:ameya/19e315ba 2026-09-27 13:08] |
| <a id="f-org-09"></a>F-ORG-09 | Script control. A running shell script cannot be edited in place (an edit of `final_night4.sh` left a syntax error, caught by `bash -n`), so every change went into a new file. A pause guard raced with a new stage 2 (fixed 04:22), and after a takeover stale "START s2" log lines kept the pause on until "KILLED" lines were added. Process checks matched themselves (a `pgrep` saw its own command line, 12:04). Fix: the `[t]ag` pattern trick and `ps -ef` with `awk`. | [chat:ameya/19e315ba 2026-09-27 02:21]; [chat:ameya/19e315ba 2026-09-27 04:22]; [chat:ameya/19e315ba 2026-09-27 06:16] |
| <a id="f-org-10"></a>F-ORG-10 | Shell, path and line-ending traps. Bash `GROUPS` is a reserved variable, so stage 2 looked for a feature file named after the user's group id (8 minutes, 26 Sep 19:02). MSYS `/c/...` paths and `:` against `;` separators confuse native Windows Python (Bakshi hit the same). Windows Python wrote CRLF into a box script (27 Sep 14:49) and nearly changed `scripts/setup.ps1`, which must stay CRLF (25 Sep 21:41). Fix: write files with explicit LF line endings. | [chat:ameya/19e315ba 2026-09-26 19:02]; [chat:ameya/19e315ba 2026-09-25 21:41]; [chat:ameya/19e315ba 2026-09-27 14:49] |
| <a id="f-org-11"></a>F-ORG-11 | Rented-box operations and hardware. `cat > file` over a remote shell produced empty files; `pkill -f` killed the remote session; a `nohup … &` kept it open until stdin was redirected; a missing trailing newline in the start-up script and the key-list file glued an appended line on, and a key was refused (27 Sep 14:19). The torch build depends on the driver. One GPU throttled at 86 °C. Uploads to the second box ran at 3 to 6 MB/s, so stage 2 could not move there. The "4090" rented on 27 Sep was an RTX 5090. A "stuck" box of Sachi's was a tmux pane full of arrow-key escape codes; the job was healthy. Bakshi's HANDOFF lists the lessons. | [HANDOFF][b-handoff]; [chat:ameya/19e315ba 2026-09-27 14:19]; [chat:ameya/a2a1b62a 2026-09-27 01:04] |
| <a id="f-org-12"></a>F-ORG-12 | Moving files. The Google Drive upload failed on 26 Sep (12:27): no Drive for desktop or rclone, and the Claude Drive connector was not signed in and is built for documents, not 200 MB of parquet. Ameya dragged the files in by hand. Later rclone could not see a Drive folder shared by link only; it worked with the folder ID. | [chat:ameya/19e315ba 2026-09-26 12:27]; [chat:ameya/a2a1b62a 2026-09-27 14:45] |
| <a id="f-org-13"></a>F-ORG-13 | Harness and session limits. Sub-agents cannot write `.md` reports, so reports came as final messages. The usage limit paused sub-agents (27 Sep 15:28 to 16:44), the context needed compacting three times, the API connection dropped mid-response (15:59), and "Prompt is too long" hit on 29 Sep at 01:08. A foreground `sleep` is blocked. `git worktree remove` gave "Permission denied". Local `main` was 53 commits behind `origin/main` when a summary agent read it. Work resumed from transcripts and handovers. | [chat:ameya/19e315ba 2026-09-27 04:06]; [chat:ameya/19e315ba 2026-09-27 15:28]; [chat:ameya/agent-aadeeaba 2026-09-26 14:46] |
| <a id="f-org-14"></a>F-ORG-14 | Pull-request and repo hygiene. PR #15's "Closes #10 (v0 part)" closed issue #10 (reopened). Rebase-merge changes commit hashes (Sub 1 came from `55ef718`; the main commit `158f124` is the one to tag). CI lacked numba, so it became a core dependency. The dev kit was not shared for about 10 minutes (no team drive link) and went out as a GitHub pre-release. PR #67 merged with no file changes; PR #68 fixed it. PR #52's merge ran before CI registered; the agent waited rather than use `--admin`. Sachi pushed onto Ameya's PR branch, into Bakshi's folder (two one-writer breaches), handled with a normal commit after verification. | [chat:ameya/19e315ba 2026-09-25 17:09]; [chat:ameya/19e315ba 2026-09-25 17:15]; [chat:ameya/19e315ba 2026-09-27 01:44]; [PR #67]; [PR #68] |
| <a id="f-org-15"></a>F-ORG-15 | On Bakshi's machine 13 tests errored because the temp directory belonged to another Windows account, and git needed `safe.directory` entries. Neither was a code failure. Fix: `--basetemp` somewhere writable. | [handover 27 Sep 01:11][h0927-0111]; [PR #50] |
| <a id="f-org-16"></a>F-ORG-16 | Helper-agent slips, all caught by the parent session or by rebuild checks. A brief gave v7nst's threshold as 0.70 while `decide.py` had picked 0.675. The polish agent mislabelled 5 of 21 French acronym adds. The decide agent's DP overwrote the hunt's US/India changes. A wait condition matched too early ("holdout F done") on a box job. Two agents ran sub-second Python while the PAUSE flag was set. See also F-DEC-03 and F-RUL-03. | [chat:ameya/agent-acec839c 2026-09-27 04:24]; [chat:ameya/agent-a2762d22 2026-09-27 14:11] |

## NRM: normalisation, lexicons, transliteration

Normalisation produced only small items.

| ID | what happened, how it was found, what it cost, what we learned | source |
|---|---|---|
| <a id="f-nrm-01"></a>F-NRM-01 | Bakshi's normaliser (PR #20) gave "123 N Main St" the suffix "n" and "3 R. de la Paix" the suffix "r", stripped legal forms at the start of a name ("SA Engineering Works" became "engineering works") and parsed "75002 Paris Cedex, Gironde" with the city "gironde". Found in review by the agent in Ameya's parallel session (25 Sep, about 20:56). No score effect, because no stage read these columns (F-ORG-07). Hindsight: the same street-type confusion hit our own key (F-FEA-04); French and Indian addresses need their own test cases from the first version. | [chat:ameya/a2a1b62a 2026-09-25 20:56]; [handover 25 Sep 16:58][h0925-1658] |
| <a id="f-nrm-02"></a>F-NRM-02 | Honorific stop words (sree, shree, om, maa) stripped short names of their only distinctive word ("Om Services Private Limited"). On the dev pool they lost 95 true pairs and found 64 [M]. Found by the before-and-after count; reverted before the rebuild. Lesson: judge every word-list change by true pairs found against lost. | [decision blocking-v3-repairs][d-blk3] |
| <a id="f-nrm-03"></a>F-NRM-03 | RE2 has no backreferences (the skeleton run-collapse is done letter by letter) and no negative lookahead (skip words were blanked first, which caused the "1\|hno" bug). Python `\b` after a placeholder dropped the inherent "a" ("venchrs"). pyarrow has no `binary_join` kernel for (large_string, string), and an `ArrowNotImplementedError` was mistaken for "stage not implemented". Minutes each. | [chat:ameya/19e315ba 2026-09-25 17:28]; [chat:ameya/19e315ba 2026-09-25 19:29] |

## BLK: blocking and candidate generation

<a id="f-blk-01"></a>
### F-BLK-01 · The first uploads carried the wrong candidate file (bug)
- **What:** `candidate_pairs.tsv` was the raw blocking output (34.0 pairs per test S1, 781 MB), not the set the matching model scores, which the README asks for. The corrected file is the stage-2 input: 4.75 per S1, 129 MB, holdout pair recall 0.98992 → 0.98926 and oracle F0.5 0.99697 → 0.99676 [M].
- **Found:** By the candidates helper agent re-reading the README, 26 Sep 00:12 to 00:41.
- **Cost:** No score effect then, since the README said only matches were scored [R]. The 25 Sep uploads, v2 and v3 among them, carried the wrong file.
- **Learned:** Check each deliverable against the organisers' definition of it, not against its name.
- **Source:** [ANALYSIS_v3 §6][a3]; [handover 26 Sep 02:07][h0926-0207]; [chat:ameya/19e315ba 2026-09-26 00:41].

<a id="f-blk-02"></a>
### F-BLK-02 · The organisers made the candidate file part of the ranking (surprise)
- **What:** On 26 Sep (about 05:10) the organisers announced that the candidate file and its code are reviewed, and that "the approach that generates a smaller candidate set per Source 1 entity will be ranked higher in the final evaluation beyond the public/private leaderboard". Our file had 4.68 pairs per test S1. We cut it to 3.70 (stage-1 p1 at least 0.02 and the pair among its record's top 2 S1). On 27 Sep the rule was repeated and the candidate agent confirmed that 3.70 stays.
- **Found:** The organisers' announcement.
- **Cost:** On v5all the cut lowered set recall from 0.98927 to 0.98198 and oracle F0.5 from 0.99676 to 0.99452. The decision layer lost nothing measurable: holdout 0.990159 → 0.990156, Δ −0.000003 [−0.000015, +0.000011] [M]. Every tighter cut lost F0.5: the record's top 1 S1 −106e-6, p1 at least 0.05 −41e-6 [M].
- **Learned:** A deliverable's scoring rule can change mid-competition. The cut was cheap only because the lost headroom was headroom our decision layer did not use.
- **Source:** [decision candidate-set-cut][d-cut]; [RESEARCH_v6 §6.18][r6]; [chat:ameya/19e315ba 2026-09-27 12:45].

<a id="f-blk-03"></a>
### F-BLK-03 · Blocking v3 lost 2,186 French predictions (bug)
- **What:** Blocking v3 (domain, OCR-digit and ordinal repairs) raised holdout pair recall from 0.98992 to 0.99135 [M]. But 2,186 French predictions of v5all (8.4 per 1000 French S1) were no longer candidates: 953 acronyms at the S1's address, 520 brand-name or domain records and about 100 list-word copies. These match their S1 through the address only. French house numbers are small and street names common, so small score shifts pushed the true S1 out of the record's top 4. About −0.0006 France F0.5 [E].
- **Found:** By the France diff against the uploaded v5all, 26 Sep 18:04.
- **Cost:** Not separated on the LB. The acronym join (F-RUL-03) partly recovered the acronyms. An exact-address view would recover the rest but finds only 516 missed true pairs on the holdout (+0.00007), so it was not built [M].
- **Learned:** A change that gains on the holdout can lose on the country the holdout lacks. Diff the unlabelled country's predictions after every rebuild.
- **Source:** [RESEARCH_v6 §4][r6]; [chat:ameya/19e315ba 2026-09-26 18:04].

**Smaller items in BLK**

| ID | what happened, how it was found, what it cost, what we learned | source |
|---|---|---|
| <a id="f-blk-04"></a>F-BLK-04 | Dead ends and unbuilt parts. Prefix keys of the joined name: median 885 S1 per key, so they would not seed [M]. An exact-address view: +0.00007. A domain-key join: about 110 free French records. Never built: the GPU TF-IDF/SVD views (gate G2 never ran), the learned pre-ranker (G11) and the owner-removed softmax (G5; "taken by another S1" is 0.26% of true pairs). Blocking stayed an exact sparse IDF token-overlap search, and blocking v3 reaches holdout pair recall 0.99135 before the cut [M]. | [decision gate-g1-blocking-v2][d-g1]; [RESEARCH_v6 §4][r6]; [decision gate-name-uniqueness][d-uniq]; [handover 25 Sep 17:06][h0925-1706] |
| <a id="f-blk-05"></a>F-BLK-05 | The first full blocking run hung on a single-threaded pandas sort over about 110M rows, and its test half would have used newer code. Stopped at 16:20 on 25 Sep and re-run with a numpy lexsort on both splits (about 10 minutes [R]). `trim_curve` would have dropped name-only pairs; rewritten with a keep mask. | [chat:ameya/19e315ba 2026-09-25 16:20]; [chat:ameya/19e315ba 2026-09-25 16:36] |

## FEA: pair features

<a id="f-fea-01"></a>
### F-FEA-01 · Legal forms were invisible to every feature (bug)
- **What:** The blocking tokenizer drops legal forms (SAS, Inc, Pvt Ltd) on purpose, and the pair features reused it. But look-alikes add or change a legal form: 62% of orphan false positives against 6.5% of true pairs [M]. Legal-form features lifted the holdout from 0.98436 to 0.98708 (+0.00271 [0.00260, 0.00283]) [M].
- **Found:** By the error analysis of model v2, 20:45 on 25 Sep.
- **Cost:** About 0.0027 holdout F0.5 for the first models. The fix then hurt France (F-FEA-02).
- **Learned:** Features need their own tokenization. Reusing the blocking one hid the strongest look-alike signal.
- **Source:** [handover 25 Sep 21:47][h0925-2147]; [ANALYSIS_v2][a2].

<a id="f-fea-02"></a>
### F-FEA-02 · The legal-form fix that won on the holdout hurt France (bug)
- **What:** French legal forms (SAS, SASU, SARL, EURL, SNC, SCI, SA) sit in bits 12 to 19 of the bitmask, values of 4096 or more, found in 0.08% of train rows and 6 to 8% of test rows [M]. French look-alikes that added or changed the legal form and moved the house number scored 0.456 on average at stage 1, but 0.027 with the bits zeroed [M]. About 12.2k such pairs were predicted in France, 9 times the US/India rate per prediction [M].
- **Found:** By the pipeline-audit helper agent and a stage-1 re-scoring test on 59k French pairs, night of 25 to 26 Sep.
- **Cost:** Part of France's implied 0.93 on v2/v3 [E]. v4 dropped the bitmasks from stages 0 to 2 and kept the relation features.
- **Learned:** A feature value never seen in training works as a country feature, even in a model with no country feature. Check each feature's range on the unlabelled country before shipping.
- **Source:** [ANALYSIS_v3 §2, §7][a3]; [decision model-v4][d-v4].

<a id="f-fea-03"></a>
### F-FEA-03 · Unseen look-alike words counted as neutral, and "no statistics" was encoded differently on train and test (bug)
- **What:** The word-odds table (`lo`) gave words never seen in training the value 0, so French descriptors ("Participations", "Développement", "Groupe", "Amicale") looked like noise. Separately, "no statistics" was −1.94e-16 on train and holdout rows and exactly 0.0 on test rows. A classifier told train from test with AUC 0.95, and 11 to 14% of test predicted pairs were affected against none on the holdout [M]. Leave-one-country-out sized the first problem: a US-only model scored India at 0.961 with India's words known and 0.882 with them unseen [M].
- **Found:** The word-odds limitation was noted on 25 Sep (19:08); the pipeline-audit helper agent found the sentinel mismatch on 26 Sep.
- **Cost:** Part of France's implied 0.93 [E]. v4 fixed both: label-free proxy odds (F-FRA-04) and exact zeros (`lo0`).
- **Learned:** Write sentinel values exactly.
- **Hindsight:** Run the train-versus-test classifier before the first upload, not after the gap appears.
- **Source:** [ANALYSIS_v3 §3, §7][a3]; [decision model-v4][d-v4].

<a id="f-fea-04"></a>
### F-FEA-04 · The (number, street) key took the street type in France (bug)
- **What:** The key that counts how many S1 share a house number and street took the first address word, which in France is the street type: "32 Rue André Maginot" became `32|r`, about 450 S1 per key on test, far outside the training range. On reordered records it took the state. PR #18 changed it to the first word after the house number, skipping street types, articles and house markers (used from v3). A follow-up crash: `numstreet_keys` used a plain-string separator on large_string columns (25 Sep 21:58), fixed with type-matched scalars and a test.
- **Found:** While inspecting French feature values (25 Sep 19:28); the crash at build time.
- **Cost:** About 10 minutes for the crash [R]. The v2 features carried the wrong key.
- **Learned:** Read French feature values by eye. The bug was visible in a handful of rows.
- **Source:** [handover 25 Sep 19:58][h0925-1958]; [PR #18]; [chat:ameya/19e315ba 2026-09-25 19:28].

**Smaller items in FEA**

| ID | what happened, how it was found, what it cost, what we learned | source |
|---|---|---|
| <a id="f-fea-05"></a>F-FEA-05 | Ideas measured and dropped. Name-uniqueness features (Sachi): Δ +0.00054 [+0.00001, +0.00107] against the +0.002 bar. The useful finding: of true pairs with an empty record address, exact unique names were already found at 95.8%, and names shared by two or more S1 are ambiguous by construction, so abstaining is right under F0.5. The SHAP agent's two French biases: dual-use list words ("groupe", "france", "developpement") got the proxy value −4.84 as if pure look-alike words (a cap at −1.25 would add about +0.0004 France F0.5 [E], but the US holdout loses −0.00106 if "partners" gets the proxy value), and a depressed retrieval margin (a label-free re-score changed +4,460 / −1,423 French predictions, mixed, uncheckable without a retrain). Neither explained the missing 0.01. Lesson: a diagnosis can be real and too small; size a fix before building it. | [decision gate-name-uniqueness][d-uniq]; [RESEARCH_v6 §2.9][r6] |
| <a id="f-fea-06"></a>F-FEA-06 | The signed house-number features were predicted to "add little" (04:37 on 26 Sep). At 11:24 they gave +0.00021 [0.00016, 0.00025] on the holdout (US +0.00029, India +0.00007) [M] and stayed. | [ANALYSIS_v4 §3.1][a4]; [handover 26 Sep 11:23][h0926-1123] |
| <a id="f-fea-07"></a>F-FEA-07 | In `feats_nx.py` a digit swap and a substitution can give the same numeric difference (123 to 132 and 123 to 153). Rewritten as a digit-by-digit comparison (26 Sep 05:46). | [chat:ameya/19e315ba 2026-09-26 05:46] |
| <a id="f-fea-08"></a>F-FEA-08 | Rarity and rival-count features depend on pool size (test US has half of train US's S1; US predicts +0.022 matches per S1 above the holdout). The audit estimated −0.0002 to −0.0004 [E]. Later checks found the extra US predictions mostly correct (F-EVL-03). Left open. | [ANALYSIS_v3 §7][a3]; [handover 26 Sep 02:07][h0926-0207] |

## MDL: XGBoost stages 0 to 3, calibration, out-of-fold training

The model stages produced only small items.

| ID | what happened, how it was found, what it cost, what we learned | source |
|---|---|---|
| <a id="f-mdl-01"></a>F-MDL-01 | Tuning the learner gave nothing. Stage-2 seed bagging −0.00004; `max_depth` 8 and learning rate 0.03 no gain; a 4-model stage-3 bag +5e-6 [−11, +21]. A 7-model bag (v7ensall2) tied v7sq on expected LB (0.990299 against 0.990295 [E]) and was withdrawn under the tie rule. US/India converged at holdout 0.991280 to 0.991307 [M]. Lesson: once US/India is near its limit, extra information (cross-encoders, the 7B, the decision layer) moved the numbers, not tuning. | [RESEARCH_v6 §6.1, §6.16, §6.18][r6]; [MODEL_CHOICE][b-choice] |
| <a id="f-mdl-02"></a>F-MDL-02 | Stage 3: the best of three prototype variants gained +0.00011 on the holdout, and the module gave +0.000051 [+0.000023, +0.000079] [M]. The first leakage rule excluded every record with a holdout S1 among its roughly 34 blocking candidates, which removed 93% of records; the final rule uses the final candidates (1.96M of 8.24M records excluded). Found by the helper agent that built it (26 Sep 06:27). Lesson: the best of several prototypes is optimistic, and a leakage rule must be defined on what the stage sees. | [handover 26 Sep 11:23][h0926-1123]; [decision rules-v3-and-stage3][d-rules3]; [chat:ameya/agent-a2066847 2026-09-26 06:27] |
| <a id="f-mdl-03"></a>F-MDL-03 | v7sq6wg's memo figure of 0.991320 did not reproduce. Under the combo rule it is 0.991306, because its stage 3 had already chosen by expected F0.5 (27 Sep 14:57). | [chat:ameya/19e315ba 2026-09-27 14:57] |

## CE: cross-encoders

<a id="f-ce-01"></a>
### F-CE-01 · Accuracy on the labelled countries did not predict a cross-encoder's value on France (surprise)
- **What:**
  - e5-small was below stage-1 p1 in its own band (AUC 0.9240 against 0.9297 in the v6all band [M]; 0.928 against 0.932 in the first run [R]) yet added +0.00140 [0.00131, 0.00148] as a stage-2 feature and halved French look-alike acceptances.
  - A second e5-large epoch raised the holdout band AUC from 0.9391 to 0.9441 and lowered the French rule-population AUC from 0.803 to 0.792. It specialises on the training countries.
  - bge-reranker is the weakest single model on France (0.774) yet lifted the French mean most: e5-large twice plus bge 0.826 against 0.806. Its errors are decorrelated, and it accepts the fewest French pairs (share with logit above 0: 0.302 against 0.369), a sign of domain shift.
  - Averaging the two e5-large runs lowered the US/India band AUC (0.9429 against 0.9441) and raised the French check (0.806 against 0.792). v7b was stopped on the US/India number, and v7n used the mean anyway.
  - The 7B ties e5-large on band AUC (0.9436 against 0.9439). Counted twice in the mix it still gave g1w holdout 0.991323 against 0.991261 without it [M].
- **Found:** By reading the label-free French checks and the labelled gates side by side. Bakshi's labelled gate showed that the French-best mix (e5-large plus bge) costs 0.00114 band AUC on US/India.
- **Cost:** Mix decisions rested on two scales that disagreed. Bakshi put both on one LB scale: the spread across the best 40 weightings was only 0.000048.
- **Learned:** Judge a cross-encoder by what it adds to the mix on both sides, not by its own AUC. Family diversity mattered more than accuracy.
- **Source:** [RESEARCH_v6 §6.5, §6.6, §6.11, §6.13][r6]; [FINAL_PUSH_RESULTS §2][b-final]; [TRACK_B_FINDINGS][b-trackb].

<a id="f-ce-02"></a>
### F-CE-02 · Round-2 cross-encoder labels drifted (dead end)
- **What:** v7sq5g retrained a French self-trained e5-large on the guarded v7sq labels. It was negative for France under every valuation (s1 −6, own −13, s2 −53 F-units) and reverted more LB-confirmed moves than any other variant. Its US/India gate passed. Guarded round-2 labels at stage 2 did help (F-FRA-02).
- **Found:** By the three label-free valuations, 27 Sep afternoon. Ameya had already warned Bakshi.
- **Cost:** About 6,951 s of H100 time plus a full chain [R].
- **Learned:** Feedback into the cross-encoder is riskier than feedback into stage 2, even with the guards.
- **Source:** [RESEARCH_v6 §6.18][r6]; [HANDOFF][b-handoff].

<a id="f-ce-04"></a>
### F-CE-04 · Synthetic French cross-encoders raised the estimate by undoing what the leaderboard had confirmed (dead end)
- **What:** The first two synthetic-pair generators mis-weighted the French operations. synth2 labelled copies whose house number moved by −1 or −2 as non-matches, though 89% of them are true on the holdout. Sachi's `ce_synth.py` also crashed in `encode_synth` (fixed in `ce_synth2.py` and PR #68). With synth3 matched to the real mix, six synthetic cross-encoders gave the best cal values (+249e-6 and +293e-6 [E]) but own-cal values of +51 and +3. They reverted 1,182 and 1,576 LB-confirmed moves, and v7sqsyd lost −43e-6 on the US/India holdout. The e5-base detector was badly miscalibrated on France (7,263 French flags at logit −5 against 39 on the holdout), and the bge detector's extra flags were real copies. None was used.
- **Found:** By the France-diff agent's valuations and holdout checks, 27 Sep 17:00 to 20:25.
- **Cost:** The runs on Bakshi's idle boxes were stopped after 15 to 30 minutes (17:24). The H100 ran out of memory because two synthetic cross-encoders held 78 of its 80 GB (18:32).
- **Learned:** Measure the real operation mix before generating data. Synthetic cross-encoders raised cal by reverting what the leaderboard had confirmed.
- **Source:** [RESEARCH_v6 §6.19][r6]; [handover 27 Sep 20:14][h0927-2014]; [issue #63]; [PR #68]; [chat:ameya/agent-a2762d22 2026-09-27 17:15].

**Smaller items in CE**

| ID | what happened, how it was found, what it cost, what we learned | source |
|---|---|---|
| <a id="f-ce-03"></a>F-CE-03 | More French-heavy or self-trained members added nothing, or lost copies. e5fr and bgefr (band AUC 0.918 to 0.926) added nothing measurable. The weight on guarded labels saturated (×5 +167e-6 against ×3 +166e-6 [E]). Each extra French self-trained cross-encoder lost more true copies against v7nst (v7sq −2.04, v7sq3 −2.83, v7sq2 −3.20 per 1000 French S1), mostly empty-address copies the `copy` rule cannot win back [M]. Bagging only damped the French changes. Lesson: after the first guarded rounds, more French signal came from different information (the 7B), not from more members of one kind. | [RESEARCH_v6 §6.16, §6.18][r6] |
| <a id="f-ce-05"></a>F-CE-05 | The Qwen predict loop lacked `no_grad` (about 1.3 times slower). Not fixed mid-run, to keep a finished 61-minute group. | [chat:ameya/19e315ba 2026-09-27 02:11] |

## DEC: the decision layer

<a id="f-dec-01"></a>
### F-DEC-01 · The expected-F0.5 decision lost on stage-1 probabilities (surprise)
- **What:** Choosing each S1's set by expected F0.5 should beat one threshold in theory. On the first probabilities it did not: Sachi's dev kit v0 Δ −0.00024 [−0.00091, +0.00049]; Ameya's stage 1 −0.00029 [−0.00040, −0.00018]. On stage-2 probabilities it won: +0.00027 [+0.00020, +0.00036] (model v1) and +0.00018 [+0.00009, +0.00026] (model v2). On Sachi's dev kit with v2 probabilities it was +0.00010 [−0.00023, +0.00045], still under the bar [M].
- **Found:** By Sachi's G6 gate (17:31) and Ameya's chain (18:43), 25 Sep.
- **Cost:** None. The threshold stayed until stage 2 existed.
- **Learned:** The per-S1 calculation assumes independent candidates, so it needs calibrated probabilities that already know about rivals. Stage 2 supplies that.
- **Source:** [decision gate-g6][d-g6]; [handover 25 Sep 19:58][h0925-1958].

<a id="f-dec-02"></a>
### F-DEC-02 · "Already optimised" was wrong (process)
- **What:** At 02:53 on 27 Sep research note §6.15 called the per-S1 decision rule already optimised, because stage 3 compared the flat threshold with the plain expected-F0.5 rule and found +0.00003 [−0.00002, +0.00007]. By 04:24 the decide agent showed that the rule with a logit shift (+0.2), a phantom term for matches outside the candidate set (0.01) and a crowd shift (−0.3 for records that four or more S1 compete for) beats the threshold: +48.1e-6 [+7.1, +91.2] on v7s, and +23.7e-6 out of sample [M].
- **Found:** By the decide agent, one of three analysis agents (27 Sep 03:00 to 04:25).
- **Cost:** About an hour and a half with the question wrongly closed [R]. §6.16 carries the correction.
- **Learned:** Record exactly which variant a "tested and rejected" verdict covered.
- **Source:** [RESEARCH_v6 §6.15, §6.16][r6]; [decision stacked-rules][d-stack].

**Smaller items in DEC**

| ID | what happened, how it was found, what it cost, what we learned | source |
|---|---|---|
| <a id="f-dec-03"></a>F-DEC-03 | Late attempts that failed their controls. Copy-count tie-breaking −0.00057. A learned blend of the six cross-encoder logits and stage-3 pc as the decision score (band AUC 0.9575 against 0.9276 for pc) lost 0.001 and gave only +2 to +4e-6 as an edit signal [M]. The India-only count prior (+16e-6 [+2, +30]) lowered the US on every model and was picked from about 160 variants. Singleton protection, per-source zero-count adds and soft caps lost. The hunt's French per-source `cap` would drop perfect copies at pc 0.997 to 1.000, so none was applied. A more inclusive France DP (shifts 0.5, 0.8) ranged −10 to +16 and −38 to +30 [E]. A brief gave v7nst's threshold as 0.70 while `decide.py` had picked 0.675; both agents rebuilt the stored predictions exactly before testing. Lesson: rebuild a stored result exactly before testing a change on top of it. | [Documentation, App. B][doc]; [RESEARCH_v6 §6.18, §6.20][r6]; [FINAL_PUSH_RESULTS §9][b-final]; [chat:ameya/agent-acec839c 2026-09-27 04:24] |

## RUL: rules and post-processing

<a id="f-rul-01"></a>
### F-RUL-01 · French addresses broke the same-address test in rules v1 and v2 (bug)
- **What:** The op-B rule (drop a swapped-word look-alike at the S1's own address) tested "same address" with a (house number, first street word) key. French addresses broke it: suffixed numbers ("8BIS", "129 D"), typo'd street types ("AVEUNE", "Pace"), abbreviations ("Q." for Quai), two-letter typos in short street names. 1,291 op-B look-alikes (5.0 per 1000 French S1) stayed predicted, for example "Paita Culturelle SARL | 8 BIS Rue Alfred Naquet" → "PAITA COMITE SARL | 8BIS R. ALFRED NAQUET" (pc 0.982).
- **Found:** By hand review of 22 French S1 with an uncertain pair, 26 Sep afternoon. Bakshi found the same 1,148 independently.
- **Cost:** About +0.001 France F0.5 [E] left out of the uploaded v5all package. Rules v3 fixed it with a robust address test; on the US/India holdout the newly matched look-alikes were 0.0 to 1.2% true and the newly matched copies 87 to 99% true [M].
- **Learned:** Hand-review 20 raw examples before trusting a rule's key, and test the key on every country's address style.
- **Source:** [RESEARCH_v6 §2.7][r6]; [decision rules-v3-and-stage3][d-rules3]; [chat:ameya/a2a1b62a 2026-09-26 16:53].

<a id="f-rul-04"></a>
### F-RUL-04 · The look-alike drop flip-flopped, and its sign was never settled (process)
- **What:** At 12:12 on 27 Sep a France-only drop of 592 same-address "similar word" swaps ("maternelle" → "culturelle") was adopted on three label-free signals: the size-bias test (false share 0.83 [0.56, 1.10], break-even 0.28), 4,088 such French candidates against 172 in a same-size US/India sample, and a count test. It was worth about +0.00004 on those signals [E]. At 17:03 the France-diff agent's leaderboard-history test reversed the verdict (the drop probably costs about 27e-6). Packages built after that skip it. The uploaded mixmdp (454 pairs dropped) and so the France half of Composite B still carry it. The pc-based estimators put it at −20 to −31e-6, the 7B-calibrated view at neutral to mildly positive, and the LB residual at about +18e-6 [E].
- **Found:** By the leaderboard-history backtest of the size-bias test.
- **Cost:** Part of mixmdp's forecast error (F-EVL-06). The drop's true effect is unknown.
- **Learned:** The size-bias test settled the French acronyms (false share 0.00 [0.00, 0.01], validated on known-true populations). It under-states false shares for look-alikes and is invalid for populations that take most of an S1's copies. Use it to keep a population, not to drop one.
- **Hindsight:** Composite B reused mixmdp's France as uploaded because that France was leaderboard-proven (+134e-6 over v7sq-dpc, the drop included). No upload isolated the drop, so the final submission contains a change whose sign we never settled.
- **Source:** [RESEARCH_v6 §6.17, §6.18, §6.20][r6]; [FINAL_PUSH_RESULTS §4, §5][b-final]; [chat:ameya/19e315ba 2026-09-27 12:12]; [chat:ameya/19e315ba 2026-09-27 17:03].

<a id="f-rul-05"></a>
### F-RUL-05 · Recall rules and filters all failed their controls (dead end)
- **What:** Adding a pair pays only above about 72 to 75% precision (a false add costs about 0.18 F0.5, a miss about 0.07). Nothing cleared it; the best was 71%.
  - 7B recall of unpredicted candidates whose record no S1 owns peaked at 71% (logit above 4: 69 adds, 49 true) [M].
  - Empty-address exact names: 40% true (287 holdout pairs). Structural French recall rule: 40% precise (Bakshi first read it as +0.000370: "my first verdict was wrong"). Lower France threshold: 50 to 57%. Brand-name join: 37% (US) and 40% (India). Alias bridging: about 30 French pairs. House number off by 1 or 2: 97.6% true in the US but 78.2% in India. Short-code typos: 42.6 to 44%.
  - Filters: a French cross-encoder veto, cell adds, brand adds, the drop1/nudge rule, Bakshi's composed-edit rules and a consensus filter all failed their controls. The "bge disagrees" drop was anti-selective: it fires on 17.76% of known-true French pairs against 8.74% of the rest.
- **Found:** Labelled-holdout measurements and rule-population checks, 26 and 27 Sep.
- **Cost:** Hours of analysis and no upload slot.
- **Learned:** With a 75% break-even and a model already 99.9% precise, a recall rule needs a nearly clean signal. None existed (see Limits).
- **Source:** [RESEARCH_v6 §6.3, §6.19][r6]; [decision france-rules-v2][d-rules2]; [CONFIDENT_SUBSTITUTIONS][b-conf]; [handover 26 Sep 15:45][h0926-1545]; [Bakshi recovery scripts][b-recovery].

**Smaller items in RUL**

| ID | what happened, how it was found, what it cost, what we learned | source |
|---|---|---|
| <a id="f-rul-02"></a>F-RUL-02 | The first op-B classifier (about 03:00, 26 Sep) counted list words in the last slot as op-B, so the US "B" population came out 93% true. Splitting on list membership, garble similarity (Indel at least 0.5) and real-word frequency (at least 20 S1 names) gave 0.6% true (5,364 pairs). The garble exemption later let French real-word swaps through (college/ecole at 0.67; 27 Sep 11:34). Found by measuring truth rates on the US/India holdout. Lesson: validate a population definition against labels before using it. | [decision france-generator-ops][d-genops]; [chat:ameya/agent-a2762d22 2026-09-27 11:34] |
| <a id="f-rul-03"></a>F-RUL-03 | The acronym join crossed cities: 48 of 3,832 French adds (1.25%) named another city ("Souris Club SAS, 49 Rue Jules Watteeuw, Tourcoing" → "SC, 49 Rue Jules Lanery, Dunkerque"), because the same-address test accepted one shared street word and French streets share first names. First judged not worth a late change (about +0.00001 LB). The `city` rule (drop a pair whose S1 and record name different communes; French true copies change commune in 3 of 546,465 pairs; −89 on v7s) is recorded as the fix. Separately, the polish agent labelled all 21 French hunt acronym adds as number-dropped copies; 5 carry another house number or street, so the parent narrowed them to 16 (27 Sep 04:19). | [RESEARCH_v6 §6.14, §6.16][r6]; [decision stacked-rules][d-stack]; [chat:ameya/19e315ba 2026-09-27 04:19] |

## FRA: France, the unseen country

<a id="f-fra-01"></a>
### F-FRA-01 · Self-training was rejected, then shipped within one day (surprise)
- **What:**
  - 26 Sep 02:07, rejected. In the leave-one-country-out stand-in with the unseen country's words unseen, each round made it worse: 0.88235 → 0.85120 → 0.83075, and 0.823 after a third round in Sachi's ladder [M]. Confident pseudo-positives include look-alikes, so each round teaches the model to accept more (confirmation bias).
  - About 18:14, re-tested on an India stand-in with label-free word odds: +0.0009 on average of three seeds. Judged too small (+0.0001 to +0.0002 on the LB) for a 2 to 3 hour retrain.
  - 20:59 to 21:25: cross-encoders found to disagree in sign on 12% of French band pairs (3% in US/India); the team stood 17th at 21:12 [R]. Self-training on France was revived with cross-fitted pseudo-labels.
  - About 23:35: v7nst uploaded: +0.000458 on the public LB (France +0.0031, to about 0.981) [M].
- **Found:** By the leaderboard, which overturned the stand-in.
- **Cost:** The 18:14 estimate undershot the measured gain by 2 to 4 times.
- **Learned:** The stand-in (words unseen, no proxy odds, a weak teacher) did not represent the evening's pipeline (proxy odds restored, a stronger teacher, cross-fitting, guards). A rejection holds only for the regime it was measured in.
- **Hindsight:** Our notes kept saying "rejected" after the regime had changed. ANALYSIS_v4 listed self-training as "skip" on the conjecture that pseudo-labels reinforce convention errors, and RESEARCH_v5 listed it among items not worth doing. Record the regime with every rejection and re-test when its precondition changes.
- **Source:** [ANALYSIS_v3 §3][a3]; [ANALYSIS_v4 §1][a4]; [decision model-v4][d-v4]; [RESEARCH_v6 §4, §6.7][r6]; [LB 2026-09-26 #04][lb-0926-04]; [chat:ameya/19e315ba 2026-09-26 21:17].

<a id="f-fra-02"></a>
### F-FRA-02 · More rounds of self-training drifted (dead end)
- **What:**
  - Round 2 on v7nst's own decisions (v7nst2) dropped clear copies ("Projet & Cie EURL" → "Projet & Compagnie EURL"), added word swaps at the S1's address ("GY Amicale SARL" → "GY Agricole SARL") and one cross-city pair. fhs −1.54 per 1000 French S1. It was dropped after 40 changes were read by hand.
  - Guarded round-2 stage-2 labels at weight ×3 did help: mixmdp gained +154e-6 on the public LB over v7sq-dpc [M], about +134e-6 of it in France [E], together with the look-alike drop and the France decision layer.
  - Round 3 (labels from mixmdp's guarded France decisions): cal +215e-6 over v7sq-dpc, but the upload without the decision layer scored −46e-6 against Composite B (F-EVL-05). Round 4 changes only 3,553 of 1.43M labels. Corrected-label round 4 (the 859 7B rejects as negatives): −44e-6 by 7B-calibrated estimate [E].
- **Found:** By hand reading of changes, by fhs and by the leaderboard.
- **Cost:** Chain hours and two upload slots (mixf7, mixf2).
- **Learned:** Two guards (rules win; empty-address records keep their first-round labels) and cross-fitting by S1 group made rounds 1 and 2 safe. Iterating further amplified near-threshold mistakes.
- **Hindsight:** The methodology says "a third round did not add". The round-3 upload also lacked the France decision layer, so the record supports "round 3 was not shown to add", not "round 3 hurt".
- **Source:** [RESEARCH_v6 §6.14, §6.19, §6.20][r6]; [LB 2026-09-27 #05][lb-0927-05]; [Documentation §2.2, §6][doc].

<a id="f-fra-03"></a>
### F-FRA-03 · frs2 (France takes the stage-2 decision) was proposed, built and withdrawn (dead end)
- **What:** After self-training the French rule-population AUC fell from stage 2 to stage 3 (v7nst 0.9844 → 0.9791). Section 6.12 (27 Sep, 00:30 to 01:45) read this as stage 3 harming France and proposed `frs2`; Bakshi ranked it first among the cheap levers (+0.0001 to +0.0002 LB). It was packaged and withdrawn at about 02:40. Stage 2 had been trained on pseudo-labels that contain the rule populations and stage 3 had not, so the drop was circular. `frs2` drops 3,029 French pairs, 35% of them with an empty record address (base rate 2.7%), the pairs stage 3's part B lifts over the threshold. fhs: −3.86 net true copies per 1000 French S1, the worst of any candidate [M].
- **Found:** By Ameya's empty-address analysis and fhs (issue #45 at 02:38, PR #54 review at 02:42).
- **Cost:** Some chain hours. No upload.
- **Learned:** A proxy can be circular for a stage comparison too. Check what each stage was trained on before reading a score difference as damage.
- **Source:** [RESEARCH_v6 §6.12, §6.14][r6]; [ledger][b-ledger].

<a id="f-fra-06"></a>
### F-FRA-06 · France was not like the training countries (surprise)
- **What:**
  - French acronyms ran at 72.1 per 1000 French S1 (18,707 pairs), 11 times what French name shapes predict from US/India rates. A drop pays above a false share of about 25%. The size-bias test fitted f = 0.00 [0.00, 0.01], so they were kept and no upload was spent [M].
  - "SNC" is a look-alike legal form in France (14,763 records for one S1, all on its street with a nudged number). The US word "Incorporated" is the opposite: 86% true copies, a vendor spelling of "Inc".
  - French true copies rarely move the house number (digit drops 6 per 1000 S1 against 96 in the US), so a moved number is much stronger look-alike evidence there than the model learned.
  - About 11% of French S1 share an exact address, against 4 to 5.7% in US/India, with generic names. The decoys we later removed shared their name with a median of 43 other S1. France has twice the exact copies (1,018 against 510 per 1000 S1), because its S3 vendor leaves French addresses untouched.
  - Count structure matches US/India (empty share, copies per S1, S2/S3 split), so France loses on which records it picks, not how many. Σ pc per French S1 was 3.55 against a generator limit of 3.46 (US/India 3.43, equal to truth): a label-free proof of overconfidence.
- **Found:** By label-free population checks, 26 and 27 Sep.
- **Cost:** Time. For acronyms and SNC the right answer was the opposite of the naive reading.
- **Learned:** Do not assume the unlabelled country follows the labelled rates. Check each large anomaly with a test that can say "keep" before acting on it.
- **Source:** [RESEARCH_v6 §2.3, §6.2, §6.17][r6]; [ANALYSIS_v3 §2][a3]; [ANALYSIS_v4 §3.1][a4]; [chat:ameya/19e315ba 2026-09-27 11:38].

**Smaller items in FRA**

| ID | what happened, how it was found, what it cost, what we learned | source |
|---|---|---|
| <a id="f-fra-04"></a>F-FRA-04 | The first label-free word-odds method saturated. A mixture inversion with train's P(moved house number \| false) = 0.2286 assumed France's close pairs show about that share of moved numbers; they show 75% (US/India 73%), so the prior saturated and every French word got odds of 0. Found by printing France's top look-alike words (club, eau, école all 0.0; 26 Sep 00:53). About 10 minutes; the v4 chain was stopped before 50 GPU-minutes were spent [R]. Lesson: print the top and bottom of any fitted lexicon before a long chain. The replacement maps a word's moved-number share to the label-odds scale with a decreasing isotonic fit. | [ANALYSIS_v3 §4][a3]; [chat:ameya/19e315ba 2026-09-26 00:54] |
| <a id="f-fra-05"></a>F-FRA-05 | Rule labels as training data hurt on the India stand-in (India's labels hidden; US-only baseline 0.96555, in-country 0.98660). Rule positives alone −0.0034 (−0.0040 over three seeds); positives plus 449 op-B negatives +0.0015 on one seed, +0.0005 (noise) over three; the moved-number rule is 45% wrong on India's compound house numbers ("Sno 32/2/1 Hno 1048"). Easy, certain copies teach the model to accept too much. The best variants closed 5 to 7% of the 0.021 gap [M]. Rules therefore stayed post-processing, not labels. | [RESEARCH_v6 §4][r6]; [handover 26 Sep 18:17][h0926-1817] |

## LLM: the Qwen2.5-7B re-check

<a id="f-llm-01"></a>
### F-LLM-01 · A general LLM could not do this task without training (dead end)
- **What:** Zero-shot Qwen2.5-7B-Instruct on the uncertain pairs reached a holdout AUC of 0.537 against 0.898 for pc on the same pairs (blend weight 0.002, no gain). A quick LoRA fine-tune reached 0.720. Bakshi's properly trained 7B adapter, trained on French self-training labels, reached a band AUC of 0.9436.
- **Found:** By the agent on the holdout, 27 Sep around noon.
- **Cost:** About an hour of H100 time and a delay to the round-2 e5 retrain [R].
- **Learned:** A general LLM does not know this generator's conventions, so it needs supervised training. The 7B in the final is a trained second reader, not a zero-shot judge.
- **Source:** [handover 27 Sep 12:28][h0927-1228]; [handover 27 Sep 20:06][h0927-2006].

<a id="f-llm-03"></a>
### F-LLM-03 · The 7B "moonshot" was argued against, and it gave the day's best additions (surprise)
- **What:** At 13:18 on 27 Sep the agent for Ameya argued against a 7B "moonshot" [R]. Bakshi independently trained the Qwen2.5-7B French cross-encoder (q7st) on three H100s. It ties e5-large on band AUC but, counted twice in the stage-2 mix, gave the best US/India model (g1w: holdout 0.991323, India +66.1e-6 at P 0.998). As a re-reader of confident predictions its logit −6 rule gave +33e-6 on the holdout. With the French half of the rule, Composite B gained +180e-6 on the public LB over mixmdp [M].
- **Found:** By the results between 17:05 and 20:55.
- **Cost:** None; the objection did not affect the run. The reasoning behind it is not in our sources (unknown).
- **Learned:** A model that ties on accuracy can still win through diversity and through the data it reads: the 94.5% of final predictions that no cross-encoder had seen. Let a teammate run the bet when compute is free.
- **Source:** [FINAL_PUSH_RESULTS §2, §3][b-final]; [LB 2026-09-27 #04][lb-0927-04]; [chat:ameya/19e315ba 2026-09-27 13:18].

**Smaller items in LLM**

| ID | what happened, how it was found, what it cost, what we learned | source |
|---|---|---|
| <a id="f-llm-02"></a>F-LLM-02 | Pushing the 7B drop past the labelled cut-off was neutral. B7 extended the French 7B drops from logit −6 toward −2 where Qwen3-4B agrees (+251 / −1,699 French pairs) and scored 0.990875 against 0.990879, a tie [M]. The labelled holdout had already put the optimum at −6 (+37e-6, against +29e-6 at −5 and +17e-6 at −4). The reasoning "France has 25 times the decoys, so the ladder pays further down" overstated the French false rate in the −6 to −2 bands. A 3-adapter 7B ensemble was also dropped: its extra French drops hit garbled "EHPAD" copies. Cost: the last upload slot. Lesson: a rate measured in one band does not carry to the next. | [LB 2026-09-27 #07][lb-0927-07]; [FINAL_PUSH_RESULTS §3, §9][b-final]; [RESEARCH_v6 §6.20][r6] |

## SUB: leaderboard strategy and the final-model choice

<a id="f-sub-01"></a>
### F-SUB-01 · The agreed final scored below the fallback we had set aside (surprise)
- **What:** On the last evening the team agreed in issue #64 to upload one model, mixf2 (US from v7sq3, India from g1w, France from round-3 v7sq6r3, minus the 7B rejects), predicted at about 0.99091 [E]. At 20:46 to 20:53 the team changed the plan and uploaded Bakshi's Composite B first, as a probe. It scored 0.990879, our best. The three uploads after it each changed one thing from B. All scores are public LB [M].

  | upload (time) | what it changes from Composite B | LB | against B |
  |---|---|---|---|
  | Composite B (about 20:55) | the 7B parts over mixmdp (g1w US/India, 7B drops) | 0.990879 | +180e-6 over mixmdp (+149e-6 predicted) |
  | mixf7 (about 21:55) | France: round-3 labels, no France decision layer | 0.990833 | −46e-6 |
  | mixf2 (about 21:55) | as mixf7, with US from v7sq3 instead of g1w | 0.990819 | −60e-6 (g1w US is +14e-6 over v7sq3) |
  | B7 (about 23:40) | French 7B drops extended toward logit −2 | 0.990875 | −4e-6 (a tie) |

- **Found:** By uploading. The "fallback" was the best.
- **Cost:** None for the score. B+ (B plus 8 more French drops, expected about 0.99088) was prepared and never uploaded.
- **Learned:** The last rounds of French "improvements" came from estimators that were biased on decoys (F-EVL-05). One-change uploads are how we found out.
- **Source:** [LB 2026-09-27 #04][lb-0927-04]; [LB 2026-09-27 #05][lb-0927-05]; [LB 2026-09-27 #06][lb-0927-06]; [LB 2026-09-27 #07][lb-0927-07]; [handover 27 Sep 20:14][h0927-2014].

<a id="f-sub-02"></a>
### F-SUB-02 · The last upload was not the best, twice, and we do not know which one counts (process)
- **What:** At about 10:22 on 27 Sep the control v7nst-dpc (0.990264) was uploaded after v7sq-dpc (0.990545). The team had read the page as "the final submission is the ranked one", so for hours the live upload sat 0.000281 below the best. Bakshi's deliverables note flagged the "LIVE RISK" and proposed a hard rule: restore the best by 18:30. The last upload of all, B7 (0.990875), is 4e-6 below the best, Composite B (0.990879). Our sources disagree on the ranking rule. The page was read as ranking by "the maximum score of the submission and submission time" and the private board as "based on your final solution submission". Bakshi's 11:00 note said the final upload counts; his 15:30 handoff said "the best upload counts, not the latest"; his 20:06 handover said it was "reported both ways today"; Ameya's last handover left it open.
- **Found:** Bakshi's deliverables note at 11:00.
- **Cost:** None in the end, because B7 tied B. Which upload the private ranking used is not recorded anywhere we have (open item).
- **Learned:** Decide in advance whether best or last counts, and read the rule in the portal. Keep a restore slot. Never leave a control or an unproven variant as the live upload.
- **Source:** [DELIVERABLES][b-deliv]; [HANDOFF][b-handoff]; [handover 26 Sep 02:07][h0926-0207]; [handover 27 Sep 20:06][h0927-2006]; [ANALYSIS_v3 §8][a3].

<a id="f-sub-03"></a>
### F-SUB-03 · Deadline confusion: 21:00 or 23:59? (process)
- **What:** AGENTS.md and the plans say Sunday 27 Sep 23:59 IST. The competition's submission-round page gave the window as 25 Sep 03:30 UTC to 27 Sep 15:30 UTC, which is 21:00 IST. A research helper agent found this at about 02:00 on 26 Sep and asked a human to confirm it in the logged-in portal. The sources never record a confirmation. The team planned to 21:00: a code freeze at 15:00, "the chosen final last, before 21:00", a single-upload plan, and a proposed AGENTS.md fix that was never merged (AGENTS.md still says 23:59). Uploads at about 21:55 (two) and 23:40 were accepted and scored.
- **Found:** By the research helper agent's reading of the page; Bakshi flagged the AGENTS.md line again at 01:11 on 27 Sep.
- **Cost:** A compressed last day. The plan assumed one more upload that evening, and after Composite B three more were possible. Whether that changed any result is unknown.
- **Learned:** Confirm the deadline and quota in the portal on day one, and write the answer into AGENTS.md.
- **Source:** [ANALYSIS_v3 §8][a3]; [handover 26 Sep 02:07][h0926-0207]; [handover 27 Sep 01:11][h0927-0111]; [ROADMAP][roadmap].

<a id="f-sub-05"></a>
### F-SUB-05 · Uploads against the plan: the France probes were never uploaded (process)
- **What:** The plan set aside slots for probes. Gate G7 asked for one France-emptied upload. France-emptied packages were built at least three times (`probe-v4-fr0`, `probe-v6s3-fr0`, `probe-v7-fr0`), with other France probes (`probe-v4-frab`, `fr090`, `fr090r`, `frlo`), and none was uploaded. The 26 Sep morning plan "v4, then probe-v4-frab, then v5all-ops" became one upload, v5all-ops2. The leaderboard formula replaced the probe (record 2026-09-26 #01: "the France level is known to about ±0.003 from this upload; the probe would only settle the US/India assumption"). On 27 Sep Bakshi's reason for not running fr0 was that it "costs an upload slot, cannot improve the score, and no decision today depends on the answer".
- **Found:** By comparing the packaged probes with the upload records.
- **Cost:** The France level stays an estimate (F-EVL-07). We cannot say what the probes would have shown.
- **Learned:** The cheapest direct measurement of our biggest unknown was the one we skipped. Write down what each unrun probe would have decided before shelving it.
- **Source:** [FINAL_PLAN §9][plan]; [handover 26 Sep 05:20][h0926-0520]; [LB 2026-09-26 #01][lb-0926-01]; [CONFIDENT_SUBSTITUTIONS][b-conf].

<a id="f-sub-07"></a>
### F-SUB-07 · Reasoning errors, retracted in writing (process)
- **What:**
  - At 09:44 on 27 Sep the agent for Ameya told Ameya the whole gap to the leaders was France (leaders about 0.990 against our 0.981) and out of reach that day.
  - Bakshi's supporting argument, that the French gap is the same whatever US/India level is assumed, was circular: both teams' levels were set equal, so it cancelled by construction. He retracted it on issue #45 at 10:04; `CONFIDENT_SUBSTITUTIONS.md` still carries it.
  - Bakshi had called 0.991 unlikely and put the v7sq-dpc gain at +0.00012; it was +0.000366 (F-EVL-04). He ranked frs2 first (F-FRA-03) and estimated +0.000256 for bge (F-ORG-05); the first was circular, the second too high.
  - His results note first called "same number, different street" "100% true among US/India predictions". Ameya corrected it (issues #62, #64): the pattern is a copy where the model accepts it and a decoy where it rejects it. That correction made his 7B drops the day's best French finding (F-LLM-03).
  - A MiB/MB unit error made v7qbag and v7sq4 look 4.5% smaller than v7sq-dpc; Bakshi corrected it himself.
- **Found:** By Ameya's review and by Bakshi's own re-checks.
- **Cost:** The circular argument stood for about 45 minutes [R] and is still in one repo file. Nothing else.
- **Learned:** Check whether an "invariance" is a consequence of your own assumption. We corrected each other in writing, which is what kept these errors out of the uploads.
- **Source:** [CONFIDENT_SUBSTITUTIONS][b-conf]; [MODEL_CHOICE][b-choice]; [ledger][b-ledger]; [FINAL_PUSH_RESULTS §6][b-final]; [chat:ameya/19e315ba 2026-09-27 09:44].

**Smaller items in SUB**

| ID | what happened, how it was found, what it cost, what we learned | source |
|---|---|---|
| <a id="f-sub-04"></a>F-SUB-04 | Seven upload records on 27 Sep against a limit of five a day. The rules said 5 uploads per day for the team, with the day boundary assumed to be 00:00 IST. The records for 27 Sep number seven (v7nst-dpc, v7sq-dpc, mixmdp, B, mixf7, mixf2, B7). Bakshi's 15:30 handoff counted "3 left today" when two had been uploaded. Record numbers also do not follow upload time (record 01 was uploaded after record 02). We do not know how the portal counted the day. Lesson: do not quote the daily limit as fact. | [submissions README][subs]; [LB 2026-09-27 #01][lb-0927-01]; [HANDOFF][b-handoff] |
| <a id="f-sub-06"></a>F-SUB-06 | Our public rank fell while our score rose. v7sq-dpc (0.990545) was rank 7, then 8; mixmdp (0.990699) rank 12; Composite B (0.990879) rank 16 at upload and about 20th by 22:52 [R]. The top of the board at about 16:40 was 0.991829 [R]. At 22:53 the agent wrote "Nothing validated can close a 0.001 gap in one hour". Grenuke is 2nd of the Top 10 on the private ranking (the organisers publish rankings only) [R]. Other teams improved faster on the last day, and no source we have explains the gap between our last public rank and our private rank. We do not estimate a private score. | [CHANGELOG][chg]; [chat:ameya/19e315ba 2026-09-27 22:53]; [memory:ameya] |

## PKG: packaging, reproducibility, the methodology document

<a id="f-pkg-01"></a>
### F-PKG-01 · tokens.py was dropped by a secret-filename filter (packaging)
- **What:** The ZIP builder excluded files whose names look like secrets, using the glob `*token*`. That matched `ber/features/tokens.py`, a legitimate source file. Every ZIP built before the 09:40 build on 27 Sep was unrunnable: five hashes were withdrawn, the first built at 01:30. They passed every check Bakshi had, because `compileall` compiles each file alone and never resolves an import, and because the 115-test run executed against the repository, not the archive.
- **Found:** When Bakshi first ran the shipped tests from inside the extracted archive.
- **Cost:** About 8 hours in which a broken ZIP was reported as validated. Fixed before the final. The archived output files were byte-identical in all builds.
- **Learned:** In Bakshi's words, "verify the artifact, not the source it came from". The filename globs are now narrow and never applied to source files (contents are still scanned for secrets). The builder imports all 34 `ber` submodules and runs the shipped tests from the extracted archive as hard gates.
- **Source:** [DELIVERABLES §4][b-deliv]; [ledger][b-ledger]; [commit 4981ca5]; [chat:ameya/19e315ba 2026-09-27 09:29].

<a id="f-pkg-02"></a>
### F-PKG-02 · The organisers' validator passes broken packages (packaging)
- **What:** It prints PASS with only a warning when the candidate file is missing, and with only a warning when matched pairs fall outside the candidate set. It never checks that a record is claimed by one S1, or that countries are consistent. Bakshi's `audit_matching.py` checks all of that, plus exact set equality of rows with the test S1, and exits non-zero.
- **Found:** While auditing the submitted v7nst output (27 Sep 01:11). A control (the v6all pair audits clean) showed the audit raised no false alarms.
- **Cost:** None; caught.
- **Learned:** Treat the official validator as a format check. Add an audit for the rules the organisers will apply later.
- **Source:** [handover 27 Sep 01:11][h0927-0111]; [audit_matching.py][b-audit]; [AGENTS.md §7][agents].

<a id="f-pkg-03"></a>
### F-PKG-03 · Files were nearly identified by name and by subset consistency (packaging)
- **What:** The v7nst candidate file was missing on Bakshi's machine. The v6all candidate file could not stand in: 3,790 matched pairs over 3,725 S1 (the acronym join's new candidates) fall outside it. He predicted the real file's size before seeing it (6,410,247 pairs = 6,406,457 + 3,790) and was right on arrival [M]. His local `matching_resultsv6all.tsv` was `544ffdf8…` (v6all-s3-ops3), not the packaged `0f6d8985…`. A file named `candidate_pairs_7nst_dpc.tsv` was v7sq-dpc's, caught by the hash gate. For v7sq-dpc, 69 matched pairs over 66 S1 fell outside v7nst's candidates, and he refused to build a candidate list by adding them.
- **Found:** By Bakshi's strict audit and the hash gate in `make_package.py`.
- **Cost:** The v7nst package waited about 40 minutes for its file (01:11 to 01:50), and the v7sq-dpc package until its file arrived (F-ORG-06).
- **Learned:** In Bakshi's words, "only the hash identifies a package". Subset-consistency is necessary, not sufficient.
- **Source:** [handover 27 Sep 01:11][h0927-0111]; [DELIVERABLES §2][b-deliv]; [make_package.py][b-pkg]; [chat:ameya/c0c64ad6 2026-09-27 01:05].

<a id="f-pkg-04"></a>
### F-PKG-04 · Recipes and scripts that existed only in a scratchpad (packaging)
- **What:** The variant tags for v7sq4, v7sb and v7ensall2 were "never written down", so Bakshi's `reproduce.sh` refused them. v7nst's pseudo-labels come from v7ce3, so a clean run must build the teacher first, and the merged `docs/package/reproduce_v*.sh` scripts stop at v6. The production stage-2 driver (`s2w.py` and other drivers) lived only in the agent's temporary scratchpad until 29 Sep 01:08, when 134 files were rescued into the repo.
- **Found:** By Bakshi's reproduction attempts (27 Sep) and the packaging review (29 Sep).
- **Cost:** v7ensall2 could not be reproduced and was withdrawn on that ground as well as on the tie rule. The standing risk was losing the ability to rebuild the final.
- **Learned:** Scripts used for an upload go into the repo before the upload. Write the recipe down when the variant is created.
- **Source:** [MODEL_CHOICE][b-choice]; [handover 27 Sep 01:11][h0927-0111]; [chat:ameya/a2a1b62a 2026-09-27 11:34]; [chat:ameya/19e315ba 2026-09-29 01:08].

<a id="f-pkg-05"></a>
### F-PKG-05 · The ZIP was never run end to end (packaging)
- **What:** `reproduce.sh` has never been executed end to end by anyone. Bakshi's laptop has no torch, a 4 GB GPU and 16 GB of RAM, while the chain needs an H100, 18 to 19 GB per stage and 6 to 7 hours. By 01:05 on 29 Sep every rented GPU machine had been destroyed, and the driver has no small-sample mode. Verified: syntax; the variant dispatch; every flag against the scripts' own argument parsers; 34 of 34 submodule imports and 115 tests from the archive [M]; a byte-identical rebuild of the last composition step (matching `df4bccd7…`), a deterministic ZIP build and 8 of 8 final-ZIP checks by Bakshi's agent [R]. Also on 27 Sep Bakshi's rebuild of the pipeline on rented boxes reproduced v7sq-dpc (holdout 0.991261 against 0.991246).
- **Found:** By Bakshi's deliverables review (27 Sep 11:00) and the 29 Sep package review.
- **Cost:** The reproducibility claim in the methodology is limited to what was checked.
- **Learned:** Say plainly what was and was not executed. The methodology does: a rerun should land "within about 0.0001".
- **Source:** [DELIVERABLES §4][b-deliv]; [FINAL_PUSH_RESULTS §1][b-final]; [Documentation, App. A][doc]; [chat:ameya/19e315ba 2026-09-29 01:08].

<a id="f-pkg-07"></a>
### F-PKG-07 · The first final ZIP and document were neither presentable nor fully accurate (packaging)
- **What:** The trial ZIP carried personal paths, rented-machine addresses and remote-shell commands in as-run records, research notes, agent mentions, a to-do note and the organisers' validator. It was curated from 289 to 146 files and matched to the organisers' tree. The methodology draft had overstatements: three caught by the agent at 03:28 and four by Bakshi's agent at 04:01 on 29 Sep, after the first "final" ZIP was built. The document build had its own bugs (a regex backreference `\1` written as a control character so the PDF lost its labels; the page count overflowing seven pages again and again). The first `requirements.txt` could not be installed (pins from a laptop with transformers 5.2.0) and needed PR #74 at 02:48.
- **Found:** By the agent's review, Bakshi's accuracy pass and Ameya's dry run.
- **Cost:** Rework between 00:08 and 04:09 on 29 Sep, before the package was due at 10:00 [R].
- **Learned:** A "don't overstate" pass by someone who did not write the text is worth the time. Resolve pinned requirements once in a clean environment.
- **Source:** [chat:ameya/19e315ba 2026-09-29 03:27]; [chat:ameya/19e315ba 2026-09-29 03:28]; [chat:ameya/19e315ba 2026-09-29 04:01]; [PR #72]; [PR #74]; [ROADMAP][roadmap].

**Smaller items in PKG**

| ID | what happened, how it was found, what it cost, what we learned | source |
|---|---|---|
| <a id="f-pkg-06"></a>F-PKG-06 | Reruns are not bit-identical. Stage 3 differs across machines (232k test pc values differ, largest difference 0.09, about 500 decisions flip), and GPU training does too (a model rebuilt on other hardware moved from 0.991246 to 0.991261 on the holdout) [M]. Found by comparing reruns (27 Sep, around 14:41). The methodology therefore claims "within about 0.0001", not an exact match. | [RESEARCH_v6 §6.18][r6]; [Documentation, App. A][doc]; [chat:ameya/agent-ad467765 2026-09-27 14:41] |
| <a id="f-pkg-08"></a>F-PKG-08 | The session died mid-commit (exit 137) on 28 Sep at 00:12 while committing the seven 27 Sep submission records. The records are on `main` by 3 Oct. | [chat:ameya/19e315ba 2026-09-28 00:12] |

## Limits we shipped with

Known weaknesses of the final submission, kept apart from the failures so they are not forgotten in a Q&A.

- **Empty-address copies of businesses that share a name.** About 22k holdout pairs are essentially unrecoverable (95 to 100% missed) [M]. Of the true holdout pairs we miss, about 16.5k never become candidates and about 15.2k score near zero. No recall rule was more than 71% precise against a break-even near 75% (F-RUL-05). [handover 25 Sep 21:47][h0925-2147]; [Documentation §5][doc].
- **France was never measured directly.** All French levels rest on an assumption about US/India on test (F-EVL-07).
- **Generic-name French decoys** remain France's main error type. 97% of v7sq-dpc's French predictions already sat at pc 0.99 or higher, so little uncertain band was left for a rule to act on. [MODEL_CHOICE][b-choice].
- **The 7B drop lists cover only pairs that were scored.** Pairs not in Bakshi's scored sets are never dropped, and the cut-off is fixed at logit −6 (F-LLM-02). [handover 27 Sep 20:14][h0927-2014].
- **The look-alike drop in France has an unsettled sign** (F-RUL-04).
- **Stage 3 and GPU training are not bit-reproducible**, and the ZIP was not run end to end (F-PKG-05, F-PKG-06).
- **Pool-size dependence of the rarity and rival-count features** was left open (F-FEA-08).

## Conflicts and open items

For the curator to carry into [`conflicts.md`](conflicts.md). Where sources disagree, the measured record is preferred and both readings are kept.

1. **Which upload did the private ranking use?** Composite B (public 0.990879) or the last upload B7 (public 0.990875, a tie)? No source states it, and the team's own notes disagree on whether the best or the last upload counts (F-SUB-02). Open item.
2. **Deadline and quota.** AGENTS.md and the plans say 23:59 IST; ROADMAP records the window as closing at 21:00 IST; uploads at about 21:55 (two) and 23:40 were accepted and scored. The rule of 5 uploads per day sits against seven records dated 27 Sep, and the portal's day boundary is not recorded (F-SUB-03, F-SUB-04).
3. **"A third round did not add" (methodology) against the record.** The round-3 upload also lacked the France decision layer. RESEARCH_v6 §6.20 gives +24e-6 for the round-3 model and +51e-6 for the decision layer that mixf7 lacked, a net of −27e-6 against the measured −46e-6 (F-EVL-05, F-FRA-02).
4. **Candidate-set recall.** The methodology says the 3.70-per-S1 candidate set keeps 99.1% of true holdout pairs and misses about 16.5k. Those figures (0.99135; 16,455) belong to the blocking output before the candidate cut. The cut record puts the cut set's recall lower (0.98927 to 0.98198 on v5all). The recall of the final 3.70 file is not re-measured in our records [U] (F-BLK-02).
5. **Per-record renormalisation of French probabilities.** RESEARCH_v6 gives +0.000015 on the holdout and no change after stage 3. The methodology (App. B) and the theory pages say "up to −0.000137" on France. We found no calculation for it in the repo files we read [U].
6. **The acronym join crossing cities.** One working extract lists it as left in the final; RESEARCH_v6 §6.16 records it as fixed by the `city` rule. We follow the measured record and did not re-measure the 48 pairs (F-RUL-03).
7. **What the final upload was.** `docs/status/ameya.md` names B+ as "the final"; submission record 07 and Bakshi's results show the last slot went to B7 and B+ was never uploaded. The ZIP carries Composite B (F-SUB-01).
8. **Record order and times.** Record 01 (v7nst-dpc) was uploaded after record 02 (v7sq-dpc); records 05 and 06 are ordered "approximately"; B7 is 23:36 in FINAL_PUSH_RESULTS and about 23:40 in the record (F-SUB-04).
9. **Smaller discrepancies.** Who caught the ownership bug in Sachi's first run (F-EVL-09). The normaliser review lists four example bugs where a summary line says three (F-NRM-01). PR #27's promised v3 port is in no branch we checked [U] (F-ORG-07, F-ORG-14).

[a2]: ../experiments/ameya/model-v1/ANALYSIS_v2.md
[a3]: ../experiments/ameya/model-v1/ANALYSIS_v3.md
[a4]: ../experiments/ameya/model-v1/ANALYSIS_v4.md
[agents]: ../AGENTS.md
[b-art]: ../experiments/bakshi/final-package/ARTIFACT_REQUEST.md
[b-audit]: ../experiments/bakshi/final-package/audit_matching.py
[b-choice]: ../experiments/bakshi/final-package/MODEL_CHOICE.md
[b-conf]: ../experiments/bakshi/final-package/CONFIDENT_SUBSTITUTIONS.md
[b-deliv]: ../experiments/bakshi/final-package/DELIVERABLES.md
[b-final]: ../experiments/bakshi/box/FINAL_PUSH_RESULTS.md
[b-handoff]: ../experiments/bakshi/box/HANDOFF.md
[b-ledger]: ../experiments/bakshi/final-package/ledger.json
[b-pkg]: ../experiments/bakshi/final-package/make_package.py
[b-recovery]: ../experiments/bakshi/recovery/
[b-trackb]: ../experiments/bakshi/final-package/TRACK_B_FINDINGS.md
[chg]: ../CHANGELOG.md
[d-blk3]: ../docs/decisions/2026-09-26_1122_blocking-v3-repairs.md
[d-cut]: ../docs/decisions/2026-09-26_0532_candidate-set-cut.md
[d-g1]: ../docs/decisions/2026-09-25_2142_gate-g1-blocking-v2.md
[d-g6]: ../docs/decisions/2026-09-25_1731_gate-g6-dp-vs-threshold.md
[d-genops]: ../docs/decisions/2026-09-26_0417_france-generator-ops-and-final-fit.md
[d-rules2]: ../docs/decisions/2026-09-26_0626_france-rules-v2.md
[d-rules3]: ../docs/decisions/2026-09-26_1557_rules-v3-and-stage3.md
[d-stack]: ../docs/decisions/2026-09-27_0636_stacked-rules.md
[d-uniq]: ../docs/decisions/2026-09-25_2111_gate-name-uniqueness.md
[d-v4]: ../docs/decisions/2026-09-26_0207_model-v4-france-and-cross-encoder.md
[d-v7n]: ../docs/decisions/2026-09-26_2135_model-v7n.md
[doc]: ../experiments/ameya/final-zip/doc/Documentation_template.md
[exp-readme]: ../experiments/README.md
[h0925-1414]: ../docs/handover/2026-09-25_1414_ameya_final-plan.md
[h0925-1425]: ../docs/handover/2026-09-25_1425_ameya_dev-skeleton.md
[h0925-1658]: ../docs/handover/2026-09-25_1658_bakshi_normalize-v0.md
[h0925-1706]: ../docs/handover/2026-09-25_1706_ameya_block-v0-baseline.md
[h0925-1958]: ../docs/handover/2026-09-25_1958_ameya_model-v1.md
[h0925-2056]: ../docs/handover/2026-09-25_2056_bakshi_features-v0.md
[h0925-2147]: ../docs/handover/2026-09-25_2147_ameya_analysis-v2-and-v3.md
[h0926-0207]: ../docs/handover/2026-09-26_0207_ameya_leaderboard-gap-france-v4.md
[h0926-0520]: ../docs/handover/2026-09-26_0520_ameya_research-gap-candidates.md
[h0926-1123]: ../docs/handover/2026-09-26_1123_ameya_solutions-round1.md
[h0926-1545]: ../docs/handover/2026-09-26_1545_bakshi_v7-france.md
[h0926-1817]: ../docs/handover/2026-09-26_1817_ameya_ce-large-box.md
[h0927-0111]: ../docs/handover/2026-09-27_0111_bakshi_final-package.md
[h0927-1228]: ../docs/handover/2026-09-27_1228_ameya_final-day.md
[h0927-2006]: ../docs/handover/2026-09-27_2006_bakshi_final-push.md
[h0927-2014]: ../docs/handover/2026-09-27_2014_ameya_final-upload.md
[lb-0926-01]: ../submissions/records/2026-09-26_sub01.md
[lb-0926-03]: ../submissions/records/2026-09-26_sub03.md
[lb-0926-04]: ../submissions/records/2026-09-26_sub04.md
[lb-0927-01]: ../submissions/records/2026-09-27_sub01.md
[lb-0927-03]: ../submissions/records/2026-09-27_sub03.md
[lb-0927-04]: ../submissions/records/2026-09-27_sub04.md
[lb-0927-05]: ../submissions/records/2026-09-27_sub05.md
[lb-0927-06]: ../submissions/records/2026-09-27_sub06.md
[lb-0927-07]: ../submissions/records/2026-09-27_sub07.md
[plan]: ../plans/FINAL_PLAN.md
[plan-decision]: ../plans/DECISION.md
[r5]: ../experiments/ameya/model-v1/RESEARCH_v5.md
[r6]: ../experiments/ameya/model-v1/RESEARCH_v6.md
[roadmap]: ../docs/ROADMAP.md
[subs]: ../submissions/README.md
