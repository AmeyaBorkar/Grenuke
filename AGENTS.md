# AGENTS.md: rules for AI coding agents (and a quick reference for humans)

AI coding agents load this file automatically: Claude Code (through `CLAUDE.md`), Codex, Cursor, Copilot, Gemini, Aider and others.
**Read all of it at the start of every session. It overrides your defaults.**
If it conflicts with an explicit instruction from the human member you work for, stop and ask before acting.

---

## 1. The project

- **Team Grenuke**, Amazon ML Challenge 2026: Business Entity Resolution.
- **Task:** for every Source-1 (S1) business record, list all Source-2/3 (S2/S3) records that describe the same business. That is 0 to 11 matches, 3.46 on average.
- **Metric:** macro F0.5 per S1 entity. Singletons count: an empty prediction scores 1.0 and any prediction scores 0.
- **Data:** 23.7M records. Train covers US and India; test adds France, which never appears in train.
- **Deadline:** **Sun 27 Sep 2026, 23:59 IST.**
- **Team:** three members work in parallel.
  - **The plan we build: `plans/FINAL_PLAN.md`.** The reasons for it are in `plans/DECISION.md`. The candidate plans are kept in `plans/<member>/`.
  - Current work: `docs/ROADMAP.md`. What changed: `CHANGELOG.md`.

---

## 2. Session protocol (every session)

### Start

1. `git fetch --all --prune`, then read in this order:
   1. this file
   2. `docs/ROADMAP.md`
   3. `plans/FINAL_PLAN.md`: at least §0, the §4 section for your area, and §9 (gates)
   4. `docs/TEAM.md` (who owns what)
   5. `docs/status/<member>.md`
   6. the 3 newest files in `docs/handover/` for your area
   7. `docs/CONTRACTS.md` and `docs/DEVELOPMENT.md`, if you touch code or data flow
2. **Find out which member you work for** and ask if unclear. You act only for that member, on that member's branches.
3. `git config core.hooksPath` must print `.githooks`. If it doesn't, run `git config core.hooksPath .githooks`.
4. Work on a branch **`<member>/<topic>`** created from the latest `origin/main`, e.g. `git switch -c ameya/blocking-v1 origin/main`. **Never work on `main`.**
5. If another agent session may run at the same time on this machine, give each session its own `git worktree`. Two agents must never share one working tree.

### During

- Edit only paths your member owns (`docs/TEAM.md`) and `experiments/<member>/`. If you need a shared file (§4) or another owner's path, **stop and ask the human**.
- Make small, focused commits (§5). Push your branch often: `git push -u origin <branch>`.
- Before calling a task done:
  - run `python -m pytest code/business_entity_resolution/tests -q`;
  - if outputs changed, run the validator (§7).

### End (mandatory)

1. **Handover.** Run `python scripts/new_doc.py handover --member <member> --topic <topic>`, fill in every section, and commit it on your branch.
2. **Status.** Update `docs/status/<member>.md`, and only your member's file.
3. **Push and PR.** Push the branch, then open or update the PR to `main`: `gh pr create --base main --fill`, or the web UI. Do **not** merge unless the human explicitly asks.

---

## 3. Hard rules

**MUST NOT**

- Commit, push, force-push, rebase or reset **`main`**. Changes reach `main` only through PRs that a human reviews and merges.
- Push to, rebase or rewrite **another member's branch**.
- Use `git push --force`. On your own branch, after a rebase, use `git push --force-with-lease`.
- Add **`Co-authored-by:`**, "Generated with …", "Assisted-by:", tool signatures, emoji bylines or **any co-author, collaborator or attribution line** to commits, PR titles or PR bodies.
  - The commit author is the human member.
  - Git hooks and CI reject violations.
- Commit data or large artifacts:
  - nothing from `student_resource/dataset/`, `data_cache/`, `work/` or `output/*.tsv`;
  - no `*.parquet`, `*.npy`, `*.pkl`, `*.pt` or `*.zip`;
  - no file over 5 MB;
  - no secrets or tokens.
- Use **external data, APIs, web lookups, geocoders or internet datasets** to resolve entities. The competition disqualifies for this. Only the provided data is allowed.
  - Hand-written lexicons (abbreviations, state names) are fine if documented.
- Upload to the leaderboard, or decide which submission is final. Humans do that (`submissions/README.md`).
- Edit shared files (§4), except in a dedicated PR the human asked for.
- Delete or rewrite other people's handovers, status files, decision records or plans.

**MUST**

- Use only models licensed **MIT or Apache-2.0** with **at most 8B parameters** in the final pipeline. Put the model name and license in the PR description.
- Treat `country` as an **open set**. Never hard-code, filter or one-hot it to {US, India}.
- Keep numbers comparable: evaluate with `ber.eval.metric` on the **shared holdout** from `ber.eval.splits` (§6).
- Add a component beyond the v0 baseline only after its gate has passed and been recorded:
  - the gates are in `plans/FINAL_PLAN.md` §9;
  - the test is a paired bootstrap from `ber.eval.gates`;
  - the result is a record in `docs/decisions/` (`docs/CONTRACTS.md` C10). Ties go to the simpler option.

