# The Qwen2.5-7B model and the re-check (LLM)

**Summary.**
- We fine-tuned Qwen2.5-7B with LoRA as a pair classifier (`q7st`). It ties a self-trained e5-large on the uncertain band (AUC 0.9436 against 0.9439), so it enters the stage-2 mix twice for diversity.
- Its second job is a re-check of confident predictions that no encoder had read (p1 above 0.99): drop a pair when the 7B logit is below −6. Composite B dropped 840 French and 310 US/India pairs, about +37e-6 on the holdout and roughly +0.0001 of the +0.00018 over mixmdp (an estimate).
- Path key: `box/` = `experiments/bakshi/box/`, `mv1/` = `experiments/ameya/model-v1/`, `sachi/` = `experiments/sachi/`. Bakshi built the 7B chain; Ameya's agent rebuilt its decisions and ran the gates. Levels as in [STANDARD §3](../STANDARD.md).

## 1. Purpose

Catch confident mistakes. 94.5% of final predictions have p1 above 0.99 and were never read by a cross-encoder; the errors left there are decoys that look like copies. A strong reader, run only on those predictions, removes the ones it firmly rejects.

## 2. How it works

**Training** (`box/llm_group.py`, which reproduces `mv1/ce_llm_st.py` group by group; the model is built in `sachi/ce_llm.py`)
- Model `Qwen/Qwen2.5-7B` at revision `d149729398750b98c0af14eb82c78cfe92750796` (`box/compositeB.sh:50, 83-85`), `AutoModelForSequenceClassification(num_labels=1, torch_dtype=bfloat16)`, pad token set (`sachi/ce_llm.py:57-59`).
- **LoRA r = 16, alpha = 32, dropout 0.05, task SEQ_CLS, targets q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj** (`:60-62`); trainable weights in fp32 (`:63-65`). The score head is trained and saved with the adapter by PEFT's SEQ_CLS behaviour.
- AdamW lr 1e-4, weight decay 0; linear warm-up over 3% of steps, then linear decay; batch 64; 1 epoch; bf16 autocast; BCE on the logit; gradient-norm clip 1.0; non-finite-gradient guard (`box/llm_group.py:129-173`, defaults `:62-73`).
- Input as for the other encoders ([cross-encoders.md](cross-encoders.md)): name ; address, record side prefixed with `" || "`, max 96 tokens, median 37. Batches: rows sorted by length, cut into chunks of 64, chunk order shuffled (`sachi/ce_llm.py:37-43`). Inference batch 512.
- Rows for group g: a 50% sample (`--us-in-frac 0.5`) of the labelled band rows of the other two OOF groups plus the French pseudo-labelled pairs (y ≥ 0) of the other two thirds (`box/llm_group.py:102-111, 232-233`). The random draws of earlier groups are replayed, so three parallel processes use exactly the rows of the sequential script. As run: 392,391 / 394,567 / 391,928 labelled plus 226,027 / 226,562 / 242,381 pseudo rows; 9,663 / 9,706 / 9,912 steps; 0 non-finite steps [M].
- Crash safety: a checkpoint every 600 s (weights, optimiser, scheduler, step, CPU and CUDA RNG), written atomically, so a rerun resumes at the same step (`:119-186, 193, 234-269`). `llm_merge.py` refuses parts with different configs and any non-finite logit.
- Output: out-of-fold band logits (holdout = mean of the 3 adapters; French test pairs from the adapter of their third) feed the `zg1w` mix, counted twice; and `adapter_{0,1,2}` of 161,547,632 bytes each [R]. Labels: round 2, from v7sq-dpc (385,274 French band pairs: 74,325 positive, 273,160 negative, 37,789 unlabelled) [M].

