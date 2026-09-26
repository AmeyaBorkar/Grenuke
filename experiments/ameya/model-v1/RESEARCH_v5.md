# Research, 26 Sep: why the leaderboard is below the holdout, where we fail, the candidate-set size

This note answers three questions:
- why an upload scores below the holdout;
- where the model fails and in what pattern;
- how small the candidate set can get (the organisers now rank a smaller candidate set higher).

**Part 1 (05:20 IST)** covers the gap, the holdout anatomy and the candidate-set size. **Part 2 (06:00 IST)** adds the three research threads and the ranked plan: ground-truth structure and joint decoding, preprocessing, France residuals.

- Holdout numbers are on the full shared holdout (549,699 S1).
- Test numbers are label-free.
- Scripts: `gap_check.py`, `cand_size.py`, `analysis.py`, `feats_nx.py`.
- The research threads' scripts are in the session scratchpad (`deep2/structure`, `deep2/prep`, `deep2/france`).

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

## TL;DR (part 2, 06:00 IST)

- **US/India: most of the remaining loss is at the Bayes limit.**
  - The generator is clean and measurable:
    - copy counts are independent of anything observable;
    - addresses are dropped independently (4.4% of copies);
    - an empty-address record is a true copy 97.7% of the time.
  - But 62.5% of the lost records sit between S1 with identical names and nothing else to separate them.
  - Every structural prior together gains **+0.00011** (joint re-scoring, section 4).
- **Preprocessing: the vendor formats are not where we lose.**
  - Every transformation left after our normalisation is recovered at or above the average rate.
  - In France, variant-only pairs are predicted 99.84%.
  - What is left is blocking work: domain names, OCR digits, ordinal street words. It is worth +0.0003–0.0005 on the holdout for one 3–4 h rebuild (section 5).
- **France's level is unknown; only an upload can measure it** (correction in section 8).
  - A structural estimator first put v5all + rules at 0.959 (leaderboard about 0.985).
  - Its two largest "false-positive" families turned out to be profiling artifacts: weak-address pairs and concatenated or domain names it failed to recognise.
  - Without them the estimate would be about 0.98, but then v2/v3 come out about 0.03 above their leaderboard-implied level. So about 0.027 of France loss (or 0.005 of US/India test loss) is invisible to every label-free check.
  - **The France-emptied probe (`2026-09-26-probe-v4-fr0`) is the only way to know.**
  - Version differences still hold: the France rules are worth +0.013 France F0.5 (+0.002 LB).
  - Section 8 adds three more rule populations checked on the holdout.
- **The candidate set is cut** to 3.70 per S1 at no cost (`2026-09-26-v5all-ops-c2`, decision record `2026-09-26_0532`).

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
- **Done** (decision record `docs/decisions/2026-09-26_0532_candidate-set-cut.md`):
  - `common.candidate_mask` defines the set: p0 ≥ tau0, p1 ≥ 0.02 and the record's top 2 S1 by p1.
  - `cands_final.py --p-cand 0.02 --top-r 2` writes it; `decide.py` with the same options only owns and predicts inside it. Stage 2 scores rows independently, so it needs no refit.
  - Holdout 0.990156 vs 0.990159, Δ −0.000003 [−0.000015, +0.000011].
  - Package `submissions/files/2026-09-26-v5all-ops-c2/`: 3.70 pairs per S1, validator PASS, matching sha256 `482caa7b…`.

## 4. The generator's ground-truth structure, and joint decoding

**The generator** (all 2,206,821 train S1; `deep2/structure/s01_truth.py`):

- **Ownership.** Every record belongs to at most one S1 and always sits in its S1's country (0 exceptions).
- **Copy count T** does not depend on anything observable. Singletons are 5.58–5.59% and mean T is 3.46 in every stratum: country, name length, legal form, shared-name group size from 1 to 50+.
- **Copies per source.**
  - About 5% of S1 are forced singletons.
  - The others draw their S2 and S3 counts independently, capped at 5 S2 and 6 S3 copies.
  - Given T, the S2/S3 split is far from binomial. At T = 2 it is one of each 71.9% of the time, against 49.9% for a binomial.
