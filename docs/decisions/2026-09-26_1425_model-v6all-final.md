# Decision: model-v6all-final

- **Date (IST):** 2026-09-26 14:25
- **Author:** ameya
- **Status:** accepted (holdout gate passed). The captain decides the uploads.
- **Affects:** the final candidate (`submissions/files/2026-09-26-v6all-ops-c2/`), `experiments/ameya/model-v1/RECIPE.md`

## Context

v6all bundles the round-1 solutions (`RESEARCH_v5.md` §8):
- blocking v3 repairs (domain/handle segmentation, OCR repair, ordinal street words);
- the signed house-number features (`nx`);
- the candidate cut (p1 ≥ 0.02, the record's top 2 S1);
- France rules v2.

It was rebuilt end to end:
- blocking `ameya-block-v3`;
- features `ameya-fx5` (str, cx, nx, lo, lg, lop, lo0) and a new cross-encoder;
- stages 1/2 `--all`;
- decision, candidate set, rules.

## Options considered

| | v5all-c2 (current final's model) | **v6all-c2** |
|---|---|---|
| holdout blocking pair recall | 0.98992 | **0.99135** (missed 19,163 → 16,455) |
| blocking candidate pairs (train) | 66.8M | 66.4M |
| stage 1 holdout (best threshold) | 0.9870 | **0.9878** |
| cross-encoder out-of-fold AUC (uncertain band) | | 0.919 |
| stage 2 holdout (pc, threshold 0.70) | | 0.9908 |
| **holdout macro F0.5 (decision)** | 0.990156 | **0.990788** (US 0.99065, India 0.99100) |
| precision / recall | 0.9988 / 0.9713 | 0.9987 / **0.9738** |
| gate vs v5all-c2 (paired bootstrap) | | **Δ +0.00063 [+0.00057, +0.00070]**, p_better 1.0; US +0.00068, India +0.00056 |
| decision rule (G6) | expected-F0.5 DP | threshold 0.70 (the DP is +0.00004 [−0.00001, +0.00008]; ties go to the threshold) |
| candidates per test S1 (US / India / France) | 3.66 / 3.61 / 4.09 | 3.64 / 3.62 / 4.10 (all 3.70) |
| France rules | 19,503 dropped; A 7,227 / APP 3,877 / ACR 853 | 20,168 dropped; A 3,622 / APP 2,955 / ACR 670 (the model now accepts more true copies itself) |
| final predictions per test S1 (US / India / France) | 3.382 / 3.367 / 3.336 | 3.390 / 3.376 / 3.360 |
| package | `2026-09-26-v5all-ops2-c2`, matching `76fe7eff…` | `2026-09-26-v6all-ops-c2`, matching `0f6d8985…`, candidates `cc3750d0…` |

## Decision

- **v6all + rules v2 + the cut is the final candidate:** `2026-09-26-v6all-ops-c2` (validator PASS).
- `2026-09-26-v5all-ops2-c2` stays as the fallback.
- The blocking v3 repairs are accepted at full scale (`2026-09-26_1122_blocking-v3-repairs.md`).

## Consequences (what changes, what we give up, how we'll know it was right)

- Expected leaderboard gain over v5all-ops2-c2: about +0.0005 from US/India (0.85 × 0.00063), plus France's share of the same improvements (unmeasured).
- The candidate file stays at 3.70 pairs per S1.
- **Right if** the leaderboard of v6all-ops-c2 ≥ v5all-ops2-c2.
- **Wrong if** it drops. Then France reacts differently to the new blocking/features: upload the fallback.

Commands: `experiments/ameya/model-v1/RECIPE.md` (v6all section; the chain is `run_v6all.sh`, resumable per step).