---

## 4. Ownership and shared files

- **Area owners** are listed in `docs/TEAM.md` and `.github/CODEOWNERS`.
- **Shared files** change only through one small dedicated PR, reviewed by the coordinator:
  - `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `README.md`, `CHANGELOG.md`
  - `plans/FINAL_PLAN.md`, `plans/DECISION.md`
  - `docs/ROADMAP.md`, `docs/TEAM.md`, `docs/CONTRACTS.md`, `docs/DEVELOPMENT.md`
  - `code/business_entity_resolution/requirements.txt`, `pyproject.toml`
  - `src/ber/{io,ids,paths,artifacts,config}.py`, `src/ber/eval/**`
  - `.github/**`, `.githooks/**`, `scripts/**`, `.claude/settings.json`
- **One-writer files** have exactly one author, so they cannot conflict:

| path | the only writer |
|---|---|
| `docs/status/<member>.md` | that member |
| `docs/handover/*` | the author |
| `docs/decisions/*` | the author |
| `plans/<member>/**` | that member |
| `experiments/<member>/**` | that member |
| `submissions/records/*` | the submissions captain |

---

## 5. Commits and pull requests

- **Subject line:** Conventional Commits format, imperative mood, at most 72 characters. Example: `feat(block): add address-view kNN retriever`.
  - Types: `feat fix perf refactor test docs exp data build ci chore revert`.
  - Scopes: `normalize block features model eval io pipeline docs plans infra` and similar.
- **Body** (optional): what changed and why, plus numbers (holdout F0.5 before → after). No trailers of any kind.
- **PRs:**
  - Keep them small (aim for under ~400 changed lines).
  - Use the same title format and fill in the template.
  - Link your handover and state the metric impact.
  - A human merges them, **rebase-merge only**, after review and green CI.

---

## 6. Engineering conventions

- **Python and package.** Python ≥ 3.11 (team default 3.13). The package lives in `code/business_entity_resolution/src/ber`. Install it with `pip install -e code/business_entity_resolution`.
- **I/O.** Read data only through `ber.io` (tab separator, quoting disabled, because names contain quotes). Write outputs only through `ber.io.write_matching` / `ber.io.write_candidates`.
- **IDs.** Use integer `eid`s from `ber.ids` (`source * 1_000_000_000 + number`) in artifacts. Never rely on row order.
- **Artifacts.** Store them under `work/<stage>/<tag>/` (git-ignored), with the schemas in `docs/CONTRACTS.md`. Name tags `<member>-<stage>-v<N>` (C0), and never write into someone else's tag.
- **Evaluation.**
  - Shared holdout: `ber.eval.splits.is_holdout(...)`, 25% of train S1.
  - Metrics: `ber.eval.metric` (macro F0.5, blocking recall, oracle ceiling). Report them per country too.
- **Scale.** Never write Python loops over pairs. Use numpy/pandas/pyarrow, rapidfuzz `process.cpdist`, numba or the GPU.
  - Watch memory: teammates may have 16–32 GB.
  - Guard entry points with `if __name__ == "__main__":` (Windows uses spawn).
- **Reproducibility.** Fix seeds. Log the config and git commit with every reported number.

---

## 7. Validating outputs

```
python student_resource/utils/validate_submission.py --matching output/matching_results.tsv --candidate output/candidate_pairs.tsv --test-dir student_resource/dataset/test
```

- It must print `PASS`.
- The matches must be a subset of the candidates.
- There must be one row per test S1.

---

## 8. Where things are

| need | file |
|---|---|
| team rules (humans) | `CONTRIBUTING.md` |
| who owns what, branch prefixes | `docs/TEAM.md` |
| what to do next | `docs/ROADMAP.md` |
| **the plan we build** (stages, gates, milestones) | `plans/FINAL_PLAN.md` |
| why that plan, grafts, rejected ideas | `plans/DECISION.md` (candidates: `plans/<member>/PLAN.md`) |
| stage I/O schemas, holdout, folds, reporting, gate records | `docs/CONTRACTS.md` |
| how to run and extend the pipeline | `docs/DEVELOPMENT.md` |
| what changed, and every leaderboard upload | `CHANGELOG.md` |
| handovers / status / decisions | `docs/handover/`, `docs/status/`, `docs/decisions/` |
| leaderboard protocol | `submissions/README.md` |
| official problem statement, validator, doc template | `student_resource/` |

---

## 9. When unsure

Ask the human. For anything involving `main`, shared files, submissions, licenses or external data, a question is always better than a guess.
