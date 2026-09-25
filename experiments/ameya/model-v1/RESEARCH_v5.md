# Research, 26 Sep: why the leaderboard is below the holdout, where we fail, the candidate-set size

This note answers three questions:
- why an upload scores below the holdout;
- where the model fails and in what pattern;
- how small the candidate set can get (the organisers now rank a smaller candidate set higher).

**Part 1 (05:20 IST)** covers the gap, the holdout anatomy and the candidate-set size. **Part 2** comes after the research threads (ground-truth structure and joint decoding, preprocessing, France residuals) and adds the plan.

- Holdout numbers are on the full shared holdout (549,699 S1).
- Test numbers are label-free.
- Scripts: `gap_check.py`, `cand_size.py`, `analysis.py`.

## TL;DR (part 1)

- **The leaderboard is below the holdout because of France alone.**
  - US and India on test score like the holdout, even re-weighted to the test's ratios.
  - Nothing leaks.
  - The test file is shuffled, so the public board holds 15% France.
  - The leaderboard implies France at **0.925–0.944 for v2/v3**, against 0.984–0.989 for US/India.
- **Forecast for v4 and later:** LB ≈ **0.8423 + 0.14975 × F_France**; equivalently F_France = (LB − 0.8423) / 0.14975. France at 0.96 gives 0.9861, at 0.98 gives 0.9891.
- **The holdout (v5all, 0.99016) is recall-bound.**
  - Missed records are 89% of the loss.
  - 69% of the misses are records with an **empty address** whose name several S1 share; only 55% of those are found.
- **Candidate set: 4.68 → 3.70 pairs per S1 (−21%) at no cost.** Keep the pairs with p1 ≥ 0.02 among each record's top 2 S1 by p1.
  - Holdout F0.5 is unchanged at 0.99016 (81 of 1.85M predictions fall outside).
  - Test predictions lost per S1: US 0.0001, India 0.0001, France 0.0009.

## 1. Why the leaderboard is below the holdout

| model | holdout | leaderboard | gap |
|---|---|---|---|
| v2 | 0.98436 | 0.97608 | −0.0083 |
| v3 | 0.98882 | 0.97961 | −0.0092 |

**Checks on the evaluation:**

- **Test make-up.** The test S1 file is shuffled: every tenth of `test_source1.tsv` holds about 25.9k France, 81k India and 66.3k US S1. Any public subset holds about 15% France. Shares: US 0.38274, India 0.46751, France 0.14975.
- **Leakage (none).**
  - The label odds (`lo`) are out of fold by stacking group; the holdout uses the training folds only.
  - The cross-encoder is out of fold; the holdout gets the mean of three models trained on the training folds.
  - The Indic dictionary is learned on folds 5–19.
  - Isotonic calibration is fitted on the training folds' out-of-fold scores. The `--all` fit also uses the holdout's own out-of-fold p2 (negligible).
  - The DP shift is chosen on the holdout (tiny optimism).
- **IDs and row order carry no signal.**
  - Correlation of S1 and record IDs over true pairs: 0.0002.
  - Correlation of their row positions in the raw TSVs: 0.0014.
  - Median position difference: 0.293, which is what uniformly random positions give.

**The test's different ratios do not lower US/India:**

- **Records per S1 (+23%, twice the look-alike distractors).** The model rejects the extra look-alikes at the holdout rate: predicted look-alike-signature pairs per S1 are equal on test and holdout (`ANALYSIS_v3.md` §1).
- **Pool size (fewer S1 share a name on test).**

  | same-core-name group | train US | test US | train India | test India | test France |
  |---|---|---|---|---|---|
  | S1 with a unique name | 53.6% | **61.3%** | 46.3% | 47.0% | 49.6% |
  | mean group size | 21.6 | **11.5** | 19.4 | 17.9 | 18.1 |

- **Re-weighting the holdout to the test's group-size mix** (`gap_check.py`). Per-S1 F0.5 falls from 0.995 for unique names to 0.982–0.986 for shared names. So the test's smaller US groups make US slightly easier, not harder.

  | model | US holdout → re-weighted | India holdout → re-weighted | predicted per S1: test − re-weighted holdout (US / India) |
  |---|---|---|---|
  | v2 | 0.98473 → 0.98574 | 0.98381 → 0.98393 | +0.024 / +0.009 |
  | v3 | 0.98891 → 0.98979 | 0.98868 → 0.98880 | +0.012 / +0.001 |
  | v4 | 0.98995 → 0.99083 | 0.99044 → 0.99055 | +0.010 / 0.000 |
  | v5all | 0.98998 → 0.99086 | 0.99043 → 0.99054 | +0.010 / 0.000 |

- **The model's own expected-F0.5 forecast** (v5all) agrees:
  - US/India: test 0.99301 / 0.99381, holdout 0.99225 / 0.99379;
  - France: 0.98044.
- **Empty share of test S1:** 5.76–5.77% in US/India, against a 5.59% singleton share in every country.

**So LB = 0.38274 F_US + 0.46751 F_India + 0.14975 F_France, with US/India at the re-weighted holdout.** The range is from "no false positives in the extra US predictions" to "all of them false" (0.19 each):

| model | France implied by the leaderboard |
|---|---|
| v2 | 0.927 – 0.944 |
| v3 | 0.925 – 0.931 |

- The v3 model forecast France at 0.970. France's errors are confident: +0.04 of overconfidence there, against +0.003 on the holdout. **The model's France forecast cannot be trusted; only the leaderboard can measure France.**
- **v4/v5all:** LB ≈ 0.8423 + 0.14975 × F_France.

  | F_France | 0.95 | 0.96 | 0.97 | 0.98 | 0.99 |
  |---|---|---|---|---|---|
  | LB | 0.9846 | 0.9861 | 0.9876 | 0.9891 | 0.9906 |

