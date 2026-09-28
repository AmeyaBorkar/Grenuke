# Status: bakshi

- **Last updated (IST):** 2026-09-27 20:10
- **Current focus:** Final push done. The team's single upload `mixf2` (#64, predicted ~0.99091) uses Bakshi's g1w
  India (7B cross-encoder ×2 in stage 2) and Bakshi's 7B drop rule in all countries. Bakshi confirmed it on #64.
- **Branch(es):** `bakshi/final-push` (PR #62, last commit b3e3400); `bakshi/opus-exec` (PR #56, package tooling).
- **ETA:** Done. Remaining: upload by the captain; the final package includes the 7B components.
- **Blocked on / need:** nothing.
- **Latest handover:** `docs/handover/2026-09-27_2006_bakshi_final-push.md`.
- **Next up:** after the deadline, close the Vast boxes, revoke today's GitHub token, and remove the `grenuke-vast` key.
- **Verified this session (measured):**
  - the rebuild reproduces v7sq-dpc (holdout 0.991261; band coverage 99.9999%);
  - q7st holdout AUC 0.9436;
  - g1w holdout 0.991323 (+0.000062 over g0);
  - the 7B drop rule is +0.000033 on the labelled holdout, both halves positive;
  - Composites A/B/B′ pass the validator and strict audit.
  - Closed leads (US/India recall rules, empty-S1 rescue, 7B weight ×3) are listed in `FINAL_PUSH_RESULTS.md` §6.

---

Previous status (27 Sep 01:30), kept for the record:

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
