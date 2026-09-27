# Handover: recovery-audit

- **Author:** bakshi
- **When (IST):** 2026-09-27 09:52
- **Branch / PR / last commit:** `bakshi/recovery-audit`, based on main `1dd5a71`; PR accompanies this handover.
- **Area and paths touched:** `plans/bakshi/RECOVERY_0991.md`, this handover, `docs/status/bakshi.md`.

## TL;DR (3 lines max)

The reported impossibility of 0.991 is not established by the diagnostics reviewed.
A bounded candidate-recovery audit through trusted sibling aliases is specified; no gain is claimed.
Keep v7nst's measured 0.990179 protected while the prepared stacked models get public measurements.

## What was done

- Fetched latest main and reviewed PR56, PR58, issue45 comments, stage-2, cluster-support and stage-3 code.
- Corrected conditional country-score arithmetic, singleton behavior under fr0, confidence/recall reasoning,
  and the inference from rule-positive vs unknown-population disagreement.
- Wrote an executable investigation brief with input requirements, 45-minute coverage screen,
  labelled evaluation, exact F0.5 scale examples, deadlines and package safeguards.

## Current state

- **Works:** Source-reviewed plan; 115 repository tests pass; target arithmetic recomputed.
- **Half-done:** No recovery implementation or candidate search is claimed. Existing packaging remains with its active session.
- **Known bugs and caveats:** The report's French gap assumes equal UI scores for both teams; rule labels remain proxies.
  Proposed retrieval may have too little room. High-confidence accepted predictions do not establish recall.

## Numbers (shared holdout, `ber.eval`; include the command)

| metric | value | command / tag |
|---|---|---|
| holdout macro F0.5 | unchanged; no new model | documentation only |
| blocking pair recall / oracle F0.5 | not measured in this audit | proposed recovery remains unrun |
| repository tests | 115 passed, 45.84 s | command below |
| runtime / peak RAM | no ML runtime or RAM measured | no training or inference launched |

## How to reproduce or continue (exact commands)

```
python -m pytest code/business_entity_resolution/tests -q --basetemp <fresh-task-temp-path>
```

Tests used `GrenukeGit2/.venv/Scripts/python.exe` with PYTHONPATH set to this checkout's
`code/business_entity_resolution/src`. Continue with `plans/bakshi/RECOVERY_0991.md`.

## Artifacts (local paths / drive links + sha256)

- Plan: `C:/Users/baksh/Documents/Codex/2026-09-25/in/work/GrenukeRecoveryAudit/plans/bakshi/RECOVERY_0991.md`.
- User copy: `C:/Users/baksh/Documents/Codex/2026-09-25/in/outputs/RECOVERY_0991.md`.
- Protected matching SHA256: `659f5169cabbb2a3de2cb8580b614bbff718ea62d5b1fb4497243b50fcc34533`.
- Protected candidate SHA256: `510a33ea18a7ab4cd2ec5ad4e8ad113bbc4fd4f46818941c00f29852f3e258aa`.

## Next steps (ordered, with suggested owner)

1. Captain: report actual v7sq-dpc/v7nst-dpc scores and remaining quota; user will send later.
2. Execution session: run the bounded missing-candidate coverage screen with full current artifacts, if time allows.
3. Keep only a measured, feasible correction; otherwise stop the experiment and finish the existing best package.

## Blockers, open questions, decisions needed

- No public score yet supplied for the stacked candidates; 0.990295 is an estimate only.
- Full integration artifacts and current runtime availability are not established in this review session.
- Do not merge PR58 or overwrite the active package session's work as part of this documentation PR.
