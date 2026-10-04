# F13. Linear algebra and optimisation

**Summary**

- Vectors and matrices are how text, pairs and neural networks become numbers. TF-IDF cosine, attention and LoRA are all dot products and matrix products.
- SVD gives the best low-rank approximation of a matrix, PCA is the same idea on centred data, and LoRA uses low rank to train 0.53% of a 7.6B model.
- Training is gradient descent. The chain rule gives gradients, momentum and Adam steer the steps, warm-up and decay schedule them, and XGBoost adds second-order information to size each step.

## What you need first

- [F03 machine learning fundamentals](F03-machine-learning-fundamentals.md): what a loss is, what training does.
- High-school calculus: a derivative is a slope.
- Helpful: [F06 text, strings and retrieval](F06-text-strings-and-retrieval.md) for TF-IDF cosine, [F05 trees and ensembles](F05-trees-and-ensembles.md) for boosting.

---

## 1. Vectors, dot products, norms, cosine

**Intuition.** A vector is a list of numbers, or an arrow. Two arrows pointing the same way are similar, whatever their lengths.

**Definition.** For $a,b\in\mathbb{R}^n$: the **dot product** is $a\cdot b=\sum_i a_ib_i$; the **norm** (length) is $\lVert a\rVert=\sqrt{a\cdot a}$; the **cosine similarity** is

$$\cos\theta=\frac{a\cdot b}{\lVert a\rVert\,\lVert b\rVert}\in[-1,1].$$

A **unit vector** has norm 1. For unit vectors $u,v$: $\lVert u-v\rVert^2 = 2-2\cos\theta$, so ranking by cosine and by distance agree, and the cosine is just the dot product.

**Other norms.** The L1 norm is $\sum|a_i|$. As a penalty on weights, L2 ($\lambda\sum w^2$) shrinks them smoothly, and L1 ($\alpha\sum|w|$) pushes some to exactly zero. XGBoost's `lambda` is L2 and its `alpha` is L1; AdamW's weight decay is L2-like. We use L2 (`lambda` 2 in stages 1 and 2).

**Worked example.** $a=(1,2,2)$, $b=(2,0,1)$. $a\cdot b = 2+0+2=4$, $\lVert a\rVert=3$, $\lVert b\rVert=\sqrt5=2.236$, so $\cos\theta = 4/(3\times2.236)=0.596$. As unit vectors their squared distance is $0.807 = 2-2\times0.596$.

**In our project.** The retrieval score of [F06](F06-text-strings-and-retrieval.md) is a cosine. Give each record a vector with one entry per word: $\sqrt{\text{idf}}$ if the word is present, 0 if not. The dot product of two records is then the sum of idf over their shared words, and the norm is $\sqrt{\sum \text{idf}}$ over their own words. That is exactly the formula in [search.py](../../../code/business_entity_resolution/src/ber/block/search.py).

## 2. Matrices

**Intuition.** A matrix is a machine that turns a vector into another vector. A neural-network layer is one: $y=Wx+b$.

**Definition.** An $m\times n$ matrix times an $n\times p$ matrix is an $m\times p$ matrix, $(AB)_{ij}=\sum_k A_{ik}B_{kj}$. It costs $m\cdot n\cdot p$ multiply-adds. The **rank** is the number of independent rows (equivalently, columns). A rank-1 matrix is an outer product $uv^\top$.

**Worked example.** $A=\begin{pmatrix}1&2&0\\0&1&3\end{pmatrix}$, $B=\begin{pmatrix}1&0\\2&1\\0&4\end{pmatrix}$. $AB=\begin{pmatrix}1+4+0&0+2+0\\0+2+0&0+1+12\end{pmatrix}=\begin{pmatrix}5&2\\2&13\end{pmatrix}$, using $2\times3\times2=12$ multiply-adds.

