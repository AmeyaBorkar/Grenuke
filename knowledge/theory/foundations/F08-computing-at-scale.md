# F08. Computing at scale

**Summary**

- Comparing every record with every other grows with the square of the data, so everything here is built to avoid it: hashing and sorting to group records, an inverted index to find neighbours, and stages that go from cheap to costly so the expensive models see few pairs.
- Total cost is pairs times cost per pair. Candidates per entity (3.70 per S1 for us) is the number that drives it. The 7B model at about 600 pairs per second would need about 27 GPU-hours for the 58.4M retrieved test pairs.
- Memory and file layout decide what fits. Our stage 2 peaked at 16.5 to 19 GB on a 31 GB laptop, which is why we use columnar files, binned matrices, and no Python loops over pairs.

## What you need first

- [F01 data and problem](F01-data-and-problem.md): what a record and a pair are.
- [F06 text, strings and retrieval](F06-text-strings-and-retrieval.md): the inverted index and top-k search.
- Helpful: [F07](F07-neural-networks-transformers-llms.md) for the 7B model and GPU memory, [F13](F13-linear-algebra-and-optimisation.md) for vectors.

---

## 1. Big-O and why all-pairs is impossible

**Intuition.** We care about how the cost grows when the data grows. Doubling the data should not quadruple the work.

**Definition.** $f(N)=O(g(N))$ means $f$ grows no faster than a constant times $g$ for large $N$. Typical classes, for $N=10^6$:

| cost | name | operations at $N=10^6$ |
|---|---|---|
| $\log N$ | binary search | 20 |
| $N$ | one pass, hash lookup per item | $10^6$ |
| $N\log N$ | sorting | $2\times10^7$ |
| $N^2$ | all pairs | $10^{12}$ |

**Worked example.** Comparing every record with every other one in a collection of 23.7M records means $N(N-1)/2 = 2.8\times10^{14}$ pairs. Take a deliberately generous (made-up) rate of $10^7$ comparisons per second per core, one cheap comparison per pair, no model yet. One core needs 325 days. All 24 cores of our laptop need 13.5 days. The real task compares only S1 with S2/S3 records inside a country, which is smaller, but still far beyond reach. The fix is blocking: compare only pairs that share something. Our retrieval produced 58.4M test pairs, about 34 per S1 ([02 blocking](../02-blocking.md)).

## 2. Hashing

**Intuition.** A hash function turns any key into a number that looks random. Equal keys always give equal numbers, so you can find an item without searching.

**Definition.** A hash table stores items at position $h(\text{key}) \bmod B$ in an array of $B$ buckets, so lookup is $O(1)$ on average. Two keys may land in the same bucket (a **collision**); tables handle that by chaining or probing. Hash partitioning sends each key to bucket $h(\text{key})\bmod B$ so that related work lands together and data spreads evenly.

**In our code.** The fold of an S1 is `splitmix64(eid) mod 20`; folds 0 to 4 are the holdout ([splits.py](../../../code/business_entity_resolution/src/ber/eval/splits.py)). `splitmix64` is a fast mixing function from integers to integers. It gives us four things at no storage cost:

- the assignment is the same on every machine and every rerun;
- all pairs of one S1 go to the same fold;
- each fold gets about 5% of S1, so five folds are 25% (549,699 holdout S1 implies about 2.2M train S1);
- a second hash with a different salt gives an independent slice, such as the 10% S1 sample for stage 0 (`s1_hash_slice`).

**Collisions.** For $n$ keys hashed into 64 bits, the chance of any collision is about $n^2/2^{65}$. For $n=10^9$ that is $0.027$. For 32-bit hashes it would be certain. Joins use hashing too: build a hash table on the smaller table, probe it with the larger, cost $O(n+m)$.

## 3. Sorting, sparse layout, counting sort

**Intuition.** Sorted data can be searched in $O(\log N)$ and merged in one pass. Packing variable-length lists into two flat arrays avoids millions of small objects.

