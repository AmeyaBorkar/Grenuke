# Amazon ML Challenge 2026 — Final Approach v2 (Stress-Tested)

> Supersedes `amazon_ml_challenge_2026_FINAL.md`. Built from measurements on the actual training files.
> **Tags:** **[M]** = measured on your data · **[H]** = hypothesis, must be tested · **[F]** = fact from the problem statement.
> Measurements come from full-file scans where noted, otherwise from a random sample of 33,189 S1 entities (148,469 records, 115,280 matched pairs).

---

## 1. Evidence ledger — what we actually know

| # | Finding | Status | Source |
|---|---|---|---|
| 1 | S1 2.21M, S2 5.03M, S3 5.29M records; US ≈ 60%, India ≈ 40% | [M] | full files |
| 2 | Each S2/S3 record belongs to at most one S1 entity (0 violations in 7.64M) | [M] | full GT |
| 3 | Singletons 5.6%; mean 3.46 matches/entity; 2–5 matches is typical | [M] | full GT |
| 4 | ~26% of S2 and S3 records are orphans (match no S1) | [M] | full GT vs files |
| 5 | Matched pairs always share the country label | [M] | sample (100%) |
| 6 | 47% of S1 entities share their exact core name with another S1 entity | [M] | full S1 |
| 7 | 5.3% of S1 entities share an exact normalized address with another S1 entity (max 14 at one address) | [M] | full S1 |
| 8 | Same core name **and** same exact address: 4 entities out of 2.2M | [M] | full S1 |
| 9 | Same name + same street words, differing only in numbers: 0.016% of S1 | [M] | full S1 |
| 10 | Address numbers identical in only 69% of true matches (overlap 91%): 401↔403, 713↔71, 1604↔01604, 4343↔4343B | [M] | sample |
| 11 | Postcodes present in <1.2% of records | [M] | sample |
| 12 | ~28% of India S2/S3 names contain non-ASCII (Indic scripts + injected accents); ~7% of US names (accents) | [M] | sample |
| 13 | Noise types: domain names ~5%, DBA prefixes ~1%, OCR swaps ~3%, empty address 4.4%, junk words, duplicated tokens, reordering, `##`/`H.NO` prefixes, state abbreviations, state names in regional scripts | [M] | sample |
| 14 | Orphans with an exact S1 name match: 21%; of those, only 0.4% also share the address | [M] | sample |
| 15 | Naive key blocking (shared number + address word, OR shared name token) covers 97.3% of true pairs | [M] | sample — **upper bound**, ignores top-K truncation |
| 16 | A sibling S2/S3 record rescues ~31% of the 5% of records that look weak against S1 (~1.5% of records) | [M] | sample |
| 17 | No ID-ordering leakage (correlation −0.001) | [M] | sample |
| 18 | Small label noise: a few orphans look like true matches | [M] (qualitative) | sample |
| 19 | France follows the same noise templates as US/India | **[H]** | — |
| 20 | Test resembles train (singleton rate, orphan rate, pool density) | **[H]** | — |
| 21 | Blocking can exceed 99% recall at manageable K | **[H]** | — |
| 22 | Ownership softmax beats a simpler argmax + margin rule | **[H]** | — |
| 23 | Expected-F₀.₅ selection beats a tuned threshold | **[H]** | — |
| 24 | Transliteration materially helps Indic-script names | **[H]** | — |

---

## 2. Stress test — component by component

Each component ends with a **verdict: KEEP / MODIFY / CUT / GATED**.

### 2.1 Loading and scale

- **What could go wrong:** 10M records of text in pandas can exceed 8–16 GB RAM; runs crash or swap; iteration slows to a crawl.
- **Edge cases:** quotes inside names breaking parsing; embedded tabs (none found, NF=4 on every row [M]).
- **Unverified:** runtime of every downstream stage at full scale.
- **Validate:** time and memory each stage on a 100k-entity world, then extrapolate before the full run.
- **Simpler/robust:** process per country partition; use `pyarrow`-backed strings; train on a ~200k-entity world, infer on the full data.
- **Verdict: KEEP, with partitioning mandatory.**

### 2.2 Normalization and rule parsers

