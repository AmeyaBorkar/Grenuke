# Model v2: where the macro F0.5 is lost, and the v3 plan (25 Sep, evening)

Model v2 is Submission 3 (holdout 0.98436). All numbers below are on the full shared holdout: 549,699 S1, folds 0–4, `ber.eval`.

The tables come from:
- `analysis.py`: loss by outcome and bucket, slices, reliability;
- throwaway checks on top of the tables it writes to `work/analysis/ameya-analysis-v2/`.

## TL;DR

- **Missed true pairs cost 81% of the loss** (0.0127 of the 0.0156). Precision is 0.997 and recall 0.960.
- **Empty-address records cost the most.** They are 4.4% of true pairs but 52% of the misses (miss rate 47%).
  - When the S1's name is unique, 20% of these records are missed.
  - When 2 or more S1 share the name, 95–100% are missed. From name alone the owner is a coin flip, so about 22k of these misses (+0.0037 counterfactual) are irreducible.
- **The legal form was invisible, yet it separates look-alikes from matches.**
  - The blocking tokenizer, which the features reuse, drops legal forms. But look-alikes change or add them (`LP → Corp`, `LLP → Limited`, `Ltd → LLP`).
  - In the 0.8–0.9 score band, a pair is true 94% of the time when the legal form is unchanged, and 13% when it changed.
  - **Legal features in stage 2 alone: 0.98436 → 0.98708** (paired bootstrap +0.00271 [0.00260, 0.00283]; holdout log-loss −20%).
- **Blocking misses 17.9k true pairs even though the record has an address.** The missed types:
  - domain or handle names (`renterianaborweddle.com`, `@eastcomplete`);
  - typo'd names with a number-less street;
  - brand names at a shared address;
  - "first token + legal form + a noise word" names (`Federal LLC Services`).

  The seed-based search never seeds the true S1 when the record's only rare tokens are typos. Cosine normalisation also favours short S1 addresses over the true S1's long one.

## 1. Where the loss is

**By S1 outcome** (loss = 1 − F0.5 per S1):

