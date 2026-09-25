# Team, roles and ownership

This is a shared file owned by the coordinator. Change it through a small PR. Ownership is finalized right after the plan decision (`plans/DECISION.md`).

## Members

| member | GitHub | branch prefix | role(s) | contact |
|---|---|---|---|---|
| Ameya | @AmeyaBorkar | `ameya/` | repo admin; **coordinator** (proposed); **submissions captain** (proposed) | team chat |
| _Member 2 (name)_ | @_handle_ | `<name>/` | _TBD_ | team chat |
| _Member 3 (name)_ | @_handle_ | `<name>/` | _TBD_ | team chat |

Replace the placeholders, then:
- the admin invites each handle as a repo collaborator: `gh api -X PUT repos/AmeyaBorkar/Grenuke/collaborators/<handle> -f permission=push`;
- add the handle to `.github/CODEOWNERS` for the areas that person owns.

## Roles

- **Coordinator:** owns shared files, keeps `docs/ROADMAP.md` current, breaks ties after a 15-minute timebox, and reviews shared-file PRs.
- **Submissions captain:** the only person who uploads to the leaderboard. Manages the 5-per-day budget, writes `submissions/records/*` and tags `sub/*`.
- **Area owner:** decides everything inside their area and reviews PRs that touch it.

## Area ownership (fill in after the plan decision)

| area | paths | owner | backup |
|---|---|---|---|
| shared foundation (I/O, IDs, metric, holdout) | `src/ber/{io,ids,paths}.py`, `src/ber/eval/**` | Ameya | _TBD_ |
| normalization and lexicons (US/IN/FR, Indic transliteration) | `src/ber/normalize/**` | _TBD_ | _TBD_ |
| blocking and candidate generation | `src/ber/block/**` | _TBD_ | _TBD_ |
| pair features | `src/ber/features/**` | _TBD_ | _TBD_ |
| models, calibration, decision | `src/ber/model/**` | _TBD_ | _TBD_ |
| pipeline, CLI, packaging, final zip | `src/ber/pipeline.py`, `scripts/package_*` | _TBD_ | _TBD_ |
| methodology document | `docs/methodology/**` | _TBD_ | _TBD_ |
| personal experiments | `experiments/<member>/**` | that member | — |

Rule: outside your areas, open an issue, ask the owner, or send a PR that the owner reviews. Never push to the owner's branch.
