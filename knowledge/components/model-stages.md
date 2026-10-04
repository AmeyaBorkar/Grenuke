# Model stages 0 to 3 (MDL)

**Summary.** Four XGBoost classifiers form a cascade: stage 0 is a cheap filter, stage 1 scores each pair, stage 2 re-scores it against its rivals over the whole candidate graph and is isotonic-calibrated into pc, and stage 3 re-scores contested and empty-address records.
In the final fit (`--all`) stages 1 and 2 use four out-of-fold groups: the holdout is one of them. Holdout predictions are out of fold, but the test models did see the holdout labels, so "never trained on the holdout" is true only in that narrow sense.
Path prefixes: `ber/` is `code/business_entity_resolution/src/ber/`; `mv1/` is `experiments/ameya/model-v1/`. Parameters are read from the code at the cited line.

## 1. Purpose

Turn about 66M pair-feature rows into one calibrated match probability per candidate pair, spending model capacity only where pairs are uncertain: the cascade removes about 85% of pairs at stage 0, and the stages after it work on 10M rows or fewer.
Provide honest out-of-fold scores for every labelled S1, so that the decision layer and the gates can be tuned and measured on the holdout.

## 2. How it works

### 2.1 Folds and groups ([`ber/eval/splits.py`](../../code/business_entity_resolution/src/ber/eval/splits.py), details in [evaluation.md](evaluation.md))

`fold = splitmix64(eid) mod 20`. Holdout = folds 0-4 (549,699 S1); training folds 5-19; groups 0, 1, 2 = folds 5-9, 10-14, 15-19. Each group is a quarter of the labelled S1. Without `--all`, model g trains on the other two training groups (50% of S1) and the holdout gets the mean of the three models. With `--all` the holdout becomes group 3: model g trains on the other three quarters (75% of S1), scores its own quarter, and test gets the mean of the four models (`mv1/s1.py:132-160, 198-202`; `mv1/s2.py:272-275`).

### 2.2 Hyperparameters

All stages 0 to 2: `binary:logistic`, logloss, `hist`, `device cuda`, `max_bin 256`, subsample 0.8.

| stage | rows | parameters | rounds and stopping |
|---|---|---|---|
| 0 (`mv1/s1.py:34-36, 120-130`) | a 10% S1 hash slice of training folds (salt `0x51A6E0`) | max_depth 6, eta 0.2, colsample 0.8, min_child_weight 5 | 200 rounds, no early stopping; one in-sample model, not out of fold |
| 1 (`:37, 132-160`) | pairs with p0 at least tau0; models trained per group | max_depth 9, eta 0.06, colsample 0.7, min_child_weight 10, lambda 2.0 | up to 4000 rounds, early stopping 60 on a 2% S1 slice (salt `0x51A6E1`) of the other groups' rows |
| 2 (`mv1/s2.py:42-45, 210, 276, 297-298`) | p0 at least tau0 and p1 at least 0.002 (`P_MIN`); g1w: 10,065,671 train rows [M] | max_depth 7, eta 0.05, colsample 0.8, min_child_weight 10, lambda 2.0; seed 0 | up to 3000 rounds, early stopping 60 on a 2% S1 slice (salt `0x51A6E2`) |
| 3A (`mv1/stage3.py:57-58, 215-222`) | contested records | max_depth 6, eta 0.1, subsample 0.8, min_child_weight 20, nthread 8, seed 0 | up to 2000 rounds, early stopping 50 on a 10% record hash slice |

Stage 0 sets `tau0` as the 0.0005 quantile of p0 over training-fold positives outside its sample (`--keep-pos 0.9995`, `:90, 126-127`); pairs below it keep p1 = p0 and never go further. Stage-1 inputs are the 91 pair features ([features.md](features.md)). Stage-2 inputs: 26 own rivalry and cluster features, the top 30 stage-1 features by gain of `stage1_g0` (`--top 30`), and extras not already among them (6 legal-form, `ce__logit`, the cross-encoder mix logit, 6 signed-number); 65 features in the France block [R, `mv1/s2.py:155-175, 236-240`]. g1w best iterations 824, 957, 1,032, 911 [M].

### 2.3 Stage 2 and calibration

Stage 2 sees the full candidate graph: per record the best and second-best p1, margin, rank, claims above 0.5, sum and share; per S1 rank, max, sum (the expected cluster size), counts above 0.5, 0.8 and 0.95, neighbour gaps and per-source balance. These need every real rival, so sampling is only acceptable for training rows (D-MDL-03). Test p2 is the mean of four models, except French rows that carry pseudo-labels, which are cross-fitted ([france.md](france.md)). Calibration (`mv1/s2.py:316-322`): `IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1)` fitted on the OOF p2 of labelled stage-2 rows, applied to train and test rows, giving pc. With `--all`, `train_rows` is all rows, so the fit includes the holdout's OOF p2 (`:272-275, 319`). Calibration bins are within about 0.015 and pc is reliable within about 0.03 per decile in every country by source cell [M, D-MDL-03].

