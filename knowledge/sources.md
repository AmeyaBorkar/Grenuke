# Sources

**Summary.** This page lists every source mined into the knowledge base and how far each was read: Ameya's three Claude Code sessions and their 26 sub-agent logs, the repository's records, plans, research documents and code, and GitHub's pull requests and issues. It says which extract (T1–T8, R1–R4) covered what, and what is not covered yet: Bakshi's and Sachi's own chats, WhatsApp and calls. State of 4 Oct 2026; times are IST.

## 1. How the sources were mined

- **Chats.** The session logs stay on Ameya's machine and are never committed ([STANDARD] §6). On 3 Oct `scripts/kb/digest_transcripts.py` made redacted digests in three modes: narrative (the text, one line per tool call, a short head and tail of each tool result), full (long tool results kept, for finding numbers) and brief (each sub-agent's task and final report).
- **Extracts.** Twelve agents each read one slice completely, in order, and wrote a structured extract with the same eleven parts: summary, timeline, decisions, experiments, failures, numbers, people, process, theory, conflicts and jury questions. Numbers cut from the narrative digests were recovered from the full digests.
- **Curated pages.** The curator's agents merged the extracts into the pages of `knowledge/`. Where sources disagree, the page keeps both statements and lists the conflict in [conflicts].
- **Interruption.** Extraction hit a usage limit on the night of 3–4 Oct. The agents were resumed, and all twelve extracts exist, written between 3 Oct 23:34 and 4 Oct 11:05.
- **Working files.** Digests and extracts live outside the repository. Only the curated pages are committed.
- **Cite forms** are in [STANDARD] §3: a chat is `[chat:ameya/<first 8 characters of the session id> YYYY-MM-DD HH:MM]`.

## 2. Chat sources

Sizes are characters in the digests [M].

| session | what it was | span | narrative digest | full digest | extract |
|---|---|---|---|---|---|
| 19e315ba | Ameya's main Claude Code session: built and ran the whole chain, directed 22 sub-agents | 25 Sep 11:00 → 3 Oct 23:07 | 13 parts, 4.28M | 4 parts, 6.70M | T1–T6 |
| a2a1b62a | Ameya's parallel research and coordination session | 25 Sep 13:08 → 27 Sep 18:39 | 2 parts, 0.69M | 1 part, 1.01M | T7 |
| c0c64ad6 | a short parallel session: summary of our pipeline, search for top-10 teams' public code, artifact export to Bakshi's agent | 26 Sep 14:45 → 27 Sep 01:56 | 1 part, 0.05M | 1 part, 0.09M | T7 |
| 26 sub-agents | launched by 19e315ba (22) and c0c64ad6 (4) | 25 Sep 20:33 → 29 Sep 02:11 | 27 files, 2.10M | task briefs: 26 files, 0.34M | T8 |

**The main session, by slice.**

| extract | digest parts | span | what it holds |
|---|---|---|---|
| T1 | 1–2 | 25 Sep 11:00 → 21:31 | problem intake, repository set-up, review of the final plan, blocking v0, baseline, models v1–v2, legal-form features |
| T2 | 3–4 | 25 Sep 21:32 → 26 Sep 14:28 | model v3, the leaderboard gap, France fixes (v4), generator rules, the candidate cut, research v5, blocking v3, v6all |
| T3 | 5–6 | 26 Sep 14:31 → 27 Sep 00:16 | research v6, rented H100, cross-encoders, v7n and v7nst, Sachi's Qwen PR |
| T4 | 7–8 | 27 Sep 00:18 → 10:58 | overnight chains, the stacked rules, the 03:35 crash, v7sq-dpc and its control |
| T5 | 9–10 | 27 Sep 10:59 → 18:08 | acronym test, per-country composites, France decision layer, language-model tests, mixmdp |
| T6 | 11–13 | 27 Sep 18:09 → 3 Oct 23:07 | the 7B re-check, Composite B and the later uploads, the ZIP, the methodology, 3 Oct |

**The 26 sub-agent logs.** T8 read every task and final report in full (the 26 briefs), plus the parent sessions around each launch and two task texts the brief file cut. Of the 2.10M characters of agent logs, only the decide and France-diff logs were read, in part. The intermediate reasoning of the other 24 agents was not read.

