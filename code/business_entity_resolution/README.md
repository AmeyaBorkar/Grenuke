# business_entity_resolution: reproducible pipeline

This folder is the **deliverable code package**. It is copied as-is into `<team>_submission.zip` under `code/business_entity_resolution/`.
Anyone must be able to regenerate `output/matching_results.tsv` and `output/candidate_pairs.tsv` from the raw data using only this folder.

> Status: shared foundation only (I/O, IDs, metric, holdout). The pipeline stages are added after the plan decision (`plans/DECISION.md`).
> Exact end-to-end commands and run times are filled in during Phase 4 (`docs/ROADMAP.md`).

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
| `BER_WORK_DIR` | intermediate artifacts | `<repo>/work` |
| `BER_OUTPUT_DIR` | final TSVs | `<repo>/output` |

## Reproduce (to be completed)

```
python -m ber.pipeline --stage all          # data → normalize → blocking → matching → output
python student_resource/utils/validate_submission.py --matching output/matching_results.tsv --candidate output/candidate_pairs.tsv --test-dir student_resource/dataset/test
```

## Package map

| module | purpose |
|---|---|
| `ber.io` | safe TSV readers (tab separator, quoting disabled) and exact-format output writers |
| `ber.ids` | integer entity keys `eid = source * 1e9 + number` (lossless) |
| `ber.paths` | default paths plus environment overrides |
| `ber.eval.metric` | official macro F0.5, blocking pair recall, oracle ceiling |
| `ber.eval.splits` | shared deterministic holdout (25% of train S1) |

Tests: `python -m pytest tests -q`
