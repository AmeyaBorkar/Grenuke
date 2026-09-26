# Status: ameya

- **Last updated (IST):** 2026-09-26 14:35
- **Current focus:** v6all is the final candidate.
  - Holdout 0.990788 vs 0.990156, +0.00063 [0.00057, 0.00070].
  - It combines blocking v3 repairs, signed number features, the 3.70-per-S1 candidate set and France rules v2.
  - Waiting on the uploads, and on `probe-v4-fr0` for France's level.
- **Branch(es):** `ameya/model-v6all` (v6all records, PR open). #24–#29 and #31 merged.
- **Leaderboard vs holdout:**

  | model | holdout | leaderboard | gap | France implied |
  |---|---|---|---|---|
  | v2 (Sub 3) | 0.98436 | 0.97608 | −0.0083 | 0.927–0.944 |
  | v3 | 0.98882 | 0.97961 | −0.0092 | 0.925–0.931 |
  | v4 | 0.99015 | | | |
  | v5all + rules (final candidate) | 0.99016 | | | |
  | v6nx (+ signed number features, 3 groups) | 0.99034 | | | |
  | **v6all + rules v2 + cut (final candidate)** | **0.99079** | | | |

  For v4 and later: LB ≈ 0.8423 + 0.14975 × F_France, so F_France = (LB − 0.8423) / 0.14975.

  **France's level is unknown** (`RESEARCH_v5.md` §8.2). The structural estimator's 0.959 rested on artifacts. `probe-v4-fr0` measures it: LB_fr0 = US/India part + 0.0084.
  - If US/India score like the holdout, LB_fr0 ≈ 0.8507.
  - France = (LB_v4 − LB_fr0) / 0.14975 + 0.0559.
- **Ready to upload** (validator PASS), in this order:
  1. `submissions/files/2026-09-26-v6all-ops-c2/`: **the final candidate**; matching sha256 `0f6d8985…`, candidates `cc3750d0…`; 3.70 per S1.
  2. `submissions/files/2026-09-26-v4/` (`cd09df65…`) and `2026-09-26-probe-v4-fr0/` (`36247a77…`): France's level. LB_fr0 ≈ 0.8507 if US/India match the holdout; France = (LB_v4 − LB_fr0) / 0.14975 + 0.0559.
  3. Fallback: `2026-09-26-v5all-ops2-c2/` (`76fe7eff…`).
- **Candidate set:** the organisers rank a smaller `candidate_pairs.tsv` per S1 higher. Done: p1 ≥ 0.02 and each record's top 2 S1 (4.68 → 3.70 per S1, holdout tie). Decision record `2026-09-26_0532`.
- **Deadline:** the submission-round page says the window closes 27 Sep 15:30 UTC = **21:00 IST**, and the private leaderboard uses the **final** submission. To be confirmed in the logged-in portal.
- **ETA for the current task:** done; the next steps depend on the France probe.
- **Blocked on / need from others:** the captain's uploads and their scores.
- **For Sachi (French pattern discovery):** `work/kits/france-kit-v1/` (209 MB, on the team drive), from `experiments/ameya/model-v1/france_kit.py`. Take truth rates from the `*_rule_pairs` files: the stage-2 set is selection-biased.
- **For Sachi (final package):** `experiments/ameya/model-v1/RECIPE.md` answers the five reproduction questions and gives the exact v6all and v5all recipes. `decide.py --base` is now optional, and `feats.py --dict-only` builds blocking's Indic dictionary.
- **Latest handover:** `docs/handover/2026-09-26_1428_ameya_model-v6all-final.md`.
- **Next up:**
  - read the uploads (France level);
  - if France < 0.95, French pattern work with Sachi's kit findings;
  - optional: stage 3 on v6all (+0.00005), and rule adds outside the candidate set.
