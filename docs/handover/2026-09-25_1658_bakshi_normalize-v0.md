# Handover: normalize-v0

- **Author:** bakshi (Codex)
- **When (IST):** 2026-09-25 20:43
- **Branch / PR / last commit:** `bakshi/normalize-v0` / PR pending / commit pending
- **Area and paths touched:** `src/ber/normalize/**`, `tests/test_normalize_v0.py`, one obsolete assertion in `tests/test_pipeline.py`, this handover and `docs/status/bakshi.md`.

## TL;DR (3 lines max)

C3 normalization is implemented and has produced complete train and test Parquet artifacts. The full 40-test suite passes. Feature stage development continues on `bakshi/features-v0`.

## What was done

- Added chunked, parallel normalization with atomic Parquet output and provenance; preserves each input `eid`, `source` and open-set `country`.
- Added name and address parsing, hand-written legal/state/street lexicons, and ASCII Indic transliteration. Emits all C3 v0 fields plus `f_addr_null` and `f_arrondissement`.
- Tested legal forms, domains, hashtags, honorifics, house/unit numbers, reordered US/French address components, null addresses and Indic names.
- Updated the pipeline test's old normalize-stub assertion to the implemented stage result. Coordinator should review this shared test change.

## Current state

- **Works:** full train and test C3 artifacts; 12,527,040 train and 11,702,133 test records, 29 columns each; full test suite 40 passed.
- **Half-done:** none in normalization v0.
- **Known bugs and caveats:** hand-written French region names are handled, but the lexicon does not comprehensively map French departments to regions. Address component order is heuristic. Artifacts were generated before commit, so metadata records `e955810+dirty`.

## Numbers (shared holdout, `ber.eval`; include the command)

| metric | value | command / tag |
|---|---|---|
| holdout macro F0.5 | N/A: normalization stage only | — |
| blocking pair recall / oracle F0.5 | N/A: no candidates in this stage | — |
| runtime / peak RAM | train 484.2 s; test 516.1 s; peak RAM not measured | `bakshi-norm-v0a`, 8 workers |

## How to reproduce or continue (exact commands)

```powershell
$env:BER_DATA_DIR='C:\Users\baksh\Downloads\New folder\6ab10eb3b23ba_student_resource\student_resource\dataset'
$env:PYTHONPATH=(Resolve-Path 'code\business_entity_resolution\src').Path
python -m ber.pipeline --stage records --split train
python -m ber.pipeline --stage records --split test
python -m ber.pipeline --stage normalize --split train --tag bakshi-norm-v0a --n-jobs 8
python -m ber.pipeline --stage normalize --split test --tag bakshi-norm-v0a --n-jobs 8
python -m pytest code\business_entity_resolution\tests -q -p no:cacheprovider --basetemp work\pytest_normalize
```

## Artifacts (local paths / drive links + sha256)

- `work/norm/bakshi-norm-v0a/train.parquet` SHA256 `B82AC6BBEC0E8BEFCEFEA7EB086628EB2D5452EA82CDD1DBA79770A3F4835B51`
- `work/norm/bakshi-norm-v0a/test.parquet` SHA256 `F29C798D0718D3B285A4B1F29813974D00BE65483BB58703F2292D100D7F9EC7`
- Both artifacts are local and git-ignored; coordinate transfer to Ameya's integration machine.

## Next steps (ordered, with suggested owner)

1. Bakshi: open the normalization PR and complete C8 string features on `bakshi/features-v0`.
2. Ameya: review and merge the PR, then run normalization on the integration machine or obtain the two local artifacts.
3. Bakshi with Ameya's dev candidates: benchmark real-pair C8 output and share it with Sachi.

## Blockers, open questions, decisions needed

- Ameya's candidate artifact `ameya-block-v0-dev` is needed for the agreed real-pair C8 benchmark and is not in the local workspace yet.
- No matching submission was produced by this stage, so the submission validator does not apply.
