# Handovers

A handover passes context to the next person or agent session: your teammate, your own next session, or someone taking over your area.

- **When:** at the end of **every** working session (human or agent), and whenever you pass an area to someone else.
- **How:** `python scripts/new_doc.py handover --member <member> --topic <kebab-topic>`. This creates `YYYY-MM-DD_HHMM_<member>_<topic>.md` (IST) from `TEMPLATE.md`.
- **Rules:**
  - One file per handover. Never edit anyone else's handover. To correct one, write a new handover that references it.
  - Commit it on your branch, where it travels with the code in the PR.
  - Include exact commands and numbers. "It works" is not a handover.
- **Reading:** the newest files for your area first. `ls docs/handover | sort | tail` shows the latest.
