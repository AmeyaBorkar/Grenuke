# Decision Log — Sachi's Plan

Short version of *why* this plan looks the way it does. Full reasoning and all measurements are in `PLAN.md`.

## Core call

Treat this as an **ownership assignment + per-entity decision problem**, not plain pairwise match/no-match classification. This follows directly from a fact in the problem statement: Source 1 is deduplicated, so every Source 2/Source 3 record belongs to at most one Source 1 entity. We verified this holds with zero exceptions across all 7.64M ground-truth matches.

## What the data changed our minds about

We started from assumptions in the problem statement and the original playbook. After actually scanning the training files, several of those assumptions were wrong or overstated:

| Assumption | What we found | Change |
|---|---|---|
| Postcode is a strong discriminating feature | Present in <1.2% of records | Cut as a dedicated feature |
| House-number mismatch is near-fatal for a match | Only 69% of true matches have identical numbers (401↔403, 713↔71, 4343↔4343B are common) | Use soft/tolerant number matching, not exact |
| Business name is a strong signal | 47% of Source 1 entities share their exact name with another Source 1 entity | Address must carry more weight; name alone can't decide |
| Address is therefore the safe fallback | 5.3% of Source 1 entities share an exact address with another entity too | Neither signal alone is safe — score name and address jointly, weighted by how ambiguous each is per-pair |
| Cross-encoder / neural model is the primary differentiator | Transformers are weak at exact numeric comparison, which is what separates neighboring branches | Demoted to a gated, optional component — only built if error analysis shows it's needed on a specific (Indic-script) slice |
| Singletons are the main lever | Only 5.6% of entities are singletons; typical entities have 2–5 matches | Downgraded the singleton-specific model; focus shifted to correctly sizing multi-match sets |
| A "smart" expected-F₀.₅ decision layer is automatically better than a threshold | Never assumed without testing | Built to compete against a simple tuned threshold; whichever wins on validation is what ships |

## What we're deliberately not building (and why)

- **LLM judge** — too slow at this scale (10M+ records), and a fine-tuned small model beats it anyway if a neural component is needed at all.
- **Full graph/cluster resolution** — reduced to one cheap competition-margin feature; only escalated if error analysis shows it's needed.
- **State-based blocking partitions** — state fields are missing, abbreviated, or in regional scripts often enough that partitioning by state would silently drop true matches.
- **Country as a model feature** — the problem explicitly warns against country-specific logic (France is unseen in training); we rely on structural, language-agnostic features instead.

## What's still unproven (explicitly flagged, not hidden)

Everything about France is a hypothesis, since no French records exist in training. We rely on leave-one-country-out testing (train on US, validate on India, and reverse) as the closest proxy, plus a leaderboard probe comparing France predictions against an empty prediction for France.

The ownership-softmax layer and the expected-F₀.₅ decision layer are both required to prove themselves against a simpler alternative (a margin rule, and a tuned threshold, respectively) before being kept. Neither is assumed to win by design.

## Bottom line

This plan is built to be falsifiable at every major step — every "we do X because Y" claim in `PLAN.md` is tagged as either measured on the actual training data, or a hypothesis with a named experiment attached to test it.
