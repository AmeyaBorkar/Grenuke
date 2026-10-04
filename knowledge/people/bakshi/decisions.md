# Decisions: bakshi

Every decision Bakshi made or influenced, including options rejected and things decided *not* to do (`knowledge/STANDARD.md` §2.1). Local IDs are `B-D-NN`; the curator maps them to global IDs. "Agent for Bakshi" means his Codex agent (25–27 Sep) or his Claude Code agent (27 Sep onward); the source ID says which.

**Summary.** On day 1 Bakshi's agent built normalisation and string features that the final chain never used (B-D-03 to B-D-06). On 26 Sep Bakshi chose to build a France-focused "v7" alone; every rule it tried failed its gate (B-D-07 to B-D-09). From the night of 26 Sep he steered the final day: a low-cost plan, a handover to Claude, then rented GPUs, Qwen2.5-7B, the 7B re-check and Composite B, the team's best public score (B-D-10 onward).

### B-D-01 · No competing plan (Plan C) from Bakshi
- **When (IST):** 2026-09-25 12:21–14:15 · **Phase:** P0 · **Area:** ORG
- **Decided by:** unknown; no plan was submitted. The agent for Bakshi wrote a kick-off strategy in chat.
- **Status:** not submitted (`plans/README.md`: "C | Member 3 | none | not submitted").
- **Problem:** each member was to write `plans/<member>/PLAN.md` for the 14:15 decision meeting.
- **Options considered:**
  1. Turn the agent's 12:31 strategy into Plan C: multi-view retrieval per source, an oracle ceiling, CatBoost on hard negatives, a threshold tuned on exact macro F0.5, an explicit no-match decision, optional e5 embeddings [chat:bakshi/01a0d754 2026-09-25 12:31].
  2. Submit nothing (what happened).
- **Choice and why:** unknown. Context: at 14:30 Ameya's status was still waiting for "Member 3 (@trustdemons05)" to confirm name and ownership; Bakshi was added to `docs/TEAM.md` at 15:46; his agent reached the private repo only at 16:23 [chat:bakshi/01a0d828 2026-09-25 16:25].
- **Evidence:** the strategy's main points (per-S1 F0.5 tuning, multi-view blocking with measured recall and oracle, no country feature, an explicit no-match decision) are already in `plans/FINAL_PLAN.md`, written independently. The differences were CatBoost vs XGBoost and e5 as a retrieval signal vs a cross-encoder [E, comparison].
- **Outcome:** nothing from the strategy entered the repo.
- **Hindsight:** for Bakshi to answer (open-questions.md).
- **Links:** `plans/README.md` · `plans/DECISION.md`

### B-D-02 · A stand-alone prototype while the repo was unreachable
- **When (IST):** 2026-09-25 15:15–15:56 · **Phase:** P1 · **Area:** ORG / BLK
- **Decided by:** agent for Bakshi, reading his "continue with the plan" as "build and test a model" [chat:bakshi/01a0d754 2026-09-25 15:56]. Bakshi did not choose it.
- **Status:** abandoned when Bakshi intervened ("what are you even doing", 15:55).
- **Problem:** the team repo was private and returned 404; there was no team pipeline to work in.
- **Options considered:** wait for access; or continue "the local baseline while that's clarified" (chosen) [chat:bakshi/01a0d754 2026-09-25 15:19].
- **Choice and why:** measure retrieval recall first, because "the matcher cannot recover a true match that never reaches it".
- **Evidence:** a SQLite FTS5 full-pool probe on 400 sampled train S1 reached pair recall 0.826 → 0.911 (US 0.973, India 0.838) with a cross-field name-AND-address route; 85 of 100 remaining misses were India, 33 of 100 had a script change [M, 400 S1] (B-X-02).
- **Outcome:** nothing committed; about 40 minutes of agent time.
- **Hindsight:** the probe's finding (India recall lost to script changes and partial addresses) is the same one the team acted on with its own transliteration (D-NRM-02), but it was never shared [E].
- **Links:** B-X-01, B-X-02

### B-D-03 · Do the work assigned to Bakshi (issues #6, #7)
- **When (IST):** 2026-09-25 16:29 · **Phase:** P1 · **Area:** ORG
- **Decided by:** Bakshi: "yea go ahead if you see any work assigned to aarush bakshi / bakshi just do it" (proposed by: agent for Bakshi, after it found the stubs) [chat:bakshi/01a0d754 2026-09-25 16:29].
- **Status:** adopted.
- **Problem:** the plan gave Bakshi normalisation (contract C3) and string pair features (C8). Both were `NotImplementedError` stubs at `e955810`.
- **Options considered:** continue the prototype; or implement #6 and #7 on `bakshi/` branches (chosen).
- **Choice and why:** this was the team plan (`docs/TEAM.md`).
- **Evidence:** issue #7: "start after normalize, around 18:00", due Fri 21:00, "about 30 features" [R] [chat:bakshi/01a0d828 2026-09-25 16:30].
- **Outcome:** PR #20 merged 25 Sep 20:55; PR #21 merged 26 Sep 10:12. Neither was used by the final chain (B-D-06).
- **Links:** issues #5, #6, #7 · [PR #20] · [PR #21]

