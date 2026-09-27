# Handover: final-upload

- **Author:** ameya (human / agent: Claude Code)
- **When (IST):** 2026-09-27 20:14
- **Branch / PR / last commit:** `ameya/final-stack` / PR opened with this handover / `ea2067b` (the notes and `compose3.py`)
- **Area and paths touched:**
  - `experiments/ameya/model-v1/RESEARCH_v6.md` §6.19
  - `experiments/ameya/model-v1/stack/compose3.py`
  - earlier today on this branch: `ce_box.py`, `stack/dp_france.py`, `ce_synth2.py`, `synth_fr2.py`, `synth_fr3.py`

## TL;DR (3 lines max)

- The team agreed on one final upload, `mixf2`, in issue #64 (Bakshi and Sachi confirmed). Predicted about 0.99091, against the measured 0.990699 (mixmdp).
- Recipe: US v7sq3-dpc + India g1w-dpc (Bakshi's 7B ×2) + France v7sq6r3-dpc (round-3 labels), minus the out-of-band pairs Bakshi's 7B rejects (832 France, 310 US/India).
- 0.992 was not reached. US/India sits at this model family's ceiling, and France is limited by generic-name decoys and missed recall.

## What was done

- **Round-3 stage-2 labels:** mixmdp's guarded French decisions ×3.
  - v7sq6r3 cal +215e-6 vs v7sq-dpc; round 2 gave +159 to +179.
  - Round 4 (v7sq6r4) adds nothing on its own (+212).
- **synth3:** a French generator matched to the real operation mix, plus six synthetic cross-encoders on three GPUs.
  - v7sqsyc cal +249, but weak corroboration (own-holdout +51).
- **Bakshi's 7B `q7st`, used three ways:**
  1. India via g1w: +66.1e-6 F on the holdout, P 0.998.
  2. Out-of-band rescoring: drop when logit < −6. Holdout +33e-6, both halves positive.
     - The French rejects are same name + same house number + different street decoys with generic names.
     - On the labelled holdout that pattern is 0.5% true where our model rejected it, with 7B median −9.9, and 99.7% true where it predicted it, with 7B median +7.9.
  3. Recall: rejected. Precision tops out at 71%, below the ~75% break-even.
- **Negative results, all in §6.19:**
  - synthetic cross-encoders as detectors;
  - empty-address and acronym recall rules;
  - reassigning the rejected records;
  - g1x3 / g7only for India;
  - US from g1w.

## Current state

- **Works:** `mixf2`, `mixf3`, `mixf4`, `mixqq` and `mixqc` are all built; validator PASS and strict audit PASS.
- **Half-done:** v7sqsyd (all six synthetic cross-encoders + round 3) is still being built and valued (~20:30). It is recorded only; the upload is decided.
- **Known bugs and caveats:**
  - Stage 3 is not bit-reproducible across machines (about 500 decisions differ).
  - The 7B drop lists come from Bakshi's scores (adapter_0). Pairs not in his scored sets are never dropped.
  - `mixf2`'s France depends on round-3 labels, which have no leaderboard measurement yet.

## Numbers (shared holdout, `ber.eval`; include the command)

| metric | value | command / tag |
|---|---|---|
| holdout macro F0.5, US/India | v7sq3 combo 0.991307; g1w India +66.1e-6 F (P 0.998) | fdiff agent's paired bootstrap, `agents/fdiff/boot.txt` |
| 7B drop rule (holdout sample, 186,897 S1) | +0.000033 (halves +0.000022 / +0.000043) | Bakshi's `rescore_eval.py --out-band-only` |
| France (no labels): cal vs v7sq-dpc | v7sq6r3 +215e-6; mixmdp's France +146, measured about +134 | fdiff agent's `bt_cal.py` |
| leaderboard | mixmdp 0.990699 (measured); `mixf2` pending upload | |

## How to reproduce or continue (exact commands)

```
# per-country compose + drops + package (the laptop's work dir has every tag)
python experiments/ameya/model-v1/stack/compose3.py mixf2 ameya-cands-mixqc \
  US=ameya-model-v7sq3-s3-ops3a-dpc India=<g1w_india_test.parquet> France=ameya-model-v7sq6r3-s3-ops3a-dpc \
  --drop <drop_q7_fr.parquet> --drop <drop_q7_usin.parquet>
bash <scratchpad>/package6.sh ameya-model-mixf2 ameya-cands-mixf2 2026-09-27-mixf2-c2   # then validator + audit
# drop lists: Bakshi's score_pairs.py (adapter_0) on the final pairs, keep q7__logit < -6 and p1 > 0.99
```

## Artifacts (local paths / drive links + sha256)

- `submissions/files/2026-09-27-mixf2-c2/`: `matching_results.tsv` `4c3b4527d608fdf5…`, `candidate_pairs.tsv` `d2c7af15cf5331fd…`.
- The same files are in `Downloads/` as `matching_resultsv7sq6r3-g1wIndia-q7all.tsv` and `candidate_pairsv7sq6r3-g1wIndia-q7all.tsv`.
- Alternatives:
  - `mixf4` `9267f34c74a29560…` (France v7sq6r4 + DP);
  - `mixf3` `bec18446ebbf39c3…` (France v7sqsyc);
  - Bakshi's Composite B `df4bccd7…` (in Drive `grenuke-train-backup/candidates/`).
- Bakshi's 7B outputs and rescoring files: Drive `grenuke-train-backup`. Local copies: `work/bakshi_pull/`.

## Next steps (ordered, with suggested owner)

1. Upload `mixf2` and record the score in `CHANGELOG.md` and `submissions/records/`. Owner: Ameya.
2. If the score differs from 0.99091 by more than ±0.00005, split it with the parts in §6.19. France is the least certain part.
3. Destroy the rented instances (grenuke-vast3 H100, both RTX 5090s) and remove the session SSH keys (`~/.ssh/grenuke_vast`, `~/.ssh/grenuke_vast2`). Owner: Ameya.
4. Final documentation: merge Bakshi's `COMPONENTS_FOR_DOC.md` (PR #62) into the solution document. Owner: Bakshi / Ameya.

## Blockers, open questions, decisions needed

- Does the leaderboard keep the best upload or the last one? The team does one upload tonight, so the question does not change the choice.
