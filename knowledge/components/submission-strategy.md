# Submission strategy (SUB)

**Summary.**
- We made 13 scored uploads over three days, from 0.97608 to 0.990879 on the public leaderboard (+0.014799). Each upload was designed to isolate one change; France was measured by composing files so that US/India stayed byte-identical.
- The package is Composite B (0.990879). The last portal upload was B7 (0.990875), a France-only variant that tied it. The organisers publish rankings only: we placed 2nd of the Top 10, there is no private score, and which upload the private ranking used is unknown.
- Path key: `box/` = `experiments/bakshi/box/`. Public-LB records are in `submissions/records/`. Evidence levels as in [STANDARD §3](../STANDARD.md).

## 1. Purpose

Spend a limited number of public-leaderboard uploads so that each one answers a question, never tune many knobs on the leaderboard, and end with the best expected file. The public leaderboard is a subset of test with noise of about ±0.00004 between near-identical candidates.

## 2. How it works

**The budget and the policy** ([D-SUB-01]): the protocol allowed 5 uploads a day and 15 in all; the records show 13 scored uploads (2 on 25 Sep, 4 on 26 Sep, 7 on 27 Sep). The plan: about 10–11 uploads with one slot a day in reserve; the leaderboard is a sanity check, "never tune several knobs on the public leaderboard", decisions come from the 550k-entity holdout; every upload gets a record, a tag and a changelog row; the last upload is the chosen model. The real quota and the real close time are in no source ([CF-04], [CF-05]); uploads were accepted until about 23:40 on 27 Sep.

**Controls.** Pairs of uploads change one thing: v7nst-dpc against v7nst is the stack (+0.000085); v7sq-dpc against v7nst-dpc is the model (+0.000281) ([D-SUB-15]). The score formula LB = 0.38274·F_US + 0.46751·F_India + 0.14975·F_France [E] lets a composite isolate France: keep the US/India rows and read the difference ([D-SUB-16]).

**Composition** (`box/compose_tsv.py`)
- Countries with labels are the unique countries of `train_source1.tsv` (`:53-55`); the test S1 set must be identical in both inputs (`:69`).
- For each test S1, both the matching row and the candidate row come from one source: labelled countries from `--labelled` (g1w), the others from `--unlabelled` (the France block) (`:66-74`).
- Drop list: all `fr_scored` and `usin_scored` parquet files filtered to `q7__logit < −6` and `p1 > 0.99` (`:59-64`); drops remove ids from matching rows only (`:75-82`).
- Because records never cross countries, one owner per record and matches inside the candidates hold by construction; `audit_matching.py` re-checks both. Output is a pandas TSV with `\n` line ends (`:83-84`).

**Composite B, measured** [M]: drop list 1,169 pairs, 1,150 present and dropped (840 France, 310 US/India); 5,851,832 predicted pairs; 99,802 S1 left empty; 3.3776 per S1; France 870,307, India 2,734,227, US 2,247,298; audit: 0 records with two owners, 0 cross-country pairs, 0 matches outside the 6,410,308 candidates. Public LB 0.990879, +0.000180 over mixmdp (0.990699).

**Every scored upload**

| date and slot | file | public LB | note |
|---|---|---|---|
| 25 Sep | v2 | 0.97608 | holdout 0.98436 |
| 25 Sep | v3 | 0.97961 | +0.0035 |
| 26 Sep #01 | v5all, rules v2, the cut | 0.98781 | rank 15 [LB](../../submissions/records/2026-09-26_sub01.md) |
| 26 Sep #02 | v6all, stage 3, rules v3, acronym join | 0.988609 | rank 15 |
| 26 Sep #03 | v7n | 0.989721 | rank 8; predicted 0.9894–0.9900, hit |
| 26 Sep #04 | v7nst (self-training) | 0.990179 | rank 7 |
| 27 Sep #01 | v7nst-dpc | 0.990264 | the stack, +0.000085 |
| 27 Sep #02 | v7sq-dpc | 0.990545 | rank 7; +0.000281 |
| 27 Sep #03 | mixmdp | 0.990699 | rank 12; +0.000154 |
| 27 Sep #04 | **Composite B** | **0.990879** | team's best; +0.000180; predicted +0.000149 |
| 27 Sep #05 | mixf7 | 0.990833 | B with round-3 France, −0.000046 |
| 27 Sep #06 | mixf2 | 0.990819 | US from v7sq3, −0.000014 against mixf7 |
| 27 Sep #07 | B7 | 0.990875 | last upload about 23:40, −0.000004 against B |