**Definition.** Sorting costs $O(N\log N)$. **CSR** (compressed sparse row) stores row $i$'s items at `codes[indptr[i] : indptr[i+1]]`. A **counting sort** puts integer keys in order in $O(N+K)$ by counting, taking prefix sums, and placing.

**Worked example.** Three records with token codes $r_0=\{2,5\}$, $r_1=\{5\}$, $r_2=\{2,3,5\}$. CSR: `indptr = [0,2,3,6]`, `codes = [2,5,5,2,3,5]`. To build the inverted index: count records per code (code 2: 2, code 3: 1, code 5: 3), prefix-sum to start offsets, then scatter the record ids. Posting lists: code 2 gives $[0,2]$, code 3 gives $[2]$, code 5 gives $[0,1,2]$. This is `build_postings` in [index.py](../../../code/business_entity_resolution/src/ber/block/index.py), linear in the number of tokens. Because each record's codes are sorted and unique, checking "does this record contain token $t$?" is a binary search. Our search uses it for exact re-scoring.

When data exceeds memory, an external sort sorts chunks, writes them out, and merges them $k$ at a time.

**Index size and sharding.** Our posting lists hold record ids as 32-bit integers, so an index over 100M tokens takes about 0.4 GB, plus one offset per distinct token. A query touches only the lists of its own tokens, so its cost is the sum of their lengths and does not depend on the total number of records. To spread an index over machines you can shard by document (each machine holds some records, every query goes to all machines, and the top-$k$ lists are merged) or by term (each machine holds some tokens, a query goes to a few machines, but a hot token overloads its machine). Our per-country partitions are document shards.

## 4. Partitioning by country

**Intuition.** Split the problem into independent pieces that each fit in memory and run in parallel.

**Our partitions.** All searches run per exact country label. The label set is open, so France needs no code change. This has four effects.

- IDF weights and nearest neighbours never mix countries, and France gets its own statistics.
- Records without a country are searched in every partition.
- The candidate graph is closed inside a country, so stage-2 features can be built per country (checked exactly in [RESEARCH_v6](../../../experiments/ameya/model-v1/RESEARCH_v6.md)).
- Partitions are lopsided. The leaderboard weights of the three countries are 0.38274 (US), 0.46751 (India) and 0.14975 (France) in the same note, which, because the metric averages over S1, are their shares of test S1; the largest partition is about 3.1 times the smallest. One big partition sets the finish time (a straggler).

The risk of any hard partition is a record whose key is wrong or missing: it never meets its S1. That is why a missing country means "search everywhere". A weaker key such as city or state is better used as a weight than as a wall ([02 blocking](../02-blocking.md)). In production the same idea is called sharding.

## 5. MapReduce, Spark, skew and hot keys

**Intuition.** Count words in a billion documents: each machine counts its share, then counts for the same word are brought together and added.

**Definition.** **MapReduce** (Dean and Ghemawat 2004) has three steps: map each record to (key, value) pairs; **shuffle** so that all pairs with the same key reach the same machine; reduce each key's values. The shuffle is the expensive step, because it moves data across the network and writes to disk. Spark (Zaharia et al. 2012) keeps data in memory in partitions, builds a plan of the steps, and can recompute a lost partition from the plan.

**Our retrieval in these terms.** Map each record to (token, record id); shuffle by token; reduce to a posting list. Then join each S1's tokens with the postings, emit (S1, record, partial score), group by S1 and keep the top $k$. We ran it on one machine with 24 cores and numba. At this scale (23.7M short records) the data fits in memory, and a shuffle costs more than shared memory. A well-tuned single machine often beats a cluster at moderate scale (McSherry et al. 2015, "Scalability! But at what COST?"). Spark pays off when data outgrows one machine.

**Skew.** If a key is shared by $L$ records, joining on it makes $L(L-1)/2$ pairs: $L=3{,}000$ gives 4.5M; $L=100{,}000$ gives $5\times10^9$; $L=10^6$ gives $5\times10^{11}$, and one machine gets all of them. These are **hot keys**, and our data has them: between 46% and 54% of S1 share their name with another S1, and a French decoy shares its name with a median of 43 other S1 ([method note](../../../experiments/ameya/final-zip/doc/Documentation_template.md)). Remedies:

