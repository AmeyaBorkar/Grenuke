# F17. Entity resolution in production: systems, cost, monitoring and governance

**Summary.**
- A competition scores one file once. A production system resolves entities continuously, at a cost, with monitoring, human review and rules about data and licences. This page maps our pipeline onto that setting.
- It covers batch against incremental and streaming ER, candidate generation as a service, feature stores, cost and latency per stage (XGBoost, cross-encoder, 7B), drift monitoring (France is our live example), review queues, A/B tests, reproducibility and governance.
- It ends with what we would change to run our pipeline in production, and what we did not measure and so must not claim.

Tier P1. About 2.5 hours in full, about 1.25 hours on the fast path (sections 2.2, 2.5, 2.6, 2.8, 2.9 and 2.11). Prepares you for the advanced pages [11 scaling][adv11], [10 LLM verification and compute][adv10], [05 evaluation][adv05] and [09 self-training and domain shift][adv09].

---

## 1. What you need first

[F01][f01] (data and problem), [F03][f03] sections 2.8 and 2.9 (out-of-fold predictions, leakage) and [F04][f04] (metrics). [F08][f08] on computing at scale helps. Evidence levels: **M** measured, **E** estimated or derived, **R** reported. Statements about what a production system should do are design advice and general engineering practice. They are not claims about how any company, Amazon included, runs its systems. Where we did not measure something (online latency, review cost, A/B outcomes) this page says so.

---

## 2. The concepts from zero

### 2.1 From a file to a service

**Intuition.** In the challenge the input was fixed files and the output one file, scored once. A production system lives for years, takes in new records every day, answers other systems, and must be trusted, paid for and explained.

| aspect | challenge | production |
|---|---|---|
| input | fixed files | continuous feeds, schema changes, bad batches |
| output | one TSV | a versioned link store that other systems read |
| success | macro F0.5 on a hidden subset | service levels, business outcomes, cost |
| labels | ground truth for train | scarce, delayed, biased by who gets reviewed |
| change | frozen at the deadline | new markets, vendors and naming habits |
| accountability | a ranking | audits, privacy rules, licences, rollbacks |

**The shape of an ER service.** The stages of our pipeline, with an operating layer around them:

```
sources --> ingest and validate --> normalise (per locale)
                                         |
                              candidate service (one index per country)
                                         |
   pair scoring: cheap model -> cross-encoder (uncertain band only) -> LLM re-check (confident only)
                                         |
                    decision (set per entity, ownership) --> link store --> consumers
              ^                                                |
   review queue (uncertain pairs)  <---------------------------+
   monitoring: data, model, decisions, audit sample
```

### 2.2 Batch, incremental and streaming ER

- **Batch:** recompute all links over all records on a schedule. Simple, reproducible, easy to test; cost grows with everything and results go stale between runs. Our pipeline is batch.
- **Incremental:** when records arrive or change, update only the links they can affect. It needs a persistent index that accepts inserts, stable entity IDs, and a rule for recomputing the neighbourhood of a changed record (Gruenheid, Dong and Srivastava 2014).
- **Streaming:** per-event processing within seconds, with a shorter candidate lookup and approximate answers, reconciled by a batch job later.

| situation | fits |
|---|---|
| a nightly catalogue refresh | batch |
| new vendors linked within the hour | incremental |
| a sign-up form that warns "this business already exists" | streaming lookup, with batch reconcile |

**What helps us.** Our blocking already searches both ways: each S1's top records and each record's top S1 ([methodology 3][doc]). A new S2/S3 record can ask "who is my owner?", and a new S1 "who are my copies?". The output is **star-shaped**: every record attaches to at most one S1, with no chains of matches to close, which makes partitioning, parallel decisions and incremental updates simple ([scaling page 5][adv11]).

**What is hard.** The per-S1 decision is local, but **ownership couples S1s**: two S1 can compete for one record. A streaming system needs a rule for contested records: an owner pointer with the winning score, a challenger that replaces it only by a margin (to stop flip-flopping), and a periodic reconcile. Without a clean reference you also need **merges, splits and stable entity IDs** (aliases when two entities merge). Our task avoided that because S1 is a clean reference.