| Parser | What could go wrong / false results | Fix | Verdict |
|---|---|---|---|
| **Transliteration** (ICU Any-Latin or an Indic library) | Output is phonetic, not English: साउथ बिल्डर्स → "sauth bildarsa", not "south builders". Char-gram similarity may stay low → FN. | Compare on a **consonant skeleton** too (sth bldrs ≈ s th b ld rs). Map transliterated legal suffixes via the mined lexicon. Verify library license. | **MODIFY** — keep transliteration, add skeleton, measure lift on the Indic slice |
| Regional-script state names in addresses | Low information; transliteration noise | Map to state via the mined state lexicon, or simply drop non-Latin address tokens | **MODIFY** — simplest option first: drop |
| **Domain names** | Short tokens ("co", "in", "the") match anything → FP | Require tokens ≥3 chars; score = fraction of S1 core tokens contained in the domain stem | **KEEP** |
| **DBA parser** | Picking the wrong side (random prefix vs real name) → FN | Score both sides, keep the max | **KEEP** |
| **OCR fix** (5→s, 0→o, 1→l inside words) | Damages real digit names ("3M", "24/7 Fitness") → FN | Keep original **and** fixed variant; features take the max | **MODIFY** |
| **Number normalization** | Leading zeros, `##`, `H.NO`, letter suffixes | Strip prefixes/zeros; split 4343B → 4343 + b | **KEEP** |
| **State abbreviation map** (mined from matched pairs) | Mining noise (spurious pairs) | Keep only pairs with high co-occurrence counts; re-run the miner on test text for France | **KEEP** |
| Postcode 3-state feature | <1.2% presence [M] → almost no signal | Treat postcodes as ordinary numbers | **CUT** as a dedicated feature |

### 2.3 Country blocking

- **Validated:** 100% country agreement in matched pairs [M].
- **What could go wrong:** test country labels could differ in spelling or be empty for some rows (unverified).
- **Validate:** print the unique country labels in the test files before anything else.
- **Fallback:** a record with an unseen or empty label is searched against all blocks.
- **Verdict: KEEP.**

### 2.4 Candidate generation

This is the recall ceiling. Anything missed here is lost for good — and worse, a missed owner can turn into a false merge downstream (see 2.6).

| Risk | Detail | Fix |
|---|---|---|
| **Common-name explosion** | Name-only top-K for "Meridian" returns 523 near-identical scores; arbitrary truncation drops the true owner → FN | Never block on name alone. Use **combined name+address** text so the address breaks ties |
| **Shared-address explosion** | Up to 14 businesses at one address [M] | Address-only pass K must exceed the largest shared-address group; the name then decides downstream |
| **Partition by state fails** | State missing, abbreviated, reordered, or in regional script → true pair in different partitions → FN | Don't partition blocking by state. Partition by country only; if compute forces it, add a "no-state" bucket searched against everything |
| **Script-changed names** | Char-grams on Devanagari vs Latin share nothing | Address pass catches most (addresses stay mostly Latin); transliterated skeleton covers the rest |
| **Empty address (4.4%) + common name** | Genuinely unresolvable: 500 equally plausible owners | Accept the loss. The ownership softmax will spread probability and the decision layer will leave these out, which is the correct behavior under F₀.₅. **Measure how many there are and don't spend effort on them** |
| **97.3% is an upper bound** | It ignores top-K truncation; real recall will be lower for key passes | Char-gram passes should push it back up — **measure the real curve** |
| **Learned pruner** | Adds a model, a training step and a failure point | **CUT for now.** Use fixed per-pass K and a cap; add a pruner only if candidate volume is unmanageable |

**Passes kept:**
1. Combined name+address char 3-gram TF-IDF, top-K, **both directions**.
2. Address-only char 3-gram TF-IDF, top-K.
3. Name-only (transliterated + skeleton) top-K, **only for records with empty or very short addresses**.
4. Exact keys: normalized number + street word; domain stem; DBA inner name.

- **Validate:** recall and candidates/entity per pass and for the union on a 100k-entity world against the full record pool; report marginal recall of each pass. Drop any pass adding <0.1 pt recall.
- **Verdict: MODIFY** (no state partitioning, no name-only pass for full-address records, pruner cut).

### 2.5 Pair features

