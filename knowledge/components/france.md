# France: the unseen country (FRA)

**Summary.**
- France never appears in train, so it has no labels, no holdout and no direct score. It carries 14.975% of the public-score weight (259,452 of 1,732,544 test S1). Every French F0.5 on this page is an estimate [E] unless marked otherwise.
- We closed most of the early gap with label-free look-alike odds, generator-based rules and cross-fitted self-training of our own predictions. Round 1 of self-training was worth +0.000458 on the public LB; later rounds were checked one by one and round 3 was rejected by the leaderboard.
- Path key: `mv1/` = `experiments/ameya/model-v1/`, `stk/` = `experiments/ameya/model-v1/stack/`, `box/` = `experiments/bakshi/box/`, `pipe/` = `experiments/ameya/model-v1/pipeline/`. Evidence levels as in [STANDARD §3](../STANDARD.md).

## 1. Purpose

Make a model trained on US and India transfer to a country it has never seen, and decide what to predict there without labels. The rule is the open set: any country absent from the train records is treated as unlabelled, and no model has a country feature ([D-PRB-01]).

## 2. How it works

**What counts as "without labels."** Scripts read the countries of the train records and treat the rest as unlabelled (`mv1/pseudo_labels.py:19-23`, `mv1/post_ops.py:310-315`, `stk/apply_combo.py:60`, `stk/merge_dpc.py:16`, `box/compose_tsv.py:53-55`). Exceptions that filter on `country == "France"`: `stk/dp_france.py:116`, `box/rescore_export.py:56` ([CF-26]).

