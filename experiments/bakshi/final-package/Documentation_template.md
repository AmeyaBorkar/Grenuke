# ML Challenge 2026: Business Entity Resolution Solution

**Team Name:** Grenuke
**Team Members:** Ameya Borkar (coordinator, submissions captain), Sachi Dhoka, Aarush Bakshi
**Submission Date:** 2026-09-27

**Submitted model: `v7nst`** (package `2026-09-27-v7nst-s3-ops3a-c2`).
Public leaderboard macro F0.5 **0.990179**. Shared-holdout macro F0.5 **0.991194**.

> **Provenance of every number below.** Figures marked **[measured]** were recomputed directly from the
> submitted output files and the provided test data while preparing this package. Figures marked
> **[holdout]** come from the team's shared 25% holdout via `ber.eval` and are recorded in
> `docs/decisions/` with a paired-bootstrap CI. Figures marked **[public]** are leaderboard readings.
> Figures marked **[proxy]** are label-free diagnostics, which are *not* ground truth — §5.4 explains
> what each can and cannot support. Two items are marked **[confirm]** where an authoritative value was
> not available to verify.

---

## 1. Executive Summary

We treat entity resolution as a **constrained decision problem**, not independent pair classification.
Multi-view blocking (IDF token retrieval, name n-grams, name×address compound keys) feeds an XGBoost
cascade — a cheap filter, a pair model, then a **collective** model that sees every rival S1 of each
record — whose isotonic-calibrated probabilities pass through **argmax ownership** (each record has at
most one owner) and an **exact expected-F0.5 set choice per S1**.

The hard part was not accuracy on the labelled countries. It was **France, which appears only in the
test set and has no training labels at all** — 14.98% of test S1 [measured]. Three ideas closed most of
that gap, and each is label-free by construction:

1. **Look-alike word odds with a label-free proxy** for countries without labels, so the generator's
   business-changing words are penalised in France too.
2. **Generator-operation rules** (`post_ops.py`): the data generator's edit families are identifiable,
   and their truth rates are *measured on the labelled countries* and applied to France.
3. **Self-training on the target country** (`s2.py --pseudo`): stage 2 additionally fits France's own
   test rows against pseudo-labels taken from an earlier finished chain, cross-fitted by S1 group so no
   French pair is ever scored by a model that saw its own pseudo-label.

Trajectory: **0.9683 → 0.99016** on the shared holdout, and **0.97608 → 0.990179** on the public
leaderboard. The single most instructive result is in §5.2: the final self-training step made the model
**slightly worse** on the holdout and **clearly better** on the leaderboard, because the holdout contains
no French entities at all.

---

## 2. Methodology

### 2.1 Problem Analysis

Measured on the provided data (23.7M records; 2.2M train S1; test 1,732,544 S1 and 9,969,589 S2/S3
records [measured]):

- **Structure.** Every S2/S3 record belongs to **at most one S1** — 0 violations in 7.64M true training
  pairs. S1 have 3.46 true records on average; 5.6% are singletons; 26% of S2/S3 records match no S1.
  **Matched pairs never cross countries.** These three facts are enforced as hard constraints, not
  learned: ownership is exclusive, the decision is per-S1, and blocking partitions by country.
- **The metric shapes everything.** Macro F0.5 per S1, with singletons scored 1.0 for an empty
  prediction and 0 for any prediction. A false merge costs about 3× a miss. The break-even probability
  therefore *rises with set size*: 0.50 for a lone candidate, 0.73 for a second, 0.77 for a fourth. A
  single global threshold is provably the wrong decision rule, which is why §4 uses a per-S1 DP.
- **Names collide; addresses rarely.** 46–54% of S1 share their exact core name with another S1; ~5%
  share an exact normalised address; only 6 share both. Neither field decides alone.
