# Grenuke: Business Entity Resolution (Amazon ML Challenge 2026)

[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![Status: archived competition solution](https://img.shields.io/badge/status-archived-lightgrey.svg)

Team Grenuke's solution to the **Amazon ML Challenge 2026** business entity resolution task.
- **Result: 3rd place at the Grand Finale**, after reaching the Top 10 among more than 32,000 teams.
- The final submission ("Composite B") scored **0.990879 macro F0.5 on the public leaderboard**.

Team: **Ameya Borkar, Aarush Bakshi, Sachi Dhoka.**

## The task

For every **Source-1** business record, list every **Source-2/3** record that describes the same business.

| aspect | detail |
|---|---|
| Evidence available | names and addresses only |
| Matches per Source-1 record | 0 to 11, 3.46 on average |
| Records | 23.7M |
| Countries | train covers the US and India; **test adds France**, which never appears in train and has no labels |
| Metric | macro **F0.5**, computed per Source-1 entity. Precision weighs twice as much as recall, and singletons count: an empty prediction scores 1.0 when the entity truly has no match |
| Distractors | test hides look-alike decoys (a nudged house number, a swapped business word) among the true copies |

## How it works

```
raw TSVs ─► records + normalisation ─► blocking (multi-view token retrieval)      33.7 pairs per test S1
          ─► stage 0/1: XGBoost on string, number, legal-form and context features 4.77 per S1
          ─► cross-encoders on the uncertain band only (multilingual e5 / bge /
             Qwen LoRA, France self-trained)
          ─► stage 2 + 3: calibrated re-scoring with rival-S1 and cluster context
          ─► candidate cut (the stage-2 input set)                                 3.70 per S1
          ─► expected-F0.5 set decision, one owner per record
          ─► France: generator-aware rules + a Qwen2.5-7B re-check of confident pairs
          ─► matching_results.tsv                                                  3.38 matches per S1
```

The key ideas:
- **Spend compute where the uncertainty is.** Cheap gradient-boosted trees score every retrieved pair. The costly
  cross-encoders read only the ~2.6% of pairs the trees are unsure about. A 7B model re-reads confident French
  predictions, which are where a second opinion pays most.
- **Decide the way the metric scores.** The last layer chooses a *set* of records per entity from calibrated
  probabilities to maximise the expected F0.5, rather than thresholding pairs. Each record has at most one owner.
- **An unseen country needs its own care.** The holdout can't see France, so we used leave-one-country-out tests
  and label-free French diagnostics, and treated the public leaderboard as the only French measurement. Rules
  derived from the data generator's edit vocabulary remove French word-swap decoys. Guarded self-training adapts the
  cross-encoders to French text.
- **Precision first and gates always.** Every component shipped only after a paired-bootstrap gate on a fixed
  holdout. Ties went to the simpler option.

The full write-up is the methodology document,
[`experiments/ameya/final-zip/doc/Documentation_template.md`](experiments/ameya/final-zip/doc/Documentation_template.md)
(with a PDF alongside). The curated knowledge base, [`knowledge/`](knowledge/README.md), records every decision,
experiment and number with its evidence.

## Results

| measure | value | evaluation |
|---|---|---|
| Final submission (Composite B) | **0.990879** macro F0.5 | public leaderboard |
| Final placement | **3rd place, Grand Finale** (Top 10 finalist of 32,000+ teams) | organisers |
| Pipeline on labelled data | 0.9913 macro F0.5 (US 0.9911, India 0.9916); precision 99.9%, recall 97.5% | local holdout (549,699 US/India entities, no France) |
| Retrieval recall | 0.99135 of true pairs retrieved | local holdout |
| Candidate file | 3.70 candidates per Source-1 record | test |
| Leaderboard progression (selected uploads) | v2 0.97608 → v3 0.97961 → v5all 0.98781 → v6all 0.988609 → v7n 0.989721 → v7nst 0.990179 → v7sq-dpc 0.990545 → **Composite B 0.990879** | public leaderboard |

Private-leaderboard scores were never published; only rankings were.

## Repository map

```
code/business_entity_resolution/   the `ber` package: CLI, I/O, blocking, features, evaluation, tests
experiments/ameya/model-v1/        the final model chain (features, stages 0-3, cross-encoders, decision, rules)
                                   + RECIPE.md (exact commands) and the research notes ANALYSIS_*/RESEARCH_*
experiments/ameya/final-zip/doc/   the methodology document (Markdown + PDF) and its figures
experiments/<member>/              each member's research code and notes (a log; not maintained)
docs/                              developer guide, stage contracts, gate decisions, packaging and reproduce scripts
knowledge/                         the curated knowledge base: story, timeline, decisions, experiments, numbers, theory, Q&A
plans/                             the competition plan (FINAL_PLAN.md), why it was chosen, and the candidate plans
submissions/                       the leaderboard protocol
scripts/  .githooks/  .github/     setup, document scaffolding, policy hooks and CI
```

## Reproducing

**The data isn't included.** The competition dataset and the organisers' validator belong to the challenge and are
available to participants on the challenge platform. Put the data in `student_resource/dataset/{train,test}/`
(git-ignored), or point `BER_DATA_DIR` at it.

```bash
git clone https://github.com/AmeyaBorkar/Grenuke.git && cd Grenuke
bash scripts/setup.sh --venv          # Windows: powershell -ExecutionPolicy Bypass -File scripts/setup.ps1 -Venv
pip install -r code/business_entity_resolution/requirements.txt
pip install -e code/business_entity_resolution
python -m pytest code/business_entity_resolution/tests -q
```

- The exact end-to-end commands for the final models are in
  [`experiments/ameya/model-v1/RECIPE.md`](experiments/ameya/model-v1/RECIPE.md).
- The reproduce scripts are [`docs/package/reproduce_v6all.sh`](docs/package/reproduce_v6all.sh) and
  [`reproduce_v5all.sh`](docs/package/reproduce_v5all.sh).
- The pipeline CLI is documented in [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md).

**Hardware.**
- The XGBoost chain (v6all) runs end to end in about 3 hours on one machine: RTX 5070 Ti 12 GB, 24 cores, 31 GB RAM.
- The larger cross-encoders and the 7B re-check ran on rented GPUs.

**Models** (downloaded from their publishers; all MIT or Apache-2.0 and at most 8B parameters, as the challenge
required):
- multilingual-e5-small, -base and -large (MIT);
- bge-reranker-v2-m3 (Apache-2.0);
- Qwen2.5-1.5B and Qwen2.5-7B (Apache-2.0);
- XGBoost (Apache-2.0).

## How we worked

Three people and several AI coding agents worked in parallel for three days. The process is documented in
[`AGENTS.md`](AGENTS.md), [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`docs/`](docs/):
- one rule file for every agent;
- rebase-only PRs with git hooks and CI that block data, secrets and attribution lines;
- stage contracts and a shared holdout;
- a paired-bootstrap gate, recorded in [`docs/decisions/`](docs/decisions/), for every component.

## Citing

If this work helps you, please cite it (see [`CITATION.cff`](CITATION.cff)):

```
Borkar, A., Bakshi, A., Dhoka, S. (2026). Grenuke: Business Entity Resolution (Amazon ML Challenge 2026).
https://github.com/AmeyaBorkar/Grenuke
```

## License

[Apache License 2.0](LICENSE). See also [`NOTICE`](NOTICE).
- Security: [`SECURITY.md`](SECURITY.md).
- Conduct: [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

## Acknowledgements

Thanks to the Amazon ML Challenge 2026 organisers and jury, and to the authors of the open models and libraries this
work builds on.
