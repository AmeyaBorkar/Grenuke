# Team, roles and ownership

This is a shared file owned by the coordinator. Change it through a small PR.
- Ownership follows `plans/FINAL_PLAN.md` §10. Tonight's tasks are GitHub issues assigned to each member: `gh issue list --assignee @me` (milestone "Fri: v0 end-to-end").

## Members

| member | GitHub | branch prefix | role(s) | contact |
|---|---|---|---|---|
| Ameya | @AmeyaBorkar | `ameya/` | repo admin; **coordinator**; **submissions captain**; blocking; pipeline and packaging | team chat |
| Sachi | @ssdhoka06 | `sachi/` | model, calibration, decision; gates and ablations; error analysis | team chat |
| Bakshi | @trustdemons05 | `bakshi/` | normalization and lexicons; pair features (string groups) | team chat |

- All three handles are repo collaborators with push access.
- `.github/CODEOWNERS` mirrors the areas below.
- **Team drive** for shared artifacts (dev kit, candidates, features; CONTRIBUTING §7): _link: Ameya posts it in the team chat_.

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
