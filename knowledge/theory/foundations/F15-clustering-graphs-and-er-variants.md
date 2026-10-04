# F15. Clustering, graphs and ER variants: from pairs to groups

**Summary.**
- Entity resolution (ER) has several shapes: deduplication (one table), record linkage (two or more tables) and entity linking (mentions to a knowledge base). Ours is linkage of a clean master list (S1) to two noisy sources (S2/S3). It is one-to-many, and every S2/S3 record belongs to at most one S1 (0 violations in 7,638,365 true pairs).
- Seen as a graph, records are nodes and candidate pairs are weighted edges. Turning pairwise decisions into groups is the hard part in general. Transitive closure chains clusters together; correlation clustering and assignment algorithms are principled alternatives.
- Our structure, one star per S1, removed the need for clustering. Each record goes to its highest-scoring S1, each S1 picks a set ([F11][f11]), and context enters as rivalry and cluster-support features. Our metric is a macro F0.5 per S1 with a singleton rule, not a pairwise or cluster score.

About 2.5 hours with the exercises. Prepares you for [01 entity resolution][adv01] and the ownership parts of [04 metrics and decisions][adv04].

---

## 1. What you need first

- [F01][f01]: S1, S2/S3, copies, singletons, decoys and candidates.
- [F04][f04]: precision, recall, F0.5. [F11][f11]: the count form of F0.5 and the idea of ownership.
- A little graph vocabulary, explained here: node, edge, path, connected component.
- Evidence levels: **M** measured, **E** estimated, **R** reported (not re-checked here), **U** uncertain; "toy" is invented for practice. "Local holdout" is the fixed 25% of labelled US/India S1 (549,699 S1, no France).

---

## 2. The concepts from zero

### 2.1 Three shapes of entity resolution

**Intuition.** All three decide which records describe the same real-world thing. They differ in what you start with, and so in what can go wrong.

| shape | start with | goal | typical risk |
|---|---|---|---|
| **deduplication** | one table with repeated entities | partition the table into groups of duplicates | chaining: a false link merges two groups |
| **record linkage** | two or more tables | find the pairs (or groups) across tables | cardinality: one-to-one assumed when it is not |
| **entity linking** | text mentions and a knowledge base | map each mention to a KB entry, or to none | ambiguity of names; mentions with no entry |

A related distinction: a table is **clean** if it has no duplicates inside it, **dirty** otherwise. Linking two clean tables is the easy case.

**Worked example.** Our task is record linkage against a reference ([01][adv01]). S1 is the clean reference, already deduplicated. S2 and S3 together hold the noisy copies, with several copies of the same business. For every S1 we output the set of S2/S3 records that describe it. Two facts shape everything [M]: 5.6% of S1 have no copy at all, and 26% of S2/S3 records match nothing (orphans, which include the look-alike decoys). So the answer for an S1 may be "none", and a record may belong to nobody. Entity-linking systems face the same need and call it NIL prediction: the mention has no entry. We have two kinds of none, an S1 with no copy and a record with no S1, and the metric rewards getting the first one right with a full point.

### 2.2 Cardinality: one-to-one, one-to-many, many-to-many

**Definition.** The **cardinality** of a linkage says how many records on one side can match one record on the other.

| cardinality | meaning | usual tool |
|---|---|---|
| one-to-one | each record has at most one partner | assignment (Hungarian method) |
| one-to-many | each S1 has several records, each record at most one S1 | per-record choice of owner, then a set per S1 (ours) |
| many-to-many | records can belong to several entities | clustering |

**Worked example.** In train, an S1 has 0 to 11 copies, 3.46 on average. Every S2/S3 record belongs to at most one S1: 0 violations in 7,638,365 true pairs. No pair crosses countries [M] ([01][adv01]). The generator never gives an S1 more than 5 S2 records, 6 S3 records or 11 records in all [M] ([04][adv04]).

What would go wrong if we assumed one-to-one? Each S1 could receive one record. 94.4% of S1 have at least one copy, so the best possible recall would be 0.944 / 3.46 = 27% [E]. One-to-one is the wrong model for our data.

### 2.3 The graph view

**Intuition.** Draw each record as a dot (a **node**) and each candidate pair as a line (an **edge**) with the model's probability written on it. A set of dots joined by lines is a **connected component**. A clustering is a way of cutting the picture into groups.

