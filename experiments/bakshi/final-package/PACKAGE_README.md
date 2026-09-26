# Business Entity Resolution: Team Grenuke

Reproduces `output/matching_results.tsv` and `output/candidate_pairs.tsv` from the raw challenge TSVs.
Method and evidence: `Documentation_template.md` (zip root). Command-level source of truth: `reproduce.sh`
and `src/model_v1/RECIPE.md`.

**Submitted model: `v7nst`** (package tag `2026-09-27-v7nst-s3-ops3a-c2`).

## Layout

| path | what |
|---|---|
| `output/` | the submitted TSVs, verbatim. `reproduce.sh` writes to `$BER_OUTPUT_DIR`, never over these. |
| `src/ber/` | team package, one CLI: `python -m ber.pipeline --stage <stage> --split <train\|test> --tag <tag>`. Stages: records, blocking (multi-view retrieval, Indic transliteration, domain/OCR repairs, French address normalisation), context features, write (organiser TSV format), evaluate. |
| `src/model_v1/` | the model chain: pair features (`feats*.py`, `lo_mix.py`), stages 0+1 (`s1.py`), cross-encoders (`ce.py`, `ce_box.py`, `zmean_ce.py`, `ce_import.py`), stage 2 and calibration (`s2.py`, `cluster.py`), stage 3 (`stage3.py`), decision (`decide.py`), final candidate set (`cands_final.py`), France rules (`post_ops.py`), acronym join (`acr_join.py`), self-training labels (`pseudo_labels.py`), `RECIPE.md` |
| `reproduce.sh` | the full run for the submitted model, in order |
| `src/model_v1/audit_matching.py` | strict output audit (see "Checking the result") |
| `requirements.txt` | pinned versions |
| `tests/` | unit tests (`pytest -q`) |
| `MANIFEST.sha256` | sha256 of every file in this archive |

## Setup

```bash
python3.13 -m venv .venv && source .venv/bin/activate     # 3.11+ required; 3.13 is what the pins were read from
pip install -r code/business_entity_resolution/requirements.txt
pip install -e code/business_entity_resolution
pytest -q code/business_entity_resolution/tests
```

Data: the organiser folder `student_resource/dataset/{train,test}/*.tsv`. Set `BER_DATA_DIR` if it lives elsewhere.
Intermediate artifacts go to `work/` (`BER_WORK_DIR`), fresh outputs to `output/` (`BER_OUTPUT_DIR` — point this
somewhere else if you want to keep the submitted files untouched).

## Run

From the unzipped package root:

```bash
MODEL_DIR="$PWD/code/business_entity_resolution/src/model_v1" \
  BER_OUTPUT_DIR="$PWD/output_rerun" \
  bash code/business_entity_resolution/reproduce.sh
```

`v7nst` is **self-trained**: its stage 2 additionally fits the French test rows against pseudo-labels taken from an
earlier finished chain (`v7ce3`). A clean run therefore builds the teacher before the student — `reproduce.sh`
does this in one pass, in this order:

| step | what | time on the reference machine |
|---|---|---|
| 0 | records + Indic dictionary | ~2 min |
| 1 | blocking v3 (train + test) | ~25 min |
| 2 | pair features (`ameya-fx5`) | ~1 h |
| 3 | stage 0 + 1 on all of train | ~30 min, peak ~18 GB RAM |
| 4 | cross-encoder, e5-small | ~40 min (GPU) |
| 5 | cross-encoders e5-large ×2 and e5-base, then the z-mean | ~2.5 h on one H100 |
| 6 | **teacher** `v7ce3`: stage 2, decision, candidate set, stage 3, rules, acronym join | ~45 min, peak ~19 GB |
| 7 | pseudo-labels from the teacher's final decisions | ~2 min |
| 8 | **student** `v7nst`: stage 2 with `--pseudo`, decision, stage 3, decision | ~40 min, peak ~19 GB |
| 9–12 | France rules v3, acronym join, write, validate, audit, hashes | ~10 min |

