# Components: the pipeline in one place

**Summary.** Our solution is a cascade that spends compute only where a pair is still uncertain: exact blocking proposes about 34 candidates per S1, four XGBoost stages cut that to 3.70 per S1, cross-encoders read only the uncertain band, a decision layer picks each S1's set, and a Qwen2.5-7B re-checks confident predictions.
Public leaderboard 0.990879 for the submitted Composite B; local holdout (US/India, no France) 0.9913. We placed 2nd of the Top 10 and there is no private score to quote ([numbers.md](../numbers.md)).
Each page below follows [STANDARD §2.6](../STANDARD.md): purpose, how it works, why, alternatives, numbers, failure modes, scale, theory links, likely questions.

Path prefixes used in all component pages: `ber/` is `code/business_entity_resolution/src/ber/`; `mv1/` is `experiments/ameya/model-v1/`; `stk/` is `mv1/stack/`; `pipe/` is `mv1/pipeline/`; `fpk/` is `experiments/bakshi/final-package/`; `box/` is `experiments/bakshi/box/`. Scores: public LB = the leaderboard during the challenge; local holdout = the fixed 25% of labelled US/India S1 (549,699 S1).

## The funnel

Pairs per test S1 [M, final pipeline, [numbers §2](../numbers.md)]:

| step | pairs per S1 | pairs on test | note |
|---|---|---|---|
| all possible | about 10 million | 1.7 x 10^13 | S1 times S2/S3 records [E] |
| blocking (retrieval) | 33.73 | 58,437,794 | holdout recall 0.99135 |
| after stage 0 | 4.77 | | drops about 85% at 99.95% of true pairs |
| the learned cut (candidate file) | 3.70 | 6,410,308 | holdout recall 0.98354 |
| uncertain band, read by cross-encoders | 0.86 | 1,490,930 | 0.02 <= p1 <= 0.99 |
| final matches (Composite B) | 3.378 | 5,851,832 | true matches average 3.46 per S1 |

## End to end, with artifact names

Driver: `fpk/reproduce.sh` with `VARIANT=compositeB` calls `box/compositeB.sh`, which calls the driver back for the v7sq chain; every step skips work whose output exists. Source: [packaging.md](packaging.md).

1. Records: `ber.pipeline --stage records` turns the raw TSVs into `work/records/{train,test}.parquet` and `truth.parquet` ([data-and-problem.md](data-and-problem.md)).
2. Indic dictionary: `mv1/feats.py --dict-only` gives `work/models/ameya-fx1/indic_dict.parquet`, 693 entries ([normalisation.md](normalisation.md)).
3. Blocking v3: `ber.pipeline --stage block` gives `work/candidates/ameya-block-v3/{split}.parquet`, 66,429,057 train and 58,437,794 test pairs ([blocking.md](blocking.md)).
4. Pair features, bundle `ameya-fx5` (groups str, cx, nx, lo, lg, lop, lo0): 91 features, `work/features/ameya-fx5-*` ([features.md](features.md)).
5. Stage 0 and 1 (`s1.py --all`): `work/scores/ameya-s1-v6all/{train,test}` with p0, p1, and four stage-1 models ([model-stages.md](model-stages.md)).
6. e5-small feature `ce__logit` and the band export (1,568,554 train and 1,490,930 test rows) ([cross-encoders.md](cross-encoders.md)).
7. Teacher v7ce3: e5-large and e5-base, stage 2, the cut `ameya-cands-v6all-c2`, stage 3, decision, French rules, acronym join ([decision-layer.md](decision-layer.md), [rules.md](rules.md)).
8. Round-1 French pseudo-labels from the teacher; self-trained cross-encoders e5ls, Qwen2.5-1.5B (qst) and bge, z-averaged into one group `cmq`; the v7sq chain; the stacked rules `-dpc` ([france.md](france.md)).
9. Round-2 band labels (385,274 French pairs), then the Qwen2.5-7B (q7st), three adapters, one out-of-fold group per GPU ([llm-recheck.md](llm-recheck.md)).
10. g1w: the 7B counted twice in the cross-encoder mix, stage 2 to `-dpc`; its US/India rows become Composite B's.
11. 7B re-check scoring of every French final pair and of US/India predictions with p1 above 0.99.
12. France block: more self-trained cross-encoders, guarded round-2 stage-2 labels at weight 3, France set selection, `mixmdp`; 871,147 French pairs.
13. Compose: US/India from g1w, France from the France block, minus 7B drops below logit -6; the organisers' validator and a strict audit; sha256 of both TSVs ([submission-strategy.md](submission-strategy.md)).

