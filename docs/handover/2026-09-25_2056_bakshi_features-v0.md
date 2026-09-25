# Handover: features-v0

- **Author:** bakshi (Codex)
- **When (IST):** 2026-09-25 21:00
- **Branch / PR / last commit:** `bakshi/features-v0` / PR pending / commit pending
- **Area and paths touched:** `src/ber/features/{__init__,string,tokens,numbers}.py`, `tests/test_features_v0.py`, this handover and `docs/status/bakshi.md`.

## TL;DR (3 lines max)

C8 stage now computes 56 float32 name, extra-word, number and address features in candidate order, plus optional coordinator-owned context features. A 100,000-positive-pair real-record probe finished in 73 seconds; this is a throughput smoke test, not a match-quality score.

## What was done

- Added RapidFuzz batch string similarities, sparse token/IDF comparisons and Numba numeric-set kernels. IDF is fitted on fixed-seed, per-country samples of unlabeled records.
- Added chunked candidate processing, fold and truth labels, C8 Parquet output and provenance. Country is used for unsupervised IDF partitioning and never emitted as a feature.
- Added optional `--set include_context=true` integration with Ameya's `context.compute(cands, s1_records)` API. It computes context once over the *complete* candidate set so rivalry/count features remain exact across string-feature batches.
- Tested hand-made name, number and address cases, C8 row alignment, truth labels and context integration across two batches.

## Current state

- **Works:** 56 string features, C8 output, train labels and folds, optional exact context integration; 97 tests pass against current `origin/main`.
- **Half-done:** benchmark on Ameya's real dev candidates, including nonmatches, pending artifact access.
- **Known bugs and caveats:** `include_context=true` loads all candidates and raw S1 records in memory because the coordinator API expects the full candidate set; use the integration machine for large runs. String-only mode is streaming and the default. The 100k probe contained only known positives, so no predictive metric can be inferred.

## Numbers (shared holdout, `ber.eval`; include the command)

| metric | value | command / tag |
|---|---|---|
| holdout macro F0.5 | N/A: feature stage, model not trained on this artifact | — |
| blocking pair recall / oracle F0.5 | N/A: supplied candidates only | — |
| runtime / peak RAM | 100,000 positive pairs in 73.1 s (71.4 s stage); peak RAM not measured | `bakshi-feat-probe`, string-only |

## How to reproduce or continue (exact commands)

```powershell
$env:BER_WORK_DIR='C:\Users\baksh\Documents\Codex\2026-09-25\in\work\GrenukeGit2\work'
$env:PYTHONPATH=(Resolve-Path 'code\business_entity_resolution\src').Path
.\.venv\Scripts\python.exe -m ber.pipeline --stage features --split train --tag bakshi-feat-probe --in norm=bakshi-norm-v0a --in candidates=bakshi-feature-probe --set idf_docs=10000 --set batch_size=100000
.\.venv\Scripts\python.exe -m pytest code\business_entity_resolution\tests -q -p no:cacheprovider --basetemp C:\Users\baksh\Documents\Codex\2026-09-25\in\work\pytest_features_final
```

For Ameya's C4 candidates, replace the candidate tag and optionally add `--set include_context=true`. The required `rapidfuzz`, `scikit-learn` and `numba` packages are pinned in `requirements.txt`.

## Artifacts (local paths / drive links + sha256)

- `work/features/bakshi-feat-probe/train.parquet` SHA256 `317DF460720E50729852416AEC417FD2D6D89CF5A0813BC3919C883A03EC60D1`; 100,000 rows, 60 columns, all `y=1`, git-ignored.

## Next steps (ordered, with suggested owner)

1. Bakshi: run a dev C4 candidate artifact with positives and negatives; report throughput and feature distributions.
2. Ameya: review PR and decide whether to include context at full scale or precompute it with a streaming API.
3. Sachi: evaluate C8 features on the shared holdout after candidate artifact is available.

## Blockers, open questions, decisions needed

- Ameya's `ameya-block-v0-dev` candidates were not available locally; the positive-only probe cannot validate ranking or F0.5.
- Normalizer PR #20 was merged before this branch's rebase; its status-file overlap has been resolved.
