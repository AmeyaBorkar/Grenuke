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

## 4. New training data for France, tested on India first (26 Sep evening)

**Question.** Can French training pairs close France's gap if they are made without labels, either from the generator's operations (rule labels) or from the model's own confident predictions (self-training)?

**The stand-in.** India plays France (`r6/loco_rules.py`, `r6/loco_rules2.py`):
- India's training pairs lose their labels;
- India's word odds become the label-free proxy (`fx5-lop`);
- the stage-1 model and its features are those of v6all, trained on 35% of US training S1 and 50% of India's;
- the score is stage-1 F0.5 on the whole India holdout (argmax + best threshold).

| variant | India holdout F0.5 | vs US only |
|---|---|---|
| US + India true labels (the ceiling) | 0.98660 | +0.02105 |
| **US only** (the unseen country) | **0.96555** | |
| + rule labels: positives (exact copy / A / APP / ACR at the address, 98.0% true), op-B negatives and "house number moved +3…+21" negatives | 0.96463 | −0.0009 |
| + rule positives only | 0.96217 | −0.0034 |
| + rule positives and the 449 op-B negatives | 0.96705 | +0.0015 |
| + self-training (b's p ≥ 0.95 → 1, ≤ 0.02 → 0: 77% of India's pairs, positives 99.3% true) | 0.96671 | +0.0012 |
| + rules (incl. moved numbers) + self-training | 0.96450 | −0.0011 |

- **The moved-number rule fails on India:** 45% of those "look-alikes" are true, because India's compound house numbers ("Sno 32/2/1 Hno 1048") make first-number offsets meaningless.
- **Rule positives alone hurt** (−0.0034): easy certain copies teach the model to accept too much. 449 op-B negatives turn that into +0.0015, so the result is fragile.
- **Self-training helps a little** in the current setting (+0.0012). The earlier rejection was measured with India's words unseen.
- **Verdict:**
  - the best variants close 5–7% of the 0.021 gap;
  - for France, the rules already apply what the rule labels would teach;
  - so a France retrain on rule or self labels is worth about +0.0001–0.0002 on the leaderboard. Not worth a 2–3 h retrain before the deadline.
  - What labels in the target country give (the in-country ceiling) is out of reach without French labels.

**Self-training, repeated with seeds 1 and 2** (different US/India subsamples and XGBoost seeds):

| India holdout F0.5 (stage 1) | seed 0 | seed 1 | seed 2 | mean vs US only |
|---|---|---|---|---|
| US only | 0.96555 | 0.96665 | 0.96779 | |
| + rule positives only | 0.96217 | 0.96278 | 0.96323 | −0.0040 |
| + rule positives and op-B negatives | 0.96705 | 0.96681 | 0.96750 | +0.0005 (noise) |
| + self-training | 0.96671 | 0.96789 | 0.96802 | **+0.0009** |

Self-training is a small, consistent gain (about 4% of the gap).

