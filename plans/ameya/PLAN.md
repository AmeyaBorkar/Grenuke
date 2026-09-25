# Amazon ML Challenge 2026: Business Entity Resolution Plan

**Plan A, by Ameya.** Proposal written 25 Sep 2026. It is one of three team plans; the team will pick one or merge the best parts (see `plans/README.md`).

Deadline: **Sun 27 Sep 2026, 23:59 IST**. There are at most 5 leaderboard uploads per day, 15 in total.
Metric: macro F0.5 per Source-1 entity, averaged over all entities including singletons.

All numbers in §1 were measured on the full dataset. Any plan can reuse them.

---

## 0. TL;DR

A seven-stage pipeline, cached stage by stage, designed around what the data showed:

1. **Normalization.** Strip accents and unify Unicode. Transliterate Indic scripts to Latin using our own table plus a dictionary learned from train. Extract legal forms, domain/hashtag names and phone numbers. Parse addresses into numbers, street, city and state.
2. **Multi-view blocking.** Run top-k retrieval separately on name, address and name+address, in both directions (S1→R and R→S1), within each country. Add exact-key buckets. A cheap pre-ranker then trims the union to about 25 candidates per S1. That trimmed set is `candidate_pairs.tsv`.
3. **Stage-1 matcher.** A GPU gradient-boosted model (XGBoost) on about 150 pair features. The key feature groups are house-number comparison and the "extra token" features that tell harmless noise words from words that mean a different business.
4. **Stage-2 collective model.** Adds competition between S1 records for the same R record (each R can match only one S1), each S1's context among its candidates, and how strongly its other confident matches support a candidate.
5. **Calibration and a per-entity expected-F0.5 decision.** Each S1 gets the subset that maximizes its expected score, rather than one global cutoff.
6. **France (test only).** Use country-agnostic features, unsupervised statistics fitted on the test data, and French lexicons. Leave-one-country-out validation stands in for measuring it.

---

## 1. What the data says (measured on 25 Sep)

### 1.1 Scale

| | S1 | S2 | S3 | Countries |
|---|---|---|---|---|
| train | 2,206,821 | 5,034,616 | 5,285,603 | US 60%, India 40% |
| test | 1,732,544 | 4,887,273 | 5,082,316 | India 47%, US 38%, **France 15%** |

There are 23.7M records in total. Every stage must be vectorized or compiled. A Python loop over pairs is not an option.

### 1.2 Cluster structure (from the train ground truth)

- **Matches per S1:** mean 3.46 (S2 1.67, S3 1.79), max 11.
  - Full distribution: 0: 5.6%, 1: 5.4%, 2: 17%, 3: 24%, 4: 22%, 5: 14.6%, 6: 7.5%, 7+: 4%.
  - This is mostly a "find all 3–4" problem, not "find the one".
- **Singletons are 5.6%**, the same in both countries.
- **Exclusivity holds 100%.** Every S2/S3 record matches at most one S1.
  - So each R record effectively has one owner. Competition between S1 candidates for the same R is a strong precision signal.
- **No cross-country matches** (0 of 7.64M pairs). Blocking stays strictly within a country label, treated as an open set.
- **About 26% of S2/S3 records match nothing.** Most are *sibling look-alikes* generated from a real S1:
  - the name gets a meaningful word added or swapped ("Viswam Nursing Home" → "... **Exports**", "IZ **Infratech**" → "IZ **Security**");
  - the house number is nudged on the same street (4104 → 4108, 13-38/7 → 13-38/18);
  - then the usual vendor noise is applied on top.
  - Some are unrelated records, and some share an address with a different business.

### 1.3 Noise catalogue (seen in US, India and France)

- **Names**
  - Typos and OCR-style swaps (l→1, o→0, s→5).
  - Injected accents ("Léarning", "Ámpercap").
  - Word shuffles ("Inc SZ Royal Coastal").
  - Legal-form variants, moves and spurious additions (L.L.C., "Pvt." ↔ "Private", added LP/Corp, SARL/SAS/EURL/SASU).
  - Brackets ("Office of [Sanitation]").
  - Honorifics (Sri, Shri, Smt, Dr, Mr, The).
  - Truncation ("Northern School of").
  - Duplicated words ("AND AND").
  - Phone numbers appended.
  - **Domain names** ("peridolahotel.com") and **hashtags** ("#OUTRESERVICES").
  - **Initials** ("UO").
  - **D.B.A. forms** ("Noviriza D.B.A. Union de Verbe").
  - **Invented brand names at the true address** ("Evobrix", "Dovasynxylo"), about 2.8% of positives.
  - **Indic-script names**: Devanagari, Tamil, Telugu, Kannada, Malayalam and Bengali. These are 23% of matched India S2 records and 13% of India S3 records.
