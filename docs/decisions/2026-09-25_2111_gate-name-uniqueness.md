# Decision: gate-name-uniqueness

- **Date (IST):** 2026-09-25 21:15
- **Author:** sachi
- **Status:** rejected (below the gate bar)
- **Affects:** pair features (candidate for `ber.features`), stage 1/2

## Context

Error analysis of model v2 (dev fold 0): 61% of below-threshold misses and 98% of records taken by another S1 have an
empty address. Hypothesis: an exact name that no other S1 in the country shares is trustworthy even without an address.
Five features added to `ameya-fx2-dev` -> `sachi-fx2-name-dev` (`experiments/sachi/add_name_uniqueness.py`):
`ctx__s1_core_n`, `ctx__r_core_n` (S1 sharing the record's core name, same country, counted over all S1: no labels,
buildable on test), `name__core_eq`, `name__core_eq_unique`, `addr__r_empty`.

## Options considered

1. Stage 1 on the 79 v2 features (`sachi-s1-fx2-dev`): 0.97745.
2. Same + 5 name-uniqueness features (`sachi-s1-name-dev`): 0.97800.

## Decision

Not kept. Delta +0.00054, CI [+0.00001, +0.00107], p_better 0.975, n 27,651. Real but far below the +0.002 bar.

Why (`experiments/sachi/check_name_uniqueness.py`), true candidate pairs with an empty R address (3,779, 4.0%):
- exact + unique name (1,439): already found 95.8% -> 98.5%. Little headroom left.
- exact name shared by 2+ S1 (1,126): found 2.8% -> 1.6%. Ambiguous by construction: no address and several
  S1 with the same name. Abstaining is correct under F0.5.
- name not exact (1,214): 52.6% -> 52.1%. The only part with headroom (~0.6% of true pairs).

## Consequences (what changes, what we give up, how we'll know it was right)

- Empty-address losses are mostly a data limit, not a model gap. Do not spend more effort on them.
- G5 (softmax ownership) has low expected value: "taken by another S1" is 0.26% of true pairs, almost all the
  ambiguous empty-address records above.
- If stage 2 is retrained anyway, these 5 cheap columns could be offered; they do not justify a feature-stage change alone.
