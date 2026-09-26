# Status: ameya

- **Last updated (IST):** 2026-09-26 22:25
- **Current focus:** France, the only gap left (`RESEARCH_v6.md` §6).
  - v6all scored **0.988609**. The US/India part is 0.8429 (re-weighted holdout), so France is about **0.973**, 0.018 below US/India. US/India have about +0.0003 left.
  - The leaderboard has moved: **0.99+ is the top 7**, and we were 17th. The top 3 were 0.99074 / 0.99052 / 0.99033 at 20:00.
- **Branch(es):** `ameya/squeeze` (this round, PR open). #35–#41 merged.
- **Leaderboard vs holdout:**

  | model | holdout | leaderboard | France implied |
  |---|---|---|---|
  | v2 / v3 | 0.98436 / 0.98882 | 0.97608 / 0.97961 | 0.93 |
  | v5all + rules v2 + cut (26 Sep #01) | 0.99016 | 0.98781 | 0.971 |
  | **v6all + stage 3 + rules v3 + acronym join** | 0.99084 | **0.988609** | **0.973** |
  | v7ce3 (e5-small/base/large) | 0.99114 | | |
  | **v7n** (e5-small + mean of two e5-large; next candidate) | **0.99121** | predicted 0.9889 (France 0.973) / 0.9894 (0.976) / 0.9900 (0.980) | |

  LB = 0.843226 + 0.14975 × F_France for v7n; the same formula gives v6all's actual score exactly.

- **France, label-free** (§6.8): AUC of pc on the rule populations, whose truth is known from US/India.
  - v6all 0.855 → v7ce3 0.865 → **v7n 0.872** (v7m, lost with the box: 0.878).
  - The cross-encoders are what fix France. On French pairs they disagree 4× as often as on US/India (§6.6), so v7n feeds stage 2 their mean.
- **Ready to upload** (validator PASS, all in `submissions/files/`):
  1. **`2026-09-27-v7n-s3-ops3a-c2`**: the candidate. Matching `9b902971…`, candidates `7246d9ec…`.
  2. `2026-09-27-probe-v7n-fr090r`: France's model predictions below pc 0.9 dropped before the rules (70 per 1000 French S1); the rules re-add their true copies. It prices France's unexplained uncertain band. Matching `f18f0898…`.
  3. `2026-09-27-probe-v7n-fr095r`, `-fr080r`: follow-ups to #2 (a stronger or a milder cut).
  4. `2026-09-27-v7nst-s3-ops3a-c2` (if built tonight): v7n + stage-2 self-training on France. Pseudo-labels come from v7ce3's decisions, cross-fitted; the holdout cannot score France.
  5. Fallbacks:
     - `2026-09-27-v7ce3-s3-ops3a-c2` (`671dca1e…`);
     - `2026-09-26-v6all-s3-ops3a-c2` (0.988609).
- **Upload plan for 27 Sep** (5 slots; the final submission counts, so the best must also be the last upload):
  1. v7n.
  2. `probe-v7n-fr090r`. If it beats v7n, try `fr095r` next; if not, `fr080r`.
  3. v7nst (the self-training bet), if built. Keep it if it beats v7n.
  4. A follow-up from 2 or 3.
  5. The best of the above, re-uploaded last.
- **Deadline:** the window closes 27 Sep **21:00 IST**, and the private leaderboard uses the final submission.
- **Vast.ai box:** a spot instance, interrupted at 21:40. Lost with it:
  - bge's logits;
  - v7m/v7c scores;
  - the self-trained e5-large run.

  If it comes back with its disk, v7m can be rebuilt from 20 MB of logits. Traffic so far about 15 GB of the 30 GB cap.
- **Blocked on / need from others:** the captain's uploads and their scores.
- **Latest handover:** `docs/handover/2026-09-26_2049_ameya_squeeze-v7n.md`.
- **Next up:** read tomorrow's scores against the plan above. The France probes decide the France threshold for the final.
