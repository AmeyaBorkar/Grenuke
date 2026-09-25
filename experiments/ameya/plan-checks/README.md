# Plan checks (25 Sep 2026)

These are the throwaway scripts behind the 25 Sep measurements tagged [M] in `plans/FINAL_PLAN.md` §1: facts #6–#10, #13 and #14. They settled the disagreements between Plan A and Plan B, and the handover `docs/handover/2026-09-25_1414_ameya_final-plan.md` has the results.

**The normalisation is crude on purpose:** ASCII folding, lowercase, alphanumeric tokens. The goal was to test the direction and rough size of each claim, not to build pipeline code. Re-measure with the real pipeline on the shared holdout before quoting any of these numbers as final.

| script | what it measures | runtime |
|---|---|---|
| `make_cache.py` | builds `data_cache/*.parquet` from the TSVs through `ber.io` (run once) | ~1 min |
| `plan_checks.py` | S2/S3 per S1 by country (train vs test); S1 name and address collisions; weak-name and weak-address shares; number agreement; postcodes; orphans; the look-alike signature (rare-token nearest S1) | ~4 min |
| `density_check.py` | how close S2/S3 records sit to their nearest S1, train vs test per country (which kind of distractor grew in test) | ~4 min |
| `ownerless_check.py` | the same profile for records whose S1 was dropped (what a drop-S1 stress test would create) | ~1.5 min |
| `nn_lib.py` | shared helpers (normalisation, rare-token nearest-S1 retrieval, closeness buckets) | — |

```
pip install -e code/business_entity_resolution
cd experiments/ameya/plan-checks
python make_cache.py
python plan_checks.py
python density_check.py
python ownerless_check.py
```

- `BER_DATA_DIR` sets where the raw TSVs are.
- `BER_CACHE_DIR` sets where the cache goes. The default is `<repo>/data_cache`, which is git-ignored.

**The retrieval proxy is weak.** The rare-token nearest S1 is the true owner for only about 49% of true pairs. So the look-alike shares are lower bounds, and only comparisons made with the same proxy are meaningful:
- orphans vs true pairs;
- train vs test for India. India's S1 pools are similar in size: 883k in train, 810k in test.
