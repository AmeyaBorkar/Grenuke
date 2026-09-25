# Team, roles and ownership

This is a shared file owned by the coordinator. Change it through a small PR.
- Ownership follows `plans/FINAL_PLAN.md` §10.
- It is **proposed** until each member confirms it in the review of the decision PR.

## Members

| member | GitHub | branch prefix | role(s) | contact |
|---|---|---|---|---|
| Ameya | @AmeyaBorkar | `ameya/` | repo admin; **coordinator**; **submissions captain**; blocking; pipeline and packaging | team chat |
| Sachi | @ssdhoka06 | `sachi/` | model, calibration, decision; gates and ablations; error analysis | team chat |
| Member 3 (_name: please fill in_) | @trustdemons05 | `<name>/` (please fill in) | normalization and lexicons; pair features | team chat |

- All three handles are repo collaborators with push access.
- `.github/CODEOWNERS` mirrors the areas below.

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
| normalization and lexicons (US/IN/FR, Indic transliteration) | `src/ber/normalize/**` | Member 3 | Ameya |
| pair features | `src/ber/features/**` | Member 3 | Ameya |
| models, calibration, ownership, decision | `src/ber/model/**` | Sachi | Ameya |
| methodology document | `docs/methodology/**` | each owner writes their section; Ameya compiles | — |
| personal experiments | `experiments/<member>/**` | that member | — |

Paths are relative to `code/business_entity_resolution/`.

Rule: outside your areas, open an issue, ask the owner, or send a PR that the owner reviews. Never push to the owner's branch.
