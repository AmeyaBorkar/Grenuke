# F07. Neural networks, transformers and LLMs

**Summary**

- A neural network is a stack of simple functions trained by gradient descent. Backpropagation is the chain rule applied layer by layer.
- Attention lets every token read every other token. Encoders (e5, bge) and decoders (Qwen) are the same blocks with different masks and goals. We use both as pair classifiers (cross-encoders), and fine-tune the 7B one with LoRA.
- The practical side matters too: number formats (fp32, bf16, TF32), why GPU runs are not bit-identical, memory arithmetic for a 7.6B model, our 96-token limit, and why we z-score logits before averaging.

## What you need first

- [F03 machine learning fundamentals](F03-machine-learning-fundamentals.md): loss, gradient descent, overfitting.
- [F13 linear algebra and optimisation](F13-linear-algebra-and-optimisation.md): vectors, matrices, the chain rule, AdamW.
- [F14 information theory and losses](F14-information-theory-and-losses.md): logits, sigmoid, softmax, cross-entropy.
- [F06 text, strings and retrieval](F06-text-strings-and-retrieval.md): why the same name appears in many spellings.

---

## 1. Neurons and layers

**Intuition.** A neuron takes numbers in, multiplies each by a weight, adds them up, and passes the sum through a bend (an activation function). A layer is many neurons side by side. Stacking layers lets the network build complicated functions from simple pieces.

**Definition.** One neuron: $a = w\cdot x + b$, output $\phi(a)$. A layer: $h = \phi(Wx + b)$ with a weight matrix $W$. Common activations: ReLU $=\max(0,a)$, GELU (a smooth ReLU), and SiLU $= a\,\sigma(a)$ where $\sigma$ is the sigmoid. Without the bend, stacked linear layers collapse into one linear layer, so the bend is what gives depth its power.

**Worked example.** Input $x=(1,2)$, weights $w=(0.5,-0.25)$, bias $0.1$. Then $a = 0.5 - 0.5 + 0.1 = 0.1$ and $h=\text{ReLU}(0.1)=0.1$. An output unit with weight $1.5$ and bias $-0.2$ gives $z = 1.5\times0.1 - 0.2 = -0.05$. The match probability is $p=\sigma(-0.05)=0.4875$. If the true label is $y=1$, the log loss is $-\ln 0.4875 = 0.7185$.

## 2. Training and backpropagation

**Intuition.** To lower the loss we need to know how each weight changes it. Backpropagation computes all these slopes in one backward sweep, reusing work.

**Definition.** The **chain rule**: if $L$ depends on $z$, and $z$ on $w$, then $\partial L/\partial w = \partial L/\partial z \cdot \partial z/\partial w$. Run forward and keep the intermediate values; then walk backward, multiplying local slopes. Gradient descent then moves each weight against its slope ([F13](F13-linear-algebra-and-optimisation.md)).

**Worked example** (the neuron above, $y=1$). Going backward:

- $\partial L/\partial z = p - y = -0.5125$;
- output weight: $\times h$ gives $-0.0513$; output bias: $-0.5125$;
- into the hidden unit: $\times 1.5$ gives $-0.7687$; ReLU passes it through since $a>0$;
- first-layer weights: $\times x=(1,2)$ gives $(-0.7687,\,-1.5375)$; bias: $-0.7687$.

PyTorch's autograd gives the same numbers, and a finite-difference check ($(L(w+\epsilon)-L(w-\epsilon))/2\epsilon$) gives $-0.768746$ for the first weight. Notice that the backward sweep needs the forward values $h$ and $a$. For a large model those stored values (activations) can dominate memory (section 11).

Three helpers appear in every modern network. **Residual connections** add a layer's input to its output, so gradients flow straight through. **Normalisation** (LayerNorm, or RMSNorm in Qwen) rescales each token's vector to keep numbers in a steady range. **Dropout** randomly zeroes some units during training to reduce overfitting.

