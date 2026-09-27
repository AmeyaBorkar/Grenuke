# Documentation section: Bakshi's components in the final model (`mixf2`)

Ready to paste into the final documentation. Every number is measured on the shared US/India holdout
(`ber.eval`) unless marked otherwise.

## A. France self-trained 7B cross-encoder (`q7st`)

- **Model:** Qwen/Qwen2.5-7B, Apache-2.0, 7.6B parameters (within the ≤ 8B, MIT/Apache-2.0 rule).
  - Fine-tuned with LoRA (r 16, α 32, dropout 0.05, all attention and MLP projections) plus a 1-logit sequence-classification head.
  - bf16, one epoch, lr 1e-4, batch 64, max 96 tokens.
- **Input text:** `name ; address` of each side, with " || " before the record side (the `ce_llm_st.py` recipe, unchanged).
- **Training rows:** the stage-1 uncertainty band (p1 in [0.02, 0.99]). For each of the 3 OOF groups:
  - a 50% sample of the labelled US/India rows of the other groups;
  - plus French test band pairs pseudo-labelled from the best leaderboard model's final decisions (v7sq-dpc, `pseudo_labels.py`: y = 1 if predicted with pc ≥ 0.9 or rule-added; y = 0 if not predicted with pc ≤ 0.05; the rest unlabelled).
  - The pseudo-labels are cross-fitted by S1 group, so no French pair is scored by a model that saw its own label.
- **Implementation:** `experiments/bakshi/box/llm_group.py` runs each OOF group on its own GPU, with the same rows and seeds as the sequential script. Checkpoints every ~10 min make it resumable. `llm_merge.py` assembles the parts.
- **Compute:** 3x H100 80 GB, about 2 h per group, including scoring 2.0M pairs per group.
- **Quality:** band AUC holdout 0.9436, OOF 0.9396. For comparison: e5-large self-trained 0.9439, Qwen2.5-1.5B 0.9381.

## B. Stage-2 use: India from `g1w`

- **Mix:** the stage-2 cross-encoder feature is the mean of z-scored logits (`zmean_ce.py`) of e5l, qst, e5ls, bge and q7st, with **q7st counted twice** (2 of 6 votes).
- **Holdout macro F0.5:** 0.991323, against 0.991261 for the same pipeline without the 7B (+0.000062).
  - Weighting ablation: 1 vote +0.000015, 2 votes +0.000062, 3 votes +0.000061, 7B alone +0.000025.
  - Ameya's paired bootstrap: India +66.1e-6, P 0.998. This is why `mixf2` takes India from g1w.
- **Rebuild:** our independent rebuild of the pipeline reproduces the v7sq model to holdout 0.991261 (original 0.991246), with 99.9999% band coverage. Cross-encoder logits move between machines only by (s1, r) (`remap_ce.py`, coverage gate 99.5%).

## C. The 7B drop rule (applied to all countries in `mixf2`)

- **Why:** 94.5% of final predictions have p1 > 0.99, so no cross-encoder ever scores them. The 7B is used as an independent reader of those pairs (`score_pairs.py`, adapter of group 0).
- **Rule:** drop a predicted pair outside the band when its 7B logit < −6.
- **Labelled check** (`rescore_eval.py`, 186,897 holdout S1 that no adapter trained on):
  - that bucket is 8% true;
  - +0.000033 macro F0.5, positive in both fixed halves (+0.000022 / +0.000043);
  - lower cut-offs turn negative (−4: +0.000012, −2: −0.000055, 0: −0.0032), so −6 is kept.
- **Size on test:** 859 French predictions (0.10% of French predictions, 25× the US/India rate) and 310 US/India.
- **What it catches in France** (Ameya's analysis on #62/#64): mostly decoys with a generic name and the same house number on a different street.
  - On the labelled holdout, such decoys are 0.5% true and the 7B scores them around −9.9.
  - Real copies with the same pattern score around +7.9.
  - In France, generic names (a median of 43 same-name S1) let these decoys through stage 1 at p1 > 0.99.
- **Bias check:** adapter 0 saw French pseudo-labels of S1 thirds 1–2 (band pairs only), yet the drop rate is the same in all three thirds (0.112% / 0.108% / 0.107%, median logit 9.6 in each). There is no leakage effect.

## D. Checked and not used (so the documentation can say why)

- **US/India recall rules** for empty-address name variants: the unassigned slice is 17–24% true, against a ~75% break-even.
- **Empty-S1 rescue:** negative at every threshold.
- **7B additions** (recall): best holdout precision 71%.
- **Qwen3-4B** (Apache-2.0, 4.0B): trained and merged, but not in the final model (no time for a variant).
- **Details:** `FINAL_PUSH_RESULTS.md` §6.
