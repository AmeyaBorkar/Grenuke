# Status: ameya

- **Last updated (IST):** 2026-09-26 06:00
- **Current focus:** solutions phase (`experiments/ameya/model-v1/RESEARCH_v5.md`: part 2 and the ranked plan in §7).
  - Research done:
    - US/India are at the Bayes limit;
    - formats are not a loss source;
    - France is about 0.959 with v5all + rules (leaderboard about 0.985).
  - The candidate set is cut to 3.70 per S1.
  - Running: signed number features (v6nx). Next:
    - France patterns a–e in `post_ops.py`;
    - research on France weak-address and unrelated-name acceptance.
- **Branch(es):** `ameya/cands-cut`:
  - candidate cut (`common.candidate_mask`, `decide.py`/`cands_final.py --p-cand/--top-r`);
  - research part 2.

  `ameya/research-v5` is merged (#24).
- **Leaderboard vs holdout:**

  | model | holdout | leaderboard | gap | France implied |
  |---|---|---|---|---|
  | v2 (Sub 3) | 0.98436 | 0.97608 | −0.0083 | 0.927–0.944 |
  | v3 | 0.98882 | 0.97961 | −0.0092 | 0.925–0.931 |
  | v4 | 0.99015 | | | |
  | v5all + rules (final candidate) | 0.99016 | | | |

  For v4 and later: LB ≈ 0.8423 + 0.14975 × F_France, so F_France = (LB − 0.8423) / 0.14975.

  France estimated from structural profiles (checked against v2/v3):
  - v4 0.946 (LB about 0.984);
  - v5all + rules 0.959 (LB about 0.985).
- **Ready to upload** (validator PASS), in this order:
  1. `submissions/files/2026-09-26-v4/`: the anchor.
  2. `submissions/files/2026-09-26-probe-v4-frab/`: v4 + the France rules; minus (1) = the rules alone, expected +0.002.
  3. `submissions/files/2026-09-26-v5all-ops-c2/`: **the final candidate**: v5all + rules with the smaller candidate set, 3.70 per S1; matching sha256 `482caa7b…`.
     - It supersedes `2026-09-26-v5all-ops`, which has the same predictions except 742 pairs and 4.68 candidates per S1.
  4. Optional:
     - `2026-09-26-probe-v4-fr0/` (France emptied): F_France = (LB_v4 − LB_fr0) / 0.14975 + 0.0559;
     - `2026-09-26-probe-v5-frab/`;
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
