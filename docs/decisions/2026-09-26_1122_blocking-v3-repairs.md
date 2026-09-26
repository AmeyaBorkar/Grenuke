# Decision: blocking-v3-repairs

- **Date (IST):** 2026-09-26 11:22
- **Author:** ameya
- **Status:** accepted at full scale. Holdout blocking pair recall 0.98992 → 0.99135 (missed 19,163 → 16,455) with 0.6% fewer pairs; model v6all +0.00063 [0.00057, 0.00070] vs v5all-c2 (`2026-09-26_1425_model-v6all-final.md`).
- **Affects:**
  - blocking: `ber/block/repair.py` (new), `ber/block/index.py`, `ber/block/text.py`, `ber/block/__init__.py`;
  - `ber/features/context.py`;
  - `experiments/ameya/model-v1/legal.py`.

## Context

The preprocessing research (`RESEARCH_v5.md` §5) found that vendor formats are not a loss source. Three blocking gaps remained:
- domain/handle names: 2,092 holdout FN, 97.7% of them blocking misses, 99.9% accepted once they are candidates;
- OCR digits in names;
- ordinal street words.

## Options considered

1. **Repairs as extra name tokens for S2/S3 records** (`repair.py`, params `seg_domains`, `ocr_repair`, default on). The original tokens stay; the joined-name key and the n-grams keep the originals.
   - Domain/handle names (8+ letters, or 6+ with a .com/@/#/www marker) are segmented by dynamic programming into the country's S1 name words (frequency-weighted, up to 2 initials, www/com/net/org/in/co/info/biz affixes, full cover only).
   - OCR digits (0→o, 1→l/i, 5→s, 8→b, 6→g, 3→e, 4→a) are repaired only when the result is an S1 word.
2. **Ordinal street words → digits** (first…twentieth, twenty-first style) in the address text and `numstreet_keys`.
3. **Honorifics sree/shree/om/maa as stop words.** Reverted: it stripped short names' only distinctive word ("Om Services Private Limited"). On the dev pool that lost 95 true pairs and found 64.
4. **OCR'd French legal forms:** read 5 as s (5arl, 5as) in `legal.py`.

## Decision

Options 1, 2 and 4. Country is an open set: the vocabularies are built per country label from the pool's own S1 names. There are no external data; the lexicons (affixes, the OCR map, ordinals) are hand-written.

**Dev pool** (all 110,442 dev-sample S1, their true records and the records `ameya-block-v2-dev` retrieved for them: 2.61M records; same parameters as block v2). Forward retrieval is the S1's top 15 plus the name_short top 5.

| slice | true pairs | forward recall before → after | found / lost |
|---|---|---|---|
| all | 382,269 | 0.97240 → **0.97939** | +2,881 / −206 |
| dev holdout (fold 0) | 95,870 | 0.97191 → 0.97894 | +720 / −46 |
| domain/handle records | 31,030 | 0.86813 → 0.93713 | +2,197 / −56 |
| OCR digits in the record name | 10,931 | 0.90632 → 0.95215 | +511 / −10 |
| ordinal word in the record address | 6,985 | 0.97165 → 0.98984 | +137 / −10 |

- Forward pairs per S1: 18.04 → 18.02.
- Tests: 106 pass, 6 of them new.

## Consequences (what changes, what we give up, how we'll know it was right)

- Every feature group must be rebuilt on the new candidates (`ameya-fx5`), including the cross-encoder.
- Expected +0.0003–0.0005 holdout F0.5.
- Full-scale S1 vocabularies are larger than the dev pool's: more names get segmented, and noise words get added. On the true-pair sample 5% of added words are not the S1's own; among blocking misses, 22%. The dev pool's displacement (206 lost) may grow.
- `numstreet_keys` changes for English ordinals only, so France's rule key is unaffected.
- **Right if** `ameya-model-v6all-c2` ≥ `ameya-model-v5all-c2` on the holdout with blocking pair recall up.
- **Wrong if** recall or F0.5 drops: set `seg_domains=0` / `ocr_repair=0` and rebuild.

Commands:
```
python -m ber.pipeline --stage block --split train --tag ameya-block-v3 --set trim_s1=15 --set trim_r=4 --set indic_dict=ameya-fx1 --set ns_ngrams=4 --set ns_domain_len=8 --set nw_words=6 --set dev_tag=ameya-block-v3-dev
python -m ber.pipeline --stage block --split test --tag ameya-block-v3 --set trim_s1=15 --set trim_r=4 --set indic_dict=ameya-fx1 --set ns_ngrams=4 --set ns_domain_len=8 --set nw_words=6
```
