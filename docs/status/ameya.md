# Status: ameya

- **Last updated (IST):** 2026-09-27 09:20
- **Current focus:** the 5 uploads of 27 Sep. The window closes **21:00 IST**; the final upload counts, so the chosen best goes up last.
- **Branch(es):** `ameya/final-stack` (#58, ready for review: the stacked rules `experiments/ameya/model-v1/stack/`, RESEARCH_v6.md §6.16, the decision record, an `fhs.py` fix, this file). #35–#57 merged.
- **Leaderboard vs holdout:**

  | model | holdout (s3) | leaderboard | France implied |
  |---|---|---|---|
  | v5all + rules v2 + cut (26 Sep #01) | 0.99016 | 0.98781 | 0.971 |
  | v6all + stage 3 + rules v3 + acronym join | 0.99084 | 0.988609 | 0.973 |
  | v7n (e5-small + mean of two e5-large) | 0.99121 | 0.989721 | 0.978 |
  | **v7nst** (v7n + France stage-2 self-training) | 0.99119 | **0.990179 (rank 7; now 13)** | **0.981** |

  LB = US/India part + 0.14975 × F_France; US/India part 0.843210 for v7nst.

- **Models** (against v7nst):

  | model | cross-encoder mean | holdout (s3) | US/India part | `fhs` model alone | `fhs` with the stack (`-dpc`) |
  |---|---|---|---|---|---|
  | v7nst (uploaded) | e5l, e5l2 | 0.991194 | 0.843210 | — | +1.43 |
  | v7s | e5l, e5ls, bge | 0.991229 | 0.843247 | +0.02 | +1.11 |
  | v7sb | e5l, e5ls, bges | 0.991226 | 0.843241 | +0.33 | +1.13 |
  | **v7sq** | e5l, **qst**, e5ls, bge | **0.991246** | **0.843258** | **+1.24** | **+2.19** |
  | v7ensall | bag of the five above | 0.991239 | 0.843253 | | +1.94 |
  | v7sq3 | v7sq + e5ls2 | 0.991250 | 0.843265 | | +1.13 |
  | v7sq2 | e5l, qst, e5ls, bges | 0.991245 | 0.843256 | | +0.86 |
  | **v7ensall2** | bag of all seven | **0.991256** | **0.843266** | | +1.85 |

  e5ls/e5ls2: multilingual-e5-large self-trained on French pseudo-labels (MIT); bges: bge-reranker-v2-m3, the same (Apache-2.0); qst: Qwen2.5-1.5B LoRA, the same (Apache-2.0).

- **The stack** (RESEARCH_v6.md §6.16, `docs/decisions/2026-09-27_0636_stacked-rules.md`):
  - `-dpc` = US/India expected-F0.5 with a crowd shift + acr + cap (+48.1e-6 [+7.1, +91.2] on v7s) and French copy + city + number-dropped acronym copies.
  - `-h2pc` = the conservative US/India hunt rules (+9.4e-6) with the same France.
- **Upload plan for 27 Sep** (5 slots, no pure probes; protect the floor). All packages: validator and strict audit PASS.
  1. **`2026-09-27-v7sq-s3-ops3a-dpc-c2`** (the default final; matching sha `cdda9a2d…`). A score far below about 0.9902 would flag a French regression.
  2. **`2026-09-27-v7nst-s3-ops3a-dpc-c2`** (the rules on the uploaded model; sha `f3490125…`). Its French predictions differ from v7sq's by about 20 per 1000 S1, enough for the LB to show whether the new cross-encoders help France.
  3. and 4. Held in reserve.
  5. **The final, re-uploaded early enough that nothing is rushed:** v7sq-dpc, unless v7nst-dpc leads it by more than about 0.00008.
  - `v7ensall2-dpc` is out of contention: it ties v7sq on expected LB, ties go to the simpler option, and its seven bagged tags are not in `reproduce.sh`.
- **The gap to first place** (0.991483, +0.0013; we are 15th): if the leaders' US/India matches ours, their France F is about 0.990 against our 0.981–0.982. 97% of our French predictions have pc ≥ 0.99, so the gap is confident substitutions, out of reach of thresholds or rules today.
- **Done (08:25):** every model stacked and audited; the repo port of the stack reproduces the scratchpad outputs set for set (`PORT OK`), 115 tests pass. #58 is ready for review.
- **Crash and memory:** the integration laptop froze at 03:35 (memory) and rebooted. The memory reaper killed shell wrappers at 04:46 and 06:30, but every script survived. Nothing was lost (§6.16).
- **Vast.ai:** `grenuke-vast` was stopped at 06:21 after Qwen, bges and e5ls2 were fetched. Destroy it in the console after the competition.
- **Blocked on / need from others:** the captain's uploads and their scores; Ameya: send `Downloads/grenuke-for-bakshi-final/` to Bakshi (he builds the final zip from it). Bakshi's `reproduce.sh` (#56) now runs v7sq with the stack by default.
- **Latest handover:** `docs/handover/2026-09-27_0706_ameya_final-stack.md`.
