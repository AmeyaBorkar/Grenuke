# Decisions: NRM (normalisation, lexicons, transliteration)

**Summary.**
- Five decisions on how we cleaned names and addresses before matching: what we wrote ourselves, what we dropped and what we left alone. All of it uses the provided data and hand-written lexicons only. (S1 is a source-1 business record; S2 and S3 are the two vendor sources matched to it.)
- We wrote our own Indic-to-Latin transliteration, a 693-entry dictionary and French address rules, skipped postcodes (too rare to help), and measured that vendor-format quirks needed no more normalisation.
- The blocking tokenizer, which doubled as the pipeline's normaliser, is D-BLK-04. The honorific stop words that were tried and reverted are in D-BLK-11. D-NRM-04 (final fit on all of train) is listed here because its source record also covered French normalisation.

## Index

| ID | decision | when (IST) | status |
|---|---|---|---|
| D-NRM-01 | No postcode field or feature | 2026-09-25 14:15 | adopted (Plan A's postcode field rejected) |
| D-NRM-02 | Our own Indic transliteration, skeletons and learned dictionary; no external transliterator | 2026-09-25 16:18–21:27 | adopted |
| D-NRM-03 | v5 French address normalisation and EI as a legal form | 2026-09-26 01:14–04:17 | adopted (neutral on the local holdout) |
| D-NRM-04 | Final fit on all of train (`--all`): the holdout becomes a fourth out-of-fold group | 2026-09-26 04:17 | adopted |
| D-NRM-05 | No further vendor-format normalisation | 2026-09-26 05:28 | rejected |

## Records

### D-NRM-01 · No postcode field or feature
- **When (IST):** 2026-09-25 14:15 · **Phase:** P0 · **Area:** NRM / FEA
- **Decided by:** Ameya (in `plans/DECISION.md`), from data checks that both plans' data agreed with
- **Status:** adopted. Plan A's postcode field was rejected.
- **Problem:** Plan A parsed postal codes (US 5 digits, India 6, France 5) into a field and into blocking keys (the keys the first pass uses to propose candidate pairs), and the 11:23 brief also listed "postcode keys". Would they pay?
- **Options considered:**
  1. A postcode field, keys and a feature.
  2. No postcode handling: a postcode is just another number in the address.
- **Choice and why:** Option 2. Postcodes appear in at most 0.5% of addresses, France included (25 Sep check), and in under 1.2% of records in Plan B's sample. At that rarity a postcode key would fire on at most one address in two hundred.
- **Evidence:** at most 0.5% of addresses [M]; under 1.2% of records, in Plan B's random sample of 33,189 S1 [M] ([FINAL_PLAN §1 #10](../../plans/FINAL_PLAN.md), [Plan B #11](../../plans/sachi/PLAN.md), [Sachi's decision log](../../plans/sachi/DECISION.md)).
- **Outcome:** Not built. No postcode appears in any feature list: baseline v0, dev kits v2 and v3 ([v0](../../experiments/ameya/baseline/FEATURES.md), [v2](../../FEATURES.md), [v3](../../experiments/ameya/model-v1/FEATURES.md)).
- **Hindsight:** Consistent with the submitted methodology ("no postcodes"). Same choice today.
- **Links:** [DECISION, rejected ideas](../../plans/DECISION.md) · [FINAL_PLAN §12](../../plans/FINAL_PLAN.md) · D-ORG-03

