# Entity resolution: the problem, the classic pipeline, and where we sit

**Summary.** Entity resolution (ER) decides which records describe the same real-world thing when no shared identifier exists. This page covers the classic pipeline, the Fellegi–Sunter model that still underlies the field, the move from rules to probabilities to learned and deep models, and the special structure of our task: a clean reference source, 0 to 11 copies per entity, and every copy owned by at most one entity. It ends with where our solution sits.

Related pages: [blocking](02-blocking.md), [string similarity](03-string-similarity.md), [metrics and decisions](04-metrics-and-decisions.md), [evaluation](05-evaluation-methodology.md), [boosting](06-gradient-boosting-and-stacking.md), [cross-encoders](08-transformers-and-cross-encoders.md), [glossary](glossary.md).

---

## 1. Intuition

A person sees at once that "Bright Voya LP, 42 Main St, Andover MA" and "BRIGHT VOYA L.P. | 42 MAIN STREET, ANDOVER" are the same business. A program must make that call for about 10 million records, through typos, abbreviations, Indic scripts and missing fields, and against **decoys** the data generator built to look similar: "Bright Voya Holdings, 44 Main St" is a different business.

Every ER system answers three questions:
1. **Which pairs do we look at?** Comparing everything with everything is impossible at this size. This is **blocking** (candidate generation).
2. **How alike is each pair?** This is **comparison**: similarity features, or a model that reads both records.
3. **What do we output?** A **classifier** turns evidence into a match probability, and a **decision** step turns probabilities into an answer that respects the structure of the problem and the metric.

The hard cases are not the obvious copies. They are the pairs that look almost right: a common name at another address, or the right address with one business word swapped.

## 2. Formal definition

**The task** ([official README][task]). Source A = S1, the reference, already deduplicated. Source B = S2 ∪ S3. There is an unknown set of true pairs M ⊆ A × B. For each a ∈ A we output P(a) ⊆ B, which should equal T(a) = {b : (a, b) ∈ M}.

**Structure of our data** (train, [M], [FINAL_PLAN §1][plan]):
- |T(a)| runs from 0 to 11, mean 3.46; 5.6% of S1 have no copy (**singletons**).
- **Every S2/S3 record belongs to at most one S1**: 0 violations in 7,638,365 true pairs. M is a partial function from B to A.
- No pair crosses countries; 26% of S2/S3 records match nothing (**orphans**).
- 46% of US and 54% of India S1 share their exact core name with another S1.

**The classic pipeline** (Christen 2012): preprocess → block → compare → classify → cluster or assign → evaluate. Preprocessing and comparison are linear in what they touch; blocking exists because the cross product is not. On our test set it is 1,732,544 S1 × 9,969,589 S2/S3 ≈ 1.7 × 10¹³ pairs [E, counted from the test files].

### 2.1 Fellegi–Sunter: probabilistic record linkage

Fellegi and Sunter (1969) gave ER its first theory. For a pair, compute a **comparison vector** γ, for example (names agree, house numbers agree, city agrees), and define

```
m(γ) = P(γ | match)      u(γ) = P(γ | non-match)      R(γ) = m(γ) / u(γ)   (likelihood ratio)
```

- **Decision rule:** link if R ≥ T_upper, non-link if R ≤ T_lower, and send the band between them to clerical (human) review.
- **Optimality:** for fixed error rates μ = P(link | non-match) and λ = P(non-link | match), ordering pairs by R with two thresholds gives the smallest review band. It is the record-linkage cousin of the Neyman–Pearson lemma.
- **Conditional independence** of fields given match status turns log R into a sum of **match weights**: w_k = log(m_k/u_k) when field k agrees, and log((1 − m_k)/(1 − u_k)) when it disagrees.
- **Value-specific weights:** agreeing on a rare value is stronger evidence, because u is the chance that two non-matching records share it by accident. With u_t ≈ df_t / N for a token t, the agreement weight is log m_t + log(N / df_t). **The second term is inverse document frequency (IDF)**, so our blocking score is in effect a normalised sum of Fellegi–Sunter agreement weights ([02](02-blocking.md)).
- **Estimation without labels:** P(γ) = π·m(γ) + (1 − π)·u(γ) is a two-class mixture, fitted with EM (Jaro 1989). u can also come from random pairs, which are almost all non-matches.

