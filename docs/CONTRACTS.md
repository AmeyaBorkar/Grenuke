# Interface contracts

This is a shared file. Change it only through a dedicated PR reviewed by the coordinator and every affected stage owner.

These contracts let the stages be built in parallel and swapped independently:
- each stage reads the previous stage's artifact **by tag** and writes its own;
- anyone can re-run, replace or A/B-test one stage without touching the others;
- components from different people compare on equal terms.

The stages and their order are in `plans/FINAL_PLAN.md` §3.

**v1 (25 Sep)** adds the plan-specific details: stacking folds, normalized columns, candidate metadata, stage-1 scores, and three new contracts (features, matches, gate records).

## C0. Tags and artifact paths

- **Artifact path:** `work/<stage>/<tag>/<split>.parquet`, where `<split>` ∈ {`train`, `test`}. The stage directories are `norm`, `candidates`, `features`, `scores`, `matches`, `models`, `reports`.
- **Tag format:** `<member>-<stage>-v<N>[-<variant>]`, for example `ameya-block-v0` or `sachi-model-v1-dp`.
  - Never reuse a tag for different content, and never write into someone else's tag.
- **Metadata:** every Parquet artifact carries the git commit, the command, the creation time (IST) and the input tags (`ber.artifacts`).
- **Sharing:** artifacts shared through the team drive keep the same relative path and include a `MANIFEST.txt` with sha256 hashes (CONTRIBUTING §7).

## C1. Entity IDs (`ber.ids`)

- **`eid` = `source * 1_000_000_000 + number`**, stored as int64.
  - Example: `S2-681193310` → `2_681_193_310`.
  - IDs are globally unique across sources, reversible (`ber.ids.to_entity_id`), and independent of row order.
- `source` is the prefix digit: 1, 2 or 3. Measured: every numeric part is below 1e9.
- Artifacts store `eid` values, never string IDs. Strings appear only when writing the final TSVs.

## C2. Shared holdout, training folds, OOF groups (`ber.eval.splits`)

- **`fold(eid)` = splitmix64(eid) mod 20.**
  - It is deterministic on every machine and independent of pandas, numpy or Python versions.
  - A test locks the value for known IDs.
- **Holdout = train S1 entities with `fold ∈ {0,1,2,3,4}`**: 549,699 S1 (US 329,717; India 219,982). Their matched S2/S3 records go with them.
- **Training folds = 5–19.**
  - Stacking and OOF use three groups: `oof_group = (fold − 5) // 5`, which gives 0 (folds 5–9), 1 (10–14) and 2 (15–19). The holdout gets −1.
  - Each group is scored by a model trained on the other two. Holdout and test are scored by a model trained on all training folds.
- **Report every number on the full holdout** (noise about ±0.001).
  - Quick iterations may use **fold 0 only** (about 110k S1, noise about ±0.002), but PR numbers use the full holdout.
- **Never fitted on the holdout:** anything supervised, such as dictionaries learned from pairs, token target encodings, city aliases, calibration and model weights.
  - Tuning one or two scalars on the holdout (a threshold or shrink) is allowed.
- **Pools stay full:**
  - Blocking and search run over the **full** train S2/S3 pool, as in test. Never shrink the pool to the holdout.
  - Competition and collective features use the **full** candidate graph. Training rows may be a sample of training-fold entities.

## C3. Records and normalized records

**Raw records.** `work/records/<split>.parquet` (stage `records`) has one row per record across S1, S2 and S3:

| column | dtype | notes |
|---|---|---|
| `eid` | int64 | C1 |
| `source` | int8 | 1, 2 or 3 |
| `country` | string | open set; never hard-code values |
| `name` | string | raw `business_name` |
| `address` | string | raw `business_address` (may be empty) |

For train only, `work/records/truth.parquet` holds the true pairs: `s1`, `r` (int64), unique. Singletons have no rows.

**Normalized records.** `work/norm/<tag>/<split>.parquet` (stage `normalize`) has one row per record, keyed by `eid`. The **v0 minimum** columns are below.
- The normalization owner may add columns with the `n_` / `a_` / `f_` prefixes, documented in `ber.normalize`.
- Renaming or removing a column needs a contracts PR.

| column | dtype | meaning |
|---|---|---|
| `eid`, `source`, `country` | int64, int8, string | as in the raw records |
| `n_full` | string | full normalized name: lowercase ASCII after transliteration and accent removal, tokens space-joined |
| `n_core` | string | name tokens without legal forms, honorifics or junk |
| `n_concat` | string | `n_core` without spaces (compared with domains and hashtags) |
| `n_legal` | string | canonical legal-form code (`llc`, `pvt_ltd`, `sarl`, …) or `""` |
| `a_norm` | string | full normalized address, tokens space-joined, null tokens removed |
| `a_street` | string | street tokens: words minus city, state and numbering markers |
| `a_city` | string | city (the component before the state), or `""` |
| `a_state` | string | canonical state/region code, or `""` |
| `a_num1` | int64 | primary (house) number, leading zeros stripped; −1 if none |
| `a_num1_sfx` | string | letter suffix of the primary number (`b`, `bis`, `ter`), or `""` |
| `a_nums` | list\<int64\> | every number in the address, in order |
| `a_unit` | int64 | unit, flat or suite number; −1 if none |
| `a_ntok` | int16 | address token count |
| `f_domain`, `f_hashtag`, `f_phone`, `f_dba`, `f_indic`, `f_honorific` | bool | name flags |
| `f_addr_empty`, `f_addr_short`, `f_landmark`, `f_pobox`, `f_fragment` | bool | address flags (`short` = ≤3 tokens) |

