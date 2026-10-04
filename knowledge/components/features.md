# Pair features (FEA)

**Summary.** Each candidate pair gets about 91 numeric features for stages 0 and 1: token, fuzzy, skeleton and number overlaps, retrieval and rivalry context, look-alike word odds, legal-form relations and signed house-number edits.
Nothing is a country feature, all rarity statistics are fitted per country on text, and name-frequency features are counts, not rates, so France looks as ambiguous as it really is.
Path prefixes: `ber/` is `code/business_entity_resolution/src/ber/`; `mv1/` is `experiments/ameya/model-v1/`. The bundle name is `ameya-fx5`. Constants are read from the code at the cited line.

## 1. Purpose

Turn a retrieved (S1, record) pair into numbers that separate true copies from look-alikes: same name and number with a different street, a nudged house number with an extra business word, a changed legal form.
Keep every feature transferable to a country that was never labelled.

## 2. How it works

### 2.1 The bundle, by group

The count is ours, from the code: 55 + 18 + 6 + 6 + 6 = 91 features into stages 0 and 1 [E]. The earlier v3 bundle had 87 (55 + 18 + 6 + 8, [FEATURES.md:15](../../experiments/ameya/model-v1/FEATURES.md)); fx5 adds `nx` and drops two bit-mask columns.

| group | file | what | count |
|---|---|---|---|
| `str` | `mv1/feats.py:380-421` | name, word and number overlaps (8 each); name IDF; skeleton overlaps; fuzzy matching; house-number relations; rapidfuzz scores | 55 |
| `cx` | `ber/features/context.py:110-143`, `mv1/feats.py:424-446` | retrieval scores and ranks per view, gaps, margins, candidate counts, name and (number, street) rivalry, source, record-side rivalry | 18 |
| `lo0` | `mv1/feats_lo.py`, `feats_lo_proxy.py`, `lo_mix.py` | look-alike word odds: label-based for US/India, label-free proxy for France | 6 |
| `lg` | `mv1/feats_legal.py`, `legal.py` | legal-form relation and counts | 6 (+2 masks dropped) |
| `nx` | `mv1/feats_nx.py` | signed house-number edits | 6 |
| `ce` and mix | `mv1/ce.py`, `zmean_ce.py`, `ce_import.py` | cross-encoder logits (stage 2 only; see [cross-encoders.md](cross-encoders.md)) | 2 |
| stage-2 own | `mv1/s2.py:47-49, 139-175`, `cluster.py` | 20 rivalry and aggregate features over p1, 4 cluster features, p1, logit(p1) | 26 |

### 2.2 `str`: overlaps, fuzzy matching, numbers, rapidfuzz

- IDF is computed per split and per country: `wt = ln(N_c / df_c)` (`_field_csr`, `mv1/feats.py:107-128`, formula `:122`). Test features use test-split statistics: unsupervised and transductive, no labels.
- Overlap (`_set_group`, `:364-377`) for name tokens, address words and address numbers: shared count, IDF-weighted Jaccard `w_inter / (w_s1 + w_r - w_inter)`, containment each way, extra IDF mass each side, lengths. Also on consonant skeletons and on skeleton prefixes of 4 letters.
- Fuzzy token matching (`_fuzzy`, `:222-299`): exact matches first, then typo matches for unmatched tokens of 3 or more letters; the edit bound is 1 if the shorter token has 5 letters or fewer, otherwise 2, the length difference must be within the bound, Levenshtein over at most 63 characters, at most 62 tokens per side. A swapped first name is not a typo: unmatched mass and a substituted-token count (`fz_sub`) expose it.
- First-number relation (`_rel`, `:302-317`): 0 missing, 1 equal, 2 truncation (1 to 3 trailing digits dropped), 3 nudge (absolute difference at most 10), 4 other; plus `num__logdiff1`, whether the S1's first number appears among the record's numbers (`s1first_in_r`, the top feature by gain in v1 [M]) and the reverse.
- rapidfuzz `process.cpdist` (`:402-420`): token-sort and partial ratio on the folded raw name; token-set, ratio and Jaro-Winkler on cleaned tokens; ratio and partial ratio on tokens joined without spaces (domains, hashtags); token-set and token-sort on the folded address. NaN when a side is empty.

### 2.3 `cx`: retrieval and rivalry context

