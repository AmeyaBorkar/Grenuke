# Research, 26 Sep evening: where the leaderboard still loses, and what can reach 0.99

**Starting point:**
- v5all + France rules v2 + the candidate cut scored **0.98781 (rank 15)**. Holdout 0.990156; France implied 0.971–0.976.
- The final candidate v6all-ops-c2 (holdout 0.990788) is expected at about 0.9883.
- First place is 0.990556.

This note checks the other session's gap budget (pool size, crowding, France), adds new label-free checks on v6all, and ranks what can still move the score. Holdout numbers are on the full shared holdout (549,699 S1). Test checks are label-free. Scripts are in the session scratchpad (`r6/`).

## TL;DR

**The other session's budget, checked on v6all:**
- The US over-prediction on test is mostly correct: the half-size US pool resolves more identical-name ties, and expected false positives are unchanged (§1).
- Crowding costs at most −0.00009 (§2.6).
- **France is what's left, but its level hangs on one number.** If US/India on test score like the holdout, France ≈ 0.971. If they sit 0.002 below it, France ≈ 0.987. Only the France-emptied probe can say which, so it is the most valuable upload (§3).

**New label-free findings on France:**
- **France's pc is provably overconfident.** Σ pc per S1 is 3.55, while the generator allows at most 3.46; US/India match their truth exactly at 3.43. About 0.075 per S1 of it is the op-B mass the rules drop; the rest is identical-name ties (§2.3).
- **Blocking is not France's problem.** 100% of exact name + house-number/street pairs are candidates; the empty-address misses sit in name groups of more than 6 S1 (§2.6).
- **A rule gap:** about 1,291 op-B look-alikes are still predicted because French addresses break the (number, street word) key: "8BIS", "AVEUNE", "Q.".
  - **Rules v3** closes it with a robust address test.
  - On the holdout the newly matched look-alikes are 0.0–1.2% true and the newly matched copies 87–99% true.
  - About +0.001 France F0.5 (§2.7).
- **Stage 3 on v6all:** holdout +0.000055 [+0.000025, +0.000085] (§2.8).
- **Why France is less confident (SHAP, §2.9):** exact copies are fine. True-copy families lose 1–5 logits, from two France-specific biases:
  - the proxy odds treat "groupe", "france" and "developpement" as pure look-alike words;
  - French house numbers are small and shared, which depresses the retrieval margin.

  Fixing either moves only about 1–2% of French predictions (about +0.0004 and ±0.001 France F0.5), so neither is the missing 0.01.
- **Families checked and fine:**
  - France's visible uncertainty is mostly intrinsic ties: French names are reused, e.g. "Deleves Amis SAS" names more than 12 S1.
  - Domains with accents dropped, acronyms, and brand names at the address are true copies.
  - Street-type typos are true copies.
  - Random same-street house numbers are a copy operation that US/India share (§2.4, §2.8).

**Next candidate:** `2026-09-26-v6all-s3-ops3-c2` (v6all + stage 3 + rules v3; validator PASS), expected about 0.9885.

**What decides whether 0.99 is reachable:** the three probes in §3.

## 1. US/India on test: is the pool-size over-prediction a loss?

**The other session's claim** (v3 era): test US predicts +0.020 matches per S1 more than the holdout, India +0.001. It attributes this to US test having half the S1 pool (663k vs 1.32M in train), and bounds the cost at up to −0.0015 on the leaderboard if the extra predictions are false.

**Checked on v6all, family by family** (edit profile of each candidate pair; test = a 15% S1 sample of US/India, holdout with labels; per 1000 S1):

| | US test | US holdout | India test | India holdout |
|---|---|---|---|---|
| predicted pairs | 3384.5 | 3366.7 | 3367.4 | 3368.3 |
| model's expected false positives (Σ 1−pc over predictions) | 4.96 | 4.70 (actual 4.38) | 4.83 | 4.74 (actual 4.45) |

- **The extra US predictions** (+17.8 per 1000 S1) sit mostly in one family: the record has an empty address and the S1's exact name (+7.7 per 1000).
- In a pool half the size, fewer S1 share a name, so more of these name-only records have a single owner. The unpredicted mass of that family drops from 35.0 to 26.2 per 1000 S1.
- The model's expected false positives barely move (+0.26 per 1000 S1).
- **Reading:** the extra US predictions are mostly correct assignments of records that are no longer ties. US test should score at or slightly above the holdout, consistent with the re-weighting in `RESEARCH_v5.md` §1. Only the probe can prove it.

## 2. France on v6all, label-free

