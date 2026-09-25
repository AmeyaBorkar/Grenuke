# Roadmap

This is a shared file edited by the coordinator. Everyone else reports progress in `docs/status/<member>.md` and proposes changes there or in a PR.
All times are IST. Status values: `todo` / `doing` / `done` / `blocked` / `dropped`.

Window: **Fri 25 Sep 00:00 → Sun 27 Sep 23:59 IST.** Leaderboard budget: **5 uploads per day per team** (15 total).

## Phase 0: set up and decide (Fri, until about 16:00, time to be confirmed by the team)

| # | task | owner | status |
|---|---|---|---|
| 0.1 | Repo, rules, agent file, hooks, CI, templates, shared metric/holdout/IO | Ameya | done |
| 0.2 | Everyone: clone, run `scripts/setup`, get the dataset, run `pytest` | all | todo |
| 0.3 | Plans submitted to `plans/<member>/PLAN.md` (+ PDF) | each member | Ameya: done |
| 0.4 | Plan review with the `plans/README.md` rubric; pick a base plan and grafts; write `plans/DECISION.md` | all, chaired by the coordinator | todo |
| 0.5 | Fill in `docs/TEAM.md` (handles, owners); invite collaborators; update `CODEOWNERS` | coordinator | todo |
| 0.6 | Adjust `docs/CONTRACTS.md` to the chosen plan (dedicated PR) | coordinator + stage owners | todo |

## Phase 1: first end-to-end submission (Fri 16:00 → 23:30)

Goal: a **valid, honest baseline on the leaderboard before midnight**, so Friday's quota isn't wasted.

| # | task | owner | status |
|---|---|---|---|
| 1.1 | Normalization v1 (names, addresses, scripts) and cached records (`work/records/`) | _TBD_ | todo |
| 1.2 | Blocking v1 and candidate set; report pair recall and oracle ceiling on the holdout | _TBD_ | todo |
| 1.3 | Features v1 and stage-1 model; holdout macro-F0.5 | _TBD_ | todo |
| 1.4 | Decision rule (threshold or expected-F); write outputs; validator PASS | _TBD_ | todo |
| 1.5 | **Submission 1** (captain) + record + `sub/` tag | captain | todo |

## Phase 2: improve (Sat)

| # | task | owner | status |
|---|---|---|---|
| 2.1 | Error analysis on the holdout (false positives, false negatives by category and country) | _TBD_ | todo |
| 2.2 | Blocking v2: raise the recall ceiling | _TBD_ | todo |
| 2.3 | Stage-2 or collective features, calibration, per-entity decision | _TBD_ | todo |
| 2.4 | Distractor stress test and leave-one-country-out check (France proxy) | _TBD_ | todo |
| 2.5 | France-specific checks (lexicons, spot checks, leaderboard probe) | _TBD_ | todo |
| 2.6 | Submissions 2–6, each with a record | captain | todo |

## Phase 3: final improvements (Sun until 17:00)

| # | task | owner | status |
|---|---|---|---|
| 3.1 | Optional extras gated on holdout gain (ensembles, cross-encoder, and so on) | _TBD_ | todo |
| 3.2 | Choose the final model from the holdout (normal and stress) plus leaderboard consistency | all | todo |
| 3.3 | **Code freeze at 17:00**: only packaging and documentation fixes after this | coordinator | todo |

## Phase 4: package and submit (Sun 17:00 → 23:00, with a buffer)

| # | task | owner | status |
|---|---|---|---|
| 4.1 | Clean end-to-end re-run from raw TSV in a fresh env with pinned `requirements.txt` | _TBD_ | todo |
| 4.2 | `code/business_entity_resolution/README.md` with exact commands and run times | _TBD_ | todo |
| 4.3 | Fill in `Documentation_template.md` (methodology, blocking, features, results, error analysis) | _TBD_ | todo |
| 4.4 | Build `<team>_submission.zip` (output/, code/, doc); verify its structure; run the validator on the zipped outputs | _TBD_ | todo |
| 4.5 | **Final leaderboard upload = the chosen final model**; tag `final`; upload the zip on the portal | captain | todo |

## Standing rules

- Every session ends with a handover and a status update.
- Every leaderboard upload has a record plus a tag.
- No result counts without holdout numbers from `ber.eval` and the commit that produced them.