**Unit cost (our test run, scaled).** Per S1 the run did 33.7 cheap pair scorings, passed 0.86 pairs to the cross-encoders and re-read 3.2 predictions with the 7B [M] ([scaling page 2.3][adv11]). From the reported totals the 7B re-check cost about 7.5 ms of GPU time per S1 (3.6 GPU-hours [R]) and a 7B pass over the band about 1.4 ms (41 GPU-minutes [E]): roughly 2.5 H100-hours per million S1 [E]. Blocking (15 minutes on 64 vCPUs for 1.73M S1) is about 9 vCPU-hours per million S1, and pair features about 15 [E]. These exclude the XGBoost stages and the other cross-encoders.

### 2.3 Candidate generation as a service

**Definition.** A service that, given a record or an S1, returns K candidate IDs with ranks, within a latency budget, with a promised **recall at K**.

What our blocking teaches about running one ([blocking page][adv02], [scaling page 2.2][adv11]):
- **One index per country partition.** IDF weights and neighbours never mix countries, so a new market is a new partition with no code change.
- **Bounded posting lists.** Only tokens with short lists (a cap of 1,000 or 3,000 records) seed candidates. In a ten times larger partition the cap silently drops recall, so **monitor recall per view and per country**.
- **Several views.** A token view, a names-only view (4-grams) for empty addresses, and name repairs; their union is more robust than any one.
- **Hot keys.** Generic names ("lille club sarl" is shared by dozens of S1) make giant blocks. Remedies: purge oversized lists, compound keys such as (house number, street word).
- **Approximate indexes** (HNSW, product quantisation) trade recall for speed: measure each against exact search on a sample ([scaling page 6][adv11]).
- **Updates.** Append new records to small segments and merge them in the background, so queries never wait for a rebuild.

**The ratio that drives cost.** Pairs scored scale as (number of entities) × K, so **candidates per entity** is the cost lever. Ours: 33.7 per S1 at retrieval, 3.70 after the learned cut ([methodology 3][doc]). The organisers' ranking rewarded fewer candidate pairs per record ([finale brief][finale]).

### 2.4 Features, feature stores and training-serving skew

A **feature store** computes, stores and serves features in one place, so training (historical values, as they were then) and serving (current values, fast) share definitions. It prevents **training-serving skew** (a feature computed one way offline and another online) and time leakage (using the future).

| our feature group ([methodology 4][doc]) | depends on | production implication |
|---|---|---|
| name, address, house number | the pair only | easy to compute online |
| context: ranks in each view, gaps to the best candidate and to rival S1, name-collision counts, per-S1 aggregates | the whole candidate pool | change whenever a competing record arrives; recompute or refresh |
| corpus statistics: IDF per country, look-alike word odds | a country partition, and labels | version them; refresh on a schedule, never silently |

**A skew built in by design.** Stage 2 trains on out-of-fold stage-1 scores but serves scores from a model trained on all folds ([F03][f03] section 2.8, [CONTRACTS C2][contracts]). That is standard stacking, but it is a known training-serving difference: document and test it.

### 2.5 Cost and latency by stage

**The cascade formula.** If a share πk of pairs reaches stage k at cost ck per pair, the cost per retrieved pair is `C = Σ πk × ck` ([LLM page 2.1][adv10]). Spend where the decision can change.

**Our cascade on the test set** ([LLM page 4][adv10], [scaling page 2.3][adv11]):

| stage | pairs | reader | cost |
|---|---|---|---|
| retrieval | 58.4M | IDF token search per country | about 15 minutes on 64 vCPUs [R] |
| stages 0 and 1 | 58.4M, then about 15 to 20% survive | XGBoost, 200 trees then deeper | about 4 minutes [R] |
| stages 2 and 3 | the candidates, 6.41M | XGBoost with context features | minutes to score [R] |
| cross-encoders | 1,490,930 band pairs | e5, bge, Qwen2.5-1.5B and 7B | e5-large trio about an hour on one H100 [R]; 7B about 2 hours on three H100s, training included [R] |
| 7B re-check | 5,614,414 confident predictions | Qwen2.5-7B | about 3.6 GPU-hours [R] |
| 7B on every retrieved pair (not done) | 58.4M | Qwen2.5-7B | about 27 GPU-hours at 600 pairs/s [E] |

