# Decision: model-v3-end-to-end

- **Date (IST):** 2026-09-25 23:28
- **Author:** ameya
- **Status:** accepted as the candidate for the next upload (the captain decides the upload)
- **Affects:** the whole chain: blocking v2 → features v3 (`ameya-fx3`: str, cx, lo, lg) → stage 1 `ameya-s1-v3` → stage 2 `ameya-s2-v3` → decision `ameya-model-v3`

## Context

Model v2 (Submission 3) scores 0.98436 on the holdout. The v2 error analysis (`experiments/ameya/model-v1/ANALYSIS_v2.md`) led to three changes, each gated on its own:
- **legal-form features:** `2026-09-25_2142_gate-legal-form-features.md`, +0.00271 in stage 2 alone;
- **blocking v2:** `2026-09-25_2142_gate-g1-blocking-v2.md`, pair recall 0.9857 → 0.9899;
- **the (number, street) context key fix:** merged in PR #18, used from v3 on.

v3 rebuilds everything on those and adds the legal features to stage 0/1 as well.

## Options considered

1. Model v2lg: v2 features + legal features in stage 2 only; 0.98708.
2. **Model v3**: full rebuild.

## Decision

**Model v3.** Shared holdout (549,699 S1), paired bootstrap with 1,000 resamples.

| stage (holdout macro F0.5) | v2 | v3 |
|---|---|---|
| stage 0: share of pairs kept at 99.95% positive recall | 0.176 | **0.154** |
| stage 1, best threshold | 0.9820 | **0.9871** |
| stage 2, best threshold | 0.9842 | **0.9887** |
| **model (expected F0.5 decision)** | 0.98436 | **0.98882** |

- US 0.98891, India 0.98868; precision 0.99833, recall 0.96893; singletons 0.99126.
- **Gate vs model v2: Δ +0.00445, 95% CI [0.00431, 0.00459].**
- Stage-1 early-stopping log-loss fell 0.059–0.061 → 0.050–0.052.
- G6 re-check (expected F0.5 vs threshold 0.650): +0.00011 [0.00005, 0.00017]. The DP is kept, shift 0.

**The model's own forecast of macro F0.5** (the mean of the DP's expected F0.5 per S1):

| | forecast | real |
|---|---|---|
| holdout | 0.99139 | 0.98882 |

The forecast is 0.0026 optimistic because it cannot see true pairs outside the candidates.

Test forecast: US 0.99141, India 0.99157, **France 0.97001**, all 0.98828. The model is far less certain on France.

**Test diagnostics** (predicted records per S1 / empty share):

| | holdout | test |
|---|---|---|
| US | 3.357 / 5.8% | 3.380 / 5.8% |
| India | 3.356 / 5.7% | 3.358 / 5.8% |
| France | | 3.539 / 4.4% |

## Consequences (what changes, what we give up, how we'll know it was right)

- **Submission package:** `submissions/files/2026-09-26-v3/`. The validator result and sha256 are in the handover; `output/` still holds Submission 3.
- **What would show it was right:** the leaderboard score of v3 minus Submission 3 should be about the holdout gap (+0.0045) or more. The test has more look-alikes, where the legal features act.
- **France is the main risk.** Its forecast is 0.02 below US/India, which argues for the G7 probe.
