# Data and problem (PRB)

**Summary.** The task is to list, for every Source-1 (S1) business, the Source-2 and Source-3 (S2/S3) records that describe the same business, and the score is a macro F0.5 per S1 in which an empty answer for a singleton earns 1.0.
This page covers the data as we measured it, the structure the labels revealed (one owner per record, no cross-country pairs, look-alike distractors, a Bayes limit on empty addresses) and the code that reads the files and writes the two output files.
Path prefixes used on this page: `ber/` is `code/business_entity_resolution/src/ber/`; `mv1/` is `experiments/ameya/model-v1/`. Constants are read from the code at the cited path and line; they are facts of the submitted code, not measurements.

## 1. Purpose

Frame the problem so that every later design choice has a reason: what is matched, what is scored, what the data allows and what no model can recover.
Fix the data contract (ids, files, output format) so that every stage and every teammate reads and writes the same thing.

## 2. How it works

### 2.1 The task and the rules we built to

- Input per record: `entity_id`, `business_name`, `business_address`, `country` (`ber/io.py:26`). The source (S1, S2 or S3) is the id prefix. S1 is the deduplicated reference; S2 and S3 are vendor formats with noise ([official statement](../../student_resource/README.md)).
- Output 1, `matching_results.tsv`: one row per test S1, with the comma-separated matched S2/S3 ids (empty for no match). Output 2, `candidate_pairs.tsv`: the exact set of records the matching model scored, "the final candidate list just before the ML model scores them". The candidate file is not scored on the leaderboard; the organisers use it for blocking quality and for the efficiency ranking. Every match must be a candidate.
- Metric: per S1, F0.5 = 1.25 c / (0.25 |T| + |P|), where c is the number of correct matches, T the true set and P the predicted set; an S1 with no true match scores 1 if P is empty and 0 otherwise; the mean runs over all S1 ([evaluation.md](evaluation.md)).
- Rules that shaped the design: the `country` label is an open set (test adds France, which never appears in train); no external data, APIs, geocoders or web lookups (disqualification); models MIT or Apache-2.0 with at most 8B parameters; hand-written lexicons are allowed if documented ([AGENTS.md](../../AGENTS.md) section 3).

### 2.2 What the data looks like

| fact | value | level | source |
|---|---|---|---|
| Records, train | S1 2,206,821; S2 5,034,616; S3 5,285,603; total 12,527,040 | M | [numbers §1](../numbers.md) |
| Records, test | S1 1,732,544; S2 4,887,273; S3 5,082,316; total 11,702,133 | M | [numbers §1](../numbers.md) |
| All records | 24,229,173, about 24.2M. AGENTS.md says 23.7M; that is not the sum ([CF-41](../conflicts.md)) | M | sum of the rows above |
| S1 by country | train US 1,323,633 and India 883,188; test India 809,986, US 663,106, France 259,452 (14.975%) | M | [numbers §1](../numbers.md) |
| True pairs (train) | 7,638,365 (S2 3,693,619; S3 3,944,746) | M | [handover 25 Sep 13:00](../../docs/handover/2026-09-25_1300_ameya_repo-setup.md) |
| Matches per S1 | mean 3.46 (S2 1.67, S3 1.79), maximum 11 (5 S2 plus 6 S3); 5.6% of S1 have none | M | [FINAL_PLAN §1](../../plans/FINAL_PLAN.md) |
| Orphans | 26.0% of S2/S3 records match no S1 | M | [FINAL_PLAN §1](../../plans/FINAL_PLAN.md) |
| Name collisions | 46.2% of US and 53.6% of India S1 share an exact core name with another S1 | M | [numbers §1](../numbers.md), [CF-39](../conflicts.md) |
| Noise in true pairs | weak name 15.9%; weak address 4.7%; both weak 0.09% | M, 200k true pairs | [FINAL_PLAN §1](../../plans/FINAL_PLAN.md) |
| Empty record address | 4.4% of true pairs; the generator drops 4.41% of addresses; an empty-address record is a true copy 97.7% of the time | M | [numbers §1](../numbers.md) |
| Postcodes | at most 0.5% of addresses (India 0.02%, US 0.33%) | M | [FINAL_PLAN §1](../../plans/FINAL_PLAN.md) |
| Indic scripts | Indic-script names in 18.3% of India true pairs | M | [numbers §1](../numbers.md) |