| outcome | S1 | share of loss | macro points |
|---|---|---|---|
| true records partly missed, no extras | 64,573 | 60.3% | 0.00943 |
| non-singleton left empty (loss 1 each) | 1,668 | 19.4% | 0.00303 |
| extras only (look-alikes or another S1's records) | 3,966 | 10.9% | 0.00171 |
| singleton given matches (loss 1 each) | 518 | 6.0% | 0.00094 |
| misses and extras | 805 | 3.0% | 0.00047 |
| all predictions wrong | 26 | 0.3% | 0.00005 |

- By set size, S1 with one true record score 0.949 and carry 17.8% of the loss (a miss costs 1.0).
- 1,283 of the 1,668 empty non-singletons have n_true = 1.

**By pair bucket.** Buckets are exclusive. The gain is counterfactual: F0.5 if only that bucket were fixed.

| bucket | pairs | gain |
|---|---|---|
| true pair is not a candidate (blocking) | 27,108 | +0.00477 |
| true pair owned, rejected by the decision | 26,845 | +0.00462 |
| true pair lost by ownership (another S1 has higher p) | 20,518 | +0.00359 |
| true pair filtered by stage 0 | 1,071 | +0.00021 |
| predicted orphan (look-alike; the record matches no S1) | 4,407 | +0.00240 |
| predicted record that belongs to another S1 | 1,057 | +0.00054 |

Misses are spread evenly over countries (India 0.9838, US 0.9847) and sources (S2 vs S3).

## 2. What kinds of data fail

**True pairs by record type.** The miss share is each type's share of all 75.6k misses.

| record | true pairs | miss rate | share of misses |
|---|---|---|---|
| **address empty** | 83,904 | **47.3%** | **52.5%** |
| house number nudged (\|d\| ≤ 10) | 36,300 | 19.4% | 9.3% |
| house number different ("other") | 157,918 | 4.9% | 10.3% |
| house number truncated (8230 → 823) | 151,685 | 4.5% | 8.9% |
| one side without a number | 159,463 | 2.9% | 6.1% |
| first number equal | 1,311,997 | 0.7% | 12.8% |

| record name | true pairs | miss rate | notes |
|---|---|---|---|
| brand name (no shared word: "Halocira One", "Korvio") | 33,043 | 16.2% | the address is the only evidence |
| domain or handle ("ewinnovations.com", "@eastcomplete") | 154,839 | 7.0% | 72% of these misses are blocking misses |
| shares a word (typos, shuffles, noise words) | 1,168,758 | 4.0% | |
| Indic script | 136,949 | 2.6% | transliteration + dictionary works well now |
| exact name | 407,678 | 2.3% | mostly empty addresses with a shared name |

**Empty-address records vs name ambiguity.** "S1 with that name" is a crude exact-name key over train S1.

| S1 with that name | empty-address true pairs | missed |
|---|---|---|
| 1 | 54,986 | 20.4% |
| 2 | 8,208 | 95.0% |
| 3–5 | 7,268 | 99.6% |
| 6+ | 13,442 | ~100% |

Non-empty addresses are missed at 1.7–2.7% whatever the name frequency. The address disambiguates chains.

**Look-alikes: nudged numbers cut both ways.** The legal form separates the two groups:
- 85% of the 5.4k rejected true pairs with a nudged house number keep, drop or reformat it ("Mountain Purecycle LLC 12446" ↔ "((LLC)) 12447");
- 70% of the 800 nudged-number orphan false positives add or change it ("Bright Voya LP 2" ↔ "Bright Voya Corp 3", "Tall Trading Ltd" ↔ "Tall Trading LLP").

The holdout y-rate in each score band shows it:

| model-v2 score | legal same | none | dropped | subset | added | changed | superset |
|---|---|---|---|---|---|---|---|
| 0.6–0.8 | 0.84 | 0.77 | 0.80 | 0.62 | 0.48 | **0.08** | **0.01** |
| 0.8–0.9 | 0.94 | 0.91 | 0.92 | 0.81 | 0.66 | **0.13** | **0.06** |
| 0.9–0.97 | 0.98 | 0.97 | 0.98 | 0.92 | 0.86 | **0.26** | **0.11** |

- 62% of orphan false positives add or change the legal form (27% change it), against 6.5% of true pairs (0.3% change it).
- On test, model v2 predicts a changed legal form 1.1–1.9× as often as on the holdout (US 0.64% vs 0.56%, India 0.19% vs 0.10%, France 0.78%). This matches the test's doubled look-alike density.

**Blocking misses with an address** (17.9k pairs; the counterfactual gain is +0.0032):

| type | pairs | why it is missed | key that recovers it |
|---|---|---|---|
| domain / handle | 7,442 | the joined name only prefix-matches ("renterianaborweddle" vs "...weddlepartners"). Address matches with short S1 addresses outrank it, and "ewinnovations.com" exists for 3 different S1 | name-only search with character 4-grams: prefix keys are shared by 56% |
| shares a word | 6,037 | a typo'd or dropped distinctive word ("Dynamic Nnsaq", "Federal LLC Services") with a number-less street. The only rare tokens are the typos, so the true S1 is never seeded | (name token × address word) compounds: shared by 38%, or 97% for Indic names |
| brand name | 2,759 | nothing in the name; the address has a different number or is shared | none reliable ((number, street) key: 8%) |
| Indic script | 1,435 | transliteration variants | (name × address word) compounds: 97% |

**Calibration.** Isotonic `pc` is reliable within about 0.03 per decile in every country × source cell, so the decision rule is not the problem. What limits the score is the information in the features.

## 3. Research

Sources are summarised from the research notes (Foursquare write-ups, EM papers); the links are in the session notes.

- **Kaggle Foursquare Location Matching (2022), 1st place.** Candidates → LightGBM (CV 0.875) → mdeberta-v3-base (MIT) cross-encoder on the survivors, with 70–90 GBDT features concatenated into the head (0.907) → blend (0.911) → graph merge of match sets (0.9166).
  - Every top team trained the pair model on the GBDT survivors, which are hard negatives by construction.
  - Cost warning: a base model at 128 tokens took up to 40 GPU-hours per epoch for one team. Keep max_len at 64 or below and score only the uncertain band.
- **Ditto-style input** (`[COL] name [VAL] … [COL] address [VAL] …`), tagging numbers, and pair-flip augmentation are cheap wins for text cross-encoders.
- **Candidate-list models** (Foursquare 2nd place's "transformer blocking" over each record's candidates; a 13th-place GNN) score all candidates of an entity jointly. Our stage-2 rivalry features cover part of this.
- **Decision.** An exact F-beta decision that models P(no match) directly (Dembczyński et al., GFM) beat the independence version on 5 of 6 datasets.
  - Cheap variant: a separate S1-level "no match" classifier feeding the DP's empty option.
  - Target: the 518 singletons given matches and the 1,668 empty non-singletons.
- **Look-alike stress test.** Add synthetic look-alikes (nudged number + business word, changed legal form) to the holdout at test density (about 2× train) and measure the precision drop. Use it to check the test-time threshold (G8).
- **Cross-script names.** Our in-data transliteration + dictionary already brought Indic names to parity (0.9872 vs 0.9870).
  - IndicXlit (MIT) is trained on external data (Aksharantar). Using it needs a human decision on the external-data rule, and the remaining Indic loss is small.

## 4. The v3 plan

| # | component | targets | status / evidence | expected |
|---|---|---|---|---|
| 1 | legal-form features (`legal.py`, `feats_legal.py`, group `lg`) in stage 1 and 2 | look-alike FPs, nudged-number misses | **gate passed** in stage 2: +0.00271 [0.00260, 0.00283] | +0.0027 or more with stage 1 |
| 2 | blocking v2: name × address-word compounds (`nw_words`), name-only search for one-token names (`ns_domain_len`) | 17.9k blocking misses with an address | **done**: pair recall 0.9857 → **0.9899** (India 0.9875, US 0.9916), oracle F0.5 0.9956 → 0.9970, candidates per S1 29.5 → 30.3 | +0.001 |
| 3 | `(number, street)` context key fix (`context.numstreet_keys`) | France (the old key used the street type) | code merged in PR #18, used from v3 | small on the holdout, France only |
| 4 | cross-encoder on the uncertain band as a stage-2 feature (G10): multilingual-e5-small or mdeberta-v3-base (MIT), OOF over the 3 groups, legal + number relations as text tags | typos, transliteration, brand/descriptor semantics, France | next, on the GPU | +0.001–0.003 (unmeasured) |
| 5 | S1-level P(no match) model for the DP's empty option (GFM variant) | singletons given matches, empty non-singletons | after v3 | +0.0002–0.0005 |
| 6 | look-alike stress test at test density | test precision (G8) | after v3 | protects the leaderboard |

**Not worth chasing:** empty-address records whose name is shared by several S1 (about 22k misses). No field in the record points to the owner.
