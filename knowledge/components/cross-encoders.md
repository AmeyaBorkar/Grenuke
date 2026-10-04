# Cross-encoders (CE)

**Summary.**
- A cross-encoder is a transformer that reads both records of a pair in one pass and returns one score (a logit). We run it only on the uncertain band, 0.02 ≤ p1 ≤ 0.99: 1,490,930 of 58,437,794 test pairs (about 2.6%) [M].
- Stage 2 receives the cross-encoders as two features: e5-small's own logit and one z-scored mean of the larger models, with the Qwen2.5-7B counted twice. Models are out of fold, MIT or Apache-2.0 and at most 8B parameters.
- Path key: `mv1/` = `experiments/ameya/model-v1/`, `box/` = `experiments/bakshi/box/`, `fpk/` = `experiments/bakshi/final-package/`, `pipe/` = `experiments/ameya/model-v1/pipeline/`. Line numbers are from the submitted package. Evidence levels M, E, R, U as in [STANDARD §3](../STANDARD.md).

## 1. Purpose

Give stage 2 an independent, pair-level reading of exactly the pairs that stage 1 (the first XGBoost classifier, p1) cannot decide. On France, where there are no labels, self-trained cross-encoders are also the main way the model learns the French conventions (see [france.md](france.md)).

## 2. How it works

**The band** (`mv1/ce.py:43-52`, `LO, HI` at `:35`): stage-1 rows with p0 ≥ tau0 and 0.02 ≤ p1 ≤ 0.99. Train 1,568,554 pairs (27.2% positive), test 1,490,930, labelled holdout band 389,668 rows [M]. Every other row gets NaN in the cross-encoder features. Truth rate by p1 on the holdout: below 0.002 it is 0.03–0.06%, at 0.01–0.02 it is 1.4%, at 0.99 and above it is 99.98% [M]. So 94.5% of final predictions have p1 above 0.99 and are never read by an encoder (France 90.5%); the 7B re-check covers those ([llm-recheck.md](llm-recheck.md)).

**Input text** (`mv1/ce.py:55-70`): for each record, name + " ; " + address, each side cut to 300 characters (`:63`). The tokenizer gets the S1 text first and the record text second, `truncation="longest_first"`, `max_length=96` (`:68`). The Qwen variants prepend `" || "` to the record text (`mv1/ce_llm_st.py:43-60`, `:55`) because Qwen's tokenizer joins a text pair with no separator (`:8-9`). The median pair is 37 tokens for the 7B [R] ([MB]).

**Encoder training loop** (`mv1/ce.py:83-123`, reused by `mv1/ce_box.py`):
- `AutoModelForSequenceClassification.from_pretrained(model, num_labels=1)`, full fine-tune, binary cross-entropy on the logit.
- AdamW with weight decay 0.01 (`:96`); linear warm-up over the first 5% of steps, then linear decay to 0 (`:97-98`); bf16 autocast; gradient-norm clip 1.0 (`:110`).
- **Non-finite-gradient guard** (`:111-115`): a step whose gradient norm is not finite is skipped. This is mandatory on torch 2.11 (`fpk/reproduce.sh:45-46`).
- Batches: shuffle, sort by length inside random windows of 50 batches, then shuffle the batch order (`:86-94`). Prediction batch 1024, sorted by length (`:127-135`). TF32 on in `ce_box.py` (`:58`).
- Defaults: `ce.py` lr 5e-5, batch 128, 1 epoch, max_len 96, seed 26 (`:35-40`); `ce_box.py` `--lr 2e-5 --batch 128 --epochs 1 --max-len 96 --seed 26` (`:41-45`).

**Out of fold** (`mv1/ce.py:183-204`, `mv1/ce_box.py:107-148`): three models. Model g trains on band rows of the training folds outside group g and scores only group g. Holdout and test get the mean of the three (`--hold-groups` can restrict the holdout to some groups). A stage 2 trained on logits that had seen their own labels would learn a leak, so every logit it sees is honest.

**Self-training on France** (`ce_box.py --pseudo`, `ce_llm_st.py`, `box/llm_group.py`): the French third of a pair is `fold_of(s1) % 3` (`mv1/ce_box.py:73-78`). Model g trains on the labelled rows plus the pseudo-labelled (y ≥ 0) French rows of the other two thirds. **Each French test pair is scored only by the model of its own third**; other test pairs get the mean of three (`:113-127, 144-147`). `--us-in-frac` subsamples the labelled rows per group (`:111-112`); `--target-only-test` scores only French test rows (`:123-124, 145-146`).

**Models in Composite B** (the final path):