### 2.4 Stage 3 (`mv1/stage3.py`)

Reads rows with pc at least 0.001 (`P_KEEP`) or p1 at least 0.02; with `--p-cand 0.02 --top-r 2` the candidate cut of [blocking.md](blocking.md) is applied and every other pair gets pc = 0.
- A, contested records: records with at least 2 S1 at pc at least 0.01 (`P_CONTEST`). 11 features: logit pc, the pair's S1's confident copies (owned, pc at least 0.5, this record excluded) in the same source and the other source, a none flag, the best rival's logit pc and its counts, the number of contesting S1, empty address, is_s3 (`:59-60, 192-204`). Three OOF groups; records with any holdout S1 among their candidates are never trained on (`:181-184, 219`).
- B, empty-address records: an isotonic map from the record's total pc (its mass) to "its owner is a candidate", fitted on records not touching the holdout; that record's pcs are scaled up only, capped at 0.999 (`P_MAX`) (`:244-270`). Rationale: an empty-address record is a true copy 97.7% of the time.

### 2.5 What "never trained on the holdout" really means

| component | holdout labels used? |
|---|---|
| Stage 0 and `tau0` | no: folds 5-19 only (`s1.py`: `train_rows = fold >= 5`) |
| Holdout's own p1, p2, pc | out of fold: model 3 never saw group 3 |
| Test p1 and p2 | mean of 4 models; models 0, 1, 2 each trained on group 3, so 3 of 4 saw the holdout |
| Stage-2 training rows | include holdout rows with their OOF p1, for models 0 to 2 |
| Isotonic calibration | fitted on OOF p2 including the holdout |
| Look-alike odds, Indic dictionary | no: groups 0-2 and folds 5-19 only |
| Stage 3 and the cross-encoders | no: three groups, holdout excluded |
| Thresholds, set-selection shifts, 7B cut-off, rule thresholds | tuned on the holdout |

So the holdout is a comparison set, not an untouched test. The tie measured when `--all` was introduced (v5 to v5all +0.00002 [-0.00003, +0.00007], D-MDL-10) is expected: the holdout scores one 75% model while test gets the mean of four. The benefit of `--all` is therefore invisible locally and was adopted on reasoning; by the tie rule it would have lost. Say it as: "holdout predictions are out of fold; the final test models also saw holdout rows" (CF-18 in [conflicts](../conflicts.md)).

## 3. Why this design

Decision records: [MDL](../decisions/MDL.md). D-MDL-01 XGBoost on the GPU, not LightGBM (2M rows x 100 features x 200 rounds in 4.6 s [M]). D-MDL-02 the v0 baseline. D-MDL-03 stage 2 over the full graph with cluster support (G4 passed). D-MDL-05 the stage-0 filter keeps 15.4 to 17.9% of pairs at 99.95% of positives, about 5 times faster. D-MDL-06 out-of-fold stage 1, holdout and test get the mean of the models. D-MDL-07 run the chain from Ameya's experiment folder rather than `ber.model` (memory and speed). D-MDL-08 gate G4 (Sachi). D-MDL-10 and D-NRM-04 final fit on all of train. D-MDL-11 stage 3 (adopted at 15:44 on 26 Sep after it gained on v6all). D-MDL-12 v6all with a plain threshold. D-MDL-15 and D-MDL-16 US/India converged, then India and the US from Bakshi's g1w. Related: D-EVL-03, D-DEC-08 (set selection).

## 4. Alternatives and why not

- LightGBM or a blend (G10): never tested; the XGBoost GPU speed made the learner secondary.
- Sachi's `ber/model` v0 (depth 8, eta 0.08, full refit at 1.1 times the mean best iteration, cross-fitted isotonic; `ber/model/stage1.py:12-28`): kept as the baseline path, not on the final path.
- Softmax over a record's S1 plus none (G5), owner-removed training examples (D-MDL-04): never built.
- Stage-2 tuning (D-MDL-13): seed bagging -0.00004; depth 8 and learning rate 0.03 no better early-stopping loss. A bag of four over v7sq3 +4.6e-6 [-10.6, +21.1], P 0.714: a tie, so the simpler (D-MDL-15).
- France from stage 2 instead of stage 3 (`frs2`, D-MDL-14): withdrawn; 35.4% of its extra drops had an empty address (base rate 2.7%).
- A stage-1-only or stage-2-only model: stage 2 over stage 1 gave +0.0022 (v2) and +0.0017 (v3) at full scale [M].

