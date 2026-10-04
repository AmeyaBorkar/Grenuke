# F01. Data and the problem: records, matches, look-alikes and how to look at data

**Summary.**
- The task: for every Source-1 (S1) business record, list all Source-2 and Source-3 (S2/S3) records that describe the same business, using only name and address. Some S1 have no copies, and saying so is worth a full point.
- The data is large (23.7M records), noisy and full of look-alikes: records that resemble a match and are not. The test set adds a country, France, that has no labels.
- This page gives you the vocabulary, a method for looking at a dataset before you model it, and what each fact about our data forced us to build.

Tier P1. About 2 hours in full, about 1 hour on the fast path (sections 2.2, 2.5, 2.6, 2.9 and 2.10). Prepares you for the advanced pages [01 entity resolution][adv01], [02 blocking][adv02] and [11 scaling][adv11].

---

## 1. What you need first

Nothing. You should be able to read a table and a few lines of Python with pandas. Every term is defined where it first appears and is also in the [glossary][gloss].

Numbers about our project carry an evidence level: **M** measured (on labels, or scored by the leaderboard), **E** estimated or derived by arithmetic, **R** reported in a document and not re-checked. "Local holdout" is the fixed 25% of labelled US/India S1 (549,699 S1) that we never trained on; "public LB" is the leaderboard during the challenge. Made-up numbers for practice are labelled "toy".

---

## 2. The concepts from zero

### 2.1 Records, entities and sources

**Intuition.** A business exists once in the real world. Many files describe it. Each file was made by a different provider, who wrote the name and address in their own style. We never see the business itself, only these descriptions.

**Definitions.**
- A **record** is one row of a file. Here it has four fields: an ID, a business name, a business address and a country.
- An **entity** is the real thing a record describes: one business.
- A **source** is the file a record comes from. The ID prefix tells you: `S1-`, `S2-` or `S3-`. S1 is the reference file. It is "deduplicated", which means it lists each business once. S2 and S3 come from other providers and format places in their own way. For example US Source 3 spells states out, India abbreviates them, and French street types appear as "R." or "Q." ([blocking page, section 4][adv02]).
- There is **no shared key**: no tax number, no phone, no website. Name and address are all we have.

**Worked example.** The five records below use toy IDs. The first three are the story we use throughout this guide.

| ID | source | name | address |
|---|---|---|---|
| S1-00001 | S1 | Acme Robotics Inc | 500 Market St, San Jose |
| S2-00047 | S2 | Acme Robotics Incorporated | 500 Market Street, San Jose CA |
| S3-00812 | S3 | Acme Robotics | Nr. City Hall, San Jose |
| S2-00555 | S2 | Acme Bakery | 500 Market St, San Jose |
| S3-00404 | S3 | Acme Robotix | 12 Elm Rd |

A person reads rows 1 to 3 as one business. The legal form is written two ways, "St" became "Street", a state was added, and row 3 replaced the street number by a landmark. Row 4 sits at the same address but sells different things, so it is another business. Row 5 has almost the same name at another address. The computer sees only strings, so it must learn all of this from examples.

### 2.2 Matches, copies, singletons and ownership

**Definitions.**
- A **match** is a pair (an S1 record, an S2/S3 record) that describe the same business. We call the S2/S3 record a **copy** of the S1 business.
- One S1 can have several copies. In the training labels the count runs from 0 to 11 and averages **3.46** [M]. Per source, S2 copies range from 0 to 5 and S3 copies from 0 to 6 ([problem decisions, D-PRB-03][prb]). This is the **one-to-many** shape of the task.
- A **singleton** is an S1 with no copy at all: **5.6%** of S1 [M] ([methodology 2.1][doc]).
- **Ownership.** Each S2/S3 record belongs to at most one S1. In the labels, 0 of 7,638,365 true pairs break this, and none cross a country [M] ([D-PRB-01 and D-PRB-02][prb]). So the picture is a set of stars: an S1 in the middle with its copies around it, and no chains.

The answer file has one row per S1 and a comma-separated list of copies, empty for a singleton ([task][task]). In the integer form we use inside the code, an ID is `source × 1,000,000,000 + number`, so the source can be read back from the number ([`ber.ids`][io], [AGENTS.md][agents] section 6).

**Worked example.** A toy answer file:

```
source1_entity_id   matched_entity_ids
S1-00001            S2-00047,S3-00812
S1-00002            S3-00004
S1-00003
```

S1-00001 has two copies, S1-00002 has one, S1-00003 is a singleton. If the truth for S1-00003 is "no copies", the empty row scores 1.0. If we had listed any record there, it would score 0.0 ([task][task]).

### 2.3 Entity resolution in one page

**Intuition.** Entity resolution (ER) means deciding which records describe the same entity. It also goes by record linkage (matching records across files), deduplication (finding repeats inside one file) and entity matching (the pair decision itself). Ours is **linkage against a clean reference**: S1 is the reference, and we attach S2/S3 records to it.

**Why it is hard.**
1. **No shared key**, so evidence is spread over noisy text.
2. **Too many pairs.** On the test set, comparing every S1 with every S2/S3 record of the same country would mean about 6.7 trillion pairs (6.7e12) [E] ([scaling page, 2.1][adv11]). So we first **block**: cheaply pick a short list of plausible records for each S1.
3. **Look-alikes** that agree with the S1 on one field but are different businesses (section 2.5).
4. **A metric that scores sets**, not pairs (page [F04][f04]).

**The pipeline in plain words**, with our test-set sizes ([scaling page, 2.1][adv11]):

```
records (S1, S2, S3)
  |  normalise: lower-case, fold accents, expand abbreviations
  v
block: a short list of plausible records per S1
  |    58,437,794 pairs retrieved, 33.7 per S1 [M]
  |    6,410,308 pairs kept as candidates, 3.70 per S1 [M]
  v
compare: turn each pair into numbers (features)
  v
classify: a probability that the pair is a match
  v
decide: pick the set of records for each S1, possibly empty
       5,851,832 pairs predicted, 3.38 per S1 [M]; the truth averages 3.46
```

The advanced page [01 entity resolution][adv01] tells the same story with the classic names (preprocess, block, compare, classify, assign).

### 2.4 Noise: how copies differ from the original

A **copy** is never a clean duplicate. The problem statement lists the kinds of noise ([task][task]), and our own analysis adds numbers ([methodology 2.1][doc], [data checks][checks]).

| kind | example | size (level) |
|---|---|---|
| case, accents | "ACME ROBOTICS" | common |
| legal form dropped, rewritten | Inc, Incorporated, nothing | about 23% of French copies [M] |
| abbreviation | St and Street, Rd and Road, "Rue" written "R." | common |
| word order, extra or missing words | "Robotics Acme", "Acme Robotics services" | common |
| acronyms | a long name shortened to initials | present |
| typos, OCR swaps | "ehpvd" for "ehpad" | present |
| house number changed, cut or missing | 500 becomes 502 | first number equal in 83.3% of true pairs [M] |
| landmark instead of a number | "Nr. City Hall" | present |
| empty address | nothing, or the text `<NULL>` | 4.4% of true pairs [M] |
| script change | Indic script names | 18% of India true pairs [M] |

**Worked example.** Compare row 1 with rows 2 and 3 of the table in section 2.1.

| field | S1 | S2 copy | S3 copy |
|---|---|---|---|
| name | Acme Robotics Inc | Acme Robotics Incorporated (legal form rewritten) | Acme Robotics (legal form dropped) |
| street | 500 Market St | 500 Market Street (abbreviation expanded) | missing (landmark instead) |
| city, state | San Jose | San Jose CA (state added) | San Jose |

Two things are stable in every copy: the rare word "Robotics" and the city. A good matcher leans on what survives the noise.

### 2.5 Look-alikes (hard negatives)

**Definition.** A **look-alike** is a record that is not a match but resembles one. In machine learning this is a **hard negative**. Random non-matches are easy: they share nothing. Look-alikes share one field and differ in another, and they are the reason the task is hard. The test set also contains **decoys**, which is our word for look-alikes that were added in bulk.

**Kinds we met** ([methodology 5][doc], [data checks][checks]):
- **A business word swapped at the same address.** "antenne danse" against "antenne gaz". Our analysis found that look-alikes at the S1's own address are mostly made this way: a different real word takes the place of one word of the S1 name and the legal form is kept. Only 0.6% of such records are true copies [M] ([package document 2.1][pkgdoc]).
- **A nudged house number.** 500 becomes 501 to 510.
- **The same generic name, same number, another street.** "lille ecole sarl, 42 rue gutenberg" against "lille ecole sarl, 42 q. du wault".
- **Very short names one letter apart.** "osd" and "otd".
- **Branches of a chain** that share a name.