| agent | parent | span | task |
|---|---|---|---|
| a666ee54 | 19e315ba | 25 Sep 20:33–20:55 | web research on entity-resolution winning methods (no dataset content sent) |
| ada9694b | 19e315ba | 26 Sep 00:12–00:41 | web research on methods per stage, France, organiser updates |
| a1f88e87 | 19e315ba | 26 Sep 00:12–00:40 | fork: candidate-set size and duplicates |
| a4fa18c7 | 19e315ba | 26 Sep 00:12–00:39 | fork: audit of the v3 pipeline |
| a4957c58 | 19e315ba | 26 Sep 02:42–03:37 | leave-one-country-out anatomy |
| afe57301 | 19e315ba | 26 Sep 02:42–03:44 | catalogue of the data generator |
| a9638892 | 19e315ba | 26 Sep 04:59–05:30 | fork: ground-truth structure and joint decoding |
| ace27900 | 19e315ba | 26 Sep 04:59–05:28 | fork: preprocessing and vendor formats |
| a1f04ee8 | 19e315ba | 26 Sep 04:59–05:51 | fork: French residual errors and an estimator |
| a000fd3b | 19e315ba | 26 Sep 05:56–06:06 | fork: French weak-address families |
| a2066847 | 19e315ba | 26 Sep 05:56–06:27 | fork: the stage-3 module |
| a43953b5 | 19e315ba | 26 Sep 05:59–06:25 | fork: blocking v3 repairs, in its own worktree |
| a9bd3e4e | 19e315ba | 26 Sep 15:12–16:01 | SHAP attribution of French confidence |
| abb9ffcd | 19e315ba | 27 Sep 03:02–04:05 | hunt: simple rules from holdout errors |
| aeb3d218 | 19e315ba | 27 Sep 03:01–04:19 | polish: French rules |
| acec839c | 19e315ba | 27 Sep 03:01–12:42 | decide: the decision rule, then ranking of models |
| a2762d22 | 19e315ba | 27 Sep 10:16–22:31 | France-diff: why v7sq gained; referee of every late candidate |
| a4ea3fde | 19e315ba | 27 Sep 10:17–10:43 | teacher labels and the GPU plan |
| abeb7453 | 19e315ba | 27 Sep 10:17–11:34 | French error populations |
| ac6dce8e | 19e315ba | 27 Sep 12:58–14:30 | squeeze: US/India holdout gains |
| ad467765 | 19e315ba | 27 Sep 12:58–14:41 | candidate set and blocking note |
| a0889d36 | 19e315ba | 29 Sep 01:54–02:11 | fork: the France block of the ZIP |
| aadeeaba | c0c64ad6 | 26 Sep 14:45–14:46 | summary of our pipeline (Explore agent) |
| a8c26b84, a8b656b0, a56d262f | c0c64ad6 | 26 Sep 14:45–14:55 | search for the top-10 teams' public code, ranks 1–3, 4–6, 7–10 |

## 3. Repository sources

| source | what it is | extract | notes |
|---|---|---|---|
| `docs/handover/` | 24 handovers, 25 Sep 13:00 → 27 Sep 20:14 | R1 | all read |
| `docs/decisions/` | 16 decision and gate records | R1 | all read |
| `docs/status/` | `ameya.md` and `bakshi.md`; Sachi has none | R1 | all 47 committed versions read |
| `submissions/`, `CHANGELOG.md` | the protocol, 11 upload records (26–27 Sep), the Submissions table | R1, R2 | exact upload times exist only in the portal |
| `docs/ROADMAP.md`, `docs/TEAM.md`, `README.md`, `CONTRIBUTING.md`, `AGENTS.md` | coordination documents | R1 | ROADMAP was last updated 26 Sep 16:40 |
| `plans/` | Plan A, Plan B, the final plan, the decision record | R2, R3 | Plan C was never submitted |
| `experiments/ameya/model-v1/` | ANALYSIS_v2–v4, RESEARCH_v5–v6, the feature dictionaries, RECIPE, the pipeline and plan-check READMEs | R2 | the main research record |
| `docs/CONTRACTS.md`, `docs/DEVELOPMENT.md` | stage contracts C0–C10, developer guide | R2 | |
| `experiments/ameya/final-zip/doc/Documentation_template.md` | the submitted methodology | R2 | read first by every extract for orientation |
| code: `code/business_entity_resolution/src`, `experiments/ameya/model-v1/` (scripts, `stack/`, `pipeline/`), `experiments/bakshi/box/`, `experiments/sachi/*.py` | the final pipeline and the experiments | R4 | read as of 3 Oct (code unchanged between commits c01d6c2 and 4b5fa12) |
| `experiments/bakshi/**`, `plans/sachi/**`, unmerged branches | teammates' own folders | R3 | scripts outside the final chain were read by header only |
| GitHub pull requests and issues | export of 3 Oct 23:05: 61 PRs (56 merged, 5 open; 38 by Ameya, 14 by Bakshi, 9 by Sachi) and 16 issues (10 closed, 6 open) [M] | R3 | numbers #1–#77 |
| `git log` of main, unmerged branches | 229 commits; 10 unmerged remote branches (5 Bakshi, 3 Ameya, 2 Sachi) [M] | R3 | |
| `student_resource/`, organisers' blog and video | problem statement, guidelines, validator | T1 | read inside session 19e315ba |
| `finale/README.md`, finale template | logistics and judging criteria | T6 | relayed by Ameya on 3 Oct |

