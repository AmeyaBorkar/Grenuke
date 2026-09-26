# Dev kit v2: model-v2 pair features (79), scores and candidates

These are the features, scores and candidates behind **model v2**, which is Submission 3 (0.9844 on the full shared holdout). They cover the dev sample only.

## Files (unzip `grenuke-devkit-v2.zip` into the repo root; the files land in `work/`)

| file | rows | what |
|---|---|---|
| `work/features/ameya-fx2-dev/train.parquet` | 3,262,031 | C8 layout: `s1, r, fold, y` + 79 float32 features |
| `work/scores/ameya-s2-v2-dev/train.parquet` | 3,262,031 | `s1, r, fold, y, p0, p1, p2, pc` (same row order as the features) |
| `work/candidates/ameya-block-v1-dev/train.parquet` | 3,262,031 | C4 candidates (blocking v1) |

- **Dev sample:** `ber.eval.splits.in_dev_sample`, about 110k S1.
  - Fold 0 is the dev holdout: 27,651 S1.
  - Folds 5, 10 and 15 each give one OOF group (`ber.eval.splits.oof_group`).
- **Memory:** about 1.1 GB for all columns. On 8 GB, load only the columns you need: `pd.read_parquet(path, columns=[...])`.
- **How the files were built:** on the integration machine over the **full** candidate graph (65.2M train pairs), then sliced to the dev sample. So the context/rivalry features, the look-alike odds (`lo__*`) and the scores all saw every S1 and record, not only the dev sample. Use them as they are; a dev-only recomputation would differ.

## Reference numbers

| system | dev holdout (fold 0, 27,651 S1) | full holdout (549,699 S1) |
|---|---|---|
| baseline v0 (dev kit v0, Submission 1) | 0.9682 | 0.9683 |
| **model v2** (Submission 3) | **0.9845** (US 0.9848, India 0.9841; P 0.997, R 0.961) | **0.9844** |

## Features

The text is transliterated with the blocking tokenizer (`ber.block.text`, `ber.block.indic`):
- On Indic-script names, the transliterated legal forms and honorifics are dropped.
- The tokens then go through an Indic -> Latin dictionary: 693 entries learned from true pairs of train folds 5-19 only, for example tek -> tech, kanstrakshan -> construction, eksaports -> exports.
- IDF weights are computed **per country** (France gets its own statistics).
- NaN means the value is undefined, for example an empty side.

**Token overlap.** `name__*`, `word__*` and `num__*` each have 8 features. They are computed on name tokens, address words and address numbers respectively.

| feature | definition |
|---|---|
| `f__inter` | shared tokens |
| `f__jac_w` | IDF-weighted Jaccard |
| `f__cont_s1`, `f__cont_r` | share of the S1's (record's) tokens found in the other |
| `f__extra_r_w`, `f__extra_s1_w` | IDF mass only the record (only the S1) has |
| `f__len_s1`, `f__len_r` | token counts |
| `name__idf_s1`, `name__idf_r` | total name IDF (how specific the name is) |

**Name variants.**

