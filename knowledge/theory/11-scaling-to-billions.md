# Scaling to billions of records

**Summary.** Every stage after blocking costs time in proportion to the number of pairs it handles, so the candidates-per-entity ratio is the main cost driver: we retrieve 33.7 pairs per S1 (99.1% of true holdout pairs) and keep 3.70 per S1 after a learned cut, against 3.46 true matches per S1.
At a billion records, our design scales linearly if the blocking partitions stay small, the cross-encoders stay confined to the uncertain band, and the 7B is targeted or distilled.
This page gives the complexity of each stage, back-of-envelope costs, and what we would change for production.

Related pages: [entity resolution](01-entity-resolution.md), [blocking](02-blocking.md), [gradient boosting and cascades](06-gradient-boosting-and-stacking.md), [cross-encoders](08-transformers-and-cross-encoders.md), [LLM verification and compute](10-llm-verification-and-compute.md), [glossary](glossary.md).

---

## 1. Intuition

- Comparing every reference record with every source record is quadratic: a million by a million is a trillion pairs. **Blocking** turns that into a short list per record; everything after it pays per pair on that list.
- So the questions at scale are: how short is the list (pairs per entity), how much recall does it keep, how evenly is the work spread across machines, and which pairs deserve an expensive model.
- Our pipeline is a funnel: 58.4M retrieved test pairs → 6.41M candidates → 1.49M for the cross-encoders → 5.85M predicted matches, of which 5.6M were re-read by the 7B.

## 2. Formal definition

### 2.1 Measures of blocking

For a candidate set C, the true pairs T, and all possible pairs A:
- **pair completeness (recall)** = $|C \cap T| / |T|$;
- **reduction ratio** = $1 - |C| / |A|$;
- **pairs per entity** = $|C| / \#\text{S1}$, which bounds recall from below: with m true matches per S1 on average, recall R needs at least $m \cdot R$ pairs per S1.

Our numbers (test split, 1,732,544 S1; [`Documentation_template`](../../experiments/ameya/final-zip/doc/Documentation_template.md) §3, [decision records](../../docs/decisions/)):

