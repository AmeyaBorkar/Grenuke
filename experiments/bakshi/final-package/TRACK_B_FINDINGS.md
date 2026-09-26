# Track B: family-balanced cross-encoder consensus — measured result

**Date (IST):** 2026-09-27, round 1 at ~02:00, **round 2 at ~02:30 after `out_bge` was recovered.**
**Author:** bakshi. **Branch:** `bakshi/opus-exec`.

## Conclusion (round 2 — supersedes round 1)

**The family-diversity hypothesis is correct and it is the largest French lever found.** Round 1 below
concluded Track B was closed; that was right about the artifacts then in hand and **wrong as a conclusion
about the hypothesis**. `out_bge` was recovered in the `grenuke-for-bakshi-v7ens2` delivery, and with it:

| cross-encoder input | French rule AUC | source |
|---|---|---|
| `out_cem2` = e5l + e5l2 (v7nst production) | 0.8062 | reproduced, §6.13 says 0.806 |
| `out_cem` = e5l + e5l2 + bge (v7mst input) | 0.8260 | reproduced, §6.13 says 0.826 |
| e5l + bge, equal (§6.13's best) | 0.8291 | reproduced, §6.13 says 0.829 |
| **e5l 0.6 / bge 0.4** | **0.8311** | **new — best found here** |

**The new point beats §6.13's best equal mean by +0.00201, 95% CI [+0.00147, +0.00252]** (cluster bootstrap
over 47,985 S1, 1,000 resamples, 100% favouring it), and beats `out_cem` — the mix v7mst actually uses — by
**+0.00509, CI [+0.00438, +0.00577]**.

**Recommendation: adopt 0.6/0.4 only if it is free.** If a v7s/v7sq stage-2 fit has not yet started, using
`--weight e5l=0.6 --weight bge=0.4` instead of an equal mean costs nothing and gains a little. **Do not rerun
a completed fit for it, and do not spend an upload slot on it.** Calibrating through the known hops
(CE +0.020 → stage-2 pc +0.0056 → France +0.0016 → LB +0.00024, i.e. LB ≈ CE gain × 0.012), +0.005 CE is
worth of order **+0.00006 LB** and +0.002 CE about +0.00002. Real, and far below what a leaderboard slot can
resolve. **The prize was adding bge at all (+0.020 CE ≈ +0.00025 LB); the weighting is a rounding error on
top of it.**

Caveat on selection: 0.6 is the argmax of a 6-point grid scored on the same proxy it is credited on, so the
CI does not correct for that. The curve is smooth and unimodal with an interior peak
(0.3→0.8138, 0.4→0.8232, 0.5→0.8291, **0.6→0.8311**, 0.7→0.8291, 0.8→0.8234), which is reassuring, but a
smooth peak is not a gate.

**Adding `e5l2` back at any weight never helps France.** Best three-way found was
e5l 0.50 / e5l2 0.15 / bge 0.35 at 0.8297, still below the two-way 0.8311 — so §6.13's conclusion that the
US/India-specialised second epoch should be left out of the French mean holds under weighting too, not just
under equal averaging.

Round 1's within-family finding was a correct signal of this: it measured that tilting away from `e5l2`
toward `e5l` helps France (+0.00086), which is exactly what the fuller experiment confirms. It simply could
not see the magnitude without an independent family to combine with.

---

## Round 1 (before `out_bge` was recovered) — kept for the record

**Conclusion at the time: Track B as designed cannot be run, and the fallback question it degenerates to has
no meaningful headroom.** Correct given the artifacts available at 02:00; superseded by round 2 above.

---

## 1. What arrived, and what that rules out

Delivered by ameya (`grenuke-for-bakshi-20260926T195414Z-1-001`, 201.4 MB, **all 13 files hash-verified
against the included `SHA256SUMS.txt`, 13 OK / 0 failed**):

| artifact | rows | note |
|---|---|---|
| `band_train.parquet` | 1,568,554 | `s1, r, row, p1, fold, y`; folds 0–4 = holdout (389,668), ≥5 = train (1,178,886) |
| `band_test.parquet` | 1,490,930 | matches the 452,178 US + 653,478 India + 385,274 France in RESEARCH_v6 §6.6 |
| `out_e5l/` | | e5-large, 1 epoch, seed 26. Band AUC OOF 0.93498, holdout 0.93908 |
| `out_e5l2/` | | e5-large, 2 epochs, seed 7. Band AUC OOF 0.94033, holdout 0.94408 |
| `out_cem2/` | | the production z-mean of the two |
| `rulepop_fr.parquet` | 128,856 | A 38,304 + ACR 14,884 + APP 11,652 = 64,840 true-copy, B 64,016 look-alike |
| `candidate_pairs.tsv` | 6,410,247 pairs | v7nst's paired candidate file, `510a33ea…` |

**`out_bge` and `out_q15` do not exist** — ameya confirms they are not on the integration machine, and the
spot box that would have produced BGE's logits was destroyed at 21:40 (RESEARCH_v6 §6.9).

That kills Track B's actual hypothesis. The point of family balancing was to stop two highly correlated
E5-large runs from numerically outvoting an **independent** model. With only `out_e5l` and `out_e5l2`
available there is no independent family: they correlate at **+0.9757** on the test band (measured here;
+0.986 was reported on the holdout band, and the lower test figure is consistent with France diverging).
`out_e5b` (e5-base) was not delivered either, and on France it is far weaker anyway (rule AUC 0.687), so
promoting it would be exactly the "a family that is inaccurate does not deserve a vote merely because it is
different" failure the plan warned against.

## 2. Alignment proof, before changing anything

`fam_blend.py build --family e5=out_e5l,out_e5l2 --weight e5=1 --z-rows all --verify-against out_cem2`