## The pages

| page | area | what it covers |
|---|---|---|
| [data-and-problem.md](data-and-problem.md) | PRB | the task, the data, one owner per record, look-alikes, the Bayes limit, ids and file format |
| [evaluation.md](evaluation.md) | EVL | the metric, the hash holdout, folds, paired bootstrap gates, leaderboard arithmetic, probes, controls |
| [normalisation.md](normalisation.md) | NRM | folding, lexicons, Indic transliteration, name repairs, legal forms |
| [blocking.md](blocking.md) | BLK | per-country IDF retrieval in both directions, repairs, the learned cut, an honest section on city and state keys |
| [features.md](features.md) | FEA | the 91 pair features and why France needed count-based and label-free ones |
| [model-stages.md](model-stages.md) | MDL | stages 0 to 3, hyperparameters, four out-of-fold groups, what "never trained on the holdout" means |
| [cross-encoders.md](cross-encoders.md) | CE | e5, bge and Qwen cross-encoders on the uncertain band, the z-mean mix, self-training |
| [decision-layer.md](decision-layer.md) | DEC | per-S1 expected-F0.5 set selection, ownership, thresholds, the stacked layer |
| [rules.md](rules.md) | RUL | France generator rules, acronym join, stacked rules, look-alike drop |
| [france.md](france.md) | FRA | the unseen country: proxy odds, self-training, guarded labels, probes, estimates |
| [llm-recheck.md](llm-recheck.md) | LLM | Qwen2.5-7B as a cross-encoder and as a re-checker of confident predictions |
| [submission-strategy.md](submission-strategy.md) | SUB | upload budget, controls, composites, the final choice |
| [packaging.md](packaging.md) | PKG | reproduce.sh, the audit, hashes, the ZIP, hardware, the methodology document |
| [process-and-infra.md](process-and-infra.md) | ORG | team, repo rules, machines, rented GPUs, failures, coordination |

## How the components connect

- **One owner and one country at a time.** Blocking, IDF and features are fitted per exact country label, so France is handled by the same code with its own vocabulary and no labels. The model and decision layer enforce one owner per record.
- **Cheap to expensive.** Each stage hands the next a smaller set: retrieval (CPU, exact) to stage 0 (a 200-tree filter) to stage 1 (per-pair scoring) to the cut to the cross-encoders (only 0.86 pairs per S1) to stage 2 (rivalry over the whole graph, calibrated into pc) to stage 3 to the decision layer, and last the 7B, which reads only predictions that are confident already. Running the 7B on every retrieved pair would take about 27 GPU-hours [E].
- **Labels for US/India, proxies for France.** Look-alike word odds use labels where they exist and a label-free proxy for France; France gets pseudo-labels from our own decisions, guarded, and its decisions come from a separate France block.
- **One holdout, honest about its limits.** Every step is gated on the same hash holdout, out of fold; it has no France, so France is judged by label-free diagnostics and by leaderboard arithmetic. See [evaluation.md](evaluation.md) and the caveats in [model-stages.md](model-stages.md).
- **The candidate file is the set the model scores.** It is the stage-1 cut, so the decision layer can only choose inside it ([blocking.md](blocking.md)).

## Conventions and cross-links

- Evidence levels: M measured, E estimated, R reported, U uncertain ([STANDARD §3](../STANDARD.md)). Numbers to quote and numbers not to quote: [numbers.md](../numbers.md). Disagreements between sources: [conflicts.md](../conflicts.md).
- Decisions by ID: [decisions.md](../decisions.md). The story, timeline, failures and lessons: [story.md](../story.md), [timeline.md](../timeline.md), [failures.md](../failures.md), [lessons.md](../lessons.md). Jury questions with spoken answers: [qa.md](../qa.md).
- Theory: [theory/README.md](../theory/README.md) (pages 01 to 11 and foundations F01 to F18).
- Final-path note: the code tree holds more than Composite B uses (for example `ber/normalize/`, `ber/features/` except `context.py`, `ber/model/`); each page says which parts are on the path, and `fpk/reproduce.sh` with `box/compositeB.sh` is the authoritative list of what runs ([packaging.md](packaging.md)).
