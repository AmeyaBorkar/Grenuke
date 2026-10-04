# F16. Learning with limited labels: transfer, zero-shot, active learning, weak supervision and synthetic data

**Summary.**
- Labels are the scarce resource. US and India had about 7.6M labelled true pairs; France had none. This page covers the tools for few or no labels: transfer learning, multilingual models, zero- and few-shot LLMs, active learning, weak supervision, augmentation and synthetic data, and pseudo-labels.
- Our evidence is clear on one point. A Qwen2.5-7B scored a band AUC of 0.537 zero-shot, 0.720 after a quick LoRA and 0.944 properly trained [R]. Pretraining gives a start; labels teach the task. For France we used multilingual encoders, our rules as weak labels, pseudo-labels and a synthetic-data detector. We did no active learning.
- In a thought experiment with 500 French labels we would not retrain. We would spend them on calibration, on the 7B cut-off and on a stratified estimate of France's precision.

About 2.5 hours with the exercises. Prepares you for [09 self-training and domain shift][adv09] and [10 LLM verification][adv10].

---

## 1. What you need first

- [F03][f03]: training, validation, overfitting. [F07][f07]: transformers, cross-encoders and LLMs. [F04][f04]: AUC and calibration. [F10][f10]: pseudo-labels and domain shift.
- Evidence levels: **M** measured, **E** estimated or derived, **R** reported (stated in a team document or by a teammate, not re-checked here), **U** uncertain; "toy" is invented for practice. "Local holdout" is the fixed 25% of labelled US/India S1 (549,699 S1, no France).

---

## 2. The concepts from zero

### 2.1 The label budget

**Intuition.** Labels cost people and time. Unlabelled text is cheap. Every method here is a way to get more learning from fewer labels, and each one trades a risk for a saving.

**Worked example.** In train we had 7,638,365 labelled true pairs across the US and India [M] ([01][adv01]). France had none, and hand-labelling test data was not allowed in the challenge ([09][adv09]). We did not hand-label French pairs for training; we read samples only for error analysis [R]. So France is the whole of this page: how to do well in a country with a model trained elsewhere.

**A map of the settings.**

| setting | what you have | example |
|---|---|---|
| supervised | many labels in the target | US and India |
| semi-supervised | some labels and much unlabelled data | France pseudo-labels, [F10][f10] |
| weakly supervised | noisy labels from rules or heuristics | the French rules |
| transfer | labels in a related task or domain | US/India to France |
| zero-shot, few-shot | none, or a handful of examples | the untrained 7B |
| active | a human labels on request | what we would do with a budget |

**How many labels do you need?** Plot the score against the number of training labels. This is a **learning curve**. It usually rises fast and then flattens. If it is flat, more labels will not help and you should change the model or the data. If it still climbs, labels are worth buying. We did not publish a learning curve (U), so we cannot say how many US/India labels the final models needed.

### 2.2 Transfer learning and LoRA

**Intuition.** **Transfer learning** starts from a model that already learned general patterns from a huge corpus (the **pretrained** model) and adapts it with a small labelled set (**fine-tuning**). The pretrained model already knows what words are, so the labels only teach the task.

**Definition.** Three ways to adapt:
- **Feature extraction**: freeze the model, train a small head on its outputs.
- **Full fine-tuning**: update all weights. Used for e5 and bge.
- **LoRA** (low-rank adaptation): freeze the weights W and learn a small correction, W' = W + (alpha / r) × B × A, where A is r × k and B is d × r with a small rank r. Only A and B are trained.

The number of trained values per matrix falls from d × k to r × (d + k). For a toy matrix with d = k = 1,000 and r = 16 that is 32,000 instead of 1,000,000, 3.2%. We trained the Qwen2.5-7B with r = 16 and alpha = 32, on three H100s in about 2 hours [R].

**Worked example (our models).** All were fine-tuned as cross-encoders: a model that reads both records together as "name ; address", cut to 96 tokens, and outputs a score [R] ([methodology doc][doc]).

| model | size | licence | adaptation |
|---|---|---|---|
| multilingual-e5-small / large | 118M / 560M | MIT | full fine-tune |
| bge-reranker-v2-m3 | 568M | Apache-2.0 | full fine-tune |
| Qwen2.5-1.5B | 1.5B | Apache-2.0 | LoRA |
| Qwen2.5-7B | 7.6B | Apache-2.0 | LoRA |

The rule was MIT or Apache-2.0 and at most 8B parameters. Qwen2.5-3B was excluded by its licence ([10][adv10]), and so was jina-reranker-v2, which is non-commercial [R].

