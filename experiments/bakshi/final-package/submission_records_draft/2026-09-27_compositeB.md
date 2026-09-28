# Submission (Composite B): 2026-09-27

Draft for the submissions captain (`submissions/records/` is captain-only). Numbering: the captain assigns NN.

- **Uploaded by (captain):** the captain (Aarush handed the files over; the upload time is in the portal)
- **Upload time (IST):** 2026-09-27, about 22:05 (reported with the score)
- **Git commit / tag:** `bakshi/final-push` `76adeb9` (PR #62); Ameya's France from `ameya/final-stack` (mixmdp, PR #65) / `sub/2026-09-27-<NN>`
- **Package:** Drive `grenuke-train-backup/candidates/UPLOAD1_compB_mixmdpFR_g1wUSIN_7Bdrops/`
  - US/India: `g1w` (the v7sq recipe rebuilt on Bakshi's box with Bakshi's Qwen2.5-7B cross-encoder counted twice in the stage-2 mix), decided with the stacked rules (`-dpc`);
  - France: mixmdp's France (v7sq7wg: round-2 guarded self-training ×3, minus 454 look-alike swaps, plus the French expected-F0.5 decision);
  - minus the confident out-of-band predictions the 7B rejects (logit < −6): 840 French and 310 US/India pairs.
- **File sha256 (`matching_results.tsv`):** `df4bccd785b3fa785b7edcf0532288bcddc0010e2e31ce6f358064529ecb62e8` (candidates `58c824a3f61c184fe7da1a448a4ac94284f288feff9c351abfe16a3dfc0520e5`)
- **Produced by (command):** `phaseB.sh g1w "e5l qst e5ls bge q7st q7st" pseudo_s2_fr_v7ce3.parquet` (US/India), then `compose_tsv.py --labelled g1w_dpcsfq --unlabelled mixmdp --drop "rescore/fr_scored_*.parquet" "rescore/usin_scored_*.parquet" --drop-logit -6` (`experiments/bakshi/box`)
- **Hypothesis (what this tests):** do the 7B in the stage-2 mix (US/India, +62e-6 on the holdout) and the 7B re-check of the confident predictions (+33e-6 on the holdout) transfer to the leaderboard, on top of mixmdp's France?

## Scores

| | value |
|---|---|
| public leaderboard F0.5 | **0.990879** (rank 16 at the time; the team's best) |
| holdout macro F0.5 (all) | 0.991323 (g1w, US/India; France has no labels) |
| holdout, US / India | India +66.1e-6 vs v7sq3 (P 0.998), US +26e-6 (P 0.906), paired bootstrap |
| 7B drop rule (holdout sample, 186,897 S1) | +33e-6, halves +22e-6 / +43e-6 |
| mean predicted matches per S1 (test) | 3.38 (France 3.36) |

## Notes and takeaways

- **+0.000180 over mixmdp (0.990699).** About +0.00004 is the US/India model change; the rest (about +0.00014) is the 840 French 7B drops, i.e. they were nearly all false. The French rejects are generic-name decoys: same name, same house number, different street.
- **mixf2** (same US/India except US from v7sq3, France from round-3 self-training) scored 0.990819, so round-3 French labels are below round 2's: self-training helped for two rounds and hurt at the third.
- B7 (this file with the French drop rule extended to −2 with Qwen3-4B agreement, +251 / −1,699 French pairs) scored 0.990875: the extension was neutral, so the labelled −6 cut-off was already right.
