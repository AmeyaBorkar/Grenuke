# Decisions: FRA (France: the unseen country, self-training, probes)

**Summary.**
- France appears only in the test set, so it has no labels and the local holdout cannot score it. Our first uploads implied France at about 0.93 against about 0.99 for US/India. Most work after 26 Sep went into closing that gap without labels: look-alike odds for French words (how likely a word is to mark a decoy), rules that copy the organisers' generator (area RUL), self-training (training on the model's own confident decisions) and a French-only decision layer.
- Self-training was rejected twice (00:37 and 18:07 on 26 Sep, both on stand-in tests where India played France) and adopted at 21:17 once the look-alike odds, rules and stronger cross-encoders (text models that read both records together) existed. Round 1 gained +0.000458 on the public LB (France alone). Round 2, with guards, a French decision layer and the look-alike drop, gained +0.000134 for France (mixmdp, +0.000154 in total). Round 3, built without the decision layer, lost 0.000046.
- Synthetic French pairs, French probes and label-free estimators each failed a control or proved biased on decoys (look-alike records that the model accepts with confidence). The leaderboard, not the estimators, settled France.

## Index

| ID | decision | when (IST) | status |
|---|---|---|---|
| D-FRA-01 | France at the first model stage: country-agnostic features and test-fitted statistics only | 2026-09-25 15:20 | adopted for 25 Sep; superseded by D-FRA-03, D-RUL-01, D-FRA-13 |
| D-FRA-02 | Self-training on France: first rejection (confirmation bias in the LOCO test) | 2026-09-26 00:37 | superseded by D-FRA-13 |
| D-FRA-03 | Label-free look-alike odds for words never seen in training (v4) | 2026-09-26 00:41 | adopted |
| D-FRA-04 | No external data; only own-data augmentation | 2026-09-26 02:13 | adopted |
| D-FRA-05 | Synthetic French training pairs not built (superseded by the rules) | 2026-09-26 02:17 | superseded by D-RUL-01; revisited in D-FRA-23 |
| D-FRA-06 | Skip French address clusters, per-stratum calibration and cross-encoder pretraining | 2026-09-26 02:25 | rejected |
| D-FRA-07 | No fix for "weak-address" and "unrelated-name" families; the first France estimate withdrawn | 2026-09-26 05:52 | adopted (no action) |
| D-FRA-08 | Hand French pattern discovery to Sachi through a France kit | 2026-09-26 12:12 | adopted |
| D-FRA-09 | Two France biases found by SHAP: neither fixed | 2026-09-26 16:08 | rejected (fix 2); not packaged (fix 1) |
| D-FRA-10 | Rule-labelled French training pairs rejected after the India stand-in | 2026-09-26 16:54 | rejected |
| D-FRA-11 | Second rejection of self-training: retrain judged too small | 2026-09-26 18:07 | superseded by D-FRA-13 |
| D-FRA-12 | France probes (empty France, threshold cuts, lower threshold): built, never uploaded | 2026-09-26 20:39 | deferred, then dropped |
| D-FRA-13 | Self-train on France with cross-fitted pseudo-labels (v7nst) | 2026-09-26 21:17 | adopted (reverses D-FRA-02, D-FRA-11) |
| D-FRA-14 | Drop the transductive French assignment and the 2x A100 request; cheap tracks only | 2026-09-26 23:03 | adopted |
| D-FRA-15 | Re-plan the night around self-training (v7nst2, v7mst, v7s) | 2026-09-26 23:40 | adopted |
| D-FRA-16 | Stop unguarded self-training at round 1; withdraw frs2 | 2026-09-27 00:30 | adopted; guarded round 2 returned in D-FRA-18 |
| D-FRA-17 | After 0.990545: push the French-encoder direction; a second H100 for GPU work only | 2026-09-27 10:09 | adopted |
| D-FRA-18 | Guarded round-2 stage-2 labels at weight 3 | 2026-09-27 10:43 | adopted |
| D-FRA-19 | Keep the French acronym matches (no `noacr` upload): the size-bias test | 2026-09-27 11:38 | adopted |
| D-FRA-20 | A French decision layer on guarded round 2: mixmdp's France | 2026-09-27 13:30 | adopted |
| D-FRA-21 | No French cross-encoder veto | 2026-09-27 13:49 | rejected |
| D-FRA-22 | No round-2 self-training of the cross-encoders | 2026-09-27 13:56 | adopted (round 1 kept) |
| D-FRA-23 | Synthetic French supervision: run it as a priority, correct the generator, do not upload | 2026-09-27 14:16 | rejected for the upload |
| D-FRA-24 | Round 3 as a candidate; round 4 not used | 2026-09-27 16:36 | round 3 rejected by the leaderboard; round 4 rejected |
| D-FRA-25 | No drops on the synthetic-data detectors; the bge detector kept as corroboration | 2026-09-27 19:25 | rejected as a drop source |
| D-FRA-26 | After the verdicts: distrust pc-based French estimators | 2026-09-27 20:50 | adopted |

Related records: the rules that encode the generator are D-RUL-01 to D-RUL-17; the 7B re-check that removed French decoys is D-LLM-05; the upload strategy around the France-only controls is in D-SUB-15, D-SUB-16 and D-SUB-22 to D-SUB-26.

## Records

### D-FRA-01 · France at the first model stage: country-agnostic features and test-fitted statistics only
- **When (IST):** 2026-09-25 15:20, 19:16–19:28, 19:57 · **Phase:** P1 · **Area:** FRA
- **Decided by:** agent for Ameya
- **Status:** adopted for 25 Sep; superseded by D-FRA-03 (label-free odds), D-RUL-01 (rules) and D-FRA-13 (self-training)
- **Problem:** There are no French labels. Model v2 predicts 3.48 records per S1 in France against 3.34–3.37 elsewhere, and French extra words are unseen in training, so their look-alike odds are unknown. (S1 is a Source-1 business record; pc is the calibrated probability that a pair is a true match.)
- **Options considered:**
  1. French look-alike lexicons and rules now.
  2. Pseudo-labels on test, flagged at 15:20 as "risky, since the rules say 'using only the provided training data'".
  3. Diagnose, and wait for gate G7: upload the pipeline output with France emptied, so the score difference isolates France.
