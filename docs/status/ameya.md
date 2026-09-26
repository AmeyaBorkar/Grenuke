# Status: ameya

- **Last updated (IST):** 2026-09-26 23:45
- **Current focus:** France, the only gap left (`RESEARCH_v6.md` §6).
  - v6all scored **0.988609**. The US/India part is 0.8429 (re-weighted holdout), so France is about **0.973**, 0.018 below US/India. US/India have about +0.0003 left.
  - **v7nst scored 0.990179 (rank 7)**: self-training on France works (France about 0.981). v7n scored 0.989721 (rank 8).
  - At 21:00, 0.99+ was the top 7; the top 3 were 0.99074 / 0.99052 / 0.99033 at 20:00.
- **Branch(es):** `ameya/squeeze` (this round, PR open). #35–#41 merged.
- **Leaderboard vs holdout:**

  | model | holdout | leaderboard | France implied |
  |---|---|---|---|
  | v2 / v3 | 0.98436 / 0.98882 | 0.97608 / 0.97961 | 0.93 |
  | v5all + rules v2 + cut (26 Sep #01) | 0.99016 | 0.98781 | 0.971 |
  | **v6all + stage 3 + rules v3 + acronym join** | 0.99084 | **0.988609** | **0.973** |
  | v7ce3 (e5-small/base/large) | 0.99114 | | |
  | **v7n** (e5-small + mean of two e5-large) | **0.99121** | **0.989721 (rank 8)** | **0.978** |
  | **v7nst** (v7n + France stage-2 self-training) | 0.99119 | **0.990179 (rank 7)** | **0.981** |

  LB = 0.843226 + 0.14975 × F_France for v7n; the same formula gives v6all's actual score exactly.

- **France, label-free** (§6.8): AUC of pc on the rule populations, whose truth is known from US/India.
  - v6all 0.855 → v7ce3 0.865 → **v7n 0.872** (v7m, lost with the box: 0.878).
  - The cross-encoders are what fix France. On French pairs they disagree 4× as often as on US/India (§6.6), so v7n feeds stage 2 their mean.
- **Ready to upload** (validator PASS, all in `submissions/files/`):
  1. **`2026-09-27-v7n-s3-ops3a-c2`**: the candidate. Matching `9b902971…`, candidates `7246d9ec…`.
  2. `2026-09-27-probe-v7n-fr090r`: France's model predictions below pc 0.9 dropped before the rules (70 per 1000 French S1); the rules re-add their true copies. It prices France's unexplained uncertain band. Matching `f18f0898…`.
  3. `2026-09-27-probe-v7n-fr095r`, `-fr080r`: follow-ups to #2 (a stronger or a milder cut).
  4. **`2026-09-27-v7nst-s3-ops3a-c2`**: v7n + stage-2 self-training on France (validator PASS, matching `659f5169…`). It changes 31 per 1000 French final predictions (+14.0 / −17.4) and leans toward precision. The leaderboard decides.
  5. Fallbacks:
     - `2026-09-27-v7ce3-s3-ops3a-c2` (`671dca1e…`);
     - `2026-09-26-v6all-s3-ops3a-c2` (0.988609).
- **Upload plan for 27 Sep** (5 slots; the final submission counts, so the best must also be the last upload):
  1. **v7s**: the France self-trained e5-large + bge in the mean + stage-2 self-training (built tonight, about 02:30).
  2. **v7nst2**: round-2 self-training (labels from v7nst), or **v7mst** (bge + self-training). Whichever the French rule check ranks higher.
  3. `fr090r` on the best so far (built for v7n and v7nst; about 5 minutes for any other).
  4. A follow-up: `fr095r` or `fr080r`, or the remaining variant.
  5. The best, re-uploaded last.
- **Deadline:** the window closes 27 Sep **21:00 IST**, and the private leaderboard uses the final submission.
- **Vast.ai:** the first box (a spot instance) was outbid at 21:40 and destroyed. A new on-demand H100 (`grenuke-vast`, key `grenuke_vast2`) runs bge and the self-trained e5-large. Lost with the first box:
  - bge's logits;
  - v7m/v7c scores;
  - the self-trained e5-large run.

  Traffic so far about 24 GB of the 30 GB cap.
- **Blocked on / need from others:** the captain's uploads and their scores.
- **Latest handover:** `docs/handover/2026-09-26_2049_ameya_squeeze-v7n.md`.
- **Next up:** read tomorrow's scores against the plan above. The France probes decide the France threshold for the final.
