# Transformers and cross-encoders

**Summary.** A cross-encoder reads both records together and scores the pair, which is more accurate than comparing two separately computed embeddings but costs one full transformer pass per pair.
We fine-tuned five model families (multilingual-e5, bge-reranker-v2-m3, Qwen2.5-1.5B and Qwen2.5-7B with LoRA) only on the 1.49M test pairs stage 1 was unsure about (0.02 ≤ p1 ≤ 0.99), out of fold, and gave stage 2 the mean of their z-scored logits.
The mean, rather than separate logits, was a deliberate choice for France, where the models disagreed four times as often.

Related pages: [string similarity](03-string-similarity.md) (what the hand features already capture), [gradient boosting](06-gradient-boosting-and-stacking.md), [self-training](09-self-training-and-domain-shift.md), [LLM verification and compute](10-llm-verification-and-compute.md), [glossary](glossary.md).

---

## 1. Intuition

- A **bi-encoder** turns each record into a vector on its own; two records match if their vectors are close. It is fast (one pass per record, then a nearest-neighbour search), but each record is encoded without seeing the other.
- A **cross-encoder** reads "S1 text, separator, record text" as one sequence. Every token of one record can attend to every token of the other, so the model sees directly that "R." lines up with "Rue", that "Cie" stands for "Compagnie", or that "école" replaced "club".
- A **decoder LLM** used as a classifier does the same with a much larger model: it reads the pair and a small head turns its last hidden state into one logit.
- Cross-encoders are expensive, so we used them only where stage 1 hesitated.

## 2. Formal definition

### 2.1 The transformer in one page

Text becomes tokens; each token becomes a vector (plus position information). A layer then applies:
- **multi-head self-attention**: $\mathrm{Attention}(Q,K,V) = \mathrm{softmax}\!\big(QK^\top/\sqrt{d_k}\big)\,V$, with $Q = XW_Q$, $K = XW_K$, $V = XW_V$. Each token takes a weighted mix of the others, the weights coming from query–key similarity;
- a position-wise **MLP**;
- residual connections and layer normalisation around both.

For a sequence of L tokens and width d, attention costs about $L^2 d$ per layer and the MLP about $L d^2$. At our L ≤ 96, the MLP dominates, so cost grows roughly with the parameter count times the tokens.

**Encoders** (BERT, XLM-R, e5, bge) let every token see every other token. **Decoders** (Qwen) use a causal mask: a token only sees those before it.

### 2.2 Bi-encoder against cross-encoder

| | bi-encoder | cross-encoder |
|---|---|---|
| score | $\cos\big(E(a), E(b)\big)$ | $w^\top h(a \oplus b) + c$ |
| passes | one per record, reusable | one per pair |
| token alignment between a and b | none (only through the vectors) | full attention across the pair |
| our test split | about 11.7M records [E] | 58.4M retrieved pairs, or 1.49M band pairs |

A bi-encoder suits retrieval (blocking); a cross-encoder suits re-ranking a short list.

### 2.3 The models and their pre-training

- **multilingual-e5** (small 118M, base 278M, large 560M; MIT) was pre-trained contrastively on text pairs. The InfoNCE loss for a query q, its positive $d^+$ and negatives N is
  $$\mathcal{L} = -\log \frac{\exp\big(s(q,d^+)/\tau\big)}{\sum_{d \in \{d^+\}\cup N} \exp\big(s(q,d)/\tau\big)} .$$
  We used e5 only as a starting point: a fresh one-logit head on the joint encoding of the pair, fully fine-tuned on our pairs.
- **bge-reranker-v2-m3** (568M, Apache-2.0) is already a multilingual cross-encoder reranker, built on an XLM-RoBERTa backbone; fully fine-tuned the same way.
- **Qwen2.5-1.5B and Qwen2.5-7B** (Apache-2.0; 1.5B and 7.6B parameters) are decoder LLMs, fine-tuned with LoRA as sequence classifiers ([`sachi/ce_llm.py`](../../experiments/sachi/ce_llm.py), Sachi; [`ce_llm_st.py`](../../experiments/ameya/model-v1/ce_llm_st.py); [`llm_group.py`](../../experiments/bakshi/box/llm_group.py), Bakshi). With a causal mask only the last token has seen the whole input, so the classification head reads the hidden state of the last real token. The pad token is the end-of-sequence token, and " || " separates the two records because Qwen's tokenizer joins a text pair with no separator.

### 2.4 LoRA

Freeze a weight matrix $W_0 \in \mathbb{R}^{d\times k}$ and learn a low-rank update:

