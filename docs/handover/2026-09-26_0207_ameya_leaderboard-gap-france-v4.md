# Handover: leaderboard-gap-france-v4

- **Author:** ameya (agent: Claude Code)
- **When (IST):** 2026-09-26 02:07
- **Branch / PR / last commit:** `ameya/france-v4` / #_ / see the PR
- **Area and paths touched:** `experiments/ameya/model-v1/` (`ANALYSIS_v3.md`, `feats_lo_proxy.py`, `lo_mix.py`, `loco.py`, `cands_final.py`, `probe.py`, `probe_shift.py`, `s1.py`, `s2.py`), `docs/decisions/`, `docs/status/ameya.md`

## TL;DR (3 lines max)

The v3 holdout → leaderboard gap (−0.0092) is France, at about 0.93. The legal-form bitmasks are out of range there, and look-alike words unseen in train read as neutral.
v4 fixes both (label-free French word odds, no bitmasks) and adds the cross-encoder. Holdout 0.99015 (v3 0.98882). France goes to 3.37 predictions per S1 (v3 3.54, US/India 3.37).
v4 and v3ce are packaged; v5 (French address normalization + EI) is building on `ameya/analysis-v3`.

## What was done

- **Gap analysis** (`ANALYSIS_v3.md`):
  - US/India test predictions match the holdout on every label-free diagnostic.
  - France over-predicts by about 0.18 per S1.
  - French patterns, a stage-1 re-scoring test of the legal bits, and examples.
- **Leave one country out** (`loco.py`, G13). US → India:

  | | F0.5 |
  |---|---|
  | India's words known | 0.961 |
  | unseen | 0.882 |
  | unseen, filled with the label-free proxy | 0.960 |

  Self-training fails with unseen words: 0.882 → 0.831.
- **Label-free look-alike odds** (`feats_lo_proxy.py`, `lo_mix.py`): a word's moved-house-number share in its own country, mapped to the label-odds scale.
- **Model v3ce** (cross-encoder as a stage-2 feature) and **model v4** (v3ce + France fixes). See `docs/decisions/2026-09-26_0207_model-v4-france-and-cross-encoder.md`.
- **Final candidate set = the stage-2 input** (`cands_final.py`): 4.7 per test S1 instead of 34.
- **Probe tooling:** `probe.py` (swap or empty one country), `probe_shift.py` (France-only decision shift).
- **Three helper agents:**
  - **Pipeline audit.** France bits and words, the −1.9e-16 vs 0 encoding of unseen words, pool-size-dependent rarity features, French address normalization.
  - **Candidates and duplicates.** Exact duplicates are always one S1 in the truth: nothing to do.
  - **Research.** Deadline and ranking rules; methods; French lexicons.

## Current state

- **Works:** v4 and v3ce test predictions, packaged and validated.
- **Half-done:** v5 on `ameya/analysis-v3`: `ber.block.text` French address normalization (department → region, R → rue, articles, bis/ter) and EI in `legal.FORMS`. Features `ameya-fx4` are building; a gate follows. These two commits are not in this PR (no gate yet).
- **Known bugs and caveats:**
  - v4 drops some same-number word-swap predictions in France (0.793 → 0.709 per S1); part of that may be recall.
  - Rarity and rival-count features depend on pool size (test US has half of train US's S1); the audit estimates −0.0002 to −0.0004.

## Numbers (shared holdout, `ber.eval`; include the command)

| metric | value | command / tag |
|---|---|---|
| holdout macro F0.5 | v3 0.98882 → v3ce 0.99021 → **v4 0.99015** | `decide.py --scores ameya-s2-v4 --tag ameya-model-v4 --base ameya-model-v3ce` |
| stage 1 (p1, best threshold) | v4 0.9869 (v3 0.9871) | `s1.py --tag ameya-s1-v4 ...` |
| candidate set recall / oracle F0.5 | 0.98926 / 0.99676 (4.7 per S1) | `cands_final.py --s1 ameya-s1-v4 --tag ameya-cands-v4` |
| test France predicted per S1 / empty | 3.370 / 5.3% (v3 3.539 / 4.4%) | `decide.py` diagnostics |
| runtime | lop + lo0 about 8 min; stage 1 about 12 min; stage 2 about 26 min (with test); decide about 9 min | |

## How to reproduce or continue (exact commands)

```
python experiments/ameya/model-v1/feats_lo_proxy.py --feats ameya-fx3 --split train --calib
python experiments/ameya/model-v1/feats_lo_proxy.py --feats ameya-fx3 --split test
python experiments/ameya/model-v1/lo_mix.py --feats ameya-fx3
python experiments/ameya/model-v1/s1.py --feats ameya-fx3 --tag ameya-s1-v4 --groups str,cx,lo0,lg --drop leg__r_only_bits,leg__s1_only_bits
python experiments/ameya/model-v1/s2.py --feats ameya-fx3 --s1 ameya-s1-v4 --tag ameya-s2-v4 --groups str,cx,lo0,lg,ce --cluster --extra leg__rel,leg__n_s1,leg__n_r,leg__inter,leg__s1_only,leg__r_only,ce__logit
python experiments/ameya/model-v1/decide.py --scores ameya-s2-v4 --col pc --tag ameya-model-v4 --base ameya-model-v3ce
python experiments/ameya/model-v1/cands_final.py --s1 ameya-s1-v4 --tag ameya-cands-v4
python -m ber.pipeline --stage write --split test --tag ameya-model-v4 --in candidates=ameya-cands-v4 --in matches=ameya-model-v4
```

## Artifacts (local paths / drive links + sha256)

- `submissions/files/2026-09-26-v4/`:
  - `matching_results.tsv`: `cd09df6533981f41919674545e7a3459b0e41e0d3f8165531e9cdf4a5d418e4a`
  - `candidate_pairs.tsv`: `1cbecef05b59afb0aed457a48e15484891996b8f8fc0b09e421127dbdccec09f`
- `submissions/files/2026-09-26-v3ce/`:
  - `matching_results.tsv`: `aec289c0053f42604a5224db7cac9e4e743fa15281b77b5bf620f4a079602207`
  - `candidate_pairs.tsv`: `d6a0eeeda60270e5247882c8586239cf5bec2fa1a96407afccd3c9374fcf1f2c`
- Work tags:
  - features: `ameya-fx3-lop`, `ameya-fx3-lo0`, `ameya-fx3-lop-dev`
  - scores: `ameya-s1-v4`, `ameya-s2-v4`, `ameya-s2-v3ce`
  - matches: `ameya-model-v4`, `ameya-model-v3ce`
  - candidates: `ameya-cands-v4`, `ameya-cands-v3`

## Next steps (ordered, with suggested owner)

1. Captain: confirm the deadline in the portal. The submission-round page says 27 Sep 15:30 UTC = 21:00 IST, and that the final submission is the ranked one. Then upload v4 (and v3ce, if an upload is spare, to separate the two effects).
2. ameya: v5 gate (holdout vs v4) and France diagnostics, then package.
3. ameya: a France-only decision probe (`probe_shift.py`) if v4's leaderboard move is below +0.006.
4. Submission records and CHANGELOG entries for the uploads (captain).

## Blockers, open questions, decisions needed

- G10's +0.003 bar is not met on the holdout alone (+0.0014). The cross-encoder is kept for France; the captain decides with the leaderboard.
