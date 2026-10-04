# LLM verification and compute-aware cascades

**Summary.** A cascade spends compute where it can change a decision: cheap trees on every pair, cross-encoders on the uncertain band, and a 7B model where a second opinion pays.
Because 94.5% of our final predictions had p1 > 0.99, no cross-encoder had ever read them. Bakshi's LoRA-tuned Qwen2.5-7B re-read them, and we dropped those it rejected with a logit below −6, a cut-off fixed on labelled data before France was touched.
It removed 840 French decoys, and the 7B's two roles together added +0.00018 on the public leaderboard.

Related pages: [gradient boosting and cascades](06-gradient-boosting-and-stacking.md), [calibration](07-calibration.md) (break-even arithmetic), [cross-encoders and LoRA](08-transformers-and-cross-encoders.md), [scaling](11-scaling-to-billions.md), [glossary](glossary.md).

---

## 1. Intuition

- **Triage.** A hospital gives everyone a cheap test and sends only the unclear cases to the scanner. Our trees are the cheap test, the cross-encoders the scanner for the 2.6% of pairs stage 1 hesitates on.
- **A second opinion** is worth asking where an error is costly and a different kind of reader might see what the first missed. Under F0.5 a wrong match costs about twice as much as a missed one, and our feature models and a 7B reading raw text are very different readers.
- **Confident is not the same as correct.** A model can be sure and wrong in a systematic way. In France, generic names let decoys reach p1 > 0.99, where no cross-encoder looked.
- **Abstaining is an action.** Dropping a doubtful match is the F0.5 version of saying "I don't know".

## 2. Formal definition

### 2.1 Cost of a cascade

If a share $\pi_k$ of the pairs reaches stage k at cost $c_k$ per pair, the cost per retrieved pair is $C = \sum_k \pi_k c_k$. Running an expensive reader B on a pair is worth it when

$$P(\text{B changes the decision}) \times \mathbb{E}[\text{gain} \mid \text{change}] > \text{cost of B}.$$

The band (0.02 ≤ p1 ≤ 0.99) maximises the first factor for the cross-encoders. The re-check targets a different term: changes there are rare, but each correct drop is worth a lot, about +0.19 F0.5 for the S1 concerned (self-test 2).

### 2.2 Selective prediction

Chow's reject option gives a classifier a third action, abstain, at a fixed cost. A selective classifier is judged by its risk (the error rate on what it keeps) against its coverage (the share it keeps). Our version is one-sided: a predicted match is kept unless a second reader rejects it strongly,

$$\text{keep}(s, r) \iff \neg\big(p_1(s,r) > 0.99 \ \wedge\ \ell_{7B}(s,r) < t\big),$$

with t = −6. Every pair dropped lowers coverage by one prediction; the gain is the false matches removed.

### 2.3 Why a second model helps: error independence

For two readers A and B,

$$P(\text{both wrong}) = P(A\ \text{wrong})\; P(B\ \text{wrong} \mid A\ \text{wrong}).$$

If errors were independent, the second factor would be B's own error rate and a veto would remove most of A's mistakes. In practice it is larger, because models trained on the same data and labels err on the same hard cases. The value of a second opinion therefore depends on **where the errors decorrelate**: a different model family, different inputs (raw text against hand features), different training data (French pseudo-labels). On the US/India holdout the 7B removed only 22 of roughly 650 false predictions in the sample [E]; in France it removed a whole class of decoys the feature models shared.

### 2.4 Fixing the cut-off on labelled data first

A cut-off chosen by looking at French scores would be tuned on our own beliefs (France has no labels) or on leaderboard probes, which is data snooping with five uploads a day. So the rule was set on labelled US/India pairs, checked on two fixed halves and on random subsets, and only then applied, unchanged, to France. The leaderboard was the outside check, not the tuning set.

## 3. Variants

| variant | idea | relation to ours |
|---|---|---|
| Boosted cascades (Viola–Jones) | cheap stages reject most inputs early | stages 0 → 1 → cross-encoders |
| Reject option, selective classification | abstain when unsure; trade risk against coverage | the 7B veto is a one-sided reject option |
| Learning to defer | learn when to hand a case to a stronger decider | a learned router could replace our fixed band |
| LLM cascades (FrugalGPT) | query cheap models first, escalate when unsure | the same economics with API costs |
| Co-training, multi-view checks | two views of the data correct each other | text view (7B) against feature view (XGBoost) |
| Distillation | a small model learns a large model's scores | how a 7B reader would scale ([page 11](11-scaling-to-billions.md)) |
| Zero-shot LLM judging | prompt a general LLM to decide a match | possible, but prompt-sensitive; we fine-tuned instead |

