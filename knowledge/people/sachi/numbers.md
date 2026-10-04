# Sachi: numbers

Summary: the numbers from Sachi's work worth quoting, plus the few team numbers needed to read them. Each row has a scope,
an evidence level (M measured, E estimated, R reported, U uncertain) and a source. Never quote a row without its scope.
Times are IST. "France kit v1" came from an older model.

## 1. Baseline model (dev kit)

| fact | value | scope | level | source |
|---|---|---|---|---|
| macro F0.5, v0 baseline | 0.9652 | dev kit v0, dev-sample fold 0, 27,651 S1, threshold decision | M | [chat:sachi/web-1 2026-09-25 17:52] |
| precision / recall, v0 | 0.988 / 0.929 | same | M | same |
| training pairs / evaluation pairs | 2,393,231 / 819,316 | same | M | same |
| G6: DP minus threshold | -0.0004, CI [-0.0011, +0.0002] | same, stage-1 probabilities | M | same |
| tests passing | 92 | `ber` test suite at that commit | R | same |

## 2. Gates and studies

| fact | value | scope | level | source |
|---|---|---|---|---|
| name-uniqueness features | +0.0005 (below bar) | local holdout, stage 2 | R | [chat:sachi/web-1 2026-09-25 18:03] |
| unseen-country gap | about 0.028 (Ameya quoted 0.024) | dev kit v2, US to India | M / U | [chat:sachi/web-2 2026-09-26 12:50] |
| edit-profile features | +0.0005 against a +0.003 bar | dev kit v2, US to India | M | same |

## 3. e5-small vs e5-base (dev-kit pairs)

| fact | value | scope | level | source |
|---|---|---|---|---|
| log-loss reduction over stage-1 probability: e5-small / e5-base / both | 6.5% / 10.0% / 10.1% | 40,000 train, 20,000 eval, batch 32, RTX 3090 | M | [chat:sachi/web-3 2026-09-26 evening] |
| AUC of stage-1 probability plus cross-encoder | 0.9647 (small), 0.9666 (base) | same | M | same |
| training time | 1.28 min (small), 3.20 min (base) | same | M | same |

## 4. Qwen2.5 LoRA cross-encoder

