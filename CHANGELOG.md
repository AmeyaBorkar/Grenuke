# Changelog

Notable changes to the pipeline, the plan, the contracts and the team process. Newest first; times are IST.
- **Format:** based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Each leaderboard upload also gets a row under **Submissions**.
- **Who writes it:**
  - The coordinator updates this file when a batch of PRs merges.
  - The submissions captain adds a row for every upload.
- **Feature PRs don't edit it,** because parallel edits would conflict. Put a one-line `Changelog:` note in your PR description instead, and the coordinator copies it here.
- **Versions** follow milestones:
  - 0.x until the first end-to-end submission;
  - 1.0.0 for Submission 1 (the v0 baseline);
  - a minor bump for each submitted improvement;
  - the tag `final` for the packaged final submission.

## [Unreleased]

### Added
- `plans/FINAL_PLAN.md` v1.0, the plan we build. It combines:
  - Plan A as the base;
  - Plan B's gates and evidence tags;
  - Plan B's blocking, normalization and ownership grafts;
  - the data checks of 25 Sep: the test shift type, the look-alike signature, no postcodes.
- `docs/CONTRACTS.md` v1:
  - C0: tags and artifact paths;
  - C2: OOF groups and a fold-0 dev subset;
  - C3: normalized record columns;
  - C4: candidate metadata;
  - C5: stage-1 scores;
  - C7: report keys;
  - C8: features (new);
  - C9: matches (new);
  - C10: gate records (new).
- This changelog.

### Changed
- `plans/DECISION.md`: filled in with the base, grafts, rejected ideas, rubric scores and owners.
- `docs/ROADMAP.md`: rebuilt around milestones M0–M9 of the final plan, with owners, "done when" criteria, gates G1–G13 and the submission plan.
- `docs/TEAM.md` and `.github/CODEOWNERS`: added Sachi (@ssdhoka06) and Member 3 (@trustdemons05), plus the proposed area owners.
- `AGENTS.md`, `README.md`, `CONTRIBUTING.md` and `plans/README.md` now point to the final plan, the changelog and the developer guide. The shared-file list and the gate rule are updated.
- The PR template has fields for the roadmap task, the gate and a changelog line.

### In progress
- The pipeline skeleton and `docs/DEVELOPMENT.md`, in PR #4. It adds:
  - the `ber.pipeline` CLI;
  - the `records`, `write` and `evaluate` stages;
  - artifact metadata;
  - OOF groups;
  - the paired-bootstrap gates;
  - stubs for the stages owned by each area.

## [0.1.0] - 2026-09-25 - repo bootstrap and plans

### Added
- The organizer bundle (problem statement, validator, documentation template) and repo hygiene files (`09955f4`).
- Team rules and coordination:
  - `AGENTS.md`, with pointers from `CLAUDE.md`, `GEMINI.md`, Copilot and Cursor;
  - `CONTRIBUTING.md`;
  - the roadmap, team page and contracts v0;
  - templates for handovers, status, decisions and submissions (`ea0a619`).
- Enforcement (`b9f583f`):
  - git hooks: no commits or pushes to `main`, no data, large files or secrets, no attribution lines, Conventional Commits;
  - CI checks and setup scripts.
- The shared foundation, with 24 tests (`a9a7218`):
  - `ber.io`: safe TSV I/O and exact-format writers;
  - `ber.ids`: int64 eids;
  - `ber.eval.metric`: macro F0.5, pair recall, oracle ceiling;
  - `ber.eval.splits`: the shared 25% holdout.
- Plan A by Ameya, Markdown and PDF (`4dd7fb2`), and Plan B by Sachi (`07259b8`, PR #2).
- The repo-setup handover and status (`9b5a73c`), and a record of the branch protection on `main` (`3fcbfb3`, PR #1).

## Submissions

| # | date (IST) | tag | commit | holdout F0.5 (all / US / India) | public score | notes |
|---|---|---|---|---|---|---|
| earlier | 25 Sep | — | — | v2 0.98436; v3 0.98882 | v2 0.97608; v3 0.97961 | recorded in `docs/status/ameya.md`; France ≈ 0.93 (`RESEARCH_v5.md` §1) |
| 2026-09-26 #01 | 26 Sep | `sub/2026-09-26-01` | `75655e5` | 0.990156 / 0.98997 / 0.99043 | **0.98781** (rank 15) | v5all + France rules v2 + 3.70 candidates per S1 (`2026-09-26-v5all-ops2-c2`); France implied 0.971–0.976; record `submissions/records/2026-09-26_sub01.md` |
| 2026-09-26 #02 | 26 Sep | `sub/2026-09-26-02` | `017f2e6` | 0.990842 / 0.99070 / 0.99106 | **0.988609** (rank 15) | v6all + stage 3 + rules v3 + acronym join (`2026-09-26-v6all-s3-ops3a-c2`); France implied 0.973; record `submissions/records/2026-09-26_sub02.md` |
| 2026-09-26 #03 | 26 Sep | `sub/2026-09-26-03` | PR #43 | 0.991211 / 0.99102 / 0.99150 | **0.989721** (rank 8) | v7n: stage 2 with the mean of two multilingual-e5-large cross-encoders (`2026-09-27-v7n-s3-ops3a-c2`); France implied 0.978; record `submissions/records/2026-09-26_sub03.md` |
| 2026-09-26 #04 | 26 Sep | `sub/2026-09-26-04` | `72a221f` | 0.991194 / 0.99101 / 0.99147 | **0.990179** (rank 7) | v7nst: v7n + stage-2 self-training on France (`2026-09-27-v7nst-s3-ops3a-c2`); France implied 0.981; record `submissions/records/2026-09-26_sub04.md` |
| 2026-09-27 #01 | 27 Sep | — | PR #58 | 0.991194 (s3) | **0.990264** | v7nst + the stacked decision (`-dpc`: expected-F0.5 per S1 + rules); record `submissions/records/2026-09-27_sub01.md` |
| 2026-09-27 #02 | 27 Sep | — | PR #58 | 0.991246 / combo 0.991280 | **0.990545** (rank 7) | v7sq-dpc: Qwen2.5-1.5B and a self-trained e5-large in the mix; France +0.0016; record `2026-09-27_sub02.md` |
| 2026-09-27 #03 | 27 Sep | — | PR #65 | US/India v7sq3 combo 0.991307 | **0.990699** (rank 12) | mixmdp: v7sq3 US/India + round-2 guarded French self-training (v7sq7wg) − look-alikes + France DP; record `2026-09-27_sub03.md` |
| 2026-09-27 #04 | 27 Sep | — | PR #62, #65 | g1w 0.991323 | **0.990879** (rank 16) — **team best** | Composite B: g1w US/India (7B ×2 in stage 2) + mixmdp France, minus the 7B out-of-band rejects (840 FR, 310 US/IN); record `2026-09-27_sub04.md` |
| 2026-09-27 #05 | 27 Sep | — | PR #65 | as B | **0.990833** | mixf7: B with round-3 France (v7sq6r3); −46e-6 vs B; record `2026-09-27_sub05.md` |
| 2026-09-27 #06 | 27 Sep | — | PR #65 | as B, US v7sq3 | **0.990819** | mixf2: mixf7 with v7sq3 US; g1w US is +14e-6; record `2026-09-27_sub06.md` |
| 2026-09-27 #07 | 27 Sep | — | PR #62 | as B | **0.990875** | B7 (the last upload): B + French 7B drops extended with Qwen3-4B agreement; a tie with B; record `2026-09-27_sub07.md` |
