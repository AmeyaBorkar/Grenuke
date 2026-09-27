# Status: ameya

- **Last updated (IST):** 2026-09-27 22:45
- **Current focus:** the final upload `B+` (Composite B, LB 0.990879, plus 8 confirmed 7B decoy drops; matching `a5b0e90f36d5c598…`). mixf7 0.990833 and mixf2 0.990819 were measured tonight; RESEARCH_v6.md §6.20.
- **Branch(es):** `ameya/final-stack`, commits ad84d66 to ea2067b:
  - `ce_box.py` options;
  - `stack/dp_france.py`;
  - `ce_synth2.py`, `synth_fr2.py`, `synth_fr3.py`;
  - `stack/compose3.py`;
  - RESEARCH_v6.md §6.18–6.19;
  - this file and the handover.
  - Earlier PRs #35–#58 are merged.
- **Leaderboard vs holdout:**

  | model | holdout (s3) | leaderboard | France implied |
  |---|---|---|---|
  | v7n | 0.99121 | 0.989721 | 0.978 |
  | v7nst | 0.99119 | 0.990179 | 0.981 |
  | v7nst-dpc | 0.99119 | 0.990264 | about 0.982 |
  | v7sq-dpc | 0.99125 | 0.990545 | about 0.983 |
  | **mixmdp** (v7sq3 US/India + v7sq7wg France − look-alikes + France DP) | 0.99131 (combo) | **0.990699 (rank 12)** | about 0.984 |

- **The final, `mixf2`:** validator and strict audit PASS; matching `4c3b4527d608fdf5…`, candidates `d2c7af15cf5331fd…`.
  - Files: `submissions/files/2026-09-27-mixf2-c2/`, and `Downloads/*v7sq6r3-g1wIndia-q7all.tsv`.
  - US: v7sq3-dpc.
  - India: g1w-dpc (Bakshi's 7B ×2 in stage 2). +66.1e-6 F on the holdout, P 0.998.
  - France: v7sq6r3-dpc (round-3 stage-2 labels). cal +215e-6 vs v7sq-dpc, against mixmdp's +146.
  - Drops: Bakshi's 7B rejects outside the band (logit < −6, p1 > 0.99), 832 French and 310 US/India pairs. The rule gives +33e-6 on the holdout. The French rejects are generic-name decoys (RESEARCH_v6.md §6.19).
  - Predicted gain over mixmdp: about +0.0002.
- **Alternatives built (not uploaded):**
  - `mixf4`: France v7sq6r4 + DP. +11e-6 by cal, but one more self-training round.
  - `mixf3`: France v7sqsyc. The highest cal, but weak corroboration.
  - Bakshi's Composite B: the team's backup.
- **Running:** v7sqsyd is being built and valued on the laptop (record only). Detector jobs run on grenuke-vast3 and 5090 #2 (low value; stop them with the instances).
- **Vast.ai:**
  - Destroy these in the console after the upload: `grenuke-vast3` (H100), the RTX 5090 at 180.189.55.43:28839, and the RTX 5090 at 31.13.237.164:42151.
  - Remove the session SSH keys (`~/.ssh/grenuke_vast`, `~/.ssh/grenuke_vast2`).
  - Bakshi's boxes are wound down; my scratch folders there (`ameya_oob`, `ameya_q7add`, `ameya_val`) can be deleted.
- **Candidate set:** 3.70 pairs per test S1, as before (the stage-2 input; organisers review it with the code).
- **Blocked on / need from others:** the captain's upload of `mixf2` and its score, which goes in `CHANGELOG.md` and `submissions/records/`.
- **Latest handover:** `docs/handover/2026-09-27_2014_ameya_final-upload.md`.