**PR and issue numbers #78–#81.** They were opened after the export, so no extract read them as GitHub records. #78 is the PR that added `knowledge/` and `finale/`; #80 and #81 are the capture requests to Bakshi and Sachi. The finale-plan issue also came after the export, and its number was not checked [U]. Their content is known from the files #78 added and from the 3 Oct part of the main session (T6).

## 3a. Bakshi's branch documents (merged on 4 Oct)

Five of Bakshi's PRs (#37, #42, #49, #59, #60) were still open when the knowledge base was mined; extract R3 read them from the branches. They are now on `main`, with his authorship kept:
- handovers: `docs/handover/2026-09-26_1613_bakshi_v5-tsv-audit.md`, `…_1637_bakshi_v7-france-probe.md`, `…_1903_bakshi_score-improvement-ideas.md`, `…_2339_bakshi_final-plan-review.md`, `docs/handover/2026-09-27_0952_bakshi_recovery-audit.md`, `…_1010_bakshi_score-0990545.md`, `…_1022_bakshi_nstdpc-control.md`;
- documents: `experiments/bakshi/PROGRESS_CAPSULE.md`, `experiments/bakshi/FINAL_DAY_REVIEW.md`, `plans/bakshi/RECOVERY_0991.md`, `plans/bakshi/AFTER_0990545.md`;
- code: `experiments/bakshi/v7/` (TSV audit, France probe, robust-drop probe, with tests: 17 pass).

His status snapshots from those branches were superseded by his current `docs/status/bakshi.md` and were not merged. The commits keep them.

## 4. The twelve extracts

Sizes are bytes of each extract file [M].

| extract | source slice | size | main content |
|---|---|---|---|
| T1 | main session, 25 Sep 11:00 → 21:31 | 131,554 | problem intake, set-up, plan review, blocking v0, models v1–v2 |
| T2 | main session, 25 Sep 21:32 → 26 Sep 14:28 | 140,647 | the France gap, v4, generator rules, candidate cut, v6all |
| T3 | main session, 26 Sep 14:31 → 27 Sep 00:16 | 123,604 | cross-encoders, v7n, v7nst, self-training |
| T4 | main session, 27 Sep 00:18 → 10:58 | 133,983 | overnight chains, stacked rules, v7sq-dpc |
| T5 | main session, 27 Sep 10:59 → 18:08 | 132,447 | composites, France decision layer, LLM tests, mixmdp |
| T6 | main session, 27 Sep 18:09 → 3 Oct | 127,555 | 7B re-check, Composite B, ZIP, methodology |
| T7 | sessions a2a1b62a and c0c64ad6 | 116,763 | plan checks, reviews, the loss ledger, gap research |
| T8 | the 26 sub-agent logs | 149,706 | tasks, findings and what the team did with them |
| R1 | handovers, decision and gate records, status files, upload records, changelog | 199,798 | what the team recorded, in time order |
| R2 | plans and research documents, contracts, methodology | 212,717 | plan against reality, the research record |
| R3 | all PRs and issues, teammates' folders and branches | 171,369 | Bakshi's and Sachi's work, process |
| R4 | code | 101,427 | how the final pipeline works, constant by constant |

## 5. What is not covered yet

- **Bakshi's own chats and notes.** His Claude Code sessions (the 27 Sep execution and review sessions, a cloud session), his Codex sessions for normalisation and features, and anything he decided by phone or message. The capture request is issue #80, due Sun 4 Oct 12:00. At the time of writing `knowledge/people/` holds only Ameya's folder, still with empty templates. What the pages say about his work comes from the repository, from PRs and issues, and from what Ameya's agents saw.
- **Sachi's own chats and notes.** Her AI-assistant sessions (their existence is inferred from a comment in her script [E]) and her own reasoning for the Qwen run, the synthetic French pairs and the gates. Capture request: issue #81, same deadline. Her own Qwen2.5-1.5B result is not recorded anywhere we read.
- **WhatsApp.** The team chat and the organisers' group. Only messages that Ameya pasted into a session are known, second hand.
- **Calls and talks in person.** None is recorded. A team call is planned for Sun 4 Oct 15:00.
- **The organisers' e-mails and the portal.** Known only as Ameya relayed them; exact upload times are only in the portal.
- **Ameya's own memory.** Reasons that never went through a chat (`[memory:ameya]`) are not captured yet.
- **Ameya's Claude Code memory notes** (six files) were not a mining target. They summarise the same sessions.
- **28 Sep.** The main session died at 00:12 (exit 137) and resumed on 29 Sep at 00:05, so that day has almost no chat coverage. The seven upload records of 27 Sep were written just before the crash; the commit was cut off, but the records reached main.
- **Depth limits.** Digests cut long tool results to a head and a tail. Sub-agent reasoning is covered by tasks and reports only. Experiment scripts outside the final chain are covered by headers.

[STANDARD]: STANDARD.md
[conflicts]: conflicts.md