- **Addresses**
  - Component reordering. S2 is uppercase and abbreviated (ST/AVE/DR/TRL/R./AVE/IMP.).
  - The state appears as a code, a full name, or a regional-script name.
  - Neighbouring cities are substituted (PLATTSBURGH ↔ Beekmantown). France swaps region and department (Hauts-de-France ↔ Nord).
  - `<NULL>`/`NULL` tokens, leading zeros ("0629"), `#`/`##`/`N°`/`NO.`, "96 TER"/"100ter".
  - Wrong ordinals ("7nd", "130rd"), ordinal words ("TWENTIETH ST", "Tenth Street").
  - Wrong expansion ("Dwight Saint").
  - PMB and PO Box additions.
  - India numbering variants: Plot No / Door No / H.No / D.No / Flat / Site / Sf / Sy No.
  - Truncated numbers ("Np. 504" → "Np. 04", "17/2" → "17/").
  - Fragments ("Shop-3, Mumbai, MH") and empty addresses (about 4.5% of positives).
- **S1 has quirks too**: reordered components and "Unit APARTMENT C".

### 1.4 Difficulty of true pairs (sample of 500k positives)

- **Weak name signal: 15.8%.** Token Jaccard < 0.2, or Indic script, or a domain/hashtag name.
- **Weak address signal: 5.2%.** Empty, or no shared number and fewer than 2 shared words.
- **Weak on both: 0.14%.** Retrieving by name *and* by address separately, then taking the union, can recover almost everything. A combined-only retriever cannot.

### 1.5 Train → test shift (important)

- **More R records per S1 in test: 5.75 vs 4.68 (+23%).**
- Exact-key overlap of R with S1 is lower in test (India 0.884 → 0.854).
- Both point to **more distractors in test**.
- Consequences:
  - Precision must hold up under heavier distractor load.
  - Decision thresholds are stress-tested (§5.3) and not only tuned on train out-of-fold (OOF) predictions.

---

## 2. What the metric implies

Per entity: F = 1.25·c / (0.25·|T| + |P|), where c is the number of correct predictions, T the true set and P the predicted set. An empty prediction scores 1 on a singleton and 0 otherwise.

Break-even calibrated probabilities, assuming independence:

| situation | include the candidate if p > |
|---|---|
| only candidate (singleton vs 1 match) | 0.50 |
| 2nd candidate, 1st is certain | 0.73 |
| 4th candidate, 3 are certain | 0.77 |

- **A false merge costs about 3 times a miss** at typical cluster sizes, and the bar rises with set size.
- **Calibration and high-confidence precision are the whole game.**
- **Recall still matters,** because mean |T| is 3.46.
- **Decision rule:** for each S1, take candidates sorted by p. Compute the exact expected F for every prefix length k = 0..K, using a Poisson-binomial dynamic program over "true inside the prediction" and "true outside it". Pick the best k. This is vectorized over 1.7M entities in numba and costs almost nothing.

---

## 3. Architecture

```
TSV ─► 00 ingest ───────► parquet, int32 ids, country partitions
    ─► 01 normalize ────► name_core / legal_form / flags, addr tokens / numbers / street / city / state
    │                       (multiprocess, 23.7M records, cached)
    ─► 02 lexicon+stats ─► IDF tables, name/address frequencies (as rates), learned Indic→Latin dictionaries,
    │                       city-alias and extra-token statistics (OOF where supervised)
    ─► 03 block ────────► per country, per view: TF-IDF char/word → dense (SVD) → GPU tiled exact top-k,
    │                       both directions + exact-key buckets → union with retrieval metadata
    ─► 04 pre-rank ─────► cheap GBDT on retrieval metadata → trim to about 25 per S1, keep ≥99.9% of union recall
    │                       ═► candidate_pairs.tsv  (= exactly what the matcher scores)
    ─► 05 features ─────► about 150 pair features (rapidfuzz cpdist, numba CSR token/number ops, embedding cosines)
    ─► 06 stage-1 GBDT ─► p1  (XGBoost on the GPU)
    ─► 07 collective ───► exclusivity competition, S1 context, cluster support (candidate-to-candidate similarity)
    ─► 08 stage-2 GBDT ─► p2 → isotonic calibration
    ─► 09 decide ───────► per-R best owner + per-S1 expected-F0.5 DP ═► matching_results.tsv
    ─► 10 check ────────► official validator, local metric, submission log
```