## 5. Numbers

Local holdout macro F0.5 (US/India, 549,699 S1, no France) unless stated [M, [numbers §3.1](../numbers.md)].

| version | F0.5 | note |
|---|---|---|
| baseline v0 | 0.9683 | stage 1 only, one threshold |
| model v2 | 0.98436 | public LB 0.97608 |
| model v3 | 0.98882 | public LB 0.97961 |
| v5all | 0.990156 | `--all`, the cut; public LB 0.98781 with rules |
| v6all, with stage 3 | 0.990788; 0.990842 | stage 3 +0.000055 [+0.000025, +0.000085] |
| v7sq | s3 0.991246 | self-trained cross-encoders |
| g1w (behind Composite B) | 0.991323 (US 0.991114, India 0.991635) | the stage-3 decision; public LB of Composite B 0.990879 |

Stage 3 on v5all: +0.000051 [+0.000023, +0.000079], 72 s, 1.7 GB. Stage 2 over stage 1 at G4: dev +0.00692 [+0.00622, +0.00772]. Stage 0 keeps 15.4% of pairs (v3 bundle). Runtime on the box: stage 1 8 + 4 min, g1w stage 2 20 min [R]; on the laptop stage 1 about 30 min at 18 GB, stage 2 about 25 min at 19 GB [R].

## 6. Failure modes and limits

- A CUDA GPU is needed for the whole chain: `device: "cuda"` is hard-coded in stages 0 to 2 (`mv1/s1.py:34`, `mv1/s2.py:43`), although the package README says CPU ([CF-37](../conflicts.md)).
- Reproduction lands within about 0.0001 and is not byte-identical: the v7sq rebuild gave 0.991261 against 0.991246, and stage 3 moves about 500 decisions between machines.
- Train p1 and p2 are single-model OOF scores, test scores are 4-model means, so the isotonic map fitted on single-model scores is applied to averaged scores: a mild shift.
- The document says "four XGBoost stages, each out of fold over three groups"; exact only for stage 3 and the cross-encoders ([CF-22](../conflicts.md)). The `s2.py` docstring says calibration never uses the holdout; with `--all` it does ([CF-18](../conflicts.md)).
- `s1.py` crashes on its last, report-only line in a fresh work directory (it reads `matches/ameya-baseline-v0`); the box needed an empty placeholder, which makes `gate_vs_baseline_v0` fields of rebuilt reports meaningless.
- No explicit XGBoost seed in stages 0 and 1 (library default 0).
- Stage 3 was gated on US/India only; several stage-2 fits must run serially because of memory.

## 7. Scale

Cost is O(pairs x trees x depth) and shrinks per stage: 66M rows into stage 0, about 10M into stage 2. Stages 1 to 3 peak at 18-19 GB, so a 32 GB machine runs them one at a time; `s2.py` builds the test-side matrix before the train matrix so the two never coexist (`mv1/s2.py:243`); stage 3 streams row groups in two passes. At 100 times the pairs the cascade keeps working if stage 0 keeps its 15% and the later stages move to distributed or out-of-core GBDT; the full-graph rivalry features become a distributed group-by ([theory 06](../theory/06-gradient-boosting-and-stacking.md), [theory 11](../theory/11-scaling-to-billions.md)) [E].

## 8. Theory links

[06 Gradient boosting, cascades and stacking](../theory/06-gradient-boosting-and-stacking.md), [07 Calibration](../theory/07-calibration.md), [05 Evaluation methodology](../theory/05-evaluation-methodology.md), [F03 Machine learning fundamentals](../theory/foundations/F03-machine-learning-fundamentals.md), [F05 Trees and ensembles](../theory/foundations/F05-trees-and-ensembles.md), [F18 Tuning, ensembles and interpretability](../theory/foundations/F18-tuning-ensembles-and-interpretability.md).

## 9. Likely questions

- **Why four stages?** Each does a job the previous cannot: a cheap filter, a pair scorer, a rival-aware re-scorer with calibration, and a joint re-scorer for contested records.
- **Is the holdout clean?** Its predictions are out of fold; the final test models also saw its rows; thresholds were tuned on it. Paired differences are fair, absolute levels slightly optimistic.
- **Why XGBoost and not a neural model?** Tabular features of this kind suit gradient-boosted trees, the GPU made them fast, and the transformers are used where text must be read jointly ([cross-encoders.md](cross-encoders.md)).
- **Why did tuning stop?** Bagging, depth 8 and a smaller learning rate gave no gain (D-MDL-13).
- **Why is stage 0 not out of fold?** It only drops pairs far below the decision range, keeping 99.95% of positives; a single in-sample model is enough.
- More in [qa.md](../qa.md).
