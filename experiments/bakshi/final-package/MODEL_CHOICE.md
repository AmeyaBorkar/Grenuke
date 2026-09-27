# Model choice for the final package

**Decision (bakshi, 2026-09-27 09:15 IST): `v7sq-dpc`.**
Package `2026-09-27-v7sq-s3-ops3a-dpc-c2`.

| file | expected sha256 |
|---|---|
| `matching_results.tsv` | `cdda9a2da0147c06039d83b673e26d8bfc71c5171915148c1dcd24979ea0e85c` |
| `candidate_pairs.tsv` | `55b766efbe7473e17985d06810d27f5d758951b1ce42832a0dd9081a76af5331` |

Hashes are from ameya, issue #45. **They are pre-registered here so the build is gated on them** — 
`make_package.py` refuses on a mismatch, so the archive cannot silently disagree with what is uploaded.

---

## The field, after v7ensall2 was withdrawn

v7ensall2 tied v7sq on expected LB (0.990299 vs 0.990295, a 0.000004 difference against a ~0.00005 noise
floor), so `AGENTS.md` §3's "ties go to the simpler option" applied, and its seven bagged stage-2 tags were
never recorded — which also means no reproduction script could be written for it. Withdrawn by ameya.

That leaves two real contenders:

| | v7sq-dpc | v7nst-dpc |
|---|---|---|
| holdout macro F0.5, s3 | **0.991246** | 0.991194 |
| US/India part | **0.843258** | 0.843210 |
| `fhs.py` net true copies vs v7nst, per 1000 French S1 | **+2.19** | +1.43 |
| cross-encoder mix | `cmq` = e5l + Qwen `qst` + e5ls + bge — **4 families** | `cem2` = e5l + e5l2 — 1 family, 2 checkpoints |
| covered by `reproduce.sh` | **yes, verified** | yes |

## Why v7sq-dpc

**1. It is not a tie — v7nst-dpc is dominated on every measured axis.** +0.000052 holdout, +0.000048 US/India
part, +0.76 on the France proxy. The v7ensall2 tie-break reasoning does not transfer here, because there is
no tie.

**2. Its advantage is in the dimension where our deficit actually is.** US/India is at its ceiling — the team
estimates ~0.0003 left, and the holdout differences between candidates sit inside the noise floor. Every
remaining point is French, and `fhs.py` is the only France-specific evidence we have that is not circular
(COPY pairs are not a population the rules override, unlike the rule-population AUC, which is saturated for
self-trained models at 0.9844/0.9857/0.9846). On that measure v7sq leads clearly: **+2.19 against +1.43.**

**3. Family diversity is the one mechanism established to help France.** §6.13 showed bge lifts the French
mean most despite being the weakest single model, because its French errors are decorrelated from e5's — and
my own round-3 work confirmed the France-optimal mixes all combine *different families* rather than reweight
one. v7sq has four families including a decoder (Qwen), so it is the most diverse mix built. v7s, its
precursor, was also the only variant that did not lose true copies against v7nst (`fhs` +0.02).

**4. Every component is gated, not assumed.** Qwen entered only after passing a predeclared gate — band AUC
0.9381 against a 0.93 threshold, and correlation with e5l 0.9433 against a ≤0.975 ceiling, i.e. it had to be
both accurate *and* diverse. The stacked `-dpc` rules gained +48.1e-6 on the holdout with **+23.7e-6 out of
sample under repeated 2-fold CV, positive in 86% of 42 splits**, against the control that tuning the flat
threshold instead gives −18.8e-6.

**5. It is reproducible today.** `VARIANT=v7sq` is verified in the switch and resolves to matches
`ameya-model-v7sq-s3-ops3a-dpc` against candidates `ameya-cands-v7sq-c2a`, with `STACK=1` running
`stack/stack.sh`. v7ensall2 could not have satisfied the reproduction deliverable at all.

## What this pick does NOT claim

**It will not reach first place.** Expected public LB is ≈0.990295 against a leader at 0.991483 — a gap of
about **0.00119, of which this pick closes roughly 9%**. Two independent readings say the rest is unreachable
today:

- **97% of v7sq-dpc's French predictions already sit at pc ≥ 0.99** (3.26 of 3.29 per S1), with only 0.034 per
  S1 between 0.70 and 0.95. There is almost no uncertain band left for a threshold or a rule to act on.
- If the leaders' US/India matches ours, their France F0.5 is ≈0.990 against our 0.981–0.982. That gap is
  **confident substitutions** — pairs our model is sure about and wrong about — which needs a better French
  model, not better post-processing.

So this is the best available model, not a route to the top. The honest goal is to bank ≈+0.00012 over the
measured 0.990179 and protect the floor.

## Fallbacks, in order

1. **`v7nst-dpc`** — matching `f349012516cdd239106cc88f53e4f5ccaf8b5531d30a9345e82f0584783494a2`, candidates
   unchanged from v7nst (`510a33ea…`, because the stack adds no candidates). Worth uploading as a
   *measurement* even though it is not the pick: its French predictions differ from v7sq-dpc's by ~20 per
   1000 S1, so the leaderboard difference isolates whether the new cross-encoders help France, with the
   stack held fixed. If it leads by more than ~0.00008 the final switches to it.
2. **`v7nst`** — the only candidate with a *measured* public score, 0.990179. Zip `4bd6c7a1…` is built and
   validated. This is the floor and it must never be lost.

## Conditions on this decision

- It is made on **holdout and label-free proxies**, since no stacked candidate has a public score yet. **A
  measured public score overrides all of it.** If v7sq-dpc comes back below 0.990179, the pick reverts to
  whatever is highest measured, and the last upload must be that file.
- The captain uploads. This is a recommendation with its reasoning, not an upload.
