# Handover: dev-skeleton

- **Author:** ameya (human; the agent was Claude Code)
- **When (IST):** 2026-09-25 14:25
- **Branch / PR / last commit:** `ameya/dev-skeleton` / see the PR "feat(pipeline): add pipeline skeleton, records stage and gates" / the head of the branch
- **Area and paths touched:**
  - shared foundation and pipeline (Ameya), in `code/business_entity_resolution/`: `src/ber/{pipeline,config,artifacts,records,outputs,paths}.py`, `src/ber/eval/{splits,gates,evaluate,__init__}.py`, stage stubs `src/ber/{normalize,block,features,model}/__init__.py`, tests, `README.md`, and the version bump to 0.2.0;
  - `docs/DEVELOPMENT.md` (new).

## TL;DR (3 lines max)

`python -m ber.pipeline` runs every stage by tag, and each artifact records the commit, command and inputs. `records`, `write` and `evaluate` work on the full data; the other stages are stubs for their owners. Gates are one command (`python -m ber.eval.gates`), and `docs/DEVELOPMENT.md` explains how to build a stage.

## What was done

- **The CLI**, `ber.pipeline`, runs stages in order:
  - records → normalize → block → features → train → predict → decide → write → evaluate;
  - options: `--tag`, `--in KIND=TAG`, `--set KEY=VALUE`, `--folds`, `--seed`, `--device`;
  - `all` runs the stages valid for the split; a stub exits with code 2 and names its roadmap task.
- **`ber.config.RunConfig`:** the split, tags, inputs, parameters, folds and seed, given to every stage.
- **`ber.artifacts`:** Parquet I/O with provenance (git commit with `+dirty`, command, IST time, inputs), atomic writes, and report JSONs that merge train and test results per tag.
- **The `ber.records` stage** builds `work/records/<split>.parquet` and `truth.parquet`. It keeps the pyarrow strings, and S1 order matches `test_source1.tsv`.
- **The `ber.outputs` stage (`write`)** checks subset, S2/S3-only and S1-order invariants, then writes both TSVs through `ber.io`.
- **The `ber.eval.evaluate` stage:**
  - holdout (or `--folds`) macro F0.5 per country;
  - a blocking section: recall, oracle, candidates per S1, recall per country and source;
  - test diagnostics per country for gate G8.
- **`ber.eval.splits`:** `TRAIN_FOLDS`, `oof_group`, `in_folds` and `DEV_FOLDS` (C2).
- **`ber.eval.gates`:** a Poisson paired bootstrap, `compare()` with the keep rule, and a CLI that prints the gate record table (C10).
- **Stubs** for `normalize`, `block`, `features` and `model` (`train`, `predict`, `decide`). Their docstrings give each owner the exact inputs, outputs, rules and suggested modules.
- **12 new tests** (36 in total), including a synthetic end-to-end run of records, write and evaluate.

## Current state

- **Works, verified on the full data:**
  - `records`: train in 50 s (12,527,040 records, 7,638,365 true pairs); test in 22 s (11,702,133 records; S1 by country: India 809,986, US 663,106, France 259,452);
  - `evaluate` on an empty prediction gives holdout 0.0558 (549,699 S1), matching the known baseline;
  - the gate CLI (empty vs oracle) takes 50 s on the full holdout.
  - The records cache is already built on Ameya's machine in `work/records/`, which completes roadmap task 1.1.
- **Half-done:** the stage stubs, which are Phase 1 tasks for their owners.
- **Known caveats:**
  - Loading the full test records takes about 3 GB of RAM, so load only the columns you need.
  - A report's `git_commit` shows `+dirty` if you run with uncommitted changes.

## Numbers (shared holdout, `ber.eval`; include the command)

| metric | value | command / tag |
|---|---|---|
| holdout macro F0.5, empty prediction | 0.0558 (India 0.0554, US 0.0560) | `python -m ber.pipeline --stage evaluate --split train --tag ameya-empty-v0` |
| gate: empty → oracle | Δ +0.9442 (95% CI +0.9436, +0.9448), KEEP | `python -m ber.eval.gates --base ameya-empty-v0 --new ameya-oracle-v0` |
| runtime | records 50 s / 22 s; evaluate 8 s; gates 50 s | the same commands |

## How to reproduce or continue (exact commands)

```
pip install -e "code/business_entity_resolution[dev]"
python -m pytest code/business_entity_resolution/tests -q                  # 36 passed
python -m ber.pipeline --stage records --split train
python -m ber.pipeline --stage records --split test
python -m ber.pipeline --stage normalize --split train --tag m3-norm-v0     # exits 2 until roadmap 1.2 lands
```

## Artifacts (local paths / drive links + sha256)

- `work/records/{train,test,truth}.parquet` on Ameya's machine. They can be rebuilt in about 75 s with the commands above, so there's no need to share them.

## Next steps (ordered, with suggested owner)

1. Merge after review. Merge `ameya/final-plan` first or second; the two PRs don't overlap.
2. Member 3: `ber.normalize` v0 (roadmap 1.2), then `ber.features` v0 (1.4).
3. Ameya: `ber.block` v0 with keys first (1.3a, by 16:30), then the views (1.3b).
4. Sachi: `ber.model.train` / `predict` / `decide` v0 (1.5, 1.6) on the key candidates of fold 0.

## Blockers, open questions, decisions needed

- None for this PR. The ownership confirmations are tracked in the final-plan handover.