**Where it hides.** The feed-forward matrix of Qwen2.5-7B has $3584\times18944 = 67.9$M entries. Attention scores for all token pairs are one product, $QK^\top$ ([F07](F07-neural-networks-transformers-llms.md)). Scoring 1.73M queries against 10M documents is one huge product ([F08](F08-computing-at-scale.md)). GPUs are built to do matrix products fast.

## 3. Sparse versus dense

**Intuition.** If almost every entry is zero, store only the non-zeros.

**Definition.** In CSR (compressed sparse row) format, row $i$'s non-zero columns sit in `codes[indptr[i]:indptr[i+1]]`. Memory is proportional to the number of non-zeros (nnz), not to rows $\times$ columns.

**Worked example (toy numbers).** 10M records over a 5M-word vocabulary. Dense float32: $10^7\times5\times10^6\times4$ bytes $=2\times10^{14}$ bytes, 200 TB. Sparse with 8 words per record: nnz $=8\times10^7$, at 8 bytes per entry (index plus value) 640 MB. Our index stores only record ids (the vectors are binary), 4 bytes per entry.

Sparse vectors suit retrieval: a shared rare word is an exact, visible signal, and a dot product only visits shared non-zeros (the inverted index of [F06](F06-text-strings-and-retrieval.md)). Dense vectors (embeddings of 256 to 1024 numbers) are small and capture similarity beyond shared words, but blur exactness (section 6).

## 4. Eigenvalues and eigenvectors

**Intuition.** Most vectors change direction when a matrix acts on them. Some special directions are only stretched.

**Definition.** $Av=\lambda v$ with $v\ne0$: $v$ is an **eigenvector** and $\lambda$ its **eigenvalue**. They solve $\det(A-\lambda I)=0$. A symmetric matrix has real eigenvalues and orthogonal eigenvectors, so $A=Q\Lambda Q^\top$ (spectral theorem).

**Worked example.** $A=\begin{pmatrix}2&1\\1&2\end{pmatrix}$. $\det(A-\lambda I)=(2-\lambda)^2-1=\lambda^2-4\lambda+3$, so $\lambda=3$ or $1$. Check: $A(1,1)=(3,3)=3\,(1,1)$ and $A(1,-1)=(1,-1)=1\,(1,-1)$. The unit eigenvectors are $(1,1)/\sqrt2$ and $(1,-1)/\sqrt2$.

## 5. Singular value decomposition

**Intuition.** Any matrix, even a non-square one, can be written as a sum of simple rank-1 layers, ordered from most important to least.

**Definition.** Every $m\times n$ matrix factors as $A=U\Sigma V^\top$, with orthonormal columns in $U$ and $V$ and non-negative **singular values** $\sigma_1\ge\sigma_2\ge\dots$ on the diagonal of $\Sigma$. Equivalently $A=\sum_i\sigma_i u_iv_i^\top$. The $\sigma_i^2$ are the eigenvalues of $A^\top A$. The **Eckart-Young theorem** (1936) says the best rank-$k$ approximation of $A$, in the sense of squared error, is the sum of the first $k$ layers, and its squared error is $\sum_{i>k}\sigma_i^2$.

**Worked example.** Four businesses over four words (dental, clinic, pizza, grill), 1 if present:

$$A=\begin{pmatrix}1&1&0&0\\1&0&0&0\\0&0&1&1\\0&0&0&1\end{pmatrix}.$$

Rows 1 and 2 are dental places, rows 3 and 4 are pizza places. The singular values are $1.618,\ 1.618,\ 0.618,\ 0.618$ (the golden ratio and its inverse; checked in numpy). Keeping rank 2 leaves squared error $0.618^2+0.618^2=0.764$, and the rank-2 matrix keeps the two blocks, one per topic, while smoothing inside them. In text retrieval this is latent semantic analysis (Deerwester et al. 1990): SVD of a TF-IDF matrix places documents in a few "topic" dimensions. For huge matrices a randomised SVD (Halko et al. 2011) multiplies $A$ by a thin random matrix to capture its main directions, orthonormalises, and takes an exact SVD of the small result, so the cost is about $mnk$ instead of $mn^2$. New rows are embedded without refitting by projecting onto the fitted directions, $x\mapsto xV_k$. That is the plan's "fit on a 2M sample, transform in chunks" ([FINAL_PLAN](../../../plans/FINAL_PLAN.md)).

