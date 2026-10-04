# Decisions: CE (cross-encoders)

**Summary.**
- A cross-encoder is a transformer that reads the two records of a pair together and scores the pair. It is more accurate than comparing two separately computed embeddings, but costs one full pass per pair. We ran them only on the uncertain band (stage-1 probability p1 from 0.02 to 0.99, 1.49M of 58.4M test pairs) and gave stage 2 one z-scored mean of their logits (each model's score standardised on the training band, then averaged).
- Twenty-three decisions, in time order: why only the band, the licence screen (MIT or Apache-2.0, at most 8B parameters), the models (multilingual-e5 small, base and large; bge-reranker-v2-m3; Qwen2.5-1.5B and 7B with LoRA), the consensus mean, the gate for new members, and what we rejected (weight tuning, French-heavy members, synthetic French supervision).
- Scope: unless marked LB (public leaderboard), F0.5 means macro F0.5 on the local holdout (549,699 labelled US/India S1, no France). Band AUC is the AUC on labelled holdout pairs inside the band. Evidence levels: [M] measured, [E] estimated, [R] reported, [U] uncertain. Times are IST. 1e-6 means 0.000001 of F0.5.

## Index

| ID | decision | when (IST) | status |
|---|---|---|---|
| D-CE-01 | Cross-encoders only as a gated extra; no LLM judge, graph clustering or singleton model | 2026-09-25 14:15 | partly reversed |
| D-CE-02 | Read only the uncertain band with a cross-encoder | 2026-09-25 20:55 | adopted |
| D-CE-03 | Licence screen: MIT or Apache-2.0, at most 8B parameters, no external-data models | 2026-09-25 21:27 | adopted |
| D-CE-04 | First cross-encoder: multilingual-e5-small on the band [0.02, 0.99], as a stage-2 feature | 2026-09-25 21:45 | adopted |
| D-CE-05 | Keep the e5-small cross-encoder although it missed the gate bar | 2026-09-26 00:46 | adopted |
| D-CE-06 | Rent GPUs for stronger, more diverse cross-encoders (on demand, not spot) | 2026-09-26 16:29 | adopted |
| D-CE-07 | Larger multilingual cross-encoders on the band (v7ce3) | 2026-09-26 17:43 | adopted; superseded by D-CE-11 |
| D-CE-08 | Qwen2.5-1.5B (not 3B) with LoRA as an extra cross-encoder (Sachi) | 2026-09-26 17:59 | adopted |
| D-CE-09 | Add bge-reranker-v2-m3 after a licence check | 2026-09-26 19:48 | adopted |
| D-CE-10 | Averaging two e5-large runs into one feature (v7b) stopped | 2026-09-26 20:56 | rejected; the mean returned in D-CE-11 |
| D-CE-11 | One z-scored consensus mean instead of separate logits (v7m, then v7n) | 2026-09-26 20:57 | adopted |
| D-CE-12 | Qwen: pair separator, French self-training and a two-sided gate (`qst`) | 2026-09-26 23:39 | adopted |
| D-CE-13 | Skip optimizer steps with non-finite gradients | 2026-09-26 23:58 | adopted |
| D-CE-14 | Equal z-mean of diverse families; no weight tuning | 2026-09-27 01:42 | adopted |
| D-CE-15 | Gate every new cross-encoder on labelled US/India data and on decorrelation | 2026-09-27 01:50 | adopted |
| D-CE-16 | French self-trained cross-encoders in the mix: v7s, then v7sq as the first upload | 2026-09-27 02:45 | adopted |
| D-CE-17 | GPU plan for 27 Sep: weight the self-trained models; skip seeds, xlm-roberta-large and the 7B; stop the Qwen round-2 retrain | 2026-09-27 10:43 | partly adopted; the 7B skip superseded by D-CE-19 |
| D-CE-18 | French-heavy cross-encoders as extra members | 2026-09-27 14:09 | tried, dropped |
| D-CE-19 | Pull the model-scale lever: Qwen2.5-7B on rented boxes, gated by a reproduction check (Bakshi) | 2026-09-27 14:15 | adopted |
| D-CE-20 | Synthetic French supervision for cross-encoders | 2026-09-27 14:17 | rejected |
| D-CE-21 | Wire Bakshi's 7B (`q7st`) into our own pipeline | 2026-09-27 14:28 | adopted as a variant |
| D-CE-22 | Train on Ameya's band files; move logits by (s1, r) with a 99.5% coverage gate (Bakshi) | 2026-09-27 14:30 | adopted |
| D-CE-23 | Count the 7B twice in the stage-2 mix (g1w) | 2026-09-27 18:05 | adopted |

Related records: the French self-training these models fed is D-FRA-13, D-FRA-18 and D-FRA-22; synthetic supervision from the France side is D-FRA-23 and D-FRA-25; the French veto test is D-FRA-21; the 7B re-check of confident predictions is D-LLM-05; the rule built on cross-encoder disagreement is D-RUL-12; the stage that consumes the logits is in area MDL (D-MDL-03, D-MDL-16). Bakshi's 7B and its weight are also D-LLM-04 and D-LLM-09; the rented boxes are D-ORG-15 to D-ORG-17; the French yardsticks are D-EVL-11, D-EVL-12 and D-EVL-14; the first upload of 27 Sep is D-SUB-13.

## Records

### D-CE-01 · Cross-encoders only as a gated extra; no LLM judge, graph clustering or singleton model
- **When (IST):** 2026-09-25 14:15 · **Phase:** P0 · **Area:** CE / LLM
- **Decided by:** Ameya (FINAL_PLAN §12); Plan B (Sachi) on the caution about transformers
- **Status:** partly reversed. Cross-encoders became core from 26 Sep about 02:00; a Qwen2.5-7B classifier was added later as a re-check; no graph clustering was built; the singleton model was skipped.
- **Problem:** Scale: 23.7M records, about 10M of them in test, against a one-laptop budget.
- **Options considered:**
  1. An LLM judge.
  2. Full graph clustering.
  3. A singleton ("no match") model.
  4. Cross-encoders on the uncertain band only.
- **Choice and why:** The LLM judge and graph clustering are "too slow at this scale; competition + cluster support cover the useful part". Singletons (5.6% of S1) are left to the decision layer. Cross-encoders (e5-small; bge-reranker on 0.1 < p < 0.9 or the Indic slice) only as a Sunday extra worth +0.003 (gate G10). Plan B: transformers are weak at exact numbers, so a cross-encoder only for ambiguous Indic pairs.
- **Evidence:** planning statements [R] ([FINAL_PLAN §4.8, §12](../../plans/FINAL_PLAN.md), [Plan B](../../plans/sachi/PLAN.md)).
- **Outcome:** Cross-encoders became core (D-CE-05, D-CE-07). The Qwen2.5-7B came in as a classifier on a targeted set, not a generative judge (area LLM). A "no match" S1 model was considered and skipped at +0.0001 to +0.0003 (D-DEC-07).
- **Hindsight:** The constraint was compute, and rented H100s relaxed it (D-CE-06).
- **Links:** [FINAL_PLAN §4.8, §12](../../plans/FINAL_PLAN.md) · [Plan B](../../plans/sachi/PLAN.md) · D-DEC-07

### D-CE-02 · Read only the uncertain band with a cross-encoder
- **When (IST):** 2026-09-25 20:55–21:31 (research and sizing) · re-examined 2026-09-26 20:26 · **Phase:** P1 · **Area:** CE
- **Decided by:** agent for Ameya (proposed by: research agent a666ee54, after Ameya asked at 20:29 for research on better methods)
- **Status:** adopted (built from 23:28)
- **Problem:** Hand-made pair features plus XGBoost had reached 0.9844 (model v2). A text model could add signal on typos, transliteration and descriptor semantics, but scoring every retrieved pair (tens of millions) was out of reach on one 12 GB GPU.
- **Options considered** (the research agent's ranking):
  1. A cross-encoder with the GBDT features in its head, run only on the uncertain band and stacked into stage 2 out of fold. Foursquare 2022 (Kaggle) 1st place: 0.875 (GBDT) to 0.907 (mDeBERTa with features) to 0.911 (blend). The agent's own guess: +0.1 to +0.4 points of F0.5 for 3–6 GPU-hours.
  2. One model over each S1's whole candidate list (Foursquare 2nd place "transformer blocking"; a 13th-place GNN, LB 0.924 to 0.946). Less expected, because our rivalry features already cover part of it.
  3. An exact F-beta rule that models "no match" directly (GFM): minutes of CPU, 0 to +0.2 points.
  4. A look-alike stress test and a prior-shift check.
  5. A cross-script name model trained on our own train pairs.
- **Choice and why:** Option 1. The agent called the Foursquare evidence the strongest it found, and the band is small: (0.05, 0.95) holds only 1,001,351 train pairs (1.56%) but 4.74% of all positives. e5-small trains at about 1,757 pairs/s and infers at about 11,654 pairs/s on 4 GB: "A 3-model out-of-fold cross-encoder over ~1M uncertain pairs takes about 45 minutes of GPU time" [E]. The notes also said: score only the band, keep max_len at 64 or below, train on the GBDT survivors (hard negatives by construction). Cost warning: one Foursquare team needed 40 h per epoch on a V100 when it scored everything.
- **Evidence:**
  - Band sizes and throughput [M] [chat:ameya/19e315ba 2026-09-25 18:20] [chat:ameya/19e315ba 2026-09-25 21:30].
  - Re-check on 26 Sep 20:26 for the final band [0.02, 0.99]: 1,568,554 train and 1,490,930 test pairs, against 66.4M and 58.4M retrieval pairs. Holdout truth rate by p1: below 0.002, 0.03–0.06% true; 0.01–0.02, 1.4%; 0.99 and above, 99.98% [M].
  - France has about twice the band pairs per S1 (test, p1 0.02–0.99: about 1,485 per 1000 S1 against 682 US and 807 India; p1 0.05–0.99: about 1,040 against 360–420) [E], "so the cross-encoders decide a much larger share of French pairs" [RESEARCH_v6 §6.2](../../experiments/ameya/model-v1/RESEARCH_v6.md).
  - e5-large trains at about 925 pairs/s on an H100, so one pass over 58.4M pairs would take about 17.5 h (derived) [E].
- **Outcome:** The band design carried the whole cross-encoder line, from e5-small to e5-large, bge and Qwen2.5-1.5B and 7B. The methodology: XGBoost scores all 58M retrieved pairs, the cross-encoders "are affordable on the 1.49M pairs where that score is uncertain".
- **Hindsight:** Options 3–5 were never built as such. The lower edge 0.02 equals the candidate-cut floor, so pairs below it could not be predicted anyway [E]. At about 600 pairs/s, scoring all 58.4M test pairs with the 7B would take about 27 GPU-hours, so the 7B was used only on the band and on confident predictions (D-CE-19).
- **Links:** [ANALYSIS_v2 §3](../../experiments/ameya/model-v1/ANALYSIS_v2.md) · [chat:ameya/agent-a666ee54 2026-09-25 20:55] · [theory: transformers and cross-encoders](../theory/08-transformers-and-cross-encoders.md) · D-DEC-07

### D-CE-03 · Licence screen: MIT or Apache-2.0, at most 8B parameters, no external-data models
- **When (IST):** 2026-09-25 21:27–21:31 (first screen) · 2026-09-26 19:48 (bge, jina) · 2026-09-27 14:15 (7B and fillers) · **Phase:** P1–P4 · **Area:** CE
- **Decided by:** agent for Ameya (the research agent flagged licences; Sachi checked the Qwen sizes; Bakshi picked the 7B candidates). The rule itself comes from the competition and AGENTS.md.
- **Status:** adopted
- **Problem:** Only models licensed MIT or Apache-2.0 with at most 8B parameters may be used in the final pipeline, and no external data. Every candidate needed its licence read before use.
- **Options considered** (licence as read from the model card or the Hugging Face API):
  1. Allowed and used: multilingual-e5-small (MIT, 118M), -base (MIT, 278M) and -large (MIT, 560M); bge-reranker-v2-m3 (Apache-2.0, 568M); Qwen2.5-1.5B (Apache-2.0); Qwen2.5-7B (Apache-2.0, 7.6B).
  2. Allowed, tried or only noted: Qwen3-4B-Base (Apache-2.0, 4.0B); mdeberta-v3-base (MIT, 278M); gte-multilingual-reranker-base (Apache-2.0, 0.3B); LaBSE, Qwen2.5-0.5B, Qwen3-0.6B and 1.7B, Mistral-7B-v0.3 (all Apache-2.0); bge-m3 (MIT, no safetensors file).
  3. Rejected: Qwen2.5-3B (licence "other", not Apache-2.0); jina-reranker-v2-base-multilingual (CC-BY-NC); IndicXlit (MIT, but trained on external data, which the rules forbid).
- **Choice and why:** Read each licence before any use. Anything outside option 1 or 2 is not used. XGBoost is Apache-2.0.
- **Evidence:** [R] licence reads [chat:ameya/19e315ba 2026-09-25 21:31] [chat:ameya/19e315ba 2026-09-26 19:49]; [ANALYSIS_v3 §8](../../experiments/ameya/model-v1/ANALYSIS_v3.md) ("Qwen2.5-3B ('other') and jina-reranker-v2 (CC-BY-NC) are not" allowed); [decision model-v7n](../../docs/decisions/2026-09-26_2135_model-v7n.md) ("Models, all MIT/Apache-2.0 and ≤ 8B"); Sachi's note on 3B in [PR #46]; Bakshi's list in [FINAL_PUSH_PLAN](../../experiments/bakshi/box/FINAL_PUSH_PLAN.md).
- **Outcome:** Every model in the final pipeline is MIT or Apache-2.0 and at most 8B (methodology Table 3 and Appendix A).
- **Hindsight:** The 3B check mattered: a mid-sized Qwen would have been non-compliant.
- **Links:** [AGENTS.md hard rules](../../AGENTS.md) · [methodology Table 3](../../experiments/ameya/final-zip/doc/Documentation_template.md) · D-CE-08 · D-CE-09 · D-CE-19

### D-CE-04 · First cross-encoder: multilingual-e5-small on the band [0.02, 0.99], as a stage-2 feature
- **When (IST):** 2026-09-25 21:45 (band) · 23:28 (run) · **Phase:** P2 · **Area:** CE
- **Decided by:** agent for Ameya, from the research in ANALYSIS_v2 §3 (Foursquare-style cross-encoders on GBDT survivors)
- **Status:** adopted
- **Problem:** Typos, transliteration and brand or descriptor semantics are hard for string features. Scoring all 58M test pairs with a transformer on the 12 GB local GPU was out of reach.
- **Options considered:**
  1. Bands: [0.01, 0.995] (3.0M train pairs); [0.02, 0.99] (2.07M train pairs, holding 671k of 7.53M true pairs); [0.05, 0.98] (1.17M).
  2. Models: multilingual-e5-small against mdeberta-v3-base (both MIT).
- **Choice and why:** [0.02, 0.99] with e5-small, about 45 GPU-minutes. It is trained out of fold over the three stacking groups and written as `ce__logit` for stage 2, so the GBDT decides how much to trust it. Settings: input "name ; address" of both records, max_len 96, batch 128, 1 epoch, learning rate 5e-5, bf16, length-bucketed batches.
- **Evidence:** the built train band had 1,628,160 pairs (28.1% positive) and the test band 1,673,075; about 1,940 pairs/s; three groups in 2,295 s; OOF AUC 0.9244. On the holdout band the cross-encoder alone scored AUC 0.9278 while p1 scored 0.9315 [M] [chat:ameya/19e315ba 2026-09-26 00:09]. The options list gives 2.07M train pairs for the same band; the sources do not explain the gap with the 1.63M built [U].
- **Outcome:** v3ce, +0.00140 (D-CE-05). Rebuilt for v6all: OOF band AUC 0.9191, holdout 0.9240, against 0.9297 for p1.
- **Hindsight:** The cross-encoder alone was weaker than p1 inside its band; its value was complementary information. The later e5-large, bge and Qwen work built on this pattern: a band-only cross-encoder feeding a stacked GBDT.
- **Links:** [ANALYSIS_v3 §5](../../experiments/ameya/model-v1/ANALYSIS_v3.md) · [chat:ameya/19e315ba 2026-09-25 21:45] · [`ce.py`](../../experiments/ameya/model-v1/ce.py)

### D-CE-05 · Keep the e5-small cross-encoder although it missed the gate bar
- **When (IST):** 2026-09-26 00:46 (gate) → 02:07 (decision record, [PR #23]) · **Phase:** P2 · **Area:** CE / EVL
- **Decided by:** Ameya (proposed by: agent for Ameya, recorded as "proposed"; "the captain decides with the leaderboard"; Ameya merged [PR #23])
- **Status:** adopted
- **Problem:** Gate G10 measured v3ce against v3 at +0.00140 [0.00131, 0.00148]. The gate script's `min_gain` of 0.002 set "keep: false", and the decision record cites a +0.003 bar for heavy components.
- **Options considered:**
  1. Drop the cross-encoder (about 45 GPU-minutes less).
  2. Keep it for France.
- **Choice and why:** Keep. It "halves French look-alike acceptances" (the uncertain share of French predictions 9.0% to 6.2%; pattern A, number moved plus legal form added or changed, 0.047 to 0.023 per S1). It raises singleton F0.5 from 0.9913 to 0.9974, and stage-2 log-loss falls from 0.044 to 0.039. The holdout cannot see France, so "the cross-encoder moves France toward the US/India profile, and the leaderboard gain should be larger than +0.0014".
- **Evidence:** v3 to v3ce holdout 0.98882 to 0.99021, +0.00140 [0.00131, 0.00148] (India +0.00178, US +0.00114); precision and recall 0.99833 and 0.96893 to 0.99868 and 0.97221; French predictions per S1 3.539 to 3.470, S1 left empty 4.4% to 5.1% [M] ([ANALYSIS_v3 §5](../../experiments/ameya/model-v1/ANALYSIS_v3.md)). The e5-small model is MIT, 118M.
- **Outcome:** The cross-encoder stayed in every later model. v3ce itself was never uploaded, so the France argument was not tested on its own; the cross-encoder line later gave the largest LB step (v6all to v7n, +0.001112).
- **Hindsight:** The clearest case of a reason outside the holdout (France) overriding the holdout bar. The exception was written down with its reason, and the leaderboard later confirmed it.
- **Links:** [decision model-v4](../../docs/decisions/2026-09-26_0207_model-v4-france-and-cross-encoder.md) · [PR #23] · [chat:ameya/19e315ba 2026-09-26 00:46] · D-CE-04 · D-CE-07 · D-EVL-03

### D-CE-06 · Rent GPUs for stronger, more diverse cross-encoders (on demand, not spot)
- **When (IST):** 2026-09-26 16:29 (plan) · 23:08 (after v7n's leaderboard proof) · **Phase:** P3 · **Area:** CE / ORG
- **Decided by:** Ameya (credits and rentals); agent for Ameya (specifications); the main session ran the box
- **Status:** adopted
- **Problem:** The only GPU-bound component was the cross-encoder, and the 12 GB laptop GPU limited model size. French errors are about meaning ("club" against "comité"), which word odds derived from train cannot know.
- **Options considered:**
  1. AWS g6e.xlarge or g6e.2xlarge (L40S, 48 GB); the GPU quota is often 0 on a new account.
  2. Vast.ai: A100 80 GB at up to $1.30/h, RTX 4090 at up to $0.50/h; storage is billed even when stopped; bandwidth is priced per host ($33–40/TB in the offer, about $0.40 for 10 GB).
  - Bakshi asked for 2× A100 40 GB, 64 vCPU, 256 GB; the agent recommended 2 GPUs, at least 32 vCPU and at least 128 GB.
- **Choice and why:** "Rent it now. It's the proven lever." On demand, not spot (interruptible), because "a spot outage already cost us v7m once": the rented spot box was interrupted at 21:40 on 26 Sep and took the bge logits with it.
- **Evidence:** v6all to v7n gained +0.00111 on the LB against +0.0003 expected from US/India on the holdout, so France gained about +0.005 F0.5 [M/E] ([LB 2026-09-26 #03](../../submissions/records/2026-09-26_sub03.md)).
- **Outcome:** e5-large (twice), bge-reranker-v2-m3, a self-trained e5-large, Qwen2.5-1.5B and later Qwen2.5-7B entered the mix.
- **Hindsight:** none recorded.
- **Links:** [handover 2026-09-26_1817](../../docs/handover/2026-09-26_1817_ameya_ce-large-box.md) · [RESEARCH_v6 §6.9](../../experiments/ameya/model-v1/RESEARCH_v6.md) · D-CE-07 · D-CE-19 · D-ORG-15 · D-ORG-17

### D-CE-07 · Larger multilingual cross-encoders on the band (v7ce3)
- **When (IST):** 2026-09-26 17:43–19:42 (runs) · 19:33 (decision record) · **Phase:** P3 · **Area:** CE
- **Decided by:** Ameya (proposed by: agent for Ameya, track B; compute by Ameya)
- **Status:** adopted; superseded by D-CE-11. v7ce3 was packaged and never uploaded.
- **Problem:** v6all's cross-encoder (e5-small) reached holdout band AUC 0.9240, below stage-1 p1 on the same pairs (0.9297). The laptop GPU was too small for bigger models.
- **Options considered:**
  1. multilingual-e5-large (MIT, 560M).
  2. multilingual-e5-base (MIT, 278M), a cheap extra member using spare H100 capacity.
  3. Domain pretraining on our own record text first (skipped, "hours of GPU for an uncertain gain").
  4. A second e5-large seed averaged in (v7b; D-CE-10).
- **Choice and why:** e5-large and e5-base, with the same band (1.57M train and 1.49M test pairs), the same three OOF groups and the same training loop as `ce.py`, so their logits are honest stage-2 features. Only the records and the band pairs went to the box (about 1.2 GB; about 7.8 GB of traffic for the whole session). "e5-large beats stage 1 on the pairs stage 1 is unsure about, so it carries new information."
- **Evidence:**
  - Band AUC, OOF and holdout: e5-small 0.9191 and 0.9240; e5-base 0.9244 and 0.9287; e5-large 0.9350 and 0.9391; stage-1 p1 on the same pairs 0.9297. Runtimes 35 min (local), 37 min and 61 min (shared H100) [M].
  - Stage 2 with all three logits: v6all-c2 to v7ce3-c2 0.990788 to 0.991099, +0.000311 [+0.000258, +0.000362] (US +0.00026, India +0.00039); with stage 3, 0.990842 to 0.991138, +0.000296 [+0.000252, +0.000342]. Precision rose 0.9987 to 0.9991 at the same recall. The DP now beat the threshold (+0.00005 [+0.00001, +0.00009]) [M].
- **Outcome:** The v7 family. Its decisions became the teacher for the first French self-training round, so reproducing v7nst requires e5-base ([handover 2026-09-27_0111](../../docs/handover/2026-09-27_0111_bakshi_final-package.md)). Its successor v7n scored +0.001112 over v6all on the LB, the largest single step.
- **Hindsight:** none recorded.
- **Links:** [decision model-v7ce3](../../docs/decisions/2026-09-26_1933_model-v7ce3.md) · [RESEARCH_v6 §5.1](../../experiments/ameya/model-v1/RESEARCH_v6.md) · [`ce_box.py`](../../experiments/ameya/model-v1/ce_box.py) · D-CE-06

### D-CE-08 · Qwen2.5-1.5B (not 3B) with LoRA as an extra cross-encoder (Sachi)
- **When (IST):** 2026-09-26 17:59 (run start) · 23:37 (PR) · **Phase:** P3 · **Area:** CE
- **Decided by:** Sachi
- **Status:** adopted (the code). Sachi's own `q15` run's result is not recorded.
- **Problem:** A decoder LLM is a different model family from the e5 and bge encoders. Could it add signal on the uncertain band within the licence and size rules, on a 24 GB card?
- **Options considered:**
  1. Qwen2.5-3B (rejected: not Apache-2.0).
  2. Qwen2.5-1.5B, Apache-2.0 (chosen). The 0.5B and 7B are also Apache-2.0, and so is Mistral-7B-v0.3.
  3. Full fine-tuning against LoRA (chosen: LoRA, which trains small adapter matrices instead of all weights).
- **Choice and why:** The same band, OOF groups, text encoding (`ce.encode`) and output format as `ce_box.py`, so `ce_import.py` reads her logits unchanged. LoRA r = 16 on all attention and MLP projections, a sequence-classification head, pad = EOS. The full run used `--train-frac 0.35 --batch 32 --grad-ckpt`, because batch 64 ran out of memory on the 24 GB RTX 4090, and an on-demand box "so no interruption risk like the box that was lost tonight".
- **Evidence:** a smoke test on group 0 (3,000 rows) was clean; about 32 min per group, about 1.6 h in total [R].
- **Outcome:** `ce_llm.py` became the core of both Qwen models in the final submission. Ameya's `ce_llm_st.py` imports it unchanged to train `qst` (in v7sq), and Bakshi's `llm_group.py` runs the same recipe per GPU to train `q7st`, the Qwen2.5-7B. Ameya told Sachi at 01:56 on 27 Sep not to rerun Qwen, because the French self-trained version was already training on the H100.
- **Hindsight:** A licence check that mattered, and a reusable script. The decoder's value turned out to be diversity, not accuracy: `qst` reached band AUC 0.9381 against 0.9439 for the French self-trained e5-large.
- **Links:** [ce_llm.py](../../experiments/sachi/ce_llm.py) · [handover 2026-09-26_1800](../../docs/handover/2026-09-26_1800_sachi_llm-cross-encoder.md) · [PR #46] · [PR #51] · D-CE-12 · D-CE-19

### D-CE-09 · Add bge-reranker-v2-m3 after a licence check
- **When (IST):** 2026-09-26 19:48–19:49 · **Phase:** P3 · **Area:** CE
- **Decided by:** agent for Ameya
- **Status:** adopted
- **Problem:** There was spare GPU memory while the second e5-large trained.
- **Options considered** (licences read from the Hugging Face API):
  1. BAAI/bge-reranker-v2-m3 (Apache-2.0, a pair re-ranker).
  2. BAAI/bge-m3 (MIT, no safetensors file).
  3. intfloat/multilingual-e5-large-instruct (the fallback).
  4. A gte multilingual reranker.
  5. jina-reranker-v2-base-multilingual (CC-BY-NC, rejected).
- **Choice and why:** Option 1: "pre-trained as a pair re-ranker, so it should suit our task better than e5", Apache-2.0, 568M, under the 8B cap.
- **Evidence:** band AUC OOF 0.9383, holdout 0.9417–0.9418 [M] [chat:ameya/19e315ba 2026-09-26 20:58].
- **Outcome:** It entered v7c and v7m (the best French rule-population AUC, 0.878) and was lost with the box at 21:40. Reruns on later boxes were lost again or hit NaN losses until D-CE-13. It later joined the equal z-mean (D-CE-14), and a French self-trained version, `bges`, entered the variants v7sb and v7sq2.
- **Hindsight:** none recorded.
- **Links:** [RESEARCH_v6 §6.5](../../experiments/ameya/model-v1/RESEARCH_v6.md) · [chat:ameya/19e315ba 2026-09-26 19:48] · D-CE-03 · D-CE-11

### D-CE-10 · Averaging two e5-large runs into one feature (v7b) stopped
- **When (IST):** 2026-09-26 20:00–20:57 · **Phase:** P3 · **Area:** CE / MDL
- **Decided by:** agent for Ameya
- **Status:** rejected at the time; the mean returned as v7n (D-CE-11)
- **Problem:** Whether to average the 1-epoch and the 2-epoch e5-large runs into one stage-2 feature.
- **Options considered:**
  1. The average (v7b).
  2. The 2-epoch run alone.
  3. All logits separately (v7c).
- **Choice and why:** Stop v7b. On the holdout band the average (0.9429) is below the 2-epoch run alone (0.9441); the two runs correlate at 0.986, "so averaging the weaker one in only dilutes the stronger". Stopping it freed the laptop for v7c's local half.
- **Evidence:** holdout band AUC: e5l (1 epoch) 0.9391, e5l2 (seed 7, 2 epochs) 0.9441, mean 0.9429, z-weighted 0.3 and 0.7 0.9436; OOF 0.9350, 0.9403, 0.9400. A second epoch is worth 0.005 AUC [M] ([RESEARCH_v6 §6.5](../../experiments/ameya/model-v1/RESEARCH_v6.md)).
- **Outcome:** About 45 minutes later the box died, and v7n used exactly this mean. At 23:41 the French check showed the mean is best for France (rule-population AUC 0.806, against 0.803 and 0.792 for the single runs).
- **Hindsight:** The holdout AUC (US/India) and the French check point in opposite directions. The second epoch "specializes on the training countries". The same reasoning stopped a seed-bagged stage 2 (D-MDL-13).
- **Links:** [RESEARCH_v6 §6.11](../../experiments/ameya/model-v1/RESEARCH_v6.md) · D-CE-11 · D-CE-14

### D-CE-11 · One z-scored consensus mean instead of separate logits (v7m, then v7n)
- **When (IST):** 2026-09-26 20:57–21:43 · **Phase:** P3 · **Area:** CE
- **Decided by:** Ameya (proposed by: agent for Ameya)
- **Status:** adopted. v7n was uploaded (LB 0.989721).
- **Problem:** On US/India test band pairs the cross-encoders are nearly interchangeable (correlation 0.978–0.984, sign disagreement 2.7–3.1%). On France they part ways: correlation of e5l2 with bge 0.906, sign disagreement 12.0%. "A stage 2 that gets each logit separately (v7c) has learned its splits where the models agree. On France it extrapolates on their disagreements."
- **Options considered:** each variant was gated against v7ce3, once after stage 2 (gate c2; v7ce3-c2 holdout 0.991099) and once after stage 3 (gate s3). The French rule-population AUC is the AUC of stage-2 pc on French pairs whose truth is known from US/India rules (copies true, look-alikes false); it is label-free [E].

  | variant | what goes into stage 2 | gate c2 | gate s3 | French AUC |
  |---|---|---|---|---|
  | v7c | five separate logits | +0.000071 [+0.000027, +0.000115] | +0.000114 [+0.000081, +0.000150] | 0.8741 |
  | v7m | e5-small logit plus the z-mean of e5l, e5l2, bge | +0.000050 [+0.000008, +0.000097] | lost with the box | 0.8776 |
  | v7n | e5-small logit plus the z-mean of e5l, e5l2 | +0.000072 [+0.000040, +0.000103] | +0.000073 [+0.000041, +0.000102] | 0.8721 |

  v7ce3 scored 0.8651 and v6all 0.8546 on the same French check.
- **Choice and why:** The mean design (v7m). A 0.00002 gap is a tie, and "if they tie there, v7m is preferred: it has fewer features, and its inputs are the models' consensus". It also had the higher French AUC. z is computed on the train band; e5-base was dropped as the model that diverges most on France. The rented spot box died at 21:40 with bge's logits, so v7m was rebuilt locally in about an hour as v7n, without bge.
- **Evidence:**
  - Label-free, v7c is more conservative in France: crossing pc 0.7, +8.2 and −21.7 per 1000 French S1 against v7m, where US/India move about 0.8 each way [E].
  - LB: v7n 0.989721 (rank 8), +0.001112 over v6all's 0.988609; the US/India part rose +0.00033; France went from about 0.973 to about 0.978 [E]. The pre-upload prediction (0.9894 at France 0.976, 0.9900 at 0.980) held [M] ([LB 2026-09-26 #03](../../submissions/records/2026-09-26_sub03.md)).
- **Outcome:** Later means added bge, e5ls and qst (D-CE-14, D-CE-16). The methodology keeps the reason: given separate scores, stage 2 extrapolated where the models disagree, "four times as often in France".
- **Hindsight:** The reason for z-scoring before averaging (the logit scales differ) is not stated in the sources; they say only "z from the train band". Bakshi later tested a learned blend of all six cross-encoder logits and pc as the decision score: band AUC 0.9575 (pc alone 0.9276), but it lost 0.001 F0.5 as a replacement and was worth only +2e-6 to +4e-6 as an edit signal [M] ([FINAL_PUSH_RESULTS §9](../../experiments/bakshi/box/FINAL_PUSH_RESULTS.md)).
- **Links:** [decision model-v7n](../../docs/decisions/2026-09-26_2135_model-v7n.md) · [RESEARCH_v6 §6.6–6.10](../../experiments/ameya/model-v1/RESEARCH_v6.md) · [`zmean_ce.py`](../../experiments/ameya/model-v1/zmean_ce.py) · [PR #43] · D-CE-10 · D-CE-14 · D-ORG-16 · D-EVL-11

### D-CE-12 · Qwen: pair separator, French self-training and a two-sided gate (`qst`)
- **When (IST):** 2026-09-26 23:39 (review of Sachi's [PR #46]) → 2026-09-27 01:37 (`ce_llm_st.py`) · **Phase:** P3 · **Area:** CE / FRA
- **Decided by:** Ameya (suggested in his review of PR #46; his direction: "train it more on the whole data and lean more on french"); built by agent for Ameya
- **Status:** adopted
- **Problem:** Qwen's tokenizer adds no separator, so `tok(a, b)` concatenates the S1 and record strings. And a US/India-trained model is weakest on France.
- **Options considered:**
  1. Use Sachi's logits as they are (trained on 35% of the band, no separator).
  2. Continue from her weights (impossible: her script saves logits, not the LoRA adapters).
  3. A fresh run: her code imported unchanged, plus cross-fitted French pseudo-labels (labels we derive from our own French decisions), a " || " separator before the record text, and French emphasis: half the US/India labelled band rows plus all French pseudo-pairs, about 34% French (chosen, `ce_llm_st.py`).
- **Choice and why:** Option 3, and merge [PR #46] (clean diff, her own area, Apache-2.0; a non-blocking note about the missing separator). "Adding a separator … may help the model see the boundary." A Qwen2.5 decoder is "a different architecture with strong French", the diversity the mean needs. The model enters the mix only if it passes a predeclared two-sided gate on accuracy and decorrelation: holdout band AUC at least 0.93 and correlation with e5l at most 0.975 (D-CE-15).
- **Evidence:** a smoke test (3,000 labelled and 3,000 pseudo pairs) gave OOF AUC 0.7017 and holdout band AUC 0.726, a pipeline check only [M]. The first group reached OOF AUC 0.9334 on half the labels (gate 0.93) [R, issue #45 02:38]. Final `qst`: band AUC 0.9381, correlation with e5l 0.9433 [M, issue #45 05:17].
- **Outcome:** `qst` is one of the four members of v7sq's `cmq` mix. v7sq-dpc scored 0.990545 on the LB (D-CE-16). Bakshi later cited the two-sided gate as evidence that "admitting a model on accuracy alone would have been the wrong test".
- **Hindsight:** none recorded.
- **Links:** [PR #46] · [PR #51] · [issue #45] · [`ce_llm_st.py`](../../experiments/ameya/model-v1/ce_llm_st.py) · [chat:ameya/19e315ba 2026-09-27 00:16] · D-CE-08

### D-CE-13 · Skip optimizer steps with non-finite gradients
- **When (IST):** 2026-09-26 23:58 → 2026-09-27 00:16 · **Phase:** P3 · **Area:** CE
- **Decided by:** agent for Ameya
- **Status:** adopted
- **Problem:** On the second and third rented boxes (different PyTorch, CUDA and transformers versions) both cross-encoder runs logged loss NaN from step 1000. The same code had trained cleanly on the first box.
- **Options considered:**
  1. Change the environment.
  2. Patch the training loop (chosen).
- **Choice and why:** Patch. A forward pass was clean and a simple training loop was clean. A replay of the exact length-bucketed batching found a non-finite gradient at step 305 (batch 128 × 64 tokens), after which the weights went NaN (6 bad batches in the replay). `ce.train_one` now skips the optimizer step when gradients are non-finite. The same guard went into `ce_llm_st.py`.
- **Evidence:** after the relaunch, step-1000 losses were 0.3282 (bge) and 0.3391 (e5ls), with 6 and 9 non-finite steps skipped [M] [chat:ameya/19e315ba 2026-09-27 00:16].
- **Outcome:** Both runs train, at 394 pairs/s, about half of the first box's speed (the cause is not settled: environment or GPU sharing).
- **Hindsight:** The guard cannot rescue a model that overflows at nearly every step: mDeBERTa had 999 of its first 1,000 steps non-finite in bf16, and 5,999 of 6,122 in the French-heavy run (D-CE-18, D-CE-19).
- **Links:** [`ce.py`](../../experiments/ameya/model-v1/ce.py) · [chat:ameya/19e315ba 2026-09-26 23:58]

### D-CE-14 · Equal z-mean of diverse families; no weight tuning
- **When (IST):** 2026-09-27 01:42 (diversity finding) → 02:41–02:51 (labelled gate) → 03:50 (falsifiable test closed) · **Phase:** P3 · **Area:** CE
- **Decided by:** Ameya (analysis: agent for Ameya, with Bakshi's Track B rounds 2 and 3 and `ce_weight_fit.py`); Bakshi recommended, and Ameya kept equal z-means in v7s and v7sq
- **Status:** adopted (weight tuning rejected)
- **Problem:** Which cross-encoder logits to average into stage 2's single cross-encoder feature, so that France improves without hurting US/India (85% of the scored S1). Two e5-large runs correlated at 0.986 outvote one bge in an equal z-mean.
- **Options considered** (French rule-population AUC [E] and labelled US/India holdout band AUC [M]):
  1. `cem2` = e5l + e5l2, production in v7nst: 0.806 and 0.9428.
  2. `cem` = e5l + e5l2 + bge (v7mst): 0.826 and 0.9433.
  3. e5l + bge, equal: 0.829 and 0.9417. It costs 0.00114 of US/India band AUC against option 1, because it drops e5l2.
  4. Bakshi's weighted e5l 0.6 and bge 0.4: French 0.8311, +0.00201 [+0.00147, +0.00252] over the equal e5l + bge mean (0.8340 on a held-out half against `cem2`'s 0.8083), but 0.9414 labelled, −0.00144 against option 1, because it also drops e5l2, the best single US/India model (0.9441).
  5. Family-balanced blends (`fam_blend.py`): 0.8234 (50/50) and 0.8122 (33/67).
  6. `cms` = e5l + e5ls + bge (v7s): labelled 0.9433.
- **Choice and why:** An equal z-mean of diverse families. bge is the weakest single model on France (0.774), yet it lifts the mean the most (+0.020), because it is a different family (an XLM-R reranker) and its French errors are decorrelated from e5's. The US/India-specialised second e5 epoch leaves a French-optimal mix only when the French self-trained e5ls (holdout 0.9439) replaces it. No weight tuning: the spread of the estimated LB change across the best 40 weightings was only 0.000048, and "adding bge at all is worth about +0.00026 and that is the whole prize". Bakshi's three rounds: round 1, reweighting e5l and e5l2 (0.7/0.3: +0.00086 [+0.00037, +0.00136] of French AUC) was "statistically distinguishable from zero, and practically negligible", so Track B closed; round 2, after the bge logits were recovered, e5l 0.6 / bge 0.4 gave 0.8311, "adopt only if free"; round 3, with a fit and validate split by S1 and the labelled US/India gate, flipped the advice: `cem` is "the only bge mix that improves both sides (France +0.021, labelled +0.00053)".
- **Evidence:** [E] French proxy AUCs; [M] labelled AUCs [chat:ameya/19e315ba 2026-09-27 01:42] [chat:ameya/19e315ba 2026-09-27 02:41] [chat:ameya/19e315ba 2026-09-27 02:51]. Bakshi warned that v7s drops e5l2 and set a falsifiable test: v7s's US/India part should come out negative if his reading carried through. It came out +0.000037 over v7nst (v7mst +0.000013), so the warning was closed [M]. Ameya corrected Bakshi's "+0.00026 LB for adding bge" as probably high, because self-training absorbs most cross-encoder differences: v7mst moved only 8 French predictions per 1000 S1 against v7nst, while v7n to v7nst moved 31 [M].
- **Outcome:** v7s and v7sq kept equal z-means (D-CE-16).
- **Hindsight:** The labelled gate was the right correction to the French-only column of §6.13; the weighting itself was "a rounding error". The methodology keeps the result: "We average their z-scored logits into one stage-2 feature."
- **Links:** [TRACK_B_FINDINGS](../../experiments/bakshi/final-package/TRACK_B_FINDINGS.md) · [fam_blend.py](../../experiments/bakshi/final-package/fam_blend.py) · [ce_weight_fit.py](../../experiments/bakshi/final-package/ce_weight_fit.py) · [ce_diag.py](../../experiments/bakshi/final-package/ce_diag.py) · [PR #54] · [issue #45] · [RESEARCH_v6 §6.13–6.16](../../experiments/ameya/model-v1/RESEARCH_v6.md) · D-CE-15 · D-EVL-12

### D-CE-15 · Gate every new cross-encoder on labelled US/India data and on decorrelation
- **When (IST):** 2026-09-27 01:50–01:55 · **Phase:** P3 · **Area:** CE
- **Decided by:** Ameya ("Do that"); proposed by Bakshi (point 6 of his review) and the agent for Ameya
- **Status:** adopted
- **Problem:** A French self-trained model's French proxy score is circular: it trained on labels derived from those same populations, so the French check cannot qualify it.
- **Options considered:**
  1. Trust the French proxy.
  2. Gate on the labelled US/India holdout band AUC, plus a correlation cap with e5l so that a new model is not a copy of e5 (chosen).
- **Choice and why:** Option 2. Qwen: holdout band AUC at least 0.93 and correlation with e5l at most 0.975 (`final_night3.sh`). bges: AUC at least 0.935 (`final_night5.sh`). Later queues used a correlation cap of 0.99.
- **Evidence:** qst 0.9381, correlation 0.9433: pass [chat:ameya/19e315ba 2026-09-27 05:17]. bges 0.9424, correlation 0.9786: pass [04:19]. e5ls2 0.9440, correlation 0.985: pass [06:22]. e5ls's French proxy AUC was about 0.997, circular and ignored [02:50] [M].
- **Outcome:** Every later member passed this gate before joining a mix.
- **Hindsight:** The gate protected US/India but not France: adding more French self-trained members made the models drop more French true copies (v7sq lost 2.04, v7sq3 2.83 and v7sq2 3.20 copies per 1000 French S1 against v7nst; [RESEARCH_v6 §6.16](../../experiments/ameya/model-v1/RESEARCH_v6.md)).
- **Links:** [chat:ameya/19e315ba 2026-09-27 01:50] · [PR #54] · D-CE-12 · D-CE-14

### D-CE-16 · French self-trained cross-encoders in the mix: v7s, then v7sq as the first upload
- **When (IST):** 2026-09-27 02:45–07:10 · **Phase:** P3–P4 · **Area:** CE / FRA
- **Decided by:** Ameya (analysis: agent for Ameya); the gate by Bakshi; the Qwen classifier from Sachi
- **Status:** adopted
- **Problem:** Self-training of stage 2 had worked (D-FRA-13). Would self-trained cross-encoders help France more, and which should be in the mix?
- **Options considered** (holdout F0.5 after stage 3; US/India part; `fhs`, a label-free tally per 1000 French S1 of the stacked candidate's changes against v7nst, higher is better):

  | model | cross-encoder mean | holdout (s3) | US/India part | `fhs` |
  |---|---|---|---|---|
  | v7s | e5l, e5ls, bge | 0.991229 | 0.843247 | +1.11 |
  | v7sb | e5l, e5ls, bges | 0.991226 | 0.843241 | +1.13 |
  | **v7sq** | e5l, qst, e5ls, bge | **0.991246** | **0.843258** | **+2.19** |
  | v7ensall | bag of five | 0.991239 | 0.843253 | +1.94 |
  | v7sq3 | v7sq plus e5ls2 | 0.991250 | 0.843265 | +1.13 |
  | v7sq2 | e5l, qst, e5ls, bges | 0.991245 | 0.843256 | +0.86 |
  | v7ensall2 | bag of seven | 0.991256 | 0.843266 | +1.85 |

- **Choice and why:** v7sq-dpc as the first upload, for "best combined evidence". Qwen was gated at OOF AUC 0.93; group 0 reached 0.9334. v7s passed Bakshi's labelled test: US/India part +0.000037 over v7nst. v7sq and the seven-model bag tied on expected LB (about 0.990295 against 0.990299); ties go to the simpler option, and v7sq reproduces from 4 cross-encoders and 1 stage 2, against 7 and 7.
- **Evidence:**
  - LB 0.990545 against v7nst-dpc's 0.990264: the model change is worth +0.000281, about +0.0016 of French F0.5 (about +0.00023 of the LB score) [M] ([LB 2026-09-27 #02](../../submissions/records/2026-09-27_sub02.md)).
  - The France-diff agent found that the French self-trained cross-encoders (qst, e5ls) "overruled the US-trained ones, mostly by dropping confident false pairs". Carrying US/India truth by pc band over to France predicts 82% of the gain (+362 of +441 F-units) [E].
- **Outcome:** v7sq-dpc was the first upload of 27 Sep.
- **Hindsight:** More French self-trained members drop more true copies; only v7sq keeps the balance (copies lost against v7nst, per 1000 French S1: v7sq −2.04, v7sq3 −2.83, v7sq2 −3.20) ([RESEARCH_v6 §6.16](../../experiments/ameya/model-v1/RESEARCH_v6.md)).
- **Links:** [handover 2026-09-27_0706](../../docs/handover/2026-09-27_0706_ameya_final-stack.md) · [handover 2026-09-27_1228](../../docs/handover/2026-09-27_1228_ameya_final-day.md) · [status ameya](../../docs/status/ameya.md) · D-CE-12 · D-CE-14 · D-CE-15 · D-SUB-13

### D-CE-17 · GPU plan for 27 Sep: weight the self-trained models; skip seeds, xlm-roberta-large and the 7B; stop the Qwen round-2 retrain
- **When (IST):** 2026-09-27 10:43 → 12:01 · **Phase:** P4 · **Area:** CE
- **Decided by:** agent for Ameya and Ameya (proposed by: agent a4ea3fde); the parent session killed the Qwen round-2 retrain at 12:01
- **Status:** partly adopted; the round-2 cross-encoders failed; the "skip the 7B" call was superseded by Bakshi's 7B run (D-CE-19)
- **Problem:** A rented H100 for about 8 hours, with results needed on the laptop by about 19:00.
- **Options considered** (the agent's ranking):
  1. Plan B: more weight on the self-trained models in the mix (laptop only; −0.0005 to +0.0015 of France F0.5).
  2. `qstr` and `e5lsr` in parallel on the guarded labels (4.5 h; about +0.0002 of France F0.5).
  3. mdeberta-v3-base (about 1 h).
  4. xlm-roberta-large (skip: the same XLM-R ancestry as e5 and bge).
  5. More seeds (skip: v7sq3's extra seed lost true copies).
  6. Stage 2 on the new labels (laptop only, guarded labels only).
  7. Qwen2.5-7B with LoRA (about 5 times `qst`, roughly 17 h alone: skip).
- **Choice and why:** Plan B, built as v7sq4 (e5l, qst, e5ls, e5ls2, bges) and v7sq6 (only the French-trained cross-encoders), plus guarded round-2 cross-encoders on the box. At 12:01 the Qwen round-2 retrain (`qstr2g`, three rounds, finishing about 14:15, its variant about 16:15) was killed: the design agent had shown that the self-trained cross-encoders already agree with the new v7sq labels on 98% of pairs, so round-2 retraining "teaches little". That saved about 75 minutes and freed the GPU the 7B checks needed. The round-2 e5 (`e5lsr2g`) was kept alone, as v7sq5g.
- **Evidence:** On France the self-trained cross-encoders correlate 0.94–0.98 with each other and 0.60–0.69 with the untrained ones. They agree in sign with the new labels on 98.0% of labelled band pairs (loss 0.054), whereas in round 1 the untrained e5l2 disagreed with its labels on 19.2% (loss 0.433): the training signal is about ten times weaker [M] [chat:ameya/agent-a4ea3fde 2026-09-27 10:43].
- **Outcome:** v7sq5g was "negative under every valuation" [E] and was dropped (s1 −6, own −13, s2 −53 F-units; it reverts the most LB-confirmed moves). v7sq4 and v7sq6 led to v7sq6wg and v7sq7wg. Bakshi trained the Qwen2.5-7B on three H100s (about 2 h).
- **Hindsight:** "Round 2 would behave like another random seed" held for the cross-encoders. The 17 h estimate for the 7B was far above what the methodology reports (about 6 h on one GPU, about 2 h on three).
- **Links:** [RESEARCH_v6 §6.18](../../experiments/ameya/model-v1/RESEARCH_v6.md) · [chat:ameya/19e315ba 2026-09-27 12:01] · [chat:ameya/agent-a2762d22 2026-09-27 13:56] · D-FRA-22 · D-CE-19

### D-CE-18 · French-heavy cross-encoders as extra members
- **When (IST):** 2026-09-27 14:09–16:03 · **Phase:** P4 · **Area:** CE
- **Decided by:** agent for Ameya
- **Status:** tried, then dropped
- **Problem:** Give the cross-encoders more French emphasis by training them mostly on pseudo-labelled French rows.
- **Options considered:**
  1. Four French-heavy models: e5fr (multilingual-e5-large), bgefr (bge-reranker-v2-m3), mdfr (mdeberta-v3-base, MIT, 278M) and e5bfr (e5-base). Each trains on a quarter of the US/India band plus round-1 French labels, for one epoch, and scores only French test rows.
  2. Leave the mix as it was.
- **Choice and why:** Try them, with the gate lowered from 0.93 to 0.90 because their US/India AUC is low by design [14:42]. They were tried in v7sq7wg (plus e5fr) and v7sq8wg (plus bgefr). Their scores on the calibrated French estimator `cal` (an estimate of the French gain that treats the new model's pc as calibrated on the US/India holdout) were +0.000159 and +0.000179, a tie with v7sq6wg's +0.000166, so the members "added nothing measurable". mdeberta collapsed (5,999 of 6,122 steps non-finite, most likely a DeBERTa-v3 mixed-precision overflow). The remaining GPU time went to round-1 full-recipe seeds (bges2, e5ls3, e5bs, bges4) and to synthetic members (D-CE-20).
- **Evidence:** holdout band AUC e5fr 0.918, bgefr 0.926, e5bfr 0.917 [M]; `cal` values [E] ([RESEARCH_v6 §6.18](../../experiments/ameya/model-v1/RESEARCH_v6.md)).
- **Outcome:** Even so, v7sq7wg became the uploaded French model (mixmdp), as the `cal` leader at 16:30, tied with two other variants (LB 0.990699).
- **Hindsight:** none recorded.
- **Links:** [chat:ameya/19e315ba 2026-09-27 16:03] · [chat:ameya/19e315ba 2026-09-27 15:00] · D-CE-13 · D-FRA-20

### D-CE-19 · Pull the model-scale lever: Qwen2.5-7B on rented boxes, gated by a reproduction check (Bakshi)
- **When (IST):** 2026-09-27 14:15–14:45 · **Phase:** P4 · **Area:** CE / FRA / ORG
- **Decided by:** Bakshi
- **Status:** adopted
- **Problem:** Post-processing was exhausted, small encoders barely moved France (v7sq4: 10.9 changed predictions per 1000 French S1), self-training rounds were shrinking (+0.0026, +0.0011, +0.0002 on LOCO), and every cross-encoder saturated at 0.938–0.944 band AUC.
- **Options considered:**
  1. The main bet: Qwen/Qwen2.5-7B (Apache-2.0, 7.6B).
  2. A second member: Qwen/Qwen3-4B-Base (Apache-2.0, 4.0B), if it finished by 17:45.
  3. Cheap fillers: Alibaba-NLP/gte-multilingual-reranker-base (Apache-2.0, 0.3B) and microsoft/mdeberta-v3-base (MIT, 0.28B).
- **Choice and why:** "The one lever never tried." All new models self-train on France with the v7sq-dpc teacher's pseudo-labels (`pseudo_fr_v7sq.parquet`). Two rented boxes: a training box (4×H100, interruptible, one OOF group per GPU, checkpoints about every 10 minutes, Drive backup every 5) and a pipeline box (2×RTX 4090: rebuild through stage 1 and the band). Nothing built on the pipeline box counted until variant g0 (v7sq rebuilt with remapped logits) reproduced v7sq-dpc to about 0–3 changed French predictions per 1000 S1.
- **Evidence:** forecast, central about 0.9909, a new best about 2 in 3, at least 0.991 about 1 in 3, at least 0.9918 under 5% [E, Bakshi]. g0: holdout 0.991261 against v7sq's 0.991246; France 4.34, India 1.13 and US 1.23 changed predictions per 1000 S1 [M] ([FINAL_PUSH_PLAN](../../experiments/bakshi/box/FINAL_PUSH_PLAN.md)).
- **Outcome:** `q7st` was done at about 18:05 (holdout band AUC 0.9436, OOF 0.9396), level with e5ls (0.9439): "scale alone did not buy AUC". Qwen3-4B was merged at 18:43, too late for any candidate except as the agreement signal in the last upload's ladder. mDeBERTa (999 of its first 1,000 steps non-finite in bf16) and gte (an index assertion in its remote code under a newer transformers) failed. The 7B's value came from diversity (D-CE-23) and as a re-reader of confident predictions (D-LLM-05). The best upload, Composite B, scored 0.990879 on the LB, close to the central forecast.
- **Hindsight:** The bet paid through a use nobody planned at 14:30: re-reading confident pairs. Scoring all 58.4M test pairs with the 7B at about 600 pairs/s would take about 27 GPU-hours, so it was used only on the band and on confident predictions.
- **Links:** [PR #62] · [HANDOFF](../../experiments/bakshi/box/HANDOFF.md) · [METHODOLOGY_bakshi §3](../../experiments/bakshi/final-package/METHODOLOGY_bakshi.md) · [FINAL_PUSH_RESULTS §1](../../experiments/bakshi/box/FINAL_PUSH_RESULTS.md) · [LB 2026-09-27 #04](../../submissions/records/2026-09-27_sub04.md) · D-CE-22 · D-CE-23 · D-LLM-04

### D-CE-20 · Synthetic French supervision for cross-encoders
- **When (IST):** 2026-09-27 14:17 → 17:28 (built and run) · 15:05 → 20:25 (evaluated and rejected) · **Phase:** P4 · **Area:** CE / FRA
- **Decided by:** Ameya set the priority ("have to put searches part on priority", read as Sachi's part); the idea and first scripts are Sachi's (`synth_fr.py`, `ce_synth.py`); agent for Ameya ran and modified them; the rejection by agent for Ameya and Ameya
- **Status:** rejected as a final source (one synthetic detector kept as a cross-check)
- **Problem:** Self-training had saturated because it recycles our own decisions. Correctly labelled French examples would be new information.
- **Options considered:**
  1. Sachi's `synth_fr.py` and `ce_synth.py` as they were.
  2. `synth_fr2`, which adds three operations: brand copies at the S1 address (true), house-number look-alikes (false), another real business at the S1 address (false).
  3. `synth_fr3`, re-weighted to the real French operation mix (chosen).
  4. Where to run: Bakshi's idle GPUs, our H100, or the 5090s.
- **Choice and why:** synth3. The France-diff agent's comparison showed both earlier generators were mis-weighted: legal-form changes are 22.6% of real French copies against about 3% synthetic; about 30% of real non-matches are the same name at another place; −1 and −2 house-number moves are true copies and only +d nudges are look-alikes; 32% of addresses carry a department name. Sachi's trainer crashed on `Series.set_index`; the fix in `ce_synth2.py`, with speed flags, cut a run from about 1 h 45 to about 50 min. The runs on Bakshi's boxes were stopped at Ameya's request [17:24]. synth3 gives 107,766 pairs from 40,000 French S1 (39.7% true) [M]; cesy3b's US/India band AUC is 0.9095 [M].
- **Evidence (the rejection):**
  - v7sqsyc (synthetic cross-encoders plus round 3): `cal` +249e-6 but own estimate +51e-6. It reverses 1,182 of the LB-confirmed v7nst to v7sq moves, and its drops are pairs our French cross-encoders like (z +0.59 against +0.43).
  - v7sqsyd (all six synthetic cross-encoders plus round 3): `cal` +293e-6, own-cal +3e-6. It reverts 1,576 confirmed moves; its drops have French-cross-encoder z +0.73 where the confirmed direction is −0.20; its US/India holdout is −43e-6.
  - Synthetic e5-base detectors are miscalibrated: at logit below −4, 181 of 192 holdout drops are true; France flags 7,263 at −5 against 39 on the holdout [M/E] ([RESEARCH_v6 §6.19](../../experiments/ameya/model-v1/RESEARCH_v6.md)).
  - "Synthetic cross-encoders raise cal by reverting what the leaderboard confirmed."
- **Outcome:** Not used. One synthetic model stayed useful as a cross-check: the bge detector `cesyoobg` (US/India labels plus synthetic data, no self-training labels) flags 708 of the 859 French pairs the 7B rejects (82%); at logit below −8, 13 of its 15 holdout drops are false (+21e-6, both halves positive). Its 329 extra French flags add +1e-6, so they were not used.
- **Hindsight:** An estimator can rank a method first while the method undoes what the leaderboard already confirmed. The same lesson reappears after the verdicts (D-FRA-26).
- **Links:** [synth_fr.py](../../experiments/sachi/synth_fr.py) · [ce_synth.py](../../experiments/sachi/ce_synth.py) · [ce_synth2.py](../../experiments/ameya/model-v1/ce_synth2.py) · [synth_fr3.py](../../experiments/ameya/model-v1/synth_fr3.py) · D-FRA-23 · D-FRA-25 · D-EVL-14 · D-EVL-15

### D-CE-21 · Wire Bakshi's 7B (`q7st`) into our own pipeline
- **When (IST):** 2026-09-27 14:28 (plan) → 17:10–17:12 (variant v7sqq7) · **Phase:** P4 · **Area:** CE
- **Decided by:** agent for Ameya, with Ameya, who arranged access to Bakshi's boxes
- **Status:** adopted as a variant
- **Problem:** Bakshi's 7B was trained on our band files (the same checksum), so it could feed our already-built pipeline sooner than his rebuild from scratch.
- **Options considered:**
  1. Wait for Bakshi's own chain (g1, g1w, g2; packages about 19:30).
  2. Relay `q7st` to our box and run `cmq9` + `q7st` with the guarded labels at weight 3.
- **Choice and why:** Relay it. That gives two independent chains, ours about 45 minutes earlier. The agent first asked Bakshi to copy `out_q7st`, then pulled it directly once Ameya gave access [17:11].
- **Evidence:** `q7st` holdout band AUC 0.9436, the same level as our e5-large; fold g2 OOF AUC 0.9399 in 5,135 s. Alignment check: 1,568,554 and 1,490,930 rows, no NaN [M] [chat:ameya/19e315ba 2026-09-27 17:10] [17:12].
- **Outcome:** v7sqq7's stage 2 finished at 17:32 and mixq7 was due about 18:15–18:35. In the mix France was a tie (v7sqq7 +159 against about +160 for the other round-2 models).
- **Hindsight:** The 7B's value came through g1w (India) and through the re-check drops at logit below −6, not through France's mix.
- **Links:** [RESEARCH_v6 §6.19](../../experiments/ameya/model-v1/RESEARCH_v6.md) · [chat:ameya/19e315ba 2026-09-27 14:28] · D-CE-19 · D-CE-23 · D-LLM-04

### D-CE-22 · Train on Ameya's band files; move logits by (s1, r) with a 99.5% coverage gate (Bakshi)
- **When (IST):** 2026-09-27 14:30 · **Phase:** P4 · **Area:** CE / PKG
- **Decided by:** Bakshi
- **Status:** adopted
- **Problem:** `ce_import.py` places logits by positional `row`, and a rebuild on another machine need not reproduce the row order (parallel top-k with ties, thread counts, float drift moving pairs across the band edge). Importing rows across machines would put "every logit on the wrong pair — silently".
- **Options considered:**
  1. Reuse the row numbers.
  2. Re-key by (s1, r) and gate on coverage (chosen).
- **Choice and why:** Option 2: "`row` never crosses machines." The share of rebuilt band rows that receive a logit measures whether blocking and stage 1 reproduced; below 99.5% the run aborts. Tested: identity is exact, permuted rows follow the pair, a 2% gap fails.
- **Evidence:** all six cross-encoder inputs: train 100.0000%, test 99.9999% (1 pair missing) [M, log]. Blocking reproduced 66,429,057 and 58,437,794 pairs [M].
- **Outcome:** The rebuilt chain reproduced v7sq-dpc (D-CE-19, g0).
- **Hindsight:** none recorded.
- **Links:** [remap_ce.py](../../experiments/bakshi/box/remap_ce.py) · D-CE-19

### D-CE-23 · Count the 7B twice in the stage-2 mix (g1w)
- **When (IST):** 2026-09-27 about 18:05–19:47 · **Phase:** P4 · **Area:** CE / MDL
- **Decided by:** Bakshi (g1w); the team adopted it
- **Status:** adopted (India in the plan for mixf2; US and India in Composite B)
- **Problem:** How much weight should `q7st` get in the z-mean of e5l, qst, e5ls and bge?
- **Options considered** (holdout F0.5 after stage 3):
  1. g0, no 7B: 0.991261.
  2. g1, the 7B once: 0.991276.
  3. g1w, the 7B twice: **0.991323**.
  4. g1x3, three times: 0.991322.
  5. g7only, the 7B alone: 0.991286.
  6. gbag, a bag of g0, g1 and g1w: 0.991313.
- **Choice and why:** ×2, the smallest weight at the plateau; the 7B alone is worse than the mix. A mean rather than separate logits, because the models disagree four times as often on France and a stage 2 given separate logits extrapolates on the disagreements. The methodology: the 7B "is no more accurate than a self-trained e5-large; both score 0.944", and it earns its place by diversity and by its independent reading of confident pairs.
- **Evidence:** [M, holdout] ([METHODOLOGY_bakshi §4](../../experiments/bakshi/final-package/METHODOLOGY_bakshi.md)). Ameya's paired bootstrap against v7sq3: India +66.1e-6 (P 0.998; our combo decision code on Bakshi's pc reproduces his g1w-dpc within 25 pairs), US +26.2e-6 (P 0.906, which "fails a multiple-testing correction"). Paired against g1w on India: g1x3 −13.5e-6, g7only −70.3e-6. In France the 7B mix was a tie (v7sqq7 +159 against about +160), and g1w's France (`cal` +75e-6) was not competitive with Ameya's round-2 and round-3 French models [M/E].
- **Outcome:** mixf2 took India from g1w and the US from v7sq3; Composite B took both from g1w, and the LB pair mixf7 against mixf2 put g1w's US at +14e-6, "holdout-consistent" (D-MDL-16).
- **Hindsight:** none recorded.
- **Links:** [FINAL_PUSH_RESULTS §2](../../experiments/bakshi/box/FINAL_PUSH_RESULTS.md) · [PR #62] · [issue #64] · [RESEARCH_v6 §6.19](../../experiments/ameya/model-v1/RESEARCH_v6.md) · D-CE-19 · D-MDL-16 · D-LLM-09 · D-SUB-21