- drop very common tokens (legal forms, stop words);
- cap the posting list used to start a search (`seed_cap`: 3000 in the record index, 1000 in the S1 index);
- salt the key (split "lille" into lille#0 to lille#9) and combine later;
- broadcast the small side of a join to every machine;
- aggregate in two stages (partial sums first, then totals).

## 6. Approximate nearest neighbours: LSH, HNSW, FAISS

When exact search is too slow, trade a little recall for a lot of speed.

**LSH** (Indyk and Motwani 1998). For set similarity, MinHash (Broder 1997) gives a signature where two sets agree on one entry with probability equal to their Jaccard similarity $s$. Split a signature into $b$ bands of $r$ entries; a pair is a candidate if any band matches fully. The probability is $1-(1-s^r)^b$. With $r=5$, $b=20$:

| $s$ | 0.3 | 0.5 | 0.6 | 0.7 | 0.8 | 0.9 |
|---|---|---|---|---|---|---|
| candidate probability | 0.047 | 0.470 | 0.802 | 0.975 | 0.9996 | 1.000 |

The curve is an S: near $(1/b)^{1/r}=0.55$ it switches from rare to common. For cosine, SimHash uses random hyperplanes: two vectors at angle $\theta$ agree on one bit with probability $1-\theta/\pi$ (0.857 at cosine 0.9).

**HNSW** (Malkov and Yashunin 2020). Build a layered graph where each point links to near neighbours. Search starts at the sparse top layer, walks greedily towards the query, and drops a layer at a time. Parameters: links per node $M$, build effort, and search effort (which sets the recall/speed trade-off). Memory is the vectors plus the links.

**IVF and product quantisation** (Jégou et al. 2011), in FAISS (Johnson et al. 2021). Cluster the vectors with k-means, search only the few nearest clusters (`nprobe`), and compress each vector into a few bytes. Memory for $10^7$ vectors of 256 dimensions: 10.24 GB in fp32, 5.12 GB in fp16, 0.16 GB with 16-byte codes.

**Exact on a GPU** can beat approximate search when it is feasible. Queries $\times$ documents $\times$ dimension $\times$ 2 gives the operations: $1.73\text{M}\times10\text{M}\times256\times2 = 8.9\times10^{15}$. At an assumed effective $10^{14}$ per second that is about 90 seconds. Our plan had this (gate G2: TF-IDF to SVD-256, then exact GPU top-k in fp16 tiles; [FINAL_PLAN](../../../plans/FINAL_PLAN.md)). The gate was dropped: the [ROADMAP](../../../docs/ROADMAP.md) records that the GPU views were not needed. Exact search also keeps recall attributable: a miss is a missing token, not an approximation.

## 7. The memory hierarchy

**Intuition.** Fast memory is small; big memory is slow. Speed depends on where the data sits and how it is read.

Typical orders of magnitude (hardware varies):

| level | latency | bandwidth |
|---|---|---|
| L1 cache | about 1 ns | very high |
| L2 and L3 cache | 5 to 40 ns | high |
| RAM | about 100 ns | 50 to 100 GB/s (desktop) |
| NVMe SSD | about 100 microseconds | 3 to 7 GB/s |
| data-centre network round trip | about 500 microseconds | 1 to 100 Gbit/s |
| GPU memory (data-centre cards) | n/a | 2 to 3 TB/s |

Two rules follow. Read sequentially: memory comes in cache lines of 64 bytes, so scanning a flat array uses every byte it fetches, while hopping between objects wastes most of it. And keep the **working set** (the data live at one time) in the fastest level that holds it.

**Our laptop** has 31 GB of RAM, 24 cores and a 12 GB GPU. Stage 2 peaked at 16.5 to 19 GB in our runs (the recipe notes about 18 to 19 for stages 1 and 2, [RECIPE.md](../../../experiments/ameya/model-v1/RECIPE.md)), so nothing else heavy can run beside them. Peak memory is the largest live set, which includes the feature matrix, the group features, the candidate arrays and the library's own copies, not the sum of file sizes. Habits that keep it down: load only the needed columns, work in chunks, use 32-bit types, delete intermediates, and store the training matrix as histogram bins (XGBoost's `QuantileDMatrix`). A bin index fits in 8 bits where a float needs 32: 10M rows $\times$ 100 features is 4.0 GB as float32 and about 1.0 GB as 8-bit bins (100 features is illustrative; the v3 dev kit had 87).