### 2.3 Cross-lingual transfer and multilingual models

**Intuition.** A **multilingual** model is pretrained on text in about a hundred languages with one shared subword vocabulary and one set of weights, as XLM-R is (Conneau et al., 2020). The e5 and bge models we used come from this tradition (U: not re-checked against the model cards). Words and pieces from different languages land in the same space, so what it learns about a task in one language often carries to another. That is **zero-shot cross-lingual transfer**.

**Why e5 and bge suit our three countries** (the design reasoning; we never ran an English-only comparison, U):
- The records mix English, Indic names (some of them transliterated) and French, with accents (é, è, ç) and abbreviations ("Rue" becomes "R."). A shared multilingual vocabulary splits these into pieces the model has seen.
- We train on US and India labels and must score France. A model with a shared space has a chance of treating a French decoy like an English one.
- Both families are open: MIT and Apache-2.0.

**Worked example (an illustration, not a measurement).** The pair ("rue gutenberg", "r. gutenberg"). A multilingual tokenizer has seen "rue" and "r." in French text, so it can learn that they play the same role. A tokenizer built mostly on English may split "gutenberg" into odd fragments and have no sense of "rue".

**What the evidence says.** Cross-encoders helped France more than the holdout shows [R]. They disagreed with each other about four times as often in France, so we averaged their z-scored logits into one feature [R]. The 7B scored the French decoys like the US/India decoys and rejected them [R] ([methodology doc][doc]). That is consistent with transfer, but the 7B had also seen French pseudo-labels, so it is not a clean test.

**Two options we did not use.** **Domain-adaptive pretraining** continues the pretraining on unlabelled text from the target domain, here French records, before fine-tuning. It needs GPU time and we had other uses for it. **Distillation** trains a small model on a big model's scores, which is how a 7B reader could scale to every pair ([10][adv10]).

### 2.4 Zero-shot and few-shot LLMs

**Intuition.** A large language model can follow an instruction without any training on your task (**zero-shot**), or with a few worked examples in the prompt (**few-shot**, or in-context learning).

**Definition.** AUC is the chance that a random true pair scores above a random false pair. 0.5 is a coin flip; 1.0 is perfect. Toy: positives scored 0.9, 0.8, 0.6, 0.4 and negatives 0.7, 0.5, 0.3, 0.2. Of the 16 (positive, negative) pairs, 13 are ranked correctly, so AUC = 13 / 16 = 0.81.

**Worked example.** The same Qwen2.5-7B, on our labelled pairs [R] (the evaluation sample is not recorded in the sources for this page, U):

| state | AUC | reading |
|---|---|---|
| zero-shot, prompt only | 0.537 | barely above a coin flip |
| a quick LoRA | 0.720 | it has learned part of the task |
| trained properly on our labels | 0.944 | tied for the best reader we had in the band |

Why zero-shot failed (an interpretation, E): the decoys are built to look alike, and "same business" here follows the generator's convention: a nudged house number or a swapped business word makes a different business. A general model has no way to know that without examples.

**Cost.** Reading a pair costs tokens. We measured about 600 pairs per second for the 7B on an H100 [R]. At that rate the 1.49M band pairs take about 41 minutes and all 58.4M retrieved pairs about 27 GPU-hours. Few-shot makes it worse: a prompt with 8 examples of 96 tokens plus the pair is about 864 tokens against 96, roughly 9 times the compute unless a cached prefix is shared [E, arithmetic]. Prompted LLMs also change their answers with wording and example order ([10][adv10]). So we fine-tuned a classification head and used the 7B only where a second reading pays.

### 2.5 Active learning

**Intuition.** If you can only afford a few labels, choose the ones that teach most. **Active learning** loops: train, score the unlabelled pool, pick the most useful items, have a human label them, retrain.

**Definition.** Common picking rules:
- **Uncertainty**: the least confident, the smallest margin between classes, or the highest entropy.
- **Disagreement** (query by committee): items on which several models disagree most.
- **Diversity**: avoid labelling near-copies of each other.

One caution. Labels picked this way are not a random sample, so you cannot average them to estimate accuracy. To estimate a rate you need a random or stratified sample with known sampling shares, and you weight each label by the inverse of its selection probability. For ER see Sarawagi and Bhamidipaty (2002).

**What we did.** Nothing: US and India had 7.6M labels, and hand-labelling French test data was not allowed. The records list hand reviews of 22 S1, 40 changes and a 24-pair sample; these were for error analysis, not training [R].

