# Handover: research-v6-gap-budget

- **Author:** ameya (agent: Claude Code)
- **When (IST):** 2026-09-26 15:57
- **Branch / PR / last commit:** `ameya/research-v6` / PR opened with this handover / see `git log`
- **Area and paths touched:**
  - `experiments/ameya/model-v1/RESEARCH_v6.md` (new);
  - `post_ops.py` (`--robust-addr`, rules v3);
  - `fr_threshold.py` (new);
  - `docs/decisions/2026-09-26_1557_rules-v3-and-stage3.md`;
  - status.

## TL;DR (3 lines max)

- The other session's gap budget, checked on v6all:
  - the US test over-prediction is correct tie resolution in a smaller pool;
  - crowding is ≤ 0.0001;
  - France's level hinges on US/India's test level, which only the France-emptied probe measures.
- New: France's pc is provably overconfident (Σ pc per S1 3.55 > 3.46 allowed). About 1,291 French look-alikes slipped the rules through address parsing; rules v3 fixes that. Stage 3 on v6all is +0.000055.
- Next candidate `2026-09-26-v6all-s3-ops3-c2`, plus two probes (`fr0`, `fr090`) that decide where 0.99 could come from.

## What was done

- **Label-free diagnostics on v6all (US/India test vs holdout vs France), in `RESEARCH_v6.md`:**
  - confidence bands and per-S1 counts;
  - probability-mass invariants (per record ≤ 1 owner; per S1 ≤ the generator's 3.46);
  - edit-family decomposition of expected errors;
  - identical pairs;
  - blocking recall (exact name + address pairs, empty-address pairs);
  - a crowding simulation on the holdout (S1-side cap 15 → 10);
  - hand review of 22 French candidate lists.
- **Rules v3** (`post_ops.py --robust-addr`) validated on the holdout and applied.
- **Stage 3** run on v6all and gated.
- **Packages built:**
  - candidate `v6all-s3-ops3-c2`;
  - `v6all-ops3-c2`;
  - probes `probe-v6s3-fr0` and `probe-v6s3-fr090`;
  - `probe-v6all-fr0` (v6all without stage 3 / rules v3).
- An attribution agent (SHAP on stages 1–2, France vs US/India) was still running at the time of writing. Its findings go into the next update.

## Current state

- **Works:** everything above.
- **Half-done:** the SHAP attribution agent (why France is less confident).
- **Known bugs and caveats:**
  - France's absolute level stays unknown until the probe.
  - The newly matched APP pairs are 89% true in US (97% India) and A 87% in India: positive value, but less clean than the key-matched ones.

## Numbers (shared holdout, `ber.eval`; include the command)

| metric | value | command / tag |
|---|---|---|
| holdout macro F0.5, v6all + stage 3 | 0.990842 vs 0.990788, Δ +0.000055 [+0.000025, +0.000085] | `stage3.py --scores ameya-s2-v6all --tag ameya-s3-v6all --p-cand 0.02 --top-r 2`; `decide.py --scores ameya-s3-v6all --col pc --tag ameya-model-v6all-s3 --base ameya-model-v6all-c2 --p-cand 0.02 --top-r 2` |
| rules v3, pairs matched only by the robust address (holdout truth) | B India 0.0% / US 1.2%; A 87.4% / 99.1%; APP 97.0% / 89.4%; ACR 95.8% / 100% | `post_ops.py --measure --robust-addr --matches ameya-model-v6all-c2 --feats ameya-fx5` |
| crowding (tok S1-side cap 15 → 10 on the holdout) | −0.00009 | scratchpad `r6/crowd.py` |
| per-record renormalisation | +0.000015 (not taken) | scratchpad `r6/mass2.py` |

## How to reproduce or continue (exact commands)

```
python stage3.py --scores ameya-s2-v6all --tag ameya-s3-v6all --p-cand 0.02 --top-r 2
python decide.py --scores ameya-s3-v6all --col pc --tag ameya-model-v6all-s3 --base ameya-model-v6all-c2 --p-cand 0.02 --top-r 2
python post_ops.py --matches ameya-model-v6all-s3 --scores ameya-s3-v6all --cands ameya-cands-v6all-c2 --feats ameya-fx5 --tag ameya-model-v6all-s3-ops3 --robust-addr
python -m ber.pipeline --stage write --split test --tag ameya-model-v6all-s3-ops3 --in candidates=ameya-cands-v6all-c2 --in matches=ameya-model-v6all-s3-ops3
python probe.py --base ameya-model-v6all-s3-ops3 --country France --empty --tag ameya-probe-v6s3-fr0
python fr_threshold.py --final ameya-model-v6all-s3-ops3 --model ameya-model-v6all-s3 --scores ameya-s3-v6all --thr 0.9 --tag ameya-probe-v6s3-fr090
```

## Artifacts (local paths / drive links + sha256)

All under `submissions/files/`, validator PASS, candidates `cc3750d0…` (3.70 per S1):
- `2026-09-26-v6all-s3-ops3-c2`: `544ffdf89410c2fe00d09c20941f57ca5e9afb998db1d8251f161c362ac98710` (**next candidate**);
- `2026-09-26-v6all-ops3-c2`: `8c3d3a63fa5fa99e96a93d9c06c520a6399ee66f063dbb9f3b72be9637dbfb48`;
- `2026-09-26-probe-v6s3-fr0`: `48ddacd436cc0eeb9c7e10cc6cca952e1ac382aef0f047c28d238ee08584eb48`;
- `2026-09-26-probe-v6s3-fr090`: `0914b6d6ceaaf996bcb36286d72044a30c50591d09e0ab752441e3067753128d`;
- `2026-09-26-probe-v6all-fr0`: `9ef846d1f71d3158f461daa3ec02f84eb432cab27071b47fb9bddfca58fcc7c0`.

## Next steps (ordered, with suggested owner)

1. Captain: upload `v6all-s3-ops3-c2`, `probe-v6s3-fr0` and `probe-v6s3-fr090`, and report the scores.
2. ameya: read the probes (`RESEARCH_v6.md` §3 table) and follow the matching branch: France threshold, France model-level features, or US/India test families.

## Blockers, open questions, decisions needed

- The captain's uploads and their scores.
- How many upload slots remain today and tomorrow.