**What is re-checked** (`box/compositeB.sh:145-172`)
- **France:** every French final prediction of v7sq-dpcsf (as run 870,019 pairs), with p1 and pc (`box/rescore_export.py:36-42, 55-60`).
- **US/India:** g1w-dpc predictions with **p1 > 0.99**, 4,744,395 pairs (`box/analysis/export_usin.py:37-44`).
- **Holdout check** (`CHECK_7B=1`): a 34% random sample of holdout S1 (seed 7), 186,897 S1 and 631,001 predictions at precision 0.99896 (`rescore_export.py:50, 62-76`) [M].
- The scorer is `score_pairs.py` with **`adapter_0` only**, batch 512, 96 tokens, separator `" || "` (`:28-31, 54-59`).

**The rule.** Drop a final predicted pair if `q7__logit < −6` and `p1 > 0.99` (`box/compose_tsv.py:62`; `--drop-logit -6` at `box/compositeB.sh:192`). Drops remove ids from matching rows only; candidates stay unchanged.

**Choosing −6** (`box/rescore_eval.py`): thresholds {−8, −6, −5, −4, −3, −2, −1, 0}, out-of-band pairs only, with fixed halves by (s1 // 7) % 2 (`:42, 57-63`). On the 34% sample, −6 drops 24 pairs, 2 of them true (8.3%): +33e-6 (halves +22e-6 and +43e-6); −5 +26e-6; −4 +12e-6 with a negative half; −3 and looser lose. On the whole holdout: −6 +37e-6 (halves +33 / +41; US +18, India +18), −7 +27e-6, −5 +29e-6, −4 +17e-6, −3 +3e-6 [M]. Positive in 99.7% of 3,000 random 25% subsets (mean +32.8e-6, sd 16.7e-6) (`box/analysis/resample_drop.py`). −6 is the cut-off with the largest gain, not "the loosest that gains in both halves" (−5 also does) ([D-PKG-20]).

**Leakage reasoning.** `adapter_0` trained on labelled groups 1–2 (folds 10–19) and on the French pseudo-labels of thirds 1–2, band pairs only. It never saw holdout S1, and every re-checked pair is out of band (p1 > 0.99), so no re-checked pair's own label was in training. The French reject rate per third is 0.112% (the third it never saw), 0.108% and 0.107%, median logit 9.6 in each (`box/analysis/leak_by_third.py`) [M].

**Runtime.** q7st about 2 h on three 80 GB H100 (about 6 h on one); 3.6 steps/s on the first box, 2.3 on the second after a pre-emption; scoring about 600 pairs/s per GPU alone, 430–480 shared. Re-check: France 2 × 15 min, US/India 4 × 46 min, holdout 23 min on H100s, about 4 GPU-hours in all [R].

## 3. Why this design

- A big LLM judge was dismissed as "not worth it in 40 hours" ([D-LLM-01], reversed by events). Zero-shot and quickly tuned 7B-Instruct failed first ([D-LLM-02], [D-LLM-03]).
- **Train it properly instead of prompting it:** [D-LLM-04] (Bakshi's plan; [D-CE-19], [D-CE-21], [D-CE-22]).
- **The re-check:** [D-LLM-05]. The threshold −6 was fixed on labelled holdout S1 no adapter trained on, before any French use. Under F0.5 a drop pays whenever more than about 25% of the dropped pairs are false.
- **Gate on the 7B, not on the pattern:** [D-LLM-06]. The pattern "same name, same house number, different street" is both a copy pattern and a decoy pattern; only the 7B separates them.
- **Same drop in US/India:** [D-LLM-07]. The gain is measured exactly where it is applied.
- **Counted twice in the mix:** [D-LLM-09], [D-CE-23].
- **Composed with a pre-set rule:** Composite B was uploaded first as a controlled probe ([D-SUB-23]).

## 4. Alternatives and why not

- **7B-driven additions:** best holdout precision 71%, below the roughly 75% an F0.5 addition needs (at logit above 4: 69 adds, 49 true; above 5: 42 adds, 30 true) ([D-LLM-08]).
- **Three-adapter ensemble and an in-band drop:** the union gained +0.000038 against +0.000033 but its 88 extra French drops included garbled real copies ("ehpad de troisieme" against "chpad de troisieme"); adapters correlate only 0.403; three in-band drops gave +0.000002 with halves disagreeing ([D-LLM-10]).
- **Drops mined from a decision tree:** half A +33e-6, held-out half B −15e-6 (overfit) [M].
- **Blends of the logits as a decision score:** −0.001 even at band AUC 0.9575 [M].
- **Pattern-only drop:** on US/India the same pattern is 99.7% true when our model keeps the pair ([D-LLM-06]).
- **Extending the French drop toward −2 with Qwen3-4B (B7):** a tie on the public LB, 0.990875 against 0.990879 ([D-SUB-26]).
- **Scoring every pair:** about 27 GPU-hours for 58.4M test pairs at 600 pairs/s, before any training [E].

## 5. Numbers

| fact | value | scope | level |
|---|---|---|---|
| Band AUC of q7st | 0.9436 holdout, 0.9396 out of fold; e5ls 0.9439, qst 0.9381, p1 0.9297 | holdout band | M |
| Drops in Composite B | list 1,169; 1,150 present and dropped: **840 France, 310 US/India** (India 204, US 106) | test | M |
| Flagged on test | 859 French pairs (0.10% of French predictions); 310 of 4.74M US/India (0.0065%); holdout US/India rate 0.004%, so 15× (test) to 25× (holdout) | test; holdout | M |
| Truth by 7B logit, 34% sample | below −6: 8.3% of 24; −6 to −4: 86.3% of 51; −4 to −2: 94.9% of 138; −2 to 0: 99.6% of 6,616; 0 to 2: 99.8% of 16,893; 2 or more: 100.0% of 579,440 | holdout, out of band | M |
| Truth of the strong rejects | **8.3% (2 of 24)** on the 34% sample; **20% (16 of 80)** on the whole holdout. Both far below the 75% at which a drop stops paying | holdout | M |
| Gain at −6 | sample +33e-6; whole holdout **+37e-6** | holdout | M |
| Decoy pattern | model kept it: 99.7% true (n = 380, 7B median +7.9, none below −6); model rejected it: 0.5% true (n = 218, median −9.9, 202 below −6) | holdout sample | M |
| French rejects | about 78% follow the pattern (80.1% of 859); 747 of 859 S1 have generic names; 827 S1 affected, 68 would be emptied; a median of 43 same-name S1 per rejected pair | test France | M |
| bge detector, no self-training labels | flags 708 of the 859 (82%) | test France | M |
| Share of Composite B's +0.000180 over mixmdp | French drops about +111e-6 (remainder), US/India drops about +28e-6, g1w US/India about +41e-6; the record says about +0.00014 for the drops ([CF-30]) | public LB split by holdout deltas | E |

**Why generic names make France special.** French names are generic, so decoys (another business with the same name and number at a different street) pass stage 1 above 0.99. String features tell decoys apart in US/India; in France they fail because the names are generic ([D-PKG-20]). The 7B reads both records and sees the street differ.

**8.3% against 20%.** The methodology quotes 8% (2 of 24 on a 34% sample). The whole holdout gives 20% (16 of 80). Both are far below break-even; say "20% on the whole holdout, 8% on the sample" ([CF-19]).

## 6. Failure modes and limits

- **One adapter decides.** `adapter_0` makes every re-check decision. The three adapters correlate only 0.403 on holdout pairs. For French S1 of thirds 1–2 it had trained on pseudo-labels of other (band) pairs of the same S1; the per-third reject rates show no effect ([CF-21]).
- **Cut-off and list built on neighbours.** −6 was chosen on v7sq/g0 holdout predictions and applied to g1w's US/India and the France block. The French list was built from v7sq-dpcsf; 19 of 859 pairs are absent from mixmdp, and predictions unique to mixmdp were never re-checked ([CF-28]).
- **A tiny sample.** 24 pairs, 2 true; the whole-holdout figure (80 pairs) is the better guide. The French gain is an estimate with no French truth [E].
- **Real copies can look like decoys.** "thompson and davidson llc" against "inc", garbled copies of "ehpad"; the single −6 cut keeps these losses small, and looser cuts lose.
- **Compute.** The 7B needs an 80 GB card to train and about 4 GPU-hours to re-check.
- **Doc fix.** The 7B ties e5-large; the methodology says no more accurate ([CF-35]). `rescore_eval.py`'s docstring says "fold-parity halves"; the code uses (s1 // 7) % 2 ([CF-38]).

## 7. Scale

Scoring is linear in the pairs read. Reading all 58.4M test pairs would cost about 27 GPU-hours; the re-check reads about 5.6M predictions (870k French, 4.74M US/India), about 4 GPU-hours [R/E]. At 100× the data that is about 400 GPU-hours and at 1000× about 170 GPU-days, so the design choice scales if the re-check is narrowed (for example to predictions with generic names, which hold 747 of 859 French rejects) or the 7B is distilled into a smaller model. These are projections, not tests. Training is one group per GPU, resumable, with 161 MB adapters. See [theory 10](../theory/10-llm-verification-and-compute.md).

## 8. Theory links

[10 LLM verification and compute](../theory/10-llm-verification-and-compute.md), [08 transformers and cross-encoders](../theory/08-transformers-and-cross-encoders.md), [04 metrics and decisions](../theory/04-metrics-and-decisions.md), [11 scaling to billions](../theory/11-scaling-to-billions.md), foundations [F07](../theory/foundations/F07-neural-networks-transformers-llms.md), [F08](../theory/foundations/F08-computing-at-scale.md). Neighbours: [cross-encoders.md](cross-encoders.md), [submission-strategy.md](submission-strategy.md).

## 9. Likely questions

- **Why does a re-check help when the model is 99.9% precise there?** Precision is 0.99896 on the sample, so almost every prediction is right; the re-check targets the rare confident decoys, where a drop pays above about 25% false. The measured gain is +37e-6.
- **Why logit −6?** It has the largest gain on the whole holdout and is positive in both halves; −5 gains less, −4 has a negative half, −3 and looser lose.
- **How often are the rejects real copies?** 20% on the whole holdout (16 of 80), 8% on the 34% sample. Break-even is about 75% true.
- **Why France more than US/India?** Generic French names create decoys that pass stage 1; the rate is 0.10% against 0.0065% on test.
- **Is there leakage?** The adapter never saw holdout S1, re-checked pairs are out of band, and the reject rate is the same on all thirds.
- **Is the 7B better than e5-large?** No, they tie at about 0.944. It adds diversity and an independent reading of confident pairs.
- **Could you run it on every pair?** About 27 GPU-hours at 600 pairs/s; we did not measure it.
- **Which licence?** Apache-2.0, 7.6B parameters, within the 8B cap.

[CF-19]: ../conflicts.md
[CF-21]: ../conflicts.md
[CF-28]: ../conflicts.md
[CF-30]: ../conflicts.md
[CF-35]: ../conflicts.md
[CF-38]: ../conflicts.md
[D-CE-19]: ../decisions/CE.md
[D-CE-21]: ../decisions/CE.md
[D-CE-22]: ../decisions/CE.md
[D-CE-23]: ../decisions/CE.md
[D-LLM-01]: ../decisions/LLM.md
[D-LLM-02]: ../decisions/LLM.md
[D-LLM-03]: ../decisions/LLM.md
[D-LLM-04]: ../decisions/LLM.md
[D-LLM-05]: ../decisions/LLM.md
[D-LLM-06]: ../decisions/LLM.md
[D-LLM-07]: ../decisions/LLM.md
[D-LLM-08]: ../decisions/LLM.md
[D-LLM-09]: ../decisions/LLM.md
[D-LLM-10]: ../decisions/LLM.md
[D-PKG-20]: ../decisions/PKG.md
[D-SUB-23]: ../decisions/SUB.md
[D-SUB-26]: ../decisions/SUB.md