**Worked example.** Score the two look-alikes of section 2.1 against S1-00001, field by field.

| evidence | Acme Bakery, 500 Market St | Acme Robotix, 12 Elm Rd |
|---|---|---|
| name | shares "Acme", but the business word differs | one letter changed in "Robotics", could be a typo |
| house number | equal (500) | different (12) |
| street | equal (Market) | different (Elm) |
| verdict | address says match, name says no | name says maybe, address says no |

Neither agrees on both fields. That is the signature of a look-alike: **agreeing on one field is not enough**. Compare with the true copies of section 2.4, which agree on the rare name word and on most of the address.

### 2.6 Counts, rates and pool size

**Intuition.** A **count** is a number of things: 3.46 copies per S1, or 16 S1 sharing one name. A **rate** is a count divided by a denominator: the share of S2/S3 records that match some S1. A denominator is a choice. When the denominator moves, the rate moves, even if nothing real changed.

**Worked example 1: the test pool is bigger.** The test set has 23% more S2/S3 records per S1 than train, and the same number of true copies ([methodology 2.1][doc]).

| per S1 | train | test |
|---|---|---|
| S2/S3 records | 4.68 [M] | 5.75 [M] |
| true copies | 3.46 [M] | 3.46 [M], the same |
| records that match no S1 (orphans) | 1.22 [E] | 2.29 [E] |
| share of S2/S3 records that match some S1 | 73.9% [E] | 60.2% [E] |

The first two rows are measured ([data checks][checks]); the rest is subtraction and division. The process that creates copies did not change (3.46 per S1). All of the extra records are orphans, so there are about 1.9 times as many per S1. The share that matches fell by 14 points purely because the pool grew. A model or a reader that watches the rate would think matching got harder when what grew is the number of look-alikes.

**Worked example 2: ambiguity is a count.** What makes a record ambiguous is how many S1 it could belong to. A name shared by 16 S1 is equally ambiguous among France's 259,452 S1 and among the 1.32M US training S1. As rates they differ by a factor of about 5 (16/259,452 = 6.2e-5 against 16/1.32M = 1.2e-5) ([D-PRB-01][prb], [evaluation page 2.9][adv05], [self-training page 2.5][adv09]). So our "rival" features are counts, stored as `log1p(count)` ([`ber.features.context`][context]).

**Rule of thumb.** Pick the quantity whose meaning does not depend on the pool size. Counts still move with pool size (in the half-size US test pool fewer S1 share each name, so records really are less ambiguous), but they move in the right direction.

### 2.7 Exploring a dataset: a method

Before any model, look at the data in a fixed order. Each step answers one question and can catch a bug.

1. **Load it safely.** Tab separator, no quote handling (names contain `'` and `"`), everything as text, no automatic NA conversion (a business can be called "NA").
2. **Size and keys.** Row counts per file, are IDs unique, any exact duplicate rows.
3. **Emptiness.** Share of empty names and addresses per source and country. Count both the empty string and the literal `<NULL>`.
4. **Distributions.** Length in characters and tokens, scripts (Latin, Devanagari), the most frequent tokens ("services", "rue", "sarl" are heavy).
5. **Cross-tabs.** Country by source, copies per S1 by country, empty-address share by source by country.
6. **Read records by hand** (section 2.8).
7. **Compare splits.** Put train and test side by side for every number above. Differences are findings (France, the larger pool).

```python
import csv
import pandas as pd

def read_tsv(path):
    # tab separated, quote handling off, all text, no NA conversion
    return pd.read_csv(path, sep="\t", quoting=csv.QUOTE_NONE, dtype=str, keep_default_na=False)

s1    = read_tsv("train_source1.tsv")          # in the repo use ber.io.read_tsv / load_split
truth = read_tsv("train_ground_truth.tsv")

print(len(s1), s1["entity_id"].is_unique)                      # step 2
print(s1["business_address"].isin(["", "<NULL>"]).mean())      # step 3
print(s1["country"].value_counts())                            # step 5
copies = truth["matched_entity_ids"].map(lambda s: 0 if s == "" else s.count(",") + 1)
print(copies.value_counts().sort_index())                      # copies per S1
print((copies == 0).mean())                                    # singleton share
```

