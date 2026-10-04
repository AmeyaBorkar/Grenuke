# Decisions: BLK (blocking, candidate generation, the candidate cut)

**Summary.**
- Sixteen decisions on how we find candidate pairs for each source-1 business (S1) among the source-2 and source-3 records (S2/S3). Blocking is the cheap first pass that proposes pairs; pair recall is the share of true pairs that survive it.
- We built a CPU search on rare-word overlap, per country, with a names-only view and repairs. Retrieval reached 99.1% pair recall at about 34 candidates per S1 (local holdout). We then cut the file the matcher scores to 3.70 per S1, with pair recall of about 98.2–98.4%, because the organisers ranked smaller candidate sets higher.
- Rejected options are kept: the planned dense GPU search, prefix keys, an exact-address view, a decision-boundary cut, alias-bridge retrieval and every tighter cut.

## Index

| ID | decision | when (IST) | status |
|---|---|---|---|
| D-BLK-01 | Retrieve by name and by address separately and take the union; name-only search only for empty or short addresses | 2026-09-25 12:04 | adopted |
| D-BLK-02 | Partition the search by the exact country label, never by state | 2026-09-25 14:15 | adopted |
| D-BLK-03 | Heuristic trim (top 15 per S1 or top 4 per record); no learned pre-ranker in v0 | 2026-09-25 14:15 | adopted; the pre-ranker part superseded by the stage-0 filter and D-BLK-10 |
| D-BLK-04 | Blocking uses its own tokenizer instead of waiting for the normalise stage | 2026-09-25 15:20 | adopted |
| D-BLK-05 | Engine: exact IDF-weighted token overlap on the CPU instead of TF-IDF → SVD → GPU top-k | 2026-09-25 15:53 | adopted (the planned GPU search was never built) |
| D-BLK-06 | First miss analysis: exact re-scoring, compound keys, ordinal stripping | 2026-09-25 16:02 | adopted |
| D-BLK-07 | Blocking v1: learned Indic dictionary in the name keys, character 4-grams in the name-only view | 2026-09-25 17:58 | adopted |
| D-BLK-08 | Blocking v2: name × address-word compound keys and one-token names in the name-only view; no prefix keys | 2026-09-25 21:25 | adopted |
| D-BLK-09 | The candidate file is the set the model scores (stage-2 input), not the raw blocking output | 2026-09-26 00:40 | superseded by D-BLK-10 |
| D-BLK-10 | Cut the candidate file to p1 ≥ 0.02 and each record's top-2 S1 (3.70 per S1) | 2026-09-26 05:10 | adopted; kept to the end |
| D-BLK-11 | Blocking v3 repairs (domains, OCR digits, ordinals); honorific stop words reverted | 2026-09-26 05:28 | adopted; honorific stop words reverted |
| D-BLK-12 | Exact-address blocking view for the v3 regression: not built | 2026-09-26 18:05 | rejected |
| D-BLK-13 | Cut the candidates to the decision boundary (Bakshi's proposal) | 2026-09-26 22:53 | rejected |
| D-BLK-14 | Keep the candidate cut unchanged after self-training | 2026-09-27 00:56 | adopted (no change) |
| D-BLK-15 | Close the alias-bridge recall route | 2026-09-27 09:59 | rejected |
| D-BLK-16 | Keep the candidate file at 3.70 per S1 against tighter cuts | 2026-09-27 12:45 | adopted |

## Records

### D-BLK-01 · Retrieve by name and by address separately and take the union; name-only search only for empty or short addresses
- **When (IST):** 2026-09-25 12:04 (data), 14:15 (FINAL_PLAN graft from Plan B), 16:14 (built) · **Phase:** P0–P1 · **Area:** BLK
- **Decided by:** Ameya (proposed by: Sachi, Plan B; the data check was by agent for Ameya at 12:04)
- **Status:** adopted; then widened by D-BLK-07 and D-BLK-08
- **Problem:** A blocker that needs name and address to agree misses records whose name or address is garbled. A name-only search over every record floods common names, because 46–54% of S1 names collide. Plan B's example: the name-only top-K for "Meridian" returns 523 near-identical scores.
- **Options considered:**
  1. A combined name-and-address retriever only.
  2. Plan A: a name view over all records, an address view and a combined view. (A view is one retrieval pass with its own keys.)
  3. Plan B: name-only retrieval only over S2/S3 records whose address is empty or has at most three tokens, about 5% of records.
- **Choice and why:** A union of name-driven and address-driven retrieval, with Plan B's restriction on the name-only view. A weak name is 15.75% of true pairs and a weak address 5.24%, but a pair is weak on both only 0.14% of the time. So a union "can recover almost everything. A combined-only retriever cannot" (Plan A §1.4). Only 0.27% of true pairs have a weak address with more than three tokens, so Plan A's name view over all records was rejected.
- **Evidence:** weak-name and weak-address shares [M] [chat:ameya/19e315ba 2026-09-25 12:04]; [FINAL_PLAN §1 #6, #7, §12](../../plans/FINAL_PLAN.md); [Plan B §2.4](../../plans/sachi/PLAN.md).
- **Outcome:**
  - The `name_short` view (bit 4 of the view mask) was built at 16:14. On India train, blocking v1 had 5.2M `name_short` pairs against 23.1M token-view pairs [M].
  - Character 4-grams were added at 18:02 (D-BLK-07), then one-token names of 8+ letters and compound keys (D-BLK-08), then domain, OCR and ordinal repairs (D-BLK-11).
  - Empty-address records with shared names stayed the largest miss class: 69% of the misses at v5all, at the Bayes limit, the error that no key or model can remove because the record does not say which S1 owns it (D-PRB-03).
- **Hindsight:** The methodology's names-only view (character 4-grams; single-token names of 8+ letters; for "empty or short addresses, garbled names, domains and handles") descends from this decision.
- **Links:** [Plan A](../../plans/ameya/PLAN.md) · [Plan B](../../plans/sachi/PLAN.md) · [DECISION](../../plans/DECISION.md) · D-ORG-03 · D-BLK-07 · D-BLK-08 · [theory: blocking](../theory/02-blocking.md)

### D-BLK-02 · Partition the search by the exact country label, never by state
- **When (IST):** 2026-09-25 14:15 · **Phase:** P0 · **Area:** BLK
- **Decided by:** Ameya; both candidate plans agreed
- **Status:** adopted
- **Problem:** The scope of each search, with France unseen. (The rule that country is an open set is D-PRB-01.)
- **Options considered:**
  1. Country partitions by the exact label.
  2. State partitions.
  3. No partitions.
- **Choice and why:** Option 1. There are 0 cross-country matches in 7.64M true pairs. States are missing, abbreviated, reordered or written in a regional script, so state partitions would silently drop true pairs (Plan B's argument). A record with an unseen or empty label is searched against every partition (Plan B's fallback); this is defensive only, because test has exactly US, India and France.
- **Evidence:** [M] [FINAL_PLAN §1 #1, #3, §4.3, §12](../../plans/FINAL_PLAN.md), [Plan B §2.3](../../plans/sachi/PLAN.md).
- **Outcome:** Every search and every IDF statistic is per country ([FEATURES v3](../../experiments/ameya/model-v1/FEATURES.md), [methodology §3](../../experiments/ameya/final-zip/doc/Documentation_template.md)). France ran as its own partition: 259,452 S1 against 1,434,993 records on test.
- **Hindsight:** The organisers' ranking e-mail later said that finer-grained blocking keys such as city and state scored higher. We use city and state as features, not as keys, and no test of keys on them is recorded.
- **Links:** D-PRB-01 · D-ORG-28 · [theory: blocking](../theory/02-blocking.md)

### D-BLK-03 · Heuristic trim (top 15 per S1 or top 4 per record); no learned pre-ranker in v0
- **When (IST):** 2026-09-25 14:15 (plan), 16:40 (measured), 17:06 (v0 packaged) · **Phase:** P0–P1 · **Area:** BLK
- **Decided by:** Ameya (the plan, against Plan A's own pre-ranker); agent for Ameya (the 15/4 setting, from a measured curve); recorded by Ameya as blocking v0 (proposed by: agent for Ameya)
- **Status:** adopted. The 15/4 trim is kept in the final token view. The learned pre-ranker was deferred, then superseded by the stage-0 filter and D-BLK-10.
- **Problem:** Retrieval returned too many pairs. The wide union (each S1's top 40 records plus each record's top 4 S1) held 49.8 candidates per S1. Plan A trimmed with a learned pre-ranker (a gradient-boosted model on retrieval metadata, to about 25 per S1, losing under 0.1% of union recall). Plan B cut it: it "adds a model, a training step and a failure point".
- **Options considered** (local-holdout pair recall at candidates per S1):
  1. Wide run, token view top 40 per S1 plus name_short: 0.9775 at 49.8.
  2. The plan's heuristic, top 30 per S1 plus top 2 per record: 0.9743 at 34.9.
  3. Trim 15/4 (top 15 per S1 or top 4 per record): 0.9752 at 29.0.
  4. Trim 10/4: 0.9745 at 26.
  5. A learned pre-ranker, only if pairs per S1 or feature time demand it (gate G11).
- **Choice and why:** Option 3. It beats the plan's 30/2 (0.9752 at 29.0 against 0.9743 at 34.9). "The record side matters most": at 15 per S1, raising the per-record limit from 0 to 4 lifts recall from 0.9365 to 0.9752. Pairs from other views (`name_short`) are always kept.
- **Evidence:** holdout pair recall 0.9752 (US 0.9860, India 0.9590) at 29.0 candidates per S1 (99th percentile 107) [M]. Oracle F0.5 0.9914 [M]; that is the best macro F0.5 (the competition's score: the F0.5 of each S1, averaged over S1) that a perfect matcher could reach using only these candidates. Train 64.0M pairs, test 56.8M [M]. [chat:ameya/19e315ba 2026-09-25 16:40].
- **Outcome:**
  - Gate G1 (recall ≥ 0.990) was not met at v0. The misses were mostly Indic names with short addresses, empty addresses and typos, which led to blocking v1 (D-BLK-07).
  - A learned filter came back anyway. Stage 0 and stage 1 are the first two gradient-boosted models in the cascade, and p0 and p1 are the probabilities they give a pair. Stage 0 (200 trees on 10% of training S1) skips pairs with p0 below 0.00345 (v2) or 0.00555 (v3) and keeps 99.95% of true pairs in 15.4% of the pairs. Stage-1 p1 later cut the file to 3.70 per S1 (D-BLK-10).
- **Hindsight:** The Plan A idea survived in a different place: a learned filter was needed after all, but as stage 0 rather than inside blocking.
- **Links:** [FINAL_PLAN §4.3](../../plans/FINAL_PLAN.md) · [DECISION](../../plans/DECISION.md) · [handover 2026-09-25_1706](../../docs/handover/2026-09-25_1706_ameya_block-v0-baseline.md) · [FEATURES v2](../../FEATURES.md), [v3](../../experiments/ameya/model-v1/FEATURES.md) · D-EVL-03 (gate G11)

### D-BLK-04 · Blocking uses its own tokenizer instead of waiting for the normalise stage
- **When (IST):** 2026-09-25 15:20 (proposed), 15:53 (built) · **Phase:** P1 · **Area:** BLK / NRM
- **Decided by:** agent for Ameya
- **Status:** adopted. It stayed: blocking never switched to Bakshi's normalise output.
- **Problem:** Blocking keys (task 1.3a, due 16:30) depended on the normalise stage (task 1.2, due 17:30), and Submission 1 needed candidates the same day.
- **Options considered:**
  1. Wait for normalise v0.
  2. Write simple keys from the raw records with a tokenizer of our own, and switch over later.
- **Choice and why:** Option 2, which "removes a dependency on the critical path". The tokenizer folds accents (NFKD); drops legal forms, honorifics and markers; canonicalises street types and ordinal words ("saint" → "st", "rue" → "r", "2nd" → "2"); strips leading zeros; uses one ISCII table for nine Indic scripts (D-NRM-02); and builds consonant-skeleton keys. It is a vectorised pyarrow implementation. Word-rarity statistics (IDF) are fitted per country on the exact label, which is treated as an open set. The context features that count S1 sharing a name key or a (number, street) key are log-counts, not rates.
- **Evidence:** [chat:ameya/19e315ba 2026-09-25 15:20], [15:53] · [handover 2026-09-25_1706](../../docs/handover/2026-09-25_1706_ameya_block-v0-baseline.md).
- **Outcome:** The features later reused this tokenizer, so legal forms were invisible to the features until 20:45 (the legal-form feature record, area FEA). Bakshi's normalise stage was not used by the models that shipped (D-ORG-04).
- **Hindsight:** Speed won, but the legal-form signal was lost by accident for a few hours. Fitting per country under an open country set is what later let France get its own vocabularies.
- **Links:** D-PRB-01 · D-NRM-02 · D-ORG-04 · [theory: string similarity](../theory/03-string-similarity.md)

### D-BLK-05 · Engine: exact IDF-weighted token overlap on the CPU instead of TF-IDF → SVD → GPU top-k
- **When (IST):** 2026-09-25 15:53–16:17 · **Phase:** P1 · **Area:** BLK
- **Decided by:** Ameya's blocking session (agent for Ameya); no explicit decision record was written, and the reason is not stated in the sources
- **Status:** adopted for v0 and kept to the end. The planned GPU views were "to join later" and never did. Gate G2 (dense against sparse recall) was never run.
- **Problem:** FINAL_PLAN specified Plan A's GPU search: TF-IDF (word-weighted counts) over characters or words, compressed to 256 dimensions by SVD (a matrix compression), then an exact half-precision (fp16) top-k search, which returns the k best matches, on the GPU in both directions, with a sparse exact search as the fallback. A fast, exact search whose recall we could measure was needed within about an hour, on 12.5M train and 11.7M test records.
- **Options considered:**
  1. Plan A: TF-IDF → SVD-256 → fp16 GPU tiled exact top-k, S1 → record and record → S1.
  2. An exact sparse token-overlap search on the CPU.
  3. faiss (no Windows GPU wheels; faiss-cpu as a fallback).
- **Choice and why:** Option 2. Score = sum of idf over the shared tokens, divided by the product of the two vector norms, i.e. the cosine of binary token vectors with √idf weights. Candidates are seeded by the query's rarer tokens (posting list at most 3,000 for records, 1,000 for S1), and the best 200–400 are re-scored exactly with every shared token (D-BLK-06). It runs per country partition, in parallel with numba (a compiler for fast Python loops), in int32 and float32 "for determinism". It is exact, was checked against brute force in unit tests, and needs no GPU. Defaults: each S1's top 40 records and each record's top 8 S1; a pair is kept if it is in the S1's top 15 or the record's top 4 (D-BLK-03). A names-only view on character 4-grams covers short or empty addresses (D-BLK-01).
- **Evidence:** fold-0 recall 0.9475 → 0.9702 after the exact re-scoring; full holdout 0.9752 [M]. Commit message "add token-overlap blocking v0 with a name-only short-address view" [commit b267773].
- **Outcome:**
  - With targeted keys, pair recall reached 0.9857 (v1), 0.9899 (v2) and 0.99135 (v3).
  - Train blocking took about 19 min (v0) and 13 min (v1); test about 15–17 min and 11 min. The slow parts are single-threaded Python tokenisation and file writes (D-ORG-08).
  - Two weaknesses surfaced. The seed-based search never seeds the true S1 when the record's only rare tokens are typos, and cosine normalisation favours short S1 addresses over the true S1's long one [ANALYSIS_v2](../../experiments/ameya/model-v1/ANALYSIS_v2.md).
- **Hindsight:** The methodology's "token view" is this engine, and no SVD view appears in it. The GPU's real use turned out to be cross-encoders (models that read both records of a pair together) on rented machines, not retrieval (D-ORG-15).
- **Links:** `ber/block/search.py` · [FINAL_PLAN §4.3](../../plans/FINAL_PLAN.md) · D-BLK-06 · D-ORG-08 · [theory: blocking](../theory/02-blocking.md)

### D-BLK-06 · First miss analysis: exact re-scoring, compound keys, ordinal stripping
- **When (IST):** 2026-09-25 16:02 · **Phase:** P1 · **Area:** BLK
- **Decided by:** agent for Ameya
- **Status:** adopted (in v0)
- **Problem:** Fold-0 recall was 0.9475 (India 0.917). The misses were 40.3% non-ASCII record names and 16.4% empty record addresses, plus "a scoring flaw where common informative tokens don't count": seeding used only rare tokens, and the final score ignored the common ones.
- **Options considered:**
  1. Raise k (more candidates per query). The reason this lost is not recorded.
  2. Fix the scoring and add compound keys.
- **Choice and why:** Option 2: re-score the top seeded candidates with all shared tokens; add compound int64 keys (number + word, number + name token, name pairs); strip ordinal endings that created fake street tokens.
- **Evidence:** recall 0.9475 → 0.9702 at about the same 32 candidates per S1 (India 0.9171 → 0.9482) [M] [chat:ameya/19e315ba 2026-09-25 16:02].
- **Outcome:** Adopted in v0, whose full-holdout recall was 0.9752 (D-BLK-03).
- **Hindsight:** unknown (none recorded).
- **Links:** D-BLK-05

### D-BLK-07 · Blocking v1: learned Indic dictionary in the name keys, character 4-grams in the name-only view
- **When (IST):** 2026-09-25 17:58–18:03 (coded), 18:15 (run), 18:31 (measured) · **Phase:** P1 · **Area:** BLK / NRM
- **Decided by:** agent for Ameya (recorded by Ameya in his handover)
- **Status:** adopted
- **Problem:** On the full holdout, blocking v0 missed 47,111 true pairs (2.48%): 66% in India; 41.7% with Indic record names; 23.7% empty addresses with typo'd names.
- **Options considered:**
  1. The GPU character 3-gram views (planned at 17:07).
  2. Targeted keys aimed at the measured miss types.
- **Choice and why:** Option 2, which is cheaper and goes straight at the misses. Indic legal forms are dropped by their skeletons, and the 693-entry Indic→Latin dictionary learned on train folds 5–19 (D-NRM-02) is applied to name tokens. Character 4-grams of the joined name become negative int64 keys, so they never collide with token keys; they are used only in the `name_short` view.
- **Evidence:** pair recall 0.9752 → 0.9857 (India 0.9590 → 0.9836, US 0.9860 → 0.9872; S2 0.9737 → 0.9877, S3 0.9766 → 0.9839); oracle F0.5 0.9914 → 0.9956; candidates per S1 29.0 → 29.5 [M] [handover model-v1](../../docs/handover/2026-09-25_1958_ameya_model-v1.md).
- **Outcome:** Used by model v2 (Submission 3). Gate G1 (recall ≥ 0.990) was still unmet.
- **Hindsight:** unknown (none recorded).
- **Links:** D-NRM-02 · D-BLK-01 · D-BLK-08

### D-BLK-08 · Blocking v2: name × address-word compound keys and one-token names in the name-only view; no prefix keys
- **When (IST):** 2026-09-25 21:25–21:42 · **Phase:** P1–P2 · **Area:** BLK
- **Decided by:** agent for Ameya, under Ameya's 20:29 brief; recorded by Ameya
- **Status:** adopted. Blocking v3 (D-BLK-11) adds repairs on top of it.
- **Problem:** Blocking v1 missed 27.1k holdout true pairs (counterfactual +0.00477 F0.5). 17.9k of them had an address, which put +0.0032 within reach: domains and handles 7,442; typo'd names on streets without numbers 6,037; brand names at a shared address 2,759; Indic 1,435. Rare-word seeding seeds only the typos in the first case, and domain or handle names only prefix-matched.
- **Options considered:**
  1. Keep v1.
  2. Compound keys of a name word and an address word (`nw_words=6`: one of the first two name tokens with one of the first six address words of 4+ letters that are not street types; they cover 37.9% of the shared-word misses and 96.7% of the Indic ones), plus one-token names of 8+ letters sent to the character 4-gram view (`ns_domain_len=8`, `ns_ngrams=4`).
  3. Prefix keys of the joined name (7 letters): they would cover 55.6% of the missed domains, but shared 7-letter prefixes are too common (median 885 S1 per key), "so they would not seed". Rejected.
  4. A (number, street) key: it reaches only 8% of brand-name misses, so it is not reliable. Nothing reliable was found for brand names (any key reaches 10.7%).
- **Choice and why:** Option 2: +0.42 points of recall for +2.5% pairs.
- **Evidence:** pair recall 0.9857 → 0.9899 (India 0.9836 → 0.9875, US 0.9872 → 0.9916); oracle F0.5 0.9956 → 0.9970; candidates per S1 29.5 → 30.3; train run 13 min [M] [gate record G1](../../docs/decisions/2026-09-25_2142_gate-g1-blocking-v2.md), [ANALYSIS_v2 §2, §4](../../experiments/ameya/model-v1/ANALYSIS_v2.md).
- **Outcome:** The gate record says recall is "at the G1 v0 bar (99.0%)". That is rounding: 0.9899 is 0.0001 short of 0.990. Used by v3 to v5all (v3 local-holdout F0.5 0.98882). The misses that remained were empty-address records with shared names (D-PRB-03) and brand names at a different house number.
- **Hindsight:** Sound. The remaining misses were mostly empty-address records, which no key can find.
- **Links:** [chat:ameya/19e315ba 2026-09-25 21:25], [21:41] · [commit 367ee4f] · D-BLK-11

### D-BLK-09 · The candidate file is the set the model scores (stage-2 input), not the raw blocking output
- **When (IST):** 2026-09-26 00:40–00:46 (decided), 02:07 (in the model v4 record) · **Phase:** P2 · **Area:** BLK / SUB
- **Decided by:** agent for Ameya (proposed by: the candidate-size agent a1f88e87). Ameya's critique at 00:05, that our lists were about five times bigger than "theirs", triggered it.
- **Status:** superseded by D-BLK-10 (05:32 the same morning)
- **Problem:** The uploaded `candidate_pairs.tsv` was the raw blocking output: 33.99 pairs per test S1, 781 MB. The README asks for "the exact set of records you feed into your matching model for inference … if your pipeline has several blocking/filtering stages, the last one".
- **Options considered:**
  1. Keep the blocking output: holdout pair recall 0.98992, oracle F0.5 0.99697.
  2. The stage-2 input set (p0 ≥ tau0 and p1 ≥ 0.002): 4.75 per test S1 (US 4.49, India 4.50, France 6.21), about 129 MB (one source says 128 MB), recall 0.98926, oracle 0.99676, and no v3 prediction outside it.
  3. On top of 2, each record's best 2 or 3 S1 by p1: 3.73 per S1 at recall 0.9825, or 3.82 at 0.9844.
  4. A cap per S1: it would have to be 10–15, because an S1 has up to 11 true records.
- **Choice and why:** Option 2. It is exactly what the stage-2 scorer (the second model stage, which scores each pair against its competitors) reads and the decision step (which picks each S1's final set) chooses from. It is the README's own definition, it needs no model change, and it is six times smaller. Option 3 only "if a size-based ranking is confirmed", which the agent could not verify. Option 4 does not work.
- **Evidence:** all [M] [chat:ameya/agent-a1f88e87 2026-09-26 00:40]; blocking output against stage-2 input in [ANALYSIS_v3 §6](../../experiments/ameya/model-v1/ANALYSIS_v3.md): 33.99 against 4.75 per S1, recall 0.98992 against 0.98926, oracle 0.99697 against 0.99676, local-holdout F0.5 unchanged at 0.98882.
- **Outcome:** The v3ce and v4 packages used it, as did v5 and v5all. At 05:10 Ameya relayed the organisers' rule that a smaller candidate set per S1 ranks higher, and at 05:32 it was cut to 3.70 (D-BLK-10).
- **Hindsight:** Switching early paid, because the organisers confirmed the size criterion five hours later. Reading the README precisely pre-empted their rule.
- **Links:** [chat:ameya/19e315ba 2026-09-26 00:41], [00:46], [02:02] · [decision model-v4](../../docs/decisions/2026-09-26_0207_model-v4-france-and-cross-encoder.md)

### D-BLK-10 · Cut the candidate file to p1 ≥ 0.02 and each record's top-2 S1 (3.70 per S1)
- **When (IST):** 2026-09-26 05:10 (organiser rule seen), 05:16 (found), 05:32 (decided) · **Phase:** P2 · **Area:** BLK / SUB
- **Decided by:** Ameya (proposed by: agent for Ameya, after the organiser update that Ameya pasted at 05:10)
- **Status:** adopted; kept to the end
- **Problem:** A new organiser rule: "the approach that generates a smaller candidate set per Source 1 entity will be ranked higher in the final evaluation beyond the public/private leaderboard". The file was 4.68 per S1 (France 5.56), while the predictions are 3.37 per S1.
- **Options considered** (v5all predictions restricted to the kept pairs; local holdout):

  | cut | holdout pairs per S1 | holdout F0.5 | test pairs per S1 |
  |---|---|---|---|
  | p1 ≥ 0.002 (the file then) | 4.593 | 0.99016 | 4.682 |
  | p1 ≥ 0.02 | 3.928 | 0.99016 | 4.050 |
  | p1 ≥ 0.05 | 3.633 | 0.99013 | 3.706 |
  | the record's top 2 S1 | 3.758 | 0.99016 | 3.990 |
  | **p1 ≥ 0.02 and the record's top 2 S1** | **3.592** | **0.99016** | **3.702** |
  | p1 ≥ 0.05 and the record's top 2 | 3.533 | 0.99014 | 3.607 |
  | the record's top 1 S1 | 3.606 | 0.99010 | 3.795 |
  | the S1's top 6 records | 4.157 | 0.98877 | 4.233 |

- **Choice and why:** p1 ≥ 0.02 and the record's top 2. "A per-S1 top k is the wrong shape: true sets reach 11 records. A per-record cut matches the argmax ownership" (each record is assigned to its highest-probability S1): a record's lower-ranked S1 is almost never predicted. A common helper (`candidate_mask`) makes the decision step own and predict only inside the file, so the file is exactly the model's inference input.
- **Evidence:**
  - Re-decided local-holdout F0.5 0.990156 against 0.990159: Δ −0.000003 [−0.000015, +0.000011], a tie [M].
  - 8.11M → 6.41M pairs (6,413,166, 3.70 per S1: US 3.66, India 3.61, France 4.09; 105 MB). Re-deciding inside the cut drops 726 predictions and adds 16; 81 of 1.85M holdout predictions fall outside it [M].
  - Test predictions lost per S1: US 0.0001, India 0.0001, France 0.0009 [M].
  - Given up, at v5all: pair recall of the set 0.98927 → 0.98198 and oracle F0.5 0.99676 → 0.99452 [M] [RESEARCH_v5 §3](../../experiments/ameya/model-v1/RESEARCH_v5.md). The 3.70 file's pair recall is about 98.2–98.4% (the range in the [finale README](../../finale/README.md)). The only value measured in the sources is 0.98198 at v5all, and the later models were not re-measured [U]. The 99.1% figure belongs to retrieval before the cut (D-BLK-11).
- **Outcome:** Kept in every later package: 3.70 candidates per S1, against 3.38 predicted matches and about 34 from blocking (v6all: 6,406,457 pairs; the final file: 6,410,308, see D-BLK-16). The cost is "headroom the current decision layer does not use".
- **Hindsight:** A free win for the size criterion. It also bounds later models: any decoder that wants a lower-ranked S1 must be measured with the cut.
- **Links:** [decision candidate-set-cut](../../docs/decisions/2026-09-26_0532_candidate-set-cut.md) · [status ameya @591b829](../../docs/status/ameya.md) · [chat:ameya/19e315ba 2026-09-26 05:11], [05:16], [05:32] · D-BLK-09 · D-BLK-16 · [theory: blocking](../theory/02-blocking.md)

### D-BLK-11 · Blocking v3 repairs (domains, OCR digits, ordinals); honorific stop words reverted
- **When (IST):** 2026-09-26 05:28 (proposal), 06:26 (dev pool), 11:22 (record), 11:49–14:29 (full scale, the v6all rebuild) · **Phase:** P2–P3 · **Area:** BLK / NRM
- **Decided by:** Ameya (proposed by: the preprocessing agent ace27900 for Ameya; implemented by the blocking fork a43953b5 in its own worktree; reviewed and pushed by the main session)
- **Status:** adopted. The honorific stop words were tried and reverted.
- **Problem:** Blocking missed 19,163 holdout true pairs. Three fixable kinds remained: domain or handle names (BLUEGRILL.COM, #physicaltherapy; 2,092 misses, 97.7% of them blocking misses, 99.9% accepted once they are candidates); OCR digits in names (capita1, c0rp; about 1,100 misses); and ordinal street words ("Twentieth Ave"; 477 blocking misses). Their lifts in the error analysis were 2.8–3.4 (domains), 1.0–2.0 (OCR) and up to 8.4 in India (ordinals).
- **Options considered:**
  1. Extra name tokens for S2/S3 records, originals kept. Domain and handle names are cut by dynamic programming into the country's S1 name words. OCR digits (0→o, 1→l/i, 5→s, 8→b, 6→g, 3→e, 4→a) are repaired only when the result is an S1 word.
  2. Ordinal street words turned into digits.
  3. Honorifics (sree, shree, shre, om, maa) as stop words. Reverted: they strip a short name's only distinctive word ("Om Services Private Limited" becomes "services"). On the dev pool this lost 95 true pairs and found 64.
  4. OCR'd French legal forms (5arl, 5as) repaired.
  5. The cheap variant, one-token names of 8+ letters to the names-only view, was already in v2 (D-BLK-08).
- **Choice and why:** Options 1, 2 and 4. Vocabularies are built per country from each pool's own S1 names (open set, no external data), and lexicons are hand-written only.
- **Evidence:**
  - Dev pool (110k S1, 2.6M records) forward recall 0.97240 → 0.97939: domains 0.868 → 0.937, OCR 0.906 → 0.952, ordinals 0.972 → 0.990; pairs per S1 18.04 → 18.02 [M].
  - Full scale: local-holdout retrieval recall 0.98992 → **0.99135**, misses 19,163 → 16,455 (−14%), train pairs 66.8M → 66.4M, test 58.9M → 58.4M (about 34 candidates per test S1) [M]. This 99.1% is the recall before the cut of D-BLK-10.
  - The v6all rebuild (blocking v3 together with the other v6all changes, such as the signed-number features): stage 1 0.9870 → 0.9878; local-holdout F0.5 0.990156 → 0.990788, +0.00063 [+0.00057, +0.00070] (US +0.00068, India +0.00056); recall 0.9713 → 0.9738; about 3.5 h. The blocking share of that gain is not separated [M] [RESEARCH_v5 §8.5](../../experiments/ameya/model-v1/RESEARCH_v5.md).
  - Segmentable domain misses: 2,092 [M] [chat:ameya/agent-ace27900 2026-09-26 05:28]; dev-pool numbers [chat:ameya/agent-a43953b5 2026-09-26 06:25].
- **Outcome:** Final candidate at 14:29; uploaded with stage 3, rules v3 and the acronym join: 0.988609 on the public leaderboard (LB) [M]. Merged in PR #28 and listed in the methodology's Table 1 as "Repairs". A side effect found later: 2,186 French v5all predictions were no longer candidates (953 acronyms and 520 brand or domain records at the address), about −0.0006 France F0.5 [E] (D-BLK-12). The agent's risk note, that the vocabulary would be noisier at full scale (22% of the words added among the blocking misses are not the S1's own), did not show: pairs fell.
- **Hindsight:** The agents had estimated +0.0003–0.0005 on the holdout; the rebuild's +0.00063 is consistent with that but includes other changes. The honorific reversal shows the risk of stop words: a short name's one distinctive word can be the only thing that identifies it.
- **Links:** [decision blocking-v3-repairs](../../docs/decisions/2026-09-26_1122_blocking-v3-repairs.md) · [decision model-v6all-final](../../docs/decisions/2026-09-26_1425_model-v6all-final.md) · [PR #28] · [chat:ameya/19e315ba 2026-09-26 06:26], [11:49] · D-NRM-05 · D-PRB-05 · [theory: blocking](../theory/02-blocking.md)

### D-BLK-12 · Exact-address blocking view for the v3 regression: not built
- **When (IST):** 2026-09-26 18:05 · **Phase:** P3 · **Area:** BLK
- **Decided by:** agent for Ameya
- **Status:** rejected (deadline)
- **Problem:** The French blocking-v3 regression: 2,186 French v5all predictions were no longer candidates (8.4 per 1000 S1), about −0.0006 France F0.5 [E].
- **Options considered:**
  1. Rebuild blocking with an exact-address view (about 3 h).
  2. Recover only the acronym part by a join on the existing candidates (a separate decision in area RUL).
- **Choice and why:** Option 2. On the labelled holdout, only 516 missed true pairs sit at the same address (0.94 per 1000 S1) [M], worth about +0.00007, so a rebuild was not worth it.
- **Evidence:** [M] [RESEARCH_v6 §4](../../experiments/ameya/model-v1/RESEARCH_v6.md), which also gives the +0.00007 local-holdout value of an exact-address view.
- **Outcome:** The acronym join became part of the pipeline: the final candidate file includes pairs found by matching acronyms [methodology §3](../../experiments/ameya/final-zip/doc/Documentation_template.md).
- **Hindsight:** unknown (none recorded).
- **Links:** D-BLK-11

### D-BLK-13 · Cut the candidates to the decision boundary (Bakshi's proposal)
- **When (IST):** 2026-09-26 22:53 · **Phase:** P3 · **Area:** BLK / PKG
- **Decided by:** agent for Ameya (it rejected Bakshi's proposal while reviewing his "What a decimal point is made of" note, which Ameya relayed). Ameya's own ruling is not recorded.
- **Status:** rejected
- **Problem:** Bakshi proposed cutting the candidates to the decision boundary because it is "free in F0.5": the local-holdout F0.5 does not change.
- **Options considered:**
  1. Keep c2, the cut of D-BLK-10 (p1 ≥ 0.02 and the record's top 2): a real pre-model filter, gated as a tie.
  2. Cut to the decision boundary.
- **Choice and why:** Option 1. A decision-boundary cut would make the candidates nearly equal to the matches, which "misrepresents the pipeline and could fail the package review". The README asks for the set the model scores, not the model's answers.
- **Evidence:** c2 gate: 0.990156 against 0.990159, Δ −0.000003 [−0.000015, +0.000011] [M]. The same review found Bakshi's break-even rule right and his per-pair arithmetic and "proof" overstated [chat:ameya/a2a1b62a 2026-09-26 22:53].
- **Outcome:** 3.70 per S1 in every later package; the methodology reports 6,410,308 pairs.
- **Hindsight:** unknown (none recorded).
- **Links:** D-BLK-10 · D-BLK-09 · D-BLK-16

### D-BLK-14 · Keep the candidate cut unchanged after self-training
- **When (IST):** 2026-09-27 00:56–01:02 · **Phase:** P3 · **Area:** BLK
- **Decided by:** agent for Ameya, while Ameya had asked to squeeze everything out of the remaining hours
- **Status:** adopted (no change)
- **Problem:** Pairs reach the decision only if stage 1 gave p1 ≥ 0.02 or the pair is among the record's top-2 S1. Stage 1 is the part biased against France. If the self-trained stage 2 now confidently matched French pairs that the cut had thrown away, "those are recoverable matches that no model change can reach".
- **Options considered:**
  1. Widen the cut for France: recovers any such pairs, at the cost of more candidates and runtime.
  2. Keep the cut.
- **Choice and why:** Option 2. Owned pairs with a stage-2 probability above 0.7 outside the cut: France 2 (0.01 per 1000 S1), US 3, India 42 on test; on train, US 9 (truth rate 0.778) and India 18 (truth rate 0.944). Nothing worth recovering.
- **Evidence:** counts above [M] [chat:ameya/19e315ba 2026-09-27 01:02]; recorded in [RESEARCH_v6 §6.12](../../experiments/ameya/model-v1/RESEARCH_v6.md).
- **Outcome:** It held. The recall sizing at 10:02 put the remaining misses in blocking (16,455 true pairs never retrieved) and in scoring (31,574 retrieved but not predicted), not in the cut (D-BLK-15).
- **Hindsight:** Same choice today. The methodology still keeps p1 ≥ 0.02 plus the two best S1 per record.
- **Links:** D-BLK-10 · D-BLK-15

### D-BLK-15 · Close the alias-bridge recall route
- **When (IST):** 2026-09-27 09:59 (plan), 10:00–10:18 (sizing), 10:52 (closed) · **Phase:** P4 · **Area:** BLK
- **Decided by:** Bakshi (his recovery audit), with Ameya's sizing (agent for Ameya)
- **Status:** rejected (a side bet, not the main lever)
- **Problem:** Bakshi argued that 0.991 was not proven impossible and that recall, not false matches, is most of the holdout loss. Leaders might be finding true matches outside our candidates. His idea: an S1's registered name may differ from a record's trading-name alias, while two copies of that alias resemble each other, so a securely matched record could retrieve a sibling that S1-to-record retrieval missed.
- **Options considered:**
  1. A bounded anchor-based candidate audit with fixed stop conditions (planned in his RECOVERY_0991 note).
  2. Stop.
- **Choice and why:** Stop.
  - On train truth, of 611,291 sampled true pairs, 908 (0.149%) are hard to reach from their S1 and only 21 (0.0034%) are bridgeable: about 30 pairs if extrapolated to France.
  - On the model's actual misses (v7sq, US/India holdout): 1,901,267 true pairs over 519,022 S1; 97.47% predicted; 48,029 missed = 16,455 never retrieved + 31,574 retrieved but not predicted. Of the never-retrieved, 16,107 have a correctly predicted sibling of the same S1 (an anchor), but only 1,272 have an anchor both closer than the S1 and with a token-set ratio of at least 85. That is a ceiling of about +0.0002 on US/India. The examples were domain duplicates, accents and OCR digits that blocking v3 already repairs.
  - So "the misses are decision-side, not retrieval-side".
- **Evidence:** [M, train truth] [issue #45]; [M/E] sizing on the holdout [chat:ameya/19e315ba 2026-09-27 10:53]. An exact-name alias rule test grew to 21.8 GB and was killed to avoid a second freeze of the laptop (D-ORG-19).
- **Outcome:** Bakshi's own alias-bridge audit "closes in agreement". Both audits put the remaining loss elsewhere.
- **Hindsight:** unknown (none recorded).
- **Links:** [PR #59] · [issue #45] · [chat:ameya/19e315ba 2026-09-27 10:53] · D-BLK-14 · D-BLK-11

### D-BLK-16 · Keep the candidate file at 3.70 per S1 against tighter cuts
- **When (IST):** 2026-09-27 12:45–12:48 (organisers' update relayed), 14:41 (decision) · **Phase:** P4 · **Area:** BLK
- **Decided by:** agent for Ameya (analysis by the candidate-set agent ad467765); Ameya relayed the organisers' update
- **Status:** adopted
- **Problem:** The organisers announced that `candidate_pairs.tsv` "is part of your final submission … The approach that generates a smaller candidate set per Source 1 entity will be ranked higher in the final evaluation beyond the public/private leaderboard". The code that produces it is reviewed.
- **Options considered** (test size per S1; local-holdout ΔF0.5; matches of the composite package mixc that would fall outside the cut; "e-6" means ×10⁻⁶ of macro F0.5):

  | cut | test pairs per S1 | holdout Δ (95% interval) | matches outside |
  |---|---|---|---|
  | the record's top 1 S1 | 3.589 | −106e-6 [−129, −83] | 3,131 |
  | p1 ≥ 0.05 | 3.608 | −41e-6 [−52, −30] | 1,258 |
  | p1 ≥ 0.1 | 3.547 | −105e-6 | 3,794 |
  | p1 ≥ 0.2 | 3.494 | −279e-6 | 10,562 |
  | p1 ≥ 0.05 and top 1 | 3.530 | −140e-6 | |
  | p1 ≥ 0.1 and top 1 | 3.491 | −198e-6 | |
  | stage-2 probability ≥ 2e-4 | 3.595 (−2.8%) | 0 | 0 |
  | keep 3.70 (p1 ≥ 0.02 and top 2) | 3.70 | 0 | 0 |

  The stage-2 cut needs a code change and a rebuild. Cuts on stage-3 ownership or probability are "predictions plus near misses", not a filtering stage.
- **Choice and why:** Keep 3.70: "exactly what stage 3 and the decision read, so it is honest with no changes, and it is already reproducible". A 2.8% cut is unlikely to change a ranking. It would cost about 40 minutes of laptop time plus re-validation at the busiest hour, and drop 4–5 French rule-added matches. Every tighter cut loses holdout F0.5.
- **Evidence:** [M] [chat:ameya/agent-ad467765 2026-09-27 14:41], [RESEARCH_v6 §6.18](../../experiments/ameya/model-v1/RESEARCH_v6.md). The file held 6,410,310 pairs for 1,732,544 test S1 on 27 Sep 14:41 [M]. The methodology and the package audit say 6,410,308, two pairs fewer, and no source explains the difference [U]. 6,410,308 is used elsewhere.
- **Outcome:** Unchanged. The final file has 6,410,308 pairs, 3.70 per S1 (US 3.66, India 3.61, France 4.09). The methodology quotes the two tighter cuts' losses (0.000106 and 0.000041). The agent also wrote a one-page note on how blocking avoids all-pairs comparison (BLOCKING_NOTE.md, not committed to the repo [U]). The decision was posted to the team on issue #45.
- **Hindsight:** Same choice. Retrieval recall is 99.1% before the cut and about 98.2–98.4% after it. Some earlier notes pair 99.1% with 3.70 per S1; that pairing is wrong (see D-ORG-28).
- **Links:** [issue #45] · [methodology §3](../../experiments/ameya/final-zip/doc/Documentation_template.md) · [package README](../../experiments/bakshi/final-package/PACKAGE_README.md) · D-BLK-10 · D-ORG-28