| run | model, licence, size | settings | labels | used in | band AUC holdout / OOF |
|---|---|---|---|---|---|
| `ce` | multilingual-e5-small, MIT, 118M | `ce.py` defaults | none | `ce__logit`, every stage 2 | 0.9240 / 0.9191 [R] |
| `e5l` | multilingual-e5-large, MIT, 560M | lr 2e-5, batch 128, 1 epoch, seed 26 | none | the mix | 0.9391 / 0.9350 [R] |
| `e5b` | multilingual-e5-base, MIT, 278M | lr 3e-5, 1 epoch | none | first teacher v7ce3 only | 0.9287 / 0.9244 [R] |
| `e5ls` | e5-large | lr 2e-5, 2 epochs, seed 7 (`fpk/reproduce.sh:214-216`) | round 1 | the mix | 0.9439 / 0.9403 [R] |
| `bge` | bge-reranker-v2-m3, Apache-2.0, 568M | lr 2e-5, 1 epoch (`:210`) | none | the mix | 0.9417 / 0.9382 [R] |
| `qst` | Qwen2.5-1.5B, Apache-2.0, LoRA r 16 | lr 1e-4, batch 64, 1 epoch, us-in-frac 0.5 (`:217-219`) | round 1 | the mix | 0.9381 / 0.9332 [R] |
| `q7st` | Qwen2.5-7B, Apache-2.0, 7.6B, LoRA r 16 | as qst, infer batch 512 | round 2 | the mix (twice); the re-check | 0.9436 / 0.9396 [M] |
| `e5ls2`, `bges`, `e5fr` | e5-large, bge, e5-large | round-1 labels, seeds 11 / 26 (assumed) / 31 | round 1 | France block mix `cmq7` | 0.9440, 0.9424, about 0.918 by design |

Stage-1 p1 alone scores 0.9297 on the same holdout band [M]. The band is the final one (0.02–0.99); AUCs from the older 0.05–0.95 band (e5-small 0.9244 / 0.9278 against p1 0.9315) must not be mixed with these ([numbers.md](../numbers.md), "Numbers not to quote" 21).

**The mix** (`mv1/zmean_ce.py:11-12`): for each source, z = (logit − mean) / std, with mean and std taken from that source's train band (pandas, NaN-skipping). The mix is the plain mean of the z-scores (NumPy, NaN-propagating). A source listed twice counts twice: `zg1w` = z-mean(e5l, qst, e5ls, bge, q7st, q7st) (`box/compositeB.sh:117-139`), so the 7B has 2 of 6 votes. The v7sq chain uses `cmq` = z-mean(e5l, qst, e5ls, bge). `ce_import.py` writes the mix into the feature table by band `row`; non-band rows stay NaN (`mv1/ce_import.py:35-53`). e5-small is not in the mean: stage 2 gets `ce__logit` and the mix as two features.

**Why one averaged feature.** On France e5-large and bge disagree in sign on 12.0% of band pairs against 3.1% in the US and 2.7% in India, and correlate 0.91 against 0.98 [M]. A stage 2 given separate logits extrapolates on that disagreement (`fpk/reproduce.sh:222-225`).

**Remap across machines** (`box/remap_ce.py`): `row` indexes one machine's feature table, so logits trained against another band are re-keyed by (s1, r); the run aborts below 99.5% coverage (`:45, 79-81`). As run: train 100.0000%, test 99.9999% (1 pair missing) [M].

**Runtime.** e5-small about 40 min on the laptop GPU, 21 min on an RTX 4090; e5-large 61 min and e5-base 37 min on one shared H100; the five encoders of the v7sq chain about 5 h on one H100; e5ls2 about 2.0 h, bges 1.3 h, e5fr 20 min [R]. e5-large at batch 128 and 96 tokens does not fit in 12 GB; batch 32 works at 4–6× the time. Each run resumes per OOF group (checkpoint `.npz`).

## 3. Why this design

- Band only: [D-CE-02] (the band holds 4.74% of positives in 1.56% of pairs at the first cut; one Foursquare team needed 40 h per epoch scoring everything). Started gated and small: [D-CE-01], [D-CE-04].
- Licence screen, MIT or Apache-2.0 and at most 8B: [D-CE-03]. Qwen2.5-3B (other licence) and jina-reranker-v2 (CC-BY-NC) are out.
- Kept although the e5-small gate missed its +0.003 bar: [D-CE-05] (+0.00140 [0.00131, 0.00148]).
- Larger and more diverse models, rented on demand: [D-CE-06], [D-CE-07], [D-CE-08], [D-CE-09].
- One z-scored mean, equal weights: [D-CE-11], [D-CE-14], [D-CE-23]. Averaging two e5-large runs alone failed: [D-CE-10].
- Qwen separator, French self-training and a two-sided gate (AUC ≥ 0.93, correlation with e5l ≤ 0.975): [D-CE-12], [D-CE-15].
- Skip non-finite steps: [D-CE-13]. French self-trained members: [D-CE-16].
- The 7B and its plumbing: [D-CE-19], [D-CE-21], [D-CE-22].

