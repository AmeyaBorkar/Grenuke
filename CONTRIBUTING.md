# Contributing: how we work together without stepping on each other

Three people (and their AI agents) work in parallel for 72 hours. These rules keep `main` runnable, prevent merge conflicts, and make every result reproducible.
AI agents follow the same rules through `AGENTS.md`.

## 1. Principles

1. **Everyone owns an area.** You edit your area. For anything else, ask the owner (`docs/TEAM.md`).
2. **Contracts first.** Stages exchange data only through the formats in `docs/CONTRACTS.md`. That lets us build stages in parallel and swap in components from different plans.
3. **One writer per coordination file.** Each person has their own status file, each handover is its own file, and each submission record is its own file. So these files never conflict.
4. **Small PRs, merged often.** Branches live at most about a day. Rebase on `main` before opening a PR.
5. **Comparable numbers.** Everyone scores with `ber.eval.metric` on the same holdout (`ber.eval.splits`). Any number without the command and commit that produced it doesn't count.

## 2. One-time setup (per clone)

```
git clone https://github.com/AmeyaBorkar/Grenuke.git && cd Grenuke
# Windows:  powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
# mac/Linux: bash scripts/setup.sh
```

The setup script:
- enables the repo's git hooks (`core.hooksPath=.githooks`);
- sets `pull.rebase=true`, `fetch.prune=true` and `rebase.autoStash=true`;
- checks that your git name and email are set;
- with the `-Venv` / `--venv` flag, also creates `.venv` and installs the package.

Then put the Unstop dataset in `student_resource/dataset/{train,test}/`. It is git-ignored, so never force-add it.

## 3. Branches

| branch | purpose | who writes |
|---|---|---|
| `main` | integration branch, always runnable; every leaderboard upload is tagged from here | nobody directly, PRs only |
| `<member>/<topic>` | your work, e.g. `ameya/blocking-v1`, `riya/fr-lexicons` | only that member (and their agents) |
| `<member>/exp-<topic>` | throwaway experiments that may never merge | only that member |

- Branch names use a lowercase prefix plus a kebab-case topic. Prefixes are listed in `docs/TEAM.md`.
- Always branch from the latest `origin/main`: `git fetch && git switch -c <member>/<topic> origin/main`.
- To catch up with `main`, rebase: `git fetch && git rebase origin/main`. Then push with `git push --force-with-lease`, which is allowed on your own branch only.
- **Never** push to `main` or to someone else's branch, and never use `--force` without `-with-lease`.
- Tags:
  - `sub/<YYYY-MM-DD>-<NN>` marks the commit behind each leaderboard upload.
  - `final` marks the commit that produced the final zip.
- Parallel agent sessions on one machine each get their own `git worktree`: `git worktree add ../Grenuke-<topic> -b <member>/<topic> origin/main`.

## 4. Commits

- **Format:** `<type>(<scope>): <imperative summary>`, at most 72 characters.
  - Types: `feat fix perf refactor test docs exp data build ci chore revert`.
  - Example: `perf(block): tile GPU top-k to cut VRAM to 3 GB`.
- The body is optional: what and why, plus numbers (holdout F0.5 before → after, recall, runtime).
- **Forbidden:** `Co-authored-by:` lines, "Generated with …", "Assisted-by", AI tool signatures, or any collaborator or attribution line.
  - The author is the human who owns the branch.
  - This is enforced by `.githooks/commit-msg`, by CI, and by `.claude/settings.json` for Claude Code.
- Never commit:
  - data, `work/`, `data_cache/` or `output/*.tsv`;
  - files over 5 MB;
  - model weights;
  - notebooks with large outputs (clear the outputs first);
  - secrets or tokens.
  - `.githooks/pre-commit` blocks these.

## 5. Pull requests

1. Push your branch and open a PR to `main`. The template asks for what changed, the area, validation numbers and a handover link.
2. **Size:** aim for under ~400 changed lines. Split large work: contracts, then implementation, then tuning.
3. **Review:** at least **one other member** must approve PRs that touch shared files (below) or another owner's area. A PR inside your own area may be self-merged once CI is green, if nobody responds within 30 minutes.
4. **CI must be green.** It checks for co-author lines, large or data files, runs the unit tests, and compiles the package.
5. **Merge method:** **rebase and merge** only; squash and merge commits are disabled. (A GitHub squash merge would add `Co-authored-by` lines.) The branch is deleted automatically after merge.
   - **Branch protection on `main` is active on GitHub:** a PR is required, the CI checks `repo policy` and `unit tests` must pass, history stays linear, and force pushes and deletion are blocked.