In the repository, always read through [`ber.io`][io] (`read_tsv`, `load_split`) so that quoting, types and empty fields are handled the same way everywhere.

**Worked example (toy).** Ten S1 with copy counts `3 2 0 5 1 0 4 3 2 6` have mean 2.6, two singletons (20%) and maximum 6. Report the mean together with the singleton share: 2.6 alone hides that a fifth of the entities have nothing to find.

### 2.8 Reading records by hand

Numbers hide mechanisms. Sample 20 S1 per country, spread over small and large copy counts. For each, print the S1, its true copies and the three best-looking non-matches. Write down the kind of every difference, using the tables in sections 2.4 and 2.5, and count them. After 60 records you know which edits are common (for us: legal forms and street abbreviations) and which are rare.

Keep the tally in a file so the next person can repeat it, and read the failures, not only the successes. Reading failures showed us that records with an empty address are 4.4% of true pairs but were 52.5% of the misses of an early model (v2) and 69% at a later one (v5all). No rule recovered them ([D-PRB-03][prb]).

### 2.9 Our data facts and what each one implies

| fact | level | what it implies | where it shows up |
|---|---|---|---|
| 23.7M records in total | R | all-pairs comparison is impossible, so we block | [02][adv02], [11][adv11] |
| 2.2M train S1; test 1,732,544 S1, of which France 259,452 (15%) | M | France is 15% of the test S1 and has no labels | [09][adv09] |
| `country` has two values in train and three in test | M | treat country as an open set: no country feature, statistics per country | [D-PRB-01][prb] |
| 0 to 11 copies per S1, mean 3.46 | M | the answer is a set of varying size, not the top-1 | [04][adv04] |
| 5.6% singletons | M | the empty set must be an option, and it scores 1.0 | [04][adv04] |
| each S2/S3 record has at most one owner | M | records compete between S1; use ownership and rival features | [06][adv06] |
| 46.2% (US) to 53.6% (India) of S1 share an exact core name with another S1 | M | name alone cannot decide; the address breaks ties | [01][adv01] |
| about 5% of S1 share an exact address, only 6 share both | M | address plus name together almost never collide | [01][adv01] |
| test has 5.75 S2/S3 records per S1 against 4.68, same copies | M | about 1.9 times more orphans and look-alikes per S1; precision must hold | [09][adv09] |
| postcode-like numbers in at most 0.5% of addresses (India 0.02%, US 0.33%, France 0.4 to 0.5%) | M | no postcode keys; use house number plus street word | [02][adv02] |
| empty addresses: 4.4% of true pairs | M | a names-only view is needed, and these are most of the misses | [02][adv02] |
| 18% of India true pairs use Indic script | M | transliteration to Latin | [03][adv03] |
| French addresses: "R." for Rue, 32% name a department or region | M | French street-type and region handling; region names do not separate records | [03][adv03] |
| French names are generic: each French decoy we removed shares its name with a median of 43 other S1; 11% of French S1 share their exact address | M | name collisions are worse in France; a second reader (the 7B) removed many decoys | [10][adv10] |

Sources: [methodology 2.1][doc], [package document 2.1][pkgdoc], [data checks][checks], [D-PRB-01 to D-PRB-03][prb], [scaling page 2.1][adv11], and for the 23.7M [AGENTS.md][agents].

### 2.10 Sanity-checking a data claim

A claim is a sentence with a number in it. Before you repeat it, ask:
1. **What exactly is counted?** "Share a name" needs a definition. Our 46 to 54% counts S1 that share an exact "core name", a normalised form of the name defined in the check script (`plan_checks.py`, [data checks][checks]). A looser rule gives a bigger number.
2. **Over which population, and what is the denominator?** All S1, or S1 in one country? Records or pairs?
3. **Measured or derived?** Mark it M or E.
4. **Can it be reproduced in five minutes** from the files? If not, say who measured it and where.
5. **Does it agree with its neighbours?** Look for a second route to the same number.
6. **Does the sample size support the precision quoted?** (see [F02][f02]).