$$h = W_0 x + \frac{\alpha}{r}\, B A x, \qquad B \in \mathbb{R}^{d\times r},\ A \in \mathbb{R}^{r\times k},\ r \ll \min(d,k).$$

A starts random and B at zero, so training starts exactly from the pre-trained model. A matrix costs $r(d+k)$ trainable numbers instead of $dk$. The scale α/r sets how strongly the update counts; keeping α = 2r means a change of rank barely changes the effective step.

Ours: r = 16, α = 32, dropout 0.05, on all attention and MLP projections (q, k, v, o, gate, up, down), with the classification head trained too and the trainable weights kept in fp32 over a bf16 base.

**Why it fits a 7B model on one 80 GB card.** Full fine-tuning with AdamW needs about 16 bytes per parameter (fp32 weights, gradients and two Adam moments): 7.6B × 16 ≈ 122 GB. With LoRA the base sits in bf16 (about 15 GB) with no gradients or optimiser state, and only about 40.4M weights train [E]. That count follows from Qwen2.5-7B's shapes (28 layers; r = 16 on seven projections) and matches the 161.5 MB adapter files in fp32 [M] (Bakshi's [methodology](../../experiments/bakshi/final-package/METHODOLOGY_bakshi.md) §8): 0.53% of the model.

### 2.5 Input and training

- **Text:** "name ; address" for each side, each cut to 300 characters, S1 first, cut jointly to **96 tokens** (the longer side is trimmed first). The median pair is 37 tokens with Qwen's tokenizer [M], so the cut rarely binds.
- **Training:** binary cross-entropy on one logit, AdamW, warm-up then linear decay, bf16, gradient clipping at 1.0, batches of similar length to cut padding. Learning rates: 5e-5 (e5-small), 2e-5 (e5-large, bge), 1e-4 (Qwen LoRA). One epoch, except two for e5l2 and e5ls.
- **A guard:** with torch 2.11, a rare step with a non-finite gradient turned every weight into NaN, so such steps are skipped ([`ce.py`](../../experiments/ameya/model-v1/ce.py)). The 7B run skipped none.

### 2.6 Out-of-fold training

The cross-encoder logit becomes a stage-2 feature, so it must be out of fold like p1 ([page 06](06-gradient-boosting-and-stacking.md)): three models per family, model g trained on the band pairs of the other two S1 groups and scoring its own group; the holdout and the test get the mean of the three. French pseudo-labelled pairs were cross-fitted the same way, by `fold_of(s1) % 3`: model g learns from two thirds of the French S1 and alone scores the third it never saw ([page 09](09-self-training-and-domain-shift.md)).

### 2.7 Combining several cross-encoders

Each model's logit is standardised with the mean and standard deviation of its train-band logits, $z_m = (\ell_m - \mu_m)/\sigma_m$, and stage 2 receives the mean $\bar z = \frac1M\sum_m z_m$ ([`zmean_ce.py`](../../experiments/ameya/model-v1/zmean_ce.py)). Without z-scoring, the model whose logits spread widest would dominate the average. A model counted twice simply gets two votes: our final US/India mix is e5l, qst, e5ls, bge, q7st, q7st.

**Why diversity helps.** For an averaged regressor $\bar f = \sum_m w_m f_m$ under squared error (Krogh and Vedelsby 1995),

$$(\bar f - y)^2 = \sum_m w_m (f_m - y)^2 - \sum_m w_m (f_m - \bar f)^2 :$$

the ensemble's error is the members' average error minus their average disagreement. Members that err differently help even when individually weaker. There is no exact identity for AUC, but the effect is the same.

### 2.8 AUC as the band metric

$\mathrm{AUC} = P\big(s(x^+) > s(x^-)\big)$ for a random true and a random false pair; it equals the Mann–Whitney U statistic divided by $n^+ n^-$. A band AUC of 0.944 means a random true band pair outscores a random false band pair 94.4% of the time. We judged cross-encoders by AUC on the labelled holdout band because:
- the band is where they act, and stage 2 uses them as a ranking signal;
- AUC ignores each model's logit scale, so models compare fairly;
- it needs no threshold.

## 3. Variants

