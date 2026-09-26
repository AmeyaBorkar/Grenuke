# Status: ameya

- **Last updated (IST):** 2026-09-27 02:45
- **Current focus:** the 5 uploads of 27 Sep. The window closes **21:00 IST**; the final upload counts, so the chosen best goes up last.
- **Branch(es):** `ameya/final-day` (RESEARCH_v6.md §6.14, `fhs.py`, this file). #35–#53 merged.
- **Leaderboard vs holdout:**

  | model | holdout (s3) | leaderboard | France implied |
  |---|---|---|---|
  | v5all + rules v2 + cut (26 Sep #01) | 0.99016 | 0.98781 | 0.971 |
  | v6all + stage 3 + rules v3 + acronym join | 0.99084 | 0.988609 | 0.973 |
  | v7n (e5-small + mean of two e5-large) | 0.99121 | 0.989721 | 0.978 |
  | **v7nst** (v7n + France stage-2 self-training) | 0.99119 | **0.990179 (rank 7)** | **0.981** |

  LB = US/India part + 0.14975 × F_France; US/India part 0.843210 for v7nst.

- **Candidates** (validator PASS, `submissions/files/`), against v7nst:

  | package | France changes per 1000 S1 | net true copies (`fhs.py`) | US/India part | verdict |
  |---|---|---|---|---|
  | `2026-09-27-v7nst-s3-ops3a-c2` | uploaded | — | 0.843210 | **best so far; fallback** |
  | `2026-09-27-v7mst-s3-ops3a-c2` (+ bge) | +2.7 / −5.3 | −0.85 | 0.843223 | ≈ v7nst |
  | `2026-09-27-v7ens2-s3-ops3a-c2` | +2.0 / −4.4 | −0.65 | 0.843210 | ≈ v7nst |
  | `2026-09-27-v7nst2-s3-ops3a-c2` (round 2) | +3.4 / −7.5 | −1.54 | 0.843202 | worse: round 2 drifts |
  | `frs2` variants | | −3.86 | | **withdrawn** (§6.14) |

- **Coming overnight (automatic):**
  - **v7s** (e5l + self-trained e5-large + bge): e5ls lands about 02:55, packaged about 04:00.
  - **v7sq** (+ self-trained Qwen2.5-1.5B): Qwen's group 0 OOF AUC is 0.9334 (gate 0.93). It finishes about 05:00; v7sq is packaged about 06:15.
  - **v7ensall** (bag of v7nst, v7mst, v7s, v7sq), then Bakshi's strict audits: about 07:30.
- **Upload plan for 27 Sep** (5 slots, no pure probes):
  1. The best-gated of v7s / v7sq, by US/India part, French changes and true copies.
  2. The other one.
  3. v7ensall.
  4. Flexible, decided by 1–3.
  5. The best so far, uploaded last.
- **Vast.ai:** on-demand H100 `grenuke-vast` (key `grenuke_vast2`) runs e5ls and Qwen. **Destroy it after Qwen's logits are fetched** (about 05:00).
- **Blocked on / need from others:** the captain's uploads and their scores.
- **Latest handover:** `docs/handover/2026-09-26_2049_ameya_squeeze-v7n.md`.