Sources: [LB 26 Sep #03](../../submissions/records/2026-09-26_sub03.md), [LB 27 Sep #04](../../submissions/records/2026-09-27_sub04.md), [LB 27 Sep #07](../../submissions/records/2026-09-27_sub07.md) and the other records in the same folder. Whether the baseline and model v1 were uploaded on 25 Sep is not recorded ([CF-08]). Packaged and validated but never uploaded: B+, mixf4, mixf3, mixf6, mixfq, mixbp4, mixbp5, the France-empty and France-threshold probes and others.

**The path to the final choice**
1. 27 Sep morning: v7sq-dpc over a bag of seven models, because ties go to the simpler and it reproduces from fewer runs ([D-SUB-14]).
2. Hold uploads for the best package: mixmdp ([D-SUB-20]), with US/India from v7sq3 ([D-SUB-18]).
3. After the 7B: at about 20:46 the teammates proposed Composite B instead of mixf2; Ameya made it a probe with a pre-set rule (B at 0.99078 or more: upload mixf2 next; below: mixf6) ([D-SUB-23]). B scored 0.990879, so the next uploads were one-change follow-ups, mixf7 and mixf2 ([D-SUB-24]).
4. No switch away from B: the estimates for mixfq (+20e-6 nominal, about −33e-6 bias-corrected), a more inclusive France selection and others were not trusted ([D-SUB-25], [D-FRA-26]).
5. The last slot: B7, which extends the French drop toward −2 where Qwen3-4B agrees (+251 / −1,699 French pairs against B). B+ was the safe pick, B7 tested whether the drop keeps paying; it tied ([D-SUB-26]).
6. The ZIP carries Composite B, because B7 only ties and needs the Qwen3-4B step ([D-PKG-10]).

**The honest status of the last upload.** The plan said the last upload is the model to be ranked; the portal text was read both ways ("final upload counts" and "best score counts"). We planned for both: B and B7 differ by 0.000004, inside the noise, so the public standing is the same either way. Which upload the private ranking used is unknown, and so is why a public rank of 16 at upload became 2nd ([CF-01], [CF-03], [CF-10]).

## 3. Why this design

- A validated file early, to test the upload itself: [D-SUB-02]. Take verifiable ideas from other plans: [D-SUB-04].
- The candidate or the best file, never a probe, in the last slots: [D-SUB-09], [D-SUB-11], [D-SUB-12] ("5 slots, no pure probes, one change per upload, the best last"). Broken on purpose in the evening, with a pre-set rule ([D-SUB-22], [D-SUB-23]).
- Compose per country and measure France alone: [D-SUB-16]. US/India have a reliable judge (the holdout, 85% of the LB weight); France does not.
- Reject consensus editing and screen candidates by change footprint: [D-SUB-17]. Every candidate agrees with the base on 99.92–99.97% of predictions; consensus editing could reach about +0.000048; to gain +0.000455 a candidate must change about 28 French predictions per 1000 S1 [E].
- Say that 0.993 and 0.992 are out of reach: [D-SUB-19]. +0.0025 was needed against about +0.0001 from every verified gain; a perfect France would add only +0.0025.
- Deadline planning for a 21:00 close, with one person uploading and the last upload being the model to be ranked: [D-SUB-05]. The recommended v4 was never uploaded, and the plan moved on to v5all and v6all: [D-SUB-07], [D-SUB-08].

## 4. Alternatives and why not

- **Probes** (France-empty, threshold cuts, a stricter DP at shift −0.5): `fr0` scores about 0.85 and means nothing without its pair; `fr090` "is a coin flip in expectation"; they never went up ([D-SUB-03], [D-SUB-09], [D-FRA-12]).
- **The bag of seven models:** the lead was not significant (+4.6e-6 [−10.6, +21.1]) and the inputs were never recorded ([D-SUB-14], [D-SUB-18]).
- **mixf2 as the single evening upload:** replaced by B as a probe, which hedged mixf2's one unverified part, the round-3 France ([D-SUB-22]). Round 3 then lost 46e-6.
- **B+ instead of B7:** the agent's safe pick; Bakshi wanted the drop test. Unresolved, B7 uploaded ([D-SUB-26]).
- **A France-only model upload** (`fr-v7sq4`, US/India byte-identical): planned in [D-SUB-12]; composition ([D-SUB-16]) generalised it.

## 5. Numbers

| fact | value | scope | level |
|---|---|---|---|
| Whole climb | 0.97608 (first recorded) → 0.990879 (best) = +0.014799 | public LB | M |
| Largest steps | v6all → v7n +0.001112; v5all → v6all +0.000799 (a bundle); v7nst +0.000458; v7sq +0.000281; B +0.000180; mixmdp +0.000154; the stack +0.000085 | public LB | M |
| Forecast against result | v7n predicted 0.9894–0.9900, got 0.989721; mixmdp predicted +0.000234, got +0.000154; B predicted +0.000149, got +0.000180; mixf7 `cal` +69e-6, got −46e-6 | public LB | E/M |
| Noise | ±0.00004–0.00005 between near-identical candidates; for a 25% public split the SD of the score is 0.000164 (simulated on the holdout) | public LB | E |
| Final standing | Top 10 of 32,000+ teams, 2nd (organisers' e-mail, relayed by Ameya); public rank 16 at the upload of B | private LB | R |
| Output files | matching 97,854,781 bytes, candidates 105,028,761 bytes, shipped verbatim | Composite B | M |

## 6. Failure modes and limits

- **The public LB is a subset.** A change of ±0.00004 cannot be resolved; most late candidates were within it.
- **The estimators misled twice.** `s2` had the wrong sign on every pair; `cal` missed round 3 by about 115e-6 ([D-FRA-26]).
- **Process, not model, risk.** The plan changed through the evening (mixf2 at 20:14, B as a probe at 20:48, mixf7 and mixf2 at 21:55, B+ at 23:22, B7 at 23:40) ([CF-02], [CF-06]); the record for the B decision is only in the chat.
- **Open facts:** which upload counts, the real close time, the real quota, who clicked upload for B7, and the total rental cost ([CF-01], [CF-03]–[CF-05], [CF-07], [CF-12]).
- **Later rank is not ours to explain.** Other teams improved and the final ranking is private ([CF-10]).
- **Forecasts are not results.** Only uploaded scores may be quoted ([numbers.md](../numbers.md), "Numbers not to quote" 19).

## 7. Scale

The budget is fixed by the organisers, so scale changes the cost per upload, not the count. Output files grow linearly (about 203 MB for 1.73M S1), so 100× would be about 20 GB and need streamed writes and audits. The compose-by-country design scales with the number of countries, and the audit is one pass per file. At 1000× the data a full rerun per candidate would dominate, so label-free estimators and change-footprint screens would carry more of the weight, with the caveats above.

## 8. Theory links

[05 evaluation methodology](../theory/05-evaluation-methodology.md), [04 metrics and decisions](../theory/04-metrics-and-decisions.md), foundations [F09](../theory/foundations/F09-experiments-and-evidence.md), [F12](../theory/foundations/F12-interpreting-our-results.md), [F02](../theory/foundations/F02-probability-and-statistics.md). Neighbours: [evaluation.md](evaluation.md), [packaging.md](packaging.md), [timeline](../timeline.md).

## 9. Likely questions

- **Which upload did the private ranking use?** We do not know. Our package is Composite B; the last upload was B7; they differ by 0.000004 publicly. The organisers publish rankings only.
- **Why was B7 last and not B?** B7 tested whether the French drop keeps paying below −6. It tied, so the ZIP carries B, which is simpler to reproduce.
- **How did a public rank of 16 become 2nd?** We do not know; the final ranking is private and the public board moved fast.
- **Did you overfit the public leaderboard?** We tuned on the 550k-entity holdout, used the leaderboard for controlled comparisons, and kept differences within noise out of decisions.
- **How did you measure France?** We never did directly. We composed files so only France changed, and read the difference.
- **How many uploads?** 13 scored: 2, 4 and 7 on the three days. Our plan assumed 5 a day; the portal accepted all.
- **What would you do differently?** Upload the France-empty probe once, early, to pin the level down.

[CF-01]: ../conflicts.md
[CF-02]: ../conflicts.md
[CF-03]: ../conflicts.md
[CF-04]: ../conflicts.md
[CF-05]: ../conflicts.md
[CF-06]: ../conflicts.md
[CF-07]: ../conflicts.md
[CF-08]: ../conflicts.md
[CF-10]: ../conflicts.md
[CF-12]: ../conflicts.md
[D-FRA-12]: ../decisions/FRA.md
[D-FRA-26]: ../decisions/FRA.md
[D-PKG-10]: ../decisions/PKG.md
[D-SUB-01]: ../decisions/SUB.md
[D-SUB-02]: ../decisions/SUB.md
[D-SUB-03]: ../decisions/SUB.md
[D-SUB-04]: ../decisions/SUB.md
[D-SUB-05]: ../decisions/SUB.md
[D-SUB-07]: ../decisions/SUB.md
[D-SUB-08]: ../decisions/SUB.md
[D-SUB-09]: ../decisions/SUB.md
[D-SUB-11]: ../decisions/SUB.md
[D-SUB-12]: ../decisions/SUB.md
[D-SUB-14]: ../decisions/SUB.md
[D-SUB-15]: ../decisions/SUB.md
[D-SUB-16]: ../decisions/SUB.md
[D-SUB-17]: ../decisions/SUB.md
[D-SUB-18]: ../decisions/SUB.md
[D-SUB-19]: ../decisions/SUB.md
[D-SUB-20]: ../decisions/SUB.md
[D-SUB-22]: ../decisions/SUB.md
[D-SUB-23]: ../decisions/SUB.md
[D-SUB-24]: ../decisions/SUB.md
[D-SUB-25]: ../decisions/SUB.md
[D-SUB-26]: ../decisions/SUB.md