**Candidate v6all-s3-ops3 against the uploaded v5all-ops2** (`r6/frdiff.py`; for reading tonight's score):
- France gains 49.7 and loses 25.7 predictions per 1000 S1. US/India gain about 13 and lose 3.
- French gains:
  - new blocking finds (domains, OCR): +9.8;
  - brand names and domains at the address: +5.8;
  - empty-address copies: +4.3;
  - list-word copies (A/APP): several.
- Mostly at pc 0.7–0.99.
- Read the score as France change = (LB − 0.98781 − 0.00058) / 0.14975, where 0.00058 is the US/India holdout gain times 0.85.

**A small blocking regression in France.** 2,186 French predictions of v5all (8.4 per 1000 S1) are not candidates in blocking v3, though they were in v2:
- 953 acronyms at the S1's address ("PU" for "Passion Union", "CF" for "Cynegetique & Fils SASU");
- 520 brand-name or domain records at the address;
- about 100 list-word copies.

These records match their S1 through the address only. French house numbers are small and street names common, so v3's small shifts in scoring pushed the true S1 out of the record's top 4. About −0.0006 France F0.5.
- An exact-address view would recover them.
- On the holdout it finds only 516 missed true pairs (0.94 per 1000 S1, +0.00007), so it is not worth a rebuild before the deadline.

**Holdout loss breakdown, v6all + stage 3** (`analysis.py --scores ameya-s3-v6all`): F0.5 0.99084, loss 0.00916; precision 0.9986, recall 0.9742.

| bucket | pairs | gain if fixed | v5all |
|---|---|---|---|
| lost to another S1 (mostly identical-name empty-address ties) | 20,134 | +0.00342 | 19,050 |
| not a candidate (blocking) | 16,455 | +0.00269 | 19,163 |
| owned, rejected by the decision | 11,438 | +0.00187 | 15,130 |
| stage-0 filtered | 1,063 | +0.00019 | 1,206 |
| false positive: record owned by no S1 / by another S1 | 1,392 / 1,145 | +0.00063 / +0.00053 | 1,309 / 858 |

- 67% of the loss is misses only (8.1% of S1); 20% is non-singleton S1 left empty (1,001).
- Nothing new is recoverable at scale: US/India stay close to their Bayes limit.

## 5. Evening additions (26 Sep, 18:00–19:00 IST)

### 5.1 Larger cross-encoders on a rented H100 (`ce_box.py`, `ce_import.py`)

**Setup.**
- Same band (stage-1 p1 in [0.02, 0.99]: 1.57M train, 1.49M test pairs), same three OOF groups, and same loop as ce.py; the holdout gets the mean of the three models.
- Only the records and the band pairs were uploaded (about 1.2 GB).
- The whole box session used about 7.8 GB of internet traffic.

| cross-encoder | band AUC, OOF | band AUC, holdout | runtime |
|---|---|---|---|
| multilingual-e5-small (v6all) | 0.9191 | 0.9240 | 35 min (local GPU) |
| multilingual-e5-base (MIT, 278M) | 0.9244 | 0.9287 | 37 min (shared H100) |
| **multilingual-e5-large** (MIT, 560M) | **0.9350** | **0.9391** | 61 min (shared H100) |
| stage-1 p1 itself, same holdout pairs | | 0.9297 | |

e5-large beats stage 1 on the pairs stage 1 is unsure about, so it carries new information.

**Stage 2 with all three logits** (`ameya-s2-v7ce3`; decision record `2026-09-26_1933_model-v7ce3.md`):

| | holdout macro F0.5 | gate |
|---|---|---|
| v6all-c2 → **v7ce3-c2** | 0.990788 → **0.991099** | **+0.000311 [+0.000258, +0.000362]** (US +0.00026, India +0.00039) |
| v6all-s3 → **v7ce3-s3** | 0.990842 → **0.991138** | **+0.000296 [+0.000252, +0.000342]** |

- Precision goes up (0.9987 → 0.9991) at the same recall.
- The expected-F0.5 DP now beats the threshold on v7ce3-c2 (+0.00005 [+0.00001, +0.00009]).
- **Next candidate `2026-09-27-v7ce3-s3-ops3a-c2`** (validator PASS, matching `671dca1e…`), with probes `2026-09-27-probe-v7-fr0` (`ad92c0b6…`) and `-fr090`.
- A second e5-large (seed 7, 2 epochs) is training on the box, for a v7b with the two runs averaged.

### 5.2 Acronym copies at the S1's address, found by a join (`acr_join.py`)

- **Why blocking misses them.** A record whose name is the S1's initials ("AD" for "Amicale du Directeurs") has nothing but the address to match on. French records also often carry a street-name typo ("Rue Vaubna", "RUE DU PLAAIS GALLIEN").
- **The join.** It pairs such records with S1 on (country, house number, initials), then confirms with the robust same-address test and `post_ops.name_edit`.
- **Holdout truth of the population:**
  - US 99.72% (723 pairs). The records no S1 holds, which are the ones France gets, are 19 of 19 true; the model predicts the other 704;
  - India 66.1% (758): India's compound addresses make "same address" unreliable;
  - French addresses parse like US ones.
- **France:**
  - 20,471 acronym pairs at their S1's address;
  - **3,872 have a record no S1 holds and exactly one S1 with those initials at that address.** Only 75 were candidates.
  - They are added to the matches and the candidate file (countries without labels only).
  - A 24-pair sample is all genuine copies.
  - About +0.0009 France F0.5 (+0.00014 LB).
- **Package** `2026-09-26-v6all-s3-ops3a-c2` (validator PASS): today's candidate plus these adds.
  - Matching `8d4e3bbc…`, candidates `5e991eca…`.
- The v7 chain runs the join after the rules.

### 5.3 Checked, no gain
- **Per-record renormalisation** on top of stage 3: holdout unchanged (0.990842). Stage 3's mass calibration already covers it.
- **Brand-name copies at a single-S1 address** (`brand_join.py`: one invented token of 5–15 letters that no S1 name of the country uses, the only S1 at that address):
  - the model already predicts the good ones (US 7,559 pairs, 98.8% true);
  - the records no S1 holds are only 37% true (US, 197) and 40% (India, 20).
  - **Not applied.** Unlike acronyms, an invented name does not tie the record to its S1.

## 6. Late evening (26 Sep, 20:00–22:00 IST): squeezing the model, and France checks

### 6.1 Stage-2 settings (holdout, against `ameya-model-v7ce3-c2` 0.991099)

| variant | result |
|---|---|
| seed bagging: v7ce3 + a seed-1 retrain, pc averaged (`bag_scores.py`) | 0.991061 (−0.00004). No gain; the seed-2 run was stopped |
| `max_depth` 8 (`s2.py --param max_depth=8`, box) | early-stopping logloss per group 0.03686 / 0.03651 / 0.03625 / 0.03684 against 0.03684 / 0.03665 / 0.03622 / 0.03681. No gain; not scored |

### 6.2 France, label-free: nothing large is left that labels-free counts can see

- **Stage-1 bands.** France has 2.5–3× the pairs in the uncertain band (p1 0.05–0.99: about 1,040 per 1000 S1, against 360–420) and 150 fewer above 0.99 (3,076 against 3,190–3,260). So the cross-encoders decide a much larger share of French pairs than of US/India ones, and a stronger cross-encoder should help France more than the holdout shows.
- **Per-source counts.** The distributions of predicted S2 and S3 copies per S1 in France match US/India's to within 0.3 points in every bin (S2 = 0…5, S3 = 0…4). Held records per S1: France 3.366, US 3.392, India 3.378 (holdout predictions 3.374 / 3.377; truth 3.46).
- **Domain-name records.** A join on the generator's domain key (lowercase, every character outside [a-z0-9] dropped, so accented letters vanish: "tablissementsvoilesas.com") finds that the model already predicts 99.3–100% of the joinable domain records. Only about 110 free French records join to a single S1 at its address or with no address. **Not applied** (negligible).
- **Vendor tokens** (record-side name tokens against S1-side, test):
  - France's record-only words are the look-alike insert words: "participations", "holding", "distribution" and "international" (about 34k records each, like the US's "Southside", "Greater" and "Midtown", about 19k each), plus the dual-use "groupe" and "développement";
  - **"SNC" (14,763 records, one S1) is a look-alike legal form.** Every sampled SNC record sits on its S1's street with a nudged house number (+1…+21), and the model rejects them (0.06% held). The US's record-only "Incorporated" (47,959 records, 8 S1) is different: 86% are true copies, a vendor spelling of "Inc", and they are predicted normally;
  - dotted legal forms ("S.A.R.L."): held 0.585, against 0.609 for all French records; "et" for "&" and "Frs" for "Frères" are held at or above the average.
