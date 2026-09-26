# Business Entity Resolution: Team Grenuke

Reproduces `output/matching_results.tsv` and `output/candidate_pairs.tsv` from the raw challenge TSVs.
Method and evidence: `Documentation_template.md` (zip root). Command-level source of truth: `src/model_v1/RECIPE.md`.

## Layout

| path | what |
|---|---|
| `src/ber/` | team package, one CLI `python -m ber.pipeline --stage <stage> --split <train\|test> --tag <tag>`: records, blocking (multi-view retrieval, Indic transliteration, domain/OCR repairs, French address normalisation), context features, write (organiser TSV format), evaluate |
| `src/model_v1/` | the final model chain: pair features (`feats*.py`, `lo_mix.py`), stage 0 + 1 (`s1.py`), cross-encoder feature (`ce.py`), stage 2 + calibration (`s2.py`, `cluster.py`), decision (`decide.py`), final candidate set (`cands_final.py`), France rules (`post_ops.py`), `RECIPE.md` |
| `reproduce.sh` | the full run for the submitted model, in order |
| `requirements.txt` | pinned versions |
| `tests/` | unit tests (`pytest -q`) |

## Setup

```bash
python3.12 -m venv .venv && source .venv/bin/activate      # or: conda create -n ber python=3.12
pip install -r code/business_entity_resolution/requirements.txt
pip install -e code/business_entity_resolution
pytest -q code/business_entity_resolution/tests
```

Data: the organiser folder `student_resource/dataset/{train,test}/*.tsv`. Set `BER_DATA_DIR` if it lives elsewhere.
Intermediate artifacts go to `work/` (`BER_WORK_DIR`), outputs to `output/` (`BER_OUTPUT_DIR`).

## Run

From the zip (or repository) root:

```bash
MODEL_DIR=code/business_entity_resolution/src/model_v1 bash code/business_entity_resolution/reproduce.sh
```

It runs, in order: records, the Indic dictionary, blocking, features, stage 0 + 1, the cross-encoder feature, stage 2,
the decision, the final candidate set, the France rules, the write stage and the organiser validator, then prints the
sha256 of both outputs.

| step | time on the reference machine |
|---|---|
| records + dictionary | ~2 min |
| blocking (train + test) | ~25 min |
| features | ~1 h |
| stage 0 + 1 (all of train) | ~30 min, peak ~18 GB RAM |
| cross-encoder | ~40 min (GPU) |
| stage 2 (all of train) | ~25 min, peak ~19 GB RAM |
| decision, candidates, rules, write | ~10 min |

Reference machine: RTX 5070 Ti 12 GB, 24 cores, 31 GB RAM. `ce.py` needs a CUDA GPU; the XGBoost stages fall back to
CPU (slower). Run nothing else memory-heavy next to stages 1 and 2.

## Checking the result

- The validator must print PASS.
- sha256 of the submitted files: TODO (fill from the final package). GPU nondeterminism in the cross-encoder can
  change a handful of pairs; the reference check is then the holdout macro F0.5 printed by `decide.py` and written to
  `work/reports/<model tag>.json` (submitted model: TODO).

## Compliance

- Only the provided data. No external lookups, APIs, geocoding or internet data.
- Hand-written lexicons, documented in the code: legal forms, street types, US/India states, French departments →
  regions, generator list words, the OCR digit map, ordinal words.
- Models: XGBoost (Apache-2.0); `intfloat/multilingual-e5-small` (MIT, 118M parameters), fine-tuned only on our
  training pairs. Both within the ≤ 8B, MIT/Apache-2.0 rule.
- Seeds are fixed in every script; each artifact stores the git commit and the command that produced it.