- **Noise catalogue.** Typos and OCR digit swaps; word shuffles; legal-form changes; domains and
  handles (`onetechnologies.com`); DBA forms; Indic-script names (18% of India's true pairs); injected
  accents; reordered and abbreviated addresses; state as code, name or script; truncated or nudged
  house numbers (the first number is equal in only 83% of true pairs); `<NULL>` and empty addresses
  (4.4% of records). Postcodes are essentially absent (≤ 0.5%).
- **The precision trap: the generator's two operations at the S1's own address.**
  **Op A** is true-copy noise — drop a word, append a list word such as "services" — and is 97–99.8%
  true. **Op B** substitutes a *different real word* into the slot of an S1 word while keeping the legal
  form, and is 0–1.2% true. They are nearly identical string-wise and opposite semantically. Separating
  them is most of the precision work.
- **Test shift.** Test has 23% more S2/S3 records per S1 and twice the look-alike candidates per S1.
  US/India test predictions nonetheless match the holdout on every label-free diagnostic, which
  localised the leaderboard gap to France: model v3 scored 0.98882 [holdout] against 0.97961 [public].

### 2.2 Solution Strategy

**Approach type.** Hybrid: multi-view blocking → gradient-boosted cascade (pairwise, then collective) →
fine-tuned cross-encoder features → decision-theoretic set selection → label-free rules and target-country
self-training for the unlabelled country.

**Core innovations.**

1. **Collective scoring and exclusive ownership.** Stage 2 scores each pair in the context of every rival
   S1 of that record and every other record of that S1, over the *full* candidate graph, then argmax
   ownership enforces one owner per record. This is what makes the "at most one owner" fact usable rather
   than merely observed.
2. **Exact expected-F0.5 decision per S1.** A Poisson-binomial DP over all of an S1's candidates picks the
   set maximising expected F0.5. Adopted only because it beat a tuned global threshold on calibrated
   stage-2 probabilities (+0.00018, CI [0.00009, 0.00026]) — and *rejected* on stage-1 probabilities,
   where it lost (−0.00029). Calibration quality, not the DP, is the precondition.
3. **Generalising to an unseen country, in three independent layers.** Label-free proxy word odds;
   generator-operation rules whose truth rates are measured on labelled countries; and self-training on
   the target country's own pairs. Each is separately testable, and none uses French labels, because
   none exist.
4. **Consensus over correlated evidence.** Three fine-tuned cross-encoders agree on the labelled
   countries and *disagree 4× as often on France* (§4.3). Feeding stage 2 the **average** of the large
   models rather than each logit separately is deliberately less expressive and more robust, chosen on
   that evidence.
5. **Evidence discipline.** One shared holdout (folds 0–4, 549,699 S1). Every component kept only if a
   paired bootstrap over S1 entities shows a gain with a 95% CI above zero; ties go to the simpler
   option. Records in `docs/decisions/`.

---

## 3. Candidate Generation (Blocking)

- **Partition** by the exact `country` label. `country` is treated as an **open set** throughout — never
  hard-coded or one-hot encoded to {US, India} — which is why France required no schema change.
- **Views** (`ber.block`):
  - `tok` — IDF-weighted token retrieval over normalised name + address, top-K in both directions
    (S1→R and R→S1);
  - `name_short` — name character 4-grams, for records with empty or short addresses and single-token
    names (domains, handles);
  - **compound keys** (name token × address word), which recover typo'd names on number-less streets and
    most Indic-name misses.
- **Normalisation before blocking:** Indic→Latin transliteration using a 693-entry token dictionary
  learned **only from true pairs of training folds 5–19** (never the holdout); legal forms and honorifics
  dropped; French addresses normalised (department→region, "R"→rue, articles, bis/ter).
- **Repairs (blocking v3, in the submitted model):** S2/S3 names that are domains or handles are
  segmented into the country's S1 name words (`bluegrill.com` → blue, grill); OCR digits inside words are
  repaired when the repaired word is an S1 word (`capita1` → capital); ordinal street words become
  numbers ("Twentieth" → 20). Dev-pool recall 0.972 → 0.979.
- **Trim:** top 15 per S1 and top 4 per record in `tok`; other views keep their own trimmed lists.
- **Recall [holdout]:** pair recall 0.9752 (v0) → 0.9857 (v1) → **0.9899 (v2)**; oracle F0.5 0.9970;
  30.3 candidates per S1 before the cascade.
- **The submitted candidate set is the stage-2 input, not the raw blocking output.** The cascade filters
  inside it (stage 0, then stage 2 only on p1 ≥ 0.002), and it is cut to pairs with p1 ≥ 0.02 among each
  record's top 2 S1. That cut cost nothing measurable on the holdout (0.990159 vs 0.990156,
  Δ −0.000003 [−0.000015, +0.000011]) while reducing ~34 blocking pairs per S1 to **3.70** [measured on
  the c2 candidate file: 6,406,457 pairs over 1,732,544 S1 = 3.6976].
  `acr_join` then appends **3,790** acronym pairs over 3,725 S1 [measured], giving the submitted
  candidate file. **Every predicted pair lies inside the submitted candidate file.**
