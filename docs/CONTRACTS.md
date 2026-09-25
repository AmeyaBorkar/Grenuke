# Interface contracts

This is a shared file. Change it only through a dedicated PR reviewed by the coordinator and every affected stage owner.

These contracts are **plan-agnostic**. Every approach has records, candidates, scored pairs and matches. If each stage speaks these formats:
- members can build stages in parallel;
- we can combine components from different plans (for example, one plan's blocking with another's matcher);
- we can compare components on equal terms.

## C1. Entity IDs (`ber.ids`)

- **`eid` = `source * 1_000_000_000 + number`**, stored as int64.
  - Example: `S2-681193310` → `2_681_193_310`.
  - IDs are globally unique across sources, reversible (`ber.ids.to_entity_id`), and independent of row order.
- `source` is the prefix digit: 1, 2 or 3. Measured: every numeric part is below 1e9.
- Artifacts store `eid` values, never string IDs. Strings appear only when writing the final TSVs.

## C2. Shared holdout (`ber.eval.splits`)

- **`fold(eid)` = splitmix64(eid) mod 20.**
  - It is deterministic on every machine and independent of pandas, numpy or Python versions.
  - A test locks the value for known IDs.
- **Holdout = train S1 entities with `fold ∈ {0,1,2,3,4}`**, about 25% or roughly 550k entities. Their matched S2/S3 records go with them.
- The other 75% of train S1 can be used any way a plan likes: training, stacking splits, CV.
- Report **every** number on this holdout. Model selection and threshold tuning may use it too; at 550k entities the noise is about ±0.001.
- Blocking and search run over the **full** train S2/S3 pool, as in test. Never shrink the pool to the holdout.

## C3. Records (optional cache; plan-specific extensions allowed)

`work/records/<split>.parquet`, where `<split>` ∈ {`train`, `test`}. One row per record across S1, S2 and S3:

| column | dtype | notes |
|---|---|---|
| `eid` | int64 | C1 |
| `source` | int8 | 1, 2 or 3 |
| `country` | string | open set; never hard-code values |
| `name` | string | raw `business_name` |
| `address` | string | raw `business_address` (may be empty) |
| `n_*`, `a_*`, `f_*` | any | plan-specific normalized name, address and flag columns, documented by their producer |

## C4. Candidates (blocking output = matcher input)

`work/candidates/<tag>/<split>.parquet`:

| column | dtype | notes |
|---|---|---|
| `s1` | int64 | S1 eid |
| `r` | int64 | S2 or S3 eid, never S1 |
| (optional) `score_*`, `rank_*`, `view_*` | float32 / int16 / bool | retrieval metadata |

- `(s1, r)` pairs are unique.
- An S1 with no candidates simply has no rows.
- This exact set becomes `candidate_pairs.tsv`. It is what the matcher scores.
- **Blocking report** (required): pair recall and oracle F0.5 on the holdout, candidates per S1 (mean and p99), and runtime.

## C5. Scored pairs (matcher output)

`work/scores/<tag>/<split>.parquet`:

| column | dtype | notes |
|---|---|---|
| `s1` | int64 | |
| `r` | int64 | |
| `p` | float32 | **calibrated** probability that `(s1, r)` is a match, in [0, 1] |

Keep the same pairs as C4, or a documented subset. Because `p` is calibrated, scores from different models can be averaged or stacked, and any decision rule can run on top.

## C6. Final outputs (`ber.io`)

- `ber.io.write_matching(path, s1_order, pairs)` and `ber.io.write_candidates(path, s1_order, pairs)` write the exact organizer format:
  - tab-separated, UTF-8, with the organizer's header;
  - one row per S1 in `test_source1.tsv` order, with empty lists allowed;
  - no duplicate IDs; S2/S3 IDs only.
- The matching pairs must be a subset of the candidate pairs.
- Always check with `student_resource/utils/validate_submission.py`.

## C7. Result reporting

- Save a JSON next to your artifacts: `work/reports/<tag>.json`.
- Copy the headline numbers into your handover.
- Minimum keys:

```json
{
  "tag": "ameya-block-v1",
  "git_commit": "abc1234",
  "command": "python -m ber.pipeline --stage block --tag ...",
  "holdout": {"macro_f05": 0.0, "by_country": {"US": 0.0, "India": 0.0}, "singleton_f05": 0.0},
  "blocking": {"pair_recall": 0.0, "oracle_f05": 0.0, "cands_per_s1_mean": 0.0, "cands_per_s1_p99": 0},
  "runtime_s": 0,
  "notes": ""
}
```
