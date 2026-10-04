# Evaluation (EVL): metric, holdout, folds, gates, leaderboard

**Summary.** We scored every change on one fixed, hash-defined 25% holdout of labelled US/India S1, compared versions with a paired Poisson bootstrap, and kept a component only if it beat a simpler one.
The holdout has no France, so France was judged by label-free diagnostics and by leaderboard arithmetic, and the most expensive lesson of the project is that estimators built on our own probabilities share the model's blind spots.
Path prefixes: `ber/` is `code/business_entity_resolution/src/ber/`; `mv1/` is `experiments/ameya/model-v1/`; `pipe/` is `experiments/ameya/model-v1/pipeline/`; `box/` is `experiments/bakshi/box/`.

## 1. Purpose

Make every reported number comparable across machines, members and weeks, and give each design choice a falsifiable test.
Name the evaluation behind every number: local holdout (US/India, no France), public LB (a subset of test), private LB (rankings only; no score exists).

## 2. How it works

### 2.1 The metric ([`ber/eval/metric.py`](../../code/business_entity_resolution/src/ber/eval/metric.py):18-75)

Per S1, F0.5 = 1.25 c / (0.25 |T| + |P|). If T is empty the score is 1 when P is empty and 0 otherwise. The macro mean runs over every S1 of the universe, including S1 with no candidates. `per_entity_f05` is vectorised; `FastEval` (`mv1/common.py:136-166`) reproduces the same numbers for sweeps over thousands of selections. The module also reports blocking pair recall and the oracle F0.5 (the best score a perfect matcher could reach on the given candidates).

### 2.2 Holdout, folds, groups ([`ber/eval/splits.py`](../../code/business_entity_resolution/src/ber/eval/splits.py))

- `fold = splitmix64(eid) mod 20`, constants `0x9E3779B97F4A7C15`, `0xBF58476D1CE4E5B9`, `0x94D049BB133111EB` (`:22-40`). Pure unsigned-integer arithmetic, so every machine and library version gives the same split without sharing a file. The split is by S1 entity, because the metric is per S1 and stage-2 features need every candidate of an S1.
- Holdout = folds 0 to 4 = 549,699 S1 (24.91% of train S1; US 329,717, India 219,982) [M]. Training folds 5 to 19.
- Out-of-fold (OOF) groups: folds 5-9 are group 0, 10-14 group 1, 15-19 group 2, holdout -1 (`:61-67`). A model scoring group g trains on the other groups only. With `--all` the holdout becomes group 3 ([model-stages.md](model-stages.md)).
- Dev sample for 8 to 16 GB laptops: folds 0, 5, 10, 15 and one in four by a second hash digit, about 110k S1 (`:16-20, 53-58`).
- Blocking always runs over the full train pool and context features over the full candidate graph, as on test. Nothing supervised is fitted on the holdout except one or two tuned scalars (D-EVL-01).

### 2.3 Gates: the paired bootstrap ([`ber/eval/gates.py`](../../code/business_entity_resolution/src/ber/eval/gates.py):24-63)

Both systems are scored on the same S1 universe, so per-S1 differences are paired. The code resamples with Poisson(1) weights per S1 (equivalent to the classic bootstrap at this scale), 1,000 resamples in batches of 50, seed 0, and reports the mean difference, a 95% percentile interval and P(better). `keep` is true when the difference is at least `MIN_GAIN = 0.002` and the interval's lower end is above 0 (`:21, 62`). A CLI compares two match artifacts: `python -m ber.eval.gates --base A --new B`.

In practice the bar was relaxed after 26 Sep. The G6 rule in `mv1/decide.py:208-209` uses `delta > 0 and ci_low > 0` with no minimum; late changes of +10e-6 to +100e-6 were accepted on a positive interval and, for rules, on both holdout halves (CF-36 in [conflicts](../conflicts.md)). No record changes the bar; the working rule was "positive interval, positive halves, ties to the simpler".

Halves: stacked-rule gates use `splitmix64(s1) % 2`, equal to fold parity because 20 is even (`pipe/asrun/agents/decide/prep.py:9, 90`); the 7B rule uses `(s1 // 7) % 2` (`box/rescore_eval.py:42`); `box/analysis/resample_drop.py` uses 3,000 random 25% subsets.

### 2.4 The gate list G1 to G13 (FINAL_PLAN section 9)