### 2.1 Confidence bands

| predicted pairs per 1000 S1, by pc | France | US | India |
|---|---|---|---|
| 0.999–1 | 2923 | 3150 | 3110 |
| 0.99–0.999 | 223 | 188 | 213 |
| 0.7–0.99 | 186 | 52 | 53 |
| rule adds (pc < 0.7) | 28 | | |
| **unpredicted** at pc 0.3–0.7 | 143 | 55 | 48 |
| **unpredicted** at pc ≥ 0.7 (rule drops, ownership) | 79 | 0.2 | 0.3 |

France has about twice the exact copies of US/India, yet 200 fewer very confident predictions per 1000 S1 and 3–4× the uncertain band on both sides of the threshold. On the train OOF, pc is calibrated in every band (0.7–0.75: 73% true; 0.95–0.98: 97%).

### 2.2 Per-S1 counts and the generator's caps

| share of S1 with n predictions | n=0 | n=1 | n=2 | n=5 | n=7 | mean | S2 > 5 per 1000 S1 |
|---|---|---|---|---|---|---|---|
| train truth (US, India) | 5.58% | 5.40% | 17.0% | 14.6% | 2.9% | 3.46 | 0 (cap) |
| test US / India | 5.78% | 5.91–6.09% | 17.8–18.0% | 13.95–14.0% | 2.6–2.7% | 3.38–3.39 | 0.011–0.014 |
| **test France** | 5.72% | **6.37%** | 17.9% | 13.8% | 2.5% | 3.36 | **0.150** |

- France has more single-prediction S1 and a lighter right tail: lower recall, or more single false positives.
- It breaks the S2 cap ten times as often (small in absolute terms: 39 S1).

### 2.3 Probability-mass invariants (the generator's ownership and copy counts)

Each record has at most one owner, so its pc summed over candidate S1 cannot exceed 1. Each S1's expected number of true records among its candidates is at most 3.46.

| | holdout US | holdout India | test US | test India | **test France** |
|---|---|---|---|---|---|
| Σ pc per S1 (truth in candidates on the holdout) | 3.4320 (3.4323) | 3.4243 (3.4235) | 3.4419 | 3.4256 | **3.5456** |
| records with Σ pc > 1.05, per 1000 S1 | 1.9 | 1.9 | 12.1 | 15.5 | **52.4** |
| excess mass Σ max(0, Σ pc − 1), per 1000 S1 | 0.39 | 0.49 | 2.44 | 3.45 | **29.2** |

- On the holdout, pc sums to the truth exactly.
- In France the model believes in about 0.085–0.12 more true records per S1 than the generator allows. That is the label-free proof that France's pc is overconfident.
- About 0.075 per S1 of it is the op-B look-alike mass that the rules drop (the score tables keep their high pc).
- The rest is mostly identical-name ties with two confident S1.
- **Per-record renormalisation** (p / max(1, Σ p) before ownership):
  - holdout 0.990780 → 0.990795 (+0.000015);
  - it drops 6.6 French predictions per 1000 S1 (US/India 2.3–2.6).
  - Tiny, but free and label-free.

### 2.4 Where France's uncertainty sits (edit families; rule-overridden pairs excluded)

Expected errors per 1000 S1 (E[FP] = Σ(1−pc) over predictions, E[FN] = Σ pc over unpredicted candidates):
- France: E[FP] 19.2, E[FN] 134.6;
- US/India test: 4.9 and 54.5.

| family (name edit / street / number) | France excess | what it is |
|---|---|---|
| same name, record address empty | 32.5 | identical-name ties. France's names are generic ("Lille Club"), so ties among 2–5 S1 are twice as common. Bayes-limited under F0.5 |
| one word swapped / same street / same number | 19.9 | op-A (list word after the legal form, 97% true; France predicts them at pc 0.8–0.99) and op-B look-alikes the model left unpredicted. Rules handle both |
| unrelated name / same address | 10.4 | domains with accents dropped ("tablissementsvoilesas.com" for "Établissements Voile SAS"), acronyms ("NS"), made-up brand names at the address ("Nylabelo"). Consistent with true copies (train: 97% true copies of an S1 at that address) |
| same name / other street word / same number | 5.6 | street typos and genuinely different streets |

**No family with an extreme US/India truth rate is left for a new rule.** France's visible uncertainty is either intrinsic (ties) or already handled.

### 2.5 Identical pairs

