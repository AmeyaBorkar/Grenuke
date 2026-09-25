# Status: ameya

- **Last updated (IST):** 2026-09-26 05:25
- **Current focus:** research (`experiments/ameya/model-v1/RESEARCH_v5.md`).
  - Part 1 done:
    - the leaderboard gap is France alone;
    - the holdout is recall-bound (empty-address records with shared names);
    - the candidate set can shrink 21% at no cost.
  - Part 2 running: ground-truth structure and joint decoding, preprocessing, France residuals.
- **Branch(es):** `ameya/research-v5`. It carries:
  - v5: French address normalisation, EI as a legal form;
  - the `--all` final fit;
  - `post_ops.py` (France rules);
  - `ANALYSIS_v4.md`, `RESEARCH_v5.md`, `gap_check.py`, `cand_size.py`.

  `ameya/analysis-v3` is superseded.
- **Leaderboard vs holdout:**

  | model | holdout | leaderboard | gap | France implied |
  |---|---|---|---|---|
  | v2 (Sub 3) | 0.98436 | 0.97608 | −0.0083 | 0.927–0.944 |
  | v3 | 0.98882 | 0.97961 | −0.0092 | 0.925–0.931 |
  | v4 | 0.99015 | | | |
  | v5all + rules (final candidate) | 0.99016 | | | |

  For v4 and later: LB ≈ 0.8423 + 0.14975 × F_France, so F_France = (LB − 0.8423) / 0.14975.
- **Ready to upload** (validator PASS), in this order:
  1. `submissions/files/2026-09-26-v4/`: the anchor.
  2. `submissions/files/2026-09-26-probe-v4-frab/`: v4 + the France rules; minus (1) = the rules alone, expected +0.0027.
  3. `submissions/files/2026-09-26-v5all-ops/`: the current final candidate; matching sha256 `f8b6245f…`.
  4. Optional:
     - `2026-09-26-probe-v4-fr0/` (France emptied): F_France = (LB_v4 − LB_fr0) / 0.14975 + 0.0559;
     - `2026-09-26-probe-v5-frab/`;
     - `2026-09-26-probe-v4-in0/`.
- **Candidate set:** the organisers rank a smaller `candidate_pairs.tsv` per S1 higher. Next build: stage-2 input = p1 ≥ 0.02 and each record's top 2 S1 (4.68 → 3.70 per S1, holdout unchanged).
- **Deadline:** the submission-round page says the window closes 27 Sep 15:30 UTC = **21:00 IST**, and the private leaderboard uses the **final** submission. To be confirmed in the logged-in portal.
- **ETA for the current task:**
  - research part 2 by about 07:30;
  - then the candidate-cut build (about 1 h).
- **Blocked on / need from others:** the captain's uploads and their scores.
- **Latest handover:** `docs/handover/2026-09-26_0520_ameya_research-gap-candidates.md`.
- **Next up:**
  - research part 2 and the plan;
  - the candidate cut;
  - then the fixes the research ranks highest.
