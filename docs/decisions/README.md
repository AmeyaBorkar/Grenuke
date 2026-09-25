# Decision records

Short records of choices that affect more than one area: approach, contracts, thresholds, the final-model choice. They also give us the "why" for the methodology document.

- Create one with `python scripts/new_doc.py decision --member <member> --topic <kebab-topic>`. This makes `YYYY-MM-DD_HHMM_<topic>.md` from `TEMPLATE.md`.
- Each decision is its own file, so records never conflict. It is merged through a PR, and the reviewers are the affected owners.
- If a decision is superseded, write a new record that links the old one. Don't edit old records.
