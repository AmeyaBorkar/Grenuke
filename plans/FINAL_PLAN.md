# Final plan: Business Entity Resolution (Team Grenuke)

**Status: accepted, v1.0, Fri 25 Sep 2026, 14:15 IST.** The coordinator (Ameya) chose this plan from Plan A (`plans/ameya/PLAN.md`) and Plan B (`plans/sachi/PLAN.md`). Plan C was not submitted. The decision record, grafts and rejected ideas are in `plans/DECISION.md`.
**Changes after v1.0:** each change gets a record in `docs/decisions/`. Only the coordinator edits this file. The version history is at the end.

- **Deadline:** Sun 27 Sep 2026, 23:59 IST.
- **Leaderboard budget:** 5 uploads per day (15 in total).
- **Metric:** macro F0.5 per Source-1 (S1) entity, singletons included.
- **Tags used below:**
  - **[M]**: measured on the provided data;
  - **[F]**: a fact from the problem statement;
  - **[H]**: a hypothesis. Every hypothesis has a gate in §9 that can overturn it.

---

## 0. TL;DR

- **Pipeline.** Eight stages, each cached and vectorized:
  - records → normalize → block (multi-view retrieval + exact keys) → pair features;
  - stage-1 GBDT → stage-2 collective model with calibration;
  - ownership (who owns each S2/S3 record) → per-entity F0.5 decision → outputs.
- **Why this shape [M]:**
  - S1 names collide constantly: 46–54% share an exact name with another S1. Name and address together almost never collide.
  - Every S2/S3 record has at most one owner.
  - A false merge costs about 3 times a miss.
  - The main false-positive trap is the **look-alike**: the same street, a nudged house number, and a business-changing word ("Exports", "Holdings").
  - Test has **23% more S2/S3 records per S1** than train.
- **How we work.**
  - Friday is a **v0 baseline**. Each later step is an increment that has to pass its gate.
  - Every complex component must beat a simpler one on the shared holdout, using a paired bootstrap (§9). This rule comes from Plan B.
  - Every claim carries a tag.
- **First valid submission:** Fri 25 Sep before 23:30 IST.

---

## 1. Evidence ledger

