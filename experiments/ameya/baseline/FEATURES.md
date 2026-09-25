# Baseline v0 pair features (37)

These are in `work/features/ameya-baseline-v0-dev/train.parquet` (dev kit) and are produced by `experiments/ameya/baseline/pairfeat.py`.

- **Rows:** one per candidate pair of the dev sample, 3,212,547 in total.
- **Keys:** `s1`, `r` (int64 eids), `fold` (int8) and `y` (1 = true match).
- **Values:** every feature is float32; NaN means undefined.
- **Dev holdout:** `fold == 0`, 27.7k S1. **Training:** folds 5, 10 and 15, one per OOF group (`ber.eval.splits.oof_group`).

## Token overlap per field

`f` is one of:
- `name`: name tokens without legal forms and honorifics. Indic names are *not* transliterated in this v0 feature set.
- `word`: address words, with street types canonicalized.
- `num`: address numbers, with leading zeros stripped.

| feature | definition |
|---|---|
| `f__inter` | number of tokens shared by S1 and R |
| `f__jac_w` | IDF-weighted Jaccard of the two token sets |
| `f__cont_s1` | share of the S1's tokens that are also in R |
| `f__cont_r` | share of R's tokens that are also in the S1 |
| `f__extra_r_w` | IDF mass of R's tokens that the S1 doesn't have. For names, this is the **look-alike** signal: an added business word such as "Exports" or "Holdings" |
| `f__extra_s1_w` | IDF mass of the S1's tokens that R doesn't have |
| `f__len_s1`, `f__len_r` | token counts |

## House numbers

| feature | definition |
|---|---|
| `num__rel1` | relation of the first numbers: 0 missing, 1 equal, 2 truncation (1–3 trailing digits dropped, e.g. 8924 vs 892), 3 nudge (\|d\| ≤ 10, e.g. 4104 vs 4108), 4 other |
| `num__logdiff1` | log1p(\|first number of S1 − first number of R\|); NaN if either is missing |

## String similarity

These are rapidfuzz scores from 0 to 100, on folded, lowercased text.

| feature | definition |
|---|---|
| `name__tsort` | token_sort_ratio of the names |
| `name__partial` | partial_ratio of the names |
| `addr__tset` | token_set_ratio of the addresses |

## Retrieval and context

These come from the blocking view `tok`.

| feature | definition |
|---|---|
| `ret__score` | IDF-weighted token cosine from blocking (NaN if only the name_short view found the pair) |
| `ret__rank_s1` | rank of R in the S1's candidate list (0 = best; 99 = not in the top 40) |
| `ret__rank_r` | rank of the S1 in R's list of S1 (0 = best; 99 = not in the top 8). **This is the strongest feature**, because every record has at most one owner |
| `ctx__n_cand_s1` | number of candidates of the S1 |
| `ctx__n_cand_r` | number of candidate S1 of the record |
| `ctx__gap_s1_best` | best score among the S1's candidates minus this pair's score |
| `ctx__gap_r_best` | best score among the record's candidate S1 minus this pair's score |
| `src__is_s3` | 1 if the record comes from Source 3, 0 if from Source 2 |

## Baseline model trained on these features

- **Features and data:** all 37 features; `y` as the label; rows of folds 5–16 (a 30% S1 sample on the full data); early stopping on folds 17–19.
- **Settings:** XGBoost, `hist`, `max_depth=8`, `eta=0.08`, `subsample=0.8`, `colsample_bytree=0.8`, `min_child_weight=5`, 800 rounds (it didn't stop early, so more rounds help).
- **Decision:** each record goes to its highest-p S1, with a threshold of 0.675 tuned on the holdout.
- **Full holdout score:** macro F0.5 **0.9683** (US 0.9765, India 0.9561), precision 0.990, recall 0.935.
- **Top gain, in order:**
  1. `ret__rank_r`
  2. `ctx__gap_r_best`
  3. `num__cont_s1`
  4. `num__cont_r`
  5. `num__extra_r_w`
  6. `ret__rank_s1`
  7. `addr__tset`
  8. `word__cont_r`
  9. `name__extra_r_w`
  10. `name__len_r`
- **Model files in the release:** `xgb.ubj` (load it with `xgboost.Booster(model_file=...)`) and `decide.json` (the threshold and the feature order).

## Loading them (8 GB is enough: about 0.6 GB in memory)

```python
import pandas as pd
df = pd.read_parquet("work/features/ameya-baseline-v0-dev/train.parquet")
features = [c for c in df.columns if "__" in c]
train, hold = df[df.fold.isin([5, 10, 15])], df[df.fold == 0]
X_train, y_train = train[features].to_numpy("float32"), train["y"].to_numpy()
```

On the dev holdout, score the matches with `ber.eval.metric.report(matches, truth, universe)`. `universe` is the fold-0 S1 of the dev sample:

```python
import numpy as np
from ber.eval.splits import in_dev_sample, in_folds
from ber.records import load_records, load_truth

rec = load_records("train", ["eid", "source"])
s1 = rec.loc[rec.source == 1, "eid"].to_numpy()
universe = s1[in_dev_sample(s1) & in_folds(s1, (0,))]
```

Or use the pipeline instead: `python -m ber.pipeline --stage evaluate --split train --tag <tag> --folds 0 --set sample=dev`.