## 4. Where we used it

**The cascade on the test set** [M]/[R]:

| stage | test pairs | reader | cost |
|---|---|---|---|
| retrieval | 58.4M | IDF token search per country | about 15 minutes on a 64-vCPU box |
| stages 0–1 | 58.4M → about 15–20% | 200 trees, then about 1,600 deep trees × 4 | about 4 minutes |
| stages 2–3 | the candidates | XGBoost with context features | minutes to score; about 20 minutes per stage-2 fit |
| cross-encoders | 1,490,930 band pairs | e5, bge, Qwen 1.5B and 7B | about 1 hour per e5-large trio on one H100; the 7B about 2 hours on three H100s, training included |
| 7B re-check | 5,614,414 confident predictions (870,019 French, 4,744,395 US/India) | Qwen2.5-7B, one adapter | about 3.6 GPU-hours |
| 7B on every pair (not done) | 58.4M | Qwen2.5-7B | about 27 GPU-hours at 600 pairs/s |

**The re-check** (Bakshi: [`score_pairs.py`](../../experiments/bakshi/box/score_pairs.py), `rescore_eval.py`, [`compose_tsv.py`](../../experiments/bakshi/box/compose_tsv.py); analysis with Ameya). The adapter of OOF group 0 scored every final prediction with p1 > 0.99. Truth by 7B logit, on a 34% sample of holdout S1 that no adapter trained on (186,897 S1, 631,001 predictions) [M]:

| 7B logit | holdout predictions | truly a match | French predictions (share) |
|---|---|---|---|
| < −6 | 24 | 8.3% | 859 (0.10%) |
| −6 to −4 | 51 | 86.3% | 209 (0.02%) |
| −4 to −2 | 138 | 94.9% | 321 (0.04%) |
| −2 to 0 | 6,616 | 99.6% | 897 (0.10%) |
| ≥ 0 | 596,333 | 99.8–100% | 785,090 (90.2%) |