| Feature | What could go wrong | Evidence / validation | Verdict |
|---|---|---|---|
| **Soft number match** (equal / prefix-truncation / small difference / letter suffix) | Neighbouring businesses (401 vs 403) → FP | Same name + same street + different numbers is only 0.016% of S1 [M]; orphan traps with same name and strong address overlap 0.4% [M]. Low risk, and the competition features handle the rest | **KEEP** |
| Street/locality IDF-weighted overlap | Generic words ("road", "nagar") dominate if IDF is wrong | IDF computed per country on train+test | **KEEP** |
| City/state match | State map errors | Mined map + missing flags | **KEEP** |
| **Name rarity** (how many S1 share this core name) | None significant; tells the model when to trust the address | [M] 47% collisions justify it | **KEEP** |
| **Shared-address count** (how many S1 at this address) | None significant; tells the model when to trust the name | [M] 5.3% shared addresses justify it | **KEEP** |
| Name fuzzy scores on transliterated + skeleton + OCR-variant forms | Transliteration weakness | Measure lift on the Indic slice | **KEEP** |
| Domain containment, DBA max score | Short-token FP | Token length guard | **KEEP** |
| **Competition margins** (round-2, OOF): margin to the best competing S1 for this record, rank, mutual-best | Leakage if not OOF | Strict OOF | **KEEP** |
| Separate "sibling distinctive-token" module | Redundant: the record's other S1 candidates *are* its siblings, and the margin features already compare them | — | **CUT** (subsumed by competition margins) |
| Sibling support (best confidence of a same-candidate S2/S3 sibling record) | Needs record↔record scoring; chaining risk; ceiling ~1.5% of records [M] | Compute only among records sharing the same S1 candidate list | **GATED** — Day 3, only if the error gallery shows weak-direct records as a big error class |
| Source pair (S2 vs S3), has-non-Latin flag | None significant | — | **KEEP** |
| `country` as a feature | Breaks on France | [F] warning | **CUT** |

### 2.6 LightGBM + calibration

- **What could go wrong:**
  - Training world with the wrong distractor density → competition features and calibration shift at test time → systematic FP or FN.
  - Class imbalance → poorly calibrated probabilities for rare positives in crowded neighbourhoods.
- **Unverified:** that subsampled training transfers to full scale.
- **Fix:** sample *entities* for training, but generate their candidates **against the full record pool**, so density matches reality.
- **Validate:** reliability plots per country and per source pair; compare calibration on the 100k world vs a 300k world.
- **Simpler alternative:** none better — GBDT on engineered features is the right workhorse for short structured strings at this scale.
- **Verdict: KEEP.**

### 2.7 Ownership softmax with "none"

- **Validated premise:** at most one owner per record [M].
- **What could go wrong:** when blocking missed the true owner, the softmax pushes the record onto the best *wrong* S1 → confident FP. This is the single most dangerous failure in the pipeline.
- **Fix:** the "none" logit includes the absolute best score, not just relative ones; train "none" on real orphans (26% of records [M] — plenty of examples) **and** on records whose owner was deliberately removed from the candidate list.
- **Simpler alternative:** per record, keep only the top S1 if p > t and margin > m.
- **Validate:** ablation softmax vs margin rule; report FP rate specifically on records whose owner was missed by blocking.
- **Verdict: KEEP, but it must beat the margin rule in ablation; otherwise use the margin rule.**

### 2.8 Decision layer (expected-F₀.₅) and singleton model

- **What could go wrong:**
  - Assumes independent, calibrated probabilities. Records aren't independent (one wrong S1 can attract several records), and calibration errors propagate directly into over-inclusion.
  - With only 5.6% singletons [M], the gain over a well-tuned threshold may be smaller than I originally argued.
