# Handover: nstdpc-control

- **Author:** bakshi
- **When (IST):** 2026-09-27 10:22
- **Branch / PR / last commit:** `bakshi/score-0990545` / PR60 / follows `8945085`.
- **Area and paths touched:** own plan, status and this handover; no prediction changes.

## TL;DR (3 lines max)

User reports v7nst-dpc 0.990264; downloaded matching hash verified.
v7sq-dpc 0.990545 remains best by +0.000281. Latest upload is lower.
Keep one restoration slot; use v7sq-dpc as the recovery experiment's parent.

## What was done

- Computed the control's SHA256, recorded the measured comparison and updated next steps.
- Inspected the other recovery session's directory; a script was present but no result report.

## Current state

- **Works:** both matching-file identities verified; scores supplied by the user.
- **Half-done:** correct v7sq candidate file/full package remains with the active package session.
- **Known bugs and caveats:** quota not confirmed; comparison changes more than Qwen alone and both country groups.

## Numbers (shared holdout, `ber.eval`; include the command)

| metric | value | command / tag |
|---|---|---|
| public nst -> nst-dpc | +0.000085 | user-reported scores |
| public nst-dpc -> sq-dpc | +0.000281 | user-reported scores |
| holdout / blocking oracle | no new measurement | no ML change |
| runtime / peak RAM | tests rerun; no ML runtime measured | pytest below |

## How to reproduce or continue (exact commands)

```
Get-FileHash -LiteralPath 'C:\Users\baksh\Downloads\New folder\matching_results_7nst_dpc.tsv' -Algorithm SHA256
python -m pytest code/business_entity_resolution/tests -q
```

Tests use the shared scientific venv and this checkout's src on PYTHONPATH.

## Artifacts (local paths / drive links + sha256)

- Control: `C:/Users/baksh/Downloads/New folder/matching_results_7nst_dpc.tsv`.
- Control SHA256: `f349012516cdd239106cc88f53e4f5ccaf8b5531d30a9345e82f0584783494a2`.
- Winner: `C:/Users/baksh/Documents/Codex/2026-09-25/in/outputs/best_measured_0990545/matching_results.tsv`.
- Winner SHA256: `cdda9a2da0147c06039d83b673e26d8bfc71c5171915148c1dcd24979ea0e85c`.

## Next steps (ordered, with suggested owner)

1. Captain: reserve a slot to restore the measured winner as the final upload.
2. Recovery session: evaluate one bounded correction against v7sq-dpc by 13:00.
3. Package session: complete the correct candidate/source/output pairing.

## Blockers, open questions, decisions needed

- Remaining quota unknown; no uploads or merges performed here.