## 6. PCA, and the planned-but-unbuilt SVD retrieval

**PCA.** Centre the data (subtract the mean of each column) to get $X_c$. The covariance matrix is $C=X_c^\top X_c/(n-1)$. Its eigenvectors are the **principal components**, directions of greatest variance, and its eigenvalues are the variances along them. It is the same as the SVD of $X_c$, with $\lambda_i=\sigma_i^2/(n-1)$.

**Worked example.** Points $(1,1),(2,3),(3,2),(4,4)$, mean $(2.5,2.5)$. $C=\begin{pmatrix}1.667&1.333\\1.333&1.667\end{pmatrix}$, with eigenvalues 3.0 and 0.333 and directions $(1,1)/\sqrt2$ and $(1,-1)/\sqrt2$. The first component carries $3/3.333=90\%$ of the variance.

**The plan we did not build.** [FINAL_PLAN](../../../plans/FINAL_PLAN.md) section 4.3 planned a dense retrieval view: TF-IDF per view, SVD to 256 dimensions fitted on a 2M-record sample, L2-normalised, then exact GPU top-$k$ over fp16 tiles in both directions. Gate G2 would first measure its recall against exact sparse search on 100k entities. The gate was dropped because the GPU views were not needed ([ROADMAP](../../../docs/ROADMAP.md)).

**Why the gate mattered.** SVD keeps directions of large variance, and the words that identify a business are rare, so they carry little variance. A toy shows the risk. On the six-record corpus of F06 (sqrt-idf vectors), the decoy "lille ecole quai wault" has cosine 0.391 with the S1 "lille ecole rue gutenberg", and the record "paris ecole rue gutenberg" (other city) has 0.563. After a rank-2 SVD those become 0.922 and 0.9998: everything clumps. At rank 4 they are 0.489 and 0.762. In a six-record toy this is exaggerated, and with 256 dimensions for millions of records it would be milder, but the direction is the same: low rank erases the rare-word differences between a copy and its look-alike. We never measured it on real data.

## 7. Low-rank approximation and LoRA

**Idea.** When fine-tuning changes a weight matrix by $\Delta W$ ($d_\text{out}\times d_\text{in}$), that change seems to be simple: fine-tuning has a low intrinsic dimension (Aghajanyan et al. 2021). So write $\Delta W\approx BA$ with $B$ of shape $d_\text{out}\times r$ and $A$ of shape $r\times d_\text{in}$, and train $B$ and $A$ only ([F07](F07-neural-networks-transformers-llms.md), Hu et al. 2022).

**Counts.** Full: $d_\text{out}d_\text{in}$ numbers. LoRA: $r(d_\text{in}+d_\text{out})$. For the query projection of Qwen2.5-7B ($3584\times3584$) with $r=16$: 12,845,056 against 114,688, which is 112 times fewer. Over all seven projections and 28 layers: 40,370,176 numbers, 0.53% of 7.6B. The update $BA$ has rank at most 16, though a full $\Delta W$ could have rank 3584.

**Link to SVD.** Eckart-Young says that for a given $\Delta W$ the best rank-$r$ approximation is its truncated SVD. LoRA never forms $\Delta W$. It learns $B$ and $A$ directly by gradient descent, so it needs no full-size update at any time. Starting with $B=0$ makes the first update zero.

## 8. Gradients and the chain rule

**Intuition.** The gradient is the arrow pointing uphill on the loss surface. To lower the loss, step the other way.