| gate | question | what happened |
|---|---|---|
| G1 | blocking recall at least 99.0% (v0), 99.5% (v1)? | 0.9752, 0.9857, 0.9899, 0.99135 [M]; the 99.5% bar was never met |
| G2 | dense search as good as sparse? | never run; the sparse engine was built |
| G3, G9 | look-alike word odds help? cluster support help? | in model v2 bundled with blocking v1; no isolated number |
| G4 | stage 2 beats stage 1 alone? | passed: dev +0.00692 [+0.00622, +0.00772] |
| G5 | softmax with "none" beats argmax? | never built |
| G6 | set selection beats a tuned threshold? | decided model by model (see [decision-layer.md](decision-layer.md)) |
| G7, G8 | France predictions beat an empty France? does test need a shift? | probes built, never uploaded; diagnostics found no shift |
| G10 | cross-encoder adds value (bar +0.003)? | e5-small +0.00140, kept below the bar |
| G11 | learned pre-ranker needed? | the stage-0 filter and the cut took its role |
| G12 | Indic handling lifts the Indic slice? | parity: 0.9872 against 0.9870 |
| G13 | features transfer across countries (leave one country out)? | run; an unseen country costs 0.022 with words known and 0.10 with words unseen |

### 2.5 Reports and label-free checks

`work/reports/<tag>.json` holds the holdout macro F0.5 per country, the threshold and set-selection grids, the G6 result, diagnostics (predictions per S1, empty share) and the model's own expected-F0.5 forecast on holdout and test (`mv1/decide.py:211-247`). Label-free France tools: `mv1/rule_auc.py`, `mv1/ce_rule_auc.py`, `mv1/fhs.py`, `fpk/rulepop_decisions.py`. Leaderboard probes (built, not uploaded): `mv1/probe.py`, `probe_shift.py`, `fr_add.py`, `fr_threshold.py`.

### 2.6 Leaderboard arithmetic and controls

- The test S1 file is shuffled (each tenth holds about 15% France), nothing leaks, and US/India test predictions behave like the holdout (predicted records per S1 within 0.01, same empty share). So LB is about 0.85 times the US/India score plus 0.15 times the France score; precisely LB = 0.8423 + 0.14975 F_France with US/India taken at the holdout level (D-EVL-08) [E].
- Controls: one change per upload where possible, pairs of uploads that isolate one change (v7nst against v7n changed France only: +0.0031 on France), and a pre-set read-out rule written before each upload (D-SUB-11, D-SUB-23). Composite B was predicted at about 0.99085 and scored 0.990879.
- The France-emptied probe (fr0) would have turned France estimates into measurements; it was packaged three times and never uploaded, because a slot spent on a probe cannot improve the score (D-EVL-06, D-FRA-12).

## 3. Why this design

Decision records: [EVL](../decisions/EVL.md). D-EVL-01 shared deterministic holdout; D-EVL-02 test shift by diagnostics; D-EVL-03 gates G1-G13 (Sachi's discipline grafted onto Ameya's plan, D-ORG-03); D-EVL-04 model v1 used although the gate printed `keep: False` (+0.001995, a hair under the bar); D-EVL-05 label-free forecasts are diagnostics only; D-EVL-06 and D-EVL-10 probes built, never uploaded; D-EVL-07 and D-EVL-08 the gap is France, estimated by arithmetic; D-EVL-09 triage with a loss ledger; D-EVL-11 and D-EVL-12 rule-population AUC, then `fhs.py`; D-EVL-13 three memory-capped analysis sub-agents, gains must hold on two disjoint halves; D-EVL-14 value French changes with `cal`; D-EVL-15 trust the leaderboard over our estimators; D-EVL-16 keep the -6 threshold; D-EVL-17 lead with the public score.

## 4. Alternatives and why not

- Cross-validation over all of train: the metric is per S1 and the competition features need the whole graph; a fixed hash split gives one comparison set for everyone and costs no extra training.
- A single leaderboard as the judge: five uploads a day, a public subset, and about 15% France; it resolves differences of about 0.00004 only between near-identical candidates (D-SUB-12).
- Spending slots on pure probes: rejected by Ameya ("5 slots, no pure probes; protect the floor").
- A drop-S1 stress test to set thresholds: it models the wrong shift (records with a missing owner; the closeness profile did not show that) (D-EVL-02).
- Trusting our own probability-based France estimators: see section 6.

## 5. Numbers

