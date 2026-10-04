# Sachi: journal

Summary: one entry per working session, in time order. Format: when, goal, what was done, results, decisions, problems,
next. Times are IST. Chat aliases are defined in `sources.md`. Decision and experiment IDs link to `decisions.md` and
`experiments.md`.

---

## 2026-09-25 10:28 to 13:33 · Understand the problem and choose a plan
- **Goal:** read the problem statement and the data description, compare approaches, and get into the team repo.
- **Done:** asked for a ranking of approaches and a stress test of the final design; read Ameya's plan after he pushed it; cloned the team repo and pushed my own plan under `plans/sachi/` (about 13:31).
- **Results:** no numbers. Ameya's plan became `plans/FINAL_PLAN.md`; mine stayed a candidate plan.
- **Decisions:** none of mine.
- **Problems:** repo access took several tries (a deleted fork, then direct access).
- **Next:** take the model tasks assigned to me (#8, #9).
- **Source:** [chat:sachi/web-1 2026-09-25 10:28 to 13:33]

## 2026-09-25 16:19 to 18:00 · Model v0 and gate G6
- **Goal:** build the baseline model stages (issues #8, #9) and run gate G6.
- **Done:** set up `experiments/sachi/` (dev-feature builder, dev and real runners, tests); ran on the dev kit; wrote the G6 record; fixed the ownership step; opened [PR #16] (merged by Ameya). My follow-up commit moved the code into `ber.model` so the pipeline stages train, predict, decide run; Ameya rebased it and opened it as [PR #17].
- **Results:** dev kit fold 0 macro F0.5 0.9649 with the dev runner and 0.9652 through the pipeline stages; G6 delta -0.00024, then -0.00044 (S-X-01).
- **Decisions:** S-D-01, S-D-02.
- **Problems:** issues #8 and #9 stayed open after the first PR; the test file for `decide` shadowed the stage name and was removed. [PR #17]'s checklist records that the model-v0 handover was not included.
- **Next:** wait for Ameya's full features.
- **Source:** [chat:sachi/web-1 2026-09-25 16:19 to 18:00]

## 2026-09-25 20:54 to 23:37 · Features v2, three gates, and a sync
- **Goal:** use Ameya's v2 features, run the follow-up gates, answer his agent's questions.
- **Done:** got Ameya's v2 features at 20:54. At 20:55 re-ran G6 on model v2 probabilities (S-X-15); at 21:03 ran gate G4, stage 2 against stage 1 (S-X-16); ran an error analysis of model v2 (S-X-17); at 21:15 ran the name-uniqueness gate (S-X-02). At 23:29 his agent asked what I had run and noted nothing from me was on GitHub after 18:00.
- **Results:** G4 +0.00692, kept (S-D-16); name-uniqueness +0.00054, rejected (S-D-03); G6 on v2: DP +0.00010 over the threshold, threshold kept.
- **Decisions:** S-D-01 (update), S-D-03, S-D-16.
- **Problems:** I had no status file or handover on the repo yet. The agent asked me to port stage 2 and the expected-F0.5 decision into `ber.model`, build the France-emptied probe, and recalibrate the "no match" probability. The port was not started yet at 23:33; it followed overnight and became [PR #27] (next entries).
- **Next:** port v3, the probe script, status and handover.
- **Source:** [chat:sachi/web-1 2026-09-25 20:54 to 23:37], [G6 record](../../../docs/decisions/2026-09-25_1731_gate-g6-dp-vs-threshold.md), [G4 record](../../../docs/decisions/2026-09-25_2103_gate-g4-stage2.md), [name-uniqueness record](../../../docs/decisions/2026-09-25_2111_gate-name-uniqueness.md)

## 2026-09-26 10:09 to 13:04 · LOCO studies, France kit v1
- **Goal:** find out whether a feature group causes the unseen-country drop; look for French patterns.
- **Done:** at 10:09 drafted the summary for porting Ameya's v3 chain into `ber.model` ([PR #27], merged; synthetic-data tests only, S-D-17); committed package drafts ([PR #30]: reproduce scripts, README, requirements); ran `loco_groups.py` (it stalled on the laptop for a long time); ran the France kit analyses.
- **Results:** no feature group explains the gap; edit-profile features +0.0005 (S-X-03, S-X-04); no new French rule (S-X-05).
- **Decisions:** S-D-04, S-D-05.
- **Problems:** the laptop is slow on large runs; the chat's 20-file upload limit made it hard to show the assistant all of Ameya's files, so I used a one-file dump script.
- **Next:** test e5-base against e5-small; talk to Ameya.
- **Source:** [chat:sachi/web-2 2026-09-26 10:09 to 13:04]

## 2026-09-26 17:04 to about 22:00 · e5-small vs e5-base, first rented GPU
- **Goal:** run `ce_compare.py` at a useful size.
- **Done:** three failed laptop runs (memory), then a rented RTX 3090. The first rented host could not pull the container image; the second ran but had no copy of my access key because the key was added after the machine was created; the third worked.
- **Results:** e5-base 10.0 percent log-loss reduction against 6.5 percent for e5-small; AUC 0.9666 vs 0.9647 (S-X-06).
- **Decisions:** S-D-06, S-D-15.
- **Problems:** lost about 4.5 hours to memory and host problems. Ameya's H100 runs on the full band (decision record, 2026-09-26 19:33) had already measured e5-base and e5-large before my result came in, and I only saw them after pulling main at about 22:00. My comparison duplicated his work. Whether I messaged him my result: unknown.
- **Also:** at about 21:56 I rented a 192-core machine to rerun the whole v6all recipe with e5-base, then did not use it after reading his decision record (S-D-15).
- **Next:** try a different model family.
- **Source:** [chat:sachi/web-3 2026-09-26 17:04 to 22:00]

## 2026-09-26 22:57 to 2026-09-27 early morning · Qwen2.5-1.5B LoRA cross-encoder
- **Goal:** build and run a decoder-model cross-encoder on the band.
- **Done:** wrote `ce_llm.py`; set up a new RTX 4090 (the script file had not been copied up and I recreated it on the machine); smoke test at about 23:18; full run started 23:29 with 35 percent of the data; committed `ce_llm.py` at 23:37 ([commit 5bff1e7]) with a handover (`docs/handover/2026-09-26_1800_sachi_llm-cross-encoder.md`); followed the run until group 2 had finished training. Destroyed the machine before the run ended.
- **Results:** group 1 out-of-fold AUC 0.9279 (S-X-07).
- **Decisions:** S-D-07.
- **Problems:** silent scoring phases (about 55 minutes per group) looked like a stall; a nested terminal session and an empty log file cost time; destroying the machine lost all three groups' outputs.
- **Next:** hand the idea to Ameya, who rebuilt it as `qst` with self-training.
- **Source:** [chat:sachi/web-3 2026-09-26 22:57 to 2026-09-27 03:30]

## 2026-09-27 08:26 to about 11:15 · reproduce_v7sq.sh, 7B smoke tests
- **Goal:** help the final package and test the recipe at 7B.
- **Done:** read the stack scripts and the v7nst reproduction script; wrote `reproduce_v7sq.sh` and pushed it to `ameya/final-stack` ([commit 99a404d], visible in PR #58 at 08:41); rented RTX 4090s for 7B smoke tests.
- **Results:** 7B smoke: AUC 0.6761 on one machine; NaN scores on another (S-X-08).
- **Decisions:** S-D-08, S-D-14.
- **Problems:** the 7B run on the second machine gave NaN scores. Ameya later dropped `reproduce_v7sq.sh` from his branch.
- **Also:** at 08:28 I was ready to train mDeBERTa-v3-base as a fifth cross-encoder family; I did not start it once the stack was frozen (S-D-14).
- **Next:** the final-day analysis.
- **Source:** [chat:sachi/web-3 2026-09-27 08:26 to 11:15]

## 2026-09-27 13:24 to 15:00+ · Copy-count test, synthetic French
- **Goal:** find a new lever for France.
- **Done:** `size_bias_owner.py` (13:24); `synth_fr.py` and `ce_synth.py`; a rented 4090 for the synthetic trainer; stopped the run after reading #63.
- **Results:** S-X-09 (coin flips), S-X-10 (99,702 pairs; run stopped at step 9,800 of 26,609).
- **Decisions:** S-D-09.
- **Problems:** `ce_synth.py` crashed in `encode_synth` (a Series method); I fixed it on the box. A PR of mine for these merged with no files (see 29 Sep).
- **Next:** more audits on France kit v1.
- **Source:** [chat:sachi/web-3 2026-09-27 13:24 to 15:00]

## 2026-09-27 18:09 to 22:30 · Audits, upload discussion, leaderboard results
- **Goal:** analyse everything the others had done; check Ameya's French pattern; weigh in on the final upload.
- **Done:** read the final-day notes and the final-push plan; ran `tie_audit.py` (18:30) and `street_swap.py` (18:48); commented on #64 about mixf2 vs mixf4; then read the leaderboard results at 22:15.
- **Results:** S-X-11, S-X-12, S-X-13. mixf2 0.990819, mixf7 0.990833, Composite B 0.990879 (public LB).
- **Decisions:** S-D-10, S-D-11, S-D-12.
- **Problems:** my first tie-audit run had an artefact (rule adds counted as model predictions). My cal over-prediction figure was wrong (a third; Ameya's correction: about 9 percent). I argued for mixf2 and against the France DP; the leaderboard showed the DP was real.
- **Next:** the package and the finale.
- **Source:** [chat:sachi/web-3 2026-09-27 18:09 to 22:30], [issue #64]

## 2026-09-28 to 2026-09-29 · Package checks and the #66 items
- **Goal:** answer the #66 checklist (items A to D) and get my audit scripts onto main.
- **Done:** checked that `ce_llm.py` has one commit on main and that `ce_llm_st.py` imports it (line 37); stashed the local `--test-once` patch; checked Hugging Face revisions; grepped for imports of `ber.model` and `experiments/sachi/model`; found that [PR #67] had merged with no files (the commit was on my local `main`); created a branch from `origin/main`, copied the four files, pushed, and the second PR merged.
- **Results:** items A to C answered; three scripts and a one-line `ce_synth.py` fix are on main (merge brought main from `8f6c0ec` to `787fa8d`).
- **Decisions:** S-D-13.
- **Problems:** I ran `git reset --hard origin/main` once before the PR merged; nothing was lost because the branch had been pushed.
- **Next:** the README dry run when Ameya pings me.
- **Source:** [chat:sachi/web-3 2026-09-28 to 2026-09-29], [issue #66]

## 2026-10-03 night · Final ZIP check
- **Goal:** open the shared `final_zip` folder and confirm the TSVs.
- **Done:** downloaded the folder, listed its files, hashed the TSVs.
- **Results:** both hashes equal Composite B (S-X-14). The submission ZIP itself was not available on my laptop, so I did not check its contents.
- **Next:** knowledge capture (#81) and the team call.
- **Source:** [chat:sachi/web-3 2026-10-03]

## 2026-10-04 · Knowledge capture (this folder)
- **Goal:** write `knowledge/people/sachi/` for [issue #81].
- **Done:** read the standard and capture kit; wrote these files from my chats and the repo records pasted into them. The deadline of 12:00 had passed; I told Ameya the PR would follow.
- **Next:** review the unsure list in `open-questions.md`; open the PR from `sachi/kb-capture`.
