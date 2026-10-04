# Status: ameya

- **Last updated (IST):** 2026-10-04 18:00
- **Current focus:** the Grand Finale (Wed 7 Oct). The deck is due Tue 6 Oct 14:00 IST and will be built on Mon 5 Oct.
  - Knowledge base v1 is on `main` (#84): story, 247 decisions, fact sheet, conflicts, failures, lessons, Q&A, and 29 theory pages.
  - Bakshi's open PRs are merged through the integration PR.
- **Branch(es):** `ameya/merge-bakshi`.
- **Blocked on / need from others:** Bakshi's capture (#80).
- **Next up:**
  - the deck outline and deck v1 (Mon 5 Oct);
  - rehearsals;
  - optionally the paused pages: timeline, experiment ledger, components.

## State at the close of the competition (27 Sep 23:55)

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

- **The final, `B+`:** validator and strict audit PASS; matching `a5b0e90f36d5c598…`, candidates `b55c2b1d01fa9699…`.
  - Files: `submissions/files/2026-09-27-mixbp-c2/`, and `Downloads/matching_resultscompBplus.tsv` + `candidate_pairscompBplus.tsv`.
  - It is Composite B (LB 0.990879; rebuilt byte-identical, matching `df4bccd785b3fa78…`) plus 8 more French decoys dropped by the LB-confirmed 7B rule.
  - US/India: g1w-dpc minus 310 7B rejects. France: mixmdp's France minus 848 7B rejects.
- **Measured tonight:**
  - B 0.990879.
  - mixf7 0.990833: round-3 France is −46 vs B.
  - mixf2 0.990819: g1w US is +14 vs v7sq3.
  - See RESEARCH_v6.md §6.20 for the decomposition and the estimator bias on decoys.
- **Not uploaded:**
  - mixfq: round-3 France with B's treatment, bias-corrected about −33.
  - More inclusive France DP at shifts 0.5 and 0.8: unvalidated ranges.
  - Corrected-label round 4: −44.
  - 7B ensemble: its extras hit real copies.
- **Vast.ai:**
  - Both RTX 5090s are destroyed. Destroy `grenuke-vast3` (H100) after the upload.
  - Remove the session SSH keys (`~/.ssh/grenuke_vast`, `~/.ssh/grenuke_vast2`).
  - Bakshi's boxes are wound down; my scratch folders there (`ameya_oob`, `ameya_q7add`, `ameya_val`) can be deleted.
- **Candidate set:** 3.70 pairs per test S1, as before (the stage-2 input; organisers review it with the code).
- **Blocked on / need from others:**
  - the captain: merge #62 and #65, number and commit the submission records (Bakshi's drafts), destroy `grenuke-vast3`, remove the session SSH keys;
  - Bakshi: fold the three edits (#64) into the solution document.
- **Latest handover:** `docs/handover/2026-09-27_2014_ameya_final-upload.md`.