**Definition.** A graph is a set of nodes and edges, here weighted by p. Ours is **bipartite** at the matching stage: edges join an S1 to an S2/S3 record, never two S1 or two S2/S3 records. A group of one S1 and its records is a **star**: the S1 is the hub.

**Worked example (toy graph).** Business A has three records a1, a2, a3. Business B has b1, b2, b3. They share a generic name. The record a3 is "lille ecole sarl, 42 rue gutenberg" and b1 is "lille ecole sarl, 42 q. du wault", the kind of decoy pair that cost us most in France. The model's probabilities:

| edge | p | edge | p |
|---|---|---|---|
| a1 to a2 | 0.95 | b1 to b2 | 0.96 |
| a2 to a3 | 0.93 | b2 to b3 | 0.94 |
| a1 to a3 | 0.90 | b1 to b3 | 0.92 |
| a3 to b1 | 0.60 | | |

Six strong edges form two triangles. One weak edge, 0.60, joins them. Everything below is about what to do with that edge.

**How empty the real graph is.** The test has 1,732,544 S1 and 9,969,589 S2/S3 records, so 1.7 × 10^13 possible edges. Blocking keeps 58.4M of them, about 1 in 300,000, and the candidate file keeps 6,410,308, about 1 in 2.7 million [E, arithmetic]. Choosing which edges exist at all is the job of blocking; this page is about what to do with the edges that remain.

### 2.4 Transitive closure and connected components

**Definition.** **Transitive closure** says: if a is linked to b and b to c, then a is linked to c. Applied to a set of accepted edges, it produces the connected components. A fast way to compute them is **union-find**: start with every node alone, and for each accepted edge merge the two groups it joins.

```
for each accepted edge (u, v):   merge the group of u with the group of v
groups = the sets that remain          (near-linear time with path compression)
```

**Worked example.** Accept every edge with p of at least a threshold:

| threshold | components | result |
|---|---|---|
| 0.5 or 0.6 | {a1, a2, a3, b1, b2, b3} | one component of 6 |
| 0.61 or higher | {a1, a2, a3} and {b1, b2, b3} | the two true groups |

At 0.5 the single decoy edge chains two businesses into one group. True pairs: 3 + 3 = 6. Predicted pairs inside the group: 15. Pairwise precision 6 / 15 = 40%, recall 100%. In general, joining groups of size a and b adds a × b false pairs (5 and 5 add 25), so a single false edge costs quadratically.

When is closure fine? When the matcher is very precise and the groups are well separated. It is dangerous when a few false edges can bridge large groups, which is the norm for generic names. In France a name is shared by a median of 43 other S1 for the decoys we removed [M] ([methodology doc][doc]).

### 2.5 Correlation clustering

**Intuition.** Do not cut at one threshold. Choose the partition that disagrees least with all the pairwise scores at once. A weak edge between two dense groups is outvoted by the strong edges inside them.

**Definition.** Give each pair of records a "same group" probability p (0 if there is no edge). For a partition, the cost is the sum over pairs inside a group of (1 − p), plus the sum over pairs in different groups of p. **Correlation clustering** (Bansal, Blum and Chawla, 2004) picks the partition with the smallest cost. It is NP-hard, and the Pivot algorithm of Ailon, Charikar and Newman (2008) gives a 3-approximation in expectation: pick a random record, group it with every record joined to it by an edge above 0.5, remove them, repeat.

Simpler relatives exist. **Center (star) clustering** picks centres and attaches each record to its best centre. **Agglomerative clustering** merges the two most similar groups again and again until a stopping threshold. In our data the centres come for free: each S1 is the hub of its own star.

**Worked example.** For our toy graph (15 pairs, 8 of them with no edge, p = 0):

| partition | cost |
|---|---|
| everything in one group | 8.8 |
| each record alone | 6.2 |
| {a1, a2, a3} and {b1, b2, b3} | 1.0 |

The two triangles cost only 1.0: 0.40 for the weak links inside the triangles, plus 0.60 for cutting the bridge. Correlation clustering finds the two true groups even where a threshold of 0.5 would not.

### 2.6 Assignment and the Hungarian algorithm

**Intuition.** If each record can have at most one partner, the problem is to pair them off so that the total score is highest. Taking the best-scoring pair first (greedy) can block better pairings later.

**Definition.** In the **assignment problem** you have a score for every (row, column) pair and want one column per row, no column used twice, with the largest total. The **Hungarian method** (Kuhn, 1955) solves it exactly in O(n^3) time. In Python, `scipy.optimize.linear_sum_assignment`.

