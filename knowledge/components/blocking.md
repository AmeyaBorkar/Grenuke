# Blocking and candidate generation (BLK)

**Summary.** Blocking proposes about 34 candidate records per S1 (58.4M pairs on test) by exact, IDF-weighted key overlap searched separately in each country and in both directions, with a names-only view for short addresses and repairs for glued domains and OCR digits.
A learned cut then shrinks that to the 6,410,308 pairs (3.70 per S1) that the matching model actually scores: retrieval keeps 99.1% of the true holdout pairs, the candidate file keeps 98.35%.
Path prefixes: `ber/` is `code/business_entity_resolution/src/ber/`; `mv1/` is `experiments/ameya/model-v1/`; `fpk/` is `experiments/bakshi/final-package/`. Parameters are read from the code at the cited line.

## 1. Purpose

Fix the recall ceiling of everything after it, at a size that every later stage can afford: 1.7 x 10^13 possible pairs become 58.4M retrieved pairs, then 6.41M candidates.
Produce the organisers' `candidate_pairs.tsv` honestly: the set the model scores, not the raw first pass.

## 2. How it works

### 2.1 Parameters of the final run (`fpk/reproduce.sh:116-119`; defaults `ber/block/__init__.py:152-167`)

| parameter | value | meaning |
|---|---|---|
| `k_s1` / `k_r` | 40 / 8 (defaults) | S1 to S2/S3: top 40 records per S1; S2/S3 to S1: top 8 S1 per record |
| `trim_s1` / `trim_r` | 15 / 4 (set; defaults 30 / 2) | keep a pair if the record is in the S1's top 15 or the S1 is in the record's top 4 |
| `seed_cap_r` / `seed_cap_s1` | 3000 / 1000 | a key with a longer posting list does not seed candidates |
| `verify_s1` / `verify_r` | 400 / 200 | seeded candidates re-scored exactly |
| names-only view | on; `ns_k` 10 both ways, trims 5 / 5, verify 200 / 200 | `ns_max_addr_tokens` 3: records with at most 3 address tokens join it |
| `ns_ngrams` | 4 | character 4-grams of names in the names-only view |
| `ns_domain_len` | 8 | one-token names of 8 or more letters also join it |
| `nw_words` | 6 | name-word by address-word compound keys in the token view |
| `seg_domains`, `ocr_repair` | 1, 1 | S2/S3 name repairs ([normalisation.md](normalisation.md)) |
| `indic_dict` | `ameya-fx1` | the 693-entry dictionary |

### 2.2 Keys per record ([`ber/block/index.py`](../../code/business_entity_resolution/src/ber/block/index.py):135-212)

Base keys, each in its own namespace: name tokens including repairs; the joined name for names of 2 or more tokens; address words; address numbers; consonant skeletons of name tokens of 3 or more characters. Compound keys, bit-packed into int64 (kind in bits 61-62):
- kind 2: unordered pairs among the first 4 name tokens;
- kind 1: one of the first 2 numbers with one of the first 3 address words (street types are not skipped here);
- kind 3: one of the first 2 numbers with one of the first 3 name tokens;
- kind 0: one of the first 2 name tokens with one of the first `nw_words` = 6 address words that have at least 4 letters and are not street types.
Names-only view: character 4-grams of the name tokens joined without spaces, stored as negative int64 so they never collide with token keys (`:115-132`).

### 2.3 Partition, weight, score

- One partition per exact country label; records with an empty label join every partition (`ber/block/__init__.py:52-62`). The search never crosses countries, and France gets its own IDF.
- Weight of a key: `w = max(ln(n_docs / df), 0.01)`, where `df` counts the partition's S1 and S2/S3 records holding the key (`ber/block/index.py:298-300`). Row norm is `sqrt(sum of w)`.
- Score of a pair: `sum of w over shared keys / (norm_q * norm_d)`, the cosine of binary key vectors with sqrt(idf) entries (`ber/block/search.py:3-4, 114`). Exact, checked against brute force in tests, float32 and int32 for determinism.
- Search (`:65-121`, numba): only query keys with posting length within the seed cap add to accumulators; the best `n_verify` candidates by partial score are re-scored exactly with every common key found by binary search; a min-heap keeps the top k. A query that shares no rare key gets no candidates.
- Both directions per view. `union_trim` keeps a pair when `rank_s1 < trim_s1` or `rank_r < trim_r`; the pair score is the maximum of the two directions (`ber/block/__init__.py:65-105`). Why both: S1 lists get crowded by look-alikes, and a record finds its own S1 from its side even when that S1's list is full.
- Views: `tok` over all S2/S3 of the partition, and `name_short` between every S1 and the S2/S3 records with at most 3 address tokens or a one-token name of 8 or more letters, names only (`:206-243`). Output: s1, r, a view bitmask, score and both ranks per view, sorted by (s1, r).

### 2.4 The learned cut (the candidate file)

