# HANDOFF: final push, 27 Sep (for the Claude cloud session)

Read this file first, then `FINAL_PUSH_PLAN.md` beside it. You act for **Bakshi** (GitHub `trustdemons05`).
Branch `bakshi/final-push`, PR #62. `AGENTS.md` rules apply:
- no attribution lines in commits or PRs;
- never push to `main`;
- no data, parquet, zip or secrets in git;
- don't edit other members' files;
- don't upload to the leaderboard (humans do that).

Relay asks for Ameya to the user in chat. Don't ask him through GitHub.

## Goal and deadline

- **Goal:** beat our best measured score, v7sq-dpc at **0.990545**. The leaderboard top is 0.991811.
- **Uploads:** 3 left today, and the **best** upload counts, not the latest.
- **Deadline:** finished, audited candidate TSVs by **~19:30 IST**; uploads by ~20:00.
- **All box clocks are UTC.** IST = UTC + 5:30.
- The user wants lean, token-efficient updates, and wants trade-offs escalated to them rather than decided silently.

## Machines

| role | ssh | what's there |
|---|---|---|
| **pipeline** (2x RTX 4090, 64 vCPU, on-demand) | `ssh -p 48742 root@216.144.178.146` | `/workspace/grenuke/{repo,work,box,box_ameya,ref,logs,output}`, `env.sh` |
| **training** (4x H100, on-demand) | `ssh -p 28860 root@202.122.49.242` | `/workspace/grenuke/{repo,box,logs}` |
| old interruptible training box, Vast id 52916777 | dead | the user was asked to stop or destroy it; ignore it |

