# Blocking and candidate generation

**Summary.** Blocking picks the few pairs worth comparing out of 1.7 × 10¹³ possible ones, and it fixes the recall ceiling of everything after it. This page defines the quality measures, surveys the standard methods (keys, sorted neighbourhood, canopies, q-grams, inverted-index retrieval, MinHash-LSH, embedding search, meta-blocking, learned filters) and explains our design: per-country IDF token retrieval in both directions plus a names-only view and repairs, then a learned cut to 3.70 candidates per S1. It ends with an honest comparison against city/state blocking keys.

Related pages: [entity resolution](01-entity-resolution.md), [string similarity](03-string-similarity.md), [boosting and the cascade](06-gradient-boosting-and-stacking.md), [scaling to billions](11-scaling-to-billions.md), [glossary](glossary.md).

---

## 1. Intuition

You cannot find a match you never compare, and you cannot afford to compare everything. Blocking is a cheap first pass that proposes candidates; the expensive matcher only scores those. Two numbers pull against each other:
- **recall**: the share of true pairs that survive blocking. A pair lost here is lost for good;
- **size**: how many pairs survive, per entity. It drives the cost of every later stage, and the organisers ranked finalists partly on it (fewer candidate pairs per record scored higher, [finale README][finale]).

Good blocking uses cheap evidence that true pairs almost always share and random pairs almost never do: a rare name token, a house number with its street, a character fragment that survives a typo.

## 2. Formal definition

Let M be the true pairs, C the candidate set, Ω the pairs one could compare, and N₁ the number of S1.

```
pair completeness  PC = |C ∩ M| / |M|        (pair recall)
reduction ratio    RR = 1 − |C| / |Ω|
pairs quality      PQ = |C ∩ M| / |C|        (precision of the candidate set)
candidates per S1     = |C| / N₁
oracle F0.5           = macro F0.5 of a perfect matcher that predicts exactly C ∩ T(a) for each S1
```

PC alone can mislead under a macro metric: losing the only copy of an S1 costs that S1 its whole score, while losing one of eleven costs little. The **oracle F0.5** measures the ceiling in the metric's own units ([`metric.py`][metric]).

**Our numbers** (test sizes counted from the test files; holdout = the fixed 25% of labelled US/India S1):

