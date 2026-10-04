# The decision layer (DEC)

**Summary.**
- The decision layer turns calibrated pair probabilities pc into the list for each S1. Each S1 gets the prefix of its candidates with the highest expected F0.5, computed exactly with a Poisson-binomial recursion. US and India use a logit shift +0.2, a crowd shift −0.3 and a phantom 0.01.
- The quoted gain, +0.000048 [+0.000007, +0.000091] over the best flat threshold, belongs to the combined layer (set selection + crowd shift + `acr` + `cap`). The set selection alone is +33.2e-6 [−7.5, +75.0] and not significant.
- Path key: `mv1/` = `experiments/ameya/model-v1/`, `stk/` = `experiments/ameya/model-v1/stack/`, `fpk/` = `experiments/bakshi/final-package/`. Evidence levels M, E, R, U as in [STANDARD §3](../STANDARD.md).

## 1. Purpose

Choose, per S1, which candidate records to list, so as to maximise expected macro F0.5. The metric punishes a wrong extra more than a miss, and an empty list scores 1.0 for a true singleton, so the choice cannot be one global threshold.

## 2. How it works

**Candidate cut** (`mv1/common.py:86-100`): a pair stays if p1 ≥ 0.02 and its S1 is among the record's top 2 S1 by p1 (ties go to the lower s1). It is an intersection, not a union (the methodology words it as a union, [CF-14]). Applied in `mv1/decide.py:172-181`, `mv1/stage3.py:166-169`, `stk/apply_hunt.py:60-73`, `stk/dp_france.py:57-67, 80-100`. Pairs outside get p = 0.

