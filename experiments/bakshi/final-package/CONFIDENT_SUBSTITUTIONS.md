# Is the French "confident substitution" population findable? No.

**Date:** 2026-09-27 09:30 IST. **Tool:** `confident_disagree.py`. **Artifacts:** cached logits only, no GPU.

**Conclusion: the population is large enough to matter — and cross-encoder disagreement, the only signal we
have that could find it, fires twice as often on pairs we know are TRUE. It is anti-selective. Do not build a
drop rule on it.**

---

## Why this was worth testing

§6.16 and issue #45 establish that 97% of v7sq-dpc's final French predictions sit at pc ≥ 0.99, so the
remaining French loss is pairs the model is **confident about and wrong about**. No threshold and no rule can
reach those — by construction, they are nowhere near a threshold.

The natural candidate signal is cross-encoder disagreement: on France the encoders disagree about 4× as often
as on US/India (§6.6), and bge is a different family whose French errors are decorrelated from e5's. So among
pairs the model *kept*, does bge voting against identify the wrong ones?

Two things make that answerable with no labels:

1. **US/India calibrates the background.** Their final predictions are ~99.8% precise, so their disagreement
   rate is what disagreement looks like among pairs that are almost all correct.
2. **The rule populations give a direct false-alarm rate.** Final French predictions inside the A/APP/ACR
   populations are known-true. If the signal fires on those, it is not selective.

## Coverage first

Only **5.5% of final predictions lie inside the cross-encoder band** (stage-1 p1 in [0.02, 0.99]) — France
9.2%, India 5.5%, US 4.0%. The other 94.5% were already certain at stage 1 and have no cross-encoder logit at
all. Everything below is the band subset.

## The population is real, and big enough to matter

Among pairs the model kept, rate at which bge votes against while the e5 runs agree:

| country | kept in band | bge < 0 | **bge < 0 while e5 > 0** | bge in low 10% |
|---|---|---|---|---|
| France | 80,036 | 29.87% | **12.17%** | 21.92% |
| India | 151,589 | 7.55% | **1.44%** | 3.43% |
| US | 88,845 | 20.80% | **2.63%** | 10.47% |

- Background (US/India mean): **2.04%**. France: **12.17%**. Excess: **+10.13%**.
- That is **8,111 suspect French pairs** of 80,036 kept in band.

**And the arithmetic is tantalising.** +0.0008 LB needs about 1,386 S1 worth of summed F0.5. Dropping a false
positive gains ≈0.18, so 8,111 pairs are worth **up to +0.000843 LB if every one of them is wrong** — almost
exactly the gap to the leaders. This is why the idea is tempting, and why it needed testing rather than
dismissing.

## But the signal is anti-selective

Of the **30,413** final French kept pairs that carry a **known-true** rule-population label,
**17.76% show the flip signal.**

That is *higher* than the 12.17% rate across all French kept pairs. Working out the complement: the 49,623
pairs of unknown truth flip at **8.74%**, while the known-true pairs flip at **17.76%**.

**The signal fires twice as often on pairs we know are true.** It is not merely unselective — as a drop
criterion it is worse than random, because it preferentially discards true copies.

## Why, mechanically

bge is the **weakest single model on France** (French rule AUC 0.774, against e5l's 0.803 — §6.13), and it is
systematically more conservative there: its share of positive logits on France is 29.9% against e5l's 36.9%
(`ce_diag.py`). So "bge < 0" on a French pair is largely bge's own scale and weakness on French text, not
evidence about that pair.

This is entirely consistent with §6.13's central finding: bge lifts the *mean* the most while being the worst
alone. Its value is in aggregate, where its decorrelated errors average out. **Its individual votes are not
trustworthy, and a drop rule uses exactly those individual votes.**

## What this settles

The last plausible route to the leaders' France level is closed, with numbers rather than by assertion:

- the population that would need fixing **exists and is roughly the right size** (~8,100 pairs, ~+0.00084 if
  perfectly identified);
- the only available signal for finding it is **anti-correlated with wrongness**;
- and 94.5% of final predictions are outside the band entirely, so even a good signal would only ever see a
  twentieth of the output.

So the remaining French gap needs **a better French model**, not better post-processing — which is what
§6.16 concluded qualitatively and this now supports quantitatively. There is no time to train one today.

**Recommendation unchanged: ship `v7sq-dpc`, bank the ≈+0.00012, protect the 0.990179 floor.**

## Reproducing

```bash
python experiments/bakshi/final-package/confident_disagree.py \
  --matching <final matching_results.tsv> --s1-tsv "$BER_DATA_DIR/test/test_source1.tsv" \
  --band-test band_test.parquet --rule-pop rulepop_fr.parquet \
  --run e5l=out_e5l --run e5l2=out_e5l2 --run bge=out_bge
```

Run above on v7nst's final output, the measured model. Re-running it on v7sq-dpc's output would be a fair
check of whether its more diverse mix narrows the France/US-India disagreement gap — worth doing when those
files arrive, as a diagnostic, but it cannot change the anti-selectivity result.
