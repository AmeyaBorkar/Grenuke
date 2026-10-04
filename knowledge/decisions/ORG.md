# Decisions: ORG (team, process, repo, compute, plan selection)

**Summary.**
- Twenty-nine decisions on how three people and their AI agents organised the work: the repo rules, how the plan was chosen, who ran what on which machine, how compute was rented and protected, how the ZIP was assembled, and how the finale is being prepared. (S1 is a source-1 business record; S2 and S3 are the vendor sources matched to it.)
- Plan A was the base with nine grafts from Plan B, chosen by the coordinator, who also wrote Plan A; the rubric scores on record are the coordinator's alone. Compute was the bottleneck: one 31 GB laptop was the integration machine and froze once, and rented GPUs did the heavy cross-encoder work after a lost spot instance.
- Plans that were not held are kept: the Sunday code freeze, the 21:00 deadline reading, and the early reliance on teammates' stages that the faster chain bypassed.

## Index

| ID | decision | when (IST) | status |
|---|---|---|---|
| D-ORG-01 | One-writer files, member branches, rebase-merge only, hooks, no attribution lines | 2026-09-25 12:41 | adopted |
| D-ORG-02 | Choose the base plan by pitch, weighted rubric and hard gates, with grafts | 2026-09-25 13:02 | adopted, with deviations |
| D-ORG-03 | Plan A is the base, with nine Plan B grafts | 2026-09-25 13:56 | adopted |
| D-ORG-04 | Roles, machines and tasks as issues: "code moves, data doesn't" | 2026-09-25 14:14 | adopted on paper; changed in practice |
| D-ORG-05 | Contracts C0–C10 and stage-by-tag artifacts | 2026-09-25 14:15 | adopted |
| D-ORG-06 | Share dev artifacts through private GitHub pre-releases | 2026-09-25 17:15 | adopted |
| D-ORG-07 | Run heavy jobs one at a time; add a lean test-only scoring mode | 2026-09-25 18:00 | adopted |
| D-ORG-08 | Keep text work on the CPU; only matrix-style work goes on the GPU | 2026-09-25 18:54 | adopted |
| D-ORG-09 | Point Bakshi at France, Indic recall and documentation instead of duplicate features | 2026-09-25 18:58 | partly adopted |
| D-ORG-10 | No AWS for Bakshi's slow features; test their value first | 2026-09-25 21:05 | adopted |
| D-ORG-11 | Treat the window as closing at 21:00 IST, without editing AGENTS.md | 2026-09-26 02:05 | adopted as the working deadline |
| D-ORG-12 | Do not restart reaped jobs without the human; then resumable, memory-aware chains | 2026-09-26 06:30 | adopted |
| D-ORG-13 | Competitors' public work: ideas only, no code reuse | 2026-09-26 14:45 | adopted (moot: nothing to read) |
| D-ORG-14 | Code freeze Sun 15:00 and final upload by 19:00 | 2026-09-26 16:40 | adopted on paper; not held |
| D-ORG-15 | Rent GPUs for larger cross-encoders; upload only records and band pairs; stage 2 stays local | 2026-09-26 16:52 | adopted |
| D-ORG-16 | After the spot box died, rebuild v7m's design locally as v7n | 2026-09-26 21:41 | adopted |
| D-ORG-17 | Box policy: one on-demand 80 GB GPU; the traffic cap lifted | 2026-09-26 22:29 | adopted |
| D-ORG-18 | Coordinate on issue #45; merge on Ameya's orders; only the captain uploads | 2026-09-27 01:37 | adopted |
| D-ORG-19 | After the crash: one heavy job at a time, a 15 GB memory guard, a pause flag | 2026-09-27 03:27 | adopted |
| D-ORG-20 | Stop the rented H100 once every output is safe; keep stage 2 on the laptop | 2026-09-27 03:51 | adopted |
| D-ORG-21 | Handle Sachi's push to Ameya's PR branch with a normal commit, not a force-push | 2026-09-27 08:43 | adopted |
| D-ORG-22 | Decline extra GPU instances until a concrete job existed | 2026-09-27 12:03 | mixed |
| D-ORG-23 | Pause the sub-agents for the usage limit; resume after the reset | 2026-09-27 15:28 | adopted |
| D-ORG-24 | Use every idle GPU, including Bakshi's boxes, in the last hours | 2026-09-27 18:38 | adopted; ended 19:37 |
| D-ORG-25 | Who writes what for the ZIP: Bakshi's driver, a fork's France block, the agent's document and assembly | 2026-09-29 01:26 | adopted |
| D-ORG-26 | Edit Bakshi's packaging files, with Ameya's permission | 2026-09-29 01:59 | adopted |
| D-ORG-27 | Merge order; build the ZIP only from main | 2026-09-29 03:32 | adopted |
| D-ORG-28 | Finale: lead with candidate efficiency and the cascade | 2026-10-03 22:47 | deferred (a proposal) |
| D-ORG-29 | Knowledge capture: redacted transcript digests and a common standard | 2026-10-03 22:58 | adopted (in progress) |

## Records

### D-ORG-01 · One-writer files, member branches, rebase-merge only, hooks, no attribution lines
- **When (IST):** 2026-09-25 12:41–13:06 (design), 13:00 (recorded) · **Phase:** P0 · **Area:** ORG
- **Decided by:** Ameya (requirements at 12:40); designed and built by agent for Ameya
- **Status:** adopted
- **Problem:** Three people and their AI agents would share one repo for about 72 hours. `main` had to stay runnable and numbers comparable, no attribution lines, data or secrets could slip into commits, and every AI agent had to follow the same rules.
- **Options considered:**
  1. Everyone pushes directly to a shared main.
  2. Trunk-based work with pull requests (PRs) on member branches. Chosen.
  3. Squash merges. Rejected.
  Other options were not recorded.
- **Choice and why:** Option 2, in detail.
  - **Branches and merging.** `main` is protected: a PR is required, the CI checks (automatic checks on each PR) "repo policy" and "unit tests" must pass, history is linear, and no force-push. Work goes on `<member>/<topic>` branches. Merges are rebase-merge only (each commit is replayed on main, with no squash), "because squash adds Co-authored-by". Approvals were kept "as a team norm rather than a hard gate so no one gets blocked overnight".
  - **One writer per coordination file**, so these files never conflict: a status file per member, one handover file per session, one decision record per decision, one upload record per upload.
  - **Contracts first**, so the team could "take the best parts of all three plans and combine them" (D-ORG-05).
  - **One rulebook.** `AGENTS.md` is the single source of truth for every agent, with pointer files for Claude, Gemini, Copilot and Cursor.
  - **No attribution lines, enforced in four places:** a commit-message hook, a CI check on commits and PR title and body, `.claude/settings.json` with attribution off, and squash merges disabled. The commit-message hook also enforces Conventional Commits.
  - **Hygiene:** a pre-commit hook blocks commits on main, data, files over 5 MB and secrets; a pre-push hook blocks pushes to main.
- **Evidence:** 24 tests at bootstrap and a passing validator on `ber.io` output [M] ([handover 2026-09-25_1300](../../docs/handover/2026-09-25_1300_ameya_repo-setup.md)). The hooks were tested on 16 cases, and PR #1 went through the full cycle [M] [chat:ameya/19e315ba 2026-09-25 13:06].
- **Outcome:**
  - The rules held all competition: 24 handovers, 16 decision records, 11 upload records, and PRs up to #65 (the packaging PRs ran to #77). Every merge on the first day (#4, #14, #15, #18, #19) used the process; 95 tests ran in CI by 20:00. The agent merged only when Ameya explicitly asked.
  - Deviations: the 25 Sep uploads got no records; the 27 Sep uploads got no `sub/*` tags; the ROADMAP was frozen at 26 Sep 16:40; Sachi never created a status file.
