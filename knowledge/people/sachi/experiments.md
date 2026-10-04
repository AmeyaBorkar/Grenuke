# Sachi: experiments

Summary: every measured attempt Sachi ran, kept or dropped, with local IDs `S-X-NN`. Scope and evidence level (M, E, R, U)
are on every result. "France kit v1" is the kit built from an older model's outputs (before self-training), so
France-side numbers from it show whether an effect exists and its rough size, not final values.

| ID | when (IST) | area |
|---|---|---|
| S-X-01 | 2026-09-25 17:07 to 18:00 | MDL, DEC |
| S-X-02 | 2026-09-25 21:15 | FEA |
| S-X-03 | 2026-09-26 10:00 to 13:00 | FRA |
| S-X-04 | same | FRA |
| S-X-05 | 2026-09-26 about 12:52 to 13:04 | RUL |
| S-X-06 | 2026-09-26 17:04 to about 22:00 | CE |
| S-X-07 | 2026-09-26 23:29 to 2026-09-27 early morning | CE |
| S-X-08 | 2026-09-27 about 09:25 to 11:15 | CE, LLM |
| S-X-09 | 2026-09-27 13:24 | DEC |
| S-X-10 | 2026-09-27 about 13:30 to 15:00+ | FRA |
| S-X-11 | 2026-09-27 18:30 | DEC |
| S-X-12 | 2026-09-27 18:30 | FRA |
| S-X-13 | 2026-09-27 18:48 | LLM |
| S-X-14 | 2026-10-03 night | PKG |
| S-X-15 | 2026-09-25 20:55 | DEC |
| S-X-16 | 2026-09-25 21:03 | MDL |
| S-X-17 | 2026-09-25 about 21:00 | PRB, EVL |

---