| variant | idea | note |
|---|---|---|
| Bi-encoder (Sentence-BERT) | embeddings + nearest neighbours | retrieval; a candidate view at scale ([page 11](11-scaling-to-billions.md)) |
| Late interaction (ColBERT) | per-token vectors, cheap matching | between the two in cost and accuracy |
| Poly-encoder | a few global vectors attend to the candidate | the same trade-off |
| Cross-encoder (monoBERT) | joint encoding of the pair | ours |
| LLM classifier or reranker | a decoder LLM with a head, or prompted | ours, as a fine-tuned classifier |
| Adapters, prefix tuning, QLoRA | other parameter-efficient methods | QLoRA adds a 4-bit base |
| Distillation | train a small model on a large one's scores | the production path ([page 11](11-scaling-to-billions.md)) |
| Entity-matching models (DeepMatcher, Ditto) | pre-trained language models on serialised records | the line of work our cross-encoders belong to |

## 4. Where we used it

**The band.** Pairs with 0.02 ≤ p1 ≤ 0.99: 1,568,554 train and **1,490,930 test** pairs [M], 2.6% of the 58.4M retrieved test pairs ([`ce.py`](../../experiments/ameya/model-v1/ce.py) `band_pairs`). Outside it the logit is missing, and stage 2 learns what that means from the same rule on train.

| model | size, licence | training | holdout band AUC (OOF) | role |
|---|---|---|---|---|
| stage-1 p1, same pairs | | | 0.9297 | the reference |
| multilingual-e5-small | 118M, MIT | full | 0.9240 (0.9191) | its own stage-2 feature, from v3ce on |
| multilingual-e5-base | 278M, MIT | full | 0.9287 (0.9244) | the round-1 French teacher only |
| multilingual-e5-large, 1 / 2 epochs (e5l / e5l2) | 560M, MIT | full | 0.9391 / 0.9441 | e5l in every mix |
| e5-large, French self-trained (e5ls) | 560M, MIT | full | 0.9439 (0.9403) | v7s on |
| bge-reranker-v2-m3 (bge) | 568M, Apache-2.0 | full | 0.9417 (0.9382) | v7mst on |
| Qwen2.5-1.5B, French self-trained (qst) | 1.5B, Apache-2.0 | LoRA | 0.9381 (0.9332) | v7sq on |
| Qwen2.5-7B, French self-trained (q7st) | 7.6B, Apache-2.0 | LoRA | **0.9436** (0.9396) | ×2 in g1w; the re-check |

Sources: [RESEARCH_v6 §5.1, §6.5](../../experiments/ameya/model-v1/RESEARCH_v6.md), Bakshi's methodology §3 [M]. Qwen3-4B (0.9411) was trained but finished too late to use.

**Cost** [R]: e5-small 35 minutes on the laptop GPU; e5-large 61 minutes for three OOF models on a shared H100; the 7B about 2 hours on three H100s (one OOF group each), including scoring about 2.0M pairs per group at about 600 pairs per second.

**What each step bought:**

| step | evidence |
|---|---|
| first cross-encoder, e5-small (v3 → v3ce) | local holdout +0.00140 [+0.00131, +0.00148]; singleton F0.5 0.9913 → 0.9974; France predictions per S1 3.539 → 3.470 [M] |
| e5-base and e5-large as features (v6all → v7ce3) | local holdout +0.000311 [+0.000258, +0.000362] [M] |
| the two e5-large runs as a z-mean (v7n) | public LB 0.988609 → 0.989721, France implied 0.973 → 0.978 [M]/[E] |
| the 7B counted twice in the mix (g1w against g0) | local holdout +0.000062; India +66.1e-6, P 0.998; US +26.2e-6, P 0.906 [M] |

**Separate logits or one mean?** On the US/India test band the cross-encoders nearly agree; on France they part ways (label-free, [RESEARCH_v6 §6.6](../../experiments/ameya/model-v1/RESEARCH_v6.md)):

| test band | correlation e5l2–bge | correlation e5l2–e5l | sign disagreement e5l2 vs bge |
|---|---|---|---|
| US | 0.978 | 0.985 | 3.1% |
| India | 0.984 | 0.985 | 2.7% |
| **France** | **0.906** | **0.951** | **12.0%** |

A stage 2 given each logit separately learns its splits where the models agree, because that is all the labelled data contains. In France it then meets pairs where, say, e5 is confident and bge strongly disagrees, a region it never saw, and it extrapolates. The mean behaves predictably there: disagreeing votes cancel toward the middle, and stage 2 falls back on its other features.
- On the labelled holdout the two designs tie: v7c (five separate logits) +0.000071 and v7m (one mean) +0.000050 over v7ce3, a 0.00002 gap; after stage 3, v7c 0.991252 against v7n's mean 0.991211 [M].
- On France's rule populations (truth known from US/India), the mean separated better: AUC 0.8776 against 0.8741 [E].
- Ties go to the simpler design, so we took the mean (decision record [model-v7n](../../docs/decisions/2026-09-26_2135_model-v7n.md)).

