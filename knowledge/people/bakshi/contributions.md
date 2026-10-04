# Contributions: bakshi

What Bakshi built, owned, originated and reviewed, so the deck and the Q&A credit everyone accurately. Code was written by his agents (Codex on 25–27 Sep, Claude Code from 27 Sep) under his direction; the commit author is `trustdemons05`.

**Summary.** Composite B, the final submission, is half Bakshi's: its US/India model (g1w, with his Qwen2.5-7B counted twice), the 7B re-check that dropped 1,150 confident predictions, and the per-country composition. Its France half is Ameya's mixmdp. Bakshi also owned the strict auditor, the hash-gated package builder and the Composite B reproduction driver. His day-1 normalisation and string features were merged but never used by the final chain.

## Built or owned

| what | when | where (paths, PRs) | used in the final submission? |
|---|---|---|---|
| Normalisation v0 (C3): streaming normaliser, lexicons, Indic transliteration, name and address parsers | 25 Sep 16:31–20:55 | `ber/normalize/`, [PR #20] | no (the chain uses Ameya's own text processing, D-FEA-07) |
| String pair features v0 (C8): 56 features, CSR/numba kernels, context join, batch text reuse | 25 Sep 17:05 → 26 Sep 10:12 | `ber/features/{string,tokens,numbers}.py`, [PR #21] | no |
| v7 France diagnostics: composed-edit rules, address guard, rescue probes (all disabled) | 26 Sep 15:32–16:16 | `ber/features/rule_edits.py`, `experiments/bakshi/v7/`, [PR #34] | no |
| v5-based France probe with repetition protection (robust op B is Ameya's rule) | 26 Sep 16:24–16:43 | `experiments/bakshi/v7/robust_drop_probe.py`, [PR #37] | no (never uploaded) |
| Reviews and plans: progress capsule, final-day review, recovery audit, score records | 26 Sep 20:29 → 27 Sep 10:27 | [PR #42], [PR #49], [PR #59], [PR #60]; `plans/bakshi/` | no (records) |
| Strict output auditor: rows, ids, one owner per record, country, matches ⊆ candidates | 27 Sep 00:26 | `final-package/audit_matching.py`, [PR #50] | yes: ships in the ZIP; Ameya ran it on every candidate (D-PKG-04) |
| Hash-gated, deterministic package builder that verifies the extracted archive | 27 Sep 00:31–09:29 | `final-package/make_package.py`, [PR #50], [PR #56], [PR #72] | yes (D-PKG-05) |
| Variant-driven `reproduce.sh` (refuses unrecorded variants) | 27 Sep 02:55–11:08 | `final-package/reproduce.sh`, [PR #56], [PR #72] | yes (`VARIANT=compositeB` is the default) |
| Track B tools and the labelled gate for the cross-encoder mix | 27 Sep 01:14–02:40 | `final-package/{fam_blend,ce_weight_fit,ce_diag}.py`, `TRACK_B_FINDINGS.md`, [PR #54] | the gate's verdict (equal `cem`, no tuning) is in the mix (D-CE-14) |
| Screens that closed dead ends: CE disagreement, rule populations, consensus, footprints, recall | 27 Sep 02:20–12:28 | `final-package/`, `experiments/bakshi/recovery/`, [PR #56] | no (negative results) |
| `MODEL_CHOICE.md`: pick v7sq-dpc | 27 Sep 09:15 | [PR #56] | superseded (v7sq-dpc scored 0.990545) |
| Final-push box scripts: setup, phase A/B, (s1, r) remap, 7B training one group per GPU, merge, backups | 27 Sep 13:00–17:20 | `experiments/bakshi/box/` ([PR #62]) | yes |
| g0, the rebuild of v7sq on a rented box (gate V0) | 27 Sep 14:00–17:20 | `box/phaseA.sh`, `box/phaseB.sh` | the base of g1w |
| q7st: Qwen2.5-7B LoRA cross-encoder, 3 out-of-fold groups, France self-trained | 27 Sep 14:26–17:12 | `box/llm_group.py`, `box/llm_merge.py` (Ameya's `ce_llm_st.py` recipe, Sachi's `ce_llm.py`) | yes: in g1w's mix ×2 and as the re-checker |
| q34st: Qwen3-4B cross-encoder | 27 Sep 14:26–18:43 | same | no (used only in the B5–B8 ladder) |
| g1w: stage-2 mix with the 7B counted twice | 27 Sep 17:18–18:07 | `box/phaseB.sh` variants | yes: US/India of Composite B |
| The 7B re-check of confident predictions (drop if logit < −6) | 27 Sep 17:36–19:28 | `box/rescore_export.py`, `box/score_pairs.py`, `box/rescore_eval.py`, `box/analysis/export_usin.py` | yes: 840 French + 310 US/India drops in Composite B |
| Composite A / B / B′ and `compose_tsv.py` | 27 Sep 18:30–19:41 | `box/compose_tsv.py` ([PR #62]) | yes: Composite B, public LB 0.990879 |
| B+ and the French drop ladder B3–B8 | 27 Sep 22:02–23:34 | `box/bplus_tsv.py`, `box/fr_drop_ladder.py` | B7 was the last upload (0.990875, a tie) |
| Paste-ready documentation of the 7B, `SOLUTION_DOC_compositeB.md`, record drafts | 27 Sep 20:08–23:45 | `box/COMPONENTS_FOR_DOC.md`, `final-package/` | parts used in the final document |
| ZIP work for Composite B: methodology, as-run record, evidence scripts, runnable driver, pins | 29 Sep 00:56–01:50 | `final-package/METHODOLOGY_bakshi.md`, `REPRO_compositeB.sh`, `box/compositeB.sh`, `requirements.txt`; [PR #70], [PR #72] | yes (`src/box/` in the ZIP) |
| Compute for the push: rented and ran the pipeline and training boxes; Drive backups | 27 Sep 13:54 → 28 Sep | Vast.ai; Drive folder `grenuke-train-backup` | — |

## Ideas I originated (even if someone else built them)

Ideas from Bakshi's agents are listed when the agent proposed them for him; the source says which.

| idea | when | what happened to it | source |
|---|---|---|---|
| Build v7 alone instead of submitting v6 | 26 Sep 15:28 | v7 shipped nothing; the team uploaded v6all anyway | B-D-07 |
| Spend as little as possible: Tracks A/B/C | 26 Sep 23:47 (goal), 23:53 (agent's plan) | Track B became the labelled mix gate (B-D-13); A withdrawn; C rejected | B-D-10 |
| Hand execution to a Claude session | 27 Sep 00:05 | ran the rest of the competition | B-D-11 |
| Rent our own GPUs and act independently | 27 Sep 11:06 | produced g1w and the 7B re-check | B-D-22 |
| Smaller boxes per job instead of one 8× H100 | 27 Sep 13:42 | a 2× RTX 4090 box plus a 4× H100 box | B-D-26 |
| Continuous Drive backup of the training box | 27 Sep 14:06 | saved the 7B run when the box was taken away | B-D-26 |
| Keep the Qwen3-4B | 27 Sep 15:00 | used as the second opinion in the drop ladder | B-D-28 |
| A Codex read-only watcher; relay its advice | 27 Sep 15:51, 17:33 | its "re-check high-confidence French matches outside the band" became the 7B re-check | B-D-29, B-D-31 |
| The 7B re-check rule itself (threshold −6, out-of-band, labelled validation) | 27 Sep 17:36–18:20 | in Composite B | agent for Bakshi (Claude) |
| Count the 7B twice (g1w) | 27 Sep 17:14 | US/India of Composite B | agent for Bakshi (Claude) |
| Compose finals per country (Composite B) | 27 Sep 18:07 | the final submission | agent for Bakshi (Claude); Ameya's `compose.py` did the same for mixmdp |
| Hold the evening's first upload for Composite B | 27 Sep 18:51 | B became the team's best | B-D-33 |
| Push the French drop below −6 (B5–B8, "reduce the gamble and increase the cap") | 27 Sep 23:02–23:22 | B7 tied B | B-D-38 |
| The (s1, r) remap with a coverage gate | 27 Sep 12:49 | used on the boxes | agent for Bakshi (Claude), B-D-24 |
| Verify the archive, not the source | 27 Sep 09:22 | a builder gate; caught a missing `tokens.py` | agent for Bakshi (Claude), B-D-17 |
| Repetition protection for the robust-address drop | 26 Sep 16:29 | not adopted into rules v3 as far as recorded (CF-52p) | agent for Bakshi (Codex) |
| Earlier findings by the Codex agent: the cross-encoder sees only p1 ∈ [0.02, 0.99]; the French rule key `12\|jean` collides (58% of French keys vs 22% US); v6all's fresh-run script misses a baseline file; v6all `--all` calibrates on former holdout labels | 26 Sep 14:56–15:17 | the band blind spot led, a day later, to the 7B re-check; the missing-file bug crashed the 27 Sep rebuild | [chat:bakshi/01a0d754 2026-09-26 15:17] |

## Reviews, checks and help given

| what | when | outcome | source |
|---|---|---|---|
| GitHub review of `main` after rank 15: reproduction bug, `--all` leakage, stale methodology, unpinned torch | 26 Sep 14:47–14:59 | a local report; not acted on in the repo | [chat:bakshi/01a0dd05 2026-09-26 14:58] |
| Review of a pasted "$100 plan" and PR #30's package | 26 Sep 23:39 | PR #49; $0 spent | [chat:bakshi/01a0d754 2026-09-26 23:44] |
| Disputed a pasted "0.991 is impossible" report | 27 Sep 09:49 | PR #59 (bounded recovery plan) | [chat:bakshi/01a0df0b 2026-09-27 09:49] |
| 13 comments on issue #45 and a review of PR #58 (Ameya's stack) | 27 Sep 02:18–10:57 | corrections exchanged both ways (frs2 withdrawn; v7s warning falsified) | [chat:bakshi/b0c6934d 2026-09-27 02:51] |
| Packages audited and built for v7nst, v7nst-dpc, v7sq-dpc, v7ens2, v7qbag, v7sq4 | 27 Sep 01:31–12:14 | a validated package for each measured result | [chat:bakshi/b0c6934d 2026-09-27 11:47] |
| Confirmed mixf2 on #64; approved Ameya's PR #65 (`compose3.py`) | 27 Sep 20:02–20:44 | merged | [chat:bakshi/b0c6934d 2026-09-27 20:44] |
| Verified the final `Grenuke_submission.zip` (8 checks of #75) | 29 Sep 03:43–04:01 | all passed; byte-identical rebuild; 4 wording fixes suggested | [issue #75] |

## What I can explain best to the jury

- **The Qwen2.5-7B cross-encoder (q7st):** LoRA r 16 on all attention and MLP projections, a classification head, bf16; three out-of-fold groups, one per H100; France self-trained from the v7sq-dpc teacher's decisions, cross-fitted by S1 group. Its AUC matched e5-large; its value was diversity in the mix (g1w) and re-reading confident pairs.
- **The 7B re-check:** why 94.5% of final predictions were never read by a cross-encoder; why −6 (labelled holdout: +0.000033, both halves positive; below −6 only 8.3% true); why it is not leakage (equal drop rates by S1 third); what it removes in France (generic-name decoys at another street with the same house number).
- **Composite B:** per-country composition, the one-owner and candidate checks, and the honest split of its +0.000180.
- **Reproducibility:** the strict auditor, the hash-gated builder, the (s1, r) remap, gate V0, and why a rerun is not byte-identical across GPUs.
- **The final day:** how the dead ends were closed by measurement, and what B7 taught (the labelled cut-off was right).
- **Normalisation and string features (day 1):** what they do and why the final chain did not use them.
