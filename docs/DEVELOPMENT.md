# Developer guide: running, building and gating pipeline stages

This guide covers **how** to work on the pipeline.
- **What** we build is in `plans/FINAL_PLAN.md`.
- The data formats stages exchange are in `docs/CONTRACTS.md`.
- **Who** owns what is in `docs/TEAM.md`.
- The team process is in `CONTRIBUTING.md`.

This is a shared file, owned by the coordinator.

## 1. Setup (once per machine)

```
git clone https://github.com/AmeyaBorkar/Grenuke.git && cd Grenuke
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1 -Venv      # or: bash scripts/setup.sh --venv
pip install -r code/business_entity_resolution/requirements.txt       # pinned: rapidfuzz, numba, xgboost, lightgbm, ...
pip install -e "code/business_entity_resolution[dev]"
# put the dataset in student_resource/dataset/{train,test}/ (git-ignored)
python -m pytest code/business_entity_resolution/tests -q
python -m ber.pipeline --stage records --split train                  # ~50 s: work/records/train.parquet + truth.parquet
python -m ber.pipeline --stage records --split test                   # ~25 s
```

- **GPU (blocking and XGBoost):** install the CUDA build of torch from the comment in `requirements.txt`. XGBoost uses `device="cuda"` when a GPU exists. Every stage must also run on the CPU.
- **Paths:** set these environment variables when your data or artifacts live elsewhere, for example on a second disk: `BER_DATA_DIR`, `BER_WORK_DIR`, `BER_OUTPUT_DIR`. Never hard-code personal paths.

## 2. The pipeline at a glance

```
python -m ber.pipeline --stage <stage|all> --split <train|test> --tag <tag> [--in KIND=TAG ...] [--set KEY=VALUE ...] [--folds 0-4]
```

| stage | module (owner) | reads | writes | contract |
|---|---|---|---|---|
| `records` | `ber.records` (Ameya) | TSVs | `work/records/<split>.parquet`, `truth.parquet` | C3 |
| `normalize` | `ber.normalize` (Bakshi) | records | `work/norm/<tag>/<split>.parquet` | C3 |
| `block` | `ber.block` (Ameya) | norm | `work/candidates/<tag>/<split>.parquet` | C4 |
| `features` | `ber.features` (Bakshi; context groups Ameya) | candidates, norm, truth | `work/features/<tag>/<split>.parquet` | C8 |
| `train` | `ber.model` (Sachi), train only | features | `work/models/<tag>/`, `work/scores/<tag>-s1/train.parquet` | C5 |
| `predict` | `ber.model` (Sachi) | features, models | `work/scores/<tag>/<split>.parquet` | C5 |
| `decide` | `ber.model` (Sachi) | scores, candidates | `work/matches/<tag>/<split>.parquet` | C9 |
| `write` | `ber.outputs` (Ameya), test only | candidates, matches | `output/*.tsv` | C6 |
| `evaluate` | `ber.eval.evaluate` (Ameya) | matches, candidates, truth | `work/reports/<tag>.json` | C7 |

- **Tags** (C0) are `<member>-<stage>-v<N>`, for example `ameya-block-v0`. Every run writes under its own tag, so nobody overwrites anybody.
- **`--in KIND=TAG`** reads an input from another tag. The kinds are `norm`, `candidates`, `features`, `models`, `scores` and `matches`. Without `--in`, a stage reads its inputs under its own `--tag`.
  - Example: `--stage features --tag m3-feat-v0 --in norm=m3-norm-v0 --in candidates=ameya-block-v0`.
- **`--folds 0`** restricts train S1 to fold 0 (about 110k entities) for quick iterations. PR numbers use the full holdout (C2).
- **`--set KEY=VALUE`** passes a stage parameter. The owner documents the keys, and the stage reads them with `cfg.param("k", 40, int)`.
- **`--stage all`** runs every stage valid for the split, in order, with one tag.

The **status as of today**: `records`, `write` and `evaluate` work. The other stages are stubs that exit with code 2 and point to their roadmap task.

## 3. Building a stage

Each stage is one function, `run(cfg: RunConfig) -> dict`, or `train` / `predict` / `decide` in `ber.model`. The returned dict is a short summary that the CLI prints.

```python
from ..artifacts import read_table, write_table
from ..config import RunConfig
from ..records import load_records, load_truth

def run(cfg: RunConfig) -> dict:
    rec = load_records(cfg.split, columns=["eid", "source", "country", "name", "address"])   # load only what you need
    cands = read_table("candidates", cfg.input_tag("candidates"), cfg.split)
    ...
    write_table(df, "features", cfg.require_tag(), cfg.split, command=cfg.command,
                inputs={"candidates": cfg.input_tag("candidates"), "norm": cfg.input_tag("norm")})
    return {"pairs": len(df)}
```

- **Contracts first.** Write exactly the columns in `docs/CONTRACTS.md`. Adding documented columns is fine; renaming or removing one needs a contracts PR.
- **Provenance is automatic.** `write_table` stores the git commit (`+dirty` if you have uncommitted changes), the command, the time and the inputs. Commit before a run whose numbers you will report.
- **Keep the package importable in CI.** CI installs numpy, pandas, pyarrow and numba (numba kernels are `@njit` at module level). Import the other heavy libraries (rapidfuzz, xgboost, torch) **inside** your functions, not at module top level.
- **Split big stages into modules** inside your package, and keep `run()` thin. The suggested modules are in each package docstring.
- **Seeds:** use `cfg.seed` everywhere (numpy, xgboost, sampling).
- **Leakage (C2).** Anything fitted on labels uses training folds 5–19 only:
  - models, calibration, token encodings, learned dictionaries;
  - out-of-fold scores use `ber.eval.splits.oof_group`.
  - Tuning one or two scalars on the holdout is fine.