- **SSH key:** the laptop used `~/.ssh/vast_grenuke`. The cloud session needs its own key: generate one and give the user the public half, so it can be added to both boxes' `~/.ssh/authorized_keys`.
- **Google Drive:** both boxes back up every 5 min with `rclone` (remote `gdrive:`, scope drive.file, config at `~/.config/rclone/rclone.conf` on each box; never print it) to `My Drive/grenuke-train-backup` (https://drive.google.com/drive/folders/1czpvbONZ_nvG7JOdyHgD0jOk2aIeICgL):
  - `box/`: training outputs;
  - `logs/`: training logs;
  - `pipeline/{logs,box,output,work}`: pipeline outputs.
- Ameya pulls from that folder.

## What is running (as of ~15:30 IST)

**Training box: Qwen2.5-7B France cross-encoder (`q7st`).**
- Three OOF groups run on GPUs 0-2 (`llm_group.py`), resumed from Drive checkpoints after the interruptible box was taken away.
- Arguments: `--model Qwen/Qwen2.5-7B --name q7st --pseudo /workspace/grenuke/box/pseudo_fr_v7sq.parquet --infer-batch 512`, other flags at their defaults (lr 1e-4, batch 64, 1 epoch, max-len 96, lora-r 16, us-in-frac 0.5, sep " || ", seed 26).
- It merges automatically (`llm_merge.py`) into `/workspace/grenuke/box/out_q7st/{ce_train,ce_test}.parquet, config.json`. **Target: ~17:05 IST.**
- Logs: `/workspace/grenuke/logs/q7st_g{0,1,2}.log`, `q7st_merge.log`, `backup.log`.
- Status: `bash /workspace/grenuke/repo/experiments/bakshi/box/train_jobs.sh status`.
- Qwen3-4B (`q34st`) was dropped for time. mDeBERTa (bf16 non-finite gradients) and gte (index assert under transformers 5.17) failed and were dropped.

**Pipeline box: `run_chain2.sh` (nohup).**
- `phaseA.sh`: records -> dict -> blocking v3 -> fx5 features -> s1 `ameya-s1-v6all` -> e5-small `ce.py` -> band export -> `cands_final` -> coverage check vs Ameya's band. **ETA ~17:05 IST.**
- Then it runs `phaseB.sh g0 "e5l qst e5ls bge" box_ameya/pseudo_s2_fr_v7ce3.parquet` on GPU 0. **g0** is v7sq rebuilt as the **reproduction gate**: France must differ from v7sq-dpc by only about 0-3 per 1000, or nothing built on this box can be trusted.
- Logs: `/workspace/grenuke/logs/phaseA.log` (START/DONE/FAIL lines), `A_<step>.log`, `phaseB_<v>.log`, `B_<v>_<step>.log`.
- `phaseA.sh` and `phaseB.sh` skip steps that already finished. Don't edit `phaseA.sh` while it runs (bash reads it as it goes).
- Blocking reproduced: 66,429,057 train / 58,437,794 test pairs.

## What to do next

1. **When `out_q7st/ce_test.parquet` exists on the training box,** check `config.json` AUCs. Compare with the existing models' band AUC of 0.938-0.944: this is the first quality signal. On the pipeline box:
   `rclone copy gdrive:grenuke-train-backup/box/out_q7st /workspace/grenuke/box_ameya/out_q7st --include "ce_*.parquet" --include "config.json"`
   It must be row-aligned with `box_ameya/band_*.parquet`, which is Ameya's band (the one it trained on).
2. **When phase A is done** (g0 starts on GPU 0), launch g1 on GPU 1 at the same time:
   `cd /workspace/grenuke && CUDA_VISIBLE_DEVICES=1 setsid nohup bash repo/experiments/bakshi/box/phaseB.sh g1 "e5l qst e5ls bge q7st" /workspace/grenuke/box_ameya/pseudo_s2_fr_v7ce3.parquet > logs/g1.out 2>&1 < /dev/null &`
   - phaseB remaps every cross-encoder by (s1, r) (`remap_ce.py`, coverage at least 99.5% or it aborts), then runs z-mean -> ce_import -> s2 (--pseudo) -> decide -> stage3 -> decide -> post_ops -> acr_join -> stack.sh (dpc) -> apply_swapsim (dpcs) -> dp_france (dpcsf) -> write -> validator -> audit -> diff vs `ref/v7sq_dpc_matching.tsv`.
   - Outputs land in `output/<v>/dpc/` and `output/<v>/dpcsf/`.
3. **If a GPU frees early, a possible gC** is g1 with round-2 stage-2 labels (`box_ameya/pseudo_s2_fr_v7sq.parquet`). Ameya's warning: round-2 labels made France worse for e5 in his one comparison (v7sq5g, estimates without labels). The 7B itself was trained on round-2 labels.
4. **Choose the uploads:**
   - Hard gate: validator PASS + `audit_matching.py` PASS.
   - No regression on the labelled US/India holdout (see the reports).
   - France footprint vs v7sq-dpc from `diff_candidates.py`: want at least ~15 changed per 1000 French S1, ideally 28+ (~0.000016 LB per net-correct change per 1000).
   - g0 must pass the reproduction gate before any g1 result counts.
   - Recommend 2-3 uploads to the user and give exact file paths. The TSVs also reach Drive under `pipeline/output/`.
   - Fallback if the chain fails: v7sq4 (audited PASS), already on the laptop / in Ameya's round-2 folder.
5. Commit script fixes to `bakshi/final-push` (no attribution). Update `FINAL_PUSH_PLAN.md` with results.

## Lessons from today (avoid repeating them)

- Writing files with `cat > file` over ssh has produced EMPTY files. Use scp.
- `pkill -f <pattern>` can kill your own ssh session when the pattern appears in the command line.
- A `nohup ... &` inside an ssh command keeps the ssh open unless the whole list is redirected. Use `setsid nohup ... > /dev/null 2>&1 < /dev/null &`.
- The old box's `onstart.sh` had no trailing newline, so an appended line got glued onto it. Check with `cat -A`.
- Interruptible boxes get taken away. Stay on-demand for the rest of the day.
- Driver versions differ per host: torch cu126 below driver 570, cu128 at 570 or above.

## Forecast (unchanged)

Central **~0.9909**. New best: about 2 in 3. 0.991 or more: about 1 in 3. 0.9918 or more: under 5%.