## 3. Tokens and embeddings

**Intuition.** A network works on numbers, so text must be cut into pieces (tokens) and each piece looked up as a vector.

**Definition.** Subword tokenisers (BPE, SentencePiece) learn a vocabulary of frequent pieces, so common words are one token and rare words split into several. An **embedding** is a row of a learned table: token id $i$ becomes vector $E_i$. The table has vocabulary size $\times$ hidden size entries.

**Worked example** (real output of the e5 tokenizer):

| text | tokens |
|---|---|
| lille ecole sarl ; 42 rue gutenberg | lille, e, cole, sar, l, ;, 42, rue, guten, berg (10) |
| ehpvd | eh, pv, d |
| 42 and 205 | one token each |

Each side of a pair gets its own tokens, and the tokenizer joins them as `<s> A </s></s> B </s>`. For the first pair above (against "lille ecole sarl ; 42 q. du wault") that is 26 token ids. Two facts for the project. A garbled word breaks into unusual pieces, so the model must work from letter-level fragments. And "42" and "205" are two unrelated ids: nothing in the table says they are close as numbers.

**Our limit.** We cut each pair at 96 tokens (`MAX_LEN`, truncating the longer side first). The example pairs here use 20 to 31 tokens, so 96 is generous for them; the training log prints the median length (`tokens p50`), which is not recorded on this page. Cost grows with length, and attention grows with its square.

**Size.** The table can be most of a small model. For multilingual-e5-small, 250,037 tokens $\times$ 384 numbers $= 96.0$M of its 117.7M parameters (82%). For Qwen2.5-7B, 152,064 $\times$ 3,584 $= 545$M of 7.6B.

## 4. Attention from scratch

**Intuition.** Each token asks a question (its **query**), and every token advertises what it holds (its **key**). The better a query matches a key, the more of that token's content (its **value**) is copied into the asker. In a cross-encoder, the "42" of the S1 can look at the "42" or "205" in the record directly.

**Definition.** With token matrix $X$ and learned matrices $W_Q, W_K, W_V$: $Q=XW_Q$, $K=XW_K$, $V=XW_V$, and

$$\text{Attention}(Q,K,V)=\text{softmax}\!\left(\frac{QK^\top}{\sqrt{d_k}}\right)V .$$

The softmax runs along each row and turns scores into weights that sum to 1. Dividing by $\sqrt{d_k}$ matters: a dot product of two random $d_k$-dimensional vectors with unit-variance entries has a spread of about $\sqrt{d_k}$ (a quick simulation gives 2.0, 8.0 and 32.0 for $d_k$ = 4, 64, 1024), which would push the softmax into saturation with tiny gradients.

**Worked example.** Three tokens, $d=2$: $X=\begin{pmatrix}1&0\\0&1\\1&1\end{pmatrix}$, $W_Q=W_V=I$, $W_K=\text{diag}(1,2)$. So $K=\begin{pmatrix}1&0\\0&2\\1&2\end{pmatrix}$. For token 3, $q=(1,1)$: scores $q\cdot k_j=(1,\,2,\,3)$, divided by $\sqrt2$: $(0.707,\,1.414,\,2.121)$. Softmax gives weights $(0.14,\,0.284,\,0.576)$. Output $=0.14\,(1,0)+0.284\,(0,1)+0.576\,(1,1)=(0.716,\,0.860)$.

**Variants.**
- **Multi-head**: split the vectors into $h$ heads that attend separately and concatenate, so different heads can look for different relations (same number, same street word).
- **Masks**: a padding mask hides pad tokens. A **causal mask** lets token $i$ see only tokens $\le i$. With it, token 1 of the example can only copy itself and outputs $(1,0)$.
- **Position**: attention ignores order by itself, so position is added (learned vectors in BERT-style encoders, rotary embeddings in Qwen).
- **Cost**: $n^2$ scores per head per layer. At $n=96$ this is small next to the feed-forward layers, but it is why long texts are expensive. FlashAttention (Dao et al. 2022) computes the same result without storing the full $n\times n$ matrix.
- **Grouped-query attention** (Qwen): 28 query heads share 4 key/value heads, so the key and value matrices are small (3584 by 512).