- **How true matches were kept:** recall was measured per country, per source and per hard case (Indic,
  domain, empty address) on the holdout; every blocking change was gated on recall *and* oracle F0.5; each
  new view came from a miss analysis rather than from guessing.

---

## 4. Matching Model

### 4.1 Features

Float32, NaN when undefined. **IDF is computed per country**, so France gets its own statistics.

- **Name.** Token overlap per field (shared count, IDF-weighted Jaccard, containment both ways, IDF mass
  held by only one side); consonant-skeleton and skeleton-prefix overlaps (transliteration variants);
  typo-tolerant matching (edit distance 1, or 2 from 6 letters) with unmatched IDF mass, max and count;
  substituted tokens; rapidfuzz scores on folded and concatenated names (domains, hashtags);
  **legal-form relation** (same / dropped / added / changed, plus counts) — look-alikes change the legal
  form, true copies keep or reformat it.
- **Look-alike word odds (`lo`, `lo0`).** Per unmatched name word, the out-of-fold log-odds of a true
  match when that word is extra or missing (holdings −9.8, group −9.7; benign: c0mpany, formerly). **For
  countries without labels, a label-free proxy** derived from each word's moved-house-number share within
  its own country, mixed onto the same scale. This is the component that made France tractable at all.
- **Address.** Address-word overlap; rapidfuzz on folded addresses; house-number relations (equal,
  truncation, nudge ≤ 10, other, missing) on the first number and over whole number sets — the S1's first
  number found among the record's numbers is the **top feature by gain**; plus **signed** relations (`nx`:
  signed first-number difference, nudge set, digit substitution and swap, suffix, length difference).
- **Context / retrieval.** Per-view scores and ranks both ways, candidate counts, gaps to the best
  candidate, rival counts (S1 sharing the name key or the (number, street) key), source flag.
- **Collective (stage 2).** Per record: best and second-best p1, margin to the best rival, rank, claims
  above 0.5, share of p1 mass. Per S1: rank, max and sum of p1, counts above 0.5/0.8/0.95, neighbour
  gaps, same-source sums. Plus cluster support (similarity of a record to the S1's other confident
  records), the top-30 stage-1 features by gain, and the legal-form group.
- **Cross-encoder logits.** See §4.3.

### 4.2 Model and calibration

XGBoost cascade:

| stage | what | notes |
|---|---|---|
| 0 | 200 trees on a 10% S1 slice | keeps ~15% of pairs and 99.95% of true pairs |
| 1 | depth 9, eta 0.06, early-stopped (~2,000 trees) | out-of-fold groups, so stage 2 sees honest scores |
| 2 | depth 7, on out-of-fold p1 | the collective matching model |
| 3 | contested-record model + empty-address mass calibration | `stage3.py` |

- **Calibration:** isotonic regression on out-of-fold stage-2 probabilities of *training folds only*,
  never the holdout. Reliable to within about 0.01–0.03 per bin in every country × source cell.
- **Final fit (`--all`):** the holdout becomes a fourth out-of-fold group, so the submitted models use
  all training labels. This is why the submitted model's own holdout figure is a fit-quality reference
  and not an untouched test set — §5.4.

**Decision.** Argmax ownership, then the exact expected-F0.5 DP per S1 (§2.2 item 2). For countries
without training labels only, `post_ops.py` then drops op-B look-alike predictions and adds op-A true
copies (argmax owner, inside the candidate set, not already predicted elsewhere), and `acr_join.py` adds
acronym copies at the S1's own address that blocking can miss when many S1 share a street.

### 4.3 Cross-encoders, and why the *average* is used

Fine-tuned out-of-fold on the uncertain band (stage-1 p1 in 0.02–0.99), input `"name ; address"` for both
sides, logit consumed as a stage-2 feature.

