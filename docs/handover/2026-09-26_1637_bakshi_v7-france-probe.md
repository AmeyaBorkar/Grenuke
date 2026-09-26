# Handover: v7-france-probe

- **Author:** Bakshi
- **When (IST):** 2026-09-26 16:37
- **Branch:** `bakshi/v7-tsv-audit`; follow-up PR pending
- **Area and paths:** `experiments/bakshi/v7/`, Bakshi handovers/status. Ameya's source was only read as a frozen snapshot.

## TL;DR

Prepared a v5-based experimental matching TSV removing 1,148 additional France B-rule predictions. It fixes suffix/street-type parsing gaps and protects repeated source words. Format and integrity checks pass; France score is unknown and this is not selected as final v7.

## What was done

A fresh fetch found the first diagnostic PR #34 already merged and the new `ameya/research-v6` branch. Continued on a branch from latest main. Tested its robust-address B rule on the dev-v3 accepted residuals; all 18 would-be rejections were genuine repeated-word copies. Added a whole-token repetition exception, protecting all 18 including three holdout pairs. Applied only additional non-repetition B drops to the supplied v5 France predictions. Other new proposal families remain disabled.

## Current state

- **Works:** verified v5 import, full prediction diagnostics, frozen-source robust B probe, repetition protection, TSV writer, independent audit and validator.
- **Half-done:** an independently measured France gain and final v7 with v6/stage-3 score-bearing inputs.
- **Known caveats:** the published additional B population's low truth rate is unconditional; dev residual acceptance differs. The protected dev gate has zero gain, not a positive result. Only a human leaderboard experiment measures France. The candidate file was not supplied.

## Numbers

| check | result |
|---|---|
| v5 pairs / experimental pairs | 5,835,593 / 5,834,445 |
| additional France drops / affected S1 | 1,148 / 1,137 |
| US / India added or removed pairs | 0 / 0 |
| new pairs outside baseline | 0 |
| S1 coverage / target IDs / ownership | all valid; no conflicts |
| repeated dev pairs protected | 18 true US pairs; 3 holdout |
| protected dev macro F0.5 / delta | 0.9885633928 / 0; CI [0,0] |
| tests | 132 passed |
| official matching validator | PASS |
| France score / rank effect | unknown |

## How to reproduce

See the experiment README. `robust_drop_probe.py --write-experimental` requires the verified base pair cache, source TSV and frozen research source module. It refuses overwrite, wrong country scope, missing baseline pairs, invalid coverage or conflicting ownership. The independent `audit_tsv.py` comparison checks the written file against v5, not merely the intended transform.

## Artifacts

- Workspace `outputs/v7_v5base_robustB_probe/matching_results.tsv` (97,630,521 bytes).
- SHA256 `714112f929188d813e0e22a3e96ee77699a32fc47be1080c429ac926ab4894e9`.
- Verified source v5 SHA256 `76fe7eff4bb37e9eab392b25d4cb0e563a91f0953131bc9b908909ca44fa3d4b`.
- Rule source: commit `717f00b`; file SHA256 `414231a265927f05bb059db3792f2a400a5736df072407dd73fe657f49afb6fa`.
- Cache reports: `../GrenukeGit2/work/v7/bakshi-robust-drop-v7/` and `bakshi-v7-robustb-probe-audit/`.
- No TSV, Parquet or model data committed. Original submissions unchanged.

## Next steps

1. Human: if spending an upload on this isolated probe, compare against the v5 baseline; its score is not predicted as a fact.
2. Bakshi: use that result plus full v6/stage-3 outputs when available to build and measure final v7.
3. Keep failed exact-rescue and broad address-veto ideas disabled. Do not apply blind unions of older submissions.

## Blockers and decisions

User reports v6 is still running. This probe needs no full model scores, but is not equivalent to v6 + stage 3 + all rules-v3 additions. It targets an existing measured operation and exposes the remaining France uncertainty explicitly. No leaderboard upload, main merge or final selection was performed by this work.