**Why the cascade pays.** At the measured 600 pairs per second on an H100, the 7B over all 58.4M retrieved pairs takes 27.1 hours; over the 1.49M band pairs, 0.69 hours (41 minutes): a factor of 39. Over the 6.41M candidates it would take 3.0 hours.

**Throughput is not latency.** 600 pairs per second is a rate for a saturated, batched GPU. A single online request with a handful of pairs cannot fill a batch, so its latency is set by batching delay, queueing and model load. The re-check totals imply only about 430 pairs per second (5.6M pairs in 3.6 hours), so the rate depends on input length, batch and hardware. Quote measured totals, and measure p50 and p99 latency under load before promising anything. **We did not measure online latency.**

**Memory.** The weights of a 7.6B-parameter model in 16-bit numbers take about 15 GB (7.6e9 × 2 bytes) [E], before activations. The XGBoost stages needed 24 or more cores and 32 GB of RAM; the cross-encoders ran on one 80 GB card ([methodology appendix][doc]).

**Options we did not use.** Distilling the 7B into a smaller model (Hinton et al. 2015); lower-precision weights; caching scores by a hash of the two texts, so unchanged pairs are never rescored; routing, where a cheap model answers first and the expensive one only when unsure (the idea behind our cascade; Chen, Zaharia and Zou 2023). Each needs its own gate: the F0.5 lost against the cost saved.

**At a billion records** (about 148M S1, 85 times our test) our measured costs scale to about 5.0B retrieved pairs, 550M candidates, 127M band pairs, and 220 to 310 GPU-hours for the re-check [E] ([scaling page 2.3][adv11]).

### 2.6 Monitoring and drift

**Definitions.** **Data drift:** the inputs change (a new country, a larger pool, a new vendor format). **Concept drift:** the right answer for the same input changes (businesses rename). **Performance drift** needs labels to see. The kinds of shift are explained in [F10][f10].

**What to watch**, by slice (country, source, script) and not only in total:

| layer | signals |
|---|---|
| data | records per source and country; empty and `<NULL>` rates; script mix; records per S1; share of unseen tokens |
| model | score distribution; share of pairs in the uncertain band; disagreement between models; summed probability per S1 against the expected number of copies |
| decisions | predictions per S1; empty-answer rate; records with several claimants; ownership flips |
| outcomes | audit-sample precision; review overrides; complaints |

A global average hides a new market: France was 15% of test S1, so a problem confined to France shows up in a global rate at 15% of its size.

**Label-free signals that worked for us in France** (all [M]):
- the summed probability per S1 matched the truth in US/India (3.4320 against 3.4323) and read 3.5456 in France: overconfidence ([evaluation page 2.8][adv05]);
- two cross-encoders disagreed about four times as often in France ([methodology 4][doc]);
- the 7B rejected 0.10% of French confident predictions (859 of 870,019) against 0.0065% in US/India (310 of 4,744,395): 15 times the rate ([LLM page 4][adv10]).

**Response playbook** (design advice): stop automatic merging for the slice (raise the cut-off), route its uncertain pairs to review, collect labels, retrain, and release behind a canary. **Replace pseudo-labels with human labels as soon as they exist.** Our own self-training helped for two rounds and not for a third, and a leave-one-country-out ladder drifted (0.882, 0.851, 0.831, 0.823 over successive rounds) [M] ([evaluation page 2.8][adv05], [F10][f10]).

### 2.7 Human review queues

**Design.** Split pairs by confidence: **auto-accept** above a high cut-off, **auto-reject** below a low one, **review** in between. The review budget sets how wide the middle band is. Rank the queue by expected saving: the chance the model is wrong, times the cost of the error, per second of reviewer time. Show both records side by side with differences highlighted, and decide whether to show the model's score (it speeds reviewers and can anchor them).

**Our analogue.** The uncertain band 0.02 ≤ p1 ≤ 0.99 holds 1,490,930 test pairs, 0.86 per S1 [M]. A human queue would take a thin slice of it.

**Worked example (toy assumption: 20 seconds per pair).** Review hours = pairs × seconds ÷ 3,600. Reviewing 0.1% of the band is 1,491 pairs, 8.3 hours. Reviewing 1% is 14,909 pairs, 83 hours. We have no measured review cost.

**Cautions.** Reviewed pairs are not a random sample, so keep a **separate random audit sample** for unbiased metrics. Measure agreement between reviewers, because labels are noisy. Store each decision as a must-link or cannot-link constraint that the pipeline honours in later runs, or the same pair returns next week. Choosing the pairs that teach the model most is active learning ([F16][f16]).