| set | pairs | per S1 | recall on the holdout |
|---|---|---|---|
| all within-country pairs | about 6.7e12 [E] | about 3.9M | 1 |
| retrieval (blocking v3) | 58,437,794 | 33.7 | **99.135%** [M] |
| candidate file (learned cut: p1 ≥ 0.02 and the record's top 2 S1, plus acronym joins) | 6,410,308 | **3.70** | 98.20% when measured on the v5all chain; F0.5 unchanged [M] |
| predictions (Composite B) | 5,851,832 | 3.38 | precision 99.9%, recall 97.5% [M] |
| truth | | 3.46 | |

The within-country count multiplies each country's S1 by its records (US about 0.66M × 3.8M, India 0.81M × 4.7M, France 0.26M × 1.4M). The reduction ratio is then 0.9999913 for retrieval and 0.99999904 for the candidate file [E]. The file is 7% above the 3.46 truth, and 3.4 per S1 (the predictions) is the floor for this model.

**Read the 99.1% carefully.** It is the recall of retrieval at 33.7 pairs per S1. The cut to 3.70 per S1 drops true pairs that the decision would never predict: measured on the v5all chain it lowered pair recall from 98.93% to 98.20% and the oracle F0.5 from 0.99676 to 0.99452, while the holdout F0.5 stayed level (Δ −0.000003 [−0.000015, +0.000011]) ([candidate-set-cut record](../../docs/decisions/2026-09-26_0532_candidate-set-cut.md)). It was not re-measured on blocking v3.

### 2.2 Complexity per stage

N is the number of records, P the number of pairs a stage handles, L ≤ 96 the tokens per pair.

| stage | work | grows with | our code |
|---|---|---|---|
| normalise, tokenise | O(N) | records | `ber.block.text`, repairs |
| index per country | O(tokens), then sort | records | [`ber.block.index`](../../code/business_entity_resolution/src/ber/block/index.py) |
| top-k search, both directions | per query: seeds from rare tokens only (posting list ≤ a cap of 1,000 or 3,000), exact scores for the best 400 or 200, keep 40 and 8 | records, if posting lists stay bounded | [`ber.block.search`](../../code/business_entity_resolution/src/ber/block/search.py) |
| pair features | O(P) string operations | retrieved pairs | `feats*.py` |
| context features, ownership | group-by S1 and by record: O(P log P) | pairs | [`s2.py`](../../experiments/ameya/model-v1/s2.py) |
| stages 0–3 | O(P × trees × depth) | pairs, shrinking per stage | [page 06](06-gradient-boosting-and-stacking.md) |
| cross-encoders | O(band × L × parameters) | band pairs (0.86 per S1) | [page 08](08-transformers-and-cross-encoders.md) |
| expected-F0.5 decision | per S1, at most 48 candidates and 16 set sizes | S1, fully parallel | [`decide.py`](../../experiments/ameya/model-v1/decide.py) |
| 7B re-check | O(predictions × L × parameters) | predictions (3.2 per S1) | [page 10](10-llm-verification-and-compute.md) |

Everything is linear in N, with one catch: the search stays linear only while posting lists stay short. In a partition ten times larger, a token's document frequency is ten times larger; with a fixed seed cap, more tokens stop seeding candidates, and recall falls silently. **Small partitions are what keep the search both cheap and exact.**

### 2.3 Back-of-envelope at a billion records

Assume the same mix as our test split (about 11.7M records, one S1 per 6.75 records), so a billion records hold about 148M S1, 85 times our test. Costs below scale our measured test runs linearly [E] (measured times [R]: Bakshi's [methodology](../../experiments/bakshi/final-package/METHODOLOGY_bakshi.md), [package README](../../experiments/bakshi/final-package/PACKAGE_README.md)).

| quantity | our test split | at 1B records [E] |
|---|---|---|
| retrieved pairs | 58.4M | about 5.0B |
| candidate pairs (3.70 per S1) | 6.41M | about 550M |
| band pairs (0.86 per S1) | 1.49M | about 127M |
| predictions to re-check (3.2 per S1) | 5.6M | about 480M |
| blocking | 15 min on 64 vCPUs | about 21 h on one such box: about 1,400 vCPU-hours |
| pair features (test share of 52 min) | about 24 min on 64 vCPUs | about 2,200 vCPU-hours |
| 7B over the band | 41 GPU-minutes per pass | about 59 GPU-hours per pass |
| one e5-large-sized cross-encoder over the band | well under an hour | a few GPU-hours (13 times fewer parameters than the 7B) |
| 7B re-check | about 3.6 GPU-hours | about 220–310 GPU-hours |
| 7B over every retrieved pair (not done) | about 27 GPU-hours | about 2,300 GPU-hours |

The CPU stages parallelise across partitions and finish in minutes to hours on a cluster. The danger is a model that touches every pair: the 7B over all retrieved pairs would need about 2,300 GPU-hours, about forty times a 7B pass over the band. Pairs per entity, and which pairs reach the expensive models, decide the bill.

## 3. Variants

| technique | idea | at scale |
|---|---|---|
| Standard blocking, sorted neighbourhood | exact keys; a window over sorted keys | cheap, but brittle to typos in the key |
| Canopy clustering | cheap distance makes overlapping canopies | an early answer to the same problem |
| Inverted index with IDF (ours) | records sharing rare tokens | posting lists must stay short |
| Block purging | ignore oversized blocks or posting lists | our seed cap does this |
| Meta-blocking | weight the graph of co-blocked pairs, prune weak edges | our learned cut (stages 0–1, top 2 per record) is supervised meta-blocking |
| Similarity joins with prefix filtering | provably find all pairs above a threshold | exact, but sensitive to frequent tokens |
| MinHash LSH | similar sets collide in hash buckets | sub-quadratic candidate generation |
| ANN on embeddings (HNSW, IVF-PQ, ScaNN) | nearest neighbours in vector space | a recall view for garbled or transliterated names |
| MapReduce / Spark load balancing | split large blocks across workers | needed for heavy keys |
| Incremental and progressive ER | update matches as records arrive; best pairs first | needed for streams |

## 4. Where we used it

- **Partitions by country**, from the data's own label (an open set; records without a label join every partition). IDF weights and neighbours never mix countries, so France got its own statistics with no code change ([`ber.block`](../../code/business_entity_resolution/src/ber/block/__init__.py)).
- **Rare compound keys** stay selective where single tokens are common: (house number, one of the first address words), (house number, name token), pairs of name tokens, and name token × address word. A (house number, street word) key behaves like a finer key than city or state, because it names one stretch of one street.
- **Block purging** through the seed cap: only tokens with short posting lists seed candidates; common tokens still count in the exact re-scoring.
- **Supervised meta-blocking:** stage 0 (200 trees) and stage 1 cut 58.4M retrieved pairs to 6.41M with no F0.5 change; tighter cuts lost (each record's top 1: −0.000106; p1 ≥ 0.05: −0.000041) ([Documentation](../../experiments/ameya/final-zip/doc/Documentation_template.md) §3).
- **Compute where uncertain:** cross-encoders on 2.6% of retrieved pairs, the 7B on the band and on confident predictions only.
- **Measured runs** [R]: blocking 11 and 15 minutes (train, test) on 64 vCPUs; features 52 minutes; stages 0–1 12 minutes; a stage-2 fit about 20 minutes; e5-large about an hour per three-model run on one H100; the 7B about 2 hours on three H100s; the XGBoost stages fit in 32 GB of RAM.

**Why no explicit city or state keys?** At our size, per-country search was affordable, and the IDF-weighted compound keys already acted as fine keys, while hard city partitions risk recall:
- 4.41% of true copies have an empty address, so no city at all (the names-only view catches them);
- vendors format places differently: US Source 3 spells states out, India abbreviates, 32% of French addresses name a department or region, and French street types appear as "R." or "Q.";
- where the place is present and canonical, a city key is safe: copy-like French pairs change commune only 3 times in 546,465 ([stacked-rules record](../../docs/decisions/2026-09-27_0636_stacked-rules.md)).

**Hindsight:** at a billion records we would add hierarchical partitions (country, then state or region, then city) as soft keys for the address view, with hand-written lexicons to canonicalise place names, a country-wide names-only view for address-less records, and per-view recall measured on the holdout as we did for every view (a view stayed only if it added at least 0.1 point of recall).

## 5. Why it fits this problem

- The reference side (S1) is deduplicated and each record has at most one owner, so matching is **star-shaped**: each record attaches to one S1, with no chains of matches to close transitively. That makes partitioning, parallel decisions and incremental updates simple.
- The data's country label gives a natural first partition; places give the next levels.
- 3.46 true matches per S1 on average means a list of a few candidates per S1 is enough, if it is the right few.

## 6. Pitfalls

1. **Skew.** Common tokens ("services", "rue", big cities) and big partitions create giant blocks and stragglers. Remedies: purging, salting or splitting heavy keys, compound keys.
2. **Silent recall loss.** Posting lists grow with the partition; a fixed seed cap then drops tokens. Monitor recall per view and per country, not only the total.
3. **Hard keys lose recall.** Empty or differently formatted places lose matches under exact partitions; use soft keys with fallbacks.
4. **Approximate search is approximate.** HNSW and PQ trade recall for speed; measure the recall of each index against an exact search on a sample.
5. **Quoting the wrong recall.** 99.1% belongs to retrieval at 33.7 per S1, not to the 3.70-per-S1 file.
6. **Group features need shuffles.** Per-record and per-S1 features (ranks, margins, ownership) need data grouped by key; at scale that is a distributed sort.
7. **Expensive models creep.** Each new cross-encoder in the mix is another pass over the band; a 7B pass at a billion records is about 60 GPU-hours.
8. **Reproducibility.** Hash-based folds and fixed seeds keep CPU stages deterministic; GPU models are not bit-identical across machines (our reruns land within about ±0.0001).

## 7. Jury questions with answers

**Q1. How would your pipeline scale to a billion records?**
Linearly, if three things hold: partitions stay small enough that posting lists stay short (country, then region and city), the cross-encoders stay confined to the uncertain band, and the 7B is targeted or distilled. At a billion records that is roughly 5B retrieved pairs, 550M candidates and 127M band pairs; the CPU stages need a few thousand vCPU-hours and a band cross-encoder a few GPU-hours per pass.

**Q2. What is your candidate-pairs-per-entity ratio?**
3.70 candidate pairs per S1 in the submitted file (6,410,308 for 1,732,544 S1), against 3.46 true matches per S1 and 3.38 predictions. Retrieval finds 33.7 per S1 with 99.1% recall; the learned cut keeps the pairs the decision can use, at no measured F0.5 cost.

**Q3. Is 99.1% the recall of your candidate file?**
No, it is the recall of retrieval. When we measured the cut on an earlier chain, the file's pair recall was 98.2%, but the pairs it dropped were ones the model never predicted, so F0.5 did not change. We would rather say that precisely than overclaim.

**Q4. Why no city or state blocking keys?**
Our compound keys (house number × street word, name × address word) are finer than city or state and tolerate missing places, and per-country search was affordable. Hard place keys lose the 4.41% of copies with no address and those whose place is written differently. At a billion records we would add place partitions as soft keys, with canonicalised names and a names-only fallback.

**Q5. What breaks first as data grows?**
Blocking skew: giant posting lists for common tokens and big partitions, which either slow the search or, with a fixed cap, silently cost recall. Second, any model run on all pairs.

**Q6. What is the most expensive stage at scale, and how do you control it?**
The transformers. Their workload is set by the band (0.86 pairs per S1) and the re-check (3.2 per S1). We would narrow the band to a budget, route only disagreements to the large model, distil the ensemble into one small cross-encoder, and run the 7B only on risky slices such as names shared by many S1.

**Q7. What recall would you lose at 2 candidates per S1?**
At least 42% of true pairs, even with a perfect ranker, because S1 have 3.46 true matches on average: 2 / 3.46 = 58% at best. Our cut is 2 per record instead, which matches the rule that a record has one owner; dropping to 1 per record lost 0.000106 F0.5.

**Q8. How would you make it incremental?**
Matching is star-shaped, so a new record only needs its own candidates: query the indexes both ways, score its pairs, assign it to its best S1, and re-run the per-S1 decision for the S1 it joins or leaves. A new S1 re-decides only the records it now competes for. Statistics such as IDF are refreshed periodically, with full rebuilds on a schedule.

**Q9. What would you change for production?**
Hierarchical, skew-aware blocking with an embedding view; one production model per stage instead of out-of-fold ensembles; a distilled cross-encoder; label-free monitors (probability mass per S1 and per record, per-source caps, match-count distributions) as drift alarms; and a small labelled sample for each new country instead of relying on self-training alone.

## 8. Self-test

1. With 6.7e12 within-country pairs, what are the reduction ratios of 58.4M retrieved pairs and of 6.41M candidates?
<details><summary>Answer</summary>

1 − 58.4e6 / 6.7e12 = 1 − 8.7e-6 = 0.9999913; 1 − 6.41e6 / 6.7e12 = 1 − 9.6e-7 = 0.99999904.

</details>

2. S1 have 3.46 true matches on average. What is the fewest candidates per S1 that can reach 99% pair recall?
<details><summary>Answer</summary>

3.46 × 0.99 ≈ 3.43 per S1, and only with a perfect ranker. Our 3.70 is about 8% above that floor.

</details>

3. How long would the 7B take on 5B retrieved pairs at 600 pairs per second per GPU, and on 100 GPUs?
<details><summary>Answer</summary>

5e9 / 600 ≈ 8.3M GPU-seconds ≈ 2,300 GPU-hours ≈ 96 GPU-days; on 100 GPUs about 23 hours.

</details>

4. A billion 768-dimensional float32 embeddings take how much memory, and how much with 64-byte product quantization?
<details><summary>Answer</summary>

768 × 4 = 3,072 bytes each, about 3.1 TB; with 64-byte codes about 64 GB, plus the index structure.

</details>

5. A token appears in 2,000 records of a partition, and the seed cap is 3,000. What happens if the partition grows tenfold?
<details><summary>Answer</summary>

Its posting list grows to about 20,000, above the cap, so it no longer seeds candidates. Records whose only rare-enough evidence was that token are no longer found. Splitting the partition (by region or city) brings the list back under the cap.

</details>

6. Why does star-shaped matching make incremental updates cheap?
<details><summary>Answer</summary>

Each record has at most one owner among deduplicated S1, so there are no chains of matches to re-close. A new record affects only its own candidate pairs, its ownership, and the decision of the one or two S1 involved.

</details>

## 9. Further reading

- Fellegi and Sunter (1969). A theory for record linkage.
- Hernández and Stolfo (1995). The merge/purge problem for large databases.
- McCallum, Nigam and Ungar (2000). Efficient clustering of high-dimensional data sets with application to reference matching.
- Christen (2012). Data Matching: Concepts and Techniques for Record Linkage, Entity Resolution, and Duplicate Detection.
- Christen (2012). A survey of indexing techniques for scalable record linkage and deduplication.
- Papadakis, Ioannou, Niederée and Fankhauser (2011). Efficient entity resolution for large heterogeneous information spaces.
- Papadakis, Koutrika, Palpanas and Nejdl (2014). Meta-blocking: taking entity resolution to the next level.
- Papadakis, Papastefanatos and Koutrika (2014). Supervised meta-blocking.
- Papadakis, Skoutas, Thanos and Palpanas (2020). Blocking and filtering techniques for entity resolution: a survey.
- Bayardo, Ma and Srikant (2007). Scaling up all pairs similarity search.
- Broder (1997). On the resemblance and containment of documents.
- Indyk and Motwani (1998). Approximate nearest neighbors: towards removing the curse of dimensionality.
- Jégou, Douze and Schmid (2011). Product quantization for nearest neighbor search.
- Malkov and Yashunin (2020). Efficient and robust approximate nearest neighbor search using hierarchical navigable small world graphs.
- Johnson, Douze and Jégou (2019). Billion-scale similarity search with GPUs.
- Guo et al. (2020). Accelerating large-scale inference with anisotropic vector quantization.
- Dean and Ghemawat (2004). MapReduce: simplified data processing on large clusters.
- Zaharia et al. (2012). Resilient distributed datasets: a fault-tolerant abstraction for in-memory cluster computing.
- Kolb, Thor and Rahm (2012). Load balancing for MapReduce-based entity resolution.
- Whang, Marmaros and Garcia-Molina (2013). Pay-as-you-go entity resolution.
- Gruenheid, Dong and Srivastava (2014). Incremental record linkage.
- Hinton, Vinyals and Dean (2015). Distilling the knowledge in a neural network.