### 2.3 Structure the labels revealed

- **One owner.** Across 7,638,365 true pairs, no S2/S3 record belongs to two S1 and no pair crosses a country [M]. So a record has at most one owner, and competition between S1 for the same record is a strong precision signal (D-PRB-02).
- **Look-alikes.** About 26% of S2/S3 records belong to no S1, and many sit close to one. Compared with true pairs, such an orphan keeps the S1's first house number in 12.4% of cases (true pairs: 84.8%) and adds a business word in 76.5% (true pairs: 23.3%) [M]. The look-alike's number is the S1's plus a small step d in {1, 2, 3, 4, 5, 7, 9, 11, 13, 21} (99.5% of US nudges go up) [M, [ANALYSIS_v4 §3.1](../../experiments/ameya/model-v1/ANALYSIS_v4.md)]. This is the central difficulty of the whole task.
- **The test set is denser.** Test has 5.75 S2/S3 records per S1 against 4.68 in train (+23%; India 5.82, US 5.76, France 5.53) [M]. The number of true matches per S1 is not higher (inferred from label-free predictions, [E]), so the extra records are distractors: about 2.4 per S1 against 1.2 in train [E]. We handled this with diagnostics rather than by assuming test looks like train (D-EVL-02).
- **The Bayes limit.** An empty-address record whose name several S1 share cannot be assigned from the record: the miss rate of empty-address records is 20.4% when one S1 has the name, 95.0% for two, 99.6% for three to five and about 100% for six or more [M]. Records with an address miss only 1.7 to 2.7% at any name frequency. Under F0.5 two S1 at probability about 0.49 are both better left empty. About 22k holdout misses (counterfactual +0.0037 F0.5) are irreducible (D-PRB-03).

### 2.4 Code: reading, ids, records, output

- Reading (`ber/io.py:34-45`): pyarrow CSV with `delimiter="\t"`, `quote_char=False`, `escape_char=False`, every column a string, empty stays empty, block size `1 << 26`. Quoting is off because names contain quote characters.
- Ids (`ber/ids.py:13-59`): `eid = source * 1_000_000_000 + number`, accepted pattern `^S[123]-(?:0|[1-9][0-9]{0,8})$`; lossless because no id has leading zeros. All artifacts use the integer eid; nothing relies on row order.
- Records (`ber/records.py:22-41`): S1 first, then each source in file order; duplicate eids raise. Truth (`ber/io.py:67-74`): unique (s1, r) pairs; singletons give no rows. Strings stay pyarrow-backed to avoid about 10M Python string objects.
- Writers (`ber/io.py:85-124`): exact header, one row per test S1 in `test_source1.tsv` order, ids de-duplicated and sorted by (s1, r), written unpadded, comma-joined, `\n` line ends, only S2/S3 ids allowed. The `write` stage refuses matches that are not candidates (`ber/outputs.py:21-27, 36`).
- Artifacts: `work/<kind>/<tag>/<split>.parquet` (`ber/paths.py:39-46`), tags `^[a-z0-9][a-z0-9._-]*$`; every parquet stores the git commit, command, IST time and inputs in its schema metadata; writes are atomic (`.tmp` then `os.replace`, `ber/artifacts.py:42-63`). Default seed 2026 (`ber/config.py:15`). Records build in about a minute.
- On the final path only the `records`, `block` and `write` stages of `ber.pipeline` are used (`fpk/reproduce.sh:112-119, 278`); the model chain in `mv1/` replaces the other stages. The final TSVs are written by `box/compose_tsv.py` with pandas, copying id strings from two `ber.io` outputs, so the format is preserved.

## 3. Why this design