- **Simpler alternative:** one tuned threshold on ownership probability q, optionally plus "always include the top record if q > t₁".
- **Validate:** paired bootstrap of expected-F vs the best tuned threshold vs top-k rule on the same probabilities.
- **Singleton model:** only 5.6% of entities; the independence estimate from q is probably enough.
- **Verdict:** expected-F layer **KEEP, conditional on beating the tuned threshold** (it's cheap; if it ties, keep the simpler threshold). Singleton model **CUT** unless singleton false-merge rate is high in validation.

### 2.9 Cross-encoder

- **What could go wrong:** slow at 10M-record scale; weak on numbers; overconfident; GPU dependency.
- **Only defensible use:** ambiguous pairs where one side is in an Indic script, if transliteration + skeleton don't solve them.
- **Validate:** error gallery after v1 — is the Indic slice a top error class? If yes, run on that slice only and require a paired gain.
- **Verdict: GATED.**

### 2.10 France

- **Hypothesis:** same generator templates with French vocabulary. Unverified — no French records seen.
- **Specific risks:**
  - `12 bis` / `12 ter` numbers → treat like letter suffixes.
  - `St` = Saint, not Street; `Cedex`; arrondissements (`Paris 8e`).
  - Legal forms (SARL, SAS, EURL, SA) — mined from test text.
  - French addresses may actually contain postcodes — handled as ordinary numbers.
  - Calibration learned on US/India may be off for France → over- or under-inclusion.
- **Fixes:** refit IDF, legal-suffix and state/region miners on test text; number parser handles bis/ter.
- **Validate:**
  1. Leave-one-country-out (train US → test India and reverse): the drop tells you how fragile the pipeline is to a new country.
  2. Leaderboard probe: France predictions vs France-empty. If predictions don't beat empty, the France pipeline is broken — investigate before the final submission.
  3. Compare France's distribution of max-q per entity against US/India; a much lower distribution means weaker evidence and the decision layer will already be more conservative.
- **Verdict: KEEP the country-agnostic design; treat every France claim as [H] until the probe.**

### 2.11 Validation setup

- **What could go wrong:** validation density differs from test → the validation score lies.
- **Unverified:** test pool sizes and orphan rate (need the test files).
- **Fix:** cluster-level split; score validation entities against the full training record pool when test is similar in size; check test file sizes first.
- **Validate:** first leaderboard submission — the val–LB gap must be small and stable.
- **Verdict: KEEP.**

### 2.12 Thresholds and hyperparameters to tune (never guess)

| Knob | Tuned on |
|---|---|
| K per blocking pass | Recall-vs-candidates curve |
| Soft-number tolerance | Validation F₀.₅ + FP rate on crowded-address slice |
| Ownership softmax parameters | OOF likelihood |
| Decision threshold (if expected-F doesn't win) | Validation macro F₀.₅ |
| Cross-encoder band (if built) | Paired validation gain |
| Pseudo-label confidence for France (if used) | LOCO analogue |

Never tune any of these on the public leaderboard.

---

## 3. Revised final architecture

```
Test/Train TSVs
  │  per-country partitions, arrow strings
  ▼
[1] Normalize + parsers
    transliteration + consonant skeleton · domain stem · DBA both-sides
    OCR variants (kept alongside originals) · number normalization
    mined state-abbreviation + legal-suffix maps (re-mined on test for France)
  ▼
[2] Blocking (country partition, both directions)
    a) combined name+address char-3gram TF-IDF top-K
    b) address-only char-3gram TF-IDF top-K
    c) name-only (transliterated/skeleton) top-K — empty/short-address records only
    d) exact keys: number+street word · domain stem · DBA inner name
                                                  ──► candidate_pairs.tsv
  ▼
[3] Features
    address (soft numbers, IDF street overlap, city/state, char cosine, missing flags,
             shared-address count)
    name    (IDF overlap on transliterated/skeleton/OCR variants, fuzzy, domain, DBA,
             legal suffix, name rarity)
    source pair · non-Latin flag · round-2 OOF competition margins
  ▼
[4] LightGBM (OOF) → isotonic calibration
  ▼
[5] Ownership: softmax over each record's S1 candidates + "none"
    (must beat argmax+margin rule in ablation, else use the rule)
  ▼
[6] Decision: expected-F0.5 per entity on ownership probabilities
    (must beat a tuned threshold, else use the threshold)
                                                  ──► matching_results.tsv

GATED (only if the error gallery demands it):
  · sibling-support feature  · cross-encoder on Indic ambiguous pairs
```

**Removed after the stress test:** postcode feature, state partitioning in blocking, name-only blocking for records with an address, learned pruner, separate sibling-distinctive-token module, singleton model, LLM judge, full graph clustering, `country` feature.

---

## 4. Experiment order (each answers one question)

| # | Question | Decision rule |
|---|---|---|
| V0 | Test files: country labels, pool sizes, France share | Sets validation density; flags label surprises |
| V1 | Real blocking recall and candidates/entity per pass, 100k world | Keep passes adding ≥0.1 pt; pick K on the curve |
| V2 | Baseline: features + LightGBM + tuned threshold. **Submit.** | Records val–LB gap |
| V3 | Round-2 competition margins | Keep if paired gain |
| V4 | Ownership softmax vs argmax+margin rule | Keep the winner |
| V5 | Expected-F vs tuned threshold | Keep the winner; ties go to the simpler |
| V6 | Transliteration + skeleton lift on Indic slice | Keep if slice F₀.₅ improves |
| V7 | LOCO (US→India, India→US) | Prune features that collapse |
| V8 | Error gallery → decide gated items | Build a gated item only if its slice is a top error class |
| V9 | France probe on LB (predicted vs empty) | If predictions lose, investigate France pipeline |
| V10 | Ablation table for the documentation | Remove one component at a time |

---

## 5. What gives us the edge (and what's still unproven)

1. **Name × address joint reasoning with rarity-awareness** — [M]-backed: names collide 47%, addresses 5.3%, both together essentially never. The model knows which signal to trust per pair.
2. **Ownership competition with "none"** — premise [M]-validated; benefit [H] until V4.
3. **Rule parsers that undo the generator's noise** (transliteration, domain, DBA, OCR, number variants) — noise types [M]; lift [H] until V6.
4. **Per-entity decisions** — [H] until V5; if a tuned threshold ties, we use the threshold.

Nothing in this plan is foolproof. Every [H] above has a named experiment that can overturn it.
