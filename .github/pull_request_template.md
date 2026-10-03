## What and why

## Area, roadmap task and gate
<!-- e.g. block (owner @handle), docs/ROADMAP.md task 1.3b, gate G1. Touching shared files or another owner's area? Tag them for review. -->

## Validation (shared holdout, `ber.eval`)

| metric | before | after |
|---|---|---|
| holdout macro F0.5 (all / US / India) | | |
| blocking pair recall / oracle F0.5 | | |
| gate result (Δ, 95% CI), if this adds a component | | |
| runtime / peak RAM | | |

Commands used:
```
```

Changelog: <!-- one line for CHANGELOG.md; the coordinator copies it in -->

## Checklist

- [ ] Branch is `<member>/<topic>` and rebased on the latest `origin/main`
- [ ] Small and focused (under ~400 changed lines), or the size is explained
- [ ] `python -m pytest code/business_entity_resolution/tests -q` passes
- [ ] Outputs (if changed) pass `student_resource/utils/validate_submission.py`
- [ ] Follows `docs/CONTRACTS.md`, or this PR updates it with the owners' approval
- [ ] Anything beyond the v0 baseline has a gate record in `docs/decisions/` (`plans/FINAL_PLAN.md` §9)
- [ ] No data, large files or secrets; no external data, APIs or lookups
- [ ] Any pretrained model: name + license stated (MIT / Apache-2.0, ≤ 8B params)
- [ ] No co-author / attribution lines in the commits or this description
- [ ] Handover written: `docs/handover/...`
- [ ] Knowledge recorded: decisions and experiments from this PR are in `knowledge/` or `knowledge/people/<member>/` (`knowledge/STANDARD.md`); no transcripts, IPs, e-mails or personal paths