**The gap diagnosis.** The public LB is LB = 0.38274·F_US + 0.46751·F_India + 0.14975·F_France [E]. For v2 and v3 the holdout said 0.98436 and 0.98882 and the public LB said 0.97608 and 0.97961 (gaps −0.0083 and −0.0092); backing out, France was about 0.93 [E]. The causes found:
- Op-B look-alikes in French words the model had never seen: v4 predicted op B at 65.9 per 1000 French S1 against 0.04–0.05 in US/India [M] ([rules.md](rules.md)).
- Legal-form bits: stage-1 p1 on 30,518 French pairs was 0.456 as is, 0.027 with the bits zeroed, 0.232 with English bits, so the legal bitmasks were dropped for France [M].
- The leave-one-country-out test (US to India, India's labels hidden) priced an unseen country: in-country 0.98346; US only with India's words known 0.96106; India's words hidden 0.88235; with the label-free proxy 0.95984 [M] ([D-FRA-03]). It became the stand-in for every France experiment.

**Label-free odds.** The proxy look-alike odds `lop` replace the learned word odds `lo` for words never seen in training (`feats_lo_proxy.py`, `lo_mix.py`; see [features.md](features.md)). Look-alike patterns per French S1 fell from 0.047 to 0.002–0.007 [M, label-free count] ([D-FRA-03], [D-FRA-01]).

**Rule populations** (`mv1/rule_pop.py:20-24`): `post_ops.classify` with the robust address on French test candidate pairs; A, APP and ACR give y = 1, op B gives y = 0. As run: 128,856 pairs, A 38,304 + ACR 14,884 + APP 11,652 positive and 64,016 op-B negative [R].

**Pseudo-labels** (`mv1/pseudo_labels.py`, `:17, 41-46`)
- y = 1 if the pair is in the teacher's final matches with teacher stage-3 pc ≥ 0.9, or the rules added it (in `-ops3`, not in `-s3`), or the acronym join or stack did (in the final, not in `-ops3`).
- y = 0 if the pair is not in the final with pc ≤ 0.05, or was an op-B prediction the rules dropped (in `-s3`, not in `-ops3`). y = 0 is assigned after y = 1 and overrides it. Everything else is −1: unlabelled, still cross-fitted and scored.
- Pair sets (`:24-33`): the cross-encoder band, or every French stage-2 row (p0 ≥ tau0, p1 ≥ 0.002).
- **Guard, France block only** (`mv1/pseudo_guard.py:30-53`): start from round-2 labels; records with an empty address keep their round-1 label, because the round-2 teacher had turned about 12.7k empty-address same-name collision pairs into confident negatives; the rule populations override. As run: 1,429,666 pairs, 214,288 with an empty record address (16,803 changed), 95,350 rule pairs; 861,340 positive, 516,463 negative, 51,863 unlabelled [R].

| label file | teacher | pairs | guard | trained |
|---|---|---|---|---|
| `pseudo_fr_v7ce3` | v7ce3 | French band | none | e5ls, qst; France block e5ls2, bges, e5fr |
| `pseudo_s2_fr_v7ce3` | v7ce3 | all French stage-2 rows | none | stage 2 of v7sq and g1w (weight 1) |
| `pseudo_fr_v7sq` | v7sq-dpc | French band, 385,274 | none | q7st |
| `pseudo_s2_fr_v7sq_guard` | v7sq-dpc, guarded | 1,429,666 | yes | France-block stage 2 (weight 3) |

**Cross-fitting.** Cross-encoders: third = `fold_of(s1) % 3`, so model g never sees the labels of the third it scores (`mv1/ce_box.py:76`, `box/llm_group.py:95`). Stage 2 with `--all`: `fold_of(s1) % 4` (`mv1/s2.py:256`). Early stopping and calibration use labelled rows only. A dry run showed 0 S1 overlap.

**The France decision layer** (`stk/dp_france.py`, `:45, 80-177`): the expected-F0.5 selection on French stage-3 pc with shift 0.2, crowd −0.3, phantom 0.01, p1 ≥ 0.02, top 2, French S1 only. Guards: pairs the rules added stay, pairs they dropped stay dropped, look-alike swaps are removed; an addition is refused when it is a one-word swap to a real word that resembles the S1's word (Indel ≥ 0.5) or sits at the S1's address in an op-B position (`:146-160`). As run: drops 224, adds 357 of 361, 21 swap additions refused [R]. See [decision-layer.md](decision-layer.md).

**The France block in Composite B** (mixmdp's French rows, `pipe/france_mixmdp.sh`): cross-encoders qst, e5ls, e5ls2, bges, e5fr → `cmq7`; stage 2 on the guarded round-2 labels at weight 3 (1,377,803 labelled rows, 0.625 positive); decide (c2 0.991186) → stage 3 → decide (threshold 0.725, 0.991223) → rules (`post_ops`, `acr_join`, stack: copy +375, city −76) → `apply_swapsim` (−454) → `dp_france` → 871,147 French pairs on 244,531 S1, 870,307 after the 7B drops [R/M].

**The label-free estimators and their bias.**
- `cal`: values a change by treating the new model's pc as calibrated on the US/India holdout. Backtest on 5–6 past LB pairs: scale 0.96, mean absolute error 42e-6, correlation 0.98. It failed on round 3 (predicted +69e-6, measured −46e-6) [E/M].
- `s1` under-predicts by about 20%; `s2` had the wrong sign on every pair; rule-only changes are undervalued. After the 7B verdicts, pc-based estimators were 53–98e-6 too optimistic for the round-3 family ([D-FRA-26]). The "within ±0.00005" claim did not hold.
- `fhs.py`: a label-free count of true copies gained and lost per 1000 French S1 (the narrowed hunt plus polish scores +1.09) [E].
- **Size-bias test** ([D-FRA-19]): a true copy of S1 x was drawn in proportion to x's number of copies, so x's other copies follow a size-biased distribution, while a planted extra attaches to any S1. Fitting the false share f by maximum likelihood gives French acronym holders 0.00 [0.00, 0.01], look-alike swaps 0.83 [0.56, 1.10], the encoder-veto pairs −0.04 [−0.24, 0.24]. On US/India true populations score −0.05 to 0.0 and false ones 0.10–0.76 [E].

**Probes never uploaded.** France-empty (`fr0`, about 0.85, "means nothing without its pair"), France threshold cuts (`fr090`, `probe_shift`) and a lower-threshold probe were built five times and never uploaded: the last slots always went to a real candidate ([D-FRA-12], [D-SUB-09], [D-SUB-11]). By 27 Sep self-training had emptied the band around the threshold (owned pairs at pc 0.7–0.8 fell from 36.5 to 11.8 per 1000 S1), so moving the threshold touches about 12 predictions per 1000 S1, about ±0.00005 [M/E]. About 97% of French predictions have stage-3 pc ≥ 0.99.

**Synthetic French.** Sachi's generator made 99,702 pairs (40.1% true) from 40,000 French S1; `synth_fr3` 107,766 (39.7% true). Real copies differ: legal-form edits 22.6% real against 2.5–3.2% synthetic; list append 1.2% against 11.6–13.8%; typo 1.2% against 10.3–12.3%; acronym 1.6% against 9.1–11.2% [M]. Rejected as a source; one bge detector kept as corroboration (it flags 708 of the 859 French 7B rejects) ([D-FRA-23], [D-FRA-25]).

## 3. Why this design

- Country-agnostic features and test-fitted statistics at stage 1: [D-FRA-01]. No external data, own-data augmentation only: [D-FRA-04].
- Look-alike odds without labels: [D-FRA-03]; rules instead of synthetic pairs: [D-FRA-05], [D-RUL-01].
- Self-training, rejected twice ([D-FRA-02], [D-FRA-11]), was adopted once the look-alike odds and the rules existed: [D-FRA-13] (cross-fitted, round 1; "a dropped false positive gains 0.18 while a dropped true pair costs 0.07").
- Stop unguarded round 2; guarded round-2 stage-2 labels at weight 3 (weight 5 gave the same +0.000167 [E]): [D-FRA-16], [D-FRA-18]. No round 2 for the encoders: [D-FRA-22].
- A French decision layer: [D-FRA-20], after [D-DEC-16], [D-DEC-18]. Acronym matches kept after the size-bias test: [D-FRA-19].
- After the leaderboard contradicted pc-based estimates: [D-FRA-24], [D-FRA-26].

## 4. Alternatives and why not

- **Self-training without guards, or more rounds.** In the leave-one-out test with the country's words unseen, each round got worse: 0.88235 → 0.8512 → 0.83075 → 0.823 (words known: 0.96106 → 0.96498). Round 2 unguarded tied round 1 on the holdout (v7nst2 0.991187 against 0.991194) but, read by hand, dropped clear copies and added word swaps; 35% of `frs2`'s drops had an empty record address (base rate 2.7%). Round 3 scored −46e-6 on the LB (mixf7). Round 4 changed 3,553 of 1.43M labels ([D-FRA-24]).
- **Rule-labelled French pairs:** India stand-in 0.96463 against 0.96555 US-only ([D-FRA-10]).
- **Stricter threshold, per-record renormalisation, transductive assignment, address clusters:** none paid ([D-DEC-10], [D-DEC-11], [D-FRA-14], [D-FRA-06]).
- **A French encoder veto:** vetoed pairs are true copies by the size-bias test ([D-FRA-21]).
- **Synthetic supervision:** `cal` rose by reverting leaderboard-confirmed moves ([D-FRA-23]).

## 5. Numbers

| fact | value | scope | level |
|---|---|---|---|
| Round 1 self-training (v7n → v7nst) | +0.000458, US/India unchanged to 0.00002, France about +0.0031; 31 changes per 1000 French predictions (+14.0 / −17.4) | public LB | M |
| v7nst-dpc → v7sq-dpc | +0.000281, about +0.00023 from France | public LB | M/E |
| mixmdp over v7sq-dpc | +0.000154: US/India +20e-6, France +134e-6 (`cal` said +146e-6) | public LB | M |
| mixf7 (round-3 France) against B | −0.000046 (`cal` said +69e-6) | public LB | M |
| French part of each LB step | 780 → 470 → 240 → 130 (e-6), about half the last | public LB | E |
| French uncertain band after round 1 | pc 0.3–0.99 from 358.2 to 186.1 per 1000 S1; op-B pairs above 0.7 from 28% to 0.4% | test France | E |
| Σ pc per French S1 | 3.5456 against the generator's 3.46; holdout 3.4320 against truth 3.4323 | label-free | M (counts) |

**Implied France level, as an estimate only.** From the public-LB algebra [E]: v2/v3 about 0.93; v5all 0.971–0.976; v6all about 0.973; v7n 0.978; v7nst about 0.981; v7nst-dpc about 0.982; v7sq-dpc about 0.983; mixmdp about 0.984. No source gives Composite B a value except an unquotable "about 0.9886". Both assumptions behind it (US/India score on test like the re-weighted holdout; the public subset has the test's country mix) are unverified, and France was never measured ([CF-09]). Say: "from about 0.93 to about 0.98."

## 6. Failure modes and limits

- **No labels, no gate.** Self-training variants cannot be judged on the holdout; only the leaderboard can, at about ±0.00004 noise.
- **Confirmation bias** out of distribution (see the ladder above); every round was one more risk.
- **pc is overconfident in France**; the estimators inherit that. Hence [D-FRA-26].
- **Mixed label sets** ([CF-28]): q7st trained on unguarded round-2 band labels; g1w's stage 2 on round-1 labels; only the France block's stage 2 used the guard.
- **`cmq7` is NaN on US/India band rows**, so the France block's US/India output is never reused.
- **7B coverage.** The French drop list was built from v7sq-dpcsf; 19 of 859 pairs are absent from mixmdp and mixmdp-only predictions were never re-checked ([llm-recheck.md](llm-recheck.md)).
- **Departments.** `DEPARTMENT_REGION` maps departments of three regions only, so other departments keep the department word.
- **Self-training on test records** with "only the provided data": our own predictions on provided unlabelled records, no external data; the agreed one-sentence wording is still open ([CF-11]).

## 7. Scale

A new country needs no code change: absent from train means unlabelled. Cost is one pseudo-labelling pass and one cross-fitted retrain per country family, linear in that country's pairs; thirds and quarters are by S1, so groups shard cleanly. At 100× or 1000× the number of unseen countries, round-by-round drift is the risk, not compute, so each added country would need its own guarded labels and a label-free check. Count thresholds such as "real word in at least 20 S1 names" assume a country of French size and would need rescaling for small ones. See [theory 09](../theory/09-self-training-and-domain-shift.md).

## 8. Theory links

[09 self-training and domain shift](../theory/09-self-training-and-domain-shift.md), [05 evaluation methodology](../theory/05-evaluation-methodology.md), [01 entity resolution](../theory/01-entity-resolution.md), foundations [F10](../theory/foundations/F10-semi-supervised-and-domain-shift.md), [F12](../theory/foundations/F12-interpreting-our-results.md), [F09](../theory/foundations/F09-experiments-and-evidence.md). Neighbours: [rules.md](rules.md), [cross-encoders.md](cross-encoders.md), [evaluation.md](evaluation.md).

## 9. Likely questions

- **How do you know France's score with no labels?** We do not. We back it out of the public score (about 0.93 early, about 0.98 at the end) and treat it as an estimate with two unverified assumptions.
- **Isn't self-training on test records cheating?** It uses our own predictions on the provided unlabelled test records, cross-fitted by S1 group, with no test labels and no external data.
- **Self-training failed in your leave-one-out test; why use it?** That ladder is a stage-1-only test and it warned us that more rounds drift. So we used one round for the encoders, guards on round 2 and stopped at round 3. The leaderboard, not the ladder, showed round 1 (+0.000458) and guarded round 2 paying and round 3 not.
- **Why did round 3 fail?** We do not know exactly; the estimator predicted +69e-6 and the leaderboard said −46e-6. We distrust pc-based estimators for this family.
- **Why trust the rules in France?** They come from the generator's operations, each measured on US/India labels, and checked label-free (size-bias test, counts).
- **What would you change?** Build the France-empty probe earlier to pin the level down, and keep an estimator that does not rely on pc.

[CF-09]: ../conflicts.md
[CF-11]: ../conflicts.md
[CF-26]: ../conflicts.md
[CF-28]: ../conflicts.md
[D-DEC-10]: ../decisions/DEC.md
[D-DEC-11]: ../decisions/DEC.md
[D-DEC-16]: ../decisions/DEC.md
[D-DEC-18]: ../decisions/DEC.md
[D-FRA-01]: ../decisions/FRA.md
[D-FRA-02]: ../decisions/FRA.md
[D-FRA-03]: ../decisions/FRA.md
[D-FRA-04]: ../decisions/FRA.md
[D-FRA-05]: ../decisions/FRA.md
[D-FRA-06]: ../decisions/FRA.md
[D-FRA-10]: ../decisions/FRA.md
[D-FRA-11]: ../decisions/FRA.md
[D-FRA-12]: ../decisions/FRA.md
[D-FRA-13]: ../decisions/FRA.md
[D-FRA-14]: ../decisions/FRA.md
[D-FRA-16]: ../decisions/FRA.md
[D-FRA-18]: ../decisions/FRA.md
[D-FRA-19]: ../decisions/FRA.md
[D-FRA-20]: ../decisions/FRA.md
[D-FRA-21]: ../decisions/FRA.md
[D-FRA-22]: ../decisions/FRA.md
[D-FRA-23]: ../decisions/FRA.md
[D-FRA-24]: ../decisions/FRA.md
[D-FRA-25]: ../decisions/FRA.md
[D-FRA-26]: ../decisions/FRA.md
[D-PRB-01]: ../decisions/PRB.md
[D-RUL-01]: ../decisions/RUL.md
[D-SUB-09]: ../decisions/SUB.md
[D-SUB-11]: ../decisions/SUB.md