- **Record ids are shuffled.** They carry no ownership signal: the correlation between S1 and record numbers is 0.0001.

### 6.3 A second France probe: a lower threshold (`fr_add.py`)

- `fr_threshold.py` asks whether France's band just above the threshold is overconfident. `fr_add.py` asks whether the band just below it is underconfident.
- For target-country S1 it adds the owned pairs with pc above `--lo` that the decision left out, then runs the rules and the acronym join.
- **On v7ce3** (threshold 0.675, `--lo 0.5`):
  - 13,040 French pairs added before the rules (median pc 0.568);
  - the rules drop 1,739 of them as op-B look-alikes, and about 3,200 are A/APP/ACR copies the rules would have added anyway;
  - net +7,993 final pairs (30.8 per 1000 French S1).
  - Package `2026-09-27-probe-v7-frlo` (validator PASS).
- **Expected:**
  - about −0.00017 LB if the band is calibrated (precision about 0.57);
  - about +0.0001 LB if it is 80% true;
  - break-even precision about 0.72.

### 6.4 The France threshold probes, redesigned: cut before the rules

**What they touch** (v7ce3; `r7/frlo_prof.py`: the pairs one package has and another does not):

| probe | French pairs changed | what they are |
|---|---|---|
| `fr090` (cut after the rules, `fr_threshold.py`) | −18,263 (70 per 1000 S1), median pc 0.775 | 48% one-word swaps, 6% appends, 6% acronyms, 69% at the S1's address. About half are the rules' true-copy edits (A/APP/ACR, 97–99.8% true in US/India) that the model scored 0.7–0.9 because of the French biases (§2.9). Dropping them is a known loss that would hide the answer |
| **`fr090r`** (the same cut before the rules; `make_frcut.sh`: `fr_threshold.py --final M --model M`, then `post_ops`, then `acr_join`) | **−10,738 (41 per 1000 S1)**, median pc 0.792 | the rules re-add their true-copy edits. What stays dropped is France's unexplained band: 38% same name (other or empty address), 30% non-list swaps, 28% unrelated names at the address, 0.3% acronyms; 80% have a single S1 above pc 0.1 |
| `frlo` (`fr_add.py --lo 0.5`) | +8,076 (31 per 1000 S1), median pc 0.557 | 56% of the records have two S1 above pc 0.1 (ties) and 44% an empty address. Precision is likely near 50%, below the 0.72 break-even. **Low value as an upload** |

- `fr090r` answers the useful question: is France's unexplained uncertain band worth keeping?
  - If it scores above the candidate, the band is below about 0.72 precision. Then `fr095r` and `fr080r` bracket the best cut.
  - If it scores below, the candidate's threshold stands.
- **Expected:**
  - −0.0001 LB if the band is calibrated (pc 0.79);
  - +0.0003 LB if it is 50% true.
- Package `2026-09-27-probe-v7-fr090r` (validator PASS). It replaces `probe-v7-fr090` in the upload plan.
