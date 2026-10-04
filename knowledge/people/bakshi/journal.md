# Journal: bakshi

One entry per working session, in time order (`knowledge/STANDARD.md` §2.5). Times are IST. Bakshi worked through two agents: Codex (main session `01a0d754`, 25–27 Sep; a watcher session `01a0e269` from 27 Sep) and Claude Code (session `b0c6934d`, 27 Sep onward). Sources are listed in `sources.md`.

**Summary.** 25 Sep: normalisation and string features, merged but unused. 26 Sep: a France "v7" audit that shipped nothing, then review and planning. 27 Sep: the package auditor and builder, six negative screens, then a rented-GPU push that produced g1w, the 7B re-check and Composite B, the team's best upload. 28–29 Sep: the generalisation check and the final ZIP.

## 2026-09-25 12:21–12:51 · Kick-off: how to win
- **Goal:** Bakshi: "how should we approach this such that we end up winning" [chat:bakshi/01a0d754 2026-09-25 12:21].
- **What was done:** the Codex agent read the problem statement and rules with four sub-agents (rules, strategy, metric, resources) and proposed a strategy: multi-view retrieval, an oracle ceiling, a pair classifier on hard negatives, a threshold tuned on macro F0.5, an explicit no-match decision. It audited the 7 TSVs.
- **Results:** 24,229,173 rows; train S1 2,206,821 (US 1,323,633, India 883,188); test S1 1,732,544 (France 259,452); 7,638,365 true links; 5.585% singletons; predicting nothing scores macro F0.5 0.05585 on train [M] [chat:bakshi/01a0d759 2026-09-25 15:18].
- **Decisions:** B-D-01 (no Plan C).
- **Problems:** the agent assumed four teammates; nothing reached the repo.
- **Next:** the dataset path and "continue with the plan".

## 2026-09-25 15:15–17:22 · Prototype, repo access, normalisation and features
- **Goal:** "continue with the plan"; then the work assigned to Bakshi.
- **What was done:**
  - 15:15–15:55: a stand-alone prototype and a full-pool retrieval probe while the private repo returned 404 (B-X-01, B-X-02). Bakshi stopped it: "what are you even doing".
  - 15:59–16:23: repo access (SSH key, then a token; the approval reviewer refused two over-broad actions).
  - 16:29: Bakshi: "yea go ahead if you see any work assigned to aarush bakshi / bakshi just do it". Issues #5, #6, #7.
  - 16:31–17:20: C3 normalisation (`bakshi-norm-v0`, then v0a with an address-order fix) and C8 string features in a second worktree.
- **Results:** B-X-03; first feature tests pass.
- **Decisions:** B-D-02, B-D-03, B-D-04, B-D-05.
- **Problems:** about 65 minutes lost on repo access; from 17:22 to 20:37 the session stalled because the Codex approval reviewer hit its usage limit. Issue #6 was due at 18:00.
- **Sources:** [chat:bakshi/01a0d754 2026-09-25 15:15]–[chat:bakshi/01a0d754 2026-09-25 17:22]; reviewer sessions `01a0d759`, `01a0d828`.

## 2026-09-25 20:37–22:24 · PRs #20 and #21
- **What was done:** PR #20 (normalisation) opened 20:49 and merged 20:55 by Ameya. Dev-kit feature benchmark, a 2× speed-up, PR #21 opened 21:05 (merged 26 Sep 10:12). Setup issue #5 ticked.
- **Results:** B-X-03, B-X-04.
- **Problems:** at 22:18 Bakshi asked for a matching TSV to upload; none existed on GitHub, and he stopped the agent from generating one: "stop dont do that" [chat:bakshi/01a0d754 2026-09-25 22:24].
- **Next:** none that evening.