### 2.8 Offline metrics, online metrics and A/B tests

**Offline** (our macro F0.5 on a labelled holdout) is cheap and repeatable, but static and limited to what was labelled. **Online** metrics are business outcomes: duplicate rate in the catalogue, wrong-merge complaints, review workload, downstream conversion. How offline F0.5 relates to them is an empirical question.

**A ladder for a new model:**
1. **Offline** on the holdout with a paired bootstrap ([F02][f02]).
2. **Shadow mode:** run beside the current model without acting; send disagreements to review to learn who is right.
3. **Canary:** act on a small slice, with rollback.
4. **A/B test:** randomise at the **entity** level (an S1 with its candidate records) or by market, because records that compete for one S1 interfere if randomised per record. Plan the sample size with a power calculation, fix guardrail metrics beforehand, and do not peek.

**Audit samples for precision.** To estimate a precision near 99.9% to within ±0.1 point at 95% confidence you need about n = 1.96² × p(1 − p) / h² = 3,838 labelled predictions [E]; ±0.05 point needs about 15,350. Use a Wilson interval near 1 ([F02][f02] section 2.8). Recall is harder: it needs labels from outside the predicted set, so sample the candidate set and the near-miss bands.

**Choosing the cost ratio.** Instead of a β, set explicit costs. If a false merge costs `C_FP` and a missed link `C_FN`, predict a match when `p > C_FP / (C_FP + C_FN)`. With the weights of the F0.5 count form (1 and 0.25) this is 0.8, the large-set limit of our break-even ([F04][f04] section 2.7). If the business says a wrong merge costs ten missed links, the cut-off is 0.91.

### 2.9 Reproducibility, versioning and lineage

**What to version:** code (git commit), data snapshot (immutable path or hash), configuration, environment (pinned requirements, container image), seeds, model artifacts (in a registry) and outputs.

**What we do** ([AGENTS.md][agents], [CONTRACTS][contracts], [methodology appendix][doc]):
- artifacts live under `work/<stage>/<tag>/` with a documented schema; tags are `<member>-<stage>-v<N>`; IDs are integers; nothing relies on row order;
- every artifact records the command and git commit that made it; seeds are fixed; `output/` holds the exact bytes we submitted;
- the output validator is a **data contract check**: one row per S1, only existing S2/S3 IDs, no duplicates, matches a subset of candidates;
- tests lock the fold assignment for known IDs, so splits are identical on every machine ([`ber.eval.splits`][splits]).

**Determinism has limits.** CPU stages are deterministic given fixed seeds and hash-based folds. GPU training is not bit-identical across machines: an earlier model rebuilt on other hardware moved the holdout from 0.991246 to 0.991261 [M], stage 3 differs in about 500 test decisions between machines [M], and a rerun should land within about 0.0001 [R] ([evaluation page 2.4][adv05]). Define reproducibility as "within a tested tolerance" and keep the released bytes.

**Promotion path:** development, shadow, canary, full release, with a rollback target. Write tests in four families (Breck et al. 2017): data, model, infrastructure and monitoring.

### 2.10 Governance, licences, privacy and safety

- **Licences.** The final pipeline uses only models under MIT or Apache-2.0 with at most 8B parameters: multilingual-e5 (MIT), bge-reranker-v2-m3 (Apache-2.0), Qwen2.5-1.5B and 7B (Apache-2.0) ([methodology 4 and appendix][doc]). In production keep a bill of materials for models and data, and check **each checkpoint's** licence: licences can differ between sizes of one family.
- **Data provenance.** The challenge banned external lookups, geocoders and web data, and we used only the provided files. Production keeps the discipline: know where every input came from, under what terms, and what happens when a source withdraws a record (derived links must go).
- **Privacy.** Names and addresses of sole traders can be personal data under laws such as the GDPR (France is in the EU). We are not lawyers: involve them for retention, access control, deletion and data residency.
- **Fairness across slices.** Report errors per country and per script. Our per-country breakdown is the start.
- **Untrusted text.** Record text is untrusted input; a name could contain instructions aimed at a language model. Keep the model a scorer with a constrained output (ours returns a logit used against a fixed cut-off), give it no tools, and watch its score distribution. We did not test adversarial text.
- **Reversible actions.** Merges are hard to undo. Store links, not merged records; require more confidence to auto-merge than to suggest; keep an unmerge path.
- **Documentation.** Model cards (Mitchell et al. 2019), datasheets (Gebru et al. 2021), decision records (`docs/decisions/`) and the methodology document are the audit trail.