Change in holdout macro F0.5 for "drop if logit < t" [M] (Bakshi's [methodology](../../experiments/bakshi/final-package/METHODOLOGY_bakshi.md) §5):

| t | drops | truly matches | ΔF0.5, all | half A | half B |
|---|---|---|---|---|---|
| −8 | 7 | 0 | +11e-6 | +4e-6 | +19e-6 |
| **−6** | **24** | **2** | **+33e-6** | **+22e-6** | **+43e-6** |
| −5 | 36 | 12 | +26e-6 | +8e-6 | +43e-6 |
| −4 | 75 | 46 | +12e-6 | −3e-6 | +27e-6 |
| −2 | 213 | 177 | −55e-6 | −67e-6 | −42e-6 |

- −6 has the largest gain and is positive in both halves. On the whole holdout (three times larger) it gave +37e-6 (halves +33 and +41), and it was positive in 99.7% of 3,000 random 25% subsets (mean +32.8e-6).
- The bucket just above, −6 to −4, is 86.3% true, above the 77–80% break-even for a drop ([page 07](07-calibration.md)), which is why looser cut-offs lose.

**On test:** 859 French rejects (0.10% of French predictions) against 310 of 4.74M US/India predictions (0.0065%): 15 times the US/India test rate, 25 times their holdout rate. Composite B dropped 1,150 pairs, 840 of them French.

**What the French rejects are.** 78% have the same generic name and the same house number on a different street, such as "lille ecole sarl | 42 rue gutenberg" against "42 q. du wault". On labelled US/India data that pattern is both a copy and a decoy, and the 7B separates the two:

| same name, same number, different street (holdout) | pairs | true | 7B median | 7B < −6 |
|---|---|---|---|---|
| predicted by our model | 380 | 99.7% | +7.9 | 0 |
| rejected by our model | 218 | 0.5% | −9.9 | 202 |

In France, where each rejected pair's name is shared by a median of 43 S1, the feature models accepted these decoys with confidence; the 7B scores them like the US/India decoys. Only 4 of the 859 records sit at another same-name S1's street and number, so they are decoys, not copies given to the wrong S1 ([RESEARCH_v6 §6.19](../../experiments/ameya/model-v1/RESEARCH_v6.md)).

**Checks from outside the loop.**
- **Leakage:** adapter 0 learned French pseudo-labels of S1 thirds 1–2, yet flags French pairs at the same rate in all thirds: 0.112% in the unseen third, 0.108% and 0.107% in the others.
- **An independent detector:** a bge cross-encoder trained on US/India labels and synthetic French pairs, with no self-training labels, flags 708 of the 859 French rejects (82%).
- **The leaderboard:** Composite B scored 0.990879 against mixmdp's 0.990699, +180e-6 (we predicted +149e-6). Bakshi's split by holdout deltas: India g1w ≈ +31e-6, US g1w ≈ +10e-6, US/India drops ≈ +28e-6, so the 840 French drops ≈ +111e-6 [E], meaning they were nearly all false.
- **Going further did not pay:** B7 extended the French drops toward −2 where Qwen3-4B agreed (+251 / −1,699 French pairs) and scored 0.990875, a tie. The labelled −6 was already right.

**What we tried and dropped.** Using the 7B for recall: its best holdout precision for additions was 71% (69 pairs above logit 4, 49 true), under the 75% break-even. A depth-5 tree mining extra drops gained +33e-6 on half A and lost 15e-6 on the held-out half B: overfit.

## 5. Why it fits this problem

- **The blind spot was in the confident region.** 94.5% of final predictions sit at p1 > 0.99, outside the band, so their correctness rested on hand features alone, and the French decoys lived exactly there.
- **The second reader is genuinely different:** a 7.6B decoder reading raw text, against gradient-boosted trees on string and context features.
- **It is affordable:** 5.6M pairs, about 3.6 GPU-hours, against 27 for every retrieved pair.
- **F0.5 rewards precision:** dropping a pair that is only 8% likely true gains in expectation, because the break-even false rate for a drop is 20–25%.

## 6. Pitfalls

1. **Small numbers behind the cut-off:** 24 holdout drops at −6. We leaned on both halves, the whole holdout and 3,000 subsets rather than on one figure, and still treat the exact value as approximate.
2. **Extrapolating a rate:** France has 15–25 times the decoy rate at < −6, but that did not carry into −6 to −2 (B7 tied).
3. **Correlated errors:** a second model trained on the same labels repeats most of the first one's mistakes; the veto removed only a few percent of US/India false positives.
4. **Calibration:** an LLM logit is not a probability. We read it through truth rates per bucket on labelled pairs.
5. **Prompt and format sensitivity:** prompted LLMs change answers with wording and example order. We fine-tuned a classification head instead, which moves the risk to keeping one input format: `score_pairs.py` reuses the training encoding exactly (" || " separator, 96 tokens).
6. **Inherited bias:** the 7B was self-trained on French pseudo-labels, so it could repeat the teacher; the leakage-by-third check and the independent bge detector address this.
7. **Licence and size:** only MIT or Apache-2.0 models up to 8B parameters. Qwen2.5-7B (7.6B, Apache-2.0) fits; Qwen2.5-3B is excluded by its licence.
8. **Infrastructure:** interruptible boxes. The 7B training resumed from checkpoints written every 600 seconds; scores differ slightly across GPUs.

## 7. Jury questions with answers

**Q1. Why re-check predictions you were already 99% sure of?**
Because 94.5% of our predictions were there and no cross-encoder had read them. Confidence came from hand features, which France's generic names could fool. The re-check changed 0.10% of French predictions and almost nothing elsewhere, which is what a targeted second opinion should do.

**Q2. How did you choose −6 with only 24 holdout drops?**
On labelled data, before France: it had the largest gain (+33e-6), was positive in both fixed halves, gave +37e-6 on the whole holdout and was positive in 99.7% of random subsets. Looser cut-offs had a negative half or lost outright.

**Q3. 8% of the rejected pairs are real matches. Why drop them?**
Under F0.5, dropping a prediction pays when it is more than about 20–25% likely to be false; at 92% false, each drop gains about +0.19 F0.5 for its S1 in expectation. The two true pairs lost on the holdout were outweighed by the 22 false ones removed.

**Q4. How do you know the 7B was not just repeating your French pseudo-labels?**
It flags French pairs at the same rate in the S1 third it never trained on (0.112% against 0.108% and 0.107%), an independent bge detector agrees on 82% of its rejects, and the leaderboard rose by +180e-6 when they were dropped.

**Q5. Why not run the 7B on every pair?**
At about 600 pairs per second per H100, the 58.4M test pairs alone are about 27 GPU-hours, before training. The band and the confident predictions together are about 7.1M pairs.

**Q6. Why fine-tune a classifier instead of prompting an LLM?**
A fine-tuned head gives one calibratable logit per pair, learns our exact noise from 1.5M labelled band pairs, and avoids prompt sensitivity. A 7B prompted zero-shot would be cheaper to set up but less accurate and harder to calibrate, and API models were ruled out anyway.

**Q7. Why not push further for France, where decoys are 25 times as common?**
We tried: B7 extended the French drops toward −2 and tied with Composite B (0.990875 against 0.990879). The higher decoy rate did not carry into the higher logit buckets, so the labelled cut-off stood.

**Q8. What does this cost at scale?**
The re-check is linear in predictions, about 3.2 per S1, so at 100 times our size it is about 360 GPU-hours. We would restrict it to risky slices, such as names shared by many S1, or distil the 7B into a small model ([page 11](11-scaling-to-billions.md)).

## 8. Self-test

1. At 600 pairs per second, how long does the 7B take for the 58.4M retrieved pairs, the 1.49M band pairs and the 5.6M re-check pairs?
<details><summary>Answer</summary>

58.4M / 600 ≈ 97,000 s ≈ 27 GPU-hours; 1.49M / 600 ≈ 2,500 s ≈ 41 minutes; 5.6M / 600 ≈ 9,400 s ≈ 2.6 hours (we measured about 3.6 GPU-hours at 430–480 pairs per second with several jobs per box).

</details>

2. An S1 has three true predictions and a fourth that is true with probability 0.08 (if true, the S1 has 4 copies; if not, 3). What is the expected gain of dropping it?
<details><summary>Answer</summary>

Keep: 0.08 × 1.0 + 0.92 × 1.25·3/4.75 = 0.08 + 0.92 × 0.789 = 0.806. Drop: 0.08 × 1.25·3/4 + 0.92 × 1.0 = 0.075 + 0.92 = 0.995. Gain about +0.19.

</details>

3. Readers A and B are wrong on 1% and 5% of pairs. How often are both wrong if errors are independent, and if half of A's errors are also B's?
<details><summary>Answer</summary>

Independent: 0.01 × 0.05 = 0.05%. Correlated: 0.01 × 0.5 = 0.5%, ten times more. Decorrelation is what makes a veto useful.

</details>

4. Why does a cut-off at −4 do worse than −6?
<details><summary>Answer</summary>

It also drops the −6 to −4 bucket, which is 86.3% true, above the 77–80% break-even for a drop. Those drops lose more than the extra false pairs gain; one half turns negative.

</details>

5. Write the re-check as a selective-prediction rule and say what it costs in coverage on the holdout sample.
<details><summary>Answer</summary>

Keep a predicted pair unless p1 > 0.99 and the 7B logit < −6. It removed 24 of 631,001 predictions (coverage falls by 0.004%), and 22 of those were false.

</details>

6. Why fix the cut-off on labelled data rather than on the French scores?
<details><summary>Answer</summary>

France has no labels, so a French-tuned cut-off would follow the model's own beliefs or leaderboard probing. A labelled choice, checked on halves, can be applied unchanged and then judged by an outside check, the leaderboard.

</details>

## 9. Further reading

- Chow (1970). On optimum recognition error and reject tradeoff.
- El-Yaniv and Wiener (2010). On the foundations of noise-free selective classification.
- Geifman and El-Yaniv (2017). Selective classification for deep neural networks.
- Viola and Jones (2001). Rapid object detection using a boosted cascade of simple features.
- Madras, Pitassi and Zemel (2018). Predict responsibly: improving fairness and accuracy by learning to defer.
- Chen, Zaharia and Zou (2023). FrugalGPT: how to use large language models while reducing cost and improving performance.
- Dietterich (2000). Ensemble methods in machine learning.
- Kuncheva and Whitaker (2003). Measures of diversity in classifier ensembles and their relationship with the ensemble accuracy.
- Blum and Mitchell (1998). Combining labeled and unlabeled data with co-training.
- Hinton, Vinyals and Dean (2015). Distilling the knowledge in a neural network.
- Zhao, Wallace, Feng, Klein and Singh (2021). Calibrate before use: improving few-shot performance of language models.
- Narayan, Chami, Orr and Ré (2022). Can foundation models wrangle your data?
- Hu et al. (2022). LoRA: low-rank adaptation of large language models.