- **Addresses are dropped independently,** 4.41% per copy (US 4.74%, India 3.92%), exactly binomial per S1.
- **Orphans** (records with no owner) are 26% of records and **almost never have an empty address: 0.29%, against 4.41% of true copies.**
  - So an empty-address record is a true copy 97.7% of the time; the only question is which S1 it belongs to.
  - Orphans come at about one per S1, flat in T.
- **Copies never equal their S1 raw** (18 in 7.6M). 1.96% of S1 have raw-identical duplicate copies.

**Why the "lost" records are lost** (v5all holdout, 19,050–20,117 pairs, 91.7% with an empty address):

| true S1 vs the S1 that took the record | share | what separates them |
|---|---|---|
| identical names after folding | **62.5%** | nothing ("Prairie Institute" ×2, "City Solutions Private Limited" ×2) |
| names differ only in the legal form or a stop word | 16.3% | the record's form matches the rival 59% of the time (the generator changes forms) |
| different core names | 21.3% | made-up brand names at shared addresses ("Nexcira", "Tavodrex") |

- Calibration of the competing rows for empty-address records is within 0.01–0.05 in every group.
- The true S1 does not have systematically fewer copies than the rival.

**Joint re-scoring on the holdout** (parameters fitted without the holdout's records; paired bootstrap):

| method | holdout F0.5 | Δ [95% CI] |
|---|---|---|
| v5all | 0.99016 | |
| A: stage 3 on contested records (the rival S1's copies and pc per source) | 0.99022 | +0.00006 [+0.00002, +0.00009] |
| A with the *true* copy counts (upper bound for any count prior) | 0.99024 | +0.00008 |
| B: calibrate each empty-address record's total pc (its owner is a candidate 7–18 points more often than the total says in 0.3–0.9) | 0.99023 | +0.00007 |
| **A + B** | **0.99027** | **+0.00011 [+0.00007, +0.00015]** |

Upper bounds, if the unseparable could be separated:
- every lost pair to the right S1: +0.00335;
- every ambiguous empty-address record resolved: +0.00463.

**Verdict.** Stage 2's per-S1 features already hold the count prior. The empty-address ties are at the Bayes limit under F0.5: two S1 at p ≈ 0.49 each are both better left empty, because a false positive costs about 0.19 and a miss about 0.06. A + B is worth about +0.0001 on the leaderboard for 1–2 h of work.

## 5. Preprocessing: can the dataset be cleaned better?

**Vendor formats are not where we lose matches** (`deep2/prep/`, 300k mined true pairs, lifts = FN share ÷ TP share):

| transformation left after normalisation | share | FN lift | examples |
|---|---|---|---|
| US S3 spells the state out | 89% of US S3 | 0.27 | "Nixa, MO" → "Nixa, Missouri" |
| India S3 abbreviates the state | 57% of India S3 | 0.42 | Maharashtra → MH |
| India S2 native-script state / names | 13–24% | 0.25–0.33 | उत्तर प्रदेश |
| US S2 city → county / neighbourhood / nearby town (257 aliases) | 1.4% | 0.36–0.41 | Afton → UNION; Boston → DORCHESTER |
| house-number noise | | 0.07–0.39 | "07801", "##209", "Hn #899 House No.593" |
| street-type typos | | 0.19–0.67 | STRET, RODA, CIY |
| name OCR / typos | | 1.0–2.0 | capita1, 5UAREZ, lnc, c0rp |
| ordinal street words | | 1.1 (US) – 8.4 (India) | "20th Avenue" → "Twentieth Ave" |
| domains and handles | | 2.8–3.4 | BLUEGRILL.COM, @LUCKYICE, acnservicescom |

France, from confident pseudo-pairs:
- vendor variants (cours → crs, résidence → res, appartement → app, cie ↔ compagnie, frères → frs, street-name typos, OCR forms 5arl/5as, region dropped in 30%) are predicted **99.84%** when they are the only difference;
- no empty French S1 has such a candidate.

**When the address is present, the misses come from generator noise, not formats:**
- first number changed: lift 5.2;
- no common number: 6–7;
- name word swapped: 3.4–4.4.

**What preprocessing can still win** (all in blocking or features; one rebuild of blocking + features + stages, 3–4 h):

| change | target | holdout gain |
|---|---|---|
| segment domain/handle names into S1 words + initials; send long one-token names to the n-gram view | 2,092 FN (97.7% are blocking misses; when they are candidates, 99.9% are accepted) | +0.0002–0.0003 |
| OCR digit repair (0→o, 1→l, 5→s … when the repaired word is in the S1 vocabulary); honorifics sree/shree/om/maa | about 1,100 FN | +0.00005–0.0001 |
| ordinal street words → digits | 477 blocking misses | +0.00005–0.00008 |
| signed first-number difference, digit-edit flag, nudge-set flag (features only) | small negative d is 100% true at recall 0.935; digit substitutions 97–100% true at 0.95 | +0.0001–0.0002 |

Total: about +0.0003–0.0005 on the holdout, +0.0003–0.0004 on the leaderboard. The empty-address losses (69% of misses) are untouched.

**One France finding.** Same name, same street, a number change that is not a look-alike +d nudge, legal form the same or dropped:
- France accepts only 30–72% of these pairs, though the same classes are 97–100% true in US/India;
- about 16 per 1000 French S1;
- ≤ 0.0015 France F0.5, ≤ 0.0002 leaderboard;
- e.g. "Nantes Comite SARL | 9 Rue Arsène Leloup" → "Nantes Comite | 8 Rue Arsene Leloup", pc 0.35.

## 6. France: where it still fails (label-free)

**Method.**
- A structural edit profile of every pair is computed from the raw records, independent of feature versions:
  - name edit: same, noisy, acronym, domain, one word added/dropped/swapped;
  - the added word's class (list word, real, rare, pseudo-word, garble) and its position;
  - the legal-form relation;
  - house-number relation: equal, +1/+2, −1/−2, the +3…+21 nudge set, digit edit, other, missing, empty address;
  - street word same or different.
- It covers all blocking candidates: 16.6M holdout pairs and 16.3M test pairs (all of France and a 15% sample of US/India).
- Derived without labels, the list words match the hand lists exactly:
  - US/India: center, partners, service, services;
  - France: fils, associés, services, groupe, cie, développement, france.
- Scripts are in the session scratchpad (`deep2/france/`).

**Transferring absolute truth rates per profile fails.**
- US from India: 0.855; India from US: 0.729; France v2/v3: 0.80–0.85.
- Truth shares are country-specific. France has twice the exact copies (1,018 vs 510 per 1000 S1) and five times the "same name, same number, other street" pairs, because its names are generic ("Lille Club").

**The share-shift estimator works.**
- France predictions beyond the US/India predicted share of a profile count as false positives, at US/India's truth rate among unpredicted pairs.
- Misses count only in profiles that are at least 90% true in both US and India.
- It gives France **0.936 / 0.930 for v2 / v3**, against the leaderboard's 0.929 / 0.927. That is within 0.002–0.007, slightly optimistic, with the right order.

| | v2 | v3 | v4 | v4 + rules | v5all | v5all + rules |
|---|---|---|---|---|---|---|
| France F0.5 (estimated) | 0.936 | 0.930 | 0.946 | **0.959** | 0.945 | **0.959** |
| France predicted per S1 | 3.478 | 3.539 | 3.370 | 3.323 | 3.367 | 3.320 |
| leaderboard (forecast) | 0.97608 (actual) | 0.97961 (actual) | 0.983–0.984 | | | about 0.985 |

- The forecast is lower than the earlier leave-one-country-out forecast (0.987–0.989 for v4). The v4 upload decides between them.
- Differences between versions are more reliable than the level:
  - the rules add **+0.013–0.014 France F0.5 (+0.002 LB)**;
  - v5all is −0.0016 against v4 and ties once the rules are applied;
  - v4 beats v3 by +0.017.

**France's likely false positives (acceptances beyond the US/India share) and misses, per 1000 French S1:**

| family | v2 | v3 | v4 | v4 + rules | v5all | v5all + rules |
|---|---|---|---|---|---|---|
| word swap/add (real or rare word) | 94.4 | 108.8 | 63.7 | 7.7 | 69.8 | **8.6** |
| number nudged +1…+21 | 6.2 | 34.8 | 0.0 | 0.0 | 0.0 | 0.0 |
| list-word append | 5.0 | 4.1 | 0.1 | 0.1 | 0.0 | 0.1 |
| **weak address (empty / no number)** | 66.2 | 75.4 | 73.7 | 73.7 | 74.3 | **74.3** |
| **unrelated name** | 46.1 | 50.7 | 49.5 | 49.5 | 48.7 | **48.7** |
| other | 11.1 | 10.1 | 9.8 | 9.8 | 9.9 | 9.9 |
| misses in profiles ≥ 90% true | 30.5 | 30.0 | 52.3 | 34.2 | 57.9 | 34.7 |

- **The two families no version touched** (weak address, unrelated name) **are artifacts, not false positives** (section 8):
  - France's "unrelated" names are mostly its own words concatenated into domains, with accents dropped, stop words and legal forms kept, or words reordered ("Fédération des Commerciale" → "fdrationdescommerciale.com"; "Fitness Club SASU" → "clubfitness.com"). Domain plus unrelated copies per 1000 S1: France predicted 220, US true 214, India true 202.
  - France predicts 54% of its empty-address records, against 62–64% in US/India.
  - So the estimator's level (0.959) is not reliable. It matched v2/v3 by coincidence.
- **Five systematic errors remain after the rules** (per 1000 French S1; US/India truth in brackets):
  - **a. Op-B swaps where the record's street has a typo** [0.0–0.8% true]. The number/street key differs, so the rules miss them: 6–7 false positives.
    - Examples: "Delices Groupement SAS | 64 Rue Bonnefin" → "Delices Comite S.A.S | 64 Rue Bonneuin" (pc 0.978); "Pogo Club SASU | 14 Rue d'Antin" → "POGO CULTURELLE SASU | 14 Rue D'attin".
    - Fix: street within edit distance 2. **+0.0013 France F0.5.**
  - **b. A list word appended with no word dropped, same address** [99.6% true]. France predicts 63%: about 5 misses.
    - Example: "Chasseurs & Fils SAS" → "Chasseurs Fils SAS France" (pc 0.10).
    - **+0.0004.**
  - **c. Acronyms at the same address** [about 100% true]. France has 58 pairs against 1–2 in US/India and predicts 87.5%: about 7 misses.
    - Example: "Ets Motards SAS" → "EM" (pc 0.74).
    - **+0.0006.**
  - **d. Same name and street, −1/−2 or a one-digit edit of the number** [US 99–100%, India 84–97%]. France predicts about 50%: about 7 misses.
    - Example: "Mérignac Maison SAS | 83 Av de la Marne" → "93 Av. De La Marne" (pc 0.38).
    - **+0.0006.** The signed number features (`feats_nx.py`) address it in the model.
  - **e. Typos in 2–3-letter codes:** "YU Primaire SASU" → "YYU Primaire SASU" (pc 0.00). Part of 5.9 misses.
- **Checked and fine:**
  - "same name, same number, different street" pairs are genuinely different streets ("20 Rue Jules Siegfried" vs "#20 Avenue Des Roses");
  - weak-address acceptance per S1 overall matches US/India (235.6 vs 237.6/238.9 per 1000).
- **US/India on test vs the holdout** (profile view):
  - 11–12% more candidates and 25–28% more look-alike-profile pairs per S1;
  - predicted per S1 and true-copy profile rates match (exact copies 508.8 vs 510.1 per 1000);
  - no sign that US/India score below the holdout.

## 7. The best ways to overcome the issues (ranked)

| # | issue | action | expected gain | cost | status |
|---|---|---|---|---|---|
| 1 | France can only be measured on the leaderboard | upload `2026-09-26-v4`, `-probe-v4-frab` and the final candidate `-v5all-ops-c2`; `probe-v4-fr0` gives France exactly | the France level and the rules' true value | uploads | captain |
| 2 | organisers rank smaller candidate sets | p1 ≥ 0.02 and the record's top 2 S1 | 4.68 → 3.70 per S1, holdout tie | done | `2026-09-26-v5all-ops-c2` |
| 3 | France patterns a–e | `post_ops.py` v2: typo-tolerant street key for B and A, list-word appends, acronyms; number edits and code typos measured and not applied | about +0.002 France F0.5 ≈ +0.0003 LB | done | §8.1, `2026-09-26-v5all-ops2-c2` |
| 4 | weak-address and unrelated-name acceptance in France (123 per 1000 S1) | verified with generator invariants | none: profiling artifacts (section 8); France's identical-name ties are worth at most +0.0005 France F0.5 | done | no fix |
| 5 | unsigned house-number features | `feats_nx.py` (signed difference, nudge set, digit substitution/swap, leading digits dropped), stages 1–2 refit | **+0.00021 [0.00016, 0.00025] holdout** | done | §8.3; in the rebuild |
| 6 | the rival S1 is invisible to stage 2 | stage-3 joint re-scoring (A + B) | +0.00005 [0.00002, 0.00008] holdout | done | §8.4; optional, not in the recipe |
| 7 | blocking misses: domains, OCR, ordinals | segmentation, OCR repair, ordinal → digit; full rebuild | holdout blocking recall 0.98992 → 0.99135; with `nx`, holdout +0.00063 | done | §8.5; final `2026-09-26-v6all-ops-c2` |

Items that are **not** worth doing, from this research:
- self-training;
- count priors beyond stage 2;
- per-stratum calibration;
- a stricter France threshold;
- vendor-format normalisation beyond today's;
- source caps (they bind 4 times).

## 8. Solutions, round 1 (26 Sep, 06:00–14:30 IST)

### 8.1 France rules, version 2 (`post_ops.py`)

`post_ops.py --measure` classifies every candidate pair of the US/India holdout into the generator's edit populations and prints their truth rates. It uses the same code that runs on France:
- at the S1's own address, meaning the same first house number and the street word equal or within a typo;
- `name_edit` for the name; `number_edit` for the house number.

| population (at the S1's address) | US truth / predicted | India truth / predicted | France action |
|---|---|---|---|
| B: a real word swapped into the slot of an S1 word | 3.1% / 3.1% | 0.6% / 0.5% | **drop** (19,503 pairs) |
| B with a street typo (new) | 5.1% | 0.0% | drop (included above) |
| A: a word dropped plus a list word appended | 99.7% / 99.7% | 98.3% / 98.3% | **add** 7,227 (was 6,086) |
| A with a street typo (new) | 99.8% | 97.1% | add (included above) |
| APP: list word appended, nothing dropped (new) | 98.9% / 99.0% | 99.6% / 99.6% | **add** 3,877 |
| ACR: the name as its initials (new) | 99.9% / 98.0% | 99.8% / 98.4% | **add** 853 |
| CODE: typo in a 2–3 letter code | 42.6% | 44.0% | not used |
| NUM: same name, house number −1/−2 | 97.6% / 88.5% | 78.2% / 76.9% | not used |
| NUM: one digit substituted | 91.0% / 89.1% | 70.9% / 70.0% | not used |
| NUM: one digit inserted/deleted | 95.0% / 94.3% | 90.4% / 90.3% | not used |

- Adds require four things:
  - the pair is in the candidate set;
  - its S1 is the record's best-scoring S1;
  - the record is not predicted elsewhere;
  - the S1's country has no training labels.
- 1,562 adds fall outside the smaller candidate set, so they are not made. That is worth about +0.00005 on the leaderboard.
- **NUM is not used.** The model already predicts US/India's number edits at about their truth rate, so the unpredicted ones are mostly false in India. France's truth rate is unknown and adding only pays above about 75% precision. The signed number features (8.3) let the model learn it instead.
- **CODE is not used** (43–44% true).
- Against the first rules, on the same v5all predictions with the cut: about +1,100 more look-alike drops, +1,141 A, +3,877 APP and +853 ACR. That is about **+0.002 France F0.5 (+0.0003 LB)**.
- Package: `2026-09-26-v5all-ops2-c2`.

### 8.2 France's weak-address and unrelated-name families: artifacts, not errors

Checked against the generator's invariants (`deep2/sol_france/`):

- **Unrelated names.** France predicts 149 unrelated-name pairs per 1000 S1, against 76–79 in US/India. But its "unrelated" names are mostly its own words concatenated into domains, which the profiler missed:
  - accents deleted: "Fédération des Commerciale" → "fdrationdescommerciale.com";
  - stop words or legal forms kept: "Lille Sportive EURL" → "lillesportiveeurl.com";
  - words reordered: "Fitness Club SASU" → "clubfitness.com".

  Domain plus unrelated copies per 1000 S1:

  | | France (predicted) | US (true) | India (true) |
  |---|---|---|---|
  | domain + unrelated copies per 1000 S1 | 220 | 214 | 202 |

  Made-up brand names: France 38 predicted, against 44–47 true in US/India.
- **Weak addresses.** France has 166 empty-address records per 1000 S1, against about 158 expected from the generator. It predicts 54% of them, against 62–64% in US/India. It has fewer weak-address candidates per S1 (2.97, against 6.1 US and 3.5 India), so the same prediction count looked like a larger share.

  Precision estimated from the holdout's precision by stratum: France 0.972 against US/India 0.983, an excess of about 2.2 false positives per 1000 S1 (≈ 0.0004 France F0.5).
- **Identical-name ties.** France's pc is overconfident on identical-name ties: 14.6% of its empty-address records have pc summed over candidate S1 above 1.1, against 0.2% on the holdout. Ownership and the DP keep them out: about 650 pairs are predicted. Renormalising nets about zero, so there is no fix.
- **Consequence: the structural estimator's France level (0.959) is not reliable.** Without the artifacts, v5all + rules would be about 0.98, but v2/v3 would then be about 0.955, far above the leaderboard's 0.927–0.929.
  - So either about 0.027 of France's loss is invisible to every label-free check, or US/India on test sit about 0.005 below the holdout.
  - **`probe-v4-fr0` settles it:** LB_fr0 = 0.38274 F_US + 0.46751 F_India + 0.14975 × 0.0559. So it gives the US/India test level directly (expected 0.8507 if they score like the re-weighted holdout), and LB_v4 − LB_fr0 gives France.

### 8.3 Signed house-number relations (`feats_nx.py`): +0.0002

`nx` group:
- signed first-number difference;
- look-alike nudge set;
- one digit substituted or swapped;
- leading digits dropped;
- length difference.

The v5 recipe with and without it, three OOF groups, same candidates:

| | v5 | **v6nx** (+ `nx`) |
|---|---|---|
| stage-1 early-stopping log-loss (groups 0/1/2) | 0.0504 / 0.0525 / 0.0509 | 0.0496 / 0.0513 / 0.0500 |
| stage-1 holdout (best threshold) | 0.9869 | 0.9873 |
| **holdout macro F0.5 (DP)** | 0.99013 | **0.99034** |
| gate vs v5 (paired bootstrap) | | **Δ +0.00021 [+0.00016, +0.00025]**; US +0.00029, India +0.00007 |
| test predicted per S1 (US / India / France) | 3.382 / 3.367 / 3.399 | 3.386 / 3.370 / 3.414 |

The DP picks shift +0.25 (v5: 0). France gains 0.015 predictions per S1: the model now accepts the true-copy number edits that France rejected (§6 d). It is in the rebuild (§8.5).

### 8.4 Stage-3 joint re-scoring (`stage3.py`): +0.00005, optional

The structure thread's A + B as a pipeline step between stage 2 and the decision:
- A: an out-of-fold XGBoost on contested records, seeing the rival S1's pc and copies per source;
- B: record-mass calibration of empty-address records.

Runtime 72 s, peak 1.7 GB.

| variant (with the candidate cut) | holdout | Δ vs v5all-c2 |
|---|---|---|
| A + B | 0.990207 | +0.000051 [+0.000023, +0.000079] |
| A only | 0.990198 | +0.000042 [+0.000016, +0.000067] |

- It is half the prototype's +0.00011. The prototype was the best of three variants on the same holdout, and with the top-2 cut every contested record has two S1, which leaves little for B.
- Test predictions per S1 move by at most 0.001.
- **Not in the final recipe** (+0.00004 LB for one more stage). It is kept for a last step if everything else is done.

### 8.5 Blocking repairs (`ameya/block-v3`) and the v6all rebuild

Decision record `docs/decisions/2026-09-26_1122_blocking-v3-repairs.md`. `ber/block/repair.py` adds extra name tokens for S2/S3 records:
- domain/handle names segmented into the country's S1 words;
- OCR digits repaired when the result is an S1 word;
- ordinal street words become digits.

Honorifics as stop words were tried and reverted. Dev pool (110k S1, 2.6M records):

| slice | forward recall before → after |
|---|---|
| all | 0.97240 → 0.97939 |
| domain/handle names | 0.86813 → 0.93713 |
| OCR digits | 0.90632 → 0.95215 |
| ordinal words | 0.97165 → 0.98984 |

Candidates per S1 are unchanged.

**The v6all rebuild** (`run_v6all.sh` in the session scratchpad; resumable per step, and each heavy step waits for free memory):

    blocking v3 → features fx5 (+ nx) → lo, lg, lop, lo0 → s1 --all → cross-encoder → s2 --all →
    decision with the candidate cut (gate vs v5all-c2) → candidate set → France rules v2 → 2026-09-26-v6all-ops-c2

About 3.5 h (11:30–14:27).

**Result** (decision record `docs/decisions/2026-09-26_1425_model-v6all-final.md`):

| | v5all-c2 | v6all-c2 |
|---|---|---|
| holdout blocking pair recall | 0.98992 | 0.99135 (missed 19,163 → 16,455, 0.6% fewer pairs) |
| stage 1 | 0.9870 | 0.9878 |
| holdout macro F0.5 | 0.990156 | **0.990788** |
| gate | | Δ +0.00063 [+0.00057, +0.00070] (US +0.00068, India +0.00056) |
| recall | 0.9713 | 0.9738 |
| decision rule | | threshold 0.70 (DP +0.00004, not significant) |
| candidates per test S1 | 3.70 | 3.70 |
| final predictions per S1 (US / India / France) | 3.382 / 3.367 / 3.336 | 3.390 / 3.376 / 3.360 |

**Final candidate: `submissions/files/2026-09-26-v6all-ops-c2/`** (validator PASS, matching sha256 `0f6d8985…`).

## 9. Leaderboard reading, 26 Sep afternoon

v5all + France rules v2 + the candidate cut (`2026-09-26-v5all-ops2-c2`, holdout 0.990156) scored **0.98781, rank 15**. The top 3 were 0.990556, 0.989141 and 0.988842.

- **France implied:**

  | US/India assumption | France F0.5 |
  |---|---|
  | re-weighted holdout | 0.971 |
  | plain holdout | 0.974 |
  | the extra US test predictions all false positives | 0.976 |

  v2/v3 were about 0.93, so the France work since v3 is worth about +0.04 France F0.5 (+0.006 LB).
- **The holdout-to-leaderboard gap** is now −0.0024 (v3: −0.0092).
- **France's remaining headroom** (0.014–0.019 France F0.5 ≈ 0.0021–0.0028 LB) is about the whole gap to first place (0.00275). US/India give v6all about +0.0005.
- **So France is where the rest of the leaderboard is.**
  - Sachi's France kit (`france_kit.py`) is the tool: the rule populations over all candidates, plus the French stage-2 pairs with their edit profiles.
  - The open leads are France's number edits (NUM: 25% accepted in France vs 84–93% in US/India, measured on all candidates) and whatever the kit shows next.