**Thought experiment: 500 French labels.** This is a design for the study guide, not something we did. The largest unknown in France is calibration: the probabilities summed to 3.55 copies per S1 against about 3.46 ([F10][f10]). So we would spend the labels on measurement.

| labels | which pairs | question it answers | precision of the answer |
|---|---|---|---|
| 150 | kept pairs, 50 each in pc bands 0.5 to 0.75, 0.75 to 0.9 and 0.9 to 0.99 | how far off is French calibration? fit a 2-parameter correction on the logit | about ±14, ±11 and ±6 points per band alone (at assumed rates 0.6, 0.8, 0.95); the pooled fit is tighter |
| 100 | random sample of the 859 French pairs the 7B flagged (below −6) | what share of French rejects is real? | ±4.3 points if the share is 5% |
| 50 | the −6 to −4 band (209 French predictions) | where does the cut-off belong? | ±10 points if 86% are real |
| 100 | pairs where the feature models and the 7B disagree most | what should the next model learn? | not a rate: biased by design |
| 100 | empty-address pairs the model scores low | would a recall rule clear the 75% bar? | ±10 points |

The half-widths are 1.96 × sqrt(p (1 − p) / n) for the assumed p [E]. The labels would not retrain stage 2. They would recalibrate, set the cut-off and give a stratified estimate of French precision. Recall is harder: it needs labels on pairs we did not predict, where true matches are rare.

### 2.6 Weak supervision

**Intuition.** Instead of labelling pairs by hand, write rules that label them roughly. Each rule is a **labelling function**: it votes match, non-match or abstain. The rules are noisy, but many noisy labels with known accuracy can train a model (Ratner et al., data programming and Snorkel).

**Definition.** For each labelling function, track its **coverage** (how often it votes), its **accuracy** (how often it is right when it votes) and its **conflicts** with the others. If accuracies are unknown, a label model can estimate them from agreement patterns (Dawid and Skene, 1979). We did not need that, because we could measure each rule's accuracy in the two labelled countries.

**Worked example (our French rules).** Each rule defines a population of pairs and a vote. Truth rates are measured on US and India labels [M] ([decision][d-rules2]).

| population | vote | true in US / India | used in France? |
|---|---|---|---|
| B: look-alike swap at the S1's address | not a match | 3.1% / 0.6% | yes, drop |
| A: a word dropped and a list word appended | match | 99.7% / 98.3% | yes, add |
| APP: a list word appended, nothing dropped | match | 98.9% / 99.6% | yes, add |
| ACR: acronym at the same address | match | 99.9% / 99.8% | yes, add |
| NUM: house number lower by 1 or 2 | match | 97.6% / 78.2% | no |
| CODE: short-code typo | match | 42.6% / 44.0% | no |

The record rejects NUM because the model's rejections are right in India, France's rate is unknown, and adding pays only above about 75% precision ([F11][f11]). CODE is a coin flip. The kept populations have extreme truth rates in both labelled countries, which is why they could be trusted in a third (an interpretation, E). The kept rules also had to satisfy three conditions: the pair is a candidate, the S1 is the record's best-scoring S1, and the record is not predicted elsewhere.

**Combining votes (toy).** Two independent rules say "match" with accuracies 0.99 and 0.90. The likelihood ratios are 99 and 9, so the odds multiply: 891 to 1, probability 0.9989. If the two rules look at the same evidence, they are not independent and the answer is 0.99. A related design choice (an interpretation, E): in self-training the rules override the teacher instead of being added to its vote.

**Pitfall.** Easy rule-labelled positives alone lowered F0.5 by 0.0034 on the India stand-in, because certain copies taught the model to accept too much [M] ([09][adv09]).

### 2.7 Augmentation and synthetic data

**Intuition.** **Augmentation** makes new training examples by changing real ones in ways that keep the label. **Synthetic data** generates examples from a model of how the data is made.

**Definition for ER.** Take a clean record and apply the edits seen in real copies to make a positive: change case or accents, drop or rewrite the legal form, reorder or append words, shorten "Rue" to "R.", introduce a typo, empty the address. Make a hard negative with a look-alike edit: nudge the house number or swap a business word. The risk is the **sim-to-real gap**: if the edits do not match the real mix, the model learns the simulator.

**Worked example (what we did).** We learned the generator's operations from US and India labels. The finding: the same look-alike machinery is used everywhere, and descriptor swaps are decoys. Sachi built the synthetic French set and Ameya extended it. The result [R] ([09][adv09]):
- Synthetic cross-encoders raised our estimators by reverting moves that the leaderboard had confirmed, so we judged them unreliable for France and did not upload them.
- One bge cross-encoder, trained on US/India labels and synthetic French with no self-training labels, proved useful as a detector. It flagged 708 of the 859 French 7B rejects (82%).

