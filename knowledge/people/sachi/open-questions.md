# Sachi: open questions

Summary: facts that are unknown, conflicting or that only Sachi, Ameya or Bakshi can confirm. Nothing here was guessed
into the other files. Sachi to answer the first block before the PR; the curator may take the second block.

## 1. For Sachi to confirm (before the PR)

| # | question | where it matters |
|---|---|---|
| Q-01 | Did I send Ameya the LOCO and France-kit findings on 26 Sep (about 13:04), and the e5-small vs e5-base result that evening? What did I write? | journal 26 Sep, S-X-03, S-X-05, S-X-06 |
| Q-02 | Is `france_probe.py` on `main`? Was the France-emptied upload built from it? | contributions §1 |
| Q-03 | LOCO unseen-country gap: my run gave about 0.028, Ameya quoted 0.024. Which is right, and why do they differ? | S-D-04, numbers §2 |
| Q-04 | What are the file names of my three decision records (G4, G6 on v2, name-uniqueness)? | S-D-01, S-D-03 |
| Q-05 | What was the gate bar for name-uniqueness on 25 Sep (`plans/FINAL_PLAN.md` §9)? | S-D-03 |
| Q-06 | [PR #16] and [PR #17]: are these my PRs? I took the numbers from Ameya's agent message ("#17 was the last", "the old #16 commit"). | S-D-01, journal 25 Sep |
| Q-07 | Did I start the port of stage 2 and the expected-F0.5 decision into `ber.model` that Ameya's agent asked for on 25 Sep 23:29? I believe not. | contributions §4 |
| Q-08 | Total GPU spend and total credit added. I only have snapshots ($4.78, $9.71, $7.90, $5.48). | numbers §8 |
| Q-09 | When exactly did I destroy the first RTX 4090 machine (27 Sep, early morning), and what was its total run time? | S-X-07 |
| Q-10 | Group 0 and group 2 out-of-fold AUCs of my Qwen2.5-1.5B run: I never saw them. Are they in the log I deleted? | S-X-07 |
| Q-11 | Was the first local `ce_compare.py` stall (the first run) a network or a memory problem? I read it as network first, but the later failures were memory. | S-D-06 |
| Q-12 | The 7B NaN: was it a divergence in training, or bf16 overflow? Not diagnosed. | S-X-08 |
| Q-13 | Total effect of the ownership fix: I did not record the before and after numbers. | S-D-02 |
| Q-14 | The Qwen2.5-1.5B revision: I verified it against the Hub on 2026-09-29. Was the model I trained on 26 Sep the same revision? The log line shows the same hash (`8faed761…`), but I did not re-check the log. | numbers §4 |
| Q-15 | The submission ZIP (`Grenuke_submission.zip`, 88,353,544 bytes on Drive): did the final version contain the TSVs, the README and the documentation? I only checked the TSVs in the `final_zip` folder. | S-X-14 |
| Q-16 | Times from rented machines were converted from the machine's UTC clock (+5:30) and are approximate. | numbers §4, S-X-07 |
| Q-17 | Did Ameya originate an LLM cross-encoder before my proposal? I credit the LoRA Qwen cross-encoder to me; his zero-shot LLM test (AUC 0.537) came from his side. | contributions §2 |

## 2. For the curator or other members

| # | question | owner |
|---|---|---|
| Q-20 | Which upload is the final one: Composite B (AGENTS.md and the ZIP) or B+ (Composite B plus 8 decoys, Ameya's 22:15 comment in #64)? Was B+ uploaded, and what did it score? | Ameya |
| Q-21 | Baseline v0: what was the public LB score of the first submission, and who uploaded it? My chats name only the holdout (0.9683 in Ameya's records). | Ameya |
| Q-22 | The `qst` group-0 AUC (0.9334, Ameya) against my group-1 AUC (0.9279): different data and self-training make them not comparable. Should `knowledge/` say so? | curator |
| Q-23 | Ameya's check that nothing imports `ber/model` or `experiments/sachi/model/`: I grepped his drivers and Bakshi's box scripts. An import written as `from ber import model` would not have matched. I did not run that second grep. | Ameya |
| Q-24 | `reproduce_v7sq.sh`: Ameya dropped it from his branch ([commit 21bf128]). Is there a copy worth keeping in `knowledge/`? | Ameya |

## 3. Conflicts between sources

- **LOCO gap:** 0.024 (Ameya, 26 Sep) against about 0.028 (my run). Not reconciled.
- **Final upload:** AGENTS.md says Composite B; Ameya's #64 comment (22:15) says B+; Bakshi's later note mentions B7 (0.990875). The jury story should use Composite B (0.990879) unless Ameya says otherwise.
- **Direction of my street-swap reading:** my own first reading (France under-keeps the pattern, so dropping would hurt) differs from the final design (drop only where the 7B rejects). Both are recorded in S-D-11; the table that explains the difference is Ameya's.

## 4. A note on templates

The `knowledge/templates/` folder printed nothing when I read it. If `python scripts/new_doc.py person --member sachi` creates
different file names or headings, move these pages into those files; the content follows the formats in
`knowledge/STANDARD.md` §2.
