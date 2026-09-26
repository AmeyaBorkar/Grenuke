# Status: ameya

- **Last updated (IST):** 2026-09-26 11:45
- **Current focus:** the v6all rebuild (running since 11:22, about 3.5 h), which bundles:
  - blocking v3 repairs (dev-pool forward recall 0.972 → 0.979);
  - signed number features (holdout +0.00021);
  - the candidate cut;
  - France rules v2.

  Stage 3 (+0.00005) is optional.
- **Branch(es):** `ameya/solutions-r1` (blocking v3 + `stage3.py` + research §8.3–8.5), PR open. `ameya/france-rules-v2` merged (#26).
- **Leaderboard vs holdout:**

  | model | holdout | leaderboard | gap | France implied |
  |---|---|---|---|---|
  | v2 (Sub 3) | 0.98436 | 0.97608 | −0.0083 | 0.927–0.944 |
  | v3 | 0.98882 | 0.97961 | −0.0092 | 0.925–0.931 |
  | v4 | 0.99015 | | | |
  | v5all + rules (final candidate) | 0.99016 | | | |
  | v6nx (+ signed number features, 3 groups) | 0.99034 | | | |

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
- **ETA for the current task:** v6all about 15:00 (gate vs v5all-c2, then package `2026-09-26-v6all-ops-c2`).
- **Blocked on / need from others:** the captain's uploads and their scores.
- **For Sachi (final package):** `experiments/ameya/model-v1/RECIPE.md` answers the five reproduction questions and gives the exact v6all and v5all recipes. `decide.py --base` is now optional, and `feats.py --dict-only` builds blocking's Indic dictionary.
- **Latest handover:** `docs/handover/2026-09-26_1123_ameya_solutions-round1.md`.
- **Next up:**
  - the v6all gate and package;
  - then, if time, stage 3 on v6all and the rule adds outside the candidate set (+0.00005 each).
