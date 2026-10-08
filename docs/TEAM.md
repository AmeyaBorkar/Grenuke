# Team, roles and ownership

This is a shared file owned by the coordinator. Change it through a small PR.
- Ownership follows `plans/FINAL_PLAN.md` §10. During the challenge, tasks were GitHub issues assigned to each member.

## Members

| member | GitHub | branch prefix | role(s) |
|---|---|---|---|
| Ameya Borkar | @AmeyaBorkar | `ameya/` | repo admin; **coordinator**; **submissions captain**; blocking; pipeline and packaging |
| Sachi Dhoka | @ssdhoka06 | `sachi/` | model, calibration, decision; gates and ablations; error analysis |
| Aarush Bakshi | @trustdemons05 | `bakshi/` | normalization and lexicons; pair features (string groups) |

- All three handles are repo collaborators with push access.
- `.github/CODEOWNERS` mirrors the areas below.
- Shared artifacts (dev kits, candidates, features) were exchanged through a private team drive; they are not part of this repository.

## Machines and what runs where

| member | machine | use it for |
|---|---|---|
| Ameya | RTX 5070 Ti 12 GB, 24 cores, 31 GB RAM | **the integration machine**: every full-scale run (blocking on the GPU, features, training, test predictions) and every leaderboard upload |
| Bakshi | i5-12450H (8 cores), RTX 2050 4 GB, 16 GB RAM | records + normalization on the full data (chunked); features on the dev sample |
| Sachi | MacBook Air M3 (8 cores), 8 GB RAM, no CUDA | model, calibration and decisions on the dev sample (never load the full train features) |

- **Code moves, data doesn't.** Everyone develops on the **dev sample** (about 110k train S1 across folds 0/5/10/15 with their candidates, `ber.eval.splits.in_dev_sample`) and merges code through PRs; Ameya re-runs the stages at full scale.
- Every stage must run on the CPU. GPU code picks `cuda` only when it exists.

## Roles

- **Coordinator:**
  - owns shared files and keeps `docs/ROADMAP.md` and `CHANGELOG.md` current;
  - breaks ties after a 15-minute timebox;
  - reviews shared-file PRs.
- **Submissions captain:**
  - the only person who uploads to the leaderboard;
  - manages the 5-per-day budget;
  - writes `submissions/records/*`, tags `sub/*` and adds the changelog entry for each upload.
- **Area owner:**
  - decides everything inside their area and reviews PRs that touch it;
  - runs the gates (`plans/FINAL_PLAN.md` §9) for their area and records the results (`docs/CONTRACTS.md` C10).

## Finale roles (from 3 Oct; proposed, confirm in the team call)

| role | who | what |
|---|---|---|
| curator | Ameya | merges every capture into `knowledge/`, keeps `knowledge/numbers.md` as the single source of quoted numbers, owns `finale/` |
| capture | each member | their own chats and notes → `knowledge/people/<member>/` (`knowledge/CAPTURE.md`), by Sun 4 Oct 12:00 |
| reviewer | each member | checks the pages about their own work (credit, numbers, reasons) |
| presenter | to decide (6.10) | who speaks which slides; everyone answers questions on any part |

**Proposed Q&A leads**, by who built or studied each part (`knowledge/people/*/contributions.md` will confirm):

| topic | lead | backup |
|---|---|---|
| problem framing, data analysis, overall strategy | Ameya | Sachi |
| blocking and candidate generation; the candidates-per-entity ratio; scale | Ameya | Bakshi |
| normalisation, lexicons, string features | Bakshi | Ameya |
| XGBoost stages, calibration, gates and bootstrap, ablations | Sachi | Ameya |
| cross-encoders: e5, bge, Qwen2.5-1.5B LoRA | Sachi (Qwen 1.5B), Ameya (e5, bge) | Bakshi |
| Qwen2.5-7B: the cross-encoder in the mix and the re-check of confident predictions; Composite B | Bakshi | Ameya |
| France: self-training, rules, probes, synthetic French | Ameya (self-training, rules), Sachi (synthetic French, diagnostics) | Bakshi |
| decision layer: expected-F0.5 set selection, ownership | Ameya | Sachi |
| reproducibility, the package, compliance (licences, no external data) | Bakshi | Ameya |

## Area ownership

| area | paths | owner | backup |
|---|---|---|---|
| shared foundation (I/O, IDs, paths, artifacts, metric, holdout, gates) | `src/ber/{io,ids,paths,artifacts,config}.py`, `src/ber/eval/**` | Ameya | Sachi |
| pipeline CLI, records, outputs, packaging, final zip | `src/ber/{pipeline,records,outputs}.py`, `scripts/package_*` | Ameya | Sachi |
| blocking and candidate generation (GPU runs) | `src/ber/block/**` | Ameya | Sachi |
| normalization and lexicons (US/IN/FR, Indic transliteration) | `src/ber/normalize/**` | Bakshi | Ameya |
| pair features: string groups (`name`, `extra`, `num`, `addr`) and the stage `run()` | `src/ber/features/**` | Bakshi | Ameya |
| pair features: context groups (`ret`, `src`, `ctx`) | `src/ber/features/context.py` | Ameya (Bakshi reviews) | Bakshi |
| models, calibration, ownership, decision | `src/ber/model/**` | Sachi | Ameya |
| methodology document | `docs/methodology/**` | each owner writes their section; Ameya compiles | — |
| personal experiments | `experiments/<member>/**` | that member | — |

Paths are relative to `code/business_entity_resolution/`.

Rule: outside your areas, open an issue, ask the owner, or send a PR that the owner reviews. Never push to the owner's branch.
