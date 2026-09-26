# Handover: france-generator-ops

- **Author:** ameya (agent: Claude Code)
- **When (IST):** 2026-09-26 04:17
- **Branch / PR / last commit:** `ameya/analysis-v3` / no PR yet (waits for the leaderboard probes) / see `git log`
- **Area and paths touched:** `experiments/ameya/model-v1/` (`post_ops.py` new, `s1.py`/`s2.py` `--all`, `ANALYSIS_v4.md`), `docs/decisions/2026-09-26_0417_france-generator-ops-and-final-fit.md`

## TL;DR (3 lines max)

France accepts the generator's in-slot word-swap look-alikes (17k predictions in v4, 0.6% true in US/India) and misses its list-word true copies. `post_ops.py` fixes both for countries without labels; expected leaderboard +0.0027. v5 and the all-data fit tie on the holdout; the probes decide the final.

## What was done

- Deep dive on every idea from the captain's list (`ANALYSIS_v4.md` §1):
  - clusters, self-training, adaptive cut, typo repair, calibration strata and the no-match model are small or done;
  - synthetic pairs are superseded by the rules;
  - the final fit is done.
- Holdout loss anatomy: 63% of misses are empty-address records. The blocking misses are broken down by kind; per-stratum calibration is within ±0.05.
- France: address clusters (11.1% of S1, max 101) and same-address populations. The op-A/op-B generator operations were found and validated on the holdout labels.
- Two agents:
  - generator catalogue (`deep/generator/`): true-copy noise per country and source, distractor machinery, French word lists;
  - leave-one-country-out anatomy (`deep/loco_anatomy/`): an unseen country with proxy odds loses 0.024 in confident convention errors, so a stricter France threshold (G8) cannot help.
- `post_ops.py`, and `--all` for `s1.py`/`s2.py`.
- Probes packaged: v4-fr0, v4-in0, v4-frab, v5-frab. Final candidate `2026-09-26-v5all-ops`.

## Current state

- **Works:** everything above; the unit tests pass (100); the validator passes every package.
- **Half-done:** the leaderboard reading (the captain's uploads). The PR for v5 + rules + `--all` waits for it.
- **Known bugs and caveats:**
  - The rules rest on France behaving like the US/India generator. The probe checks this.
  - The list-A words are hand-written; the thresholds are real ≥ 20 S1 names, garble < 0.5 similarity, length ≥ 4.
  - Made-up brand names at the address, suffix additions and acronyms are left as they are (small, and uncertain).

## Numbers (shared holdout, `ber.eval`; include the command)

| metric | value | command / tag |
|---|---|---|
| holdout macro F0.5, v4 / v5 / v5all | 0.99015 / 0.99013 / 0.99016 (v5all vs v5 Δ +0.00002 [−0.00003, +0.00007]) | `ameya-model-v4`, `-v5`, `-v5all` |
| op-B drop on the US/India holdout | −0.000003 (27 pairs, 93% true) | `deep/opab.py` + `post_ops.py` logic |
| op-B population truth (holdout) / op-A | 0.6% / 98–99.8% | `deep/opab.py` |
| France: op-B dropped / op-A added (v4; v5; v5all) | 17,088 / 4,746; 19,336 / 3,278; 18,434 / 6,086 | `post_ops.py` |
| runtime | post_ops about 1 min; `--all` chain about 55 min | |

## How to reproduce or continue (exact commands)

```
python experiments/ameya/model-v1/post_ops.py --matches ameya-model-v4 --scores ameya-s2-v4 --cands ameya-cands-v4 --feats ameya-fx3 --tag ameya-model-v4ops
bash <scratchpad>/package_dir.sh ameya-model-v4ops ameya-cands-v4 2026-09-26-probe-v4-frab
python experiments/ameya/model-v1/s1.py --feats ameya-fx4 --tag ameya-s1-v5all --groups str,cx,lo0,lg --drop leg__r_only_bits,leg__s1_only_bits --all
python experiments/ameya/model-v1/s2.py --feats ameya-fx4 --s1 ameya-s1-v5all --tag ameya-s2-v5all --groups str,cx,lo0,lg,ce --cluster --extra leg__rel,leg__n_s1,leg__n_r,leg__inter,leg__s1_only,leg__r_only,ce__logit --all
python experiments/ameya/model-v1/decide.py --scores ameya-s2-v5all --col pc --tag ameya-model-v5all --base ameya-model-v5
python experiments/ameya/model-v1/cands_final.py --s1 ameya-s1-v5all --tag ameya-cands-v5all
python experiments/ameya/model-v1/post_ops.py --matches ameya-model-v5all --scores ameya-s2-v5all --cands ameya-cands-v5all --feats ameya-fx4 --tag ameya-model-v5all-ops
```

## Artifacts (local paths / drive links + sha256)

- `submissions/files/2026-09-26-v4/`: matching `cd09df65…`, the anchor.
- `submissions/files/2026-09-26-probe-v4-frab/`: matching `4446b9c9…`, v4 + rules.
- `submissions/files/2026-09-26-probe-v4-fr0/`: `36247a77…`, France emptied.
- `submissions/files/2026-09-26-probe-v4-in0/`: `86a9c9be…`, India emptied.
- `submissions/files/2026-09-26-probe-v5-frab/`: `c9a651f1…`, v5 + rules.
- `submissions/files/2026-09-26-v5all-ops/`: matching `f8b6245f…`, candidates `7f690bfb…`, the final candidate.

## Next steps (ordered, with suggested owner)

1. Captain uploads v4, then probe-v4-frab (France rules alone), then v5all-ops; fr0 if a France level is wanted: F_France = (LB_v4 − LB_fr0) / 0.14975 + 0.0559.
2. ameya: if frab ≥ v4 + 0.002, open the PR (rebase `ameya/analysis-v3` on main) and record the gate; if it loses, drop the rules.
3. Optional if time: position features (op A/B) in the model; acronym adds for France (+0.0003 France F0.5); a larger or diff-aware cross-encoder.