### D-NRM-02 · Our own Indic transliteration, skeletons and learned dictionary; no external transliterator
- **When (IST):** 2026-09-25 16:18 (blocking), 17:42 (features), 19:58 (learned dictionary and name n-grams), 21:27 (external transliterator set aside) · **Phase:** P1 · **Area:** NRM / BLK
- **Decided by:** agent for Ameya, building on Plan A's offset table and Plan B's (Sachi's) consonant skeleton; recorded as Ameya's decision in his handover. The question about the external model was left for a human ruling, and no ruling is recorded.
- **Status:** adopted (the external transliterator was not used)
- **Problem:** Indic-script names are 23.5% of India S2 names and 13.2% of S3 names. The baseline features folded them to empty strings, so S1 with Indic names (30% of India S1) scored 0.923 against 0.975 and carried 29.5% of the baseline's loss. 41.7% of the blocking misses had an Indic-script name. (Blocking is the first pass that proposes candidate pairs; a blocking miss is a true pair it never proposed.)
- **Options considered:**
  1. Our own rules. One ISCII offset table covers the nine Indic Unicode blocks (ISCII is the Indian script encoding whose letter order those blocks share, so the same offset means the same sound), with handling of the inherent vowel, the virama (the mark that cancels it) and vowel signs. Add consonant skeletons (phonetic merges, vowels dropped), so that "मार्केटिंग" and "Marketing" both reduce to `mrktng`, and drop transliterated legal forms (words such as Inc, LLC or SARL). Rules alone give "kanstrakshan", not "construction", so add a dictionary of Indic→Latin tokens learned from true pairs, and character 4-grams of names (every run of four letters) for the name-only search of blocking.
  2. IndicXlit, a pretrained transliteration model (MIT licence) trained on external data (Aksharantar). "Using it needs a human decision on the external-data rule."
  3. Leave Indic text as the baseline did (folded to empty). This was the starting point.
- **Choice and why:** Option 1. It is our own code, has no dependency and uses no external data. It transliterated all 752,869 Indic names in 3.8 s [M]. The dictionary has 693 entries (for example tek → tech, kanstrakshan → construction). It is learned only from true pairs in train folds 5–19, never from the holdout. IndicXlit was set aside: "Not needed now: Indic names are at parity", and it would have needed the ruling.
- **Evidence:**
  - India blocking pair recall (the share of true pairs that survive blocking) 0.9590 (v0, with transliteration) → 0.9836 (v1, with the dictionary and 4-grams); US 0.9860 → 0.9872 [M] [handover model-v1](../../docs/handover/2026-09-25_1958_ameya_model-v1.md).
  - Model v2 against v1: India +0.0100 and US +0.0005 on the local holdout F0.5. F0.5 is the competition's score, averaged over S1; the local holdout is the fixed 25% of labelled US/India S1 that no model trains on [M].
  - Indic-name slice 0.9872 against 0.9870 for the rest (gate G12, parity; no separate delta) [M] [ANALYSIS_v2 §3](../../experiments/ameya/model-v1/ANALYSIS_v2.md).
  - India local-holdout F0.5 0.9561 (baseline v0) → 0.9910 (v6all). This is the whole model path, not this change alone [ROADMAP 2.4](../../docs/ROADMAP.md).
- **Outcome:** India reached parity with the US. The submitted methodology lists "an Indic-to-Latin dictionary of 693 entries learned from training pairs" among the blocking repairs.
- **Hindsight:** No ruling on IndicXlit was ever needed, because our own transliteration already brought Indic names to parity. The question stays open as a rules question only.
- **Links:** [handover 2026-09-25_1958](../../docs/handover/2026-09-25_1958_ameya_model-v1.md) · [handover 2026-09-25_2147](../../docs/handover/2026-09-25_2147_ameya_analysis-v2-and-v3.md) · D-BLK-07 (blocking v1 uses the dictionary) · D-PRB-05 (item 8) · [theory: string similarity, transliteration](../theory/03-string-similarity.md)

### D-NRM-03 · v5 French address normalisation and EI as a legal form
- **When (IST):** 2026-09-26 01:14–01:31 (built), 03:28 (result), 04:17 (decision record) · **Phase:** P2 · **Area:** NRM
- **Decided by:** agent for Ameya, from audit finding #5 and the research agent's French lexicons; recorded as Ameya's decision (agent) in the handover
- **Status:** adopted into the v5 lineage (it is in v5all and v6all)
- **Problem:**
  - A third of French true pairs carry one to three unmatched region or department words.
  - "R" was dropped as a street type.
  - 4.1% of French predictions were absent from the S1's token list (US and India about 1%).
  - EI (entreprise individuelle, a French sole-trader form; 4.2k French test S1 and 16.4k records) was missing from the legal-form list.
- **Options considered:**
  1. Full French address parsing.
  2. A targeted fix: a department → region map for the three regions present (Hauts-de-France, Nouvelle-Aquitaine, Pays de la Loire), R → rue, articles and bis/ter/quater/cedex as stop words, and EI as a legal form.
- **Choice and why:** Option 2. It is cheap and testable. It was applied only after the v4 processes had loaded their code, so the v4 run stayed clean.
- **Evidence:**
  - Local holdout v5 0.99013 against v4 0.99015, a tie [M].
  - France, label-free count: op A found +4.1 per 1000 S1, but op B was accepted +8.6 per 1000 [M, label-free count] [ANALYSIS_v4 §6](../../experiments/ameya/model-v1/ANALYSIS_v4.md). Op A is a list word appended or swapped in, which makes a true copy. Op B is a real word swapped into the slot of an S1 name word at the S1's own address, which makes a look-alike.
- **Outcome:** Neutral on the holdout. In France it found more true copies and also made op-B decoys match better; the rule for op B (area RUL) removes them.
- **Hindsight:** Normalisation can help decoys as much as true copies. It was fortunate that the op-B rule arrived the same night.
- **Links:** [chat:ameya/19e315ba 2026-09-26 01:14] · [commits 8d86417, aa6d719] · [decision france-generator-ops-and-final-fit](../../docs/decisions/2026-09-26_0417_france-generator-ops-and-final-fit.md) · [theory: string similarity](../theory/03-string-similarity.md)

### D-NRM-04 · Final fit on all of train (`--all`): the holdout becomes a fourth out-of-fold group
- **When (IST):** 2026-09-26 04:17 · **Phase:** P2 · **Area:** NRM / MDL (the source record combined it with D-NRM-03)
- **Decided by:** Ameya (agent)
- **Status:** adopted
- **Problem:** The final model should learn from every labelled row, but the holdout is also the yardstick.
- **Options considered:** not recorded.
- **Choice and why:** The `--all` option makes the holdout a fourth out-of-fold (OOF) group in stages 1 and 2 (the first two model stages). An OOF score comes from a model that did not train on that row. Each of the four models is trained on three groups, about 75% of the labelled rows, and scores the group it did not see. Test gets the mean of the four models. Holdout numbers therefore stay out-of-fold.
- **Evidence:** v5all against v5: Δ +0.00002 [−0.00003, +0.00007], local holdout, "a tie, as expected: the holdout sees one 75% model, test the mean of four" [M].
- **Outcome:** The "all" models (v5all, v6all) were fitted this way. The gain from more data and from averaging four models cannot show on the holdout, as the evidence line explains.
- **Hindsight:** unknown (none recorded).
- **Links:** [decision france-generator-ops-and-final-fit](../../docs/decisions/2026-09-26_0417_france-generator-ops-and-final-fit.md) · D-EVL-01 · [theory: evaluation methodology, out-of-fold training](../theory/05-evaluation-methodology.md)

### D-NRM-05 · No further vendor-format normalisation
- **When (IST):** 2026-09-26 05:28 · **Phase:** P2 · **Area:** NRM / PRB
- **Decided by:** agent for Ameya (preprocessing fork). Ameya had asked "whether we can pre process the dataset itself better".
- **Status:** rejected (beyond the blocking repairs of D-BLK-11)
- **Problem:** S2 is the upper-case vendor and S3 is Title case (and the only source of "DBA" names, the trading names a business operates under). Do their systematic transformations cost matches?
- **Options considered:** state spelled out or abbreviated; native-script states; US city → county or neighbourhood aliases (257); house-number noise; street-type typos; name OCR (scanning errors); ordinals; domains.
- **Choice and why:** Every transformation left after normalisation is recovered at or above the average rate (false-negative lifts 0.25–0.67, where 1.0 is the average), except OCR, ordinals and domains, which went into blocking v3 (D-BLK-11). In France, variant-only pairs are predicted 99.84% of the time. When the address is present, the misses come from generator noise (number changed: lift 5.2; no common number: 6–7; a name word swapped: 3.4–4.4), not from formats.
- **Evidence:** 300k mined true pairs [M] [RESEARCH_v5 §5](../../experiments/ameya/model-v1/RESEARCH_v5.md).
- **Outcome:** No change to the normaliser.
- **Hindsight:** It answered a reasonable but expensive question in about 30 minutes of agent time.
- **Links:** [chat:ameya/19e315ba 2026-09-26 05:28] · D-BLK-11 · D-PRB-03
