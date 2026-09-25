# Status: ameya

- **Last updated (IST):** 2026-09-26 04:40
- **Current focus:** France. The generator's in-slot word-swap look-alikes are accepted in France: 17k predictions in v4, a population that is 0.6% true in US/India. Its list-word true copies are missed. `post_ops.py` fixes both for countries without labels; expected leaderboard +0.0027.
- **Branch(es):** `ameya/analysis-v3`:
  - v5: French address normalisation, EI as a legal form;
  - `--all` final fit;
  - `post_ops.py`;
  - `ANALYSIS_v4.md`.

  The PR waits for the leaderboard probes.
- **Leaderboard vs holdout:**

  | model | holdout | leaderboard | gap |
  |---|---|---|---|
  | v2 (Sub 3) | 0.98436 | 0.97608 | −0.0083 |
  | v3 | 0.98882 | 0.97961 | −0.0092 |
  | v4 | 0.99015 | | |
  | v5all + rules (final candidate) | 0.99016 | | |

- **Ready to upload** (validator PASS), in this order:
  1. `submissions/files/2026-09-26-v4/`: the anchor; expected 0.987–0.989.
  2. `submissions/files/2026-09-26-probe-v4-frab/`: v4 + the France rules; minus (1) = the rules alone, expected +0.0027.
  3. `submissions/files/2026-09-26-v5all-ops/`: the final candidate (v5 features, all-data fit, rules); matching sha256 `f8b6245f…`.
  4. Optional:
     - `2026-09-26-probe-v4-fr0/` (France emptied): F_France = (LB_v4 − LB_fr0) / 0.14975 + 0.0559;
     - `2026-09-26-probe-v5-frab/` (v5 + rules, isolates v5);
     - `2026-09-26-probe-v4-in0/` (India emptied).
- **Deadline:** the submission-round page says the window closes 27 Sep 15:30 UTC = **21:00 IST**, and the private leaderboard uses the **final** submission. To be confirmed in the logged-in portal.
- **ETA for the current task:** done; waiting for the uploads.
- **Blocked on / need from others:** the captain's uploads and their scores.
- **Latest handover:** `docs/handover/2026-09-26_0417_ameya_france-generator-ops.md`.
- **Next up:**
  - read the probes, then open the PR for v5 + `--all` + rules and record the gate;
  - if time: op-A/op-B position features in the model; acronym adds for France; a larger or diff-aware cross-encoder.