**Worked example: a consistency check.** The candidate file has 6,410,308 pairs at "3.70 per S1". Then there should be 6,410,308 / 3.70 = 1,732,516 S1. The test file has 1,732,544, and 3.70 is rounded, so the claim is consistent. The retrieval file gives 58,437,794 / 1,732,544 = 33.7 pairs per S1, which matches the table in section 2.3. The final answer has 5,851,832 / 1,732,544 = 3.38 pairs per S1, so about a tenth of the retrieved pairs survive. Two routes to the same number: good.

**Worked example: a derived number you must flag.** "Orphans per S1 almost double." This is derived (5.75 − 3.46 = 2.29 and 4.68 − 3.46 = 1.22), assuming every S2/S3 record is either a copy or an orphan. It agrees with the measurement that 26% of train S2/S3 records match no S1 (1.22 / 4.68 = 26.1%). Say "about twice as many" and mark it E.

---

## 3. How it shows up in our project

- **Open set.** Because France is absent from train, there is no country feature and every statistic is fitted per country ([D-PRB-01][prb]). Retrieval is partitioned by country, so France got its own word statistics with no code change ([blocking page][adv02]).
- **Ownership and name collisions.** With about half of S1 sharing a name, each pair is scored against its rivals, and each record is kept under its best S1 only ([D-PRB-02][prb], [boosting page][adv06]).
- **Singletons.** The expected-F0.5 selection treats the empty set as one option among others ([metrics page][adv04]).
- **Look-alikes.** We learned word-level odds for the business words that signal a look-alike ([string similarity page 2.9][adv03]), and a Qwen2.5-7B model re-reads confident predictions; it dropped 840 French predictions, which were mostly decoys ([LLM page][adv10]).
- **Pool-size shift and empty addresses.** Rival features are counts, not rates ([self-training page 2.5][adv09]). A names-only view in blocking finds some empty-address copies; the rest are a Bayes limit ([D-PRB-03][prb]).
- **First uploads.** Our first uploads scored 0.976 to 0.980 on the public LB while the local holdout said 0.984 to 0.989. The only difference was France, which has no labels, so no local number could show it ([methodology 2.1][doc]).

---

## 4. How to read the numbers

| number | scope and level | what it tells you | what it does not tell you |
|---|---|---|---|
| 3.46 copies per S1 | train labels [M]; test said to be the same | typical answer size | the spread; use the 0 to 11 range and the singleton share |
| 5.6% singletons | train labels [M] | the cost of ignoring the empty answer | which S1 they are |
| 4.68 to 5.75 records per S1 | all S2/S3 records per S1, train and test [M] | the pool grew by 23% | where the extra records sit; they are orphans (derived [E]) |
| 46.2% to 53.6% share a name | exact core name, US and India S1 [M] | names cannot decide alone | how strict "core name" is; loosening it raises the number |
| 0.9913 local holdout, 0.990879 public LB | macro F0.5 [M]; France is only in the second | two different populations | an error bar; see [F02][f02] |
| no private LB score | the organisers publish rankings only | we cannot compute the public to private gap | whether we would rank the same on other splits |

---

## 5. Common misconceptions

1. **"Entity resolution is string matching."** Similar strings are neither necessary nor sufficient: "Acme Bakery" is similar and wrong, "Nr. City Hall" is different and right. The task is a decision under competition between candidates.
2. **"Same name means same business."** About half of S1 share a name with another S1.
3. **"A different address means a different business."** The first house number is not the same in 16.7% of true pairs (changed, cut or missing), and 4.4% have no address at all.
4. **"A bigger pool means more matches."** Test has 23% more records and the same copies per S1.
5. **"Singletons are an edge case."** They are 5.6% of the score, and each one is lost completely by a single wrong prediction.
6. **"The training data shows what test looks like."** France is absent from train, and the US test pool is half the size of the US train pool (about 663k against 1.32M S1) ([evaluation page 2.9][adv05]).
7. **"A row is an entity."** Several rows describe one entity, and the evaluation is per S1, not per row.

---

## 6. Check yourself

**1.** S1 is "Acme Robotics Inc, 500 Market St, San Jose". Classify each candidate as copy or look-alike and name the noise or look-alike type: (a) "ACME ROBOTICS INCORPORATED, 500 market street san jose ca"; (b) "Acme Robotics, Nr. City Hall, San Jose"; (c) "Acme Bakery, 500 Market St, San Jose"; (d) "Acme Robotix, 12 Elm Rd"; (e) "Acme Robotics Inc" with an empty address.