| stage | test pairs | per test S1 | holdout pair recall |
|---|---|---|---|
| all S1 × all S2/S3 | 1.73 × 10¹³ [E] | 9,969,589 | 1 |
| within country only | 6.72 × 10¹² [E] | about 3.9M | 1 (no cross-country pairs [M]) |
| **retrieval** (token view + names-only view, blocking v3) | 58.4M [M] | about 34 [E] | **0.99135** [M] |
| stage-0 filter | about 80% fewer [M] | | keeps 99.95% of true pairs [M] |
| **candidate file** (p1 ≥ 0.02 and the record's top 2 S1, plus acronym joins) | **6,410,308** [M] | **3.70** (US 3.66, India 3.61, France 4.09) [M] | **0.98198** at model v5all [M]; not re-measured on the final model [U] |
| final predictions | about 5.85M [E] | about 3.38 | recall 0.975 [M] |

Sources: [methodology §3][doc], [blocking v3 record][blk3], [candidate-cut record][cut], [FEATURES.md][feat].

- **RR** of the candidate file is 1 − 6.41 × 10⁶ / 6.72 × 10¹² ≈ 1 − 9.5 × 10⁻⁷ within country [E]. The country split alone removes 61% of pairs [E].
- **PQ** on the holdout is about 3.46 × 0.982 / 3.59 ≈ 0.95 [E]: about 19 of every 20 candidates are true pairs. The candidate file is 0.64 pairs per S2/S3 record [E].
- **Two recalls, never mix them.** 99.1% is the retrieval recall (about 34 pairs per S1). The 3.70-per-S1 file kept 98.2% when measured (model v5all, blocking v2), and the cut changed holdout F0.5 by only −0.000003 [−0.000015, +0.000011] [M] ([cut record][cut]). Our methodology's sentence "cuts them down to 3.70 per S1 while keeping 99.1%" ([§1][doc]) merges the two numbers; quote them separately.

## 3. Variants

1. **Standard blocking** (exact keys): records sharing a key value, such as Soundex(surname) + postcode, form a block; only pairs inside a block are compared. Several passes with different keys are unioned to recover recall. Cheap and parallel, but a garbled or missing key field loses the pair, and blocks on common values are huge: cost grows with Σ (block size)².
2. **Sorted neighbourhood** (Hernández and Stolfo 1995): sort by a key and compare records inside a sliding window of size w. Cost O(n log n + n·w). A typo in the first characters moves a record far away in the order, hence multiple passes.
3. **Canopy clustering** (McCallum, Nigam and Ungar 2000): a cheap distance (token TF-IDF via an inverted index) with a loose threshold T1 forms overlapping canopies, a tight T2 removes centres; compare only inside canopies.
4. **q-gram and suffix indexing**: index substrings, so a typo still shares most q-grams. One edit destroys at most q q-grams, the basis of count filtering (Gravano et al. 2001).
5. **Inverted-index retrieval** (TF-IDF, BM25): each entity is a query against an index of records, scored by shared rare tokens, keeping the top k. BM25 (Robertson and Zaragoza 2009) adds term-frequency saturation and length normalisation. **Set-similarity joins** with **prefix filtering** (Chaudhuri, Ganti and Kaushik 2006; Bayardo, Ma and Srikant 2007) index only each record's rarest tokens, because two sets above a similarity threshold must share at least one of them.
6. **MinHash-LSH** (Broder 1997; Indyk and Motwani 1998): the probability that two sets share a min-hash equals their Jaccard similarity s. With b bands of r hashes, P(candidate) = 1 − (1 − s^r)^b, an S-curve whose threshold is tuned with b and r. Sublinear, but approximate, and blind to IDF.
7. **Embedding kNN**: encode each record as a vector (TF-IDF + SVD, or a sentence encoder) and search nearest neighbours with approximate methods: HNSW graphs (Malkov and Yashunin 2020), inverted files with product quantisation in FAISS (Jégou, Douze and Schmid 2011; Johnson, Douze and Jégou 2019). Learned deep blockers are studied by Thirumuruganathan et al. (2021).
8. **Meta-blocking** (Papadakis et al. 2014): treat co-occurrence in blocks as a weighted graph and prune weak edges. **Supervised meta-blocking** learns the pruning from labelled pairs.
9. **Learned blocking schemes and pre-rankers**: learn which keys to use (Michelson and Knoblock 2006; Bilenko, Kamath and Mooney 2006), or score retrieved pairs with a cheap classifier and keep the best. Our stage-0/stage-1 cut is this.

**Multi-view blocking** unions views with different failure modes. The union's recall is at least that of its best view, and its cost is the sum. Plan B's rule (Sachi) was that a view stays only if it adds at least 0.1 point of holdout pair recall ([FINAL_PLAN §4.3][plan]).

## 4. Where we used it

Ameya built and ran blocking v0–v3 ([`ber/block`][blockpkg]); the multi-view, two-direction design comes from Plan A (Ameya), the names-only view for short addresses from Plan B (Sachi) ([FINAL_PLAN §14][plan]).

**Partition.** Records are split by the exact country label, and records with an empty label join every partition, so country stays an open set. Each partition gets its own vocabulary and IDF, fitted on its own S1, S2 and S3 records; France therefore has French statistics without any labels.

**Keys per record** ([`index.py`][index], [`text.py`][text]): name tokens, the joined name, address words, address numbers and consonant skeletons, each in its own namespace, plus **compound keys** that stay rare where single tokens are common:
- (one of the first 2 numbers) × (one of the first 3 address words): a house-number-plus-street key;
- (one of the first 2 numbers) × (one of the first 3 name tokens);
- unordered pairs among the first 4 name tokens;
- (one of the first 2 name tokens) × (one of the first 6 address words of 4+ letters that are not street types), added in v2 so that "Dynamic Nnsaq P.C. | DURHAM DR, ANDOVER" still meets its S1 through dynamic × andover ([v2 record][blk2]).

**Score** ([`search.py`][search]): with IDF w_t = max(log(N/df_t), 0.01),

```
score(q, d) = Σ_{t in q ∩ d} w_t / ( sqrt(Σ_{t in q} w_t) · sqrt(Σ_{t in d} w_t) )
```

This is the cosine of binary token vectors with √IDF entries, and it is symmetric, so both search directions use the same scale. Candidates are **seeded** by the query's rarer tokens only (posting lists of at most 3,000 records for S1 → record, 1,000 for record → S1); the best 400 (or 200) seeds are re-scored exactly with every shared token. It is prefix filtering with a cap instead of a threshold: exact for anything that shares a rare token, blind to pairs that share only common ones.

**Views and trims.**
- **Token view:** each S1's top 40 records and each record's top 8 S1. A pair is kept if it is in the S1's top 15 **or** the record's top 4. The trims came from the recall-versus-size curve: on v0 the untrimmed 40/4 run had recall 0.9775 at 49.8 per S1, against 0.9752 at 29.0 for 15/4 [M] ([v0 handover][b0]).
- **Names-only view:** character 4-grams of names, top 10 each way with trims 5/5, over records whose address has at most 3 tokens (about 5% of records) or whose name is one token of 8+ letters (domains and handles).
- **Repairs** ([`repair.py`][repair], [`indic.py`][indic]): domain and handle names segmented into the country's S1 words by dynamic programming; OCR digits repaired only when the result is an S1 word; a 693-entry Indic-to-Latin dictionary learned on training folds; ordinal words to digits; French departments to their region ([03](03-string-similarity.md)).

| version (holdout) | pair recall | candidates per S1 | oracle F0.5 | what changed |
|---|---|---|---|---|
| v0 | 0.9752 | 29.0 | 0.9914 | token view, names-only view, transliteration, skeletons |
| v1 | 0.9857 | 29.5 | 0.9956 | Indic dictionary; character 4-grams in the names-only view (India 0.959 → 0.984) |
| v2 | 0.9899 | 30.3 | 0.9970 | name × address-word keys, one-token names in the n-gram view |
| v3 | 0.99135 | about 0.6% fewer pairs | | domain segmentation, OCR repair, ordinals |

All [M]: [v0 handover][b0], [model-v1 handover][m1], [v2 record][blk2], [v3 record][blk3]. Train blocking took about 13 minutes on Ameya's laptop at v2 [M].

**The learned cut** ([cut record][cut]). XGBoost stage 0 (200 trees, trained on 10% of training S1) removes about 80% of retrieved pairs and keeps 99.95% of true ones; stage 1 gives p1. The candidate file keeps pairs with **p1 ≥ 0.02 among the record's top 2 S1 by p1**, plus acronym-join pairs. A per-record cut matches the ownership constraint (each record has at most one owner, so a record's third-best S1 is almost never right); a per-S1 top-k is the wrong shape, because true sets reach 11 records. On the final model, tighter cuts lost F0.5: top 1 S1 per record −0.000106, p1 ≥ 0.05 −0.000041 [M] ([RESEARCH_v6 §6.18][r6]).