### 2.11 What we would change to run this in production

| area | our pipeline | production change |
|---|---|---|
| mode and ownership | batch; argmax ownership at the end | incremental index with owner lookups, a claim protocol with a margin, a nightly reconcile |
| statistics | per-country IDF fitted on train and test | versioned statistics with a refresh policy |
| new markets | self-training on our own decisions | human labels as soon as available; self-training only to bootstrap |
| cost | cross-encoders and 7B on the band and re-check | distillation, caching, routing; cost per 1,000 records as a metric |
| rules and cut-offs | hand-written France rules; +0.2, −0.3, 0.01 and −6 tuned once | locale modules with tests per market; cut-offs retuned on rolling audit labels, with change control |
| monitoring and humans | label-free checks by hand; no reviewers | slice dashboards and alerts; a review queue on a thin band; overrides kept as constraints |
| evaluation | holdout and leaderboard | shadow, canary, entity-level A/B tests, a random audit sample |
| reproducibility | seeds, commits, exact bytes | container images, pinned drivers, a model registry, tolerance tests |

**What we would keep:** the per-S1 expected-F0.5 decision (stateless, cheap, easy to serve), the cascade principle, per-country partitions, and the discipline of paired tests and written gates.

---

## 3. How it shows up in our project

- **Scale and cost:** per-stage complexity and the billion-record table in [11 scaling][adv11]; the cascade and the re-check in [10 LLM verification and compute][adv10].
- **Drift and unlabelled markets:** France in [09 self-training and domain shift][adv09]; the label-free diagnostics in [05 evaluation][adv05].
- **Reproducibility and contracts:** [AGENTS.md][agents], [CONTRACTS][contracts], [DEVELOPMENT](../../../docs/DEVELOPMENT.md) and the [package README](../../../code/business_entity_resolution/README.md).
- **Governance:** the licence and no-external-data rules in the [problem statement][task] and AGENTS.md section 3; the licence table in the [methodology][doc].

---

## 4. How to read the numbers

| number | scope and level | what it tells you | what it does not tell you |
|---|---|---|---|
| 58.4M, 6.41M, 3.70 per S1 | test retrieval, candidate file [M] | the cost driver, pairs per entity | final accuracy |
| 1.49M, 0.86 per S1 | pairs in the uncertain band [M] | how many pairs need the expensive readers | which reader is best |
| 600 pairs/s, 27 GPU-hours | 7B on an H100, all retrieved pairs [E] | why we did not read every pair | online latency; the re-check implies about 430 pairs/s |
| 3.6 GPU-hours | the 7B re-check of 5.6M predictions [R] | its cost | its benefit (+0.000037 on the holdout) |
| about 2.5 H100-hours per million S1 | the two 7B steps, scaled [E] | a unit cost | the full cost: XGBoost stages and other cross-encoders are excluded |
| 0.991246 to 0.991261 | same model on other hardware, holdout [M] | GPU noise | that the code is wrong |
| 0.10% against 0.0065% | 7B rejects, France and US/India, test [M] | a drift signal | which rejects are right |
| about 4 times as often | cross-encoder disagreement, France against others [M] | a drift signal | the size of the error |
| 3,838 | audit sample for ±0.1 point at precision 99.9% [E] | the sample size to plan for | recall |

---

## 5. Common misconceptions

1. **"Production is the notebook on a schedule."** The model is the small part. Data checks, serving, monitoring, review, rollback and governance are most of the work (Sculley et al. 2015).
2. **"A higher offline F0.5 means a better product."** It means a better score on labelled data. The online effect must be measured.
3. **"More candidates are safer."** Cost scales with candidates per entity. The learned cut from 33.7 retrieved to 3.70 candidates per S1 left holdout F0.5 level when it was measured (−0.000003, on an earlier model chain), while the later stages see about a ninth of the pairs ([scaling page 2.1][adv11]).
4. **"The biggest model should read every pair."** That was 27 GPU-hours against 41 minutes for the band.
5. **"You cannot monitor without labels."** You can watch slices of inputs, scores, disagreement and totals, and keep a small random audit sample.
6. **"Retraining on a schedule fixes drift."** Retraining on your own outputs reinforces them; drift needs new information.
7. **"Reproducible means bit-identical."** On GPUs it means within a tested tolerance, with the released bytes kept.
8. **"Open weights mean free to use anywhere."** Licences differ by checkpoint and by use.
9. **"A throughput figure is a latency figure."** Latency includes batching, queueing and cold starts.

