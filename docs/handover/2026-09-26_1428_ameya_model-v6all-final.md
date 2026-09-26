# Handover: model-v6all-final

- **Author:** ameya (agent: Claude Code)
- **When (IST):** 2026-09-26 14:28
- **Branch / PR / last commit:** `ameya/model-v6all` / PR opened with this handover / see `git log`
- **Area and paths touched:**
  - `docs/decisions/2026-09-26_1425_model-v6all-final.md`;
  - `docs/decisions/2026-09-26_1122_blocking-v3-repairs.md` (status);
  - `experiments/ameya/model-v1/RESEARCH_v5.md` §8.5, `RECIPE.md` (status);
  - status.

## TL;DR (3 lines max)

- The v6all rebuild (blocking v3 + signed number features + cut + France rules v2) passes its gate: holdout 0.990788 vs 0.990156, +0.00063 [0.00057, 0.00070].
- It is the new final candidate `2026-09-26-v6all-ops-c2` (validator PASS, 3.70 candidates per S1).
- France's level still needs `probe-v4-fr0`.

## What was done

- **Full rebuild, 11:30–14:27** (`run_v6all.sh`, resumable per step; heavy steps wait for free memory).
- **Claude Code's low-memory reaper** stopped the harness's handle on the chain once while the session was idle. The chain's processes kept running.
- **Blocking v3 at full scale:** holdout pair recall 0.98992 → 0.99135 (missed 19,163 → 16,455), 0.6% fewer pairs.
- **Models:**
  - stage 1 0.9878 (v5all 0.9870);
  - cross-encoder out-of-fold AUC 0.919;
  - stage 2 0.9908 at threshold;
  - G6 picks a threshold of 0.70 (the DP +0.00004, not significant).
- **France rules v2 on v6all:** 20,168 look-alike drops; adds A 3,622, APP 2,955, ACR 670.
- **France kit** for Sachi (`work/kits/france-kit-v1`, #31); reproduction answers (#29).

## Current state

- **Works:** everything above.
- **Half-done:** nothing running.
- **Known bugs and caveats:**
  - France's level is unmeasured.
  - v6all accepts slightly more in France (3.360 vs 3.336 per S1 after the rules).

## Numbers (shared holdout, `ber.eval`; include the command)

| metric | value | command / tag |
|---|---|---|
| v6all-c2 vs v5all-c2 | 0.990788 vs 0.990156, Δ +0.00063 [0.00057, 0.00070]; US +0.00068, India +0.00056 | `decide.py --scores ameya-s2-v6all --tag ameya-model-v6all-c2 --base ameya-model-v5all-c2 --p-cand 0.02 --top-r 2` |
| blocking recall, holdout | 0.98992 → 0.99135 | `ameya-block-v2` vs `ameya-block-v3` |
| runtime | about 3 h end to end (blocking 32 min, features 60 min, s1 16 min, CE 35 min, s2 24 min) | `run_v6all.sh` |

## How to reproduce or continue (exact commands)

See `experiments/ameya/model-v1/RECIPE.md` (v6all section).

## Artifacts (local paths / drive links + sha256)

- `submissions/files/2026-09-26-v6all-ops-c2/`:
  - matching `0f6d8985be05877276e16a4d95562d8d72f36c38f962441f1a6f9928d22890be`;
  - candidates `cc3750d0c38e7d7863576fb1550668471cd65ad17b66187e8d457e5cf9dceaae`.
- Fallback: `2026-09-26-v5all-ops2-c2` (`76fe7eff…`).
- Probes: `2026-09-26-v4` (`cd09df65…`) and `2026-09-26-probe-v4-fr0` (`36247a77…`).

## Next steps (ordered, with suggested owner)

1. Captain: upload `v6all-ops-c2`, then `v4` + `probe-v4-fr0`.
2. ameya/Sachi: if France < 0.95, French pattern work (the kit); otherwise small items (stage 3, rule adds outside the candidate set).

## Blockers, open questions, decisions needed

- The captain's uploads.
