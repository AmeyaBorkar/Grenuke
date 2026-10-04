# Decisions: FEA (pair features)

**Summary.**
- Pair features turn one (S1, record) pair into numbers the model can score. S1 is a Source-1 reference business, a record is a Source-2 or Source-3 vendor record that may be a copy of it, and a look-alike is a decoy that differs from a true copy in one business-defining detail, a word or the house number.
- Fifteen decisions, in time order: the features we kept (look-alike word odds, legal-form relations, signed house numbers, counts instead of rates), the two that France forced us to change (legal-form bitmasks, odds for words never seen in training), and the ones we rejected, deferred or never built.
- Scope: unless marked LB (public leaderboard), F0.5 means macro F0.5 on the local holdout (549,699 labelled US/India S1, no France). Evidence levels: [M] measured, [E] estimated, [R] reported, [U] uncertain. Times are IST. 1e-6 means 0.000001 of F0.5.

## Index

| ID | decision | when (IST) | status |
|---|---|---|---|
| D-FEA-01 | Keep the look-alike word features (Plan B's cut reversed) | 2026-09-25 13:56 | adopted |
| D-FEA-02 | Left out on purpose: no country, no postcode, no embedding cosines | 2026-09-25 13:56 | adopted |
| D-FEA-03 | Counts, not rates, for name-frequency and rivalry features | 2026-09-25 15:20 | adopted |
| D-FEA-04 | Features v1: learned Indic dictionary, typo-tolerant names, number-set relations, per-country IDF | 2026-09-25 17:42 | adopted |
| D-FEA-05 | Look-alike word odds learned out of fold (G3) and cluster support (G9) | 2026-09-25 18:06 | adopted (in model v2) |
| D-FEA-06 | Fix the (number, street) key for French addresses | 2026-09-25 19:28 | adopted |
| D-FEA-07 | Bakshi's normalisation and string-feature stages not wired into the model chain | 2026-09-25 evening | adopted in practice (implicit) |
| D-FEA-08 | Name-uniqueness features rejected; empty-address losses are a data limit | 2026-09-25 21:15 | rejected |
| D-FEA-09 | Legal-form relation features (`lg`) | 2026-09-25 21:42 | adopted; the bitmask columns were reverted by D-FEA-10 |
| D-FEA-10 | Drop the legal-form bitmasks from stages 0–2 (v4) | 2026-09-26 00:22 | adopted (reverts part of D-FEA-09) |
| D-FEA-11 | Label-free proxy look-alike odds for countries without labels (`lop`, `lo0`) | 2026-09-26 00:23 | adopted |
| D-FEA-12 | Pool-size-dependent rarity and rival features left as they are | 2026-09-26 00:41 | deferred (never done) |
| D-FEA-13 | Signed house-number features (`nx`) | 2026-09-26 05:45 | adopted |
| D-FEA-14 | Number-aware retrieval margin | 2026-09-26 16:01 | rejected |
| D-FEA-15 | Cap the dual-use French proxy words | 2026-09-26 16:01 | deferred (never packaged) |

Related records: the same France fixes seen from the France side are D-FRA-03 and D-FRA-09; the country and postcode rules are D-PRB-01 and D-NRM-01; the rules that use these signals are D-RUL-01 to D-RUL-03; the blocking tokenizer is D-BLK-04; the models that consume the features are in area MDL. The full feature catalogue is [FEATURES](../../experiments/ameya/model-v1/FEATURES.md). Feature counts by version: baseline v0 37, v1 73, v2 79, v3 87, v4 85 (the two bitmasks dropped) [R].

## Records

### D-FEA-01 · Keep the look-alike word features (Plan B's cut reversed)
- **When (IST):** 2026-09-25 13:56–14:15 · **Phase:** P0 · **Area:** FEA
- **Decided by:** Ameya (proposed by: agent for Ameya). The idea is Plan A's (Ameya's plan); Plan B (Sachi's plan) had cut it.
- **Status:** adopted
- **Problem:** Plan B dropped the "sibling distinctive-token module" as "subsumed by competition margins" (the gap between an S1 and its best rival S1 for a record). Did we still need per-word features for words that a record adds or lacks?
- **Options considered:**
  1. Rely on the competition margins and have no per-word features (Plan B).
  2. Keep extra-token features with learned per-word distractor odds (Plan A, gate G3).
- **Choice and why:** Option 2. Records that belong to no S1 (orphans) but sit close to an S1 on name and street keep the same first house number in only 12% of cases (true pairs 85%) and add a name word in 77% (true pairs 23%). The added words change the business (group, holdings, industries, exports, infratech, ventures, overseas). The noise words of true pairs are harmless (center, services, dba, shri/sri/smt, formerly, incorporated). And 37% of these orphans have no rival S1 at all, "so a margin has nothing to compare".
- **Evidence:** the look-alike signature, row 9 of the plan's evidence ledger [M] ([FINAL_PLAN §1](../../plans/FINAL_PLAN.md)); the 37% share [M] [chat:ameya/a2a1b62a 2026-09-25 13:56].
- **Outcome:** It became feature group `lo`: a first `name__extra_r_w` in v0, learned per-word log-odds in model v2 (D-FEA-05), label-free proxy odds for France (D-FEA-11), and the rules for look-alike patterns (area RUL).
- **Hindsight:** Look-alikes became the central problem of the whole competition, above all in France, where unseen French words got neutral odds. That was the first France failure.
- **Links:** [FINAL_PLAN §4.4, §12](../../plans/FINAL_PLAN.md) · [handover 2026-09-25_1414](../../docs/handover/2026-09-25_1414_ameya_final-plan.md) · [theory: string similarity](../theory/03-string-similarity.md) · D-FEA-05 · D-FEA-11

### D-FEA-02 · Left out on purpose: no country, no postcode, no embedding cosines
- **When (IST):** 2026-09-25 13:56–14:15 · **Phase:** P0 · **Area:** FEA / FRA / NRM
- **Decided by:** Ameya (proposed by: agent for Ameya). Both plans agreed on the country rule; the no-postcode design is a graft from Plan B.
- **Status:** adopted. The embedding cosines were planned and never built.
- **Problem:** France appears only in test, so any feature that identifies the country can break there. Plan A also kept a postcode field, and its feature list planned cosines of dense (SVD) text embeddings.
- **Options considered:**
  1. A `country` feature.
  2. Country-agnostic features with unsupervised statistics fitted per country (chosen).
  3. A postcode feature (Plan A) or none (Plan B).
  4. SVD embedding cosines (planned for the plan's v1 feature list).
- **Choice and why:**
  - No `country` feature, because it "breaks on France". IDF and TF-IDF (word-rarity weights) are fitted per country on train and test together, which is unsupervised and so adapts to France.
  - The French lexicons are hand-written and documented: street types, legal forms (SARL, SAS, SASU, EURL, SA, SCI, SNC, EI), bis/ter, Cedex, arrondissements, department to region. No GPL libraries (for example no `unidecode`); the Indic transliteration is our own code.
  - No postcode feature: 6-digit runs appear in 0.02% of India addresses, 5-digit tails in 0.33% of US ones, and none in France.
  - Name-only search only for empty or short addresses (3 tokens or fewer, about 5% of records): 46–54% of S1 share an exact name, so name-only search on every record floods the lists, and only 0.27% of true pairs have a weak address of more than 3 tokens.
  - The embedding cosines were never built. They were to come from the SVD views of the planned dense search, and that search was never built (D-BLK-05). No decision to drop them is recorded; the cross-encoders took that role (area CE).
- **Evidence:** ledger rows 6, 7 and 10 of the plan [M] ([FINAL_PLAN §1](../../plans/FINAL_PLAN.md)); the 0.02% and 0.33% shares [M] [chat:ameya/a2a1b62a 2026-09-25 13:56]; no feature list in the repo contains an embedding cosine [R] ([FEATURES](../../experiments/ameya/model-v1/FEATURES.md)).
- **Outcome:** Kept. But leaving out the country column was not enough: the legal-form bitmasks put French forms into values never seen in training, an implicit country signal that hurt France (D-FEA-10). The names-only view is part of the final blocking (Table 1 of the methodology).
- **Hindsight:** Any feature whose values are unseen in training (new bits, unseen words) behaves like a country feature.
- **Links:** [FINAL_PLAN §4.4, §6, §12](../../plans/FINAL_PLAN.md) · [AGENTS.md hard rules](../../AGENTS.md) · [methodology §3, §4](../../experiments/ameya/final-zip/doc/Documentation_template.md) · D-PRB-01 · D-NRM-01 · D-BLK-01 · D-FEA-10 · D-FEA-11

### D-FEA-03 · Counts, not rates, for name-frequency and rivalry features
- **When (IST):** 2026-09-25 15:20 (proposed) · 16:23 (implemented) · **Phase:** P1 · **Area:** FEA / FRA
- **Decided by:** agent for Ameya. It changed FINAL_PLAN §4.4, which said rates.
- **Status:** adopted
- **Problem:** "How many S1 share this name, or this (house number, street) pair" as a rate depends on the size of the S1 pool. France has 259k S1 on test; train US has 1.32M.
- **Options considered:**
  1. Rates per split and country (the plan).
  2. Log-counts (chosen).
- **Choice and why:** "As rates, France names look 3–4 times more common than anything in train. As counts, they look about as ambiguous, which is correct."
- **Evidence:** share of test S1 whose core name another S1 shares: France 48.8%, India 53.4%, US 38.7%. Mean S1 per name: France 16.01, India 17.95, US 11.5 on test; US 21.6 and India 19.47 in train [M].
- **Outcome:** `ctx__log_s1_same_name`, `ctx__log_s1_same_numstreet` and their record-side twins are log-counts. The later audit still saw a pool-size effect for the US (D-FEA-12).
- **Hindsight:** none recorded.
- **Links:** [issue #12] · [`ber.features.context`](../../code/business_entity_resolution/src/ber/features/context.py) · [FEATURES v3](../../experiments/ameya/model-v1/FEATURES.md)

### D-FEA-04 · Features v1: learned Indic dictionary, typo-tolerant names, number-set relations, per-country IDF
- **When (IST):** 2026-09-25 17:42–18:00 · **Phase:** P1 · **Area:** FEA
- **Decided by:** agent for Ameya (Ameya: "improve it further… go all in")
- **Status:** adopted
- **Problem:** Where did baseline v0 lose? On the dev holdout (0.9682), gain if the bucket were fixed: true pairs below the threshold +0.0131; blocking misses +0.0092; accepted look-alikes +0.0048; records given to the wrong S1 +0.0046; true pairs lost to another S1 by ownership +0.0012 [M]. Indic-name S1 (30% of India S1) scored 0.923 against 0.975 and carried 29.5% of the loss, because the baseline features fold Indic names to empty strings.
- **Options considered:**
  1. Tune the baseline (more rounds).
  2. New feature groups (chosen).
- **Choice and why:** Option 2, in four parts, 73 features in total (55 string and 18 context):
  - Indic names transliterated, plus an Indic-to-Latin dictionary of 693 entries learned from true pairs of training folds 5–19 only (tek to tech, kanstrakshan to construction, eksaports to exports).
  - Typo-tolerant token matching (edit distance 1, or 2 from 6 letters), with unmatched IDF mass per side and a substituted-token count: "a swapped first name is not a typo". It catches look-alikes such as "Cathrin Dunsmore" to "Walbert Dunsmore".
  - Skeleton (consonant-only) and skeleton-prefix overlaps, and concatenated-name scores for domains and hashtags.
  - Number relations over whole number sets; NaN rapidfuzz scores when a side is empty; per-country IDF; record-side rivalry counts.
- **Evidence:** stage 1 v1 on the holdout 0.9781 against 0.9683 for baseline v0: +0.0097 [0.0095, 0.0099] (India +0.0153, US +0.0060) [M]. The top feature by gain is `num__s1first_in_r`, whether the S1's first number appears among the record's numbers [M].
- **Outcome:** Kept. The final feature table (fuzzy name ratios, unexplained tokens, house-number relations, context) descends from this.
- **Hindsight:** none recorded.
- **Links:** [handover 2026-09-25_1958](../../docs/handover/2026-09-25_1958_ameya_model-v1.md) · [FEATURES](../../experiments/ameya/model-v1/FEATURES.md) · D-NRM-02

### D-FEA-05 · Look-alike word odds learned out of fold (G3) and cluster support (G9)
- **When (IST):** 2026-09-25 18:06 (coded) · 18:55 (learned) · 19:22 (measured) · 19:58 (handover) · **Phase:** P1 · **Area:** FEA
- **Decided by:** Ameya (proposed by: agent for Ameya; Plan A's idea, FINAL_PLAN gates G3 and G9)
- **Status:** adopted in model v2, bundled with blocking v1 (there is no isolated G3 ablation)
- **Problem:** A true copy adds noise words; a look-alike adds a business-changing word. The model needed a per-word prior. Brand names and Indic records sitting next to a confident sibling also needed support.
- **Options considered:**
  1. A hand-written word list.
  2. Target-encoded, out-of-fold log-odds of a true match when a word is extra or missing in close training pairs (chosen). Out-of-fold means each training pair's odds are computed without its own S1 group, so the label is never used on itself.
- **Choice and why:** Option 2, learned without the holdout and keyed by the token string "so test and France reuse train's statistics". Shrunk toward a prior (A_PRIOR 20; 6,630,237 close training pairs; prior rate 0.691). Cluster support (`cluster.py`) measures how similar a record is to the S1's other confident records (those with a stage-1 probability p1 of at least 0.5), which rescues brand names and Indic records.
- **Evidence:**
  - Learned table [M]: holdings −9.8, group −9.7, industries and enterprises about −8.7, ventures and public −8.6, exports, overseas and infratech −8.5, north/south/valley/harbor/metro about −7.6 to −7.7. Benign words: labs +0.7, c0mpany +0.7, lnc +1.1, fka +1.4, formerly +1.6.
  - `lo__extra_r_sum` and `lo__extra_r_min` rank in the stage-1 v2 top 25 by gain [M].
  - Model v2 against v1: +0.00431 [0.00418, 0.00445] (India +0.0100, US +0.0005), bundled with blocking v1 and cluster support [M]. Stage 2 with cluster support adds +0.0022 over stage 1 (0.9842 against 0.9820) [M].
  - Owned pairs in the uncertain 0.5–0.9 band on test fell from about 2× the holdout's (model v1) to about 1.2× (model v2) [M].
  - LOCO (leave one country out: train on one country, score another): a US-only model scores India at 0.96106 with the `lo` group and 0.94180 without it [M] [ANALYSIS_v3 §3].
- **Outcome:** In France, words never seen in training got odds of exactly 0 (neutral): "participations", "développement", "groupe" and "holding" never occur in train. That was one of the two causes of the France gap (D-FEA-10, D-FEA-11).
- **Hindsight:** The audit (finding 6) said the stage-2 cluster features "amplify accepted look-alikes" in France; the later SHAP review found their effect on French confidence about zero ([RESEARCH_v6 §2.9](../../experiments/ameya/model-v1/RESEARCH_v6.md)). The methodology lists "learned look-alike word odds" among the name features.
- **Links:** [handover 2026-09-25_1958](../../docs/handover/2026-09-25_1958_ameya_model-v1.md) · [ANALYSIS_v3 §3, §7](../../experiments/ameya/model-v1/ANALYSIS_v3.md) · [chat:ameya/19e315ba 2026-09-25 19:08] · D-FEA-01 · D-MDL-03

### D-FEA-06 · Fix the (number, street) key for French addresses
- **When (IST):** 2026-09-25 19:28–19:30 · **Phase:** P1 · **Area:** FEA / FRA
- **Decided by:** agent for Ameya
- **Status:** adopted (code merged in [PR #18]; used from v3 on, not in v2)
- **Problem:** The rivalry key took the first address word. In France that is the street type: "32 Rue André Maginot" became `32|r`, about 450 S1 per key on test, far outside the training range. On reordered records it took the state.
- **Options considered:**
  1. Leave it.
  2. Take the first significant word after the house number, skipping street types, articles and house markers (chosen).
- **Choice and why:** Option 2. It is a France-only bug that distorts the count features. The RE2 regex engine has no negative lookahead, so the skip words are blanked before extraction.
- **Evidence:** keys now read `32|andre`, `972|old`, `1048|gulabnagar`; 52 tests [M]. The gain was "small on the holdout, France only" [R] ([ANALYSIS_v2 §4](../../experiments/ameya/model-v1/ANALYSIS_v2.md)).
- **Outcome:** Used from model v3. French addresses kept breaking address keys later (suffixed numbers, typo'd street types), which led to rules v3 (D-RUL-03).
- **Hindsight:** none recorded.
- **Links:** [handover 2026-09-25_1958](../../docs/handover/2026-09-25_1958_ameya_model-v1.md) · [`numstreet_keys`](../../code/business_entity_resolution/src/ber/features/context.py) · [PR #18]

### D-FEA-07 · Bakshi's normalisation and string-feature stages not wired into the model chain
- **When (IST):** 2026-09-25 evening onward (implicit; Ameya's first feature build was at 17:42) · **Phase:** P1–P2 · **Area:** FEA / NRM
- **Decided by:** unknown. It was never recorded as a decision; it follows from Ameya building features v1 to v5 in `experiments/ameya/model-v1/`.
- **Status:** adopted in practice (implicit)
- **Problem:** The plan had Bakshi own normalisation (C3) and the string features (C8). Ameya's experiment chain moved faster and produced the gains.
- **Options considered:**
  1. Port Bakshi's `ber.normalize` and the `ber.features` string groups into the model chain.
  2. Keep Ameya's `feats.py` family (chosen in practice).
- **Choice and why:** Not stated. The facts: blocking used its own tokenizer "so blocking does not wait for the normalize stage" (D-BLK-04); the final `feats.py` imports only `ber.features.context`, Ameya's module; [PR #21] said "no predictive-quality claim is made until Sachi evaluates the downstream model", and no such evaluation appears in the sources.
- **Evidence:** a search of the final chain (`experiments/ameya/model-v1`, `experiments/bakshi/box`) finds no import of `ber.normalize` or of the `ber.features` string, token or number groups; only `ber.features.context` is imported (by `feats.py` and `post_ops.py`) [M, repo search]. The v3 analysis says the same: "Bakshi's C3 normalization is not used by v3" ([ANALYSIS_v3 §7](../../experiments/ameya/model-v1/ANALYSIS_v3.md)).
- **Outcome:** Bakshi's v0 stages remain in the package and its tests, but Composite B does not depend on them.
- **Hindsight:** For crediting: Bakshi's day-1 work was delivered and tested but did not reach the submission. His decisive contributions came on 26 and 27 Sep (the audit, the packaging, the 7B). One source dates the start of Ameya's chain "from 20:00"; the first feature build was at 17:42 [U].
- **Links:** [PR #20] · [PR #21] · [handover 2026-09-25_1658](../../docs/handover/2026-09-25_1658_bakshi_normalize-v0.md) · [handover 2026-09-25_2056](../../docs/handover/2026-09-25_2056_bakshi_features-v0.md) · D-BLK-04

### D-FEA-08 · Name-uniqueness features rejected; empty-address losses are a data limit
- **When (IST):** 2026-09-25 21:15 · **Phase:** P1 · **Area:** FEA / DEC
- **Decided by:** Sachi
- **Status:** rejected (the features); the conclusion was adopted
- **Problem:** In Sachi's error analysis of model v2, 61% of the below-threshold misses and 98% of the records taken by another S1 have an empty address. Her hypothesis: an exact name that no other S1 in the country shares can be trusted even without an address.
- **Options considered:**
  1. The 79 v2 features (holdout 0.97745 at stage 1, dev fold 0).
  2. Those plus five label-free columns (`ctx__s1_core_n`, `ctx__r_core_n`, `name__core_eq`, `name__core_eq_unique`, `addr__r_empty`): 0.97800.
- **Choice and why:** Not kept: +0.00054 [+0.00001, +0.00107], p_better 0.975, "real but far below the +0.002 bar". The breakdown shows little headroom. Among the 3,779 true candidate pairs with an empty record address (4.0%): exact and unique names (1,439) were already found 95.8% of the time (98.5% with the features); exact names shared by two or more S1 (1,126) are "ambiguous by construction", found 2.8% then 1.6%, and abstaining is correct under F0.5; only non-exact names (1,214) have headroom, about 0.6% of true pairs.
- **Evidence:** [M, dev fold 0, 27,651 S1] ([decision gate-name-uniqueness](../../docs/decisions/2026-09-25_2111_gate-name-uniqueness.md)). "Taken by another S1" is 0.26% of true pairs, almost all of them these ambiguous empty-address records.
- **Outcome:** "Do not spend more effort on them." The softmax-ownership idea (G5) was judged low value (D-DEC-02). The same conclusion was re-derived on 27 Sep: Bakshi's empty-address recall rules were 17–24% true against a break-even near 75%, and Sachi's copy-count test could not break the ties (D-DEC-12).
- **Hindsight:** Correct and cheap; it saved the team from chasing the largest-looking loss bucket. Note the bar (D-EVL-03): later components were accepted at much smaller gains once their confidence interval cleared zero (signed numbers +0.00021 in D-FEA-13, stage 3 +0.000055 in D-MDL-11). Under that later practice, +0.00054 with a lower bound above zero would have passed. The methodology still names empty-address records with changed names as the main loss.
- **Links:** [add_name_uniqueness.py](../../experiments/sachi/add_name_uniqueness.py) · [check_name_uniqueness.py](../../experiments/sachi/check_name_uniqueness.py) · D-PRB-03 · D-DEC-12

### D-FEA-09 · Legal-form relation features (`lg`)
- **When (IST):** 2026-09-25 21:42 (decision record; analysis and code 20:43–21:21) · **Phase:** P1–P2 · **Area:** FEA
- **Decided by:** Ameya (proposed and built by: agent for Ameya, under Ameya's 20:29 brief). Sachi had asked, in a message relayed before 21:42, whether the features use labels, whether log-loss and ECE (expected calibration error) also drop, and for a paired bootstrap.
- **Status:** adopted. The two bitmask columns were reverted by D-FEA-10; the relation features stayed.
- **Problem:** The blocking tokenizer, which the features reuse, drops legal forms, so the name features never saw them. Yet look-alikes change or add the form (LP to Corp, LLP to Limited, Ltd to LLP). In the 0.8–0.9 score band of model v2, a pair is true 94% of the time when the form is the same, 92% when dropped, 66% when added and 13% when changed (an earlier extractor gave 18% for changed). 62% of orphan false positives add or change the form (27% change it), against 6.5% of true pairs (0.3% change it). And 85% of the 5.4k rejected true pairs with a nudged number keep, drop or reformat it.
- **Options considered:**
  1. Keep v2.
  2. Add the `lg` group (8 pair features) to stage 2: a hand-written 20-bit legal-form mask per name (a bitmask: one bit per legal form; Latin forms with OCR variants such as c0rp, lnc and 1td; dotted acronyms such as L.L.C.; Indic words through consonant skeletons, praivet to pvt; French forms), then a relation code (none, same, dropped, added, subset, superset, changed), counts, shared and one-sided counts, and the two bitmasks.
- **Choice and why:** Option 2. The lexicon is hand-written and uses no labels, so there is no out-of-fold issue, and it cleared the +0.002 bar by a wide margin. Version 3 also put it into stages 0 and 1.
- **Evidence:** holdout 0.98436 to 0.98708, +0.00271 [0.00260, 0.00283], p_better 1.0; holdout log-loss 0.04978 to 0.03993; ECE 0.00070 to 0.00046; precision and recall 0.9970 and 0.9602 to 0.9982 and 0.9643; stage-2 early-stopping log-loss 0.0509 to 0.0405 [M]. Test: model v2 predicted a changed legal form 1.1–1.9 times as often on test as on the holdout (US 0.64% against 0.56%, India 0.19% against 0.10%, France 0.78%) [M].
- **Outcome:** In model v3 (holdout 0.98882), the biggest single holdout gain after v2. In France the bitmasks took values never seen in train (D-FEA-10).
- **Hindsight:** The relation codes travel across countries; raw bitmasks used as numbers do not. Only the relation codes should have gone in from the start. The decision record had warned: "The France descriptor swaps … keep the same legal form, so this does not address them."
- **Links:** [decision gate-legal-form-features](../../docs/decisions/2026-09-25_2142_gate-legal-form-features.md) · [ANALYSIS_v2](../../experiments/ameya/model-v1/ANALYSIS_v2.md) · [chat:ameya/19e315ba 2026-09-25 21:41] · D-FEA-10

### D-FEA-10 · Drop the legal-form bitmasks from stages 0–2 (v4)
- **When (IST):** 2026-09-26 00:22 (cause found) · 01:11 (v4 trained) · 02:07 (decision record) · **Phase:** P2 · **Area:** FEA / FRA
- **Decided by:** Ameya (proposed by: agent for Ameya; the audit agent a4fa18c7 flagged the same cause independently at 00:39, as its finding 2)
- **Status:** adopted (reverts part of D-FEA-09)
- **Problem:** French forms (SAS, SASU, SARL, EURL, SNC, SCI, SA) sit in bits 12–19 of the two bitmask columns, values of 4096 and above. They occur in 0.08% of train rows and 6–8% of test rows, so every French value lies beyond the largest training split. French look-alikes that add or change the form and move the house number ("Demployeurs Patrimoine SAS 176" to "… SASU 177") got a mean stage-1 score of 0.456.
- **Options considered:**
  1. Remap French forms to English bits at inference (the audit's suggestion: "inference-time only… about 40 minutes"; sarl to llc, sas to inc, sa to corp). Estimated +0.0005 to +0.002.
  2. Zero the bits.
  3. Drop both bitmask columns and retrain, keeping the language-independent relation features (chosen).
  4. Leave them.
- **Choice and why:** Option 3: `--drop leg__r_only_bits,leg__s1_only_bits`, plus a one-line fix of the unseen-token encoding (D-FEA-11) and EI added as a legal form. On 59,273 French pairs with p1 ≥ 0.05, the 30,518 with the form added or changed and the number moved scored 0.456 as is (43% above 0.5), 0.027 with the bits zeroed (0.8%) and 0.232 with French forms mapped to English bits (21%); the other 28,755 pairs did not move (0.807, 0.806, 0.808). Remapping therefore still left many look-alikes alive. Values outside the training range cannot be trusted in a tree model, and dropping them is the simplest country-agnostic fix.
- **Evidence:**
  - Where labels exist the bitmasks barely matter (LOCO, India holdout): US plus India 0.98346 to 0.98286 without them; US only 0.96106 to 0.95996. Indian forms (pvt, ltd, llp, opc) sit between the US bits [M] [ANALYSIS_v3 §3].
  - France had 12.2k such predictions, 9 times the US/India rate per prediction [M].
  - Stage-1 cost 0.9871 to 0.9869 [M]; the whole v4 package (this plus the proxy odds) against v3ce: −0.00006 [−0.00012, −0.00001], a tie on the holdout because the fixes are country-agnostic [M].
  - France pattern A (number moved and legal form added or changed) fell from 0.047 to 0.002 per French S1 [M, label-free count].
  - LB: the first upload that carried this fix with the other France work (v5all plus rules) scored 0.98781 against 0.97961 for v3, so the bundle is worth about +0.008 [M] ([LB 2026-09-26 #01](../../submissions/records/2026-09-26_sub01.md)). The fix alone was never isolated.
- **Outcome:** v4 trained with 85 features. The audit's other findings from the same pass: 3 (exact zeros, D-FEA-11) and 4 (pool size, D-FEA-12).
- **Hindsight:** "Numeric encodings of categorical codes extrapolate badly for unseen categories in trees." Leaving out the country column was not enough (D-FEA-02).
- **Links:** [ANALYSIS_v3 §2, §3, §7](../../experiments/ameya/model-v1/ANALYSIS_v3.md) · [decision model-v4](../../docs/decisions/2026-09-26_0207_model-v4-france-and-cross-encoder.md) · [chat:ameya/19e315ba 2026-09-26 00:22] · [chat:ameya/agent-a4fa18c7 2026-09-26 00:39] · D-FRA-03

### D-FEA-11 · Label-free proxy look-alike odds for countries without labels (`lop`, `lo0`)
- **When (IST):** 2026-09-26 00:23 (idea) · 00:40 (v1) · 00:55 (v2) · 01:09 (`lo0`) · **Phase:** P2 · **Area:** FEA / FRA
- **Decided by:** Ameya (proposed by: agent for Ameya). Version 1 was the research agent's top recipe, a per-word mixture inversion (Rogan–Gladen / BBSE).
- **Status:** adopted (the v2 method)
- **Problem:** The label-derived odds table gives words unseen in train exactly 0 (neutral), so "participations", "développement", "groupe" and "amicale" looked like noise words. In LOCO, a US-only model scores India at 0.961, and at 0.882 when India's words are unseen. A second artifact: the "no statistics" value was −1.94e-16 on train and the holdout but exactly 0.0 on test, and an adversarial classifier (one that tells train from test) separated them with AUC 0.95; it touched 11–14% of test predicted pairs (audit finding 3).
- **Options considered:**
  1. A hand-written French-to-English lexicon (groupe to group, holding to holdings). Considered at 23:50, not built.
  2. Version 1: invert a two-class mixture with train's P(moved | false) = 0.2286.
  3. Version 2: a word's moved-number share, mapped to the label-odds scale (chosen).
  4. Train on the proxy everywhere.
  5. Lo-dropout ("blank-out") training.
  6. Self-training (rejected at the time: D-FRA-02).
- **Choice and why:** Version 2, used only where a country has no labels. Among close pairs in the word's own country where it is the extra record word (or the missing S1 word), how often did the first house number move? Look-alikes move the number and true copies seldom do. A decreasing isotonic fit on US/India words maps the share to the label-odds scale; rare words shrink toward the neutral share; words with under 30 close pairs get exactly 0. Group `lo0` keeps the label odds for US/India, writes "no statistics" as exactly 0 and uses the proxy for France. Version 1 saturated: France's close pairs are 75% moved (US/India 73%), above the rate it assumed, so the prior collapsed to 0.001 and every French word came out 0. A share-to-odds map has no prior to saturate.
- **Evidence:**
  - The proxy follows the label odds with Spearman 0.74 (US) and 0.40 (India) [M]. Mapped odds: share 0.05 gives +2.2, 0.45 is neutral, 0.8 gives −4.8, 0.98 gives about −7.5.
  - Unlabelled, it finds the look-alike vocabulary: US midtown, holdings, group −7.3 to −7.8; India industries and exports −4.8; France groupe, holding, participations and développement −4.8 (moved share 0.79–0.90 over 59k–98k pairs each); French descriptors (club, école, amicale, comité) −2.1 to −3.8; benign suffixes (services, associés, fils, cie) +0.2 [M, label-free count].
  - LOCO, US-only stage-1 model scored on India (version 2, with version 1 in brackets): India's own proxy 0.95984 (0.93963); trained on the proxy 0.93679 (0.95031); dropout 0.93846 (0.94645). References: words known 0.96106, unseen 0.88235, no `lo` group 0.94180, in-country 0.98346 [M]. The proxy recovers 77% of the 0.101 that unseen words cost against in-country [M] ([ANALYSIS_v4 §4](../../experiments/ameya/model-v1/ANALYSIS_v4.md)).
  - French predictions per S1 3.470 to 3.370 (US/India 3.38); France pattern B (number moved and extra word) 0.047 to 0.007 [M, label-free count].
- **Outcome:** In v4 and every later model. It flags words only through moved numbers, which left France exposed to look-alikes that keep the number (op B: another real word put into the dropped word's slot; op A is the true-copy mirror, a word dropped and a list word appended). Those got the rules in area RUL (D-RUL-01).
- **Hindsight:** A strong idea, and a good case of a sanity check catching a silent failure (a constant odds column). Its blind spot was found two hours later by asking which generator operations keep the number. It also mislabels dual-use words as pure look-alike words (D-FEA-15).
- **Links:** [ANALYSIS_v3 §4, §7](../../experiments/ameya/model-v1/ANALYSIS_v3.md) · [ANALYSIS_v4 §4](../../experiments/ameya/model-v1/ANALYSIS_v4.md) · [decision model-v4](../../docs/decisions/2026-09-26_0207_model-v4-france-and-cross-encoder.md) · [chat:ameya/19e315ba 2026-09-26 00:54] · [chat:ameya/19e315ba 2026-09-26 01:09] · D-FRA-03 · [theory: self-training and domain shift](../theory/09-self-training-and-domain-shift.md)

### D-FEA-12 · Pool-size-dependent rarity and rival features left as they are
- **When (IST):** 2026-09-26 00:41–02:01 · **Phase:** P2 · **Area:** FEA
- **Decided by:** agent for Ameya
- **Status:** deferred (never done)
- **Problem:** Test US has half the S1 of train US. Rarity and rival counts shift (KS distance, the largest gap between two cumulative distributions, 0.10–0.13; audit finding 4), and US predicts +0.022 matches per S1 more than on the holdout.
- **Options considered:**
  1. A density-matched holdout or pooled IDF.
  2. Leave it (chosen).
- **Choice and why:** Leave it; the estimated cost was −0.0002 to −0.0004 [E].
- **Evidence:** [E] ([ANALYSIS_v3 §7](../../experiments/ameya/model-v1/ANALYSIS_v3.md)). Later checks: re-weighting the holdout to the test's name-group mix showed the half-size pool makes the US slightly easier, not harder. The extra US predictions sit mostly in one family (the record has an empty address and the S1's exact name): in a half-size pool fewer S1 share a name, so more such records have a single owner. The model's expected false positives barely move (+0.26 per 1000 S1) [M] ([RESEARCH_v6 §1](../../experiments/ameya/model-v1/RESEARCH_v6.md)). Separately, crowding (the test has 23% more records per S1) costs at most −0.00009 [M] (§2.6).
- **Outcome:** Not done.
- **Hindsight:** The low priority was justified.
- **Links:** [chat:ameya/19e315ba 2026-09-26 00:41] · D-FEA-03

### D-FEA-13 · Signed house-number features (`nx`)
- **When (IST):** 2026-09-26 05:45 (built) · 11:23 (gate) · **Phase:** P2–P3 · **Area:** FEA
- **Decided by:** Ameya (proposed by: agent for Ameya, from the finding of the generator-preprocessing fork, agent ace27900, its finding 8)
- **Status:** adopted (v6all and every later model)
- **Problem:** The number features were unsigned, so a true-copy edit of −1 looked like a look-alike nudge of +1. The generator's look-alikes move the number up by +d, with d in {1, 2, 3, 4, 5, 7, 9, 11, 13, 21} (99.5% of US nudges are positive), while true-copy edits are symmetric (mostly ±1 or ±2) or digit edits. France accepted far fewer true-looking number edits than US/India: 30–72% in the fork's classes (about 50% for pattern d, 25% over all candidates), against 84–100% in US/India.
- **Options considered:**
  1. The NUM rule in the post-processing rules (rejected: D-RUL-02).
  2. Features (chosen): `nx__d1` (signed first-number difference), `nx__nudge` (in the look-alike nudge set), `nx__digit_sub`, `nx__digit_swap`, `nx__suffix` (leading digits dropped), `nx__len_diff`.
  3. Nothing. The generator agent had said at about 04:00–04:37 that "a signed-nudge feature would add little", because the model already tracks the true rate cell by cell.
- **Choice and why:** Option 2, a features-only rerun of stages 1 and 2, row-aligned with the existing features. The research forecast was +0.0001 to +0.0002. It was kept at +0.00021: positive with the interval above 0, though far below the +0.002 bar, an early sign that the bar had changed.
- **Evidence:**
  - v5 to v6nx: 0.99013 to 0.99034, +0.00021 [+0.00016, +0.00025] (US +0.00029, India +0.00007) [M].
  - Stage-1 early-stopping log-loss about 2% lower in all three groups (0.0504, 0.0525, 0.0509 to 0.0496, 0.0513, 0.0500); stage 1 0.9869 to 0.9873; the DP picks shift +0.25; France +0.015 predictions per S1 [M] ([RESEARCH_v5 §8.3](../../experiments/ameya/model-v1/RESEARCH_v5.md)).
  - Design evidence, same name and street: a digit substitution outside the nudge set is 97–100% true (recall 0.95–0.96); a small negative d is 100% true (recall 0.935); truncation is 93% true (recall 0.977); +d nudges are 3.6% true [M] [chat:ameya/agent-ace27900 2026-09-26 05:28].
- **Outcome:** Part of v6all's +0.00063 (D-MDL-12).
- **Hindsight:** The call that it "would add little" was half right: the gain is small (+0.00021) but significant. Measuring beat reasoning.
- **Links:** [handover 2026-09-26_1123](../../docs/handover/2026-09-26_1123_ameya_solutions-round1.md) · [handover 2026-09-26_0554](../../docs/handover/2026-09-26_0554_ameya_research-part2-plan.md) · [chat:ameya/19e315ba 2026-09-26 05:46] · [chat:ameya/19e315ba 2026-09-26 11:23] · D-RUL-02

### D-FEA-14 · Number-aware retrieval margin
- **When (IST):** 2026-09-26 16:01–16:09 · **Phase:** P3 · **Area:** FEA
- **Decided by:** agent for Ameya (finding by the SHAP agent a9bd3e4e; SHAP splits a model's score into per-feature contributions)
- **Status:** rejected (the retrain, called track C, was never run; the label-free re-score was not adopted)
- **Problem:** SHAP showed the retrieval-margin features (`ret__margin_r`, `gap_r_best`, `tok_rank_r`; stage 2 inherits them through `s2__r_margin`) depressed in France by 0.4–2.8 logits. French house numbers are small and shared, so a rival S1 on the same street scores almost as high. France before the rules: 475.5 predicted pairs per 1000 S1 below pc 0.999 (pc is the calibrated stage-2 probability), against 252.8 for US/India.
- **Options considered:**
  1. Recompute the margin against rivals at the record's own house number only, and re-score stages 1–2 with the saved models (a label-free test).
  2. Retrain stages 1–2 with the new feature (about 2 h, 18–19 GB).
  3. Leave it.
- **Choice and why:** Leave it. The shortcut moved a mixed bag: the additions were mostly one-word swaps (which the rules already sort) and "same name, same number, other street" pairs (4.6 per 1000), which in France hold generic-name look-alikes. "Mixed and small", and without a retrain it cannot be checked on the holdout.
- **Evidence:** 3,231,869 French pairs share a house number; the features changed on 1,848,433; mean margin −0.194 to −0.046; France +4,460 and −1,423 predictions (+17.2 and −5.5 per 1000 S1) [E] [chat:ameya/19e315ba 2026-09-26 16:08]. SHAP gaps, France minus US/India, in logits: swap1_A −2.98 (word odds −1.87); add1_A −3.31 (−2.33); acronym −4.27 (retrieval −2.21; French margin 0.038 against 0.17); same name with the number missing on one side −4.05 (retrieval −2.82) [M]. Exact copies are fine (99.57% reach pc ≥ 0.999, against 99.73–99.83%).
- **Outcome:** Not adopted. "Fixing either moves only 1–2% of French predictions, so neither is the missing loss." Self-training later addressed the French biases directly.
- **Hindsight:** Much of France's remaining loss turned out to be generic-name decoys (same name and number, other street), which the 7B re-check caught. Neither fix targeted them.
- **Links:** [RESEARCH_v6 §2.9](../../experiments/ameya/model-v1/RESEARCH_v6.md) · [chat:ameya/agent-a9bd3e4e 2026-09-26 16:01] · D-FRA-09 · D-FEA-15

### D-FEA-15 · Cap the dual-use French proxy words
- **When (IST):** 2026-09-26 16:01–18:29 · **Phase:** P3 · **Area:** FEA
- **Decided by:** agent for Ameya (finding by the SHAP agent)
- **Status:** deferred (estimated, never packaged); overtaken by self-training
- **Problem:** The proxy odds gave "groupe", "france" and "développement" −4.84, the value of "holding". In France these words are both op-A list words (about 6,500 same-address pairs each) and look-alike insert words (about 26k nudged pairs each). Cost: −5 to −6 logits on about 75 pairs per 1000 French S1.
- **Options considered:**
  1. Cap them at −1.25, the US label odds of "partners" (France only, no retraining).
  2. Set them to the benign value +0.34 (rejected: it lets about 5,700 nudged look-alikes through).
  3. Leave them.
- **Choice and why:** Listed as "if time allows (needs a French re-score)". Worth about +0.0004 France F0.5 (+0.00006 to +0.0001 on the LB), far from the missing 0.01.
- **Evidence:** If "partners" gets its proxy value (−4.842) instead of its label odds (−1.255), the US holdout loses −0.00106 (0.990648 to 0.989593; 12,582 affected pairs) [M]. In France the cap gives +8,512 and −311 predictions; 6,078 of the additions the rules already add, and 2,434 are new, none of them a nudged look-alike [E] ([RESEARCH_v6 §2.9](../../experiments/ameya/model-v1/RESEARCH_v6.md)).
- **Outcome:** Never packaged. After self-training the rules needed to drop only 305 op-B predictions (v7nst) instead of 17,914 (v7n), so the model had learned these patterns itself.
- **Hindsight:** none recorded.
- **Links:** [chat:ameya/19e315ba 2026-09-26 16:08] · D-FRA-09 · D-FRA-13 · D-FEA-11