**Diversity, measured on France** (raw logits on 53,290 French rule-population pairs; RESEARCH_v6 §6.11, §6.13):
- **bge is the weakest single model on France (0.774) yet lifts the mean most:** e5l + e5l2 scores 0.806, adding bge 0.826. It is a different family, so its French errors differ from e5's.
- **A second epoch specialises:** e5-large rose on the holdout band (0.9391 → 0.9441) but fell on France (0.803 → 0.792).
- **A weak member hurts:** adding e5-base to the three-model mean lowered it to 0.813.

**Scale alone did not buy accuracy.** The 7B ties the self-trained e5-large on the band (0.9436 against 0.9439). It earned its place by being a different family in the mix and an independent reader of confident pairs ([page 10](10-llm-verification-and-compute.md)).

## 5. Why it fits this problem

- The noise is lexical and multilingual: accents, transliterated Indic names, abbreviations ("Cie", "R."), reordered words, typos, brand names. Hand features see token overlap; a cross-encoder reads meaning and alignment.
- Multilingual pre-training covers French, a language absent from our labels.
- Only 2.6% of pairs need it, so the cost is affordable; the rest are settled by cheap trees.
- As a stage-2 feature, a cross-encoder only has to add information, not to decide alone.

## 6. Pitfalls

1. **Cost explodes outside the band.** The 7B on all 58.4M test pairs would take about 27 GPU-hours, before any training.
2. **In-sample logits leak into stage 2.** Hence three OOF models per family.
3. **AUC is not decision quality.** e5-small (0.9240) ranked worse than p1 (0.9297) yet added +0.00140 F0.5 as a feature, because its errors differ. In the other direction, a cross-fitted blend of six logits and pc reached band AUC 0.9575 against pc's 0.9276, yet lost 0.001 F0.5 when used as the decision score (Bakshi, FINAL_PUSH_RESULTS §9).
4. **Correlated checkpoints add little.** The two e5-large runs correlate at 0.986 on the holdout band.
5. **Training on the labelled countries specialises the model** away from the unseen one (the second e5-large epoch).
6. **Numerics and tooling.** mDeBERTa-v3 had 999 non-finite steps in its first 1,000 under bf16, and a gte reranker crashed in its remote code; both were dropped. Logits are not bit-identical across GPUs, so reruns land within about ±0.0001.
7. **Licences are model by model.** Qwen2.5-0.5B, 1.5B and 7B are Apache-2.0, Qwen2.5-3B is not; jina-reranker-v2 is non-commercial. We checked each model card ([ANALYSIS_v3 §8](../../experiments/ameya/model-v1/ANALYSIS_v3.md)).
8. **Rented machines vanish.** A spot box went down at 21:40 on 26 Sep with the bge logits; the 7B run later resumed from checkpoints written every 600 seconds.

## 7. Jury questions with answers

**Q1. Why not match with embedding similarity?**
A bi-encoder encodes each record alone, so it cannot line up "R." with "Rue" or notice that one word was swapped at the same address. That fine alignment is what decides our uncertain pairs. Embeddings are the right tool for retrieval, and we would add them as a blocking view at scale.

**Q2. Why only the band 0.02 ≤ p1 ≤ 0.99?**
Below 0.02 the pairs are almost all false and leave the candidate file anyway; above 0.99 stage 1 is almost always right. The band holds 2.6% of pairs and most of the decisions that can change. For the confident side we later added the 7B re-check.

**Q3. Why a 7B model if it is no more accurate than e5-large?**
It is a different family. Counted twice in the mix, it gained +0.000062 on the local holdout (India +66.1e-6, P 0.998), and as an independent reader it found French decoys that every other model accepted.

**Q4. What is LoRA, and how did a 7B fit on your GPUs?**
LoRA freezes the model and learns a rank-16 update BA for each projection, about 40M weights instead of 7.6B. The frozen base takes about 15 GB in bf16, with no gradients or optimiser state, so one 80 GB H100 trains it; full fine-tuning would need about 120 GB.

**Q5. How did you stop the cross-encoders leaking labels into stage 2?**
Three models per family, each trained on two S1 groups and scoring the third, with the holdout and test getting the mean. French pseudo-labels were cross-fitted by S1 third, so no French pair was scored by a model that saw its own label.

**Q6. Why average z-scored logits rather than let XGBoost weigh them?**
On labelled data the models agree, so XGBoost learns weights only where they agree. In France they disagree four times as often (12% sign disagreement against 3%), and separate inputs make stage 2 extrapolate there. The mean tied on the holdout and separated French rule populations better (0.8776 against 0.8741), and ties go to the simpler design.

