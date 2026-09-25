# Handover: analysis-v2-and-v3

- **Author:** ameya (human; the agent was Claude Code)
- **When (IST):** 2026-09-25 21:47 (updated through the evening)
- **Branch / PR / last commit:** `ameya/analysis-v2` / PR (see the branch) / head of the branch
- **Area and paths touched:**
  - `experiments/ameya/model-v1/`: `analysis.py`, `ANALYSIS_v2.md`, `legal.py`, `feats_legal.py`, `ce.py`, `s2.py --extra`, `dev_export.py --scores-only`, `decide.py` (expected-F forecast);
  - `src/ber/block/{index,__init__}.py`: blocking v2 (`nw_words`, `ns_domain_len`) + test;
  - `src/ber/features/context.py`: large_string fix in `numstreet_keys` + test;
  - `docs/decisions/`: the two gate records.

## TL;DR (3 lines max)

The error analysis of model v2 found that the legal form, which our tokenizer drops, separates look-alikes from matches. Stage 2 with legal-form features: 0.98436 → 0.98708 (+0.00271, CI [0.00260, 0.00283]). Blocking v2 raises recall from 0.9857 to 0.9899. Model v3 combines both, plus the (number, street) key fix: holdout **0.98882**, +0.00445 [0.00431, 0.00459] vs model v2.

## What was done

- **Error analysis of model v2** on the full holdout (`analysis.py` → `work/analysis/ameya-analysis-v2/`; write-up in `experiments/ameya/model-v1/ANALYSIS_v2.md`):
  - 81% of the 0.0156 loss is missed true pairs. Records with an empty address are 4.4% of true pairs but 52% of the misses.
  - When the S1's name is shared, the owner of an empty-address record cannot be determined: 95–100% are missed, about 22k pairs, irreducible. The truth has no per-source count structure to use either.
  - Look-alikes add or change the legal form (62% of orphan false positives, against 6.5% of true pairs), and the model was blind to it.
  - Blocking misses with an address come from typo'd names on number-less streets, domains/handles and brand names.
- **Legal-form features** (`legal.py`, `feats_legal.py`, group `lg`):
  - bitmask of 20 legal forms per name: Latin, OCR variants, transliterated Indic via skeletons, French forms;
  - pair features: relation code, counts, and the added/dropped forms.
  - Gate record: `docs/decisions/2026-09-25_2142_gate-legal-form-features.md`. Sachi's re-check data is the `scores-v2lg-dev` release.
- **Blocking v2**: (name token × address word) compound keys and one-token names in the name-only view. Gate record: `docs/decisions/2026-09-25_2142_gate-g1-blocking-v2.md`.
- **Research** (Foursquare Location Matching write-ups, Ditto, GFM decision, hard negatives). Summary in `ANALYSIS_v2.md` §3:
  - a cross-encoder on the uncertain band as a stage-2 feature is the best-supported next step;
  - `ce.py` is ready (multilingual-e5-small, MIT, 118M; about 1,750 training pairs/s on our GPU).
- **Checks that ruled things out:**
  - The independence P(no match) used by the DP is calibrated overall (5.63% vs 5.58% actual). It runs about 0.05 low in the 0.5–0.8 bins, which caps a GFM-style fix at +0.0001–0.0003.
  - The per-source record counts per S1 carry no usable constraint.

## Current state

- **Works:** the legal features, blocking v2, the v3 chain and the expected-F forecast in `decide.py`.
- **Half-done:** G10 cross-encoder: code and smoke test done; the full run follows v3.
- **Known bugs and caveats:**
  - `numstreet_keys` failed on the large_string records cache; fixed in this branch.
  - The (number, street) key changes the `ctx__*numstreet*` features from v3 on.

## Numbers (shared holdout, `ber.eval`; 549,699 S1)

| system | macro F0.5 | US / India | P / R | tag |
|---|---|---|---|---|
| model v2 (Sub 3) | 0.98436 | 0.9847 / 0.9838 | 0.9970 / 0.9602 | `ameya-model-v2` |
| + legal features in stage 2 | 0.98708 | 0.9870 / 0.9872 | 0.9982 / 0.9643 | `ameya-model-v2lg` |
| **model v3** (blocking v2 + features v3 + legal in stages 1–2) | **0.98882** | 0.98891 / 0.98868 | 0.99833 / 0.96893 | `ameya-model-v3` |

