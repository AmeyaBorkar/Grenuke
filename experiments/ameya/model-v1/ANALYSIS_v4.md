# Where we fail, part 2: the generator's word-swap look-alikes in France (26 Sep, early morning)

Follow-up to `ANALYSIS_v3.md`. The ideas checked:
- French address clusters, self-training, adaptive cuts, typo repair, per-stratum calibration, a "no match" model;
- synthetic French pairs, a final fit on all of train, cross-encoder pretraining.

Each was measured against the holdout labels, the test data (label-free) or a leave-one-country-out stand-in for France. Holdout numbers are on the full shared holdout (549,699 S1). Scripts are named in each section; throwaway checks are in the session scratchpad (`deep/`).

## TL;DR

- **Root cause found: France accepts the generator's word-swap look-alikes.**
  - The generator makes look-alikes at the S1's own address (same house number and street) by putting a different real word in the slot of one S1 name word, legal form kept: "Arcot Motors Corp" → "Arcot Solutions Corp", "Troupe Ecole SAS" → "Troupe Centre SAS".
  - On the US/India holdout, 5,364 records fit this exact signature and **0.6% are true**. v4 predicts 27 of them, and those 27 are 93% true.
  - In France v4 predicts **16,971** (65 per 1,000 French S1) at a median pc of 0.989; v5 predicts 19,211.
  - Why: French descriptors (club, amicale, école, comité, sportive…) have no label odds. The label-free proxy flags look-alike words by moved house numbers, and this operation keeps the number.
- **The mirror error.** The generator's true-copy noise at the same address drops one word and appends a list word after the legal form ("Crandall Enterprises Inc" → "Crandall Inc Services"). US/India: 98–99.8% true. France's list is fils, cie, services, associés, groupe, développement, france; v4 leaves about 4,000 of these unpredicted.
- **Fix** (`post_ops.py`, countries without training labels only): drop op-B predictions, add op-A owner pairs.
  - Expected leaderboard gain: **+0.0027** if France follows the US/India rates; −0.0017 in the worst case (every French op-B record true and every op-A record false).
  - Holdout cost of the same drop: −0.000003.
  - The rules, lists and thresholds all come from US/India labels and label-free test counts.
- **An unseen country, measured on labels** (US-only model scored on India):
  - The proxy word odds recover the unseen-word loss: 0.882 → 0.960, against 0.983 in-country.
  - The rest (0.024) is country conventions: half confident false positives, half confident misses.
  - A stricter France threshold (G8) cannot help in this regime.
  - France in v4 is estimated at 0.97–0.98 (v3: 0.92–0.94, matching the leaderboard's implied 0.927).
- **The other ideas are small here:**
  - clusters: at most 0.001 on the leaderboard;
  - calibration strata: gaps ≤ 0.05;
  - typo repair: at most +0.0005 on the holdout, and it needs a full rebuild;
  - the "no match" model: +0.0001–0.0003.
- **A final fit on all of train** (`s1.py --all`, `s2.py --all`) ties on the holdout, as expected, and is packaged with the rules as the final candidate `2026-09-26-v5all-ops`.

## 1. The ideas, checked

| idea | what we measured | verdict |
|---|---|---|
| French address clusters | 11.1% of French S1 share an exact normalised address (max 101; 0.9% in groups ≥ 10) vs US/India 4–5.7% (max 10–14). On the holdout, clustered S1 score 0.984–0.987 vs 0.990–0.991 alone and carry 7–8% of the loss. France's contested predictions (the record's runner-up S1 ≥ 0.5): 0.003 per S1 (US/India 0.001) | real but small: ≤ 0.005 France F0.5, ≤ 0.001 on the leaderboard. No change |
| Self-training (France, test US/India) | US → India: +0.003 with the country's words known, −0.05 with them unseen (confirmation bias). With the proxy odds the remaining errors are confident convention errors (section 4), which pseudo-labels reinforce | skip |
| Adaptive per-S1 cut + owner pruning | done in v4: the candidate file is the stage-2 input set, 4.7 per S1. The README says the candidate file is not scored | done |
| Typo repair against the S1 vocabulary (blocking) | section 2: blocking misses are half empty-address records with common names (the key exists, the pair is cut among many same-name S1), 20% made-up names, 16% domains/concatenations (segmentation would join about 90%), 1.3% OCR, 0.5% acronyms | at most +0.0005 on the holdout; needs a full rebuild. Not now |
| Per-stratum calibration | holdout, owned pairs with pc 0.05–0.95, by empty address, name-sharing size, country and source: gaps ≤ 0.05, mostly +0.01–0.04 (the argmax selection effect). France cannot be calibrated without labels | skip |
| "No match" S1 model | capped at +0.0001–0.0003 earlier. France's empty share (5.3%) is at the generator's 5.59% | skip |
| Synthetic French pairs | the generator applies the same operations in every country with country word lists (section 3). France's failure is one operation whose words are French; the rule learned from US/India labels fixes it directly, which is what a synthetic generator would have had to encode | superseded by `post_ops.py` |
| Final fit on 100% of train | `--all`: the holdout becomes a fourth OOF group, so every model sees 75% of train instead of 50% and the holdout stays out of fold | running (`ameya-model-v5all`) |
| Cross-encoder pretraining | +0.0014 for the whole cross-encoder; hours of GPU for an uncertain gain | skip |