**Q7. What does a band AUC of 0.944 mean, and why AUC?**
A random true band pair outscores a random false one 94.4% of the time. AUC is threshold-free and scale-free, so models with different logit ranges compare fairly. We never used it alone: every model also had to raise holdout F0.5 through stage 2.

**Q8. How did you respect the licence and size rules?**
Every model is MIT or Apache-2.0 and at most 7.6B parameters: e5 (MIT), bge-reranker-v2-m3 and Qwen2.5-1.5B/7B (Apache-2.0). We checked each model card before training and left out Qwen2.5-3B and jina-reranker-v2 for their licences.

## 8. Self-test

1. How many trainable numbers does LoRA with r = 16 add to one 4096 × 4096 matrix, and what share is that?
<details><summary>Answer</summary>

r(d + k) = 16 × 8192 = 131,072, against 16,777,216: 0.78%.

</details>

2. Why is B initialised to zero, and what does α/r = 2 do?
<details><summary>Answer</summary>

With B = 0 the update BA is zero, so training starts from the pre-trained model exactly. α/r scales the update; holding α = 2r keeps the effective step similar if the rank changes.

</details>

3. Why does a decoder's classification head read the last token rather than the first?
<details><summary>Answer</summary>

Under a causal mask, a token sees only earlier tokens. Only the last real token has attended to the whole pair.

</details>

4. Model A's logits have standard deviation 4, model B's 1. What goes wrong if you average raw logits?
<details><summary>Answer</summary>

A dominates: a change of one standard deviation in A moves the mean four times as much as one in B. Z-scoring puts both on the same scale, so each counts as one vote.

</details>

5. Positives score 0.9 and 0.4; negatives score 0.5 and 0.1. What is the AUC?
<details><summary>Answer</summary>

Of the four positive–negative pairs, three are ordered correctly (0.9 > 0.5, 0.9 > 0.1, 0.4 > 0.1) and one is not (0.4 < 0.5): AUC = 0.75.

</details>

6. e5-small had a lower band AUC than p1, yet it improved F0.5. How?
<details><summary>Answer</summary>

Stage 2 already had p1. What matters is the information e5-small adds beyond it: it reads the text, so its errors differ from p1's, and the combination ranks better than either. AUC alone measures a model in isolation.

</details>

7. Why can't a 7.6B model be fully fine-tuned on one 80 GB GPU with AdamW?
<details><summary>Answer</summary>

About 16 bytes per parameter (fp32 weights, gradients and two Adam moments) gives about 122 GB before activations. LoRA trains about 40M weights, so the optimiser state is under 1 GB and the frozen bf16 base is about 15 GB.

</details>

## 9. Further reading

- Vaswani et al. (2017). Attention is all you need.
- Devlin, Chang, Lee and Toutanova (2019). BERT: pre-training of deep bidirectional transformers for language understanding.
- Conneau et al. (2020). Unsupervised cross-lingual representation learning at scale.
- Reimers and Gurevych (2019). Sentence-BERT: sentence embeddings using Siamese BERT-networks.
- Nogueira and Cho (2019). Passage re-ranking with BERT.
- Humeau, Shuster, Lachaux and Weston (2020). Poly-encoders: architectures and pre-training strategies for fast and accurate multi-sentence scoring.
- Khattab and Zaharia (2020). ColBERT: efficient and effective passage search via contextualized late interaction over BERT.
- van den Oord, Li and Vinyals (2018). Representation learning with contrastive predictive coding.
- Wang et al. (2022). Text embeddings by weakly-supervised contrastive pre-training.
- Wang et al. (2024). Multilingual E5 text embeddings: a technical report.
- Chen et al. (2024). BGE M3-Embedding: multi-lingual, multi-functionality, multi-granularity text embeddings through self-knowledge distillation.
- Qwen Team (2024). Qwen2.5 technical report.
- Houlsby et al. (2019). Parameter-efficient transfer learning for NLP.
- Hu et al. (2022). LoRA: low-rank adaptation of large language models.
- Dettmers, Pagnoni, Holtzman and Zettlemoyer (2023). QLoRA: efficient finetuning of quantized LLMs.
- Mudgal et al. (2018). Deep learning for entity matching: a design space exploration.
- Li, Li, Suhara, Doan and Tan (2020). Deep entity matching with pre-trained language models.
- Hanley and McNeil (1982). The meaning and use of the area under a receiver operating characteristic (ROC) curve.
- Krogh and Vedelsby (1995). Neural network ensembles, cross validation, and active learning.
