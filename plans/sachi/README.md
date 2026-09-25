# Plan — Sachi

Entity resolution approach for the Amazon ML Challenge 2026 (Business Entity Resolution track).

- **`PLAN.md`** / **`PLAN.pdf`** — full architecture, feature list, blocking strategy, and validation plan. Every design decision is tagged as either measured on the actual training data (`[M]`), a fact from the problem statement (`[F]`), or an unverified hypothesis with a named experiment to test it (`[H]`).
- **`DECISION.md`** — short summary of the key calls made, what the data changed our minds about, and what we deliberately chose not to build.

## One-line summary

Business names collide constantly (47% of Source 1 entities share an exact name with another entity) and addresses collide too, but rarely (5.3%), and almost never both at once — so the pipeline scores name and address jointly per pair rather than trusting either alone, resolves competing claims on each record through an ownership layer with an explicit "no match" option, and picks how many matches to report per entity based on which method — a learned per-entity calculation or a simple tuned threshold — actually wins on validation.
