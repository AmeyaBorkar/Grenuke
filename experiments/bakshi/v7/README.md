# V7 France diagnostic — not a submission

This experiment tests complete street/locality evidence and composed name edits using only the provided records. It imports the existing rule classifier without modifying Ameya's files. No new model or external dataset is used.

## Findings from the released v3 dev kit

The audit selected 698,372 candidate pairs from 3,345,119 rows. This is the released v3 sample, **not v6**. Ownership is reconstructed on the sliced sample, so residual results are diagnostic only.

* The proposed address guard vetoed three eligible baseline additions, all labeled true (India fold 15: one; US folds 10 and 15: one each). There were no vetoes in holdout fold 0. It is disabled.
* `swap_list` had 48 eligible training predictions in India, all true, and 197 in US, 196 true. Treating this broad family as a rejection rule would cause harm. It is disabled.
* `multi_append` had no eligible training additions. `drop_multi_list` had one, labeled false. Neither meets support/precision requirements. Both are disabled.
* No full-v6 macro F0.5 gain or France score has been measured. The default policy preserves the original B/A/APP/ACR behavior and does not enable NUM/CODE.

The parser can now expose combined edits for further investigation, but these findings do not justify generating a new submission or claiming a rank improvement.

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
