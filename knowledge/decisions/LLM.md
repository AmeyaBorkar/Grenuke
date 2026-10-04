# Decisions: LLM (the Qwen2.5-7B re-check of confident predictions)

**Summary.**
- A large language model was first dismissed (26 Sep), then prompted cold and quickly fine-tuned (27 Sep midday), and both failed: AUC (how well a score ranks true pairs above false ones; 0.5 is chance) was 0.537 and 0.720, against 0.898 for our own pair probability pc. It worked once Bakshi trained it properly: Qwen2.5-7B (7.6B parameters, Apache-2.0), fine-tuned with LoRA (small adapter matrices) on the French self-training labels, using the LoRA script that Sachi wrote for Qwen2.5-1.5B.
- It was used in two ways. Counted twice among the cross-encoder scores that feed the stage-2 model (the mix called g1w) it added +0.000066 on India (P 0.998). As a re-check of the 94.5% of final predictions that no cross-encoder (a text model that reads both records together) ever reads, dropping pairs it scores below logit −6 (its raw score) removed 840 French and 310 US/India pairs; Composite B gained +0.000180 on the public leaderboard (LB).
- It was never used to add matches (best precision 71%, below the 72-77% an added pair needs), and widening the drop (three adapters, inside the band, down to −2) tied or lost.

## Index