| # | Fact | Tag | Consequence |
|---|---|---|---|
| 1 | Train: S1 2,206,821, S2 5,034,616, S3 5,285,603 (US 60%, India 40%). Test: S1 1,732,544, S2 4,887,273, S3 5,082,316 (India 47%, US 38%, **France 15%**). Test labels are exactly {US, India, France}. | [M] | Everything is vectorized or compiled, processed per country. `country` is an open set. |
| 2 | Each S2/S3 record matches **at most one** S1: 0 violations in 7,638,365 true pairs. | [M] | Competition between S1s for a record is a strong precision signal (ownership, §4.7). |
| 3 | No cross-country matches. | [M] | Block within a country label only. |
| 4 | Matches per S1: mean 3.46, max 11. Distribution: 0: 5.6%, 1: 5.4%, 2: 17%, 3: 24%, 4: 22%, 5: 14.6%, 6: 7.5%, 7+: 4%. | [M] | The job is mostly "find all 3–4". Getting the set size right matters more than singletons. |
| 5 | 26% of S2/S3 records match nothing (S2 26.6%, S3 25.3%). We call them orphans. | [M] | There are many hard negatives, and they have to be modelled. |
| 6 | Exact core-name collisions: 46% of US S1 and 54% of India S1 share a name with another S1. Exact normalized address collisions: about 5% (largest group 14). Both at once: 6 S1. | [M] | Never trust the name alone. Name-rarity and shared-address counts become features. |
| 7 | True pairs: weak name 15.9% (India 26.1%), weak address 4.7%, both weak 0.09%. The S2/S3 address is empty in 4.4% of pairs. Weak address with more than 3 tokens: only 0.27%. | [M] | Address-driven plus name+address retrieval recovers almost everything. Name-only retrieval is needed only for records with empty or short addresses. |
| 8 | House numbers in true pairs: first number equal 83% (US 88%, India 77%), number sets equal 73%, some overlap 95%. | [M] | Use number *relations* (truncation, suffix, leading zeros, nudges), not exact equality. |
| 9 | **Look-alike signature.** Orphans close to an S1 on name and street words: the first number is equal in only 12% (true pairs 85%), and 77% add a name word (true pairs 23%). The added words are business-changing: *group, holdings, industries, public, enterprises, exports, infratech, ventures, overseas*. In true pairs they are noise: *center, services, dba, shri/sri/smt, dr/mr, formerly, incorporated*. | [M] | Number-relation features and extra-token features (with learned per-token distractor rates) are core, not optional. |
| 10 | Postcodes are essentially absent: ≤0.5% of addresses in US, India **and France**. | [M] | No postcode field or feature. |
| 11 | Indic-script S2/S3 names appear in 18% of India true pairs (7% overall). Accents are injected in every country. | [M] | Transliteration plus name variants (§4.2). |
| 12 | Noise catalogue (Plan A §1.3): typos and OCR swaps, word shuffles, legal-form changes, domains and hashtags, initials, DBA forms, invented brand names at the true address, appended phones, reordered address parts, abbreviations, state as code/name/script, neighbouring cities, `<NULL>`, `#`/`N°`/bis/ter, wrong ordinals, India numbering (H.No/Plot/Door No), truncated numbers, fragments. | [M] | These drive the normalizer and features. |
| 13 | **Test shift:** 5.75 S2/S3 per S1 in test vs 4.68 in train (India 5.82, US 5.76, France 5.53). | [M] | Thresholds tuned on train may not transfer. We need test diagnostics (§4.7, gate G8). |
| 14 | The extra test records are **the same kinds as train's**, not records whose S1 owner is missing. In India, where train and test S1 pools are similar in size, how close records sit to their nearest S1 is unchanged: close on name and address 31.7% vs 31.8%; nothing close 43% vs 44%. Removing owners would give about 26% and 53%. | [M] (crude proxy) | So test has more matches and/or more look-alikes per S1. A "drop S1s" stress test models the wrong shift. It checks one failure mode only. |
| 15 | France follows the same generator as US and India: the same closeness profile (30.6% close on both), `R`/`AVE`/`IMP.`, `N°16`, bis/ter, region ↔ department swaps, generic names (Amis, Club, Union…). | [M] (qualitative) | Use country-agnostic features plus French lexicons (§6). |
| 16 | No ID-order leakage (correlation −0.001). A few orphans look like true matches (label noise). | [M] | Never use IDs or row order. Expect a small irreducible error. |

The measurements for #6–#10, #13 and #14 were made on 25 Sep; method and numbers are in `docs/handover/2026-09-25_1414_ameya_final-plan.md`. The rest comes from Plan A §1 and Plan B §1.

---

## 2. What the metric implies

Per entity, F = 1.25·c / (0.25·|T| + |P|), where c is the number of correct predictions, T the true set and P the predicted set. An empty prediction scores 1 on a singleton and 0 otherwise.

Break-even calibrated probabilities, assuming independence:

| situation | include the candidate if p > |
|---|---|
| only candidate (singleton vs 1 match) | 0.50 |
| 2nd candidate, the 1st is certain | 0.73 |
| 4th candidate, 3 are certain | 0.77 |

- **A false merge costs about 3 times a miss,** and the bar rises with set size. Calibration and high-confidence precision decide the score.
- **Recall still matters,** because the mean |T| is 3.46.
- **Decision rule candidates** (compared at gate G6):
  - a tuned global threshold (simple);
  - an exact expected-F0.5 per S1. Candidates are sorted by p. The expected F is computed for every prefix length with a Poisson-binomial dynamic program over "true inside" and "true outside". It costs almost nothing in numba.

---

## 3. Pipeline

```
stage          module              writes (docs/CONTRACTS.md)                                   contract
00 records     ber.records         work/records/{train,test}.parquet, work/records/truth.parquet  C3
01 normalize   ber.normalize       work/norm/<tag>/{split}.parquet                                C3
02 block       ber.block           work/candidates/<tag>/{split}.parquet + blocking report        C4
03 features    ber.features        work/features/<tag>/{split}.parquet                            C8
04 train       ber.model           models + OOF stage-1 scores work/scores/<tag>-s1/train.parquet C5
05 predict     ber.model           work/scores/<tag>/{split}.parquet (calibrated p)               C5
06 decide      ber.model           work/matches/<tag>/{split}.parquet                             C9
07 write       ber.outputs         output/matching_results.tsv, output/candidate_pairs.tsv        C6
08 evaluate    ber.eval            work/reports/<tag>.json (holdout, per country)                 C7
```