Blocking (holdout): v1 0.9857 → v2 0.9899 (India 0.9875, US 0.9916); oracle F0.5 0.9956 → 0.9970; 30.3 candidates per S1.

v3 by stage (holdout, best threshold): stage 1 0.9820 → **0.9871**, stage 2 0.9842 → **0.9887**. Stage 0 keeps 15.4% of pairs (was 17.6%).

**Model's own forecast** (mean expected F0.5 of the DP): holdout 0.99139 against 0.98882 real, so 0.0026 optimistic (it cannot see blocking misses). On test the forecast is:

| US | India | France |
|---|---|---|
| 0.9914 | 0.9916 | **0.9700** |

Predicted records per S1 on test: US 3.38, India 3.36, France 3.54.

Record: `docs/decisions/2026-09-25_2328_model-v3-end-to-end.md`.

## How to reproduce or continue (exact commands)

```
python -m ber.pipeline --stage block --split train --tag ameya-block-v2 --set trim_s1=15 --set trim_r=4 --set indic_dict=ameya-fx1 --set ns_ngrams=4 --set ns_domain_len=8 --set nw_words=6 --set dev_tag=ameya-block-v2-dev
python -m ber.pipeline --stage block --split test  --tag ameya-block-v2 --set trim_s1=15 --set trim_r=4 --set indic_dict=ameya-fx1 --set ns_ngrams=4 --set ns_domain_len=8 --set nw_words=6
cd experiments/ameya/model-v1
python feats.py --cands ameya-block-v2 --split train --tag ameya-fx3        # and --split test
python feats_lo.py --feats ameya-fx3 --split train                          # and --split test
python feats_legal.py --feats ameya-fx3 --split train                       # and --split test
python s1.py --feats ameya-fx3 --tag ameya-s1-v3 --groups str,cx,lo,lg
python s2.py --feats ameya-fx3 --s1 ameya-s1-v3 --tag ameya-s2-v3 --groups str,cx,lo,lg --cluster --no-test --extra leg__rel,leg__n_s1,leg__n_r,leg__inter,leg__s1_only,leg__r_only,leg__r_only_bits,leg__s1_only_bits
python s2.py ... --test-only                                                # same arguments, test scores from the saved models
python decide.py --scores ameya-s2-v3 --col pc --tag ameya-model-v3 --base ameya-model-v2
python ce.py --feats ameya-fx3 --s1 ameya-s1-v3 --tag ameya-ce-v1           # G10, then s2.py with --groups ...,ce --extra ...,ce__logit
```

## Artifacts (local paths / drive links + sha256)

- `work/analysis/ameya-analysis-v2/{s1,pairs,pair_types,pair_legal}.parquet`, `report.json`, `examples.txt`
- Release `scores-v2lg-dev` (dev-sample stage-2 scores with legal features), sha256 `be2fac69...a469`
- **v3 submission package** (validator PASS with `--check-ids`; 1,732,544 S1, 96,241 empty), in `submissions/files/2026-09-26-v3/`. `output/` still holds Submission 3.
  - `matching_results.tsv`: sha256 `57380f657b0138ee1dfc955fb81ba4e7f7f3ffa045437d7a97c3485ccee4cde2`
  - `candidate_pairs.tsv`: sha256 `4c8485cc8051026fe20259c91285cab4138d553fd6c9a349209a4dab0d74cb2e`
  - built from code commit `3bc01d3` on `ameya/analysis-v2`
- Tags: `ameya-block-v2`, `ameya-fx3` (str, cx, lo, lg), `ameya-s1-v3`, `ameya-s2-v3`, `ameya-model-v3` (train + test)

## Next steps (ordered, with suggested owner)

1. Upload v3 once its holdout number is confirmed; records, tags and changelog (Ameya, captain).
2. G10: cross-encoder → stage 2 → gate vs v3 (Ameya).
3. G7 France probe (Ameya + Sachi): v3 vs v3 with only high-confidence French pairs.
4. Recalibrate P(no match) inside the DP (GFM variant; Sachi's area, small).
5. Port the legal features and stage-2 extras into `ber.features` / `ber.model` (Bakshi / Sachi).

## Blockers, open questions, decisions needed

- Leaderboard scores of Submissions 1–3 (holdout → leaderboard transfer).
- Whether a pretrained transliteration model trained on external data (IndicXlit) is allowed. Not needed now: Indic names are at parity.
