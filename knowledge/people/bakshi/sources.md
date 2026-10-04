# Sources: bakshi

Every source about Grenuke on Bakshi's machine, and how far it was mined (`knowledge/CAPTURE.md` step 2). Mined on 4 Oct by the agent for Bakshi (Claude Code) from redacted digests made with `scripts/kb/digest_transcripts.py`; every digest part was read in full by a reader agent, and their notes were merged into the other six files. Transcripts and digests stay on Bakshi's machine. Times are IST.

| source | kind | span (IST) | size | mined | notes |
|---|---|---|---|---|---|
| Codex `01a0d754` | Codex, Bakshi's main working session | 25 Sep 12:21 → 27 Sep 15:27 | 25.2 MB, 3 digest parts | fully | kick-off, prototype, normalisation and string features (#20, #21), the GitHub review, the v7 France audit and probe (#34, #37), capsule (#42), final-day review (#49), low-cost strategy, the Claude handover, recovery audit (#59), score records (#60) |
| Codex `01a0d755`, `01a0d75a`, `01a0d75b`, `01a0d76c` | sub-agents of `01a0d754` (rules, strategy, metric, resources) | 25 Sep 12:21–12:47 | 0.03–0.05 MB each | fully | kick-off reading |
| Codex `01a0d759`, `01a0d828`, `01a0d924` | automatic approval-reviewer sessions for `01a0d754`; each replays the main transcript with fuller tool output | 25 Sep 12:25–20:46 | 0.1–0.3 MB per digest part | fully | exact numbers for 25 Sep; two reviewer denials |
| Codex `01a0dd01`, `01a0dd05`, `01a0dd57`, `01a0dee2`, `01a0df0b` | approval-reviewer sessions for `01a0d754` | 26 Sep 14:48 → 27 Sep 10:41 | 0.06–0.3 MB per digest part | fully | the 26 Sep review, the v7 work, the final-day plan, #59, #60 |
| Codex `01a0e253` | watcher attempt, abandoned (no access) | 27 Sep 15:35–16:05 | 0.02 MB | fully | — |
| Codex `01a0e269` | read-only watcher of the rented boxes; later idea search and a finale deck draft | 27 Sep 15:59 → 4 Oct 14:30 | 0.2 MB | fully | backup alerts; the 17:32 advice that became the 7B re-check; the oracle best-of-6 (22:20) |
| Codex `01a0e26a`, `01a0e284`, `01a0e28c`, `01a0e2b4`, `01a0e2bb`, `01a0e3be` | approval-reviewer sessions for `01a0e269` | 27 Sep 16:00–22:20 | 0.04–0.13 MB | fully | box logs with exact times and numbers |
| Claude Code `b0c6934d` | Bakshi's Claude Code session ("opus-exec", the final push, the ZIP, this capture) | 27 Sep 00:20 → 4 Oct | 23 MB, 4 digest parts | fully | auditor and builder (#50, #54, #56), the screens, the Vast.ai push, q7st, g1w, the 7B re-check, Composite B, B7, the ZIP (#62, #70, #72, #75) |
| Claude Code `b0c6934d` sub-agent briefs | 4 briefs (pipeline agent, trainer agents) | 27 Sep 14:02–15:27 | small | fully | pointers only |
| Claude Code `90302bb3`, `48e9575b` | short side sessions | 27 Sep 09:38; 28 Sep 13:08 | 3 kB, 0.6 kB | fully | a status question; a settings command |
| Codex `01a0bd73` (20–25 Sep), `01a0ec8d` (29 Sep), `01a0f1eb` (30 Sep → 1 Oct) | Codex | — | — | checked | not about Grenuke (other projects); not used |
| Claude Code memory | three working-preference notes | 27 Sep → 4 Oct | 3 files | fully | escalate real trade-offs to Bakshi; prefer checks on the target hardware; keep updates short |
| The repository | `git log --author=trustdemons05`, `experiments/bakshi/`, `plans/bakshi/`, `docs/handover/*bakshi*`, `docs/status/bakshi.md`, `submissions/records/`; PRs #20, #21, #34, #37, #42, #49, #50, #54, #56, #59, #60, #62, #70, #72; issues #45, #64, #66, #69, #71, #75, #80 | 25 Sep → 4 Oct | — | fully | the record for every number cited from a file |
| Google Drive `grenuke-train-backup` | backups of the rented boxes: logs, 7B adapters and logits, re-check scores | 27–29 Sep | about 2 GB | partly (logs and configs) | run times and the model revision |
| WhatsApp and calls with Ameya and Sachi | — | 25 Sep → 4 Oct | — | not mined | decisions relayed through them are cited from the chats where Bakshi pasted them |
