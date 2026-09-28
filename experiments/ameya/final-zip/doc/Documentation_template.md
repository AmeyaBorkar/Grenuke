# ML Challenge 2026: Business Entity Resolution Solution Template

**Team Name:** Grenuke  
**Team Members:** Ameya Borkar, Aarush Bakshi, Sachi Dhoka  
**Submission Date:** 29 September 2026 (the files in this package are our best leaderboard submission, "Composite B", public macro F0.5 **0.990879**)

### Contents

| section | what it covers | the organisers' item |
|---|---|---|
| [1. Executive Summary](#1-executive-summary) | the approach, the pipeline figure, the rules we kept | |
| [2. Methodology](#2-methodology) | [2.1 Problem Analysis](#21-problem-analysis), [2.2 Solution Strategy](#22-solution-strategy) | methodology used |
| [3. Candidate Generation (Blocking)](#3-candidate-generation-blocking) | keys, candidate counts, recall | candidate generation / blocking strategy |
| [4. Matching Model](#4-matching-model) | features, model stages, cross-encoders, decision | model architecture and feature engineering |
| [5. Results & Error Analysis](#5-results--error-analysis) | scores, the score build-up, common errors | other relevant information |
| [6. Conclusion](#6-conclusion) | results and lessons | |
| [Appendix A. Code Artefacts](#a-code-artefacts) | package layout, how to run, hardware, reproducibility | other relevant information |
| [Appendix B. Additional Results](#b-additional-results) | ablations, the cross-encoder mix, the 7B re-check, what did not work | other relevant information |

---

## 1. Executive Summary

- **Pipeline.** We match each Source-1 business to its Source-2/3 copies with a precision-first pipeline:
  - per-country multi-view blocking;
  - three gradient-boosted scoring stages on name, address and legal-form evidence;
  - fine-tuned multilingual cross-encoders on the uncertain pairs: e5, bge, and LoRA-tuned Qwen2.5-1.5B/7B;
  - a per-S1 decision that maximises expected F0.5.
- **France.** It appears only in the test set.
  - We self-trained on our own guarded, cross-fitted French decisions, for two rounds.
  - An independent Qwen2.5-7B re-check of the confident predictions removed French look-alike decoys that string models accept.
- **Scores.** 0.9913 macro F0.5 on a labelled US/India holdout, and 0.990879 on the public leaderboard.

![Figure 1: the pipeline, with test-set counts at each stage](figures/fig1_pipeline.png)

*Figure 1. The pipeline, with test-set counts at each stage. The dashed loop is the French self-training (§2.2).*

**Rules we kept:**
- **Only the provided data.** No external databases, APIs or look-ups.
- **Hand-written lexicons** are spelling equivalences only:
  - legal forms, street types, state and region names;
  - list-append words, the OCR digit map, ordinal words.
- **Models:** every one is MIT or Apache-2.0 and at most 8B parameters. The largest is Qwen2.5-7B, with 7.6B.

---

## 2. Methodology

### 2.1 Problem Analysis

**The task, as the metric sees it:**
- Each S1 business has 0–11 noisy vendor copies in S2/S3, 3.46 on average.
- About 5.6% have none. For those, an empty prediction scores 1 and any prediction scores 0.
- F0.5 weights precision twice as much as recall. So a wrong pair costs more than a missed one, and we designed for precision first.

**How true copies differ from the original** (measured on labelled pairs):
- case and accent changes;
- legal forms reformatted or dropped: LLC / Inc / Pvt Ltd, and in France SARL / SAS / EURL in about 23% of copies;
- word reorders and list appends ("& Fils", "Services");
- acronyms, typos and whole-word garbles;
- street-type abbreviations (Rue → R., Avenue → Av);
- city-first ordering, and region or department swaps;
- house-number changes, and empty addresses.

The blocking keys (§3) and the features (§4) are built around these edits.

**Decoys:**
- The test set has about 23% more records per S1 than train, while true matches per S1 stay flat. So the extra records are look-alike decoys:
  - a business word swapped at the same address;
  - a nudged house number;
  - the same name at another address.
- 46–54% of S1 share their name with another S1, so the address has to decide.
- Our response:
  - features for each look-alike edit;
  - candidates compete per S1 in a set-level decision;
  - every record is owned by at most one S1.

**France** (test only, no labels):
- **Generic names** (city + category word, e.g. "lille club sarl"). Each French decoy we removed shares its name with a median of 43 other French S1.
- **Shared addresses:** about 11% of French S1 share their exact address with another S1.
- **Administrative names:** about 32% of French addresses carry department or region names.
- **What our first uploads showed.** They scored 0.976–0.980 on the leaderboard, against 0.984–0.989 on the US/India holdout, which implied France at about 0.93. That gap is why most of our later work targets France:
  - per-country statistics and French address normalisation;
  - self-training;
  - a second opinion on confident pairs.

### 2.2 Solution Strategy

**Approach Type:** Hybrid.
- Multi-key blocking → gradient-boosted pair classifiers (three stages) → transformer cross-encoders on the uncertain band → per-S1 expected-F0.5 set selection → rules → an LLM re-check of confident predictions.

**Core Innovation:**
1. **Self-training for a country without labels.**
   - French pairs are pseudo-labelled from our best model's final decisions: positive if kept with calibrated p ≥ 0.9, negative if rejected with p ≤ 0.05, otherwise unlabelled.
   - The labels are guarded: rule-derived populations override them, and empty-address records keep round-1 labels.
   - They are cross-fitted by S1 group, so no French pair is scored by a model that saw its own label.
   - Two rounds, each taught by the previous best model.
2. **A set-level decision.** For each S1 we choose the prediction set with the highest *expected* F0.5 under calibrated probabilities, instead of thresholding each pair.
3. **An independent re-check of confident predictions.**
   - 94.5% of final predictions have stage-1 p1 > 0.99, so no cross-encoder ever read them.
   - A LoRA-tuned Qwen2.5-7B re-reads them and removes the pairs it rejects (logit < −6).
   - The cut-off was fixed on labelled data first.

**How we decided what to keep:**
- **US/India.**
  - A fixed shared holdout: 25% of train S1 (549,699 S1), never used for fitting, scored with the official macro F0.5.
  - A component was added only when a paired bootstrap on this holdout showed a gain. Ties went to the simpler option.
  - Post-hoc rules also had to gain on both fixed halves of the holdout.
- **France.**
  - Label-free checks, e.g. predicted matches per S1 against the generator's limit.
  - Estimates corrected with the 7B's judgement.
  - Leaderboard probes that changed only France.

---

## 3. Candidate Generation (Blocking)

**Blocking keys used** (blocking v3, `ber.block`):
- **Per-country search.** Every search runs per exact country label, so IDF weights and neighbours are never borrowed across countries. Records with an empty label join every partition.
- **Token view:**
  - IDF-weighted token overlap over name + address, in both directions: each S1's top 40 records and each record's top 8 S1;
  - a pair is kept if the record is in the S1's top 15 or the S1 is in the record's top 4;
  - name-word compound keys, and a (house number, street word) key that skips street types, so French addresses match.
- **Names-only view,** for records whose address is empty or has at most 3 tokens:
  - character 4-grams, which catch garbles;
  - single-token names of 8+ letters, which catch domains and handles such as `renterianaborweddle.com`.
- **Repairs before matching:**
  - domain and handle names segmented into the country's S1 words;
  - OCR digits in names repaired;
  - an Indic→Latin token dictionary (693 entries, e.g. `kanstrakshan → construction`), learned only from true pairs of the training folds.

**Candidate pairs generated:**
- **Retrieval:** 66.4M train and 58.4M test pairs.
- **Cut:**
  - a stage-0/1 gradient-boosted scorer keeps pairs with p1 ≥ 0.02;
  - for each record it also keeps its two highest-scoring S1;
  - acronym joins are added.
- **Submitted file:** `candidate_pairs.tsv` has **6,410,308 pairs, 3.70 per test S1**.

**How you ensured true matches were not lost:**
- **Measured, not assumed.** We tracked blocking recall on the holdout. **99.1% of true holdout pairs are candidates**: 16.5k of about 1.9M are missed, mostly empty-address records whose name was changed.
- **One key per noise type:**
  - n-grams catch garbles;
  - the domain key catches web-style names;
  - house numbers and address words catch renamed businesses;
  - transliteration catches Indic script.
- **The cut was tested.** Tighter candidate cuts (top-1 per record; p1 ≥ 0.05) lost −0.000106 and −0.000041 holdout F0.5, so we kept the more generous cut.

---

## 4. Matching Model

**Features used.** All IDF statistics are fitted per country; there is no country feature.

| group | features |
|---|---|
| **Name** (normalised core names, legal forms stripped) | character ratio, token-sort, token-set, partial ratio, Jaro-Winkler · token Jaccard and containment both ways · IDF-weighted token cosine · first/last-token agreement · space-free similarity for domains and hashtags · Indic-script mismatch · legal form equal / compatible / conflict / missing, plus an 8-feature legal-form group · "unexplained token" counts and IDF mass on each side, with an edit-distance substitution flag · learned look-alike odds (per-token log-odds from training folds only) |
| **Address and house number** | house number: equal, truncation, suffix, letter/bis suffix, nudge (1–10), absolute and relative difference, digit edit distance, set Jaccard, S1-only / record-only numbers, unit equality · edit profile: ±1 move, digit substitution, digit swap, suffix, length difference · street-token Jaccard and IDF overlap, street Jaro-Winkler · city and state equality · whole-address token-set and character 3-gram cosine · empty / short / landmark / PO-box / null flags, token counts |
| **Context** | retrieval: the pair's score and rank in each blocking view, and how many views found it · rivalry: gap to the S1's best candidate, margin over any other S1 for the same record · log-counts of candidates and of S1 sharing the name (counts, not rates, so France's smaller pool is not over-weighted) · per-S1 aggregates of p1: expected cluster size, counts above thresholds, rank · cluster support: similarity to the S1's other confident records · source (S2/S3) · the cross-encoder score (below) |

**Model type:**
- **XGBoost (GPU), four stages.** Each stage is out-of-fold over three S1 groups, so the next stage learns from honest scores. Seeds are fixed.
  - Stage 0 prunes about 80% of pairs cheaply.
  - Stage 1 gives p1, which sets the candidate cut and the cross-encoder band.
  - Stage 2 adds the cross-encoder, cluster and per-S1 features. It also adds the French pseudo-labelled rows: cross-fitted, with weight 3 in the model behind France's predictions and weight 1 in the US/India model.
  - Stage 2 is isotonic-calibrated on out-of-fold scores.
  - Stage 3 re-scores each pair in the context of its S1's other candidates.
- **Cross-encoders** run only on the uncertain band, 0.02 ≤ p1 ≤ 0.99: 1.57M train and 1.49M test pairs. That's where reading the text pays.
  - Input: `name ; address` of both sides, at most 96 tokens.
  - Each is three out-of-fold models.
  - The French-facing members also train on French pseudo-labelled pairs, cross-fitted by S1 third.

  | model | size | licence | training | band AUC (holdout) |
  |---|---|---|---|---|
  | stage-1 p1, for reference | | | | 0.930 |
  | multilingual-e5-small | 118M | MIT | full fine-tune, 1 epoch, lr 5e-5 | |
  | multilingual-e5-base (round-1 French teacher only) | 278M | MIT | full fine-tune | |
  | multilingual-e5-large (+ French self-trained) | 560M | MIT | full fine-tune, 1 epoch, lr 2e-5, batch 128 | 0.939 (0.944) |
  | bge-reranker-v2-m3 (+ French self-trained) | 568M | Apache-2.0 | same as e5-large | 0.942 (0.942) |
  | Qwen2.5-1.5B, French self-trained | 1.5B | Apache-2.0 | LoRA | 0.938 |
  | Qwen2.5-7B, French self-trained | 7.6B | Apache-2.0 | LoRA | 0.944 |

  - **The Qwen models** use a one-logit classification head with LoRA:
    - r 16, α 32, dropout 0.05, on all attention and MLP projections;
    - bf16, AdamW, lr 1e-4 with 3% warm-up, batch 64, 1 epoch.
    - The 7B trained on three H100s, one out-of-fold model per GPU, in about 2 hours.
  - **Why a mix, not the biggest model:** the 7B's band AUC (0.944) only matches the self-trained e5-large (0.944). Its value is diversity: a different model family in the mix, and an independent reader of confident pairs.
  - **The mix.** The z-scored logits are averaged into one stage-2 feature. Separate logits made stage 2 extrapolate where the models disagree, which is 4× as common in France.
    - US/India: e5-large, French-self-trained e5-large, bge, Qwen2.5-1.5B, and Qwen2.5-7B counted twice.
    - France: Qwen2.5-1.5B, two e5-large seeds and bge, all self-trained, plus a France-weighted e5-large.

**Threshold selection method:**
- **Expected-F0.5 set selection.** Calibrated stage-3 probabilities feed a dynamic programme over each S1's owned candidates. It picks the prefix with the highest expected F0.5.
  - It replaced a tuned global threshold after a paired bootstrap on the holdout: +0.000048 [+0.000007, +0.000091], together with the acronym join and caps.
  - Settings tuned on the holdout:
    - logit shift +0.2;
    - −0.3 for records contested by 4 or more S1;
    - a 0.01 expected true match outside the candidates, a recall term.
- **Ownership:** each record goes to its highest-scoring S1.
- **Rule layers:**
  - acronym join;
  - per-source caps;
  - for France:
    - an exact-address copy rule, 99.99% precise on US/India;
    - a cross-commune drop;
    - a look-alike word-swap drop;
    - the same expected-F0.5 set selection applied to France's stage-3 probabilities, where France had used a threshold until then.
- **The 7B re-check cut-off (−6).** Chosen on the holdout, where it gave the largest gain: +0.000037, positive in both fixed halves and in 99.7% of 3,000 random holdout subsets. Looser cut-offs gained less (−5: +0.000029; −4: +0.000017), and from −3 on they lose.

---

## 5. Results & Error Analysis

**F_0.5 Score (macro):**

| evaluation | macro F0.5 |
|---|---|
| labelled holdout (US/India, 549,699 S1) | **0.9913** (US 0.9911, India 0.9916); micro precision 99.9%, recall 97.5% |
| public leaderboard (US, India and France) | **0.990879** |

**Where the score came from.** Each step is a leaderboard submission built on top of the previous one.

![Figure 2: public leaderboard score, step by step](figures/fig2_score.png)

*Figure 2. Public leaderboard macro F0.5 after each step, with the gain over the previous step. The last bar is the submission in this package.*

**Common false positives (wrong merges):**
- ***Generic-name decoys* (France),** e.g. `lille ecole sarl | 42 rue gutenberg` vs `lille ecole sarl | 42 q. du wault`: same name and house number, different street.
  - On labelled data this pattern is 0.5% true where our model rejects it, and 99.7% true where it accepts it.
  - String features cannot separate the two cases; the 7B could.
  - Removing its 840 French rejects gave an estimated +0.00011 of our last +0.00018.
- ***Business-word swaps at the same address*** ("antenne danse" vs "antenne gaz").
- ***Near-identical short names*** ("osd" vs "otd").
- ***Chain branches*** sharing one name.

**Common false negatives (missed matches):**
- **Where the loss is.** On the US/India holdout the model is 99.9% precise, so the remaining loss is mostly recall:
  - 69% comes from partially-missed S1;
  - 20% from S1 missed entirely;
  - 8% from false positives.
- **Which pairs are missed:** mostly empty-address copies with changed or invented names. They either never become candidates (16.5k) or are scored near 0 (15.2k).
- **Garbles:** heavy garbles also cause misses, e.g. the French "EHPAD" typed as "ehpvd" or "phpad".
- **We did not add recall rules.** Every one we tried was 17–71% precise, below the ~75% a match needs to help F0.5:
  - empty-address name match;
  - an alias at the same address;
  - the top candidate of an empty S1;
  - 7B-confirmed additions.

---

## 6. Conclusion

- **Results.** A precision-first design with calibrated, set-level decisions brought the labelled countries to 0.9913. Guarded self-training carried France, which has no labels, most of the way.
- **The 7B re-check.** An independent re-check of the "obvious" predictions found decoys that feature models accept.
- **What we learned:**
  - Self-training paid for two rounds. A third round did not beat them without the same French decision layers.
  - Without labels, a probability-based estimate needs a second, independent judge, because it inherits the model's blind spots.

---

## Appendix

### A. Code Artefacts

`code/business_entity_resolution/` regenerates both output files from the raw train/test TSVs.

| path | contents |
|---|---|
| `reproduce.sh` | the entry point. `VARIANT=compositeB` (the default) runs `src/box/compositeB.sh` |
| `src/ber/` | the team package: I/O, IDs, normalisation, blocking, context features, output writer, evaluation (holdout split, macro F0.5, paired bootstrap). One CLI: `python -m ber.pipeline --stage <stage> --split <split> --tag <tag>` |
| `src/model_v1/` | pair features, stages 0–3, cross-encoder training (e5/bge; Qwen LoRA), self-training labels, the decision, the rules, the stacked rules and France layers, `pipeline/france_mixmdp.sh` (France) |
| `src/box/` | the Composite B driver, the Qwen2.5-7B out-of-fold training (`llm_group.py`, `llm_merge.py`), the 7B re-check (`rescore_export.py`, `score_pairs.py`), and the per-country composition (`compose_tsv.py`) |
| `tests/`, `requirements.txt`, `README.md` | unit tests, pinned versions, exact run instructions |

**How to run** (from the unzipped package; details in `README.md`):

```bash
pip install -r code/business_entity_resolution/requirements.txt && pip install -e code/business_entity_resolution
MODEL_DIR="$PWD/code/business_entity_resolution/src/model_v1" BER_OUTPUT_DIR="$PWD/output_rerun" \
  VARIANT=compositeB bash code/business_entity_resolution/reproduce.sh
```

**What the driver runs:**
1. The US/India chain: records → blocking → features → stages 0–1 → cross-encoders → stages 2–3 → decision → rules. The round-1 French teacher is built along the way.
2. French pseudo-labels from that model.
3. Qwen2.5-7B training (three out-of-fold groups).
4. The US/India model with the 7B in the mix.
5. The 7B re-check of confident predictions.
6. The France block (round-2 guarded labels ×3 and the French layers).
7. Per-country composition, the 7B drops, the validator and a strict audit.

**Hardware and time:**
- **CPU stages:** 24+ cores, 32 GB RAM.
- **Cross-encoders:** one H100 80 GB.
- **Qwen2.5-7B:** three 80 GB GPUs, about 2 hours.
- **Per-step times** are in `README.md`; the GPU stages dominate.
- **Software:** Python 3.12–3.13, torch 2.11, transformers 5.17, peft 0.21, xgboost 3.2.0.
- **Model revision:** Qwen2.5-7B `d149729398750b98c0af14eb82c78cfe92750796`.

**Reproducibility:**
- Seeds are fixed, and every artifact records its command and git commit.
- GPU training is not bit-deterministic across machines.
  - Rebuilding an earlier model on different hardware gave 0.991261 holdout F0.5, against 0.991246 originally.
  - It moved 1–4 predictions per 1,000 S1.
- So a rerun lands within about ±0.0001. `output/` holds the exact submitted bytes, and the final composition reproduces `matching_results.tsv` byte-for-byte from the saved intermediates.

### B. Additional Results

**Ablations** (labelled US/India holdout; paired bootstrap):

| change | effect on macro F0.5 |
|---|---|
| expected-F0.5 set selection vs a tuned threshold | +0.000048 [+0.000007, +0.000091] |
| Qwen2.5-7B ×2 in the cross-encoder mix | India +0.000066 (P 0.998), US +0.000026 |
| 7B re-check (drop logit < −6) | +0.000037, both halves positive |
| tighter candidate cut (top-1 / p1 ≥ 0.05) | −0.000106 / −0.000041 |
| French self-training, round 1 / round 2 (leaderboard) | +0.00046 / +0.00015 |

**The cross-encoder mix** (holdout after stage 3 and the decision; only the mix changes):

| mix | overall | US | India |
|---|---|---|---|
| e5-large, e5-large self-trained, bge, Qwen2.5-1.5B | 0.991261 | 0.991064 | 0.991558 |
| + Qwen2.5-7B ×1 | 0.991276 | 0.991076 | 0.991577 |
| **+ Qwen2.5-7B ×2 (used)** | **0.991323** | **0.991114** | **0.991635** |
| + Qwen2.5-7B ×3 | 0.991322 | 0.991111 | 0.991639 |
| Qwen2.5-7B alone | 0.991286 | 0.991089 | 0.991581 |

**The 7B re-check.** The table covers predictions with p1 > 0.99 that no cross-encoder had read: 631,001 predictions on a labelled 34% holdout sample, plus the French test predictions.

| 7B logit | holdout predictions | truly a match | French predictions |
|---|---|---|---|
| < −6 | 24 | 8.3% | 859 |
| [−6, −4) | 51 | 86.3% | 209 |
| [−4, −2) | 138 | 94.9% | 321 |
| [−2, 0) | 6,616 | 99.6% | 897 |
| [0, 2) | 16,893 | 99.8% | 4,461 |
| ≥ 2 | 579,440 | 100.0% | 780,629 |

- **Rejection rates:** the 7B rejects 0.10% of French predictions, against 0.004–0.007% of US/India ones.
- **Leakage check:** the rejection rate is the same in each third of French S1 (0.107–0.112%), including the third the model never saw labels for.

**Controls on the leaderboard:**
- **Composite B with the round-3 French model, without the French decision layers:** 0.990833, −0.000046.
  - By our 7B-corrected estimate, the missing French expected-F0.5 decision accounts for about +0.00005.
  - The round-3 model itself was slightly better.
- **Composite B with the French 7B drops extended below −6** (1,699 more drops, 251 look-alikes restored): 0.990875, a tie. The −6 cut-off was already right.

**What did not work** (measured, then dropped):
- **Recall rules**, 17–71% precise:
  - empty-address name matches;
  - aliases at the same address;
  - rescuing an empty S1's top candidate;
  - 7B-confirmed additions.
- **A learned blend of all six cross-encoder logits** as the decision score: band AUC 0.9575 against 0.9276, but −0.001 macro F0.5.
- **A decision tree mining extra drops:** +0.000033 on one half, −0.000015 on the held-out half.
- **Copy-count tie-breaking** for empty-address records: owner accuracy 0.31, against 0.27 by chance. An add rule on it loses about 0.00057.
- **Renormalising French probabilities per record:** −0.000007 to −0.000137.
- **Other encoders:**
  - Qwen3-4B scored below the 7B (band AUC 0.941).
  - mDeBERTa-v3 hit non-finite bf16 gradients.
  - gte-multilingual-reranker's remote code crashed under our transformers version.