| ID | decision | when (IST) | status |
|---|---|---|---|
| D-LLM-01 | A large LLM judge: "not worth it in 40 hours" | 2026-09-26 02:58 | superseded by D-LLM-04 |
| D-LLM-02 | Zero-shot Qwen2.5-7B-Instruct on the uncertain pairs | 2026-09-27 11:57 | rejected |
| D-LLM-03 | A quick LoRA fine-tune of Qwen2.5-7B-Instruct as a re-scorer | 2026-09-27 12:03 | rejected |
| D-LLM-04 | Train a 7B properly (Bakshi's q7st) instead of prompting one | 2026-09-27 14:30 | adopted |
| D-LLM-05 | The 7B re-check: drop confident out-of-band predictions below logit −6 | 2026-09-27 18:05 | adopted |
| D-LLM-06 | Gate the drop on the 7B, not on the pattern "same name + same number + different street" | 2026-09-27 18:48 | adopted |
| D-LLM-07 | Apply the same drop to US/India | 2026-09-27 19:12 | adopted |
| D-LLM-08 | No 7B-driven additions | 2026-09-27 19:24 | rejected |
| D-LLM-09 | Count the 7B twice in the stage-2 mix (g1w) | 2026-09-27 20:06 | adopted |
| D-LLM-10 | No three-adapter 7B ensemble and no in-band extension of the drop | 2026-09-27 20:55 | rejected |

Related records: how the 7B parts entered the uploads is D-SUB-21, D-SUB-23 and D-SUB-26; the synthetic-data detector that agreed with the 7B is D-FRA-25; the rejected recall rules are D-RUL-17. The cross-encoder training itself is in area CE.

## Records

### D-LLM-01 · A large LLM judge: "not worth it in 40 hours"
- **When (IST):** 2026-09-26 02:58 · **Phase:** P2 · **Area:** LLM / CE
- **Decided by:** agent for Ameya (recommendation, research session)
- **Status:** superseded by D-LLM-04 (reversed by events)
- **Problem:** Ameya asked which model-level levers could close France's gap with 40 hours left.
- **Options considered:** A, a multilingual word bridge that maps French words to English look-alike odds (e5 or LaBSE), called the "best option". B, a bigger cross-encoder (bge-reranker-v2-m3, 568M, Apache-2.0, or mdeberta-v3-base, MIT), "maybe". C, a 7–8B LLM judge (Qwen2.5-7B or Qwen3-8B): "uncalibrated, slow on a 12 GB laptop GPU … not worth it".
- **Choice and why:** C was dropped for the laptop's limits. Licence note: "Qwen2.5-3B is not Apache, although 0.5B, 1.5B and 7B are."
- **Evidence:** [R] the recommendation of a parallel research session of Ameya's [chat:ameya/19e315ba 2026-09-26 02:58].
- **Outcome:** Reversed within a day. Sachi started a LoRA cross-encoder on Qwen2.5-1.5B on a rented RTX 4090 at 17:59 on 26 Sep, using her new script `ce_llm.py`. Its self-trained version `qst` entered v7sq (which scored 0.990545), and Bakshi trained Qwen2.5-7B and Qwen3-4B on 27 Sep (D-LLM-04). Option A was never built; the label-free proxy odds served instead (D-FRA-03).
- **Hindsight:** Rented H100 and 4090 boxes removed the laptop constraint, and cross-encoder diversity proved to be the lever for France [RESEARCH_v6 §6.13](../../experiments/ameya/model-v1/RESEARCH_v6.md). The 1.5B `qst` has holdout band AUC 0.9381 and a correlation of 0.943 with e5-large; adding it to the mix moved US/India by +0.000011 and gave the best French copy count of the candidates [M] [RESEARCH_v6 §6.16].
- **Links:** [handover 2026-09-26_1800](../../docs/handover/2026-09-26_1800_sachi_llm-cross-encoder.md) · [ce_llm.py](../../experiments/sachi/ce_llm.py) · [ce_llm_st.py](../../experiments/ameya/model-v1/ce_llm_st.py) (imports Sachi's script unchanged) · [theory: LLM verification and compute](../theory/10-llm-verification-and-compute.md)

### D-LLM-02 · Zero-shot Qwen2.5-7B-Instruct on the uncertain pairs
- **When (IST):** 2026-09-27 11:57 (started) → 12:16–12:17 (closed) · **Phase:** P4 · **Area:** LLM
- **Decided by:** agent for Ameya
- **Status:** rejected
- **Problem:** Find a new, independent signal for the pairs the pipeline is unsure about, "only after it proves it improves decisions on the US/India holdout".
- **Options considered:** 1. Zero-shot "same business?" yes/no logit margin from Qwen2.5-7B-Instruct (Apache-2.0, 7.6B) on pairs with 0.05 ≤ pc < 0.995. 2. A fine-tune (D-LLM-03). 3. Nothing.
- **Choice and why:** Test option 1 first because it was quick and independent. It was near chance. The agent's reading: the model "lacks knowledge of this dataset's conventions".
- **Evidence** [M], 113,857 pairs (44,866 holdout, 53.5% true; 68,991 France) scored in 783 s on an H100:
  - AUC 0.537 against pc's 0.898; correlation with logit(pc) 0.133.
  - A cross-validated blend gave it a weight of 0.002 (blend AUC 0.8979; log-loss 0.3898 against 0.3894 for pc alone).
  - Every threshold flip lost holdout F0.5; at a threshold of 0.7, −18.2e-6 [−36.0, −0.8].
- **Outcome:** Closed at 12:17.
- **Hindsight:** An LLM did matter in the final, but as a supervised, self-trained 7B cross-encoder (D-LLM-04), not zero-shot.
- **Links:** [chat:ameya/19e315ba 2026-09-27 12:16] · D-LLM-03

### D-LLM-03 · A quick LoRA fine-tune of Qwen2.5-7B-Instruct as a re-scorer
- **When (IST):** 2026-09-27 12:03 (queued) → 13:04 (closed) · **Phase:** P4 · **Area:** LLM
- **Decided by:** agent for Ameya
- **Status:** rejected
- **Problem:** A fine-tuned 7B might beat the pipeline on the uncertain pairs.
- **Options considered:** 1. A quick run: one LoRA pair classifier trained once on 80,000 labelled non-holdout cross-encoder-band rows (US/India), scored on the same 113,857 pairs. 2. A proper 3-fold run: about 5 GPU-hours plus about 2 h through the pipeline, which "cannot meet the deadline" (13:42).
- **Choice and why:** The quick run first. It reached AUC 0.720 against pc's 0.898, a blend weight of 0.037 and an unchanged cross-validated blend AUC (0.8980). Every flip was negative or flat; at 0.7, −10.4e-6 [−29.2, +8.8].
- **Evidence:** [M] holdout, 3,750 steps on 80k rows [chat:ameya/19e315ba 2026-09-27 13:04].
- **Outcome:** Closed. The GPU went to the round-2 e5 retrain and then to the bge folds.
- **Hindsight:** Bakshi's properly trained, 3-fold, self-trained 7B reached holdout band AUC 0.9436 (D-LLM-04). "The 7B doesn't help" was true of an under-trained run, not of the model.
- **Links:** D-LLM-02 · D-FRA-22

### D-LLM-04 · Train a 7B properly (Bakshi's q7st) instead of prompting one
- **When (IST):** 2026-09-27 ~14:30 (plan) → 17:10 (first holdout AUC) · **Phase:** P4 · **Area:** LLM / CE
- **Decided by:** Bakshi (with his agent)
- **Status:** adopted
- **Problem:** After 0.990545 the candidates agreed with v7sq-dpc on 99.92–99.97% of predictions, and every cross-encoder saturated at a holdout band AUC of 0.938–0.944. More small encoders barely moved France (v7sq4 changes only 10.9 per 1000 French S1, at most +0.00017). The records carry only name, address and country, so no unused field was left. Bakshi's plan: "Pull the one lever never tried: model scale."
- **Options considered:**
  1. Zero-shot or quickly tuned prompting (D-LLM-02, D-LLM-03): failed.
  2. Qwen2.5-7B (Apache-2.0, 7.6B), LoRA, the `ce_llm_st.py` recipe trained on the v7sq-dpc teacher's French pseudo-labels, one out-of-fold group per GPU (chosen as the main bet).
  3. Qwen3-4B-Base (Apache-2.0, 4.0B), a second big member if it could finish by 17:45.
  4. Cheap fillers: gte-multilingual-reranker-base (0.3B, Apache-2.0) and mdeberta-v3-base (0.28B, MIT).
- **Choice and why:** Option 2, within the licence rule (MIT or Apache-2.0, at most 8B parameters, no external data). Option 3 was trained and merged (`q34st`) but used in no mix; its only use was as an agreement signal in B7 (D-SUB-26). Bakshi's forecast: central estimate about 0.9909; a new best above 0.990545 about 2 in 3; 0.991 or more about 1 in 3.
- **Evidence:** `q7st` holdout band AUC 0.9436, out-of-fold 0.9396, against e5ls 0.9439 and `qst` (Qwen2.5-1.5B) 0.9381 [M]. It is not stronger on US/India; its value is diversity and French re-scoring. Cost: three 80 GB GPUs for about 2 hours, or about 6 on one [R]. Resumable checkpoints and a backup every 5 minutes let the run survive a taken-away interruptible box.
- **Outcome:** Used three ways: in the stage-2 mix (D-LLM-09), as a re-check (D-LLM-05), and for recall, which was rejected (D-LLM-08).
- **Hindsight:** The 7B is no more accurate than a self-trained e5-large (both 0.944). It earns its place by diversity and by being an independent reader of confident pairs. Credit: Sachi's `ce_llm.py` LoRA script and Qwen2.5-1.5B run; the `ce_llm_st.py` self-training wrapper in Ameya's model folder, which imports her script unchanged; Bakshi's one-group-per-GPU training (`llm_group.py`, `llm_merge.py`), the 7B run itself and the re-check.
- **Links:** [FINAL_PUSH_PLAN](../../experiments/bakshi/box/FINAL_PUSH_PLAN.md) · [handover 2026-09-27_2006](../../docs/handover/2026-09-27_2006_bakshi_final-push.md) · [FINAL_PUSH_RESULTS §1](../../experiments/bakshi/box/FINAL_PUSH_RESULTS.md) · [handover 2026-09-27_1228](../../docs/handover/2026-09-27_1228_ameya_final-day.md)

### D-LLM-05 · The 7B re-check: drop confident out-of-band predictions below logit −6
- **When (IST):** 2026-09-27 18:05 (Bakshi's plan) → 18:40–18:47 (Ameya's agent re-checks) → 19:47 (rule) · **Phase:** P4 · **Area:** LLM
- **Decided by:** Bakshi (rule and threshold). The agent for Ameya re-checked it, extended it to US/India (D-LLM-07) and explained what it catches (D-LLM-06); Ameya as captain used it in the uploads.
- **Status:** adopted in all countries (mixqq, mixf1–mixf7, Composite B, B7)
- **Problem:** 94.5% of final predictions have p1 above 0.99 (p1 is the stage-1 probability), so no cross-encoder ever read them. The cross-encoders only see the uncertain band, pairs with 0.02 ≤ p1 ≤ 0.99, which is 1.49M test pairs. An error among the confident predictions is invisible to the band models. France has no labels, and its generic-name decoys were accepted with confidence. Bakshi's 7B flagged 859 confident French predictions, 0.10% of them and about 25 times the holdout rate.
- **Options considered:**
  1. Ignore the flags.
  2. Drop the flagged pairs, with the threshold chosen on labelled US/India data (chosen). Candidates: drop when the 7B logit is below t, for t from −8 to 0, on predicted pairs outside the band; in-band drops; two-model agreement.
  3. Reassign each flagged record to another S1 with the same generic name: a wrong pair would become a right one, doubling the gain if the record were a real copy elsewhere.
  4. Drop on the pattern alone (same name and number, different street), without the 7B.
- **Choice and why:** Option 2 with t = −6, fixed on labelled data before any French use: score the pairs with `q7st`'s adapter 0 and choose t on labelled holdout S1 that no adapter trained on. t = −6 has the largest gain and is positive in both fixed halves; −5 gains less, −4 has a negative half, −3 and looser lose. Under F0.5 a drop pays whenever more than about 25% of the dropped pairs are false. The 68 drops that empty an S1 were the riskiest (a real copy dropped scores that S1 zero; a truly empty S1 predicted empty scores one) and were 84% the same pattern. Option 3 failed: only 4 of the 859 had another same-name S1 at the record's street and house number, so they are decoys, not copies of another S1. Option 4 failed: on US/India the same pattern is 99.7% true when our model keeps the pair, so the 7B is what separates the cases (D-LLM-06).
- **Evidence:**
  - Holdout sample of 186,897 S1 (34%) [M]: t = −6 drops 24 pairs, 2 of them true, +33e-6 (halves +22e-6 and +43e-6); 3,000 random 25% subsets are positive in 99.7% (mean +32.8e-6, sd 16.7e-6). On the whole holdout (Ameya): −6 +37e-6, −5 +29e-6, −4 +17e-6.
  - Truth by logit bucket on the sample [M]: below −6 is 8.3% true, −6 to −4 86.3%, −4 to −2 94.9%. On the whole holdout 16 of the 80 pairs rejected at −6 are real (20%), still far below break-even.
  - Leakage check [M]: adapter 0 trained on French thirds 1–2, yet the drop rate is 0.112%, 0.108% and 0.107% across the three thirds, with median logit 9.6 in each.
  - On test: 859 French predictions (0.10%) and 310 of 4.74M US/India predictions (0.0065%), 15–25 times fewer outside France.
  - A bge detector trained on synthetic French data, with no self-training labels, flags 708 of the 859 (82%) [M] (D-FRA-25).
- **Outcome:** Composite B dropped 840 French and 310 US/India pairs and scored +0.000180 over mixmdp against +149e-6 predicted [M] [LB 2026-09-27 #04](../../submissions/records/2026-09-27_sub04.md). (The French count differs by base model: 859 flagged on the scored set, 832 in mixf2, 840 in Composite B; the sources do not itemise the gap.) The French drops are estimated at about +0.00011 to +0.00014 of that [E]. B7, which pushed the French drop toward −2 where Qwen3-4B agrees, tied at 0.990875 and so confirmed −6 [LB 2026-09-27 #07](../../submissions/records/2026-09-27_sub07.md).
- **Hindsight:** The most effective French change of the final day came from an independent model reading pairs that the pipeline was sure about; it reversed the plan's "no LLM judge" in a narrow, affordable form. Running the 7B on everything was ruled out by a compute estimate, not a measurement: at the roughly 600 pairs per second seen on an H100, the 58M test pairs would take about 27 GPU-hours before any training. The re-check itself needs about 4 GPU-hours. The sample figure "8% true" is for the 34% sample; the whole holdout gives 20%.
- **Links:** [rescore_eval.py](../../experiments/bakshi/box/rescore_eval.py) · [score_pairs.py](../../experiments/bakshi/box/score_pairs.py) · [resample_drop.py](../../experiments/bakshi/box/analysis/resample_drop.py) · [leak_by_third.py](../../experiments/bakshi/box/analysis/leak_by_third.py) · [chat:ameya/19e315ba 2026-09-27 18:40] · [chat:ameya/19e315ba 2026-09-27 19:05] · [issue #64] · [PR #62] · [theory: LLM verification and compute](../theory/10-llm-verification-and-compute.md)

### D-LLM-06 · Gate the drop on the 7B, not on the pattern "same name + same number + different street"
- **When (IST):** 2026-09-27 18:48 → 19:52 → 20:00 · **Phase:** P4 · **Area:** LLM / FRA
- **Decided by:** Ameya (correction), corroborated by Sachi; Bakshi updated his write-up
- **Status:** adopted
- **Problem:** Bakshi's results note first said this pattern is "not an error pattern": 100% true among US/India predictions, and the 7B rejects only 0.55–2.5% of the French ones. Ameya found that 78% of the 7B's French rejects are this pattern, against 0.2–3% in every other bucket, and by eye about 34 of 40 random ones are different businesses ("lille ecole sarl | 42 rue gutenberg" against "lille ecole sarl | 42 q. du wault").
- **Options considered:** 1. Drop on the pattern alone. 2. Ignore the pattern. 3. Drop only where the 7B rejects (chosen).
- **Choice and why:** The pattern is both a copy pattern and a decoy pattern, and the 7B separates the two. On the labelled holdout, predicted pairs with the pattern (380) are 99.7% true, with 7B median +7.9 and none below −6; pairs the model rejected (218) are 0.5% true, median −9.9, 202 below −6. French names are generic (a median of 43 same-name S1 per rejected pair), so in France the decoys pass stage 1 at p1 above 0.99. Sachi's `street_swap.py`: the pattern is 99.9% true where the model keeps it (23.2 per 1000 S1), "so gating the drop on the 7B (not the pattern alone) is the right design".
- **Evidence:** [M, holdout] [issue #64] · [PR #62]. A bge reranker trained on US/India labels plus synthetic French data, with no self-training labels, flags 708 of the 859 French 7B rejects (82%) [M].
- **Outcome:** The drops went into mixf2, Composite B and B7. The decoy table became a figure-level argument in the methodology document.
- **Hindsight:** The same pattern has opposite truth depending on whether the model kept the pair, so only a reader that separates the two cases is safe to drop on.
- **Links:** [street_swap.py](../../experiments/sachi/street_swap.py) · [FINAL_PUSH_RESULTS §6](../../experiments/bakshi/box/FINAL_PUSH_RESULTS.md) · D-LLM-05

### D-LLM-07 · Apply the same drop to US/India
- **When (IST):** 2026-09-27 19:12–19:34 · **Phase:** P4 · **Area:** LLM
- **Decided by:** agent for Ameya (the scoring run by Bakshi)
- **Status:** adopted (mixf2 onward, Composite B)
- **Problem:** The rule had gained on the labelled holdout, which is US/India, but the test-side US/India confident pairs had not been scored.
- **Options considered:** 1. France only. 2. All countries.
- **Choice and why:** All countries. The holdout gain is measured exactly where it is applied. The 310 test drops (India 204, US 106) are about 1.6 times the holdout rate, consistent with the extra look-alike decoys in test. A sample read mostly as decoys (word swaps, a different city, one-digit number changes), with a few real copies ("thompson and davidson llc" against "… inc").
- **Evidence:** Holdout +0.000033 in both halves [M]; on the full holdout later +0.000037, of which US +0.000018 and India +0.000018 [M] [chat:ameya/19e315ba 2026-09-27 23:21].
- **Outcome:** In Composite B.
- **Hindsight:** Confirmed by the full-holdout run.
- **Links:** [chat:ameya/19e315ba 2026-09-27 19:31] · [chat:ameya/19e315ba 2026-09-27 19:34] · D-LLM-05

### D-LLM-08 · No 7B-driven additions
- **When (IST):** 2026-09-27 19:24–19:35 (agent), evening (Ameya and Bakshi) · **Phase:** P4 · **Area:** LLM / RUL
- **Decided by:** Ameya and Bakshi
- **Status:** rejected
- **Problem:** Could the 7B also add missed pairs?
- **Options considered:** Add unpredicted candidates the 7B accepts, scoring those whose record no S1 owns; a two-way rule (our stage-3 probability and the 7B both high); drops only (chosen).
- **Choice and why:** The best holdout precision of a 7B addition rule was 71%, below the roughly 75% an F0.5 addition needs at a typical S1 state: at logit above 4, 69 adds with 49 true (71.0%); at logit above 5, 42 adds with 30 true (71.4%). The two-way rule at pc of at least 0.5 and logit above 4 gave 30 adds at 66.7%, with halves −0.000014 and +0.000019.
- **Evidence:** [M, Ameya] [issue #64] · [COMPONENTS_FOR_DOC §D](../../experiments/bakshi/box/COMPONENTS_FOR_DOC.md) · [RESEARCH_v6 §6.19](../../experiments/ameya/model-v1/RESEARCH_v6.md).
- **Outcome:** The methodology states that "none of the recall rules we tried was more than 71% precise".
- **Hindsight:** unknown (none recorded).
- **Links:** D-RUL-17 · D-RUL-13

### D-LLM-09 · Count the 7B twice in the stage-2 mix (g1w)
- **When (IST):** 2026-09-27, first tested by 18:51; in the plan by 20:06–20:14 · **Phase:** P4 · **Area:** LLM / DEC
- **Decided by:** Bakshi (the variants and g1w); adopted by Ameya and the team
- **Status:** adopted (Composite B; US and India)
- **Problem:** The 7B is no more accurate than the smaller cross-encoders (band AUC 0.9436 against 0.9439 for e5ls). Could it still help stage 2 as one more, different voice?
- **Options considered.** Bakshi's variants, holdout macro F0.5 on US/India [M]:

  | variant | cross-encoder mix | F0.5 | against g0 |
  |---|---|---|---|
  | g0 | e5l, qst, e5ls, bge (v7sq reproduction) | 0.991261 | |
  | g1 | + q7st once | 0.991276 | +0.000015 |
  | g1w | + q7st counted twice | 0.991323 | +0.000062 |
  | g1x3 | + q7st counted three times | 0.991322 | +0.000061 (flat) |
  | g7only | q7st alone | 0.991286 | +0.000025 |
  | gbag | bag of g0, g1, g1w | 0.991313 | +0.000052 |

  Paired against g1w on India: g1x3 −13.5e-6 and g7only −70.3e-6. In the French mix the 7B was a tie (v7sqq7 +159e-6).
- **Choice and why:** g1w. The agent for Ameya rebuilt every model's decisions with the same production code and ran a paired bootstrap per country against v7sq3. India: +66.1e-6 [+19.4, +112.9], P 0.998, which survives a multiple-testing correction for about 8 sources times 2 countries. US: +26.2e-6, P 0.906, which fails it. No hybrid (only g1w's adds, only its drops, extra gbag pairs) beats full g1w.
- **Evidence:** [M] [chat:ameya/agent-a2762d22 2026-09-27 18:51] · [FINAL_PUSH_RESULTS §2](../../experiments/bakshi/box/FINAL_PUSH_RESULTS.md).
- **Outcome:** Composite B took both US and India from g1w, although the agent had recommended India only (D-SUB-21). The leaderboard later showed g1w's US at +14e-6 over v7sq3 (mixf2 against mixf7). The methodology reports "+0.000066 on India (P 0.998) and +0.000026 on the US (P 0.906, not significant)".
- **Hindsight:** The submission record says the holdout implied about +10e-6 for the US, against +26.2e-6 in the agent's bootstrap; the two figures use different comparisons and were not reconciled.
- **Links:** [handover 2026-09-27_2006](../../docs/handover/2026-09-27_2006_bakshi_final-push.md) · [LB 2026-09-27 #06](../../submissions/records/2026-09-27_sub06.md) · D-LLM-04

### D-LLM-10 · No three-adapter 7B ensemble and no in-band extension of the drop
- **When (IST):** 2026-09-27 20:55–20:56 (in-band); 21:34–21:40 (ensemble) · **Phase:** P4/P5 · **Area:** LLM
- **Decided by:** agent for Ameya
- **Status:** rejected
- **Problem:** Only adapter 0 of Bakshi's three out-of-fold 7B adapters had scored the pairs. Would all three, or drops inside the band, catch more decoys?
- **Options considered:** 1. A union of "adapter 0 below −6" and "all three adapters below −4". 2. The mean of the three below −5. 3. Extending the −6 rule to in-band predictions (p1 at most 0.99).
- **Choice and why:** The union gained +0.000038 against +0.000033 on the holdout sample [M], but its 88 extra French drops included garbled real copies ("ehpad de troisieme" against "chpad de troisieme", "ehpad aero" against "ehpaj aero sa"), and its US/India extras added only +0.000004 on 8 pairs. The adapters agree only moderately: correlation 0.403 between adapter 0 and each of the others [M]. In band, 3 holdout drops at −6 gave +0.000002 with the halves disagreeing [M]. The single-adapter −6 rule stays.
- **Evidence:** [chat:ameya/19e315ba 2026-09-27 20:55] · [20:56] · [21:39] · [21:40].
- **Outcome:** Rejected. Bakshi's B7 later pushed the French drop below −6 with Qwen3-4B agreement, for a tie (D-SUB-26). His other closed variants agree: drops at −4, −2 or 0 cost −0.000003 to −0.0032, the 7B weight at 3 times or alone was flat or lower than 2 times, a cross-fitted blend of all six cross-encoder logits plus pc scored band AUC 0.9575 yet lost 0.001 as a decision score, and a depth-5 tree mining extra drops failed on the held-out half.
- **Hindsight:** Fine: the extra drops hit exactly the garbled names that the documentation lists as a recall problem.
- **Links:** [FINAL_PUSH_RESULTS §6, §9](../../experiments/bakshi/box/FINAL_PUSH_RESULTS.md) · D-LLM-05