- **Hindsight:** The one-writer trail is what makes this knowledge base possible to build. It did not move artifacts, though: data stayed on the integration machine, and that blocked Bakshi twice on the last day (the first time is in [handover 2026-09-27_0111](../../docs/handover/2026-09-27_0111_bakshi_final-package.md) and his [artifact request](../../experiments/bakshi/final-package/ARTIFACT_REQUEST.md)).
- **Links:** [CONTRIBUTING §1–6](../../CONTRIBUTING.md) · [AGENTS §3–5](../../AGENTS.md) · D-ORG-05 · D-ORG-04

### D-ORG-02 · Choose the base plan by pitch, weighted rubric and hard gates, with grafts
- **When (IST):** 2026-09-25 13:02 (process written) → 14:15 (applied) · **Phase:** P0 · **Area:** ORG
- **Decided by:** Ameya (coordinator)
- **Status:** adopted, with deviations
- **Problem:** Three members were to write competing plans in parallel. The team needed one plan by the afternoon without losing the others' best ideas.
- **Options considered:**
  1. Pick one plan whole.
  2. Merge freely.
  3. One base plus "grafts" that fit the shared contracts and are "clearly better for one stage", chosen by a weighted rubric and hard gates.
- **Choice and why:** Option 3. Each author pitches for 5 minutes: what is different, the biggest risk, and the time to the first valid submission. Everyone scores 1–5 independently and the scores are averaged. Weights: expected F0.5 30%, blocking recall 15%, robustness 15%, time to first submission 15%, compute 10%, validation clarity 10%, parallelisability 5%. Hard gates for the base: a valid submission by Fri 23:30; provided data only and models under MIT or Apache-2.0 with at most 8B parameters; runs on team hardware, test inference on about 10M records included; no hard-coded {US, India}.
- **Evidence:** the rubric and gates in [plans/README.md](../../plans/README.md).
- **Outcome:** The decision came at 14:15, 44 minutes after Plan B landed (13:31). Only the coordinator's scores are on record. Teammates were to add theirs in the PR review, "and the averages then replace these", and the file still shows his alone ([DECISION](../../plans/DECISION.md)).
- **Hindsight:** unknown (none recorded). D-ORG-03 shows what the scores did and did not decide.
- **Links:** [plans/README.md](../../plans/README.md) · [DECISION](../../plans/DECISION.md) · D-ORG-03