### S-X-01 · v0 baseline on the dev sample, gate G6
- **Hypothesis:** an exact expected-F0.5 set per S1 beats a tuned global threshold.
- **Setup:** dev kit v0, features `ameya-baseline-v0-dev` (37 features), stage-1 XGBoost, 3 out-of-fold groups, isotonic calibration cross-fitted. Trained on dev-sample folds 5, 10 and 15 (2,393,231 pairs). Evaluated on dev-sample fold 0 (27,651 S1, 819,316 pairs). Ownership over all S1 candidates. Tests: 43 passed at [PR #16] (the DP checked against brute force), 92 at [PR #17].
- **Result** ([M], dev kit v0, fold 0, [G6 record](../../../docs/decisions/2026-09-25_1731_gate-g6-dp-vs-threshold.md)). Dev runner (threshold 0.70, the run in [PR #16]): macro F0.5 0.9649 (the PR says 0.9648), ECE 0.0004; DP (shift -0.25) 0.9647; delta -0.00024, CI [-0.00091, +0.00049], p_better 0.234. The official evaluator reproduced 0.96492 with precision 0.988, recall 0.929, singleton F0.5 0.953, 3.26 predicted per S1, US 0.974, India 0.952. Through the pipeline stages (threshold 0.71, the run in [PR #17]): 0.96517, DP 0.96473, delta -0.00044, CI [-0.00107, +0.00022], p_better 0.101.
- **Verdict:** threshold kept (S-D-01). Superseded by Ameya's calibrated stage 2.
- **Source:** [chat:sachi/web-1 2026-09-25 17:52], [G6 record](../../../docs/decisions/2026-09-25_1731_gate-g6-dp-vs-threshold.md)

### S-X-02 · Name-uniqueness features
- **Hypothesis:** an exact name that no other S1 in the country shares is trustworthy even without an address.
- **Setup:** `add_name_uniqueness.py` added five columns to `ameya-fx2-dev` (giving `sachi-fx2-name-dev`); stage 1 retrained (`sachi-s1-name-dev`); `check_name_uniqueness.py` for the breakdown. Dev fold 0, 27,651 S1, paired bootstrap.
- **Result** ([M], dev kit v2, fold 0, [name-uniqueness record](../../../docs/decisions/2026-09-25_2111_gate-name-uniqueness.md)): 0.97745 to 0.97800, delta +0.00054, CI [+0.00001, +0.00107], p_better 0.975. Among 3,779 true pairs with an empty record address: unique exact name 95.8% to 98.5% found; shared exact name 2.8% to 1.6%; non-exact name 52.6% to 52.1%.
- **Verdict:** dropped: far below the +0.002 bar (S-D-03).
- **Source:** [name-uniqueness record](../../../docs/decisions/2026-09-25_2111_gate-name-uniqueness.md)

### S-X-03 · Leave-one-country-out by feature group
- **Hypothesis:** one feature group causes the unseen-country drop.
- **Setup:** `loco_groups.py` on dev kit v2: train on US, test on India, drop one group at a time; candidate if dropping it raises unseen-country F0.5 by at least +0.003 with under 0.001 in-country cost. The first local run stalled for a long time on the laptop.
- **Result:** no group qualified. Unseen-country gap about 0.028 in my run [M, dev kit v2] [chat:sachi/web-2 2026-09-26 12:50].
- **Verdict:** dropped. See open question Q-03 on the 0.024 vs 0.028 gap.

### S-X-04 · LOCO edit-profile features
- **Hypothesis:** features that describe how a record differs from its S1 (generator operations) transfer to an unseen country.
- **Setup:** `loco_profile.py`, US to India.
- **Result:** +0.0005 against the +0.003 bar [M, dev kit v2, US to India] [chat:sachi/web-2 2026-09-26 12:50].
- **Verdict:** dropped.

### S-X-05 · France kit v1: pattern hypotheses
- **Hypothesis:** there are French patterns with a clear truth rate that a rule could use.
- **Setup:** `france_discover.py`, `france_hypotheses.py`, `france_hyp_split.py` on the kit, truth rates taken from the labelled holdout.
- **Result:** the empty-address and unique-name pattern was already handled well by the model. French names collide far more than US/India (groups of 100 to 200 or more S1). Remaining patterns were 63 to 88 percent true after rules v2 [M, France kit v1, older model] [chat:sachi/web-2 2026-09-26 13:04].
- **Verdict:** no new rule. Drives D: S-D-05.

### S-X-06 · e5-small vs e5-base as the cross-encoder
- **Hypothesis:** the larger e5 adds signal over e5-small.
- **Setup:** `ce_compare.py`, dev-kit pairs, 40,000 train and 20,000 eval, batch 32. First tried on the 8 GB laptop at 2,000 pairs (worked, AUC 0.73, log-loss reduction 0.07 percent: meaningless) then 20,000 pairs (system thrashed). Moved to a rented RTX 3090.
- **Result:** log-loss reduction over the stage-1 probability: e5-small 6.5 percent, e5-base 10.0 percent, both together 10.1 percent. AUC with the cross-encoder: 0.9647 (small) vs 0.9666 (base). Run time: small 1.28 min, base 3.20 min [M, dev-kit pairs] [chat:sachi/web-3 2026-09-26 evening].
- **Verdict:** the script said "keep e5-small (no clear gain)" because the gap was 3.5 points, below its 5-point bar. I read it as a borderline positive. It did not change the pipeline: Ameya's H100 runs on the full band (decision record 2026-09-26 19:33) had already measured it, and I saw them only after my run. They gave: band AUC e5-small 0.9240, e5-base 0.9287, e5-large 0.9391 [R, local holdout band] (his decision record on v7ce3).
- **Setup notes:** the laptop failures were memory, not code. The script loaded the whole training file before filtering.

### S-X-07 · Qwen2.5-1.5B LoRA cross-encoder: smoke test and partial full run
- **Hypothesis:** a decoder-model pair classifier adds diversity to the e5 and bge band models.
- **Setup:** `ce_llm.py`: LoRA rank 16 on all attention and MLP projections, learning rate 1e-4, one epoch, maximum length 96, bf16 autocast, seed 26. Band files from Ameya (1,568,554 train pairs, 0.272 positive; 1,490,930 test pairs; median 36 tokens). Rented RTX 4090. Full run used `--train-frac 0.35 --batch 32 --grad-ckpt`. A batch of 64 ran out of memory.
- **Result:** smoke test (3,000 pairs): holdout AUC 0.7336, no crash [M, band] [chat:sachi/web-3 2026-09-26 about 23:18]. Full run: group 1 out-of-fold AUC 0.9279 with 276,196 training pairs [M, band, out-of-fold]. Training took about 35 minutes per group; scoring about 55 minutes per group [E, from log timestamps]. Group 0 and 2 AUCs: not seen.
- **Verdict:** concept proven. The machine was destroyed before the run finished, so no logits were kept. Ameya built `qst` from the same code.
- **Source:** [chat:sachi/web-3 2026-09-27 02:31]

### S-X-08 · Qwen2.5-7B: smoke tests
- **Hypothesis:** the same recipe at 7B fits a 24 GB card.
- **Setup:** `ce_llm.py --model Qwen/Qwen2.5-7B --smoke --batch 16 --grad-ckpt` on an RTX 4090.
- **Result:** first box: ran clean, 3,000 pairs, holdout AUC 0.6761, total 338 seconds including a 2.5-minute model download [M] [chat:sachi/web-3 2026-09-27 about 09:30]. A later full launch lost its connection. Second box: the smoke test failed with NaN in the scores at the AUC step (the training output went non-finite) [M] [chat:sachi/web-3 2026-09-27 about 11:15].
- **Verdict:** abandoned on my side. I think the NaN is a divergence in training; this is an inference [E]. Ameya's `ce_llm_st.py` adds a guard that skips non-finite-gradient steps, and Bakshi's 7B runs worked on H100s. Whether the guard would have fixed my run is not tested.

### S-X-09 · Copy counts and the empty-address name ties
- **Hypothesis:** the S1s competing for a same-name record with an empty address are not interchangeable, because the generator gives each a copy count with caps. How many copies each holds might reveal the owner.
- **Setup:** `size_bias_owner.py` on France kit v1 holdout pairs and the training truth: records with an empty address, an exact normalised name match to two or more S1, exactly one true. Honest split: posterior fitted on half the records, rule scored on the other half.
- **Result:** 13,105 such records (23.8 per 1,000 S1); the model predicted 9.0 percent of them. Picking the S1 with the fewest same-source copies was right 31.3 percent of the time against 27.3 percent by chance; other pick rules 23 to 28 percent. No posterior reached 0.6. Adding the best-posterior S1 at 0.50: 1,836 pairs, precision 0.516, holdout change -0.000672, about -0.000571 on the LB. Pairs whose S1 already held the source cap: 406, 0 percent true [M, France kit v1 holdout, older model] [chat:sachi/web-3 2026-09-27 13:24].
- **Verdict:** dropped. These ties are coin flips from the available fields. Supports the decision to abstain.

### S-X-10 · Synthetic French pairs and a cross-encoder trained on them
- **Hypothesis:** French pairs with correct labels by construction can teach a model what self-training cannot, because self-training reinforces the model's own confident mistakes.
- **Setup:** `synth_fr.py`: from 40,000 real French S1 (names and addresses, no labels) it built true copies by the measured operations (case, accents, legal-form edits, list-word appends, word drop plus append, acronym, typo, street abbreviation, region drop, city-first order, empty address) and look-alikes (one content word swapped for a French word, optional legal-form change or house-number nudge). `ce_synth.py` trained e5-large on the US/India band plus these pairs, three out-of-fold groups. Rented RTX 4090. Batch 128 ran out of memory; batch 32 with gradient checkpointing worked.
- **Result:** 99,702 pairs, 40.1 percent true, vocabulary 1,575 words [M] [chat:sachi/web-3 2026-09-27 about 13:30]. Smoke test ran end to end (holdout AUC 0.68, meaningless at 3,000 pairs). Full run stopped at step 9,800 of 26,609 in group 0, about 52 minutes left for that group [M, log] [chat:sachi/web-3 2026-09-27 14:25]. Ameya's real-vs-synthetic comparison: legal-form drop, change or order is 22.6 percent of real French copies against about 3 percent synthetic; list-word appends, typos and acronyms are 10 to 14 percent of synthetic and 1 to 2 percent of real; about 30 percent of real French non-matches are the same name at another address and neither generator made any; house-number moves of -1 or -2 are true copies; 32 percent of real French addresses name the department [R] ([issue #63]).
- **Verdict:** my run was stopped (S-D-09). Ameya's synthetic models lost on five of six estimators and were negative on the US/India holdout (v7sqsyd: own-cal +3 vs +127; net s1 +139 vs +170; US/India -43e-6 vs +82e-6) [R] ([issue #64] 20:25). A synthetic-trained bge flagged 82 percent (708 of 859) of the French pairs the 7B rejects, and at logit below -8 on the holdout 13 of its 15 drops are false (+21e-6) [R] ([issue #64]). So the idea became a label-independent check, not a model.

### S-X-11 · Renormalising French probabilities per record
- **Hypothesis:** a record has one owner, so if its candidates' probabilities sum past 1 the extra is overconfidence. Rescaling to pc / max(1, sum) and dropping low rescaled pairs would remove confident ties in France.
- **Setup:** `tie_audit.py` on France kit v1. First run counted rule-added pairs as model predictions. Second run kept only model-kept pairs with pc at least 0.5 and not added by a rule.
- **Result, first run:** records with sum pc above 1.05 per 1,000 S1: holdout 2.06, France 43.82; excess mass 0.45 vs 25.08. Implied false shares of 0.64 to 0.87 were an artefact: the lowest bin held rule-added pairs, and its truth rate came from 4 holdout pairs.
- **Result, second run:** sum pc above 1.05 per 1,000 S1: holdout 0.41, France 5.86; excess mass 0.10 vs 2.23. Kept pairs with a rival at pc of 0.3 or more: holdout 0.1, France 2.9 per 1,000 S1. Dropping kept pairs with rescaled pc below 0.60: holdout 107 pairs, 58.9 percent true, change -0.000007; France 2.7 per 1,000 S1, implied false share 0.41. Below 0.70: -0.000047, France 4.2 per 1,000, 0.36. Below 0.76: 541 pairs, 71.5 percent true, -0.000137, France 5.8 per 1,000, 0.32 [M, France kit v1, older model] [chat:sachi/web-3 2026-09-27 about 18:35].
- **Verdict:** dropped. French genuine ties are rare, and dropping them loses on the holdout at every cut. The remaining French errors are uncontested.

### S-X-12 · Department versus region formats in French addresses
- **Hypothesis:** French records name the department while S1s name the region, so same-name S1s could look identical.
- **Setup:** the same `tie_audit.py` (part 3, since removed): learn department to region from confident French pairs, count kept pairs where the record's department points to a different region.
- **Result:** the heuristic was crude. The "departments" it learned included towns and the "regions" included cities, so its 137.8 mismatches per 1,000 S1 were mostly artefacts. The examples (Lille and Nord, Bordeaux and Gironde) were correct matches at pc about 1.00 [E, France kit v1] [chat:sachi/web-3 2026-09-27 about 18:35].
- **Verdict:** dropped on weak evidence. The model already links department-style records to city-style S1s.

### S-X-13 · Same name, same house number, different street
- **Hypothesis:** Ameya's French false-merge pattern is a look-alike operation that a rule could drop.
- **Setup:** `street_swap.py` on France kit v1, candidates with pc at least 0.3. Street similarity from difflib on the street words after removing street types and numbers.
- **Result (per 1,000 S1):** different street: holdout 23.20, 99.9 percent true, 99.9 percent predicted; France 6.56, kept 51.5 percent, median pc 0.75. Similar street: 28.25 holdout, 28.64 France, France kept 98.0 percent. Near-typo: 66.37 holdout, 287.97 France, France kept 99.8 percent. France kept different-street pairs: 870, which is 3.4 per 1,000 French S1 [M, France kit v1, older model] [chat:sachi/web-3 2026-09-27 18:48].
- **Verdict:** a pattern-only drop would remove real copies. The pairs the model rejects are outside this table (pc below 0.3), which is where the decoys are. Ameya's 7B table covers them (S-D-11). Kept as supporting evidence for gating the drop on the 7B.

### S-X-14 · Hash check of the final TSVs
- **Hypothesis:** the two TSVs in the shared `final_zip` Drive folder are the Composite B pair.
- **Setup:** `shasum -a 256` on the downloaded folder.
- **Result:** matching_results.tsv `df4bccd785b3fa785b7edcf0532288bcddc0010e2e31ce6f358064529ecb62e8`; candidate_pairs.tsv `58c824a3f61c184fe7da1a448a4ac94284f288feff9c351abfe16a3dfc0520e5`. Both equal the Composite B hashes [M] [chat:sachi/web-3 2026-10-03 night]. The folder also holds the three q7st LoRA adapters (about 154 MB each).
- **Verdict:** confirmed. I did not open the submission ZIP (88,353,544 bytes on Drive); its contents are unverified by me.

### S-X-15 · Gate G6 again, on model v2 probabilities
- **Hypothesis:** with better-calibrated probabilities the exact expected-F0.5 decision should beat the tuned threshold.
- **Setup:** decide stage on Ameya's `ameya-s2-v2-dev` calibrated `pc` (tag `sachi-decide-v2`), dev kit v2, dev fold 0, 27,651 S1.
- **Result** ([M], dev kit v2, fold 0, [G6 record](../../../docs/decisions/2026-09-25_1731_gate-g6-dp-vs-threshold.md), update 20:55): threshold 0.67 gave 0.98438 (the evaluate stage agrees; it matches Ameya's reported 0.9845). DP gave 0.98447. Delta +0.00010, CI [-0.00023, +0.00045], p_better 0.714.
- **Verdict:** threshold kept, below the +0.002 bar. The DP moved from slightly worse (-0.00044 on stage-1 probabilities) to slightly better. Ameya's later full-holdout gate found +0.00018, CI above 0 [R]. Fed S-D-01.

### S-X-16 · Gate G4: stage 2 against stage 1
- **Hypothesis:** the collective stage 2 adds real accuracy over stage 1 alone.
- **Setup:** same 79 features (`ameya-fx2-dev`), dev fold 0, 27,651 S1; stage 1 only (`sachi-s1-fx2-dev`, threshold 0.68) against model v2 stage 2 (`ameya-s2-v2-dev` pc, threshold 0.67); paired bootstrap, 1,000 resamples.
- **Result** ([M], dev kit v2, fold 0, [G4 record](../../../docs/decisions/2026-09-25_2103_gate-g4-stage2.md)): 0.97745 to 0.98438, delta +0.00692, CI [+0.00622, +0.00772], p_better 1.000. Singleton F0.5 0.968 to 0.985; recall 0.949 to 0.963.
- **Verdict:** kept (S-D-16).

### S-X-17 · Error analysis of model v2
- **Hypothesis:** the biggest remaining loss in model v2 has one identifiable cause.
- **Setup:** `experiments/sachi/error_analysis_v2.py` on dev fold 0 of model v2.
- **Result** ([M], dev kit v2, fold 0, cited in the [G4 record](../../../docs/decisions/2026-09-25_2103_gate-g4-stage2.md) and the [name-uniqueness record](../../../docs/decisions/2026-09-25_2111_gate-name-uniqueness.md)): the remaining loss is mainly recall on records with an empty address: 61% of below-threshold misses, and 98% of the records taken by another S1. Of v2's gain over v0, about two thirds came from the 79 features and one third from stage 2.
- **Verdict:** led to the name-uniqueness gate (S-X-02), which found no headroom there. The later copy-count test (S-X-09) closed the shared-name part.