| fact | value | scope | level | source |
|---|---|---|---|---|
| band size | 1,568,554 train pairs (27.2% positive), 1,490,930 test pairs | Ameya's band export | M | [chat:sachi/web-3 2026-09-26 23:29] |
| median tokens per pair | 36 | same | M | same |
| smoke test holdout AUC, 1.5B | 0.7336 | 3,000 training pairs | M | same |
| group 1 out-of-fold AUC, 1.5B | 0.9279 | band, 276,196 training pairs (35% of the data), out-of-fold | M | [chat:sachi/web-3 2026-09-27 02:31] |
| training steps per group | about 8,600 | batch 32, 35% of the data | M | same |
| time per group: train / score | about 35 min / about 55 min | RTX 4090 | E | same |
| group 0 out-of-fold AUC, `qst` (Ameya's run) | 0.9334 | band, with France self-training | R | `docs/status/ameya.md` 27 Sep |
| 7B smoke test holdout AUC | 0.6761 | 3,000 pairs, batch 16, gradient checkpointing, RTX 4090 | M | [chat:sachi/web-3 2026-09-27 09:30] |
| memory limit | batch 64 ran out of memory at 1.5B on a 24 GB card; batch 128 at e5-large | RTX 4090 | M | [chat:sachi/web-3 2026-09-26 and 2026-09-27] |
| Hugging Face revision, Qwen/Qwen2.5-1.5B | `8faed761d45a263340a0528343f099c05c9a4323` | checked against the Hub on 2026-09-29 | M | [chat:sachi/web-3 2026-09-29 00:40] |
| Hugging Face revision, intfloat/multilingual-e5-large | `3d7cfbdacd47fdda877c5cd8a79fbcc4f2a574f3` | same | M | same |
| `ce_llm.py` on main | one commit, [commit 5bff1e7] (2026-09-26 23:37) | repo | R | [issue #66] |

## 5. Audits (France kit v1, older model)

| fact | value | scope | level | source |
|---|---|---|---|---|
| empty-address same-name ties | 13,105 records, 23.8 per 1,000 S1 | holdout universe 549,699 S1 | M | [chat:sachi/web-3 2026-09-27 13:24] |
| share of those the model predicted | 9.0% | same | M | same |
| owner accuracy from copy counts / chance | 0.313 / 0.273 | same | M | same |
| add rule at posterior 0.50 | 1,836 pairs, precision 0.516, holdout change -0.000672 | same | M | same |
| S1 at source cap: true rate | 0% | 406 pairs | M | same |
| records with sum pc above 1.05, per 1,000 S1 | holdout 0.41, France 5.86 | model-kept, pc at least 0.5, no rule adds | M | [chat:sachi/web-3 2026-09-27 18:35] |
| kept pairs with a rival at pc 0.3 or more, per 1,000 S1 | holdout 0.1, France 2.9 | same | M | same |
| dropping low renormalised pairs: holdout change | -0.000007 (below 0.60), -0.000047 (0.70), -0.000137 (0.76) | local holdout | M | same |
| different street, same name and number: true rate | 99.9% | US/India holdout, 23.2 per 1,000 S1, model-kept | M | [chat:sachi/web-3 2026-09-27 18:48] |
| same pattern in France: kept | 51.5% of 6.56 per 1,000 French S1 (median pc 0.75) | France kit v1 | M | same |
| kept different-street French pairs | 870 (3.4 per 1,000 French S1) | same | M | same |

## 6. Synthetic French

| fact | value | scope | level | source |
|---|---|---|---|---|
| pairs generated | 99,702, 40.1% true | from 40,000 French S1, seed 26 | M | [chat:sachi/web-3 2026-09-27 about 13:30] |
| generator vocabulary | 1,575 French words | words of at least 4 letters seen at least 20 times | M | same |
| my training run | stopped at step 9,800 of 26,609, group 0; about 52 min left for the group | RTX 4090, e5-large, batch 32 | M | [chat:sachi/web-3 2026-09-27 14:25] |
| legal-form drop/change/order in real French copies / synthetic | 22.6% / about 3% | Ameya's France-diff agent | R | [issue #63] |
| synthetic-trained bge on the 7B's French rejects | flags 708 of 859 (82%) | out of band | R | [issue #64] |

## 7. Team numbers used above

| fact | value | scope | level | source |
|---|---|---|---|---|
| Composite B | 0.990879 | public LB | M | `AGENTS.md`, [issue #64] |
| mixf2 / mixf7 | 0.990819 / 0.990833 | public LB | M | [issue #64] 22:15 |
| mixmdp | 0.990699 | public LB | M | [issue #64] |
| v7sq-dpc | 0.990545 | public LB | M | `docs/status/ameya.md` |
| cal over-prediction on mixmdp's France | about 9% (+146e-6 against +134e-6) | pc-based estimator | R | [issue #64] Ameya's correction |
| round-3 over-valuation by pc-based cal | about 115e-6 | decoy-aware 7B-cal decomposition | R | [issue #64] 22:15 |
| TSV hashes, Composite B | `df4bccd7…62e8` / `58c824a3…20e5` (full values in `S-X-14`) | final_zip folder | M | [chat:sachi/web-3 2026-10-03] |

## 8. Cost and compute (rough)

| fact | value | level | source |
|---|---|---|---|
| rented GPU price range | about $0.2 to $0.6 per hour (3090 and 4090) | R | screenshots |
| credit at selected moments | $4.78 (26 Sep 21:56), $9.71 (26 Sep 22:57), $7.90 (27 Sep 08:26), $5.48 (27 Sep 14:42) | R | screenshots |
| total GPU spend | unknown | U | see open-questions |