## 5. The transformer block, encoders and decoders

A block is: normalise, attend, add the input back; normalise, feed-forward network, add back. Stack 12 to 28+ blocks.

- An **encoder** (BERT, XLM-RoBERTa: e5, bge) lets every token see every token. Good for reading a full text and classifying it.
- A **decoder** (GPT, Qwen) uses the causal mask and is trained to predict the next token. Good for generating text, and also usable as a classifier (section 8).

Sizes from the model configs (checked on the cached files):

| model | layers | hidden | parameters | note |
|---|---|---|---|---|
| multilingual-e5-small | 12 | 384 | 117.7M | 96.0M in the embedding table |
| bge-reranker-v2-m3 | 24 | 1024 | 567.8M | 256.0M embeddings; built on bge-m3 |
| Qwen2.5-7B | 28 | 3584 | 7.62B | 6.53B outside the embeddings; 28 query, 4 key-value heads; feed-forward width 18,944 |

The Qwen shapes are from the public model configuration (check `config.json` before quoting them); the parameter count follows from the shapes (rebuilding the model on PyTorch's meta device gives 7,615,616,512).

## 6. Pre-training

Pre-training teaches general language skill from unlabelled text, so fine-tuning needs few labels.

- **Masked language modelling** (BERT, Devlin et al. 2019): hide about 15% of the tokens and predict them from both sides. The loss is cross-entropy at the hidden positions.
- **Contrastive learning** (e5, Wang et al. 2022): take pairs of related texts, embed each alone, and pull matched pairs together while pushing the other texts in the batch apart. For a query with similarities $s_j$ to the matched text ($j=1$) and the others, the loss is $-\log\frac{e^{s_1/\tau}}{\sum_j e^{s_j/\tau}}$, where $\tau$ is a temperature. Example: $s=(0.8,0.2,0.1)$. At $\tau=1$ the matched text gets weight 0.489 and the loss is 0.716. At $\tau=0.1$ it gets 0.997 and the loss is 0.003. A small temperature makes the loss care about the sharpest differences.
- **Causal language modelling** (GPT, Qwen): maximise $\sum_t \log p(x_t\mid x_{<t})$. Its exponential is the perplexity ([F14](F14-information-theory-and-losses.md)).

## 7. Fine-tuning, bi-encoders and cross-encoders

**Fine-tuning** starts from pre-trained weights, adds a fresh output head, and trains on labelled pairs with a small learning rate.

- A **bi-encoder** embeds each text alone and compares vectors by cosine. Records are embedded once, so $N$ records need $N$ forward passes and the vectors can be indexed for fast search ([F08](F08-computing-at-scale.md)). It sees the two texts only through two summaries.
- A **cross-encoder** reads both texts in one input and outputs one number. It costs one forward pass per pair, but can compare token to token. That is what spots a nudged house number.

Our cross-encoders are the second kind, on the uncertain band only (1.49M test pairs). The recipe in [ce.py](../../../experiments/ameya/model-v1/ce.py) (the e5-small script; larger runs changed some settings, such as epochs):

- Input: "name ; address" for each side, the S1 first, cut at 96 tokens. Output: one logit, trained with binary cross-entropy.
- Optimiser: AdamW, learning rate 5e-5, weight decay 0.01, batch 128, one epoch, 5% warm-up then linear decay, bf16 autocast.
- Safety: gradient norm clipped to 1. A step with a non-finite gradient is skipped (seen with torch 2.11, where one such step turned every weight into NaN).
- Efficiency: batches are grouped by length to save padding.
- Out of fold: three models, each scoring its own group; the holdout and test get their mean logit.

bge-reranker-v2-m3 already has a one-logit reranker head, and we fine-tuned it fully. The method note's Table 3 lists band AUCs: 0.939 (e5-large), 0.942 (bge), 0.938 (Qwen 1.5B), 0.944 (Qwen 7B), against 0.930 for stage-1 p1 alone.

## 8. A decoder LLM as a pair classifier

**Mechanism.** The text is the S1 string, then " || ", then the record string: "name ; address || name ; address". It goes through the causal transformer. We take the hidden state of the last real token and apply a linear layer (3,584 to 1) to get one logit. The last position is the only one that has seen the whole pair, so the final judgement is read from there. The code sets the pad token id so the model can find that position, and reuses the end-of-sequence token as padding if the tokenizer has none ([llm_group.py](../../../experiments/bakshi/box/llm_group.py), [ce_llm.py](../../../experiments/sachi/ce_llm.py)). This variant has no vocabulary head, so about 7.07B parameters are loaded, not 7.6B.

**Why a decoder helps.** It is pre-trained on far more text, which helps with abbreviations and languages, and its errors differ from an encoder's. The method note: the 7B is no more accurate than a self-trained e5-large (both 0.944), but it adds diversity in the mix and an independent reading of confident pairs ([F18](F18-tuning-ensembles-and-interpretability.md)). Training used one H100 per out-of-fold group, about two hours on three H100s (about six hours on one). Scoring runs at about 600 pairs per second.

## 9. LoRA

**Intuition.** Fine-tuning changes each weight matrix by some update $\Delta W$. That update tends to be simple (low rank), so learn a small factorised update instead of the full one, and freeze $W$ (Hu et al. 2022).

**Definition.**

$$W' = W + \frac{\alpha}{r}\,BA,\qquad B\in\mathbb{R}^{d_\text{out}\times r},\ A\in\mathbb{R}^{r\times d_\text{in}},\ r\ll d .$$

$A$ starts random and $B$ starts at zero, so training begins from the original model. $r$ is the rank and $\alpha$ a scale. Dividing by $r$ keeps the update's size similar when $r$ changes, so the learning rate needs little retuning (Hu et al. 2022). Ours: $r=16$, $\alpha=32$, so the update is scaled by 2, with dropout 0.05, on all seven projections (q, k, v, o, gate, up, down) in all 28 layers, plus a fully trained score head.

**Worked example** (arithmetic from the Qwen2.5-7B shapes). The query projection is $3584\times3584 = 12{,}845{,}056$ numbers. Its LoRA has $16\times(3584+3584)=114{,}688$, which is 112 times fewer. Per layer, the seven projections add up to $1{,}441{,}792$; over 28 layers, $40{,}370{,}176$ trainable numbers, about 0.53% of 7.6B. The key and value projections are narrower (3584 by 512), so they shrink by 28 times only.

After training you can fold $\frac{\alpha}{r}BA$ into $W$ and run at full speed. The gain is mostly memory: gradients and optimiser state exist only for the 40M numbers.

## 10. Number formats, mixed precision and non-determinism

**Formats.** A floating-point number has a sign, exponent bits (range) and mantissa bits (precision).

| format | bits (sign, exponent, mantissa) | spacing near 1 | largest value |
|---|---|---|---|
| fp32 | 1, 8, 23 | $1.2\times10^{-7}$ | $3.4\times10^{38}$ |
| fp16 | 1, 5, 10 | $9.8\times10^{-4}$ | 65,504 |
| bf16 | 1, 8, 7 | $7.8\times10^{-3}$ | $3.4\times10^{38}$ |
| TF32 | 1, 8, 10 (inside tensor cores) | $9.8\times10^{-4}$ | $3.4\times10^{38}$ |

Examples (run in PyTorch): bf16 turns 1.003 into 1.0, fp16 gives 1.0029; 70,000 is `inf` in fp16 but 70,144 in bf16. So bf16 keeps fp32's range with coarser steps, and needs no loss scaling. fp16 has finer steps but a small range. TF32 is a matrix-multiply mode of recent NVIDIA GPUs: inputs rounded to 10 mantissa bits, sums kept in fp32.

**Mixed precision** (Micikevicius et al. 2018): do the heavy matrix multiplies in low precision, keep sums, the loss and the master weights in fp32. Ours: the 7B base weights are frozen in bf16, the LoRA and score-head weights are fp32, matmuls run under bf16 autocast, the loss is computed in float, and TF32 is allowed for matmuls.

**Why runs are not bit-identical.** Floating-point addition is not associative. In float32, $(10^8+1)-10^8 = 0$ but $(10^8-10^8)+1 = 1$. Summing the same 1,000,000 random float32 numbers forwards and backwards gave 998.57056 and 998.5707 (float64: 998.57066). On a GPU, thousands of threads add partial sums in an order that depends on the kernel, the batch shape, the card, the number of GPUs and the library version. Some CUDA operations (such as scatter-style atomic adds) can be non-deterministic unless deterministic mode is requested. Tiny differences then compound over thousands of steps. Our evidence: an earlier model rebuilt on other hardware moved from 0.991246 to 0.991261 on the holdout, so a rerun should land within about 0.0001 ([method note](../../../experiments/ameya/final-zip/doc/Documentation_template.md), appendix A). Even the inference batch size changes bf16 rounding ([llm_group.py](../../../experiments/bakshi/box/llm_group.py)). Fixed seeds remove random choices, not hardware order.

## 11. GPU memory arithmetic for a 7.6B model

| item | arithmetic | size |
|---|---|---|
| weights in fp32 | 7.6B $\times$ 4 bytes | 30.4 GB |
| weights in bf16 | 7.6B $\times$ 2 bytes | 15.2 GB (14.1 GB without the vocabulary head) |
| full fine-tune with Adam, mixed precision | 7.6B $\times$ 16 bytes | 121.6 GB |
| LoRA trainable state | 40.4M $\times$ 16 bytes | 0.65 GB |

The 16 bytes per parameter for full fine-tuning are: 2 (bf16 weight), 2 (gradient), 12 (fp32 master copy, momentum and variance) (Rajbhandari et al. 2020). That is more than an 80 GB H100 before counting activations, so full fine-tuning does not fit and LoRA does: 15.2 GB frozen plus 0.65 GB of trainable state.

**Activations.** A batch of 64 pairs at 96 tokens is 6,144 tokens. One hidden-size tensor in bf16 is $6144\times3584\times2 = 44$ MB. One feed-forward-width tensor is $6144\times18944\times2 = 233$ MB. The backward pass needs several tensors of both kinds per layer, across 28 layers, so activations can reach tens of GB. **Gradient checkpointing** (flag `--grad-ckpt`) keeps only each layer's input and recomputes the rest, trading about a third more compute for much less memory. Batches are grouped by length, which limits padding.

**Why three GPUs.** The three out-of-fold models are independent, so each ran on its own H100 (about 2 hours instead of about 6).

## 12. Logits and z-scoring before averaging

A **logit** is the raw output before the sigmoid: $\text{logit}(p)=\ln\frac{p}{1-p}$. A logit of $-6$ means $p=0.0025$; $-2$ means 0.119; 0 means 0.5; $+2$ means 0.881.

Different models give logits on different scales: one head may spread over $\pm 4$, another over $\pm 15$. A plain average lets the widest model dominate. So we **z-score** each model first: $z=(\ell-\mu)/\sigma$, with $\mu,\sigma$ the mean and standard deviation of that model's logits over the training band, then average the $z$ values ([zmean_ce.py](../../../experiments/ameya/model-v1/zmean_ce.py)).

**Worked example (toy).** Model A: $\mu=0,\sigma=4$, logit 3.0, so $z=0.75$. Model B: $\mu=0,\sigma=1.5$, logit 1.2, so $z=0.80$. Mean $z=0.775$ (the models roughly agree). The raw mean is 2.1, which is almost entirely A's opinion.

We average logits, not probabilities, because probabilities saturate: logits $-9$ and $-14$ are both $p\approx0$ but very different evidence. Logit space is where models add up evidence.

---

## How it shows up in our project

- Cross-encoders: [ce.py](../../../experiments/ameya/model-v1/ce.py) (e5, bge), [ce_llm.py](../../../experiments/sachi/ce_llm.py) and [llm_group.py](../../../experiments/bakshi/box/llm_group.py) (Qwen, LoRA), [zmean_ce.py](../../../experiments/ameya/model-v1/zmean_ce.py) (z-scored mean).
- Advanced pages: [08 transformers and cross-encoders](../08-transformers-and-cross-encoders.md), [10 LLM verification and compute](../10-llm-verification-and-compute.md).

## How to read the numbers

- **AUC 0.930 to 0.944.** AUC is the chance that a random true pair outscores a random false pair. These are measured only on the uncertain band, where pairs are hard, so they are not comparable with an AUC over all pairs. A gain of 0.014 is a real but modest change in ranking.
- **Logit $-6$ for the 7B re-check.** On a labelled 34% sample, 8.3% of confident predictions scored below $-6$ were real matches, against 92.6% between $-6$ and $-2$ (method note, appendix B). A logit of $-6$ would mean 0.25% for a typical pair. But these are predictions that stage 1 had already made confidently, a pre-selected population with a much higher base rate. So the logit is not a calibrated probability here, and we fixed the cut on labelled data ([07 calibration](../07-calibration.md)).
- **Parameter counts.** "7.6B" counts the embedding tables; our classifier variant loads 7.07B.

## Common misconceptions

1. "A neural network is a black box nobody can analyse." Every number in section 2 is checkable by hand.
2. "Attention means the model understands." It is a weighted average, learned.
3. "Bigger always means better." Qwen 7B equals a self-trained e5-large on band AUC (0.944 each).
4. "LoRA trains fewer parameters, so it is weaker." It trains 0.53% of the numbers, and was reported to match full fine-tuning on many tasks (Hu et al. 2022); for a given task, test it.
5. "bf16 is a lower-quality fp16." It has fewer mantissa bits but fp32's range.
6. "Same seed, same result." Not on GPUs (section 10).
7. "Logits are probabilities." They are log-odds; apply the sigmoid.
8. "Averaging model outputs is always safe." Not without putting them on one scale.

## Check yourself

Exercise 1. Run the neuron of section 1 with $x=(2,0)$, $w=(0.5,-0.25)$, $b=0.1$, output weight 1.5, output bias $-0.2$. What are $p$ and the loss for $y=1$?

<details><summary>Answer</summary>

$a=1+0+0.1=1.1$, $h=1.1$, $z=1.5\times1.1-0.2=1.45$, $p=\sigma(1.45)=0.810$, loss $=-\ln0.810=0.211$.

</details>

Exercise 2. For that neuron, what is $\partial L/\partial w_1$ at $x=(2,0)$?

<details><summary>Answer</summary>

$\partial L/\partial z=p-y=-0.190$. Through the output weight: $\times1.5=-0.285$. ReLU passes it ($a>0$). Times $x_1=2$: $-0.570$.

</details>

Exercise 3. Why do attention scores get divided by $\sqrt{d_k}$?

<details><summary>Answer</summary>

A dot product of two random $d_k$-dimensional vectors has standard deviation about $\sqrt{d_k}$ (2, 8, 32 for $d_k$ = 4, 64, 1024). Without the division, large $d_k$ gives large scores, the softmax saturates to a one-hot vector, and gradients almost vanish.

</details>

Exercise 4. What does a causal mask do, and why does the decoder classifier read the last token?

<details><summary>Answer</summary>

It stops token $i$ from attending to later tokens. So only the last real token has seen the whole pair, and its hidden state is the one fed to the linear score layer.

</details>

Exercise 5. A LoRA with $r=16$ on a $4096\times4096$ matrix: how many trainable numbers, and what fraction of the full matrix?

<details><summary>Answer</summary>

$16\times(4096+4096)=131{,}072$. The full matrix has $16{,}777{,}216$. Fraction $=0.78\%$ (128 times fewer).

</details>

Exercise 6. Why can 7.6B parameters be fine-tuned with LoRA on one 80 GB GPU but not fully?

<details><summary>Answer</summary>

Full fine-tuning with Adam in mixed precision needs about 16 bytes per parameter: $7.6\text{B}\times16=121.6$ GB, above 80 GB. With LoRA the base weights are frozen in bf16 (15.2 GB) and only 40M numbers need gradients and optimiser state (0.65 GB), plus activations.

</details>

Exercise 7. Why does bf16 need no loss scaling but fp16 does?

<details><summary>Answer</summary>

fp16 has a small range (largest 65,504, smallest normal about $6\times10^{-5}$), so tiny gradients underflow to zero. Loss scaling multiplies the loss to keep gradients in range. bf16 has fp32's exponent range, so gradients do not underflow.

</details>

Exercise 8. Give two reasons the same GPU job can give slightly different results on two machines.

<details><summary>Answer</summary>

Float addition is not associative, so a different summation order (different kernel, batch shape, card, GPU count, library version) changes low-order bits. Some operations use atomic adds in a non-deterministic order. The differences compound over many steps. We saw 0.991246 versus 0.991261 for a model rebuilt elsewhere.

</details>

Exercise 9. Model A has $\mu=1,\sigma=2$ and logit 5; model B has $\mu=-1,\sigma=1$ and logit 2. Compute the z-scored mean.

<details><summary>Answer</summary>

$z_A=(5-1)/2=2$. $z_B=(2+1)/1=3$. Mean $=2.5$.

</details>

Exercise 10. A pair's 7B logit is $-6$. What probability does that mean, and what share of such predictions were real matches in our labelled check? What do you conclude?

<details><summary>Answer</summary>

$\sigma(-6)=0.0025$. In the labelled check, 8.3% of confident predictions below $-6$ were real matches. The population was already filtered by stage 1, so its base rate of matches is far higher than for a random pair, and the logit is not a calibrated probability there. The cut at $-6$ was chosen on labelled data for its measured effect, not from its nominal probability.

</details>

## Going deeper

- Rumelhart, Hinton and Williams (1986). Learning representations by back-propagating errors.
- Vaswani et al. (2017). Attention is all you need.
- Devlin et al. (2019). BERT: pre-training of deep bidirectional transformers for language understanding.
- Reimers and Gurevych (2019). Sentence-BERT.
- Wang et al. (2022). Text embeddings by weakly-supervised contrastive pre-training.
- Qwen Team (2024). Qwen2.5 technical report.
- Hu et al. (2022). LoRA: low-rank adaptation of large language models.
- Micikevicius et al. (2018). Mixed precision training. Kalamkar et al. (2019). A study of BFLOAT16 for deep learning training.
- Rajbhandari et al. (2020). ZeRO: memory optimizations toward training trillion parameter models.
- Dao et al. (2022). FlashAttention. Chen et al. (2016). Training deep nets with sublinear memory cost.
- Sennrich, Haddow and Birch (2016). Neural machine translation of rare words with subword units.

## Where next

- [F18](F18-tuning-ensembles-and-interpretability.md): why diversity of cross-encoders helped France.
- [F13](F13-linear-algebra-and-optimisation.md): the optimisers and schedule used here.
- [F08](F08-computing-at-scale.md): throughput and cost arithmetic.
- [08](../08-transformers-and-cross-encoders.md) and [10](../10-llm-verification-and-compute.md) for the advanced treatment.