**Definition.** For $L(w_1,\dots,w_n)$ the **gradient** is $\nabla L=(\partial L/\partial w_1,\dots,\partial L/\partial w_n)$. The **chain rule** gives $\partial L/\partial w=\partial L/\partial z\cdot\partial z/\partial w$ for $L(z(w))$. Backpropagation is the chain rule applied from the loss backward through the layers, reusing partial results (reverse-mode automatic differentiation).

**Worked example: logistic regression.** $z=w\cdot x+b$, $p=\sigma(z)$, $L=-[y\ln p+(1-y)\ln(1-p)]$. The sigmoid and the log cancel neatly: $\partial L/\partial z=p-y$, so $\nabla_wL=(p-y)\,x$. Take $x=(1,2)$, $w=(0.3,-0.1)$, $b=0.2$, $y=1$: $z=0.3$, $p=0.5744$, $\nabla_wL=-0.4256\,(1,2)=(-0.4256,\,-0.8511)$. A finite-difference check on the first weight gives $-0.42556$. The quantity $g=p-y$ is the same one XGBoost uses ([F05](F05-trees-and-ensembles.md)), but taken with respect to the margin instead of the weights.

## 9. Convexity

**Definition.** A function is **convex** if the line between any two points on its graph lies above the graph. For a twice-differentiable function, that means a non-negative second derivative (the hessian is positive semi-definite in many dimensions). A convex function has no bad local minima: any local minimum is global (Boyd and Vandenberghe 2004).

**Examples.** The logistic loss as a function of the margin $z$ has second derivative $p(1-p)\ge0$, so it is convex; logistic regression is therefore a convex problem. Neural-network losses are not convex in the weights (many minima and saddle points), yet gradient descent works well in practice. In boosting, the problem for one leaf is a convex quadratic in the leaf value, since $h=p(1-p)\ge0$, so the closed-form leaf weight is its exact minimiser (section 11).

**Curvature decides the step.** For a quadratic loss $f(w)=\tfrac12 w^\top Hw$, the eigenvalues of $H$ are the curvatures along the eigenvector directions. Gradient descent shrinks the error along direction $i$ by $1-\eta\lambda_i$ per step. It is stable only if $\eta<2/\lambda_{\max}$, and the slowest direction is the flattest one, so the number of steps grows with the **condition number** $\kappa=\lambda_{\max}/\lambda_{\min}$. Worked example: $f=\tfrac12(w_1^2+100\,w_2^2)$, so $\kappa=100$, start at $(1,1)$. The best fixed step $\eta=2/101$ shrinks the error by 0.98 per step on both axes, and counting gives 231 steps until both coordinates are below 0.01. A step of 0.021, just above $2/\lambda_{\max}=0.02$, diverges ($w_2$ reached 304 after 60 steps). Momentum with tuned settings needed 45 steps. So long thin valleys are slow, and momentum and Adam's per-weight scaling help. The Newton step of section 11 goes further: it divides by the curvature.

## 10. SGD, momentum, Adam, schedules, clipping

**Update rules.** With gradient $g_t$ on a mini-batch, learning rate $\eta$:

- **SGD**: $w\leftarrow w-\eta g_t$.
- **Momentum**: $v\leftarrow\beta v+g_t$, $w\leftarrow w-\eta v$. Past gradients smooth the path, which helps in narrow valleys.
- **Adam** (Kingma and Ba 2015): $m\leftarrow\beta_1m+(1-\beta_1)g$, $s\leftarrow\beta_2s+(1-\beta_2)g^2$, then $\hat m=m/(1-\beta_1^t)$, $\hat s=s/(1-\beta_2^t)$ and $w\leftarrow w-\eta\,\hat m/(\sqrt{\hat s}+\varepsilon)$. Each weight gets its own scale. Typical $\beta_1=0.9$, $\beta_2=0.999$.
- **AdamW** (Loshchilov and Hutter 2019): weight decay is applied to the weights directly, separate from the gradient scaling.

**Worked example.** Minimise $f(w)=w^2$ from $w=1$ with $\eta=0.1$ (gradient $2w$), four steps:

| step | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| SGD | 1 | 0.800 | 0.640 | 0.512 | 0.410 |
| momentum 0.9 | 1 | 0.800 | 0.460 | 0.062 | -0.309 |
| Adam | 1 | 0.900 | 0.800 | 0.702 | 0.604 |

Momentum builds speed and overshoots zero. Adam's first steps are almost exactly $\eta$ whatever the gradient: its step is the gradient divided by a running gradient size. Replacing $f$ by $100\,w^2$ gives the same Adam path to seven digits, while SGD would behave very differently.

**Warm-up and decay.** At the start, Adam's running averages are poor estimates and the head is random, so large steps can damage pre-trained weights. Warm-up raises the rate from near zero over the first few percent of steps. Decay lowers it to zero at the end: big steps explore, small steps settle. Our code multiplies the base rate by $\min(1,\,(k+1)/\text{warm})\cdot\max(0,\,(N-k)/N)$ at step $k$ of $N$ ([ce.py](../../../experiments/ameya/model-v1/ce.py), [llm_group.py](../../../experiments/bakshi/box/llm_group.py)). For $N=1000$ and 5% warm-up ($\text{warm}=50$), the multiplier is 0.02 at step 0, 0.507 at step 25, 0.951 at step 49, 0.5 at step 500, 0.1 at step 900 and 0.001 at step 999. The peak is 0.951, not 1, because decay starts at step 0.

**Our settings.** The e5 script ([ce.py](../../../experiments/ameya/model-v1/ce.py)): AdamW, rate 5e-5, weight decay 0.01, 5% warm-up, batch 128, one epoch. The Qwen LoRA script (defaults of `llm_group.py`): AdamW, rate 1e-4, weight decay 0, 3% warm-up, batch 64. LoRA tolerates a higher rate because it trains only a small update, which starts at zero.

**Gradient clipping.** If $\lVert g\rVert>c$, rescale: $g\leftarrow g\cdot\min(1,c/\lVert g\rVert)$. With $c=1$ and $g=(3,4)$ (norm 5) we get $(0.6,0.8)$. Our scripts clip at 1 and also skip any step whose gradient norm is not finite, since one such step turned every weight into NaN with torch 2.11.

## 11. Why XGBoost uses second-order information

**Newton's method.** To minimise $f$, a first-order step moves by $-\eta f'$. A second-order step models $f$ locally as a parabola and jumps to its bottom: $-f'/f''$. For a true parabola it lands exactly in one step.

**In a leaf.** The loss change from adding a constant $\Delta$ to every pair in a leaf is approximately $G\Delta+\tfrac12(H+\lambda)\Delta^2$, with $G=\sum g_i$ and $H=\sum h_i$. This parabola is minimised at $\Delta^\star=-G/(H+\lambda)$. That is the XGBoost leaf weight ([F05](F05-trees-and-ensembles.md)).

**Worked example.** A leaf of pairs that all sit at $p_0$, of which a share $\pi$ are true matches. The exact best shift in the margin is $\text{logit}(\pi)-\text{logit}(p_0)$. Newton gives $(\pi-p_0)/(p_0(1-p_0))$ (with $\lambda=0$). A gradient-only step with rate 1 gives $\pi-p_0$.

| $p_0$ | $\pi$ | exact | Newton | gradient only |
|---|---|---|---|---|
| 0.5 | 0.8 | 1.386 | 1.200 | 0.300 |
| 0.9 | 0.99 | 2.398 | 1.000 | 0.090 |
| 0.01 | 0.05 | 1.651 | 4.040 | 0.040 |
| 0.001 | 0.01 | 2.312 | 9.009 | 0.009 |

Where the model is unsure (top row) Newton is close. Where it is confident (small $p_0(1-p_0)$), the raw gradient is tiny and misleading, roughly 25 to 250 times too small. Newton rescales by the curvature, but far from the optimum it can overshoot (4.04 against 1.65), which is why XGBoost adds $\lambda$, a learning rate $\eta$ and a `min_child_weight` floor on $H$.