| cross-encoder | band AUC, OOF | band AUC, holdout | French rule AUC [proxy] |
|---|---|---|---|
| stage-1 `p1`, same pairs | — | 0.9297 | — |
| multilingual-e5-small (118M) | 0.9191 | 0.9240 | — |
| multilingual-e5-base (278M) | 0.9244 | 0.9287 | 0.687 |
| multilingual-e5-large, 1 epoch, seed 26 | 0.9350 | 0.9391 | 0.803 |
| multilingual-e5-large, 2 epochs, seed 7 | **0.9403** | **0.9441** | 0.792 |
| **z-mean of the two e5-large runs** (submitted, group `cem2`) | 0.9400 | 0.9429 | **0.806** |

**The second epoch is worth +0.005 band AUC on the labelled countries and slightly *hurts* France.** It
specialises on the training countries. So the submitted model feeds stage 2 the **mean of the two
z-scored e5-large logits**, not the single best one — a decision taken against the labelled-country
metric, on label-free French evidence.

Why: on the test band the models are nearly interchangeable where labels exist and diverge sharply where
they do not.

| country | band pairs | corr e5l2–e5l | corr e5l2–bge | sign disagreement, e5l2 vs bge |
|---|---|---|---|---|
| US | 452,178 | 0.985 | 0.978 | 3.1% |
| India | 653,478 | 0.985 | 0.984 | 2.7% |
| **France** | 385,274 | **0.951** | **0.906** | **12.0%** |

A stage 2 given each logit separately learns its splits where the models agree, then extrapolates on
their disagreements in France. Averaging removes that failure mode. This is also why the two e5-large
runs are treated as **one source of evidence**: they correlate at 0.986 on the holdout band, so they are
not two independent votes.

### 4.4 Self-training on the unlabelled country (the submitted model's final step)

France has no labels, so stage 2 is additionally fitted on France's **own test rows** against
pseudo-labels derived from an earlier finished chain (`v7ce3`):

| pair | pseudo-label |
|---|---|
| in the teacher's final matches with pc ≥ 0.9; a rule add (A/APP/ACR); an acronym-join add | 1 |
| not in the final matches with pc ≤ 0.05; an op-B prediction the rules dropped | 0 |
| everything else | unlabelled (−1), still scored |

Over all 1.43M French stage-2 rows: 851,116 positive, 493,352 negative (of which 19,537 are op-B drops),
85,198 unlabelled.

**Cross-fitting, which is what keeps this honest.** French S1 are split into four groups by
`fold_of(s1) % 4`. Model *g* trains on the other groups' pseudo-labels and **alone** scores its own
group's French rows. So no French pair is ever scored by a model that saw its own pseudo-label, or the
pseudo-labels of other records belonging to its S1. US/India rows are handled exactly as before, and
**early stopping and isotonic calibration use labelled rows only.**

Effect on France [proxy, label-free]: op-B predictions above pc 0.7 fall from 28% to **0.4%**; the
uncertain band (pc 0.3–0.99) shrinks from 358 to **186** pairs per 1,000 S1; Σpc per S1 falls from 3.52
to 3.41; final predictions move +14.0 / −17.4 per 1,000 French S1 while US/India move about +1.5 / −0.6.
The rules consequently almost stop firing: 305 op-B drops, against 17,914 for the previous model.

**Why this is a good bet under F0.5 specifically:** it leans toward dropping, and dropping a false
positive gains ≈0.18 while dropping a true pair costs ≈0.07. It is therefore roughly neutral even if only
half its changes are right.

---

## 5. Results & Error Analysis

### 5.1 Scores

| system | holdout macro F0.5 | public leaderboard |
|---|---|---|
| baseline v0 | 0.9683 | — |
| model v1: features v1 + stage 2 + DP | 0.9801 | — |
| model v2: blocking v1 + look-alike odds + cluster support | 0.98436 | 0.97608 |
| model v3: blocking v2 + legal forms in stages 1–2 | 0.98882 | 0.97961 |
| model v4: + cross-encoder + France fixes | 0.99015 | — |
| v5all: all-data fit, France rules v2, candidate cut | 0.99016 | — |
| v6all: blocking v3 repairs, signed number features | 0.990842 (s3) | 0.988609 |
| v7ce3: + e5-large and e5-base logits, stage 3, rules v3, acronym join | 0.991138 (s3) | — |
| v7n: e5-small + z-mean of two e5-large | 0.991211 (s3) | 0.989721 |
| **v7nst (submitted): + France stage-2 self-training** | **0.991194 (s3)** | **0.990179** |

