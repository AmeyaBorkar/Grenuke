# Roadmap

- This is a shared file edited by the coordinator. Everyone else reports progress in `docs/status/<member>.md` and proposes changes there or in a PR.
- All times are IST. Status values: `todo` / `doing` / `done` / `blocked` / `dropped`.
- The plan is **`plans/FINAL_PLAN.md`**. Its section numbers (§) and gates (G1–G13) are referenced below.
- **Owners** (see `docs/TEAM.md`, which also says which machine runs what):
  - **A** = Ameya (coordinator, captain, blocking, pipeline; the integration machine);
  - **S** = Sachi (model, decision, gates);
  - **B** = Bakshi, @trustdemons05 (normalization, string features).
- **Last updated:** Sun 4 Oct, evening.
  - The competition is over: the leaderboard closed on 27 Sep and the ZIP went in on 29 Sep.
  - We are in the Top 10 (2nd). **Phase 6 (the Grand Finale) is the current work.** Phases 0–5 are kept as the record.
- **Competition window (past):**
  - Fri 25 Sep 00:00 → Sun 27 Sep, 21:00 IST;
  - 5 leaderboard uploads per day per team.

## Phase 6: Grand Finale (3–7 Oct): current

- **Plan, logistics and judging criteria:** `finale/README.md`. **Knowledge base:** `knowledge/README.md`.
- **Owners are proposed.** Confirm them in the team call (6.10).
- **The deck is due Tue 6 Oct, 14:00 IST.** Knowledge capture comes first; the deck is built on Monday.