Friedman's original TreeBoost for the logistic loss already used a one-step Newton approximation for leaf values (Friedman 2001). XGBoost uses the second-order terms consistently, in the split gain and the leaf values, with an explicit penalty (Chen and Guestrin 2016). The hessian $h=p(1-p)$ also acts as a confidence weight: certain pairs ($p$ near 0 or 1) count little in `min_child_weight`.

---

## How it shows up in our project

- Cosine retrieval: [search.py](../../../code/business_entity_resolution/src/ber/block/search.py), [index.py](../../../code/business_entity_resolution/src/ber/block/index.py) (CSR arrays).
- Optimisers and schedules: [ce.py](../../../experiments/ameya/model-v1/ce.py), [llm_group.py](../../../experiments/bakshi/box/llm_group.py). LoRA: [ce_llm.py](../../../experiments/sachi/ce_llm.py).
- Second-order boosting: [s1.py](../../../experiments/ameya/model-v1/s1.py) and the other stages. The SVD view: [FINAL_PLAN](../../../plans/FINAL_PLAN.md), gate G2.

## How to read the numbers

- **Singular values.** The fraction of "energy" kept at rank $k$ is $\sum_{i\le k}\sigma_i^2/\sum\sigma_i^2$. In the dental/pizza toy, rank 2 keeps $(2.618+2.618)/(2.618+2.618+0.382+0.382)=87\%$.
- **Cosines near 1** say two vectors point the same way, not that two records are the same business. After compression the cosines of copies and look-alikes both move towards 1.
- **LoRA's 0.53%** counts trainable numbers, not the information the update can carry.
- **Learning-rate numbers** (5e-5, 1e-4) are per-step sizes under Adam. Adam's step is about the rate itself, so the rate is directly interpretable as a typical weight change per step.

## Common misconceptions

1. "Cosine similarity is a distance." It is a similarity; for unit vectors it is monotone in distance.
2. "SVD and PCA are different things." PCA is SVD of centred data.
3. "Low rank means low quality." It means fewer degrees of freedom, which can be enough (LoRA), or not (rare-word identity).
4. "Gradient descent finds the global minimum." Only for convex problems.
5. "Adam makes the learning rate unimportant." It makes the scale of gradients unimportant, not the rate.
6. "Warm-up is superstition." It protects pre-trained weights while Adam's averages settle.
7. "Second-order means slower trees." The hessian is a per-row number computed with the gradient; the cost is small.

## Check yourself

Exercise 1. Cosine of $(3,4)$ and $(4,3)$?

<details><summary>Answer</summary>

Dot $=24$, norms $5$ and $5$: $24/25=0.96$.

</details>

Exercise 2. Compute $AB$ for $A=\begin{pmatrix}1&2\\3&4\end{pmatrix}$ and $B=\begin{pmatrix}0&1\\1&0\end{pmatrix}$. What does $B$ do?

<details><summary>Answer</summary>

$AB=\begin{pmatrix}2&1\\4&3\end{pmatrix}$. $B$ swaps the columns of $A$.

</details>

Exercise 3. 1M records, 2M-word vocabulary, 10 words per record. Dense float32 versus sparse (8 bytes per non-zero).

<details><summary>Answer</summary>

Dense: $10^6\times2\times10^6\times4=8\times10^{12}$ bytes, 8 TB. Sparse: $10^7\times8=80$ MB.

</details>

Exercise 4. Find the eigenvalues and eigenvectors of $\begin{pmatrix}4&1\\2&3\end{pmatrix}$.

<details><summary>Answer</summary>

Trace 7, determinant 10: $\lambda^2-7\lambda+10=0$, so $\lambda=5,2$. For 5: $(1,1)$ since $A(1,1)=(5,5)$. For 2: $(1,-2)$ since $A(1,-2)=(2,-4)$.

</details>

Exercise 5. Singular values are $5,3,1$. Squared error of the best rank-2 approximation? Share of energy kept?