`ret__{tok,name_short}_{score,rank_s1,rank_r}` (rank 99 when a view missed the pair), `ret__n_views`, gaps and margin on the token score, `ctx__log_cands_s1/_r`, `src__is_s3` (`ber/features/context.py:116-142`). Name and street rivalry are log-counts: `ctx__log_s1_same_name` and `ctx__log_s1_same_numstreet` (S1 sharing the S1's name key or (number, street) key), plus the record-side versions (`mv1/feats.py:348-359, 430-445`). The rule "counts, not rates" is explained in the source comment: 16 of 259k French S1 is as ambiguous as 16 of 1.3M US S1 (`:6-8`).

### 2.4 `lo`: look-alike word odds (labels), `lop`: the label-free proxy

- `lo` (`mv1/feats_lo.py`): after exact and typo matching, up to K = 3 unmatched name tokens per side, highest IDF first. Odds are counted on "close" training pairs (OOF group at least 0, word Jaccard at least 0.3, at least one fuzzy-matched token) as `log((n1 + 20 prior) / (n - n1 + 20 (1 - prior))) - log(prior / (1 - prior))`, with `A_PRIOR = 20`. Out of fold: group g uses counts from the other two groups; holdout and test use all three; the holdout's own labels never enter. Features: min, sum and the count below -1, for the record's extra tokens and the S1's missing tokens. Learned words: holdings -9.8, group -9.7, industries and enterprises about -8.7, exports, overseas, infratech -8.5 [M]; benign words: labs +0.7, formerly +1.6.
- `lop` (`mv1/feats_lo_proxy.py`) for a country with no labels: per country and token, the share of "moved" first numbers (`num__rel1` in {3, 4}) among close numbered pairs where the token is extra or missing, shrunk with 20 pseudo-pairs; support under 30 gives exactly 0; the rate is mapped to the label-odds scale by a decreasing isotonic regression fitted on US/India tokens (support at least 200, 201-point grid). Idea: look-alikes move the number and true copies seldom do.
- `lo_mix.py`: US/India keep `lo` (values below 1e-9 written as 0); on test, an S1 whose country is not among the train countries gets `lop`. Leave-one-country-out on the dev kit, India as the unseen country: words unseen 0.88235, proxy 0.95984, words known 0.96106 [M, [ANALYSIS_v4 §4](../../experiments/ameya/model-v1/ANALYSIS_v4.md)].

### 2.5 `lg` and `nx`

- `lg` (`mv1/legal.py:80-100`): `leg__rel` 0 none, 1 same, 2 dropped, 3 added, 4 subset, 5 superset, 6 changed; counts of forms on each side, shared, S1-only, record-only. The two raw bit-mask columns are dropped by `s1.py --drop leg__r_only_bits,leg__s1_only_bits`.
- `nx` (`mv1/feats_nx.py:74-91`): d is the record's first number minus the S1's; `nx__d1` is d clipped to plus or minus 50; `nx__nudge` is d in {1, 2, 3, 4, 5, 7, 9, 11, 13, 21}, the look-alike nudge set (`:38`); `nx__digit_sub`, `nx__digit_swap`, `nx__suffix`, `nx__len_diff`.

### 2.6 Stage-2 features over the whole candidate graph

`mv1/s2.py:52-152`: record side `r_rank, r_best, r_second, r_margin, r_n05, r_sum, r_share, r_n`; S1 side `s_rank, s_max, s_sum, s_n05, s_n08, s_n095, s_gap_up, s_gap_down, s_sum_same_src, s_n08_same_src, s_sum_other_src, s_n`, all over stage-1 p1 with the pair itself excluded where noted. Cluster support (`mv1/cluster.py:13-82`): over the S1's other candidates with p1 at least 0.5, the best IDF-Jaccard between the record and them on name tokens and on address words, the best p1 times their mean, and their count. Details in [model-stages.md](model-stages.md).

## 3. Why this design

Decision records: [FEA](../decisions/FEA.md).
- D-FEA-01 keep the look-alike word features (Plan A's idea; Plan B had cut them). Orphans close to an S1 keep its first number in 12% (true pairs 85%) and add a name word in 77% (true 23%); 37% of such orphans have no rival S1, so a margin has nothing to compare.
- D-FEA-02 left out on purpose: no country, no postcode (6-digit runs in 0.02% of India addresses, 5-digit tails in 0.33% of US ones), no embedding cosines (planned, never built).
- D-FEA-03 counts, not rates: France names look 3 to 4 times as common as anything in train as rates, and about as ambiguous as they are as counts.
- D-FEA-04 features v1; D-FEA-05 look-alike odds out of fold (G3) and cluster support (G9); D-FEA-06 French (number, street) key fix.
- D-FEA-09 legal-form relations, D-FEA-10 drop the bit masks (bit values unseen in training behave like a country feature: 30,518 French pairs scored 0.456, 0.027 with bits zeroed); D-FEA-11 label-free proxy odds; D-FEA-13 signed numbers.
- Not adopted: D-FEA-07 (Bakshi's normalise and string stages never wired in), D-FEA-08 (name-uniqueness features +0.00054 [+0.00001, +0.00107], below the bar; empty-address losses are a data limit), D-FEA-12 (pool-size-dependent rarity, deferred), D-FEA-14 (number-aware margin), D-FEA-15 (cap dual-use French words, deferred).

## 4. Alternatives and why not

- A `country` feature, one-hot or numeric: breaks on France.
- Postcode keys and features: too rare. City and state: no dedicated feature in the final bundle; the methodology's Table 2 lists "city and state" and "empty and PO-box flags" but they exist only in the unused `ber/features/string.py` ([CF-24](../conflicts.md)). An empty address is visible only through zero counts and NaN scores (and explicitly in stage 3).
- Embedding cosines: replaced by the cross-encoders ([cross-encoders.md](cross-encoders.md)).
- Rates for name frequency: wrong under pool-size shift.
- Raw legal-form bit masks as numbers: dropped.
- The v0 string-feature stage (`ber/features/*`, Bakshi): delivered and tested, not on the path; the final chain imports only `ber/features/context.py` (D-FEA-07).

## 5. Numbers

| fact | value | level | source |
|---|---|---|---|
| Features v1 vs baseline v0 (stage 1) | 0.9781 against 0.9683, +0.0097 [0.0095, 0.0099]; India +0.0153, US +0.0060 | M, local holdout | [D-FEA-04](../decisions/FEA.md) |
| Model v2 over v1 (blocking v1 + look-alike odds + cluster support bundled) | +0.00431 [0.00418, 0.00445] | M | [D-FEA-05](../decisions/FEA.md) |
| Legal-form relations | +0.00271 [0.00260, 0.00283]; log-loss 0.04978 to 0.03993 | M | [D-FEA-09](../decisions/FEA.md) |
| Signed numbers `nx` | +0.00021 [+0.00016, +0.00025] (0.99013 to 0.99034) | M | [D-FEA-13](../decisions/FEA.md) |
| LOCO, US-only model scores India | 0.96106 with `lo`, 0.94180 without | M, India holdout | [D-FEA-05](../decisions/FEA.md) |
| Proxy recovers | 77% of the 0.101 that unseen words cost against in-country | M | [D-FEA-11](../decisions/FEA.md) |
| S1 sharing a core name, test | France 48.8%, India 53.4%, US 38.7% | M | [D-FEA-03](../decisions/FEA.md) |
| Feature count | 37 (v0), 79 (v2), 87 (v3), 91 (fx5, our count) | M / E | [numbers §3.6](../numbers.md) |

## 6. Failure modes and limits

- **Dual-use words.** The proxy treats words like partners, groupe and developpement as look-alike words (about -4.8) although they also occur in true copies; for "partners" the proxy value would cost the US holdout -0.00106 [M]. Capping them was estimated at about +0.0004 France F0.5 and never packaged (D-FEA-15).
- **Pooled statistics.** The documentation says all statistics are fitted per country; true for IDF and the proxy, but `token_lo` pools US and India labels by token string and the stage-2 calibration is pooled (code review of the package). "No country feature" holds.
- **France's remaining loss is mostly decoys the features do not separate**: generic names with the same number on another street, which the 7B re-check later caught; SHAP gaps showed lower retrieval margins and word odds in France (D-FEA-14 and its hindsight).
- **Order matters.** Each train run writes a table its test run reads (dictionary, `token_lo`, proxy map), so the bundle must be built train first.
- Features need the whole candidate table in memory (`mv1/feats.py:495-505`).

## 7. Scale

Features are computed on row groups of 4,000,000 pairs (`CHUNK`, `mv1/feats.py:47`) with numba-parallel kernels and parallel rapidfuzz: 52 minutes for fx5 on the 64-vCPU box [R]. The cost is linear in retrieved pairs (66M train, 58M test), so pairs per entity is the cost driver. At a billion records this is about 2,200 vCPU-hours [E, [theory 11](../theory/11-scaling-to-billions.md)]. The context group's need for the whole candidate table would become a distributed group-by.

## 8. Theory links

[03 String similarity](../theory/03-string-similarity.md), [06 Gradient boosting and stacking](../theory/06-gradient-boosting-and-stacking.md), [09 Self-training and domain shift](../theory/09-self-training-and-domain-shift.md), [F05 Trees and ensembles](../theory/foundations/F05-trees-and-ensembles.md), [F06 Text, strings and retrieval](../theory/foundations/F06-text-strings-and-retrieval.md), [F10 Semi-supervised learning and domain shift](../theory/foundations/F10-semi-supervised-and-domain-shift.md).

## 9. Likely questions

- **How do you make features work on an unseen country?** No country feature, per-country IDF fitted on text, counts instead of rates, a label-free proxy for look-alike odds, and no bit-masks.
- **What is the single most useful feature type?** By gain, whether the S1's first house number appears among the record's numbers; the look-alike word odds and legal-form relations followed in measured gains.
- **Why signed house numbers?** Look-alikes nudge the number up by a fixed set of steps; a truncation or digit substitution is a true copy. +0.00021 on the holdout.
- **Do you use city or state?** Not as dedicated features; the address enters through word and number overlaps (see [blocking.md](blocking.md) section 2.5).
- **Where do the look-alike odds come from?** Training pairs only, out of fold; France uses the label-free proxy.
- More in [qa.md](../qa.md).