The candidate file is not the blocking output. It is the stage-1 filter of the model chain: a pair stays only if (a) stage 0 keeps it (`p0 >= tau0`), (b) its stage-1 probability is at least 0.02, and (c) its S1 is one of the record's two best S1 by p1, ties going to the lower s1 (`mv1/common.py:86-100`, `mv1/cands_final.py:43-44`). This is an intersection, not a union ([CF-14](../conflicts.md); the submitted document's "plus" is loose). The result is `ameya-cands-v6all-c2`; the France-only acronym join then adds 3,853 pairs outside the cut (`mv1/acr_join.py:115-116`), giving the `-c2a` sets. The submitted file: 6,410,308 pairs, 3.70 per test S1.

Funnel, pairs per test S1 [M, final pipeline, [numbers §2](../numbers.md)]: retrieval 33.73, stage 0 4.77, stage-2 input 4.65, the cut 3.698, candidate file 3.700, final matches 3.378. Holdout pair recall along the same funnel: 0.99135, 0.99079, 0.99078, 0.98354 [M]. By country, candidates per S1: US 3.640, India 3.617, France 4.111 [M]; 75,361 S1 have no candidate.

### 2.5 Honest section: city and state keys

- **What we did.** We partition by the exact country label only (D-BLK-02) and use no hard city or state key. City and state words enter softly: as ordinary address words, inside the name-word by address-word compounds (kind 0, which act like (name, city) keys) and inside the house-number by address-word compounds (kind 1, which are finer than any city key because they pin a building). A key adds IDF weight to a ranking instead of defining a block, so one missing or garbled field lowers a score instead of losing the pair.
- **What the earlier notes got wrong.** D-BLK-02, D-ORG-28 and the submitted methodology (Table 2) say city and state are used as features. The code review found no city or state column in the final feature bundle; parsed city and state exist only in the unused `ber/features/string.py` ([CF-24](../conflicts.md)). A parsed city is used in exactly one place, a France-only rule in the decision layer (cross-commune drop, `stk/apply_polish.py` with `stk/citylib.py`). The accurate sentence is: the address enters as word and number overlaps, and city and state have no dedicated feature or key.
- **What the organisers said.** Their ranking e-mail said that finer-grained blocking keys (for example city/state) and compute-efficient methods scored higher ([finale README](../../finale/README.md)).
- **What we did not do.** We never measured a pure city or state key variant, so we cannot quote its recall or its retrieved volume. Reasons we expected a hard key to lose recall [M/E]: 4.4% of true pairs have an empty S2/S3 address and carry no city, which alone caps a hard (country, city) key without fallback near 95.6% pair recall against our 99.1% [E]; state and city are spelled, abbreviated, replaced by a county or written in native script inconsistently ([theory 02 section 5.1](../theory/02-blocking.md)); France has no postcodes to fall back on.
- **What a hard key would have bought, and what we did instead.** A smaller retrieved set. Our retrieval is larger than a keyed one might be (33.73 per S1). We got the efficiency from the learned cut: 3.70 per S1 against 3.46 true copies per S1 (within 7%), with a holdout F0.5 tie (-0.000003 [-0.000015, +0.000011], v5all) [M].

## 3. Why this design

Decision records: [BLK](../decisions/BLK.md).
- D-BLK-01 union of name-driven and address-driven retrieval, names-only view only for empty or short addresses: weak name 15.75% of true pairs, weak address 5.24%, both 0.14%.
- D-BLK-02 partition by exact country label, never by state: 0 cross-country pairs in 7.64M; states are missing, abbreviated or in regional script.
- D-BLK-03 heuristic trim 15 and 4, no learned pre-ranker: the record side matters most (at 15 per S1, record limit 0 to 4 lifts recall 0.9365 to 0.9752).
- D-BLK-04 own tokenizer; D-BLK-05 exact IDF overlap on the CPU instead of TF-IDF to SVD to GPU top-k (gate G2 never run).
- D-BLK-06 exact re-scoring and compound keys (0.9475 to 0.9702); D-BLK-07 learned Indic dictionary and 4-grams (0.9752 to 0.9857); D-BLK-08 name by address-word compounds (0.9857 to 0.9899).
- D-BLK-09 then D-BLK-10: the candidate file is the set the model scores, cut to p1 at least 0.02 and each record's top 2. Free win for the size criterion; Ameya's critique at 00:05 on 26 Sep ("our lists were about five times bigger than theirs") started it.
- D-BLK-11 repairs: 0.98992 to 0.99135. D-BLK-12 exact-address view not built (516 missed pairs, about +0.00007). D-BLK-13 decision-boundary cut rejected (it would misrepresent the pipeline). D-BLK-14 cut unchanged after self-training. D-BLK-15 alias-bridge route closed (ceiling about +0.0002). D-BLK-16 keep 3.70 against tighter cuts.

## 4. Alternatives and why not