## 5. Why it fits this problem

- **No cross-country pairs** [M], so partitioning by country costs no recall and gives France its own IDF.
- **Rare tokens are the evidence.** IDF is the Fellegi–Sunter agreement weight ([01](01-entity-resolution.md)). Half of all S1 share their name, so the address tokens and the number × street compounds break ties.
- **Two directions** because S1 lists get crowded: common names attract many look-alikes, and test has 23% more records per S1 than train [M]. A record finds its own S1 from its side even when that S1's list is full; on v0 the record side mattered most (trim 10/4 still reached 0.9745 at 26 per S1) [M]. Tightening the S1-side cap from 15 to 10 on the holdout, harsher than test's crowding, cost only −0.00009 F0.5 [M] ([RESEARCH_v6 §2.6][r6]).
- **The names-only view** covers what the address cannot: 4.4% of true pairs have an empty S2/S3 address [M] ([FINAL_PLAN §1, #7][plan]). It is restricted to short-address records because names collide too often to retrieve on names everywhere.
- **The cut follows the metric**: holdout F0.5 did not move while the file shrank 21% (4.68 → 3.70 per test S1) [M].

### 5.1 City and state keys: an honest comparison

The organisers rewarded finer-grained keys such as city or state. Hard keys are cheap, parallel and easy to explain. Here is what we know, and what we did not measure.

**We do use fine keys, softly.** City names are address words in the index, and the name × address-word compounds act as (name, city) keys. The (house number, street word) compound is **finer than any city key**: it pins down a building. The difference is that a key adds IDF weight to a ranking instead of defining a hard partition, so one garbled or missing field lowers a score instead of losing the pair.

**Where a hard city or state key loses recall** (measured populations):
- 4.4% of true pairs have an empty S2/S3 address, so they carry no city at all [M];
- US S2 replaces the city with a county, neighbourhood or nearby town in 1.4% of copies (257 aliases, e.g. Boston → Dorchester) [M] ([RESEARCH_v5 §5][r5]);
- states are spelled out in 89% of US S3, abbreviated in 57% of India S3, and written in native script in 13–24% of India S2 [M] ([RESEARCH_v5 §5][r5]); India also uses landmark addresses ("Near SBI ATM");
- in France S1 names the region and a third of S2/S3 the department [M] ([`text.py`][text]); there are no postcodes in any country (at most 0.5% of addresses) [M].

On empty addresses alone, a hard (country, city) key without a fallback caps pair recall near 95.6%, against our 99.1% retrieval [E]. With a fallback, the fallback is our names-only view anyway. Day-1 planning rejected state-partitioned blocking for these reasons ([FINAL_PLAN §12][plan]).

**What a city key would not fix.** Blocks on big cities are large and skewed, so the matcher would still need a ranking inside each block, and the count of pairs per S1 would depend on city size rather than on the evidence.

**What we did not do.** We never measured a pure city/state-key variant, so we cannot quote its recall. An exact-address view, which we did estimate, would have recovered 516 missed holdout pairs (+0.00007 F0.5) [M], and we expect most of the French acronym and brand-name records lost in v3 [E] ([RESEARCH_v6 §4][r6]).

**How to argue it.** "We chose every key by measured recall. A hard key's recall is capped by how often its field is present and canonical; empty addresses alone are 4.4% of true pairs. We kept the precision of fine keys, including house number with street, without that cap, by using them as weights in a ranked search, and a learned filter then took us to 3.70 candidates per S1, within 7% of the 3.46 true copies per S1."

## 6. Pitfalls

- **Quoting the wrong recall** (retrieval 99.1% against the cut file's 98.2%).
- **A shrunken pool.** Evaluate blocking against the full record pool, as on test; fewer distractors make blocking look better ([CONTRACTS C2][contracts]).
- **IDF fitted on train only** would mis-weight a new country; fit it per country on all records, which uses no labels.
- **Seeding misses pairs that share only common tokens.** Generic French names are the risk; a label-free check found 100% of French same-name, same-number-and-street pairs among candidates, and the missed empty-address French records sit in name groups of six or more S1 [M] ([RESEARCH_v6 §2.6][r6]).
- **Small score shifts move ranks** where house numbers are small and shared: v3 dropped 2,186 French v5all predictions out of the record's top 4, mostly acronyms and brand names at the address [M] ([RESEARCH_v6 §4][r6]).
- **A learned cut depends on its model.** A later model that ranks differently must be re-measured with the cut.
- **Per-S1 top-k cuts** cap recall for large entities (table in Q3).

## 7. Jury questions with answers

**Q1. Why didn't you block on city or state?**
Say the §5.1 argument: hard keys lose every pair whose field is missing or non-canonical, and empty addresses alone are 4.4% of true pairs; we use city words and number × street compounds as weighted keys inside a ranked search, then a learned filter. Admit that we did not measure a pure city-key variant, and name what we would add: a (country, normalised city) view gated by the 0.1-point rule, and an exact-address view (+516 holdout pairs).

**Q2. What is your candidate-pairs-per-entity ratio, and what recall do you keep?**
Retrieval keeps 99.1% of true holdout pairs at about 34 per S1. A gradient-boosted cut brings the file to 3.70 per test S1 (6.41M pairs); when we measured that cut it kept 98.2% of true pairs and changed holdout F0.5 by −0.000003, because the pairs it drops are ones the matcher never predicts. The floor is the 3.46 true copies per S1.

**Q3. Could you get to 2 candidates per S1?**
Not with a fixed per-S1 budget. Even a perfect ranker loses recall for large entities [E, from the copy-count distribution]:

| per-S1 top k | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| pair-recall ceiling | 27% | 53% | 74% | 88% | 95% | 99% |
| oracle macro F0.5 | | 0.87 | 0.95 | 0.98 | | |

Budgets must adapt per entity, which a per-record cut does. On the final model, the per-record top-1 cut (3.61 per holdout S1 when measured at v5all) already cost −0.000106 F0.5 [M].

**Q4. Why search in both directions?**
Common names and test's 23% extra look-alikes crowd S1 lists; from the record's side its true S1 is usually the top hit. On v0 the record-side trim mattered most, and simulated crowding beyond test's level cost only −0.00009 [M].

**Q5. Why sparse IDF retrieval instead of embeddings and ANN?**
Our evidence is exact rare tokens and house numbers, which sparse retrieval matches exactly and dense vectors blur: 42 and 44 Main Street embed almost identically. It ran on CPUs in minutes, needed no training, and gave France its own IDF without labels. A dense-versus-sparse gate (G2) was planned and dropped because the GPU views were not needed ([ROADMAP][roadmap]). Dense retrieval would be a useful extra view for transliterated or paraphrased names.

**Q6. Isn't the learned cut matching, not blocking?**
It is the last filter before the final models, and the README asks for exactly that set: "whatever your model actually runs inference over" ([task][task]). Every later stage (stage 2, stage 3, cross-encoders, the decision) sees only these 3.70 pairs per S1. In the literature it is a learned pre-ranker, or supervised meta-blocking.

**Q7. How would this scale to a billion records?**
Everything is per partition and embarrassingly parallel: key generation is linear, posting lists are capped (3,000 and 1,000), and each query costs at most its rare tokens times the cap. Partitions finer than country (region) and sharded indexes keep memory bounded; see [11](11-scaling-to-billions.md).

**Q8. How did you choose K = 40/8 and the trims 15/4?**
From the measured recall-versus-pairs curve on the holdout, then kept: the wide run (40/4 untrimmed) bought 0.23 points of recall for 72% more pairs [M].

**Q9. Without French labels, how do you know blocking was not France's problem?**
A label-free check: pairs that are obviously the same (same name key, same house number and street word) were 100% candidates in France, as in US/India; the misses are empty-address records in huge name groups, which are ties anyway [M].

**Q10. What does blocking still miss?**
16,455 holdout pairs: mostly empty-address records whose name was also changed, and invented-name records whose address lost its number [M] ([RESEARCH_v6 §6.18][r6]). No key can find their owner, and unowned records of that kind are only 37–40% true, below the precision at which adding pairs pays ([04](04-metrics-and-decisions.md)).

## 8. Self-test

1. Define PC, RR and PQ, and compute RR for our candidate file within country.
<details><summary>Answer</summary>PC = |C ∩ M|/|M|, RR = 1 − |C|/|Ω|, PQ = |C ∩ M|/|C|. RR = 1 − 6.41 × 10⁶ / 6.72 × 10¹² ≈ 1 − 9.5 × 10⁻⁷.</details>

2. MinHash with b = 20 bands of r = 5 rows: what is P(candidate) at Jaccard 0.8 and at 0.3?
<details><summary>Answer</summary>1 − (1 − s⁵)²⁰. At 0.8: 0.8⁵ = 0.328, so 1 − 0.672²⁰ ≈ 0.9996. At 0.3: 0.3⁵ = 0.0024, so 1 − 0.9976²⁰ ≈ 0.047.</details>

3. Compute our blocking score for q = {a, b, c} with IDF 4, 1, 1 and d = {a, c, e} with IDF 4, 1, 2.
<details><summary>Answer</summary>Shared a and c: 4 + 1 = 5. Norms √6 ≈ 2.449 and √7 ≈ 2.646. Score 5 / 6.481 ≈ 0.77.</details>

4. Why does a per-S1 top-2 cut cap pair recall near 53%?
<details><summary>Answer</summary>It keeps at most min(T, 2) of each S1's T copies. With the train distribution (5.6% T = 0, 5.4% T = 1, the rest T ≥ 2), E[min(T, 2)] ≈ 0.054 + 0.89 × 2 = 1.83, against E[T] = 3.46.</details>

5. Which true pairs can our rare-token seeding never find?
<details><summary>Answer</summary>Pairs whose shared tokens all have posting lists above the cap (3,000 or 1,000): common words only, such as a generic name with an empty address. Common tokens count in the score only after a candidate has been seeded by a rare one.</details>

6. Why is sorted neighbourhood sensitive to the first characters of the key?
<details><summary>Answer</summary>Sorting puts records with the same prefix together; a typo in the first character moves a record far away in the order, outside any window. Multiple passes with different keys compensate.</details>

7. Why is "p1 ≥ 0.02 among the record's top 2 S1" the right shape for our data?
<details><summary>Answer</summary>Each record has at most one owner and argmax ownership keeps only its best S1, so a record's lower-ranked S1 are almost never predicted. A per-record limit removes them without capping S1 that own many records, which a per-S1 top-k would.</details>

## 9. Further reading

- Christen (2012), "A Survey of Indexing Techniques for Scalable Record Linkage and Deduplication", IEEE TKDE.
- Papadakis, Skoutas, Thanos and Palpanas (2020), "Blocking and Filtering Techniques for Entity Resolution: A Survey", ACM Computing Surveys.
- Hernández and Stolfo (1995), "The Merge/Purge Problem for Large Databases", SIGMOD.
- McCallum, Nigam and Ungar (2000), "Efficient Clustering of High-Dimensional Data Sets with Application to Reference Matching", KDD.
- Broder (1997), "On the Resemblance and Containment of Documents".
- Indyk and Motwani (1998), "Approximate Nearest Neighbors: Towards Removing the Curse of Dimensionality", STOC.
- Bayardo, Ma and Srikant (2007), "Scaling Up All Pairs Similarity Search", WWW.
- Robertson and Zaragoza (2009), "The Probabilistic Relevance Framework: BM25 and Beyond", Foundations and Trends in IR.
- Malkov and Yashunin (2020), "Efficient and Robust Approximate Nearest Neighbor Search Using Hierarchical Navigable Small World Graphs", IEEE TPAMI.
- Johnson, Douze and Jégou (2019), "Billion-scale similarity search with GPUs", IEEE Transactions on Big Data.
- Papadakis, Koutrika, Palpanas and Nejdl (2014), "Meta-Blocking: Taking Entity Resolution to the Next Level", IEEE TKDE.
- Michelson and Knoblock (2006), "Learning Blocking Schemes for Record Linkage", AAAI.

[finale]: ../../finale/README.md
[metric]: ../../code/business_entity_resolution/src/ber/eval/metric.py
[doc]: ../../experiments/ameya/final-zip/doc/Documentation_template.md
[blk2]: ../../docs/decisions/2026-09-25_2142_gate-g1-blocking-v2.md
[blk3]: ../../docs/decisions/2026-09-26_1122_blocking-v3-repairs.md
[cut]: ../../docs/decisions/2026-09-26_0532_candidate-set-cut.md
[feat]: ../../experiments/ameya/model-v1/FEATURES.md
[plan]: ../../plans/FINAL_PLAN.md
[blockpkg]: ../../code/business_entity_resolution/src/ber/block/__init__.py
[index]: ../../code/business_entity_resolution/src/ber/block/index.py
[text]: ../../code/business_entity_resolution/src/ber/block/text.py
[search]: ../../code/business_entity_resolution/src/ber/block/search.py
[repair]: ../../code/business_entity_resolution/src/ber/block/repair.py
[indic]: ../../code/business_entity_resolution/src/ber/block/indic.py
[b0]: ../../docs/handover/2026-09-25_1706_ameya_block-v0-baseline.md
[m1]: ../../docs/handover/2026-09-25_1958_ameya_model-v1.md
[r5]: ../../experiments/ameya/model-v1/RESEARCH_v5.md
[r6]: ../../experiments/ameya/model-v1/RESEARCH_v6.md
[contracts]: ../../docs/CONTRACTS.md
[roadmap]: ../../docs/ROADMAP.md
[task]: ../../student_resource/README.md
