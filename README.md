# Grenuke: Amazon ML Challenge 2026, Business Entity Resolution

Private team repository. Deadline: **Sun 27 Sep 2026, 23:59 IST**. Leaderboard uploads are limited to **5 per day** across the whole team.

**The task:** for every Source-1 business record, find all Source-2/3 records that describe the same business.
- Only the name and address are available.
- Train covers US and India; test also includes **France**.
- Scoring is macro **F0.5** per Source-1 entity, and singletons count.

## Start here

| you are | read |
|---|---|
| a teammate | `CONTRIBUTING.md` (rules), `docs/TEAM.md` (owners), `docs/ROADMAP.md` (what's next) |
| an AI coding agent | **`AGENTS.md`** (mandatory; `CLAUDE.md`, `GEMINI.md`, Copilot and Cursor files point there) |
| comparing plans | `plans/README.md`, then `plans/<member>/PLAN.md` |
| submitting to the leaderboard | `submissions/README.md` |

## One-time setup

```
git clone https://github.com/AmeyaBorkar/Grenuke.git
cd Grenuke
# Windows  : powershell -ExecutionPolicy Bypass -File scripts/setup.ps1 -Venv
# mac/Linux: bash scripts/setup.sh --venv
```

Then copy the Unstop dataset into `student_resource/dataset/train/` and `student_resource/dataset/test/`. It is git-ignored and must never be committed.

## Daily loop

1. `git fetch`, then `git switch -c <you>/<topic> origin/main` (or rebase your existing branch on `origin/main`).
2. Work inside your area. Make small commits in `type(scope): summary` form, with **no co-author lines**.
3. Run the tests with `python -m pytest code/business_entity_resolution/tests -q`, and score with the shared metric and holdout.
4. Write a handover with `python scripts/new_doc.py handover ...` and update `docs/status/<you>.md`.
5. Push and open a PR to `main`. After review and green CI, **rebase-merge** it.

## Repo map

```
AGENTS.md  CLAUDE.md  GEMINI.md        agent rules (AGENTS.md is the source of truth)
CONTRIBUTING.md                        team rules
plans/<member>/PLAN.md|.pdf            candidate plans; plans/DECISION.md = what we chose
docs/ROADMAP.md  TEAM.md  CONTRACTS.md roadmap, owners, stage I/O contracts
docs/status/  handover/  decisions/    one-writer coordination docs (+ TEMPLATE.md each)
submissions/                           leaderboard protocol + one record per upload
experiments/<member>/                  personal scratch space (notebooks, prototypes)
code/business_entity_resolution/       the deliverable package (src/ber, README, requirements)
student_resource/                      organizer bundle: problem README, validator, doc template
scripts/                               setup + document scaffolding
.githooks/  .github/                   enforcement (hooks, CI, PR template, CODEOWNERS)
```

## Shared building blocks (already in `main`)

- `ber.io`: safe TSV readers (tab separator, quoting disabled) and exact-format output writers.
- `ber.ids`: integer entity keys (`source * 1e9 + number`).
- `ber.eval.metric`: the official macro F0.5, blocking pair recall and an oracle ceiling.
- `ber.eval.splits`: the **shared holdout** (25% of train S1, deterministic), so everyone's numbers are comparable.

## Final deliverable (built at the end, see `docs/ROADMAP.md`)

```
<team>_submission.zip
├── output/matching_results.tsv, candidate_pairs.tsv
├── code/business_entity_resolution/{src/, README.md, requirements.txt}
└── Documentation_template.md   (filled in)
```