- The holdout has 7 raw-identical pairs (all true) and 10.6k case-only-identical pairs (all true).
- France has 1,696 raw-identical S3 pairs and 15.4k case-only-identical ones, all predicted.
- France's S3 vendor leaves French addresses untouched (US S3 spells states out, India's abbreviates). This explains France's doubled exact copies, and it is not an error.

### 2.6 Blocking recall in France: fine

Label-free check (`r6/blockmiss.py`): pairs that are obviously the same (same name key and same house number + street word), and same-name pairs whose record has no address. Are they blocking candidates?

| | holdout US / India | test US / India | **test France** |
|---|---|---|---|
| same name + same number/street: pairs per 1000 S1 | 1355 / 944 | 1370 / 956 | **1900** |
| … of which blocking candidates | 100% / 99.93% (missed ones 1.3% true) | 100% / 99.94% | **100%** |
| same name, record address empty: candidates | 79.8% / 96.1% (missed ones 0.4–1.2% true) | 91.5% / 96.1% | 60.1% |

- France's missed empty-address pairs sit in huge name groups. 2,208 of the 2,489 records concerned have six or more same-name S1: "Deleves Amis SAS" is the name of more than 12 French S1, "Cap Fetes" of 5, "YG Comite" of 3.
- Only 68 records are small-group misses.
- So blocking is not where France loses.

**Crowding is negligible too.**
- Test has +23% records per S1, so true records sit lower in the S1's list.
- Simulated on the holdout by tightening the S1-side cap from 15 to 10 (stricter than +23%):
  - 600 predictions lost;
  - F0.5 −0.00009;
  - the record-side lists and the name-only view catch the rest.
- The other session's −0.0003 to −0.001 is too high.

### 2.7 A rule gap: French addresses that the (number, street word) key misreads

A hand review of 22 French S1 with an uncertain pair (raw names and addresses, `r6/s1view.py`) finds that the op-B rule misses look-alikes whose address the key misreads:
- **suffixed numbers:** "8 BIS" / "8BIS", "129 D" / "129D", "2 a", "51 TER" / "51 T";
- **typo'd street types:** "ASLEE", "AVEUNE", "AENUE", "Pace", "DIGEU";
- **abbreviations:** "Q." for Quai;
- **two-letter typos in short street names:** "Arts" / "Arst", "Menin" / "Meinn".

Examples, all still predicted:
- "Paita Culturelle SARL | 8 BIS Rue Alfred Naquet" → "PAITA COMITE SARL | 8BIS R. ALFRED NAQUET" (pc 0.982);
- "DKD Sportive SARL | 4 Place du Pradeau" → "DKD Amis SARL | 4 Pace Du Pradeau" (0.975).

That is **1,291 predicted look-alikes (5.0 per 1000 French S1).** The same misreadings also block op-A/APP adds.

**Fix: rules v3** (`post_ops.py --robust-addr`). The first house number is read without its suffix. The street is the set of words after it, with street types (exact or up to a typo), articles and suffixes skipped. Two addresses match when the numbers are equal and the street sets share a word up to a typo.
- Unit checks pass: all nine misread cases above match.
- "4 Rue de Saverne" vs "4 R. Roger Astic" and "59 Rue d'Isly" vs "117 R. D'isly" correctly do not.
- The holdout measurement is below.

### 2.8 Other families checked and fine

- **Same name + same number + "different street word"** (France 218 per 1000 S1 predicted): mostly street-type typos ("Avcnue De L'aérodrome"), which the key reads as the street word. True copies, pc ≈ 1.
- **Same name + same street + a random other number** (France 16.5 per 1000 S1 predicted): US/India have the same copy operation ("Great Partners | 24 Manhattan Ave" → "205 Manhattan Ave", true). The model predicts those at 99.6–99.9% precision there; France's rate sits between India's (10.7) and the US's (52.7).
- **Record-mass calibration of empty-address records** (stage 3 B) on v6all: holdout about +0.00005 (with A), as in `RESEARCH_v5.md` §8.4.

### 2.9 Why France is less confident: SHAP attribution (agent report, `r6/agentA/`)

- **Method:**
  - stage-1 SHAP from the four group models, averaged; it reproduces p1 exactly;
  - the stage-2 matrix rebuilt exactly per country (the candidate graph is closed within a country; p2 max difference 0.0 on 123k rows).
  - France is compared with US/India inside the same edit family.
- **Exact copies are not the problem:** France gives 99.57% of them pc ≥ 0.999, against 99.73–99.83%.
- **The deficit is 1–5 logits, inside true-copy families:**
  - list-word swaps and appends: 58–63% at pc ≥ 0.999, against 89–98%;
  - acronyms: 17%, against 81–83%;
  - garbled or dropped words;
  - same-name pairs with part of the address missing.

