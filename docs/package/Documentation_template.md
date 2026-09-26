# ML Challenge 2026: Business Entity Resolution Solution Template

**Team Name:** Grenuke <!-- TODO: confirm the registered team name -->
**Team Members:** Ameya Borkar (coordinator), Sachi Dhoka, <!-- TODO: third member's full name (bakshi, @trustdemons05) -->
**Submission Date:** 2026-09-27 <!-- TODO: confirm -->

> DRAFT v0.1 (Sachi, 26 Sep). Every number comes from the team's handovers, analyses and gate records in the repository
> (`docs/handover/`, `docs/decisions/`, `experiments/ameya/model-v1/ANALYSIS_v2..v4.md`, `RESEARCH_v5.md`).
> Items marked TODO need the final leaderboard reading or a confirmation before submission.

---

## 1. Executive Summary

We treat entity resolution as a **constrained decision problem**, not independent pair classification. Multi-view
blocking (TF-IDF tokens, name n-grams, name×address compound keys) feeds a three-stage XGBoost cascade (a cheap filter,
a pair model, and a collective stage-2 model that sees every rival S1 of each record), whose calibrated probabilities go
through **argmax ownership** (every record has at most one owner) and an **exact expected-F0.5 decision per S1**.
The main innovations are evidence-driven: legal-form and look-alike word features that separate the generator's
look-alikes from true copies, **label-free word odds and generator-operation rules for France** (a country with no
training labels), and a candidate set cut to 3.70 pairs per S1 with no holdout cost. Shared-holdout macro F0.5:
**0.9683 (baseline) → 0.99016 (final)**.

---

## 2. Methodology

### 2.1 Problem Analysis

Measured on the provided data (2.2M train S1, 10.3M S2/S3 records; test 1.73M S1 incl. 15% France):

- **Structure.** Every S2/S3 record belongs to at most one S1 (0 violations in 7.64M true pairs). S1 have 3.46 true
  records on average; 5.6% are singletons. 26% of S2/S3 records match no S1 (orphans / distractors). Matched pairs
  never cross countries.
- **Names collide, addresses rarely.** 46–54% of S1 share their exact core name with another S1; about 5% share an
  exact normalised address; only 6 share both. Neither field decides alone.
- **Noise catalogue.** Typos and OCR swaps, word shuffles, legal-form changes, domains and hashtags
  (`onetechnologies.com`), DBA forms, Indic-script names (18% of India true pairs), injected accents, reordered or
  abbreviated addresses, state as code/name/script, truncated or nudged house numbers (first number equal in only 83%
  of true pairs), `<NULL>` and empty addresses (4.4% of records). Postcodes are essentially absent (≤ 0.5%).
- **Look-alikes** (the precision trap): orphans at the S1's street with a nudged house number and a business-changing
  word (holdings, group, exports, industries…). Later analysis showed the generator's two operations at the S1's own
  address: **op A** (true-copy noise: drop a word, append a list word such as "services"; 98–99.8% true) and **op B**
  (look-alike: a different real word in the slot of an S1 word, legal form kept; 0.6% true).
- **Test shift.** Test has 23% more S2/S3 records per S1 and twice the look-alike candidates per S1; US/India test
  predictions nevertheless match the holdout on every label-free diagnostic. **France** (test only) was the
  leaderboard gap: model v3 scored 0.9888 on the holdout and 0.9796 on the leaderboard, implying France ≈ 0.93.
- **Metric.** Macro F0.5 per S1 with singletons: a false merge costs about 3× a miss, and the break-even probability
  rises with set size (0.50 for a lone candidate, 0.73 for a second, 0.77 for a fourth).

### 2.2 Solution Strategy

**Approach Type:** Hybrid: multi-view blocking + gradient-boosted cascade (pairwise + collective) + small
cross-encoder feature + decision-theoretic set selection + label-free rules for the unlabeled country.