> train: bit-identical=**True**, max|diff| 0.000e+00
> test:  bit-identical=**True**, max|diff| 0.000e+00

The fitted moments also match `out_cem2/config.json` exactly (e5l mean −1.890309453 / sd 3.7405710220;
e5l2 mean −1.987168789 / sd 4.1104855537). So these copies and this tooling reproduce production exactly
before any experiment is run, and the config confirms production standardises on the **full** train band
(all 1,568,554 rows, holdout included), not on training folds only.

Two things this proof caught that would otherwise have silently corrupted the comparison:
- The builder originally computed in **float64** while `zmean_ce.py` uses **float32** — a 2.384e-07 gap, one
  float32 ULP, enough to make a "reproduction" fail for a reason unrelated to the experiment.
- Production's `--z-rows all` differs from the statistically cleaner `train_folds`. Mixing the two would have
  attributed a row-population difference to family weighting.

## 3. Screener validated against the published numbers

`fam_blend.py screen` on the 53,290 rule-population pairs that fall inside the band (true-copy share 0.576):

| run | French rule AUC, measured here | reported in issue #45 / §6.11 |
|---|---|---|
| `out_e5l` | 0.8026 | 0.803 |
| `out_e5l2` | 0.7919 | 0.792 |
| `out_cem2` (equal mean) | 0.8062 | 0.806 |

Exact agreement, so the screener is trustworthy for new arms.

**A correction to something I flagged earlier.** `ce_rule_auc.py`'s hand-written `auc()` ranks with
`np.argsort` and does not average tied scores, which is a real defect in principle. In practice it is
**immaterial on this data**: it agrees with `sklearn.metrics.roc_auc_score` to four decimals on every run,
including the raw logits where 77.5% of values are tied. Stable sorting plus row order that is uncorrelated
with the label makes the tie bias vanish in expectation. The repo's published numbers are not wrong.

## 4. The only question these artifacts can answer, and its answer

Without an independent family, the remaining live question is *within*-family: RESEARCH_v6 §6.5 recorded a
"z-scored 0.3 / 0.7 blend" of the two e5-large runs with a better **holdout band** AUC (0.9436) than the
equal mean (0.9429), but its **French** behaviour was never measured. Predeclared 5-point sweep, all with
production's `--z-rows all` so each arm is a drop-in replacement for `cem2`:

| weight on `e5l` (1 epoch) / `e5l2` (2 epochs) | French rule AUC |
|---|---|
| 1.0 / 0.0 | 0.8026 |
| **0.7 / 0.3** | **0.8071** |
| 0.6 / 0.4 | 0.8070 |
| 0.5 / 0.5 — **production `cem2`** | 0.8062 |
| 0.4 / 0.6 | 0.8047 |
| 0.3 / 0.7 | 0.8024 |
| 0.0 / 1.0 | 0.7919 |

The curve is smooth and peaks near 0.65–0.7 on the 1-epoch run. Direction agrees with the existing evidence
that the second epoch specialises on the training countries and costs France a little.

**Cluster bootstrap over S1** (47,985 S1, 1,000 resamples — S1 rather than pairs, because pairs sharing an S1
are correlated), 0.7/0.3 against production:

> observed **+0.00086**, mean +0.00086, **95% CI [+0.00037, +0.00136]**, 100% of resamples favour it.

So it is **statistically distinguishable from zero — and practically negligible.**

## 5. Why this is still a "no"

- **Magnitude.** +0.00086 CE-level AUC is about a quarter of the `e5l` → equal-mean step (+0.0036), and that
  larger step was only one part of a change worth roughly +0.003 implied France. Scaling crudely, this is
  worth order **+0.0001 public** — below the ~+0.00015 that separates us from rank 3, and plausibly
  invisible.
- **Selection.** 0.7/0.3 was chosen as the argmax of a sweep scored on the *same* proxy it is now being
  credited on. The bootstrap CI does not correct for that selection, so +0.00086 is an optimistic estimate of
  a quantity that is already small.
- **The proxy is not ground truth.** These are `post_ops` operation families, not French labels. And the
  effect would still have to survive stage 2 + self-training + stage 3 + the rules + the acronym join, every
  one of which compresses differences.
- **Cost.** Testing it properly needs `ce_import` plus a full self-trained stage-2 fit (~40 min, ~19 GB),
  then stage 3, decide, post_ops, acr_join, write — competing for the same RAM as `v7nst2` / `v7mst` / `v7s`,
  which are testing far larger hypotheses.

**Recommendation: close Track B.** Not "untested" — measured, bounded, and too small to buy. The production
equal mean sits within 0.0009 proxy AUC of the best weighting available from these two checkpoints.

**What would reopen it:** `out_bge` or a usable `out_q15`. An independent family is the whole premise; a
reweighting of two runs correlated at 0.976 was never going to be worth much, and now we know by how little.

## 6. Reproducing this

```bash
F=<delivered folder>;  E=experiments/bakshi/final-package
python $E/fam_blend.py build --band-train $F/band_train.parquet --band-test $F/band_test.parquet \
  --family e5=$F/out_e5l,$F/out_e5l2 --weight e5=1 --z-rows all --out /tmp/out_repro \
  --verify-against $F/out_cem2                      # must print REPRODUCED EXACTLY
python $E/fam_blend.py build --band-train $F/band_train.parquet --band-test $F/band_test.parquet \
  --family e5l=$F/out_e5l --family e5l2=$F/out_e5l2 --weight e5l=0.7 --weight e5l2=0.3 \
  --z-rows all --out /tmp/out_w07_03
python $E/fam_blend.py screen --band-test $F/band_test.parquet --rule-pop $F/rulepop_fr.parquet \
  $F/out_e5l $F/out_e5l2 $F/out_cem2 /tmp/out_w07_03
```
