# business_entity_resolution: reproducible pipeline

This folder is the **deliverable code package**. It is copied as-is into `<team>_submission.zip` under `code/business_entity_resolution/`.
Anyone must be able to regenerate `output/matching_results.tsv` and `output/candidate_pairs.tsv` from the raw data using only this folder.

> **Status (final, Oct 2026):**
> - This package holds the shared pipeline: the CLI, records, normalization, blocking (multi-view retrieval, Indic transliteration, domain/OCR repairs, French address normalisation), context features, the writer, evaluation, folds and gates.
> - The final model chain (pair features, XGBoost stages 0–3, cross-encoder features, the expected-F0.5 decision and the French rules) lives in `experiments/ameya/model-v1/`. Its exact commands are in `experiments/ameya/model-v1/RECIPE.md`.
> - The submitted package's layout and reproduce scripts are in `docs/package/`. The developer guide is `docs/DEVELOPMENT.md`.
> - The organisers' validator and dataset aren't included; see the repository README.

## Environment

```
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Data layout

By default the pipeline reads `student_resource/dataset/{train,test}/*.tsv` from the repo root.
Override the locations with environment variables:

| variable | meaning | default |
|---|---|---|
| `BER_DATA_DIR` | folder that contains `train/` and `test/` | `<repo>/student_resource/dataset` |
| `BER_WORK_DIR` | intermediate artifacts (`work/<kind>/<tag>/<split>.parquet`) | `<repo>/work` |
| `BER_OUTPUT_DIR` | final TSVs | `<repo>/output` |

## Reproduce

```
python -m ber.pipeline --stage all --split train --tag <tag>     # records → normalize → block → features → train → predict → decide → evaluate
python -m ber.pipeline --stage all --split test  --tag <tag>     # records → normalize → block → features → predict → decide → write → evaluate
python student_resource/utils/validate_submission.py --matching output/matching_results.tsv --candidate output/candidate_pairs.tsv --test-dir student_resource/dataset/test
```

| stage | time (measured) |
|---|---|
| `records` train / test | ~50 s / ~25 s |
| `evaluate` (holdout) | ~10 s |
| other stages | filled in as they land |

## Package map

| module | purpose |
|---|---|
| `ber.pipeline` | the CLI: stage order, `--tag`, `--in`, `--set`, `--folds` |
| `ber.config` | `RunConfig`, passed to every stage |
| `ber.records` | stage `records`: cached raw records, truth pairs, S1 order |
| `ber.normalize` | stage `normalize` (C3), a stub |
| `ber.block` | stage `block` (C4), a stub |
| `ber.features` | stage `features` (C8), a stub |
| `ber.model` | stages `train`, `predict`, `decide` (C5, C9), stubs |
| `ber.outputs` | stage `write`: submission TSVs with invariant checks (C6) |
| `ber.artifacts` | Parquet and report I/O with provenance (commit, command, inputs) |
| `ber.io` | safe TSV readers (tab separator, quoting disabled) and exact-format output writers |
| `ber.ids` | integer entity keys `eid = source * 1e9 + number` (lossless) |
| `ber.paths` | default paths, environment overrides, artifact paths |
| `ber.eval.metric` | official macro F0.5, blocking pair recall, oracle ceiling |
| `ber.eval.splits` | shared holdout (folds 0–4), training folds 5–19, OOF groups, dev fold |
| `ber.eval.evaluate` | stage `evaluate`: holdout report per country and test diagnostics (C7) |
| `ber.eval.gates` | paired bootstrap and a gate CLI (C10) |

Tests: `python -m pytest tests -q`