**Core Innovation:**
1. **Ownership competition and collective features.** Stage 2 scores each pair against every rival S1 of the record
   and every other record of the S1, over the *full* candidate graph; argmax ownership enforces one owner per record.
2. **Exact expected-F0.5 decision per S1** (Poisson-binomial over all the S1's candidates), used only because it
   passed its gate against a tuned threshold.
3. **Generalising to an unseen country without labels:** look-alike word odds estimated from label-free signals
   (a word's moved-house-number share in its own country), French address normalisation, and generator-operation
   rules (drop op-B, add op-A) whose truth rates are measured on the US/India holdout.
4. **Evidence discipline.** One shared holdout (folds 0–4, 549,699 S1); every component kept only if a paired
   bootstrap over S1 entities shows a gain (Δ ≥ +0.002 and 95% CI > 0; ties go to the simpler option).

---

## 3. Candidate Generation (Blocking)

- **Partition:** by the exact country label (no cross-country matches in train).
- **Blocking keys / views** (`ber.block`, blocking v2 + French normalisation for the final model):
  - `tok`: IDF-weighted token retrieval over normalised name + address, top-K in both directions (S1→R and R→S1);
  - `name_short`: name character 4-grams, for records with empty or short addresses and one-token names
    (domains, handles);
  - compound keys: (name token × address word), which recover typo'd names on number-less streets and most Indic-name
    misses;
  - normalisation before blocking: Indic → Latin transliteration with a 693-entry token dictionary learned from true
    pairs of training folds only; legal forms and honorifics dropped; French addresses normalised (department → region,
    "R" → rue, articles, bis/ter).
- **Repairs (blocking v3, final model):** S2/S3 names that are domains or handles are segmented into the country's S1
  name words ("bluegrill.com" → blue, grill), OCR digits inside words are repaired when the repaired word is an S1 word
  ("capita1" → capital), and ordinal street words become numbers ("Twentieth" → 20). Dev-pool recall 0.972 → 0.979.
- **Trim:** top 15 per S1 and top 4 per record in the `tok` view; other views keep their own trimmed lists.
- **Recall:** holdout pair recall 0.9752 (v0) → 0.9857 (v1) → **0.9899 (v2)**; oracle F0.5 0.9970; 30.3 candidates
  per S1 before the cascade.
- **Final candidate set = what the matcher scores.** The cascade filters inside the candidate set (stage 0, then
  stage 2 only on p1 ≥ 0.002), so `candidate_pairs.tsv` is the stage-2 input, further cut to pairs with p1 ≥ 0.02
  among each record's top 2 S1: **3.70 pairs per test S1** (US 3.66, India 3.61, France 4.09), holdout F0.5 unchanged
  (0.990159 vs 0.990156, Δ −0.000003 [−0.000015, +0.000011]). Overall, **34 blocking pairs per S1 become 3.70**.
  Every predicted pair lies inside it.
  <!-- TODO: total candidate pairs in the final candidate_pairs.tsv (≈ 3.70 × 1,732,544 ≈ 6.4M; read the file) -->
- **How true matches were kept:** recall measured per country, source and hard case (Indic, domain, empty address)
  on the holdout; every blocking change gated on recall and oracle F0.5; miss analyses drove each new view.

---

## 4. Matching Model

**Features used** (float32, NaN when undefined; IDF per country, so France gets its own statistics):
- **Name features:** token overlap per field (shared count, IDF-weighted Jaccard, containment both ways, IDF mass only
  one side has); consonant-skeleton and skeleton-prefix overlaps (transliteration variants); typo-tolerant matching
  (edit distance 1, or 2 from 6 letters) with unmatched IDF mass, max and count; substituted tokens; rapidfuzz scores
  on folded and concatenated names (domains, hashtags); **legal-form relation** (same / dropped / added / changed,
  counts), since look-alikes change the legal form and true copies keep or reformat it.
- **Look-alike word odds (`lo`, `lo0`):** per unmatched name word, the out-of-fold log-odds of a true match when the
  word is extra or missing (holdings −9.8, group −9.7; benign: c0mpany, formerly); for France, label-free proxy odds
  from each word's moved-house-number share, mixed into the same scale.
- **Address features:** address-word overlap, rapidfuzz on folded addresses, house-number relations (equal, truncation,
  nudge ≤ 10, other, missing) on the first number and over the whole number sets (the S1's first number found among
  the record's numbers is the top feature by gain); in the final model also **signed** relations (`nx`: signed first-
  number difference, nudge set, digit substitution/swap, suffix, length difference; +0.0002 on the holdout).
- **Context / retrieval:** per-view scores and ranks both ways, candidate counts, gaps to the best candidate, rival
  counts (S1 sharing the name key or the (number, street) key), source flag.
- **Stage 2 (collective):** per record: best and second-best p1, margin to the best rival, rank, claims above 0.5,
  share of p1 mass; per S1: rank, max and sum of p1, counts above 0.5/0.8/0.95, neighbour gaps, same-source sums;
  cluster support (similarity of the record to the S1's other confident records); the top-30 stage-1 features and the
  legal-form group.
- **Cross-encoder feature:** multilingual-e5-small (MIT, 118M parameters) fine-tuned out of fold on the uncertain band
  (p1 in 0.02–0.99), input "name ; address" for both sides; its logit is a stage-2 feature.
  <!-- TODO: total feature count of the final set (fx4 + lo0 + lg + ce) -->

**Model type:** XGBoost cascade.
- Stage 0: 200 trees on a 10% S1 slice; keeps about 15% of pairs and 99.95% of true pairs.
- Stage 1: depth 9, eta 0.06, early-stopped (about 2,000 trees); three out-of-fold models (the team's OOF groups).
- Stage 2: depth 7, on out-of-fold p1, so it learns from honest scores.
- Calibration: isotonic regression on out-of-fold p2 of training folds only (never the holdout); reliable within about
  0.01–0.03 per bin in every country × source cell.
- Final fit (`--all`): the holdout becomes a fourth OOF group, so the submitted models use all training labels.

**Threshold selection method:** after argmax ownership, gate G6 compares one global threshold tuned on the holdout
(0.675) with the exact expected-F0.5 set per S1 (logit shift tuned on the holdout; best shift 0). On stage-1
probabilities the DP loses (−0.00029); on the calibrated stage-2 probabilities it wins (+0.00018, CI [0.00009,
0.00026]), so the final model uses the DP. For France only, `post_ops.py` then drops op-B look-alike predictions and
adds op-A true copies (argmax owner, in the candidate set, not predicted elsewhere).

---

## 5. Results & Error Analysis

- **F_0.5 Score (macro), shared holdout (549,699 S1):**

  | system | holdout | public leaderboard |
  |---|---|---|
  | baseline v0 (Sub 1) | 0.9683 | <!-- TODO --> |
  | model v1: features v1 + stage 2 + DP | 0.9801 | |
  | model v2: blocking v1 + look-alike odds + cluster support | 0.98436 | 0.97608 |
  | model v3: blocking v2 + legal forms in stages 1–2 | 0.98882 | 0.97961 |
  | model v4: + cross-encoder + France fixes | 0.99015 | <!-- TODO --> |
  | v5all: v5 features, all-data fit, France rules v2, candidate cut (fallback) | 0.99016 | <!-- TODO --> |
  | **final v6all: blocking v3 repairs, signed number features, as v5all otherwise** | <!-- TODO: gate result --> | <!-- TODO --> |

  Selected gates (paired bootstrap, 1,000 resamples): features v1 +0.0097 [0.0095, 0.0099]; stage 2 vs stage 1
  (dev) +0.0069 [0.0062, 0.0077]; legal-form features +0.00271 [0.00260, 0.00283]; model v3 vs v2 +0.00445
  [0.00431, 0.00459]; model v2 vs v1 +0.00431 [0.00418, 0.00445]. Rejected: name-uniqueness features (+0.0005, below
  the bar). Leave-one-country-out (US → India): 0.961 with India's words known, 0.882 unseen, 0.960 with the
  label-free proxy odds, the evidence for the France design.
- **Common false positives (wrong merges):** precision is 0.998. The remaining wrong merges are look-alikes at the
  S1's street: a nudged or truncated house number plus a changed legal form or an added business word ("Bright Voya LP
  2" vs "Bright Voya Corp 3"). In France, before the fixes, the generator's op-B word swaps ("Troupe Ecole SAS" →
  "Troupe Centre SAS") were accepted at 65 per 1,000 S1 because French descriptors had no label odds.
- **Common false negatives (missed matches):** the model is recall-bound (missed records are 89% of the holdout loss).
  69% of misses are **empty-address records whose name several S1 share**: from the name alone the owner is a coin
  flip, so abstaining is correct under F0.5 (about 22k irreducible misses). The rest: blocking misses (domains, OCR
  digits, ordinal street words; +0.0003–0.0005 left), brand names at a shared address, nudged numbers.

---

## 6. Conclusion

A careful reading of the data (one owner per record, colliding names, the generator's look-alike operations) shaped a
cascade whose collective stage and per-entity decision optimise the actual metric, reaching 0.990 macro F0.5 on the
shared holdout. The largest lesson was the unlabeled country: the leaderboard gap came entirely from France, and the fix
was not a bigger model but label-free statistics and generator rules measured on the labeled countries. Every
component earned its place through a paired-bootstrap gate on one shared holdout, recorded in `docs/decisions/`.

---

## Appendix

### A. Code Artefacts

`code/business_entity_resolution/`:
- `src/ber/`: the team package, with one CLI (`python -m ber.pipeline --stage <stage> --split <split> --tag <tag>`):
  `records`, `normalize`, `block` (multi-view blocking, Indic transliteration, French address normalisation),
  `features` (context and rivalry features), `model` (stage-1 model, calibration, ownership and the expected-F0.5
  decision), `write` (organiser TSV format), `evaluate` (holdout macro F0.5, gates).
- `src/model_v1/`: the final model chain (feature groups, stages 0–2, cross-encoder, decision, candidate set, France
  rules) and `RECIPE.md`, the command-level source of truth.
- `README.md`: setup, the run command, run times, hardware and checks; `reproduce.sh` runs every step in order
  (`MODEL_DIR=code/business_entity_resolution/src/model_v1 bash code/business_entity_resolution/reproduce.sh`).
- `requirements.txt`: pinned versions (numpy, pandas, pyarrow, scikit-learn, xgboost, lightgbm, rapidfuzz, numba,
  torch, transformers). <!-- TODO: pin torch/transformers versions -->
- Hardware: the cross-encoder needs a CUDA GPU; everything else runs on CPU (slower). About 2.5–3 h end to end on an
  RTX 5070 Ti / 31 GB machine; stages 1 and 2 peak at 18–19 GB RAM.
- Compliance: only the provided data; hand-written lexicons (legal forms, street types, states, French departments);
  models MIT/Apache-2.0 (XGBoost Apache-2.0, multilingual-e5-small MIT, 118M parameters); no external lookups.

### B. Additional Results

- Blocking recall per country: v2 India 0.9875, US 0.9916.
- By stage (v3, best threshold): stage 1 0.9871, stage 2 0.9887.
- Loss anatomy (model v2, full holdout): blocking misses +0.00477 if fixed, rejected by the decision +0.00462, lost by
  ownership +0.00359, predicted orphans +0.00240.
- Test diagnostics: predicted records per S1 on test US 3.38, India 3.36 (holdout 3.36), France 3.37 after the v4
  fixes (3.54 before).
- France estimate (label-free, level uncertain): 0.93 (v3) → about 0.96 (final); the France-emptied leaderboard probe
  measures it exactly: F_France = (LB − 0.8423) / 0.14975. <!-- TODO: fill with the probe result -->