Submitted model, per country [holdout]: US 0.991005, India 0.991472.

Selected gates (paired bootstrap over S1, 1,000 resamples): features v1 +0.0097 [0.0095, 0.0099];
stage 2 vs stage 1 +0.0069 [0.0062, 0.0077]; legal-form features +0.00271 [0.00260, 0.00283]; v3 vs v2
+0.00445 [0.00431, 0.00459]; v7ce3 vs v6all-s3 +0.000296 [+0.000252, +0.000342]; v7n vs v7ce3-s3
+0.000073 [+0.000041, +0.000102]; v7nst vs v7ce3-s3 +0.000055 [+0.000022, +0.000089].
**Rejected** for being below the bar: name-uniqueness features (+0.0005), stage-2 seed bagging
(−0.00004), `max_depth` 8, eta 0.03.

Leave-one-country-out (train US → test India), the evidence behind the France design: 0.961 with India's
words known, **0.882 unseen**, and **0.960** restored by the label-free proxy odds.

### 5.2 The most important result: the holdout ranked the last two models the wrong way round

| | holdout (s3) | public |
|---|---|---|
| v7n | 0.991211 | 0.989721 |
| v7nst (submitted) | 0.991194 (**−0.000017**) | 0.990179 (**+0.000458**) |

The self-training step was **marginally worse on the holdout and decisively better in public**, because
**the shared holdout contains no French entities**. Its gate could only confirm that US/India did not
regress; it was structurally incapable of measuring the thing the change was built to do.

This is the single most transferable lesson of the project: when a test distribution contains a
population your validation set does not, your validation set cannot rank models on it — and a model
selected purely on that validation set will be selected against the shift.

### 5.3 Submitted output, measured

All recomputed from `output/matching_results.tsv` against the provided test sources [measured]:

| property | value |
|---|---|
| rows | 1,732,544 — exactly one per test S1, no duplicates, none missing or extra |
| predicted pairs | 5,856,096 (2,838,803 to S2; 3,017,293 to S3) |
| empty predictions | 100,137 S1 (5.78%) |
| mean predictions per S1 | 3.3801 |
| records claimed by more than one S1 | **0** |
| cross-country predicted pairs | **0** |
| target IDs absent from `test_source2/3.tsv` | **0** |

| country | test S1 | non-empty | predicted pairs | per S1 |
|---|---|---|---|---|
| France | 259,452 (14.98%) | 244,429 | 871,242 | 3.3580 |
| India | 809,986 | 763,186 | 2,735,918 | 3.3777 |
| US | 663,106 | 624,792 | 2,248,936 | 3.3915 |

The three countries predict at almost the same rate (3.358–3.392 per S1) against a training truth of 3.46,
and France is no longer the outlier it was before the France work (3.54 → 3.37 at model v4).

### 5.4 Limits of our own evidence

Stated explicitly, because several of these are easy to overclaim:

1. **France's score was never directly measured.** Every "France ≈ 0.981" figure in our notes is derived
   from `F_France = (LB − 0.843226) / 0.14975`. The 0.14975 is exactly France's share of *whole-test* S1
   (259,452 / 1,732,544 = 0.149752) [measured], so the formula assumes the scored public subset has the
   same country composition as the whole test set. We could not verify that. France levels are
   **estimates**, not measurements.
2. **The submitted model's holdout figure is not an untouched test score.** The final fit (`--all`) uses
   the holdout as a fourth out-of-fold group, and the pipeline was developed against this holdout over
   many iterations. Cross-country gates and paired bootstraps keep comparisons *like for like*; they do
   not make the absolute number an unbiased estimate of generalisation.
3. **The self-trained model cannot be ranked by the rule-population diagnostic.** That diagnostic scores
   how well a model separates op-A/APP/ACR from op-B. The submitted model was *trained on pseudo-labels
   derived from those very populations*, so its 0.984 rule-population AUC is **circular** and is not
   evidence of French accuracy. Cross-fitting by S1 prevents label leakage; it does not turn agreement
   with one's own teacher into independent truth. The honest ranking evidence for French changes is a
   controlled public comparison with all other countries held fixed.