Every stage reads and writes Parquet or NumPy under `work/`, so it can be re-run on its own. Records are addressed by int32 row indices; strings exist only in stages 01–02.

---

## 4. Stage design

### 4.1 Ingest (done)

- `pyarrow.csv` with `quote_char=False`. Names contain `'` and `"`, and default quoting would corrupt rows.
- Row counts verified against line counts.
- Parquet cache in `data_cache/`, taking 30 s instead of minutes.

### 4.2 Normalization (the data-engineering core)

**Unicode**
- NFKC, then transliterate Indic scripts, then NFKD with combining marks dropped. This removes both real French accents and injected fake ones.
- Lowercase.
- `&`/`+` become "and". Junk symbols (`* # < > -- !`) are stripped. Bracket contents are kept.

**Indic → Latin (our own code, no dependency)**
- The nine Indic Unicode blocks share the same ISCII-derived layout: the same offset is the same sound. So one offset table covers Devanagari, Bengali, Gurmukhi, Gujarati, Oriya, Tamil, Telugu, Kannada and Malayalam.
- It handles virama, vowel signs, anusvara and nukta. It deletes schwa and collapses long vowels (aa→a, ee→i, oo→u).
- **Learned token dictionary from train pairs** maps each Indic token to the most similar Latin token in the paired S1 name (e.g. प्राइवेट → private, குளோபல் → global).
- Accepted if it has at least 2 supporting pairs and at least a 60% share.
- Test tokens use the dictionary first and the rule-based table as fallback.
- The same approach handles regional-script state names.

**Name fields**
- `name_core`: tokens without legal forms, honorifics or junk.
- `legal_form`: a canonical code (llc, inc, corp, co, ltd, pvt_ltd, llp, lp, pllc, pc, sa, sas, sasu, sarl, eurl, sci, snc, ei, …).
- `name_concat`: the core with spaces removed, for comparing against domains and hashtags.
- Flags: `is_domain`, `is_hashtag`, `has_phone`, `is_acronym`, `has_dba` (DBA parts are split and both kept), `was_indic`, `has_honorific`, `n_tokens`.

**Address fields**
- Remove null tokens.
- Canonicalize numbering markers: h.no / door no / d.no / plot no / flat / site / sf / sy / no. / n° / # / unit / apt / suite / pmb / po box.
- Ordinals: "7nd" → "7"; "tenth"/"twentieth" → "10"/"20".
- Street types map to one short form across US, India and France: street/st, avenue/ave/av, road/rd, drive/dr, lane/ln, boulevard/blvd/bd, court/ct, place/pl, trail/trl, marg, nagar, colony, sector, rue/r, chemin/ch, impasse/imp, allee, quai, route/rte, faubourg/fg. "saint" also becomes "st", which is harmless because it collapses the same way on both sides.
- States and regions: US names ↔ codes, India states ↔ codes (plus the learned script names), France department → region.
- **Numbers**:
  - All digit runs have leading zeros stripped and letter suffixes split off ("8444b" → 8444 + b).
  - Composite ids ("20-52/2", "5-9-58/1-15") are kept both as a string and as parts.
  - Separate fields for the primary number, unit number and postal code (US 5 digits, IN 6, FR 5).
- **Street tokens** are the remaining words minus city, state and markers. **City** is the component before the state (S1 format), and alias pairs are learned from train.
- Flags: `addr_empty`, `has_landmark` (near/opp/behind/beside/nr/près/face), `has_pobox`, `has_null`, `n_components`, `is_fragment`.

**Performance**
- Pure-Python regex over 24 processes: about 1–2M records/s, so a few minutes for 23.7M records.
- Tokens are encoded once into int32 vocabularies (CSR arrays with IDF weights) for fast pair features in numba.