**Ownership** (`mv1/common.py:75-83`): each record is owned by its argmax-pc S1 inside the cut (ties go to the lower s1 eid); only owned pairs can be predicted, so a record never gets two owners. Later steps re-assert it (`stk/import_tag.py:17-18`, `stk/merge_dpc.py:24-25`, `stk/apply_hunt.py:179-182`, `fpk/audit_matching.py:17`). Ownership is computed over every S1, training folds included, so the holdout sees the same competition as test ([D-DEC-04], Sachi's fix). The methodology says each record is assigned after the selection; in code ownership comes first and the selection works on owned pairs only (same result).

**Calibration.** pc comes from stage 2 and stage 3, isotonic-calibrated on labelled rows only (v2 with legal forms: ECE 0.00046, Brier 0.010935 [M]). The selection is meaningful only on calibrated numbers: on raw stage-1 probabilities it loses to a threshold (Δ −0.00029 [−0.00040, −0.00018]) ([D-DEC-05]).

**`mv1/decide.py`, run after stage 2 and after stage 3 in every chain**
- Threshold rule: owned and p > t, t on a grid 0.30–0.95 in steps of 0.025, tuned on the holdout (`:194`).
- Expected-F0.5 rule (`:40-120`) with a global logit shift tuned on the holdout over {−1, −0.5, −0.25, 0, 0.25, 0.5, 1} (`:199`).
- Gate G6 (`:208-210`): paired bootstrap of the selection against the threshold on the holdout. The selection is used if Δ > 0 and the lower end of the interval is above 0; otherwise the threshold.
- As run: g1w's stage 3 chose the expected-F0.5 rule, the best flat threshold on record being 0.675, holdout 0.991323 [M]. v7sq7wg's stage 3 chose the threshold 0.725, holdout 0.991223 [M].

**The expected-F0.5 computation, exactly** (`mv1/decide.py:40-120`; the same code plus a phantom in `stk/core.py:73-158`)
1. q = sigmoid(logit(clip(pc, 1e-7, 1 − 1e-7)) + shift) (`:109-110`).
2. Per S1, sort candidates by q descending and keep at most `MAX_C = 48` with q ≥ `Q_MIN = 1e-3` (`:35-36, 50-55`). Owned and non-owned candidates are both kept: a non-owned one can still be a true match of this S1.
3. E[F_0] = P(no true match) = (1 − λ) · Π_j (1 − q_j). The phantom λ is 0 in `decide.py` and **0.01** in the stack (`stk/core.py:88`).
4. Candidate sets are prefixes of the owned candidates in q order, size k ≤ min(#owned, `MAX_K = 16`) (`:37, 60-65`). For each owned candidate i, for every prefix size k that contains it: E[F_k] += 1.25 · q_i · E[1 / (0.25 · (1 + S) + k)], where S is the number of true matches among the other candidates. S is Poisson-binomial over the q_j (j ≠ i), plus a Bernoulli(λ) phantom. Its pmf comes from the O(n²) recursion pmf[s] = pmf[s]·(1 − q_j) + pmf[s − 1]·q_j (`:74-91`; phantom `stk/core.py:117-121`).
5. The chosen size is the argmax over k of E[F_k], with a strict ">", so ties go to the smaller set. The first k owned candidates of that size are predicted (`:93-104`).

**Why it is exact.** With |P| = k fixed, F0.5 = 1.25 · |P ∩ T| / (0.25 · |T| + k). So E[F_k] is a sum over i in P of P(i ∈ T) times E[1.25 / (0.25 · |T| + k) given i ∈ T], and given i ∈ T, |T| = 1 + S under independence. Singletons are scored correctly: E[F_0] is P(T empty), and any non-empty prediction needs some i ∈ T. The phantom stands for true matches outside the candidate list; without it |T| ignores them.

**Complexity.** Per S1, O(K · n²) for the pmfs plus O(K² · n) for the sums, with n ≤ 48 and K ≤ 16 (about 50k operations at most). Numba-parallel over S1 groups after one O(P log P) sort. Linear in the number of S1.

**The stacked decision for countries with labels** (`stk/apply_combo.py`, run inside `stk/stack.sh:34-36`)
- q = sigmoid(logit(pc) + **0.2** − **0.3** · [the record has ≥ 4 S1 with p1 ≥ 0.02, counted before the top-2 cut]), phantom **0.01** (`:51-56, 80-86`; crowd count `stk/apply_hunt.py:70`).
- Then the hunt's `acr` and `cap` rules, restricted to those countries, with THR = 0 so every selected pair counts as a model prediction for `cap` (`:95-101`). Details in [rules.md](rules.md).
- This replaces the `decide.py` output for US/India in the `-dpc` tag; France comes from the narrowed path (`stk/merge_dpc.py:16-25`).
- Selection discipline: shift and phantom chosen on v7nst's half A and confirmed on half B (+45.5e-6); crowd shift chosen from {0.15, 0.3, 0.45} on v7s's half A and confirmed on half B [M].

**France.** `stk/dp_france.py` runs the same selection on French stage-3 pc with the same constants (`SHIFT, CROWD, PHANTOM, P_CAND, TOP_R = 0.2, 0.3, 0.01, 0.02, 2`, `:45`) and the rule-layer guards described in [france.md](france.md).

## 3. Why this design

- **Per-S1 expected F0.5, gated against a threshold:** [D-DEC-01]. In count form one false merge weighs as much as four missed copies, so the bar for adding a pair rises with set size; one threshold cannot say that.
- **Argmax ownership;** the softmax with a "none" option (gate G5) never ran: [D-DEC-02]. "Taken by another S1" is only 0.26% of true pairs.
- **The gate decides per model:** [D-DEC-03], [D-DEC-05], [D-DEC-08]. Calibrated stage-2 probabilities make the selection work; raw stage-1 ones do not.
- **The stack:** [D-DEC-15]. For an S1 whose chosen pairs are certain, the k-th pair helps only if q is above the break-even, so a flat 0.70 is too strict for the first pair and too loose from the third. Crowded records are overconfident, hence the crowd shift. [D-RUL-11] stacks it on every final candidate; `nsa` was replaced by the crowd shift ([D-RUL-09]).
- **France gets its own selection** only after the first version was kept on a flat threshold for lack of labels ([D-DEC-16], then [D-DEC-18]).

## 4. Alternatives and why not

- **Richer tuned rules** (top/rest thresholds, by set size): +0.00024 and +0.00022 on untouched folds, the same as the untuned selection, which needs no tuning ([D-DEC-06]).
- **A separate "no match" model:** capped at +0.0001 to +0.0003 because P0 is already calibrated (0.0563 against 0.0558) ([D-DEC-07]).
- **Duplicate completion, tie renormalisation, copy-count tie-breaking, empty-S1 rescue:** all lost or tied ([D-DEC-09], [D-DEC-11], [D-DEC-12], [D-DEC-13]; the rescue's best rule was +0.000021 [−0.000008, +0.000049]).
- **Stricter France threshold:** the curve is flat with the label-free look-alike odds ([D-DEC-10]).
- **Consensus filter, India-only count prior, a French cross-encoder veto:** rejected ([D-DEC-17], [D-DEC-19], [D-FRA-21]).
- **A more inclusive France selection** (shift 0.5 or 0.8): the 1,008 added pairs have mean truth 0.756, right at break-even, so about −2.5e-6 [E] ([D-DEC-20]).

## 5. Numbers

**Gain of the layer**, local holdout, model v7s, paired bootstrap [M]:

| variant | gain over the best flat threshold (0.70) |
|---|---|
| set selection alone (shift +0.2, phantom 0.01) | +33.2e-6 [−7.5, +75.0], P 0.945; halves disagree |
| plus `acr` and `cap` | +35.9e-6 [−4.8, +77.6] |
| plus the crowd shift −0.3 (the combined layer) | **+48.1e-6 [+7.1, +91.2]**, P 0.987; half A +7.7, half B +108.7; US +70.8, India +13.9 |
| out of sample, repeated 2-fold CV on v7nst, 42 splits | selection with phantom +23.7e-6, positive in 86%; re-tuning the flat threshold the same way −18.8e-6, positive in 0% |

The leaderboard share of the stack: +0.000085 (v7nst 0.990179 → v7nst-dpc 0.990264) [M]. On v7sq3 the combination added +57e-6 (0.991250 → 0.991307) [M].

**Break-even probabilities** (F0.5 arithmetic, earlier picks certain) [E]:

| the pair is the | 1st (only) | 2nd | 3rd | 4th | limit |
|---|---|---|---|---|---|
| it pays if true with probability above | 0.500 | 0.727 | 0.759 | 0.771 | 0.8 |

The formula is (5(k−1)+1) / (6.25(k−1)+2). "About 75%" is the round figure; do not say "exactly". A drop pays if more than about 25% of the dropped pairs are false. For an S1 with 4 true copies and a perfect list a wrong addition costs 0.167 and a missed copy 0.0625, a ratio of 2.7 ([numbers.md](../numbers.md), "Numbers not to quote" 3 and 15).

**G6 by model** (selection minus best threshold, local holdout) [M]: stage 1 −0.00029; stage 2 v1 +0.00027, v2 +0.00018, v3 +0.00011 [+0.00005, +0.00017], v4 +0.00006; v6all +0.00004 [−0.00001, +0.00008] so threshold kept; v7ce3 +0.00005 [+0.00001, +0.00009]; v7mst +0.00003 [−0.00002, +0.00007]. The verdict depends on the model ([CF-50]).

**What it predicts.** The selection converges to the same density from any model: 3.389 (US) and 3.376 (India) per S1 on v7s, v7sb and v7nst [M]. Composite B: 3.3776 per S1 and 99,802 empty S1 (5.76%; the truth is 5.58%) [M].

## 6. Failure modes and limits

- **Independence.** The recursion treats an S1's candidates as independent. Matches within an S1 are not, and most probabilities sit near 0 or 1, which erodes the edge ([D-DEC-05]).
- **Not significant alone.** The set selection by itself is a tie on v6all and v7mst ([D-DEC-08], [D-DEC-14]). We keep it because it is principled, needs no tuned parameters, and wins out of sample; we do not claim a significant gain from it alone ([CF-16]).
- **The submitted rows were not re-measured.** 0.991323 is `decide.py`'s stage-3 decision on g1w. `apply_combo` writes test output only, and its gain was measured on v7s ([CF-17]).
- **Fixed constants.** Shift, crowd shift and phantom were tuned on v7nst and v7s halves; the phantom 0.01 is an estimate of out-of-list matches.
- **France is overconfident.** About 97% of French predictions have stage-3 pc ≥ 0.99, so the selection only acts at the margin and its value is an estimate [E].
- **Cut loses recall.** The top-2 and p1 ≥ 0.02 cut keeps 98.35% of true holdout pairs; the rest cannot be recovered here (see [blocking.md](blocking.md)).
- **Stage 3 is not bit-reproducible:** about 500 decisions move between machines.

## 7. Scale

The selection is linear in the number of S1 and constant per S1 (at most about 50k operations), and it is embarrassingly parallel by S1. At 100× or 1000× the data it stays negligible next to the model stages. The global steps are the sort and the per-record argmax for ownership (one group-by on the record, which can be sharded by record). `decide.py` peaked at 9.8 GB on the test set [M]; at 100× the pair table would be sharded by S1 hash, with ownership resolved first. See [theory 11](../theory/11-scaling-to-billions.md).

## 8. Theory links

[04 metrics and decisions](../theory/04-metrics-and-decisions.md), [07 calibration](../theory/07-calibration.md), [05 evaluation methodology](../theory/05-evaluation-methodology.md), foundations [F04](../theory/foundations/F04-classification-metrics.md), [F11](../theory/foundations/F11-decision-theory-and-optimisation.md), [F02](../theory/foundations/F02-probability-and-statistics.md). Neighbours: [rules.md](rules.md), [france.md](france.md), [model-stages.md](model-stages.md), [evaluation.md](evaluation.md).

## 9. Likely questions

- **Why not just a threshold?** F0.5 charges one wrong extra as much as four misses, so the bar rises from 0.50 for a lone candidate to 0.77 for a fourth. The selection encodes that. On calibrated models it beat the best threshold in most gates, but on v7s alone it is a tie.
- **What is the +0.000048?** The whole layer: selection, crowd shift, `acr` and `cap`. The selection alone is +0.000033 and not significant. Out of sample it gives +0.000024 while re-tuning the threshold loses 0.000019.
- **Why a phantom?** Candidates are a cut. A phantom of 0.01 says there may be a true match we did not retrieve, which makes an empty prediction less attractive.
- **Why a crowd shift?** A record that four or more S1 compete for is overconfident: on such records, pairs with pc up to 0.75 are only 65–68% true [M].
- **Is it exact?** Under independence, yes; the sets are prefixes of owned candidates by q, k ≤ 16, n ≤ 48.
- **Does it scale?** Linear in S1; the DP is not the bottleneck.
- **Which numbers are measured?** Holdout deltas are M. France values are E: there are no French labels.

[CF-14]: ../conflicts.md
[CF-16]: ../conflicts.md
[CF-17]: ../conflicts.md
[CF-50]: ../conflicts.md
[D-DEC-01]: ../decisions/DEC.md
[D-DEC-02]: ../decisions/DEC.md
[D-DEC-03]: ../decisions/DEC.md
[D-DEC-04]: ../decisions/DEC.md
[D-DEC-05]: ../decisions/DEC.md
[D-DEC-06]: ../decisions/DEC.md
[D-DEC-07]: ../decisions/DEC.md
[D-DEC-08]: ../decisions/DEC.md
[D-DEC-09]: ../decisions/DEC.md
[D-DEC-10]: ../decisions/DEC.md
[D-DEC-11]: ../decisions/DEC.md
[D-DEC-12]: ../decisions/DEC.md
[D-DEC-13]: ../decisions/DEC.md
[D-DEC-14]: ../decisions/DEC.md
[D-DEC-15]: ../decisions/DEC.md
[D-DEC-16]: ../decisions/DEC.md
[D-DEC-17]: ../decisions/DEC.md
[D-DEC-18]: ../decisions/DEC.md
[D-DEC-19]: ../decisions/DEC.md
[D-DEC-20]: ../decisions/DEC.md
[D-FRA-21]: ../decisions/FRA.md
[D-RUL-09]: ../decisions/RUL.md
[D-RUL-11]: ../decisions/RUL.md