4. **Rule truth rates are transferred, not verified in France.** The 97–99.8% (op A) and 0–1.2% (op B)
   figures are measured on the US/India holdout and *assumed* to carry to France because the generator is
   shared. The label-free French checks are consistent with that, but it remains an assumption.
5. **Not every France component has its own positive holdout gate**, because the holdout has no French
   rows to gate on. Several were adopted on label-free evidence plus a US/India no-regression check.
6. Larger cross-encoders **did** help (§4.3) — an earlier draft of this document claimed the opposite,
   which was true only of e5-base and of adding correlated checkpoints to an average.

### 5.5 Error analysis

- **Precision is 0.998.** The residual wrong merges are look-alikes at the S1's own street: a nudged or
  truncated house number plus a changed legal form or an added business word ("Bright Voya LP 2" vs
  "Bright Voya Corp 3"). In France, before the fixes, op-B word swaps ("Troupe Ecole SAS" → "Troupe
  Centre SAS") were accepted at 65 per 1,000 S1 because French descriptors had no label odds.
- **The model is recall-bound:** missed records are 89% of the holdout loss.
  **69% of misses are empty-address records whose name several S1 share.** From the name alone the owner
  is close to a coin flip, and under F0.5 abstaining is the correct action — roughly 22k of these are
  irreducible rather than fixable. The remainder: blocking misses (domains, OCR digits, ordinal street
  words; +0.0003–0.0005 still available), brand names at a shared address, and nudged house numbers.
- **Loss anatomy** (model v2, full holdout, if each were fixed in isolation): blocking misses +0.00477;
  rejected by the decision +0.00462; lost to ownership +0.00359; predicted orphans +0.00240.

---

## 6. Conclusion

A careful reading of the data — one owner per record, colliding names, and the generator's two edit
operations — shaped a cascade whose collective stage and per-entity decision optimise the actual metric
rather than pairwise accuracy, reaching **0.991194** on the shared holdout and **0.990179** in public.

The decisive problem was the country with no labels. The fix was not a larger model but **label-free
statistics, generator rules whose truth was measured where labels exist, and self-training on the target
country's own pairs** — with cross-fitting to keep it honest. The most valuable single lesson is §5.2:
our validation set could not see France, so it ranked our last two models in the wrong order, and only a
held-fixed public comparison could tell them apart. Every component earned its place through a
paired-bootstrap gate recorded in `docs/decisions/`, and the components that could not be gated are
listed as such in §5.4 rather than presented as proven.

---

## Appendix

### A. Code artefacts

`code/business_entity_resolution/`:

- **`src/ber/`** — the team package, one CLI (`python -m ber.pipeline --stage <stage> --split <split>
  --tag <tag>`): `records`, `block` (multi-view blocking, Indic transliteration, domain/OCR repairs,
  French address normalisation), `features` (context and rivalry), `model` (stage-1 model, isotonic
  calibration, ownership, expected-F0.5 decision), `write` (organiser TSV format), `evaluate` (holdout
  macro F0.5, paired-bootstrap gates).
- **`src/model_v1/`** — the model chain: `feats*.py`, `lo_mix.py` (features); `s1.py` (stages 0–1);
  `ce.py`, `ce_box.py`, `zmean_ce.py`, `ce_import.py` (cross-encoders); `s2.py`, `cluster.py` (stage 2 and
  calibration); `stage3.py`; `decide.py`; `cands_final.py`; `post_ops.py` (France rules);
  `acr_join.py`; `pseudo_labels.py` (self-training labels); `RECIPE.md`.
- **`reproduce.sh`** — every step in order, from the raw TSVs to the outputs and the validator.
  Because the submitted model is self-trained, this **builds the `v7ce3` teacher before the student**;
  cached pseudo-labels are not an undeclared prerequisite.
- **`src/model_v1/audit_matching.py`** — strict output audit. The organiser validator reports a missing
  candidate file, and matches falling outside the candidate set, as *warnings* and still prints `PASS`;
  it also never checks owner uniqueness or country consistency. This script checks all of it and exits
  non-zero, and is what produced §5.3.
- **`requirements.txt`** — pinned. `MANIFEST.sha256` lists the sha256 of every archived file.
- **Hardware:** cross-encoders need a CUDA GPU; everything else runs on CPU (slower). Reference machine
  RTX 5070 Ti 12 GB, 24 cores, 31 GB RAM, plus a rented H100 80 GB for the e5-large runs. Stages 1–3
  peak at 18–19 GB RAM and the two stage-2 fits must run serially. `pytest -q`: **115 passed**.
- **Reproducibility:** seeds fixed in every script; each artifact records the git commit and the command
  that produced it. XGBoost is deterministic on the same machine; **the cross-encoders are not
  bit-reproducible across GPUs**, so a rerun can move a few pairs and change the output hash. The
  reference check is then the holdout macro F0.5 in `work/reports/`, not the file hash. The submitted
  bytes in `output/` are shipped verbatim and are never regenerated.

### B. Compliance

- **Only the provided competition data** was used to resolve entities. No external datasets, web lookups,
  company registries, APIs or geocoders.
- **Hand-written lexicons**, all documented in the code: legal forms, street types, US/India states,
  French departments → regions, generator list words, the OCR digit map, ordinal words.
- **Pretrained models — all ≤ 8B parameters and MIT or Apache-2.0:**

  | model | role | parameters | license |
  |---|---|---|---|
  | XGBoost | stages 0–3 | — | Apache-2.0 |
  | `intfloat/multilingual-e5-small` | stage-2 feature `ce` | 118M | MIT |
  | `intfloat/multilingual-e5-large` | two fine-tunes, z-averaged into feature `cem2` | 560M | MIT |
  | `intfloat/multilingual-e5-base` | **teacher only** — feature `ceb` of `v7ce3`, whose decisions become the pseudo-labels. Needed to reproduce; absent from the submitted model's own feature set. | 278M | MIT |

  Every cross-encoder was fine-tuned **only on our own training pairs**. `BAAI/bge-reranker-v2-m3` and
  `Qwen2.5-1.5B` were evaluated during development and are **not** part of the submitted model.

### C. Additional results

- Blocking recall per country [holdout]: India 0.9875, US 0.9916 (blocking v2).
- Macro F0.5 by stage (model v3, best threshold): stage 1 0.9871, stage 2 0.9887.
- French rule-population AUC of stage-2 `pc` [proxy]: v6all 0.8546 → v7ce3 0.8651 → v7n 0.872, with
  v7m 0.8776 and v7c 0.8741. Every cross-encoder upgrade raised it. **The submitted model's 0.984 is not
  comparable to these** — see §5.4 item 3.
- Stage 3 lowers this proxy AUC by about 0.005 for every model, and moves 2.5 up / 6.5 down per 1,000
  French S1 across the 0.7 threshold. It passed its holdout gate; its effect on France is unmeasured.
- Cross-encoder-level French rule AUC on raw logits (53,290 rule-population band pairs, 57.6% true
  copies): e5-base 0.687, e5-large 1 epoch 0.803, 2 epochs 0.792, **mean 0.806**.

### D. Items not independently confirmed

1. **[confirm]** The registered team name as it appears in the portal — recorded here as "Grenuke".
2. **`torch` / `transformers` versions are only partly recoverable**, and `requirements.txt` records this
   rather than guessing. The two cross-encoder scripts ran on different machines:
   - `ce.py` (multilingual-e5-small, feature `ce`) ran on the integration machine, which still exists, so
     its versions can be read off and pinned.
   - `ce_box.py` (the two e5-large fine-tunes behind feature `cem2`, and e5-base for the `v7ce3` teacher)
     ran on a rented H100 with non-persistent disk that was destroyed on 26 Sep (§6.9 of the research log).
     **Those exact versions are unrecoverable.** This does not affect reproducibility of the *method*: any
     recent CUDA-enabled torch/transformers runs the same recipe, and the cross-encoders are not
     bit-reproducible across GPUs regardless, so the reference check is the holdout macro F0.5 rather than
     the logits or the output hash.
3. **The three France threshold probes were not audited here.** Their sha256 are recorded (matching
   `f16af635…` / `a0da9110…` / `8d1290fa…` for fr080r / fr090r / fr095r), but the files live on the
   integration machine, so their reported change counts remain second-hand. Only the submitted package was
   independently verified.
