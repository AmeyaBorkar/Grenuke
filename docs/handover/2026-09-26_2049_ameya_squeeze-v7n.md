# Handover: squeeze-v7n (the late-evening squeeze)

- **Author:** ameya (agent: Claude Code)
- **When (IST):** 2026-09-26 20:49 (updated 23:15)
- **Branch / PR / last commit:** `ameya/squeeze` / PR opened with this handover / see `git log`
- **Area and paths touched:**
  - `experiments/ameya/model-v1/`:
    - `s2.py` (`--seed`, `--param`, `--pseudo`);
    - `ce_box.py` (`--pseudo`);
    - new: `bag_scores.py`, `fr_add.py`, `pseudo_labels.py`;
    - `RESEARCH_v6.md` §6;
  - decision record `2026-09-26_2135_model-v7n.md`;
  - status and this handover.

## TL;DR (3 lines max)

- **v7n (`2026-09-27-v7n-s3-ops3a-c2`) scored 0.989721, rank 8** (+0.00111 over v6all), so France is about 0.978. Stage 2 gets e5-small plus the mean of two e5-large cross-encoders.
- **France is the whole gap.** v6all's 0.988609 means France is at about 0.973. The cross-encoders are what lift it: the French rule-population AUC went 0.855 → 0.872. On French pairs the models disagree 4× as often, hence the mean.
- **Next:** `v7nst` (+ France stage-2 self-training; packaged), then v7m/v7s from the new H100. 0.99 needs France at 0.9801.

## What was done

- **Stage-2 settings, all no gain (§6.1):**
  - seed bagging: −0.00004;
  - `max_depth` 8;
  - eta 0.03.
- **Cross-encoders on the rented H100 (§6.5):**
  - e5-large with 2 epochs: band AUC 0.9441 (1 epoch: 0.9391);
  - BAAI/bge-reranker-v2-m3 (Apache-2.0): 0.9418;
  - a z-mean of the two e5-large runs: 0.9429.
- **France, label-free (§6.2, §6.6, §6.8):**
  - stage-1 bands: France has 2.5–3× the uncertain pairs;
  - per-source counts: fine;
  - domain join: nothing left;
  - "SNC": a look-alike legal form, correctly rejected;
  - record ids: shuffled;
  - the cross-encoders disagree 4× as often on France (12% vs 3%);
  - **a new check**: the AUC of pc on France's rule populations, whose truth is known from US/India. It ranks models by French competence without labels.
- **Stage-2 variants, gated on the box:**
  - v7c (five separate logits): c2 +0.000071, s3 +0.000114;
  - v7m (e5-small + mean of e5l, e5l2, bge): c2 +0.000050; best French AUC, 0.878.
- **The box was lost (§6.9):** a spot instance, interrupted at 21:40. **v7n** rebuilt v7m's design locally without bge: c2 +0.000072, s3 +0.000073, French AUC 0.872.
- **France probes redesigned (§6.4):**
  - `fr090r` cuts before the rules (`make_frcut.sh`), so the rules re-add their true copies;
  - the old `fr090` dropped them;
  - `frlo` (`fr_add.py`) is mostly ties, so it has low value.
- **Self-training on France (§6.7):**
  - pseudo-labels (`pseudo_labels.py`): confident decisions plus the rules' adds and op-B drops;
  - cross-fitted in both the cross-encoder (`ce_box.py --pseudo`, lost with the box) and stage 2 (`s2.py --pseudo`, v7nst, running locally).

## Current state

- **Works:** v7n and its probes are packaged (validator PASS).
- **Half-done:** on the new on-demand H100, bge (for v7m) and the France self-trained e5-large (for v7s) are training, ETA 23:55 and 00:50; the local chains follow.
- **Known bugs and caveats:**
  - the self-training variants can't be gated on the holdout (no France there); only the leaderboard can judge them;
  - bge's logits and the self-trained e5-large were lost with the spot box.

## Numbers (shared holdout, `ber.eval`; include the command)

| metric | value | command / tag |
|---|---|---|
| v7n holdout macro F0.5, c2 / s3 | 0.991171 / 0.991211 (US 0.991018, India 0.991500) | `run_local_full.sh v7n str,cx,lo0,lg,ce,cem2,nx ce__logit,cem2__logit` |
| gate vs v7ce3, c2 / s3 | +0.000072 [+0.000040, +0.000103] / +0.000073 [+0.000041, +0.000102] | `decide.py --base ameya-model-v7ce3-c2` / `-s3` |
| French rule-population AUC (v6all / v7ce3 / v7n / v7c / v7m) | 0.855 / 0.865 / 0.872 / 0.874 / 0.878 | scratchpad `box/rule_auc.py` |
| predicted LB for v7n | 0.843226 + 0.14975 × F_France: 0.9889 / 0.9894 / 0.9900 at France 0.973 / 0.976 / 0.980 | |