## 4. Performance rules (23.7M records, laptops with 16–32 GB)

- **Never write a Python loop over pairs.**
  - For string similarity, use `rapidfuzz.process.cpdist(a, b, scorer=..., workers=-1)` on aligned arrays of the pair's strings.
  - For token work, map tokens to int32 ids once, build CSR arrays (indptr, indices, idf), and write `numba.njit(parallel=True)` kernels over pairs.
  - For top-k, use a torch fp16 matmul in tiles with `torch.topk`, and keep running top-k buffers on the GPU. faiss-gpu has no Windows wheels.
- **Work per country and in chunks** of about 1–5M pairs.
  - Use `float32` features and `int32` codes. Load only the columns you need; the full test records take about 3 GB in memory.
  - Build XGBoost data with `xgboost.QuantileDMatrix` from chunks.
- **Windows uses spawn** for multiprocessing. Keep worker functions at module top level, and guard entry points with `if __name__ == "__main__":`.
- **Measure** with `time.perf_counter()`, and log peak memory for the handover.

## 5. Evaluating

```
python -m ber.pipeline --stage evaluate --split train --tag <tag>                  # holdout: macro F0.5 per country (+ blocking)
python -m ber.pipeline --stage evaluate --split train --tag <tag> --folds 0        # quick check on fold 0
python -m ber.pipeline --stage evaluate --split test  --tag <tag>                  # test diagnostics per country (no labels)
```

- The report is `work/reports/<tag>.json` (C7). Paste its headline numbers into your handover and PR.
- For reference, the empty prediction scores **0.0558** on the holdout (the singleton share).
- The blocking section reports pair recall, oracle F0.5, candidates per S1 (mean and p99), and recall per country and per source.

### Dev sample (small machines)

- `ber.eval.splits.in_dev_sample(eids)` selects about 110k train S1 (a quarter of folds 0, 5, 10 and 15). Its fold-0 part is a dev holdout (about 27k S1), and folds 5/10/15 give one fold per OOF group, so train → OOF → calibrate → decide all work on it.
- Ameya shares dev artifacts on the team drive: `work/candidates/ameya-block-v0-dev/train.parquet`, then the dev features. Use them with `--in candidates=ameya-block-v0-dev`.
- Evaluate on it: `python -m ber.pipeline --stage evaluate --split train --tag <tag> --folds 0 --set sample=dev`. Gates: `python -m ber.eval.gates ... --folds 0 --sample dev`.
- Numbers for PRs still come from the full holdout, run on the integration machine.

## 6. Gates (plans/FINAL_PLAN.md §9)

A component beyond the v0 baseline ships only if it beats the simpler alternative on the holdout:

```
python -m ber.eval.gates --base sachi-model-v0 --new sachi-model-v1          # compares work/matches/<tag>/train.parquet
```

- It prints the mean Δ macro F0.5, the 95% paired-bootstrap interval, P(better) and Δ per country.
- **Keep** the new component if Δ ≥ +0.002 and the lower bound is above 0. Heavy components need +0.003. Ties go to the simpler option.
- Record every result with `python scripts/new_doc.py decision --member <you> --topic gate-g6-dp-vs-threshold` (C10), and paste the printed table into it.

## 7. Producing a submission

```
python -m ber.pipeline --stage write --split test --tag <tag> --in candidates=<block tag> --in matches=<model tag>
python student_resource/utils/validate_submission.py --matching output/matching_results.tsv --candidate output/candidate_pairs.tsv --test-dir student_resource/dataset/test
```

`write` checks the invariants first:
- one row per test S1, in file order;
- S2/S3 ids only;
- matches ⊆ candidates.

Only the captain uploads, following `submissions/README.md`. Every upload gets a record, a `sub/` tag and a `CHANGELOG.md` row.

## 8. Sharing artifacts between machines

GPU stages (blocking) run on Ameya's laptop. To pass artifacts on:
- upload `work/<kind>/<tag>/` to the team drive under the same path;
- include a `MANIFEST.txt` with `sha256sum` of each file, the git commit and the command;
- link it in your handover.

The Parquet metadata (`ber.artifacts.read_meta(path)`) also carries the commit and command.

## 9. Tests

- Put unit tests for your module in `code/business_entity_resolution/tests/test_<area>_*.py`.
  - Use tiny synthetic inputs; `tests/test_pipeline.py` shows how to fake a dataset with `BER_*` environment variables.
  - Tests must not need the real data or a GPU.
- **Good test cases** are the noise the plan lists:
  - Indic script, `N°16`, `8444b`, `<NULL>`, legal-form moves, domains and hashtags;
  - a nudged house number (4104 vs 4108), a business word (Exports), an empty address.
- Run `python -m pytest code/business_entity_resolution/tests -q` before every PR.

## 10. Troubleshooting

| symptom | fix |
|---|---|
| `work/records/train.parquet not found` | run `python -m ber.pipeline --stage records --split train` |
| `... not found: produce it first, or point at another tag with --in` | the input tag has no artifact for this split. Check `--in` and `ls work/<kind>/` |
| `stage X is not implemented yet` (exit code 2) | that stage is still a stub; see its roadmap task |
| a git commit ending in `+dirty` in reports | you ran with uncommitted changes. Commit and re-run before reporting |
| out of memory | load fewer columns, process per country, chunk pairs, use `float32` |