<details><summary>Answer</summary>

Error $=1^2=1$. Energy kept $=(25+9)/(25+9+1)=34/35=97.1\%$.

</details>

Exercise 6. Centred data have covariance eigenvalues $3.0$ and $0.333$. What share does the first component explain?

<details><summary>Answer</summary>

$3.0/3.333=90\%$.

</details>

Exercise 7. LoRA with $r=8$ on a $4096\times11008$ matrix: trainable numbers and the saving?

<details><summary>Answer</summary>

$8\times(4096+11008)=120{,}832$. Full: $4096\times11008=45{,}088{,}768$. About 373 times fewer.

</details>

Exercise 8. Logistic regression with $x=(1,-1)$, $w=0$, $b=0$, $y=1$. What is the gradient with respect to $w$?

<details><summary>Answer</summary>

$z=0$, $p=0.5$. $\nabla_wL=(p-y)x=-0.5\times(1,-1)=(-0.5,\,0.5)$.

</details>

Exercise 9. Adam's first step with gradient 10, and with gradient 0.001?

<details><summary>Answer</summary>

At step 1, $\hat m=g$ and $\hat s=g^2$, so the step is $\eta\,g/(|g|+\varepsilon)\approx\eta$ in both cases (for $\varepsilon=10^{-8}$, the second is $\eta\times0.99999$). Adam normalises away the scale of the gradient.

</details>

Exercise 10. Schedule with $N=2000$ steps and 3% warm-up. Multiplier at steps 29, 59 and 1000?

<details><summary>Answer</summary>

warm $=60$. Step 29: $\min(1,30/60)\times(2000-29)/2000=0.5\times0.9855=0.493$. Step 59: $1\times(1941/2000)=0.9705$. Step 1000: $1\times0.5=0.5$.

</details>

Exercise 11. A leaf has $p_0=0.5$ and a true match share of 0.8. What do the exact, Newton and gradient-only shifts say, and why is the gradient-only one too small?

<details><summary>Answer</summary>

Exact $\text{logit}(0.8)-0=1.386$. Newton: $0.3/0.25=1.2$. Gradient only: $0.3$. The gradient is in probability units. Near $p=0.5$ one unit of margin moves the probability by only $h=0.25$, so closing a probability gap of 0.3 takes a margin step of about $0.3/0.25$. Dividing by $h$ converts a probability error into a margin step.

</details>

## Going deeper

- Strang. Introduction to Linear Algebra. Trefethen and Bau (1997). Numerical Linear Algebra.
- Eckart and Young (1936). The approximation of one matrix by another of lower rank.
- Deerwester et al. (1990). Indexing by latent semantic analysis. Halko, Martinsson and Tropp (2011). Finding structure with randomness.
- Boyd and Vandenberghe (2004). Convex Optimization.
- Kingma and Ba (2015). Adam: a method for stochastic optimization. Loshchilov and Hutter (2019). Decoupled weight decay regularization.
- Goyal et al. (2017). Accurate, large minibatch SGD: training ImageNet in 1 hour (warm-up).
- Hu et al. (2022). LoRA. Aghajanyan, Zettlemoyer and Gupta (2021). Intrinsic dimensionality explains the effectiveness of language model fine-tuning.
- Friedman (2001). Greedy function approximation: a gradient boosting machine. Chen and Guestrin (2016). XGBoost.
- Goodfellow, Bengio and Courville (2016). Deep Learning, chapters 2, 4 and 8.

## Where next

- [F14 information theory and losses](F14-information-theory-and-losses.md): the losses whose gradients we used.
- [F07](F07-neural-networks-transformers-llms.md): attention and LoRA in use.
- [F11 decision theory and optimisation](F11-decision-theory-and-optimisation.md): optimising a decision rather than a loss.
- [02 blocking](../02-blocking.md) and [06 gradient boosting and stacking](../06-gradient-boosting-and-stacking.md).