| feature | definition |
|---|---|
| `name__skel_{jac_w,cont_s1,cont_r,extra_r_w}` | the same overlap on consonant skeletons (maarketing / marketing -> mrktng) |
| `name__skel4_*` | on the first 4 letters of the skeletons (teknolojiij / technologies -> tknl) |
| `name__fz_inter` | record tokens matched exactly or within an edit distance of 1 (2 from 6 letters) |
| `name__fz_extra_r_w`, `name__fz_extra_s1_w` | IDF mass left unmatched after typo-tolerant matching |
| `name__fz_extra_r_max`, `name__fz_extra_s1_max` | the rarest unmatched token |
| `name__fz_sub` | substituted tokens: min(# unmatched on each side). A swapped first name is not a typo |
| `name__fz_n_extra_r` | unmatched record tokens |

**Strings.** These are rapidfuzz scores from 0 to 100, NaN if a side is empty.
- `name__tsort` and `name__partial` use the full folded names.
- `name__c_tset`, `name__c_ratio` and `name__c_jw` (Jaro-Winkler) use the clean name tokens.
- `name__cat_ratio` and `name__cat_partial` use the concatenated tokens, which catches domains and hashtags such as onetechnologies.com.
- `addr__tset` and `addr__tsort` use the folded addresses.

**House numbers.**

| feature | definition |
|---|---|
| `num__rel1` | first numbers: 0 missing, 1 equal, 2 truncation, 3 nudge (\|d\| <= 10), 4 other |
| `num__logdiff1` | log1p of \|first number of the S1 - first number of the record\| |
| `num__rel_best` | the best relation between the S1's first number and **any** number of the record |
| `num__s1first_in_r` | the S1's first number appears among the record's numbers (top feature by gain) |
| `num__rfirst_in_s1` | the record's first number appears among the S1's numbers |

**Retrieval and context** (`ber.features.context`, full candidate graph).
- **Per view** (`tok`, `name_short`):
  - `ret__<view>_score` is the similarity (NaN if that view missed the pair);
  - `ret__<view>_rank_s1` and `ret__<view>_rank_r` are its ranks, with 99 meaning absent.
- **Views:** `ret__n_views` is the number of views that found the pair.
- **Gaps:** `ret__gap_s1_best` and `ret__gap_r_best` measure the distance to the best candidate on each side.
- **Margin:** `ret__margin_r` is this pair's score minus the record's best other S1.
- **Candidate counts:** `ctx__log_cands_s1` and `ctx__log_cands_r` are log counts of candidates.
- **Rivalry:** these are log-counts.
  - `ctx__log_s1_same_name` counts the other S1 with the S1's name key.
  - `ctx__log_s1_same_rname` counts the S1 with the record's name key.
  - `ctx__log_s1_same_numstreet` and `ctx__log_s1_same_rnumstreet` count the S1 sharing the (number, first address word) key. v3 will switch this key to the street name; in France the first word is the street type.
  - `ctx__same_name_key` flags identical name keys.
- **Source:** `src__is_s3` is 1 for Source 3 and 0 for Source 2.

**Look-alike word odds** (`lo__*`, gate G3).
- **What is scored:** after typo-tolerant matching, up to 3 unmatched name tokens per side.
- **The table behind it:** each token's log-odds of a true match when it is extra in the record or missing from it. These are counted on close pairs: shared address words and a shared name token.
- **Out of fold:** training-fold rows use counts from the other two OOF groups. Fold 0 (and test) uses every training fold. Tokens never seen in train get 0.
- **Features:** `lo__extra_r_{min,sum,nlow}` and `lo__missing_s1_{min,sum,nlow}`, where nlow counts the tokens below -1.
- **What it learned:**
  - look-alike words: holdings -9.8, group -9.7, industries, enterprises and exports about -8.6, north, valley and harbor about -7.6;
  - benign words: c0mpany, lnc, formerly.

## Scores (`work/scores/ameya-s2-v2-dev/train.parquet`)

| column | meaning |
|---|---|
| `p0` | stage-0 filter: 200 trees on 10% of training S1. Pairs with p0 < 0.00345 skip stage 1; they keep 99.95% of true pairs |
| `p1` | stage 1: XGBoost depth 9, eta 0.06, about 2,100 trees. **Out of fold** on training folds, the mean of the 3 group models on fold 0 |
| `p2` | stage 2: rivalry features over the full candidate graph + cluster support + p1 + the top-30 stage-1 features. Depth 7, out of fold the same way |
| `pc` | `p2` after isotonic calibration, fitted on OOF p2 of training folds only. Reliable within about 0.01 per bin on the holdout |

**The model-v2 decision:**
1. Argmax ownership: every record stays only under its highest-`pc` S1, computed over **all** S1, not only the dev sample.
2. Per S1, the exact expected F0.5, with the logit shift at 0 and no tuning.
   - Code: `expected_f_select` in `experiments/ameya/model-v1/decide.py`.
   - The G6 result on the full holdout: +0.00018, CI [0.00009, 0.00026] over the best global threshold (0.675).
   - On stage-1 probabilities the same rule **loses** (-0.00029), which agrees with the dev-sample record of 25 Sep.

## Loading

```python
import pandas as pd
df = pd.read_parquet("work/features/ameya-fx2-dev/train.parquet")
features = [c for c in df.columns if "__" in c]                    # 79
train, hold = df[df.fold.isin([5, 10, 15])], df[df.fold == 0]      # folds 5/10/15 = OOF groups 0/1/2
sc = pd.read_parquet("work/scores/ameya-s2-v2-dev/train.parquet")   # same row order
assert (sc["s1"].to_numpy() == df["s1"].to_numpy()).all()
```

To evaluate on the dev holdout, use `ber.eval.metric.report(matches, truth, universe)`, where `universe` holds the fold-0 S1 of the dev sample (see the dev kit v0 notes), or run `python -m ber.pipeline --stage evaluate --split train --tag <tag> --folds 0 --set sample=dev`.

The full pipeline is in `experiments/ameya/model-v1/`. The steps, commands and gate results are in `docs/handover/2026-09-25_1958_ameya_model-v1.md`.
