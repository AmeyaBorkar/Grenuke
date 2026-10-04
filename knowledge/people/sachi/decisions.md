# Sachi: decisions

Summary: choices Sachi made or influenced, in the standard format, with local IDs `S-D-NN`. Phases follow
`knowledge/STANDARD.md` §4. Times are IST. Where the exact time is unknown the entry says so. Hindsight is kept apart
on its own line.

---

### S-D-01 · Keep the threshold decision in the v0 baseline
- **When (IST):** 2026-09-25 17:31, numbers updated 17:52, pipeline-stage update 18:00, re-run on model v2 probabilities 20:55 · **Phase:** P1 · **Area:** DEC
- **Decided by:** Sachi
- **Status:** adopted for v0; the later re-runs kept it too
- **Problem:** gate G6 asks whether the exact expected-F0.5 set per S1 beats one tuned global threshold. The keep rule in `plans/FINAL_PLAN.md` §5.4 is a gain of at least +0.002 with the 95% CI above 0, and ties go to the threshold. (On 26 Sep my [PR #27] description called delta above 0 with the CI lower bound above 0 the plan's actual rule and +0.002 my earlier loose heuristic; see Q-25.)
- **Options considered:**
  1. Exact expected-F0.5 per S1: a dynamic program over the Poisson-binomial distribution of true copies, with one global logit shift. Follows the metric, but needs calibrated probabilities. Checked against brute-force enumeration on 40 random cases.
  2. One global threshold tuned on the holdout: simple, and the keep rule favours it on a tie.
- **Choice and why:** kept the threshold. With the dev runner, threshold 0.70 gave 0.9649 and the DP (shift -0.25) gave 0.9647: delta -0.00024, CI [-0.00091, +0.00049], p_better 0.234. The DP was not better.
- **Evidence** (dev kit, fold 0, 27,651 S1, [M]): the dev runner as above, and the official evaluator reproduced 0.96492 (precision 0.988, recall 0.929, singleton F0.5 0.953, 3.26 predicted per S1, India 0.952, US 0.974) [[G6 record](../../../docs/decisions/2026-09-25_1731_gate-g6-dp-vs-threshold.md)]. Through the pipeline stages at 18:00 (threshold 0.71): 0.96517, DP 0.96473, delta -0.00044, CI [-0.00107, +0.00022], p_better 0.101 (same record). On model v2 calibrated pc at 20:55 (dev kit v2): threshold 0.67 gave 0.98438, DP 0.98447, delta +0.00010, CI [-0.00023, +0.00045], p_better 0.714 (same record; S-X-15). [PR #16] reports 0.9648 and a delta of -0.0002; [PR #17] reports 0.9652 and -0.0004.
- **Outcome:** the baseline shipped with the threshold. Ameya's later gate on the full holdout with calibrated stage-2 probabilities gave the DP +0.00018, CI above 0 [R].
- **Hindsight:** DP minus threshold went from -0.00044 (stage-1 probabilities) to +0.00010 (model v2, dev fold 0) to +0.00018 (Ameya, full holdout): the verdict depended on the probabilities, as the record itself warned. No run of mine met the +0.002 bar. The record also noted a test shift: the threshold was tuned at 4.68 S2/S3 records per S1 on train, and test has 5.75; any adjustment was left to gate G8.
- **Links:** [G6 record](../../../docs/decisions/2026-09-25_1731_gate-g6-dp-vs-threshold.md) · `ber.model` · [PR #16] (opened by me) · [PR #17] (opened by Ameya, carrying my follow-up commit)

### S-D-02 · Compute ownership over every S1 of a record
- **When (IST):** 2026-09-25 about 17:50 · **Phase:** P1 · **Area:** DEC
- **Decided by:** Sachi
- **Status:** adopted
- **Problem:** my first ownership step ([PR #16]) took the argmax over holdout S1s only, so a record whose best S1 sat in a training fold looked owned by a holdout S1. [PR #17] calls this "the holdout-only ownership bug from #16".
- **Options considered:**
  1. Argmax over holdout S1s only: quick, but wrong, because test has no hidden S1s to leave out.
  2. Argmax over all S1 candidates of each record, training folds included: matches how test behaves.
- **Choice and why:** option 2, so the holdout score reflects the test setting.
- **Evidence:** the [G6 record](../../../docs/decisions/2026-09-25_1731_gate-g6-dp-vs-threshold.md) says its numbers were updated at 17:52 after the fix: "An earlier run took the argmax over holdout S1s only; it was fixed before these numbers were produced." The size of the effect is **not isolated** [U]. [PR #16] reports 0.9648 and delta -0.0002, the record 0.9649 and -0.00024, which are almost the same. [PR #17]'s table shows 0.9648 then 0.9652 and credits the fix, but 0.9652 is the 18:00 pipeline-stage run (threshold 0.71) and the dev runner used 0.70. [PR #16] says 0.9648 where the record's evaluator says 0.96492.
- **Outcome:** `ber.model` uses it, and Ameya carried it into main through [PR #17]. The final chain has its own ownership code.
- **Hindsight:** I should have run the same script before and after the fix. The G6 record was updated in place, so no clean before and after pair exists.
- **Links:** `ber.model` · [PR #16] · [PR #17]

### S-D-03 · Reject the name-uniqueness features
- **When (IST):** 2026-09-25 21:15 (the record's Date field; its file name says 2111) · **Phase:** P1 · **Area:** FEA
- **Decided by:** Sachi
- **Status:** rejected
- **Problem:** error analysis of model v2 (dev fold 0) showed that 61% of below-threshold misses and 98% of records taken by another S1 have an empty address. Hypothesis: an exact name that no other S1 in the country shares is trustworthy even without an address.
- **Options considered:**
  1. Stage 1 on the 79 v2 features (`sachi-s1-fx2-dev`): macro F0.5 0.97745.
  2. The same plus five name-uniqueness columns (`ctx__s1_core_n`, `ctx__r_core_n`, `name__core_eq`, `name__core_eq_unique`, `addr__r_empty`; the counts use S1 only, so they could be built on test): 0.97800.
- **Choice and why:** not kept. Delta +0.00054, CI [+0.00001, +0.00107], p_better 0.975, n 27,651: real, but far below the +0.002 bar.
- **Evidence** (dev kit v2, fold 0, [M], [name-uniqueness record](../../../docs/decisions/2026-09-25_2111_gate-name-uniqueness.md)): among the 3,779 true candidate pairs with an empty record address (4.0%): exact and unique name, 1,439 pairs, found 95.8% before and 98.5% after, so little headroom; exact name shared by two or more S1, 1,126 pairs, found 2.8% before and 1.6% after, ambiguous by construction (abstaining is correct under F0.5); name not exact, 1,214 pairs, 52.6% before and 52.1% after, the only part with headroom (about 0.6% of true pairs).
- **Outcome:** not used in any later version. The record concluded that empty-address losses are mostly a data limit, and that gate G5 (softmax ownership) has low expected value because "taken by another S1" is only 0.26% of true pairs. It added that the five columns could be offered if stage 2 were retrained anyway; they were not.
- **Hindsight:** two days later the copy-count test (S-X-09) reached the same conclusion for the shared-name empty-address group: coin flips, so abstaining is right. Whether Ameya's rival counts already covered the unique-name signal: unknown. Under the CI-only rule my [PR #27] description later used (delta above 0, CI lower bound above 0), this result (CI lower bound +0.00001) would just have passed; the record judged it against the +0.002 bar (Q-25).
- **Links:** [name-uniqueness record](../../../docs/decisions/2026-09-25_2111_gate-name-uniqueness.md) · `experiments/sachi/add_name_uniqueness.py`, `check_name_uniqueness.py`

### S-D-04 · Study why an unseen country is worse, one feature group at a time
- **When (IST):** 2026-09-26 10:00 to about 13:00 · **Phase:** P2 · **Area:** FRA
- **Decided by:** Sachi, after Ameya's note that the unseen-country residual was about 0.024
- **Status:** adopted as a study; no code change followed
- **Problem:** train on one country, test on another gave a lower score. Could one feature group be the cause?
- **Options considered:**
  1. Leave-one-country-out ablation by feature group (`loco_groups.py`).
  2. Add generator edit-profile features and test them on the unseen country (`loco_profile.py`).
  3. Do nothing and wait for France labels (impossible).
- **Choice and why:** 1 and 2 are cheap on the dev kit and give a measured answer. The bar for a candidate was +0.003 on the unseen country at a realistic threshold with under 0.001 in-country cost.
- **Evidence:** no feature group explained the gap (about 0.028 in my run; Ameya quoted 0.024 earlier) [M, dev kit v2, US to India] [chat:sachi/web-2 2026-09-26 12:50]. Edit-profile features: +0.0005 against the +0.003 bar [M, same] same source.
- **Outcome:** no action. Ameya's later study (word-odds features missing in an unseen country) explains the drop better.
- **Hindsight:** the gap size differs between my run (0.028) and Ameya's note (0.024): unknown why.
- **Links:** `experiments/sachi/loco_groups.py`, `loco_profile.py`

### S-D-05 · Look for new France rules, label-free, before building more
- **When (IST):** 2026-09-26 about 12:52 to 13:04 · **Phase:** P2 · **Area:** RUL
- **Decided by:** Sachi
- **Status:** adopted as a study; no new rule
- **Problem:** France has no labels. Are there French patterns the rules do not yet cover?
- **Options considered:** run hypothesis tests on France kit v1 with US/India truth rates (`france_discover.py`, `france_hypotheses.py`, `france_hyp_split.py`), or write new rules on a hunch.
- **Choice and why:** test hypotheses first, so a rule is only added if the same pattern is clearly true or false in the labelled countries.
- **Evidence:** the empty-address and unique-name pattern was already handled well by the model. French names collide far more than US/India (groups of 100 to 200 or more S1 sharing a name). Remaining candidate patterns landed at 63 to 88 percent true, too uncertain for a rule [M, France kit v1, older model] [chat:sachi/web-2 2026-09-26 13:04].
- **Outcome:** no new rule candidates after rules v2.
- **Hindsight:** none beyond noting the kit came from an older model.
- **Links:** `experiments/sachi/france_discover.py` and the two siblings

### S-D-06 · Run model comparisons on a rented GPU, not the 8 GB laptop
- **When (IST):** 2026-09-26 17:04 to 21:40 · **Phase:** P3 · **Area:** ORG
- **Decided by:** Sachi
- **Status:** adopted
- **Problem:** `ce_compare.py` failed on my laptop three times.
- **Options considered:**
  1. Shrink the run (batch 4, length 48, 5,000 pairs): cheap, but only a rough answer.
  2. Hand the experiment to Ameya: costs his GPU time.
  3. Rent a single RTX 3090 (about $0.2 to $0.4 per hour).
- **Choice and why:** option 3, because the three failures were memory, not code. The first was a stalled download that never timed out, the second a kernel kill on an 8 GB machine with background virtual machines running, the third a load average of 22.8 with a 9.1 GB process (the script read the whole 12.5M-row training file).
- **Evidence:** failure details [M] [chat:sachi/web-3 2026-09-26 17:04 to 18:28]. Run time on the GPU: e5-small 1.28 minutes, e5-base 3.20 minutes [M] same.
- **Outcome:** the comparison finished (S-X-06). Hosting needed three rentals before one worked (two hosts failed to pull the container image or lacked my access key).
- **Hindsight:** I should have read the script's loading code before the first run. The memory problem was visible in it.
- **Links:** `experiments/sachi/ce_compare.py`

### S-D-07 · Build a LoRA Qwen2.5-1.5B cross-encoder in the e5 trainer's format
- **When (IST):** 2026-09-26 about 22:30 to 23:30 · **Phase:** P3 · **Area:** CE
- **Decided by:** Sachi, proposed to Ameya's pipeline through the band files he shared
- **Status:** adopted by the team (became `qst`)
- **Problem:** the e5 and bge cross-encoders plateau near the same band AUC. Could a different model family add diversity?
- **Options considered:**
  1. Zero-shot LLM judge (up to 8B): Ameya's own test of Qwen2.5-7B-Instruct gave AUC 0.537 [R] (his research notes), so no.
  2. Full fine-tune of a 1.5B model: too large for a 24 GB card with a usable batch.
  3. LoRA (rank 16) on Qwen2.5-1.5B as a sequence classifier: fits a 4090.
  4. Qwen2.5-3B: not Apache-2.0, so not allowed.
- **Choice and why:** option 3, reading the same `band_{train,test}.parquet` as `ce_box.py`, with the same out-of-fold groups and output files, so Ameya's `ce_import.py` accepts it unchanged. Apache-2.0, under 8B.
- **Evidence:** my partial run reached out-of-fold AUC 0.9279 in group 1 with 35 percent of the data [M, band] [chat:sachi/web-3 2026-09-27 02:30]. Ameya's own `qst` run reached 0.9334 in group 0 [R] (`docs/status/ameya.md`, 27 Sep). `qst` is in v7sq, public LB 0.990545 [R].
- **Outcome:** `ce_llm.py` is the base for `qst` and for Bakshi's `q7st` (7B).
- **Hindsight:** the value came from diversity, not size: the 7B's band AUC (0.9436) equals e5-large's (0.9439) [R]. I did not test that myself.
- **Links:** `experiments/sachi/ce_llm.py` · `ce_llm_st.py` docstring · S-X-07

### S-D-08 · Stay inside the GPU credit by choosing cheap cards and small fractions
- **When (IST):** 2026-09-27 08:26 to 09:14 · **Phase:** P4 · **Area:** ORG
- **Decided by:** Sachi
- **Status:** adopted
- **Problem:** about $7.8 of credit left; an H100 costs about $2 per hour and a 7B run was uncertain.
- **Options considered:** H100 with 20 percent of the data; RTX 4090 with 15 percent of the data.
- **Choice and why:** RTX 4090 at about $0.4 per hour, `--train-frac` 0.15, so the whole run fits with a margin.
- **Evidence:** credit $7.90 at 08:26 and $7.82 at 09:13 [R] [chat:sachi/web-3 2026-09-27 09:13].
- **Outcome:** a smoke test of the 7B ran clean on the 4090; the full run was never completed on my side (S-X-08).
- **Hindsight:** a 7B LoRA run is slow on a 24 GB card. Ameya and Bakshi ran it on H100s, which is the right size.

### S-D-09 · Stop my synthetic-French run when Ameya ran the same job
- **When (IST):** 2026-09-27 after about 15:00, exact time unknown · **Phase:** P4 · **Area:** FRA
- **Decided by:** Sachi, after reading [issue #63]
- **Status:** adopted
- **Problem:** Ameya's side was running synthetic e5-large (cesy2) on faster GPUs. Mine would finish about two hours later.
- **Options considered:** let it finish; stop and keep the credit for a corrected generator (synth3).
- **Choice and why:** stop. My run was at step 9,800 of 26,609 in group 0 with about 52 minutes left for that group alone, at about $0.6 per hour.
- **Evidence:** log tail [M] [chat:sachi/web-3 2026-09-27 14:25] and the machine screenshot at 14:42 (GPU 96 percent, credit $5.48) [R].
- **Outcome:** the results of the synthetic models came from Ameya's runs (S-X-10).
- **Hindsight:** none.

### S-D-10 · Close three French ideas with labelled audits instead of arguing them
- **When (IST):** 2026-09-27 13:24 to 18:48 · **Phase:** P4 · **Area:** FRA, DEC
- **Decided by:** Sachi
- **Status:** the first two audits closed their ideas; the third changed meaning (see S-D-11)
- **Problem:** three untested ideas aimed at the French errors: copy counts to break empty-address ties; per-record renormalisation of French probabilities; department versus region formats.
- **Options considered:** spend upload slots, or measure on the labelled holdout and the France kit.
- **Choice and why:** measure, because uploads were scarce and each audit needed no GPU.
- **Evidence:** see S-X-09, S-X-11, S-X-12.
- **Outcome:** copy counts: closed (coin flips). Tie renormalisation: closed (neutral to negative). Departments: closed, with a weak check (the heuristic was crude).
- **Hindsight:** my first tie-audit run had an artefact (S-X-11). Reading raw numbers without checking what was counted cost an hour.

### S-D-11 · Read the street-swap result as a reason to gate the French drop on the 7B
- **When (IST):** 2026-09-27 18:48 to 20:20 · **Phase:** P4 · **Area:** LLM
- **Decided by:** Sachi (analysis), Ameya (the rule)
- **Status:** adopted
- **Problem:** Ameya found French false merges of generic names at one house number on different streets. Should a rule drop them by pattern?
- **Options considered:** drop by pattern alone; drop only where the 7B also rejects the pair.
- **Choice and why:** my check showed that in the labelled holdout this pattern is 99.9 percent true where the model keeps it, so a pattern-only drop would remove real copies. The 7B check separates the cases (Ameya's table), so the drop is gated on it.
- **Evidence:** [M, France kit v1, older model] different-street pattern 23.2 per 1,000 S1 in the holdout, 99.9 percent true and 99.9 percent predicted; France keeps only 51.5 percent of the same pattern (6.56 per 1,000 French S1, median pc 0.75). Ameya's table: of 380 pairs kept by the model 99.7 percent are true, 7B median +7.9; of 218 rejected by the model 0.5 percent are true, 7B median -9.9, 202 below -6 [R] ([issue #64]).
- **Outcome:** Ameya recorded my check as one of three supports for the French 7B drop ([issue #64]). Composite B scored 0.990879 on the public LB [M].
- **Hindsight:** my first reading of the result was that France was "under-keeping" true copies and a drop would hurt. The table that included the model-rejected pairs showed that was incomplete: my script only looked at candidates with pc of at least 0.3, so the decoys the model rejects near zero were outside the view.
- **Links:** `experiments/sachi/street_swap.py` · S-X-13

### S-D-12 · Back mixf2 over mixf4 for the final upload
- **When (IST):** 2026-09-27 20:10 to 20:25 · **Phase:** P4 · **Area:** SUB
- **Decided by:** Ameya (the upload). Sachi argued for mixf2.
- **Status:** adopted at the time, then reversed by the leaderboard
- **Problem:** two candidates within about 10e-6 of each other on estimators.
- **Options considered:** mixf2, mixf4 (adds a round-4 model and a France DP), and Composite B as the fallback.
- **Choice and why:** my reasons: the gap is below the public noise (about 5e-5); own-cal pointed the other way (+122 against +127); the DP had been called neutral earlier; more self-training rounds were the main known risk.
- **Evidence:** [issue #64] estimator table.
- **Outcome:** mixf2 scored 0.990819, below Composite B at 0.990879 and below mixf7 at 0.990833 [M, public LB] ([issue #64] at 22:15). Ameya's decomposition: the pc-based cal over-valued round 3 by about 115e-6 and the France DP carried about +51e-6 of B's edge.
- **Hindsight:** I argued that the DP was probably noise. It was real. My caution about extra self-training rounds was right in direction but I applied it only to round 4.
- **Links:** [issue #64]

### S-D-13 · Keep the unused local patch out of the repo
- **When (IST):** 2026-09-29 00:40 · **Phase:** P5 · **Area:** PKG
- **Decided by:** Sachi
- **Status:** adopted
- **Problem:** my local `ce_llm.py` had a `--test-once` edit used only for my own 7B runs. The version on main is the one Ameya imports.
- **Options considered:** commit it; stash it.
- **Choice and why:** stash it, so the repo copy stays identical to what built `qst`.
- **Evidence:** `git diff` against main showed only that flag; one commit on main for the file ([commit 5bff1e7]) [M] [chat:sachi/web-3 2026-09-29 00:35].
- **Outcome:** [issue #66] item A answered.
- **Hindsight:** none.

### S-D-14 · Do not add an mDeBERTa cross-encoder on the final day
- **When (IST):** 2026-09-27 08:28 to about 08:45 · **Phase:** P4 · **Area:** CE
- **Decided by:** Sachi (after Ameya's PR comment that the stack was frozen)
- **Status:** rejected before any run
- **Problem:** with a free RTX 4090 and about $7.8 of credit, I wanted a fifth model family (microsoft/mdeberta-v3-base, MIT, 278M) for the cross-encoder mean.
- **Options considered:** train it with Ameya's `ce_box.py` and hand over the logits; or skip it.
- **Choice and why:** skip. Ameya reported every model landed and stacked, 12 of 12 audits passing. Adding a fifth input would mean redoing the z-mean, a stage-2 retrain, a gate and the audits on the last day, for a gain nobody had measured.
- **Evidence:** none measured. The reasoning rests on [issue #45] and the PR #58 comment [R].
- **Outcome:** the machine was released without a run.
- **Hindsight:** the later leaderboard results showed that even tested extra models and rounds could lose (mixf2, mixf7), which supports the call.
- **Links:** [PR #58]

### S-D-15 · Do not rebuild the whole pipeline on a rented 192-core machine
- **When (IST):** 2026-09-26 about 21:56 to 22:10 · **Phase:** P3 · **Area:** ORG
- **Decided by:** Sachi
- **Status:** rejected after the machine was rented
- **Problem:** I wanted a clean end-to-end rerun of the v6all recipe (roadmap task 4.1) with e5-base swapped in, and rented a machine with 192 cores, 503 GB of memory and an RTX 3090.
- **Options considered:** rerun the full chain (about 3 to 4 hours of compute plus uploads); stop and read what Ameya had pushed.
- **Choice and why:** I pulled main first and found his decision record for v7ce3 (+0.000311 holdout over v6all, [R] with a confidence interval above zero) and his large-machine handover. He had already run e5-base and e5-large through the real pipeline. A rerun would only have reproduced a smaller version of it.
- **Evidence:** [chat:sachi/web-3 2026-09-26 22:05] pull of main; decision record `2026-09-26_1933_model-v7ce3.md`.
- **Outcome:** no run on that machine. Cost: a short rental, amount unknown.
- **Hindsight:** I should have pulled main before renting. The pull that showed the overlap came after the rental.
- **Links:** S-X-06

### S-D-16 · Keep the stage-2 collective model (gate G4)
- **When (IST):** 2026-09-25 21:03 · **Phase:** P1 · **Area:** MDL
- **Decided by:** Sachi (the gate). Ameya built model v2 and its stage 2.
- **Status:** adopted
- **Problem:** does the stage-2 collective model beat stage 1 alone (plan §9, gate G4)?
- **Options considered:** 1. stage 1 only (`sachi-s1-fx2-dev`, threshold 0.68): macro F0.5 0.97745. 2. stage 1 plus stage 2 (`ameya-s2-v2-dev` pc, threshold 0.67): 0.98438.
- **Choice and why:** keep stage 2. Same 79 features (`ameya-fx2-dev`), dev fold 0, 27,651 S1, paired bootstrap with 1,000 resamples.
- **Evidence** ([M], dev kit v2, fold 0, [G4 record](../../../docs/decisions/2026-09-25_2103_gate-g4-stage2.md)): delta +0.00692, CI [+0.00622, +0.00772], p_better 1.000 (bar +0.002 with CI above 0). Stage 2 lifts singleton F0.5 from 0.968 to 0.985 and recall from 0.949 to 0.963. Of v2's gain over v0 (0.9652 to 0.9844), about two thirds came from the 79 features and one third from stage 2.
- **Outcome:** stage 2 stayed in every later version. The record left a full-holdout re-check to the integration run; I do not have one of my own: unknown.
- **Hindsight:** the comparison is between a stage 1 I trained and a stage 2 Ameya trained, on the same features. That tests the architecture fairly, but either side could have been tuned differently.
- **Links:** [G4 record](../../../docs/decisions/2026-09-25_2103_gate-g4-stage2.md) · S-X-16

### S-D-17 · Port Ameya's v3 chain into `ber.model`
- **When (IST):** 2026-09-25 23:36 to 2026-09-26 10:09 (draft description at 10:09) · **Phase:** P2 · **Area:** MDL
- **Decided by:** Sachi, after Ameya's agent asked on 2026-09-25 23:29 (its first priority for me)
- **Status:** adopted; merged as [PR #27]
- **Problem:** the real model lived only in `experiments/ameya/model-v1`; the final ZIP needs `code/` that reproduces the result, and the pipeline's train, predict and decide stages ran stage 1 only.
- **Options considered:**
  1. Port the files line by line into `ber.model`, changing only input and output.
  2. Leave the chain in `experiments/` and document it.
  3. Rewrite it inside `ber.model`.
- **Choice and why:** option 1, so numbers stay comparable with Ameya's reference. Per the draft description: explicit feature groups instead of a module global, so it no longer needs about 19 GB in memory; train, predict and decide default to v3 (`--set model=v0` keeps the old path); the decide stage applies gate G6 with delta above 0 and CI lower bound above 0, ties to the threshold, and saves the rule for test [R].
- **Evidence:** 74 tests pass (43 existing plus one new: `expected_f_select` against brute force, 30 random cases, n at most 6); tested end to end on synthetic data in the C8, C5 and C9 formats; "not yet run on real data" when written [R] [chat:sachi/web-2 2026-09-26 10:09].
- **Outcome:** merged as [PR #27]. Composite B did not use it: its drivers call only the records, block and write stages ([issue #66] check B). Whether the ported chain was ever run on full features: unknown.
- **Hindsight:** the port made the repo's own pipeline stages run the full v3 chain, but the submission came from Ameya's original chain. I have no evidence that the port reproduced his numbers.
- **Links:** [PR #27] · S-D-01 · Q-25