**Why the 7B counts twice.** Two was the smallest weight at the plateau: against g0 the 7B once adds +15e-6, twice +62e-6, three times +61e-6, alone +25e-6 (point estimates, local holdout) [M]. It ties a self-trained e5-large (0.9436 against 0.9439), so its value is diversity, not accuracy ([D-LLM-04], [D-LLM-09]).

**Why not separate features, and why not tuned weights.** The spread of estimated public-LB change across the best 40 weightings was only 0.000048, and "adding bge at all is worth about +0.00026 and that is the whole prize" [E] ([D-CE-14]). bge is the weakest single model on France (rule-population AUC 0.774) yet lifts the mean most, because it is another family.

## 4. Alternatives and why not

- **Score every pair.** e5-large trains at about 925 pairs/s on an H100, so one pass over 58.4M pairs is about 17.5 h; the 7B at 600 pairs/s would need about 27 GPU-hours [E].
- **Weight tuning, extra seeds, French-heavy members** (e5fr, bgefr; gate lowered to AUC 0.90): no measurable gain over v7sq6wg ([D-CE-18]).
- **Synthetic French supervision** (six encoders): the label-free estimator `cal` rose by reverting 1,182–1,576 leaderboard-confirmed moves; US/India holdout −43e-6 ([D-CE-20], [D-FRA-23]).
- **Round-2 self-training of the encoders:** negative for France under every valuation ([D-FRA-22]).
- **Not in B for technical reasons:** mDeBERTa-v3 (5,999 of 6,122 steps non-finite in bf16), gte-multilingual (remote-code crash), Qwen3-4B-Base (AUC 0.9411, merged too late; used only in B7) [R].
- **A zero-shot or quickly tuned LLM judge:** AUC 0.537 and 0.720 against 0.898 for stage 2 ([D-LLM-02], [D-LLM-03]).
- **A logit blend** of six logits plus p1 and pc reaches band AUC 0.9575 but scores −0.001 as a decision score [M].

## 5. Numbers

| fact | value | scope | level |
|---|---|---|---|
| e5-small added to v3 | +0.00140 [0.00131, 0.00148]; singleton F0.5 0.99126 → 0.99742 | local holdout | M |
| e5-large and e5-base added (v7ce3) | stage 2 +0.000311 [0.000258, 0.000362]; with stage 3 +0.000296 | local holdout | M |
| v7n over v7ce3 (z-mean, bge dropped) | +0.000072 [0.000040, 0.000103] | local holdout | M |
| v6all to v7n | +0.001112 (US/India part about +0.00033, so France about +0.005 F0.5) | public LB | M/E |
| French self-training, round 1 (v7nst) | +0.000458, France about +0.0031 | public LB | M/E |
| v7nst-dpc to v7sq-dpc (French self-trained encoders in the mix) | +0.000281, about +0.00023 from France | public LB | M/E |
| g1w over v7sq3 | India +66.1e-6 [+19.4, +112.9], P 0.998; US +26.2e-6, P 0.906, not significant | local holdout | M |
| Self-trained encoders on France | correlate 0.94–0.98 among themselves, 0.60–0.69 with untrained ones | test France band | M |

The methodology's description of the mix and of the 7B is qualified in [CF-35].

## 6. Failure modes and limits

- **Not bit-reproducible** across GPUs (TF32, cuDNN kernel choice) [M].
- **`cmq7` is NaN on every US/India test band row**, because e5fr writes NaN there. The France block's US/India output is invalid by design; only its French rows are used.
- **Self-training absorbs encoder differences.** v7mst moved only 8 French predictions per 1000 S1 against v7nst, so Bakshi's "+0.00026 for adding bge" was probably high [M] ([D-CE-14]).
- **Description gap.** The methodology says the z-scored logits are averaged into one stage-2 feature; e5-small stays a separate feature ([CF-35]).
- **Gate by hand.** Qwen's gate (AUC ≥ 0.93, correlation ≤ 0.975) is a human check in `mv1/RECIPE.md:74`, not code.
- **Docstring.** `ce.py` speaks of a fresh one-logit head; bge-reranker ships one, and the code loads what the checkpoint has.
- **Transformers and exact numbers.** Plan B warned they are weak at house numbers, which is why stage 2 stays a gradient-boosted model and the encoder is only a feature ([D-CE-01]).
- **96 tokens and 300 characters** truncate long records; the median is 37 tokens, so few are cut [R].