### B-D-04 · Normalisation v0 design (C3)
- **When (IST):** 2026-09-25 16:36–17:02 · **Phase:** P1 · **Area:** NRM
- **Decided by:** agent for Bakshi, implementing `plans/FINAL_PLAN.md` §4.2 and issue #6. No design input from Bakshi is recorded.
- **Status:** delivered and merged ([PR #20]); not used by the final chain.
- **Problem:** produce the C3 columns for all 24.2M records on a 16 GB laptop, with no external data.
- **Options considered and choices:**
  1. Streaming batches with a process pool (8 workers) and atomic Parquet output, one row per record, `country` kept as an open set.
  2. Hand-written, country-agnostic lexicons: 26 legal-form variants, honorifics, street types for US/India/France, US and Indian states, the 13 French regions. Ambiguous abbreviations (CA, IN, GA) left as they are.
  3. Indic text: the team's own offset-table transliteration ("intentionally phonetic and lossy"), 9 Brahmic blocks.
  4. Addresses: street, city, state, house number and suffix, unit, flags (empty, PO box, null, arrondissement…); no postcode field.
  5. After reading 20 sampled rows per country, a fix for addresses that put the city or state before the street ("NY, Islip, 235 Furrows Road"), re-run under a new tag `bakshi-norm-v0a` [chat:bakshi/01a0d754 2026-09-25 17:02].
- **Choice and why:** the plan's v0 field list, within the laptop's memory.
- **Evidence:** 29 columns; train 12,527,040 rows in 484.2 s, test 11,702,133 in 516.1 s; 40 tests [M] ([handover](../../../docs/handover/2026-09-25_1658_bakshi_normalize-v0.md)). The address fix on the first 100k train rows: state present 0.859 → 1.0, city longer than 5 words 0.006 → 0.0 [M] [chat:bakshi/01a0d754 2026-09-25 17:16].
- **Outcome:** a review in Ameya's session found three parsing bugs (direction letters read as house-number suffixes, leading legal forms stripped, Cedex/department parsing) (F-NRM-01). French departments were not mapped to regions. The chain never read these columns, so the bugs cost nothing.
- **Hindsight:** French and Indian addresses needed their own test cases from the first version.
- **Links:** B-X-03 · [components/normalisation.md](../../components/normalisation.md)

### B-D-05 · String features v0 design (C8): 56 vectorised features
- **When (IST):** 2026-09-25 17:05–21:41 · **Phase:** P1 · **Area:** FEA
- **Decided by:** agent for Bakshi, implementing `FINAL_PLAN.md` §4.4 and issue #7.
- **Status:** delivered and merged ([PR #21]); not used by the final chain.
- **Problem:** name, number and address similarities for millions of pairs, with no Python loop over pairs and no country feature.
- **Options considered and choices:**
  1. `rapidfuzz.process.cpdist` scorers, token CSR arrays with a compiled pair kernel, numba number-set kernels.
  2. IDF fitted on fixed-seed per-country samples of unlabelled records; country "never emitted as a feature".
  3. 56 float32 features in four groups: `name__` 18, `extra__` 7 (unexplained tokens after typo absorption), `num__` 15, `addr__` 16.
  4. Ameya's 15 context features joined over the complete candidate set, so rivalry counts stay exact across batches.
  5. After profiling showed repeated tokenisation of the same S1 strings: each distinct text processed once per batch.
- **Choice and why:** issue #7 required about 3M dev pairs in under 5 minutes; the first run took 434 s, so the agent profiled and deduplicated.
- **Evidence:** 3,212,547 dev pairs (372,902 positive) in 434.4 s → 214.4 s; peak RSS 4.28 → 5.89 GiB; values verified identical; 100 tests [M] [chat:bakshi/01a0d754 2026-09-25 21:28], [handover](../../../docs/handover/2026-09-25_2056_bakshi_features-v0.md). No F0.5 was claimed: the first probe had only true pairs, so separation was never tested.
- **Outcome:** merged 26 Sep 10:12; no gate ever measured its value (D-FEA-07).
- **Links:** B-X-04 · [components/features.md](../../components/features.md)

### B-D-06 · Bakshi's v0 stages were not wired into the final chain (context, not his decision)
- **When (IST):** implicit, from 25 Sep evening · **Phase:** P1–P2 · **Area:** FEA / NRM
- **Decided by:** unknown (D-FEA-07 records it as implicit).
- **Status:** adopted in practice.
- **Problem:** the plan had Bakshi own C3 and C8, but the model chain grew in `experiments/ameya/model-v1/` with its own tokenizer and features.
- **Facts:**
  - Ameya's blocking had its own transliteration by 16:21 on 25 Sep (D-BLK-04); his model-v1 features scored local holdout 0.9801 by 18:00.
  - Bakshi's normalisation was due 18:00 and reached `main` at 20:55. His session lost about 65 minutes to repo access (15:17–16:23) and sat stalled from 17:22 to 20:37 when the agent's automatic approval reviewer hit a usage limit [chat:bakshi/01a0d754 2026-09-25 17:22], [chat:bakshi/01a0d754 2026-09-25 20:37].
  - On 26 Sep Bakshi's agent found it itself: "The final competition chain uses Ameya's `feats.py` … rather than the standalone C3/C8 stages we developed" [chat:bakshi/01a0dd05 2026-09-26 14:58].
- **Outcome:** Composite B does not depend on `ber/normalize` or the C8 string groups.
- **Hindsight:** day-1 modules were delivered, tested and merged but unused; Bakshi's contribution to the result came on 27 Sep.
- **Links:** D-FEA-07 · D-ORG-09 · D-ORG-10

### B-D-07 · Build "v7" alone instead of submitting v6
- **When (IST):** 2026-09-26 15:28 · **Phase:** P3 · **Area:** SUB / FRA
- **Decided by:** Bakshi: "we wont submit v6 we will submit v7 and i am working on this alone from now on so we need to create a v7 that boosts are rank from 15 to somewhere near 5" [chat:bakshi/01a0d754 2026-09-26 15:28]. His agent had proposed the opposite.
- **Status:** adopted for Bakshi's own work; the team uploaded v6all anyway (public LB 0.988609, 26 Sep #02).
- **Problem:** the team was 15th (public LB 0.98781, v5all). Bakshi asked for a "wow factor" route to 99%+.
- **Options considered:**
  1. Agent's plan (15:28): Ameya submits v6all (holdout 0.990788, +0.00063 [0.00057, 0.00070] over v5all [M]); Bakshi does address checks; each France change tested alone against v6all; one upload reserved to restore the best.
  2. Bakshi builds a separate v7 (chosen).
- **Choice and why:** Bakshi wanted a bigger jump than v6all; no reason beyond the rank target is recorded.
- **Evidence:** a pasted review (author not named, likely Ameya's side) cut the agent's five ideas to two: a light composed-edit rule and an address check before rule-based additions [chat:bakshi/01a0d754 2026-09-26 15:26].
- **Outcome:** every v7 rule failed its gate (B-D-08); the only candidate file (B-D-09) was never uploaded. Meanwhile Ameya's v7n / v7nst line moved the team to rank 7.
- **Hindsight:** working alone duplicated effort; the gains came from the shared pipeline.
- **Links:** B-X-05 to B-X-11 · [PR #34] · [PR #37]

### B-D-08 · Keep the v7 composed-edit, address-guard and rescue rules disabled
- **When (IST):** 2026-09-26 15:45–16:16 · **Phase:** P3 · **Area:** RUL / FRA
- **Decided by:** agent for Bakshi, on evidence.
- **Status:** adopted (all disabled).
- **Problem:** do composed name edits, a full-address guard, or exact-key rescues improve v5?
- **Options considered:** enable any of them; keep them as diagnostics (chosen).
- **Evidence:**
  - the address guard rejects 3 true additions in the dev sample; one proposed rule passes at only 0.79 precision [M, devkit-v3 dev] [chat:bakshi/01a0d754 2026-09-26 15:45];
  - only 18 France predictions in v5 fall in the composed-edit categories [E, test count] [chat:bakshi/01a0dd57 2026-09-26 16:21];
  - exact rescue: 0 dev residuals, 2 ambiguous France transfers on test; street rescue: 12 test changes, 7 of which differ in later house-number parts [chat:bakshi/01a0d754 2026-09-26 16:16].
- **Outcome:** draft PR #34 (diagnostics, merged by a human) and the v5 audit in PR #37.
- **Links:** B-X-05, B-X-07, B-X-08

### B-D-09 · A France-only v7 probe from Ameya's robust-address rule, with repetition protection; upload left to the humans
- **When (IST):** 2026-09-26 16:24–16:43 · **Phase:** P3 · **Area:** RUL / FRA
- **Decided by:** agent for Bakshi (proposed and built); the upload decision was left to the humans.
- **Status:** built (draft [PR #37]); never uploaded.
- **Problem:** after the rescues failed, Ameya's rules-v3 "robust-address op B" (commit `717f00b` on `ameya/research-v6`) was the strongest measured France lead.
- **Options considered:** apply it as is; or apply only its extra France drops, with no additions, and protect names that repeat a word (chosen).
- **Evidence:** on the devkit-v3 dev gate (n = 27,651 S1) the rule as is cost −1.08e-05 [CI −2.64e-05, 0]; all 18 wrongly dropped true pairs repeated a name word ("Pinnacle Asset Group" vs "Pinnacle Asset Asset"). With whole-token repetition protection the gate delta is 0 [M, dev sample] [chat:bakshi/01a0dd57 2026-09-26 16:28], [chat:bakshi/01a0dd57 2026-09-26 16:33]. On test it drops 1,148 France pairs over 1,137 S1, US/India unchanged; validator PASS [E].
- **Outcome:** its France effect was never measured. The repetition guard did not fire on test (0 protected), so it changed only the dev gate.
- **Links:** B-X-09, B-X-10 · handover `docs/handover/2026-09-26_1637_bakshi_v7-france-probe.md`

### B-D-10 · A low-cost route to 0.991: Tracks A/B/C, no new GPU rentals
- **When (IST):** 2026-09-26 23:47–27 Sep 00:00 · **Phase:** P3 · **Area:** SUB / CE
- **Decided by:** Bakshi set the goal ("win .991 … for as low cost as possible") (proposed by: agent for Bakshi, Codex) [chat:bakshi/01a0d754 2026-09-26 23:47], [chat:bakshi/01a0d754 2026-09-26 23:53].
- **Status:** adopted as the night plan; superseded on 27 Sep by v7sq-dpc and the final push.
- **Problem:** v7nst had just scored public LB 0.990179; 0.991 needed +0.000821, or about +0.0055 France F0.5 [E].
- **Options considered:**
  1. Track A: French threshold probes on v7nst (fr080r / fr090r / fr095r).
  2. Track B: family-balanced cross-encoder votes (count the two e5-large runs as one family, add bge).
  3. Track C: expensive inference only where model families disagree.
  4. Rent more GPUs.
- **Choice and why:** A and B at $0; C cut by a teammate-side review that Bakshi pasted in (author not named) [chat:bakshi/01a0d754 2026-09-26 23:59].
- **Evidence:** fr090r would change 7,190 French S1, a ceiling of ±0.0041 and an expectation near −0.0002 if calibrated [E].
- **Outcome:** Track A was built by Ameya and withdrawn by its own retest; Track B became B-D-13; Track C was tested analytically and rejected (B-D-18).
- **Links:** B-X-14 to B-X-18 · D-FRA-14

### B-D-11 · Hand execution to a Claude Code session
- **When (IST):** 2026-09-27 00:05–00:20 · **Phase:** P3 · **Area:** ORG
- **Decided by:** Bakshi: "create an entire plan that lets claude opus takes over" [chat:bakshi/01a0d754 2026-09-27 00:05].
- **Status:** adopted. The Codex agent wrote `plans/bakshi/CLAUDE_OPUS_TAKEOVER.md`; its own publication was blocked when the Codex approval reviewer hit a usage limit at 00:18.
- **Problem:** the Codex session was stalling on the approval reviewer and Bakshi wanted one agent to execute end to end.
- **Choice and why:** the brief's terms were to protect v7nst, gate new variants by 13:00, open focused PRs and never invent results.
- **Outcome:** the Claude Code session `b0c6934d` (branch `bakshi/opus-exec`) ran from 00:20 to the end of the competition and through packaging. Bakshi kept Codex for a second line of work (#59, #60) and later as a watcher.
- **Links:** [PR #50] · [PR #54] · [PR #56]

### B-D-12 · A strict output auditor; never ship a mismatched or synthesised candidate file
- **When (IST):** 2026-09-27 00:26–01:31 · **Phase:** P3 · **Area:** PKG / EVL
- **Decided by:** agent for Bakshi (Claude Code).
- **Status:** adopted (D-PKG-04, D-PKG-05). Ameya ran the auditor on every candidate package; it ships in the ZIP.
- **Problem:** the official validator prints PASS with a missing candidate file or with matches outside it, and never checks owner uniqueness or country. Only v6all's candidate file was on the laptop.
- **Options considered:**
  1. Ship v7nst with v6all's candidates (rejected: matches fall outside).
  2. Synthesise candidates from the matches (rejected: "would be fabrication").
  3. Ask for the real file and predict its size as a check (chosen).
- **Evidence:** 3,790 v7nst matches over 3,725 S1 fall outside v6all's candidates; they are exactly the new acronym candidates. Predicted size 6,410,247 pairs (6,406,457 + 3,790); the real file had exactly that [M] [chat:bakshi/b0c6934d 2026-09-27 00:43], [chat:bakshi/b0c6934d 2026-09-27 01:31].
- **Outcome:** PR #50 merged by Ameya at 01:55.
- **Hindsight:** it caught the gap the validator only warns about.
- **Links:** `experiments/bakshi/final-package/audit_matching.py` · B-X-12

### B-D-13 · Cross-encoder mix (Track B): equal three-way mean, no weight tuning
- **When (IST):** 2026-09-27 01:35 → 02:05 → 02:40 · **Phase:** P3 · **Area:** CE
- **Decided by:** agent for Bakshi recommended; Ameya kept equal z-means. Bakshi asked for it: "yea work on track b right make it work" [chat:bakshi/b0c6934d 2026-09-27 02:33].
- **Status:** adopted (no tuning). Round 1 was closed too early and reopened.
- **Problem:** does reweighting the cross-encoder mean, especially towards bge, help France without hurting US/India?
- **Options considered** (French rule-proxy AUC [E] / labelled US/India holdout band AUC [M]):
  1. `cem2` (e5l + e5l2): 0.8083 / 0.9428.
  2. `cem` (equal three-way, adds bge): 0.8289 / 0.9433.
  3. e5l + bge: 0.8324 / 0.9417.
  4. e5l 0.6 / bge 0.4: 0.8340 / 0.9414.
- **Choice and why:** `cem`, "the only bge mix that improves both sides"; the estimated LB spread across the best 40 weightings is only 0.000048 [E] [chat:bakshi/b0c6934d 2026-09-27 02:40].
- **Evidence:** round 1 (without bge) found only +0.00086 proxy AUC and closed the track at 01:43; Ameya's research showed bge lifts the French mean, so the agent retracted publicly at 02:01 [chat:bakshi/b0c6934d 2026-09-27 02:01].
- **Outcome:** Ameya ran Bakshi's labelled gate on `cms` (e5l + e5ls + bge): 0.9433, a pass, which falsified the agent's warning about v7s [R] [chat:bakshi/b0c6934d 2026-09-27 02:54].
- **Hindsight:** round 1 "was right about the artifacts then in hand and wrong as a conclusion about the hypothesis" (F-ORG-05).
- **Links:** `final-package/ce_weight_fit.py`, `TRACK_B_FINDINGS.md` · [PR #54] · D-CE-14 · B-X-14, B-X-15, B-X-17

### B-D-14 · Talk to Ameya on GitHub; later relay everything through Bakshi
- **When (IST):** 2026-09-27 02:03 → 11:16 · **Phase:** P3–P4 · **Area:** ORG
- **Decided by:** Bakshi, both times: "from now on communicate using github with ameya" (02:03); "dont ask through github anymore" (11:16) [chat:bakshi/b0c6934d 2026-09-27 02:03], [chat:bakshi/b0c6934d 2026-09-27 11:16].
- **Status:** adopted, then reversed.
- **Evidence:** 13 comments on issue #45 and one review of PR #58 between 02:18 and 10:57 [M].
- **Outcome:** after 11:16 the agent wrote ask lists that Bakshi passed to Ameya himself (11:32, 11:49, 13:27). GitHub posting resumed in the evening for #62, #64 and #65.

### B-D-15 · One variant-driven `reproduce.sh`; no clean end-to-end rerun on the final day
- **When (IST):** 2026-09-27 02:55–03:09 (extended 09:05, 11:08) · **Phase:** P3–P4 · **Area:** PKG
- **Decided by:** agent for Bakshi.
- **Status:** adopted (D-PKG-06, D-PKG-07).
- **Problem:** the final model could be any of eight family members, and a full clean rerun takes 6–7 h plus an H100.
- **Options considered:** one script per variant (rejected: "two scripts covering overlapping chains is how they drift apart"); one switch that refuses unrecorded variants (chosen); a clean rerun (skipped and recorded as "not done").
- **Evidence:** every dispatch path exercised; unknown variant exits 2, unrecorded tag exits 4 [M, static check] [chat:bakshi/b0c6934d 2026-09-27 02:57].
- **Outcome:** it caught a trap: a round-2 teacher's final tag is `-s3-ops3a-dpc`, not v7ce3's pre-stack tag. The g0 rebuild (B-X-29) later served as the partial clean run.
- **Links:** `final-package/reproduce.sh` · `DELIVERABLES.md`

### B-D-16 · Pick v7sq-dpc as the model to upload
- **When (IST):** 2026-09-27 09:11–09:15 · **Phase:** P4 · **Area:** SUB
- **Decided by:** agent for Bakshi, on Bakshi's delegation: "just pick one … we are the team lead now pick a model with the highest accuracy" [chat:bakshi/b0c6934d 2026-09-27 09:11]. Ameya's default was the same (D-SUB-14).
- **Status:** adopted; confirmed by the leaderboard, later superseded by mixmdp and Composite B.
- **Options considered:** v7ensall2-dpc (tags unrecorded, tie on expected LB); v7nst-dpc (holdout 0.991194); v7sq-dpc (holdout 0.991246, four cross-encoder families, Qwen gate passed) [R, Ameya's numbers].
- **Choice and why:** v7nst-dpc is "dominated on every measured axis"; v7sq-dpc leads on France, where the deficit is, and is reproducible.
- **Evidence:** expected public LB about 0.990295 [E].
- **Outcome:** public LB 0.990545 [M] [LB 2026-09-27 #02]; the agent: "I was low by 3×".
- **Hindsight:** the label-free French proxies under-sized real French gains.
- **Links:** `final-package/MODEL_CHOICE.md` · D-SUB-14

### B-D-17 · The package builder verifies the artifact, not the source
- **When (IST):** 2026-09-27 09:22–09:29 · **Phase:** P4 · **Area:** PKG
- **Decided by:** agent for Bakshi.
- **Status:** adopted (D-PKG-05).
- **Problem:** a smoke test from the extracted zip failed: the `*token*` secret filter had removed `ber/features/tokens.py` from every earlier zip.
- **Choice:** narrow the filename filter; make "import every `ber` submodule" and "run the shipped tests from the extracted archive" hard gates; mark five earlier zip hashes as broken.
- **Evidence:** after the fix, 34 of 34 submodules import and 115 tests pass from the archive [M] [chat:bakshi/b0c6934d 2026-09-27 09:27].
- **Hindsight:** "verify the artifact, not the source it came from."
- **Links:** `final-package/make_package.py` · B-X-20 · F-PKG-01

### B-D-18 · No drop rule from cross-encoder disagreement
- **When (IST):** 2026-09-27 09:15–09:17 (scope narrowed 10:02) · **Phase:** P4 · **Area:** RUL / FRA
- **Decided by:** agent for Bakshi (D-RUL-12).
- **Status:** rejected.
- **Problem:** does "bge < 0 while both e5 > 0" find confident French false positives?
- **Evidence:** the flip rate is 12.17% in France against a 2.04% background (8,111 excess pairs), but it fires on 17.76% of known-true (rule-population) French pairs against 8.74% of the rest: anti-selective [E, proxy labels] [chat:bakshi/b0c6934d 2026-09-27 09:17].
- **Outcome:** at 10:02 the agent accepted that this rejects only the raw-sign deletion rule, not every verifier.
- **Hindsight:** a stronger verifier (the 7B, B-D-31) re-reading confident pairs did pay later.
- **Links:** `CONFIDENT_SUBSTITUTIONS.md` · B-X-18

### B-D-19 · No fr0 (empty-France) leaderboard probe
- **When (IST):** 2026-09-26 23:39 (Codex), 2026-09-27 09:21 (Claude) · **Phase:** P3–P4 · **Area:** EVL / SUB
- **Decided by:** agent for Bakshi (both agents); Ameya had already ruled the same way (D-EVL-06).
- **Status:** adopted (never run).
- **Problem:** pin down France's level with an upload that predicts nothing for France.
- **Choice and why:** "it would pin the level down but costs a slot, can't improve the score, and no decision depends on it" (D-FRA-12). The 09:21 argument that the French gap was "invariant" was retracted at 10:02 as circular; fr0 also cannot isolate US/India, because singleton French S1 still score 1 when empty.
- **Links:** B-X-19

### B-D-20 · Spend a slot on the v7nst-dpc control; restore the best file
- **When (IST):** 2026-09-27 10:13–10:55 · **Phase:** P4 · **Area:** SUB / EVL
- **Decided by:** agent for Bakshi (Codex) recommended the control at 10:13; Ameya's record says "Bakshi had asked for v7nst-dpc as slot 2" (D-SUB-15). The restore rule was proposed by Bakshi's side (D-SUB-12).
- **Status:** adopted.
- **Problem:** separate the gain of the rule stack (`-dpc`) from the gain of the newer models.
- **Evidence:** public LB v7nst 0.990179 → v7nst-dpc 0.990264 (stack +0.000085) → v7sq-dpc 0.990545 (models +0.000281) [M] [chat:bakshi/01a0d754 2026-09-27 10:21].
- **Outcome:** the agent proposed "if the best measured file isn't the last upload by 18:30, stop experimenting and restore". By 14:30 Bakshi's plan said the best upload counts, not the latest (B-D-32).
- **Hindsight:** the order of the two morning uploads is disputed (open-questions.md).
- **Links:** [PR #60] · D-SUB-12 · D-SUB-15

### B-D-21 · Close the recall routes: alias bridge and structural recall
- **When (IST):** 2026-09-27 10:33–11:25 · **Phase:** P4 · **Area:** BLK / FRA
- **Decided by:** agent for Bakshi (both agents) on measurement; Bakshi's pasted 10:46 plan said "stop spending time on the tested alias-recovery approach".
- **Status:** rejected.
- **Problem:** can a matched S2/S3 record retrieve a missed sibling, or a structural rule recover French pairs the pipeline rejected?
- **Evidence:**
  - Codex alias audit on France: 61 hits, 5 outside the candidates, 0 better through the alias; non-exact mode 1,452 proposals, 14 with a unique exact name [E] [chat:bakshi/01a0d754 2026-09-27 10:40];
  - Claude bridge audit on train truth: 21 of 611,291 sampled true pairs bridgeable (0.0034%) [E] [chat:bakshi/b0c6934d 2026-09-27 10:50];
  - structural recall: precision conditional on the pipeline's own rejections is 0.4010 for core name + house number and 0.0563 for core name alone, both far under the ~0.75 an addition needs [E] [chat:bakshi/b0c6934d 2026-09-27 11:25]. The first verdict (+0.000370) had a sign error, stated openly.
- **Hindsight:** rules that compete with a well-tuned model on its own rejections fail; misses are 2:1 on the decision side.
- **Links:** B-X-22 to B-X-24 · D-BLK-15 · D-RUL-13

### B-D-22 · Act independently and rent Vast.ai GPUs
- **When (IST):** 2026-09-27 11:06–11:16; 13:15 · **Phase:** P4 · **Area:** ORG
- **Decided by:** Bakshi, over the agent's advice at 11:10: "lets not wait for ameya we can spin up another vast ai instances and do our own"; "i will create a vast ai access dont worry about it" [chat:bakshi/b0c6934d 2026-09-27 11:06], [chat:bakshi/b0c6934d 2026-09-27 11:11].
- **Status:** adopted.
- **Problem:** waiting on Ameya's files and machine; the goal was 0.991+.
- **Options considered:** wait for Ameya's round-2 files (the agent's "Method A"); rent and rebuild independently (chosen).
- **Evidence:** the agent's objections: no Vast access on the laptop, missing feature and stage-1 artifacts, 16 GB RAM against 19 GB peaks, 7–9 h for a full pipeline. Its estimate for the push: about $100–150 [E].
- **Outcome:** the push produced g1w and the 7B re-check, the two parts of Composite B that are Bakshi's (public LB 0.990879, the team's best).
- **Hindsight:** without this decision there is no Composite B.
- **Links:** B-D-23 · B-D-26 · D-CE-19

### B-D-23 · The model bet: Qwen2.5-7B (and Qwen3-4B) as cross-encoders, self-trained on France
- **When (IST):** 2026-09-27 12:32 → 12:35 → 13:20 · **Phase:** P4 · **Area:** CE / LLM
- **Decided by:** agent for Bakshi recommended; Bakshi questioned each step ("are we sure that qwen is the best use case for us?", "why do we need 4xh100") [chat:bakshi/b0c6934d 2026-09-27 12:34].
- **Status:** adopted at 13:20 (D-CE-19).
- **Problem:** the candidate family had converged (B-X-25, B-X-26); something qualitatively different was needed within about 8 hours.
- **Options considered:**
  1. 12:32: Qwen2.5-7B as "the most defensible bet".
  2. 12:35, reversed: diversity over scale (gte-multilingual-reranker, mDeBERTa-v3, Qwen3-Reranker-4B); Llama and jina-reranker-v2 excluded on licence.
  3. 13:20, reversed again: Qwen2.5-7B (7.6B) and Qwen3-4B-Base (4.0B), both Apache-2.0, France self-trained from the v7sq-dpc teacher; gte and mDeBERTa only on idle GPUs.
- **Choice and why:** "the largest model used so far is 1.5B, and adding it was part of our last real jump"; the only change that can move both France and US/India and be measured on the holdout. The LOCO ladder (B-X-27) argued against another self-training round as its own candidate.
- **Evidence:** forecast central 0.9909–0.9910, ≥0.991 about 1 in 3 [E] [chat:bakshi/b0c6934d 2026-09-27 13:20].
- **Outcome:** q7st reached holdout band AUC 0.9436, level with e5ls (0.9439) [M]; its value came from diversity in the mix (B-D-30) and from re-reading confident pairs (B-D-31). mDeBERTa and gte failed to train.
- **Hindsight:** scale alone did not buy AUC.
- **Links:** B-X-30 to B-X-32 · `experiments/bakshi/box/llm_group.py`

### B-D-24 · Remap cross-encoder logits by (s1, r) with a 99.5% coverage gate
- **When (IST):** 2026-09-27 12:49 (found) → 13:01 (built and tested) · **Phase:** P4 · **Area:** CE / PKG
- **Decided by:** agent for Bakshi.
- **Status:** adopted (D-CE-22, which dates it 14:30).
- **Problem:** `ce_import.py` writes logits by row position. A rebuild on another machine that reorders one row would put every logit on the wrong pair, silently.
- **Evidence:** on real e5l logits, a permutation follows the pair (a naive row import is right on only 0.31%); a band with 2% unscored pairs gives 98.04% coverage and fails [M] [chat:bakshi/b0c6934d 2026-09-27 13:01]. On the box: 100% train, 99.9999% test coverage (1 pair missing) [M].
- **Links:** `experiments/bakshi/box/remap_ce.py` · B-X-28

### B-D-25 · The rebuild must reproduce v7sq before any new candidate counts (gate V0)
- **When (IST):** 2026-09-27 13:20 (stated) → 17:20 (passed) · **Phase:** P4 · **Area:** EVL
- **Decided by:** agent for Bakshi.
- **Status:** adopted; passed.
- **Evidence:** g0 holdout 0.991261 against v7sq's 0.991246 [M]; France differs from v7sq-dpc on 4.3 predictions per 1000 S1, US/India about 1.2 [E] [chat:bakshi/b0c6934d 2026-09-27 17:08], [chat:bakshi/b0c6934d 2026-09-27 17:20].
- **Links:** B-X-29

### B-D-26 · Boxes: a 2× RTX 4090 pipeline box and a 4× H100 training box, interruptible with Drive backup
- **When (IST):** 2026-09-27 13:41–14:06; 15:24 · **Phase:** P4 · **Area:** ORG
- **Decided by:** Bakshi (the agent proposed the split after he asked "cant we create different smaller boxes for each step?") [chat:bakshi/b0c6934d 2026-09-27 13:42].
- **Status:** adopted; the interruptible box was replaced by an on-demand one.
- **Options considered:** one 8× H100 box (about $19–25/h); a small pipeline box plus a 4× H100 training box (chosen; estimated $45–60 total) [E].
- **Choice and why:** Bakshi picked a 2× RTX 4090 offer at $0.999/h and an interruptible 4× H100 (bid $5.94/h), with continuous Google Drive backup as a condition: "ask the second agent to constantly keep backing it up to google drive set that up first" [chat:bakshi/b0c6934d 2026-09-27 14:06]. The agent's 13:20 spec had said on-demand.
- **Outcome:** the interruptible box was taken away at about 15:05 with the 7B groups at steps of roughly 4,300–6,600. Training resumed from Drive checkpoints on an on-demand 4× H100 (about $9/h) at 15:44 [chat:bakshi/b0c6934d 2026-09-27 15:46].
- **Hindsight:** the backup rule saved the run; on-demand from the start would have saved about 40 minutes.

### B-D-27 · Keep the running 7B on round-2 French labels
- **When (IST):** 2026-09-27 14:35–14:40 · **Phase:** P4 · **Area:** FRA / CE
- **Decided by:** Bakshi: "dont spin up another instance … just do what you are doing for now its perfect" [chat:bakshi/b0c6934d 2026-09-27 14:40].
- **Status:** adopted.
- **Problem:** Ameya reported that round-2 labels made France worse for e5 (D-FRA-22); the 7B was training on round-2 labels (`pseudo_fr_v7sq`).
- **Options considered:** A, rent another 4× H100 for a round-1 7B in parallel (about $25; the agent's recommendation); B, restart on round-1 labels (lose about 20 min); C, keep the run (chosen).
- **Outcome:** q7st on round-2 labels is in Composite B (CF-28).

### B-D-28 · Keep training the Qwen3-4B
- **When (IST):** 2026-09-27 15:00; 15:48 · **Phase:** P4 · **Area:** CE
- **Decided by:** Bakshi: "nah after 7b use all 3gpu for qwen"; "start qwen also use all gpu" [chat:bakshi/b0c6934d 2026-09-27 15:00], [chat:bakshi/b0c6934d 2026-09-27 15:48]. The agent had recommended cancelling it (saving about $12–14).
- **Status:** adopted.
- **Outcome:** q34st finished (holdout band AUC 0.9411 [M]) but is not in Composite B; it was used only as the second opinion in the French drop ladder (B-D-38).

### B-D-29 · A Codex session as a read-only watcher of the boxes
- **When (IST):** 2026-09-27 15:51 · **Phase:** P4 · **Area:** ORG
- **Decided by:** Bakshi: "ask codex to only act as a watcher only watch dont do anything else" [chat:bakshi/b0c6934d 2026-09-27 15:51].
- **Status:** adopted.
- **Outcome:** the watcher flagged overdue backups and, at 17:32, recommended "investigate high-confidence French mistakes outside the cross-encoder band". Bakshi relayed that to the Claude agent at 17:33, and it became the 7B re-check (B-D-31) [chat:bakshi/01a0e269 2026-09-27 17:32], [chat:bakshi/b0c6934d 2026-09-27 17:33].

### B-D-30 · Count the 7B twice in the stage-2 mix for US/India (g1w)
- **When (IST):** 2026-09-27 17:14 (proposed) → 18:07 → 19:22 · **Phase:** P4 · **Area:** CE / MDL
- **Decided by:** agent for Bakshi (proposed and measured); Ameya and Bakshi adopted it for Composite B (D-SUB-21).
- **Status:** adopted (US/India source of Composite B).
- **Options considered** (local holdout, US/India, 549,699 S1 [M]): g0 (no 7B) 0.991261; g1 (7B ×1) 0.991276; **g1w (7B ×2) 0.991323**; g1x3 (7B ×3) 0.991322; g7only (7B alone) 0.991286; gbag (mean of g0, g1, g1w stage 2) 0.991313 [chat:bakshi/b0c6934d 2026-09-27 18:07], [chat:bakshi/b0c6934d 2026-09-27 19:22].
- **Choice and why:** best holdout; more weight did not help.
- **Evidence:** Ameya's paired bootstrap of g1w against v7sq3: India +66.1e-6 [+19.4, +112.9], P 0.998; US +26.2e-6, P 0.906 [M] (D-SUB-21).
- **Hindsight:** the US half of the gain is not significant on its own.
- **Links:** B-X-33

### B-D-31 · The 7B re-check: drop confident predictions the 7B scores below −6
- **When (IST):** 2026-09-27 17:36–18:20 · **Phase:** P4 · **Area:** LLM
- **Decided by:** agent for Bakshi (built, chose the threshold, validated). The idea came from Bakshi's Codex watcher, relayed by Bakshi (B-D-29).
- **Status:** adopted in Composite B, all three countries.
- **Problem:** 94.5% of final predictions have stage-1 p1 > 0.99 and were never read by any cross-encoder.
- **Options considered** (drop thresholds on the 7B logit, out-of-band predicted pairs, labelled US/India holdout sample of 186,897 S1 [M]): −6 gives +0.000033 (both halves positive); −5 +26e-6; −4 +12e-6 (one half negative); −3 −4e-6; −2 −55e-6; 0 −0.003168.
- **Choice and why:** −6, the loosest cut that is positive on both halves. Truth by 7B bucket on the holdout sample: below −6, 24 pairs, 8.3% true; [−6, −4), 51 pairs, 86.3% true [M].
- **Evidence:** positive in 99.7% of 3,000 random 25% subsets; drop rate by S1 third 0.1118% / 0.1082% / 0.1070%, so no leakage from the French pseudo-labels the 7B trained on [M] [chat:bakshi/b0c6934d 2026-09-27 20:07], [chat:bakshi/b0c6934d 2026-09-28 13:16].
- **Outcome:** on test it drops 840 French and 310 US/India pairs from Composite B. Ameya found 78% of the French drops are generic-name decoys (same name, same house number, different street).
- **Hindsight:** looser French cuts (B3–B8) were neutral on the leaderboard (B-D-38); the labelled −6 was right.
- **Links:** `box/rescore_export.py`, `box/score_pairs.py`, `box/rescore_eval.py` · B-X-34 · [components/llm-recheck.md](../../components/llm-recheck.md)

### B-D-32 · "The best upload counts, not the latest"
- **When (IST):** 2026-09-27 13:35; 18:38 · **Phase:** P4 · **Area:** SUB
- **Decided by:** Bakshi: "the best upload counts not the latest one so we have 3 left"; "the best one counts ignore if something else is said" [chat:bakshi/b0c6934d 2026-09-27 13:35], [chat:bakshi/b0c6934d 2026-09-27 18:38].
- **Status:** adopted for Bakshi's planning; never confirmed from the portal (CF-03).
- **Problem:** Ameya's notes said "the final one counts, as far as we know".
- **Outcome:** it let the evening uploads be bold (B7 as the last upload). Moot in the end: B7 tied B (0.990875 against 0.990879).

### B-D-33 · No upload until Composite B is ready
- **When (IST):** 2026-09-27 18:51 · **Phase:** P4 · **Area:** SUB
- **Decided by:** Bakshi: "we are not uploading till composite b" [chat:bakshi/b0c6934d 2026-09-27 18:51].
- **Status:** adopted.
- **Options considered:** upload g1w-dpcsfq at 18:25 or Composite A at 18:48 (the agent's recommendations); wait for B.
- **Outcome:** Composite B was built by 19:41 and uploaded at about 20:50.

### B-D-34 · Composite B: compose per country, then apply the 7B drops
- **When (IST):** 2026-09-27 18:07 (idea) → 18:30 (`compose_tsv.py`) → 19:41 (built) · **Phase:** P4 · **Area:** SUB
- **Decided by:** agent for Bakshi (designed and built); Ameya had built `compose.py` for mixmdp and later `compose3.py` (D-SUB-16).
- **Status:** adopted; Composite B is the final submission.
- **Problem:** the best US/India output (g1w) and the best France (mixmdp, public LB 0.990699) came from different pipelines.
- **Options considered:** Composite A (US/India g1w-dpcsfq, France mixmdp minus French 7B drops); **Composite B** (A plus the US/India 7B drops); Composite B′ (France from g1w instead of mixmdp).
- **Choice and why:** B for the first evening slot; B′ as an A/B test of the French direction.
- **Evidence:** B: 1,169-pair drop list, 1,150 dropped; 5,851,832 pairs; validator and strict audit PASS; matching sha256 `df4bccd7…` [M] [chat:bakshi/b0c6934d 2026-09-27 19:41].
- **Outcome:** public LB **0.990879**, +0.000180 over mixmdp [M] [LB 2026-09-27 #04].
- **Links:** `box/compose_tsv.py` · B-X-39 · D-SUB-23

### B-D-35 · Evening slots: confirm mixf2, then Composite B rather than B′ or mixf4
- **When (IST):** 2026-09-27 20:00–20:53 · **Phase:** P4 · **Area:** SUB
- **Decided by:** agent for Bakshi recommended; Bakshi approved posting it ("yea send this") [chat:bakshi/b0c6934d 2026-09-27 20:02]. Ameya defined mixf2 and proposed mixf4 (issue #64).
- **Status:** mixf2 confirmed; second slot changed from B′ to B.
- **Options considered:** mixf2 (predicted 0.99091 [E]); Composite B′; Composite B; mixf4 (+11e-6 over mixf2, within noise, one more self-training round).
- **Choice and why:** in its review of Ameya's PR #65 the agent switched the second slot to B: "B is mixf2 with the proven France, so it covers exactly mixf2's one risk" [chat:bakshi/b0c6934d 2026-09-27 20:44].
- **Outcome:** mixf2 scored 0.990819 and mixf7 0.990833, both below B [M].
- **Links:** [issue #64] · [PR #65] · D-SUB-22

### B-D-36 · Upload Composite B before mixf2
- **When (IST):** 2026-09-27 20:49 · **Phase:** P4 · **Area:** SUB
- **Decided by:** Bakshi: "give me the tsx file for composite B i will upload it now" [chat:bakshi/b0c6934d 2026-09-27 20:49]. The KB records "Ameya with Bakshi" (D-SUB-23).
- **Status:** done.
- **Outcome:** 0.990879, rank 16 on the public board at the time [M] [chat:bakshi/b0c6934d 2026-09-27 20:55]. The team's best upload.

### B-D-37 · Do not look at another team's solution
- **When (IST):** 2026-09-27 22:28 · **Phase:** P5 · **Area:** ORG
- **Decided by:** agent for Bakshi (refused); Bakshi did not insist.
- **Problem:** Bakshi pasted a top team's public score (0.992082) and asked the agent to "look at them".
- **Choice and why:** disqualification risk during the competition; the agent only reasoned about what the score implies (about 15% fewer US/India errors, likely better candidate generation or cluster-level evidence).

### B-D-38 · Last upload: B7, the far end of a French drop ladder
- **When (IST):** 2026-09-27 22:11–23:39 · **Phase:** P5 · **Area:** SUB / LLM
- **Decided by:** Bakshi: "we are uploading this as our final" (23:36). The agent built B+ (22:11), B++ (22:38), B3 (22:41), B4 (22:57), B5 (23:10), B6 (23:22), and B7 and B8 (23:34) as Bakshi asked for more ("b5 … reduces the gamble and increases the cap", "now b6", "upto b8"). At 23:23 it refused B7/B8 on time and evidence grounds; Bakshi insisted ("just do what i am asking") [chat:bakshi/b0c6934d 2026-09-27 23:23].
- **Status:** uploaded; a tie.
- **Problem:** one slot left after B; the team wanted 0.991.
- **Options considered:** B+ (+255 restored look-alikes, −83 unscored French pairs the 7B rejects); B++ (also −113 in-band French pairs below −6); B3–B8 (French drops extended toward logit −2, from B5 on only where Qwen3-4B also disagrees).
- **Choice and why:** B7 (+251 / −1,699 French pairs against B), recommended by the agent over B8; under B-D-32 a miss could not lower the standing.
- **Evidence:** the labelled checks behind the looser cuts were weak (B6's in-band rule +8.2e-6 overall, one half negative [M]); expected 0.99095–0.99106 [E] [chat:bakshi/b0c6934d 2026-09-27 23:34].
- **Outcome:** public LB 0.990875, −0.000004 against B [M] [LB 2026-09-27 #07].
- **Hindsight:** extrapolating France's decoy density below −6 was "too optimistic"; the labelled cut-off was already right.
- **Links:** `box/bplus_tsv.py`, `box/fr_drop_ladder.py` · B-X-42, B-X-45, B-X-47 · D-SUB-26

### B-D-39 · The ZIP and its documents describe Composite B; ship a runnable driver
- **When (IST):** 2026-09-27 23:45; 2026-09-29 00:56–01:50 · **Phase:** P5 · **Area:** PKG
- **Decided by:** agent for Bakshi raised it (the guidelines want artefacts for the best submission) [chat:bakshi/b0c6934d 2026-09-27 23:45]; Ameya opened #66, #69, #71 and #75; Bakshi: "yea go ahed resolve the issue with what we have" [chat:bakshi/b0c6934d 2026-09-29 00:56].
- **Status:** adopted (D-PKG-10, D-PKG-12).
- **Choices:** as-run box scripts on `main` plus a record (`REPRO_compositeB.sh`, PR #70); then a runnable driver `box/compositeB.sh` (one 7B job per GPU), `VARIANT=compositeB` as the default of `reproduce.sh`, Qwen2.5-7B pinned to revision `d1497293…`, Sachi's `ce_llm.py` shipped, a pinned version list "not a pip freeze" because the boxes were gone (PR #72). Four deviations from the as-run job were declared.
- **Evidence:** test build PACKAGE OK (156 files, both output hashes match, 115 tests, validator and audit PASS) [M] [chat:bakshi/b0c6934d 2026-09-29 01:50].
- **Outcome:** the final `Grenuke_submission.zip` (`7f077875…`, 88,353,544 bytes) passed all eight checks of #75, including a byte-identical rebuild from `main` [M] [chat:bakshi/b0c6934d 2026-09-29 04:01].
- **Links:** [PR #70] · [PR #72] · [issue #75] · B-X-49, B-X-50

### B-D-40 · Check generalisation by resampling the holdout, not with outside data
- **When (IST):** 2026-09-28 13:11–13:18 · **Phase:** P5 · **Area:** EVL
- **Decided by:** agent for Bakshi; Bakshi asked "we need to figure out if it genralises well" and allowed outside data after the round closed [chat:bakshi/b0c6934d 2026-09-28 13:18].
- **Options considered:** a Fodors–Zagat test of the 7B (about 30 min, about $1; says nothing about the private board); simulate public/private splits on the holdout (chosen).
- **Evidence:** public − private gap sd 0.00016 on the holdout at a 25% public share (0.000231 at 10%) [M, simulation]; the 7B drop rule positive in 99.7% of 3,000 subsets [M].
- **Outcome:** the team finished in the Top 10 of 32,000+ teams, 2nd on the list [R, issue #79]; no private score is published.
- **Links:** `box/analysis/resample_drop.py` · B-X-48
