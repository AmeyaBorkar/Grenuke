# Handover: features-v0

- **Author:** bakshi (Codex)
- **When (IST):** 2026-09-25 21:40
- **Branch / PR / last commit:** `bakshi/features-v0` / PR #21 / updated on branch
- **Area and paths touched:** `src/ber/features/{__init__,string,tokens,numbers}.py`, `tests/test_features_v0.py`, this handover and `docs/status/bakshi.md`.

## TL;DR (3 lines max)

C8 stage computes 56 float32 string features and automatically joins 15 coordinator-owned context features. On the team dev kit it wrote all 3,212,547 pairs in 214.4 seconds, under the five-minute target, with 5.89 GiB peak process memory.

## What was done

- Added RapidFuzz batch string similarities, sparse token/IDF comparisons and Numba numeric-set kernels. IDF is fitted on fixed-seed, per-country samples of unlabeled records.
- Added chunked candidate processing, fold and truth labels, C8 Parquet output and provenance. Country is used for unsupervised IDF partitioning and never emitted as a feature.
- Joins Ameya's `context.compute(cands, s1_records)` automatically when available. It computes context once over the *complete* candidate set so rivalry/count features remain exact across string-feature batches. `--set include_context=false` keeps a streaming string-only mode.
- Reuses each distinct name/address text within a batch before tokenization and character hashing. The complete dev run fell from 431 seconds initially to 190–214 seconds with context; all original string feature values remained equal.
- Tested hand-made name, number and address cases, C8 row alignment, truth labels and context integration across two batches.

## Current state

- **Works:** 56 string features plus 15 context features, C8 output, train labels/folds, full dev-kit run, and 100 passing tests.
- **Half-done:** downstream model quality assessment by Sachi; this feature stage does not produce match decisions.
- **Known bugs and caveats:** context mode loads complete candidates and raw S1 records in memory; Ameya should measure full-scale memory on the 31 GB integration machine. The dev runtime is measured on Bakshi's 16 GB laptop. It is not a predictive-quality score.

## Numbers (shared holdout, `ber.eval`; include the command)

| metric | value | command / tag |
|---|---|---|
| holdout macro F0.5 | N/A: feature stage, model not trained on this artifact | — |
| blocking pair recall / oracle F0.5 | N/A: supplied candidates only | — |
| runtime / peak RAM | 3,212,547 dev pairs in 214.4 s (217.4 s monitored wall time); 5.89 GiB peak process RSS | `bakshi-feat-v0`, full context |

## How to reproduce or continue (exact commands)

```powershell
$env:BER_WORK_DIR='C:\Users\baksh\Documents\Codex\2026-09-25\in\work\GrenukeGit2\work'
$env:PYTHONPATH=(Resolve-Path 'code\business_entity_resolution\src').Path
.\.venv\Scripts\python.exe -m ber.pipeline --stage features --split train --tag bakshi-feat-v0 --in norm=bakshi-norm-v0a --in candidates=ameya-block-v0-dev --set idf_docs=20000 --set batch_size=250000
.\.venv\Scripts\python.exe -m pytest code\business_entity_resolution\tests -q -p no:cacheprovider --basetemp C:\Users\baksh\Documents\Codex\2026-09-25\in\work\pytest_features_final
```

The dev candidates come from private GitHub release `devkit-v0`; the manifest verifies their SHA256 as `e074e3e520f5d08a8bf93953aa1c86d2a8b73d6c7a549af2d041acb05496f064`. The required `rapidfuzz`, `scikit-learn` and `numba` packages are pinned in `requirements.txt`.

## Artifacts (local paths / drive links + sha256)

- `work/features/bakshi-feat-v0/train.parquet` SHA256 `45575B8D5A3B7ED6ED8E2E69D1F73B224A238026F44E51A3F80AC4F1305B29C0`; 3,212,547 rows, 75 columns, 372,902 positive labels, git-ignored.

## Next steps (ordered, with suggested owner)

1. Ameya: review/merge PR #21 and rerun C8 on the integration machine for full train and test candidates; monitor context memory.
2. Sachi: evaluate the dev C8 artifact on the shared holdout and decide feature/model changes through the project gates.
3. Bakshi: support integration and address any review findings.

## Blockers, open questions, decisions needed

- The dev kit was obtained from the private release, but the feature artifact is local and git-ignored. No model was trained on it here, so no F0.5 is claimed.
- Normalizer PR #20 was merged before this branch's rebase; its status-file overlap has been resolved.
