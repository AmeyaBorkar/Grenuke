# Live status (one file per member)

- `docs/status/<member>.md` answers "what is this person doing right now?"
- **Only that member (and their agents) edit it**, so it never conflicts.
- Update it at the start and end of every session, and whenever your focus changes.
- Create yours with `python scripts/new_doc.py status --member <member>`. The coordinator reads all of them to update `docs/ROADMAP.md`.