- TF-IDF to SVD to GPU nearest neighbours (Plan A): never built; the sparse exact engine was faster to ship and exact.
- A learned pre-ranker inside blocking (G11): the stage-0 filter and the cut took that role.
- Per-S1 top-k: wrong shape, true sets reach 11; a per-record cut matches argmax ownership.
- Tighter cuts [M, v7sq3 rule]: record's top 1 only -106e-6 [-129, -83] (3.589 per S1); p1 at least 0.05 -41e-6 (3.608); at least 0.1 -105e-6; at least 0.2 -279e-6. A stage-2 pc gate at 2e-4 would cut 2.8% more at no loss but needed a rebuild.
- Cutting to the decision boundary (Bakshi): candidates would nearly equal matches; the README asks for the set the model scores.
- Blocking views from MinHash-LSH or embeddings: no record of a trial; exact keys already reached 99.1%, and the dense view planned in Plan A was never built (G2 never run).

## 5. Numbers

| fact | value | level | source |
|---|---|---|---|
| Retrieval volume | 58,437,794 test pairs (33.73 per S1); 66,429,057 train | M | [numbers §2](../numbers.md) |
| Retrieval recall by version | v0 0.9752, v1 0.9857, v2 0.9899, v3 0.99135 | M, local holdout | [numbers §2](../numbers.md) |
| Retrieval misses | 16,455 of 1,901,267 true pairs (0.87%); 54% are empty-address records with a changed name | M | [numbers §2](../numbers.md) |
| Oracle F0.5 after retrieval / after the cut | 0.99743 / 0.99499 | M | [numbers §2](../numbers.md) |
| Candidate-file recall | 0.98354: 31,304 true pairs outside the file, 14,849 of them lost by the cut | M | [numbers §2](../numbers.md) |
| Candidate file | 6,410,308 pairs; 105,028,761 bytes | M | [numbers §2](../numbers.md) |
| Stage 0 | keeps 15.4% of pairs at 99.95% of true pairs, so removes about 85% | M | [numbers §2](../numbers.md) |
| Runtime | 938 s test and 952 s train on the 24-core laptop; 11 and 15 min on a 64-vCPU box | M / R | [numbers §2](../numbers.md) |

Do not quote "3.70 per S1 at 99.1% recall": the 99.1% belongs to retrieval at 34 per S1. The decision record's 0.98198 is the same cut on an older file (v5all) and is superseded ([CF-13](../conflicts.md), [numbers.md](../numbers.md), "Numbers not to quote").

## 6. Failure modes and limits

- Crowded lists: 23.1% (India) and 24.9% (US) of holdout S1 lists are full at the cap of 15 (test: US 31.3%, India 28.1%, France 24.2%). Cap 15 to 10 cost only -0.00009 [M], so crowding is negligible; the record-side top 4 rescues owners.
- Seed caps: with a fixed cap, a bigger partition silently stops seeding on common tokens and recall falls.
- Empty-address, changed-name records: no key can find what is not there; 54% of the 16,455 retrieval misses.
- Look-alikes are retrieved as easily as true copies; separating them is the model's job.
- The cut is bounded by the model: any decoder that wants a lower-ranked S1 must be measured with the cut (D-BLK-10 hindsight). The France recall of the cut is unmeasured (no labels).
- Documents that joined 99.1% with 3.70 per S1 were wrong; the submitted methodology still does ([CF-13](../conflicts.md)).
- Planned GPU views were never built; blocking is CPU-only.

## 7. Scale

Work per query is about the sum of the posting lengths of its rare keys (at most 3000 or 1000 each) plus `n_verify` times the number of common keys times the log of the key-list length; per-country partitions run in parallel, and each parallel block allocates arrays of length n_docs (`ber/block/search.py:76-77, 133`). It stays linear in records only while posting lists stay short, so small partitions keep it cheap and exact. At 1,000 times the data we would shard by country and by a coarse key, move the heap search to a cluster and add an embedding or LSH view for skew; [theory 11](../theory/11-scaling-to-billions.md) estimates blocking at about 21 hours on one 64-vCPU box for a billion records [E].

## 8. Theory links

[02 Blocking](../theory/02-blocking.md), [11 Scaling to billions](../theory/11-scaling-to-billions.md), [01 Entity resolution](../theory/01-entity-resolution.md), [F06 Text, strings and retrieval](../theory/foundations/F06-text-strings-and-retrieval.md), [F08 Computing at scale](../theory/foundations/F08-computing-at-scale.md).

## 9. Likely questions

- **Why not city or state keys?** See 2.5. We never measured them; a hard key is capped by how often its field is present and canonical, and we used fine keys softly with a learned cut for efficiency.
- **How many candidates per S1, and what recall?** Retrieval about 34 per S1 at 99.1%; the file 3.70 per S1 at 98.35%; true copies average 3.46.
- **Why top 2 per record?** Each record has one owner, so a record's third-best S1 is almost never predicted; holdout F0.5 did not move.
- **What do you lose in the cut?** 14,849 true holdout pairs, which the decision would almost never have predicted.
- **Does blocking depend on the country list?** No: the partition is the exact label; France was handled by the same code.
- More in [qa.md](../qa.md).