## 2. Holdout (US/India): where the 0.0099 is lost

From `analysis.py` (v3, same structure in v4):
- blocking misses (true record not a candidate of its S1): 19,163 pairs (0.0032);
- lost to another S1 (the record's argmax owner is wrong): 19,383 (0.0033);
- rejected below the rule: 19,273 (0.0031);
- stage-0 filtered: 1,241 (0.0002);
- false positives: 3,083 (0.0017).

- **Empty addresses dominate.** 63% of all missed true records have an empty record address, and only 54.5% of empty-address true pairs are found. Of the "lost" pairs, 17,595 of 19,383 have an empty address: a name-only record with several same-name S1 is a coin toss. This part is at the Bayes limit.
- **Blocking misses** (`deep/blockmiss.py`, 19,163 pairs):

  | record name vs its S1 | share | record address |
  |---|---|---|
  | shares a name token | 59.4% | 47.4 points of it empty (common names: the key exists, the pair is cut) |
  | unrelated (made-up brand word) | 19.7% | mostly no number / other number |
  | domain | 13.4% | |
  | concatenated tokens | 2.7% | |
  | empty name | 3.1% | |
  | OCR (5wift, La1iva) | 1.3% | |
  | acronym | 0.5% | |

- **Calibration by stratum** is within ±0.05 everywhere. Owned pairs are slightly underconfident (+0.01–0.04 true minus pc in 0.3–0.7), as argmax selection implies.

## 3. France: the generator's operations at the S1's own address

Label-free test counts per country, checked against the same signatures on the holdout labels (`deep/opab.py`, `deep/annotate.py`). Two agents' reports (generator catalogue, leave-one-country-out anatomy) are summarised in section 4.

**One S1 name word replaced, same house number and street word** (the added word is "real" if at least 20 S1 names of the country use it, "list" if in the op-A lists, a "garble" if its Indel similarity to the dropped word is ≥ 0.5):

| population | US/India holdout: pairs, true | v4 test predicted per 1000 S1: US / India / France |
|---|---|---|
| **op B**: real word in the slot, not list, not garble | 5,364, **0.6% true** | 0.05 / 0.04 / **65.4** (v5: 74.0) |
| **op A**: list word appended after the legal form / at the end | about 99% true (after legal form: US 99.8%, India 98.3%) | about 90 of France's 109 per 1000 predicted |
| garble in the slot (typo) | 95–99% true | predicted in every country |

- **The op-B words.**
  - US/India false op-B records swap business descriptors in place: solutions ↔ marketing, technologies ↔ foundation, services ↔ solutions.
  - The rare true ones are abbreviations (cl, bb, cn) and "technologies ↔ systems".
  - France's op-B records swap association descriptors: club ↔ amicale ↔ école ↔ comité ↔ sportive ↔ amis ↔ parents ↔ union ↔ centre.
- **The op-A lists.**
  - English: center, services, service, partners.
  - French: fils (37 per 1000 S1), cie, services, associés, groupe, développement, france (19–20 per 1000 each).
  - Other French words never appear in this signature: participations, holding, international and distribution are look-alike words that come with moved numbers.
  - v4 predicts fils/cie/services/associés at 90–97% but groupe only 56% and développement 48%. The proxy gives groupe and développement −4.8 because they also occur in moved-number look-alikes.
- **Why France is exposed.** The proxy odds (`lop`) flag a word by its moved-number share among close pairs. Op B keeps the number, so French descriptors get only −2 to −4. With the same number and street, the model then says 0.9–0.99.
- **Other same-address populations** are consistent with US/India or explained:
  - same name, nudged number: the French ones add or change the legal form (pattern A, correctly rejected);
  - made-up names at the address: France has twice the US count per S1 and scores them 0.43 vs 0.81–0.88; open;
  - suffix additions: France predicts 86% vs US/India 99.8% true; open, about +0.0001.

**The fix** (`post_ops.py`) applies to countries absent from the training labels:
- it drops predicted op-B pairs;
- it adds op-A pairs (list word after the legal form, at the end, or in the last slot of a name without a legal form) where the S1 is the record's argmax owner, the pair is in the candidate set, and no other S1 has the record.

On v4 it drops 17,088 predictions and adds 4,746 pairs in France (65.9 and 18.3 per 1000 French S1). On v5 it drops 19,336 and adds 3,278.

- **Forecast by per-S1 arithmetic** (0.14975 = France's share of test S1):
  - op-B drop: +0.00248 at the US/India true rate, −0.00115 if all were true;
  - op-A add: +0.00019 if all true, −0.00053 if all false.
- **Holdout cost** of the op-B drop applied to US/India: −0.000003.

### 3.1 The generator, reverse-engineered (agent report; `deep/generator/`)

Catalogue of the noise on true copies (per source) and on distractors, from the train labels, then the same detectors on France's test records.

- **Distractors, one machinery for every country.**
  - About 1.2 per S1 in train and 2.4 in test.
  - Look-alikes move the house number up by +d, d uniform over {1, 2, 3, 4, 5, 7, 9, 11, 13, 21}; 99.5% of US nudges are positive. True-copy nudges are symmetric, mostly ±1/±2.
    - The model has learned this without a signed feature: on the US holdout its pc tracks the true rate cell by cell (−2: 0.57 vs 0.60 true; +3: 0.006 vs 0.005; +10: 0.149 vs 0.152). A signed-nudge feature would add little.
  - They insert a word from a per-country list:
    - US: 21 place words plus Partners/Holdings/Group;
    - India: industries, enterprises, public, exports, group, ventures, overseas, holdings, infratech;
    - France: groupe, distribution, holding, participations, développement, international, france.
  - Or they change the legal form, or swap one name word in place (op B).
- **True-copy noise, per country and source.**
  - S2 is the upper-case vendor; S3 is Title case and the only source of "Brand DBA name" records.
  - France's true copies almost never get house-number noise: digit drops 6 per 1000 S1 (US 96).
  - French street-name typos are 4× the US rate.
  - The region is dropped or turned into a department in about a third of French copies each; "R"/"R." stands for Rue in 25%.
  - Accents are drawn from à ç é ô â è ï ë î ê ù û. There are no junk prefixes, ID suffixes, honorifics or <NULL>.
- **France vs its own look-alike words** (per 1000 French S1, true-copy cell = one word dropped + word appended after the legal form, same number):

  | word | true-copy cell | look-alike cell (inserted before the legal form, nudged) |
  |---|---|---|
  | groupe / développement / france | 27.6 / 33.5 / 30.3 | 76.4 / 81.9 / 92.6 |
  | distribution / holding / international / participations | 1.2–1.9 | 78.7–81.3 |
  | fils / cie / associés / services | 61.2 / 23.9 / 34.0 / 24.1 | 0.0–0.3 |

  - The look-alike operation leaks into the true-copy cell at 1–5% of its size. Groupe/développement/france sit there at 30–44% of their look-alike size, so they double as list-A words. v4 predicts only 31–44% of them there.
- **Other France-specific error sources** (per 1000 French S1, agent estimates):
  - in-place swaps accepted (FP): 65–90;
  - list appends rejected (FN): 25–35;
  - acronyms rejected (FN): 5–7. French acronyms run 7–22× the US/India rate and are about 100% true in train in every band.
  - Made-up brand names at the address are 97% true copies of *some* S1 at that address in train. For the record's best S1 they are only 40–45% true in the uncertain band, so leaving them is right.
- **Synthetic generator:** feasible in about a day from this catalogue, but superseded. The failure it would have fixed is the op-B/op-A confusion, which the rules address directly.

## 4. Leave one country out, dissected (agent report; `deep/loco_anatomy/`)

US-only stage-1 model scored on India's holdout, four settings reproduced exactly:
- a, in-country: 0.98346;
- b, US-only: 0.96106;
- c, India's words unseen: 0.88235;
- d, India's label-free proxy odds: 0.95984.

- **c − a = 0.101** is mostly confident false positives: look-alikes that differ by a word (patterns D, B, E). The proxy removes 77% of c's excess.
- **d − a = 0.024** is half false positives, half missed true records, in every pattern, mostly confident. It comes from India's conventions:
  - look-alikes nudge the second part of a compound number or swap Pvt Ltd for Limited;
  - true records keep only city/state, use native script, or prefix "Door No".
- d's best threshold equals a's, so a stricter rule for France (G8) only loses in this regime. It would have helped in c, which was v3.
- **Mapped to France with v4**, three routes give 0.969–0.973 (0.982 if stage 2 shrinks the penalty as it does in-country). That implies a v4 leaderboard of about 0.987–0.989.
  - The same method on the words-unseen setting gives 0.916–0.940, which brackets v3's leaderboard-implied 0.927.
  - France's remaining uncertainty is concentrated in same-number descriptor edits: 83 uncertain predictions and 82 near misses per 1000 S1, against about 2 in US/India. That is exactly the op-A/op-B population of section 3.

## 5. Leaderboard probes (packaged, validator PASS)

| folder | what the difference measures | expected |
|---|---|---|
| `2026-09-26-v4` | anchor | 0.987–0.989 (section 4) |
| `2026-09-26-v5all-ops` | final candidate: v5 features, all-data fit, rules; minus v4-frab = v5 + all-data | ≥ v4-frab |
| `2026-09-26-probe-v4-frab` | v4 + `post_ops` rules; minus v4 = France's op fix alone | +0.0027 |
| `2026-09-26-probe-v4-fr0` | v4 with France emptied; F_France = (LB_v4 − LB_fr0) / 0.14975 + 0.0559 (singleton share of every country: 5.59%) | |
| `2026-09-26-probe-v5-frab` | v5 + rules; minus v4-frab = v5's address normalisation in France | |
| `2026-09-26-probe-v4-in0` | India emptied (only if fr0 shows US/India off the holdout) | |

## 6. v5 (French address normalisation + EI)

| | v4 | v5 |
|---|---|---|
| holdout macro F0.5 (stage 1 / DP) | 0.98694 / 0.99015 | 0.98693 / 0.99013 |
| test France: predicted per S1 / empty | 3.370 / 5.3% | 3.399 / 5.2% |
| France op-A predicted per 1000 S1 | 90.5 | 94.6 |
| France op-B predicted per 1000 S1 | 65.4 | 74.0 |
| model's forecast, France | 0.980 | 0.979 |

The address normalisation finds more true records (op A +4.1 per 1000, department/region) but also makes op-B look-alikes match better (+8.6). With `post_ops` the second effect goes away, so v5 + rules should beat v4 + rules. The `v5-frab` probe checks this.

## 7. Final fit on all of train (`ameya-model-v5all`, `--all`)

The holdout becomes a fourth OOF group in stages 1 and 2:
- every model sees 75% of train instead of 50%;
- test gets the mean of four models;
- every train pair keeps an honest out-of-fold score.

| | v5 | v5all |
|---|---|---|
| stage 1 holdout | 0.98693 | 0.98695 |
| stage 2 early-stopping log-loss | 0.0386–0.0388 | 0.0379–0.0387 |
| holdout macro F0.5 (DP, shift 0) | 0.99013 | 0.99016 (Δ +0.00002 [−0.00003, +0.00007]) |
| test France: predicted per S1 / empty | 3.399 / 5.2% | 3.367 / 5.3% |
| model's forecast, France / US / India | 0.979 / 0.992 / 0.993 | 0.980 / 0.993 / 0.994 |
| `post_ops` in France: op B dropped / op A added | 19,336 / 3,278 | 18,434 / 6,086 |

- The holdout compares one 75% model with a bag of three 50% models and cannot see the test-time bag of four: a tie is the expected reading.
- **Final candidate:** `2026-09-26-v5all-ops` (validator PASS; candidates 4.68 per S1).
