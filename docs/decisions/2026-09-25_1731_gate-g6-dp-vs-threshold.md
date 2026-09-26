# Decision: gate-g6-dp-vs-threshold

- **Date (IST):** 2026-09-25 17:31 (numbers updated 17:52 after the ownership fix)
- **Author:** sachi
- **Status:** accepted for v0 (dev-sample evidence); re-check on the full holdout when full features exist
- **Affects:** stage 06 decide (C9 matches); `ber.model` decide code

## Context

FINAL_PLAN §9, gate G6: does the exact expected-F0.5 decision per S1 beat one tuned global threshold?
Both rules run on the same calibrated probabilities (stage-1 XGBoost, 3 OOF groups from `ber.eval.oof_group`,
isotonic calibration cross-fitted on OOF), after per-record argmax ownership.

- **Ownership:** computed over every S1 candidate of each record, training folds included, as on test.
  Only pairs owned by holdout S1s are evaluated. An earlier run took the argmax over holdout S1s only;
  it was fixed before these numbers were produced.
- **Data:** dev kit `devkit-v0`, features `ameya-baseline-v0-dev` (37 features, C8).
  Trained on dev-sample folds 5/10/15 (2,393,231 pairs); evaluated on dev-sample fold 0 (27,651 S1).
- **Baseline tag / candidate tag:** `m-v0-dev` (threshold) vs `m-v0-dev` (DP), same scores.
- **Test:** `ber.eval.paired_bootstrap` over S1 entities, 1,000 resamples.
- **Keep rule (plan §5.4):** Δ ≥ +0.002 and the 95% CI above 0. Ties go to the threshold.

## Options considered

1. **Tuned global threshold** on calibrated p: best t = 0.70, holdout macro F0.5 **0.9649**.
2. **Exact expected-F0.5 per S1:** Poisson-binomial DP over prefix sizes, with one global logit shift b tuned on the
   same holdout. Best b = −0.25, holdout macro F0.5 **0.9647**. The DP was checked against brute-force enumeration
   (40 random cases) in `test_decide.py`.

**Gate result (C10):** delta −0.00024, ci_low −0.00091, ci_high +0.00049, p_better 0.234, n 27,651.

## Decision

Keep the **tuned global threshold** (t = 0.70) as the v0 decision rule. The DP is not better (Δ < 0, CI spans 0).

The official evaluator reproduces the threshold result exactly:
`python -m ber.pipeline --stage evaluate --split train --tag m-v0-dev --folds 0 --set sample=dev` gives macro F0.5
0.96492, precision 0.988, recall 0.929, singleton F0.5 0.953, mean predicted per S1 3.26 (India 0.952, US 0.974).

## Consequences (what changes, what we give up, how we'll know it was right)

- **Changes:** stage 06 writes C9 matches with argmax ownership (over all S1) + threshold. The DP code stays,
  unused, so G6 can be re-run cheaply.
- **Give up:** the per-entity set-size adaptivity of the DP. On this evidence it is worth nothing measurable.
- **Re-check:** re-run G6 on the full holdout (folds 0–4) with the full features, and again after stage 2 (G4) or
  softmax ownership (G5), because both change the probabilities the DP depends on.
- **We'll know it was right** if the full-holdout G6 again shows the CI spanning or below 0. If it shows
  Δ ≥ +0.002 with CI > 0, switch to the DP and supersede this record.
- **Test shift (G8):** the threshold was tuned on train density (4.68 S2/S3 per S1), and test has 5.75.
  Any threshold or shift adjustment for test is G8's decision.

## Update 18:00: through the pipeline stages (`ber.model`)

`--stage train/predict/decide` on `--in features=ameya-baseline-v0-dev`, tag `sachi-model-v0-dev`, team default seed:
threshold 0.71, holdout macro F0.5 0.96517 (evaluate stage agrees), DP 0.96473.
G6: delta −0.00044, CI [−0.00107, +0.00022], p_better 0.101, n 27,651, so the threshold is kept. Same decision.

## Update 20:55: on model v2 probabilities (dev kit v2, `pc`)

Decide stage on `ameya-s2-v2-dev` calibrated `pc` (tag `sachi-decide-v2`), dev fold 0, 27,651 S1:
threshold 0.67 -> 0.98438 (evaluate stage agrees; matches Ameya's reported 0.9845); DP 0.98447.
G6: delta +0.00010, CI [−0.00023, +0.00045], p_better 0.714. Below the +0.002 bar, so the threshold is kept.
With stronger probabilities the DP moved from slightly worse to slightly better. Re-check after G5 and on the full holdout.
