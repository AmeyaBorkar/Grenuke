# Status: ameya

- **Last updated (IST):** 2026-09-26 19:55
- **Current focus:** where the rest of the leaderboard is (`RESEARCH_v6.md`).
  - 26 Sep #01 (v5all + rules v2) scored **0.98781 (rank 15)**. Top 3: 0.990556 / 0.989141 / 0.988842.
  - The other session's gap budget, checked on v6all:
    - the extra US predictions on test are mostly correct (a half-size pool resolves more ties);
    - crowding is ≤ 0.0001.
  - France's level hangs on US/India's test level: about 0.971 if they score like the holdout, about 0.987 if they sit 0.002 below. The France-emptied probe decides.
  - New label-free findings:
    - France's pc is overconfident (Σ pc per S1 3.55 > 3.46);
    - France's blocking is clean;
    - rules v3 closes an address-parsing gap (about 1,291 look-alikes);
    - stage 3 on v6all is +0.000055.
  - Next candidate: `2026-09-26-v6all-s3-ops3-c2`, expected about 0.9885.
- **Branch(es):** `ameya/research-v6` (this round, PR open). #24–#33 merged.
- **Leaderboard vs holdout:**

  | model | holdout | leaderboard | gap | France implied |
  |---|---|---|---|---|
  | v2 (Sub 3) | 0.98436 | 0.97608 | −0.0083 | 0.927–0.944 |
  | v3 | 0.98882 | 0.97961 | −0.0092 | 0.925–0.931 |
  | v4 | 0.99015 | | | |
  | v5all + rules (final candidate) | 0.99016 | | | |
  | v6nx (+ signed number features, 3 groups) | 0.99034 | | | |
  | **v5all + rules v2 + cut** (26 Sep #01) | 0.99016 | **0.98781 (rank 15)** | −0.0024 | **0.971–0.976** |
  | v6all + rules v2 + cut | 0.99079 | | | |
  | v6all + stage 3 + rules v3 + cut | 0.99084 | | | |
  | **v7ce3 (e5-large/base CE) + stage 3 + rules v3 + acronyms (next candidate)** | **0.99114** | | | |

  For v4 and later: LB ≈ 0.8423 + 0.14975 × F_France, so F_France = (LB − 0.8423) / 0.14975.

  **France's level depends on US/India's test level** (`RESEARCH_v6.md` §3). `probe-v6s3-fr0` measures both: LB_fr0 = 0.38274 F_US + 0.46751 F_India + 0.14975 × 0.0559.
  - If US/India score like the re-weighted holdout, LB_fr0 ≈ 0.8513.
  - France = (LB_candidate − LB_fr0) / 0.14975 + 0.0559.
- **Ready to upload** (validator PASS), in this order:
  00. `2026-09-27-v7ce3-s3-ops3a-c2`: **the new best candidate**. v6all + stage 2 with e5-small/base/large cross-encoder logits + stage 3 + rules v3 + acronym join. Holdout 0.991138 (+0.000296 over v6all-s3). Matching `671dca1e…`, candidates `85a1ca7d…`. Probes (same candidate file): `2026-09-27-probe-v7-fr0` (`ad92c0b6…`), `2026-09-27-probe-v7-fr090` (`b7b11a5a…`).
     - vs `v6all-s3-ops3a`, France +11.7 / −21.5 predictions per 1000 S1: v7 drops uncertain French pairs, mostly same-name / same-number / other-street and empty-address ties.
     - Read its score as France change = (LB − LB_previous − 0.00025) / 0.14975.
  0. `2026-09-26-v6all-s3-ops3a-c2`: the previous best (below plus 3,872 French acronym copies at the S1's address; `acr_join.py`); matching `8d4e3bbc…`, candidates `5e991eca…`.
  1. `2026-09-26-v6all-s3-ops3-c2`: v6all + stage 3 + rules v3; matching `544ffdf8…` (candidate file `cc3750d0…`).
  2. `2026-09-26-probe-v6s3-fr0`: #1 with France emptied (`48ddacd4…`). It gives US/India on test exactly (expected about 0.8513 if they score like the re-weighted holdout), and #1 − #2 gives France.
  3. `2026-09-26-probe-v6s3-fr090`: #1 without France's model predictions below pc 0.9 (`0914b6d6…`). It prices France's uncertain band.
  4. Fallbacks: `2026-09-26-v6all-ops-c2` (`0f6d8985…`), `2026-09-26-v6all-ops3-c2` (`8c3d3a63…`), `2026-09-26-v5all-ops2-c2` (`76fe7eff…`, 0.98781).
- **Uploaded:** 26 Sep #01 = `2026-09-26-v5all-ops2-c2` → 0.98781 (`submissions/records/2026-09-26_sub01.md`).
- **Candidate set:** the organisers rank a smaller `candidate_pairs.tsv` per S1 higher. Done: p1 ≥ 0.02 and each record's top 2 S1 (4.68 → 3.70 per S1, holdout tie). Decision record `2026-09-26_0532`.
- **Deadline:** the submission-round page says the window closes 27 Sep 15:30 UTC = **21:00 IST**, and the private leaderboard uses the **final** submission. To be confirmed in the logged-in portal.
- **ETA for the current task:** done; the next steps depend on the France probe.
- **Blocked on / need from others:** the captain's uploads and their scores.
- **For Sachi (French pattern discovery):** `work/kits/france-kit-v1/` (209 MB, on the team drive), from `experiments/ameya/model-v1/france_kit.py`. Take truth rates from the `*_rule_pairs` files: the stage-2 set is selection-biased.
- **For Sachi (final package):** `experiments/ameya/model-v1/RECIPE.md` answers the five reproduction questions and gives the exact v6all and v5all recipes. `decide.py --base` is now optional, and `feats.py --dict-only` builds blocking's Indic dictionary.
- **Latest handover:** `docs/handover/2026-09-26_1817_ameya_ce-large-box.md`.
- **Next up:**
  - **v7b:** a second e5-large (seed 7, 2 epochs; group-0 AUC 0.9405 vs 0.9348) averaged with the first, then stage 2, gate vs v7ce3, stage 3, rules, acronyms, package. Automatic when the box run ends (about 20:45 IST).
  - More cross-encoder diversity on the box's spare VRAM, and stage-2 seed bagging locally. Each goes in only if it passes the holdout gate.
  - Uploads tomorrow: the best candidate, `probe-v7-fr0`, `probe-v7-fr090`, then the best re-uploaded last before 21:00 IST.
