# Grenuke knowledge base

The complete record of how team Grenuke built its Amazon ML Challenge 2026 solution: every decision and why we made it, every experiment, every number, every dead end, who did what, and the theory behind it all.
It serves the Grand Finale (7 Oct 2026; [`finale/`](../finale/README.md)) and remains as the permanent record of the project.

**Rules:** formats, sources and evidence levels are in [`STANDARD.md`](STANDARD.md). To add what you know, use [`CAPTURE.md`](CAPTURE.md).

## Reading order

| if you have | read |
|---|---|
| 15 minutes | [`story.md`](story.md), the whole project as one narrative, then the "10 things" list in [`theory/README.md`](theory/README.md) and the ★ rows of [`numbers.md`](numbers.md) |
| 1 hour | add the component pages for the parts you will present ([`components/`](components/README.md)), [`qa.md`](qa.md), [`lessons.md`](lessons.md) and [`conflicts.md`](conflicts.md) |
| more | the theory: start at [`theory/foundations/README.md`](theory/foundations/README.md) (the curriculum, from scratch), then the advanced pages in [`theory/`](theory/README.md); test each other with the self-tests |

## Contents

| page | what it holds | status |
|---|---|---|
| [`story.md`](story.md) | the narrative: problem → insights → strategy → evolution → result → lessons; the backbone of the deck | done |
| [`timeline.md`](timeline.md) | every event, in time order (IST), with its source | done |
| [`decisions.md`](decisions.md) and [`decisions/`](decisions/) | every decision `D-<AREA>-NN`: the options, the reason, the evidence, the outcome, and hindsight | done: 247 decisions in 14 areas |
| [`experiments.md`](experiments.md) | the ledger of every measured attempt `EXP-NNN`, kept or dropped | done: 329 experiments |
| [`numbers.md`](numbers.md) | the fact sheet: every number we may quote, with scope, evidence level and source | done: 245 numbers, ★ = quote these |
| [`components/`](components/README.md) | one page per pipeline part: how it works, why, the alternatives, its limits and its scale | done: 15 pages |
| [`failures.md`](failures.md) | dead ends, bugs and surprises, and what each taught us | done: 68 entries |
| [`lessons.md`](lessons.md) | what worked, what didn't, what we would do differently | done: 37 lessons |
| [`qa.md`](qa.md) | the jury question bank: short spoken answers, evidence, follow-ups | done: 100 questions, top 15 first |
| [`theory/`](theory/README.md) | the study guide: the theory behind every technique we used, with self-tests. The whole guide, the story, the components and the finale pages also compile into one PDF book: `python scripts/build_book.py` | done: 11 advanced pages, glossary, and 18 foundations pages from scratch ([`theory/foundations/`](theory/foundations/README.md)) |
| [`conflicts.md`](conflicts.md) | facts on which our sources disagree, and open questions | done: 68 entries |
| [`sources.md`](sources.md) | every source mined (chats, PRs, issues, documents), with coverage | done |
| [`people/`](people/README.md) | each member's own capture (one writer each) | Ameya: pointers to the curated pages · Sachi: merged (#82) · Bakshi: to do (#80) |

## How it is built

1. **Capture:** each member mines their own chats, notes and memory into `people/<member>/` ([`CAPTURE.md`](CAPTURE.md)).
2. **Curate:** the curator (Ameya, with agents) merges the captures with the repo's records into the shared pages:
   - the records: handovers, decision and gate records, submission records, plans, research documents, PRs, issues and the code;
   - the merge assigns global IDs and lists every disagreement in `conflicts.md`.
3. **Review:** every member checks the pages about their own work, in a PR.
4. **Use:** the deck, the script and the Q&A draw only on these pages, so our numbers stay consistent.

Historical records are never rewritten:
- `docs/handover/`, `docs/decisions/`, `submissions/records/`, `plans/`;
- PRs and issues.

The knowledge base cites them.