## C4. Candidates (blocking output = matcher input)

`work/candidates/<tag>/<split>.parquet`:

| column | dtype | notes |
|---|---|---|
| `s1` | int64 | S1 eid |
| `r` | int64 | S2 or S3 eid, never S1 |
| `views` | int16 | bitmask of the views and keys that retrieved the pair. The bit values are documented in `ber.block`. v0: 1 = V-both, 2 = V-addr, 4 = V-name-short, 8 = key number+street, 16 = key domain, 32 = key DBA |
| `score_<view>` | float32 | retrieval similarity in that view; NaN if that view didn't retrieve the pair |
| `rank_s1_<view>` | int16 | rank of `r` in `s1`'s list for that view (0 = best); −1 if absent |
| `rank_r_<view>` | int16 | rank of `s1` in `r`'s list for that view; −1 if absent |

- `(s1, r)` pairs are unique.
- An S1 with no candidates simply has no rows.
- **This exact set becomes `candidate_pairs.tsv`.** It is what the matcher scores. Any trimming happens before this file is written.
- **Blocking report** (required, C7 `blocking` keys):
  - pair recall and oracle F0.5 on the holdout;
  - recall per country, per source and per hard case;
  - candidates per S1 (mean and p99);
  - runtime.

## C5. Scored pairs (matcher output)

| file | columns | notes |
|---|---|---|
| `work/scores/<tag>-s1/<split>.parquet` | `s1`, `r`, `p1` (float32), `oof_group` (int8) | stage-1 scores. On train they are **out-of-fold** (C2); `p1` may be uncalibrated |
| `work/scores/<tag>/<split>.parquet` | `s1`, `r`, `p` (float32) | final **calibrated** probability that `(s1, r)` is a match, in [0, 1] |

- Keep the same pairs as C4, or a documented subset.
- Because `p` is calibrated, scores from different models can be averaged or stacked, and any decision rule can run on top.

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
- The `holdout` block is `ber.eval.report(...)` on the holdout, with `by_group` given as `by_country`.
- The minimum keys:

```json
{
  "tag": "sachi-model-v0",
  "git_commit": "abc1234",
  "command": "python -m ber.pipeline --stage evaluate --split train --tag sachi-model-v0 --in matches=sachi-model-v0",
  "inputs": {"norm": "…", "candidates": "…", "features": "…", "scores": "…", "matches": "…"},
  "holdout": {"macro_f05": 0.0, "by_country": {"US": 0.0, "India": 0.0}, "singleton_f05": 0.0,
              "non_singleton_f05": 0.0, "micro_precision": 0.0, "micro_recall": 0.0, "mean_pred_per_s1": 0.0},
  "blocking": {"pair_recall": 0.0, "oracle_f05": 0.0, "cands_per_s1_mean": 0.0, "cands_per_s1_p99": 0,
               "recall_by_country": {}, "recall_by_source": {}},
  "test_diagnostics": {"mean_pred_per_s1_by_country": {}, "frac_r_assigned_by_country": {}},
  "runtime_s": 0,
  "notes": ""
}
```

## C8. Pair features

`work/features/<tag>/<split>.parquet`:

| column | dtype | notes |
|---|---|---|
| `s1`, `r` | int64 | the same pairs as C4, or a documented subset (e.g. sampled training entities plus the holdout) |
| `fold` | int8 | train: `fold_of(s1)`; test: −1 |
| `y` | int8 | train only: 1 if `(s1, r)` is a true pair, else 0 |
| `<group>__<name>` | float32 | feature values, NaN if undefined. Groups: `name`, `extra`, `num`, `addr`, `ctx`, `ret`, `src`, `var`, `emb` |

- **Rules:**
  - no `country` feature;
  - frequency features are rates per split and country;
  - every supervised encoding is out-of-fold and holdout-free (C2).
- **Feature list:** each feature has a one-line definition in `ber.features`. That list feeds the methodology document.

## C9. Matches (decision output)

`work/matches/<tag>/<split>.parquet`: `s1`, `r` (int64), the final predicted pairs.
- **Always a subset of C4.**
- On train they cover at least the holdout S1s.
- They are written to TSV only through `ber.io` (C6), using the `write` stage.

## C10. Gate records

Every gate in `plans/FINAL_PLAN.md` §9 is decided with `ber.eval.gates`: a paired bootstrap over S1 entities on the holdout. The output fields are `delta`, `ci_low`, `ci_high`, `p_better` and `n`.

The result is recorded as `docs/decisions/<date>_<hm>_gate-<id>-<topic>.md` (`python scripts/new_doc.py decision --member <you> --topic gate-g6-dp-vs-threshold`). The record contains:
- the baseline tag and the candidate tag;
- Δ macro F0.5 with its 95% CI, overall and per country;
- the runtime cost;
- the verdict (keep, drop or retry).
