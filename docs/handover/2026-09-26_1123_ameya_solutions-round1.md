# Handover: solutions-round1

- **Author:** ameya (agent: Claude Code)
- **When (IST):** 2026-09-26 11:23
- **Branch / PR / last commit:** `ameya/solutions-r1` (on `ameya/block-v3`) / PR opened with this handover / see `git log`
- **Area and paths touched:**
  - `ber/block/{repair,index,text,__init__}.py`, `ber/features/context.py`;
  - `experiments/ameya/model-v1/` (`stage3.py`, `legal.py`, `RESEARCH_v5.md` §8.3–8.5);
  - `docs/decisions/2026-09-26_1122_blocking-v3-repairs.md`;
  - status.

## TL;DR (3 lines max)

- Signed house-number features: holdout +0.00021 [0.00016, 0.00025] (v6nx 0.99034 vs v5 0.99013).
- Blocking repairs (domains, OCR, ordinals): dev-pool forward recall 0.972 → 0.979.
- Stage-3 joint re-scoring: +0.00005 (optional). The full v6all rebuild with all of it is running, about 3.5 h from 11:22.

## What was done

- `feats_nx.py` gate: v6nx (v5 recipe + `nx`) vs v5, Δ +0.00021 [0.00016, 0.00025]; US +0.00029, India +0.00007. DP shift +0.25.
- Blocking repairs (research agent, reviewed):
  - `repair.py`: domain/handle segmentation and OCR repair as extra name tokens for S2/S3, per-country S1 vocabularies;
  - ordinals → digits;
  - `legal.py` 5→s;
  - honorifics as stop words reverted (it cost recall).

  Tests: 106 pass.
- Stage 3 (research agent): `stage3.py`, out of fold, never trained on holdout records. +0.000051 [0.000023, 0.000079] with the cut. Not in the recipe.
- The earlier jobs were stopped by Claude Code's low-memory reaper while the session was idle. The orphaned stage 2 finished on its own; the v6nx decision was rerun at 11:22.
- `run_v6all.sh` is resumable: a done marker per step, and each heavy step waits for 12 GB free.

## Current state

- **Works:** everything above; France rules v2 and the candidate cut are on main (#25, #26).
- **Half-done:** the v6all rebuild (blocking v3 → fx5 → s1 --all → CE → s2 --all → decide with the cut → candidates → rules v2 → package `2026-09-26-v6all-ops-c2`).
- **Known bugs and caveats:**
  - Full-scale blocking memory with the repairs is untested.
  - Stage 2 of v6nx peaked at 19 GB; the `--all` versions may peak higher. Nothing else heavy can run alongside.

## Numbers (shared holdout, `ber.eval`; include the command)

| metric | value | command / tag |
|---|---|---|
| v6nx vs v5 | 0.99034 vs 0.99013, Δ +0.00021 [0.00016, 0.00025] | `decide.py --scores ameya-s2-v6nx --tag ameya-model-v6nx --base ameya-model-v5` |
| stage 3 vs v5all-c2 | 0.990207 vs 0.990156, Δ +0.000051 [0.000023, 0.000079] | `stage3.py --scores ameya-s2-v5all --tag ameya-s3-v5all --p-cand 0.02 --top-r 2` |
| blocking v3, dev pool forward recall | 0.97240 → 0.97939 (domains 0.868 → 0.937) | the agent's pool scripts (session scratchpad `deep2/blockv3/`) |

## How to reproduce or continue (exact commands)

```
bash <scratchpad>/run_v6all.sh      # resumable; state in work/logs/v6all_state/*.done
```
The steps are listed in `RESEARCH_v5.md` §8.5 and `docs/decisions/2026-09-26_1122_blocking-v3-repairs.md`.

## Artifacts (local paths / drive links + sha256)

- The current final candidate is `submissions/files/2026-09-26-v5all-ops2-c2/` (matching `76fe7eff…`).
- `2026-09-26-v6all-ops-c2` comes when the rebuild ends.
- Scores: `ameya-s2-v6nx`, `ameya-s3-v5all`. Reports: `ameya-model-v6nx`, `ameya-model-v5all-s3`.

## Next steps (ordered, with suggested owner)

1. ameya: v6all gate vs v5all-c2, then package and record.
2. Captain: uploads `v4` → `probe-v4-fr0` → the best final (`v6all-ops-c2` if its gate passes, else `v5all-ops2-c2`).

## Blockers, open questions, decisions needed

- France's level (only `probe-v4-fr0` measures it).
