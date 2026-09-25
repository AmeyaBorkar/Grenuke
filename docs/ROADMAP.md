# Roadmap

- This is a shared file edited by the coordinator. Everyone else reports progress in `docs/status/<member>.md` and proposes changes there or in a PR.
- All times are IST. Status values: `todo` / `doing` / `done` / `blocked` / `dropped`.
- The plan is **`plans/FINAL_PLAN.md`**. Its section numbers (§) and gates (G1–G13) are referenced below.
- **Owners** (see `docs/TEAM.md`, which also says which machine runs what):
  - **A** = Ameya (coordinator, captain, blocking, pipeline; the integration machine);
  - **S** = Sachi (model, decision, gates);
  - **B** = Bakshi, @trustdemons05 (normalization, string features).
- **Tonight's tasks are GitHub issues** with full specs, assigned to their owners (milestone "Fri: v0 end-to-end"): `gh issue list --assignee @me`.
- **Window:** Fri 25 Sep 00:00 → Sun 27 Sep 23:59 IST.
- **Leaderboard budget:** 5 uploads per day per team (15 in total).

## Phase 0: set up and decide (Fri, until 15:30)

| # | task | owner | status | done when |
|---|---|---|---|---|
| 0.1 | Repo, rules, agent file, hooks, CI, templates, shared metric/holdout/IO | A | done | — |
| 0.2 | Everyone: clone, run `scripts/setup`, get the dataset, `pip install -r code/business_entity_resolution/requirements.txt`, run `pytest` ([#5](https://github.com/AmeyaBorkar/Grenuke/issues/5)) | all | doing | tests green on every machine |
| 0.3 | Plans submitted | each member | done | A and B submitted; C not submitted |
| 0.4 | Decision: `plans/FINAL_PLAN.md` and `plans/DECISION.md` | A | done (PR #3) | PR merged |
| 0.5 | `docs/TEAM.md` owners, names, prefixes and machines | A | done | Bakshi = @trustdemons05, prefix `bakshi/` |
| 0.6 | Contracts v1 (`docs/CONTRACTS.md` C0–C10) | A | done (PR #3) | PR merged |
| 0.7 | Pipeline skeleton: CLI, `records` / `write` / `evaluate` stages, artifact metadata, OOF groups, gate bootstrap, stage stubs | A | done (PR #4) | PR merged; `python -m ber.pipeline --stage records --split train` works |

## Phase 1: v0 baseline → Submissions 1 and 2 (Fri 15:30 → 23:00)

Goal: a **valid baseline on the leaderboard by 17:30** and the **full v0 by 23:00** (FINAL_PLAN §8, M1–M3). Each task is an issue with the full spec.

| # | task | owner | issue | status | target | done when |
|---|---|---|---|---|---|---|
| 1.1 | Records cache for train and test (`--stage records`) | A | — | done (others: ~75 s, #5) | — | `work/records/*.parquet` exist |
| 1.2 | Normalize v0 → C3 | B | [#6](https://github.com/AmeyaBorkar/Grenuke/issues/6) | todo | 18:00 | C3 v0 columns for both splits; tests on tricky strings |
| 1.3 | Block v0: token retriever (CPU) now, GPU views next → C4 | A | [#10](https://github.com/AmeyaBorkar/Grenuke/issues/10) | doing | dev 17:30, full 19:30 | C4 for train and test; blocking report (G1 ≥ 99.0%) |
| 1.8a | **Submission 1 (baseline)** + dev kit on the team drive | A | [#11](https://github.com/AmeyaBorkar/Grenuke/issues/11) | doing | 17:30 | uploaded; record, tag, changelog; dev sample shared |
| 1.4 | Features v0, string groups (`name`, `extra`, `num`, `addr`) → C8 | B | [#7](https://github.com/AmeyaBorkar/Grenuke/issues/7) | todo | 21:00 | dev features < 5 min; tests on hand-made pairs |
| 1.4b | Features v0, context groups (`ret`, `src`, `ctx`) | A | [#12](https://github.com/AmeyaBorkar/Grenuke/issues/12) | todo | 21:00 | joined by the features stage |
| 1.5 | Model v0: XGBoost stage 1, OOF groups, isotonic → C5 | S | [#8](https://github.com/AmeyaBorkar/Grenuke/issues/8) | todo | 21:30 | C5 on the dev features; holdout AUC / log-loss |
| 1.6 | Decide v0: ownership + tuned threshold → C9 (then the expected-F0.5 DP) | S | [#9](https://github.com/AmeyaBorkar/Grenuke/issues/9) | todo | 22:00 | C7 report with holdout macro F0.5 per country |
| 1.7 | **Full run on the integration machine + Submission 2 (v0)** | A | [#13](https://github.com/AmeyaBorkar/Grenuke/issues/13) | todo | 23:00 | validator PASS; uploaded with record, tag, changelog |

Dependencies and timeline:
- **Now:** B starts 1.2 (needs only the records); S starts 1.5 and 1.6 on synthetic data (snippets in the issues); A builds 1.3 and 1.8a.
- **17:30:** dev candidates on the team drive → B starts 1.4 on real pairs.
- **~19:00:** dev features on the team drive → S trains and tunes on real features.
- **21:00–22:00:** the PRs for 1.4, 1.5, 1.6 merge; **22:00–23:00:** A runs everything at full scale and submits.
- If anything slips, Submission 1 (the baseline) stays our Friday result.

## Phase 2: v1 improvements (Sat)

| # | task | owner | status | gate |
|---|---|---|---|---|
| 2.1 | Error-analysis gallery: false positives and negatives by category (look-alike, common name, Indic, empty address, fragment) and country | S | todo | — |
| 2.2 | Blocking v1: V-name-short, K tuned on the recall curve, drop views adding <0.1 pt; pre-ranker check | A | todo | G1 (≥99.5%), G11 |
| 2.3 | Features v1: per-token distractor encoding, variants (OCR, skeleton), DBA/acronym, city alias | B | todo | G3 |
| 2.4 | Normalize v1: learned Indic dictionary and skeleton (holdout excluded) | B | todo | G12 |
| 2.5 | Stage-2 collective with owner-removed augmentation, calibration and reliability plots | S | todo | G4 |
| 2.6 | Decision gates: DP vs threshold, softmax vs argmax | S | todo | G6, G5 |
| 2.7 | Leave-one-country-out and the missed-owner check | S | todo | G13 |
| 2.8 | Test diagnostics and EM prior per country; France checks and 100 hand checks | A | todo | G8 |
| 2.9 | France-vs-empty leaderboard probe | A (captain) | todo | G7 |
| 2.10 | Submissions 2–6, each with a record, a tag and a changelog entry | A (captain) | todo | — |

## Phase 3: final improvements (Sun until 17:00)

| # | task | owner | status | gate |
|---|---|---|---|---|
| 3.1 | Gated extras: cluster support; encoder, cross-encoder or LightGBM blend; learned pre-ranker | S, A | todo | G9, G10, G11 |
| 3.2 | Ablation table (remove one component at a time) for the methodology | S | todo | — |
| 3.3 | Choose the final model from the holdout, test diagnostics and leaderboard consistency; write a decision record | all | todo | — |
| 3.4 | **Code freeze at 17:00**: only packaging and documentation fixes after this | A | todo | — |

## Phase 4: package and submit (Sun 17:00 → 23:00, with a buffer)

| # | task | owner | status |
|---|---|---|---|
| 4.1 | Clean end-to-end re-run from raw TSV in a fresh env with pinned `requirements.txt` | A | todo |
| 4.2 | `code/business_entity_resolution/README.md`: exact commands and run times | A | todo |
| 4.3 | Fill in `Documentation_template.md`: each owner writes their section (methodology, blocking, features, model, results, error analysis, ablations); A compiles | all | todo |
| 4.4 | Build `<team>_submission.zip` (output/, code/, doc); verify its structure; run the validator on the zipped outputs | A | todo |
| 4.5 | **Final leaderboard upload = the chosen final model**; tag `final`; upload the zip on the portal; `CHANGELOG.md` entry | A (captain) | todo |

## Gates (FINAL_PLAN §9)

Every result is recorded in `docs/decisions/` (C10).

| gate | question | owner | status | result |
|---|---|---|---|---|
| G1 | blocking recall ≥99.0% (v0) / ≥99.5% (v1) | A | open | |
| G2 | SVD-256 dense vs sparse exact recall@K | A | open | |
| G3 | per-token distractor encoding | B | open | |
| G4 | stage-2 collective vs stage 1 | S | open | |
| G5 | softmax with "none" vs argmax | S | open | |
| G6 | expected-F DP vs tuned threshold | S | open | |
| G7 | France predictions vs an empty France (leaderboard) | A | open | |
| G8 | threshold/shrink shift for test | S | open | |
| G9 | cluster support | S | open | |
| G10 | encoder / cross-encoder / blend | S, A | open | |
| G11 | learned pre-ranker | A | open | |
| G12 | Indic transliteration + dictionary + skeleton | B | open | |
| G13 | leave-one-country-out transfer | S | open | |

## Submission plan (the captain adjusts it; `submissions/README.md`)

| day | uploads | intended use |
|---|---|---|
| Fri 25 | 2–3 | baseline at 17:30, v0 at 23:00 (+1 fix if needed) |
| Sat 26 | up to 5 | stage 2 and DP (2–3), blocking and features v1 (1), France probe (1) |
| Sun 27 | up to 5 | final candidates (2–3), 1 spare; **the last upload is the chosen final model** |

## Standing rules

- Every session ends with a handover and a status update.
- Every leaderboard upload has a record, a tag and a `CHANGELOG.md` entry.
- No result counts without holdout numbers from `ber.eval` and the commit that produced them.
- A component ships only after its gate record (C10). Ties go to the simpler option.