## 7. Scale

Cost follows the band, not the pair count. Band pairs were 2.6% of test pairs at about 34 candidates per S1. At 100× the data, if the density holds, the test band is about 149M pairs: the 7B at about 600 pairs/s would take about 69 GPU-hours, at 1000× about 29 GPU-days [E, derived]. Training can subsample (the Qwen runs use 50% of labelled rows). The band edge and the candidate cut are the two levers; a smaller encoder (e5-small infers about 11,654 pairs/s) is the fallback. Inference is parallel by group; the three OOF models already run one per GPU. See [theory 11](../theory/11-scaling-to-billions.md).

## 8. Theory links

[08 transformers and cross-encoders](../theory/08-transformers-and-cross-encoders.md), [10 LLM verification and compute](../theory/10-llm-verification-and-compute.md), [09 self-training and domain shift](../theory/09-self-training-and-domain-shift.md), [06 boosting and stacking](../theory/06-gradient-boosting-and-stacking.md), foundations [F07](../theory/foundations/F07-neural-networks-transformers-llms.md), [F14](../theory/foundations/F14-information-theory-and-losses.md), [F18](../theory/foundations/F18-tuning-ensembles-and-interpretability.md). Neighbouring pages: [llm-recheck.md](llm-recheck.md), [france.md](france.md), [model-stages.md](model-stages.md).

## 9. Likely questions

- **Why only the band?** The band holds the pairs stage 1 is unsure about; 94.5% of final predictions sit above it. Scoring all 58.4M pairs would cost 17–27 GPU-hours per model.
- **Why a cross-encoder, not embeddings?** It reads both records together, so it sees number and word differences an embedding averages away. The price is one pass per pair, which the band makes affordable.
- **How do you avoid leakage into stage 2?** Out of fold: three models, each scores only the group it did not train on. For France, each pair is scored by the model of its own third.
- **Why average z-scores instead of feeding logits?** On France the models disagree four times as often; separate logits make stage 2 extrapolate on that disagreement.
- **Is the 7B better than e5-large?** No. Both score about 0.944. It adds diversity, so we count it twice; the +62e-6 against once is a point estimate.
- **Licences?** MIT (e5), Apache-2.0 (bge, Qwen2.5), all at most 8B; the Qwen2.5-3B was excluded because its licence is not Apache.
- **Did you train on test labels?** No labels exist for test. France self-training uses our own predictions on the provided test records, cross-fitted; one agreed sentence on this is still open ([CF-11]).
- **Could someone rerun it?** Within about ±0.0001; cross-encoders are not bit-identical across GPUs ([packaging.md](packaging.md)).

[CF-11]: ../conflicts.md
[CF-35]: ../conflicts.md
[D-CE-01]: ../decisions/CE.md
[D-CE-02]: ../decisions/CE.md
[D-CE-03]: ../decisions/CE.md
[D-CE-04]: ../decisions/CE.md
[D-CE-05]: ../decisions/CE.md
[D-CE-06]: ../decisions/CE.md
[D-CE-07]: ../decisions/CE.md
[D-CE-08]: ../decisions/CE.md
[D-CE-09]: ../decisions/CE.md
[D-CE-10]: ../decisions/CE.md
[D-CE-11]: ../decisions/CE.md
[D-CE-12]: ../decisions/CE.md
[D-CE-13]: ../decisions/CE.md
[D-CE-14]: ../decisions/CE.md
[D-CE-15]: ../decisions/CE.md
[D-CE-16]: ../decisions/CE.md
[D-CE-18]: ../decisions/CE.md
[D-CE-19]: ../decisions/CE.md
[D-CE-20]: ../decisions/CE.md
[D-CE-21]: ../decisions/CE.md
[D-CE-22]: ../decisions/CE.md
[D-CE-23]: ../decisions/CE.md
[D-FRA-22]: ../decisions/FRA.md
[D-FRA-23]: ../decisions/FRA.md
[D-LLM-02]: ../decisions/LLM.md
[D-LLM-03]: ../decisions/LLM.md
[D-LLM-04]: ../decisions/LLM.md
[D-LLM-09]: ../decisions/LLM.md
[MB]: ../../experiments/bakshi/final-package/METHODOLOGY_bakshi.md
