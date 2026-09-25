# Status: ameya

- **Last updated (IST):** 2026-09-26 00:10
- **Current focus:** model v3 is on the leaderboard (0.97961); next is France: the look-alike vocabulary does not transfer to French words.
- **Branch(es):** `ameya/analysis-v2`: the v2 error analysis, legal-form features, blocking v2, model v3, the cross-encoder script.
- **Leaderboard vs holdout:**

  | model | holdout | leaderboard | gap |
  |---|---|---|---|
  | v2 (Sub 3) | 0.98436 | 0.97608 | −0.0083 |
  | v3 | 0.98882 | 0.97961 | −0.0092 |
  | change | +0.0045 | +0.0035 | |

  The gap grew by 0.0009 with v3. France (15% of test S1, no labels) is the likely cause: v3 adds French look-alikes (nudged number + an added French business word + the same legal form).
- **ETA for the current task:** France fix and G10 cross-encoder gate on Saturday morning.
- **Blocked on / need from others:** Sachi re-checks the legal-feature gate on the dev kit (`scores-v2lg-dev`, `devkit-v3` releases).
- **Latest handover:** `docs/handover/2026-09-25_2147_ameya_analysis-v2-and-v3.md`
- **Next up:**
  - look-alike word odds for words unseen in train (France), using the number-nudge proxy;
  - the cross-encoder gate (G10);
  - submission records for the uploads.
