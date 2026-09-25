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
| — | — | — | — | — | — | Submission 1 is planned for Fri 25 Sep, before 23:30 |
