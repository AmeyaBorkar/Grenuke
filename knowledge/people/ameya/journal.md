# Journal: ameya

One entry per working session, in time order (`knowledge/STANDARD.md` §2.5). Times are IST.

The competition sessions (25 Sep 11:00 → 29 Sep) are not journaled here yet; they are covered by [`../../story.md`](../../story.md) and [`../../decisions.md`](../../decisions.md).

## 2026-10-03 22:40 → 2026-10-04 00:30 · Finale kick-off and repo rules

- **Goal:** set the repo up for the finale. Capture every decision and detail, and make the team fluent in the theory.
- **What was done:**
  - The organisers' template was moved to `finale/`.
  - The digest script turned Ameya's 3 sessions and 26 sub-agent logs into 16 narrative parts, 6 full parts and 26 briefs.
  - `knowledge/STANDARD.md` and `CAPTURE.md` were written, with the person templates.
  - Rules: AGENTS.md §10 and CONTRIBUTING §12. Hooks and CI block `*.jsonl` and private details, and both guards were tested.
  - `finale/README.md` was written. 14 agents were launched (8 chat slices, 4 repo slices, 2 theory).
- **Results:** PR #78 merged. Issues #79 (team plan), #80 (Bakshi) and #81 (Sachi) raised.
- **Decisions:**
  - two layers: member captures plus a curated layer;
  - evidence levels M/E/R/U;
  - transcripts never committed.
- **Problems:** the e-mail said "Monday, 6 October", but 6 Oct is a Tuesday. Ameya later confirmed Tue 6 Oct 14:00. The usage limit stopped the agents at about 23:35.
- **Next:** resume the agents, curate, theory.
- **Sources:** [chat:ameya/19e315ba 2026-10-03 22:40], PR #78, issues #79–#81.

## 2026-10-04 05:15 → 18:00 · Knowledge base v1, the foundations track, branch clean-up

- **Goal:** turn the twelve extracts into the curated knowledge base, and add theory from scratch.
- **What was done:**
  - **Extracts:** the stopped agents were resumed and all 12 extracts completed: 1.74M characters, every chat source read in full.
  - **First merge round:** the agents failed with context and usage limits. The extracts were then split by script into per-section and per-area files, and the merge agents ran on Sonnet with small inputs.
  - **Knowledge base:** the story, 247 decisions, 245 numbers, 68 conflicts, 68 failures, 37 lessons, 100 Q&A entries and 29 theory pages (11 advanced and 18 foundations).
  - **Fixes elsewhere:** the deck date and the candidate-recall wording were corrected in `finale/` and issue #79.
- **Results:**
  - PR #84 merged.
  - Bakshi's five open PRs were carried onto `main` through an integration PR. His authorship is kept, and only `docs/status/bakshi.md` conflicted, resolved to its current version.
  - Branch clean-up: 8 worktrees, 31 local and 6 remote merged branches were removed.
- **Decisions:**
  - Quote **98.35%** for the candidate file's recall (31,304 of 1,901,267 true holdout pairs outside it); 99.1% is the recall before the cut.
  - Quote no private-leaderboard score; only rankings are published.
  - Save usage: no new agents for the timeline, the experiment ledger or the component pages for now.
- **Problems:**
  - two usage-limit stops;
  - "prompt too long" when one agent read all twelve extracts;
  - Windows file locks on some worktree folders.
- **Next:**
  - Bakshi's capture (#80);
  - the deck on Mon 5 Oct, due Tue 6 Oct 14:00;
  - optionally the paused pages (timeline, experiments, components).
- **Sources:** this session; PRs #84 and #82, and the merge PR.