**A worked illustration with our numbers.** Among records close to an S1 on name and street words, the first house number is equal in 85% of true pairs but in only 12% of look-alike orphans [M] ([FINAL_PLAN §1, #9][plan]). Against look-alikes the weights are ln(0.85/0.12) ≈ +1.96 for agreement and ln(0.15/0.88) ≈ −1.77 for disagreement. "The record adds a name word" occurs in 23% of true pairs and 77% of look-alikes: ln(0.23/0.77) ≈ −1.21. Under independence, equal numbers and no added word give +1.96 + 1.21 = +3.17, a likelihood ratio of about 24. This is only an illustration: the real evidence lives in combinations of fields.

**The bridge to classifiers.** By Bayes' rule, logit P(match | γ) = log R(γ) + log(π / (1 − π)). A calibrated classifier estimates the left side directly. Fellegi–Sunter with conditional independence is exactly **naive Bayes**; a gradient-boosted model is Fellegi–Sunter without the independence assumption. It can learn that "same name and street, but a nudged house number" means a look-alike, which no sum of per-field weights can express.

### 2.2 Deterministic, probabilistic, learned

| family | decides by | strength | weakness |
|---|---|---|---|
| **deterministic** (rules) | exact or normalised keys, hand-written conditions | transparent; very precise on a narrow population | brittle; misses every variation not foreseen |
| **probabilistic** (Fellegi–Sunter, EM) | likelihood ratio of field agreements | no labels needed | independence assumption; coarse agreement levels |
| **learned** | a classifier on similarity features (Magellan) or on raw text (DeepMatcher, Ditto, LLMs) | captures interactions; best with labels | needs labels; can be miscalibrated in a new domain |

We used all three where each was strongest. The French `copy` rule (same name up to legal form and word order, exact same address) is deterministic and 99.992% (US) / 99.998% (India) precise on labelled data [M] ([stacked-rules record][stack]). The bulk of decisions is learned, and the final selection is decision-theoretic ([04](04-metrics-and-decisions.md)).

### 2.3 The shape of the answer

| setting | constraint | typical tool |
|---|---|---|
| two deduplicated files (census to census) | **one-to-one** | linear assignment, e.g. the Hungarian method (Kuhn 1955); Jaro (1989) used an assignment step |
| noisy sources against a clean reference (**ours**) | **one-to-many**: an S1 owns 0–11 records, a record has at most one owner | per-record choice of owner, then a set per entity |
| one dirty file | **many-to-many** | clustering |

Exclusivity is a strong signal: if two S1 compete for a record, at most one is right. We enforce it with **argmax ownership**, keeping each record only under its highest-probability S1 ([04](04-metrics-and-decisions.md)). The Hungarian method would allow one record per S1 and cap pair recall near 27% (0.944 of the 3.46 copies per S1) [E].

### 2.4 Transitivity and clustering

In deduplication, pairwise decisions must form a consistent partition. **Transitive closure** (connected components) is simple, but one false link chains two clusters together. **Star or centre clustering** grows clusters around centres. **Correlation clustering** (Bansal, Blum and Chawla 2004) picks the partition that disagrees least with the pairwise scores; it is NP-hard and solved approximately.

Our structure removes most of this. S1 is clean and each record has at most one owner, so the answer is one **star** per S1, and nothing can chain across S1. Transitivity still enters softly through the **cluster-support** feature: the maximum over the S1's other candidates R′ of p1(S1, R′)·sim(R, R′) ([FINAL_PLAN §4.6][plan]). Exact duplicates (same raw name, address and country) always share an S1 in train: 43,910 of 43,910 groups [M] ([ANALYSIS_v3 §6][a3]).

### 2.5 Active learning

With scarce labels, **active learning** asks a human to label the pairs the model is least sure about, or those on which a committee of models disagrees (Sarawagi and Bhamidipaty 2002; Arasu, Götz and Kaushik 2010). A few hundred well-chosen labels can beat thousands of random ones, because most random pairs are trivial non-matches.

US and India had 7.6M labelled true pairs, so we did not need it. France had no labels; we did not hand-label French pairs for training and read samples only for error analysis. Our label-free substitute was **self-training**, the mirror image of active learning: the model labels its own confident French pairs and leaves the uncertain middle unlabelled ([09](09-self-training-and-domain-shift.md)).

### 2.6 Modern learned and deep ER

- **Magellan** (Konda et al. 2016): blocking, automatic similarity features and classic classifiers in one toolkit. Our XGBoost stages on about 100 designed features belong to this family.
- **DeepMatcher** (Mudgal et al. 2018): attribute embeddings summarised by RNNs or attention; deep models help most on textual, dirty data.
- **Ditto** (Li et al. 2020): fine-tune a pre-trained transformer as a **cross-encoder** on a serialised pair. Our e5, bge and Qwen cross-encoders read "name ; address" of both records, cut to 96 tokens ([08](08-transformers-and-cross-encoders.md)).
- **LLM matching** (Narayan et al. 2022; Peeters, Steiner and Bizer 2025): prompt or fine-tune a large language model. Ours is a LoRA-tuned Qwen2.5-7B, used in the stage-2 mix and as a re-checker of confident predictions ([10](10-llm-verification-and-compute.md)).

Cost decides how they can be used: at the roughly 600 pairs per second we measured for the 7B on an H100, all 58M retrieved test pairs would take about 27 GPU-hours [M] ([methodology §2.2][doc]). Deep models must sit behind cheap filters.

## 3. Variants

- **Record linkage** (two sources), **deduplication** (one source), **reference matching** (ours).
- **Supervised, unsupervised or zero-shot**: Fellegi–Sunter with EM and ZeroER (Wu et al. 2020) need no labels; LLMs can match zero-shot.
- **Collective ER** (Bhattacharya and Getoor 2007): decisions depend on each other. Our stage 2 is a mild form: it sees each pair's rivals over the whole candidate graph.
- **Bayesian ER** (Sadinle 2017): a posterior over matchings. **Streaming ER**: records arrive continuously ([11](11-scaling-to-billions.md)).

## 4. Where we used it

| classic stage | what we built | code and records | page |
|---|---|---|---|
| preprocess | blocking tokenizer (accent folding, legal forms, street types, ordinals, department → region), Indic transliteration, name repairs | [`text.py`][text], [`indic.py`][indic], [`repair.py`][repair] | [03](03-string-similarity.md) |
| block | per-country IDF token search in both directions, a names-only view, a learned cut to 3.70 per S1 | [`ber/block`][blockpkg], [candidate-cut record][cut] | [02](02-blocking.md) |
| compare | about 100 pair features; cross-encoders on the 1.49M uncertain test pairs | [`feats.py`][feats], [FEATURES.md][feat] | [03](03-string-similarity.md), [08](08-transformers-and-cross-encoders.md) |
| classify | XGBoost stages 0–3, out-of-fold, isotonic calibration | `experiments/ameya/model-v1/s1.py`, `s2.py`, `stage3.py` | [06](06-gradient-boosting-and-stacking.md), [07](07-calibration.md) |
| assign | argmax ownership; the expected-F0.5 set per S1 | [`decide.py`][decide], [`stack/core.py`][core] | [04](04-metrics-and-decisions.md) |
| post-process | France rules, acronym join, the 7B re-check | `post_ops.py`, `acr_join.py`, [stacked rules][stack] | [09](09-self-training-and-domain-shift.md), [10](10-llm-verification-and-compute.md) |
| evaluate | macro F0.5 on a fixed 25% S1 holdout, paired bootstrap, label-free France checks | [`ber/eval`][metric] | [05](05-evaluation-methodology.md) |

Who: Ameya built blocking, the pipeline and the decision layer; Bakshi built normalisation v0, the first pair features and the Qwen2.5-7B parts; Sachi ran the first gates (G4, G6) and built the Qwen2.5-1.5B cross-encoder ([TEAM.md][team]).

## 5. Why it fits this problem

- **Names collide** for half of all S1, so the address must break ties. That rules out name-only blocking and name-only matching.
- **Decoys sit at the true address** with one word swapped or the number nudged. Their signature is an interaction of fields, which favours a learned model over independent weights.
- **The reference is clean and ownership is exclusive**, so the output is stars. Assignment replaces clustering.
- **The metric is per entity and precision-heavy**, so the last step chooses a set per S1 rather than applying one pairwise threshold.
- **France has no labels**, so every learned part needs a label-free check and a plan for domain shift.

## 6. Pitfalls

- **Learning evidence on the wrong population.** u from random pairs makes name agreement look decisive; after blocking nearly every candidate shares a name token. We trained on candidate pairs.
- **Transitive closure chaining** in dirty-file deduplication.
- **Assuming one-to-one** when entities have many copies.
- **Forgetting the empty answer:** 5.6% of S1 have no copy, and an empty prediction on them scores a full 1.0.
- **Scoring pairs when the metric scores entities:** pair accuracy can rise while macro F0.5 falls ([04](04-metrics-and-decisions.md)).
- **Splitting by pair instead of by entity**, which leaks ([05](05-evaluation-methodology.md)).
- **Over-normalising.** Dropping legal forms removes noise and also look-alike evidence; we added legal-form features back, and reverted sree/shree/om/maa as stop words because they were some names' only distinctive word ([blocking v3 record][blk3]).

## 7. Jury questions with answers

**Q1. Describe your solution in classic record-linkage terms.**
Retrieval sums IDF over shared tokens, which is a Fellegi–Sunter agreement weight with value-specific u. The XGBoost stages estimate the match log-odds, Fellegi–Sunter's log-likelihood ratio plus the prior, without assuming the fields are independent. Instead of two thresholds and a review band, we pick each S1's set with the highest expected F0.5, because that is what the metric rewards.

**Q2. Why not unsupervised Fellegi–Sunter with EM? It would work on France without labels.**
We did not run it. Decoys differ from copies through interactions (same name and street, nudged number, swapped business word) that independent field weights cannot express. And French names are generic: each French decoy we removed shares its name with a median of 43 other S1 [M] ([methodology §2.1][doc]), so EM would over-trust name agreement. We self-trained on guarded decisions instead ([09](09-self-training-and-domain-shift.md)).
**Hindsight:** an EM-fitted score would have been a cheap, independent French diagnostic.

**Q3. Is this one-to-one matching? Why not the Hungarian algorithm?**
No. An S1 owns 0–11 records and a record has at most one owner (0 violations in 7.6M true pairs) [M]. The constraint is many-to-one, and with additive pair scores the best assignment is each record's highest-scoring S1, which is our argmax ownership. One-to-one would cap pair recall near 27% [E].

**Q4. How do you keep the output consistent without transitive closure?**
S1 is deduplicated and every record gets at most one owner, so the output is one star per S1 and nothing chains across entities. Transitivity enters softly through cluster support.

**Q5. Where does deep learning help, and where not?**
The cross-encoders read only the 1.49M test pairs with stage-1 p1 between 0.02 and 0.99. On labelled pairs from that band, stage 1 has AUC 0.930; e5-large reaches 0.939, bge 0.942 and Qwen2.5-7B 0.944 [M] ([methodology Table 3][doc]). Outside the band XGBoost is already sure, and a transformer adds cost rather than accuracy, except as an independent re-check.

**Q6. Why not active learning for France?**
We did not label test data by hand; the rules allow only the provided data, and hand-labelling the test set would not be fair play. In production it would be the first step for a new country: a few thousand labelled uncertain French pairs would replace much of the self-training guesswork.

**Q7. What made this harder than standard ER benchmarks?**
23.7M records, decoys generated at the true address, names shared by half of all S1, a country absent from training, and a macro metric in which a singleton counts as much as an entity with eleven copies.

**Q8. Which single idea would you keep?**
Decide the way the metric scores: calibrated probabilities in, the expected-F0.5-optimal set per S1 out. Second: spend compute where the uncertainty is.

## 8. Self-test

1. Write the Fellegi–Sunter agreement and disagreement weights for one field and compute them for m = 0.85, u = 0.12.
<details><summary>Answer</summary>Agreement log(m/u) = ln(0.85/0.12) ≈ +1.96; disagreement log((1 − m)/(1 − u)) = ln(0.15/0.88) ≈ −1.77. Under conditional independence a pair's score is the sum over fields.</details>

2. Why is IDF a Fellegi–Sunter weight in disguise?
<details><summary>Answer</summary>u_t, the chance a non-match shares token t, is about df_t / N. So log(m_t/u_t) = log m_t + log(N/df_t): IDF plus a roughly constant term. Rare shared tokens carry more evidence.</details>

3. Why would u estimated on random pairs overstate name evidence in our pipeline?
<details><summary>Answer</summary>Random pairs almost never share a name, so u is tiny. After blocking nearly every candidate shares name tokens and half of all S1 share their exact name with another S1, so the relevant u is far higher and the true weight far smaller.</details>

4. Is our match relation one-to-one, one-to-many or many-to-many, and which fact shows it?
<details><summary>Answer</summary>One-to-many from S1 to records (many-to-one from records to S1): each S2/S3 record matches at most one S1, with 0 violations in 7,638,365 true pairs, while an S1 has 0–11 records.</details>

5. Show that naive Bayes and Fellegi–Sunter rank pairs identically.
<details><summary>Answer</summary>Naive Bayes gives logit P(M | γ) = log π/(1 − π) + Σ_k log P(γ_k | M)/P(γ_k | U). The sum is Fellegi–Sunter's log R under independence, and the prior term is the same for every pair.</details>

6. Name the six pipeline stages and our component for each.
<details><summary>Answer</summary>Preprocess: tokenizer, transliteration, repairs. Block: per-country two-direction IDF retrieval plus a names-only view, then a learned cut. Compare: pair features and cross-encoders on the uncertain band. Classify: XGBoost stages 0–3 with calibration. Assign: argmax ownership and the per-S1 expected-F0.5 set. Evaluate: macro F0.5 on the 25% S1 holdout with a paired bootstrap.</details>

7. How does transitive closure fail in deduplication, and why can it not happen in our output?
<details><summary>Answer</summary>If A is wrongly linked to B, and B correctly to C and D, closure merges A with C and D. Our output is one star per S1 with each record owned once, so a wrong link adds one wrong record to one S1 and never merges two S1.</details>

## 9. Further reading

- Fellegi and Sunter (1969), "A Theory for Record Linkage", Journal of the American Statistical Association.
- Newcombe, Kennedy, Axford and James (1959), "Automatic Linkage of Vital Records", Science.
- Jaro (1989), "Advances in Record-Linkage Methodology as Applied to Matching the 1985 Census of Tampa, Florida", JASA.
- Christen (2012), "Data Matching: Concepts and Techniques for Record Linkage, Entity Resolution, and Duplicate Detection", Springer.
- Elmagarmid, Ipeirotis and Verykios (2007), "Duplicate Record Detection: A Survey", IEEE TKDE.
- Getoor and Machanavajjhala (2012), "Entity Resolution: Theory, Practice & Open Challenges", VLDB tutorial.
- Sarawagi and Bhamidipaty (2002), "Interactive Deduplication using Active Learning", KDD.
- Bansal, Blum and Chawla (2004), "Correlation Clustering", Machine Learning.
- Konda et al. (2016), "Magellan: Toward Building Entity Matching Management Systems", PVLDB.
- Mudgal et al. (2018), "Deep Learning for Entity Matching: A Design Space Exploration", SIGMOD.
- Li, Li, Suhara, Doan and Tan (2020), "Deep Entity Matching with Pre-Trained Language Models", PVLDB.
- Narayan, Chami, Orr and Ré (2022), "Can Foundation Models Wrangle Your Data?", PVLDB.

[task]: ../../student_resource/README.md
[plan]: ../../plans/FINAL_PLAN.md
[doc]: ../../experiments/ameya/final-zip/doc/Documentation_template.md
[stack]: ../../docs/decisions/2026-09-27_0636_stacked-rules.md
[a3]: ../../experiments/ameya/model-v1/ANALYSIS_v3.md
[blk3]: ../../docs/decisions/2026-09-26_1122_blocking-v3-repairs.md
[cut]: ../../docs/decisions/2026-09-26_0532_candidate-set-cut.md
[text]: ../../code/business_entity_resolution/src/ber/block/text.py
[indic]: ../../code/business_entity_resolution/src/ber/block/indic.py
[repair]: ../../code/business_entity_resolution/src/ber/block/repair.py
[blockpkg]: ../../code/business_entity_resolution/src/ber/block/__init__.py
[feats]: ../../experiments/ameya/model-v1/feats.py
[feat]: ../../experiments/ameya/model-v1/FEATURES.md
[decide]: ../../experiments/ameya/model-v1/decide.py
[core]: ../../experiments/ameya/model-v1/stack/core.py
[metric]: ../../code/business_entity_resolution/src/ber/eval/metric.py
[team]: ../../docs/TEAM.md