Reference machine: RTX 5070 Ti 12 GB, 24 cores, 31 GB RAM, plus a rented H100 80 GB for step 5.
`ce.py`/`ce_box.py` need a CUDA GPU; the XGBoost stages fall back to CPU (slower). **Run nothing else
memory-heavy beside stages 1, 2 and 3** — and note there are two stage-2 fits here (teacher and student), which
must run serially, not side by side. e5-large at `--batch 128 --max-len 96` does not fit in 12 GB; on a smaller
card use `--batch 32`.

## Checking the result

```bash
# the organiser's validator
python student_resource/utils/validate_submission.py \
  --matching output/matching_results.tsv --candidate output/candidate_pairs.tsv \
  --test-dir "$BER_DATA_DIR/test" --check-ids
# then the strict audit
python code/business_entity_resolution/src/model_v1/audit_matching.py \
  --matching output/matching_results.tsv --candidate output/candidate_pairs.tsv \
  --test-dir "$BER_DATA_DIR/test"
```

**Why both.** `validate_submission.py` prints `PASS` even when `candidate_pairs.tsv` is missing entirely, and even
when matched pairs fall outside it — those two are *warnings*, not failures. It also never checks owner
uniqueness or country consistency. `audit_matching.py` checks all of that and exits non-zero. Read the warnings;
do not accept the exit code alone.

**sha256 of the submitted files** (both independently verified against these bytes):

| file | bytes | sha256 |
|---|---|---|
| `output/matching_results.tsv` | 97,909,982 | `659f5169cabbb2a3de2cb8580b614bbff718ea62d5b1fb4497243b50fcc34533` |
| `output/candidate_pairs.tsv` | | `510a33ea18a7ab4cd2ec5ad4e8ad113bbc4fd4f46818941c00f29852f3e258aa` |

Independently measured properties of the submitted matching file:
1,732,544 rows (exactly one per test S1), 5,856,096 pairs, 100,137 empty rows, 3.3801 matches per S1,
0 records claimed by more than one S1, 0 cross-country pairs, every target ID present in `test_source2/3.tsv`.
Per country: France 259,452 S1 / 871,242 pairs; India 809,986 / 2,735,918; US 663,106 / 2,248,936.

**A rerun may not reproduce these hashes.** XGBoost with fixed seeds is deterministic on the same machine, but the
cross-encoders are not bit-reproducible across GPUs (TF32, cuDNN kernel choice, non-deterministic reductions), so a
few pairs can move. The reference check is then the holdout macro F0.5 in `work/reports/ameya-model-v7nst-s3.json`
(**0.991194**; US 0.991005, India 0.991472), not the file hash. The submitted bytes in `output/` are shipped
verbatim and are never regenerated by `reproduce.sh`.

## Compliance

- **Only the provided data.** No external lookups, APIs, geocoding, or internet datasets were used to resolve
  entities.
- **Hand-written lexicons**, all documented in the code: legal forms, street types, US/India states, French
  departments → regions, generator list words, the OCR digit map, ordinal words.
- **Models, all within the ≤ 8B and MIT/Apache-2.0 rule:**

  | model | role in the submitted chain | parameters | license |
  |---|---|---|---|
  | XGBoost | stages 0–3 | — | Apache-2.0 |
  | `intfloat/multilingual-e5-small` | stage-2 cross-encoder feature `ce` | 118M | MIT |
  | `intfloat/multilingual-e5-large` | two fine-tunes (1 epoch seed 26; 2 epochs seed 7), z-averaged into feature `cem2` | 560M | MIT |
  | `intfloat/multilingual-e5-base` | **teacher only** — feature `ceb` of `v7ce3`, whose decisions become the student's pseudo-labels. Required to reproduce, not present in the student's feature set. | 278M | MIT |

  No other pretrained model is part of this chain. `BAAI/bge-reranker-v2-m3` and `Qwen2.5-1.5B` were evaluated
  during development and are **not** in the submitted model.
- Seeds are fixed in every script; each artifact records the git commit and the command that produced it.