**Worked example (toy).** Three S1 (A, B, C) and three records (r1, r2, r3):

| | r1 | r2 | r3 |
|---|---|---|---|
| A | 0.90 | 0.80 | 0.10 |
| B | 0.85 | 0.30 | 0.10 |
| C | 0.20 | 0.40 | 0.35 |

The row-wise best choice gives A and B the same record r1: a conflict. Greedy (best pair first) takes A with r1 (0.90), then C with r2 (0.40), then B with r3 (0.10): total 1.40. The optimal assignment is A with r2, B with r1, C with r3: 0.80 + 0.85 + 0.35 = 2.00. In practice add a "none" option, since C with r3 at 0.35 is not a match.

**Why we did not use it.** Our data is one-to-many. Each S1 may own up to 11 records, so a one-to-one assignment is wrong (section 2.2). With capacities it becomes a b-matching, solvable by min-cost flow; we used a cap rule instead, which removed 9 US and 13 India test pairs on v7s [M] ([04 section 2.7][adv04]).

### 2.7 Our ownership constraint

**Intuition.** Because a record belongs to at most one S1, a record wanted by two S1 can be right for at most one of them. The cheapest sound rule is to give it to the S1 that wants it most.

**Definition.** **Argmax ownership**: keep each record only under its highest-probability S1. When pair scores add up and nothing else binds, this is the exact best many-to-one assignment, because each record chooses independently. It is computed over all S1, as on the test. F0.5 is not additive, so "argmax, then the set selection" is a two-step heuristic ([F11][f11]).

**Worked example.** Record r has p = 0.80 with S1 a and p = 0.60 with S1 b. It goes to a. If the two were 0.49 and 0.49, giving it to neither is better: a false merge costs about 0.19 and a miss about 0.06 [M]. A softmax over each record's S1 plus "none" (gate G5) was not built, because records taken by the wrong S1 were only 0.26% of true pairs, which bounds the gain [M] ([decision][d-name]). Competition is common: 46% of US and 54% of India S1 share their exact core name with another S1 [M].

### 2.8 Collective matching: rivalry and cluster support

**Intuition.** Pairs are not independent. Whether (S1 x, record r) is a match depends on who else wants r, and on whether r looks like the other records already linked to x. Deciding with that context is **collective** ER (Bhattacharya and Getoor, 2007).

**Definition.** Two feature families in our stage 2 ([methodology doc][doc], Table 2):
- **Rivalry**: ranks in each blocking view, the gap to the S1's best candidate and to rival S1, name-collision counts, and how many S1 want the record. A record wanted by four or more S1 is "crowded", which the decision layer uses again ([F11][f11]).
- **Cluster support**: the maximum over the S1's other candidates R′ of p1(S1, R′) × sim(R, R′). If R fits the records the S1 already has, support is high.

**Worked example.** Candidate R′1 has p1 = 0.99 and similarity 0.8 to R. Candidate R′2 has p1 = 0.90 and similarity 0.2. Support = max(0.99 × 0.8, 0.90 × 0.2) = max(0.792, 0.180) = 0.792. For the decoy "42 q. du wault", if the S1's other copies all say "rue gutenberg", every similarity to them is low and the support is low.

**What it earned** [M] ([decision][d-s3]): cluster support was kept in model v2 (bundled with other changes). A prototype of joint re-scoring gained +0.00011 [0.00007, 0.00015]; rebuilt as stage 3 (contested-record re-scoring) it gained +0.000055 [0.000025, 0.000085] on v6all. Two collective ideas were measured and dropped, according to the methodology [R]: copy-count tie-breaking (−0.00057) and per-record renormalisation of probabilities (+0.000015 on v6all, up to −0.000137 on France).

### 2.9 Pairwise and cluster metrics

**Definition.**
- **Pairwise** precision and recall count all pairs of records placed in the same group. One merge of groups of 5 and 5 adds 25 false pairs.
- **B-cubed** (Bagga and Baldwin, 1998) scores each record: precision is the share of its group that truly belongs with it, recall the share of its true group it is grouped with. Average over records.
- **Adjusted Rand index** and **variation of information** compare whole partitions.
- Ours: **macro F0.5 per S1**. Compare each S1's predicted set with its true set, compute F0.5, average over S1. An S1 with no true match scores 1 for an empty prediction and 0 otherwise.

**Worked example (the toy merge).** Merge the two triangles. Pairwise: precision 6 / 15 = 0.40, recall 1.0, F1 0.57. B-cubed: every record's group has 6 members and 3 truly belong, precision 0.50, recall 1.0, F1 0.67. The same error reads differently.

