# Numbers: the fact sheet

Every number team Grenuke may quote at the Grand Finale, with scope, evidence level and source. A ★ marks the value to quote in the talk. Where sources disagree the row says so and points to `CF-nn` in [`conflicts.md`](conflicts.md).

- **Levels:** M measured (on labels or by the leaderboard, with a tag or record), E estimated (label-free, derived or inferred), R reported (stated in a chat or document, not re-checked), U uncertain (sources conflict).
- **Evaluations, always named:** the local holdout is 549,699 labelled US/India S1 and has no France. The public LB is the leaderboard during the challenge. The private LB is published as rankings only, so **no private score exists**; Grenuke is 2nd of the Top 10 (organisers' e-mail, relayed by Ameya).
- **Read "Numbers not to quote, and why" (last section) before putting any figure on a slide.** The candidate-file recall, the set-selection gain and the cost of a wrong merge are settled there.
- **Units:** F0.5 is the macro F0.5 per Source-1 (S1) entity. "e-6" means ×10⁻⁶ of the score. One test S1 is 1/1,732,544 = 5.77e-7 of the test score [E].

**Terms used here** (the full list is in the [glossary](theory/glossary.md)):

- **S1, S2, S3:** the three sources. S1 lists the businesses we match from; S2 and S3 hold the records to match.
- **Stages 0–3, p1, pc:** four XGBoost classifiers in a chain. Stage 0 is a cheap filter; stage 1 gives p1, the first match probability; stage 2 adds cross-encoder and context features and is calibrated; stage 3 re-scores contested records. pc is the final calibrated probability.
- **Band:** the pairs with 0.02 ≤ p1 ≤ 0.99. Only these are read by the cross-encoders.
- **Cross-encoder (CE):** a transformer that reads both records together and gives one score (e5, bge, Qwen).
- **Out of fold (OOF):** a pair is scored by a model that did not train on its S1 group.
- **The cut (c2):** the stage-1 filter that makes the candidate file. **s3** means after stage 3; **dpc** means with the combined decision layer.
- **Set selection:** for each S1, choose the list of records with the highest expected F0.5 (the "DP" or expected-F0.5 decision).
- **Composite B, g1w, mixmdp, B7:** Composite B is the submission (US/India from g1w, France from mixmdp, minus the 7B drops). B7 is the last upload.
- **`cal`:** our label-free estimator for the value of a French change.
- **Model names:** v2, v3, v5all, v6all, v7n, v7nst, v7sq, v7sq3, g0 and g1w are successive versions of the pipeline; section 3.1 lists them in order. mixc is an earlier 27 Sep package (US/India from v7sq3, France from v7sq) used for the funnel counts; its candidate file has 6,410,310 pairs against Composite B's 6,410,308.

---

## 1. Data facts

| fact | value | scope | level | source |
|---|---|---|---|---|
| Records, train | S1 2,206,821; S2 5,034,616; S3 5,285,603; total 12,527,040 | train | M | [FINAL_PLAN §1 #1][FP], [handover 09-25 14:25][h0925-1425] |
| Records, test | S1 1,732,544; S2 4,887,273; S3 5,082,316; total 11,702,133 | test | M | [FINAL_PLAN §1 #1][FP], [handover 09-25 14:25][h0925-1425] |
| ★ Records, all | 24,229,173, about 24.2M. AGENTS.md and Plan A say "23.7M"; that is not the sum (CF-41) | train + test | M | sum of the two rows above |
| Train S1 by country | US 1,323,633 (60%); India 883,188 (40%) | train | M | [chat:ameya/19e315ba 2026-09-25 11:49] |
| ★ Test S1 by country | India 809,986 (46.75%); US 663,106 (38.27%); France 259,452 (14.975%, the 0.14975 in every France formula) | test | M | [handover 09-27 01:11][h0927-0111], [handover 09-25 14:25][h0925-1425] |
| France in the test files | 1,694,445 records: S1 259,452; S2 703,378; S3 731,615 | test | M | [chat:ameya/19e315ba 2026-09-26 01:14] |
| True pairs | 7,638,365 (S2 3,693,619; S3 3,944,746) | train truth | M | [handover 09-25 13:00][h0925-1300] |
| ★ Matches per S1 | mean 3.46 (S2 1.67, S3 1.79), max 11. Share with 0: 5.6%; 1: 5.4%; 2: 17%; 3: 24%; 4: 22%; 5: 14.6%; 6: 7.5%; 7 or more: 4% | train truth | M | [FINAL_PLAN §1 #4][FP] |
| Singletons | 5.58% of S1 (India 5.588%, US 5.583%); holdout 30,677 of 549,699 | train; holdout | M | [chat:ameya/19e315ba 2026-09-25 11:49], [chat:ameya/a2a1b62a 2026-09-26 14:10] |
| One owner per record | 0 violations in 7,638,365 true pairs; 0 cross-country pairs. Caps in train truth: at most 5 S2 and 6 S3 per S1 (11 in all) | train truth | M | [FINAL_PLAN §1 #2-#3][FP], [handover 09-26 05:54][h0926-0554] |
| Orphans | 26.0% of S2/S3 records match no S1 (S2 26.6%; S3 25.3% India, 25.4% US). 22.0% of orphans share an exact core name with some S1 | train | M | [FINAL_PLAN §1 #5][FP], [handover 09-25 14:14][h0925-1414] |
| ★ Test has more look-alikes | 5.75 vs 4.68 S2/S3 records per S1 (+23%): India 5.82, US 5.76, France 5.53. The number of true matches per S1 is not higher (inferred from label-free predictions per S1, not measured) | test vs train | M (counts); E (inference) | [FINAL_PLAN §1 #13][FP], [RESEARCH_v5 §1][R5] |
| Distractors per S1 | about 1.2 in train, 2.4 in test (unclaimed records near the best S1: US 2.37, India 2.46, France 2.16) | generator catalogue | E | [ANALYSIS_v4 §3.1][A4] |
| Closeness profile | records close to an S1 on name and street: India 31.7% in test vs 31.8% in train, nothing close 43% vs 44%; France 30.6% and 40.1%. Removing owners would give about 26% and 53%, so the extra test records are of the same kinds as train's | train; test | M (crude proxy) | [FINAL_PLAN §1 #14-#15][FP] |
| Pool-size shift | unique-name S1 share US train 53.6% vs test 61.3% (mean name group 21.6 vs 11.5); the US test pool is about half of train's, which moves count-based features | train vs test | M | [RESEARCH_v5 §1][R5], [RESEARCH_v6 §1][R6] |
| Test composition | about 3.5 true copies and 2.3 look-alikes per S1 (train: 1.2 look-alikes); about 40% of test S2/S3 records are orphans | test | E | [chat:ameya/19e315ba 2026-09-25 15:20] |
| ★ Name collisions | 46.2% of US S1 and 53.6% of India S1 share an exact core name with another S1 (the document says "between 46% and 54%"). Other keys give other shares (CF-39) | train | M | [handover 09-25 14:14][h0925-1414], [FINAL_PLAN §1 #6][FP] |
| Address collisions | S1 sharing an exact normalised address: US 5.62% (largest group 14), India 4.84% (13); France 11.1% (largest group 101). Name and address both shared: 6 S1 | train; test France | M | [FINAL_PLAN §1 #6][FP], [ANALYSIS_v4 §1][A4] |
| True pairs are noisy | weak name 15.9% (India 26.1%, US 9.0%); weak address 4.7%; both weak 0.09%; weak address with more than 3 tokens 0.27% | 200k train true pairs | M | [FINAL_PLAN §1 #7][FP] |
| Empty addresses | record address empty in 4.4% of true pairs (3 tokens or fewer: 5.2%); the generator drops an address from 4.41% of copies (US 4.74%, India 3.92%); an empty-address record is a true copy 97.7% of the time (orphans: 0.29% empty) | train | M | [handover 09-25 14:14][h0925-1414], [RESEARCH_v5 §4][R5] |
| Empty address in the files | S2/S3 empty address: train S2 India 2.87%, US 3.68%; S3 India 3.07%, US 3.50%; test France 3.0%, US 2.89%, India 2.37% | per file | M | [chat:ameya/19e315ba 2026-09-25 11:49], [chat:ameya/19e315ba 2026-09-27 02:10] |
| House numbers in true pairs | first number equal 83.3% (US 88%, India 77%); number sets equal 73.1%; any overlap 94.6% | train true pairs with a number on both sides | M | [FINAL_PLAN §1 #8][FP] |
| ★ Look-alike signature | orphans close to an S1 vs true pairs: first house number equal 12.4% vs 84.8%; at least one extra name word 76.5% vs 23.3% | train, weak proxy | M | [handover 09-25 14:14][h0925-1414] |
| Look-alike nudge | the look-alike's house number is the S1's plus d, d in {1, 2, 3, 4, 5, 7, 9, 11, 13, 21} (about 10% each); 99.5% of US nudges go up | train orphans | M | [ANALYSIS_v4 §3.1][A4] |
| Postcodes | at most 0.5% of addresses carry one: India 0.02%, US 0.33%, France 0.4–0.5% | all | M | [FINAL_PLAN §1 #10][FP] |
| Indic scripts | Indic-script names in 23.4–23.5% of matched India S2 and 13.2% of S3 records; in 18.3% of India true pairs (7.3% overall) | train | M | [chat:ameya/19e315ba 2026-09-25 12:04], [FINAL_PLAN §1 #11][FP] |
| French copies | about 23% change their legal form (22.6% in confident French rows); 32% of French addresses name a department or region (synthetic data: 0%) | test France | E (legal form); M (addresses) | [issue #63], [PR #61] |
| French generic names | each French decoy the 7B rejected shares its name with a median of 43 other French S1 (747 of 859 rejected S1 have generic names) | test France | M | [issue #64], [chat:ameya/19e315ba 2026-09-27 19:22] |
| ★ Holdout | 549,699 S1 (24.9% of train S1): US 329,717, India 219,982; 1,901,267 true pairs. An empty prediction scores 0.0558 (India 0.05545, US 0.05605) | local holdout | M | [handover 09-25 13:00][h0925-1300], [handover 09-25 14:25][h0925-1425] |
| Dev sample | about 110k S1 (110,442 in the blocking dev pool); dev holdout 27,651 S1 | train | M | [chat:ameya/19e315ba 2026-09-25 15:47], [decision blocking-v3][d-blk3] |
| No order leak | ID and row order do not predict ownership: correlation over true pairs 0.0002 / 0.0014; test IDs spread evenly (each decile about 15.1% France, 46.8% India, 38.1% US) | train; test | M | [RESEARCH_v5 §1][R5], [chat:ameya/19e315ba 2026-09-27 02:48] |

---

## 2. Blocking and candidates

Blocking means the cheap search that proposes candidate pairs so that no one scores all pairs. "Retrieval" below is the blocking output before any classifier cut. "The cut" is the stage-1 filter that makes the candidate file.

| fact | value | scope | level | source |
|---|---|---|---|---|
| Design | per country; token view: each S1's top 40 records and each record's top 8 S1, a pair kept if it is in the S1's top 15 or the record's top 4; names-only view (character 4-grams) for addresses of 3 tokens or fewer and one-token names of 8 letters or more; repairs for domain names, OCR digits and ordinals | blocking v3 | M | [Documentation §3][DOC], [decision blocking-v3][d-blk3] |
| ★ Retrieval volume | 58,437,794 pairs on test (33.73 per test S1, "about 34"); 66,429,057 on train | blocking v3, Bakshi's rebuild matched the team's | M | [handover 09-27 20:06][h0927-2006], [METHODOLOGY_bakshi §2][MB] |
| ★ Retrieval recall | pair recall v0 0.9752 → v1 0.9857 → v2 0.9899 → v3 0.99135 | local holdout | M | [ROADMAP 2.2][ROADMAP], [decision blocking-v3][d-blk3] |
| Retrieval recall by country | v0 US 0.9860, India 0.9590; v1 US 0.9872, India 0.9836; v2 US 0.9916, India 0.9875 | local holdout | M | [chat:ameya/19e315ba 2026-09-25 16:42], [chat:ameya/19e315ba 2026-09-25 18:31], [ANALYSIS_v2 §4][A2] |
| ★ Retrieval misses | v2 19,163 → v3 16,455 of 1,901,267 true holdout pairs (0.87%); 54% are empty-address records with a changed name (66.8% have an empty record address in any case, CF-42) | local holdout | M | [decision blocking-v3][d-blk3], [RESEARCH_v6 §6.20][R6], [chat:ameya/19e315ba 2026-09-27 13:33] |
| Oracle F0.5 after retrieval | v0 0.9914; v1 0.9956; v2 0.9970; v3 0.99743. This is the best score any later stage could reach | local holdout | M | [decision gate-g1][d-g1], [chat:agent-ad467765 2026-09-27 14:41] |
| Retrieved per S1, holdout | v0 29.0 (p99 107); v1 29.5; v2 30.3; v3 30.11 | local holdout | M | [decision gate-g1][d-g1], [chat:agent-ad467765 2026-09-27 14:41] |
| Repairs (v3) | dev-pool forward recall 0.97240 → 0.97939: domain/handle records 0.868 → 0.937; OCR-digit names 0.906 → 0.952; ordinal addresses 0.9717 → 0.9898. 1,211,326 repaired name tokens in train, 890,435 in test | dev pool, 110,442 S1 | M | [decision blocking-v3][d-blk3], [chat:ameya/19e315ba 2026-09-26 11:46] |
| Indic dictionary | 693 entries learned on train folds 5–19 only; 752,869 Indic names transliterated in 3.8 s (train), 867,245 in test records | train; test | M | [handover 09-25 19:58][h0925-1958], [chat:ameya/19e315ba 2026-09-25 17:41] |
| ★ Funnel, pairs per test S1 | retrieval 33.73 → stage 0 4.77 → stage-2 input 4.65 → the cut 3.698 → candidate file 3.700 → final matches 3.378 | test, final pipeline (mixc) | M | [chat:agent-ad467765 2026-09-27 14:41] |
| Funnel, pairs per holdout S1 | 30.11 → 4.63 → 4.56 → 3.588 (final matches 3.373) | local holdout | M | [chat:agent-ad467765 2026-09-27 14:41] |
| Funnel, holdout pair recall | retrieval 0.99135 → stage 0 0.99079 → stage-2 input 0.99078 → **the cut 0.98354** | local holdout | M | [chat:agent-ad467765 2026-09-27 14:41] |
| Funnel, holdout oracle F0.5 | 0.99743 → 0.99725 → 0.99724 → 0.99499 | local holdout | M | [chat:agent-ad467765 2026-09-27 14:41] |
| ★ Candidate-file recall | **0.98354** (98.35%, say 98.4%): 31,304 of 1,901,267 true holdout pairs are outside the file. Retrieval alone is 99.1% (0.99135); the cut costs about 0.78 points. The decision record's 0.98198 is the same cut measured on v5all (blocking v2) and is superseded. Why 0.98354 is the figure: see the first entry under "Numbers not to quote" (CF-13) | local holdout, US/India, final pipeline; France has no labels | M | [chat:agent-ad467765 2026-09-27 14:41], [chat:agent-abb9ffcd 2026-09-27 04:05], [decision candidate-set-cut][d-cut] |
| True pairs lost between retrieval and the file | 14,849 (31,304 outside the file minus 16,455 never retrieved) | local holdout | M (derived) | [chat:agent-abb9ffcd 2026-09-27 04:05], [decision blocking-v3][d-blk3] |
| ★ Candidate file | 6,410,308 pairs = 3.70 per test S1; US 3.640, India 3.617, France 4.111 per S1 (mixc, within 2 pairs of the file); 105,028,761 bytes; 75,361 S1 have no candidate | test, Composite B | M | [Documentation §3][DOC], [chat:ameya/19e315ba 2026-09-29 02:48], [chat:agent-ad467765 2026-09-27 14:41] |
| The cut | keep a pair if stage 0 keeps it, p1 ≥ 0.02, and it is among its record's two best S1 by p1 (an intersection; the document's "plus" is loose, CF-14) | candidate rule | M | [decision candidate-set-cut][d-cut] |
| What the cut cost at v5all | pair recall in the set 0.98927 → 0.98198; oracle F0.5 0.99676 → 0.99452; holdout F0.5 tie: −0.000003 [−0.000015, +0.000011]; candidates per test S1 4.68 → 3.70 (−21%); file 8.11M pairs and 127 MB → 6.41M and 105 MB | local holdout, v5all; test | M | [decision candidate-set-cut][d-cut] |
| Tighter cuts, on the final rule | top 1 per record −106e-6 [−129, −83] (3.589 per S1); p1 ≥ 0.05 −41e-6 [−52, −30] (3.608); p1 ≥ 0.1 −105e-6; p1 ≥ 0.2 −279e-6. At v5all the first two were −0.00006 and −0.00002 (CF-32) | local holdout, v7sq3 rule | M | [chat:agent-ad467765 2026-09-27 14:41], [decision candidate-set-cut][d-cut] |
| A smaller file that was not built | gate stage 3 on stage-2 pc ≥ 2e-4: 3.595 per S1 (−2.8%), no holdout prediction lost, no mixc match outside; needs a rebuild and was judged not worth it | test mixc | M | [chat:agent-ad467765 2026-09-27 14:41] |
| Acronym join | adds 3,853 pairs outside the cut, 3,807 of them final matches (France only); earlier count 3,790 pairs over 3,725 S1 | test | M | [chat:agent-ad467765 2026-09-27 14:41], [PR #50] |
| Stage 0 | keeps 15.4% of pairs at 99.95% of true pairs (v3; 17.6–17.9% at v1 and v2), so it removes about 85%; funnel: 33.73 → 4.77 per test S1 is −86% (the document says "about 80%", CF-22) | train out-of-fold; test | M | [decision model-v3][d-v3], [handover 09-25 19:58][h0925-1958], [chat:agent-ad467765 2026-09-27 14:41] |
| Earlier file sizes | blocking output 33.99 per S1 and 781 MB; stage-2 input 4.75 per S1 and 129 MB (recall 0.98992 vs 0.98926) | test; holdout, blocking v2 era | M | [ANALYSIS_v3 §6][A3] |
| Blocking run time | 938 s (test) and 952 s (train) on the integration laptop; Bakshi's box 11 and 15 min; v0 train 1,117 s, test 1,039 s | full data | M | [chat:agent-ad467765 2026-09-27 14:41], [METHODOLOGY_bakshi §2][MB], [chat:ameya/19e315ba 2026-09-25 16:39] |
| Exact keys | exact name plus number or street: 100% in the candidates for France; holdout 100% / 99.93% | blocking v3 | M | [RESEARCH_v6 §2.6][R6] |
| Crowded lists | S1 lists full at the token cap of 15: holdout 23.1% India / 24.9% US; test US 31.3%, India 28.1%, France 24.2%. Cost of cap 15 → 10: −0.00009 | blocking v2; holdout | M | [chat:ameya/a2a1b62a 2026-09-26 14:11], [chat:ameya/19e315ba 2026-09-26 15:32] |

---

## 3. Model metrics

### 3.1 Local holdout, version by version

Macro F0.5 on the local holdout (549,699 US/India S1, no France). "c2" means after the candidate cut; "s3" means after stage 3 and the decision. US and India are the two country scores of the same run.

| fact | value | scope | level | source |
|---|---|---|---|---|
| Baseline v0 | 0.9683 (US 0.9765, India 0.9561); precision 0.9898, recall 0.9347; threshold 0.675 | local holdout | M | [handover 09-25 17:06][h0925-1706] |
| Model v1 | 0.98006 (US 0.9842, India 0.9738); precision 0.99698, recall 0.94958 | local holdout | M | [handover 09-25 19:58][h0925-1958] |
| Model v2 | 0.98436 (US 0.9847, India 0.9838); precision 0.99702, recall 0.96024; public LB 0.97608 | local holdout | M | [ANALYSIS_v2][A2], [chat:ameya/19e315ba 2026-09-25 19:53] |
| v2 with legal-form features | 0.98708 | local holdout | M | [decision legal-form][d-legal] |
| Model v3 | 0.98882; precision 0.99833, recall 0.96893; public LB 0.97961 | local holdout | M | [decision model-v3][d-v3] |
| v3 with the e5-small cross-encoder, v4, v5, v5all | v3ce 0.99021; v4 0.99015; v5 0.99013; v5all 0.990156 (US 0.98997, India 0.99043; precision 0.99884, recall 0.97124) | local holdout | M | [ANALYSIS_v3 §9][A3], [ANALYSIS_v4 §6-7][A4], [LB 2026-09-26 #01][lb0926-1] |
| v6nx (signed house numbers) | 0.99034 | local holdout | M | [RESEARCH_v5 §8.3][R5] |
| v6all | 0.990788 (US 0.99065, India 0.99100); precision 0.9987, recall 0.9738. With stage 3: 0.990842 (US 0.990700, India 0.991056) | local holdout | M | [decision model-v6all][d-v6all], [LB 2026-09-26 #02][lb0926-2] |
| v7ce3 (three cross-encoder logits) | c2 0.991099; s3 0.991138; precision 0.9991, recall 0.9735 | local holdout | M | [decision model-v7ce3][d-v7ce3] |
| v7n and v7nst | v7n s3 0.991211 (US 0.991018, India 0.991500); v7nst s3 0.991194 (US 0.991005, India 0.991472). v7nst has the lower holdout and the higher public LB (0.990179 vs 0.989721): the holdout cannot see France | local holdout | M | [LB 2026-09-26 #03][lb0926-3], [LB 2026-09-26 #04][lb0926-4] |
| v7s, v7sq | v7s s3 0.991229; v7sq s3 0.991246, with the combined decision layer 0.991280 | local holdout | M | [decision stacked-rules][d-stack] |
| v7sq3 | s3 0.991250; with the combined decision layer 0.991307 (US 0.991119, India 0.991590) | local holdout | M | [chat:ameya/19e315ba 2026-09-27 14:57] |
| g0 (v7sq rebuilt on Bakshi's box) | 0.991261 (US 0.991064, India 0.991558), against 0.991246 for the original | local holdout | M | [METHODOLOGY_bakshi §2][MB] |
| ★ g1w (the model behind Composite B's US and India) | 0.991323 (US 0.991114, India 0.991635); this is the `decide.py` stage-3 decision, and the final stacked layer was not re-measured on it (CF-17) | local holdout | M | [METHODOLOGY_bakshi §4][MB], [PACKAGE_README][PKG] |
| As stated in the methodology | 0.9913 (US 0.9911, India 0.9916); precision 99.9%, recall 97.5% | local holdout | M | [Documentation Table 4][DOC] |
| Variants not used | v7ensall2 (bag of seven) 0.991256; v7qbag 0.991249; v7sqq7 0.991296; v7sq6r3 (round-3 France model, US/India rows) 0.991336 | local holdout | M | [chat:ameya/a2a1b62a 2026-09-27 18:34] |
| India, before and after | 0.9561 (baseline) → 0.9910 (v6all) → 0.9916 (g1w) | local holdout | M | [ROADMAP 2.4][ROADMAP], [METHODOLOGY_bakshi §4][MB] |
| Holdout to public LB gap | v2 −0.0083; v3 −0.0092; v5all −0.0024. Re-weighting the holdout to the test's name-group mix (v4): US 0.98995 → 0.99083, India 0.99044 → 0.99055 | local holdout vs public LB | M | [chat:ameya/a2a1b62a 2026-09-26 14:38], [RESEARCH_v5 §1][R5] |

### 3.2 Gains that passed a gate

Paired bootstrap on the local holdout, difference in F0.5 with a 95% interval, unless the scope says dev (27,651 S1) or LB. The sources hold all of these as decision records.

| fact | value | scope | level | source |
|---|---|---|---|---|
| Stage 2 over stage 1 (G4) | dev +0.00692 [+0.00622, +0.00772] (0.97745 → 0.98438); full holdout, model v1 over stage 1 with a threshold +0.001995 [0.00189, 0.00210] | dev; local holdout | M | [decision gate-g4][d-g4], [handover 09-25 19:58][h0925-1958] |
| v2 over v1 | +0.00431 [0.00418, 0.00445] (India +0.0100, US +0.0005); bundles blocking v1, look-alike word odds and cluster support | local holdout | M | [chat:ameya/19e315ba 2026-09-25 19:50] |
| Legal-form features | +0.00271 [0.00260, 0.00283]; log-loss 0.04978 → 0.03993 (−20%) | local holdout | M | [decision legal-form][d-legal] |
| v3 over v2 | +0.00445 [0.00431, 0.00459] | local holdout | M | [decision model-v3][d-v3] |
| e5-small cross-encoder (G10) | +0.00140 [0.00131, 0.00148], below the +0.003 bar set for heavy parts; singletons 0.99126 → 0.99742 | local holdout | M | [decision model-v4][d-v4], [ANALYSIS_v3 §5][A3] |
| France fixes in v4 | −0.00006 [−0.00012, −0.00001] against v3ce (kept for France) | local holdout | M | [decision model-v4][d-v4] |
| Signed house-number features | +0.00021 [+0.00016, +0.00025] (0.99013 → 0.99034) | local holdout | M | [RESEARCH_v5 §8.3][R5] |
| v6all over v5all-c2 | +0.00063 [0.00057, 0.00070]; US +0.00068, India +0.00056 | local holdout | M | [decision model-v6all][d-v6all] |
| Stage 3 | v5all-c2 +0.000051 [0.000023, 0.000079]; v6all +0.000055 [0.000025, 0.000085]. 72 s and 1.71 GB | local holdout | M | [RESEARCH_v5 §8.4][R5], [decision rules-v3][d-rules3] |
| v7ce3 (e5-large, e5-base) | c2 +0.000311 [0.000258, 0.000362]; s3 +0.000296 [0.000252, 0.000342] | local holdout | M | [decision model-v7ce3][d-v7ce3] |
| v7n over v7ce3 | c2 +0.000072 [0.000040, 0.000103]; s3 +0.000073 [0.000041, 0.000102] | local holdout | M | [decision model-v7n][d-v7n] |
| v7nst over v7ce3-s3 | c2 +0.000059 [0.000021, 0.000094]; s3 +0.000055 [0.000022, 0.000089] | local holdout | M | [LB 2026-09-26 #04][lb0926-4] |
| v7sq3 over v7sq | +27.3e-6 [+2.2, +52.6] | local holdout | M | [chat:ameya/19e315ba 2026-09-27 12:58] |
| g1w over v7sq3 | India +66.1e-6 [+19.4, +112.9], P(better) 0.998; US +26.2e-6, P 0.906 (not significant; the LB later gave +14e-6) | local holdout | M | [handover 09-27 20:14][h0927-2014], [LB 2026-09-27 #06][lb0927-6] |
| The 7B in the cross-encoder mix | against g0: once +15e-6; **twice +62e-6**; three times +61e-6; alone +25e-6; mean of g0, g1 and g1w stage-2 scores +52e-6 (point estimates) | local holdout | M | [METHODOLOGY_bakshi §4][MB] |
| Tried and not kept | name-uniqueness features +0.00054 [+0.00001, +0.00107] (below the bar); stage-2 seed bagging −0.00004; bag of four over v7sq3 +4.6e-6 [−10.6, +21.1], P 0.714; India count prior +16.1e-6 [+2.2, +29.9] but hurts the US on every model | dev; local holdout | M | [decision name-uniqueness][d-nameuniq], [handover 09-26 20:49][h0926-2049], [chat:ameya/19e315ba 2026-09-27 15:03], [chat:agent-ac6dce8e 2026-09-27 14:30] |

### 3.3 Cross-encoder band AUCs

The uncertain band holds the pairs with 0.02 ≤ p1 ≤ 0.99. Only the cross-encoders read it. AUC is measured on labelled holdout pairs of the band.

| fact | value | scope | level | source |
|---|---|---|---|---|
| The band | train 1,568,554 pairs (27.2% positive); test 1,490,930 pairs; labelled holdout band 389,668 rows | stage 1 v6all | M | [RESEARCH_v6 §5.1][R6], [chat:ameya/19e315ba 2026-09-27 02:51] |
| Reference | stage-1 p1 alone 0.9297 | holdout band | M | [METHODOLOGY_bakshi §3][MB] |
| Final mix, holdout (out-of-fold) | e5-large 1 epoch 0.9391 (0.9350); e5-large 2 epochs 0.9441 (0.9403); e5-large French self-trained 0.9439 (0.9403); bge-reranker-v2-m3 0.9417 (0.9382); Qwen2.5-1.5B LoRA self-trained 0.9381 (0.9332) | holdout band | M | [METHODOLOGY_bakshi §3][MB] |
| ★ Qwen2.5-7B | LoRA, French self-trained: 0.9436 holdout, 0.9396 out-of-fold; it ties a self-trained e5-large (0.9439). The document says 0.944 for the 7B and 0.939 for e5-large (CF-35) | holdout band | M | [METHODOLOGY_bakshi §3][MB], [Documentation Table 3][DOC] |
| Small and rejected models | e5-small 0.9240; e5-base 0.9287; Qwen3-4B-Base LoRA 0.9411 (0.9370, not in the mix); bge self-trained (bges) 0.9424; e5-large self-trained, second run (e5ls2) 0.9440 | holdout band | M | [RESEARCH_v6 §5.1][R6], [chat:ameya/19e315ba 2026-09-27 06:22] |
| Mixes | z-mean of two e5-large 0.9429; cem2 0.9428; cem 0.9433; cms 0.9433; e5-large plus bge 0.9417 | holdout band | M | [issue #45], [TRACK_B_FINDINGS] |
| France-block models | e5fr 0.918; e5bfr 0.917; bgefr 0.926 (gate: 0.90 or more); synthetic-data cesy3b 0.9095 | holdout band | M | [PACKAGE_README][PKG], [chat:ameya/19e315ba 2026-09-27 17:57] |
| Zero-shot 7B | Qwen2.5-7B-Instruct AUC 0.537 against 0.898 for the stage-2 probability; quick LoRA 0.720 | uncertain holdout pairs | M | [handover 09-27 12:28][h0927-1228] |
| Logit blend | a cross-fitted blend of six logits plus p1 and pc: band AUC 0.9575 against 0.9276, but −0.001 as the decision score | holdout | M | [METHODOLOGY_bakshi §7][MB] |
| Disagreement | e5-large and bge disagree in sign on 12.0% of French band pairs against 3.1% US and 2.7% India; correlation 0.91 against 0.98 | test band, label-free | M | [RESEARCH_v6 §6.6][R6] |
| Self-trained agreement | self-trained cross-encoders correlate 0.94–0.98 among themselves on French band pairs and 0.60–0.69 with untrained ones | test France band | M | [chat:agent-a4ea3fde 2026-09-27 10:43] |
| Never read by a cross-encoder | 94.5% of final predictions have p1 above 0.99 (holdout sample 95.6%, France 90.5%) | final models | M | [METHODOLOGY_bakshi §5][MB] |
| Cross-encoder training | e5-small 1,757 pairs/s train and 11,654 pairs/s inference on the laptop GPU; e5-large about 925 pairs/s on an H100; input cut to 96 tokens (median 37 tokens for the 7B's pairs) | laptop; H100 | M | [chat:ameya/19e315ba 2026-09-25 21:31], [METHODOLOGY_bakshi §3][MB] |

### 3.4 What the final model predicts on test

| fact | value | scope | level | source |
|---|---|---|---|---|
| ★ Composite B output | 5,851,832 pairs for 1,732,544 S1 = 3.3776 per S1; 99,802 S1 with no match (5.76%; the truth is 5.58%) | test | M | [METHODOLOGY_bakshi §6][MB] |
| By country | France 870,307 pairs (3.3544 per S1; 244,469 of 259,452 S1 non-empty); India 2,734,227 (3.3756; 763,319 of 809,986); US 2,247,298 (3.3890; 624,954 of 663,106) | test | M | [chat:ameya/19e315ba 2026-09-29 02:48] |
| Audit | 0 records with two owners; 0 cross-country pairs; 0 matches outside the candidates; validator PASS | test | M | [PACKAGE_README][PKG] |
| Truth for comparison | matches per S1 US 3.457, India 3.461; 5+ matches 26.0% of S1 (France predictions: 23.7%) | train truth; v7nst | M | [chat:ameya/19e315ba 2026-09-27 02:52], [chat:ameya/19e315ba 2026-09-27 01:09] |
| US test over-prediction | US test gets +0.020 more predictions per S1 than the holdout (+0.0224 at v3, +0.0203 at v4, +0.0199 at v6nx; India +0.001–0.002; +17.8 per 1000 S1 in a 15% test sample at v6all). Explained as a pool-size effect: the extra predictions are mostly correct assignments that are no longer ties | test vs holdout | M (counts); E (cause) | [RESEARCH_v6 §1][R6], [chat:ameya/a2a1b62a 2026-09-26 14:12] |
| Earlier outputs | Sub 3 (v2) 5,842,331 pairs (3.37 per S1, 97,115 empty); v7nst 5,856,096 pairs (3.3801, 100,137 empty; France 871,242, India 2,735,918, US 2,248,936) | test | M | [chat:ameya/19e315ba 2026-09-25 19:57], [handover 09-27 01:11][h0927-0111] |

### 3.5 Where the remaining loss is

| fact | value | scope | level | source |
|---|---|---|---|---|
| v2 loss | 0.01564: misses 81% (0.01269), false positives 0.00297. Empty-address records are 4.4% of true pairs but 52.5% of the misses | local holdout, v2 | M | [handover 09-25 21:47][h0925-2147] |
| v5all loss | 0.00984; misses 89% of it; false negatives with an empty record address 69% (37,774 of 54,573); recall with a record address 0.993 / 0.988 (US / India) against 0.54 / 0.57 without | local holdout | M | [RESEARCH_v5 §2][R5], [chat:agent-ace27900 2026-09-26 05:28] |
| Loss ledger, v6all-c2 | 1,901,267 true pairs; 49,733 missed, 2,448 false. Missed: below threshold 28,353 (83% empty address); never retrieved 16,455; cut away (p1 0.002–0.02) 3,009; stage 0 1,063; lost to another S1 834. False: in the band 2,115; with p1 above 0.99: 333 | local holdout | M | [chat:ameya/a2a1b62a 2026-09-26 15:22], [RESEARCH_v6 §4][R6] |
| Value of one pair | +1.6e-7 per missed pair recovered (+0.001 is about 6,200 pairs); +4.7e-7 per false pair removed (+0.001 is about 2,100) | local holdout | M | [chat:ameya/a2a1b62a 2026-09-26 22:53] |
| ★ Recall of the final model | 97.47% of 1,901,267 true holdout pairs predicted; 48,029 missed: 16,455 never retrieved, 31,574 retrieved but not predicted (1,272 reachable by an alias) | local holdout, v7sq | M | [chat:ameya/19e315ba 2026-09-27 10:02] |
| Loss anatomy, g0 | 4,804 S1-equivalents of lost F0.5: partly missed 69% (43,863 S1), missed entirely 20% (964 S1), false positive only 8% (1,655 S1). 48,509 true pairs missed: 16,455 never candidates, 237 to another S1, the rest rejected, 15,152 of them at pc near 0 | local holdout | M | [METHODOLOGY_bakshi §7][MB] |
| Inside and outside the cut, v7nst | loss 0.0088 per S1 (misses only 0.00777, false only 0.00093, both 0.00011); 31,304 true pairs outside the cut; 16,950 missed inside it (13,553 with an empty record address, 10,993 with the S1's own name); 2,149 false predictions | local holdout | M | [chat:agent-abb9ffcd 2026-09-27 04:05] |
| Limits that look like data limits | about 22k empty-address pairs with shared names are 95–100% missed; 62.5% of pairs lost between S1 with identical names (oracle ownership ceiling 0.99351, +0.00335 over v5all) | local holdout | M | [handover 09-25 21:47][h0925-2147], [chat:agent-a9638892 2026-09-26 05:30] |
| Recall rules we could not use | empty-address exact-name rule 24% true (17% against all S1; 287 pairs 40.1% in a sample); best sibling slice 59% (193 pairs); 7B additions 71.4% at best (42 adds, 30 true); the break-even is about 75% | local holdout | M | [METHODOLOGY_bakshi §7][MB], [chat:ameya/19e315ba 2026-09-27 19:35] |

### 3.6 Model shape and the transfer tests

| fact | value | scope | level | source |
|---|---|---|---|---|
| Feature counts | 37 (v0) → 79 (v2) → 87 (v3) | dev kits | M | [handover 09-25 19:58][h0925-1958], [RESEARCH_v5][R5] |
| Rows | stage 2: 10.9–11.0M rows (v1, v2) and 10,065,671 (g1w); French pseudo-labelled rows 1.34M | train | M | [chat:ameya/19e315ba 2026-09-25 18:23], [METHODOLOGY_bakshi §4][MB] |
| Calibration | v2 with legal forms: ECE 0.00046, band ECE 0.00434, Brier 0.010935; reliable within about 0.01–0.03 | local holdout | M | [chat:ameya/19e315ba 2026-09-25 21:21] |
| Leave one country out (US → India) | India holdout, stage 1: both countries 0.98346; US only, words known 0.96106; India words unseen 0.88235; unseen with the label-free proxy 0.95984; without look-alike odds 0.94180. Ameya's own run gave an in-country 0.98660 against 0.96555 US-only (gap 0.02105); Sachi's gap was about 0.028 (CF-48) | dev kit; India holdout, 11,111 S1 | M | [ANALYSIS_v3 §3-4][A3], [chat:ameya/19e315ba 2026-09-26 17:52] |
| Self-training in the leave-one-out test | words unseen: 0.88235 → 0.8512 → 0.83075 → 0.823; words known: 0.96106 → 0.9637 → 0.96479 → 0.96498 (Sachi's ladder) | India holdout | M | [ANALYSIS_v3 §3][A3], [RESEARCH_v6 §6.19][R6] |
| India stand-in for France | self-training +0.0012 / +0.0012 / +0.0002 (mean +0.0009, three seeds); rule positives only −0.0040 | India holdout | M | [RESEARCH_v6 §4][R6] |
| French legal bits | stage-1 p1 on 30,518 French pairs: 0.456 as is → 0.027 with the bits zeroed → 0.232 with English bits; the reason the bitmasks were dropped | test France | M | [ANALYSIS_v3 §2][A3] |
| Learned look-alike word odds | "holdings" −9.8, "group" −9.7, "industries/enterprises/exports" about −8.6; dual-use proxy words (groupe, france, développement) −4.7 to −4.8 | train OOF; France proxy | M | [handover 09-25 14:25][h0925-1425], [RESEARCH_v6 §2.9][R6] |

---

## 4. Decision layer

The decision layer turns calibrated pair probabilities into the final list for each S1. It has the per-S1 expected-F0.5 set selection (a small dynamic programme), the rules, and the 7B re-check.

### 4.1 Set selection and break-even

| fact | value | scope | level | source |
|---|---|---|---|---|
| Rule | for each S1, a dynamic programme over the calibrated candidate probabilities picks the set with the highest expected F0.5; settings tuned on the holdout: logit shift +0.2, a further −0.3 for records that 4 or more S1 compete for (p1 ≥ 0.02), 0.01 expected true matches outside the candidates; each record then goes to its best S1. Flat threshold where used: 0.70 (v6all, v7s), 0.675 (v7nst, g1w) | design | M | [Documentation §4][DOC], [decision stacked-rules][d-stack] |
| ★ Combined decision layer over the best flat threshold | **+48.1e-6 [+7.1, +91.2]**, P(better) 0.987; half A +7.7, half B +108.7; US +70.8, India +13.9. This is the set selection plus the crowd shift, `acr` and `cap` together (0.991229 → 0.991277). The document attributes it to the set selection alone (CF-16) | local holdout, v7s | M | [decision stacked-rules][d-stack] |
| Its parts | set selection alone (shift +0.2, phantom 0.01) +33.2e-6 [−7.5, +75.0], P 0.945; with `acr` and `cap` +35.9e-6 [−4.8, +77.6]; with the crowd shift −0.3 +48.1e-6 | local holdout, v7s | M | [decision stacked-rules][d-stack] |
| Out of sample | repeated 2-fold CV on v7nst, 42 splits: set selection with phantom +23.7e-6, positive in 86%; re-tuning the flat threshold the same way −18.8e-6 | local holdout | M | [decision stacked-rules][d-stack], [RESEARCH_v6 §6.16][R6] |
| Set selection against a threshold, by model (G6) | dev v0 −0.00024 [−0.00091, +0.00049]; stage 1 −0.00029; stage 2: v1 +0.00027, v2 +0.00018 [+0.00009, +0.00026], v2 with legal forms +0.00014, v3 +0.00011 [+0.00005, +0.00017], v4 +0.00006; v6all +0.00004 [−0.00001, +0.00008] (not significant, threshold kept); v7ce3 +0.00005 [+0.00001, +0.00009]; v7mst +0.00003 [−0.00002, +0.00007]. The verdict depends on the model (CF-50) | local holdout; dev for v0 | M | [decision gate-g6][d-g6], [decision model-v3][d-v3], [decision model-v6all][d-v6all], [decision model-v7ce3][d-v7ce3], [RESEARCH_v6 §6.15][R6] |
| Public LB share of the stack | +0.000085 (v7nst 0.990179 → v7nst-dpc 0.990264) | public LB | M | [LB 2026-09-27 #01][lb0927-1] |
| ★ Break-even for adding a pair | the pair pays if it is true with probability above 0.500 (only candidate), 0.727 (2nd), 0.759 (3rd), 0.771 (4th), tending to 0.8; "about 75%" in the document, 72–77% in the records. A drop pays if more than about 25% of the dropped pairs are false | F0.5 arithmetic, independence | E | [FINAL_PLAN §2][FP], [decision rules-v3][d-rules3] |
| ★ Cost of one error in one S1 | for an S1 with 4 true copies and a perfect list: a wrong addition costs 0.167, a missed copy 0.0625 (ratio 2.7; the records round to 0.17–0.18 and 0.06–0.07). In F0.5 = 1.25·TP / (1.25·TP + 0.25·FN + FP) one false positive weighs as much as four false negatives at fixed TP | analytic | E | [decision rules-v3][d-rules3], [chat:ameya/19e315ba 2026-09-27 19:38] |
| Break-even for an empty S1 | about 0.5–0.6 (0.47 for a single exact candidate); two early chat figures of 8% and 6% were superseded | analytic | E | [chat:ameya/a2a1b62a 2026-09-26 23:19] |
| Empty S1 rescue | 31,574 empty S1 in v7n-s3 (5.74%), of which 30,606 are true singletons; best rescue rule +0.000021 [−0.000008, +0.000049]; adding the top free candidate is negative at every threshold (−505e-6 at pc 0.2 … −4e-6 at 0.5) | local holdout | M | [chat:ameya/a2a1b62a 2026-09-26 23:25], [METHODOLOGY_bakshi §7][MB] |

### 4.2 Rules

| fact | value | scope | level | source |
|---|---|---|---|---|
| `acr` (initials) | add an owned, unheld pair with pc ≥ 0.1 whose record name is the S1's initials and whose address is not empty: 37 of 37 true on the holdout. Acronym truth at the S1's address: US 99.72% (723), India 66.1% (758) | local holdout | M | [decision stacked-rules][d-stack], [RESEARCH_v6 §5.2][R6] |
| `cap` | an S1 with more than 5 S2, 6 S3 or 11 predicted records keeps its highest-pc predictions; train truth never exceeds 5 S2 or 6 S3 across 2.2M S1 | local holdout | M | [chat:agent-abb9ffcd 2026-09-27 04:05] |
| Rules that did not survive | `nsa` as a hard band (pairs with pc up to 0.75 when 4 or more S1 compete are 65–68% true) replaced by the crowd shift; `rank0` subsumed; soft caps −15.8 to +0.2e-6; per-source zero count −48.1e-6; singleton protection −33.7e-6 | v7nst / v7s | M | [decision stacked-rules][d-stack], [chat:agent-abb9ffcd 2026-09-27 04:05] |
| France copy rule | add an unpredicted exact-address pair with equal names where the S1 is the record's best candidate: +332 French pairs on v7s (176 abbreviation-equal); the population is 99.992% true in the US (n = 332,869) and 99.998% in India (n = 47,206) | v7s, France; US/India holdout | M | [decision stacked-rules][d-stack], [chat:agent-aeb3d218 2026-09-27 04:19] |
| France city rule | drop a pair whose S1 and record name different communes: −89 French pairs on v7s; French true copies change commune in 3 of 546,465 pairs (5.5e-6), so a drop is about 95% false and the break-even is 35%. The same rate is 4.56% in US and 0.90% in India copy populations, which is why it is used for unlabelled countries only | France, label-free; US/India | M / E | [decision stacked-rules][d-stack], [chat:agent-aeb3d218 2026-09-27 04:19] |
| Look-alike descriptor swap (op B) | 5,364 holdout pairs of this kind, 0.6% true; v4 France: 17,088 dropped by `post_ops` (65.9 per 1000 S1, median pc 0.989), 16,971 by the probe count; rules drop 17,914–21,569 depending on the model; after v7nst only 305 needed dropping | US/India holdout; test France | M | [ANALYSIS_v4 §3][A4], [decision france-generator-ops][d-frops], [decision model-v7n][d-v7n] |
| Other generator operations (US / India truth) | A (word appended, after the legal form) 99.7 / 98.3%; APP 98.9 / 99.6%; ACR 99.9 / 99.8%; B 3.1 / 0.6%; NUM 97.6 / 78.2%; CODE 42.6 / 44.0%. With the robust address of rules v3: B 0.0 / 1.2%, A 87.4 / 99.1% (India / US) | US/India holdout | M | [decision france-rules-v2][d-frrules2], [decision rules-v3][d-rules3] |
| France rule counts | v5all rules v2: −19,503, +A 7,227, +APP 3,877, +ACR 853; v6all: −20,168 (77.7 per 1000 S1), +A 3,622, +APP 2,955, +ACR 670; rules v3: −21,365, +A 4,062, +APP 3,167, +ACR 770 | test France | M | [decision france-rules-v2][d-frrules2], [decision model-v6all][d-v6all], [decision rules-v3][d-rules3] |
| French acronym predictions | 18,707 pairs (72 per 1000 French S1). True acronym pairs per 1000 S1 on the holdout: US 2.6, India 9.2; the French name shape alone predicts 6.4 (label-free); the handover calls the French rate 11× the US/India rate. Size-bias false share 0.00 [0.00, 0.01]; holdout acronym candidates 1,440 of 1,444 true | test France; holdout | M / E | [chat:ameya/19e315ba 2026-09-27 11:16], [chat:ameya/19e315ba 2026-09-27 11:34] |
| Look-alike word-swap drop | 454 pairs in mixmdp (592 in v7sq-dpc); value uncertain: −20 to −31e-6 by the pc-based estimators, +58e-6 by the size-bias method, about +18e-6 as the leaderboard remainder (CF-27) | test France | E | [RESEARCH_v6 §6.20][R6], [chat:ameya/19e315ba 2026-09-27 17:03] |
| France set selection | in mixmdp: 357 additions and 224 drops (shift 0.2); worth +51e-6 by the 7B's calibration; shift 0.5 would add 1,008 pairs at a mean truth of 0.756, valued −2.5e-6 | test France | E | [LB 2026-09-27 #03][lb0927-3], [chat:ameya/19e315ba 2026-09-27 22:53] |
| Stage 3 | contested records only (2 or more S1 at pc ≥ 0.01); not bit-reproducible: 232k test pc values differ across machines (max 0.09), about 500 decisions flip | test | M | [decision rules-v3][d-rules3], [chat:agent-ad467765 2026-09-27 14:41] |

### 4.3 The 7B re-check of confident predictions

The re-check reads the final predictions with p1 above 0.99, which no cross-encoder had scored. It drops a pair when the Qwen2.5-7B logit is below −6.

| fact | value | scope | level | source |
|---|---|---|---|---|
| ★ Pairs dropped in Composite B | drop list 1,169 pairs; 1,150 present and dropped: **840 French, 310 US/India** (India 204, US 106) | test | M | [LB 2026-09-27 #04][lb0927-4], [METHODOLOGY_bakshi §6][MB] |
| What was scored | 870,019 French final pairs; 4,744,395 US/India final predictions with p1 above 0.99 (of about 4.98M US/India predictions); a 34% holdout sample of 186,897 S1 (631,001 predictions, precision 0.99896) | test; holdout | M | [METHODOLOGY_bakshi §5][MB], [chat:ameya/19e315ba 2026-09-27 18:48] |
| Rejects on test | 859 French pairs flagged (0.10% of French predictions; 840 exist in mixmdp's France, 832 in mixf7/mixf2, 838 in mixnc); 310 of 4.74M US/India (0.0065%); holdout US/India rate 0.004%, so 15× (test) to 25× (holdout) | test; holdout | M | [METHODOLOGY_bakshi §5][MB], [chat:ameya/19e315ba 2026-09-27 18:43] |
| Truth by 7B logit (34% sample) | below −6: 8.3% of 24; −6 to −4: 86.3% of 51; −4 to −2: 94.9% of 138; −2 to 0: 99.6% of 6,616; 0 to 2: 99.8% of 16,893; 2 or more: 100.0% of 579,440 | holdout sample, predictions outside the band | M | [METHODOLOGY_bakshi §5][MB] |
| ★ Truth of the strong rejects | 8.3% (2 of 24) on the 34% sample, which the document quotes as "8%"; **20% (16 of 80)** on the whole holdout. Either way far below the 75% at which a drop stops paying (CF-19) | local holdout | M | [chat:ameya/19e315ba 2026-09-27 23:21], [Documentation §2.2][DOC] |
| ★ Gain of the drop at −6 | sample +33e-6 (halves +22 / +43); **whole holdout +37e-6** (halves +33 / +41; US +18, India +18). Looser cuts on the whole holdout: −7 +27e-6; −5 +29e-6; −4 +17e-6; −3 +3e-6 | local holdout | M | [chat:ameya/19e315ba 2026-09-27 23:21], [METHODOLOGY_bakshi §5][MB] |
| Stability | positive in 99.7% of 3,000 random 25% subsets (mean +32.8e-6, sd 16.7e-6) | holdout sample | M | [METHODOLOGY_bakshi §5][MB] |
| The decoy pattern | same name, same house number, different street: where our model predicted it 99.7% true (n = 380, 7B median +7.9); where our model rejected it 0.5% true (n = 218, 7B median −9.9, 202 of 218 below −6) | US/India holdout sample | M | [issue #64], [PR #62] |
| What the French rejects look like | about 78% follow that pattern (80.1% of all 859); 747 of 859 S1 have generic names; 827 S1 affected, 68 would be emptied; a bge detector with no self-training labels flags 708 of 859 (82%) | test France | M | [chat:ameya/19e315ba 2026-09-27 18:43], [chat:ameya/19e315ba 2026-09-27 20:20] |
| No leak through self-training | the French reject rate is the same in every third of the S1: 0.1118% (the third adapter 0 never trained on), 0.1082%, 0.1070%, median logit about 9.6 | test France | M | [METHODOLOGY_bakshi §5][MB] |
| Adapter agreement | logit correlation 0.403 between adapter 0 and adapters 1 and 2 on re-scored holdout pairs; every drop comes from adapter 0 | holdout | M | [chat:ameya/19e315ba 2026-09-27 21:39] |
| Beyond −6 | B7 (France drops extended toward −2 where Qwen3-4B agrees: +251 / −1,699 French pairs vs B) scored 0.990875 against B's 0.990879, a tie | public LB | M | [LB 2026-09-27 #07][lb0927-7] |
| Where B's +0.000180 came from | India g1w ≈ +31e-6; US g1w ≈ +10e-6; US/India drops ≈ +28e-6; French drops the remainder ≈ +111e-6 (Bakshi, used in the document). The submission record says about +0.00014 for the drops and +0.00004 for the US/India model (CF-30) | public LB split by holdout deltas | E | [METHODOLOGY_bakshi §6][MB], [LB 2026-09-27 #04][lb0927-4] |

### 4.4 Measured and dropped in the decision layer

| fact | value | scope | level | source |
|---|---|---|---|---|
| Copy-count tie-breaking | owner accuracy 0.31 vs 0.27; F0.5 −0.00057 | local holdout | M | [PR #68] |
| Tie renormalisation | −0.000007 to −0.000137 (the document calls it per-record renormalisation, CF-33). The per-record renormalisation of RESEARCH_v6 was +0.000015 on v6all and 0 after stage 3 | local holdout | M | [PR #68], [RESEARCH_v6 §2.3][R6] |
| Drop mining with a decision tree | half A +33e-6, held-out half B −15e-6 (overfit) | local holdout | M | [METHODOLOGY_bakshi §7][MB] |
| Disagreement drops, alias bridge, structural recall, consensus editing, change-footprint screen | closed by measurement; 5 validated candidates agree with v7sq-dpc on 99.92–99.97% of predictions; the alias bridge reaches 21 pairs in about 30; structural recall rule precision 0.8698 unconditional but 0.4010 on the target population | holdout; test | M / E | [issue #45], [commit 6a8df7b], [commit c7f95b3] |

---

## 5. France estimates

France has no labels, so every French F0.5 is an estimate from the public score (E). The estimate rests on two unverified assumptions: US/India score on test like the holdout re-weighted to the test mix, and the public subset has the whole test's country mix (CF-09). The France-empty probe that would have measured France directly was built five times and never uploaded.

| fact | value | scope | level | source |
|---|---|---|---|---|
| Formula | LB = 0.38274·F_US + 0.46751·F_India + 0.14975·F_France (a fitted intercept of 0.000388 appears in some analyses). The US/India part: 0.8423 (v4–v5all), 0.842897 (v6all), 0.843226 (v7n), 0.843210 (v7nst), 0.843258 (v7sq) | public LB | E | [RESEARCH_v5 §1][R5], [handover 09-26 05:20][h0926-0520], [LB 2026-09-26 #02][lb0926-2], [decision stacked-rules][d-stack] |
| ★ The early gap | local holdout 0.98436 / 0.98882 against public LB 0.97608 / 0.97961 for v2 / v3; working backwards France was about 0.93 (v2 0.927–0.944, v3 0.925–0.931) | public LB algebra | E | [RESEARCH_v5 §1][R5], [Documentation §2.1][DOC] |
| France implied by the public LB | v5all 0.971–0.976 (0.9715 / 0.9741 / 0.9763 under three US/India assumptions); v6all ≈ 0.973; v7n 0.978 (0.9783); v7nst ≈ 0.981; v7nst-dpc ≈ 0.982; v7sq-dpc ≈ 0.983; mixmdp ≈ 0.984. No source gives Composite B an estimate except Bakshi's "about 0.9886", which is not quotable | public LB algebra | E | [status ameya][status ameya], [LB 2026-09-26 #01][lb0926-1], [LB 2026-09-26 #03][lb0926-3], [LB 2026-09-26 #04][lb0926-4] |
| Sensitivity | v5all: France ≈ 0.971 if US/India score like the holdout, ≈ 0.987 if they sit 0.002 below | public LB algebra | E | [chat:ameya/a2a1b62a 2026-09-26 22:31] |
| What the points were | 26 Sep #01: US/India gave about 0.8423 of a possible 0.85025, France about 0.1455 of 0.14975; France's shortfall was roughly the whole gap to first place (0.00275). 0.99 needed France at 0.9801 (at v7n's US/India part); third place on the evening of 26 Sep (0.99033) needed 0.9823 | public LB algebra | E | [LB 2026-09-26 #01][lb0926-1], [LB 2026-09-26 #03][lb0926-3] |
| The leaders | on the morning of 27 Sep a leader at 0.991483 implied France about 0.990 if its US/India matched ours, against our 0.981–0.982 | public LB algebra | E | [status ameya][status ameya] |
| Forecast that hit | v7n was predicted at 0.9894 (France 0.976) to 0.9900 (0.980) before upload and scored 0.989721 | public LB | M / E | [LB 2026-09-26 #03][lb0926-3] |
| ★ Self-training, round 1 | v7n → v7nst: +0.000458 on the public LB with the US/India part unchanged to 0.00002, so France about +0.0031; it changed 31 per 1000 French predictions (+14.0 / −17.4) | public LB | M | [LB 2026-09-26 #04][lb0926-4] |
| French part of each LB step | 780 → 470 → 240 → 130 (e-6): each step about half the last | public LB decompositions | E | [chat:ameya/19e315ba 2026-09-27 17:00] |
| ★ Round 2 with the French decision layers | mixmdp over v7sq-dpc: +0.000154 (US/India +20e-6, France +134e-6); `cal` had predicted +146e-6 for France | public LB | M | [LB 2026-09-27 #03][lb0927-3] |
| Model change in v7sq | v7nst-dpc → v7sq-dpc +0.000281 (about +0.00023 France, French F about +0.0016): French self-trained cross-encoders overruling US-trained ones. It also changed the cross-encoder mix, so it is not pure self-training | public LB | M / E | [LB 2026-09-27 #02][lb0927-2] |
| Round 3 | mixf7 (B with round-3 France) −46e-6 against B, while `cal` had predicted +69e-6; the round-3 model itself was about +24e-6 better on 7B-scored pairs, and B's French set selection was worth +51e-6 | public LB | M / E | [LB 2026-09-27 #05][lb0927-5], [RESEARCH_v6 §6.20][R6] |
| `cal`, the label-free estimator | backtest over 5–6 past LB pairs: scale 0.96, mean absolute error 42e-6, correlation 0.98; its first-stage and second-stage variants were worse (second-stage wrong sign on all pairs, error 697e-6). A "within ±0.00005" claim did not hold on round 3 (miss about 115e-6) | public LB | E | [RESEARCH_v6 §6.18][R6], [chat:ameya/19e315ba 2026-09-27 15:18] |
| Public LB noise | between near-identical candidates about ±0.00004–0.00005; for a 25% public split the standard deviation of the score is 0.000164 (simulated on the local holdout) | public LB | E | [issue #71], [RESEARCH_v6 §6.15][R6] |
| Over-confidence in France (label-free) | Σ pc per French S1 3.5456 against the generator's 3.46 (holdout 3.4320 vs truth 3.4323); 186 predicted pairs per 1000 S1 at pc 0.7–0.99 against 52 in the US; records with Σ pc above 1.05: France 52.4 per 1000 S1 (v6all) → 0.7 (v7sq); 97% of v7sq-dpc French predictions at stage-3 pc 0.99 or more | test France | M (counts) | [handover 09-26 15:57][h0926-1557], [RESEARCH_v6 §2][R6], [chat:ameya/a2a1b62a 2026-09-27 18:34] |
| French rule-population AUC (a label-free proxy) | stage-2 probability on 128,856 rule-typed pairs: v6all 0.855 → v7ce3 0.865 → v7n 0.872 (v7m 0.878); after self-training 0.984–0.986, saturated and biased. Raw cross-encoder logits on 53,290 band pairs: e5-base 0.687, bge 0.774, e5-large 0.792–0.803, e5-large plus bge 0.829. These two series must not be mixed | test France | E | [decision model-v7n][d-v7n], [RESEARCH_v6 §6.13][R6] |
| Self-training labels | rule: positive if a kept pair has pc ≥ 0.9, negative if rejected at pc ≤ 0.05, rules override. Round 1: 385,274 band pairs (62,189 positive, 238,334 negative, 84,751 unlabelled); stage-2 rows 1,429,666 (851,116 / 493,352 / 85,198). Round 2 from v7nst: 859,422 / 502,206 / 68,038; guarded 861,340 / 516,463 / 51,863. Round 3: 864,109 / 540,977 / 24,580. Round 4 changed 3,553 (0.25%). From v7sq-dpc: 385,274 band pairs (74,325 / 273,160 / 37,789) | test France | M | [chat:ameya/19e315ba 2026-09-26 21:19], [chat:ameya/19e315ba 2026-09-27 13:08], [chat:ameya/19e315ba 2026-09-27 18:19], [METHODOLOGY_bakshi §3][MB] |
| French predictions | per S1: v3 3.539 → v4 3.370 → v5all with rules 3.320 → mixc 3.357; empty share 5.81% (India 5.76%, US 5.75%, holdout truth 5.54–5.60%) | test | M (counts) | [ANALYSIS_v3 §9][A3], [chat:ameya/19e315ba 2026-09-27 13:40] |
| Garbled-word copies | copies with heavy garbles (the French "EHPAD" typed "ehpvd"): US/India 77,488 pairs, 96.7% true and predicted; France 37,437, of which 75.3% predicted | v7nst | M | [chat:ameya/19e315ba 2026-09-27 01:23] |
| Value of a French change | about +0.000016 of public LB per net-correct changed prediction per 1000 French S1 (v7nst → v7sq changed 16.6 per 1000 for +0.000281). Gap to 0.991: +0.000821 from 0.990179 (1,422.42 S1-units, about 22,759 recoveries at +0.0625); +0.000455 from 0.990545 (788.31 units, about 12,613 recoveries) | whole test | E | [commit 9c7cb51], [chat:ameya/19e315ba 2026-09-27 09:59] |
| Synthetic French data | Sachi's generator: 99,702 pairs (40.1% true) from 40,000 French S1; synth3: 107,766 pairs (39.7% true). Real French copies differ: legal-form edits 22.6% real vs 2.5–3.2% synthetic; list append 1.2% vs 11.6–13.8%; typo 1.2% vs 10.3–12.3%; acronym 1.6% vs 9.1–11.2%. Not used in the final; synthetic bge still agreed with 82% of the 7B drops | test S1 text, no labels | M / E | [PR #61], [issue #63] |

---

## 6. Leaderboard history

Every upload with a recorded score, in time order. All scores are **public LB** (a subset of test); the rank is the rank at the time of upload as reported. Holdout figures are the local holdout of the same package. The protocol allowed 5 uploads a day (15 in all); 13 scored uploads are on record (2 + 4 + 7). Whether Sub 1 (baseline) and Sub 2 (model v1) were uploaded on 25 Sep is not recorded (CF-08).

| fact | value | scope | level | source |
|---|---|---|---|---|
| 25 Sep, model v2 ("Sub 3") | 0.97608; holdout 0.98436; gap −0.0083; rank not recorded | public LB | M | [CHANGELOG][CL], [status ameya][status ameya] |
| 25 Sep 23:28–23:54, model v3 | 0.97961; holdout 0.98882; gap −0.0092; +0.0035 over v2 | public LB | M | [CHANGELOG][CL], [chat:ameya/19e315ba 2026-09-25 23:53] |
| 26 Sep #01 (reported 14:38), v5all + France rules v2 + the cut | 0.98781, rank 15; holdout 0.990156; gap −0.0024; +0.0082 over v3 | public LB | M | [LB 2026-09-26 #01][lb0926-1] |
| 26 Sep #02 (evening), v6all + stage 3 + rules v3 + acronym join | 0.988609, rank 15 (17th by 22:25); holdout 0.990842; +0.000799 | public LB | M | [LB 2026-09-26 #02][lb0926-2] |
| 26 Sep #03 (about 23:05), v7n | 0.989721, rank 8; holdout 0.991211; +0.001112 (France about 0.978) | public LB | M | [LB 2026-09-26 #03][lb0926-3] |
| 26 Sep #04 (about 23:35), v7nst | 0.990179, rank 7 (13th by 05:20 next morning); holdout 0.991194; +0.000458 | public LB | M | [LB 2026-09-26 #04][lb0926-4] |
| 27 Sep #01 (morning), v7nst-dpc | 0.990264; +0.000085 over v7nst (the stack) | public LB | M | [LB 2026-09-27 #01][lb0927-1] |
| 27 Sep #02 (about 10:05), v7sq-dpc | 0.990545, rank 7 (then 8); holdout 0.991246 (combo 0.991280); +0.000281 over v7nst-dpc | public LB | M | [LB 2026-09-27 #02][lb0927-2] |
| 27 Sep #03 (about 16:40), mixmdp | 0.990699, rank 12; US/India v7sq3 combo 0.991307; +0.000154 (US/India +20e-6, France +134e-6) | public LB | M | [LB 2026-09-27 #03][lb0927-3] |
| ★ 27 Sep #04 (about 20:55), **Composite B** | **0.990879**, rank 16 at upload, the team's best and the package in the ZIP; holdout g1w 0.991323; +0.000180 over mixmdp (predicted +0.000149) | public LB | M | [LB 2026-09-27 #04][lb0927-4] |
| 27 Sep #05 (about 21:55), mixf7 | 0.990833: B with round-3 France, −0.000046 against B | public LB | M | [LB 2026-09-27 #05][lb0927-5] |
| 27 Sep #06 (about 21:55), mixf2 | 0.990819: mixf7 with the US from v7sq3, −0.000014 against mixf7, so g1w's US is worth +14e-6 | public LB | M | [LB 2026-09-27 #06][lb0927-6] |
| 27 Sep #07 (about 23:40), B7, the last upload | 0.990875: B with the French 7B drop extended, −0.000004 against B, a tie | public LB | M | [LB 2026-09-27 #07][lb0927-7] |
| Whole climb | 0.97608 (first recorded) → 0.990879 (best) = +0.014799 | public LB | M | rows above |
| Largest steps | v6all → v7n +0.001112 (two e5-large cross-encoders and e5-small in the mix); v5all → v6all +0.000799 (blocking repairs, stage 3, rules v3, acronym join together); v7nst +0.000458 (French self-training); v7sq +0.000281; Composite B +0.000180; mixmdp +0.000154; the stack +0.000085 | public LB, differences between uploads | M | [CHANGELOG][CL] |
| Top of the board seen | 26 Sep 14:38 top three 0.990556 / 0.989141 / 0.988842 (ranks 4–10: 0.988584 … 0.988087); evening of 26 Sep 0.99074 / 0.99052 / 0.99033; 27 Sep 09:20 first place 0.991483 (we were 15th); about 14:30 0.991811; about 16:40 0.991829 | public LB | R | [LB 2026-09-26 #01][lb0926-1], [chat:ameya/a2a1b62a 2026-09-26 14:45], [chat:ameya/19e315ba 2026-09-27 09:12] |
| Late rank | 22:52 on 27 Sep: "we were 7th, now we are 20th" (public LB, other teams improved) | public LB | R | [chat:ameya/19e315ba 2026-09-27 22:52] |
| ★ Final standing | Top 10 of 32,000+ teams, **2nd** on the list. The organisers publish rankings only; **there is no private score to quote** | private LB | R | [chat:ameya/19e315ba 2026-10-03 22:45], [finale README][finale] |
| Packaged and validated, never uploaded | B+ (Composite B plus 8 more French drops; matching `a5b0e90f…`, expected about 0.99088), mixf4 `9267f34c…`, mixf3 `bec18446…`, mixf6 `1757bda3…`, mixfq, mixbp4, mixbp5, the France-empty and France-threshold probes, and many other candidates | packages | M | [status ameya][status ameya], [chat:ameya/19e315ba 2026-09-27 19:47] |

---

## 7. Compute, runtimes and costs

| fact | value | scope | level | source |
|---|---|---|---|---|
| Integration laptop | RTX 5070 Ti (12 GB), 24 cores, 31.1 GB RAM (commit limit 42.6 GB; about 20 GB usable for a job); Python 3.13 | Ameya's machine | R | [memory:ameya], [chat:ameya/19e315ba 2026-09-27 03:57] |
| Teammates' machines | Sachi: MacBook M3, 8 GB; Bakshi: Core i5-12450H, RTX 2050 (4 GB), 16 GB | at 25 Sep 15:38 | R | [chat:ameya/19e315ba 2026-09-25 15:38] |
| Rented GPUs | H100 80 GB boxes for the cross-encoders (interruptible boxes were lost on 26 Sep; a later on-demand box with 192 CPUs and about 1 TB RAM); two RTX 5090 (32 GB) for the synthetic-French jobs (called "4090" in places); Bakshi: a 2× RTX 4090 box (64 vCPU) for the rebuild and a 4× H100 SXM box for the 7B | 26–27 Sep | R | [chat:ameya/19e315ba 2026-09-26 22:43], [chat:ameya/19e315ba 2026-09-27 14:20], [METHODOLOGY_bakshi §8][MB] |
| Cost | only estimates exist: a new on-demand H100 session about $5–8; an A100 job about $3.5–4; an RTX 4090 about $0.30–0.50 per hour (a whole job about $2.5–6); a pasted final-day plan had $42 / $24 / $34 buckets (author unknown). **The total team spend is not recorded (CF-12)** | agent estimates | E / R | [chat:ameya/19e315ba 2026-09-26 22:30], [chat:ameya/a2a1b62a 2026-09-26 17:30] |
| Early pipeline runs, laptop | records 50 s (train) and 22 s (test); blocking v0 19 and 15 min, v1 13 and 11 min; features 12 + 15 min; stage 1 about 20 min; stage 2 20–26 min; the writer and validator on 52M candidates 3.6 min (peak 13.7 GB) and 55 s | integration laptop | M / R | [handover 09-25 14:25][h0925-1425], [handover 09-25 19:58][h0925-1958], [chat:ameya/19e315ba 2026-09-25 15:22] |
| v6all end to end | about 3 h (11:22 → 14:27): blocking 2 × 16 min, features 60, stage 1 16, cross-encoder 35, stage 2 24 | laptop, 26 Sep | M | [handover 09-26 14:28][h0926-1428], [chat:ameya/19e315ba 2026-09-26 14:27] |
| Bakshi's rebuild (phase A) | about 1 h 45 min on 64 vCPU: records 45 s, Indic dictionary 4.5 min, blocking 11 and 15 min, features 52 min, stage 0+1 8 + 4 min, e5-small 21 min; g0 59 min; g1w 39–40 min | Bakshi's box, 27 Sep | R | [METHODOLOGY_bakshi §2][MB], [issue #66] |
| Memory peaks | stage 2 16.5–19 GB; decide 9.8 GB; `acr_join` 6.0 GB; `post_ops` 3.3 GB; stage 3 2.8 GB (1.71 GB in the first test); full feature table about 19 GB; stages 1–3 peak 18–19 GB | laptop | M / R | [handover 09-27 07:06][h0927-0706], [PACKAGE_README][PKG] |
| Cross-encoder runs | e5-small about 45 GPU-min for three out-of-fold models on the laptop (21 min on an RTX 4090); e5-large about 61 min on a shared H100; e5l2 6,525 s; bge 5,538 s; e5ls 9,721 s; e5ls2 7,247 s; bges 4,837 s; Qwen2.5-1.5B (qst) 16,226 s; Sachi's Qwen2.5-1.5B about 93 min per group on an RTX 4090 | H100 / 4090 | R / M | [RESEARCH_v6 §5.1][R6], [chat:ameya/a2a1b62a 2026-09-27 13:29], [handover 09-26 18:00][h0926-1800] |
| ★ Qwen2.5-7B training | one out-of-fold group per GPU: **about 2 hours on 3 H100s (about 6 on one)**: 9,663 / 9,706 / 9,912 steps at about 3.6 steps/s (first box), then about 2.3 steps/s after the move; 4,462–5,135 s per group on the second box; scoring about 2.0M pairs per group at about 600 pairs/s; no step skipped for non-finite gradients | Bakshi, 27 Sep | R (log) | [METHODOLOGY_bakshi §3][MB], [PACKAGE_README][PKG] |
| ★ 7B on every test pair | 58.44M pairs / 600 per s ≈ 27 GPU-hours, before any training: why the 7B only reads confident predictions and the uncertain band | estimate | E | [Documentation §2.2][DOC], [issue #75] |
| 7B re-check runs | France 2 × 15 min and US/India 4 × 46 min on H100; 193,524 pairs in 364 s on one H100 (about 530 pairs/s); zero-shot 7B about 145–170 pairs/s | H100 | R / M | [PACKAGE_README][PKG], [chat:ameya/19e315ba 2026-09-27 22:27] |
| France block (package) | about 4.5 h: e5ls2 about 2.0 h, bges about 1.3 h, e5fr about 20 min on one H100; stage 2 about 33 min; the rest about 25 min on 24 cores | package | R | [PACKAGE_README][PKG] |
| Compose and rebuild | Composite B composition about 5 min; a different winner repackages in about 4 minutes; a clean end-to-end run of the v7sq chain was estimated at 6–7 h on laptop plus H100 | Bakshi | R | [PACKAGE_README][PKG], [chat:ameya/19e315ba 2026-09-27 03:12] |
| Data moved | first rented boxes: about 7.8 GB, later about 23.7 GB of traffic against a 30 GB cap; 13 GB uploaded as 69 chunks of 256 MB in 8 streams (22 min); a later box took about 3 MB/s, so slim band-only records (119 MB instead of 1.08 GB) were sent | rented boxes | R | [handover 09-26 18:17][h0926-1817], [chat:ameya/19e315ba 2026-09-26 22:56], [chat:ameya/19e315ba 2026-09-27 10:35] |
| XGBoost speed | 2M rows × 100 features, 200 rounds in 4.6 s on the laptop GPU | RTX 5070 Ti | M | [chat:ameya/19e315ba 2026-09-25 12:13] |
| Waiting | about 4.7 h of idle compute waiting for approval on 26 Sep (06:37–11:19) | process | M | [chat:ameya/19e315ba 2026-09-26 11:19] |

---

## 8. Package and reproducibility

| fact | value | scope | level | source |
|---|---|---|---|---|
| ★ The ZIP | `60b601522ca8ffa9b377a2437970757411bd69056ebd5eea21df5a4f147a9ffc`, 88,353,040 bytes, 146 files, built from `main` ed5bc7e, with `MANIFEST.sha256` (18,112 bytes). Earlier builds: `7f077875…` (149 manifest entries), `4ac35cc0…` (146 files); a first set of 103-file builds was void (a missing source file) | submitted package | M | [chat:ameya/19e315ba 2026-09-29 04:09], [chat:ameya/19e315ba 2026-09-29 03:37] |
| Submitted outputs | `output/matching_results.tsv` sha256 `df4bccd785b3fa785b7edcf0532288bcddc0010e2e31ce6f358064529ecb62e8` (97,854,781 bytes); `output/candidate_pairs.tsv` sha256 `58c824a3f61c184fe7da1a448a4ac94284f288feff9c351abfe16a3dfc0520e5` (105,028,761 bytes); the uploaded bytes, shipped verbatim | Composite B | M | [PACKAGE_README][PKG], [LB 2026-09-27 #04][lb0927-4] |
| Other upload files (matching sha256, first 8) | mixmdp `00ec3d9b`; mixf7 `046df7e0`; mixf2 `4c3b4527`; B7 `3d7b09d6`; v7sq-dpc `cdda9a2d`; v7nst-dpc `f3490125`; Sub 3 `fdfb022c` | uploads | M | [submission records][SUBREADME], [chat:ameya/19e315ba 2026-09-28 00:11] |
| Checks | validator PASS and strict audit PASS; 12 of 12 audits passed on the final candidates; a reviewer's 8-item check passed on `7f077875…`; the rebuild is byte-identical; a clean Python 3.13.2 environment installs on Windows; **115 unit tests pass** in the repo and in every ZIP build | package | M | [chat:ameya/19e315ba 2026-09-29 04:02], [chat:ameya/19e315ba 2026-09-27 08:22] |
| Hardware to rerun | CPU stages 24 or more cores and 32 GB RAM (peak 18–19 GB); the XGBoost stages use a CUDA device in the code (CF-37); cross-encoders on one 80 GB H100; the 7B on three 80 GB GPUs | reproduction | R | [PACKAGE_README][PKG] |
| ★ Reproducibility | a rerun lands within about ±0.0001 and is not byte-identical: GPU training differs across machines (the v7sq rebuild gave 0.991261 against 0.991246), and stage 3 moves about 500 decisions. The France block reproduced 871,147 French pairs with 0 differences; the cross-encoder band matched by (s1, r) at 100.0000% (train) and 99.9999% (test; 1 pair missing) | reproduction | M | [METHODOLOGY_bakshi §2][MB], [PACKAGE_README][PKG] |
| Pinned environment | 15 packages pinned: transformers 5.17.0, tokenizers 0.23.2, safetensors 0.8.0, huggingface_hub 1.7.2, peft 0.21.0, torch 2.11.0, accelerate 1.15.0, xgboost 3.2.0 | `requirements.txt` | M | [chat:ameya/19e315ba 2026-09-29 01:59], [chat:ameya/19e315ba 2026-09-29 03:54] |
| ★ Models and licences | XGBoost (Apache-2.0); multilingual-e5-small 118M, -base 278M, -large 560M (MIT); bge-reranker-v2-m3 568M (Apache-2.0); Qwen2.5-1.5B (Apache-2.0); **Qwen2.5-7B, 7.6B, revision `d149729398750b98c0af14eb82c78cfe92750796` (Apache-2.0)**; Qwen3-4B-Base (Apache-2.0, used in B7 only). Excluded: Qwen2.5-3B (other licence), jina-reranker-v2 (CC-BY-NC). All at most 8B | final pipeline | M | [PACKAGE_README][PKG], [METHODOLOGY_bakshi §3][MB] |
| 7B adapter | LoRA r 16, alpha 32, dropout 0.05, all seven projections; lr 1e-4, batch 64, one epoch; three adapters of 161,547,632 bytes (about 155 MB) | q7st | M | [METHODOLOGY_bakshi §3][MB], [chat:ameya/19e315ba 2026-09-27 21:11] |
| The document | 7 pages, A4, Times New Roman 11.5 pt, 3 figures; body 19,461 characters; a first full version had 3,576 words and 12 pages. Due 29 Sep 10:00 IST | submitted methodology | M | [chat:ameya/19e315ba 2026-09-29 04:09], [chat:ameya/19e315ba 2026-09-29 03:49] |
| File round trip | the v3 test file of 5,879,524 pairs was written and read back identical, and the file-based holdout score equals the report (0.98882) | v3 | M | [chat:ameya/a2a1b62a 2026-09-26 14:10] |
| Rules followed | only the provided data; hand-written lexicons only (legal forms, street types, US/India states, French departments, generator list words, OCR digit map, ordinals); the Indic dictionary is learned from training folds; seeds fixed; every artifact records its command and commit | compliance | M | [PACKAGE_README][PKG] |

---

## 9. Team and process

| fact | value | scope | level | source |
|---|---|---|---|---|
| Team | three members: Ameya Borkar (captain and coordinator), Aarush Bakshi, Sachi Dhoka | Grenuke | M | [Documentation][DOC] |
| Dates | challenge 25–27 Sep 2026; methodology and ZIP due 29 Sep 10:00 IST; deck due **Tue 6 Oct 14:00 IST** (the organisers' e-mail says "Monday"); finale **Wed 7 Oct 09:00–14:00 IST**, 10-minute talk and 5 minutes of questions | organisers | R | [finale README][finale], [chat:ameya/19e315ba 2026-10-03 22:45] |
| How finalists were ranked | private leaderboard first; then blocking strategy and novelty; then candidate efficiency (fewer pairs per record ranks higher) | organisers' e-mail | R | [finale README][finale] |
| Plan choice | final plan = Plan A as base plus Plan B's gates and grafts; rubric (weights 30/15/15/15/10/10/5) A 3.9 against B 3.1 (coordinator's scores only) | 25 Sep | R | [DECISION][DEC] |
| Day 1 | 9 issues (#5–#13) due 16:15–23:00 on 25 Sep; unit tests 24 (12:56) → 49 (16:25) → 96 (21:27) → 115 (ZIP) | repo | M | [chat:ameya/19e315ba 2026-09-25 15:44] |
| Repo on 3 Oct | 229 commits on `main`, 14 remote branches, pull requests up to #77 | repo | M | [chat:ameya/19e315ba 2026-10-03 22:59] |
| Uploads | protocol 5 per day and 15 in all; 13 scored uploads on record; 7 on 27 Sep (CF-05). The submission window was read as closing at 21:00 IST; uploads were accepted at about 21:55 and 23:40 (CF-04) | portal | M / U | [submissions README][SUBREADME], [ROADMAP][ROADMAP], [LB 2026-09-27 #07][lb0927-7] |
| Day-1 modules by Bakshi and Sachi | Bakshi: normalisation (484.2 s train, 516.1 s test, 8 workers, 16 GB laptop) and string features (56 plus 15 context features; 3,212,547 pairs in 214.4 s, down from 431 s; 5.89 GiB). Sachi: v0 model on the dev fold (0.9648: precision 0.988, recall 0.929, ECE 0.0004; 37 features). Built and tested; the final chain used the experiment chain's own features (CF-53) | dev data | M | [PR #20], [PR #21], [PR #16] |
| Dev kits | devkit-v0 179,797,164 bytes (37 features, 3,212,547 rows); devkit-v2 383,533,421 bytes (79 features, 3,262,031 rows) so teammates on 8–16 GB machines could work | releases | M | [chat:ameya/19e315ba 2026-09-25 17:19], [chat:ameya/19e315ba 2026-09-25 20:19] |
| Hard rules | only the provided data; models MIT or Apache-2.0 with at most 8B parameters; `country` treated as an open set (CF-26) | AGENTS.md | M | [AGENTS.md](../AGENTS.md) |

---

## Numbers not to quote, and why

| # | statement | why not | quote instead |
|---|---|---|---|
| 1 | "3.70 per S1 at 99.1% recall" | 99.1% (0.99135, 16,455 misses) is the pair recall of the retrieval, 33.73 pairs per S1, before the stage-0 and stage-1 filters. The 3.70-per-S1 file keeps less. The submitted methodology (Sections 1 and 3) and the first version of the finale README joined the two (CF-13) | ★ "Retrieval keeps 99.1% of the true holdout pairs at about 34 per S1. The learned cut shrinks that to 3.70 per S1 and keeps **98.35%** (0.98354)." Why this figure: see below the table |
| 2 | "The expected-F0.5 set selection beat the best global threshold by +0.000048 (0.000007 to 0.000091)" | the interval belongs to the combined layer on v7s: set selection + crowd shift −0.3 + `acr` + `cap`. The set selection alone was +33.2e-6 [−7.5, +75.0], not significant; the crowd shift is what moved the interval above zero (CF-16) | "The decision layer as a whole gained +0.000048 [0.000007, 0.000091] over the best flat threshold on v7s; out of sample the set selection gave +0.000024 and re-tuning the threshold lost 0.000019." |
| 3 | "A wrong merge costs twice as much as a missed copy" | "twice" is the β-weighting (precision counts twice as much as recall). In the count form one false positive weighs as much as four false negatives; for an S1 with 4 true copies a wrong addition costs 0.167 and a missed copy 0.0625, a ratio of 2.7. The record also says "about 3×" and "about four times" (CF-15) | "F0.5 weights precision twice as much as recall. In counts, one false merge costs as much as four missed copies; for a typical S1 it costs about 2.7 times one missed copy." |
| 4 | any private leaderboard score | none exists: the organisers publish rankings only | "We placed 2nd of the Top 10; the public score of our submission was 0.990879." Never estimate a private score |
| 5 | "The local score 0.9913 is the score of what we submitted" | 0.991323 is the stage-3 decision of g1w; the final stacked rules were gated on v7s and not re-measured on g1w (CF-17). France is not in it | "On the holdout, US and India, the model behind Composite B scores 0.9913; the stacked rules added about +0.00005 on the earlier model." |
| 6 | "we never trained on the holdout" | in the final fit the holdout rows train the stage-1 and stage-2 models that score test and the other groups, and the isotonic fit includes them; the holdout's own predictions are out of fold, and thresholds and shifts were tuned on it (CF-18) | "Holdout predictions are out of fold; the final test models also saw the holdout rows, so the holdout is a comparison set, not an untouched test." |
| 7 | "Only 8% of the 7B's strong rejects are real matches" | 8.3% is 2 of 24 on a 34% sample; on the whole holdout it is 16 of 80 (20%) (CF-19) | "20% on the whole holdout, 8% on the sample in the document; the drop pays whenever fewer than about 75% are true." |
| 8 | "The 7B rejects French predictions 25× more often" | 25× compares France on test with US/India on the holdout; against US/India on test it is 15× (0.10% vs 0.0065%) (CF-20) | "15 to 25 times" |
| 9 | "Stage 0 removes about 80% of pairs" | it removes about 85% (4.77 of 33.73 pairs per test S1 remain; 15.4% kept in the v3 bundle) (CF-22) | "about 85%, keeping 99.95% of true pairs" |
| 10 | "23.7M records" | the files hold 24,229,173 records (12,527,040 train, 11,702,133 test) (CF-41) | "24.2M records" |
| 11 | "France was 0.93" or any final French F0.5 | 0.93 was the estimate for v2 and v3 only; later values (0.971 → 0.984) and Bakshi's "about 0.9886" are estimates from public-score algebra with two unverified assumptions; France was never measured (CF-09) | "France cannot be validated locally; from the public score we estimate it rose from about 0.93 to about 0.98." |
| 12 | "self-training added +0.00046 and the second round +0.00015" | +0.000458 is clean (France only). +0.000154 is mixmdp over v7sq-dpc and bundles US/India +20e-6, the France set selection and the look-alike drop (CF-29) | "round 1: +0.00046 on the public score; round 2 with the French decision layers: +0.00015, of which France +0.00013" |
| 13 | "blocking repairs and stage 3 added +0.0008" | the v5all → v6all step also carried the signed-number features, rules v3, the acronym join and a new cross-encoder (CF-29) | "+0.0008 for that day-2 bundle" |
| 14 | "the 840 French drops were worth +0.00011" | an estimate (holdout deltas × country share, the French part taken as the remainder); the record says about +0.00014 (CF-30) | "worth roughly +0.0001 of Composite B's +0.00018 (estimated)" |
| 15 | "break-even is exactly 75%" | it is 0.727 for the 2nd candidate, 0.771 for the 4th, 0.8 in the limit; the records use 72% and 75% | "about 75%" |
| 16 | the `cal` estimator "is accurate to ±0.00005" | the backtest error was 42e-6 on average and it missed round 3 by about 115e-6 (CF-51) | "accurate to a few ten-thousandths on past uploads; it failed on decoys" |
| 17 | per-record renormalisation "up to −0.000137" | that range is the tie renormalisation of PR #68; per-record renormalisation was +0.000015 (CF-33) | "tie renormalisation −0.00001 to −0.00014" |
| 18 | "France 7B drops 859" as the number dropped | 859 are flagged; 840 were present in Composite B's France (CF-20) | "840 French and 310 US/India pairs dropped" |
| 19 | forecasts as results (mixf2 "about 0.99091", B+ "about 0.99088") | predictions that were not confirmed: mixf7 and mixf2 scored 0.990833 and 0.990819; B+ was never uploaded | quote only uploaded scores |
| 20 | public rank at upload as the final standing ("rank 16") | public ranks moved fast (7th at 27 Sep 10:05, 20th at 22:52) and the final ranking is private (CF-10) | "2nd of the Top 10" |
| 21 | cross-encoder AUCs from different bands (0.9244 / 0.9278 vs 0.9315; 0.9240 vs 0.9297) | earlier v3 band (0.05–0.95) and the final band (0.02–0.99) differ (CF-48) | the table in section 3.3 only |
| 22 | "gate G1 was met" | 0.9899 is just below 0.990 at v2; v3 reached 0.99135; the v1 bar of 99.5% was never met (CF-52d) | "retrieval recall 99.1% at v3" |

### Why 0.98354 is the candidate-file recall (entry 1)

- **Two figures exist.** 0.98198 is in the decision record [candidate-set-cut][d-cut] (26 Sep 05:32, v5all). 0.98354 is in a sub-agent's funnel report (27 Sep 14:41, final pipeline).
- **0.98198 measures an older object.** It is the same cut (p1 ≥ 0.02 and the record's top 2 S1), but on blocking v2 and the v5all stage 1, where the set before the cut had recall 0.98927. Blocking v3 then raised retrieval from 0.98992 to 0.99135. The record is a correct measurement of a superseded file.
- **0.98354 measures the submitted cut.** It is computed on blocking v3 and the v6all stage 1, the cut rebuilt equals `ameya-cands-v6all-c2` exactly, and Composite B's file adds only the acronym-join pairs (France, which has no labels). The file's holdout recall is therefore the cut's recall.
- **An independent count agrees.** The hunt agent (27 Sep 04:05) counted 31,304 true holdout pairs outside the cut: 1 − 31,304 / 1,901,267 = 0.983535. Of those, 16,455 were never retrieved, so the cut itself loses 14,849.
- **The loss of the cut is stable.** Stage-2 input to cut: 0.98926 → 0.98198 at v5all (−0.00728); 0.99078 → 0.98354 at v6all (−0.00724).
- **Weakness of the source.** The funnel tables were left in the agent's scratchpad (`BLOCKING_NOTE.md`, `tables.txt`) and are in no committed file; the repo has only the 0.98198 record. Cite the transcript, and re-run the cut on the v6all stage-1 holdout scores if a number must be shown live.
- **How to say it.** "98.35%" or "98.4%". `finale/README.md` hedges with "about 98.2–98.4%" and "about 98.3%"; 98.3% understates it by 0.05 points.

---

[FP]: ../plans/FINAL_PLAN.md
[DEC]: ../plans/DECISION.md
[ROADMAP]: ../docs/ROADMAP.md
[CL]: ../CHANGELOG.md
[SUBREADME]: ../submissions/README.md
[status ameya]: ../docs/status/ameya.md
[finale]: ../finale/README.md
[DOC]: ../experiments/ameya/final-zip/doc/Documentation_template.md
[MB]: ../experiments/bakshi/final-package/METHODOLOGY_bakshi.md
[PKG]: ../experiments/bakshi/final-package/PACKAGE_README.md
[TRACK_B_FINDINGS]: ../experiments/bakshi/final-package/TRACK_B_FINDINGS.md
[A2]: ../experiments/ameya/model-v1/ANALYSIS_v2.md
[A3]: ../experiments/ameya/model-v1/ANALYSIS_v3.md
[A4]: ../experiments/ameya/model-v1/ANALYSIS_v4.md
[R5]: ../experiments/ameya/model-v1/RESEARCH_v5.md
[R6]: ../experiments/ameya/model-v1/RESEARCH_v6.md
[h0925-1300]: ../docs/handover/2026-09-25_1300_ameya_repo-setup.md
[h0925-1414]: ../docs/handover/2026-09-25_1414_ameya_final-plan.md
[h0925-1425]: ../docs/handover/2026-09-25_1425_ameya_dev-skeleton.md
[h0925-1706]: ../docs/handover/2026-09-25_1706_ameya_block-v0-baseline.md
[h0925-1958]: ../docs/handover/2026-09-25_1958_ameya_model-v1.md
[h0925-2147]: ../docs/handover/2026-09-25_2147_ameya_analysis-v2-and-v3.md
[h0926-0520]: ../docs/handover/2026-09-26_0520_ameya_research-gap-candidates.md
[h0926-0554]: ../docs/handover/2026-09-26_0554_ameya_research-part2-plan.md
[h0926-1428]: ../docs/handover/2026-09-26_1428_ameya_model-v6all-final.md
[h0926-1557]: ../docs/handover/2026-09-26_1557_ameya_research-v6-gap-budget.md
[h0926-1800]: ../docs/handover/2026-09-26_1800_sachi_llm-cross-encoder.md
[h0926-1817]: ../docs/handover/2026-09-26_1817_ameya_ce-large-box.md
[h0926-2049]: ../docs/handover/2026-09-26_2049_ameya_squeeze-v7n.md
[h0927-0111]: ../docs/handover/2026-09-27_0111_bakshi_final-package.md
[h0927-0706]: ../docs/handover/2026-09-27_0706_ameya_final-stack.md
[h0927-1228]: ../docs/handover/2026-09-27_1228_ameya_final-day.md
[h0927-2006]: ../docs/handover/2026-09-27_2006_bakshi_final-push.md
[h0927-2014]: ../docs/handover/2026-09-27_2014_ameya_final-upload.md
[d-g4]: ../docs/decisions/2026-09-25_2103_gate-g4-stage2.md
[d-g6]: ../docs/decisions/2026-09-25_1731_gate-g6-dp-vs-threshold.md
[d-nameuniq]: ../docs/decisions/2026-09-25_2111_gate-name-uniqueness.md
[d-g1]: ../docs/decisions/2026-09-25_2142_gate-g1-blocking-v2.md
[d-legal]: ../docs/decisions/2026-09-25_2142_gate-legal-form-features.md
[d-v3]: ../docs/decisions/2026-09-25_2328_model-v3-end-to-end.md
[d-v4]: ../docs/decisions/2026-09-26_0207_model-v4-france-and-cross-encoder.md
[d-frops]: ../docs/decisions/2026-09-26_0417_france-generator-ops-and-final-fit.md
[d-cut]: ../docs/decisions/2026-09-26_0532_candidate-set-cut.md
[d-frrules2]: ../docs/decisions/2026-09-26_0626_france-rules-v2.md
[d-blk3]: ../docs/decisions/2026-09-26_1122_blocking-v3-repairs.md
[d-v6all]: ../docs/decisions/2026-09-26_1425_model-v6all-final.md
[d-rules3]: ../docs/decisions/2026-09-26_1557_rules-v3-and-stage3.md
[d-v7ce3]: ../docs/decisions/2026-09-26_1933_model-v7ce3.md
[d-v7n]: ../docs/decisions/2026-09-26_2135_model-v7n.md
[d-stack]: ../docs/decisions/2026-09-27_0636_stacked-rules.md
[lb0926-1]: ../submissions/records/2026-09-26_sub01.md
[lb0926-2]: ../submissions/records/2026-09-26_sub02.md
[lb0926-3]: ../submissions/records/2026-09-26_sub03.md
[lb0926-4]: ../submissions/records/2026-09-26_sub04.md
[lb0927-1]: ../submissions/records/2026-09-27_sub01.md
[lb0927-2]: ../submissions/records/2026-09-27_sub02.md
[lb0927-3]: ../submissions/records/2026-09-27_sub03.md
[lb0927-4]: ../submissions/records/2026-09-27_sub04.md
[lb0927-5]: ../submissions/records/2026-09-27_sub05.md
[lb0927-6]: ../submissions/records/2026-09-27_sub06.md
[lb0927-7]: ../submissions/records/2026-09-27_sub07.md
