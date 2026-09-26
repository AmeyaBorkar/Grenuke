# V7 France diagnostic — not a submission

This experiment tests complete street/locality evidence and composed name edits using only the provided records. It imports the existing rule classifier without modifying Ameya's files. No new model or external dataset is used.

## Findings from the released v3 dev kit

The audit selected 698,372 candidate pairs from 3,345,119 rows. This is the released v3 sample, **not v6**. Ownership is reconstructed on the sliced sample, so residual results are diagnostic only.

* The proposed address guard vetoed three eligible baseline additions, all labeled true (India fold 15: one; US folds 10 and 15: one each). There were no vetoes in holdout fold 0. It is disabled.
* `swap_list` had 48 eligible training predictions in India, all true, and 197 in US, 196 true. Treating this broad family as a rejection rule would cause harm. It is disabled.
* `multi_append` had no eligible training additions. `drop_multi_list` had one, labeled false. Neither meets support/precision requirements. Both are disabled.
* No full-v6 macro F0.5 gain or France score has been measured. The default policy preserves the original B/A/APP/ACR behavior and does not enable NUM/CODE.

The parser can now expose combined edits for further investigation, but these findings do not justify generating a new submission or claiming a rank improvement.

## Full v5 TSV audit (26 September, 16:13 IST)

The user supplied `matching_resultsV5all.tsv`. SHA256 `76fe7eff4bb37e9eab392b25d4cb0e563a91f0953131bc9b908909ca44fa3d4b` matches the recorded `2026-09-26-v5all-ops2-c2` package. It contains 1,732,544 rows and 5,835,593 pairs, with exact S1 coverage, valid target IDs, unique pairs, no cross-country matches and no conflicting record owners. The official validator passes; the candidate file is absent, so candidate inclusion cannot be checked. Source files were not modified.

France has 865,630 predicted pairs across 259,452 entities. The composed-edit categories affect only 18 predictions (13 swaps with list appends and 5 drops with multiple list appends), so this broad idea cannot deliver a material rank improvement on v5. Address diagnostics flag 11,774 predictions; these are **not labeled errors** and are not removed.

Two additional score-free probes were run against the raw records and existing normalized caches:

| proposal | v3 labeled dev residuals / holdout delta | full test residuals | counterexamples |
|---|---|---|---|
| exact complete name/address | 0 / 0 | 2 transfers, both France | both existing owners have compatible names and address token sets; no evidence for choosing a different owner |
| exact parsed street/city/house/unit and complete name | 0 / 0 | 8 adds, 4 transfers | 7 differ in later numeric address components; all 4 old owners have compatible name/address evidence |

The parsed-address probe keeps every parsed street token, city, first house number, suffix and unit. Nevertheless, complex house numbers can be misparsed: `27W 10` and `27W 13` can collapse, and locality heuristics can split equivalent addresses differently. Residual inspection compares the full raw numeric sequence and the existing owner's raw evidence to expose those failure modes. Neither probe is enabled. The dev score is 0.988563 for the sample-graph threshold baseline before and after both proposals; this is **not a v5/v6 metric**.

Run these score-free diagnostics independently of the full feature cache:

```powershell
python experiments/bakshi/v7/audit_tsv.py --base PATH_TO_V5_TSV --compare PATH_TO_V3_TSV --profiles
python experiments/bakshi/v7/probe_exact.py --split train --scores "$env:BER_WORK_DIR/scores/ameya-s2-v3-dev/train.parquet"
python experiments/bakshi/v7/probe_exact.py --split test --base-pairs "$env:BER_WORK_DIR/v7/bakshi-tsv-v5-audit/base_pairs.parquet"
python experiments/bakshi/v7/probe_exact.py --split train --scores "$env:BER_WORK_DIR/scores/ameya-s2-v3-dev/train.parquet" --norm-file "$env:BER_WORK_DIR/norm/bakshi-norm-v0a/train.parquet" --tag bakshi-street-rescue-v7
python experiments/bakshi/v7/probe_exact.py --split test --base-pairs "$env:BER_WORK_DIR/v7/bakshi-tsv-v5-audit/base_pairs.parquet" --norm-file "$env:BER_WORK_DIR/norm/bakshi-norm-v0a/test.parquet" --tag bakshi-street-rescue-v7
```

Full suite including the new TSV/probe regressions passes. V5 is a usable baseline for prediction audits and targeted experiments. It does not contain rejected candidate scores, so probability changes and model retraining still require the full-run artifacts; the user reports v6 is still running.

## GitHub artifact audit

Checked origin/main at `faa0244908`, all five surviving branches, all four releases and their assets, repository submission records and issue/PR comments. The v6 source, recipe, metrics and output hashes exist. The full v6 scores/models/submission do not appear in those locations. The [devkit-v3 release](https://github.com/AmeyaBorkar/Grenuke/releases/tag/devkit-v3) explicitly says full-scale files live only on the integration machine.

Downloaded `grenuke-devkit-v3.zip`, 405,194,383 bytes; verified SHA256 `b5d61f91faee8a90f6c8182823964e985506a5704363d82e8211ce68022d75eb` before extraction. Raw records remain in the existing local cache.

## Reproduce

Set `PYTHONPATH` to `code/business_entity_resolution/src`, and `BER_WORK_DIR` to the artifact cache, then run from the repository root:

```powershell
python experiments/bakshi/v7/rules.py audit --features-file "$env:BER_WORK_DIR/features/ameya-fx3-dev/train.parquet" --scores-file "$env:BER_WORK_DIR/scores/ameya-s2-v3-dev/train.parquet"
python -m pytest code/business_entity_resolution/tests experiments/bakshi/v7/test_rules.py -q
```

Reports land in `work/v7/bakshi-rules-v7-dev/`: `profiles.parquet`, `policy.json`, `audit.json`. Nothing from the cached data is committed.

## Full-run prerequisites

To apply an independently validated policy to v6, the script needs:

* `work/matches/ameya-model-v6all-c2/test.parquet` (before France rules)
* `work/scores/ameya-s2-v6all/test.parquet`
* `work/candidates/ameya-cands-v6all-c2/test.parquet`
* `work/features/ameya-fx5-str/test.parquet`

The corresponding training scores/features are needed for a full validation gate. A final TSV alone cannot replace these cached inputs. Alternatively rebuild using `docs/package/reproduce_v6all.sh`, then continue v7 experiments. The recipe estimates roughly three hours on its reference GPU machine; that is not a local runtime estimate. Review its baseline-report dependency before a fresh rebuild.

`apply` refuses missing inputs, checks final candidate inclusion, checks ownership, and verifies unchanged predictions in labeled countries. Combined edits and the address guard remain off unless a policy explicitly records validation. A policy must be supported by a full paired holdout gate before use; the dev audit does not supply that approval.
