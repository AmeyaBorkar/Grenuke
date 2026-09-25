# Handover: block-v0-baseline

- **Author:** ameya (human; the agent was Claude Code)
- **When (IST):** 2026-09-25 17:06
- **Branch / PR / last commit:** `ameya/block-v0` / PR #15 / the head of the branch
- **Area and paths touched:**
  - `src/ber/block/**` (blocking v0);
  - `src/ber/features/context.py` (context groups, #12);
  - `src/ber/pipeline.py` (error fix);
  - `pyproject.toml` (numba is now core) and `docs/DEVELOPMENT.md`;
  - `experiments/ameya/{block-v0,baseline}/`.

## TL;DR (3 lines max)

Blocking v0 reaches holdout pair recall 0.975 and oracle F0.5 0.991 at 29 candidates per S1. It uses a token view plus a name-only view for short addresses, with Indic transliteration and skeletons. The baseline (pair signals + XGBoost + argmax + threshold) scores **0.9683 holdout macro F0.5**, and its files pass the validator. They are Submission 1. The dev kit for small machines is built.

## What was done

- **`ber.block`: its own tokenizer, so blocking doesn't wait for normalize.**
  - Tokenizer:
    - NFKD fold;
    - legal forms, honorifics and markers dropped;
    - street types and ordinals canonicalized;
    - leading zeros stripped from numbers.
  - One ISCII table transliterates the 9 Indic scripts, and name tokens add consonant-skeleton keys.
  - int64 keys include compound tokens: (number, word), (number, name token) and name pairs.
  - IDF and vocabulary are fitted per exact country label.
- **Search:** numba top-k in both directions. Rare tokens seed the candidates; the best 200–400 are re-scored exactly with every shared token.
- **Views:** `tok` (bit 64) and `name_short` (bit 4: names only, for records with ≤3 address tokens). They merge with per-view score and ranks.
- **Trim, chosen from the recall curve:** keep the record in the S1's top 15, or the S1 in the record's top 4.
  - The record side matters most: at trim 10/4, recall is 0.9745 at 26 candidates per S1.
- **`ber.features.context.compute(cands, s1_records)`** returns:
  - retrieval score and ranks per view, and the number of views;
  - the gaps to the best candidate and the record's margin over its best other S1;
  - candidate counts;
  - log-counts (not rates) of S1 sharing the name key or the (number, street) key.
- **Baseline (`experiments/ameya/baseline/baseline_v0.py`):**
  - 37 pair signals, XGBoost on the GPU trained on 30% of training-fold S1 (folds 5–16, early stopping on 17–19);
  - every pair scored, argmax ownership per record, threshold 0.675 tuned on the holdout;
  - it also writes the dev-sample features (C8 layout) for Sachi.

## Current state

- **Works:**
  - full train and test candidates: `ameya-block-v0` (train 64.0M pairs, test 56.8M);
  - the wide run `ameya-block-v0-wide`, before the trim;
  - dev candidates `ameya-block-v0-dev`;
  - baseline matches `ameya-baseline-v0`;
  - the submission files in `output/`, archived in `submissions/files/2026-09-25-01/`.
- **Half-done:**
  - the Submission 1 upload, record and tag. The file is ready; the captain uploads it.
  - G1 is not met yet: 0.975 against 0.990.
- **Known caveats:**
  - India recall is 0.959 against 0.986 for the US. The remaining misses are mostly Indic names with short addresses, plus empty addresses and typos.
  - Full blocking takes about 19 min for train and 15 min for test. Most of that is single-threaded: tokenization (about 2.5 min) and the final merge and write.
  - The baseline stopped at the round limit (800, logloss still falling), so more rounds would help.
  - `inplace_predict` warns about a CPU/GPU copy. That is harmless.

## Numbers (shared holdout, `ber.eval`)

| metric | value | command / tag |
|---|---|---|
| blocking pair recall | 0.9752 (US 0.9860, India 0.9590; S2 0.9737, S3 0.9766) | `--stage evaluate --tag ameya-block-v0` |
| oracle F0.5 / candidates per S1 | 0.9914 / 29.0 (p99 107) | same |
| wide (tok 40/4 + name_short) | recall 0.9775 at 49.8 per S1 | `trim_curve.py ameya-block-v0-wide` |
| baseline macro F0.5 | **0.9683** (US 0.9765, India 0.9561; singletons 0.9587) | `baseline_v0.py --cands ameya-block-v0 --tag ameya-baseline-v0` |
| baseline micro precision / recall | 0.9898 / 0.9347 | same |
| mean predicted matches per S1 | holdout US 3.31, India 3.20; test US 3.28, India 3.16, France 3.26 | same |
| validator | PASS with `--check-ids`; 105,648 empty rows | `validate_submission.py ... --check-ids` |
| `matching_results.tsv` | 94.3 MB, sha256 `02da444e8fc28348babf59e9871f3a5dc58d61805f979828f416d9e90fb6f992` | — |

## How to reproduce or continue (exact commands)

```
export BER_DATA_DIR=... BER_WORK_DIR=... BER_OUTPUT_DIR=...          # when running from a worktree
python -m ber.pipeline --stage block --split train --tag ameya-block-v0-wide --set trim_s1=40 --set trim_r=4
python -m ber.pipeline --stage block --split test  --tag ameya-block-v0-wide --set trim_s1=40 --set trim_r=4
python experiments/ameya/block-v0/trim_curve.py ameya-block-v0-wide --write ameya-block-v0 --trim-s1 15 --trim-r 4 --splits train --dev-tag ameya-block-v0-dev
python experiments/ameya/block-v0/trim_curve.py ameya-block-v0-wide --write ameya-block-v0 --trim-s1 15 --trim-r 4 --splits test --no-curve
cd experiments/ameya/baseline && python baseline_v0.py --cands ameya-block-v0 --tag ameya-baseline-v0
python -m ber.pipeline --stage write --split test --tag ameya-baseline-v0 --in candidates=ameya-block-v0 --in matches=ameya-baseline-v0
python student_resource/utils/validate_submission.py --matching output/matching_results.tsv --candidate output/candidate_pairs.tsv --test-dir student_resource/dataset/test --check-ids
```

## Artifacts (local paths / drive links + sha256)

- The dev kit is at `work/dev_kit/` (180 MB; sha256 values are in its `MANIFEST.txt`). Upload it to the team drive and post the link.
- The submission file is archived in `submissions/files/2026-09-25-01/matching_results.tsv` (sha256 above).

## Next steps (ordered, with suggested owner)

1. Upload Submission 1, then add the record, the tag `sub/2026-09-25-01` on commit `55ef718`, and a changelog row (Ameya, captain).
2. Put the dev kit on the team drive and post the link (Ameya).
3. Improve blocking recall for v0 (Ameya):
   - GPU char-3gram views for typos (1.3b);
   - better Indic handling, reusing Bakshi's normalize output when it lands;
   - more rounds for the baseline model.
4. Integration at 21:30 (#13): merge #6/#7/#8/#9 when they're ready, run everything at full scale, and compare with `ameya-baseline-v0` through the gates.

## Blockers, open questions, decisions needed

- The team-drive link (the user creates it).
- Whether the leaderboard score is close to the holdout's 0.968. The gap tells us how much the doubled look-alikes in test cost.