<details><summary>Answer</summary>

(a) Copy: case change, legal form rewritten, abbreviation expanded, state added. (b) Probably a copy: legal form dropped and the number replaced by a landmark; the name and city survive. (c) Look-alike: same address, but the business word differs. (d) Probably a look-alike: both name and address differ, and the name change could also be a typo, so it needs more evidence than we have. (e) Undecidable from this row alone: with an empty address the name must decide, and if other S1 share the name "Acme Robotics Inc" it is close to a coin flip. Our data shows that records with an empty address whose name is shared by six or more S1 are missed about 100% of the time, and we chose not to chase them ([D-PRB-03][prb]).

</details>

**2.** A system gets every non-singleton S1 exactly right and predicts one wrong record for every singleton. What is its macro F0.5? What does the system that predicts nothing for everyone score?

<details><summary>Answer</summary>

Singletons are 5.6% of S1. The first system scores 1 on 94.4% of S1 and 0 on the singletons: 0.944. The second scores 1 on the singletons and 0 on everyone else: 0.056. The first number shows how much a single wrong habit costs (5.6 points); the second is the trivial baseline any real system must beat.

</details>

**3.** Train has 4.68 S2/S3 records per S1 and test 5.75. Both have 3.46 true copies per S1. Compute the orphans per S1 and the share of S2/S3 records that match some S1, for each split. Which of these numbers says the matching problem changed?

<details><summary>Answer</summary>

Orphans per S1: 4.68 − 3.46 = 1.22 (train) and 5.75 − 3.46 = 2.29 (test), a factor of 1.9. Matching share: 3.46 / 4.68 = 73.9% and 3.46 / 5.75 = 60.2%. None of them says the matching process changed: copies per S1 are equal. What changed is the amount of clutter, so the difficulty of the decision (more look-alikes per S1) goes up, but the count of true matches does not.

</details>

**4.** An S2 record is named "lille club sarl", has no address, and its name is shared by 44 S1 (itself plus 43 others). What can you do with it?

<details><summary>Answer</summary>

By name alone a random choice among 44 S1 is right 1 time in 44, about 2.3%. With no address there is no other field to break the tie. Under F0.5 a wrong merge costs several times a miss, so the best action is usually to leave it unassigned. This is the "Bayes limit" of [D-PRB-03][prb]: once a name is shared by many S1, nothing in the record points to the owner.

</details>

**5.** Someone says: "Because the test set has 23% more records, the model has 23% more matches to find, so recall will fall." What is wrong, and which check would you run?

<details><summary>Answer</summary>

The extra records are orphans; true copies per S1 are the same in both splits. The check is to compare the number of predicted pairs per S1 on test with the truth per S1. Our test predictions average 3.38 per S1 against a truth of 3.46 ([scaling page 2.1][adv11]), so there is no sign of 23% more matches. A second check is to see where the extra records fall in the model's score: they sit below the candidate cut ([self-training page, table in 2.1][adv09]).

</details>

**6.** Which of these output rows break the rules? (i) `S1-00001` followed by `S2-00047,S2-00047`; (ii) `S1-00002` followed by `S1-00005`; (iii) `S1-00003` followed by nothing; (iv) `S1-00004` followed by `S2-99999`, an ID that is not in the test file; (v) two rows for `S1-00001`.

<details><summary>Answer</summary>

(i) breaks the no-duplicates rule. (ii) breaks "only S2 or S3 IDs", an S1 may not match an S1. (iii) is valid: empty means no copies. (iv) breaks "IDs must exist in the test set". (v) breaks "exactly one row per S1". Also, every matched ID should appear in the candidate file, or the validator warns ([task][task]).

</details>

**7.** You receive a new country file with no labels. List five checks you would run before any modelling and what each could reveal.

<details><summary>Answer</summary>

(1) Load safely and check that IDs are unique and no line is cut by a quote character: catches parsing bugs. (2) Share of empty and `<NULL>` fields per source: shows whether an address-free view is needed. (3) Records per S1, compared with the known countries: shows pool-size shift. (4) Scripts and the most frequent tokens: show which normalisation and stop words are needed ("rue", "sarl"). (5) The share of S1 with an exact name or exact address in common: shows how much ambiguity to expect. Then hand-read 30 records.