- A France as good as US, given France's group-size mix, would score 0.9895.

**France predictions per S1 / empty share:**

| | v3 | v4 | v4 + rules | v5all | v5all + rules |
|---|---|---|---|---|---|
| France predicted per S1 | 3.539 | 3.371 | 3.323 | 3.367 | 3.320 |
| France empty share | 4.37% | 5.31% | 5.63% | 5.31% | 5.65% |

US/India test: 3.367–3.382 per S1, 5.76–5.77% empty.

## 2. Where the holdout loses (v5all, `analysis.py`)

Macro F0.5 0.99016: precision 0.9988, recall 0.9713, loss 0.00984.

| bucket | pairs | F0.5 if fixed | empty record address |
|---|---|---|---|
| true record not a candidate (blocking) | 19,163 | +0.00319 | 9,112 |
| lost to another S1 (wrong argmax owner) | 19,050 | +0.00316 | **17,506** |
| owned, rejected by the decision (median pc 0.48) | 15,130 | +0.00238 | 10,194 |
| stage-0 filtered | 1,206 | +0.00022 | 953 |
| false positive, record owned by no S1 | 1,309 | +0.00065 | |
| false positive, record belongs to another S1 | 858 | +0.00046 | |

- **Empty-address records.**
  - They are 4.4% of true records: 46,130 found, 37,774 missed (55% recall).
  - They are **69% of all misses**.
  - Examples: "Prairie Institute Co" (no address) with S1 "Prairie Institute" in North Olmsted OH and another in the Bronx; "City Solutions Private Ltd" with two "City Solutions Private Limited" S1.
  - The model is calibrated on them (reliability within ±0.01 per bin), so they are close to the Bayes limit unless the joint structure (how many records each S1 already has) can separate them. Part 2 tests that.
- **By shared-name group.** Unique-name S1: F0.5 0.9941 (36% of the loss). S1 whose name is shared: 0.982–0.986 (64%).
- **By true set size.** T = 1 S1: 0.9668, 18% of the loss. A missed single record scores 0; 1,022 non-singleton S1 are left empty, 19% of the loss.
- **Outcomes.** "Misses only" is 8.9% of S1 and 69% of the loss; "extras only" is 0.3% of S1 and 8%.

## 3. Candidate-set size (the organisers' new ranking rule)

`candidate_pairs.tsv` is part of the final submission. They review it and the code that produces it, and "the approach that generates a smaller candidate set per Source 1 entity will be ranked higher in the final evaluation beyond the public/private leaderboard".
- Ours is the stage-2 input: blocking (34 pairs per S1) → stage-0 filter → stage 1 → p1 ≥ 0.002.
- `cand_size.py` measures tighter stage-1 cuts. The holdout F0.5 in this table restricts the current predictions to the kept pairs without re-deciding, so it slightly understates.

| cut (on top of p0 ≥ tau0) | holdout pairs/S1 | predictions lost | holdout F0.5 | pair recall | oracle F0.5 | test pairs/S1 (US / India / France) | test predictions lost per S1 (US / India / France) |
|---|---|---|---|---|---|---|---|
| p1 ≥ 0.002 (now) | 4.593 | 0 | 0.99016 | 0.98927 | 0.99676 | 4.682 (4.55 / 4.51 / 5.56) | 0 |
| p1 ≥ 0.02 | 3.928 | 52 | 0.99016 | 0.98756 | 0.99620 | 4.050 | 0.0001 / 0.0001 / 0.0006 |
| p1 ≥ 0.05 | 3.633 | 209 | 0.99013 | 0.98501 | 0.99541 | 3.706 | 0.0002 / 0.0005 / 0.0015 |
| record's top 2 S1 | 3.758 | 29 | 0.99016 | 0.98224 | 0.99461 | 3.990 | 0.0000 / 0.0001 / 0.0002 |
| **p1 ≥ 0.02 and record's top 2 S1** | **3.592** | 81 | **0.99016** | 0.98198 | 0.99452 | **3.702 (3.66 / 3.61 / 4.09)** | 0.0001 / 0.0001 / 0.0009 |
| p1 ≥ 0.05 and record's top 2 S1 | 3.533 | 233 | 0.99014 | 0.98145 | 0.99435 | 3.607 | 0.0002 / 0.0006 / 0.0016 |
| S1's top 6 | 4.157 | 24,535 | 0.98877 | 0.97390 | 0.99497 | 4.233 | 0.047 each |

- The predictions themselves are 3.37 per S1, so about 3.6–3.7 is close to the floor for this model.
- Per-S1 top-k cuts are the wrong shape: the S1's lower-ranked records are often true (sets of up to 11). A per-record cut matches the argmax ownership.
- **Recommendation:**
  - Make the stage-2 input rule p0 ≥ tau0, p1 ≥ 0.02 and the record's top 2 S1 by p1, in both `s2.py` and `cands_final.py`.
  - Refit stage 2 on it (`--all`, about 25 min), then re-run `decide.py`, `cands_final.py` and `post_ops.py`.
  - The candidate file then shrinks by 21% with the matching unchanged.
  - Stage 2's group features are computed from stage-1 scores; computing them on the kept graph keeps the matching model's input exactly the candidate set.

## 4. Part 2 (running)

- **Ground-truth structure and joint decoding:** can the records an S1 already has break the empty-address ties?
- **Preprocessing:** which S1 → S2/S3 vendor transformations our normalisation misses, in US/India with labels and in France without.
- **France residuals:** a structural edit-profile estimator of France's F0.5, validated against the v2/v3 leaderboard, and the next systematic France errors after the rules.