Decision records: [PRB](../decisions/PRB.md).
- D-PRB-01, country is an open set: no country feature, all statistics fitted per exact country label. No true pair crosses a country (0 of 7,638,365), so each country is searched alone and French vocabulary statistics need no French labels. It held to the end.
- D-PRB-02, one owner per record: argmax ownership plus rivalry features (best and second-best S1, margin). It held in the final audit (0 records with two owners).
- D-PRB-03, do not chase empty-address misses with shared names. Every recall rule tried later lost (tie rule -10e-6 to -29e-6; singleton protection and count adds lost more) and none was above 71% precise against the roughly 75% an added pair needs.
- D-PRB-04, no action on content-identical duplicates: exact duplicates always belong to the same S1 (43,910 of 43,910 groups) and only 9 of 10,827 holdout groups were split.
- D-PRB-05, eight ideas sized and skipped (French address clusters, per-stratum calibration, a no-match model, synthetic French pairs, cross-encoder pretraining, typo repair, a stricter France threshold, an external transliterator). The typo repair came back as the blocking v3 repairs (D-BLK-11).
- Related: D-EVL-02 (test shift by diagnostics), D-BLK-02 (partition by country), D-FRA-04 (no external data).

## 4. Alternatives and why not

- One-hot or hard-coded country: forbidden by the statement and our own rule, and it breaks on France.
- Independent pair scoring: ignores that 46 to 54% of S1 share a name with another S1.
- A softmax over a record's S1 plus a "none" option (Plan B, gate G5): never built; "taken by another S1" is only 0.26% of true pairs, so the value was low.
- Forcing duplicate groups to be listed together: not required by the statement and not what the truth does after case folding (4,389 groups split across S1).
- Assuming test resembles train: disproved (5.75 against 4.68 records per S1).

## 5. Numbers

- Empty prediction on the local holdout: 0.0558 (singleton share) [M]; a perfect one 1.0000. The holdout is 549,699 US/India S1 with no France ([evaluation.md](evaluation.md)).
- Empty-address records: 4.4% of true pairs but 52.5% of the misses of model v2 and 69% of the misses at v5all (37,774 of 54,573) [M, local holdout].
- Final model, local holdout (US/India only): precision 99.9%, recall 97.5% [M, [Documentation Table 4](../../experiments/ameya/final-zip/doc/Documentation_template.md)]. Public LB of the submission: 0.990879 [M, [LB 2026-09-27 #04](../../submissions/records/2026-09-27_sub04.md)].
- Output of Composite B on test: 5,851,832 pairs for 1,732,544 S1 = 3.3776 per S1; 99,802 S1 with no match (5.76%, truth 5.58%) [M, [numbers §3.4](../numbers.md)].

## 6. Failure modes and limits

- A country in a script the folding step cannot read (Cyrillic, CJK) would lose its names, because every non-Latin, non-Indic character becomes a space ([normalisation.md](normalisation.md)).
- The id scheme is lossless only because ids have no leading zeros and fit nine digits; anything else raises.
- The label-free France facts (collision shares, look-alike rates) are measured on test text without labels, so France was never validated; see [france.md](france.md).
- The holdout has no France, so the largest leaderboard effect could not be gated locally (D-EVL-01 hindsight).
- Late rule scripts name France explicitly ([CF-26](../conflicts.md)), a small breach of the open-set rule in spirit; no model has a country feature.

## 7. Scale

Reading and the id mapping are linear in records and chunked; the strings are never held as Python objects. At 100 times the data the CSV reader and the integer ids still work, but the single-machine records table (about 12M strings) would move to a partitioned store, and uniqueness checks on eids would need a distributed set. The one-owner rule and the per-country partition are what make everything after it parallel. See [theory 11](../theory/11-scaling-to-billions.md) [E].

## 8. Theory links

[01 Entity resolution](../theory/01-entity-resolution.md), [04 Metrics and decisions](../theory/04-metrics-and-decisions.md), [F01 Data and the problem](../theory/foundations/F01-data-and-problem.md), [F04 Classification metrics](../theory/foundations/F04-classification-metrics.md).

## 9. Likely questions

- **Why is the metric hard?** F0.5 weights precision more, and singletons count: one wrong merge on a singleton scores 0 for that S1. In counts, one false merge costs about as much as four missed copies.
- **How do you know a record has one owner?** 0 violations in 7,638,365 labelled pairs [M]; the final output has 0 records claimed twice.
- **What did you not solve?** Empty-address copies of names that several S1 share. It is a data limit: the record carries no signal that points to the owner (D-PRB-03).
- **Why is test harder than train?** 23% more records per S1, mostly look-alikes; the number of true matches per S1 did not grow.
- **How do you handle France?** There is no country feature; statistics are fitted per country on text only; the rest is in [france.md](france.md).
- More questions are in [qa.md](../qa.md); problems we met are in [failures.md](../failures.md).