| # | task | owner | due (IST) | status |
|---|---|---|---|---|
| 6.1 | Confirm participation; join the organisers' WhatsApp group | A | Sun 4 Oct, morning | todo |
| 6.2 | Rules and structure for knowledge capture: `knowledge/` (standard, capture kit, templates), `finale/`, digest script, hooks and CI | A (agent) | Sat 3 Oct | done (#78) |
| 6.3 | Ameya's capture: three Claude Code sessions, 26 sub-agent logs, and the repo's records (handovers, decisions, plans, research, PRs, issues, code) | A (agents) | Sun 4 Oct, 06:00 | done (#84) |
| 6.4 | Bakshi's capture into `knowledge/people/bakshi/` (`knowledge/CAPTURE.md`) | B | **Sun 4 Oct, 12:00** | done (#88) |
| 6.5 | Sachi's capture into `knowledge/people/sachi/` | S | **Sun 4 Oct, 12:00** | done (#82) |
| 6.6 | Curated knowledge base v1: story, timeline, decisions, experiments, numbers, components, failures, lessons, conflicts | A (agents) | Sun 4 Oct, 10:00 | done (#84, and the follow-up PR: timeline, 329-experiment ledger, 15 component pages) |
| 6.7 | Curated knowledge base v2: merge Bakshi's and Sachi's captures; each member reviews the pages about their work | A; B and S review | Sun 4 Oct, 20:00 | done (#88 and the curation PR) |
| 6.8 | Theory study guide: 11 pages and a glossary, each page with jury questions and a self-test | A (agents); all study | Sun 4 Oct | done (#84): 11 advanced + 18 foundations pages |
| 6.9 | Q&A bank v1: at least 60 likely questions, each with a short spoken answer and the evidence | A (agents); owners check | Sun 4 Oct, 20:00 | done: `knowledge/qa.md`, 100 questions |
| 6.10 | Team call: capture status, Q&A leads, who reviews which pages | all | Sun 4 Oct, 15:00 | todo |
| 6.11 | The storyline and `finale/deck-outline.md`; who presents what; deck v1 on the organisers' template, with speaker notes | all; A (agents) builds | Mon 5 Oct | todo |
| 6.12 | Rehearsal 1 (timed to 10:00), then fixes | all | Tue 6 Oct, morning | todo |
| 6.13 | **Submit the deck** through the organisers' survey | A | **Tue 6 Oct, 14:00** | todo |
| 6.14 | Theory self-tests in pairs; Q&A drills; rehearsals 2 and 3 | all | Sun 4 – Tue 6 Oct | todo |
| 6.15 | Optional evidence for likely questions (needs the go-ahead): blocking recall and pairs per S1 with city/state keys versus ours on the holdout; the recall-versus-candidates-per-S1 curve | A | Mon 5 Oct | proposed |
| 6.16 | Finale: technical check 30 minutes before our slot, then present | all | Wed 7 Oct | todo |

## Phase 5: package and methodology (27 Sep 21:00 → 29 Sep 10:00): done

| # | task | owner | status |
|---|---|---|---|
| 5.1 | Final model: Composite B (public LB 0.990879), chosen over mixf7 / mixf2 / B7 | A, B | done (`CHANGELOG.md`, Submissions) |
| 5.2 | Runnable package: the Composite B driver, the France block, pinned requirements, tests | B, A | done (#70, #72, #73, #74) |
| 5.3 | Methodology document (7 pages) and the ZIP in the organisers' exact structure | A | done (#73, #76, #77) |
| 5.4 | Independent ZIP check before upload | B | done (#71, #75) |

## Phase 0: set up and decide (Fri): done

| # | task | owner | status |
|---|---|---|---|
| 0.1 | Repo, rules, agent file, hooks, CI, templates, shared metric/holdout/IO | A | done |
| 0.2 | Setup on every machine ([#5](https://github.com/AmeyaBorkar/Grenuke/issues/5)) | all | done |
| 0.3 | Plans submitted | each member | done (A and B; C not submitted) |
| 0.4 | `plans/FINAL_PLAN.md` and `plans/DECISION.md` | A | done (#3) |
| 0.5 | `docs/TEAM.md`: owners, names, prefixes, machines | A | done |
| 0.6 | Contracts v1 (`docs/CONTRACTS.md` C0–C10) | A | done (#3) |
| 0.7 | Pipeline skeleton | A | done (#4) |

## Phase 1: v0 baseline (Fri): done

| # | task | owner | status |
|---|---|---|---|
| 1.1 | Records cache for train and test | A | done |
| 1.2 | Normalize v0 → C3 ([#6](https://github.com/AmeyaBorkar/Grenuke/issues/6)) | B | done (#20); not used by the v6all chain |
| 1.3 | Block v0 → C4 ([#10](https://github.com/AmeyaBorkar/Grenuke/issues/10)) | A | done (#15), replaced by v1–v3 (phase 2) |
| 1.4 | Features v0, string groups → C8 ([#7](https://github.com/AmeyaBorkar/Grenuke/issues/7)) | B | done (#21); not used by the v6all chain |
| 1.4b | Features v0, context groups ([#12](https://github.com/AmeyaBorkar/Grenuke/issues/12)) | A | done |
| 1.5 | Model v0: stage 1 → C5 ([#8](https://github.com/AmeyaBorkar/Grenuke/issues/8)) | S | done (#16, #17) |
| 1.6 | Decide v0 → C9 ([#9](https://github.com/AmeyaBorkar/Grenuke/issues/9)) | S | done (#16, #17) |
| 1.7 | Full run + Submission 2 ([#13](https://github.com/AmeyaBorkar/Grenuke/issues/13)) | A | done |
| 1.8a | Submission 1 + dev kit ([#11](https://github.com/AmeyaBorkar/Grenuke/issues/11)) | A | done (baseline v0, holdout 0.9683) |

## Phase 2: improvements (Fri night → Sat): done

| # | task | owner | status | result |
|---|---|---|---|---|
| 2.1 | Error analysis by category and country | A | done | `ANALYSIS_v2`–`v4`, `RESEARCH_v5`–`v6` in `experiments/ameya/model-v1/` |
| 2.2 | Blocking v1 → v2 → v3 | A | done | holdout pair recall 0.9752 → 0.9857 → 0.9899 → **0.99135** |
| 2.3 | Features v1: distractor word odds, variants, legal forms, signed numbers | A | done | model v1 → v6all |
| 2.4 | Indic dictionary and skeletons (holdout excluded) | A | done | India 0.9561 (v0) → 0.9910 (v6all) |
| 2.5 | Stage 2 (collective, cluster support, calibration) | S, A | done | G4 kept |
| 2.6 | Decision: DP vs threshold; softmax vs argmax | S | done | G6: threshold (v6all); G5 dropped |
| 2.7 | Leave-one-country-out | A | done | US → India 0.961; 0.882 with India's words unseen |
| 2.8 | Test diagnostics and France fixes (word odds, legal forms, rules v1–v3) | A | done | leaderboard gap 0.0092 (v3) → 0.0024 (v5all) |
| 2.9 | France probes (G7, G8) | A (captain) | **todo** | `probe-v6s3-fr0`, `probe-v6s3-fr090` packaged |
| 2.10 | Uploads, each with a record and a changelog entry | A (captain) | doing | see "Submissions" |

## Phase 3: final improvements (Sat evening → Sun freeze)

| # | task | owner | status |
|---|---|---|---|
| 3.1 | Upload `v6all-s3-ops3-c2`, then the France probes; record each score | A (captain) | todo |
| 3.2 | France work picked by the probes: dual-use word odds and margin features if France < 0.98; a stricter France rule if `fr090` wins | A | todo |
| 3.3 | Optional GPU experiments (a stronger multilingual cross-encoder), gated on the holdout and a probe | A, S | todo |
| 3.4 | Ablation table for the methodology | S | todo |
| 3.5 | Choose the final model (holdout, test diagnostics, leaderboard); decision record | all | todo |
| 3.6 | **Code freeze Sun 15:00** (six hours before a 21:00 close): only packaging and documentation fixes after this | A | todo |

## Phase 4: package and submit (Sun 15:00 → 19:00, buffer to 21:00)

| # | task | owner | status |
|---|---|---|---|
| 4.1 | Clean end-to-end re-run from raw TSV with the pinned requirements (reproduce scripts: #30) | S, A | todo |
| 4.2 | `code/business_entity_resolution/README.md`: exact commands and run times | S | doing (#30 draft) |
| 4.3 | `Documentation_template.md`: methodology, blocking, features, model, results, error analysis, ablations, model licences (multilingual-e5-small, MIT) | all | doing (#30 draft) |
| 4.4 | Build `<team>_submission.zip`; verify its structure; validator on the zipped outputs | A | todo |
| 4.5 | **Final leaderboard upload = the chosen final model, by 19:00**; tag `final`; zip on the portal; `CHANGELOG.md` entry | A (captain) | todo |

## Gates (FINAL_PLAN §9)

Every result is recorded in `docs/decisions/` (C10).

| gate | question | status | result |
|---|---|---|---|
| G1 | blocking recall ≥ 99.0% (v0) / ≥ 99.5% (v1) | 99.0% met | v2 0.9899, v3 0.99135 (`gate-g1-blocking-v2`, `blocking-v3-repairs`) |
| G2 | SVD-256 dense vs sparse exact | dropped | the GPU views were not needed |
| G3 | per-token distractor encoding | kept | in model v2 onwards |
| G4 | stage 2 vs stage 1 | kept | +0.0069 (`gate-g4-stage2`) |
| G5 | softmax with "none" vs argmax | dropped | low value (26 Sep) |
| G6 | expected-F DP vs threshold | threshold | below the +0.002 bar; v6all uses the threshold (`gate-g6-dp-vs-threshold`) |
| G7 | France predictions vs an empty France (leaderboard) | open | `probe-v6s3-fr0` packaged |
| G8 | France-only threshold shift | open | `probe-v6s3-fr090` packaged |
| G9 | cluster support | kept | stage 2 from model v2 |
| G10 | cross-encoder | kept | +0.0014, e5-small (MIT) (`model-v4-france-and-cross-encoder`) |
| G11 | learned pre-ranker / candidate cut | kept | tie at 3.70 per S1 (`candidate-set-cut`) |
| G12 | Indic transliteration + dictionary + skeleton | kept | India at parity with US |
| G13 | leave-one-country-out transfer | measured | see 2.7 |
| — | legal-form features | kept | +0.0027 (`gate-legal-form-features`) |
| — | name uniqueness | rejected | +0.0005 (`gate-name-uniqueness`) |

## Submissions (details and every score: `CHANGELOG.md`)

| day | uploads | use |
|---|---|---|
| Fri 25 | done | baseline v0, v1, v2 (0.97608), v3 (0.97961) |
| Sat 26 | 1 recorded | #01 v5all + rules v2: **0.98781** (rank 15). Next: `v6all-s3-ops3-c2`, `probe-v6s3-fr0`, `probe-v6s3-fr090` |
| Sun 27 | up to 5 | final candidates, 1 spare; **the last upload is the chosen final model, well before 21:00** |

## Standing rules

- Every session ends with a handover and a status update.
- Every leaderboard upload has a record, a tag and a `CHANGELOG.md` entry.
- No result counts without holdout numbers from `ber.eval` and the commit that produced them.
- A component ships only after its gate record (C10). Ties go to the simpler option.