## 2026-09-26 14:47–16:43 · Rank 15, the decision to build "v7", the France audit
- **Goal:** "check the github we are 15th in rank … go thoroughly through github" [chat:bakshi/01a0d754 2026-09-26 14:47].
- **What was done:**
  - A full GitHub review: 108 tests pass on `main` `faa0244`; a fresh-run bug in `reproduce_v6all.sh` (it needs `ameya-baseline-v0`, never built); v6all's `--all` calibration uses former holdout labels; the final chain does not use Bakshi's C3/C8 stages.
  - Five "wow factor" ideas, cut to two by a pasted review (author not named). 15:28: Bakshi chose to build v7 alone.
  - The composed-edit and address-guard audit (PR #34), the v5 TSV audit, two rescue probes, and Ameya's robust-B rule with repetition protection (PR #37).
- **Results:** B-X-05 to B-X-10; nothing with a measured gain.
- **Decisions:** B-D-07, B-D-08, B-D-09.
- **Problems:** the full v6 artifacts were only on Ameya's integration machine; PR #34 had already been merged when the agent pushed to it.
- **Sources:** `01a0d754` p02–p03; reviewer sessions `01a0dd01`, `01a0dd05`, `01a0dd57`.

## 2026-09-26 18:56–20:29 · Ideas and a progress capsule
- **What was done:** Bakshi asked for ideas only. The agent compared Ameya's v6 candidate file with v5 (B-X-11) and noted French words such as "groupe" penalised too hard. At Bakshi's request it wrote `experiments/bakshi/PROGRESS_CAPSULE.md` (PR #42).
- **Results:** 2,452 French pairs accepted by v5 are missing from v6's candidates [E].
- **Problems:** Bakshi's "my friend made something, which scored much better" is not tied to any upload record (CF-52j).

## 2026-09-26 23:17 → 27 Sep 00:18 · The final-day plan, a low-cost strategy, the handover to Claude
- **What was done:**
  - Reviewed a pasted "$100 plan" and the stale PR #30 package (PR #49; $0 spent). From v7n (0.989721) to 0.99 needed only +0.000279.
  - 23:48: Bakshi reported v7nst at public LB 0.990179. The agent wrote `LOW_COST_0991_STRATEGY.md` (B-D-10); a teammate-side review agreed and cut Track C.
  - 00:05: Bakshi asked for a plan for Claude Opus to take over; the agent wrote `plans/bakshi/CLAUDE_OPUS_TAKEOVER.md` (B-D-11).
- **Problems:** at 00:18 the approval reviewer hit its usage limit again; the handover file was written but not published from Codex.
- **Sources:** `01a0d754` p03; reviewer sessions `01a0dee2`, `01a0df0b`.

## 2026-09-27 00:20–03:09 · Claude takes over: auditor, package, Track B
- **Goal:** protect v7nst (0.990179) and look for 0.991 at the lowest cost.
- **What was done:**
  - The strict auditor and the hash-gated builder (PR #50, merged 01:55); the 3,790-pair candidate gap and its exact prediction (B-X-12, B-X-13).
  - Track B rounds 1–3 (B-X-14, B-X-15, B-X-17), the rule-population check (B-X-16); PR #54 (merged 02:48), PR #56.
  - 02:03: Bakshi: "from now on communicate using github with ameya"; issue #45 comments 1–5.
  - Bakshi: "continue please without compromising … ask me to make the descison dont assume" (01:05), saved as a working rule.
  - 02:32, asked what it had improved, the agent said: "nothing I did made the model better … No change of mine has moved a leaderboard score."
- **Decisions:** B-D-12, B-D-13, B-D-14, B-D-15.
- **Problems:** Track B was closed too early at 01:43 (no bge yet) and reopened at 02:05; the `frs2` recommendation was retracted after Ameya's evidence.
- **Next:** 03:09 → 09:03 Bakshi slept.

## 2026-09-27 09:03–11:00 · Rank 15, the pick, the screens, two scores
- **What was done:**
  - 09:03: Bakshi: "our highest score has dropped to rank 15 and first rank is at .991483". 09:11: "pick a model"; the agent picked v7sq-dpc (B-D-16).
  - Screens: CE disagreement (B-X-18, anti-selective), France sensitivity (B-X-19, later retracted), the broken-archive bug (B-X-20).
  - Codex in parallel: `RECOVERY_0991.md` (draft PR #59), then Bakshi reported v7sq-dpc at public LB **0.990545** (10:07) and v7nst-dpc at 0.990264 (10:21) (PR #60, B-X-21); the alias audit (B-X-22).
  - Claude: the bridge audit (B-X-23); the v7nst-dpc and v7sq-dpc packages audited; "restore the best" as a hard rule (B-D-20).
- **Decisions:** B-D-16 to B-D-20.
- **Sources:** `b0c6934d` p02; `01a0d754` p03; reviewer `01a0df0b`.

## 2026-09-27 11:06–13:27 · Going independent: the plan for the push
- **What was done:**
  - 11:06–11:16: Bakshi decided to rent Vast.ai GPUs and act independently, and to relay asks to Ameya himself (B-D-22, B-D-14).
  - The last screens: structural recall (B-X-24), footprints (B-X-25), consensus (B-X-26).
  - 12:31–13:20: the plan "from the base": a partial rebuild plus one model bet, which swung from Qwen2.5-7B to diversity models and back to Qwen2.5-7B + Qwen3-4B (B-D-23). The LOCO ladder (B-X-27) and the (s1, r) remap (B-X-28, B-D-24) were checked.
  - 13:15: Bakshi: "just verify we can use vast ai for hard ware dont waste too much time with local verification" (saved as a working rule). 13:26: one ask message for Ameya.
- **Results:** forecast central 0.9909–0.9910, ≥0.991 about 1 in 3 [E].
- **Decisions:** B-D-21 to B-D-25.

## 2026-09-27 13:32–19:59 · The final push on rented GPUs
- **Goal:** beat 0.990545 and push toward 0.991; Bakshi: "the best upload counts not the latest one so we have 3 left" (13:35).
- **What was done:**
  - Boxes: 2× RTX 4090 pipeline box, interruptible 4× H100, Drive backup every 5 minutes (B-D-26). PR #62 opened 14:17.
  - The pipeline box rebuilt v7sq as g0 (B-X-29). The H100s trained q7st (B-X-30) and q34st (B-X-31); mDeBERTa and gte failed (B-X-32).
  - About 15:05 the interruptible box was taken away; training resumed from Drive on an on-demand box at 15:44.
  - 15:51: a Codex session became a read-only watcher (B-D-29). At 17:32 it suggested re-checking confident French predictions; at 17:33 Bakshi relayed it.
  - 17:18–19:22: mix ablations, g1w best (B-X-33). 17:36–18:20: the 7B re-check, +0.000033 on the local holdout (B-X-34). Loss anatomy and recall slices (B-X-35 to B-X-38).
  - 18:36: Ameya's notes identified the 0.990699 upload as mixmdp. 18:51: Bakshi: "we are not uploading till composite b". 19:41: Composites A, B and B′ built (B-X-39).
  - 19:45: commit `726235e` with `FINAL_PUSH_RESULTS.md`; 19:59: issue #64 (Ameya: one upload tonight, mixf2).
- **Decisions:** B-D-26 to B-D-34.
- **Problems:** CRLF line endings broke the new box's setup (about 12 minutes of idle GPUs); a stage-1 crash on a missing baseline file; overdue backups (fixed 17:35); a synthetic-French job from the `sachi` folder ran on the pipeline GPU.
- **Sources:** `b0c6934d` p03; `01a0e269`, reviewers `01a0e26a`, `01a0e284`, `01a0e28c`, `01a0e2b4`, `01a0e2bb`.

## 2026-09-27 20:00–23:58 · The uploads
- **What was done:**
  - 20:02: mixf2 confirmed on #64 (B-D-35). 20:44: PR #65 approved; second slot changed to Composite B.
  - 20:49: Bakshi chose to upload Composite B ("i will upload it now"): **0.990879**, rank 16 (B-D-36). 22:01: mixf2 0.990819, mixf7 0.990833.
  - 22:02–23:34: B+, then B++ and B3–B8 as Bakshi asked for more (B-X-42 to B-X-47); external chatbot ideas triaged; drop mining overfit; the CE blend dropped. 22:28: the agent declined to look at another team's solution (B-D-37). The Codex watcher's oracle best-of-6 showed only +0.000273 (B-X-43).
  - 23:36: Bakshi chose B7 as the last upload ("we are uploading this as our final"): 0.990875 (B-D-38).
  - 23:41–23:58: `SOLUTION_DOC_compositeB.md` and record drafts; the agent flagged on #64 that the artefacts must describe Composite B.
- **Decisions:** B-D-35 to B-D-38.
- **Sources:** `b0c6934d` p04; `01a0e269`, reviewer `01a0e3be`.

## 2026-09-28 13:08–13:18 · Does it generalise?
- **What was done:** the pipeline box was gone, so the agent pulled holdout decisions from Drive and simulated public/private splits (B-X-48). Bakshi allowed outside data; the agent advised against a Fodors–Zagat test (B-D-40).
- **Results:** gap sd 0.00016; the drop rule positive in 99.7% of subsets [M].

## 2026-09-29 00:51–04:01 · The final ZIP
- **What was done:** issue #66 and #69: as-run box scripts, `REPRO_compositeB.sh`, `METHODOLOGY_bakshi.md`, `requirements_box.txt` (PR #70). Issue #71: two corrections and two evidence scripts, then the runnable driver `compositeB.sh` and package changes (PR #72, PACKAGE OK, B-X-49). Issue #75: verified Ameya's final ZIP, all 8 checks passed (B-X-50).
- **Decisions:** B-D-39.
- **Problems:** the boxes were destroyed before a `pip freeze`, so pins were reconstructed from logs; Sachi's PR #67 merged with 0 files changed.
- **Next:** the agent listed manual steps for Bakshi: share the Drive folder, destroy the Vast instances, revoke the token, remove the SSH key, revoke rclone access.

## 2026-10-04 13:45–14:30 · A first finale deck (Codex)
- **What was done:** after the Top-10 e-mail (finale Wed 7 Oct; deck due by survey; the e-mail says "Monday, 6 October", which is a Tuesday), the Codex agent built an 11-slide draft from the Amazon template, a local file not in the repo. Bakshi confirmed Composite B (0.990879) as "the final model" [chat:bakshi/01a0e269 2026-10-04 14:15].
- **Problems:** its numbers come from a pasted handover, not `knowledge/numbers.md`; the curated deck in `finale/` should win.

## 2026-10-04 22:34–23:30 · Knowledge capture (#80)
- **Goal:** Bakshi's capture into `knowledge/people/bakshi/` (issue #80, due 4 Oct 12:00, late).
- **What was done:** digests of 24 Codex rollouts and 3 Claude Code sessions with `scripts/kb/digest_transcripts.py`; every digest read in full by parallel readers; these seven files written from their notes and checked against the repo and the KB.
- **Next:** Bakshi confirms the open questions; the curator maps B-D/B-X IDs to global IDs.
