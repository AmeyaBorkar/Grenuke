# Handover: final-push

- **Author:** bakshi (human / agent: Claude Code)
- **When (IST):** 2026-09-27 20:06
- **Branch / PR / last commit:** `bakshi/final-push` / #62 / `b3e3400`
- **Area and paths touched:** `experiments/bakshi/box/**` only. Ameya's `experiments/ameya/model-v1/**` (including `stack/`) was used as-is and not committed.

## TL;DR (3 lines max)

1. Rebuilt the full pipeline on rented Vast.ai boxes; it reproduces v7sq-dpc (holdout 0.991261).
2. Trained a Qwen2.5-7B France cross-encoder. As 2 of 6 votes in the stage-2 mix (g1w) it is the best US/India variant; as a rescorer of out-of-band predictions it gives a validated drop rule.
3. Both feed the single upload `mixf2` (#64, predicted ~0.99091), which Bakshi confirmed.

## What was done

- **Two-box setup.**
  - Pipeline: 2x RTX 4090.
  - Training: 4x H100. The first box was interruptible and got taken away; it was resumed from Drive checkpoints on an on-demand box.
  - Both back up to Google Drive `grenuke-train-backup` every 5 min.
- **q7st** (Qwen/Qwen2.5-7B, Apache-2.0, 7.6B).
  - `ce_llm_st.py` recipe, trained on the v7sq-dpc pseudo-labels, one OOF group per GPU (`llm_group.py`, `llm_merge.py`, resumable checkpoints).
  - Holdout AUC 0.9436, OOF 0.9396.
- **q34st** (Qwen/Qwen3-4B-Base, Apache-2.0, 4.0B): merged, not used.
- **Rebuild.**
  - `phaseA.sh`: records, dict, blocking v3, fx5, s1 v6all, e5-small, band.
  - Our band matches Ameya's to 99.9999%.
  - All cross-encoders remapped by (s1, r) (`remap_ce.py`).
- **Stage-2 variants** via `phaseB.sh`: g0 (v7sq reproduction), g1, g1w, g1x3, g7only, gbag. Each is written as -dpc and -dpcsf and audited.
- **7B rescoring** of final predictions outside the band (`score_pairs.py`).
  - Labelled check on the holdout (`rescore_eval.py`).
  - Rule: q7 logit < −6 and p1 > 0.99 → drop. +0.000033 on the holdout, both halves positive.
- **Composites per country group** (`compose_tsv.py`): A, B, B′ — all validator + strict audit PASS.
- **Error anatomy of US/India misses**, with rule checks (all closed): `analysis/`, summarised in `FINAL_PUSH_RESULTS.md` §6.

## Current state

- **Works:** everything above. Candidates are in Drive `grenuke-train-backup/candidates/`; the 7B outputs are in `…/box/out_q7st`; the rescoring files are in `…/rescore/`.
- **Half-done:** nothing. The frp/frr France variants are built but unused (superseded by `mixf2`).
- **Known bugs and caveats:**
  - `s1.py` and `s2.py` hard-code a report-only comparison with `matches/ameya-baseline-v0`. On a fresh box that crashes at the end of stage 1.
  - Workaround used: an EMPTY placeholder tag, written by `ops/run_chain3.sh`. Ignore `gate_vs_baseline` in those reports.
  - `decide_c2` output is unused downstream and was skipped by marker, saving 12 min per variant.

## Numbers (shared holdout, `ber.eval`; include the command)

| metric | value | command / tag |
|---|---|---|
| holdout macro F0.5 g0 (v7sq reproduction) | 0.991261 | `phaseB.sh g0 "e5l qst e5ls bge" pseudo_s2_fr_v7ce3` → `ameya-model-g0-s3` |
| holdout macro F0.5 g1w (7B ×2) | 0.991323 | `phaseB.sh g1w "e5l qst e5ls bge q7st q7st" …` |
| 7B drop rule (holdout sample, 186,897 S1) | +0.000033 (A +0.000022 / B +0.000043) | `rescore_eval.py --out-band-only`, t = −6 |
| q7st band AUC | holdout 0.9436, OOF 0.9396 | `out_q7st/config.json` |
| blocking reproduction | 66,429,057 / 58,437,794 pairs; band coverage 99.9999% | `phaseA.sh`, `band_check` |
| runtime | rebuild ~1 h 45 m on 64 vCPU; variant ~35–60 min; 7B ~1 h 20 m training + ~50 m scoring per group on H100 | logs in Drive `pipeline/logs`, `logs/` |

## How to reproduce or continue (exact commands)

```
# boxes: see experiments/bakshi/box/HANDOFF.md (setup.sh / train_jobs.sh)
bash experiments/bakshi/box/phaseA.sh
bash experiments/bakshi/box/phaseB.sh g1w "e5l qst e5ls bge q7st q7st" box_ameya/pseudo_s2_fr_v7ce3.parquet
# 7B training (one group per GPU): bash experiments/bakshi/box/train_jobs.sh setup && ... launch
python experiments/bakshi/box/rescore_export.py --final <final tag> --s3 <s3 tag> --pred <s3 decision tag> --out DIR
CUDA_VISIBLE_DEVICES=0 python experiments/bakshi/box/score_pairs.py --pairs DIR/x.parquet --split test --adapter box/out_q7st/adapter_0 --out DIR/x_scored.parquet
python experiments/bakshi/box/rescore_eval.py --dir DIR --out-band-only
python experiments/bakshi/box/compose_tsv.py --labelled A --unlabelled B --s1-tsv test_source1.tsv --train-s1-tsv train_source1.tsv --drop "DIR/*_scored*.parquet" --out OUT
```

## Artifacts (local paths / drive links + sha256)

- **Drive** `grenuke-train-backup` (https://drive.google.com/drive/folders/1czpvbONZ_nvG7JOdyHgD0jOk2aIeICgL):
  - `box/out_q7st` and `box/out_q34st`: ce_train/ce_test/config + adapters;
  - `rescore/`: fr/hold/usin scored pairs;
  - `pipeline/output/<variant>/<dpc|dpcsf|dpcsfq|frp|frr>/`;
  - `candidates/`.
- **Composite B:** matching `df4bccd785b3fa785b7edcf0532288bcddc0010e2e31ce6f358064529ecb62e8`, candidates `58c824a3f61c184fe7da1a448a4ac94284f288feff9c351abfe16a3dfc0520e5`.
- **Composite B′:** matching `723be3338b52e6279bbd8b11b682bfdd7bdde2ed87f5c7035e194d07779b1968`.
- **g1w-dpcsfq:** matching `ddb969c49167a32570e66cccd5d30a5d3437bc818d85c3ad1b792bdc1cdc3296`.

## Next steps (ordered, with suggested owner)

1. Captain: upload `mixf2` after the 20:40 confirmation window (#64).
2. Ameya: final package / documentation. Include Bakshi's components:
   - q7st (model, licence, recipe);
   - the 7B drop rule (`score_pairs.py`, `rescore_eval.py`);
   - g1w India.
3. Bakshi: close the 4090 box when no rebuild is needed. Revoke the GitHub token used today, and remove the `grenuke-vast` SSH key from Vast.

## Blockers, open questions, decisions needed

- **Best vs final.** Whether the private leaderboard uses the best or the final upload was reported both ways today. With a single upload tonight it doesn't matter.
