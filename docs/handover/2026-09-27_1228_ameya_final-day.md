# Handover: final-day

- **Author:** ameya (human / agent: Claude Code)
- **When (IST):** 2026-09-27 12:28 (draft; updated as the final is chosen)
- **Branch / PR / last commit:** `ameya/final-stack` / #58 / see `git log`
- **Area and paths touched:** `experiments/ameya/model-v1/stack/` (`compose.py`, `apply_swapsim.py`, `stack.sh` notes), `experiments/ameya/model-v1/RESEARCH_v6.md` §6.17, `docs/status/ameya.md`, this file.

## TL;DR (3 lines max)

v7sq-dpc scored 0.990545 (best); the uploads split it into +0.000085 (the stack) and +0.000281 (the French self-trained cross-encoders).
French acronyms are true copies (label-free size-bias test); French look-alike word swaps (592 pairs) are mostly false and are dropped.
Candidate final `2026-09-27-mixc-c2` = v7sq3 US/India + v7sq France − look-alikes (expected about 0.99061), byte-reproducible from this branch.

## What was done

- **Leaderboard, 27 Sep:** v7sq-dpc 0.990545 (rank 7, then 8); v7nst-dpc 0.990264. The pair isolates the model change (+0.000281, about +0.0016 of French F) from the stack (+0.000085).
- **Why v7sq gained** (France-diff agent): the French self-trained cross-encoders (qst, e5ls) overruled the US-trained ones, mostly dropping confident false pairs. US/India truth by the new model's pc band, carried to France, predicts 82% of the LB-implied gain; per-category rates predict 30%.
- **French acronyms (18,707 predicted, 11× the US/India rate) are kept.** The size-bias test (RESEARCH_v6.md 6.17): holders of a true copy have size-biased other copies, holders of an extra record have ordinary ones. French acronyms fit a false share of 0% [0, 1%]; validated on the holdout (true populations −0.05 to 0.0, false same-address look-alikes 0.47).
- **French look-alike word swaps are dropped** (`stack/apply_swapsim.py`): one content word replaced by a similar real word ("college du marie" → "ecole du marie"). France has 4,088 such candidates at the S1's address against 172 in a same-size US/India sample; US/India base rates allow about 130 true copies among the 484 predicted there; size-bias false share 0.83 [0.56, 1.10]; the error agent's count test agrees. 592 pairs on v7sq-dpc, worth about +0.00004.
- **Checked and closed:** name collisions and wrong owners (278 French pairs with a same-address rival, all resolved toward the exact name); a systematic cell scan (only the two cells above and a 177-pair nudged-number cell, left alone: +0.00001 at best); zero-shot Qwen2.5-7B-Instruct on the uncertain pairs (holdout AUC 0.537 against 0.898 for pc; blend weight 0.002; no gain).
- **Composition:** `stack/compose.py` takes the countries with labels from one stacked model and the others from another, so a final can mix the best US/India (holdout) with the best France (LB).

## Current state

- **Works:** every package below passes the validator and the strict audit. `mixc` rebuilds byte-identically from this branch.
- **Half-done:** France variants v7sq6 (only the four French self-trained cross-encoders), v7sqwg (guarded v7sq labels at stage 2, French rows ×3), v7sq5g (round-2 e5 on guarded labels), and v7xbag (stage-2 bag with v7sq's seeds 1–3), each with a France-only package; a fine-tuned Qwen2.5-7B re-scorer of the uncertain pairs on `grenuke-vast3`.
- **Known bugs and caveats:** the size-bias test under-states false shares (false pairs do not attach to random S1) and is invalid for a population that takes most of an S1's copies (whole pc bands, exact names).

## Numbers (shared holdout, `ber.eval`; include the command)

| metric | value | command / tag |
|---|---|---|
| holdout macro F0.5, combo rule | v7sq 0.991280; v7sq3 0.991307 (+27.3e-6 [+2.2, +52.6]); v7sq4 0.991293 | `agents/decide/rank.py` |
| holdout macro F0.5, stage 3 | v7sq 0.991246; v7sq4 0.991255; v7sq6 0.991247 | `run_local_full.sh` gates |
| runtime / peak RAM | stage 2 16.5–17.5 GB; decide 9.8 GB; compose + swapsim + write under 4 GB, about 1 min | |

## How to reproduce or continue (exact commands)

```
bash experiments/ameya/model-v1/stack/stack.sh v7sq3
bash experiments/ameya/model-v1/stack/stack.sh v7sq
cd experiments/ameya/model-v1/stack
python compose.py ameya-model-v7sq3-s3-ops3a-dpc ameya-cands-v7sq3-c2a ameya-model-v7sq-s3-ops3a-dpc ameya-cands-v7sq-c2a mixc0
python apply_swapsim.py ameya-model-mixc0 ameya-model-mixc
cd ../../../..
python -m ber.pipeline --stage write --split test --tag mixc --in candidates=ameya-cands-mixc0 --in matches=ameya-model-mixc
```

## Artifacts (local paths / drive links + sha256)

- `submissions/files/2026-09-27-mixc-c2/` matching `3688950c…`, candidates `55b766ef…` (the candidate final).
- `submissions/files/2026-09-27-mixb-c2/` matching `e67e9b81…` (mixc without the look-alike drop).
- `submissions/files/2026-09-27-fr-v7sq4-c2/` matching `e7334cce…` (France-only test of v7sq4).
- `submissions/files/2026-09-27-v7sq-s3-ops3a-dpc-c2/` matching `cdda9a2d…` (LB 0.990545).

## Next steps (ordered, with suggested owner)

1. Captain: upload `mixc`; then about 15:00 `mixc` with France from the best new variant; re-upload the best measured by 18:30.
2. Ameya: put the chosen final into Bakshi's delivery folder with its reproduce commands.
3. After the competition: destroy `grenuke-vast` and `grenuke-vast3`; remove the SSH keys.

## Blockers, open questions, decisions needed

- The captain chooses every upload and the final.
