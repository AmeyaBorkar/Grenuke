# ML Challenge 2026: Business Entity Resolution Solution Template

**Team Name:** Grenuke  
**Team Members:** Ameya Borkar, Aarush Bakshi, Sachi Dhoka  
**Submission Date:** 29 September 2026

### Contents

- [1. Executive Summary](#1-executive-summary)
- [2. Methodology](#2-methodology)
- [3. Candidate Generation (Blocking)](#3-candidate-generation-blocking)
- [4. Matching Model](#4-matching-model)
- [5. Results & Error Analysis](#5-results--error-analysis)
- [6. Conclusion](#6-conclusion)
- [Appendix A. Code Artefacts](#a-code-artefacts)
- [Appendix B. Additional Results](#b-additional-results)

---

## 1. Executive Summary

Our submission, which we call Composite B, scores **0.990879 macro F0.5 on the public leaderboard**. On our own **local validation** set, a held-out quarter of the labelled US and India data, the same pipeline scores **0.9913**. That set has no French records, because France has no labels.

The pipeline makes three passes. **Blocking** looks up candidate records for each Source-1 (S1) business one country at a time, and a gradient-boosted classifier cuts them down to **3.70 per S1** while keeping **99.1% of the true pairs**. More **gradient-boosted models** then score every candidate pair. On the pairs they are least sure about, fine-tuned multilingual **cross-encoders** help: e5, bge, and **Qwen2.5-1.5B and 7B** with LoRA. Finally, for each S1 we pick the set of records with the **highest expected F0.5**. There is no global threshold.

**France was the hard part.** It appears only in the test set, so we had nothing to train or validate on there. We **self-trained on our own French decisions**, with guards and cross-fitting so the model would not simply confirm its own mistakes. We also had a **Qwen2.5-7B model re-read the predictions** the pipeline was already certain about, and that second reading removed a group of **French decoys** that string features could not separate.

![Figure 1: the pipeline](figures/fig1_pipeline.png)

**Figure 1.** The pipeline, from records (left) to matches (right). The dashed line is the French self-training loop (Section 2.2).

---

## 2. Methodology

### 2.1 Problem Analysis

Each S1 business has between **0 and 11 copies** in the Source-2 and Source-3 files, 3.46 on average, and about **5.6% have none** at all. The metric is F0.5 averaged over S1, so **a wrong merge costs twice as much as a missed copy**. An S1 with no copies also scores zero as soon as we predict anything for it. That pushed the whole design towards **precision**.

The copies are **noisy**. In the labelled data we found case and accent changes, **legal forms** dropped or rewritten (in France, SARL, SAS or EURL changes in about 23% of copies), reordered or appended words, **acronyms**, typos, shortened **street types** ("Rue" to "R."), reordered addresses, changed **house numbers** and **empty addresses**. Most of our blocking keys and features target one of these edits directly.

The test set also contains **decoys**. It has about **23% more records per S1** than the training set but the same number of true matches, so the extra records are **look-alikes**: a different business word at the same address, a nudged house number, or the same name somewhere else. Between **46% and 54% of S1 share their name** with another S1, so the **address** usually settles the match. We therefore let candidates **compete within each S1**, and each record can belong to **at most one S1**.

**France** is harder still. Its names are **generic**, a city plus a category such as "lille club sarl", and each French decoy we removed shares its name with a median of **43 other S1**. About **11%** of French S1 share their exact address with another S1, and **32%** of French addresses contain a department or region name.

We noticed early how much this mattered. Our first uploads scored **0.976 to 0.980** on the leaderboard, while our local validation said **0.984 to 0.989**. The only thing the leaderboard had that our validation lacked was France. Working backwards put **France at around 0.93**, and most of what we did afterwards was aimed at it.

### 2.2 Solution Strategy

**Approach Type:** Hybrid. **Blocking** generates candidates, three stages of **gradient-boosted classifiers** score the pairs, **cross-encoders** read the uncertain pairs, a **per-S1 decision** picks the final set, **rules** clean up known patterns, and an **LLM re-checks** the confident predictions (Figure 1).

**Core Innovation:** three ideas carried most of the gain.

*Self-training for a country without labels.* We **pseudo-label French pairs** from our best model's final decisions. A pair it kept with a calibrated probability of **at least 0.9** becomes a positive, one it rejected at **0.05 or below** becomes a negative, and everything in between stays unlabelled. Two **guards** stop the model from reinforcing its own errors: where our rules decided a population, the rules win, and empty-address records keep their first-round labels. The labels are also **cross-fitted by S1 group**, so a French pair is never scored by a model trained on its own label. The first round added **+0.00046** on the leaderboard, and the second round, together with the French decision layers, another **+0.00015**.

*A decision that optimises the metric directly.* For each S1, a small **dynamic programme** over the calibrated candidate probabilities finds the prediction set with the **highest expected F0.5**. On our local holdout this beat the best global threshold by **+0.000048** (95% interval 0.000007 to 0.000091).

*A second opinion on predictions we were sure about.* **94.5%** of our final predictions have a stage-1 probability above 0.99, so **no cross-encoder ever looked at them**. A LoRA-tuned **Qwen2.5-7B** reads them again, and we drop the ones it rejects with a **logit below −6**, a cut-off we fixed on labelled data first. It dropped **840 French predictions**. On labelled data, only **8%** of predictions rejected that strongly are real matches.

*How we decided what to keep.* For US and India we held out a **fixed 25% of the training S1** (549,699 S1) and never trained on it. A component stayed only if it gained on that holdout in a **paired bootstrap**, and ties went to the simpler option. Rules added late also had to gain on **both halves** of the holdout. France has no labels, so there we relied on label-free checks, on estimates corrected with the 7B model's judgements, and on **leaderboard submissions that changed France alone**.

---

## 3. Candidate Generation (Blocking)

**Blocking keys used:** All searches run **separately per country**, so IDF weights and nearest neighbours never mix countries. Records without a country are searched in every partition. Table 1 lists the **three views**. The **token view** does most of the work. The **names-only view** covers records whose address is empty or very short, and the **repairs** fix names before any matching.

**Table 1.** Blocking views.

| view | how it matches | what it catches |
|---|---|---|
| **Token view** | IDF-weighted overlap on name + address, both ways: each S1's top 40 records and each record's top 8 S1. A pair is kept if it is in the S1's top 15 or the record's top 4 | most copies. A (house number, street word) key that skips street types handles French addresses |
| **Names-only view** | character 4-grams; single-token names of 8 or more letters | empty or short addresses, garbled names, domains and handles |
| **Repairs** | domain names split into the country's words; OCR digits in names fixed; an Indic-to-Latin dictionary of 693 entries learned from training pairs | web-style names, OCR errors, transliterated names |

**Candidate pairs generated:** Retrieval produces **58.4M pairs** on the test set (66.4M on train). A first gradient-boosted scorer (stages 0 and 1) keeps every pair with **p1 ≥ 0.02**, plus the **two best S1 for each record**, and we add pairs found by matching acronyms. The candidate file has **6,410,308 pairs, 3.70 per test S1**.

**How you ensured true matches were not lost:** We **measured recall** on the local holdout at every change instead of assuming it. The candidate set contains **99.1% of the true holdout pairs**. Most of the 16.5k it misses (out of about 1.9M) are **empty-address copies** whose name was also changed. Two **tighter cuts**, keeping only the best S1 per record or raising the threshold to 0.05, lowered holdout F0.5 by 0.000106 and 0.000041, so we kept the looser cut.

---

## 4. Matching Model

**Features used:** All statistics are **fitted per country** and there is **no country feature**, so nothing in the model is tied to US or India. Table 2 groups the features and says why each group is there.

**Table 2.** Feature groups.

| group | main features | why |
|---|---|---|
| **Name** | fuzzy ratios (token-sort, token-set, partial, Jaro-Winkler); token Jaccard and containment; IDF-weighted cosine; legal-form agreement; counts of unexplained tokens; learned look-alike word odds | a copy keeps the rare words of a name, while a decoy swaps one business word |
| **Address and house number** | house-number equality, nudges of 1 to 10, digit edits and suffixes; street overlap; city and state; whole-address similarity; empty and PO-box flags | when two businesses share a name, the address tells them apart |
| **Context** | rank in each blocking view; the gap to the S1's best candidate and to rival S1; name-collision counts; per-S1 aggregates; cluster support; the cross-encoder score | a pair is judged against its competitors, not on its own |

**Model type:** The pair classifiers are **four XGBoost stages**. Each is trained **out-of-fold** over three S1 groups, so every stage learns from honest scores of the one before it.
- **Stage 0** removes about **80% of pairs** cheaply.
- **Stage 1** produces the probability **p1**, which sets the candidate cut and decides which pairs go to the cross-encoders.
- **Stage 2** adds the cross-encoder score, per-S1 and cluster features, and the **French pseudo-labelled rows**. Its output is **calibrated** with isotonic regression.
- **Stage 3** re-scores each pair against the other candidates of its S1.

The **cross-encoders** only see the **uncertain band**: pairs with 0.02 ≤ p1 ≤ 0.99, which is **1.49M** on the test set. Each is trained as three out-of-fold models on the text "name ; address" of both records, cut to 96 tokens. We **average their z-scored logits into one stage-2 feature**, because given separate scores, stage 2 extrapolated on pairs where the models disagree, and they disagree about **four times as often in France**.

Table 3 lists the models. French self-trained versions of e5-large and bge are also in the mix, and e5-base (278M, MIT) was used only for the first French teacher. The **7B model is no more accurate** than a self-trained e5-large; both score **0.944**. It earns its place in two ways: counted twice in the US/India mix it adds **diversity**, and it gives an **independent reading** of confident pairs in the re-check.

**Table 3.** Cross-encoders. Band AUC is measured on labelled pairs from the local holdout; stage-1 p1 alone reaches 0.930 on the same pairs.

| model | size | licence | training | band AUC |
|---|---|---|---|---|
| multilingual-e5-small / e5-large | 118M / 560M | MIT | full fine-tune | 0.939 (large) |
| bge-reranker-v2-m3 | 568M | Apache-2.0 | full fine-tune | 0.942 |
| Qwen2.5-1.5B | 1.5B | Apache-2.0 | LoRA | 0.938 |
| **Qwen2.5-7B** | 7.6B | Apache-2.0 | LoRA (r 16, alpha 32), three H100s for about 2 hours | **0.944** |

**Threshold selection method:** There is **no single threshold**. The calibrated stage-3 probabilities go into the **expected-F0.5 selection** from Section 2.2. Three settings were tuned on the local holdout: a **logit shift of +0.2**, a further **−0.3** for records that four or more S1 compete for, and **0.01** expected true matches outside the candidate set. Each record is then assigned to its **highest-scoring S1**.

**Rule layers** follow. Acronym joins and per-source caps apply everywhere, and France also gets an **exact-address copy rule** (99.99% precise on US and India), a **cross-commune drop**, a **look-alike word-swap drop**, and the same set selection run on France's own probabilities. The last step is the **7B re-check at −6**. That cut-off had the **largest gain on the local holdout (+0.000037)**, positive in both halves and in 99.7% of random subsets.

---

## 5. Results & Error Analysis

**F_0.5 Score (macro):** Table 4 compares the **official leaderboard score** with our **local validation**. The local number is higher because **France cannot be part of it**, and most of the gap comes from France. The **private leaderboard**, which decides the final ranking, had not been published when we wrote this.

**Table 4.** Macro F0.5.

| evaluation | macro F0.5 |
|---|---|
| public leaderboard, official (US, India and France) | **0.990879** |
| local validation: labelled holdout, US and India only (549,699 S1) | 0.9913 (US 0.9911, India 0.9916); precision 99.9%, recall 97.5% |

Figure 2 shows how the leaderboard score grew over our submissions. The largest steps were the **e5-large cross-encoders (+0.0011)** and the **blocking repairs together with stage 3 (+0.0008)**. **French self-training** added +0.00046, and the last step, the **7B model in the mix plus the re-check**, added +0.00018.

![Figure 2: public leaderboard score over our submissions](figures/fig2_score.png)

**Figure 2.** Public leaderboard score after each step. The last point is the submission in this package.

**Common false positives (wrong merges):** The most expensive errors were **generic-name decoys in France**: the same generic name and house number on a **different street**, such as "lille ecole sarl, 42 rue gutenberg" against "lille ecole sarl, 42 q. du wault". On labelled data this pattern is a real match **0.5%** of the time when our model rejects it, and **99.7%** of the time when it accepts it. String features cannot tell the two apart, but **the 7B model can**, and removing its 840 French rejects was worth an estimated **+0.00011** of the final +0.00018. Smaller groups of errors are **business words swapped** at the same address ("antenne danse" and "antenne gaz"), very **short names** that differ by one letter ("osd" and "otd"), and **branches of a chain** that share a name.

**Common false negatives (missed matches):** Precision on the local holdout is **99.9%**, so most of the remaining loss is **recall**. **69%** of it comes from S1 where we found some copies but not all, and **20%** from S1 we missed completely. The missed copies are mostly records with an **empty address and a changed name**, which either never become candidates (16.5k) or get a score near zero (15.2k). **Heavy garbles**, such as the French "EHPAD" typed as "ehpvd", account for more. None of the recall rules we tried was more than **71% precise**, and under F0.5 an added pair must be right about **75%** of the time to help, so we did not add any.

---

## 6. Conclusion

On US and India, a **precision-first pipeline** with **calibrated per-S1 decisions** reached **0.9913** on our local validation. On the public leaderboard, which includes France, the submission scored **0.990879**. **Self-training** on our own guarded decisions got France most of the way without any labels. The **7B re-check** showed that a second, independent model can catch decoys that feature-based models accept with confidence.

Two lessons stay with us. Self-training helped for **two rounds**, and a third did not add to them. And on a country without labels, any estimate built from the model's own probabilities needs an **independent check**, because it shares the model's blind spots.

---

## Appendix

### A. Code Artefacts

`code/business_entity_resolution/` **regenerates both output files** from the raw train and test TSVs. Its `README.md` gives the exact commands, the run time of each step, and what each step should print.

`reproduce.sh` is the **entry point**; with `VARIANT=compositeB` (the default) it runs `src/box/compositeB.sh`. The team package is in `src/ber`, the model chain (XGBoost stages, cross-encoders, self-training labels, decision, rules, the France block) in `src/model_v1`, and the Qwen2.5-7B training, the 7B re-check and the per-country composition in `src/box`. The XGBoost stages need **24 or more CPU cores and 32 GB of RAM**, the cross-encoders ran on **one 80 GB H100**, and Qwen2.5-7B needs **three 80 GB GPUs** for about two hours. We used Python 3.12 to 3.13, torch 2.11, transformers 5.17, peft 0.21 and xgboost 3.2.0.

**Seeds are fixed**, and every artifact records the command and git commit that made it. GPU training is not bit-identical across machines (an earlier model rebuilt on other hardware moved from 0.991246 to 0.991261 on the holdout), so a rerun should land **within about 0.0001**. The `output/` folder holds the **exact bytes we submitted**.

### B. Additional Results

**Table B1.** Ablations on the local validation set (labelled US/India holdout), each tested with a paired bootstrap.

| change | effect on macro F0.5 |
|---|---|
| expected-F0.5 set selection instead of a tuned threshold | +0.000048 (0.000007 to 0.000091) |
| Qwen2.5-7B counted twice in the cross-encoder mix | India +0.000066 (P 0.998), US +0.000026 |
| 7B re-check, dropping logit < −6 | +0.000037, positive in both halves |
| tighter candidate cut (best S1 only / p1 ≥ 0.05) | −0.000106 / −0.000041 |

On a labelled 34% sample of the local holdout, **8.3%** of the confident predictions the 7B scored below −6 were real matches, against **92.6%** between −6 and −2 and **over 99.9%** above that. The 7B rejects **0.10% of French predictions**, but only **0.004% to 0.007%** of US and India ones. The French rate is the same in each third of the French S1, including the third the model never saw labels for, so the re-check is **not repeating its training labels**.

Two **leaderboard controls** support these choices. Composite B with the round-3 French model, but without the French decision layers, scored **0.990833**, which is 0.000046 lower. Pushing the French 7B drops below −6 scored **0.990875**, a tie, so the −6 cut-off was already in the right place.

We also **measured and dropped** several ideas: **recall rules** (17% to 71% precise); **a learned blend** of all six cross-encoder scores as the decision score (band AUC 0.9575, but 0.001 lower F0.5); **mining extra drops** with a decision tree (+0.000033 on one half of the holdout, −0.000015 on the other); **breaking ties** between empty-address records by copy count (−0.00057); **renormalising French probabilities** per record (−0.000007 to −0.000137); and **other encoders** (Qwen3-4B scored below the 7B, and mDeBERTa-v3 and gte-multilingual could not be trained or run reliably).