---

## 6. Check yourself

**1.** At 600 pairs per second, how long does the 7B need for (a) 6,410,308 candidate pairs, (b) 1,490,930 band pairs? Why is the reported re-check cost of 3.6 GPU-hours for 5.6M pairs not simply pairs ÷ 600?

<details><summary>Answer</summary>

(a) 6,410,308 / 600 = 10,684 s = 3.0 hours. (b) 1,490,930 / 600 = 2,485 s = 41 minutes. For the re-check, 5,614,414 / 600 would be 2.6 hours, but 3.6 GPU-hours was reported, an effective 430 pairs per second. Throughput depends on input length, batch size and hardware, so quote measured totals, not a single rate.

</details>

**2.** A toy cascade has three stages. Stage A costs 1 unit per pair and sees all pairs. Stage B costs 1,000 and sees 2.5% of pairs. Stage C costs 10,000 and sees 2.5%. What is the cost per pair, and how does it compare with running C on everything?

<details><summary>Answer</summary>

1 + 0.025 × 1,000 + 0.025 × 10,000 = 1 + 25 + 250 = 276 units per pair. Running C on everything costs 1 + 10,000 = 10,001, 36 times more. The saving comes from the 2.5% share, and is worth it only if B and C change decisions on that share.

</details>

**3.** A new record arrives and its owner is S1-7 with a score of 0.91. Later a new S1-9 scores 0.93 for the same record. What should happen?

<details><summary>Answer</summary>

A record has at most one owner, so the two S1 are coupled. Use a margin rule: a challenger replaces the incumbent only if it wins by more than a set margin. With a margin of 0.05, S1-7 keeps the record (the lead is 0.02), and the pair is queued for the nightly reconcile or for review. The margin stops links from flipping with every small score change.

</details>

**4.** You open a new market with no labels. List five label-free monitors and what each tells you.

<details><summary>Answer</summary>

(1) Records per S1 and the empty-address rate: pool-size and format shift. (2) Share of pairs in the uncertain band: how unsure the model is. (3) Disagreement between two independent models: where errors are likely (four times higher in France). (4) Summed probability per S1 against the expected number of copies: overconfidence (3.5456 in France against 3.4320 to 3.4323 where labels exist). (5) Rate at which a second reader (the 7B) rejects confident predictions, by country: possible decoys (15 times higher in France). Keep a small random audit sample to anchor them.

</details>

**5.** How many labelled predictions do you need to measure a precision of about 99.9% to within ±0.1 point at 95% confidence? Which interval should you use?

<details><summary>Answer</summary>

n = 1.96² × 0.999 × 0.001 / 0.001² ≈ 3,838. Near 1 the normal interval misbehaves, so use a Wilson interval ([F02][f02]). To halve the half-width you need four times as many labels.

</details>

**6.** Reviewing 0.5% of the 1,490,930 band pairs at 15 seconds a pair: how many pairs and how many hours? What bias does the resulting label set have?

<details><summary>Answer</summary>

0.005 × 1,490,930 = 7,455 pairs; × 15 s = 111,825 s = 31 hours. The labelled pairs are the uncertain ones, not a random sample, so precision measured on them is not the precision of the system. Use a separate random audit sample for metrics.

</details>

**7.** Why should an A/B test of a new matcher randomise at the entity level and not per record?

<details><summary>Answer</summary>

Records compete for the same S1, so records of one S1 in different arms interfere: the old model could give one record to S1-7 while the new one gives another record to S1-7, and the outcome belongs cleanly to neither arm. Randomising whole entities (an S1 with its candidates) or whole markets keeps each decision inside one arm.

</details>

**8.** The same model scores 0.991246 on one machine and 0.991261 on another. Is that a bug? How would you test reproducibility?