**Worked example (our metric).** S1 A has 10 copies and we find all; S1 B has 1 copy and we miss it. Pooled F0.5 is 1.25 × 10 / (0.25 × 11 + 10) = 0.98. Macro F0.5 is (1 + 0) / 2 = 0.5 ([04 section 2.3][adv04]). A false pair costs 1.0 on a singleton and about 0.21 on an S1 with 3 copies ([F11][f11]). Because every S1 is a separate star, an error stays local: a wrong record hurts the S1 that took it and the S1 that lost it, not a whole merged group.

### 2.10 What we used and what we did not

| technique | used? | why |
|---|---|---|
| transitive closure, connected components | no | stars around S1; nothing can chain across S1 |
| correlation clustering | no | same |
| Hungarian method | no | one-to-many with capacities |
| argmax ownership | yes | exact for the one-to-many structure |
| set selection per S1 (expected F0.5) | yes | [F11][f11] |
| rivalry and cluster-support features | yes | collective context in stage 2 |
| stage 3 contested-record re-scoring | yes | a joint decision for contested records |

Exact duplicates (same raw name, address and country) always share an S1 in train: 43,910 of 43,910 groups [M]. That is a transitivity fact we get for free, and the model already treats such records alike.

---

## 3. How it shows up in our project

| idea | where | number |
|---|---|---|
| one star per S1 | the output format: S1 to a list of records | 0 to 11 copies, 3.46 on average |
| exclusivity | argmax ownership over all S1 | 0 violations in 7,638,365 pairs |
| capacities | cap rule | US −9, India −13 test pairs |
| rivalry | stage 2 features, the crowd shift in the decision | records wanted by 4 or more S1 |
| collective re-scoring | stage 3 | +0.000055 on v6all |
| cluster support | stage 2 feature | bundled in v2 (+0.00431 with two other changes) |

---

## 4. How to read the numbers

- **0 violations in 7,638,365 pairs** is a fact about train labels. For the test we assume the generator is the same. Treat it as [M] for train and [E] for test.
- **0.26%** is the share of true pairs taken by the wrong S1 under argmax. It bounds what a smarter ownership rule could gain.
- **27%** is a ceiling for a one-to-one model on our data, not something we measured on a one-to-one model.
- A pairwise score and a macro score for the same predictions can differ widely (0.98 against 0.5 in the toy). Always say which one.

---

## 5. Common misconceptions

1. **"ER is clustering."** The output is groups, but you can often decide per record or per entity and never build clusters, as we did.
2. **"Transitivity is always right."** Under a noisy matcher one false link merges two groups. It costs a × b false pairs.
3. **"The Hungarian method gives the best matching for any task."** Only for one-to-one with a score that adds up. Ours is one-to-many.
4. **"Argmax ownership is a hack."** It is exact when scores add up and each record chooses independently. It is a heuristic only because F0.5 does not add up.
5. **"Pairwise F1 and macro F0.5 rank systems alike."** They do not (0.98 against 0.5 above).
6. **"A constraint that holds in train holds in test."** We verified it on train labels only. We assume the generator is the same.
7. **"More context features always help."** Copy-count tie-breaking cost −0.00057 and was dropped [R].

---

## 6. Check yourself

**1.** Which shape of ER is each? (a) Find duplicate customers inside one CRM table. (b) Link S1 businesses to S2/S3 records. (c) Link company names in news text to a company registry.

<details><summary>Answer</summary>

(a) deduplication. (b) record linkage against a clean reference, one-to-many. (c) entity linking.

</details>

**2.** Why would a one-to-one assumption cap our pair recall near 27%?

<details><summary>Answer</summary>

Each S1 could take one record, so at best one of its 3.46 copies on average. 94.4% of S1 have at least one copy: 0.944 / 3.46 = 0.273.

</details>

**3.** Edges: (1,2) 0.9, (2,3) 0.8, (4,5) 0.95, (3,4) 0.55. Find the components at thresholds 0.5 and 0.6.

<details><summary>Answer</summary>

At 0.5 all four edges count: {1, 2, 3, 4, 5}. At 0.6 the bridge (3,4) drops out: {1, 2, 3} and {4, 5}.

</details>

**4.** Merging groups of 4 and 6 by one false edge: how many false pairs?

<details><summary>Answer</summary>

