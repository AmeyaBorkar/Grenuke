# Status: ameya

- **Last updated (IST):** 2026-09-26 02:05
- **Current focus:** France. The holdout → leaderboard gap (−0.0092) is France's (about 0.93 against 0.989 for US/India). v4 fixes it on the diagnostics; v5 (French address normalization) is building.
- **Branch(es):** `ameya/analysis-v3`: the gap analysis (`experiments/ameya/model-v1/ANALYSIS_v3.md`), label-free look-alike odds for France, leave-one-country-out check, final candidate set, probes, French address normalization, EI legal form.
- **Leaderboard vs holdout:**

  | model | holdout | leaderboard | gap |
  |---|---|---|---|
  | v2 (Sub 3) | 0.98436 | 0.97608 | −0.0083 |
  | v3 | 0.98882 | 0.97961 | −0.0092 |
  | v3ce (ready) | 0.99021 | | |
  | **v4 (ready)** | 0.99015 | | |

- **Ready to upload** (validator PASS; candidate file = the stage-2 input set, 4.7 per S1, 129 MB):
  - `submissions/files/2026-09-26-v4/`: v3 + cross-encoder + France fixes. France 3.37 predictions per S1 (v3 3.54; US/India 3.37–3.38), 5.3% empty (v3 4.4%).
  - `submissions/files/2026-09-26-v3ce/`: v3 + cross-encoder only (France 3.47 / 5.1%).
- **Deadline:** the submission-round page says the window closes 27 Sep 15:30 UTC = **21:00 IST**, and the private leaderboard uses the **final** submission. To be confirmed in the logged-in portal.
- **ETA for the current task:** v5 about 04:00 IST.
- **Blocked on / need from others:** the captain's uploads and the deadline check.
- **Latest handover:** `docs/handover/2026-09-25_2147_ameya_analysis-v2-and-v3.md` (a new one follows v5).
- **Next up:**
  - v5 gate and packaging;
  - a France-only decision probe (G8) if v4's leaderboard move is below the forecast;
  - submission records for the uploads.
