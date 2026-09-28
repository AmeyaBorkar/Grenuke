# Business Entity Resolution: Team Grenuke

Reproduces `output/matching_results.tsv` and `output/candidate_pairs.tsv` from the raw challenge TSVs.
Method and evidence: `Documentation_template.md` (zip root).

**Submitted model: Composite B** (public leaderboard **0.990879**, the team's best):
- **US/India** from `g1w`: the v7sq pipeline with the Qwen2.5-7B cross-encoder `q7st` counted twice in the stage-2 mix;
- **France** from `mixmdp`: round-2 guarded self-training, the look-alike drop and the French expected-F0.5 decision;
- minus every confident prediction (stage-1 p1 > 0.99, never read by a cross-encoder) that `q7st` scores below logit −6.

| file | sha256 |
|---|---|
| `output/matching_results.tsv` | `df4bccd785b3fa785b7edcf0532288bcddc0010e2e31ce6f358064529ecb62e8` |
| `output/candidate_pairs.tsv` | `58c824a3f61c184fe7da1a448a4ac94284f288feff9c351abfe16a3dfc0520e5` |

These are the uploaded bytes, shipped verbatim; the run below never writes over them.

## Layout

| path | what |
|---|---|
| `output/` | the submitted TSVs, verbatim |
| `code/business_entity_resolution/reproduce.sh` | entry point. `VARIANT=compositeB` (the default) runs `src/box/compositeB.sh`; the other variants run one chain |
| `src/ber/` | the team package, one CLI: `python -m ber.pipeline --stage <stage> --split <train\|test> --tag <tag>`. Stages: records, blocking (multi-view retrieval, Indic transliteration, domain/OCR repairs, French address normalisation), context features, write (organiser TSV format), evaluate |
| `src/model_v1/` | the model chain: pair features (`feats*.py`, `lo_mix.py`), stages 0+1 (`s1.py`), cross-encoders (`ce.py`, `ce_box.py`, `ce_llm_st.py`, `ce_llm.py`, `zmean_ce.py`, `ce_import.py`), stage 2 (`s2.py`, `cluster.py`), stage 3 (`stage3.py`), decision (`decide.py`), candidate set (`cands_final.py`), France rules (`post_ops.py`), acronym join (`acr_join.py`), self-training labels (`pseudo_labels.py`), stacked rules (`stack/`), France block (`pipeline/`) |
| `src/box/` | Composite B's driver (`compositeB.sh`); the 7B cross-encoder (`llm_group.py` one out-of-fold group per GPU, `llm_merge.py`); the 7B re-check (`rescore_export.py`, `score_pairs.py`, `analysis/export_usin.py`, `rescore_eval.py`); the per-country composition (`compose_tsv.py`); `analysis/` holds the scripts behind the documentation's numbers |
| `src/model_v1/audit_matching.py` | strict output audit (see "Checking the result") |
| `requirements.txt` | pinned versions, with the machine each pin comes from |
| `tests/` | unit tests (`pytest -q`) |
| `MANIFEST.sha256` | sha256 of every file in this archive |

## Setup

```bash
python3.13 -m venv .venv && source .venv/bin/activate   # Python >= 3.11
pip install torch==2.11.0 --index-url https://download.pytorch.org/whl/cu128   # cu126 below NVIDIA driver 570
pip install -r code/business_entity_resolution/requirements.txt
pip install -e code/business_entity_resolution
pytest -q code/business_entity_resolution/tests
```

Data: the organiser folder `student_resource/dataset/{train,test}/*.tsv` (set `BER_DATA_DIR` if it lives elsewhere).
Intermediate artifacts go to `work/` (`BER_WORK_DIR`).

## Hardware

- **CPU stages** (records, blocking, features, XGBoost stages 0–3, rules): 24+ cores, 32 GB RAM. Stages 1–3 peak at 18–19 GB, so run them one at a time on a 32 GB machine.
- **Cross-encoders:** a CUDA GPU.
  - e5-large, bge and Qwen2.5-1.5B ran on one H100 80 GB.
  - **Qwen2.5-7B (`q7st`) needs 80 GB cards.** With 3× H100/A100 80 GB (`Q7_GPUS="0 1 2"`), the three out-of-fold groups train in parallel (~2 h). On one card they run one after another (~6 h).
- A smaller card can dry-run the chain with `Q7_MODEL=<a small causal LM>`. The output is then *not* Composite B.

## Run

From the unzipped package root:

```bash
MODEL_DIR="$PWD/code/business_entity_resolution/src/model_v1" \
  BER_OUTPUT_DIR="$PWD/output_rerun" \
  VARIANT=compositeB \
  bash code/business_entity_resolution/reproduce.sh
```

Every step skips work that already exists, so a rerun after an interruption resumes. Options (environment): `Q7_MODEL`, `Q7_GPUS`, `SCORE_BATCH`, `FR_DIR`, `CHECK_7B=1`. See the header of `src/box/compositeB.sh`.

**What it runs.** Times are from the team's runs; the checks are what a correct run should show.

| # | step | time | check |
|---|---|---|---|
| 1 | `VARIANT=v7sq STACK=1 reproduce.sh`: records, blocking v3, fx5 features, stage 0+1, e5-small, band export, the e5-large / e5-base teacher `v7ce3`, its French pseudo-labels, the four v7sq cross-encoders (e5l, qst, e5ls, bge) on this package's band, stage 2 (`--pseudo`), stage 3, rules, acronym join, stacked rules (`-dpc`) | blocking 11 + 15 min; features 52 min; stage 1 12 min; e5-small 21 min (RTX 4090); e5-large ×2, e5-base, bge, Qwen2.5-1.5B ~5 h on one H100; each stage-2 fit ~20 min; rules ~10 min | blocking **66,429,057** train / **58,437,794** test pairs; band 1,568,554 / 1,490,930 pairs; v7sq holdout macro F0.5 (`work/reports/ameya-model-v7sq-s3.json`) **≈0.99125** (0.991246 original, 0.991261 on the 27 Sep rebuild) |
| 2 | `pseudo_labels.py` on v7sq-dpc → `pseudo_fr_v7sq.parquet` | ~2 min | 385,274 French band pairs: 74,325 positive, 273,160 negative, 37,789 unlabelled |
| 3 | `q7st`: `llm_group.py` ×3 (Qwen2.5-7B @ `d149729398750b98c0af14eb82c78cfe92750796`, LoRA r 16), `llm_merge.py` | ~2 h on 3× H100 (training 9.7–9.9k steps + scoring ~2.0M pairs per group) | band AUC holdout **≈0.944**, OOF ≈0.940 (0.9436 / 0.9396 on 27 Sep) |
| 4 | v7sq-dpc → `-dpcsf` (look-alike word-swap drop, then the France expected-F0.5 decision) | ~3 min | US/India unchanged |
| 5 | `g1w`: z-mean of e5l, qst, e5ls, bge, q7st, q7st → stage 2 → stage 3 → decision → rules → acronym join → stacked rules | ~40 min | holdout macro F0.5 (`ameya-model-g1w-s3.json`) **≈0.99132** (0.991323; US 0.991114, India 0.991635 on 27 Sep) |
| 6 | 7B re-check: `rescore_export.py`, `analysis/export_usin.py`, `score_pairs.py` (adapter_0) on the confident final pairs | France 2 × 15 min, US/India 4 × 46 min on H100 | 870,019 French and ~4.74M US/India pairs scored. With `CHECK_7B=1`: drop at q7 < −6 gives **+0.000033** holdout macro F0.5, positive in both halves |
| 7 | France block (`src/model_v1/pipeline/france_mixmdp.sh`) → `$FR_DIR` | <!-- TODO(ameya): France block time --> | <!-- TODO(ameya): France block checks --> |
| 8 | `compose_tsv.py` (labelled countries from g1w, France from the France block, minus q7 < −6 and p1 > 0.99), validator, strict audit, sha256 | ~5 min | ~1,150 drops (about 840 French, 310 US/India); 1,732,544 rows; ~5.85M pairs; audit PASS |

## Checking the result

```bash
python student_resource/utils/validate_submission.py \
  --matching output_rerun/matching_results.tsv --candidate output_rerun/candidate_pairs.tsv \
  --test-dir "$BER_DATA_DIR/test"
python code/business_entity_resolution/src/model_v1/audit_matching.py \
  --matching output_rerun/matching_results.tsv --candidate output_rerun/candidate_pairs.tsv \
  --test-dir "$BER_DATA_DIR/test"
```

**Why both.**
- `validate_submission.py` prints `PASS` even when matched pairs fall outside the candidate file; that is only a warning.
- It never checks owner uniqueness or country consistency. `audit_matching.py` checks all of that and exits non-zero.

Properties of the submitted Composite B (measured):
- 1,732,544 rows (one per test S1); 5,851,832 pairs; 99,802 empty; 3.3776 per S1;
- 0 records claimed by more than one S1; 0 cross-country pairs; 0 matched pairs outside the 6,410,308 candidates;
- per country: France 870,307 pairs, India 2,734,227, US 2,247,298.

**A rerun is not byte-identical.**
- XGBoost with fixed seeds is deterministic on one machine.
- The cross-encoders are not bit-reproducible across GPUs (TF32, cuDNN kernel choice, non-deterministic reductions).
- Stage 3 moves about 500 decisions between machines.
- So compare the checks in the table above (the holdout reports in `work/reports/`, q7st's AUC, the drop counts), not the hashes. A rerun is expected within about ±0.0001 of the submitted score.

## Compliance

- **Only the provided data.** No external lookups, APIs, geocoding or internet datasets were used to resolve entities.
- **Hand-written lexicons**, documented in the code: legal forms, street types, US/India states, French departments → regions, generator list words, the OCR digit map, ordinal words. The Indic→Latin dictionary is learned from the training folds.
- **Models:** all ≤ 8B parameters and MIT or Apache-2.0, each fine-tuned only on our training pairs and our own pseudo-labels.

  | model | licence | parameters | role in Composite B |
  |---|---|---|---|
  | XGBoost | Apache-2.0 | — | stages 0–3 |
  | `intfloat/multilingual-e5-small` | MIT | 118M | feature `ce` |
  | `intfloat/multilingual-e5-base` | MIT | 278M | the `v7ce3` teacher (round-1 French pseudo-labels) |
  | `intfloat/multilingual-e5-large` | MIT | 560M | e5l, e5ls (France self-trained); France block members |
  | `BAAI/bge-reranker-v2-m3` | Apache-2.0 | 568M | bge; France block member |
  | `Qwen/Qwen2.5-1.5B` | Apache-2.0 | 1.5B | qst (LoRA, France self-trained) |
  | `Qwen/Qwen2.5-7B` | Apache-2.0 | 7.6B | q7st (LoRA, France self-trained): stage-2 mix ×2 for US/India, and the re-check of confident predictions in all countries |

- Seeds are fixed in every script; each artifact records the git commit and the command that produced it.