## How to reproduce or continue (exact commands)

```
# the mean of the two e5-large runs as one feature (both run dirs from ce_box.py)
python experiments/ameya/model-v1/zmean_ce.py out_cem2 out_e5l out_e5l2   # z from the train band
python ce_import.py --feats ameya-fx5 --src out_cem2 --group cem2 --column cem2__logit
python s2.py --feats ameya-fx5 --s1 ameya-s1-v6all --tag ameya-s2-v7n --groups str,cx,lo0,lg,ce,cem2,nx --cluster \
  --extra $LEG,ce__logit,cem2__logit,$NX --all
python decide.py --scores ameya-s2-v7n --col pc --tag ameya-model-v7n-c2 --base ameya-model-v7ce3-c2 --p-cand 0.02 --top-r 2
python stage3.py --scores ameya-s2-v7n --tag ameya-s3-v7n --p-cand 0.02 --top-r 2
python decide.py --scores ameya-s3-v7n --col pc --tag ameya-model-v7n-s3 --base ameya-model-v7ce3-s3 --p-cand 0.02 --top-r 2
python post_ops.py --matches ameya-model-v7n-s3 --scores ameya-s3-v7n --cands ameya-cands-v6all-c2 --feats ameya-fx5 \
  --tag ameya-model-v7n-s3-ops3 --robust-addr
python acr_join.py --split test --matches ameya-model-v7n-s3-ops3 --cands ameya-cands-v6all-c2 --tag ameya-model-v7n-s3-ops3a \
  --cands-tag ameya-cands-v7n-c2a
# France cut before the rules (probe): fr_threshold.py on the model's matches, then post_ops + acr_join as above
python fr_threshold.py --final ameya-model-v7n-s3 --model ameya-model-v7n-s3 --scores ameya-s3-v7n --thr 0.9 --tag <tag>
# stage-2 self-training: pseudo-labels from a finished chain, then s2.py --pseudo
python pseudo_labels.py ameya-model-v7ce3-s3 ameya-s3-v7ce3 ameya-model-v7ce3-s3-ops3 ameya-model-v7ce3-s3-ops3a s1:ameya-s1-v6all <out>
python s2.py ... --all --pseudo <out>
```

## Artifacts (local paths / drive links + sha256)

- `submissions/files/2026-09-27-v7n-s3-ops3a-c2/`:
  - matching `9b902971c72ada328bb9a23e1cdae3ec171c08239034114d5f9c60d9eaa92ae5`;
  - candidates `7246d9ec1ca32ea89bce1ec30f84a997af98bce7b33b7cfae3c21679ddcc31c3`.
- `submissions/files/2026-09-27-probe-v7n-fr090r/`:
  - matching `f18f08981261f65ad3a93292612061f282a504c33c909041e5f973c03826329c`;
  - candidates `40ddeeb143a845a332cc86e1e4303f5074b67c0fdeb29cae2dd8792caa8de8a4`.
- `submissions/files/2026-09-27-probe-v7n-fr095r/` (drops 114.1 per 1000 French S1 before the rules):
  - matching `33a7b2db85f67274bd8fe170ea264a9cbd5d53e103f5cf0801f856ac21492459`;
  - candidates `3386ad04a75d9c578a8cf9114a28da7c8573f7fe0b187b141a56f8ee08c58db7`.
- `submissions/files/2026-09-27-probe-v7n-fr080r/` (drops 36.5 per 1000):
  - matching `cb0f02fd7ef7b1c0ac15056f1ea251cf5164aa2393c1b9382e69914dbb32fe73`;
  - candidates `8c5205a98a2ccb75a2ab4739d561a3dafc62d01b4f523fb84d75c9009ae287cf`.
- The cross-encoder logits are in the scratchpad (`box/out_e5l`, `out_e5l2`, `out_e5b`, `out_cem2`), and the pseudo-labels in `box/pseudo_*`.

## Next steps (ordered, with suggested owner)

1. **Captain, 27 Sep:**
   - upload v7n, then `probe-v7n-fr090r`;
   - then `fr095r` if the probe wins, `fr080r` if it loses;
   - then v7nst if it's built;
   - **re-upload the best last**: the final submission counts.
2. **ameya:** read each score as France = (LB − 0.843226) / 0.14975, and pick the France cut.
3. **If the spot box returns with its disk:** copy `out_bge` (20 MB) and rebuild v7m locally (`zmean_ce.py` over e5l, e5l2, bge). Its French AUC is 0.878, against v7n's 0.872.

## Blockers, open questions, decisions needed

- Upload slots and scores (captain).
- The Vast.ai spot instance: destroy it when done. Remove the `grenuke_vast` key from `~/.ssh` after the competition.
