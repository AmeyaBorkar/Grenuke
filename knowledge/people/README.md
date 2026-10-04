# People: each member's own capture

One folder per member, written **only by that member and their agents** (one writer, so no conflicts). Each holds the raw-but-structured record of what that person did, decided and knows, mined from their own chats, notes and memory.

| member | folder | status |
|---|---|---|
| Ameya | [`ameya/`](ameya/) | done: journal (25 Sep – 4 Oct), contributions; decisions, experiments and numbers live in the curated pages |
| Bakshi | [`bakshi/`](bakshi/) | done (#88): 40 decisions, 50 experiments, journal, contributions; folded into the curated pages (conflicts CF-54 to CF-66) |
| Sachi | [`sachi/`](sachi/) | done (#82, corrections in #83) |

- **Start a folder:** `python scripts/new_doc.py person --member <you>`, then follow [`../CAPTURE.md`](../CAPTURE.md).
- **Files in each folder:**
  - `sources.md`
  - `journal.md`
  - `decisions.md`
  - `experiments.md`
  - `contributions.md`
  - `numbers.md`
  - `open-questions.md`
- The formats are in [`../STANDARD.md`](../STANDARD.md).
- The curator merges these into the shared pages (`timeline.md`, `decisions/`, `experiments.md`, `numbers.md`, `components/`). The originals stay here as the source of record.
