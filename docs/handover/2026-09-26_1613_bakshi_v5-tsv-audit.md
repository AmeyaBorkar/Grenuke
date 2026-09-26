# Handover: v5-tsv-audit

- **Author:** Bakshi
- **When (IST):** 2026-09-26 16:13
- **Branch / PR:** `bakshi/v7-france` / #34
- **Area and paths:** `experiments/bakshi/v7/{audit_tsv,probe_exact,test_tsv_probe}.py`, experiment README, this handover and Bakshi status.

## TL;DR

The supplied v5 TSV is the exact recorded France-rules-v2 package and a valid baseline. Imported and audited all test predictions. Two independent score-free rescue experiments showed zero dev gain and counterexamples in test; neither is enabled. No v7 TSV was created or uploaded.

## What was done

- Checked the v5 SHA256 against the repository package record; verified all IDs, S1 coverage, pair uniqueness, country agreement and ownership.
- Compared v5 against v3/v2 without changing source files.
- Profiled all 865,630 France predictions for address conflicts and composed edits.
- Retrieved unique exact full-name/address pairs from raw data and unique complete-name/parsed street/city/house/unit pairs from the existing normalized cache, independently of model candidate files.
- Evaluated both proposals on the v3 dev holdout and inspected full raw numerical and existing-owner evidence for test residuals.

## Current state

- **Works:** TSV import, comparisons, full France audit, two rescue diagnostics, integrity checks and tests.
- **Half-done:** a measured v7 gain and final submission.
- **Known caveats:** v3 scores are not v5/v6; dev ownership is on a sliced graph. Test labels are absent. Exact raw text uniqueness can fail to reflect semantic S1 duplicates. Parsed first house numbers can discard later numeric parts. No new rule is enabled.

## Numbers

| check | result |
|---|---|
| v5 rows / pairs | 1,732,544 / 5,835,593 |
| valid target IDs, S1 coverage, unique pairs, same country | pass |
| conflicting owners | 0 |
| official matching validator | PASS; candidate inclusion unavailable because candidate file absent |
| France pairs / entities | 865,630 / 259,452 |
| France address diagnostic flags | 11,774; not labels |
| France composed-edit predictions | 18 (13 swap_list, 5 drop_multi_list) |
| v5 vs v3 France pairs | 8,663 v5-only, 61,242 v3-only; 59,462 changed entities |
| exact full-field rescue | 0 train-dev residuals; 2 France transfers in test, both ambiguous against compatible existing owners |
| normalized street/city rescue | 0 train-dev residuals; 12 test residuals, 7 numeric-sequence mismatches and 4 compatible existing owners |
| v3 sample baseline / both proposals | 0.9885633928 / unchanged |
| paired holdout delta, both proposals | 0; CI [0, 0]; reject |
| full-v5/v6 gain | not measured |

The full suite includes 129 tests. Exact commands and the limitations are in the experiment README. Runtime was several minutes across diagnostics; peak RAM was not instrumented.

## How to reproduce or continue

See `experiments/bakshi/v7/README.md`. Set `PYTHONPATH` to this worktree source and `BER_WORK_DIR` to the existing cache. `audit_tsv.py --base PATH_TO_V5_TSV --profiles` does not require model scores. `probe_exact.py --split train --scores PATH_TO_DEV_V3_SCORES` evaluates a diagnostic proposal, while its test mode accepts the imported pair cache.

## Artifacts

- Original baseline: `C:/Users/baksh/Downloads/New folder/matching_resultsV5all.tsv`.
- SHA256: `76fe7eff4bb37e9eab392b25d4cb0e563a91f0953131bc9b908909ca44fa3d4b`.
- Local audit: `../GrenukeGit2/work/v7/bakshi-tsv-v5-audit/` (base pairs, France profiles, summary).
- Rescue reports and candidates: `../GrenukeGit2/work/v7/bakshi-exact-rescue-v7/` and `bakshi-street-rescue-v7/`.
- User-facing report: workspace `outputs/v5_submission_audit.md`.
- None of the cached data is committed.

## Next steps

1. Bakshi: retain the verified v5 baseline; do not union older submissions or apply these rejected proposals.
2. Bakshi: when the user's v6 run finishes, import the score-bearing outputs and candidate cache for analysis of actual residual decisions and retrieval failures.
3. Bakshi: validate a new targeted component on the full shared holdout before building the improved v7 TSV; a France-only score requires a human leaderboard probe.

## Blockers and decisions

The user says v6 is still running. V5 TSV enables prediction audits and source-only probes now, but lacks probabilities and rejected candidates required for model-level changes. These experiments do not support a material rank gain. No upload, merge or final-submission selection was performed.
