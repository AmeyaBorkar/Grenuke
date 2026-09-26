# Handover: ce-large-box

- **Author:** ameya (agent: Claude Code)
- **When (IST):** 2026-09-26 18:17 (updated 19:00)
- **Branch / PR / last commit:** `ameya/ce-large` / PR opened with this handover / see `git log`
- **Area and paths touched:**
  - `experiments/ameya/model-v1/ce_box.py`, `ce_import.py`, `acr_join.py`, `brand_join.py` (new);
  - `RESEARCH_v6.md` §4–5;
  - status.

## TL;DR (3 lines max)

- A rented H100 (Vast.ai) trained multilingual-e5-large and e5-base cross-encoders on the uncertain band. e5-large's holdout band AUC is 0.939 (e5-small 0.924, stage-1 p1 0.930). The stage-2 retrain with all three logits (`ameya-s2-v7ce3`) is running locally, then the holdout gate.
- French acronym copies at the S1's address, found by a join, add 3,872 true-looking pairs (US holdout 99.7% true): package `2026-09-26-v6all-s3-ops3a-c2`.
- New-data tests on India: self-training +0.0009 (3 seeds). Rule labels do not help. No France retrain on either.

## What was done

- **The box** (`ssh -p 40913 root@93.91.156.92`, key `~/.ssh/grenuke_vast`, host alias `grenuke-vast`):
  - H100 80 GB, 23 cores, 342 GB RAM in the container; `/workspace` is **not** persistent.
  - Set up: PyTorch 2.14 (cu126), XGBoost 3.4, transformers 5.17, the `ber` package; env in `/workspace/grenuke/env.sh`.
  - Uploaded: code archive, records (1.1 GB), models `ameya-fx1`, `ameya-fx5`, band pairs (38 MB).
  - Ran `ce_box.py` for e5-large and e5-base at the same time.
  - Traffic: about 7.8 GB of the 30 GB budget.
- **India stand-in for France** (`r6/loco_rules*.py`, scratchpad): rule labels and self-training, 3 seeds.
- **French acronym join** (`acr_join.py`): measured on the holdout, applied to France, packaged.
- **Brand-name rule** (`brand_join.py`): holdout measurement running; not applied.

## Current state

- **Works:** everything above. `2026-09-26-v6all-s3-ops3a-c2` is packaged (validator PASS).
- **Half-done:**
  - `run_v7ce.sh 1` (scratchpad) is on the stage-2 retrain. The remaining steps are decide + gate vs v6all-c2 → stage 3 → decide + gate vs v6all-s3 → rules v3 → acronym join → package `2026-09-27-v7ce3-s3-ops3a-c2`.
  - The brand rule is measured only if the holdout truth is ≥ 0.9.
- **Known bugs and caveats:**
  - The box's disk is not persistent. Everything needed has been copied back (`scratchpad/box/out_e5l`, `out_e5b`).
  - The acronym rule is 66% true on India, because of India's compound addresses. It is applied to unlabelled countries only (France).

## Numbers (shared holdout, `ber.eval`; include the command)

| metric | value | command / tag |
|---|---|---|
| e5-large band AUC OOF / holdout | 0.9350 / 0.9391 | `ce_box.py --model intfloat/multilingual-e5-large --lr 2e-5 --name e5l` |
| e5-base band AUC OOF / holdout | 0.9244 / 0.9287 | `ce_box.py --model intfloat/multilingual-e5-base --lr 3e-5 --name e5b` |
| acronym-at-address truth (holdout) | US 0.9972 (723), India 0.6609 (758) | `acr_join.py --split train` |
| India LOCO, self-training | +0.0009 mean over 3 seeds (stage 1) | scratchpad `r6/loco_rules3.py` |

## How to reproduce or continue (exact commands)

```
# box: band pairs exported locally with ce.band_pairs("ameya-s1-v6all", split) -> $CE_BOX_DIR/band_{train,test}.parquet
python ce_box.py --model intfloat/multilingual-e5-large --lr 2e-5 --name e5l
# local
python ce_import.py --feats ameya-fx5 --src <out_e5l> --group cel --column cel__logit
python ce_import.py --feats ameya-fx5 --src <out_e5b> --group ceb --column ceb__logit
python s2.py --feats ameya-fx5 --s1 ameya-s1-v6all --tag ameya-s2-v7ce3 --groups str,cx,lo0,lg,ce,cel,ceb,nx --cluster --extra $LEG,ce__logit,cel__logit,ceb__logit,$NX --all
python acr_join.py --split test --matches <final tag> --cands <cands tag> --tag <new> --cands-tag <new>
```

## Artifacts (local paths / drive links + sha256)

- `submissions/files/2026-09-26-v6all-s3-ops3a-c2/`: matching `8d4e3bbca4355aeedf0e588025121b66b823cea250180793033b5af33dd4c5dc`, candidates `5e991eca80bf4535f391f5e6f408d4d2414d7aadf10abc51c044dd9aac13b89f`.
- Cross-encoder logits: scratchpad `box/out_e5l`, `box/out_e5b`; feature groups `work/features/ameya-fx5-{cel,ceb}`.

## Next steps (ordered, with suggested owner)

1. ameya: read the v7ce3 holdout gate. If it passes, the package `2026-09-27-v7ce3-s3-ops3a-c2` is the next candidate.
2. Captain: upload in this order: candidate (`v6all-s3-ops3a-c2` today, or v7ce3 if it passes), `probe-v6s3-fr0`, `probe-v6s3-fr090`, then re-upload the best last.
3. ameya: apply the brand rule if its holdout truth is ≥ 0.9.

## Blockers, open questions, decisions needed

- Upload slots, and the scores.
- When to stop the Vast.ai instance: it costs money while running, and nothing on it is needed after the logits were copied back.
