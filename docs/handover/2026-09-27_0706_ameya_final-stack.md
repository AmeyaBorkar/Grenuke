# Handover: final-stack

- **Author:** ameya (agent: Claude Code)
- **When (IST):** 2026-09-27 07:06
- **Branch / PR / last commit:** `ameya/final-stack` / #58 (draft) / `32ca9cc`
- **Area and paths touched:** `experiments/ameya/model-v1/stack/` (new), `experiments/ameya/model-v1/RESEARCH_v6.md` §6.16, `experiments/ameya/model-v1/fhs.py`, `docs/decisions/2026-09-27_0636_stacked-rules.md`, `docs/status/ameya.md`.

## TL;DR (3 lines max)

- Rules stacked on the final model: expected-F0.5 with a crowd shift on US/India (+48.1e-6 [+7.1, +91.2] on v7s) and French `copy` / `city`.
- `stack/stack.sh <model>` builds them. **The first upload candidate is `2026-09-27-v7sq-s3-ops3a-dpc-c2`** (holdout 0.991246, `fhs` +2.19; validator and strict audit PASS).
- The repo port is verified only through its scratchpad twin so far. Its own equivalence run (`PORT OK`) is queued for after the chains; PR #58 stays a draft until then.

## What was done

- **Models since v7nst:**
  - v7s: e5l + e5ls + bge;
  - v7sb: bges instead of bge;
  - v7sq: + Qwen2.5-1.5B;
  - v7ensall: a bag of five;
  - v7sq3: v7sq + a second e5ls seed.
  - Each ran s2 → s3 → rules v3 → acronym join → package. v7sq2 and v7ensall2 were running at 07:06.
- **Three analysis agents** worked on the US/India holdout (reports in the session scratchpad `agents/{hunt,polish,decide}/REPORT.md`): the hunt rules, the French polish and the decision rule. Their scripts are ported to `stack/` with only path changes, and the labelled countries are read from train.
- **Stacked on every model:**
  - `-h2pc`: the hunt rules, narrowed for France, plus polish;
  - `-dpc`: `-h2pc`'s France, plus the decision rule for US/India.
- **Crash at 03:35** (memory). Recovered with no loss. The memory reaper killed shell wrappers at 04:46 and 06:30; the scripts survived.
- **vast.ai box:** stopped at 06:21 after Qwen, bges and e5ls2 were fetched.

## Current state

- **Works:**
  - `stack_model.sh` (the scratchpad twin of `stack.sh` + `apply_combo.py`) reproduced `v7s-h2pc` byte for byte;
  - every `-dpc` package passes the validator; v7s-dpc and v7sq-dpc pass the strict audit.
- **Half-done:**
  - the repo equivalence run: `repo_test2.sh`, after `final_night9.sh` ends at about 09:30;
  - v7sq2 and v7ensall2 plus their stacks: the queue ends at about 09:30 with a decision table and audits.
- **Known bugs and caveats:**
  - `fhs.py` crashed on a candidate identical to the reference (fixed here with typed arrays);
  - the DP rule was gated on v7s, and on v7nst only without the crowd shift;
  - France's model changes (the "other" `fhs` bucket) are unknown in sign.

## Numbers (shared holdout, `ber.eval`; include the command)

| metric | value | command / tag |
|---|---|---|
| holdout macro F0.5, s3 | v7nst 0.991194, v7s 0.991229, v7sb 0.991226, **v7sq 0.991246**, v7ensall 0.991239, v7sq3 0.991250 | `run_local_full.sh` gates, `work/reports/ameya-model-<m>-s3.json` |
| US/India part (LB scale) | v7nst 0.843210, v7s 0.843247, v7sq 0.843258, v7ensall 0.843253, v7sq3 0.843265 | `final_memo.py` |
| decision rule + acr + cap on v7s | +48.1e-6 [+7.1, +91.2], P(better) 0.987 | `agents/decide/apply_combo.py`, `combo_v7s.json` |
| `fhs` vs v7nst, `-dpc` | v7s +1.11, v7sb +1.13, **v7sq +2.19**, v7ensall +1.94, v7sq3 +1.13, v7nst +1.43 | `fhs.py ameya-model-v7nst-s3-ops3a <tags>` |
| runtime / peak RAM | about 6 min per model; `apply_combo.py` 2.8 GB. Chain peaks: s2 16.5–17.5 GB, decide 9.8 GB, acr_join 6.0 GB | |

## How to reproduce or continue (exact commands)

```
bash experiments/ameya/model-v1/stack/stack.sh v7sq
python -m ber.pipeline --stage write --split test --tag ameya-model-v7sq-s3-ops3a-dpc \
    --in candidates=ameya-cands-v7sq-c2a --in matches=ameya-model-v7sq-s3-ops3a-dpc
python student_resource/utils/validate_submission.py --matching <out>/matching_results.tsv --candidate <out>/candidate_pairs.tsv --test-dir student_resource/dataset/test --check-ids
```

## Artifacts (local paths / drive links + sha256)

- `submissions/files/2026-09-27-v7sq-s3-ops3a-dpc-c2/`: matching `cdda9a2da0147c06039d83b673e26d8bfc71c5171915148c1dcd24979ea0e85c`.
- `submissions/files/2026-09-27-v7s-s3-ops3a-dpc-c2/`: matching `5aa4db2c4a16108d3b4f290b5c52a3a452165bb1f99e35154b608768d874b990`.
- `submissions/files/2026-09-27-v7nst-s3-ops3a-dpc-c2/` (fallback): matching `f349012516cdd239106cc88f53e4f5ccaf8b5531d30a9345e82f0584783494a2`.
- Cross-encoder logits (scratchpad `box/out_*`): e5l, e5l2, e5ls, e5ls2, bge, bges, qst.

## Next steps (ordered, with suggested owner)

1. Upload `v7sq-dpc` as the first of 27 Sep's five (Ameya, the captain).
2. Read its score. A score far below about 0.9902 means a French regression; the fallback is v7nst-dpc (ameya).
3. When `final_night9.sh` ends: the decision table for v7sq2 / v7ensall2; upload the best of them (ameya).
4. When the repo equivalence run prints `PORT OK`: mark #58 ready for review (ameya).
5. Add `stack/stack.sh <model>` after `acr_join` in `reproduce.sh`'s variant switch (Bakshi).
6. Upload the chosen final last, before 21:00 (Ameya).

## Blockers, open questions, decisions needed

- The captain's uploads and their scores.
- Merging #56 (Bakshi's package docs) and a small PR for the AGENTS.md deadline line (23:59 → 21:00): the captain's call.
- The vast.ai instance is stopped, not destroyed: destroy it in the console after the competition, and remove the SSH keys.