## 8. Parquet, Arrow and vectorised computation

**Row versus column storage.** A CSV stores one record after another. **Parquet** stores each column together, split into row groups. This helps in four ways.

- Read only the columns you need.
- Similar values sit together, so they compress well. **Dictionary encoding** replaces repeated strings by small integers; a country column of 10M rows with 3 distinct values needs about 2 bits per row, 2.5 MB, instead of tens of MB as text.
- Each row group stores min and max values, so a reader can skip groups that cannot match a filter.
- Compression such as zstd is applied per column.

Arrow is the matching in-memory columnar format, shared without copying between pyarrow, pandas and numpy. Its compute kernels run over whole columns with SIMD instructions (one instruction on several values).

**Vectorised or compiled.** A Python loop runs on the order of $10^7$ simple steps a second. A numpy or Arrow kernel runs on the order of $10^9$ element operations a second, so 100 times more is typical. For loops that cannot be vectorised, numba compiles them to machine code, as in our top-k heap. The project rule is to never write Python loops over pairs ([AGENTS.md](../../../AGENTS.md) section 6). In practice:

- the search splits the queries into 16 blocks per thread, a standard way to balance the load when some queries (long posting lists) cost far more than others ([index.py](../../../code/business_entity_resolution/src/ber/block/index.py), [search.py](../../../code/business_entity_resolution/src/ber/block/search.py));
- normalisation uses `pyarrow.compute` on whole columns ([text.py](../../../code/business_entity_resolution/src/ber/block/text.py));
- the cross-encoder script reads records with `iter_batches(batch_size=1_000_000, columns=[...])` and writes zstd-compressed Parquet in row groups ([ce.py](../../../experiments/ameya/model-v1/ce.py)).

## 9. Throughput arithmetic and what drives cost

**Cost model.** Total cost $=\sum_\text{stage}\ (\text{pairs entering})\times(\text{time per pair})$. Using the 7B model's 600 pairs per second as the unit:

| pairs scored by the 7B | count | seconds | GPU-hours |
|---|---|---|---|
| all retrieved | 58.4M | 97,333 | 27.0 |
| after stage 0 (about 80% removed) | 11.7M | 19,467 | 5.4 |
| candidate file | 6,410,308 | 10,684 | 3.0 |
| uncertain band | 1.49M | 2,483 | 0.69 |

The method note makes the same point: 58M pairs at about 600 per second is about 27 GPU-hours before any training, so the 7B is used on the band and on confident predictions.

**Candidates per entity.** Cost is entities $\times$ candidates per entity $\times$ time per pair. The retrieved set has about 33.7 pairs per S1 and the final candidate file 3.70 (against 3.46 true copies per S1), a 9.1 times reduction in every later stage. Tightening further is not free. Two tighter cuts, best S1 per record only or a threshold of 0.05, lowered holdout F0.5 by 0.000106 and 0.000041, so we kept the looser cut. The trade-off is recall against cost.

