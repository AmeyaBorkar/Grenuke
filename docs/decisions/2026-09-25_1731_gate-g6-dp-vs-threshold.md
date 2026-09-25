# Decision: gate-g6-dp-vs-threshold

- **Date (IST):** 2026-09-25 17:31
- **Author:** sachi
- **Status:** accepted for v0 (dev-sample evidence); re-check on the full holdout when full features exist
- **Affects:** stage 06 decide (C9 matches); `experiments/sachi/model/decide.py`, `experiments/sachi/run_real.py`

## Context

FINAL_PLAN §9, gate G6: does the exact expected-F0.5 decision per S1 beat one tuned global threshold?
Both rules run on the same calibrated probabilities (stage-1 XGBoost, 3 OOF groups from `ber.eval.oof_group`,
isotonic calibration cross-fitted on OOF), after per-record argmax ownership.

- **Data:** dev kit `devkit-v0`, features `ameya-baseline-v0-dev` (37 features, C8).
  Trained on dev-sample folds 5/10/15 (2,393,231 pairs); evaluated on dev-sample fold 0 (27,651 S1, 819,316 pairs).
- **Baseline tag / candidate tag:** `m-v0-dev` (threshold) vs `m-v0-dev` (DP), same scores.
- **Test:** `ber.eval.paired_bootstrap` over S1 entities, 1,000 resamples.
- **Keep rule (plan §5.4):** Δ ≥ +0.002 and the 95% CI above 0. Ties go to the threshold.

## Options considered

1. **Tuned global threshold** on calibrated p: best t = 0.70, holdout macro F0.5 **0.9648**.
2. **Exact expected-F0.5 per S1:** Poisson-binomial DP over prefix sizes, with one global logit shift b tuned on the
   same holdout. Best b = −0.25, holdout macro F0.5 **0.9646**. The DP was checked against brute-force enumeration
   (40 random cases) in `experiments/sachi/tests/test_decide.py`.

**Gate result (C10):** delta −0.00023, ci_low −0.00088, ci_high +0.00049, p_better 0.257, n 27,651.

A second run on cruder practice features (`dev-sachi`, 4,861 holdout S1) agrees: Δ −0.00045, CI [−0.00133, +0.00046].

## Decision

Keep the **tuned global threshold** (t = 0.70) as the v0 decision rule. The DP is not better (Δ < 0, CI spans 0),
so under the plan's rule the simpler method wins.

The official evaluator reproduces the threshold result exactly:
`python -m ber.pipeline --stage evaluate --split train --tag m-v0-dev --folds 0 --set sample=dev` gives macro F0.5
0.96484, precision 0.988, recall 0.929, singleton F0.5 0.953, mean predicted per S1 3.26 (India 0.952, US 0.974).

## Consequences (what changes, what we give up, how we'll know it was right)

- **Changes:** stage 06 writes C9 matches with argmax ownership + threshold. The DP code stays in `decide.py`,
  unused, so G6 can be re-run cheaply.
- **Give up:** the per-entity set-size adaptivity of the DP. On this evidence it is worth nothing measurable.
- **Re-check:** re-run G6 on the full holdout (folds 0–4, ~550k S1) with the full features. Re-check again after
  stage 2 (G4) or softmax ownership (G5), because both change the probabilities the DP depends on.
- **We'll know it was right** if the full-holdout G6 again shows the CI spanning or below 0. If it shows
  Δ ≥ +0.002 with CI > 0, switch to the DP and supersede this record.
- **Test shift (G8):** the threshold was tuned on train density (4.68 S2/S3 per S1), and test has 5.75.
  A threshold or shift adjustment for test is G8's decision, not this one.