- One CLI: `python -m ber.pipeline --stage <stage|all> --split <train|test> --tag <tag> [--in <stage>=<tag>]`.
- Each stage reads the previous stage's artifact by tag, so any stage can be re-run, swapped or A/B-tested alone.
- Strings exist only up to stage 01. After that, records are int64 `eid`s and int32 token codes.

---

## 4. Stage design

### 4.1 Records (00): v0 is in the skeleton PR

`ber.io` readers go in, and out come `eid`, `source`, `country`, `name` and `address` per record, plus the truth pairs (train). The cache takes about 1 minute to build.

### 4.2 Normalization (01)

**v0 (Friday)**
- **Unicode:**
  - NFKC, then Indic→Latin, then NFKD with combining marks dropped, then lowercase. This removes real and injected accents.
  - Indic→Latin uses our own offset table (Plan A). The 9 Indic blocks share the ISCII-derived layout, so one table handles virama, vowel signs, anusvara and nukta, with schwa deletion.
  - `&`/`+` become "and". Junk symbols are stripped. Bracket contents are kept.
- **Names:**
  - `n_core`: tokens without legal forms, honorifics or junk.
  - `n_legal`: a canonical code (llc, inc, corp, ltd, pvt_ltd, llp, lp, pllc, pc, sa, sas, sasu, sarl, eurl, sci, snc, ei, …).
  - `n_concat`: the core with spaces removed.
  - Flags: domain, hashtag, phone, DBA (both parts kept), Indic, honorific, token count.