- **Choice and why:** Option 3, with no patch. The model mostly relies on house numbers, so French look-alikes with nudged numbers are already rejected: 'participations', 'holding', 'distribution' and 'international' have the first number equal only 1% of the time and are predicted at 0.000. "Et Fils" variants are accepted (pc about 0.99) while "& Associés" variants are rejected (about 0.05), although both have the first number equal about 80% of the time. Word rarity explains it, so the asymmetry was flagged for the probe, not patched. v2's extra French matches were "mostly same-address records where a generic word changed… probably right, but there are no French labels".
- **Evidence:** France new pairs in v2: 53,025, of which 99.2% were already v0 candidates (median p1 and pc 0.985 and 0.992) [M]. The diagnostics are [E] for France.
- **Outcome:** G7 was deferred to Saturday and never run (D-FRA-12). The first uploads exposed the gap: v2 and v3 scored 0.97608 and 0.97961 on the public LB against 0.98436 and 0.98882 on the local holdout. Backing France out of the leaderboard formula (LB = 0.38274·F_US + 0.46751·F_India + 0.14975·F_France, where each weight is that country's share of test S1) gave France at about 0.93 [E] [CHANGELOG, Submissions](../../CHANGELOG.md) · [RESEARCH_v6 §3](../../experiments/ameya/model-v1/RESEARCH_v6.md) · [methodology §2.1](../../experiments/ameya/final-zip/doc/Documentation_template.md).
- **Hindsight:** The team later self-trained on its own French test decisions, with guards and cross-fitting (D-FRA-13), so the 15:20 compliance worry was settled in practice in favour of using test pseudo-labels; how the rule was read is not in the sources. The pattern "same name + same number, different street", looked at at 15:16, is exactly the decoy family that the 7B re-check removed (D-LLM-06).
- **Links:** [chat:ameya/19e315ba 2026-09-25 15:20] · [chat:ameya/19e315ba 2026-09-25 19:16] · [chat:ameya/19e315ba 2026-09-25 19:57]

### D-FRA-02 · Self-training on France: first rejection (confirmation bias in the LOCO test)
- **When (IST):** 2026-09-26 00:37, reaffirmed 02:02–04:37 and 16:20 · **Phase:** P2 · **Area:** FRA
- **Decided by:** agent for Ameya (analysis) and Ameya. Ameya's 00:05 and 02:17 lists had proposed it; the 02:17 list itself noted that it "needs the organisers' OK on pseudo-labels".
- **Status:** superseded by D-FRA-13. This is the first of two rejections; the second is D-FRA-11.
- **Problem:** France has no labels. Can the model's own confident pairs stand in for them? The other team's plan also proposed confident pseudo-labels (D-SUB-04).
- **Options considered:**
  1. Pseudo-label the confident pairs (pc of at least 0.97 and the record's best S1 → 1; at most 0.03 → 0) and retrain.
  2. Restore the missing look-alike odds first (D-FRA-03).
  3. A transductive joint assignment (Bakshi's idea; see D-FRA-14).
  4. None.
- **Choice and why:** Option 2, and skip self-training. A leave-one-country-out (LOCO) test trains on the US and tests on India with India's labels hidden. With India's words known, two rounds gave 0.96106 → 0.96370 → 0.96479, a gain of only about +0.003. With India's words unseen, which is France's case, they gave 0.88235 → 0.85120 → 0.83075: "each round teaches the model to accept more of them (confirmation bias)". With the proxy in place "the remaining errors are confident convention errors … which pseudo-labels reinforce". The 00:37 analysis itself said: "the look-alike odds must be restored first; self-training can then add a little."
- **Evidence:** [M, LOCO stand-in] [ANALYSIS_v3 §3](../../experiments/ameya/model-v1/ANALYSIS_v3.md) · [ANALYSIS_v4 §1](../../experiments/ameya/model-v1/ANALYSIS_v4.md).
- **Outcome:** Skipped in P2. Reversed once the odds, the rules and stronger cross-encoders were in (D-FRA-13).
- **Hindsight:** The failure was measured in the words-unseen regime. The reversal followed the condition the 00:37 analysis set, so the two choices are consistent. The 16:20 summary "tested and rejected" was right for its regime and wrong as a blanket verdict.
- **Links:** [chat:ameya/19e315ba 2026-09-26 00:37] · [decision model-v4](../../docs/decisions/2026-09-26_0207_model-v4-france-and-cross-encoder.md) · [theory: self-training and domain shift](../theory/09-self-training-and-domain-shift.md)

### D-FRA-03 · Label-free look-alike odds for words never seen in training (v4)
- **When (IST):** 2026-09-26 00:41 (design) → 02:07 (v4 decision) · **Phase:** P2 · **Area:** FRA / FEA
- **Decided by:** Ameya (proposed by: agent for Ameya; recipe from the research sub-agent ada9694b, checked by the main session's own LOCO runs)
- **Status:** adopted from v4 on. v4 itself was never uploaded.
- **Problem:** Two causes of the France gap were verified. The legal-form bitmasks were out of range for France, and look-alike words never seen in training (groupe, développement, participations, holding…) had no entry in the label-derived word-odds table, so they read as neutral. France predicted 3.54 records per S1 against the generator's 3.46 and left only 4.4% of S1 empty (truth 5.6%).
- **Options considered:**
  1. v3ce, the cross-encoder alone.
  2. v4 = v3ce plus three fixes. (a) Proxy odds: a word's share of moved house numbers among close pairs in its own country, mapped to the label-odds scale by a decreasing isotonic fit on US/India words, shrunk toward neutral for rare words. (b) Group `lo0`: unseen words written as exactly 0 (they were −1.9e-16 on train but 0 on test). (c) No legal-form bitmasks.
  3. Other word-odds ideas: a transductive mixture inversion, look-alike share = (f_t − q)/(a − q) with a about 0.98 and q the rate for true copies (it saturated for France, so every French word got 0.0; replaced at 00:54 by the isotonic map); cross-lingual embeddings to English neighbours; a hand-written French→English business-word lexicon; unknown words as missing plus a count of unknown extras.
  4. Self-training on France: rejected (D-FRA-02).
- **Choice and why:** Option 2 as the upload candidate.
- **Evidence:**
  - Holdout tie with v3ce: Δ −0.00006 [−0.00012, −0.00001] [M].
  - LOCO, US → India on the dev kit [M]: in-country 0.98346; US only 0.96106; India's words hidden 0.88235; proxy odds 0.95984. An independent sub-agent reproduced it exactly (a4957c58, 03:37). Without the `lo` group the US-only model scores 0.94180 [ANALYSIS_v3 §3](../../experiments/ameya/model-v1/ANALYSIS_v3.md).
  - Gate G13 (the same LOCO test) priced an unseen country at 0.022 with its words known and 0.10 with them unseen [M] [ANALYSIS_v3 §3](../../experiments/ameya/model-v1/ANALYSIS_v3.md) · [ANALYSIS_v4 §4](../../experiments/ameya/model-v1/ANALYSIS_v4.md). It led to the proxy odds and the bitmask drop rather than to pruning features, and became the stand-in for later France experiments.
  - French look-alike patterns per S1: 0.047 → 0.002 and 0.047 → 0.007 [M, label-free counts]. The model's France forecast rose 0.970 → 0.980 [E].
- **Outcome:** v4 was overtaken before any upload, so its forecast "+0.006 to +0.009" was never tested alone. From v4 on, US/India use label odds and France the proxy. With the rules (D-RUL-01, D-RUL-02) the public LB went 0.97961 → 0.98781 (26 Sep #01, France implied 0.971–0.976, from about 0.93 [E]).
- **Hindsight:** The proxy fixed a measurable failure (LOCO 0.882 → 0.960), but it was bundled with five other changes in one upload, so its own leaderboard value is unknown. The SHAP review later showed the isotonic map puts words that are both list words and look-alike words on the look-alike plateau (D-FRA-09).
- **Links:** [decision model-v4](../../docs/decisions/2026-09-26_0207_model-v4-france-and-cross-encoder.md) · [handover 2026-09-26_0207](../../docs/handover/2026-09-26_0207_ameya_leaderboard-gap-france-v4.md) · [chat:ameya/19e315ba 2026-09-26 00:55] · [chat:ameya/19e315ba 2026-09-26 01:02] · [chat:ameya/agent-a4957c58 2026-09-26 03:37] · [LB 2026-09-26 #01](../../submissions/records/2026-09-26_sub01.md)

### D-FRA-04 · No external data; only own-data augmentation
- **When (IST):** 2026-09-26 02:13 and 02:58 · **Phase:** P2 · **Area:** FRA / ORG
- **Decided by:** agent for Ameya (reading of the rules); the organiser answer was pasted by Ameya
- **Status:** adopted
- **Problem:** Ameya asked about augmenting, pretraining and "mix some more datasets".
- **Options considered:** 1. Mix in external datasets, for augmentation or pretraining. 2. Use only the provided data: augmentation from our own records, a final fit on all of train, self-training.
- **Choice and why:** Option 2. External datasets, including for pretraining, are disqualifying. Pretrained open weights are allowed if MIT or Apache-2.0, at most 8B parameters per model, run offline, and fine-tuned only on the provided data (the organiser answer). Hosted LLM APIs are banned inside the pipeline. Ranked options: (1) synthetic French-style pairs from test S1 text, tested first on India; (2) a final fit on 100% of train; (3) self-training (low priority after the LOCO result); (4) unlabelled cross-encoder pretraining (skip).
- **Evidence:** The organiser answer pasted by Ameya and the agent's reading of the rules [R]; the answer itself is not quoted in the sources.
- **Outcome:** (2) done as v5all and v6all; (1) superseded by the rules (D-FRA-05) and revisited on 27 Sep (D-FRA-23); (3) adopted later (D-FRA-13).
- **Hindsight:** unknown (none recorded).
- **Links:** [chat:ameya/19e315ba 2026-09-26 02:13] · [chat:ameya/19e315ba 2026-09-26 02:58]

### D-FRA-05 · Synthetic French training pairs not built (superseded by the rules)
- **When (IST):** 2026-09-26 02:13–02:17 (proposed) → 04:17 (decided) · **Phase:** P2 · **Area:** FRA
- **Decided by:** agent for Ameya. Ameya's pasted list called it "the strongest idea", to be validated first on India (synthesise India pairs, train on US plus synthetic, score India: US-only 0.960 against 0.983 with labels).
- **Status:** superseded by D-RUL-01. Revisited on 27 Sep by Sachi's work (D-FRA-23).
- **Problem:** Apply the generator's noise to French S1 text to get labelled French-style pairs.
- **Options considered:** 1. Build a synthetic generator from the generator catalogue (about a day). 2. Hand rules, derived from US/India labels, for the one failing operation.
- **Choice and why:** Rules. The generator applies the same operations in every country with country word lists. France's failure is one operation (op B) whose words are French, and a rule fixes that directly; a synthetic generator would have had to encode the same A/B rules.
- **Evidence:** The generator-catalogue sub-agent: "feasible in about a day… superseded" [R] [ANALYSIS_v4 §3.1](../../experiments/ameya/model-v1/ANALYSIS_v4.md). The rules were forecast at +0.0027 on the public LB [E].
- **Outcome:** Never built in P2. The measured France gain since v3 was about +0.04 France F0.5 for all fixes together [E].
- **Hindsight:** Time-efficient on 26 Sep. On 27 Sep Sachi's synthetic pairs did not match real French data (D-FRA-23).
- **Links:** [chat:ameya/19e315ba 2026-09-26 04:37] · D-RUL-01

### D-FRA-06 · Skip French address clusters, per-stratum calibration and cross-encoder pretraining
- **When (IST):** 2026-09-26 02:25–04:37 · **Phase:** P2 · **Area:** FRA / MDL / CE
- **Decided by:** agent for Ameya, measuring each idea from Ameya's 02:17 list (the same sizing round appears as D-PRB-05, item 1, 2 and 5)
- **Status:** rejected, each measured
- **Problem:** Ameya's list offered these as possible causes of, or levers for, France's implied 0.93.
- **Options considered, with evidence:**
  - Address clusters: 11.1% of French S1 share an exact normalised address (maximum 101) against 4–5.7% in US/India (maximum 10–14). Clustered holdout S1 score 0.984–0.987 against 0.990–0.991. At most 0.005 France F0.5, at most 0.001 on the public LB [M]/[E].
  - Per-stratum calibration (country × shared-name size × address present): holdout gaps at most 0.05, mostly +0.01–0.04, the argmax selection effect [M].
  - Cross-encoder pretraining on own records: the whole cross-encoder adds +0.0014; hours of GPU for an uncertain gain [E].
- **Choice and why:** None moves the leaderboard enough for its cost.
- **Evidence:** The numbers above, measured on the holdout and on label-free counts [M]/[E] [ANALYSIS_v4 §1](../../experiments/ameya/model-v1/ANALYSIS_v4.md).
- **Outcome:** None built.
- **Hindsight:** Right for clusters and calibration. French identical-name ties were later found overconfident (14.6% of French empty-address records have a summed pc above 1.1), but renormalising them "nets about zero" [RESEARCH_v5 §8.2](../../experiments/ameya/model-v1/RESEARCH_v5.md). The final methodology lists renormalising French probabilities among the dropped ideas (up to −0.000137).
- **Links:** [chat:ameya/19e315ba 2026-09-26 04:37] · [ANALYSIS_v4 §1](../../experiments/ameya/model-v1/ANALYSIS_v4.md)

### D-FRA-07 · No fix for "weak-address" and "unrelated-name" families; the first France estimate withdrawn
- **When (IST):** 2026-09-26 05:52 → 06:07 · **Phase:** P2 · **Area:** FRA / EVL
- **Decided by:** agent for Ameya (from the sol_france fork; the sub-agent a000fd3b raised it)
- **Status:** adopted (no action). The France estimator's level was withdrawn.
- **Problem:** A label-free France estimator (a share-shift breakdown) attributed 74.3 (weak address) and 48.7 (unrelated name) excess French acceptances per 1000 S1, constant across model versions, about 123 per 1000 likely false positives. If real, that was worth up to +0.02 France F0.5.
- **Options considered:** A France-only correction (per-country recalibration of pc for weak-address records, each carrying about 0.977 owner mass; a rule for unrelated names at shared addresses) against checking the families first against the generator's invariants; or nothing.
- **Choice and why:** Check first, then do nothing. The "unrelated" names were mostly French domains that the profiler missed ("Fitness Club SASU" → "clubfitness.com"): domain-plus-unrelated copies are 220 per 1000 in France against 214 and 202 in US and India, where they are true. France has fewer weak-address candidates per S1 (2.97 against 6.1 US and 3.5 India), so the same prediction count looked like a larger share. The real false-positive excess is about 2.2 per 1000 S1 (about 0.0004 France F0.5); identical-name ties are worth at most +0.0005 France F0.5, and renormalising pc on them nets about zero; real unrelated-name false positives are 0.33 per 1000.
- **Evidence:** France has 166 empty-address records per 1000 S1 against about 158 expected from the generator rates; it predicts 89.6 per 1000 (54%) against US 90.3 of 146 (62%) and India 77.9 of 121 (64%) [M label-free counts / E] [RESEARCH_v5 §8.2](../../experiments/ameya/model-v1/RESEARCH_v5.md).
- **Outcome:** The 0.959 France estimate became "unknown, 0.93–0.98, only an upload can measure it". After the upload of about 14:38 the leaderboard implied about 0.971–0.976. The agent also asked for the profiler to be fixed before reuse; no record of that fix exists.
- **Hindsight:** A correct retraction. Label-free estimators share the model's blind spots, which is the "independent check" lesson in the final methodology (D-FRA-26).
- **Links:** [chat:ameya/19e315ba 2026-09-26 06:07] · [chat:ameya/agent-a000fd3b 2026-09-26 06:06]

### D-FRA-08 · Hand French pattern discovery to Sachi through a France kit
- **When (IST):** 2026-09-26 12:12–12:24 · **Phase:** P3 · **Area:** FRA / ORG
- **Decided by:** Sachi (proposed taking it over "so you don't have to"); agent for Ameya built the kit
- **Status:** adopted
- **Problem:** Sachi needed portable data: French candidates with pc, edit profiles, names and addresses, plus a labelled US/India table.
- **Options considered:** Export only the stage-2 pairs, or also the rule populations over all blocking candidates.
- **Choice and why:** Both, with a README warning. Op B looks 12–43% true on stage-2 holdout pairs only because the US/India stage 1 already filtered most false look-alikes (95% of India's and 56% of the US's op-B records are below stage 2), while France's stage 1 cannot. Over all candidates it is 0.6–3.2% true.
- **Evidence:** France 1,653,843 stage-2 pairs (6.37 per S1); holdout 2,762,088; about 200 MB. Open lead: France accepts 25% of NUM edits against 84–93% in US/India [M].
- **Outcome:** [PR #31]; the kit was handed over by a manual Drive upload. Sachi's later findings include the street-swap analysis (D-LLM-06) and the synthetic generator (D-FRA-23).
- **Hindsight:** Spotting the selection bias before handing the data over prevented a wrong conclusion ("the France rules are flawed").
- **Links:** [chat:ameya/19e315ba 2026-09-26 12:17] · [chat:ameya/19e315ba 2026-09-26 12:22] · [chat:ameya/19e315ba 2026-09-26 12:24]

### D-FRA-09 · Two France biases found by SHAP: neither fixed
- **When (IST):** 2026-09-26 ~16:08 · **Phase:** P3 · **Area:** FRA / FEA
- **Decided by:** Ameya (analysis: sub-agent "agentA", an agent for Ameya)
- **Status:** rejected (fix 2); not packaged (fix 1)
- **Problem:** True-copy families in France lose 1–5 logits (raw model scores) against US/India. Exact copies are fine (99.57% get pc of at least 0.999, against 99.73–99.83%). List-word swaps and appends sit at 58–63% against 89–98%, and acronyms at 17% against 81–83%.
- **Options considered:**
  1. Cap the proxy odds of France's dual-use words. "groupe", "france" and "développement" are both op-A list words (about 6,500 same-address pairs each) and look-alike insert words (about 26k nudged pairs each), and the proxy gives them −4.84, the value of "holding". Cap at −1.25, the US label odds of "partners" (the US holdout loses −0.00106 if "partners" gets the proxy value). Effect: France +8,512 / −311 predictions, of which 6,078 the rules already added, 2,434 new and none a nudged look-alike; about +0.0004 France F0.5.
  2. Recompute the retrieval margin only against rivals at the same house number (French numbers are small and shared, so a rival S1 on the same street scores almost as high). Effect: France +4,460 / −1,423 predictions (+17.2 / −5.5 per 1000 S1), mostly one-word swaps the rules already sort and generic-name look-alikes; impossible to check on the holdout without a retrain.
- **Choice and why:** Neither changed the pipeline. "Fixing either moves only about 1–2% of French predictions … so neither is the missing 0.01."
- **Evidence:** [M]/[E] [RESEARCH_v6 §2.9](../../experiments/ameya/model-v1/RESEARCH_v6.md).
- **Outcome:** Fix 2 "not adopted"; fix 1 "not packaged yet", and it does not appear in later chains.
- **Hindsight:** unknown (none recorded).
- **Links:** [handover 2026-09-26_1557](../../docs/handover/2026-09-26_1557_ameya_research-v6-gap-budget.md) · D-FRA-03

### D-FRA-10 · Rule-labelled French training pairs rejected after the India stand-in
- **When (IST):** 2026-09-26 16:54–18:14 · **Phase:** P3 · **Area:** FRA
- **Decided by:** agent for Ameya
- **Status:** rejected
- **Problem:** A model trained on the US alone loses about 0.021 on India, and France's gap to US/India (about 0.019) is the same size. Can French training labels be made without labels?
- **Options considered:** A: label French pairs by the generator's operations (positives: exact copy, A, APP, ACR at the address; negatives: op-B swaps and nudged numbers). B: a stronger cross-encoder. C: the margin retrain. D: synthetic French pairs ("only if A proves French training data helps").
- **Choice and why:** Test A on India first. India's labels are hidden, its word odds are replaced by the label-free proxy, stage 1 is retrained on 35% of US and 50% of India training S1, and it is scored on the whole India holdout. Go ahead only if it closes a real share of the gap. It did not.
- **Evidence** [M, India stand-in, stage-1 F0.5]: ceiling with India labels 0.98660; US only 0.96555. Rule labels 0.96463 (−0.0009). Rule positives alone 0.96217 / 0.96278 / 0.96323 over three seeds (mean −0.0040). Positives plus 449 op-B negatives: mean +0.0005 (noise). The "house number moved +3…+21" negatives are 43.5–45% true on India, because compound numbers make first-number offsets meaningless [RESEARCH_v6 §4](../../experiments/ameya/model-v1/RESEARCH_v6.md).
- **Outcome:** Dropped. "For France, the rules already apply what the rule labels would teach."
- **Hindsight:** Easy certain positives "teach the model to accept too much". This framed why the later pseudo-labels came from the model's own confident decisions as well as from the rules (D-FRA-13).
- **Links:** D-FRA-11 · D-RUL-01

### D-FRA-11 · Second rejection of self-training: retrain judged too small
- **When (IST):** 2026-09-26 18:07–18:20 · **Phase:** P3 · **Area:** FRA
- **Decided by:** agent for Ameya; Ameya
- **Status:** superseded by D-FRA-13, about 3 hours later
- **Problem:** On the India stand-in, self-training (labels from the US-only model's pc of at least 0.95 → 1 and at most 0.02 → 0; 77% of India's pairs labelled, positives 99.3% true) gained a little. Is a 2–3 h France retrain worth it before the deadline?
- **Options considered:** Retrain stage 1 and 2 with French self-labels now, or skip.
- **Choice and why:** Skip. "A small, consistent gain (~4% of the gap) … too marginal to justify a retrain before the deadline." The best variants close 5–7% of the gap, and the rules already apply what rule labels would teach. Estimated +0.0001 to +0.0002 on the public LB [E]. The India stand-in also showed that "easy certain copies teach the model to accept too much".
- **Evidence:** Self-training over seeds 0–2: +0.0012, +0.0012, +0.0002; mean +0.0009 [M, India stand-in, stage 1 only]. Seed table in [RESEARCH_v6 §4](../../experiments/ameya/model-v1/RESEARCH_v6.md).
- **Outcome:** Reversed at 21:17, when the board had moved (top 7 above 0.99), US/India were near their ceiling, and the cross-encoders' French disagreement showed what self-training on the target domain could fix. Reaffirmed in [handover 2026-09-26_1817](../../docs/handover/2026-09-26_1817_ameya_ce-large-box.md): "No France retrain on them before the deadline."
- **Hindsight:** The stand-in measured stage-1 self-training only. On France, stage-2 self-training gained about 3 times the stand-in's estimate (+0.000458, D-FRA-13). The older verdict "rejected: 0.882 → 0.831" came from a setting where India's words were unseen.
- **Links:** [chat:ameya/19e315ba 2026-09-26 18:14] · D-FRA-02 · D-FRA-10

### D-FRA-12 · France probes (empty France, threshold cuts, lower threshold): built, never uploaded
- **When (IST):** 2026-09-25 (G7 planned) · 2026-09-26 12:24, 16:16, 20:39–20:49, 23:31–23:55 · 2026-09-27 01:45 · **Phase:** P1–P3 · **Area:** FRA / SUB
- **Decided by:** agent for Ameya (design); Ameya ("we can't do probing we have to keep on going and squeezing")
- **Status:** deferred at each step, then dropped. None was uploaded.
- **Problem:** Two questions about France could only be answered by an upload. How good is France? (G7: upload the candidate with France emptied, so `LB_fr0 = 0.38274·F_US + 0.46751·F_India + 0.14975 × 0.0559`, and the difference to the candidate gives France.) And is France's band of pc just above the threshold overconfident, or the band just below it underconfident?
- **Options considered.** Built as packages, validator PASS:
  1. `fr0`: France emptied (`probe-v4-fr0`, `probe-v6s3-fr0`, `probe-v7-fr0`). Alone it scores about 0.85 and means nothing without its pair.
  2. `fr090`: drop French predictions below pc 0.9 after the rules. It would drop about half of its 18,263 pairs from the rules' own true-copy edits, "a known loss that would hide the answer".
  3. `fr090r`: the same cut before the rules, so the rules re-add their true-copy edits: −10,738 French pairs (41 per 1000 S1), median pc 0.792; expected −0.0001 on the public LB if calibrated and +0.0003 if 50% true. `fr095r` and `fr080r` would bracket the best cut.
  4. `frlo`: add owned French pairs above pc 0.5: +8,076 pairs (median pc 0.557; 56% are ties); break-even precision 0.72; "low value as an upload".
- **Choice and why:** No upload.
  - 26 Sep 16:16: with one slot left, the candidate went up, not a probe (D-SUB-09).
  - 26 Sep 23:31–23:55: every remaining slot went to a real attempt (D-SUB-11, D-SUB-12).
  - 27 Sep 01:45: self-training had emptied the band around the 0.70 threshold. Owned French pairs at pc 0.7–0.8 fell from 36.5 to 11.8 per 1000 S1 (US 5.5), 0.5–0.7 from 58.7 to 28.4, 0.8–0.95 from 77.6 to 33.4. So moving the threshold either way touches about 12 predictions per 1000 S1, about ±0.00005 on the public LB [M]/[E]. At 09:09 on v7sq-dpc, about 97% of French predictions had stage-3 pc of at least 0.99 (3,261.6 of about 3,359 per 1000 S1) [M], so the remaining errors are confident and no threshold reaches them.
  - Bakshi chose not to run an fr0 probe either: "it would pin the level down but costs a slot, can't improve the score, and no decision depends on it".
  - Gate G8 had already shown that a stricter France threshold "only loses" in the LOCO setting [A4 §4].
- **Evidence:** [M] band table, [E] values [RESEARCH_v6 §3, §6.3–6.4](../../experiments/ameya/model-v1/RESEARCH_v6.md) · [chat:ameya/19e315ba 2026-09-27 01:45] · [chat:ameya/19e315ba 2026-09-27 09:10].
- **Outcome:** France was measured by leaderboard arithmetic instead: France = (LB − US/India part) / 0.14975, giving 0.971–0.976, 0.973, 0.978 and 0.981 over the 26 Sep uploads [E]. A French decision-layer change shipped later (D-FRA-20) and was judged by uploads, not probes.
- **Hindsight:** The arithmetic assumes US/India score on test as on the holdout. RESEARCH_v6 §3 framed the unknown as A (France carries about 0.014 of confident errors) or B (US/India lose about 0.0025 on test); only `fr0` could have separated them. Not knowing cost no decision.
- **Links:** [decision rules-v3-and-stage3](../../docs/decisions/2026-09-26_1557_rules-v3-and-stage3.md) · D-SUB-12 · D-PRB-05

### D-FRA-13 · Self-train on France with cross-fitted pseudo-labels (v7nst)
- **When (IST):** 2026-09-26 21:17–21:30 (design) → about 23:35 (upload) · **Phase:** P3 · **Area:** FRA
- **Decided by:** Ameya (design: agent for Ameya, within Ameya's mandate "anything which adds is good"; the uploads were Ameya's). A parallel research session of Ameya's had argued against self-training at 16:20 and accepted the leaderboard result afterwards.
- **Status:** adopted; the methodology's first "core innovation". It reverses D-FRA-02 and D-FRA-11.
- **Problem:** v6all (0.988609) put France at about 0.973, 0.018 below US/India. US/India had about 0.0003 left, and 0.99 or more was now the top 7 of the public LB (Grenuke was 17th). (v7n, uploaded at about 23:05, took France to about 0.978.) "The next step has to come from France, and it has to be large." France's specific weakness is that the text models disagree on it: cross-encoders disagree on the sign of the score for 12.0% of French band pairs against 2.7–3.1% elsewhere [M, label-free]. That is the weakness that self-training on the target domain addresses.
- **Options considered:** Keep the earlier rejections; more stage-2 tuning (exhausted); rule labels (D-FRA-10); France threshold probes (no slots to spare, D-FRA-12); self-training in stage 2 (`s2.py --pseudo`) and in the cross-encoder (`ce_box.py --pseudo`).
- **Choice and why:** Both levers, with the following design.
  - Labels from v7ce3's final decisions (`pseudo_labels.py`, positive at pc of at least 0.9, negative at most 0.05). Label 1: in the final matches with pc of at least 0.9, or added by the rules or the acronym join. Label 0: not in the final matches with pc of at most 0.05, or an op-B prediction the rules dropped. Everything else is unlabelled but still scored.
  - The rules win on rule-typed populations.
  - Cross-fitting by S1 group: French S1 are split by `fold_of % 3` for the cross-encoder and `% 4` for stage 2. Model g trains on the other groups' labels and alone scores its own group, so "no French pair is scored by a model that saw its own label or its S1's other labels". A dry run showed 0 S1 overlap.
  - US/India rows unchanged. Early stopping and isotonic calibration use labelled rows only. Pseudo rows are unweighted.
  - Why it is safe under F0.5: "a dropped false positive gains 0.18 while a dropped true pair costs 0.07", so a model that leans toward dropping is about neutral even if only half its changes are right, and about +0.0003 if 75% are.
  - "The self-training variants can't be gated on the holdout (no France there); only the leaderboard can judge them."
- **Evidence:**
  - Cross-encoder band, 385,274 French pairs: 62,189 positive (8,921 rule adds, 83 acronym), 238,334 negative (10,891 op-B drops), 84,751 unlabelled. All 1,429,666 French stage-2 rows: 851,116 positive, 493,352 negative (19,537 op-B), 85,198 unlabelled [M].
  - Holdout: v7nst c2 0.991158 (+0.000059 [+0.000021, +0.000094] against v7ce3) and s3 0.991194 (+0.000055 [+0.000022, +0.000089]); US/India within 0.00002 of v7n [M].
  - France, label-free [E]: Σ pc per S1 3.5157 → 3.4122 (the US/India level); uncertain band (pc 0.3–0.99) 358.2 → 186.1 per 1000 S1; op-B pairs above 0.7 from 28% to 0.4%; final predictions +14.0 / −17.4 per 1000 French S1 (US/India about +1.5 / −0.6).
  - Leaderboard: 0.989721 → 0.990179, +0.000458, France +0.0031 to about 0.981 [M]/[E] [LB 2026-09-26 #04](../../submissions/records/2026-09-26_sub04.md).
- **Outcome:** "Self-training on France works." Every later France model was self-trained. The self-trained cross-encoder (`ce_box.py --pseudo`) was lost twice with rented boxes and rebuilt (e5ls, bges, qst) for v7s and v7sq. The documentation counts round 1 as +0.00046 on the public LB.
- **Hindsight:** It reversed two rejections, both measured in other regimes (words unseen; stage 1 only on the India stand-in). The order mattered: fix the vocabulary first, then self-train. Later rounds needed guards (D-FRA-16, D-FRA-18, D-FRA-24).
- **Links:** [handover 2026-09-26_2049](../../docs/handover/2026-09-26_2049_ameya_squeeze-v7n.md) · [RESEARCH_v6 §6.7, §6.10, §6.11](../../experiments/ameya/model-v1/RESEARCH_v6.md) · [commit 6b74099] · [chat:ameya/19e315ba 2026-09-26 21:17] · [theory: self-training and domain shift](../theory/09-self-training-and-domain-shift.md)

### D-FRA-14 · Drop the transductive French assignment and the 2x A100 request; cheap tracks only
- **When (IST):** 2026-09-26 23:03–23:57 · **Phase:** P3 · **Area:** FRA / DEC
- **Decided by:** agent for Ameya (recommendations); Bakshi's "low-cost strategy" largely agreed
- **Status:** adopted
- **Problem:** What to do overnight for France, with no labels and little compute?
- **Options considered:** Bakshi's transductive assignment (assign records jointly over the whole test set) and a request for two A100 GPUs; Track A, threshold probes on v7nst (already built); Track B, family-balanced consensus (treat the two e5-large runs as one family and give bge its own vote); Track C, extra inference on disagreements.
- **Choice and why:** Drop the assignment: it "can't pass his own kill criterion: the holdout has no France". Track A was already built; Track B is cheap; Track C cannot be built and gated in time. The agent and Bakshi agreed not to pick self-trained models by their French rule-population AUC (0.984 for v7nst), since it is biased by the same rules that made the pseudo-labels.
- **Evidence:** [chat:ameya/19e315ba 2026-09-26 23:03] · [RESEARCH_v6 §6.8](../../experiments/ameya/model-v1/RESEARCH_v6.md).
- **Outcome:** The families v7s, v7sq, v7ensall and v7ensall2 were built overnight. Selection used the `fhs` COPY count (a label-free count of true copies gained and lost, per 1000 French S1) plus the leaderboard.
- **Hindsight:** unknown (none recorded).
- **Links:** D-FRA-12 · D-FRA-15

### D-FRA-15 · Re-plan the night around self-training (v7nst2, v7mst, v7s)
- **When (IST):** 2026-09-26 23:40 · **Phase:** P3 · **Area:** FRA
- **Decided by:** agent for Ameya
- **Status:** adopted
- **Problem:** What to build overnight for the five uploads of 27 Sep, once v7nst had scored 0.990179?
- **Options considered:** Plain v7m (bge in the mean); self-trained variants.
- **Choice and why:** Three sequential laptop builds. v7nst2: round-2 labels from v7nst's own decisions, testing whether iterating helps or "amplifies its own errors". v7mst: bge joins the mean (e5l, e5l2, bge), round-1 labels. v7s: the France self-trained e5-large replaces e5l2 in the mean (with bge), round-1 labels. Round-1 labels were kept for the bge and e5ls variants "for readability", so each change is isolated.
- **Evidence:** Round-2 labels: 859,422 positive (507 rule adds, 73 acronym), 502,206 negative (305 op-B drops), 68,038 unlabelled (round 1: 85,198). v7nst2 holdout 0.991171, equal to v7n; France Σ pc 3.4050, band 164.9 per 1000 S1 [M]/[E] [chat:ameya/19e315ba 2026-09-27 00:16].
- **Outcome:** v7nst2 drifted (D-FRA-16); v7mst and v7s fed the model families of D-FRA-17.
- **Hindsight:** unknown (none recorded).
- **Links:** [RESEARCH_v6 §6.11](../../experiments/ameya/model-v1/RESEARCH_v6.md)

### D-FRA-16 · Stop unguarded self-training at round 1; withdraw frs2
- **When (IST):** 2026-09-27 00:30–02:43 · **Phase:** P3 · **Area:** FRA / DEC
- **Decided by:** agent for Ameya; Ameya
- **Status:** adopted (unguarded round 2 rejected). Round 2 returned with guards in D-FRA-18.
- **Problem:** Does iterating the pseudo-labels help? And, since stage 3 lowers the French rule-population AUC (v7nst 0.9844 → 0.9791), should France take the stage-2 decision (`frs2`)?
- **Options considered:** Upload v7nst2 or keep it in the bags; bag both rounds (v7ens2, holdout s3 0.991193); stop at round 1. For `frs2`: keep stage 3, or let France use stage 2.
- **Choice and why:** Stop at round 1. v7nst2 holdout s3 is 0.991187 against v7nst's 0.991194, and France changes +3.4 / −7.5 per 1000 S1. Reading 40 French changes by hand: it drops clear copies ("Projet & Cie EURL" → "Projet & Compagnie EURL"; "KZ Comite SARL" → "KZ Comite-SARL" with an empty address) and adds word swaps at the S1's address ("GY Amicale SARL" → "GY Agricole SARL", "Calais Anciens SA" → "Calais Soins SA") plus one Bordeaux → Roubaix pair. COPY net −1.54, `fhs` −0.87. "Iterating the pseudo-labels on the model's own decisions amplifies its near-threshold mistakes. No further rounds; v7nst2 is out of the ensemble." The AUC drop behind `frs2` is an artifact: stage 2 trained on pseudo-labels that contain the rule populations and stage 3 did not, and the rules override both on those pairs. And 35% of `frs2`'s 3,029 French drops have an empty record address (base rate 2.7%), exactly the pairs stage 3's record-mass calibration lifts; it loses 3.86 true copies per 1000 S1 net. `frs2` was withdrawn and its four queued builds skipped.
- **Evidence:** [M] holdout and counts; [E] `fhs` [RESEARCH_v6 §6.12, §6.14](../../experiments/ameya/model-v1/RESEARCH_v6.md) · [chat:ameya/19e315ba 2026-09-27 00:24] · [02:16] · [02:25].
- **Outcome:** v7nst2 left `v7ensall`; v7ens2 was not uploaded either ("too small to spend a slot on alone"). At 10:44 the same reasoning killed run C (stage 2 on the v7sq-dpc teacher's raw labels), which "repeats the drift signal of v7nst2" (D-FRA-18).
- **Hindsight:** Bakshi's comment: "Dropping real 'Cie → Compagnie' copies was invisible to every aggregate metric", so read about 40 French changes by hand [chat:ameya/19e315ba 2026-09-27 10:53]. The methodology's successful "second round … +0.00015" refers to later work with guards, not to v7nst2.
- **Links:** D-FRA-13 · D-FRA-18

### D-FRA-17 · After 0.990545: push the French-encoder direction; a second H100 for GPU work only
- **When (IST):** 2026-09-27 10:09–10:40 · **Phase:** P4 · **Area:** FRA / ORG
- **Decided by:** Ameya (offered and rented the box between 10:14 and 10:25); proposed by: agent for Ameya
- **Status:** adopted
- **Problem:** v7sq-dpc's 0.990545 (rank 8) said the French gains are in the models. About 11 hours were left.
- **Options considered (launched together):** A, a bag of the three Qwen models (v7qbag); C, a better teacher (relabel France from v7sq-dpc, retrain stage 2); B, every French-trained cross-encoder in the mix (v7sq4); round-2 retrains of e5ls and Qwen on the new labels, on the new box.
- **Choice and why:** The new box (H100 80 GB, 503 GB RAM, 128 CPUs) takes uploads at about 3 MB/s, so stage 2 stays on the laptop and the box does GPU work only. The trainers read only `eid`, name and address, so slim band-only records (119 MB instead of 1.08 GB) were sent over parallel streams in 70 seconds.
- **Evidence:** [chat:ameya/19e315ba 2026-09-27 10:09] · [10:28] · [10:35].
- **Outcome:** v7qbag's stage-3 gate was 0.991249 and its `-dpc` was packaged and audited. C was killed at 10:44 and the retrains restarted on guarded labels (D-FRA-18). Later, v7qbag and v7sq4 were screened out by their change footprint (D-SUB-17).
- **Hindsight:** unknown (none recorded).
- **Links:** [handover 2026-09-27_1228](../../docs/handover/2026-09-27_1228_ameya_final-day.md)

### D-FRA-18 · Guarded round-2 stage-2 labels at weight 3
- **When (IST):** 2026-09-27 10:43–10:46 (guard decision) → 13:09 (builder verified) → 16:08 (weight checked) · **Phase:** P4 · **Area:** FRA
- **Decided by:** Ameya (proposed by: the GPU-plan sub-agent a4ea3fde and the design agent's "Wg" plan); built by agent for Ameya
- **Status:** adopted (v7sqwg, v7sq6wg, v7sq7wg, v7sq8wg, v7sq9wg, v7sqq7; the methodology's "two guards")
- **Problem:** A better teacher (v7sq-dpc) was available, but retraining on its labels risks confirmation bias, a student trained on its teacher's mistakes. The French-trained cross-encoders already agree with the new labels on 98% of French pairs (the labels are largely their own outputs), so a round-2 retrain is worth about another random seed; they agree 94–98% with each other on France and only 60–69% with the untrained ones.
- **Options considered:** Raw round-2 labels; "strict", "rules" and "agree" variants; guarded labels. Cross-fitting in thirds (`fold_of % 3`) with the same seeds and the untrained cross-encoders in the mix. Weight 1, 3 or 5. Mixes: v7sq's (v7sqwg) or v7sq6's France-only mix (v7sq6wg).
- **Choice and why:** Guarded labels at weight 3. The guards: pairs whose record has an empty address keep their round-1 label, and the rule populations overwrite everything else (A, APP, ACR = 1; op-B = 0). The agent found three ways bias would enter: 12,682 same-name pairs (99.4% with an empty address, a median of 12 competing French S1) would become confident negatives, which could teach "empty-address copies never match" while they are about 5.6% of true matches; 4,063 op-B swaps would lose their rule-based negative label; and the stage-2 labels repeat the v7nst2 drift (same direction on 99.6% of 50,203 pairs). Run C (raw labels) was killed; the laptop ran strictly in order: B (v7sq4), B2 (v7sq6), Wg, then R2 (v7sq5g, dropped in D-FRA-22). Weight 5 gave +0.000167, the same as 3, so the weight had saturated.
- **Evidence:**
  - Label changes [M]: 59,818 band labels change (29% of French S1 with a band pair), mostly from unlabelled to labelled; 144 flip 1 → 0 (87% word swaps that v7ce3 accepted) and 56 flip 0 → 1; band pairs left unlabelled at pc 0.05–0.9 fall from 25.3% to 9.9%; the new labels agree with the rule populations on 99.72%.
  - Guarded stage-2 labels [M]: 1,429,666 rows; 214,288 empty-address pairs keep their round-1 label (16,803 of them differ from the new one); 95,350 rule pairs; 861,340 positive, 516,463 negative, 51,863 unlabelled.
  - Valuations [E]: v7sqwg predicted the fewest look-alikes (348 against 592 for v7sq) and the smallest downside (−0.00005). With cmq6 it became v7sq6wg, the strongest French model: s1 +174, own +165, s2 −139 F-units against v7sq-dpc, cal +0.000166. The guarded labels added +70–85 units on both bases where tried.
- **Outcome:** This recipe underlies mixmdp's France (D-FRA-20). It was ported to the repo (`pseudo_guard.py`, `s2.py --pseudo-weight`, [commit 908f696]) and reproduces the labels exactly; the streaming copy `pl_lean.py` reproduces both v7ce3 label files row for row.
- **Hindsight:** The guards worked where raw round 2 did not (D-FRA-16).
- **Links:** [chat:ameya/agent-a4ea3fde 2026-09-27 10:43] · [chat:ameya/19e315ba 2026-09-27 10:44] · [chat:ameya/19e315ba 2026-09-27 13:09] · [RESEARCH_v6 §6.18](../../experiments/ameya/model-v1/RESEARCH_v6.md)

### D-FRA-19 · Keep the French acronym matches (no `noacr` upload): the size-bias test
- **When (IST):** 2026-09-27 09:30 (investigation starts) → 11:16 (raised) → 11:38 (decided) · **Phase:** P4 · **Area:** FRA / RUL
- **Decided by:** Ameya, on the agent for Ameya's report (the French error-population sub-agent abeb7453 raised it; the agent designed the deciding test)
- **Status:** adopted
- **Problem:** An acronym match is a record whose name is the initials of the S1's content words. France had 72.1 such predictions per 1000 S1 (18,707 pairs), against 5.2 true per 1000 in US/India (US 2.6, India 9.2) and 6.4 expected from French name shapes. If a share f were false, dropping all of them would be worth about +0.0028·f − 0.00095·(1 − f), which breaks even at f of about 25%, and is worth about +0.001 at f = 40%.
- **Options considered:**
  1. Drop all 18,707 (`noacr`): +0.001 to +0.002 if many are false, about −0.0003 if true.
  2. Drop only the 8,245 from S2, the most anomalous vendor (`noacr2`): 44% of French acronyms come from S2, against 25% in the US and 1% in India.
  3. Spend a France-only probe on `noacr`: settles it, but costs one of three slots.
  4. Keep them.
- **Choice and why:** Keep. Four checks were inconclusive: the count test, name-shape conditioning, the vendor split and the verbatim-address fingerprint. The labelled countries already differ 3.5 times from each other, so a country-specific vendor style was plausible. The deciding check is a new label-free test. If a record is a true copy of S1 x, then x was picked in proportion to its number of copies, so x's other copies follow a size-biased distribution. If the record is a planted extra, it attaches to any S1, singletons included. Fitting the number of other copies as (1 − f)·size-biased + f·ordinary by maximum likelihood gives the false share f.
- **Evidence:**
  - French acronym holders (17,917): f = 0.00 [0.00, 0.01]; from S2 (8,105) 0.00 [0.00, 0.06]; from S3 (10,218) 0.00 [0.00, 0.01]. A holder has no other copy 1.9% of the time, which matches true copies (1.9%), not extras (5.8%) [E].
  - Validation on the US/India holdout: true populations score −0.05 to 0.0; false candidates the model found plausible score 0.10–0.76 by address type (same address 0.47 [0.23, 0.73]); the French acronyms score −0.04 [E].
  - The sub-agent's independent count test: holders average 4.201 ± 0.011 against 4.36 if the acronyms were extras, 14 standard errors apart [E].
  - US/India acronym candidates are 99.7% true (1,440 of 1,444) [M].
- **Outcome:** `noacr` and `noacr2` were built and passed the validator at 11:20 but never uploaded; they would have cost about −0.0003. The same test flagged 592 French look-alike swaps, which were dropped (D-RUL-14). Every later package keeps the acronyms. "The 11x rate is a property of how French records were generated, not planted look-alikes."
- **Hindsight:** The test under-states f for false records that do not attach to random S1, so "0%" means "far below break-even", not exactly zero. It is also invalid for a population that takes most of an S1's copies. The final methodology keeps acronym joins, and nothing later contradicts this.
- **Links:** [RESEARCH_v6 §6.17](../../experiments/ameya/model-v1/RESEARCH_v6.md) · [chat:ameya/agent-abeb7453 2026-09-27 11:34] · [chat:ameya/19e315ba 2026-09-27 11:38] · [handover 2026-09-27_1228](../../docs/handover/2026-09-27_1228_ameya_final-day.md) · D-RUL-06 · [theory: evaluation methodology](../theory/05-evaluation-methodology.md)

### D-FRA-20 · A French decision layer on guarded round 2: mixmdp's France
- **When (IST):** 2026-09-27 13:30–16:40 · **Phase:** P4 · **Area:** FRA / DEC
- **Decided by:** Ameya (the France DP was designed by the error sub-agent for Ameya)
- **Status:** adopted. This is Composite B's France.
- **Problem:** France still used a flat threshold on its own pc, and the round-2 labels had drifted (D-FRA-16).
- **Options considered.** The France expected-F0.5 decision (`stack/dp_france.py`) applies the combo dynamic programme (shift 0.2, crowd shift −0.3, phantom 0.01) to a model's French stage-3 pc instead of a threshold, keeps the rule layer, removes look-alike swaps and never adds them. Adds / drops and conservative value on the public LB, by French base model [E]:

  | French base | adds / drops | value |
  |---|---|---|
  | v7sq | 276 / 1,199 | +13e-6 |
  | v7sq4 | 205 / 1,552 | +16e-6 |
  | v7sq6 | 436 / 272 | +15e-6 |
  | v7sqwg | 193 / 1,019 | +10e-6 |
  | v7xbag | 313 / 630 | +19e-6 |

  For v7sq6wg stage 3 had already chosen by expected F0.5, and the DP on top was −3, so it was not applied. Calibrated France value against v7sq-dpc (public LB units): v7sq7wg plus DP +0.000174, v7sq6w5 +0.000167, v7sq6wg +0.000166, v7sq6 plus DP +0.000121, v7sqwg plus DP +0.000104, v7sq4 plus DP +0.000088, v7xbag plus DP +0.000039. The France-heavy members (e5fr, bgefr; holdout band AUC 0.918–0.926) add nothing measurable.
- **Choice and why:** Upload mixmdp: US/India v7sq3-dpc; France v7sq7wg (v7sq6's four round-1 self-trained cross-encoders plus a France-heavy e5 `e5fr`; stage 2 on the guarded v7sq labels at weight 3), minus 454 look-alike swaps (D-RUL-14), plus the France DP (357 adds, 224 drops). Round-2 cross-encoder labels drift (v7sq5g is negative under every valuation), guarded stage-2 labels do not (D-FRA-18, D-FRA-22).
- **Evidence:** Public LB 0.990699 (rank 12), +0.000154 over v7sq-dpc (US/India +20e-6, France +134e-6) against +0.000234 predicted (US/India +0.00002, France model +0.000159, DP +0.000015, look-alike drop +0.00004) [M] [LB 2026-09-27 #03](../../submissions/records/2026-09-27_sub03.md). The `cal` estimate had given this France +146e-6.
- **Outcome:** Composite B's France. The shortfall of about 0.00008 was put down to `cal` error (about 0.00004) and the look-alike drop's size-bias value. The documentation counts the guarded second round with the French decision layers as +0.00015.
- **Hindsight:** After the 7B verdicts, a decoy-aware decomposition credited this France DP with +51e-6, where `cal` had seen +15e-6 (D-FRA-26).
- **Links:** [RESEARCH_v6 §6.18](../../experiments/ameya/model-v1/RESEARCH_v6.md) · [PR #65] · D-SUB-20

### D-FRA-21 · No French cross-encoder veto
- **When (IST):** 2026-09-27 13:49 · **Phase:** P4 · **Area:** FRA
- **Decided by:** agent for Ameya (analysis by the France-diff sub-agent)
- **Status:** rejected
- **Problem:** 368–373 French predictions are disliked by all four French self-trained cross-encoders (mean z-score below −0.5). Veto them?
- **Options considered:** Veto them, or keep them.
- **Choice and why:** Keep. Size bias says they are true copies: f = −0.04 [−0.24, 0.24] on one base and −0.07 [−0.27, 0.20] on the other, while the look-alike drops score 0.89 for comparison. The estimators gave −5.7 (s1) and −6.4 (s2) units; only the tiny "own" estimate (holdout truth 0.30, n = 10) was positive.
- **Evidence:** [E] [chat:ameya/19e315ba 2026-09-27 13:49].
- **Outcome:** No veto.
- **Hindsight:** unknown (none recorded).
- **Links:** D-FRA-19 · D-RUL-12

### D-FRA-22 · No round-2 self-training of the cross-encoders
- **When (IST):** 2026-09-27 13:56–13:57 · **Phase:** P4 · **Area:** FRA
- **Decided by:** agent for Ameya (proposed by: the France-diff sub-agent's ranking)
- **Status:** adopted (round 1 kept)
- **Problem:** Should the cross-encoders themselves be retrained on the round-2 (v7sq) labels?
- **Options considered:** 1. v7sq5g: the round-2 e5-large (`e5lsr2g`) in the mix. 2. A round-2 bge (`bgesr2g`). 3. v7sq5gwg: round-2 cross-encoders plus guarded labels at stage 2. 4. Keep the round-1 cross-encoders.
- **Choice and why:** Keep round 1. v7sq5g was negative for France under every valuation (s1 −6, own −13, s2 −53 units) and it reverted the v7nst → v7sq moves that the leaderboard had confirmed. Its US/India holdout was fine (stage 3 0.991247 [+0.000075, +0.000144]), so the damage was France-specific. The running `bgesr2g` and v7sq5gwg jobs were stopped and v7sq5g left v7xbag. Cross-encoder labels stay round 1 (`pseudo_fr_v7ce3`); guarded round-2 labels are used only at stage 2.
- **Evidence:** Valuations [E]; holdout [M] [RESEARCH_v6 §6.18](../../experiments/ameya/model-v1/RESEARCH_v6.md) · [chat:ameya/19e315ba 2026-09-27 13:56] · [13:57].
- **Outcome:** All later variants use round-1 cross-encoders. The agent warned Bakshi that his 7B trains on round-2 labels: "a single comparison, but worth knowing for his gA vs gC choice" [chat:ameya/19e315ba 2026-09-27 14:28].
- **Hindsight:** Bakshi's 7B, trained on round-2 labels, was a France tie in the mix (v7sqq7 +159e-6) but strong as a re-checker (D-LLM-05). The drift concern applied to mixing, not to re-checking.
- **Links:** D-FRA-18 · D-LLM-04

### D-FRA-23 · Synthetic French supervision: run it as a priority, correct the generator, do not upload
- **When (IST):** 2026-09-27 14:16 (Sachi) → 17:16–20:21 (Ameya's side) · **Phase:** P4 · **Area:** FRA / CE
- **Decided by:** Sachi proposed it; Ameya (as coordinator) prioritised it and then rejected it for the upload; the agent for Ameya and the France-diff sub-agent ran the checks
- **Status:** rejected for the upload; kept as an independent corroboration signal
- **Problem:** Self-training learns from its own decisions, so it reinforces confident French mistakes. "The only lever is a model trained with CORRECT French labels" (Sachi, PR #61).
- **Options considered:** 1. More self-training rounds. 2. Generate labelled French pairs from real French S1 text with the generator's measured operations, and train e5-large on real US/India band pairs plus synthetic French pairs (Sachi's `synth_fr.py` and `ce_synth.py`; gate: real-band holdout AUC of at least 0.9287).
- **Choice and why:** Ameya's session ran option 2 on Bakshi's idle GPUs as "the day's priority" (stopped there at 17:25 at the coordinator's request, then continued on Ameya's machines). A synthetic-versus-real comparison showed both generators mis-weighted France. Legal-form changes are 22.6% of real French copies against 3.2% in Sachi's generator; list appends, one-letter typos and acronyms are 10–14% synthetic against 1–2% real; about 30% of real non-matches are the same name elsewhere, which neither generator made; 32% of real addresses name a department, 0% synthetic. `synth_fr3.py` re-weighted them. Sachi's `ce_synth.py` crashed in `encode_synth` (`set_index` on a Series); `ce_synth2.py` fixed it.
- **Evidence:**
  - v7sqsyc (two synthetic cross-encoders, round-3 labels), packaged as mixf3: `cal` +249e-6, but own-cal +51 against +127 for v7sq6r3, and it reverses 1,182 leaderboard-confirmed moves (v7sq6r3: 927) [E].
  - v7sqsyd (all six synthetic cross-encoders): `cal` +293, own-cal +3, reverts 1,576 leaderboard-confirmed moves, US/India holdout −43e-6 [E] ([issue #64]).
  - "Synthetic cross-encoders raise cal by reverting what the leaderboard confirmed."
- **Outcome:** Not in Composite B. mixf3 stayed a high-variance option; mixf5 and mixf8 were never uploaded. The synthetic models are credited as a corroboration of the 7B drops (D-FRA-25) and as a diagnosis of how French copies differ from US/India ones.
- **Hindsight:** The "correct labels" idea was right in principle, but the generator needed real-French operation rates, which the team measured only at 17:20 on the last day. The caution was justified: an hour later the leaderboard showed that `cal` overvalued French changes (D-FRA-26).
- **Links:** [PR #61] · [issue #63] · [issue #64] · [PR #65] · [PR #67] · [synth_fr.py](../../experiments/sachi/synth_fr.py) · [ce_synth.py](../../experiments/sachi/ce_synth.py) · D-FRA-05

### D-FRA-24 · Round 3 as a candidate; round 4 not used
- **When (IST):** 2026-09-27 16:36–18:05 (round 3) · 20:09–20:11 (round 4 weighed) · **Phase:** P4 · **Area:** FRA
- **Decided by:** agent for Ameya (round 3 as a candidate); Ameya, Bakshi and Sachi on issue #64 (no round 4); the leaderboard judged round 3
- **Status:** round 3 adopted as a candidate (v7sq6r3; packages mixq and mixqc), then rejected by the leaderboard in mixf7; round 4 rejected
- **Problem:** The self-training gains were halving each round, but the teacher was now confirmed better by the leaderboard.
- **Options considered:** Round 3 with cmq6 (v7sq6r3); round 3 with cmq7 (v7sq7r3); skip round 3; later, round 4 (v7sq6r4).
- **Choice and why:** Round 3 on cmq6: "every self-training round so far paid on the leaderboard". It mirrors round 2: `pseudo_labels.py` run on mixmdp's French decisions, then `pseudo_guard.py`, weight 3. v7sq7r3 was skipped at 17:13 to free the laptop. Round 4 changes 3,553 of 1.43M labels; `cal` +212e-6 against round 3's +215e-6, so it "adds nothing", and a corrected-label round 4 (the 859 7B rejects as y = 0) scored −44e-6 by 7B-cal. "One more self-training round is a risk out of distribution" (Bakshi's LOCO ladder, `loco.py --self-train 3`: with features in distribution 0.96106 → 0.9637 → 0.96479 → 0.96498; out of distribution, like France, 0.88235 → 0.8512 → 0.83075 → 0.82307; Sachi raised it on the issue).
- **Evidence:**
  - Labels before the guard: 864,109 positive, 540,977 negative, 24,580 unlabelled (rule adds 285, acronym 807, op-B drops 68); after the guard about 863k, 523k, 43k [M, counts]. `cal` +215e-6 for v7sq6r3 against v7sq-dpc, about 0.99076 predicted [E]. The DP on top was negative (555 adds, 41 drops, `cal` −4.6 units).
  - Leaderboard: mixf7 (Composite B with v7sq6r3's France) 0.990833, −46e-6 against Composite B, where `cal` had predicted +69e-6 [M] [LB 2026-09-27 #05](../../submissions/records/2026-09-27_sub05.md).
- **Outcome:** Round 3 lost on the leaderboard. The decoy-aware decomposition: Composite B's France carries the French decision layer (+51e-6) and the look-alike treatment; mixf7's France did not. The round-3 model itself was +24e-6 better on 7B-scored pairs. The methodology: "Self-training helped for two rounds, and a third did not add to them."
- **Hindsight:** mixf7 changed two things against Composite B (round-3 model, no French decision layer), so the upload showed that round 3 without the decision layer loses, not that round 3 alone hurts. `mixfq` (round 3 with B's treatment) would have tested it; it was never uploaded (bias-corrected estimate about −33e-6). The methodology's sentence is a fair summary of the evidence only with that caveat.
- **Links:** [RESEARCH_v6 §6.19, §6.20](../../experiments/ameya/model-v1/RESEARCH_v6.md) · [handover 2026-09-27_2014](../../docs/handover/2026-09-27_2014_ameya_final-upload.md) · [FINAL_PUSH_PLAN §2](../../experiments/bakshi/box/FINAL_PUSH_PLAN.md) · D-SUB-22 · D-SUB-24

### D-FRA-25 · No drops on the synthetic-data detectors; the bge detector kept as corroboration
- **When (IST):** 2026-09-27 19:25–21:05 · **Phase:** P4 · **Area:** FRA
- **Decided by:** agent for Ameya
- **Status:** rejected as a drop source; the bge detector kept as corroboration only
- **Problem:** Could a cross-encoder trained on synthetic French copies find decoys that the 7B missed?
- **Options considered:** 1. An e5-base detector (`cesyoob`). 2. A bge detector (`cesyoobg`), alone or united with the 7B. 3. The bge detector's own 329 extra French flags (probe mixf7b).
- **Choice and why:** e5-base: no drops at all until logit −5, where 33 of 39 holdout drops were true, and it flagged 7,263 French pairs: badly miscalibrated on France [M]. bge: at logit −8, 15 holdout drops (2 true), +0.000021; 708 of its 1,037 French flags overlap the 7B's 859, so it flags 82% of the 7B drops [M]. Its 329 extra flags are the same street with a different house number; on the labelled holdout, kept pairs of that kind are 99.7% true (n = 32,786), so they are real copies, and mixf7b was withdrawn [M].
- **Evidence:** [chat:ameya/19e315ba 2026-09-27 19:25] · [20:20] · [21:04] · [21:05].
- **Outcome:** No detector drops in any upload. The overlap became the "independent model agrees" argument in the methodology.
- **Hindsight:** Synthetic training data did not transfer as a calibrated detector, but it worked as a second opinion.
- **Links:** D-FRA-23 · D-LLM-05

### D-FRA-26 · After the verdicts: distrust pc-based French estimators
- **When (IST):** 2026-09-27 17:03 (first backtest) → 20:50–23:40 (decomposition after the uploads) · **Phase:** P4/P5 · **Area:** FRA / EVL
- **Decided by:** Ameya (captain); analysis by the France-diff sub-agent and the main-session agent for Ameya
- **Status:** adopted
- **Problem:** France has no labels, so every French candidate was valued by an estimator. Why did round 3 lose when every estimator favoured it, and which estimators can be trusted?
- **Options considered:** The estimators in use. `cal`: the new model's pc, calibrated on the US/India holdout and applied to the French changes. `s1`: right shape, but under-predicts by about 20%. `s2`: the old model's pc taken as truth. `own-cal`. The rule-population AUC. The size-bias test. The `fhs` COPY count. 7B-cal: US/India holdout truth by 7B-logit band, applied to 7B-scored pairs.
- **Choice and why:** "After the 7B drops, pc-cal alone cannot rank French models. Use the 7B's own logit on the changed pairs, and prefer LB evidence." In practice: require agreement of the estimators and the leaderboard-confirmed direction before spending a slot.
- **Evidence:**
  - Backtest on every leaderboard pair [E/M]: `cal` tracks best (scale 0.96, mean absolute error 42e-6, correlation 0.98); `s1` under-predicts by about 20%; `s2` had the wrong sign on every pair; rule-only changes are undervalued.
  - After the 7B verdicts [E]: mixmdp's France DP carried +51e-6 (pc-cal saw +15e-6); the round-3 model itself was +24e-6 better on scored pairs; the look-alike drop was about neutral (leaderboard residual +18e-6; no pair was 7B-scored). The pc-based estimators value putting back the 7B-rejected French decoys at +49 to +65e-6, which the leaderboard contradicted, and were 53–98e-6 too optimistic for the round-3 family.
  - Checked and not used [E]: corrected-label round 4 (−44e-6 by 7B-cal); a 3-adapter 7B ensemble; US/India hybrids of g1w and v7sq3; a pc-times-7B recall rule (+13 to +18e-6 in one half only); the bge detector's extra flags; mixfq (nominal +20, bias-corrected about −33); a more inclusive France DP at shift 0.5 and 0.8 (ranges −10 to +16 and −38 to +30).
- **Outcome:** No switch away from Composite B on estimator evidence (D-SUB-25). The final methodology: "on a country without labels, any estimate built from the model's own probabilities needs an independent check, because it shares the model's blind spots."
- **Hindsight:** The estimators fail in one direction: decoys that the model accepts with confidence are valued as true. The earlier version of the same lesson is D-FRA-07, and the rule-population AUC cannot judge self-trained models because their pseudo-labels contain those populations (D-FRA-14).
- **Links:** [RESEARCH_v6 §6.18, §6.20](../../experiments/ameya/model-v1/RESEARCH_v6.md) · [chat:ameya/agent-a2762d22 2026-09-27 17:03] · [chat:ameya/agent-a2762d22 2026-09-27 22:31] · D-RUL-16
