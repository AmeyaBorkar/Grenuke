# Decision: gate-legal-form-features

- **Date (IST):** 2026-09-25 21:42
- **Author:** ameya
- **Status:** accepted (stage 2 on v2 features); v3 adds the same group to stage 1 as well
- **Affects:** features (group `lg`: `experiments/ameya/model-v1/legal.py`, `feats_legal.py`), stage 2 (`s2.py --extra`)

## Context

The model-v2 error analysis (`experiments/ameya/model-v1/ANALYSIS_v2.md`) found that the blocking tokenizer drops legal forms (`ber.block.text.LEGAL`). The v1/v2 name features reuse that tokenizer, so they never see the legal form. Yet look-alikes change or add it, and true records keep, reformat or drop it.

On the v2 holdout, the y-rate within one score band depends strongly on the legal relation. In the 0.8–0.9 band it is:
- same: 0.94;
- dropped: 0.92;
- added: 0.66;
- changed: 0.13.

62% of orphan false positives add or change the legal form; 6.5% of true pairs do.

## Options considered

1. **Keep v2.** Stage 2 on 56 features: top-30 stage-1 features, rivalry, cluster support, p1.
2. **v2 + `lg` group in stage 2** (`--extra`, 8 features). `legal.py` maps legal words to a 20-bit mask per name:
   - Latin words and single-character OCR variants (c0rp, lnc, 1td);
   - dotted acronyms (L.L.C.);
   - transliterated Indic words, through consonant skeletons (praivet → pvt, limited/limitet → ltd, elaelapii → llp, "pra. li.");
   - French forms (SAS, SARL, SA, SASU, EURL, SCI, SNC).

   The pair features are the relation code (none, same, dropped, added, subset, superset, changed), the counts per side, shared, S1-only and record-only, and the bitmasks of the added and dropped forms. No labels are used, so there is no out-of-fold issue; the lexicon is hand-written.

## Decision

**Keep option 2.** Paired bootstrap on the full shared holdout (549,699 S1, 1,000 resamples). Both runs use the same decision: argmax ownership + expected F0.5, shift 0.

| | model v2 (`ameya-model-v2`) | + legal (`ameya-model-v2lg`) |
|---|---|---|
| macro F0.5 | 0.98436 | **0.98708** |
| India / US | 0.9838 / 0.9847 | 0.9872 / 0.9870 |
| precision / recall | 0.9970 / 0.9602 | 0.9982 / 0.9643 |
| holdout log-loss, stage-2 rows (2.75M) | 0.04978 | 0.03993 |
| Brier / ECE (10 bins) | 0.01347 / 0.00070 | 0.01094 / 0.00046 |

- Δ **+0.00271**, 95% CI [0.00260, 0.00283], p_better 1.0. This clears the +0.002 bar.
- On the dev holdout (dev fold 0, 27,651 S1) it is 0.9845 → 0.9871. Sachi can re-run it from the `scores-v2lg-dev` release.
- The G6 re-check on the new scores: expected F0.5 vs the best threshold (0.675) is +0.00014 [0.00008, 0.00021]; the DP stays.

Commands:
```
python experiments/ameya/model-v1/feats_legal.py --feats ameya-fx2 --split train   # and --split test
python experiments/ameya/model-v1/s2.py --feats ameya-fx2 --s1 ameya-s1-v2 --tag ameya-s2-v2lg --groups str,cx,lo,lg --cluster --no-test --extra leg__rel,leg__n_s1,leg__n_r,leg__inter,leg__s1_only,leg__r_only,leg__r_only_bits,leg__s1_only_bits
python experiments/ameya/model-v1/decide.py --scores ameya-s2-v2lg --col pc --tag ameya-model-v2lg --base ameya-model-v2 --no-test
```

## Consequences (what changes, what we give up, how we'll know it was right)

- Features v3 include the `lg` group in stage 1 and stage 2.
- **Test.** Model v2 predicts a changed legal form 1.1–1.9× as often on test as on the holdout: US 0.64% vs 0.56%, India 0.19% vs 0.10%, France 0.78%. That matches the test's doubled look-alike density, so the gain should transfer and may be larger on the leaderboard.
- **France.** The relation features are language-independent and the French legal forms have their own bits. The France descriptor swaps ("Mauges Amis SAS" → "Mauges Gestion SAS") keep the same legal form, so this does not address them.