</details>

**8.** In the US/India labels, pairs of the kind "same generic name, same house number, different street" are true matches 99.7% of the time when our model accepts them and 0.5% when it rejects them. What does that tell you about using the pattern as a rule?

<details><summary>Answer</summary>

The pattern alone does not decide. On the labelled holdout 380 such pairs were predicted (99.7% true) and 218 rejected (0.5% true) [M], so a blanket rule either way would be wrong on a third or more of them. The model separates them using other evidence. In France, where one generic name is shared by a median of 43 other S1, the feature models accepted these decoys with confidence, and a second reader (the 7B model) rejected them ([methodology 5][doc], [LLM page 4][adv10]).

</details>

**9.** A teammate says: "France scores lower because it has fewer S1, so the model has less to learn from." Evaluate the claim.

<details><summary>Answer</summary>

A smaller pool, if anything, lowers ambiguity (the half-size US test pool made the US slightly easier, [evaluation page 2.9][adv05]). France is harder for other reasons: generic names, department and region names in addresses, legal forms never seen in train, and above all no labels, so nothing can be trained or validated on it. Test such a claim with name-collision counts and hand-reading, not with intuition.

</details>

**10.** A colleague adds a one-hot column for `country` with columns "US" and "India". What goes wrong on France, and what do the project rules say?

<details><summary>Answer</summary>

On France both columns are 0, a value the model has never seen, so it extrapolates arbitrarily. The problem statement and our hard rules say to treat `country` as an open set: do not hard-code, filter or one-hot it to {US, India} ([task][task], [AGENTS.md][agents]). We partition by the exact country label and fit statistics per country instead ([D-PRB-01][prb]).

</details>

---

## 7. Going deeper

- Christen (2012), "Data Matching: Concepts and Techniques for Record Linkage, Entity Resolution, and Duplicate Detection", Springer. The standard book for the whole process.
- Binette and Steorts (2022), "(Almost) all of entity resolution", Science Advances. A readable survey.
- Getoor and Machanavajjhala (2012), "Entity Resolution: Theory, Practice & Open Challenges", VLDB tutorial.
- Elmagarmid, Ipeirotis and Verykios (2007), "Duplicate Record Detection: A Survey", IEEE TKDE.
- Köpcke, Thor and Rahm (2010), "Evaluation of entity resolution approaches on real-world match problems", PVLDB. Benchmark datasets and what makes them hard.
- Fellegi and Sunter (1969), "A Theory for Record Linkage", Journal of the American Statistical Association. The probabilistic foundation (see [F02][f02]).
- Tukey (1977), "Exploratory Data Analysis", Addison-Wesley. The attitude behind section 2.7.

## 8. Where next

- [F02 Probability and statistics][f02]: why we talk in odds, and how to put an error bar on a number such as 0.9913.
- [F04 Classification metrics][f04]: how F0.5 scores a set, and why singletons matter.
- Advanced pages [01 entity resolution][adv01], [02 blocking][adv02], [03 string similarity][adv03], [11 scaling][adv11].
- The track map and your reading path: [foundations README](README.md).

[doc]: ../../../experiments/ameya/final-zip/doc/Documentation_template.md
[pkgdoc]: ../../../docs/package/Documentation_template.md
[checks]: ../../../docs/handover/2026-09-25_1414_ameya_final-plan.md
[task]: ../../../student_resource/README.md
[agents]: ../../../AGENTS.md
[io]: ../../../code/business_entity_resolution/src/ber/io.py
[context]: ../../../code/business_entity_resolution/src/ber/features/context.py
[prb]: ../../decisions/PRB.md
[gloss]: ../glossary.md
[adv01]: ../01-entity-resolution.md
[adv02]: ../02-blocking.md
[adv03]: ../03-string-similarity.md
[adv04]: ../04-metrics-and-decisions.md
[adv05]: ../05-evaluation-methodology.md
[adv06]: ../06-gradient-boosting-and-stacking.md
[adv09]: ../09-self-training-and-domain-shift.md
[adv10]: ../10-llm-verification-and-compute.md
[adv11]: ../11-scaling-to-billions.md
[f02]: F02-probability-and-statistics.md
[f04]: F04-classification-metrics.md
