# Handover: final-plan

- **Author:** ameya (human; the agent was Claude Code)
- **When (IST):** 2026-09-25 14:14
- **Branch / PR / last commit:** `ameya/final-plan` / see the PR "docs(plans): adopt final plan, contracts v1 and roadmap" / the head of the branch
- **Area and paths touched:**
  - shared docs, in a dedicated PR requested by the coordinator: `plans/FINAL_PLAN.md` (new), `plans/DECISION.md`, `plans/README.md`, `docs/ROADMAP.md`, `docs/TEAM.md`, `docs/CONTRACTS.md`, `CHANGELOG.md` (new), `AGENTS.md`, `README.md`, `CONTRIBUTING.md`, `.github/CODEOWNERS`, `.github/pull_request_template.md`;
  - my own area: `experiments/ameya/plan-checks/`.

## TL;DR (3 lines max)

The plan is decided: `plans/FINAL_PLAN.md` combines Plan A as the base with Plan B's gates and several grafts, adjusted by data checks run today. The contracts are v1, and they add folds, normalized columns, features, matches and gate records. The roadmap lists owners and "done when" criteria for Submission 1 tonight. Next up is the pipeline skeleton PR (`ameya/dev-skeleton`), then Phase 1.

## What was done

- **Compared Plans A and B, and checked every disputed claim against the full data.** The scripts are in `experiments/ameya/plan-checks/`; results are below.
- **Wrote `plans/FINAL_PLAN.md` v1.0:**
  - an evidence ledger with measured / fact / hypothesis tags;
  - the stage design, and gates G1–G13;
  - validation, France, the compute budget, milestones M0–M9 and owners;
  - risks, what we don't build, and where each part came from.
- **Filled in `plans/DECISION.md`:** the base, the grafts, rejected ideas with evidence, the coordinator's rubric scores and the owners.
- **`docs/CONTRACTS.md` v1:**
  - C0: tags and artifact paths;
  - C2: training folds 5–19, `oof_group`, fold 0 as the dev subset, and what may never be fitted on the holdout;
  - C3: normalized v0 columns;
  - C4: view metadata;
  - C5: stage-1 OOF scores;
  - C7: report keys;
  - C8: features (new);
  - C9: matches (new);
  - C10: gate records (new).
- **`docs/ROADMAP.md`** rebuilt: Phase 0–4 tasks with owners, targets and "done when" criteria, a gates table and the submission plan.
- **`docs/TEAM.md` and `CODEOWNERS`:**
  - Sachi is @ssdhoka06.
  - Member 3 is @trustdemons05. Their name and branch prefix are still to be filled in.
  - The proposed owners are listed.
- **`CHANGELOG.md`** (new) records the history so far and sets the policy: the coordinator and captain maintain it; feature PRs add a `Changelog:` line to the PR description.
- **Pointers updated in `AGENTS.md`:**
  - the reading order now includes the plan;
  - a MUST that components beyond v0 need a gate record;
  - the shared-file list, and the table of where things are.
- **Also updated:** `README.md`, `CONTRIBUTING.md` (gate principle, shared files, changelog row) and the PR template (task/gate and changelog fields).

## Current state

- **Works:** documentation only; no code changed in this PR.
- **Half-done:**
  - Member 3's name and branch prefix in `docs/TEAM.md`;
  - teammates' rubric scores in `plans/DECISION.md`;
  - `docs/DEVELOPMENT.md` and the `ber.artifacts`, `ber.config` and `ber.eval.gates` modules. These come in the skeleton PR, and the docs here already reference them.
- **Known caveats:**
  - Owners are proposed until confirmed in review.
  - The 25 Sep numbers use crude normalization, so re-measure them with the real pipeline before quoting them in the methodology.

## Numbers (25 Sep data checks, full data or large samples)

| check | value | script |
|---|---|---|
| S2/S3 per S1, train → test | 4.68 → 5.75 (India 5.82, US 5.76, France 5.53) | `plan_checks.py` §1 |
| S1 sharing an exact core name with another S1 | US 46.2%, India 53.6% | `plan_checks.py` §2 |
| S1 sharing an exact normalized address (max group) / sharing both | US 5.62%, India 4.84% (14) / 6 | `plan_checks.py` §2 |
| true pairs: weak name / weak address / both | 15.9% / 4.7% / 0.09% | `plan_checks.py` §3 |
| true pairs: S2/S3 address empty / ≤3 tokens / weak address with >3 tokens | 4.4% / 5.2% / **0.27%** | `plan_checks.py` §3 |
| true pairs: first number equal / number sets equal / any overlap | 83.3% / 73.1% / 94.6% | `plan_checks.py` §3 |
| true pairs: exactly equal normalized address | 8.5% | `plan_checks.py` §3 |
| postcode-like numbers: India 6-digit / US trailing 5-digit / France 5-digit | 0.02% / 0.33% / 0.4–0.5% | `plan_checks.py` §3, `density_check.py` |
| orphans (share of S2/S3) / with an exact S1 core-name match | 26.0% / 22.0% | `plan_checks.py` §4 |
| look-alike orphans vs true pairs: first number equal | 12.4% vs 84.8% | `plan_checks.py` §5 |
| look-alike orphans vs true pairs: ≥1 extra name word | 76.5% vs 23.3% | `plan_checks.py` §5 |
| orphans with no rival S1 within 80% of the best score (crude) | 36.8% | `plan_checks.py` §5 |
| India, close on name and address: train / test / if the extra records were owner-less | 31.8% / 31.7% / ~25.6% | `density_check.py`, `ownerless_check.py` |
| India, nothing close: train / test / if the extra records were owner-less | 44.4% / 43.1% / ~52.8% | same |

- **Extra name words in look-alike orphans:** group, holdings, industries, public, enterprises, exports, infratech, ventures, overseas.
- **Extra name words in true pairs:** center, services, dba, shri/sri/smt, dr/mr, formerly, incorporated.

## How to reproduce or continue (exact commands)

```
pip install -e code/business_entity_resolution
cd experiments/ameya/plan-checks
python make_cache.py          # data_cache/*.parquet from the TSVs (~1 min)
python plan_checks.py         # ~4 min
python density_check.py       # ~4 min
python ownerless_check.py     # ~1.5 min
```

## Artifacts (local paths / drive links + sha256)

- None shared. `data_cache/` is local and can be rebuilt with `make_cache.py`.

## Next steps (ordered, with suggested owner)

1. Teammates review this PR, confirm or adjust owners, and add their rubric scores (Sachi, Member 3). A human merges it with rebase-merge.
2. Merge the skeleton PR (`ameya/dev-skeleton`): the `ber.pipeline` CLI, records stage, artifact metadata, OOF groups, gate bootstrap and `docs/DEVELOPMENT.md` (Ameya).
3. Phase 1 of `docs/ROADMAP.md`:
   - 1.1 records (A);
   - 1.2 normalize v0 (M3);
   - 1.3a/b block v0 (A);
   - 1.4 features v0 (M3);
   - 1.5–1.6 model and decide v0 (S);
   - 1.7–1.8 outputs and Submission 1 (A).

## Blockers, open questions, decisions needed

- Member 3: their name and branch prefix, and confirmation of ownership of normalization and features.
- Sachi: confirmation of ownership of model, decision and gates.
- The team drive folder for large artifacts: add the link to `docs/TEAM.md` (CONTRIBUTING §7).