Two rules from the experience: the synthetic edit mix must match the real one, and the generator should be checked on a labelled country first (build "synthetic US", train on it, and score real US). That check is a suggestion, not something we ran (U).

**Label noise and clean validation.** Pseudo-labels, rule labels and synthetic labels are all noisy. Whatever the source of the training labels, keep a clean validation set. In our self-training, early stopping and calibration used labelled US/India rows only [R] ([09][adv09]). A student that is validated against its own pseudo-labels can only measure agreement with its teacher.

### 2.8 Pseudo-labels, and when each tool fits

Pseudo-labels, where the model labels its own confident cases, are in [F10][f10]. The table is a quick guide.

| situation | tool | what we did | main risk |
|---|---|---|---|
| labels in related domains, none in the target | transfer, then pseudo-labels | multilingual encoders; French self-training | confirmation bias |
| a small labelled set and a strong pretrained model | fine-tuning, LoRA | cross-encoders | overfitting the small set |
| no labels and a capable LLM, little data | zero- or few-shot | tested, AUC 0.537 | prompt sensitivity, cost |
| labels cost money and you choose which | active learning | not done | biased sample |
| expert rules exist | weak supervision | French rules | rule accuracy that does not transfer |
| the noise process is known | augmentation, synthetic data | tried; one detector helped | sim-to-real gap |

---

## 3. How it shows up in our project

| when | what | where |
|---|---|---|
| 25 to 26 Sep | proxy word odds, a label-free stand-in for labels | [F10][f10] |
| 26 Sep | e5-small cross-encoder; then e5-large, bge | [methodology doc][doc] |
| 26 to 27 Sep | Qwen2.5-1.5B LoRA (Sachi), Qwen2.5-7B LoRA (Bakshi) | [10][adv10] |
| 26 to 27 Sep | French rules, guarded self-training | [09][adv09] |
| 27 Sep | Sachi's synthetic French; the bge detector | [09][adv09] |

---

## 4. How to read the numbers

- **0.537, 0.720, 0.944** are AUCs for one model at three stages [R]. They say how well it ranks pairs, not what the F0.5 would be.
- **600 pairs per second** is one measurement on an H100 [R]. Throughput changes with batch size and sequence length.
- **82%** (708 of 859) is agreement between two readers. It is not accuracy.
- **A rule's truth rate** is measured in US and India. For France it is an assumption [E].
- **±4.3 points** in the label plan is the sampling error of a rate at an assumed 5%. If the true rate is different, so is the error.

---

## 5. Common misconceptions

1. **"The LLM already knows the task."** It knows language. It does not know the generator's convention for a different business. Zero-shot scored 0.537.
2. **"Multilingual means language-neutral."** It means shared space, with uneven quality across languages and scripts, and it was not ablated here.
3. **"Synthetic data is free labels."** It is labels about your model of the world. Ours moved estimators in the wrong direction.
4. **"Active learning always beats random sampling."** It beats it for training, and loses for estimation unless you weight.
5. **"Weak labels are noisy, so they hurt."** Well-measured rules with extreme truth rates help. Easy positives alone hurt (−0.0034).
6. **"LoRA is a cheap version of fine-tuning."** It trains far fewer values. It is a different trade-off, not a lesser one.
7. **"More pseudo-labels help."** They help to a point; see [F10][f10].

---

## 6. Check yourself

**1.** An AUC of 0.537 means what?

<details><summary>Answer</summary>

A random true pair outranks a random false pair 53.7% of the time, barely above the 50% of a coin flip. At 0.944 it is 94.4%.

</details>

**2.** Compute the AUC for positives 0.9, 0.8, 0.6, 0.4 and negatives 0.7, 0.5, 0.3, 0.2.

<details><summary>Answer</summary>

0.9 beats all 4 negatives, 0.8 all 4, 0.6 beats 0.5, 0.3, 0.2 (3), 0.4 beats 0.3, 0.2 (2): 13 of 16 pairs, AUC = 0.8125.

</details>

**3.** A matrix has d = k = 4,096. How many values does LoRA with r = 16 train, and what share of the full matrix?

<details><summary>Answer</summary>

