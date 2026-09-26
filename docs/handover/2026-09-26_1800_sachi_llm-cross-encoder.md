# Handover: llm-cross-encoder

- **Author:** sachi
- **When (IST):** 2026-09-26 18:00 (updated 22:30 after reading squeeze-v7n)

## TL;DR

- Training Qwen2.5-1.5B (Apache-2.0, LoRA) as an independent cross-encoder on a rented RTX 4090, same
  band/OOF/format as ce_box.py, so ce_import.py reads it unchanged.
- After reading squeeze-v7n: the real test is **French rule-population AUC** (box/rule_auc.py), not holdout
  band AUC. Current standings: v6all 0.855, v7ce3 0.865, v7n 0.872, v7c 0.874, v7m 0.878 (best, lost w/ spot box).
- If Qwen's French AUC is competitive, next step is folding it into the z-mean (zmean_ce.py) alongside
  e5l/e5l2/bge, not adding it as a lone separate logit — that's the design v7n/v7m are already using.
- Running now (RTX 4090, on-demand, not spot), ETA ~1.6h total (~32 min/group after warmup), started 17:59 IST, expect done ~19:35 IST.

## What was done

- New script `experiments/sachi/ce_llm.py`: reads `$CE_BOX_DIR/band_{train,test}.parquet`, tokenises with
  ce.encode (identical text to ce_box.py), trains with LoRA (r=16) instead of full fine-tuning, writes the
  same output format (row, ce__logit).
- Licence checked: Qwen2.5-1.5B is Apache-2.0 (avoided 3B, which isn't). Under the 8B cap.
- Smoke-tested (group 0, 3000 rows): ran clean end to end.
- Full run: --train-frac 0.35 --batch 32 --grad-ckpt (needed to avoid OOM at batch 64).

## Current state

- Running on an on-demand RTX 4090 (not spot, so no interruption risk like the box that was lost tonight).
- Not yet evaluated on French rule-population AUC — will run box/rule_auc.py once done, if ameya can share it.

## Next steps

1. sachi: when the run finishes (~23:00), pull out_q15/, compute French rule-population AUC (need
   box/rule_auc.py from ameya, or will write an equivalent).
2. If AUC is competitive with v7n's 0.872: fold into z-mean with zmean_ce.py alongside whatever ameya's H100
   run produces (bge, self-trained e5-large), test as v7-something.
3. If not competitive: still useful as one more diverse signal — ameya's call whether to include in an
   ensemble mean regardless of solo AUC.

## Blockers

- Need `box/rule_auc.py` (or the rule-population truth tables) from ameya to evaluate properly instead of
  guessing from band AUC alone.
