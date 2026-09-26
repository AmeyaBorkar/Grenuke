# Status: bakshi

- **Last updated (IST):** 2026-09-26 16:13
- **Current focus:** Build an improved v7 from the verified v5 baseline while user-reported v6 run finishes.
- **Branch / PR:** `bakshi/v7-france` / #34.
- **Done:** Imported and verified v5 (exact package SHA); audited 865,630 France predictions; compared v3/v2; measured two score-free rescue probes. Original TSVs unchanged.
- **Findings:** Only 18 composed-edit predictions in France. Both strict rescue probes have zero labeled dev gain. Raw exact transfers are ambiguous; parsed address candidates expose lost numeric components. All proposed new edits disabled; no v7 score gain or TSV claimed.
- **Inputs still needed for model-level changes:** Full v6 scores/features/candidates after the run finishes. V5 is usable for prediction audits and source-only experiments, not probability reconstruction.
- **Latest handover:** `docs/handover/2026-09-26_1613_bakshi_v5-tsv-audit.md`.
- **Next:** Evaluate narrower residual changes with full v6 outputs, gate on shared holdout, then write and validate v7. Avoid blind unions and broad address vetoes.
