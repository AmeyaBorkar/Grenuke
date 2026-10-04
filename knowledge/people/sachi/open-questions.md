# Sachi: open questions

Summary: facts that are unknown, conflicting or that only Sachi, Ameya or Bakshi can confirm. Nothing here was guessed
into the other files. Questions answered on 4 Oct from git, the PR pages and the decision records are kept, marked
**Answered**, so the trail stays visible.

## 1. For Sachi to confirm

| # | question | where it matters |
|---|---|---|
| Q-01 | Did I send Ameya the LOCO and France-kit findings on 26 Sep (about 13:04), and the e5-small vs e5-base result that evening? What did I write? | journal 26 Sep, S-X-03, S-X-05, S-X-06 |
| Q-02 | Is `france_probe.py` on `main`? **Answered 4 Oct: no.** It is not on main and in no commit on any branch (`git log --all`). The assistant in my 25 Sep chat said it was in my commit; git does not show that. The France-emptied probes in Ameya's records (for example probe-v7-fr0) are his packages. Still to check: an untracked copy on my laptop. | contributions §1 |
| Q-03 | LOCO unseen-country gap: my run gave about 0.028, Ameya quoted 0.024. Which is right, and why do they differ? | S-D-04, numbers §2 |
| Q-04 | File names of my decision records. **Answered 4 Oct:** `2026-09-25_1731_gate-g6-dp-vs-threshold.md`, `2026-09-25_2103_gate-g4-stage2.md`, `2026-09-25_2111_gate-name-uniqueness.md`. | S-D-01, S-D-03, S-D-16 |
| Q-05 | Gate bar for name-uniqueness. The records say +0.002 with the 95% CI above 0 (plan §5.4). But my [PR #27] description (26 Sep) says the plan's actual rule is delta above 0 with the CI lower bound above 0, and calls +0.002 my earlier loose heuristic. Under the CI-only rule name-uniqueness (CI lower bound +0.00001) would just have passed. Which is right? See Q-25. | S-D-03 |
| Q-06 | Are PR #16 and #17 mine? **Answered 4 Oct from the PR pages:** #16 is mine (opened by me, merged by Ameya, branch `sachi/model-v0`, 9 files, +776). #17 was opened by Ameya with my follow-up commit rebased onto main (branch `ameya/sachi-model-stages`, 7 files, +544 -33, closes #8 and #9). | S-D-01, journal 25 Sep |
| Q-07 | Did I port stage 2 and the expected-F0.5 decision into `ber.model`? **Answered 4 Oct (corrected): yes.** [PR #27], opened by me and merged, is titled "feat(model): port v3 (stage 2, legal features, cluster support, all-candidate decision) into ber.model"; my 26 Sep 10:09 chat holds its draft description. An earlier version of this answer said no, based on a `git log --author` filter on `src/ber/model` that showed only `fd7bf67`; that filter missed it (see Q-26). | contributions §1, S-D-17 |
| Q-08 | Total GPU spend and total credit added. I only have snapshots ($4.78, $9.71, $7.90, $5.48). Check the Billing page. | numbers §8 |
| Q-09 | When exactly did I destroy the first RTX 4090 machine (27 Sep, early morning), and what was its total run time? | S-X-07 |
| Q-10 | Group 0 and group 2 out-of-fold AUCs of my Qwen2.5-1.5B run: I never saw them. Are they in a log I still have? | S-X-07 |
| Q-11 | Was the first local `ce_compare.py` stall a network or a memory problem? I read it as network first, but the later failures were memory. | S-D-06 |
| Q-12 | The 7B NaN: divergence in training, or bf16 overflow? Not diagnosed. | S-X-08 |
| Q-13 | Effect of the ownership fix. **Not isolated (4 Oct).** The G6 record says its numbers (threshold 0.9649, DP 0.9647, delta -0.00024, CI [-0.00091, +0.00049]) were produced after the fix, yet PR #16 reports almost the same (0.9648, delta -0.0002, CI [-0.0009, +0.0005]). PR #17 shows 0.9648 then 0.9652 and credits the fix, but 0.9652 is the pipeline-stage run (threshold 0.71) and the dev runner used 0.70. PR #16 says 0.9648 where the record's evaluator says 0.96492. | S-D-02 |
| Q-14 | Qwen2.5-1.5B revision: verified against the Hub on 2026-09-29. Was the model I trained on 26 Sep the same revision? The log line shows the same hash (`8faed761...`), but I did not re-check the log. | numbers §4 |
| Q-15 | The submission ZIP (`Grenuke_submission.zip`, 88,353,544 bytes on Drive): did it contain the TSVs, the README and the documentation? I only checked the TSVs in the `final_zip` folder. | S-X-14 |
| Q-16 | Times from rented machines were converted from the machine's UTC clock (+5:30) and are approximate. | numbers §4, S-X-07 |
| Q-17 | Did Ameya originate an LLM cross-encoder before my proposal? I credit the LoRA Qwen cross-encoder to me; his zero-shot LLM test (AUC 0.537) came from his side. | contributions §2 |
| Q-18 | Handover and status. **Answered 4 Oct:** main has `docs/handover/2026-09-26_1800_sachi_llm-cross-encoder.md` only. There is no model-v0 handover and no `docs/status/sachi.md`; PR #17's checklist says the v0 handover was not included. | journal 25 Sep |
| Q-25 | Keep rule for gates. The G6, G4 and name-uniqueness records say +0.002 with CI above 0 (plan §5.4). My PR #27 description says the plan's actual rule (plan §9) is delta above 0 with the CI lower bound above 0, ties to the simpler option. Read `plans/FINAL_PLAN.md` §5.4 and §9 and fix whichever of my pages is wrong (S-D-01, S-D-03, S-D-16). | S-D-01, S-D-03, S-D-16 |
| Q-26 | Why did `git log origin/main --author=ssdhoka06 -- code/business_entity_resolution/src/ber/model` show only `fd7bf67`, when PR #27 ported the v3 chain there? Check the commit authors and paths on PR #27's Commits and Files tabs. | contributions §1 |
| Q-27 | The PR list shows 10 closed PRs of mine and I saw 9. What is the tenth, and what exactly did PR #30, #39, #46 and #61 contain (file lists, dates)? | contributions §6 |

## 2. For the curator or other members

| # | question | owner |
|---|---|---|
| Q-20 | Which upload is the final one: Composite B (AGENTS.md and the ZIP) or B+ (Composite B plus 8 decoys, Ameya's 22:15 comment in #64)? Was B+ uploaded, and what did it score? | Ameya |
| Q-21 | Baseline v0: what was the public LB score of the first submission, and who uploaded it? My chats name only the holdout (0.9683 in Ameya's records). | Ameya |
| Q-22 | The `qst` group-0 AUC (0.9334, Ameya) against my group-1 AUC (0.9279): different data and self-training make them not comparable. Should `knowledge/` say so? | curator |
| Q-23 | Nothing imports `ber/model` or `experiments/sachi/model/`: I grepped his drivers and Bakshi's box scripts. An import written as `from ber import model` would not have matched. I did not run that second grep. | Ameya |
| Q-24 | `reproduce_v7sq.sh`: Ameya dropped it from his branch (commit 21bf128). Is there a copy worth keeping in `knowledge/`? | Ameya |

## 3. Conflicts between sources

- **LOCO gap:** 0.024 (Ameya, 26 Sep) against about 0.028 (my run). Not reconciled.
- **Final upload:** AGENTS.md says Composite B; Ameya's #64 comment (22:15) says B+; Bakshi's later note mentions B7 (0.990875). The jury story should use Composite B (0.990879) unless Ameya says otherwise.
- **Baseline numbers:** PR #16 says 0.9648, the G6 record's evaluator says 0.96492 for what looks like the same run (see Q-13).
- **Direction of my street-swap reading:** my own first reading (France under-keeps the pattern, so dropping would hurt) differs from the final design (drop only where the 7B rejects). Both are recorded in S-D-11; the table that explains the difference is Ameya's.
- **Time of the name-uniqueness record:** its Date field says 21:15, its file name says 2111. I use 21:15.
- **Keep rule for gates:** the decision records say +0.002 with the CI above 0; my PR #27 description says delta above 0 with the CI lower bound above 0 (see Q-25).

## 4. A note on templates

If `python scripts/new_doc.py person --member sachi` created different file names or headings than these pages use, move the content
into those files; it follows the formats in `knowledge/STANDARD.md` §2.
