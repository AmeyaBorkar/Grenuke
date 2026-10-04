# Numbers: bakshi

Numbers from Bakshi's work worth quoting, each with scope, evidence level (M/E/R/U) and source (`knowledge/STANDARD.md` §2.4 and §3). Where `knowledge/numbers.md` already has the same fact, that page wins; this list adds the detail behind it.

**Summary.** Composite B scored public LB 0.990879, the team's best, +0.000180 over mixmdp. Its US/India model g1w scored local holdout 0.991323. The 7B re-check added +0.000033 on the local holdout. The final ZIP verified byte-identical on rebuild.

## Leaderboard (public LB)

| fact | value | scope | level | source |
|---|---|---|---|---|
| Composite B | **0.990879** (rank 16 on the public board at the time) | public LB, 27 Sep #04 | M | [LB 2026-09-27 #04]; [chat:bakshi/b0c6934d 2026-09-27 20:55] |
| B7, the last upload | 0.990875 (−0.000004 vs B, a tie) | public LB, 27 Sep #07 | M | [LB 2026-09-27 #07]; [chat:bakshi/b0c6934d 2026-09-27 23:39] |
| Composite B over mixmdp | +0.000180 (0.990699 → 0.990879) | public LB | M | [LB 2026-09-27 #04] |
| mixf2 / mixf7 (Ameya's, uploaded the same evening) | 0.990819 / 0.990833 | public LB | M | [chat:bakshi/b0c6934d 2026-09-27 22:01] |
| Stack vs model split, morning of 27 Sep | v7nst 0.990179 → v7nst-dpc 0.990264 (+0.000085) → v7sq-dpc 0.990545 (+0.000281) | public LB | M | [chat:bakshi/01a0d754 2026-09-27 10:21] |
| Agent's estimate for v7sq-dpc before upload | ≈0.990295, i.e. +0.00012 against +0.000366 measured ("low by 3×") | public LB forecast | E | [chat:bakshi/b0c6934d 2026-09-27 10:50] |
| Gain split of Composite B over mixmdp | India g1w ≈ +31e-6; US g1w ≈ +10e-6; US/India 7B drops ≈ +28e-6; French 7B drops ≈ +111e-6 (remainder) | public LB, decomposed | E | `experiments/bakshi/final-package/METHODOLOGY_bakshi.md`; CF-30 |
| Final standing | Top 10 of 32,000+ teams, 2nd on the list; no private score published | private LB ranking | R | issue #79 |

## Local holdout (US/India, 549,699 S1)

| fact | value | scope | level | source |
|---|---|---|---|---|
| g0 (v7sq rebuilt on Bakshi's box) | 0.991261 (US 0.991064, India 0.991558) vs v7sq 0.991246 | local holdout | M | [chat:bakshi/b0c6934d 2026-09-27 17:20]; `work/reports/ameya-model-g0-s3.json` |
| Stage-2 mix ablation with the 7B | g1 0.991276; **g1w 0.991323** (US 0.991114, India 0.991635); gbag 0.991313; g1x3 0.991322; g7only 0.991286 | local holdout | M | [chat:bakshi/b0c6934d 2026-09-27 18:07], [chat:bakshi/b0c6934d 2026-09-27 19:22] |
| g1w vs v7sq3, paired bootstrap (Ameya) | India +66.1e-6 [+19.4, +112.9], P 0.998; US +26.2e-6, P 0.906 | local holdout | M | D-SUB-21 |
| 7B re-check: drop if logit < −6 (out of band) | +0.000033 (both halves positive); −5 +26e-6; −4 +12e-6; −3 −4e-6; −2 −55e-6; 0 −0.003168 | local holdout sample, 186,897 S1 | M | [chat:bakshi/b0c6934d 2026-09-27 18:20], [chat:bakshi/b0c6934d 2026-09-27 18:25] |
| Truth by 7B logit bucket (predicted pairs, p1 > 0.99) | < −6: 24 pairs, 8.3% true; [−6, −4): 51, 86.3%; [−4, −2): 138, 94.9%; [−2, 0): 6,616, 99.6%; ≥ 0: 596,333, 99.99% | local holdout sample, 631,001 pairs | M | [chat:bakshi/01a0e3be 2026-09-27 22:20] |
| Drop rule stability | mean +0.0000328, sd 0.0000167; positive in 99.7% of 3,000 random 25% subsets | local holdout, resampled | M | [chat:bakshi/b0c6934d 2026-09-28 13:16]; `box/analysis/resample_drop.py` |
| Public − private gap of the holdout score | sd 0.00016 at a 25% public share; 0.000231 at 10% | local holdout, simulated | M | [chat:bakshi/b0c6934d 2026-09-28 13:16]; [chat:bakshi/b0c6934d 2026-09-29 01:37] |
| Loss anatomy of g0 | partial misses 69%, S1 with none found 20%, wrong matches 8%, other 3% | local holdout | M | [chat:bakshi/b0c6934d 2026-09-27 17:44] |
| Missed true pairs | 48,509 (2.6%): 16,455 never candidates, 15,152 rejected at pc ≈ 0, 237 owned by another S1 | local holdout | M | [chat:bakshi/b0c6934d 2026-09-27 17:56] |
| Precision / recall of g0 (pairs) | 0.99897 / 0.97449; 3.374 predictions per S1 | local holdout | M | [chat:bakshi/01a0e2bb 2026-09-27 17:31] |
| Recall slices tried | empty-address name match 17–24% true; best sub-slice 59%; 7B additions ≤ 71%; break-even for an addition about 75% | local holdout | M | [chat:bakshi/b0c6934d 2026-09-27 17:56], [chat:bakshi/b0c6934d 2026-09-27 18:37] |
| Blend of six cross-encoders | band AUC 0.9575; as the decision score ΔF −0.001023 | local holdout band, 389,668 rows | M | [chat:bakshi/b0c6934d 2026-09-27 22:48] |

## Cross-encoders (band AUC, labelled US/India band, p1 ∈ [0.02, 0.99])

| fact | value | scope | level | source |
|---|---|---|---|---|
| Qwen2.5-7B (`q7st`) | holdout 0.9436, OOF 0.9396; groups 0.9397 / 0.9393 / 0.9399 | holdout band / OOF | M | [chat:bakshi/b0c6934d 2026-09-27 17:12]; [chat:bakshi/01a0e2bb 2026-09-27 17:29] |
| Qwen3-4B (`q34st`) | holdout 0.94115, OOF 0.93700 | holdout band / OOF | M | [chat:bakshi/b0c6934d 2026-09-29 01:02] |
| The others, for comparison | e5l 0.9391 / 0.9350; e5l2 0.9441 / 0.9403; e5ls 0.9439 / 0.9403; bge 0.9417 / 0.9382; qst (Qwen2.5-1.5B) 0.9381 / 0.9332 (holdout / OOF) | holdout band / OOF | M | [chat:bakshi/b0c6934d 2026-09-27 17:12], [chat:bakshi/b0c6934d 2026-09-27 22:48] |
| Track B round 3 (labelled gate) | `cem2` 0.9428; `cem` 0.9433; e5l+bge 0.9417; e5l 0.6 / bge 0.4 0.9414 | holdout band | M | [chat:bakshi/b0c6934d 2026-09-27 02:40] |
| Band coverage after the (s1, r) remap | train 100%; test 1,490,929 of 1,490,930 | CE band | M | [chat:bakshi/01a0e2b4 2026-09-27 17:20] |

## Test-set counts (label-free)

| fact | value | scope | level | source |
|---|---|---|---|---|
| Composite B shape | 1,732,544 rows; 5,851,832 pairs; 99,802 empty; 3.3776 per S1; 0 two-owner records; 0 cross-country pairs; 0 pairs outside 6,410,308 candidates | test | M | [chat:bakshi/b0c6934d 2026-09-28 00:00]; `PACKAGE_README.md` |
| Composite B per country | France 870,307; India 2,734,227; US 2,247,298 pairs | test | M | `final-package/PACKAGE_README.md` |
| Composite B files | matching sha256 `df4bccd785b3fa785b7edcf0532288bcddc0010e2e31ce6f358064529ecb62e8`; candidates `58c824a3f61c184fe7da1a448a4ac94284f288feff9c351abfe16a3dfc0520e5` | files | M | [LB 2026-09-27 #04] |
| 7B drops in Composite B | 840 French + 310 US/India (1,150 of a 1,169-pair list) | test | M | [chat:bakshi/b0c6934d 2026-09-27 19:40]; `knowledge/numbers.md` |
| French 7B drops that are decoys (Ameya) | 78% of the 859 are same generic name, same house number, different street | test, France | R | [chat:bakshi/b0c6934d 2026-09-27 20:00] |
| French drop rate by S1 third (leakage check) | 0.1118% / 0.1082% / 0.1070% | test, France | M | [chat:bakshi/b0c6934d 2026-09-27 20:07] |
| Predictions never read by a cross-encoder | 94.5% of final predictions have p1 > 0.99 | test | R | [chat:bakshi/b0c6934d 2026-09-27 17:33]; SOLUTION_DOC |
| B7 vs Composite B | +251 / −1,699 French pairs; sha256 `3d7b09d6c3b964b67d3ce164512bf22df5130dab53cd99e53d8f2d35673a468d` | test | M | [chat:bakshi/b0c6934d 2026-09-27 23:34] |
| v7nst matches outside v6all's candidates | 3,790 pairs over 3,725 S1; the real candidate file held exactly the predicted 6,410,247 | test | M | [chat:bakshi/b0c6934d 2026-09-27 00:43], [chat:bakshi/b0c6934d 2026-09-27 01:31] |
| Robust-B v7 probe (never uploaded) | −1,148 French pairs over 1,137 S1; US/India unchanged | test | M | [chat:bakshi/01a0dd57 2026-09-26 16:33] |

## Day 1 modules (25 Sep)

| fact | value | scope | level | source |
|---|---|---|---|---|
| Normalisation v0a | 12,527,040 train / 11,702,133 test rows × 29 columns; train 484.2 s, test 516.1 s; 8 workers on a 16 GB laptop | full data | M | [handover 1658](../../../docs/handover/2026-09-25_1658_bakshi_normalize-v0.md) |
| String features v0 | 56 features (+15 context); 3,212,547 dev pairs in 434.4 s → 214.4 s; peak 5.89 GiB | dev kit | M | [handover 2056](../../../docs/handover/2026-09-25_2056_bakshi_features-v0.md) |
| Full-pool retrieval probe (never committed) | pair recall 0.826 → 0.911 (US 0.973, India 0.838) | 400 sampled train S1 | M | [chat:bakshi/01a0d754 2026-09-25 15:55] |

## The final ZIP

| fact | value | scope | level | source |
|---|---|---|---|---|
| `Grenuke_submission.zip` checked on #75 | sha256 `7f0778759e2c66563ad1df52a82a7e7a340e2b05f6b7bc3b26d55516aa0ff8a2`; 88,353,544 bytes; 150 files, MANIFEST 149/149; 115 tests in a clean venv; rebuild from `main` `c426861` byte-identical | package | M | [chat:bakshi/b0c6934d 2026-09-29 04:01]; [issue #75] |
| Qwen2.5-7B revision shipped | `d149729398750b98c0af14eb82c78cfe92750796` (Apache-2.0, 7.6B) | model | M | `final-package/requirements.txt` |

## Compute and time (27 Sep)

| fact | value | scope | level | source |
|---|---|---|---|---|
| Pipeline box | 2× RTX 4090 24 GB, 64 vCPU, 700 GB disk, driver 565.77; $0.999/h | hardware | M | [chat:bakshi/b0c6934d 2026-09-27 14:00] |
| Training box 1 | 4× H100 SXM, interruptible, bid $5.94/h; taken away about 15:05 | hardware | M | [chat:bakshi/b0c6934d 2026-09-27 15:18] |
| Training box 2 | 4× H100 80 GB, on-demand, about $9/h; driver 595.71, torch 2.11 + cu128 | hardware | M / R | [chat:bakshi/b0c6934d 2026-09-27 15:24] |
| 7B resume points from Drive checkpoints | group 0 step 4,321 / 9,663; group 1 6,561 / 9,706; group 2 4,371 / 9,912 | training | M | [chat:bakshi/b0c6934d 2026-09-27 15:46] |
| 7B speed | about 3.6 steps/s (box 1), 2.2–2.4 (box 2); scoring about 570–660 pairs/s per H100 | training / inference | M | [chat:bakshi/b0c6934d 2026-09-27 17:03] |
| Rebuild times | phase A done 16:11; g0 stage 2 1,293 s; each mix variant about 40 min | pipeline box | M | [chat:bakshi/b0c6934d 2026-09-27 17:20] |
| Budget estimate for the push | about $45–60 for the box split (vs $120–150 for 8× H100); total spend not recorded | estimate | E | [chat:bakshi/b0c6934d 2026-09-27 13:43] |

## Do not quote

- "France ≈ 0.9886" for Composite B and the France range [0.9813, 0.9898]: derived, and flagged unquotable in `knowledge/numbers.md`.
- The "invariant French gap +0.008708": retracted as circular (B-X-19).
- The "+0.00026 LB for adding bge": Ameya judged it too high (B-D-13).
- The B4–B8 expectations (0.99095–0.99107): the leaderboard said 0.990875.
