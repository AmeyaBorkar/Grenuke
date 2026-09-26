# Handover: final-plan-review

- Author: Bakshi
- Date: 26 Sep late evening
- Branch: `bakshi/final-plan-review`, base main `72a221f`.
- Paths: Bakshi review/status/handover only; exact PR30 diff exported outside Git.

## TL;DR

Refreshed GitHub with replacement credential. v7n is confirmed 0.989721, rank 8 at upload; replacement H100 already runs upstream. Pasted $100 plan has material inference and packaging errors; corrected review is complete.

## What was done

Read latest issue45, submission03, v7n decision/handover and package PR30. Verified local v7n/v7nst hashes. Exported PR30 diff and documented exact stale package components, missing candidate/environment inputs and corrected score target.

## Current state

- Works: authenticated GitHub fetch; current local source checkout and package analysis.
- Pending: exact v7n candidate TSV, producing environment versions, suitable clean-rerun machine/account access.
- Caveats: France proxy AUC is not real labeled France AUC; count agreement does not prove matching accuracy; no linear AUC-to-F0.5 conversion or success probability is established.

## Numbers

| item | value | source |
|---|---|---|
| public v7n | 0.989721, rank 8 at 23:05 | submission03 |
| holdout v7n | 0.991211 | upstream decision, not rerun |
| gain needed for 0.99 | +0.000279 overall | direct arithmetic |
| France-only equivalent | +0.0018631 | unchanged US/India, weight 0.14975 |
| new rental/training spend | $0 | no paid action performed |
| runtime / peak RAM | not instrumented | read-only/doc work |

## How to reproduce or continue

Read `experiments/bakshi/FINAL_DAY_REVIEW.md`. Worktree is `C:/Users/baksh/Documents/Codex/2026-09-25/in/work/GrenukeFinalPlan`. Scientific Python is the sibling GrenukeGit2 `.venv/Scripts/python.exe`; set PYTHONPATH to this worktree source for tests. Historical package PR30 is commit 161dad9. Do not rebuild v6 and call it a v7n clean rerun.

## Artifacts

Workspace `outputs/PR30_packaging.diff`, `outputs/FINAL_DAY_REVIEW.md`, refreshed `work/github_snapshot.json`. No source data, logits or credentials committed. Review contains exact matching/candidate SHA256 values.

## Next steps

1. Obtain correct v7n candidate TSV and producing run/environment manifest.
2. Reuse the already-running upstream H100 work, with explicit account access if this task must control it.
3. Update package to actual selected variant and demonstrate a clean raw-data rerun before calling it final.

## Blockers and decisions

The laptop has v7n/v7nst matching TSVs but only v6 candidates. Account/instance access and new spending have not been established. No upload, final ZIP or main merge performed. User clarification/input questions remain pending; elapsed time is not approval.