### 4.3 Blocking and candidate generation (sets the recall ceiling)

- **Partitioning.** Exact country label, as an open set with any string allowed.
- **Views.** Each is a TF-IDF vectorizer fitted *per country on train+test records together*. That is unsupervised, uses only provided data, and adapts to France automatically.
  - **V-name**: char 2–4-grams of `name_core` and `name_concat`, catching typos, shuffles, domains and transliterations.
  - **V-addr**: word tokens of street/number/city plus char 3-grams of street. This finds invented brand names and script names.
  - **V-both**: name + address combined, the general retriever.
  - **V-keys** (exact buckets, capped in size): (primary number, first street word), `name_concat`, sorted `name_core`.
  - **V-learned** (day 2, only if recall gaps justify it): a fine-tuned multilingual encoder (e5-small, MIT), which also becomes a strong feature.
- **Search.**
  - Each TF-IDF view is projected to 256-d with a truncated SVD fitted on a 2M sample, then L2-normalized.
  - **Exact GPU top-k**: tiled fp16 matmul, about 4k S1 × 250k R per tile, with running top-k buffers along *both* axes. One pass yields S1→R top-K (K≈40) and R→S1 top-k (k≈8).
  - Cost is roughly 10 min per view per split on the RTX 5070 Ti. `faiss-cpu` IVF is the fallback.
- **Union and metadata.** Per pair, per view: score, rank within S1's list, rank within R's list, and the number of views that retrieved it.
- **Pre-ranker** (stage 04). A small GBDT on retrieval metadata plus 4 cheap similarities.
  - Keep the top ~25 per S1 plus the top ~3 per R, with a probability floor.
  - Target: lose less than 0.1% of the union's recall.
  - The result is the **final candidate set**: exactly what the matcher scores, and exactly what goes into `candidate_pairs.tsv`.
- **Acceptance gate.**
  - Pair recall of at least 99.5% on the train holdout, overall and per country and source.
  - Report recall by hard-case category (script, domain, invented brand, empty address, fragment).
  - Reduction ratio will be about 0.999998 whatever we do, so recall is what gets audited.

### 4.4 Pair features (about 150; country is *not* a feature)

**Name**
- Jaro-Winkler, Indel/Levenshtein ratio, token_sort, token_set, partial ratio and WRatio, on `name_core`, the full normalized name and `name_concat`, via rapidfuzz `cpdist` (multithreaded C++).
- Token Jaccard, Dice, containment in both directions, and IDF-weighted cosine.
- Char-gram TF-IDF cosine.
- First- and last-token match, token-count difference.
- Legal-form relation (equal / compatible / conflicting / missing).
- Acronym match.
- Domain or hashtag vs `name_concat` (exact or JW).
- DBA best-part similarity.
- Indic flag and dictionary coverage.

**Extra-token model (key against siblings)**
- Tokens in R not in S1 and tokens in S1 not in R, after absorbing typos with edit distance ≤ 2.
- Count, IDF sum and IDF max for each side.
- Plus **"distractor likelihood" of each extra or missing token**, target-encoded out-of-fold from train.
  - "Exports", "Trading", "Holdings", "Overseas", "International" signal a sibling business.
  - "Corp", "LLC", "Board", "Service" are harmless noise words.
- A substitution flag when a token is both missing and added.

**Address and number (key against neighbours)**
- Primary number: equal, absolute and relative difference, digit edit distance, same length, prefix/suffix/truncation relation.
- Number sets: intersection, the two differences, Jaccard, and "every R number is compatible with some S1 number" (allowing truncation).
- Unit and postal-code equality when both are present.
- Street-token Jaccard and street-name JW.
- City equality, alias match, JW.
- State equality.
- Whole-address token_set ratio and TF-IDF cosine.
- Empty, fragment, landmark, PO box and null flags. Component counts.

**Frequency and context (rates per split and country, so train and test agree)**
- How many S1 share this `name_core`, which catches chains and generic French names.
- How many S1 share the (number, street) key, which catches co-located businesses.
- Distinctiveness of the S1 name (IDF sum).

**Retrieval metadata and source**
- Per-view scores and ranks in both directions, and view count.
- Whether R is from S2 or S3, because the two vendors add noise differently.