**Parallel speedup.** If a fraction $p$ of the work parallelises over $s$ workers, speedup is $1/((1-p)+p/s)$ (Amdahl's law). With $p=0.9$ and $s=24$ cores, 7.3 times, not 24. We got near-linear gains where jobs were independent: the three out-of-fold models ran on three GPUs, about 2 hours instead of about 6.

**Cost per pair by model.** A boosted-tree model walks each tree from root to leaf: about trees $\times$ depth comparisons. In the v3 dev kit, stage 1 had about 1,600 trees of depth up to 9, so at most about 14,400 comparisons per pair. The 7B model needs about $2\times7.07\times10^9$ operations per token, roughly $6\times10^{11}$ for a 40-token pair (an assumed length). The units differ, but the gap, about seven orders of magnitude, is why the trees can score all 58.4M retrieved pairs and the 7B cannot.

**Padding.** A GPU batch is a rectangle, so every sequence is padded to the longest. Toy case: lengths spread evenly from 20 to 96 tokens, mean 58. A random batch pads to about 96, so about 40% of the work is padding. Sorting by length inside random windows, as [ce.py](../../../experiments/ameya/model-v1/ce.py) does, cuts that to a few percent.

**At 100 times the data.** Scoring cost grows 100-fold if candidates per entity stay constant (the 7B on the band alone would be about 69 GPU-hours). Anything quadratic in group size (hot keys, rival counts) can grow faster. Memory that scales with rows (stage 2 at 19 GB) would no longer fit one machine. See [11 scaling to billions](../11-scaling-to-billions.md) and [F17](F17-production-ml-and-mlops.md).

---

## How it shows up in our project

- Retrieval code: [index.py](../../../code/business_entity_resolution/src/ber/block/index.py) (CSR, postings, partitions), [search.py](../../../code/business_entity_resolution/src/ber/block/search.py) (numba top-k).
- Hash-based folds: [splits.py](../../../code/business_entity_resolution/src/ber/eval/splits.py), `s1_hash_slice` in [common.py](../../../experiments/ameya/model-v1/common.py).
- Advanced pages: [02 blocking](../02-blocking.md), [10 LLM verification and compute](../10-llm-verification-and-compute.md), [11 scaling to billions](../11-scaling-to-billions.md).

## How to read the numbers

- **"27 GPU-hours".** It is a calculation from a measured speed (600 pairs per second), not a measured run. It excludes training and idle time.
- **Peak memory 16.5 to 19 GB.** The largest live set during a stage, not the output size. It sets the machine, not the run time.
- **58.4M versus 6.41M.** Different sets: retrieval output and the learned cut of it. Recall is measured on each separately (see the note in the [theory README](../README.md)).
- **Big-O hides constants.** A linear algorithm with a heavy constant (a transformer pass) can cost more than a quadratic one on small inputs. Compare actual rates.

## Common misconceptions

1. "More cores means proportionally faster." Amdahl: only the parallel part speeds up, and memory bandwidth is shared.
2. "A cluster is always the scalable choice." For data that fits one machine, the shuffle can cost more than it saves.
3. "Hashing sorts or orders keys." It scatters them; sorting needs a sort.
4. "LSH and HNSW are exact." They are approximate; recall must be measured.
5. "Parquet is a database." It is a file format; queries need an engine.
6. "A GPU is always faster." Only for large regular numeric work; small or branchy jobs run better on a CPU.
7. "Peak memory equals data size." Copies and intermediates often double or triple it.

## Check yourself

Exercise 1. How many pairs are there among 1M records? How long at $10^7$ comparisons per second on one core?

<details><summary>Answer</summary>

$10^6(10^6-1)/2 \approx 5\times10^{11}$ pairs. At $10^7$ per second: $5\times10^4$ s, about 13.9 hours.

</details>

Exercise 2. Why do we assign folds by hashing the S1 id instead of random numbers? What share lands in the holdout?

<details><summary>Answer</summary>

A hash is a pure function of the id, so every machine and every rerun gives the same fold with no stored table, and all pairs of an S1 share a fold. Folds 0 to 4 of 20 give 25%.

</details>

Exercise 3. Estimate the chance of any collision among $10^9$ keys hashed to 64 bits.

<details><summary>Answer</summary>

About $n^2/2^{65} = 10^{18}/3.7\times10^{19} = 0.027$, roughly 2.7%.

</details>

Exercise 4. Build the CSR arrays and the posting list for token 5 from $r_0=\{1,5\}$, $r_1=\{5,7\}$, $r_2=\{7\}$.

<details><summary>Answer</summary>

`indptr = [0,2,4,5]`, `codes = [1,5,5,7,7]`. Token 5 appears in $r_0$ and $r_1$, so its posting list is $[0,1]$.

</details>

Exercise 5. A token appears in 50,000 records. How many pairs would a naive join on it create? What does `seed_cap = 3000` do?

<details><summary>Answer</summary>

$50{,}000\times49{,}999/2\approx1.25\times10^9$ pairs. With the cap, that token never starts a candidate list, since its list is longer than 3000. It only helps re-score candidates found through rarer tokens.

</details>

Exercise 6. With $r=5$, $b=20$, compute the candidate probability for $s=0.8$ and $s=0.3$.

<details><summary>Answer</summary>

$s=0.8$: $0.8^5=0.328$, $1-(1-0.328)^{20}=0.9996$. $s=0.3$: $0.3^5=0.00243$, $1-(1-0.00243)^{20}=0.0475$.

</details>

Exercise 7. How much memory do $10^7$ vectors of 256 dimensions take in fp16? With 16-byte product-quantisation codes?

<details><summary>Answer</summary>

fp16: $10^7\times256\times2 = 5.12$ GB. PQ: $10^7\times16 = 160$ MB.

</details>

Exercise 8. How many GPU-hours would the 7B need for a candidate file twice as large as ours (12.8M pairs) at 600 pairs per second?

<details><summary>Answer</summary>

$12{,}820{,}616/600 = 21{,}368$ s, about 5.9 hours: twice the 2.97 hours for the actual file.

</details>

Exercise 9. 95% of a job parallelises. What is the speedup on 24 cores? With 1% serial work on 1000 cores?

<details><summary>Answer</summary>

$1/(0.05+0.95/24)=11.2$. With 1% serial and 1000 workers: $1/(0.01+0.99/1000)=91$. The serial part caps the gain at 100.

</details>

Exercise 10. A country column has 10M rows and 3 distinct values. How big is it dictionary-encoded?

<details><summary>Answer</summary>

Each row needs 2 bits (enough for 3 values): $10^7\times2/8=2.5$ MB, plus a tiny dictionary. Run-length encoding would shrink a sorted column further.

</details>

Exercise 11. Sanity check (with stated assumptions): a forward pass costs about $2\times$ parameters per token. For a pair of 40 tokens and 7.07B parameters, what rate in operations per second does 600 pairs per second imply?

<details><summary>Answer</summary>

$2\times7.07\times10^9\times40 = 5.7\times10^{11}$ operations per pair. Times 600 pairs per second: $3.4\times10^{14}$ per second, which is a large share of an H100's bf16 capability. So 600 is plausible and the job is compute-bound. The 40 tokens is an assumption; the real Qwen token count for our pairs was not measured here.

</details>

## Going deeper

- Dean and Ghemawat (2004). MapReduce: simplified data processing on large clusters.
- Zaharia et al. (2012). Resilient distributed datasets: a fault-tolerant abstraction for in-memory cluster computing.
- McSherry, Isard and Murray (2015). Scalability! But at what COST?
- Indyk and Motwani (1998). Approximate nearest neighbors: towards removing the curse of dimensionality. Broder (1997). On the resemblance and containment of documents.
- Malkov and Yashunin (2020). Efficient and robust approximate nearest neighbor search using hierarchical navigable small world graphs.
- Jégou, Douze and Schmid (2011). Product quantization for nearest neighbor search. Johnson, Douze and Jégou (2021). Billion-scale similarity search with GPUs.
- Kleppmann (2017). Designing Data-Intensive Applications. Hennessy and Patterson, Computer Architecture: A Quantitative Approach.
- Papadakis et al. (2020). Blocking and filtering techniques for entity resolution: a survey.

## Where next

- [F17 production ML and MLOps](F17-production-ml-and-mlops.md): serving, monitoring, reproducibility.
- [F13](F13-linear-algebra-and-optimisation.md): SVD and low-rank ideas behind the dropped GPU views.
- [11 scaling to billions](../11-scaling-to-billions.md) and [02 blocking](../02-blocking.md).
