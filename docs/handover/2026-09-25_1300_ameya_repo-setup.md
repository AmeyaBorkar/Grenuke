# Handover: repo-setup

- **Author:** ameya (human; the agent was Claude Code)
- **When (IST):** 2026-09-25 13:00
- **Branch / PR / last commit:** `main`. This was the bootstrap, pushed directly because the repo was empty. Every later change goes through PRs.
- **Area and paths touched:** the whole repo skeleton (rules, docs, hooks, CI, scripts), the shared foundation in `code/business_entity_resolution/`, and `plans/ameya/`

## TL;DR (3 lines max)

The repo is ready for three people and their agents working in parallel: branches per member, one-writer coordination docs, hooks and CI that enforce "no co-author lines, no data, no direct pushes to main", and a shared metric, holdout and I/O so numbers are comparable. Plan A is in `plans/ameya/` (MD + PDF). Next: teammates join, add plans B and C, then the decision meeting.

## What was done

- **Rules:**
  - `AGENTS.md` is the source of truth for AI agents. `CLAUDE.md` imports it; `GEMINI.md`, `.github/copilot-instructions.md` and `.cursor/rules/agents.mdc` point to it.
  - `CONTRIBUTING.md` holds the team rules.
- **Coordination:**
  - `docs/ROADMAP.md`, `docs/TEAM.md`, `docs/CONTRACTS.md`
  - templates for `docs/handover/`, `docs/status/`, `docs/decisions/` and `submissions/records/`
  - `plans/README.md` (decision process and rubric), `plans/DECISION.md` (pending)
- **Enforcement:**
  - `.githooks/commit-msg`: no co-author or attribution lines; Conventional Commit subjects.
  - `.githooks/pre-commit`: no commits on `main`, no data or files over 5 MB, no secrets.
  - `.githooks/pre-push`: no direct pushes to `main`.
  - `.github/workflows/checks.yml`: the same policies plus unit tests.
  - `.claude/settings.json`: attribution off.
  - PR template and CODEOWNERS.
- **Scripts:**
  - `scripts/setup.{ps1,sh}`: one-time setup per clone (hooks path, rebase-on-pull, optional venv).
  - `scripts/new_doc.py`: creates handover, status, decision and submission docs with IST names.
  - `scripts/md_to_pdf.py`: plan to PDF.
- **Shared code (`ber`):**
  - `ber.io`: safe TSV readers (quoting off) and exact-format writers.
  - `ber.ids`: lossless integer eids.
  - `ber.eval.metric`: macro F0.5, pair recall, oracle ceiling, report.
  - `ber.eval.splits`: splitmix64 holdout, 25%.
  - 24 unit tests.
- **Plan A:** `plans/ameya/PLAN.md` + `PLAN.pdf` (8 pages).

## Current state

- **Works:**
  - `pytest`: 24 passed.
  - On real data:
    - `ber.io.truth_pairs` gives 7,638,365 true pairs (matching the EDA).
    - The holdout has 549,699 S1 (24.9%): US 329,717, India 219,982.
    - Perfect prediction scores 1.0000; empty prediction scores 0.0558 (the singleton share).
  - `ber.io.write_matching` / `write_candidates` produce 1,732,544-row files that the **official validator passes, including `--check-ids`**.
- **Half-done:** `docs/TEAM.md` still has placeholders for members 2 and 3 (names, handles, owners).
- **Known caveats:**
  - Branch protection on `main` may be unavailable for private repos on the free GitHub plan. Hooks and CI enforce the rules in that case (see the PR or chat note).
  - Everyone must run `scripts/setup` once, otherwise the hooks are not active in their clone.

## Numbers (shared holdout, `ber.eval`; include the command)

| metric | value | command / tag |
|---|---|---|
| holdout size | 549,699 S1 (24.9%) | `ber.eval.splits.is_holdout(to_eids(train_s1.entity_id))` |
| empty-prediction baseline | 0.0558 macro F0.5 | `ber.eval.report(None, truth_pairs, holdout)` |
| official validator on `ber.io` output | PASS (with `--check-ids`) | `python utils/validate_submission.py ... --check-ids` |

## How to reproduce or continue (exact commands)

```
git clone https://github.com/AmeyaBorkar/Grenuke.git && cd Grenuke
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1 -Venv      # or: bash scripts/setup.sh --venv
# copy the Unstop dataset to student_resource/dataset/{train,test}/
python -m pytest code/business_entity_resolution/tests -q
python scripts/new_doc.py status --member <you>
git switch -c <you>/plan origin/main    # add plans/<you>/PLAN.md, then open a PR
```

## Artifacts (local paths / drive links + sha256)

- The Parquet cache of all TSVs is in Ameya's local `data_cache/` (git-ignored). Anyone can rebuild it in about 30 s with pyarrow (see Plan A §4.1).

## Next steps (ordered, with suggested owner)

1. Members 2 and 3 send their GitHub handles. Ameya invites them (`gh api -X PUT repos/AmeyaBorkar/Grenuke/collaborators/<handle> -f permission=push`) and fills in `docs/TEAM.md` and `CODEOWNERS`.
2. Every member runs setup, gets the dataset, and runs the tests.
3. Members 2 and 3 add `plans/<name>/PLAN.md` (+ PDF with `python scripts/md_to_pdf.py`) through a PR.
4. Decision meeting (`plans/README.md`): fill in `plans/DECISION.md`, assign owners, adjust `docs/CONTRACTS.md` if needed.
5. Start Phase 1 of `docs/ROADMAP.md`. The first submission is due before midnight.

## Blockers, open questions, decisions needed

- Who are the coordinator and submissions captain? Proposed: Ameya for both, to be confirmed at the decision meeting.
- The time of the decision meeting. The roadmap assumes about 16:00 IST.