<details><summary>Answer</summary>

No. GPU training is not bit-identical across hardware, and a difference of 0.000015 is within the training noise we saw (1.5 to 4e-5). Test with a tolerance (we quote about ±0.0001), fix seeds, keep the released output bytes, and compare decisions, not only the headline score.

</details>

**9.** A business says a wrong merge is ten times as costly as a missed link. What cut-off follows, and how does it compare with F0.5?

<details><summary>Answer</summary>

Predict a match when p > C_FP / (C_FP + C_FN) = 10 / 11 = 0.91. F0.5's count weights (1 and 0.25) give 1 / 1.25 = 0.8. So this business wants a more cautious system than F0.5 asks for, and you would tune the decision to its cost ratio rather than to β = 0.5.

</details>

**10.** A teammate wants to add a new open model to a production pipeline built under our rules. Which checks come first?

<details><summary>Answer</summary>

The licence of that exact checkpoint (MIT or Apache-2.0 under our rules; sizes of one family can differ), the parameter count (at most 8B), the origin of any data it was trained or tuned on (no external lookups in our task), a gate showing a gain on the holdout with a paired bootstrap, a measured cost per pair, and an entry in the bill of materials and in the decision records.

</details>

---

## 7. Going deeper

- Sculley et al. (2015), "Hidden technical debt in machine learning systems", NeurIPS.
- Breck, Cai, Nielsen, Salib and Sculley (2017), "The ML test score: a rubric for ML production readiness and technical debt reduction", IEEE Big Data.
- Kleppmann (2017), "Designing Data-Intensive Applications", O'Reilly. Batch, streams, indexes and consistency.
- Huyen (2022), "Designing Machine Learning Systems", O'Reilly. Monitoring, drift and deployment.
- Kohavi, Tang and Xu (2020), "Trustworthy Online Controlled Experiments", Cambridge University Press.
- Quiñonero-Candela, Sugiyama, Schwaighofer and Lawrence (2009), "Dataset Shift in Machine Learning", MIT Press.
- Gruenheid, Dong and Srivastava (2014), "Incremental record linkage", PVLDB; Papadakis, Skoutas, Thanos and Palpanas (2020), "Blocking and filtering techniques for entity resolution: a survey", ACM Computing Surveys.
- Hinton, Vinyals and Dean (2015), "Distilling the knowledge in a neural network"; Chen, Zaharia and Zou (2023), "FrugalGPT: how to use large language models while reducing cost and improving performance".
- Mitchell et al. (2019), "Model cards for model reporting", FAT*; Gebru et al. (2021), "Datasheets for datasets", Communications of the ACM.

## 8. Where next

- [F08 Computing at scale][f08]: the cost model and parallel patterns behind section 2.5.
- [F09 Experiments and evidence][f09]: gates, holdouts and what makes a comparison trustworthy.
- [F10 Semi-supervised learning and domain shift][f10] and [F16 Learning with limited labels][f16]: new markets and review loops.
- [F12 Interpreting our results][f12]: defending the numbers.
- Advanced pages [11 scaling][adv11], [10 LLM verification and compute][adv10], [05 evaluation][adv05], [09 self-training and domain shift][adv09].
- The track map: [foundations README](README.md).

[doc]: ../../../experiments/ameya/final-zip/doc/Documentation_template.md
[task]: ../../../student_resource/README.md
[agents]: ../../../AGENTS.md
[contracts]: ../../../docs/CONTRACTS.md
[splits]: ../../../code/business_entity_resolution/src/ber/eval/splits.py
[finale]: ../../../finale/README.md
[adv02]: ../02-blocking.md
[adv05]: ../05-evaluation-methodology.md
[adv09]: ../09-self-training-and-domain-shift.md
[adv10]: ../10-llm-verification-and-compute.md
[adv11]: ../11-scaling-to-billions.md
[f01]: F01-data-and-problem.md
[f02]: F02-probability-and-statistics.md
[f03]: F03-machine-learning-fundamentals.md
[f04]: F04-classification-metrics.md
[f08]: F08-computing-at-scale.md
[f09]: F09-experiments-and-evidence.md
[f10]: F10-semi-supervised-and-domain-shift.md
[f12]: F12-interpreting-our-results.md
[f16]: F16-learning-with-limited-labels.md
