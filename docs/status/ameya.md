# Status: ameya

- **Last updated (IST):** 2026-09-26 06:30
- **Current focus:** solutions (`RESEARCH_v5.md` §7–8).
  - Done:
    - candidate cut (3.70 per S1);
    - France rules v2 (B/A/APP/ACR, checked on the holdout);
    - the France weak-address/unrelated families are profiling artifacts, not errors.
  - Running:
    - v6nx (signed number features; stage 1 +0.0004);
    - stage-3 joint re-scoring (agent);
    - next, the full rebuild with the blocking repairs (`ameya/block-v3`: dev-pool forward recall 0.972 → 0.979).
- **Branch(es):**
  - `ameya/france-rules-v2`: `post_ops.py` v2, research §8.1–8.2, decision record;
  - `ameya/block-v3`: blocking repairs (domains, OCR, ordinals), to be rebased and rebuilt;
  - `ameya/cands-cut`: merged (#25).
- **Leaderboard vs holdout:**

  | model | holdout | leaderboard | gap | France implied |
  |---|---|---|---|---|
  | v2 (Sub 3) | 0.98436 | 0.97608 | −0.0083 | 0.927–0.944 |
  | v3 | 0.98882 | 0.97961 | −0.0092 | 0.925–0.931 |
  | v4 | 0.99015 | | | |
  | v5all + rules (final candidate) | 0.99016 | | | |

  For v4 and later: LB ≈ 0.8423 + 0.14975 × F_France, so F_France = (LB − 0.8423) / 0.14975.

  **France's level is unknown** (`RESEARCH_v5.md` §8.2). The structural estimator's 0.959 rested on artifacts. `probe-v4-fr0` measures it: LB_fr0 = US/India part + 0.0084.
  - If US/India score like the holdout, LB_fr0 ≈ 0.8507.
  - France = (LB_v4 − LB_fr0) / 0.14975 + 0.0559.
- **Ready to upload** (validator PASS), in this order:
  1. `submissions/files/2026-09-26-v4/`: the anchor.
  2. `submissions/files/2026-09-26-probe-v4-fr0/` (France emptied): **the most informative upload**. It gives the US/India test level directly and, with (1), France exactly.
  3. `submissions/files/2026-09-26-v5all-ops2-c2/`: **the final candidate**: v5all + France rules v2 (B, A, APP, ACR) + the smaller candidate set, 3.70 per S1; matching sha256 `76fe7eff…`.
     - `2026-09-26-v5all-ops-c2` (`482caa7b…`) is the same with the first rules; the difference is the v2 rules in France.
  4. Optional:
     - `2026-09-26-probe-v4-frab/` (v4 + first rules);
     - `2026-09-26-v5all-ops-c2/` (first rules; minus (3) = the v2 rules);
     - `2026-09-26-probe-v4-in0/`.
- **Candidate set:** the organisers rank a smaller `candidate_pairs.tsv` per S1 higher. Done: p1 ≥ 0.02 and each record's top 2 S1 (4.68 → 3.70 per S1, holdout tie). Decision record `2026-09-26_0532`.
- **Deadline:** the submission-round page says the window closes 27 Sep 15:30 UTC = **21:00 IST**, and the private leaderboard uses the **final** submission. To be confirmed in the logged-in portal.
- **ETA for the current task:**
  - v6nx result about 07:00;
  - `post_ops` patterns a–e about 07:30.
- **Blocked on / need from others:** the captain's uploads and their scores.
- **Latest handover:** `docs/handover/2026-09-26_0554_ameya_research-part2-plan.md`.
- **Next up:**
  - France patterns a–e;
  - the v6nx gate;
  - research agents (France weak-address/unrelated families, stage 3);
  - blocking rebuild if time.