4 × 6 = 24 false pairs. The true pairs are 6 + 15 = 21, the predicted pairs are 45, so pairwise precision is 21 / 45 = 47%.

</details>

**5.** Use the toy graph. Compute the correlation-clustering cost of "everything in one group".

<details><summary>Answer</summary>

Seven edges: (1 − p) = 0.05, 0.07, 0.10, 0.04, 0.06, 0.08 and 0.40 add to 0.80. The 8 pairs with no edge cost 1 each: 8. Total 8.8, against 1.0 for the two triangles.

</details>

**6.** In the Hungarian toy, what total does row-wise best choice try to give, and why is it invalid?

<details><summary>Answer</summary>

A to r1 (0.90), B to r1 (0.85), C to r2 (0.40) = 2.15, but r1 is used twice. A valid assignment cannot reach 2.15. The optimal valid total is 2.00.

</details>

**7.** Record r: p = 0.7 with S1 a, 0.5 with S1 b. Who owns it? What does b's set selection still do with r?

<details><summary>Answer</summary>

a owns it. Under b's expected-F0.5 selection, r is not selectable, but it still counts as a possible true copy of b, because if r truly belongs to b, giving it away is a miss.

</details>

**8.** S1 A has 10 copies, all found. S1 B has 1 copy, missed. Compute pooled and macro F0.5.

<details><summary>Answer</summary>

Pooled: 1.25 × 10 / (0.25 × 11 + 10) = 12.5 / 12.75 = 0.98. Macro: (1 + 0) / 2 = 0.5. The macro score makes small entities expensive.

</details>

**9.** The cluster support of R is max(p1 × sim) over the S1's other candidates. Compute it for (0.95, 0.6) and (0.40, 0.9).

<details><summary>Answer</summary>

0.95 × 0.6 = 0.57 and 0.40 × 0.9 = 0.36, so the support is 0.57. A close copy of a weak candidate counts for less than a middling copy of a strong one.

</details>

**10.** Suppose we added one false pair to every singleton S1 (5.6% of S1). By how much does the macro score fall?

<details><summary>Answer</summary>

Each loses 1.0 (from 1 to 0), so the mean falls by 0.056 × 1.0 = 0.056. That is why precision on S1 with no copy is so valuable.

</details>

---

## 7. Going deeper

- [01 entity resolution][adv01]: the classic pipeline, Fellegi and Sunter, the shape of the answer, transitivity, active learning and deep ER. [04 metrics and decisions][adv04] section 2.7 for ownership. [glossary][gloss] for terms.
- Christen (2012), "Data Matching", Springer. Papadakis, Skoutas, Thanos and Palpanas (2020), "Blocking and filtering techniques for entity resolution: a survey", ACM Computing Surveys.
- Fellegi and Sunter (1969), "A theory for record linkage", Journal of the American Statistical Association.
- Bansal, Blum and Chawla (2004), "Correlation clustering", Machine Learning. Ailon, Charikar and Newman (2008), "Aggregating inconsistent information: ranking and clustering", Journal of the ACM.
- Kuhn (1955), "The Hungarian method for the assignment problem", Naval Research Logistics Quarterly.
- Bhattacharya and Getoor (2007), "Collective entity resolution in relational data", ACM TKDD.
- Bagga and Baldwin (1998), "Entity-based cross-document coreferencing using the vector space model", COLING-ACL. Amigó, Gonzalo, Artiles and Verdejo (2009), "A comparison of extrinsic clustering evaluation metrics based on formal constraints", Information Retrieval.

## 8. Where next

- [F11 Decision theory and optimisation][f11]: the set selection that follows ownership.
- [F16 Learning with limited labels][f16]: what we did when France had no labels.
- [F12 Interpreting our results][f12]: the candidate funnel and the numbers behind it.
- The track map: [foundations README](README.md).

[doc]: ../../../experiments/ameya/final-zip/doc/Documentation_template.md
[gloss]: ../glossary.md
[adv01]: ../01-entity-resolution.md
[adv04]: ../04-metrics-and-decisions.md
[f01]: F01-data-and-problem.md
[f04]: F04-classification-metrics.md
[f11]: F11-decision-theory-and-optimisation.md
[f12]: F12-interpreting-our-results.md
[f16]: F16-learning-with-limited-labels.md
[d-name]: ../../../docs/decisions/2026-09-25_2111_gate-name-uniqueness.md
[d-s3]: ../../../docs/decisions/2026-09-26_1557_rules-v3-and-stage3.md
