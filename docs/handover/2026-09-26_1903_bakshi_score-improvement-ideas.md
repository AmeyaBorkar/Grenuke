# Handover: complete progress capsule

- Author: Bakshi
- Branch: `bakshi/progress-capsule`, from main `017f2e6`.
- Scope: documentation and read-only analysis; no matching/model changes.

## TL;DR

Pulled latest GitHub and created `experiments/bakshi/PROGRESS_CAPSULE.md` with full paths, hashes, results, failed ideas and continuation steps. Latest upstream v7ce3 passes its gate; supplied local files are the older v6all-stage3-rules3 package.

## What was done

Identified local matching/candidate hashes, audited all local v6 predictions and compared with v5. Read PR39/40/41 and current research/recipe/decision/status. User requested suggestions only, then a complete capsule; no new implementation.

## Current state

- Works: latest repository inventory, full local read-only v6 audit, complete capsule.
- Pending: exact new public scores and uploaded-file identity; v7b outcome; current integration artifacts.
- Caveats: omitted older predictions are not known true matches; no test labels; historical dev-v3 scores cannot gate current v7.

## Numbers

| result | value | source |
|---|---:|---|
| latest upstream holdout | 0.991138 | ameya-s3-v7ce3, upstream decision 2026-09-26_1933 |
| upstream paired gain vs v6all-stage3 | +0.000296 [0.000252, 0.000342] | not rerun locally |
| local v6 rows / pairs | 1,732,544 / 5,856,439 | audit_tsv.py --tag bakshi-tsv-v6-review |
| ownership conflicts | 0 | same audit |
| supplied candidate pairs | 6,406,457 | workspace candidate_v6_review.py |
| runtime / peak RAM | not instrumented | no training |

## How to reproduce or continue

Use capsule environment and paths. Probe scripts are on `bakshi/v7-tsv-audit` (PR37), not all merged main. Refresh GitHub before future work; latest v7b may supersede this snapshot. Keep suggestions as suggestions until implementation is requested.

## Artifacts

Workspace `work/GrenukeGit2/work/v7/bakshi-tsv-v6-review/{base_pairs.parquet,summary.json}`, `work/candidate_v6_review.json`, `work/github_snapshot.json`. Capsule gives absolute paths and full hashes. No data/model files committed.

## Next steps

1. Bakshi: record exact newer public scores and uploaded-file hash when supplied.
2. Bakshi: inspect v7b gate and same-baseline France probes before further recommendations.
3. Preserve analysis-only scope.

## Blockers and decisions

New scores and full current v7 artifacts remain unavailable locally. Deadline reports conflict; work to 27 Sep 21:00 IST until confirmed. No leaderboard upload, remote GPU action, main merge or final choice performed.
