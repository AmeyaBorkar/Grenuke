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
- **Competition (closed):**
  - the leaderboard window closed on Sun 27 Sep 2026;
  - the final ZIP was submitted on 29 Sep;
  - our submission is Composite B, public LB 0.990879.
- **Team:** three members work in parallel.
  - **The plan we built: `plans/FINAL_PLAN.md`.** The reasons for it are in `plans/DECISION.md`. The candidate plans are kept in `plans/<member>/`.
  - Current work: `docs/ROADMAP.md`. What changed: `CHANGELOG.md`.

### Current phase: Grand Finale preparation (from 3 Oct 2026)

- We are in the **Top 10 (2nd)**. The finale is **Wed 7 Oct 2026**: a 10-minute talk and 5 minutes of Q&A before senior Amazon scientists.
- **Deck deadline:** "Monday, 6 October 2026, 2:00 PM IST" per the organisers. 6 Oct is a Tuesday, so we plan for **Mon 5 Oct 14:00 IST** until they confirm. Details are in `finale/README.md`.
- **The work now is knowledge capture, the theory, the deck and rehearsal, not new models.**
  - Every decision, step and detail of how we built the solution goes into **`knowledge/`**, following **`knowledge/STANDARD.md`**.
  - Each member captures their own chats and notes with **`knowledge/CAPTURE.md`**. See §10.

---

## 2. Session protocol (every session)

### Start

1. `git fetch --all --prune`, then read in this order:
   1. this file
   2. `docs/ROADMAP.md`
   3. **in the finale phase:** `finale/README.md`, `knowledge/README.md` and `knowledge/STANDARD.md`
   4. `plans/FINAL_PLAN.md`: at least §0, the §4 section for your area, and §9 (gates)
   5. `docs/TEAM.md` (who owns what)
   6. `docs/status/<member>.md`
   7. the 3 newest files in `docs/handover/` for your area
   8. `docs/CONTRACTS.md` and `docs/DEVELOPMENT.md`, if you touch code or data flow
2. **Find out which member you work for** and ask if unclear. You act only for that member, on that member's branches.
   - Their tasks are GitHub issues assigned to them: `gh issue list --assignee <handle>` (handles in `docs/TEAM.md`). Each issue has the spec, the contract, the due time and "done when". Link the issue in the PR (`Closes #N`).
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

1. **Handover or journal.**
   - After code or data-flow work, run `python scripts/new_doc.py handover --member <member> --topic <topic>`, fill in every section, and commit it on your branch.
   - After knowledge, theory or finale work, add a session entry to `knowledge/people/<member>/journal.md` instead (`knowledge/STANDARD.md` §2.5).
   - Either way, record every decision you made in the standard decision format.
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
- **Commit chat transcripts, chat exports or digests:**
  - `*.jsonl`, `work/kb_digest/`, ChatGPT, WhatsApp or web-chat exports;
  - they stay on the member's machine;
  - hooks and CI block `*.jsonl`.
- Put **secrets or personal data** in `knowledge/` or `finale/`: IPs, ports, host names, SSH details, tokens, e-mails, phone numbers, personal paths.
- **Invent facts, numbers or references.** Unknown is written as "unknown" and listed in `open-questions.md` or `knowledge/conflicts.md`.
- Edit another member's `knowledge/people/<member>/` folder.

**MUST**

- Use only models licensed **MIT or Apache-2.0** with **at most 8B parameters** in the final pipeline. Put the model name and license in the PR description.
- Treat `country` as an **open set**. Never hard-code, filter or one-hot it to {US, India}.
- Keep numbers comparable: evaluate with `ber.eval.metric` on the **shared holdout** from `ber.eval.splits` (§6).
- Add a component beyond the v0 baseline only after its gate has passed and been recorded:
  - the gates are in `plans/FINAL_PLAN.md` §9;
  - the test is a paired bootstrap from `ber.eval.gates`;
  - the result is a record in `docs/decisions/` (`docs/CONTRACTS.md` C10). Ties go to the simpler option.
- In `knowledge/` and `finale/`, give **every number a scope, an evidence level (M/E/R/U) and a source**, as in `knowledge/STANDARD.md` §3.
  - Always say which evaluation a score comes from: the local holdout, the public LB or the private LB.

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
  - `knowledge/STANDARD.md`, `knowledge/CAPTURE.md`, `knowledge/templates/**`
- **Curated files**:
  - which: every other file in `knowledge/` (outside `people/`), and everything in `finale/`;
  - who writes: the curator, Ameya, or an agent working for him;
  - how: changes go through a PR;
  - corrections from others: comment on the PR, or send a small PR that the curator reviews.
- **One-writer files** have exactly one author, so they cannot conflict:

| path | the only writer |
|---|---|
| `docs/status/<member>.md` | that member |
| `docs/handover/*` | the author |
| `docs/decisions/*` | the author |
| `plans/<member>/**` | that member |
| `experiments/<member>/**` | that member |
| `knowledge/people/<member>/**` | that member |
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
  - Watch memory: teammates have 8–16 GB (`docs/TEAM.md`, machines). Develop on the **dev sample** (`ber.eval.splits.in_dev_sample`, `--set sample=dev`); full-scale runs happen on the integration machine.
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
| **the finale**: logistics, deadlines, judging criteria, deck, script | `finale/README.md` |
| **the knowledge base**: decisions, experiments, numbers, components, theory, Q&A | `knowledge/README.md` |
| how to record knowledge (formats, sources, evidence levels) | `knowledge/STANDARD.md` |
| how to capture your own chats and notes | `knowledge/CAPTURE.md`, `scripts/kb/digest_transcripts.py` |

---

## 9. When unsure

Ask the human. For anything involving `main`, shared files, submissions, licenses or external data, a question is always better than a guess.

---

## 10. Knowledge capture and the finale

- **Goal:** one complete, sourced record of how we built the solution.
  - What it contains: every decision and its reason, every experiment (wins and dead ends), every number we may quote, who did what, and the theory behind each technique.
  - Why: any member can then defend any part of it to the jury.
- **Formats:** `knowledge/STANDARD.md`. It covers decisions `D-<AREA>-NN`, experiments `EXP-NNN`, timeline rows, the fact sheet, component pages, theory pages, Q&A entries and evidence levels M/E/R/U.
- **Your own capture:**
  - follow `knowledge/CAPTURE.md`: make redacted digests of your chats with `scripts/kb/digest_transcripts.py`, then write `knowledge/people/<member>/` on a `<member>/kb-capture` branch;
  - digests stay in `work/kb_digest/`.
- **Agents mining chats:**
  - read every assigned source completely, in order;
  - cite each fact (`[chat:<member>/<session8> YYYY-MM-DD HH:MM]`, `[PR #N]`, or a repo path);
  - mark evidence levels;
  - put anything unclear in `open-questions.md` (`knowledge/conflicts.md` when curating);
  - never smooth a disagreement away.
- **The deck and the script** (`finale/`) quote only numbers that are in `knowledge/numbers.md`, so the talk, the Q&A and the methodology document never disagree.
- **No new modelling is planned.**
  - An experiment to answer a likely jury question needs the human's go-ahead first.
  - Example: blocking recall with city/state keys versus ours.
  - Such an experiment follows the normal rules: holdout, gate and record.