| cause | cost | fix and its measured effect |
|---|---|---|
| **The proxy word odds treat France's dual-use words as pure look-alike words.** "groupe", "france" and "developpement" are both op-A list words (about 6,500 same-address pairs each) and look-alike insert words (about 26k nudged pairs each). The proxy gives −4.84, the value of "holding" | −5 to −6 logits on about 75 pairs per 1000 French S1 | Cap at −1.25 (US "partners" label odds; the US holdout loses −0.00106 if "partners" gets the proxy value). France +8,512 / −311 model predictions: 6,078 were already added by the rules, 2,434 are new, none of them nudged look-alikes. About +0.0004 France F0.5. Not packaged yet |
| **The retrieval margin is depressed:** French house numbers are small and shared, so a rival S1 on the same street scores almost as high | −0.4 to −2.8 logits (`ret__margin_r`, `gap_r_best`, `tok_rank_r`; stage 2 inherits it through `s2__r_margin`) | Tested label-free (`r6/margin_test.py`). For pairs whose S1 and record share the house number, the margin was recomputed against rivals at that number only, then stages 1–2 were re-scored with the saved models; the baseline reproduces v6all's French decisions with 0 differences. **France +4,460 / −1,423 predictions (+17.2 / −5.5 per 1000 S1).** The additions are mostly one-word swaps at the address, which the rules already sort, and "same name, same number, other street" (4.6 per 1000), which in France holds generic-name look-alikes. Mixed and small, and without a retrain it cannot be checked on the holdout. **Not adopted** |
| rival counts `ctx__*`, cluster support | about 0 | none |
| `ce__logit` | helps France on list-word and acronym pairs (+0.4 to +0.6); hurts only other-street pairs, which are mostly look-alikes | none |

## 3. What can still move the score

**The budget.** Take LB = 0.38274 F_US + 0.46751 F_India + 0.14975 F_France, with v5all at 0.98781:
- if US/India score like the re-weighted holdout, France is 0.971. Its gap to US/India (about 0.019 France F0.5 = 0.0029 LB) is more than the gap to 0.99 from v6all (about 0.0017);
- each 0.001 that US/India lose on test moves France's implied level up by 0.0057.

**Label-free, France's calibrated expectation is about 0.985:**
- about 0.003 of excess false positives, from ties and the uncertain band;
- about 0.002 of intrinsic tie misses.

So either:
- **A:** France carries about 0.014 of confident errors that nothing label-free sees; or
- **B:** US/India lose about 0.0025 on test in a way the holdout cannot show, e.g. test-only look-alike types. India predicts exactly as many pairs per S1 on test as on the holdout, which does not rule this out: a swap of true for false pairs keeps the count.

**Uploads, in order of information** (all packaged, validator PASS, same candidate file):

| # | package | what the leaderboard tells us | expected |
|---|---|---|---|
| 1 | `2026-09-26-v6all-s3-ops3-c2` | the next candidate | about 0.9885 |
| 2 | `2026-09-26-probe-v6s3-fr0` | #1 with France emptied. LB_fr0 = 0.38274 F_US + 0.46751 F_India + 0.14975 × 0.0559, so it gives US/India on test exactly, and #1 − #2 gives France. It decides A vs B | about 0.8513 if US/India score like the re-weighted holdout |
| 3 | `2026-09-26-probe-v6s3-fr090` | #1 with France's model predictions below pc 0.9 dropped (77 per 1000 French S1): prices France's uncertain band | #1 − 0.0002 if the band is calibrated; #1 + 0.0006 if it is about 50% precise |
| — | `2026-09-26-v6all-ops3-c2` | rules v3 without stage 3, against `v6all-ops-c2` | |

**After the probes:**

| probe result | what to do (verifiable) |
|---|---|
| **A**, and #3 > #1 | France's band is overconfident. Probe a France threshold of 0.95 (`fr_threshold.py`) and keep the better one. Worth up to about +0.001 |
| **A**, and #3 < #1 | France's remaining loss is confident. Next ideas are model-level and each needs one upload: stage-2 edit-profile features, which let the model learn the generator's operations instead of word identities; a France-only DP |
| **B** | US/India test is where the gap is. Profile test-only families against the holdout by pair edit class, as in §1, and look for families with more predictions and low holdout truth |

Small, safe, already in the candidate:
- stage 3 (+0.00005);
- rules v3 (about +0.00015).