- **Addresses:**
  - Remove null tokens.
  - Canonicalize numbering markers: h.no, door no, plot, flat, site, sf, sy, no., n°, #, unit, apt, suite, pmb, po box.
  - Ordinals: 7nd→7, tenth→10.
  - Street types get one short form across US, India and France: st, ave/av, rd, dr, ln, blvd/bd, ct, pl, trl, marg, nagar, colony, sector, rue/r, ch, imp, allee, quai, rte, fg. "saint" becomes st on both sides.
  - States: US names ↔ codes, India states ↔ codes, **France department → region** (hand-written, documented).
  - Numbers: every digit run, with leading zeros stripped and letter suffixes split off ("8444b" → 8444 + b; bis/ter treated as suffixes). Composite ids are kept whole and in parts. Separate fields for the primary number and the unit.
  - `a_street` (street tokens) and `a_city` (the component before the state).
  - Flags: empty, **short (≤3 tokens)**, landmark (near/opp/behind/nr/près/face), PO box, null, fragment.
  - France: drop "Cedex"; keep arrondissements ("8e") as a number with a flag.
  - **No postcode field** (#10).
- **Performance:**
  - Regex over 24 processes: about 5 minutes for 23.7M records.
  - Tokens are encoded once into int32 vocabularies with IDF, per country, fitted on train and test together. This is unsupervised and adapts to France.

**v1 (Saturday, gate G12)**
- Learned Indic token dictionary from train pairs (Plan A). Each Indic token maps to the most similar Latin token in the paired S1 name. Accepted with ≥2 supporting pairs and ≥60% share, and **fitted without the holdout**.
- **Consonant skeleton** of names (Plan B), for proper nouns the dictionary can't cover.
- **OCR variant** of names (Plan B): 5→s, 0→o, 1→l inside words. It sits next to the original, and features take the maximum.
- Domain stem uses only tokens of 3+ characters (Plan B guard). Learned city aliases are fitted without the holdout.

### 4.3 Blocking (02): sets the recall ceiling

- **Partition** by the exact country label. A record with an unseen or empty label is searched against all partitions. That is defensive only: this test set has just three labels.
- **Views.** Each is a TF-IDF fitted per country on train+test.

  | view | text | why |
  |---|---|---|
  | V-both | name core + street/number/city, char 3-grams | the main retriever; the address breaks ties between common names (#6) |
  | V-addr | address char 3-grams + number/street word tokens | weak names: scripts, domains, invented brands (#7) |
  | V-name-short | name char 2–4-grams, **only over S2/S3 records with empty or ≤3-token addresses** (about 5% of records) | weak or empty addresses (#7). Replaces Plan A's name view over all records (Plan B's design) |
  | keys (exact, bucket-capped) | (primary number, first street word); domain stem; DBA inner name | cheap and targeted |

- **Search engine (gate G2).** TF-IDF, then SVD to 256 dimensions (fitted on a 2M sample), then L2-normalized. Then an exact GPU top-k over fp16 tiles, with running top-k buffers along **both** axes: S1→R top-K and R→S1 top-k in one pass (Plan A).
  - The CPU fallback is sparse exact top-k with the highest-frequency n-grams pruned.
  - Measure recall@K of SVD vs sparse on a 100k-entity sample before scaling up.
- **Trim.** The union carries metadata per view: score, rank in the S1 list, rank in the R list, and a view mask.
  - **v0 uses a heuristic trim:** keep the top N per S1 by best view score (N≈30), plus the top 2 per R.
  - A learned pre-ranker (Plan A) comes in only through gate G11: when pairs per S1 or feature time demand it, and only if it loses less than 0.1% of the union's recall.
- **K** is fixed in v0 (S1→R 40 per view, R→S1 8), then tuned on the recall-vs-pairs curve. A view or key stays only if it adds **at least 0.1 pt** of holdout pair recall (Plan B).
- **Acceptance gate G1:**
  - holdout pair recall **≥99.0% (v0)** and **≥99.5% (v1)**, overall and per country and source;
  - a recall report for hard cases (Indic, domain/hashtag, empty address, fragment, invented brand);
  - oracle F0.5, and candidates per S1 (mean and p99).
- **The trimmed set is exactly `candidate_pairs.tsv`:** what the matcher scores.

### 4.4 Pair features (03)

**Principles**
- No `country` feature.
- Frequency features are rates per split and country, so train and test agree.
- Computed with rapidfuzz `cdist`/`cpdist` and numba over token CSR arrays, stored as float32.
- Never a Python loop over pairs.
- Column names follow `<group>__<name>` (C8).

**v0 (about 40 features, Friday)**
- `name__*`:
  - ratio, token_sort, token_set, partial and Jaro-Winkler on `n_core`;
  - token Jaccard, containment both ways, IDF cosine;
  - first- and last-token match, token-count difference;
  - legal-form relation (equal, compatible, conflicting, missing);
  - `n_concat` vs domain/hashtag.
- `extra__*` (the look-alike detector, #9). Tokens in R not in S1, and in S1 not in R, after absorbing typos (edit distance ≤2 or JW ≥0.9). For each side: count, IDF sum and IDF max, plus a substitution flag.
- `num__*`:
  - the primary-number relation: equal, truncation, prefix, suffix, letter suffix, small nudge (|d| ≤10), or other;
  - absolute and relative difference, digit edit distance, same length;
  - number-set Jaccard and both differences, "every R number compatible", unit equality.
- `addr__*`:
  - street-token Jaccard and IDF overlap, street JW;
  - city equality and JW, state equality;
  - whole-address token_set and char TF-IDF cosine;
  - empty, short, landmark, PO box and null flags; component counts.
- `ctx__*`: how many S1 share `n_core` (rate), how many S1 share the (number, street) key (rate), and the name IDF sum.
- `ret__*` and `src__*`: per-view scores and ranks in both directions, view count, and whether R is S2 or S3.

**v1 (Saturday)**
- **Per-token distractor likelihood:** for each extra or missing token, target-encoded out-of-fold, holdout excluded. Plan A's idea; evidence in #9; gate G3.
- The maximum over name variants: original, OCR, skeleton, dictionary.
- DBA best part, acronym match, Indic dictionary coverage, city alias match.
- Embedding cosines from the SVD views.

### 4.5 Stage-1 model (04/05)

- **Model.** XGBoost 3.2 `hist`, with `device=cuda` where a GPU exists and CPU `hist` elsewhere. LightGBM is only a blend candidate (gate G10).
- **Training rows.** Candidates of S1 entities in **train folds 5–19** (C2).
  - v0 may train on a sample of those entities. Each sampled entity keeps all its candidates, and the candidates always come from the full record pool.
- **Out-of-fold scores.** Three groups: folds 5–9, 10–14 and 15–19 (`ber.eval.splits.oof_group`). Each group is scored by a model trained on the other two.
  - The holdout and test are scored by the model trained on all of folds 5–19.
  - Early stopping uses a fixed-seed slice.
- **v0 path:** p1, then isotonic calibration cross-fitted on the OOF scores (never on the holdout), then the decision (§4.7).

### 4.6 Stage-2 collective model (Saturday, gate G4)

- **Scope.** Built on OOF p1 over the **full** candidate graph: every S1 and every record, never a sampled "world". Otherwise the competition features see only a fraction of the real rivals.
- **Features:**
  - *Competition, per record:* the best and second-best p1 among its S1s, the margin to the best rival, this S1's rank for the record, the number of S1 with p1 > 0.5, and a mutual-best flag. Plans A and B.
  - *S1 context:* the record's rank among the S1's candidates; counts above 0.5, 0.8 and 0.95; Σp1, the expected cluster size; gaps between neighbouring ranks. Plan A.
  - *Source balance:* the number of confident S2 vs S3 matches. Plan A.
- **Owner-removed augmentation (Plan B).** Copies of training record groups with the true owner removed, labelled "no owner". This teaches the model what a missed owner looks like, the most dangerous failure (a confident wrong merge).
- **Cluster support (Sunday, gate G9).** The maximum over the S1's other candidates R′ of p1(S1, R′)·sim(R, R′). Plan A.
- **Calibration.** Isotonic on OOF p2, cross-fitted. Reliability plots per country and source (Plan B).

### 4.7 Ownership and decision (06)

- **Ownership.**
  - v0: keep each record only under its highest-p S1 (Plan A). This is the most likely assignment. It is not guaranteed to be expected-F-optimal.
  - Gate G5: a softmax over each record's S1 candidates plus "none" (Plan B) must beat it.
- **Decision.**
  - v0: one global threshold on p, tuned on the holdout.
  - Gate G6: the exact expected-F0.5 per S1 (§2), with one global shrink parameter, must beat the threshold in a paired bootstrap. **Ties go to the threshold** (Plan B's rule).
- **Test-shift check (gate G8).** Compare test with the holdout per country:
  - the histogram of predicted matches per S1;
  - the fraction of records assigned;
  - the distribution of max p per S1;
  - an EM estimate of the positive rate among candidates on test scores.

  Shift the threshold or shrink only when these agree, and confirm with at most one leaderboard probe (#13, #14).
- **Outputs** are written through `ber.io` and must get validator PASS.

### 4.8 Gated extras (Sunday, only with measured gain)

- Learned pre-ranker (Plan A, G11).
- Learned encoder view or feature: multilingual-e5-small, MIT (G10).
- Cross-encoder as a stage-2 feature, run on the uncertain band (0.1 < p < 0.9) or the Indic slice: bge-reranker-v2-m3, Apache-2.0, 568M parameters (G10).
- LightGBM blend (G10).
- France pseudo-label adaptation (G7/G8).
- **Rule:** at least +0.002 holdout F0.5 with a 95% CI above 0 (+0.003 for heavy components), no loss in the leave-one-country-out check or the France diagnostics, and the component fits the runtime budget.

---

## 5. Validation protocol

1. **Shared holdout** (C2): folds 0–4, 549,699 S1 (US 329,717; India 219,982).
   - Every number is reported there: overall, per country, singleton F0.5, micro precision and recall, and mean predicted per S1 (`ber.eval.report`).
   - Quick iterations may use fold 0 only (about 110k S1, noise about ±0.002). PR numbers use the full holdout.
2. **Training uses folds 5–19.** Every supervised statistic excludes the holdout: dictionaries, token encodings, city aliases, calibration.
3. **Blocking** always runs over the full train record pool. Stage-2 features always use the full candidate graph.
4. **Gates** use a paired bootstrap over S1 entities (`ber.eval.gates`, 1,000 resamples). Keep a component if Δ ≥ +0.002 and the 95% CI is above 0.
   - Every gate result becomes a record in `docs/decisions/` with the baseline tag, the candidate tag, Δ, the CI and the verdict.
5. **Robustness checks:**
   - *Leave one country out:* train on US, score India, and the reverse. Record the drop, and prune features that collapse (G13).
   - *Missed-owner check:* drop 20% of holdout S1 together with their pairs, recompute the stage-2 features, and measure false positives on the records that lost their owner. This is a failure-mode check, **not** a threshold driver (#14).
6. **Test diagnostics** per country (§4.7), plus 100 hand-checked French predictions.
7. **Leaderboard:**
   - a sanity check (a stable gap between validation and leaderboard);
   - one France-vs-empty probe (G7);
   - at most one threshold probe.
   - Never tune several knobs on the public leaderboard.
8. **Ablation table:** remove one component at a time, for the methodology document (Plan B, V10).

---

## 6. France (test only, 15% of S1)

- **Evidence:** the same generator as US and India (#15). There are no postcodes (#10). Generic names collide heavily, so rarity and number features carry the decision.
- **Handling:**
  - country-agnostic features only;
  - IDF and TF-IDF fitted on the test France records too;
  - French lexicons:
    - street types (rue/r, avenue/av, boulevard/bd, impasse/imp, chemin/ch, allée, quai, route/rte, faubourg/fg);
    - legal forms (SARL, SAS, SASU, EURL, SA, SCI, SNC, EI);
    - bis/ter, Cedex, arrondissements, and department → region.
- **Checks:**
  - the leave-one-country-out drop, as a fragility estimate;
  - France's max-p distribution and predicted matches per S1 compared with US and India;
  - 100 hand checks;
  - the France-vs-empty leaderboard probe. If the predictions don't beat an empty France, stop and investigate before the final submission.

---

## 7. Compute budget and hardware

| step | target time | notes |
|---|---|---|
| records cache | ~1 min | pyarrow |
| normalize 23.7M records | ~5 min | 24 processes |
| TF-IDF + SVD, 2 main views × 2 splits (+ small V-name-short) | ~20 min | fit on a 2M sample, chunked transform |
| GPU top-k, 2 main views × 2 splits | ~40 min | fp16 tiles, top-k buffers on the GPU |
| features: v0 about 35M pairs (train sample + holdout + test); v1 full graph about 120M | ~30 min / ~70 min | numba CSR, rapidfuzz, float32, chunked |
| XGBoost stage 1 (3 OOF + full) + stage 2 | ~20 min | QuantileDMatrix on GPU |
| decide + write + validate | ~3 min | numba DP |

- **End to end:** about 2 h, and iterations reuse cached stages.
- **GPU stages** run on Ameya's laptop (RTX 5070 Ti 12 GB, 24 cores, 31 GB). Everything else also runs on the CPU.
- **Teammates:**
  - develop on fold-0 subsets;
  - get shared candidate and feature artifacts from the team drive, with a `MANIFEST.txt` of sha256 hashes (CONTRIBUTING §7).
- **Rules:**
  - process per country;
  - use int32/float32;
  - chunk every stage;
  - guard entry points with `if __name__ == "__main__":` (Windows uses spawn);
  - no faiss-gpu (no Windows wheels), so use torch matmul top-k.

---

## 8. Milestones and submissions (IST)

| when | milestone | done when |
|---|---|---|
| **Fri 14:00–15:30** | **M0**: this plan, contracts and roadmap merged; pipeline skeleton merged; everyone set up | `pytest` green on every machine; `python -m ber.pipeline --stage records` works |
| **Fri 15:30–18:30** | **M1**: normalize v0; block v0 (keys by ~16:30 so others have real candidates, then V-both + V-addr); features v0 and model/decision plumbing on the key candidates | artifacts for fold 0 |
| **Fri 18:30–21:00** | **M2**: full train candidates and the G1 report; features v0 at scale; stage-1 XGBoost; holdout F0.5 with argmax + threshold | a holdout report JSON |
| **Fri 21:00–23:30** | **M3**: test run, outputs, validator | **Submission 1** (by 23:30), with a record and a tag |
| Sat 09:00–13:00 | **M4**: stage 2 + calibration + owner-removed augmentation (G4); DP vs threshold (G6); per-token distractor encoding (G3); V-name-short + K tuning (G1 v1); engine check (G2) | Submissions 2–3 |
| Sat 13:00–18:00 | **M5**: error-analysis gallery, features v1 (variants, Indic dictionary, DBA/acronym; G12), softmax vs argmax (G5), leave-one-country-out and missed-owner checks (G13) | Submission 4 |
| Sat 18:00–23:00 | **M6**: test diagnostics and prior estimate (G8), France checks and probe (G7), threshold choice | Submissions 5–6 |
| Sun 09:00–15:00 | **M7**: gated extras (G9–G11), final thresholds | Submissions 7–9 |
| Sun 15:00–17:00 | **M8**: choose the final candidate (holdout, diagnostics, leaderboard consistency); **code freeze at 17:00** | a decision record |
| Sun 17:00–22:00 | **M9**: clean re-run from raw TSV in a fresh environment; README commands and run times; `Documentation_template.md`; zip; validator on the zipped outputs | **final upload = the chosen model**, tag `final`, zip uploaded; buffer until 23:59 |

- The detailed tasks and owners are in `docs/ROADMAP.md`.
- Every upload gets a record in `submissions/records/` and a `sub/…` tag. Plan for about 10–11 uploads, and keep one slot per day in reserve.

---

## 9. Gates (a hypothesis, the experiment that tests it, the rule)

| gate | hypothesis [H] | experiment | keep if | area | when |
|---|---|---|---|---|---|
| G1 | Blocking reaches ≥99.0% (v0) / ≥99.5% (v1) pair recall at about 30 candidates per S1 | holdout recall per country, source and hard case; recall vs pairs per S1 | the target is met; each view adds ≥0.1 pt | block | Fri / Sat |
| G2 | SVD-256 dense search ≈ sparse exact recall@K | 100k-entity sample, the same K | loss ≤0.2 pt, else use sparse | block | Fri |
| G3 | Per-token distractor encoding helps | ablation | Δ ≥ +0.002, CI > 0 | features | Sat |
| G4 | The stage-2 collective model beats stage 1 alone | paired bootstrap | Δ ≥ +0.002, CI > 0 | model | Sat |
| G5 | Softmax with "none" beats per-record argmax | paired bootstrap | Δ ≥ +0.002, else argmax | model | Sat |
| G6 | Expected-F0.5 DP beats a tuned threshold | paired bootstrap | Δ > 0 with CI > 0; ties go to the threshold | model | Sat |
| G7 | France predictions beat an empty France | 1 leaderboard probe | yes, else investigate | captain + model | Sat |
| G8 | Test needs a threshold/shrink shift | test diagnostics + EM prior | consistent evidence, ≤1 probe | model | Sat |
| G9 | Cluster support helps weak direct evidence | ablation | Δ ≥ +0.002 | model | Sun |
| G10 | Encoder / cross-encoder / LightGBM blend adds value | ablation + runtime | Δ ≥ +0.003 and fits the budget | block / model | Sun |
| G11 | A learned pre-ranker is needed | pairs per S1, feature time, recall loss | needed and loses <0.1% recall | block | Sat / Sun |
| G12 | Transliteration + dictionary + skeleton lift the Indic slice | Indic-slice F0.5 | the slice improves with no global loss | normalize | Sat |
| G13 | Features transfer across countries | leave-one-country-out | the drop is recorded; features that collapse are pruned | model | Sat |

---

## 10. Team and ownership (proposed; confirmed in the PR review, mirrored in `docs/TEAM.md`)

| area | owner | backup |
|---|---|---|
| coordination, submissions captain, blocking (GPU runs), pipeline CLI, packaging | Ameya (@AmeyaBorkar) | Sachi |
| model, calibration, ownership and decision, gates and ablations, error analysis | Sachi (@ssdhoka06) | Ameya |
| normalization, lexicons (US/India/France, Indic), pair features | Member 3 (@trustdemons05) | Ameya |
| methodology document | each owner writes their section; the coordinator compiles it | — |

These owners match each plan's strengths: Plan A's GPU retrieval and Plan B's validation discipline. The Friday critical path is normalize → features, which is why one person owns both string-heavy stages and the contracts between them.

---

## 11. Risks and mitigations

| risk | mitigation |
|---|---|
| Test density differs (+23% records per S1) | test diagnostics + EM prior (G8), competition features, conservative until confirmed |
| Blocking misses the owner, so the record lands confidently on the wrong S1 | the recall gate per hard case, owner-removed augmentation, the missed-owner check |
| Common-name explosion (#6) | no name-only view over full addresses, rarity features, address tie-breaks in V-both |
| Look-alikes (#9) | number relations, extra-token features and encodings, competition |
| France unseen | country-agnostic features, test-fitted statistics, lexicons, leave-one-country-out, the probe |
| Friday overrun | v0 scope only; every milestone ends in a submission; extras are gated |
| One GPU machine | CPU fallbacks, cached stages, shared artifacts with manifests |
| Memory (16–32 GB machines) | per-country processing, compact dtypes, chunking, sampled training entities |
| Overfitting the public leaderboard | decisions come from the 550k-entity holdout; at most one probe per knob |
| Compliance | provided data only; MIT/Apache-2.0 models ≤8B; library licenses checked (no GPL, e.g. no unidecode) |

---

## 12. Deliberately not built (and why)

| idea | why not |
|---|---|
| Name-only retrieval over records with full addresses | 0.27% of true pairs need it (#7), and names collide 46–54% (#6) |
| Postcode feature | ≤0.5% of addresses have one, France included (#10) |
| State-partitioned blocking | states are often missing, abbreviated or in regional scripts |
| `country` as a feature | breaks on France [F] |
| Singleton-specific model | singletons are 5.6%; the decision layer handles them |
| LLM judge, full graph clustering | too slow at this scale; competition + cluster support cover the useful part |
| "Test ≈ train" assumption (Plan B #20) | disproved (#13) |
| Cutting the extra-token features as "covered by competition" (Plan B) | disproved: look-alikes often have no rival S1, so the evidence is inside the pair (#9) |
| Drop-S1 stress test as the threshold driver (Plan A §5.3) | the extra test records aren't missing their owners (#14); the test is kept as a failure-mode check only |

---

## 13. Compliance and reproducibility

- **Data:** only the provided data. No external lookups, APIs, geocoding or internet data.
  - Lexicons (street types, legal forms, states, regions, departments) are hand-written domain knowledge. They are documented in the methodology.
- **Models:**
  - XGBoost (Apache-2.0), LightGBM (MIT), our own SVD/isotonic models;
  - optionally multilingual-e5-small (MIT) and bge-reranker-v2-m3 (Apache-2.0). Both are ≤8B parameters.
  - Each PR that adds a model states its license.
- **No IDs or row order** are used as signals.
- **Reproducibility:**
  - one CLI (`python -m ber.pipeline --stage all`);
  - fixed seeds;
  - pinned `requirements.txt`;
  - the git commit and command are stored in every artifact and report;
  - the README gives exact commands and run times;
  - git history plus `CHANGELOG.md` plus submission records form the version history.

---

## 14. Where each part came from

| component | source |
|---|---|
| Noise catalogue, normalizer design, Indic offset table, learned dictionary, French lexicons | Plan A |
| Consonant skeleton, OCR variants, domain guard, DBA scored on both sides | Plan B |
| Multi-view GPU retrieval in both directions, per-view metadata, recall gate and hard-case report | Plan A |
| Name-only retrieval only for short addresses, the 0.1-pt rule per view, domain/DBA keys, no learned pruner in v0 | Plan B (+ data #7) |
| Pair features, extra-token model with per-token encodings | Plan A (+ data #9) |
| Name rarity and shared-address counts | Plans A and B |
| Stage-2 collective with S1 context and source balance | Plan A |
| Owner-removed augmentation, softmax with "none" as a gated alternative | Plan B |
| Expected-F0.5 DP | Plan A, under Plan B's "must beat the threshold" rule |
| Evidence tags, gates, paired bootstrap, reliability plots, ablation table | Plan B |
| Shared holdout, OOF groups, test diagnostics | repo contracts + Plan A |
| Shift handling by diagnostics and an EM prior (not a drop-S1 stress test) | data check of 25 Sep (#14) |

---

## Version history

| version | date (IST) | change |
|---|---|---|
| 1.0 | 2026-09-25 14:15 | Accepted: Plan A base + Plan B grafts + data checks of 25 Sep |