**Embedding**
- Cosines per view (SVD now, learned encoder later).

### 4.5 Stage-1 model

- **XGBoost 3.2 on the GPU** (`device=cuda`, hist), trained on about 10–15M candidate pairs from train split A.
- Tuned with early stopping on a slice of B. LightGBM on the CPU is the second model if a blend helps.

### 4.6 Stage-2 collective model (trained on out-of-sample p1)

- **Exclusivity:** for R, the best and second-best p1 among its S1 candidates, this pair's margin, this S1's rank for R, and the number of S1s above 0.5.
- **S1 context:** rank of R among S1's candidates, count above 0.5/0.8/0.95, sum of p1 (expected cluster size), and gaps between neighbouring ranks.
- **Cluster support:** max over other candidates R′ of S1 of p1(S1,R′)·sim(R,R′).
  - Similarity uses address-string equality, number-set Jaccard, name Jaccard and embedding cosine.
  - It rescues invented brand names and script names that share an exact vendor-formatted address with a confident sibling match.
  - Computed as batched GPU matrix products over candidate lists.
- **Source balance:** count of confident S2 vs S3 matches.

### 4.7 Calibration and decision

- Isotonic calibration of p2 on held-out data.
- **Per-R best owner:** keep R only under its highest-p S1. With unlimited S1 capacity this is the exact exclusivity-optimal assignment.
- **Per-S1 expected-F0.5 DP** (§2).
- One global shrink parameter is tuned on validation and on the stress test (§5.3).

### 4.8 Optional (day 3, only if validation gain is at least +0.003)

- A cross-encoder (multilingual MiniLM or XLM-R base, MIT) on the uncertain band only (0.1 < p1 < 0.9), used as a stage-2 feature.
- A pseudo-label adaptation pass for France.

---

## 5. Validation protocol

1. **Disjoint S1 splits of train**, hashed by S1 id: A 40% (stage 1), B 35% (stage 2), C 25% (holdout, about 550k entities).
   - Blocking runs once over the full train pool, just as in test.
   - Every supervised statistic is computed without C: learned dictionaries, token target encodings, city aliases.
2. **Metric:** an exact re-implementation of macro F0.5 with singletons, checked against the README example (0.714).
3. **Distractor stress test:** in C, drop about 20% of S1 entities together with their candidate pairs. This matches the test ratio of R per S1. Recompute the collective features and re-score. Thresholds must hold up in both settings.
4. **France proxy (leave one country out):** train on US only and score India C, and the reverse. Features that don't transfer get fixed or dropped.
5. **Test diagnostics:** compare the predicted matches-per-S1 histogram and the fraction of R assigned between C and test, per country. Spot-check 100 French predictions by hand.
6. **Public leaderboard** is used as a sanity check and for France-only decisions, never to overfit.

---

## 6. France (in test only, 15% of S1)

- Same generator as US and India, confirmed on Lille records: legal forms move, R./AVE/IMP. abbreviations, N°/NO./TER numbering, region ↔ department, domain, hashtag and initials names, sibling distractors with neighbouring numbers.
- **Generic names collide heavily** (Amis, Club, Union, Amicale, Centre...). Name-frequency features and address numbers carry the decision.
- Handling:
  - French lexicons (street types, legal forms, bis/ter, department → region).
  - TF-IDF and IDF fitted on the test France records.
  - No country feature.
  - Leave-one-country-out validation.
  - One or two public-leaderboard probes (e.g. a France-specific threshold shift).

---

## 7. Performance budget (one laptop: 24 cores, 31 GB RAM, RTX 5070 Ti 12 GB)

| step | target time | memory approach |
|---|---|---|
| normalize 23.7M records | ~5 min | 24 processes, arrow strings |
| TF-IDF + SVD for 3 views × 2 splits | ~20 min | fit on 2M sample, chunked transform |
| GPU top-k for 3 views × 2 splits | ~60 min (background) | fp16 tiles, top-k buffers on GPU |
| features (~15M train + ~40M test pairs) | ~30 min | numba CSR, rapidfuzz cpdist, float32 |
| XGBoost-GPU stage 1 + stage 2 | ~20 min | QuantileDMatrix on GPU |
| decide + write + validate | ~3 min | numba DP |

The full end-to-end run from raw data is about 2.5 h. Iterations reuse cached stages.