| fact | value | level | source |
|---|---|---|---|
| Holdout | 549,699 S1; 1,901,267 true pairs; empty prediction scores 0.0558 | M | [numbers §1](../numbers.md) |
| Final model, local holdout | 0.991323 (US 0.991114, India 0.991635), the g1w stage-3 decision; precision 99.9%, recall 97.5% | M, local holdout, no France | [numbers §3.1](../numbers.md) |
| Submission, public LB | 0.990879 (Composite B) | M, public LB | [LB 2026-09-27 #04](../../submissions/records/2026-09-27_sub04.md) |
| Holdout to public-LB gap | v2 -0.0083, v3 -0.0092, v5all -0.0024 | M | [numbers §3.1](../numbers.md) |
| Climb on the public LB | 0.97608 (first recorded) to 0.990879 (+0.014799) | M | [numbers §6](../numbers.md) |
| France implied by the LB | about 0.93 (v2, v3), 0.971 to 0.976 (v5all), 0.978 (v7n), 0.981 (v7nst) | E | [RESEARCH_v6](../../experiments/ameya/model-v1/RESEARCH_v6.md) |
| Backtest of `cal` on past uploads | right sign 4 of 5, mean absolute error 42e-6, correlation 0.98; missed round 3 by about 115e-6 | M | [D-EVL-14](../decisions/EVL.md), CF-51 |
| 7B drop cut-off, whole holdout | -6: +0.000037 (halves +0.000033, +0.000041); -5: +0.000029; -4: +0.000017 | M | [D-EVL-16](../decisions/EVL.md) |
| One test S1 | 1/1,732,544 = 5.77e-7 of the test score | E | [numbers](../numbers.md) |

Never quote: a private LB score (none exists; we placed 2nd of the Top 10), "France was 0.93" as a final figure (it was the v2/v3 estimate; France was never measured, CF-09), or "we never trained on the holdout" without the qualification in [model-stages.md](model-stages.md) (CF-18). The full list is in [numbers.md](../numbers.md), "Numbers not to quote".

## 6. Failure modes and limits

- **The holdout is optimistic in absolute level.** Thresholds, shifts and cut-offs were tuned on it, and with `--all` its labels also train other groups' models and the isotonic map. Paired differences between versions are unaffected; the halves and a 2-fold check of the set selection (+23.7e-6 out of sample) are the honest checks (CF-18, [conflicts](../conflicts.md)).
- **No France locally.** The largest leaderboard effect (France, the whole gap, D-EVL-07) could not be gated on the holdout. The levels quoted for France are algebra on public scores with two unverified assumptions [E].
- **Circular estimators.** The share-shift forecast (D-EVL-05), the rule-population AUC after self-training (D-EVL-11, D-MDL-14) and `cal` after the 7B drops (D-EVL-14, D-EVL-15) each failed because they used the model's own probabilities. Round 3: `cal` predicted +69e-6 and the public LB gave -46e-6. Hindsight: one fr0 upload on 26 Sep would have made France a measurement for the cost of one slot.
- **Holdout and LB can disagree in sign.** v7nst had the lower holdout and the higher public LB (0.990179 against 0.989721 for v7n), because the holdout cannot see France.
- **Bar drift.** The +0.002 bar suited early gains; at 0.99 useful gains were 10 to 100 times smaller. It was never formally revised (D-EVL-03 hindsight).
- Noise: a fold-0 check carries about +-0.002 and the full holdout about +-0.001 [R, D-EVL-01]; paired deltas have much tighter intervals (for example +0.0097 [0.0095, 0.0099]) [M].

## 7. Scale

The metric and the bootstrap are linear in S1 and use matrix products over batches of 50 resamples, so 1,000 resamples over 550k S1 take seconds. The hash split needs no coordination, which is what makes it work across machines and at any size. At 100 times the data the holdout would stay a fixed fraction, but per-country labelled samples for each new country would matter more than the size of the holdout ([theory 05](../theory/05-evaluation-methodology.md), [theory 11](../theory/11-scaling-to-billions.md)) [E].

## 8. Theory links

[05 Evaluation methodology](../theory/05-evaluation-methodology.md), [04 Metrics and decisions](../theory/04-metrics-and-decisions.md), [F02 Probability and statistics](../theory/foundations/F02-probability-and-statistics.md), [F04 Classification metrics](../theory/foundations/F04-classification-metrics.md), [F09 Experiments and evidence](../theory/foundations/F09-experiments-and-evidence.md), [F12 Interpreting our results](../theory/foundations/F12-interpreting-our-results.md).

## 9. Likely questions

- **Why a hash split and not random folds?** Same split on every machine without sharing files, no row-order leakage (correlation -0.001), and S1-level so the competition features stay valid.
- **How do you know France?** We do not. We estimated it from the public score (about 0.93 early, about 0.98 late) and said so; the local holdout has no France.
- **Did you train on the holdout?** The holdout predictions are out of fold. The final test models also saw holdout rows, so it is a comparison set, not an untouched test.
- **Why did you accept gains far below your own bar?** Paired intervals above zero on two disjoint halves, ties to the simpler; the bar was set for gains 10 to 100 times larger.
- **Why did you never upload the fr0 probe?** A slot spent measuring cannot raise the score, and Ameya ruled out pure probes. In hindsight it would have been cheap insurance.
- More in [qa.md](../qa.md) and [lessons.md](../lessons.md).
