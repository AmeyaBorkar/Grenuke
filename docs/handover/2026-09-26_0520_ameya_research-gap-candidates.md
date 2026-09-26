# Handover: research-gap-candidates

- **Author:** ameya (agent: Claude Code)
- **When (IST):** 2026-09-26 05:20
- **Branch / PR / last commit:** `ameya/research-v5` / PR opened with this handover / see `git log`. The PR also carries the France rules, `--all`, the v5 normalisation and `ANALYSIS_v4.md` from `ameya/analysis-v3`.
- **Area and paths touched:** `experiments/ameya/model-v1/` (`RESEARCH_v5.md`, `gap_check.py`, `cand_size.py`); `docs/status/ameya.md`

## TL;DR (3 lines max)

- The leaderboard is below the holdout because of France alone: US/India on test score like the holdout even re-weighted to the test's ratios, and nothing leaks.
- The holdout is recall-bound: 69% of the misses are empty-address records with a shared name.
- The organisers now rank a smaller candidate set higher. p1 ≥ 0.02 plus each record's top 2 S1 cuts it 21% (4.68 → 3.70 per S1) with the holdout unchanged.

## What was done

- **Gap analysis** (`gap_check.py`):
  - The test file is shuffled (15% France in any subset).
  - Leakage audit of `lo`, the cross-encoder, the Indic dictionary, isotonic calibration and the DP.
  - IDs and row order checked for signal (none).
  - The holdout re-weighted to the test's same-name group mix. US gets easier, not harder: v5all 0.98998 → 0.99086.
  - Predicted per S1 matches within 0.01.
  - France implied by the leaderboard: 0.925–0.944 (v2/v3).
- **Holdout anatomy of v5all** (`analysis.py`, `work/analysis/ameya-analysis-v5all/`):
  - recall 0.9713, precision 0.9988;
  - empty-address records are 69% of the misses (55% recall);
  - shared-name S1 carry 64% of the loss.
- **Candidate-set size** (`cand_size.py`): stage-1 cuts, per-S1 top k and per-record top m, with the holdout F0.5, recall, oracle and test pairs per S1 for each.
- **Three research threads running** (part 2 of `RESEARCH_v5.md`):
  - ground-truth structure and joint decoding;
  - preprocessing and vendor formats;
  - France residuals with a leaderboard-validated estimator.

## Current state

- **Works:** both scripts run end to end on the v5all artifacts; the numbers are in `RESEARCH_v5.md`.
- **Half-done:**
  - part 2 of the research;
  - the candidate-set cut is measured but not yet applied to the pipeline (`s2.py`/`cands_final.py` row rule + a stage-2 refit).
- **Known bugs and caveats:**
  - The candidate-cut F0.5 restricts the current predictions without re-deciding, so it slightly understates.
  - France's size under the cut (4.09 per S1) is still above US/India's.

## Numbers (shared holdout, `ber.eval`; include the command)

| metric | value | command / tag |
|---|---|---|
| holdout macro F0.5 v5all (US / India) | 0.99016 (0.98998 / 0.99043) | `analysis.py --scores ameya-s2-v5all --s1 ameya-s1-v5all --matches ameya-model-v5all --out ameya-analysis-v5all` |
| re-weighted to the test mix (US / India) | 0.99086 / 0.99054 | `gap_check.py --tags ameya-model-v5all` |
| candidates per S1: now → p1 ≥ 0.02 and top 2 per record | test 4.682 → 3.702; holdout F0.5 0.99016 → 0.99016 | `cand_size.py` |
| runtime | `gap_check.py` about 2 min; `cand_size.py` about 3 min; `analysis.py` about 6 min (7 GB) | |

## How to reproduce or continue (exact commands)

```
python experiments/ameya/model-v1/gap_check.py --tags ameya-model-v2,ameya-model-v3,ameya-model-v4,ameya-model-v5all
python experiments/ameya/model-v1/cand_size.py --s1 ameya-s1-v5all --matches ameya-model-v5all --final ameya-model-v5all-ops
python experiments/ameya/model-v1/analysis.py --scores ameya-s2-v5all --s1 ameya-s1-v5all --matches ameya-model-v5all --out ameya-analysis-v5all --examples 40
```

## Artifacts (local paths / drive links + sha256)

- `work/analysis/ameya-analysis-v5all/` (`report.json`, `pairs.parquet`, `s1.parquet`, `examples.txt`).
- Uploads ready, unchanged: `submissions/files/2026-09-26-v4/`, `-probe-v4-frab/`, `-v5all-ops/` (matching `f8b6245f…`) and the probes.

## Next steps (ordered, with suggested owner)

1. ameya: finish part 2 of the research, then apply the candidate cut (row rule in `s2.py` and `cands_final.py`, stage-2 refit `--all`, decide, post_ops) and package.
2. Captain: upload v4 → probe-v4-frab → v5all-ops. Read France as (LB − 0.8423) / 0.14975.

## Blockers, open questions, decisions needed

- The candidate-set weight in the final ranking is unknown. The cut costs nothing on the holdout, so we take it.
