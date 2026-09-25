# Decision: model-v4-france-and-cross-encoder

- **Date (IST):** 2026-09-26 02:07
- **Author:** ameya
- **Status:** proposed: v4 is the candidate for the next upload; the captain decides the upload, and the leaderboard move is the France check (G7/G8)
- **Affects:** model (`experiments/ameya/model-v1`: `s1.py`, `s2.py`, `feats_lo_proxy.py`, `lo_mix.py`, `cands_final.py`), the submission's candidate file

## Context

Model v3 scores 0.98882 on the shared holdout and 0.97961 on the public leaderboard (gap −0.0092).
`experiments/ameya/model-v1/ANALYSIS_v3.md` shows the gap is France:
- US/India test predictions behave exactly like the holdout.
- 0.97961 = 0.85 × 0.9888 + 0.15 × F_France gives F_France ≈ 0.93.

Two causes were verified:
1. **The legal-form bitmasks.** French forms sit in bit values never seen in train. French look-alikes that change the legal form and move the house number score 0.456 at stage 1, and 0.027 with the bits zeroed.
2. **Look-alike words unseen in train get odds of 0 (neutral).**

France predicted 3.54 records per S1 against a generator mean of 3.46 true (US and India: exactly 3.46), and left only 4.4% of S1 empty.

## Options considered

1. **v3 + cross-encoder (`ameya-model-v3ce`, G10).** multilingual-e5-small (MIT, 118M parameters) is trained out of fold on the stage-1 band [0.02, 0.99] and added as a stage-2 feature.
2. **v4 = option 1 + the France fixes:**
   - **Label-free look-alike odds for countries without training labels.** A word's moved-house-number share among close pairs, counted in its own country, is mapped to the label-odds scale by an isotonic fit on US/India words (`feats_lo_proxy.py`).
   - **Group `lo0` (`lo_mix.py`).** It keeps the label odds for US/India, writes unseen words as exactly 0 (they were −1.9e-16 on train and 0 on test), and uses the proxy odds for France.
   - **No legal-form bitmasks** in stages 0–2.
3. **Self-training on France.** Rejected. In the leave-one-country-out check with unseen words, it lowers the score (0.882 → 0.851 → 0.831).

## Decision

**Option 2 (v4) as the upload candidate.** Holdout numbers are on the shared holdout (549,699 S1), with a paired bootstrap of 1,000 resamples.

| | v3 | v3ce | **v4** |
|---|---|---|---|
| holdout macro F0.5 | 0.98882 | 0.99021 | **0.99015** |
| India / US | 0.9887 / 0.9889 | 0.9905 / 0.9900 | 0.9904 / 0.9900 |
| precision / recall | 0.99833 / 0.96893 | 0.99868 / 0.97221 | 0.99884 / 0.97132 |
| test France: predicted per S1 / S1 left empty | 3.539 / 4.4% | 3.470 / 5.1% | **3.370 / 5.3%** |
| test US / India: predicted per S1 | 3.380 / 3.358 | 3.386 / 3.370 | 3.382 / 3.367 |

**Gates**

- **G10, cross-encoder, v3ce vs v3.**
  - Δ +0.00140, CI [0.00131, 0.00148].
  - This is below the +0.003 bar for heavy components.
  - It is kept for France: it halves French look-alike acceptances. Singleton F0.5 also rises 0.9913 → 0.9974.
- **France fixes, v4 vs v3ce.**
  - Δ −0.00006, CI [−0.00012, −0.00001]: a tie in practice.
  - The fixes are country-agnostic, so US/India are unchanged.
- **G13, leave one country out** (`loco.py`: dev kit, stage-1 model trained on US, scored on the India holdout).

  | India's words | F0.5 |
  |---|---|
  | known | 0.96106 |
  | unseen (France's case in v3) | 0.88235 |
  | unseen, filled with the proxy odds | **0.95984** |

  For reference, a model trained on both countries scores India at 0.98346.
- **France diagnostics** (label-free; predictions per French S1):

  | pattern | v3 | v4 | US |
  |---|---|---|---|
  | house number moved + legal form added or changed | 0.047 | 0.002 | 0.022 |
  | house number moved + extra word | 0.047 | 0.007 | 0.071 |

  - The model's France forecast rises 0.970 → 0.980.
  - Its US/India forecast is 0.993.

Commands:
```
python experiments/ameya/model-v1/feats_lo_proxy.py --feats ameya-fx3 --split train --calib
python experiments/ameya/model-v1/feats_lo_proxy.py --feats ameya-fx3 --split test
python experiments/ameya/model-v1/lo_mix.py --feats ameya-fx3
python experiments/ameya/model-v1/s1.py --feats ameya-fx3 --tag ameya-s1-v4 --groups str,cx,lo0,lg --drop leg__r_only_bits,leg__s1_only_bits
python experiments/ameya/model-v1/s2.py --feats ameya-fx3 --s1 ameya-s1-v4 --tag ameya-s2-v4 --groups str,cx,lo0,lg,ce --cluster --extra leg__rel,leg__n_s1,leg__n_r,leg__inter,leg__s1_only,leg__r_only,ce__logit
python experiments/ameya/model-v1/decide.py --scores ameya-s2-v4 --col pc --tag ameya-model-v4 --base ameya-model-v3ce
python experiments/ameya/model-v1/cands_final.py --s1 ameya-s1-v4 --tag ameya-cands-v4
python experiments/ameya/model-v1/loco.py --dev ameya-fx3-dev --train-country US --eval-country India --only-proxy --lop ameya-fx3-lop-dev
```

## Consequences (what changes, what we give up, how we'll know it was right)

- **Packages** (validator PASS):
  - `submissions/files/2026-09-26-v4/` (matching sha256 `cd09df65…`);
  - `submissions/files/2026-09-26-v3ce/` (matching sha256 `aec289c0…`).
- **The candidate file is now the stage-2 input set.**
  - 4.7 per test S1 instead of 34; 129 MB instead of 781 MB.
  - Holdout pair recall 0.98926 instead of 0.98992.
  - No prediction falls outside it.
  - This is what the README asks for: the set the final model scores.
- **How we will know it was right.** US/India are tied between v3ce and v4 on the holdout, so LB(v4) − LB(v3ce) ≈ 0.15 × ΔF_France.
  - The diagnostics suggest France gains +0.03 to +0.05, so LB(v4) − LB(v3) should be about +0.006 to +0.009.
  - A smaller move points to recall lost on same-number word swaps: French predictions of that pattern fell 0.793 → 0.709 per S1. It would also argue for a France-only decision probe (`probe_shift.py`).
- **What we give up.** The G10 bar is not met on the holdout alone, and the cross-encoder adds about 45 GPU-minutes to the pipeline.
