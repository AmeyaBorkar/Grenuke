# Plan decision record

**Status: decided (Fri 25 Sep 2026, 14:15 IST).** The chosen plan is **`plans/FINAL_PLAN.md`**: Plan A as the base, with grafts from Plan B, adjusted by data checks run on 25 Sep. Shared file, maintained by the coordinator.

- **Date / time (IST):** 2026-09-25 14:15
- **Participants:**
  - Ameya, the coordinator, took the decision.
  - Plans reviewed: A (Ameya) and B (Sachi). Plan C was not submitted.
  - Sachi and Member 3 review it in the PR. Objections become a `docs/decisions/` record and a plan update.
- **Base plan:** **A** (`plans/ameya/PLAN.md`). It has the only complete time and compute budget, a stage layout and a contract fit, and its measured test shift was confirmed.

## Grafted components (plan → stage)

- **Plan B → process:**
  - measured / fact / hypothesis tags on every claim;
  - every complex component must beat a simpler alternative on the shared holdout, using a paired bootstrap (FINAL_PLAN §9, gates G1–G13);
  - an ablation table for the methodology.
- **Plan B → normalization:** consonant skeleton and OCR variants kept next to the originals (features take the max), a domain stem only from tokens of 3+ characters, and DBA scored on both sides.
- **Plan B → blocking:**
  - name-only retrieval only over S2/S3 records with empty or ≤3-token addresses;
  - domain-stem and DBA inner-name keys;
  - drop any view or key that adds less than 0.1 pt of recall;
  - no learned pre-ranker in v0 (a heuristic trim instead);
  - unseen or empty country labels are searched against every partition.
- **Plan B → model:**
  - owner-removed training examples (teaching "no owner here");
  - softmax over each record's S1s plus "none", as a gated alternative to argmax (G5);
  - reliability plots per country and source.
- **Plan B → decision:** expected-F0.5 must beat a tuned threshold, and ties go to the threshold (G6).
- **Plan B → France:** Cedex and arrondissement handling, a France-vs-empty leaderboard probe, and a comparison of France's max-p distribution.
- **Data checks of 25 Sep → everywhere:**
  - no postcode feature;
  - the extra-token and number-relation features are core;
  - thresholds for test come from test diagnostics plus an EM prior estimate, not from a drop-S1 stress test (FINAL_PLAN §1 #13–#14).

## Rejected ideas and why

- **Plan B "test resembles train" ([H] #20).** Disproved: 5.75 vs 4.68 S2/S3 per S1.
- **Plan B cutting the extra-token (sibling) module as "subsumed by competition margins".**
  - Look-alike orphans differ from their S1 by a changed house number (the first number equal in 12% vs 85%) and a business-changing word (77% vs 23%).
  - Many of them have no rival S1, so no margin can catch them.
- **Plan B's sampled "world" for competition features.** Competition features need the full candidate graph. Sampling is fine only for training rows.
- **Plan B's unspecified top-k search.** We use Plan A's engine (GPU dense top-k), with sparse exact search as the fallback (G2).
- **Plan A's name view over all records.** Only 0.27% of true pairs have a weak address with more than 3 tokens, and S1 names collide 46–54%.
- **Plan A's postcode field.** Postcodes appear in at most 0.5% of addresses, France included.
- **Plan A's drop-20%-of-S1 stress test as the threshold driver.** The extra test records aren't missing their owners. It is kept only as a failure-mode check.
- **Plan A's learned pre-ranker in v0.** Deferred behind G11. A heuristic trim goes first.

## Rubric scores

The table holds the coordinator's scores from the plan comparison. Teammates add their own in the PR review, and the averages then replace these.

| plan | expected F0.5 (30) | recall (15) | robustness (15) | time to first submission (15) | compute (10) | validation (10) | parallel (5) | weighted |
|---|---|---|---|---|---|---|---|---|
| A (Ameya) | 4 | 4 | 4 | 3 | 4 | 4.5 | 4 | **3.9** |
| B (Sachi) | 3 | 3.5 | 3 | 3 | 3 | 4 | 2 | **3.1** |
| C | not submitted | | | | | | | |

**Hard gates:**
- Both plans pass the gates on provided data only and no {US, India} assumptions.
- Plan A needs its Friday scope cut to v0 to meet the Friday 23:30 gate. FINAL_PLAN §8 does this.
- Plan B has no timeline or compute budget.

## Area owners after the decision

Proposed; mirrored in `docs/TEAM.md` and `.github/CODEOWNERS`:
- **Ameya:** coordination, submissions captain, blocking, pipeline and packaging.
- **Sachi:** model, calibration, decision, gates and ablations.
- **Member 3 (@trustdemons05):** normalization, lexicons and pair features.

## Other outcomes

- **Contract changes needed:** in the same PR as this record. `docs/CONTRACTS.md` gets:
  - C2: OOF groups and a fold-0 dev subset;
  - C3: normalized record columns;
  - C4: candidate metadata;
  - C5: stage-1 scores;
  - C7: report keys;
  - C8: features (new);
  - C9: matches (new);
  - C10: gate records (new).
- **First-submission target:** Fri 25 Sep before 23:30 IST. v0 = normalize v0 + block v0 + about 40 features + XGBoost stage 1 + argmax + tuned threshold.