---

## 8. Milestones and timeline (IST)

| when | milestone | deliverable |
|---|---|---|
| Fri 13:00–17:00 | **M0** repo skeleton, env, metric, validator wrapper; **M1** normalization v1 incl. Indic and French | cached normalized Parquet |
| Fri 17:00–21:00 | **M2** blocking v1 (3 views + keys), recall report, pre-ranker | candidate set with ≥99% recall |
| Fri 21:00–23:30 | **M3** features v1, stage-1 XGBoost, DP decision | **Submission 1** (uses Friday's quota) |
| Sat morning | **M4** stage-2 collective, calibration, stress test | Submissions 2–3 |
| Sat afternoon | **M5** blocking v2 (learned encoder if gaps remain), feature v2 from error analysis | Submission 4 |
| Sat evening | **M6** France checks, leave-one-country-out, France probes | Submissions 5–6 |
| Sun morning | **M7** optional cross-encoder / blend, final thresholds | Submissions 7–8 |
| Sun 17:00 | **Freeze.** Clean end-to-end re-run from raw TSV with pinned env | final outputs |
| Sun 17:00–22:00 | Package the zip and fill in `Documentation_template.md`; **the final upload is the chosen model** | zip + final submission, with a buffer before 23:59 |

Every submission gets its own record in `submissions/records/` with date, git commit, holdout F0.5 (normal and stress), public score and notes, plus a `sub/…` git tag. `submissions/README.md` describes the protocol.

---

## 9. Risks and mitigations

| risk | mitigation |
|---|---|
| Test has more distractors than train | stress-tested thresholds, competition features, a conservative shrink parameter |
| France unseen | country-agnostic features, test-fitted unsupervised statistics, leave-one-country-out, spot checks, leaderboard probes |
| Memory (31 GB) | per-country processing, int32/float32, chunked stages, sampled training rows |
| Time overrun | every milestone produces a working submission; optional parts are gated by measured gain |
| Blocking misses | multi-view union, per-category recall report, learned-encoder view as backup |
| Windows quirks | `if __name__ == "__main__"` for spawn, no faiss-gpu (torch k-NN instead), `pathlib` everywhere |
| Public-leaderboard overfit | decisions come from the 550k-entity holdout; the leaderboard is a sanity check |

---

## 10. Compliance and reproducibility

- **Only the provided data is used.** No external lookups, APIs, geocoding or internet data. Lexicons (street types, legal forms, state and region names) are hand-written domain knowledge, and they are documented.
- **Models**: XGBoost (Apache-2.0), LightGBM (MIT), our own SVD and GBDT models. Any pretrained transformer must be MIT or Apache-2.0 and ≤ 8B parameters, for example multilingual-e5-small (MIT) or bge-reranker-v2-m3 (Apache-2.0).
- No ID or row-order signals are used.
- **Reproducibility**: one CLI (`python -m ber.pipeline --stage all`), fixed seeds, pinned `requirements.txt`, and a README with exact commands and run times. Git history plus a submission log satisfies "maintain version history".

---

## 11. Code layout (inside the team repo)

The repo structure and collaboration rules are in the root `README.md` and `CONTRIBUTING.md`. The shared metric, holdout split and I/O helpers already exist in `ber.eval` and `ber.io`. If this plan is chosen, its stages would go here:

```
code/business_entity_resolution/src/ber/
├── io.py  paths.py                  # shared (exists)
├── eval/  metric.py splits.py       # shared (exists)
├── normalize/  text.py indic.py name.py address.py lexicons.py
├── block/      vectorize.py knn.py keys.py union.py prerank.py
├── features/   strings.py tokens.py stats.py graph.py
├── model/      train.py calibrate.py decide.py
└── pipeline.py                      # CLI: python -m ber.pipeline --stage ...
```

Stage inputs and outputs follow `docs/CONTRACTS.md`, so parts of different plans can be combined.

Work teammates can run in parallel:

1. **Lexicons.** India/US/France street types, legal forms, states/regions/departments, numbering markers.
2. **Error analysis.** Browse false positives and false negatives from the holdout, and spot-check France predictions.
3. **Documentation.** Draft `Documentation_template.md` sections 1–3 from this plan.
4. **Submission bookkeeping.** Uploads, the log and git tags.
