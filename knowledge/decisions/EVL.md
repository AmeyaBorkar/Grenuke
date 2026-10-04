# Decisions: EVL (metric, holdout, gates, bootstrap, leaderboard probes)

**Summary.**
- Seventeen decisions on how we measured progress honestly. The metric is macro F0.5: the F0.5 of each source-1 business (S1), averaged over all S1. F0.5 is a score that punishes wrong matches harder than missed ones. We used a fixed 25% local holdout of labelled US and India S1, and a paired-bootstrap gate for every component. France (15% of test, no labels) was read through leaderboard arithmetic and label-free checks.
- The holdout has no France, so the work with the largest leaderboard effect could not be gated on it. We read the leaderboard gap as France, built but never uploaded the France-emptied probe, and trusted the leaderboard over our own estimators once they proved biased on decoys.
- The +0.002 bar of the gates was relaxed in practice to "confidence interval above zero". The decision-layer gain quoted as +0.000048 is the combined layer; the expected-F0.5 dynamic programme (DP) alone was +0.0000332 (written +33.2e-6 below) and not significant (D-EVL-03).

## Index

| ID | decision | when (IST) | status |
|---|---|---|---|
| D-EVL-01 | A shared deterministic holdout: 25% of train S1, out-of-fold groups, a dev sample | 2026-09-25 12:11 | adopted |
| D-EVL-02 | Test shift by diagnostics, not "test ≈ train" and not a drop-S1 stress test | 2026-09-25 12:11 | adopted (the 15:20 "stricter cut-off" inference was not borne out) |
| D-EVL-03 | Gates: every component must beat a simpler one in a paired bootstrap (G1–G13) | 2026-09-25 14:15 | adopted; the +0.002 bar relaxed in practice |
| D-EVL-04 | Model v1 for Submission 2 although the gate printed keep: False | 2026-09-25 18:51 | adopted (an exception to the written rule) |
| D-EVL-05 | Label-free France forecasts are diagnostics, not measurements | 2026-09-25 22:10 | adopted as diagnostic; rejected as a France estimator |
| D-EVL-06 | The France-emptied probe (fr0) and its relatives: packaged, never uploaded | 2026-09-25 22:41 | rejected in practice; G7 left open |
| D-EVL-07 | Attribute the leaderboard gap to France | 2026-09-26 00:16 | adopted, with corrections |
| D-EVL-08 | Estimate France by leaderboard arithmetic | 2026-09-26 02:07 | adopted; the working method to the end |
| D-EVL-09 | Triage Bakshi's "0.990+" proposals with a loss ledger | 2026-09-26 15:22 | adopted, with one reversal by Bakshi's measurement |
| D-EVL-10 | France threshold probes (fr090r) and France-only test packages: built, never uploaded | 2026-09-26 20:28 | built, not uploaded |
| D-EVL-11 | The rule-population AUC as the label-free yardstick for France | 2026-09-26 20:49 | adopted with limits; superseded by D-EVL-12 once it saturated |
| D-EVL-12 | fhs.py replaces the saturated rule-population AUC | 2026-09-27 02:24 | adopted with limits (a drift detector, not a sizer); superseded as a sizer by D-EVL-14 |
| D-EVL-13 | Three memory-capped analysis sub-agents; gains must hold on two disjoint halves | 2026-09-27 02:57 | adopted |
| D-EVL-14 | Value French changes with "cal" | 2026-09-27 15:11 | superseded by D-EVL-15 (from 22:06) |
| D-EVL-15 | Trust the leaderboard over our estimators | 2026-09-27 22:01 | adopted |
| D-EVL-16 | Keep the −6 threshold; reject looser US/India thresholds (mixbp5, mixbp4) | 2026-09-27 22:38 | adopted (−6 kept) |
| D-EVL-17 | Lead with the public leaderboard score; label 0.9913 as local validation | 2026-09-29 02:46 | adopted |

## Records

### D-EVL-01 · A shared deterministic holdout: 25% of train S1, out-of-fold groups, a dev sample
- **When (IST):** 2026-09-25 12:11 (Plan A §5), 12:53–13:00 (built), 14:15 (contracts v1, C2), 14:25 (gate command-line tool), 15:46 (dev sample) · **Phase:** P0–P1 · **Area:** EVL
- **Decided by:** Ameya (coordinator, in contracts v1); proposed and built by agent for Ameya
- **Status:** adopted
- **Problem:** Three people on three machines must produce comparable numbers. France has no labels. Supervised statistics such as dictionaries and encodings must not leak into the evaluation. Every number needs its command and commit: "Any number without the command and commit that produced it doesn't count."
- **Options considered:**
  1. Plan A's disjoint S1 splits: A 40% (stage 1), B 35% (stage 2), C 25% holdout, about 550k entities.
  2. Plan B's cluster-level split.
  3. Contract C2: fold(eid) = splitmix64(eid) mod 20; holdout = folds 0–4 (25%); training folds 5–19 in three out-of-fold (OOF) groups, (fold − 5) // 5; a fold-0 dev subset. An OOF score comes from a model that did not train on that row.
  4. Ad-hoc random splits per person (rejected implicitly).
- **Choice and why:** Option 3.
  - The split is by S1 entity, because the metric is per S1 and stage-2 features need every candidate of an S1. (Stage 2 is the second model stage; it scores each pair against its competitors.)
  - It is a pure-integer hash of the id, so every machine computes the same split without sharing files and without using row order. Row-order leakage was checked: correlation −0.001.
  - 25% gives about 550k entities.
  - Blocking always runs over the full train pool and competition features over the full candidate graph, as on test.
  - Nothing supervised is fitted on the holdout (dictionaries, target encodings, city aliases, calibration). One or two scalars may be tuned on it.
  - Fold 0 serves quick checks (noise about ±0.002); numbers in pull requests use the full holdout (about ±0.001).
  - At 15:46 a dev sample (a quarter of folds 0/5/10/15, about 110k S1) was added for laptops with 8–16 GB. It spans the holdout and every OOF group.
  - The metric module (`ber.eval.metric`) reproduces the official macro F0.5. It also reports blocking recall and the oracle ceiling.
- **Evidence:**
  - Holdout 549,699 S1 = 24.91% of train S1 (US 329,717; India 219,982) [M]. The numpy hash matches a pure-Python reference; the share is 25.07% on 200k consecutive ids [M] [chat:ameya/19e315ba 2026-09-25 12:56], [12:57].
  - An empty prediction scores 0.0558 (the singleton share) and a perfect one 1.0000; the gate from empty to perfect gives Δ +0.9442 [0.9436, 0.9448] [M] [handover 2026-09-25_1425](../../docs/handover/2026-09-25_1425_ameya_dev-skeleton.md).
  - Paired deltas come with tight 95% intervals, e.g. +0.0097 [0.0095, 0.0099] [M].
- **Outcome:**
  - Every local number in the project is on this holdout.
  - Refinements: the holdout and test got the mean of the three group models ([FEATURES v3](../../experiments/ameya/model-v1/FEATURES.md)); from v5all the final fit made the holdout a fourth OOF group, so each model saw 75% of train (D-NRM-04); on 27 Sep fold-parity halves A/B and repeated 2-fold cross-validation were added for tuned rules (D-EVL-03, D-EVL-13).
  - Leakage audits found none ([ANALYSIS_v3 §7](../../experiments/ameya/model-v1/ANALYSIS_v3.md), [RESEARCH_v5 §1](../../experiments/ameya/model-v1/RESEARCH_v5.md)). Choosing the DP shift on the holdout is "tiny optimism".
