# Handover: research-part2-plan

- **Author:** ameya (agent: Claude Code)
- **When (IST):** 2026-09-26 05:54
- **Branch / PR / last commit:** `ameya/cands-cut` / PR opened with this handover / see `git log`
- **Area and paths touched:**
  - `experiments/ameya/model-v1/`: `RESEARCH_v5.md` part 2, `common.candidate_mask`, `decide.py`/`cands_final.py` `--p-cand/--top-r`;
  - `docs/decisions/2026-09-26_0532_candidate-set-cut.md`;
  - status.

## TL;DR (3 lines max)

- Three research threads are done:
  - US/India are at the Bayes limit (structure priors +0.00011);
  - vendor formats are not a loss source;
  - France is about 0.959 with v5all + rules, so the leaderboard should be about 0.985.
- The candidate set is cut to 3.70 per S1 at no cost. The final candidate is now `2026-09-26-v5all-ops-c2`.
- Ranked plan in `RESEARCH_v5.md` §7. The largest open France question is the weak-address and unrelated-name acceptance (123 per 1000 S1).

## What was done

- **Ground-truth structure** (research thread):
  - one owner per record;
  - T independent of anything observable;
  - S2/S3 counts drawn independently (caps 5/6);
  - addresses dropped independently (4.41%);
  - orphans almost never lack an address, so a weak-address record is a true copy 97.7% of the time.

  Joint re-scoring (stage 3 + record-mass calibration): +0.00011 [0.00007, 0.00015].
- **Preprocessing** (research thread): FN lift of every normalisation residual. Remaining blocking gains: domains, OCR, ordinals, +0.0003–0.0005. Signed number features: +0.0001–0.0002.
- **France** (research thread):
  - a structural edit-profile estimator, share-shift form, validated on v2/v3 against the leaderboard (0.936/0.930 vs 0.929/0.927);
  - France is 0.946 (v4) and 0.959 (v4/v5all + rules);
  - patterns a–e are worth +0.003 France F0.5;
  - two constant families (weak address, unrelated name) carry most of the remaining gap.
- **Candidate-set cut** implemented and packaged (`2026-09-26-v5all-ops-c2`, PASS, 3.70 per S1, holdout tie).
- **Experiment started:** `feats_nx.py` (signed house-number relations, row-aligned group `ameya-fx4-nx`) → `ameya-s1-v6nx`/`ameya-s2-v6nx`/`ameya-model-v6nx`, compared with v5.

## Current state

- **Works:** the candidate cut; the research documents; the `nx` feature files (train and test, row-aligned).
- **Half-done:**
  - the v6nx refit (running);
  - `post_ops.py` extensions for patterns a–e;
  - research on the France weak-address and unrelated-name families;
  - stage 3.
- **Known bugs and caveats:**
  - The France estimator's level is 0.002–0.007 optimistic on v2/v3; version differences are more reliable than the level.
  - The two forecasts disagree: the leave-one-country-out one gave 0.987–0.989 for v4, the share-shift one 0.983–0.984.

## Numbers (shared holdout, `ber.eval`; include the command)

| metric | value | command / tag |
|---|---|---|
| holdout v5all vs v5all with the cut | 0.990159 vs 0.990156, Δ −0.000003 [−0.000015, +0.000011] | `decide.py --scores ameya-s2-v5all --tag ameya-model-v5all-c2 --base ameya-model-v5all --p-cand 0.02 --top-r 2` |
| candidates per test S1 (US / India / France) | 3.70 (3.66 / 3.61 / 4.09) | `cands_final.py --s1 ameya-s1-v5all --tag ameya-cands-v5all-c2 --p-cand 0.02 --top-r 2` |
| France estimates v2 / v3 / v4 / v4+rules / v5all / v5all+rules | 0.936 / 0.930 / 0.946 / 0.959 / 0.945 / 0.959 | scratchpad `deep2/france/est_fp2.py` |
| joint re-scoring A+B | +0.00011 [0.00007, 0.00015] | scratchpad `deep2/structure/s10_combo.py` |

## How to reproduce or continue (exact commands)

```
python experiments/ameya/model-v1/post_ops.py --matches ameya-model-v5all-c2 --scores ameya-s2-v5all --cands ameya-cands-v5all-c2 --feats ameya-fx4 --tag ameya-model-v5all-c2-ops
python experiments/ameya/model-v1/feats_nx.py --feats ameya-fx4 --split train   # and --split test
python experiments/ameya/model-v1/s1.py --feats ameya-fx4 --tag ameya-s1-v6nx --groups str,cx,lo0,lg,nx --drop leg__r_only_bits,leg__s1_only_bits
```

## Artifacts (local paths / drive links + sha256)

- `submissions/files/2026-09-26-v5all-ops-c2/`:
  - matching `482caa7b81078640e60739cdb8a5c7b10536bdb07bfc6dd5947c00ae6d940cc3`;
  - candidates `a27e867995e0f25896773b4cae27b64f48d0014ea0bbfd1f1be9718ac8b4e695`.
- `work/features/ameya-fx4-nx/{train,test}.parquet`.

## Next steps (ordered, with suggested owner)

1. Captain: upload `2026-09-26-v4`, `-probe-v4-frab` and `-v5all-ops-c2`; `-probe-v4-fr0` if possible. France = (LB − 0.8423) / 0.14975.
2. ameya: `post_ops.py` patterns a–e; v6nx result; research agents on the France weak-address and unrelated-name families and on stage 3.
3. If time: the blocking rebuild (domains, OCR, ordinals).

## Blockers, open questions, decisions needed

- Are France's weak-address and unrelated-name acceptances real false positives? Up to +0.003 on the leaderboard if so.