### D-ORG-03 · Plan A is the base, with nine Plan B grafts
- **When (IST):** 2026-09-25 13:56–14:15 (decision recorded in `plans/DECISION.md` at 14:14–14:15; FINAL_PLAN v1.0 "accepted, 14:15") · **Phase:** P0 · **Area:** ORG / PRB
- **Decided by:** Ameya, coordinator ("make the final best plan getting in both approaches"), on the proposal of an agent for Ameya. Plan A was Ameya's, Plan B was Sachi's, and Plan C (the slot Bakshi filled later) was never submitted.
- **Status:** adopted (FINAL_PLAN v1.0, PR #3)
- **Problem:** Two plans disagreed on about six components and on build discipline, and one had to be built before the evening's first upload. At 12:40 Ameya had said: "we will decide whose to follow… or just take best from all".
- **Options considered:**
  1. Plan A (Ameya). A seven-stage pipeline: multi-view TF-IDF → SVD → GPU exact top-k in both directions, exact keys and a learned pre-ranker; about 150 features including extra-token (look-alike) features; XGBoost (a tree-boosting library) on the GPU for stage 1, collective stage-2 features, isotonic calibration (turning scores into probabilities), and a per-S1 expected-F0.5 dynamic programme (DP) that picks each S1's set. It was the only plan with a time and compute budget, a timeline, a code layout and a fit with the repo contracts, and it had already measured the test set. Weaknesses: Friday's scope was too big (it needed a cut to a v0 to meet the 23:30 gate), and it had no "must beat simple" tests.
  2. Plan B (Sachi, PR #2, "Final Approach v2, stress-tested"). The strongest method: the task framed as ownership assignment plus a per-entity decision, every claim tagged [M] measured, [F] fact or [H] hypothesis with a named experiment that can overturn it, and every complex part required to beat a simpler one. Weaknesses: no timeline, no search method for about 10M records, it ignored the shared holdout, and two of its positions were contradicted by data.
  3. A merge: Plan A's engine with Plan B's discipline. Chosen.

  | aspect | Plan A (Ameya) | Plan B (Sachi) | final plan v1.0 |
  |---|---|---|---|
  | search | TF-IDF → SVD-256 → exact GPU fp16 tiles, S1 → record and record → S1 in one pass; faiss-cpu fallback | top-K, engine unspecified | A's engine, checked against sparse search (G2) |
  | trimming | learned pre-ranker to about 25 per S1 | no learned pruner: "adds a model, a training step and a failure point" | heuristic trim; pre-ranker only through G11 |
  | ownership | each record kept under its best S1 | softmax over S1 plus "none"; must beat argmax | argmax in v0; softmax only through G5 |
  | decision | exact expected-F0.5 DP per S1 plus one global shrink | expected-F only if it beats a tuned threshold | DP must beat the threshold (G6); ties go to the threshold |
  | cross-encoder (a model that reads both records of a pair together) | optional on day 3, band 0.1 < p1 < 0.9 (p1 is the stage-1 probability), at least +0.003 | gated, Indic ambiguous pairs only: "transformers are weak at exact numeric comparison" | a Sunday gated extra (G10) |
  | validation | S1 splits 40/35/25, a drop-20%-of-S1 stress test, leave-one-country-out | cluster-level split, experiments V0–V10, ablation table | holdout folds 0–4, out-of-fold (OOF) groups, gates, diagnostics (D-EVL-01) |
  | France | "same generator" (checked on Lille records); lexicons; 1–2 leaderboard probes | every France claim [H] until a France-vs-empty probe | A's lexicons plus B's probe |
  | test shift | "more distractors in test" (5.75 against 4.68 per S1) | [H] "test resembles train" | measured shift; diagnostics |
  | compute and time | one laptop, about 2.5 h end to end, milestones M0–M7 | none given | about 2 h, milestones M0–M9 |

- **Choice and why:** "Plan A should be the base"; "Plan B's best contribution is its method." The rubric scores on record (weights as in D-ORG-02): Plan A 4, 4, 4, 3, 4, 4.5, 4 = 3.9; Plan B 3, 3.5, 3, 3, 3, 4, 2 = 3.1. Both pass the hard gates on provided data and no country assumption; Plan A needed its Friday scope cut to v0. The plan was then adjusted by data checks run that day (`plan_checks.py`, `density_check.py`, `ownerless_check.py`): test has 5.75 S2/S3 records per S1 against 4.68 in train; 46–54% of S1 share an exact core name; look-alike orphans carry a nudged number (first number equal in 12.4%, against 84.8% for true pairs) and an extra business word (76.5% against 23.3%); there are no usable postcodes.
  - **The nine grafts** (the research session's list): (1) tag claims measured or assumed and gate complex components with a paired bootstrap (D-EVL-03); (2) name-only search only for records with an empty or at most 3-token address (D-BLK-01); (3) domain-stem and DBA keys plus a 3-character domain guard; (4) OCR variants and a consonant skeleton (D-NRM-02; OCR repair in D-BLK-11); (5) train the second stage with owner-removed examples; (6) drop any blocking view adding under 0.1 point of recall; (7) calibration plots per country and source, plus an ablation table; (8) the France-vs-empty probe, Cedex and arrondissements (D-EVL-06); (9) drop the postcode feature (D-NRM-01). Also taken from B: softmax with "none" as gate G5 (D-PRB-02), the DP must beat a tuned threshold (G6), no learned pre-ranker in v0 (D-BLK-03), and unseen or empty country labels searched against every partition (D-BLK-02).
  - **Rejected from Plan B:** "test resembles train" (disproved: 5.75 against 4.68 records per S1); cutting the extra-token module as "subsumed by competition margins" (look-alikes often have no rival S1: first number equal in 12% of look-alikes against 85% of true pairs, an added business word in 77% against 23%); a sampled "world" for competition features (they need the full candidate graph; sampling is fine only for training rows); an unspecified top-k search; LightGBM only.
  - **Rejected from Plan A:** the name view over all records (D-BLK-01); the postcode field (D-NRM-01); the drop-S1 stress test as the threshold driver (D-EVL-02); a learned pre-ranker in v0 (D-BLK-03).
- **Evidence:** The rubric scores are on record as the coordinator's [R] ([DECISION](../../plans/DECISION.md)). The research session that proposed the merge called them its own scores and said to "discount them" [chat:ameya/a2a1b62a 2026-09-25 13:56]; the two accounts of whose scores they are differ [U]. The data checks [M], run with crude normalisation ([handover 2026-09-25_1414](../../docs/handover/2026-09-25_1414_ameya_final-plan.md), [plan checks](../../experiments/ameya/plan-checks/README.md)). Sachi's sample measurements: 47% of S1 share an exact core name, 5.3% an exact address, 4 of 2.2M both [M, sample of 33,189 S1] ([Plan B §1](../../plans/sachi/PLAN.md)).
- **Outcome:**
  - FINAL_PLAN, CONTRACTS C0–C10 and the ROADMAP shipped in PR #3. Gates G1–G13 organised the work (D-EVL-03); G2 and G5 were dropped, and G7 and G8 never ran on the leaderboard. The +0.002 bar with the interval above 0 became the team rule.
  - Sachi's process rules became team rules (AGENTS.md §3) and decided late choices: v7ensall2 was dropped because it tied v7sq ("ties go to the simpler option"), and mixf4 was not uploaded.
  - The late architecture went beyond the plan: band cross-encoders, self-training and the 7B re-check (the Qwen2.5-7B language model that re-checks confident predictions).
  - Teammates were to add their own rubric scores in the PR review; none appears in the record.
- **Hindsight:**
  - The base held. The shipped system kept Plan A's spine (gradient-boosted stages, isotonic calibration, argmax ownership, an expected-F0.5 DP) and Plan B's falsifiability. Plan A's GPU retrieval was never built (D-BLK-05), and the sparse fallback became the engine.
  - Plan B's demotion of cross-encoders did not hold: the e5-large step was the largest single leaderboard gain (+0.0011 on the public leaderboard, LB) ([methodology Fig. 3](../../experiments/ameya/final-zip/doc/Documentation_template.md)).
  - The look-alike checks of 25 Sep (a nudged number plus an extra business word) pointed straight at the US/India features that mattered most: look-alike word odds, signed numbers and legal forms. The plan had no France strategy beyond probes, yet France turned out to be the whole leaderboard gap (D-EVL-07).
  - The person who scored was also the author of the winning plan. The +0.002 bar proved too high for late micro-gains.
- **Links:** [FINAL_PLAN](../../plans/FINAL_PLAN.md) · [DECISION](../../plans/DECISION.md) · [Plan A](../../plans/ameya/PLAN.md) · [Plan B](../../plans/sachi/PLAN.md) · [Sachi's decision log](../../plans/sachi/DECISION.md) · [PR #2], [PR #3] · [chat:ameya/a2a1b62a 2026-09-25 13:56] · D-ORG-02 · D-EVL-03

### D-ORG-04 · Roles, machines and tasks as issues: "code moves, data doesn't"
- **When (IST):** 2026-09-25 14:14 (roles), 15:20 (split proposed), 15:41–15:47 (issues #5–#13 and PR #14) · **Phase:** P0–P1 · **Area:** ORG
- **Decided by:** Ameya, coordinator (roles at 14:14–14:15; "distribute the work on git right now" at 15:20); the split was designed by agent for Ameya. Sachi and Bakshi were asked to confirm ownership at 14:30.
- **Status:** adopted on paper; changed in practice (see Outcome)
- **Problem:** The machines differed a lot. Ameya: RTX 5070 Ti with 12 GB, 24 cores, 31 GB RAM. Bakshi: i5-12450H with 8 cores, RTX 2050 with 4 GB, 16 GB RAM. Sachi: MacBook Air M3, 8 GB RAM, no CUDA. Member 3 (Bakshi) had not yet confirmed, and the Friday critical path ran normalise → features.
- **Options considered:**
  1. Informal assignments in chat.
  2. Each member runs full scale. Rejected: memory.
  3. Pass multi-GB artifacts between laptops. Rejected.
  4. Full runs only on Ameya's machine; teammates develop code on a dev sample; tasks as issues with owner, roadmap item, contract, branch, artifact tag, due time and "done when". Chosen.
- **Choice and why:** Option 4. "Passing multi-GB feature files between three laptops at 21:00 is a bigger risk than any modelling choice." Each issue carried a full spec so a member's AI agent could pick it up (`gh issue list --assignee @me`).
  - **Roles**, matching each plan's strengths: Ameya was coordinator, submissions captain (the only uploader), and owner of blocking (GPU runs), the pipeline command line and packaging; his machine was the integration machine for every full-scale run. Sachi: model, calibration, ownership and decision, gates and ablations, error analysis. Bakshi: normalisation, lexicons and pair features.
  - **Working rules:** everyone develops on the dev sample (about 110k train S1 from folds 0/5/10/15, which fits 8–16 GB), and every stage must run on the CPU.
  - **Issues:** Bakshi #6 normalise v0 (due 18:00) and #7 string features (21:00); Sachi #8 model v0 (21:30) and #9 decision plus expected-F DP (22:00); Ameya #10 blocking, #11 baseline (17:30), #12 context features and #13 integration and Submission 2 (23:00).
- **Evidence:** machine table [R] ([TEAM](../../docs/TEAM.md)); due times against closes [M, GitHub timestamps]: #8 and #9 (Sachi) due 21:30 and 22:00, closed 18:12; #6 (Bakshi) due 18:00, closed 20:55; #7 (Bakshi) due 21:00, PR opened 21:05, merged 10:12 the next day. [chat:ameya/19e315ba 2026-09-25 15:20], [15:47]; [status ameya @4984b6f](../../docs/status/ameya.md).
- **Outcome:**
  - Ameya's agent built the model chain on the integration machine, as scripts in `experiments/ameya/model-v1`. Bakshi's normalise and features v0 were "not used by the v6all chain" ([ROADMAP 1.2, 1.4](../../docs/ROADMAP.md)); "Bakshi's C3 normalization is not used by v3" ([ANALYSIS_v3 §7](../../experiments/ameya/model-v1/ANALYSIS_v3.md)). The team's v0 integration at 21:30 did not happen; Ameya's own experiment pipeline produced Submissions 2 and 3.
  - Sachi delivered `ber.model` by about 18:01, ran the dev-kit gates (G4, G6, name uniqueness), produced error analysis and a France kit, and trained a Qwen2.5-1.5B classifier on a rented RTX 4090.
  - On 27 Sep Bakshi rented boxes and built the 7B parts that made the best submission: the cross-encoder-mix gates, the Qwen2.5-7B models and Composite B (the team's best public submission).
  - The issue pattern was reused at the end for the ZIP (#66, #69, #71, #75), with lettered items and "reply with a checklist". By the final day the "data doesn't move" rule was relaxed: artifacts moved by Drive and direct file hand-offs.
- **Hindsight:** The dev-sample rule kept 8–16 GB machines productive on day 1, but the teammates' stages (C3, C8, `ber.model`) were never run at full scale and were bypassed by Ameya's faster experiment chain. The single integration machine became the bottleneck: stage 2 (the second model stage) peaked at 16.5–19 GB and the laptop crashed at 03:35 on 27 Sep (D-ORG-19). Renting GPUs from the evening of 26 Sep changed what the team could do (D-ORG-15).
- **Links:** [TEAM](../../docs/TEAM.md) · [handover 2026-09-25_1414](../../docs/handover/2026-09-25_1414_ameya_final-plan.md) · [issues #5–#13], [PR #14], [issue #5 close comment] · D-ORG-03 · D-ORG-15

### D-ORG-05 · Contracts C0–C10 and stage-by-tag artifacts
- **When (IST):** 2026-09-25 14:15 · **Phase:** P0 · **Area:** ORG / PKG
- **Decided by:** Ameya
- **Status:** adopted
- **Problem:** Parallel work without people overwriting each other.
- **Options considered:** not recorded.
- **Choice and why:** Written contracts that every stage reads and writes.
  - C0: tags `<member>-<stage>-v<N>` and paths `work/<stage>/<tag>/<split>.parquet`, with the commit and command in every artifact.
  - C1: eid = source × 1e9 + number (int64). C2: holdout and folds (D-EVL-01). C3: records and normalised columns.
  - C4: candidates with a view bitmask ("this exact set becomes `candidate_pairs.tsv`"). C5: calibrated scores, so models can be averaged or stacked.
  - C6: outputs only through `ber.io`. C7: report JSON. C8: features named `<group>__<name>`, float32, no country, OOF and holdout-free. C9: matches are a subset of C4. C10: gate records.
  - One command line, `python -m ber.pipeline --stage …`; strings only up to stage 01.
- **Evidence:** [CONTRACTS](../../docs/CONTRACTS.md), [FINAL_PLAN §3](../../plans/FINAL_PLAN.md), [DEVELOPMENT](../../docs/DEVELOPMENT.md).
- **Outcome:** `ber.pipeline` ran records, block, write and evaluate. The model stages ran as scripts (`feats.py`, `s1.py`, `s2.py`, `decide.py`, `stage3.py`, `post_ops.py`, `acr_join.py`) chained by shell drivers, and were consolidated into `code/business_entity_resolution/src` for the ZIP (issue #66) ([RECIPE](../../experiments/ameya/model-v1/RECIPE.md), [pipeline README](../../experiments/ameya/model-v1/pipeline/README.md)).
- **Hindsight:** unknown (none recorded).
- **Links:** D-ORG-01 · D-EVL-01

### D-ORG-06 · Share dev artifacts through private GitHub pre-releases
- **When (IST):** 2026-09-25 17:15–17:19 (devkit-v0), 20:15–20:20 (devkit-v2), 21:23 (scores-v2lg-dev) · **Phase:** P1 · **Area:** ORG
- **Decided by:** Ameya ("do the faster one")
- **Status:** adopted
- **Problem:** Sachi was blocked: the dev kit was built at 17:06 but no team-drive link existed.
- **Options considered:**
  1. Ameya uploads to Google Drive.
  2. A private GitHub pre-release asset, downloadable by the collaborators only. The agent warned that "it does put competition-derived data on GitHub, so I'll only do it if you say yes".
- **Choice and why:** Option 2, for speed: it unblocks Sachi immediately, and the repo is private.
- **Evidence:** devkit-v0 is 179,797,164 bytes, checksum verified by re-download [M].
- **Outcome:** `devkit-v0` (with FEATURES.md, the stage-1 model file and the decision parameters), `devkit-v2` (383.5 MB, 79 features) and `scores-v2lg-dev` (71.5 MB).
- **Hindsight:** It worked. The datasets stayed out of git history, because release assets are not commits.
- **Links:** D-ORG-04 · [chat:ameya/19e315ba 2026-09-25 17:15]

### D-ORG-07 · Run heavy jobs one at a time; add a lean test-only scoring mode
- **When (IST):** 2026-09-25 18:00, 19:44, 20:00 · **Phase:** P1 · **Area:** ORG
- **Decided by:** agent for Ameya
- **Status:** adopted
- **Problem:** At 17:54 the feature build hit 17.1 GB with 1.1 GB free. Around 19:40 the AI coding tool reaped (killed, to free memory) the v2 chain's wrapper shell: stage-2 test scoring with cluster support peaked above 18 GB while blocking ran.
- **Options considered:**
  1. Keep overlapping jobs.
  2. Sequential chains, plus `s2.py --test-only`, which scores test from the saved models without the train arrays.
- **Choice and why:** Option 2. Only about 20 GB is usable on the 31 GB laptop, because other applications and the system hold about 10 GB. "Only overlap a GPU training job (about 8 GB) with a CPU job past its peak."
- **Evidence:** memory readings [M]; the 20 GB estimate [R].
- **Outcome:** The Python children of the reaped shell finished, so no result was lost. The agent did not restart reaped work unasked (D-ORG-12).
- **Hindsight:** The memory ceiling later pushed heavy work to rented GPU boxes (D-ORG-15).
- **Links:** D-ORG-12 · D-ORG-19

### D-ORG-08 · Keep text work on the CPU; only matrix-style work goes on the GPU
- **When (IST):** 2026-09-25 18:54–18:55 · **Phase:** P1 · **Area:** ORG / BLK
- **Decided by:** agent for Ameya (a recommendation, accepted implicitly)
- **Status:** adopted
- **Problem:** The CPU sat at 100% and the GPU at 0%.
- **Options considered:**
  1. Rewrite the string work for the GPU.
  2. Keep it on the CPU and use the GPU only for matrix work.
- **Choice and why:** Option 2. Only XGBoost uses CUDA. Normalisation, token blocking and string features are branchy, variable-length string work and a poor fit for a GPU. Rewriting `feats.py` and `feats_lo.py` would cost a day for code that already runs in minutes on 24 cores. The character 3-gram blocking views were a large matrix multiplication plus nearest-neighbour search, so they were the natural GPU job. The slow parts of blocking (about 19 min on train, 15 min on test) are single-threaded Python tokenisation and writes.
- **Evidence:** [chat:ameya/a2a1b62a 2026-09-25 18:54].
- **Outcome:** Accepted without a record.
- **Hindsight:** The GPU's real use turned out to be cross-encoders on rented boxes, not the laptop. The planned GPU blocking views were never built (D-BLK-05).
- **Links:** D-BLK-05 · D-ORG-15

### D-ORG-09 · Point Bakshi at France, Indic recall and documentation instead of duplicate features
- **When (IST):** 2026-09-25 18:58 · **Phase:** P1 · **Area:** ORG / FRA
- **Decided by:** agent for Ameya (a proposal); Ameya's action is unknown
- **Status:** partly adopted: Bakshi later worked on France diagnostics, packaging and the LLM runs
- **Problem:** Issues #6 and #7 predated Ameya's model v1, which already covered them (local holdout F0.5 0.9801).
- **Options considered:** not recorded.
- **Choice and why:** France normalisation (rue and r, bd, Cedex, arrondissements, N°, bis and ter, departments, SARL, SAS, EURL) and about 100 hand-checked French predictions, because France is "the only area where he can raise the leaderboard score without duplicating anyone".
- **Evidence:** [chat:ameya/a2a1b62a 2026-09-25 18:58].
- **Outcome:** Bakshi's later work was on the 26–27 Sep France diagnostics, the final package and the 7B (D-ORG-04, D-ORG-25).
- **Hindsight:** unknown (none recorded).
- **Links:** D-ORG-04 · D-ORG-10

### D-ORG-10 · No AWS for Bakshi's slow features; test their value first
- **When (IST):** 2026-09-25 21:05 · **Phase:** P1 · **Area:** ORG / FEA
- **Decided by:** agent for Ameya (a recommendation to Ameya)
- **Status:** adopted
- **Problem:** Bakshi's 56 string features ran at 73 s per 100k pairs, about 13 h per split on his laptop (65.2M train pairs, 57.6M test pairs). His only probe used true matches, so separation was untested.
- **Options considered:**
  1. A 96-core AWS box (about $4–5 per hour, 1–2 h of setup).
  2. A dev-kit test (about 40 min), then speed up the code.
  3. Rent hardware only after that.
- **Choice and why:** Option 2 first. "The actual issue isn't hardware … it would speed up features that may add nothing." Rented compute was judged allowed, because the rules restrict data, not compute.
- **Evidence:** [chat:ameya/a2a1b62a 2026-09-25 21:05].
- **Outcome:** Bakshi fixed the speed (dev kit 3.2M pairs in 3.6 min) [R]. PR #21 was merged by the main session on 26 Sep at 10:12; no gate showed that it added anything to model v1.
- **Hindsight:** unknown (none recorded).
- **Links:** [PR #21] · D-ORG-09

### D-ORG-11 · Treat the window as closing at 21:00 IST, without editing AGENTS.md
- **When (IST):** first seen 2026-09-26 02:05; issue #45 at 23:43; Bakshi's flag on 2026-09-27 01:11 · **Phase:** P2–P4 · **Area:** ORG
- **Decided by:** Ameya (captain). Bakshi's agent declined to edit the shared file.
- **Status:** adopted as the working deadline; AGENTS.md left at 23:59
- **Problem:** The submission-round page and AGENTS.md disagreed on the deadline.
- **Options considered:** close at 21:00, or at 23:59.
- **Choice and why:** Work to 21:00. The submission-round page gave "27 Sep 15:30 UTC = 21:00 IST" and said that "the private leaderboard uses the final submission", "to be confirmed in the logged-in portal". Bakshi's agent said: "AGENTS.md is a shared file, so it was not edited here — but it is the first file every agent reads, and it is wrong."
- **Evidence:** [status ameya @3f6d054](../../docs/status/ameya.md); [handover 2026-09-27_0111](../../docs/handover/2026-09-27_0111_bakshi_final-package.md).
- **Outcome:** Uploads were still accepted at about 21:55 ([LB 2026-09-27 #05](../../submissions/records/2026-09-27_sub05.md), [#06](../../submissions/records/2026-09-27_sub06.md)) and at about 23:40 ([#07](../../submissions/records/2026-09-27_sub07.md)) on 27 Sep. So the real close was later than 21:00, and no source says when it was [U]. A small PR to fix the AGENTS.md line was "the captain's call" and never appears. The page's sentence that the private leaderboard uses the final submission was never confirmed in the sources, and no source states whether the private ranking used Composite B (public 0.990879) or the last upload B7 (public 0.990875); this stays an open item.
- **Hindsight:** unknown (none recorded).
- **Links:** [handover 2026-09-27_0706](../../docs/handover/2026-09-27_0706_ameya_final-stack.md) · D-ORG-14

### D-ORG-12 · Do not restart reaped jobs without the human; then resumable, memory-aware chains
- **When (IST):** 2026-09-26 06:30–06:37, 11:21, 12:08 · **Phase:** P2–P3 · **Area:** ORG
- **Decided by:** agent for Ameya (a standing rule from earlier: "reaped background task: don't restart on your own"); Ameya approved at 11:19
- **Status:** adopted
- **Problem:** The AI coding tool's low-memory reaper stopped the v6nx wrapper and the queued 3.5 h rebuild at about 3 GB free. Stage 2 peaked at about 19 GB on a 31 GB machine.
- **Options considered:**
  1. Restart automatically.
  2. Wait for the human.
  3. Restart the tool with its background-shell pressure reaper disabled.
  4. A resumable chain whose steps record completion and wait for at least 12 GB free.
- **Choice and why:** Option 2 at 06:30, then option 4 after Ameya's go-ahead. The second reap (12:02) killed only the tracking; the processes kept running, and the agent recommended letting them continue.
- **Evidence:** About 4.7 h idle (06:37–11:19). The v6nx result already existed at 06:38 but was not read until 11:23 [M/R].
- **Outcome:** The rebuild finished at 14:27.
- **Hindsight:** Costly idle time. Asking before the user stepped away, or making long chains resumable and memory-aware from the start, would have saved about 4 h of compute.
- **Links:** [chat:ameya/19e315ba 2026-09-26 06:31], [11:21], [12:08] · D-ORG-07 · D-ORG-19

### D-ORG-13 · Competitors' public work: ideas only, no code reuse
- **When (IST):** 2026-09-26 14:45–14:56 · **Phase:** P3 · **Area:** ORG
- **Decided by:** agent for Ameya in session c0c64ad6, which raised the question to Ameya (searches by agents a8c26b84, a8b656b0 and a56d262f)
- **Status:** adopted (no reuse; moot, because there was nothing to read)
- **Problem:** Ameya, then 15th on the public leaderboard, wanted to know what the top 10 did differently.
- **Options considered:** not recorded beyond reading public work for ideas or not at all.
- **Choice and why:** Search public GitHub only, verify identity by name and college, and collect nothing beyond profile links. The agent warned that "copying code or ideas from another team's repo while the competition is live could break the challenge rules on plagiarism and sharing."
- **Evidence:** No 2026 solution repo from any top-10 team. About 50 public "Amazon ML Challenge 2026" repos existed, the best self-reporting about 0.981 on its own validation [R] [chat:ameya/agent-a8c26b84 2026-09-26 14:52].
- **Outcome:** Only style hints: past work of several top teams combined gradient-boosted trees with small fine-tuned language models, and one rank-1 member's recent Kaggle work used a deliberate hedge submission for a category missing from training [R] [chat:ameya/c0c64ad6 2026-09-26 14:56].
- **Hindsight:** unknown (none recorded).
- **Links:** [chat:ameya/c0c64ad6 2026-09-26 14:46]

### D-ORG-14 · Code freeze Sun 15:00 and final upload by 19:00
- **When (IST):** planned on 2026-09-26 16:40 · **Phase:** P3 → P4 · **Area:** ORG / SUB
- **Decided by:** Ameya (coordinator)
- **Status:** adopted on paper; not held
- **Problem:** Leave time for packaging before the close.
- **Options considered:** not recorded.
- **Choice and why:** "Code freeze Sun 15:00 (six hours before a 21:00 close): only packaging and documentation fixes after this." "Final leaderboard upload = the chosen final model, by 19:00; tag `final`."
- **Evidence:** [ROADMAP 3.6 and 4.5](../../docs/ROADMAP.md); [status ameya](../../docs/status/ameya.md).
- **Outcome:** Model and composition work ran to about 22:45 (the B+ package), and uploads to about 23:40. No `final` tag and no 27 Sep `sub/*` tag appear. The ZIP (the code-and-outputs package the organisers required) was assembled on 28–29 Sep.
- **Hindsight:** none recorded. For the record, the uploads after the planned freeze include mixmdp (about 16:40) and Composite B (about 20:55, the best public score) ([LB 2026-09-27 #03](../../submissions/records/2026-09-27_sub03.md), [#04](../../submissions/records/2026-09-27_sub04.md)).
- **Links:** D-ORG-11 · D-ORG-18

### D-ORG-15 · Rent GPUs for larger cross-encoders; upload only records and band pairs; stage 2 stays local
- **When (IST):** 2026-09-26 16:52–18:20; again after 21:40; Bakshi's boxes on 27 Sep · **Phase:** P3 · **Area:** ORG / CE
- **Decided by:** Ameya (compute and the traffic cap); agent for Ameya (the division of work); Sachi for her RTX 4090; Bakshi for his boxes
- **Status:** adopted
- **Problem:** The laptop (31 GB RAM, 12 GB GPU) could not run cross-encoder training and stage-2 retrains in parallel, and the GPU limited the cross-encoders to e5-small. Ameya: "we don't have to everything local, we have compute and we can spin up an EC2 instance and work parallely".
- **Options considered:**
  1. An EC2 g5.8xlarge (A10G with 24 GB, 128 GB RAM), the agent's first suggestion. Ameya provided a Vast.ai H100 instead: 80 GB GPU, 23 cores, 342 GB RAM, a non-persistent disk and a 30 GB traffic budget.
  2. Copy all computed features to the box (about 10.4–20 GB, about 45 min at 4 MB/s).
  3. Rebuild the features on the box from the records (about 2.5–3 h; it doubles as a reproduction check).
  4. Upload only the records (1.1 GB), the code and the cross-encoder band pairs (25–38 MB); bring back the logits (about 25 MB per model); retrain stage 2 locally.
- **Choice and why:** Option 4: the smallest traffic under Ameya's 30 GB cap and no rebuild delay. Later a trimmed stage-2 pack (about 3.3 GB, only the columns stage 2 reads) was also uploaded so that stage-2 variants could run on the box. Sachi chose an on-demand RTX 4090, "not spot, so no interruption risk". (An on-demand machine cannot be taken back; a spot machine is cheaper but the provider can stop it.)
- **Evidence:** e5-large band AUC 0.9391 on the holdout, against 0.9240 for e5-small and 0.9297 for stage-1 p1 [M]. Traffic about 7.8 GB at 18:26, about 13 GB after the pack, later about 24 GB of the 30 GB [R] [chat:ameya/19e315ba 2026-09-26 18:26], [19:58].
- **Outcome:** It worked until the spot interruption at about 21:40 (D-ORG-16, D-ORG-17). Every later model gain came from rented GPUs: v7ce3, v7n, v7s, v7sq and q7st.
- **Hindsight:** Spot capacity cost one model family at the worst moment: v7m, with the best French AUC (0.878).
- **Links:** [handover 2026-09-26_1817](../../docs/handover/2026-09-26_1817_ameya_ce-large-box.md) · [handover 2026-09-26_1800](../../docs/handover/2026-09-26_1800_sachi_llm-cross-encoder.md) · [decision model-v7n](../../docs/decisions/2026-09-26_2135_model-v7n.md) · [status ameya @bf744da](../../docs/status/ameya.md) · [theory: LLM verification and compute](../theory/10-llm-verification-and-compute.md)

### D-ORG-16 · After the spot box died, rebuild v7m's design locally as v7n
- **When (IST):** 2026-09-26 21:41–22:16 · **Phase:** P3 · **Area:** ORG
- **Decided by:** agent for Ameya
- **Status:** adopted
- **Problem:** The rented box stopped answering at about 21:40, and its disk is not persistent. Lost: the bge logits, the v7c, v7m and v7mst stage-2 scores (only v7m's train scores had arrived) and the running self-trained e5-large.
- **Options considered:**
  1. Wait for the box.
  2. Rebuild from the logits already copied back (e5-small, e5-base, e5l and e5l2).
- **Choice and why:** Option 2, now: e5-small plus the z-mean of e5l and e5l2 (feature group `cem2`), without bge. The local stage 2 takes about 26 minutes, so a validated package was possible by about 22:30 "regardless of the box".
- **Evidence:** v7n at c2: local holdout F0.5 0.991171 (+0.000072 [+0.000040, +0.000103]); with stage 3, 0.991211 (+0.000073 [+0.000041, +0.000102]) [M]. French rule AUC 0.8721 against v7m's 0.8776 [E] ([decision model-v7n](../../docs/decisions/2026-09-26_2135_model-v7n.md)).
- **Outcome:** Packaged at 22:16 and uploaded at about 23:05: public LB 0.989721 (rank 8 at the time).
- **Hindsight:** unknown (none recorded). The lost v7m had the best French rule AUC recorded at that point (0.8776, against 0.8721 for v7n).
- **Links:** D-ORG-15 · D-ORG-17 · D-EVL-11

### D-ORG-17 · Box policy: one on-demand 80 GB GPU; the traffic cap lifted
- **When (IST):** 2026-09-26 22:29–23:15 · **Phase:** P3 · **Area:** ORG
- **Decided by:** Ameya (purchases and the cap), on the agent's advice
- **Status:** adopted
- **Problem:** Box 1 was a spot instance and was outbid. Ameya asked whether to start a new one, and offered "2 small ones".
- **Options considered:**
  1. One H100 or A100 with 80 GB, on-demand (bge at about 00:15, e5ls at about 01:00).
  2. Two big boxes: faster, about twice the cost, two uploads.
  3. Two small 24 GB GPUs: e5-large "barely fits in 24 GB; too slow to be useful".
- **Choice and why:** Option 1, "on-demand, not interruptible, so it can't be outbid again", with at least 40 GB of GPU memory, 32 GB of RAM and 60 GB of disk; about $5–8 and a finish near 02:00 [R].
- **Evidence:** Box 2 (bought at about 22:42) also went down at about 23:10. Box 3, on-demand, ran from 23:15. Total traffic had reached about 23.7 GB, so a third setup would break the 30 GB cap; Ameya lifted it ("don't worry about the bandwidth now").
- **Outcome:** Box 3 was set up in about 14 minutes with a one-shot setup script. Both runs on it then hit NaN values (not-a-number errors in the numeric results), a cross-encoder problem recorded under area CE.
- **Hindsight:** unknown (none recorded).
- **Links:** D-ORG-15 · D-ORG-16 · D-ORG-20

### D-ORG-18 · Coordinate on issue #45; merge on Ameya's orders; only the captain uploads
- **When (IST):** 2026-09-27 01:37–02:54 (merges), 01:56, 03:25, 13:13–13:15, 17:16, 19:05 · **Phase:** P3–P4 · **Area:** ORG
- **Decided by:** Ameya (coordinator), through his agent ("push and merge our analysis so that others can see"; "Also push what we are doing so we don't waste each other's time"; "merge both PRs"; "Also merge latest, get main uptodate")
- **Status:** adopted
- **Problem:** Two agent sessions per member, rented boxes on three accounts and one upload budget. Main was also behind the work.
- **Options considered:** For merging, everything open, or only the non-draft PRs. Others not recorded.
- **Choice and why:**
  - A "live status" comment on #45 listing every running job "so nobody duplicates work". Status posts at 02:05, 02:38, 02:51, 03:25, 03:51, 05:20, 08:40, 09:15, 09:25, 09:50, 10:15 and 10:45.
  - A request for Bakshi's status every 30–45 min while Ameya slept ("Nothing is uploaded before Ameya is up").
  - Only the captain uploads.
  - Jobs placed on a teammate's idle GPUs are announced with the process ids to kill, run under `nice`, write only to their own directories, and are stopped on request.
  - Merges: rebase-merge after green CI, never `--admin` (when #52 hit branch protection, the agent waited for CI). On 27 Sep 01:37–02:54: #51, #52, #53, #50 (Bakshi's), #55, #54 (Bakshi's) and #57. At 13:13–13:15: [PR #58] (the stack, compose, the look-alike drop, guarded labels, research notes) as f71c9d9 and [PR #56] (Bakshi's) as c7f95b3. Only non-draft PRs; the drafts #60, #59, #49, #42 and #37 were left alone or for Ameya's call.
- **Evidence:** [chat:ameya/19e315ba 2026-09-27 01:37], [01:44], [01:55], [01:58], [02:48], [02:54], [13:13].
- **Outcome:**
  - Bakshi used RECIPE.md and the posts to make `reproduce.sh` switchable between models. He was silent from 03:08 to 09:08 (probably asleep) despite the 03:25 request. He acknowledged the gap ("I was idle-waiting on v7s rather than posting") and posted every 10–30 min from 09:08.
  - Ameya's synthetic jobs on Bakshi's boxes were stopped at 17:25 when he asked.
  - Main moved to c7f95b3 and the local checkout was fast-forwarded 142 commits. Later commits went on a rebased `ameya/final-stack` (ad84d66, d6c2e38, 119f204, 7cffc78 and the synth_fr3 commit).
- **Hindsight:** unknown (none recorded).
- **Links:** [issue #45], [issue #63], [PR #62 comment 19:05] · D-ORG-21 · D-ORG-24

### D-ORG-19 · After the crash: one heavy job at a time, a 15 GB memory guard, a pause flag
- **When (IST):** 2026-09-27 03:27–04:22 (the freeze was at about 03:35, the reboot at 03:40) · **Phase:** P4 · **Area:** ORG
- **Decided by:** Ameya (recorded in the research notes) and agent for Ameya (the guards)
- **Status:** adopted
- **Problem:** The integration laptop froze at about 03:35 and rebooted at 03:40, with no bugcheck and no GPU error. That fits memory exhaustion: the commit limit is 42.6 GB, about 23 GB is committed at idle, and on top ran stage 2 (16.5 GB), three analysis scripts (about 7 GB) and the acronym join (30M initials matches). Free memory had already dropped to 1.3 GB at 03:20.
- **Options considered:**
  1. Keep parallel chains.
  2. Move stage 2 to the rented box (about 1 TB of RAM and 192 CPUs), which first needs about 12 GB of stage-2 features uploaded.
  3. Serialise on the laptop with guards.
- **Choice and why:** Option 3. One stage-2 chain at a time. Wait for at least 15 GB available before each stage 2. A file `agents/PAUSE` stays on while stage 2, bagging, stage 3, decide, rules, the acronym join or a feature import runs, and sub-agents (helper agents started by the main agent session) wait for no PAUSE and at least 8 GB. At 04:22 a "gap-free" guard that also reads the chain logs replaced the first one, after a test slipped in between the guard's check and stage 2 starting.
- **Evidence:** Memory peaks measured at 05:09: decide 9.8 GB, acronym join 6.0 GB, rules 3.3 GB, stage 3 2.8 GB, stage 2 16.5–17.5 GB [M] [chat:ameya/19e315ba 2026-09-27 05:09]; [RESEARCH_v6 §6.16](../../experiments/ameya/model-v1/RESEARCH_v6.md). Nothing was lost, because artifact writes are atomic (a temporary file, then `os.replace`) and the chain resumed from its step markers; v7s was packaged at 03:49.
- **Outcome:** No further freezes. A "memory reaper" killed shell wrappers twice more (04:46 and 06:30), and every script survived.
- **Hindsight:** The guards cost serial time but protected every remaining chain on the final day.
- **Links:** [chat:ameya/19e315ba 2026-09-27 03:27], [03:46], [03:57], [04:22] · D-ORG-12 · D-ORG-20 · D-EVL-13

### D-ORG-20 · Stop the rented H100 once every output is safe; keep stage 2 on the laptop
- **When (IST):** 2026-09-27 03:51–03:55 (plan), 06:21 (stop) · **Phase:** P4 · **Area:** ORG
- **Decided by:** Ameya asked ("when you are done with vast ai, if you can you can shut off the instance from here"); the agent implemented it
- **Status:** adopted
- **Problem:** GPU billing against the risk of losing outputs.
- **Options considered:**
  1. Ship about 12 GB of stage-2 features to the box for a parallel stage 2.
  2. Keep stage 2 on the laptop and stop the box when its outputs are safe.
- **Choice and why:** Option 2. The laptop queue would finish by about 08:00 anyway. A script `box_stop.sh` fetches e5ls2, waits until qst and bges are settled, verifies all three outputs locally at full row counts (1,568,554 train and 1,490,930 test rows each), and then stops the instance with the vendor's command-line tool from inside the box, using the box's own credentials (no local tool or credentials were available). A `keep_box` file overrides it.
- **Evidence:** [chat:ameya/19e315ba 2026-09-27 06:21].
- **Outcome:** Stopped at 06:21. "Stop" is reversible, and storage keeps billing until the instance is destroyed in the vendor's console. The access keys are to be removed after the competition.
- **Hindsight:** unknown (none recorded).
- **Links:** D-ORG-19 · D-ORG-17

### D-ORG-21 · Handle Sachi's push to Ameya's PR branch with a normal commit, not a force-push
- **When (IST):** 2026-09-27 08:43–09:10 · **Phase:** P4 · **Area:** ORG
- **Decided by:** agent for Ameya; Bakshi asked for the duplicate script to go
- **Status:** adopted
- **Problem:** Sachi pushed `99a404d` (`reproduce_v7sq.sh`, placed in `experiments/bakshi/final-package/`) onto `ameya/final-stack`. That is two one-writer violations, and unreviewed content on Ameya's branch.
- **Options considered:**
  1. Force-push it away.
  2. Keep it.
  3. Remove it with a new commit.
- **Choice and why:** Option 3, after checking first. Its pseudo-label re-keying reproduced the real cross-encoder pseudo-label file exactly (385,274 pairs, 0 label disagreements), and its model naming was right. The agent asked Bakshi, as owner of the reproduction. After Bakshi folded v7sq and the stack step into his own `reproduce.sh`, the file was removed with `21bf128`. It stays in history, and two reproduction scripts cannot drift apart.
- **Evidence:** [chat:ameya/19e315ba 2026-09-27 08:44], [09:10].
- **Outcome:** Removed with a normal commit; no force-push.
- **Hindsight:** unknown (none recorded).
- **Links:** D-ORG-01 · D-ORG-18

### D-ORG-22 · Decline extra GPU instances until a concrete job existed
- **When (IST):** 2026-09-27 12:03, 13:18, 13:49, 13:55 (declined) → 14:09 (a 4090 asked for) → 16:08 (destroy recommended) → 16:11 and 17:24 (Ameya keeps it and adds a second) · **Phase:** P4 · **Area:** ORG
- **Decided by:** Ameya, who pays and provisions, on the agent's advice
- **Status:** mixed: declined at first, then accepted for specific jobs
- **Problem:** Ameya repeatedly offered GPUs: "any gain is worth spending" [13:50].
- **Options considered:**
  1. A single 4090 or 5090.
  2. A 4×H100 box.
  3. Nothing new.
- **Choice and why:** Declined while the bottleneck was the laptop's serial chain and the three uploads (as recorded): a 4090 needs 3–7 h per cross-encoder, and a 4×H100 7B run would land at 17:30–18:15 for +0.00003 to +0.0001. At 14:09 a concrete fit appeared: a French-heavy e5-large, about 1¾ h. The instance turned out to be an RTX 5090 with 32 GB. Once French-heavy members proved useless (16:03), the agent recommended destroying it. Ameya asked to keep it busy and added a second 5090 for the synthetic runs.
- **Evidence:** [chat:ameya/19e315ba 2026-09-27 13:49], [13:55], [16:11].
- **Outcome:** Two 5090s and Bakshi's idle GPUs ran synthetic models and round-1 seeds.
- **Hindsight:** unknown (none recorded).
- **Links:** D-ORG-24 · D-ORG-17

### D-ORG-23 · Pause the sub-agents for the usage limit; resume after the reset
- **When (IST):** about 2026-09-27 15:28 → 16:44 · **Phase:** P4 · **Area:** ORG
- **Decided by:** Ameya
- **Status:** adopted
- **Problem:** The AI tool's usage allowance was nearly exhausted until the reset at 17:30.
- **Options considered:** Keep the agents running, or pause them.
- **Choice and why:** Pause. The France-diff agent was stopped, and its leftover watcher scripts were killed so that they could not wake it. The agent for Ameya ran the valuations itself (`val_queue.sh`) behind a quiet watcher. At 16:44 the agent was resumed with three jobs: refit the backtest with the new leaderboard point, rank the candidates, and analyse French decisions by category.
- **Evidence:** [chat:ameya/19e315ba 2026-09-27 15:28], [16:44].
- **Outcome:** The valuations continued (D-EVL-14).
- **Hindsight:** unknown (none recorded).
- **Links:** D-EVL-14

### D-ORG-24 · Use every idle GPU, including Bakshi's boxes, in the last hours
- **When (IST):** 2026-09-27 18:38–19:37 · **Phase:** P4 · **Area:** ORG
- **Decided by:** Ameya ("you can pull all the data from his VM", 18:38; "Don't keep gpus idle", 18:50), on the proposal of agent for Ameya, who asked first because Ameya had earlier said to stop using Bakshi's boxes
- **Status:** adopted; ended by Ameya at 19:37 ("after 19:37 we will stop with the bakshi's gpu")
- **Problem:** Bakshi's 4×H100 training box had three idle GPUs and his 2×4090 pipeline box was idle. Scoring our 4.74M confident US/India pairs with the 7B needed about 55 min on three H100s, or about 2 h on our two 5090s.
- **Options considered:**
  1. Leave Bakshi's boxes alone, as Ameya had said earlier. Slower, and it misses the window.
  2. Use them for the US/India 7B scoring, the recall scoring and small detector jobs, and pull his data read-only to verify his work.
- **Choice and why:** Option 2. Every idle GPU-hour on the last evening could still feed an upload.
- **Evidence:** Bakshi had already started the US/India scoring himself (about 18:50) and it finished at 19:28. The agent's recall scoring then used all four H100s from 19:29 to 19:36 [R] [chat:ameya/19e315ba 2026-09-27 18:50], [19:29], [19:35].
- **Outcome:** It produced the 310 US/India drops that are in Composite B, and the negative recall result. One detector died with an out-of-memory error on a 4090; it duplicated an H100 run.
- **Hindsight:** Worth it: the US/India 7B scores went straight into the best submission.
- **Links:** [PR #62] comments · D-ORG-22 · D-EVL-16

### D-ORG-25 · Who writes what for the ZIP: Bakshi's driver, a fork's France block, the agent's document and assembly
- **When (IST):** 2026-09-29 01:26–01:54 · **Phase:** P5 · **Area:** ORG
- **Decided by:** agent for Ameya, approved by Ameya (issue #71)
- **Status:** adopted
- **Problem:** Bakshi's `REPRO_compositeB.sh` was a record that begins with `exit 0`, and his packaging scripts still targeted the older v7nst model. So nothing could regenerate Composite B from raw data, which the organisers require. The packaging files are in Bakshi's folder, which only he edits.
- **Options considered:**
  1. The agent extends `reproduce.sh` itself.
  2. Split the work by ownership.
- **Choice and why:** Option 2. Bakshi: a runnable driver for his half (7B training, g1w, the 7B re-check and the composition), packaging, requirements, README and two evidence scripts (items A–F of #71). Ameya's side: the France block that the driver calls (written by a fork, then reviewed), merging the rescued scripts, the documentation, and building the ZIP on the laptop.
- **Evidence:** Bakshi delivered items A and F by 01:45 and the driver (PR #72) by about 01:52; the France block landed at 02:12 [chat:ameya/19e315ba 2026-09-29 01:32], [01:52], [01:54], [02:12].
- **Outcome:** `src/box/compositeB.sh` runs steps 1–8, and step 7 calls `src/model_v1/pipeline/france_mixmdp.sh`.
- **Hindsight:** The split respected the repo's ownership rule and still finished before 04:00.
- **Links:** [issue #71] · [PR #72] · [PR #73] · D-ORG-26

### D-ORG-26 · Edit Bakshi's packaging files, with Ameya's permission
- **When (IST):** 2026-09-29 01:59–02:48 · **Phase:** P5 · **Area:** ORG
- **Decided by:** Ameya ("Yes do those edits", 02:42), on the proposal of agent for Ameya
- **Status:** adopted
- **Problem:** `pip install -r requirements.txt` from PR #72 failed: transformers 5.17.0 needs tokenizers 0.23.1 or later (below 0.24) and safetensors 0.8.0 or later, but the pins were 0.22.2 and 0.7.0, apparently from an older setup. The packager also did not ship the PDF and figures. Bakshi was probably asleep, and the repo rule says only he edits his folder.
- **Options considered:**
  1. Wait for Bakshi.
  2. Edit on a branch built on his PR, with the captain approving.
- **Choice and why:** Option 2. PR #74 pins tokenizers 0.23.2 and safetensors 0.8.0 (a pip dry run resolves), and `--doc` ships the PDF and figures. A note on #72 told Bakshi so that he would not duplicate the work or force-push.
- **Evidence:** pip ResolutionImpossible, then resolved (exit 0) [M] [chat:ameya/19e315ba 2026-09-29 02:00], [02:48].
- **Outcome:** Merged after #72; Bakshi's later clean install of the ZIP worked.
- **Hindsight:** A reviewer's first step would otherwise have failed.
- **Links:** [PR #72] · [PR #74] · D-ORG-25

### D-ORG-27 · Merge order; build the ZIP only from main
- **When (IST):** 2026-09-29 03:32–04:07 · **Phase:** P5 · **Area:** ORG
- **Decided by:** Ameya asked for the merges ("Do that finish off"); the order was chosen by the agent
- **Status:** adopted
- **Problem:** Four interdependent PRs: #70 (documents), #72 (the driver), #74 (fixes on top of #72) and #73 (the France block and the document).
- **Options considered:** not recorded.
- **Choice and why:** Rebase-merge #70, then #72, then #74 (rebased onto the new main and pushed with `--force-with-lease` to its own branch), then #73; later #76 and #77. Every ZIP was built from a clean detached checkout of main.
- **Evidence:** The trial build of #76 on its branch and the build from main had the same hash (`4ac35cc0…`) [chat:ameya/19e315ba 2026-09-29 03:32], [03:34].
- **Outcome:** The final build was made from main at ed5bc7e.
- **Hindsight:** unknown (none recorded).
- **Links:** D-ORG-18 · D-ORG-25

### D-ORG-28 · Finale: lead with candidate efficiency and the cascade
- **When (IST):** 2026-10-03 22:47 · **Phase:** P6 · **Area:** ORG
- **Decided by:** proposed by agent for Ameya; not yet decided in the sources
- **Status:** deferred (a proposal)
- **Problem:** The organisers ranked finalists on the private leaderboard, on blocking strategy and ML novelty ("finer-grained blocking keys (e.g., city/state) and novel, compute-efficient methods scored higher") and on candidate efficiency ("a lower average number of candidate pairs per record scored higher").
- **Options considered:** not recorded.
- **Choice and why:** Put the 3.70 candidates per S1 up front and tell the cascade story: XGBoost on 58M pairs, cross-encoders on 1.49M, and the 7B only as a re-checker, because running it everywhere would take about 27 GPU-hours. Prepare answers on city and state keys (in our pipeline city and state are features, not blocking keys) and on billions of records. About 7–9 slides for 10 minutes.
- **Evidence:** [chat:ameya/19e315ba 2026-10-03 22:47]. The proposal said "3.70 candidates per S1 at 99.1% true-pair recall"; that pairing is wrong. 99.1% is retrieval recall before the cut (about 34 per S1), and the 3.70 file holds about 98.2–98.4% (D-BLK-10; [finale README](../../finale/README.md)).
- **Outcome:** Open. Confirmed since: the deck is due Tue 6 Oct 2026 at 14:00 IST, and the finale is Wed 7 Oct (10 minutes plus 5 minutes of Q&A). Grenuke is 2nd of the Top 10; the organisers publish only rankings, not private scores.
- **Hindsight:** unknown (none recorded).
- **Links:** [finale README](../../finale/README.md) · D-BLK-10 · D-BLK-16 · D-BLK-02

### D-ORG-29 · Knowledge capture: redacted transcript digests and a common standard
- **When (IST):** 2026-10-03 22:58–23:07 · **Phase:** P6 · **Area:** ORG
- **Decided by:** Ameya; set up by agent for Ameya
- **Status:** adopted (in progress at the end of the sources)
- **Problem:** "We need to document, every decision, every step, every minor detail", and every member must know the whole pipeline and its theory.
- **Options considered:** not recorded.
- **Choice and why:** A repo script, `scripts/kb/digest_transcripts.py`, turns any member's chat logs into redacted, time-stamped Markdown (modes narrative, full and brief), so Bakshi and Sachi can run it too. Agents then extract from the digests.
- **Evidence:** First run: 16 narrative parts (5.2 MB), 27 sub-agent parts, 6 full parts. A redaction-order bug (3,001 leftover path fragments) was fixed and noisy notifications were collapsed [chat:ameya/19e315ba 2026-10-03 23:03], [23:06], [23:07].
- **Outcome:** This knowledge base is one product of it.
- **Hindsight:** unknown (none recorded).
- **Links:** [STANDARD](../STANDARD.md) · [CAPTURE](../CAPTURE.md)
