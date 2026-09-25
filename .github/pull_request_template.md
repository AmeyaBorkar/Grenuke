## What and why

## Area and owner
<!-- e.g. block (owner @handle). Touching shared files or another owner's area? Tag them for review. -->

## Validation (shared holdout, `ber.eval`)

| metric | before | after |
|---|---|---|
| holdout macro F0.5 (all / US / India) | | |
| blocking pair recall / oracle F0.5 | | |
| runtime / peak RAM | | |

Commands used:
```
```

## Checklist

- [ ] Branch is `<member>/<topic>` and rebased on the latest `origin/main`
- [ ] Small and focused (under ~400 changed lines), or the size is explained
- [ ] `python -m pytest code/business_entity_resolution/tests -q` passes
- [ ] Outputs (if changed) pass `student_resource/utils/validate_submission.py`
- [ ] Follows `docs/CONTRACTS.md`, or this PR updates it with the owners' approval
- [ ] No data, large files or secrets; no external data, APIs or lookups
- [ ] Any pretrained model: name + license stated (MIT / Apache-2.0, ≤ 8B params)
- [ ] No co-author / attribution lines in the commits or this description
- [ ] Handover written: `docs/handover/...`