6. After a merge, everyone runs `git fetch` and rebases their active branches.

**Shared files** (coordinator review, one dedicated small PR each):
- `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `README.md`
- `docs/ROADMAP.md`, `docs/TEAM.md`, `docs/CONTRACTS.md`
- `code/business_entity_resolution/{requirements.txt,pyproject.toml}`
- `src/ber/{io.py,ids.py,paths.py}`, `src/ber/eval/**`
- `.github/**`, `.githooks/**`, `scripts/**`, `.claude/settings.json`

## 6. Coordination documents (conflict-free by design)

| what | where | naming | written by |
|---|---|---|---|
| what I'm doing now | `docs/status/<member>.md` | fixed name | that member only |
| handover (end of every session, or when passing work on) | `docs/handover/` | `YYYY-MM-DD_HHMM_<member>_<topic>.md` (IST) | the author only |
| decision record (architecture/approach choices) | `docs/decisions/` | `YYYY-MM-DD_HHMM_<topic>.md` | the author, reviewed in a PR |
| leaderboard submission record | `submissions/records/` | `YYYY-MM-DD_subNN.md` | the submissions captain |
| roadmap, milestones and owners | `docs/ROADMAP.md` | fixed | the coordinator (others propose changes in their status file or a PR) |
| plans | `plans/<member>/` | `PLAN.md` (+ `.pdf`) | that member |

`python scripts/new_doc.py {handover|status|decision|submission} ...` creates any of these from the templates with the correct name and IST timestamp.

**Handover rule:** end every working session (human or agent) with a handover and a status update. Hand an area to someone else only through a handover that lists exact commands, artifact locations and next steps.

## 7. Data and artifacts

- Raw data goes in `student_resource/dataset/` (from Unstop), never in git.
- Intermediate artifacts go under `work/<stage>/<tag>/`, git-ignored, using the schemas in `docs/CONTRACTS.md`. Choose a new `<tag>` for each experiment so nothing overwrites a teammate's result.
- To share large artifacts (for example, candidate sets), upload them to the team drive folder under the same relative path and include a `MANIFEST.txt` with sha256 hashes and the git commit and command that produced them. Link it from your handover.
- Outputs go to `output/`. Only files produced by `ber.io.write_matching` / `ber.io.write_candidates` may be submitted.

## 8. Leaderboard submissions (team-wide budget: 5 per day)

- Only the **submissions captain** (`docs/TEAM.md`) uploads.
- To request a slot, post in the team chat with the commit, holdout numbers and what the upload tests.
- Every upload needs:
  1. a validator `PASS`;
  2. a record in `submissions/records/`;
  3. a `sub/…` tag on the exact commit.
- Keep one slot per day in reserve. On the last day, **the final upload must be the model we choose as final.** The private leaderboard may use the final submission.
- Full protocol: `submissions/README.md`.

## 9. Environment

- Python ≥ 3.11 (team default 3.13). Install with `pip install -e code/business_entity_resolution` (add `[dev]` for tests).
- New dependencies go in `requirements.txt` with a pinned version, through a shared-file PR. Mention the license: models in the final pipeline must be **MIT or Apache-2.0 with at most 8B parameters**.
- Use `pathlib` and no hard-coded absolute paths. Personal paths go in environment variables (`BER_DATA_DIR`, `BER_WORK_DIR`) or git-ignored `config.local.*` files.

## 10. Competition compliance (disqualification risks)

- Use **no external data or lookups**: no entity-resolution APIs, government registries, geocoding, web search or internet datasets.
- Hand-written lexicons (abbreviations, state and region names, legal forms) are allowed. Document them in the methodology.
- Model licenses: MIT or Apache-2.0, at most 8B parameters.
- The final zip must regenerate both output files from the raw data using only `code/business_entity_resolution/`.

## 11. Disagreements and escalation

- Technical disagreements: the area owner decides for their area. For anything cross-cutting, the coordinator decides after a timeboxed (15 min) discussion, and it is recorded in `docs/decisions/`.
- Choosing a plan: follow the process in `plans/README.md`.
- If you break `main`: revert first (`git revert` in a PR), then fix. Never rewrite `main`'s history.