- **Hindsight:** The holdout has no France. That is why the leaderboard gap (France about 0.93) was invisible locally, why the work with the largest leaderboard effect could not be gated on it, and why we needed the leaderboard arithmetic of D-EVL-08.
- **Links:** [CONTRACTS C2](../../docs/CONTRACTS.md) · `ber/eval/splits.py` · [handover 2026-09-25_1300](../../docs/handover/2026-09-25_1300_ameya_repo-setup.md) · [CONTRIBUTING §1.6](../../CONTRIBUTING.md) · D-ORG-05 · [theory: evaluation methodology](../theory/05-evaluation-methodology.md)

### D-EVL-02 · Test shift by diagnostics, not "test ≈ train" and not a drop-S1 stress test
- **When (IST):** 2026-09-25 12:11 (shift seen), 13:54–13:56, 14:15 (FINAL_PLAN #13–#14), 15:20 (look-alike type established) · **Phase:** P0–P1 · **Area:** EVL / DEC
- **Decided by:** Ameya, in the final plan, from his 25 Sep data checks (analysis and proposal: agent for Ameya)
- **Status:** adopted (the G8 diagnostics were built into `decide.py` at 18:04). Plan A's drop-S1 stress test was rejected as a threshold driver. The inference drawn at 15:20 (the test cut-off should be stricter) was not borne out; see Hindsight.
- **Problem:** Test has 5.75 vendor records (S2/S3) per S1 against 4.68 in train (+23%). Do thresholds tuned on train transfer?
- **Options considered:**
  1. Trust the train-tuned thresholds. This is Plan B's "test resembles train" ([H] #20).
  2. Plan A's stress test: drop about 20% of holdout S1 to mimic the test's density, and tune thresholds on that.
  3. Per-country test diagnostics (predicted matches per S1, empty share, owned-probability mass, max-probability distribution) plus an EM prior estimate (a way to estimate the match rate without labels). Shift only on consistent evidence, with at most one leaderboard probe (gate G8).
- **Choice and why:** Option 3.
  - In India, where train and test S1 pools are similar in size (883k against 810k), the closeness profile of records to their nearest S1 is unchanged: close on name and address 31.7% against 31.8%, nothing close 43% against 44%. Records with a missing owner would give about 26% and 53%. So the drop-S1 test "models the wrong shift" and was kept only as a failure-mode check. "So test has more matches or more look-alikes per S1, not records whose owner is missing."
  - At 15:20 exact high-precision proxies per S1 were flat from train to test: exact name and number 1.20 → 1.23 in India and 1.46 → 1.46 in the US; exact full address 0.27 → 0.27 and 0.31 → 0.31. Only "same name, different number" grew (India 0.57 → 0.68; US 0.56 → 0.81; 49% true on train). So each test S1 still has about 3.5 true matches but about 2.3 look-alikes instead of 1.2, and about 40% of test records match nothing against 26% in train.
  - The agent therefore argued that "the holdout will overstate our leaderboard score… the match cut-off on test should be higher… not lower", with a concrete G8 check: US/India predicted matches per S1 on test should equal the holdout's.
- **Evidence:**
  - Test density 5.75 against 4.68 [M] [FINAL_PLAN §1 #13, #14](../../plans/FINAL_PLAN.md); proxies [M], the inference [E] [chat:ameya/19e315ba 2026-09-25 15:20]. The retrieval proxy finds the owner for only about 49% of true pairs, so only comparisons made with the same proxy are meaningful ([plan checks](../../experiments/ameya/plan-checks/README.md)).
  - Baseline predictions per S1: 3.16–3.28 on test against 3.20–3.31 on the holdout, "not over-accepting look-alikes". Model v1's owned pairs in the uncertain 0.5–0.9 band were about 2× the holdout's on test, about 1.2× with the look-alike odds of v2. France stood out at 3.48 per S1 (v2).
  - Later, US/India predicted per S1 on test 3.37–3.39 against 3.36 on the holdout [M] [chat:ameya/a2a1b62a 2026-09-26 14:00].
- **Outcome:** US/India test behaved like the holdout at every check ([ANALYSIS_v3 §1](../../experiments/ameya/model-v1/ANALYSIS_v3.md), [RESEARCH_v6 §1, §6.18](../../experiments/ameya/model-v1/RESEARCH_v6.md)). No shift was applied, and EM was judged unnecessary ([ANALYSIS_v3 §8](../../experiments/ameya/model-v1/ANALYSIS_v3.md)). The extra 23% turned out to be look-alike distractors (about 2 per S1 on test against 1.2 on train), rejected at the holdout rate.
- **Hindsight:** Correct to measure and not assume. The holdout did overstate the leaderboard (model v2: 0.98436 on the local holdout against 0.97608 on the public leaderboard, LB), but the cause was mostly France (about 0.93), not US/India look-alikes. The US/India diagnostics matching the holdout was the right signal. The shift that mattered was a covariate shift (new words and conventions in France), not a prior shift (a different match rate).
- **Links:** [DECISION](../../plans/DECISION.md) · [FINAL_PLAN §9](../../plans/FINAL_PLAN.md) (G8) · D-EVL-07 · D-ORG-03

### D-EVL-03 · Gates: every component must beat a simpler one in a paired bootstrap (G1–G13)
- **When (IST):** 2026-09-25 14:15 (FINAL_PLAN §9, from Plan B), 14:25 (gate tool built); in use from 17:31; fold-parity halves added 2026-09-27 06:36 · **Phase:** P0–P5 · **Area:** EVL
- **Decided by:** Ameya (coordinator), grafted from Sachi's Plan B (proposed by: Sachi); built by agent for Ameya
- **Status:** adopted. The +0.002 bar was relaxed in practice (see Outcome).
- **Problem:** Three people, about 60 hours, many plausible components, and a real risk of shipping complexity that does not pay. Results had to be comparable and documentable.
- **Options considered:**
  1. Keep components on intuition or point estimates; build all of Plan A.
  2. Tag every claim ([M] measured, [F] fact, [H] hypothesis) and give each hypothesis a named gate that can overturn it. A component ships only if it beats the simpler one in a paired bootstrap over S1 (1,000 Poisson-weighted resamples of the S1; the same S1 are used for both systems) by Δ ≥ +0.002 with a 95% interval above 0 (+0.003 for heavy extras), with no loss in leave-one-country-out (LOCO: train on two countries, test on the third) or the France diagnostics, within the runtime budget. G6 needs only Δ > 0 with the interval above 0. Ties go to the simpler option. Every gate result becomes a decision record (contract C10), and the methodology gets an ablation table.
- **Choice and why:** Option 2, Plan B's discipline. Paired per-S1 differences make small gains detectable. "Every hypothesis has a gate in §9 that can overturn it."
- **Evidence:**
  - The tool: minimum gain 0.002, one Poisson(1) weight per entity [chat:ameya/19e315ba 2026-09-25 17:50]; [FINAL_PLAN §0, §4.8, §5, §9](../../plans/FINAL_PLAN.md), [CONTRACTS C10](../../docs/CONTRACTS.md), [DEVELOPMENT §6](../../docs/DEVELOPMENT.md).
  - First gates (Sachi): G6 on v0, dev sample: DP −0.00024 [−0.00091, +0.00049], threshold kept [G6 record](../../docs/decisions/2026-09-25_1731_gate-g6-dp-vs-threshold.md). G4 on v2, dev fold 0: stage 2 +0.00692 [+0.00622, +0.00772] over stage 1 alone, kept [G4 record](../../docs/decisions/2026-09-25_2103_gate-g4-stage2.md).
  - What happened to each gate:

  | gate | question | what happened |
  |---|---|---|
  | G1 | blocking recall at least 99.0% (v0) and 99.5% (v1) at about 30 candidates per S1? | 0.9752 (v0), 0.9857 (v1), 0.9899 (v2), 0.99135 (v3); the 99.5% bar was never met (D-BLK-03, D-BLK-07, D-BLK-08, D-BLK-11). No per-view 0.1-point table in the sources |
  | G2 | dense SVD search as good as sparse? | never run; the engine built was the sparse one (D-BLK-05) |
  | G3 | per-token look-alike odds (`lo`) help? | the group is in v2; no holdout gate number found. US-only LOCO 0.94180 without it, 0.96106 with it |
  | G4 | stage 2 beats stage 1 alone? | passed (above); at v3 stage 1 alone 0.9871 against 0.98882 for the full model |
  | G5 | softmax with "none" beats argmax ownership? | never built (D-PRB-02) |
  | G6 | DP beats a tuned threshold? | mixed, see Outcome |
  | G7 | France predictions beat an empty France? | probes packaged, never uploaded (D-EVL-06) |
  | G8 | does test need a threshold shift? | diagnostics found none (D-EVL-02); a stricter France threshold "only loses"; the probe leg was never run, so the repo leaves it open |
  | G9 | cluster support helps? | in stage 2 from v2; no separate gate number. An audit found the cluster features "amplify accepted look-alikes" in France |
  | G10 | encoder, cross-encoder (a model that reads both records of a pair together) or LightGBM blend (a second tree-boosting model) adds value (bar +0.003)? | e5-small cross-encoder +0.00140, kept below the bar on France reasoning; e5-large and base +0.000311; later cross-encoder mixes +0.00005 to +0.0001 each; LightGBM never tested |
  | G11 | a learned pre-ranker is needed? | not formally run; the stage-0 filter and the candidate cut took the role (D-BLK-03, D-BLK-10) |
  | G12 | transliteration, dictionary and skeleton lift the Indic slice? | parity reached, 0.9872 against 0.9870; no separate delta (D-NRM-02) |
  | G13 | features transfer across countries (LOCO)? | run: an unseen country costs 0.022 with its words known and 0.10 with words unseen. It led to the proxy odds and the bitmask drop rather than pruning, and became the stand-in for France experiments |

- **Outcome:**
  - Gates ran with the tool throughout, but after v3 almost nothing reached +0.002: v3ce +0.00140 (kept anyway), nx +0.00021, v6all +0.00063, v7ce3 +0.000311, stage 3 +0.00005 (a late model stage for contested records; D-PRB-03), and the decision layer +0.000048 [ANALYSIS_v3](../../experiments/ameya/model-v1/ANALYSIS_v3.md), [RESEARCH_v5](../../experiments/ameya/model-v1/RESEARCH_v5.md), [RESEARCH_v6](../../experiments/ameya/model-v1/RESEARCH_v6.md).
  - G6 in detail. The DP passed on v2 (+0.00018) and v3 (+0.00011) and lost on stage-1 probabilities (−0.00029); the winner varied by model. On the final model the +0.000048 [+0.000007, +0.000091] is the combined decision layer: expected-F0.5 per S1 with a logit shift of +0.2, a phantom term of 0.01 and a crowd shift of −0.3, plus the acronym-join and cap rules (area RUL). The DP alone (shift and phantom) was +33.2e-6 [−7.5e-6, +75.0e-6], probability better 0.945, not significant. Repeated 2-fold cross-validation of the decision layer gave +23.7e-6 out of sample, positive in 86% of 42 splits [stacked-rules record](../../docs/decisions/2026-09-27_0636_stacked-rules.md). Here "e-6" means ×10⁻⁶ of macro F0.5.
  - The working rule became "CI above 0, positive on both fold-parity halves for late rules, ties to the simpler" (CI is the 95% confidence interval). The process rules outlived every model graft: v7ensall2 was dropped because it tied v7sq.
- **Hindsight:** The bar suited the early, large gains; at 0.99 the useful gains were 10 to 100 times smaller. The +0.002 bar was never formally revised in a record, and the formal "keep" label was set aside more than once (D-EVL-04; v3ce was kept at +0.00140).
- **Links:** [DECISION](../../plans/DECISION.md) · [handover 2026-09-25_1425](../../docs/handover/2026-09-25_1425_ameya_dev-skeleton.md) · [gate record G1](../../docs/decisions/2026-09-25_2142_gate-g1-blocking-v2.md) · D-ORG-03 · D-EVL-04 · D-EVL-13 · [theory: evaluation methodology](../theory/05-evaluation-methodology.md)

### D-EVL-04 · Model v1 for Submission 2 although the gate printed keep: False
- **When (IST):** 2026-09-25 18:51 · **Phase:** P1 · **Area:** EVL / SUB
- **Decided by:** agent for Ameya (its handover flags the exception for the team)
- **Status:** adopted (an exception to the written rule)
- **Problem:** The gate "stage 2 plus DP against stage 1 plus threshold" printed `keep: False` at Δ +0.001995 [0.001890, 0.002104], against the +0.002 bar.
- **Options considered:**
  1. Submission 2 = stage 1 plus threshold (local holdout F0.5 0.97806).
  2. Submission 2 = model v1 (local holdout F0.5 0.98006).
- **Choice and why:** Option 2. The interval is far above 0 and the miss is a rounding hair. It matches the argument made at 15:20 that the +0.002 bar "would drop a free component that gives a real +0.001. For components with no runtime or complexity cost, a 95% interval above zero should be enough."
- **Evidence:** [M] India +0.00239, US +0.00173. The DP gate at +0.00014 also printed `keep: false` under the minimum gain but was used, because the G6 rule needs only an interval above 0.
- **Outcome:** Submission 2 was model v1. With v2 the stage-2 step added +0.0022, clearing the bar.
- **Hindsight:** The record shows the +0.002 bar was not treated as binding.
- **Links:** D-EVL-03 · [chat:ameya/19e315ba 2026-09-25 15:20], [18:51]

### D-EVL-05 · Label-free France forecasts are diagnostics, not measurements
- **When (IST):** 2026-09-25 22:10 (forecast built), 2026-09-26 05:06 (judged), 05:51 → 06:31 (share-shift estimator overturned) · **Phase:** P2 · **Area:** EVL
- **Decided by:** agent for Ameya (the share-shift estimate was made by agent a1f04ee8 and overturned by agent a000fd3b)
- **Status:** adopted as a diagnostic; rejected as a France estimator
- **Problem:** France has no labels, so a forecast was needed to steer the work and the upload plan.
- **Options considered:**
  1. The model's own expected F0.5 per country: the mean of the DP's best expected F0.5 per S1. It is cheap and validated on the holdout, but optimistic by about 0.0026 because it cannot see blocking misses.
  2. The share-shift estimator (France for v5all with rules about 0.959, giving a public LB near 0.985).
  3. The leave-one-country-out forecast (France about 0.97–0.98, public LB 0.987–0.989).
  4. A France-emptied probe upload (D-EVL-06).
- **Choice and why:** Use option 1 only to compare versions with each other. Report France's level as "somewhere between 0.93 and 0.98", and put the France-emptied probe first in the upload order. Agent a000fd3b showed that the share-shift estimator had counted about 120 artifact pairs per 1000 S1 as false positives: French domain-style copies fail the profiler's in-order concatenation check (accents deleted, stop words and legal forms included, words reordered). Its agreement with v2 and v3 was "a coincidence".
- **Evidence:**
  - v3 holdout forecast 0.99139 against a real 0.98882 [M]. The v3 France forecast was 0.970 against 0.925–0.931 implied by the public LB: about +0.04 overconfidence, against +0.003 on the holdout [E].
  - Share-shift for v2 and v3: 0.936 and 0.930 against LB-implied 0.929 and 0.927 [E] [chat:ameya/agent-a1f04ee8 2026-09-26 05:51]. "Domain plus unrelated" copies per 1000 S1: France 220 predicted, US 214 true, India 202 true [E] [chat:ameya/agent-a000fd3b 2026-09-26 06:06].
- **Outcome:** v5all with rules scored public LB 0.98781, which implied France at 0.971–0.976. That matches the LOCO forecast and not 0.959 [M for the LB, E for France] [chat:ameya/19e315ba 2026-09-26 14:41]. The parent session then called the France probes "optional".
- **Hindsight:** This is the first case of the methodology's closing lesson: any estimate built from the model's own probabilities needs an independent check, because it shares the model's blind spots.
- **Links:** [chat:ameya/19e315ba 2026-09-25 23:28], [2026-09-26 05:06] · [RESEARCH_v5 §1](../../experiments/ameya/model-v1/RESEARCH_v5.md) · D-EVL-08 · D-EVL-06

### D-EVL-06 · The France-emptied probe (fr0) and its relatives: packaged, never uploaded
- **When (IST):** first proposed 2026-09-25 22:41; built 2026-09-26 02:42–04:36; repackaged 26 Sep 04:17, 15:57, 19:45, 22:16; Ameya's rulings 26 Sep 23:54 and 27 Sep 02:45; Bakshi's recommendation 27 Sep 09:29 (reasoning corrected 10:04) · **Phase:** P2–P4 · **Area:** EVL / SUB
- **Decided by:** proposed by agent for Ameya (also by Bakshi; Sachi argued for the fr0 slot at 12:12 on 26 Sep). Decided by Ameya, who alone uploads. Bakshi recommended against it after Ameya had already ruled.
- **Status:** rejected in practice. Never uploaded; gate G7 left open.
- **Problem:** The holdout has no France, so every France number is inferred by subtracting an assumed US/India level. A France-emptied upload would give US/India on test exactly, and France by difference: "the most informative upload". Label-free estimates disagreed (0.959 against 0.97–0.98), and the model's own forecast was +0.04 overconfident.
- **Options considered:**
  1. `fr0`, France emptied: F_France = (LB_v − LB_fr0) / 0.14975 + 0.0559. Here 0.0559 is the singleton share that every country shares (an empty prediction scores 1.0 on a singleton S1), and 0.14975 is France's share of test S1. Expected LB_fr0 is about 0.8507 if US/India score like the re-weighted holdout.
  2. `in0` (India emptied) to test the US/India assumption, and `frab` against `v4` to isolate the rules.
  3. Threshold probes that act on France directly (D-EVL-10).
  4. Spend the slots on model candidates and measure France by arithmetic (D-EVL-08).
  Rule of thumb for whether more France work pays: at France 0.98 or better at most about 0.0015 of public LB is left; at 0.95 or worse, 0.006 or more.
- **Choice and why:** Option 4. Through 26 Sep fr0 was "the most informative upload" (06:30). But a slot spent on it cannot improve the score. After the first upload of 26 Sep: "`probe-v4-fr0` is now optional. The France level is known to about ±0.003 from this upload." By 23:57 it was "low priority. It measures France but doesn't improve the score directly"; the threshold probes answer the actionable question. Ameya on 27 Sep: "5 slots, no pure probes; protect the floor". The LOCO analysis argued that a stricter France threshold cannot help, because an unseen country loses 0.024 in confident convention errors; on 27 Sep 97% of French predictions had pc ≥ 0.99 (pc is the calibrated stage-2 probability), "so the gap is confident substitutions, out of reach of thresholds or rules". Bakshi's reasons (09:29, corrected 10:04): the probe costs a slot, cannot improve the score, and no decision depends on it. Truly singleton French S1 still score 1 under an empty prediction, so fr0 does not isolate US/India; his review of PR #49 had already said fr0 "identifies two quantities, not three country scores".
- **Evidence:** [E] formula and rule of thumb [RESEARCH_v5 §8.2](../../experiments/ameya/model-v1/RESEARCH_v5.md), [chat:ameya/19e315ba 2026-09-26 12:24]. Probe packages probe-v4-fr0, probe-v6s3-fr0 and probe-v7-fr0 exist and were never uploaded. [LB 2026-09-26 #01](../../submissions/records/2026-09-26_sub01.md). Bakshi's sensitivity script: [france_sensitivity.py](../../experiments/bakshi/final-package/france_sensitivity.py), [issue #45], [PR #49]. [status ameya @7568980], [@75b4276], [@6c222d7].
- **Outcome:** G7, and the probe leg of G8, never closed. France stayed an estimate [E] throughout, 0.971–0.981 for the later models.
- **Hindsight:** With five uploads a day, one fr0 upload on 26 Sep would have turned every later France estimate into a measurement; the cost was one slot that could have carried a real improvement. The research session that wrote this down adds that it is worth admitting to the jury. In practice the consistent hits of the "US/India equal the holdout" arithmetic made the probe unnecessary (D-EVL-07).
- **Links:** [handover 2026-09-26_0417](../../docs/handover/2026-09-26_0417_ameya_france-generator-ops.md) · [chat:ameya/19e315ba 2026-09-26 02:51], [04:37] · D-EVL-08 · D-EVL-10 · [theory: evaluation methodology](../theory/05-evaluation-methodology.md)

### D-EVL-07 · Attribute the leaderboard gap to France
- **When (IST):** 2026-09-26 00:16–00:29 (first attribution), 05:00–05:09 (re-checked), 14:07–14:13 (research budget, corrected 16:16), 14:52–16:09 (re-measured on v6all) · **Phase:** P2–P3 · **Area:** EVL / FRA
- **Decided by:** agent for Ameya. Ameya's critique at 00:05 had suspected France, and an audit fork found no pipeline divergence for US/India. At 14:07 Ameya asked for "deep research … why are we getting a different score"; a parallel session did it and the main session ran the corrections.
- **Status:** adopted, with corrections
- **Problem:** Model v2 scored 0.97608 on the public LB against 0.98436 on the local holdout (gap −0.0083). Model v3 scored 0.97961 against 0.98882 (gap −0.0092): +0.0045 on the holdout but only +0.0035 on the LB. Where did the gap come from?
- **Options considered (hypotheses):** a metric mismatch; a corrupted file; a wrong holdout number; an odd public-subset mix; accents; subset luck; a US/India shift on test (records per S1 +23%, about twice the look-alike distractors, smaller same-name pools); France (15% of test, no labels); US pool size; blocking crowding; holdout optimism; leakage.
- **Choice and why:** France, after each hypothesis was checked. The metric, the file path and the public-subset mix were ruled out by measurement. US/India test predictions match the holdout within 1–2% in records per S1, empty share, score profile and look-alike acceptance. France predicted 3.54 records per S1 against the generator's 3.46 everywhere, about 0.18 false positives per S1.
  - The parallel session's first budget (14:07): France −0.0065 to −0.0075, US pool size −0.001 to −0.0015, crowding −0.0003 to −0.001, holdout optimism −0.0003, noise ±0.0002.
  - The main session re-measured each term on v6all before acting (14:52–16:09). US extra predictions are mostly correct, because the half-size US pool resolves identical-name ties. Tightening the blocking S1 cap from 15 to 10 costs only −0.000093, so crowding is negligible. France's sum of pc per S1 is 3.5456 against at most 3.46.
  - So France is essentially the whole gap, and the pool-size fix (rescale count features to the train pool size, widen the blocking S1 cap from 15 to 25) was dropped. One unknown remained: France is about 0.971 if US/India score like the holdout, about 0.987 if they sit 0.002 below.
- **Evidence:**
  - France has 9% of predictions below pc 0.99, the holdout 3% [M, label-free count].
  - The holdout re-weighted to the test's same-name pool mix: US 0.98995 → 0.99083, India 0.99044 → 0.99055 for v4 [E]. France implied 0.925–0.931 (v3) and 0.927–0.944 (v2) [E].
  - The test S1 file is shuffled (each tenth holds about 25.9k France, 81k India and 66.3k US S1), so a public subset holds about 15% France [M].
  - No leakage: OOF look-alike odds and cross-encoder scores, the Indic dictionary from folds 5–19, ID correlation 0.0002, row-order correlation 0.0014 [M] [RESEARCH_v5 §1](../../experiments/ameya/model-v1/RESEARCH_v5.md).
  - US: test 3384.5 against holdout 3366.7 predictions per 1000 S1; expected false positives 4.96 against 4.70 [M/E] [RESEARCH_v6 §1](../../experiments/ameya/model-v1/RESEARCH_v6.md).
  - The predictions then hit: v7n was predicted at 0.9894–0.9900 and scored 0.989721 on the public LB [LB 2026-09-26 #03](../../submissions/records/2026-09-26_sub03.md).
- **Outcome:** v5all with rules scored 0.98781 on the public LB (France implied 0.971–0.976 [E]), and the gap shrank to −0.0024. France work (cross-encoder diversity, self-training) then moved the public LB from 0.98781 to 0.990179 with little change on the holdout.
- **Hindsight:** Right, and the decomposition guided everything after. The natural experiment in the first budget (US pool halved, India not) was a good idea, but the sign of its effect (false positives or true positives) needed the follow-up check. Report both the hypothesis and its refutation. The France-emptied probe that would have settled the last unknown was never uploaded (D-EVL-06).
- **Links:** [chat:ameya/19e315ba 2026-09-26 00:16], [00:19], [05:06], [15:19], [15:32] · [chat:ameya/a2a1b62a 2026-09-26 14:00] · [ANALYSIS_v3 TL;DR](../../experiments/ameya/model-v1/ANALYSIS_v3.md) · [handover research-v6-gap-budget](../../docs/handover/2026-09-26_1557_ameya_research-v6-gap-budget.md) · D-EVL-08

### D-EVL-08 · Estimate France by leaderboard arithmetic
- **When (IST):** 2026-09-26 02:07 (first), refined 05:20, 15:57 and 22:25; confirmed by 2026-09-27 03:00 · **Phase:** P2–P4 · **Area:** EVL
- **Decided by:** Ameya (proposed by: agent for Ameya)
- **Status:** adopted; the working method to the end
- **Problem:** France has no labels. Was the gap US/India drift or France, and how good is France?
- **Options considered:**
  1. Probes that empty one country (D-EVL-06).
  2. A label-free comparison of the US/India test predictions with the holdout, plus algebra.
  3. A decomposition LB = 0.38274·F_US + 0.46751·F_India + 0.14975·F_France, with US/India at the (re-weighted) holdout level.
  4. Uploads whose difference is France alone.
- **Choice and why:** Options 2 to 4.
  - US/India test predictions "behave exactly like the holdout": predicted records per S1 within 0.01 and the same empty share. The test file is shuffled (15% France in any subset) and nothing leaks. So LB = 0.85 × US/India + 0.15 × France.
  - Refined forms: LB ≈ 0.8423 + 0.14975 × F_France (05:20); LB_fr0 = 0.38274·F_US + 0.46751·F_India + 0.14975 × 0.0559 (15:57); the US/India part is 0.843226 for v7n (22:25).
  - RESEARCH_v5 and v6 called the fr0 probe "the only way to know"; it was packaged three times, and the slots went to model candidates instead.
  - By 27 Sep 03:00 "the LB has matched our 'US/India holdout part + 0.14975 × France' arithmetic within noise at every upload". The formula "gives v6all's actual score exactly". Each upload changed France alone where possible.
- **Evidence:** France implied by the public LB: v2 0.927–0.944, v3 0.925–0.931, v5all with rules 0.971–0.976, v6all 0.973, v7n 0.978, v7nst 0.981 [E] [RESEARCH_v5](../../experiments/ameya/model-v1/RESEARCH_v5.md), [RESEARCH_v6 §6.7–6.11](../../experiments/ameya/model-v1/RESEARCH_v6.md); the formula matches v6all's score ([status ameya @8885afc](../../docs/status/ameya.md)).
- **Outcome:** Every France number after this is an estimate [E]. Bakshi noted that 0.14975 is France's share of the whole test (259,452 of 1,732,544 S1), so the formula assumes that the public subset has the whole test's country mix. That is unverified [U].
- **Hindsight:** The method steered the work well, because each upload changed France alone where possible. But the absolute level of France was never measured.
- **Links:** [handover 2026-09-26_0207](../../docs/handover/2026-09-26_0207_ameya_leaderboard-gap-france-v4.md) · [decision model-v4](../../docs/decisions/2026-09-26_0207_model-v4-france-and-cross-encoder.md) · [handover 2026-09-26_0520](../../docs/handover/2026-09-26_0520_ameya_research-gap-candidates.md) · [LB 2026-09-26 #01](../../submissions/records/2026-09-26_sub01.md) · [handover 2026-09-27_0111](../../docs/handover/2026-09-27_0111_bakshi_final-package.md) · D-EVL-07

### D-EVL-09 · Triage Bakshi's "0.990+" proposals with a loss ledger
- **When (IST):** 2026-09-26 15:22 · **Phase:** P3 · **Area:** EVL / RUL / CE
- **Decided by:** agent for Ameya (a proposal to Ameya); Bakshi later tested his own items
- **Status:** adopted, with one reversal by Bakshi's own measurement
- **Problem:** Bakshi's note "Experiments aimed at 0.990+" listed five ideas, and about 28 hours were left.
- **Options considered and verdicts:**
  1. A verifier for confident mistakes: about +0.001 of room at most on US/India, mostly unresolvable. Skip as a separate model.
  2. An edit-process scorer: small on US/India but aimed at France. Do a light version (extend the rules to combined edits).
  3. Sibling-mediated retrieval: at most about +0.0012, on records with an address. Skip.
  4. A rival-text owner model: +0.00003. Skip.
  5. An address-evidence audit of rule additions ("12 Rue Jean Moulin" and "12 Rue Jean Jaures" both key to "12/jean"): do it, since it guards rule additions. A joint decoder: skip.
- **Choice and why:** Measure each idea against a loss ledger of the v6all errors before acting on it. In the ledger 74% of missed holdout pairs have an empty-address record, and US/India are near their floor (D-PRB-03).
- **Evidence:** the ledger [M] [chat:ameya/a2a1b62a 2026-09-26 15:22].
- **Outcome:** Bakshi's PR #34 measured both "do" items and recommended against them. The full-address check would wrongly remove 3 true additions, and swap-plus-append predictions are "overwhelmingly true". "That also refutes my suggestion to drop any combined edit that includes a swap." Everything stayed off by default.
- **Hindsight:** A good example of measuring before acting. The agent's light rule would have hurt.
- **Links:** [PR #34] · D-PRB-03

### D-EVL-10 · France threshold probes (fr090r) and France-only test packages: built, never uploaded
- **When (IST):** 2026-09-26 20:28–20:48 (threshold probes); 2026-09-27 10:59–11:45 (France-only packages), Ameya's rule at 14:46 · **Phase:** P3–P4 · **Area:** EVL
- **Decided by:** agent for Ameya (design); the uploads were Ameya's call. He ruled out pure probes at 23:54 on 26 Sep, and at 14:46 on 27 Sep that the remaining slots were for "our best, and that too not now".
- **Status:** built, then not uploaded
- **Problem:** France has three to four times the uncertain band of US/India, and whether its threshold should move is a leaderboard question. But `fr090` (drop French model predictions below pc 0.9 after the rules) would also drop the rules' own true-copy edits (A, APP and ACR, the generator's copy types that US/India labels show to be 97–99.8% true; D-EVL-11) that the model scores 0.7–0.9 because of the French biases. That is "a known loss that would hide the answer". Separately, an earlier control upload (v7nst-dpc) had shown that a leaderboard difference can isolate a change.
- **Options considered:**
  1. `fr090` as built.
  2. `fr090r`: cut before the rules, so the rules re-add their copies, plus `fr095r` and `fr080r` to bracket.
  3. `frlo` (`fr_add.py --lo 0.5`): add owned French pairs with pc between 0.5 and the threshold.
  4. France-only test uploads: US/India byte-identical to v7sq-dpc, so LB − 0.990545 is the French effect.
  5. Label-free estimates only.
  6. Upload full composites.
- **Choice and why:** `fr090r`, whose dropped set is France's unexplained band only. `frlo` was marked low value: 56% of its records have two S1 above pc 0.1 (ties) and 44% an empty address, so its precision is likely near 50%, below the 0.72 break-even. The agent built the France-only tests ready to go (fr-v7sq4 passed, with only France changed: 2,778 S1) and recommended one as upload 1 at about 12:00. Ameya's 14:46 rule ended that; from then on label-free valuation (later "cal", D-EVL-14) judged France.
- **Evidence:** [E] unless stated.
  - On v7ce3: `fr090` −18,263; `fr090r` −10,738 net (22,337 dropped before the rules; the rules re-add A 10,896, ACR 1,744 and APP 3,808). What stays dropped: 38% same name (other or empty address), 30% non-list swaps, 28% unrelated names at the address, 0.3% acronyms; 80% have a single S1 above pc 0.1 [RESEARCH_v6 §6.4](../../experiments/ameya/model-v1/RESEARCH_v6.md).
  - On v7n: `fr090r` drops 18,183 before the rules (the rules re-add 16,003), `fr095r` 29,595 (114.1 per 1000 S1), `fr080r` 9,476 (36.5 per 1000).
  - fr-v7sq4 differs only in French S1 (US 0, India 0) [M] [chat:ameya/19e315ba 2026-09-27 11:45].
- **Outcome:** Built and validated for v7ce3, v7n and v7nst. The France-only packages fr-v7sq4, fr-v7sq6, fr-v7sqwg and fr-v7xbag exist; none was uploaded.
- **Hindsight:** The later leaderboard verdicts (RESEARCH_v6 §6.20) showed that pc-based French estimators can be badly biased on decoys. For round 3, cal predicted +69e-6 and the public LB gave −46e-6. A France-only test would have exposed that earlier.
- **Links:** `fr_threshold.py`, `fr_add.py` · D-EVL-06 · D-EVL-14 · D-EVL-15

### D-EVL-11 · The rule-population AUC as the label-free yardstick for France
- **When (IST):** 2026-09-26 20:49 (first AUC), 21:36–21:39 (tools), 22:30 → 2026-09-27 02:51 (cross-encoder ranking and its limits) · **Phase:** P3 · **Area:** EVL
- **Decided by:** agent for Ameya (the AUC). Sachi and Ameya proposed using it to rank new cross-encoders; Bakshi bounded it with his saturation test.
- **Status:** adopted with limits; superseded by D-EVL-12 once it saturated
- **Problem:** France has no labels, and the holdout cannot rank models for France. The band AUC on the holdout cannot tell whether a cross-encoder helps France.
- **Options considered:**
  1. Band AUC on the US/India holdout.
  2. Label-free counts only.
  3. Leaderboard uploads only.
  4. AUC on France's rule populations, whose truth is known by type from US/India. The rules step (`post_ops`) sorts French candidate pairs by generator operation. A, APP and ACR are copy edits that US/India labels show to be 97–99.8% true (64,840 pairs: A 38,304, ACR 14,884, APP 11,652). Op-B pairs are look-alikes (64,016): a real word swapped into the slot of an S1 name word at the S1's own address.
  5. The same check on final decisions (Bakshi's `rulepop_decisions.py`).
- **Choice and why:** Option 4 for cross-encoders. The rules decide these pairs anyway, so final decisions do not depend on the model, "but how well a model's pc separates them measures its competence on French pairs of known type". For cross-encoders the spread is real (0.774 → 0.831). Bakshi showed that option 5 is saturated: every package predicts 0 of the 64,016 op-B pairs because the rules suppress them, and v7nst and v7ens2 differ on only 29 of 128,856 pairs. He also stated the requirement for a usable label-free check: a truth rate transferred from the labelled countries, and a population that no rule decides. Option 4 also becomes circular once a model is self-trained on pseudo-labels derived from those same populations.
- **Evidence:** AUC of stage-2 pc [E]: v6all 0.8546 → v7ce3 0.8651 → v7n 0.8721 → v7c 0.8741 → v7m 0.8776. It tracked the leaderboard: v6all to v7n moved France from about 0.973 to about 0.978 [LB 2026-09-26 #03](../../submissions/records/2026-09-26_sub03.md). Self-trained models saturate at 0.984–0.986 (v7nst 0.9844, v7nst2 0.9857, v7mst 0.9846) [RESEARCH_v6 §6.14](../../experiments/ameya/model-v1/RESEARCH_v6.md). Bakshi's saturation test [M] [issue #45, 02:24]; ledger `rulepop_decision_check`.
- **Outcome:** The tools `rule_pop.py`, `rule_auc.py` and `ce_rule_auc.py` were added in PR #47 for the team, including Sachi's Qwen. Packages were then compared with `fhs.py` overnight (D-EVL-12) and with `cal` on 27 Sep (D-EVL-14).
- **Hindsight:** It is biased for self-trained models, whose pseudo-labels contain these populations, and it sees only rule-typed pairs, not ties or empty-address records. Bakshi's summary (10:54 on 27 Sep): "use the offline French proxies to rank and to detect drift, never to size a gain".
- **Links:** [handover 2026-09-26_2049](../../docs/handover/2026-09-26_2049_ameya_squeeze-v7n.md) · [handover Sachi 1800](../../docs/handover/2026-09-26_1800_sachi_llm-cross-encoder.md) · [rulepop_decisions.py](../../experiments/bakshi/final-package/rulepop_decisions.py) · [PR #47], [issue #45] · [status ameya @75b4276](../../docs/status/ameya.md) · [theory: self-training and domain shift](../theory/09-self-training-and-domain-shift.md)

### D-EVL-12 · fhs.py replaces the saturated rule-population AUC
- **When (IST):** 2026-09-27 02:24–02:51 · **Phase:** P3 · **Area:** EVL
- **Decided by:** agent for Ameya; Bakshi's parallel test showed the need
- **Status:** adopted with known limits: a drift detector, not a sizer. Superseded as a sizer by D-EVL-14.
- **Problem:** The stage-2 French rule AUC saturated after self-training (D-EVL-11). Bakshi found the same check on final packages flat: every package predicts 0 of the 64,016 op-B look-alikes, true-copy recall sits at 0.9682–0.9711, and v7nst and v7ens2 differ on only 29 of 128,856 population pairs.
- **Options considered:**
  1. Keep the rule-population AUC.
  2. Leaderboard only.
  3. Count French pairs in populations whose truth the generator fixes, against a reference package. COPY: the same content words up to typos (Cie and Compagnie, Ets, St, Ste normalised) with the same or an empty address, which are true copies. SWAP: one content word replaced at the same address.
- **Choice and why:** Option 3, the "French heuristic score" `fhs.py`. Score per 1000 French S1 = (COPY gained − lost) + (SWAP removed − added), calibrated on the known step v7n → v7nst = +9.51 (a step that was worth +0.0031 for France on the public LB). At 02:28–02:29 the swap truth was found to depend on the sub-population, so COPY net became the trusted part.
- **Evidence:** [E] all fhs values [chat:ameya/19e315ba 2026-09-27 02:25], [02:29], [02:44].
- **Outcome:** It drove every morning ranking (v7sq-dpc best at +2.19). After the uploads it proved a drift detector, not a sizer: the agent's estimate for v7sq-dpc was +0.00012 against a measured +0.000366, three times more [chat:ameya/19e315ba 2026-09-27 10:09]. Bakshi called it "a working drift detector and a broken sizer", about 8× off on v7sq's magnitude [chat:ameya/19e315ba 2026-09-27 10:53].
- **Hindsight:** The methodology's closing lesson applies: on a country without labels, "any estimate built from the model's own probabilities needs an independent check, because it shares the model's blind spots".
- **Links:** [fhs.py](../../experiments/ameya/model-v1/fhs.py) · [handover 2026-09-27_0706](../../docs/handover/2026-09-27_0706_ameya_final-stack.md) · D-EVL-11 · D-EVL-14

### D-EVL-13 · Three memory-capped analysis sub-agents; gains must hold on two disjoint halves
- **When (IST):** 2026-09-27 02:57–03:00 · **Phase:** P3–P4 · **Area:** EVL / ORG
- **Decided by:** Ameya ("you can spin 2-3 agents") and the agent
- **Status:** adopted
- **Problem:** Ameya: "Don't overlook or discard negligible gains, we are now at 13th rank, people are going up on even 0.00001."
- **Options considered:** not recorded.
- **Choice and why:** Three sub-agents: polish (French post-processing), decide (the decision rule) and hunt (US/India holdout errors a rule can fix). Each worked in its own scratch folder with no git and no pipeline files, and every gain had to hold on two disjoint halves of the holdout. Reports were due about 04:15–04:45.
- **Evidence:** [chat:ameya/19e315ba 2026-09-27 02:57]. Their paired bootstraps used the shared gate tool with fold-parity halves A and B [stacked-rules record](../../docs/decisions/2026-09-27_0636_stacked-rules.md).
- **Outcome:** They produced the stacked decision layer (D-EVL-03; the rules record gives +48.1e-6 for the combined layer). The laptop crash interrupted them at 03:35 and they were resumed from their transcripts at 03:47 (D-ORG-19). The harness blocks sub-agents from writing .md files, so the main session saved their REPORT.md files.
- **Hindsight:** unknown (none recorded).
- **Links:** D-EVL-03 · D-ORG-19

### D-EVL-14 · Value French changes with "cal"
- **When (IST):** 2026-09-27 15:11–17:07 · **Phase:** P4 · **Area:** EVL
- **Decided by:** agent for Ameya (proposed by: agent a2762d22; backtest by the France-diff agent)
- **Status:** adopted for the rest of the day; superseded by D-EVL-15 from 22:06, when it was shown biased on 7B-rejected decoys
- **Problem:** The label-free French estimators disagreed (s1 had the right shape but was optimistic, s2 was pessimistic, the size-bias test works for populations only), and uploads were scarce. Several estimators below value a change by the model's own probabilities. The 7B is the Qwen2.5-7B language model that re-checks confident predictions (area LLM).
- **Options considered:**
  1. s1: truth by pc band, from contested pairs.
  2. s2: the old model's pc taken as truth.
  3. own: each variant's own US/India holdout changes, by pc band.
  4. cal: the new model's pc calibrated on the US/India holdout.
  5. The size-bias test.
  6. fhs: COPY and SWAP counts (D-EVL-12).
- **Choice and why:** cal, with corroborating checks: the own-holdout estimate, reverts of changes confirmed by the leaderboard, the cross-encoder signature, and the quality of holdout adds and drops. A switch needs a candidate to win on every estimator. "The downside scenario was never right." Size bias "is not valid for valuing change sets" [chat:ameya/19e315ba 2026-09-27 18:08].
- **Evidence:** backtest on past leaderboard moves [M against the public LB] [chat:ameya/19e315ba 2026-09-27 15:18], [chat:ameya/agent-a2762d22 2026-09-27 15:11]:

  | estimator | right sign | scale | mean absolute error | correlation |
  |---|---|---|---|---|
  | cal | 4 of 5 | 0.96 | 42e-6 | 0.98 |
  | s1 | 4 of 5 | 0.79 (about 20% low) | 75e-6 | 0.99 |
  | s2 | 0 of 5 | −0.96 | 697e-6 | −0.21 |

  The agent's later write-up counts six leaderboard pairs, probably after the point added at 16:44 [U]. For mixmdp, cal predicted +174e-6 in one note [chat:ameya/19e315ba 2026-09-27 16:36] and +146e-6 in another [chat:ameya/agent-a2762d22 2026-09-27 17:07], against about +130e-6 measured (+134e-6) [E]. The size-bias test had valued mixmdp's look-alike drop at +58e-6, and every pc-based estimator at −20e-6 to −31e-6.
- **Outcome:** cal drove the French picks (v7sq7wg → mixmdp, then v7sq6r3, then v7sq6r4). At 22:06 the leaderboard showed France(v7sq6r3) − France(mixmdp) = −46e-6, where cal had predicted +69e-6. Stage-3 pc is overconfident on generic-name decoys (all 676 decoys that v7sq6r3 would re-add have a 7B logit below −6; a logit is the 7B's raw score), so the pc-based estimators were 53e-6 to 98e-6 too optimistic on that family [M for the LB, E].
- **Hindsight:** RESEARCH_v6 §6.20 finds the pc-based estimators, cal included, biased on decoys: they valued putting back the 7B-rejected French decoys at +49e-6 to +65e-6, which the leaderboard contradicted. After the 7B drops, cal alone cannot rank French models. This is the methodology's closing lesson again.
- **Links:** [RESEARCH_v6 §6.20](../../experiments/ameya/model-v1/RESEARCH_v6.md) · [chat:ameya/agent-a2762d22 2026-09-27 17:07] · D-EVL-12 · D-EVL-15

### D-EVL-15 · Trust the leaderboard over our estimators
- **When (IST):** 2026-09-27 22:01–22:31 · **Phase:** P5 · **Area:** EVL / SUB
- **Decided by:** agent for Ameya (analysis with the France-diff agent)
- **Status:** adopted. B+ was recommended and not uploaded.
- **Problem:** Round-3 France measured −0.000046 against B's France, although cal had predicted +0.000069: a miss of about 0.000115. The same estimators had ranked every French candidate that evening.
- **Options considered:**
  1. Keep trusting cal, own and s1.
  2. Treat them as biased on decoys, and value French changes with the 7B's labelled calibration ("7B-cal").
- **Choice and why:** Option 2. The estimators use our own model's probabilities, so they share its blind spot and count accepted decoys as true matches [chat:ameya/19e315ba 2026-09-27 22:01], [22:05]. The 7B-cal breakdown of why B's France beat mixf7's [E] [chat:ameya/19e315ba 2026-09-27 22:09]: the France DP about +0.000051 (the biased estimator saw +0.000015); the round-3 model itself +0.000024 better than round 2; the look-alike drop neutral to mildly positive, not −0.000025; the corrected-label model v7sq6q4 −0.000044. The corrected-label runs were stopped at 22:27.
- **Evidence:** [LB 2026-09-27 #05](../../submissions/records/2026-09-27_sub05.md): −0.000046 against B, although cal predicted +69e-6; B's France DP +51e-6 carried it and the round-3 model itself was +24e-6 [RESEARCH_v6 §6.20](../../experiments/ameya/model-v1/RESEARCH_v6.md).
- **Outcome:** B+ = B plus 8 more French drops by the same confirmed rule; matching file `a5b0e90f…`; about 0.99088 [E] [chat:ameya/19e315ba 2026-09-27 22:08]. B+ was not uploaded; the SUB records cover what was.
- **Hindsight:** This is the main lesson the methodology states: an estimate built from the model's own probabilities needs an independent check on a country without labels.
- **Links:** [RESEARCH_v6 §6.20](../../experiments/ameya/model-v1/RESEARCH_v6.md) · [LB 2026-09-27 #05](../../submissions/records/2026-09-27_sub05.md) · D-EVL-14 · D-EVL-16

### D-EVL-16 · Keep the −6 threshold; reject looser US/India thresholds (mixbp5, mixbp4)
- **When (IST):** 2026-09-27 22:38–23:22 · **Phase:** P5 · **Area:** EVL / LLM
- **Decided by:** agent for Ameya
- **Status:** adopted (−6 kept)
- **Problem:** The 7B re-check drops a prediction when the 7B's score (a logit) falls below a cut-off. The −6 cut-off rested on a one-third sample with only 24 drops, too few to tell −6 from −5 or −4.
- **Options considered:**
  1. −6 (package B+).
  2. −5 (502 US/India drops, mixbp5).
  3. −4 (806 drops, mixbp4).
- **Choice and why:** The H100 scored the other two thirds of the holdout's confident predictions (1,169,835 pairs), giving 1,772,997 pairs on all 549,699 holdout S1. On the whole holdout, −6 gave +0.000037 (halves +0.000033 and +0.000041), −5 +0.000029 and −4 +0.000017 [M] [chat:ameya/19e315ba 2026-09-27 23:21]. So −6 stays. The agent also told Ameya to upload B+ by about 23:30 whatever happened, because a new package needs about 8 minutes to build and audit [chat:ameya/19e315ba 2026-09-27 22:40].
- **Evidence:** above. [LB 2026-09-27 #07](../../submissions/records/2026-09-27_sub07.md) agrees: "the whole-holdout check also puts the optimum at −6".
- **Outcome:** mixbp5 and mixbp4 were dropped. Bakshi's B7, which went the other way (looser, in France), tied with Composite B on the public LB: 0.990875 against 0.990879. No source states whether the private ranking used Composite B or B7; this is an open item.
- **Hindsight:** The labelled cut-off was right twice over: on three times the data and on the leaderboard (B7).
- **Links:** [LB 2026-09-27 #07](../../submissions/records/2026-09-27_sub07.md) · D-EVL-15

### D-EVL-17 · Lead with the public leaderboard score; label 0.9913 as local validation
- **When (IST):** 2026-09-29 about 02:46 · **Phase:** P5 · **Area:** EVL / PKG
- **Decided by:** Ameya (mid-task: "mention local and what was the public leader board figure rather than saying 0.9913, I think this was made on our device and the final we got was different right ?")
- **Status:** adopted
- **Problem:** The draft headline put 0.9913, the score on our labelled US/India holdout, next to the official public score 0.990879.
- **Options considered:**
  1. Keep both in the headline.
  2. Put the public leaderboard first, marked official, and label 0.9913 as "local validation, US/India only".
- **Choice and why:** Option 2. A note explains the gap: France has no labels, so it cannot be in the local score. The private leaderboard had not been published [chat:ameya/19e315ba 2026-09-29 02:48].
- **Evidence:** public LB 0.990879 (Composite B); local holdout 0.9913 (US 0.9911, India 0.9916; precision 99.9%, recall 97.5%) [M] [methodology](../../experiments/ameya/final-zip/doc/Documentation_template.md).
- **Outcome:** The executive summary and Table 4 follow this order; every other mention says "local holdout".
- **Hindsight:** The finale must keep the same order. The organisers publish only rankings for the private leaderboard, not scores: Grenuke is 2nd of the Top 10, and no private score exists to quote or estimate.
- **Links:** [finale README](../../finale/README.md) · [theory: evaluation methodology](../theory/05-evaluation-methodology.md)
