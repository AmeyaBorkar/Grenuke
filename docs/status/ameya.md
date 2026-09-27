# Status: ameya

- **Last updated (IST):** 2026-09-27 05:20
- **Current focus:** the 5 uploads of 27 Sep. The window closes **21:00 IST**; the final upload counts, so the chosen best goes up last.
- **Branch(es):** `ameya/final-stack` (the stacked rules `experiments/ameya/model-v1/stack/`, RESEARCH_v6.md §6.16, an `fhs.py` fix, this file). #35–#57 merged.
- **Leaderboard vs holdout:**

  | model | holdout (s3) | leaderboard | France implied |
  |---|---|---|---|
  | v5all + rules v2 + cut (26 Sep #01) | 0.99016 | 0.98781 | 0.971 |
  | v6all + stage 3 + rules v3 + acronym join | 0.99084 | 0.988609 | 0.973 |
  | v7n (e5-small + mean of two e5-large) | 0.99121 | 0.989721 | 0.978 |
  | **v7nst** (v7n + France stage-2 self-training) | 0.99119 | **0.990179 (rank 7; now 13)** | **0.981** |

  LB = US/India part + 0.14975 × F_France; US/India part 0.843210 for v7nst.

- **Models** (`final_memo.py`, against v7nst):

  | model | holdout (s3) | US/India part | France changes per 1000 S1 | `fhs.py` per 1000 |
  |---|---|---|---|---|
  | v7nst (uploaded) | 0.991194 | 0.843210 | — | — |
  | v7mst (+ bge) | 0.991206 | 0.843223 | +2.7 / −5.3 | −0.56 |
  | **v7s** (e5l + French self-trained e5-large + bge) | **0.991229** | **0.843247** | +7.1 / −9.5 | +0.02 |
  | v7sb (v7s with bge replaced by its French self-trained version) | 0.991226 | 0.843241 | +12.0 / −11.1 | +0.33 |

- **Upload candidates** (`submissions/files/`, validator PASS; `stack/stack.sh <model>` builds them):

  | package | US/India rules (holdout on v7s) | France rules | `fhs` vs v7nst | notes |
  |---|---|---|---|---|
  | **`2026-09-27-v7s-s3-ops3a-dpc-c2`** | expected-F0.5 + crowd shift + acr + cap: **+48.1e-6 [+7.1, +91.2]** | +16 acronym copies, +332 exact copies, −89 cross-commune | +1.11 | **recommended first upload**; strict audit PASS |
  | `2026-09-27-v7sb-s3-ops3a-dpc-c2` | same rule | same kind (+254 / −83) | +1.13 | level with v7s |
  | `2026-09-27-v7nst-s3-ops3a-dpc-c2` | same rule (not gated on v7nst: DP part +34.0e-6) | +417 / −140 | +1.43 | fallback if v7s's French changes hurt |
  | `-h2pc` versions | threshold + acr + cap + nsa: +9.4e-6 [+1.7, +17.5] | same | same | the conservative US/India rules |

- **Coming (automatic):** v7sq (+ Qwen) about 06:10; v7ensall, v7sq2, v7ensall2 by about 08:15; v7s2 (a second seed of the French e5-large) about 09:05. Each gets the same stack.
- **Upload plan for 27 Sep** (5 slots, no pure probes; the LB resolves gaps of about ±0.00004 between these candidates only):
  1. `v7s-dpc` (best expected value; a LB far below about 0.9902 would flag a French regression).
  2. and 3. The best of v7sq / v7ensall / v7s2 stacks, as they land.
  4. Flexible.
  5. The chosen best, uploaded last.
- **Crash and memory:** the integration laptop froze at 03:35 (memory) and rebooted; at 04:46 the memory reaper killed the background wrappers, but every script survived. Nothing was lost (§6.16).
- **Vast.ai:** `grenuke-vast` runs the second e5-large seed; it **stops itself** once that output is fetched (about 06:40). Destroy it in the console after the competition.
- **Blocked on / need from others:** the captain's uploads and their scores; Bakshi: the `stack/stack.sh` step in `reproduce.sh`.
- **Latest handover:** `docs/handover/2026-09-27_0706_ameya_final-stack.md`.
