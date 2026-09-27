# Status: bakshi

## Measured score update, 27 September 10:10 IST

- **New best:** user-reported v7sq-dpc **0.990545**, +0.000366 vs v7nst; +0.000455 needed for 0.991.
- **File verified:** `matching_resultsv7sq.tsv` hashes to `cdda9a2d...ea0e85c`, the registered dpc output.
  A matching preserved copy is under the workspace `outputs/best_measured_0990545/`.
- **10:22 control:** user-reported v7nst-dpc **0.990264**, local hash verified as `f3490125...3494a2`.
  v7sq-dpc remains best by +0.000281. Latest upload is lower: reserve a final restoration slot.
- **Next decisions:** `plans/bakshi/AFTER_0990545.md`; bounded recovery against v7sq-dpc, no repeat
  control upload. Quota pending. New handover: `docs/handover/2026-09-27_1022_bakshi_nstdpc-control.md`.
- **Packaging:** matching-only audit is clean; paired candidate `55b766ef...af5331` still needed in the
  active package session. Local distribution currently contains v7nst's old candidate file.
- **Branch / handover:** `bakshi/score-0990545`; `docs/handover/2026-09-27_1010_bakshi_score-0990545.md`.
- **Scope:** documentation and file-identity verification; no new predictions or paid compute.

## Historical integration status

- **Last updated (IST):** 2026-09-27 01:30
- **Current focus:** Final packaging of the submitted model **v7nst** (public 0.990179), and preparing
  Tracks A/B so they can run the moment their inputs arrive.
- **Branch(es):** `bakshi/opus-exec`, based on main `2023ffbae034e274aab5cb262c982d6fef762e5c`. PR #50.
- **ETA:** Package tooling complete and proven end to end on a control pair. The real
  `Grenuke_submission.zip` is ~10 minutes' work once the v7nst candidate file arrives.
- **Blocked on / need:** **The v7nst `candidate_pairs.tsv` (`510a33ea…f3e258aa`).** Not on this machine —
  the only candidate TSV here is v6all's, and **3,790 matched pairs over 3,725 S1 fall outside it**, so it
  cannot substitute. Also needed: the cached CE logits (`out_bge`, `out_e5l`, `out_e5l2`, `out_cem2`, band
  files, `rule_pop` output) for Track B, the producing machine's `torch`/`transformers` pins, and the
  portal's real upload quota. Full prioritised list: `experiments/bakshi/final-package/ARTIFACT_REQUEST.md`.
- **Latest handover:** `docs/handover/2026-09-27_0111_bakshi_final-package.md`.
- **Next up:** On arrival — confirm the candidate hash and the predicted 6,410,247 pairs, build and
  self-verify the zip, hand it to the captain. Then Track B screening locally (reproduce `out_cem2`
  bit-for-bit as an alignment proof first, then the 50/50 E5-family/BGE arm). Track B's downstream stage-2
  fit cannot run here: it peaks at ~19 GB against this machine's 16 GB.
- **Verified this session (measured, not reported):** the v7nst matching file's hash matches `sub04`, and it
  passes every hard check against the full test data — 1,732,544 rows (one per test S1), 5,856,096 pairs,
  100,137 empty, **0** records claimed by more than one S1, **0** cross-country pairs, **0** targets absent
  from `test_source2/3.tsv`. France 259,452 S1 / 871,242 pairs; India 809,986 / 2,735,918;
  US 663,106 / 2,248,936. Control: the v6all pair audits clean (0 outside candidates), so the 3,790 above is
  a real `acr_join` delta and not a tool artefact. 115/115 repository tests pass.
- **Flag for owners:** `AGENTS.md` line 15 still says the deadline is 23:59 IST; issue #45 says the window
  closes at **21:00 IST**. It is a shared file so it was not edited here, but it is the first file every
  agent reads.