16 × (4,096 + 4,096) = 131,072 values, against 16,777,216: 0.78%. (4,096 is a toy size, not the 7B's actual one.)

</details>

**4.** How long would 1.49M pairs take at 600 pairs per second, and 58.4M?

<details><summary>Answer</summary>

1.49M / 600 = 2,483 s, about 41 minutes. 58.4M / 600 = 97,333 s, about 27 hours.

</details>

**5.** Eight few-shot examples of 96 tokens are added to a 96-token pair. What happens to the compute?

<details><summary>Answer</summary>

The prompt grows from 96 to 96 × 9 = 864 tokens, about 9 times the compute, unless a shared prefix is cached. So 27 hours becomes about 243 hours.

</details>

**6.** You label 100 random French pairs flagged by the 7B and 5 are real. Give the estimate and a rough 95% interval.

<details><summary>Answer</summary>

5%. The standard error is sqrt(0.05 × 0.95 / 100) = 0.0218, so ±4.3 points: about 0.7% to 9.3%. For a rate this low a Wilson interval is better, but the point is that 100 labels pin it to within a few points.

</details>

**7.** Why can't you estimate France's precision by averaging labels chosen where the models disagree most?

<details><summary>Answer</summary>

Those items are the hardest ones, so their error rate is far above the average. The sample is biased by design. To estimate a rate you need a random or stratified sample, weighted by the inverse selection probability.

</details>

**8.** Two independent rules both say "match", with accuracy 0.95 and 0.80. Combine them from prior odds 1 to 1.

<details><summary>Answer</summary>

Likelihood ratios 19 and 4. Odds 76 to 1, probability 0.987. If the two rules shared the same evidence, the answer would be the stronger rule alone, 0.95.

</details>

**9.** From the table of French rules, which would you keep for a new country, and which not? Why?

<details><summary>Answer</summary>

Keep B, A, APP, ACR: truth rates extreme (below 3.1% or above 98.3%) and stable across the US and India. Reject NUM (97.6% against 78.2%: unstable, and the model's rejections were right in India) and CODE (about 43%: a coin flip). Adding a pair pays only above about 75% precision.

</details>

**10.** Design a check that tells you whether a synthetic French generator is faithful.

<details><summary>Answer</summary>

Apply the generator to a labelled country (US or India) to make synthetic pairs, train on them, and score the real labelled pairs of that country. If the synthetic-trained model is close to the real-trained one, the generator copies the real edit mix. Compare the edit frequencies too. Do it on India as a stand-in for France first.

</details>

---

## 7. Going deeper

- [09 self-training and domain shift][adv09]: the failures and the stand-in country. [10 LLM verification][adv10]: the 7B as a second reader. [01 entity resolution][adv01] section 2.5 for active learning and ER.
- Pan and Yang (2010), "A survey on transfer learning", IEEE Transactions on Knowledge and Data Engineering. Hu et al. (2022), "LoRA: Low-rank adaptation of large language models", ICLR.
- Conneau et al. (2020), "Unsupervised cross-lingual representation learning at scale", ACL. Wang et al. (2024), "Multilingual E5 text embeddings: a technical report".
- Brown et al. (2020), "Language models are few-shot learners", NeurIPS.
- Settles (2009), "Active learning literature survey", University of Wisconsin-Madison Computer Sciences Technical Report 1648. Sarawagi and Bhamidipaty (2002), "Interactive deduplication using active learning", KDD.
- Ratner et al. (2016), "Data programming: creating large training sets, quickly", NeurIPS; Ratner et al. (2017), "Snorkel: rapid training data creation with weak supervision", PVLDB. Dawid and Skene (1979), "Maximum likelihood estimation of observer error-rates using the EM algorithm", Applied Statistics.
- Wu et al. (2020), "ZeroER: entity resolution using zero labeled examples", SIGMOD.

## 8. Where next

- [F10 Semi-supervised learning and domain shift][f10]: pseudo-labels and the France story.
- [F07 Neural networks, transformers and LLMs][f07]: the models behind this page.
- [F12 Interpreting our results][f12]: where these tools sit in the numbers.
- The track map: [foundations README](README.md).

[doc]: ../../../experiments/ameya/final-zip/doc/Documentation_template.md
[adv01]: ../01-entity-resolution.md
[adv09]: ../09-self-training-and-domain-shift.md
[adv10]: ../10-llm-verification-and-compute.md
[f03]: F03-machine-learning-fundamentals.md
[f04]: F04-classification-metrics.md
[f07]: F07-neural-networks-transformers-llms.md
[f10]: F10-semi-supervised-and-domain-shift.md
[f11]: F11-decision-theory-and-optimisation.md
[f12]: F12-interpreting-our-results.md
[d-rules2]: ../../../docs/decisions/2026-09-26_0626_france-rules-v2.md
