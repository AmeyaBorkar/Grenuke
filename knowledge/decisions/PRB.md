# Decisions: PRB (problem framing, data analysis)

**Summary.**
- Five decisions on how we framed the task and read the data. Source-1 records (S1) are the businesses we match from; Source-2 and Source-3 records (S2/S3) are the vendor records we match to them.
- We treated the country as an open set, gave each S2/S3 record one owner, and chose three times not to chase a loss: the empty-address records that several S1 share (the biggest, and irreducible), content-identical duplicates, and a list of small ideas.
- The choice of the base plan is in ORG (D-ORG-03), test-shift handling and the gates are in EVL (D-EVL-02, D-EVL-03), and the country-partitioned search is in BLK (D-BLK-02).

## Index

| ID | decision | when (IST) | status |
|---|---|---|---|
| D-PRB-01 | Country is an open set: no country feature, statistics per exact country label | 2026-09-25 11:23 | adopted |
| D-PRB-02 | Each S2/S3 record has at most one owner (argmax ownership plus rivalry features) | 2026-09-25 11:23 | adopted |
| D-PRB-03 | Do not chase empty-address misses whose name several S1 share (Bayes limit) | 2026-09-25 20:40 | adopted (a decision not to act) |
| D-PRB-04 | No action on content-identical duplicate records | 2026-09-26 00:41 | adopted (no action) |
| D-PRB-05 | Eight ideas measured and skipped or deferred | 2026-09-26 04:37 | rejected or deferred, per item |

## Records

### D-PRB-01 · Country is an open set: no country feature, statistics per exact country label
- **When (IST):** 2026-09-25 11:23 (brief), 14:15 (FINAL_PLAN) · **Phase:** P0 · **Area:** PRB / BLK
- **Decided by:** Ameya (accepted in FINAL_PLAN at 14:15; proposed by: agent for Ameya at 11:23). The rule itself comes from the problem statement, and both candidate plans agreed with it.
- **Status:** adopted
- **Problem:** The test set adds France, which never appears in the labelled data. A model that learns "US" or "India" as a feature, or code with a hard-coded country list, would meet a third value it has never seen. The problem statement says to treat `country` as an open set.
- **Options considered:**
  1. One-hot country, or hard-code the two known countries. Forbidden by the statement and by our own hard rule; it breaks on France.
  2. Partition by the exact country label, keep every feature country-agnostic, and fit word-rarity statistics (IDF, "inverse document frequency": how rare a word is) per country on train plus test. Chosen.
- **Choice and why:** Option 2. No true match crosses a country (0 of 7.64 million labelled pairs), so each country can be searched on its own. Rarity statistics fitted per country adapt to French vocabulary without any French labels, because they use no labels. A record whose label is empty or unseen is searched against every partition, as a defensive rule only.
- **Evidence:**
  - Cross-country labelled pairs: 0 of 7,638,365 [M] [chat:ameya/19e315ba 2026-09-25 11:49].
  - Test has exactly three labels. France has 259,452 S1 against 1,434,993 records on test [M].
  - The plan's own ledger entry: "country as a feature: breaks on France" [FINAL_PLAN §4.3, §12](../../plans/FINAL_PLAN.md).
- **Outcome:** Held to the end. The submitted methodology says "All statistics are fitted per country and there is no country feature" [methodology §4](../../experiments/ameya/final-zip/doc/Documentation_template.md). The price is that France has no labelled twin. France work therefore needed other tools: leave-one-country-out runs (gate G13, D-EVL-03) and label-free checks (D-EVL-11, D-EVL-12).
- **Hindsight:** Same choice today. Per-country fits are what later let France get its own vocabularies and lexicons without touching the rule.
- **Links:** [chat:ameya/19e315ba 2026-09-25 11:49] · [CONTRACTS](../../docs/CONTRACTS.md) · [AGENTS.md hard rules](../../AGENTS.md) · D-BLK-02 (how the search is partitioned) · [theory: entity resolution](../theory/01-entity-resolution.md)

### D-PRB-02 · Each S2/S3 record has at most one owner (argmax ownership plus rivalry features)
- **When (IST):** 2026-09-25 11:23 (hypothesis) → 11:49 (measured) → 14:15 (FINAL_PLAN) · **Phase:** P0 · **Area:** PRB / MDL
- **Decided by:** agent for Ameya (proposed and measured); Ameya (adopted it in FINAL_PLAN)
- **Status:** adopted
- **Problem:** Source 1 holds each business once, but 46–54% of S1 share an exact name with another S1. So many S1 compete for the same S2/S3 record, and scoring each pair on its own ignores that competition.
- **Options considered:**
  1. Score pairs independently.
  2. Keep each record only under its highest-probability S1 (argmax ownership) and give the model rivalry features: the best and second-best probability among the record's S1, and the margin between them.
  3. A softmax over the record's S1 plus a "none" option (Plan B's idea; gate G5).
- **Choice and why:** Option 2. The labels confirmed that Source 1 is deduplicated and that each S2/S3 record matches at most one S1: 0 violations in 7,638,365 labelled pairs. So competition between S1 is "a strong precision signal". The argmax is the most likely assignment and is cheap. The softmax was kept only as a gated alternative.
- **Evidence:**
  - Largest number of S1 per matched record = 1; the truth-table check `r.is_unique` returned True [M] [chat:ameya/19e315ba 2026-09-25 11:49], [20:32].
  - In stage-1 model v1, the margin feature `ret__margin_r` (margin over the record's best other S1) ranked third by gain [M].
- **Outcome:**
  - In model v2 the "lost by ownership" bucket still held 20,518 local-holdout true pairs. The local holdout is the fixed 25% of labelled US/India S1 that no model trains on (D-EVL-01). Fixing all of them would add +0.00359 of macro F0.5, the competition's score: the F0.5 of each S1, averaged over all S1 [M].
  - Sachi's first gate run took the argmax over holdout S1 only, which made ownership too easy. She found and fixed it before the G6 numbers [G6 record](../../docs/decisions/2026-09-25_1731_gate-g6-dp-vs-threshold.md), [commit fd7bf67].
  - The softmax with "none" (G5) was never built; Sachi's own analysis gave it low value (D-ORG-03).
  - The final pipeline keeps "each record can belong to at most one S1" [methodology §2.1](../../experiments/ameya/final-zip/doc/Documentation_template.md). The final package audit found 0 records claimed by more than one S1 [package README](../../experiments/bakshi/final-package/PACKAGE_README.md).
- **Hindsight:** The rule held, so the choice stands. Most of the pairs still lost to ownership are the empty-address ties of D-PRB-03, which no rule recovered.
- **Links:** [chat:ameya/19e315ba 2026-09-25 11:49] · [FINAL_PLAN §9](../../plans/FINAL_PLAN.md) (G5) · D-EVL-03 · [theory: entity resolution](../theory/01-entity-resolution.md)

### D-PRB-03 · Do not chase empty-address misses whose name several S1 share (Bayes limit)
- **When (IST):** 2026-09-25 20:40–21:44 (found), 2026-09-26 05:30–05:55 (reconfirmed); the recall rules that tried anyway ran on 2026-09-27 · **Phase:** P1–P2 · **Area:** PRB / FEA
- **Decided by:** Ameya, on the analysis of agents for Ameya (proposed by: agent a9638892; confirmed by: agents ace27900, abb9ffcd, abeb7453 and ac6dce8e)
- **Status:** adopted (a decision not to act)
- **Problem:** Records with an empty address are only 4.4% of true pairs but 52.5% of the misses of model v2 (miss rate 47.3%) and 69% of the misses at v5all. Can a rule or a model get them back? The Bayes limit is the error that no model can remove because the data does not separate the cases.
- **Options considered:**
  1. Model the owner from the name alone.
  2. Exploit a fixed number of copies per source per S1. The truth has none: S2 counts range from 0 to 5 and S3 from 0 to 6.
  3. Structural priors: copy counts and record mass (probability mass per record), built by a "structure fork" of the agent.
  4. Recall rules: tie rules, singleton protection, per-source count adds.
  5. Accept the loss.
- **Choice and why:** Option 5. "From name alone the owner is a coin flip" and "No field in the record points to the owner." The miss rate depends on how many S1 share the record's name:

  | S1 sharing the name | 1 | 2 | 3–5 | 6 or more |
  |---|---|---|---|---|
  | miss rate of empty-address records | 20.4% | 95.0% | 99.6% | about 100% |

  Records with an address miss only 1.7–2.7% at any name frequency. The generator draws copy counts independently of anything observable and drops addresses independently (4.41% per copy). Of the lost records, 62.5% sit between S1 with identical folded names (case and accents removed). The record's legal form singles out the true S1 in only 0.3% of lost cases (the agents' note adds "the owner in 5.3%", without saying more). Under F0.5, two S1 at probability about 0.49 are both better left empty: per S1 a false positive costs about 0.19 and a miss about 0.06, and in F0.5's count form one false merge weighs as much as four missed copies. So about 22k holdout misses (+0.0037 counterfactual) are irreducible.
- **Evidence:**
  - "Lost" pairs: 19,050 (+0.00335 if all fixed), 91.7% of them with an empty record address [M] [chat:ameya/agent-a9638892 2026-09-26 05:30], [chat:ameya/agent-ace27900 2026-09-26 05:28].
  - Upper bounds: +0.00335 (every lost pair to the right S1) and +0.00463 (every ambiguous empty-address record resolved) [E] [RESEARCH_v5 §4](../../experiments/ameya/model-v1/RESEARCH_v5.md).
  - Structural priors together: +0.00011 [0.00007, 0.00015] on the holdout [M].
  - Rules tried later all lost [M]: tie rule −10e-6 to −29e-6 (the version without numbers −137.5e-6 [−172.5e-6, −110.2e-6]) [chat:ameya/agent-abeb7453 2026-09-27 11:34]; singleton protection −33.7e-6 to −396e-6, and per-source zero-count adds −48.1e-6 to −624e-6 [chat:ameya/agent-abb9ffcd 2026-09-27 04:05]. Here "e-6" means ×10⁻⁶ of macro F0.5.
  - No recall rule tried was more than 71% precise, against the roughly 75% an added pair needs under F0.5 [methodology](../../experiments/ameya/final-zip/doc/Documentation_template.md).
- **Outcome:**
  - Effort went to legal forms, blocking keys and cross-encoders (models that read a pair of records together and score the match) instead [chat:ameya/19e315ba 2026-09-25 20:40].
  - Only stage 3's record-mass calibration touched this bucket. Stage 3 is a late model stage for contested records. The prototype measured +0.00011 [0.00007, 0.00015]; in the real pipeline it measured +0.00005 and was parked. Another summary quotes the prototype as +0.00007, probably the lower interval bound [U].
  - In the final model this was still the largest loss bucket [RESEARCH_v6 §4](../../experiments/ameya/model-v1/RESEARCH_v6.md). Final local-holdout precision is 99.9% and recall 97.5% [M] [methodology](../../experiments/ameya/final-zip/doc/Documentation_template.md).
- **Hindsight:** Correct. This is the irreducible floor of the local holdout. The methodology names "empty-address copies whose name was also changed" as the main remaining misses. The 75% precision bar for an added pair was never reached.
- **Links:** [chat:ameya/19e315ba 2026-09-25 21:44], [2026-09-26 05:30] · [ANALYSIS_v2 §2](../../experiments/ameya/model-v1/ANALYSIS_v2.md) · [RESEARCH_v5 §2, §4](../../experiments/ameya/model-v1/RESEARCH_v5.md) · D-PRB-02 · [theory: metrics and decisions](../theory/04-metrics-and-decisions.md)

### D-PRB-04 · No action on content-identical duplicate records
- **When (IST):** 2026-09-26 00:41 · **Phase:** P2 · **Area:** PRB
- **Decided by:** agent for Ameya (candidates fork). Ameya had asked at 00:05 whether the organisers require such records to be listed together.
- **Status:** adopted (no action)
- **Problem:** A rumour said that content-identical S2/S3 records must be listed together in the output.
- **Options considered:**
  1. Force-complete the duplicate groups.
  2. Do nothing.
- **Choice and why:** Do nothing. Exact duplicates always belong to the same S1 (43,910 of 43,910 train groups), and model v3 already predicts them together: only 9 groups out of 10,827 are split on the holdout, worth +0.0000012 if completed. After case folding, the truth splits 4,389 groups across different S1, so the truth does not list content-identical records together. Nothing public required it.
- **Evidence:** [M] [ANALYSIS_v3 §6](../../experiments/ameya/model-v1/ANALYSIS_v3.md).
- **Outcome:** Never needed.
- **Hindsight:** A quick, measured way to close a rumour.
- **Links:** [chat:ameya/19e315ba 2026-09-26 02:02]

### D-PRB-05 · Eight ideas measured and skipped or deferred
- **When (IST):** 2026-09-26 04:37 · **Phase:** P2 · **Area:** PRB / FRA
- **Decided by:** Ameya (analysis: agent for Ameya)
- **Status:** rejected or deferred, per item (listed below)
- **Problem:** At the end of the overnight error analysis eight further ideas were on the table. Which deserve hours of work?
- **Options considered (idea, evidence, verdict):**
  1. French address clusters: 11.1% of French S1 share an exact address (largest cluster 101), against 4–5.7% in the US and India. On the holdout, clustered S1 score 0.984–0.987 and carry 7–8% of the loss. Worth at most 0.001 on the public leaderboard (LB). Verdict: no change.
  2. Per-stratum calibration: gaps are at most 0.05 everywhere. Verdict: skip.
  3. A "no match" model for each S1, to feed the DP's empty option (the DP is the dynamic programme that picks each S1's set by expected F0.5): +0.0001–0.0003. France's empty share (5.3%) already sits at the generator's 5.59%. Verdict: skip.
  4. Synthetic French pairs: superseded by the rules. Verdict: dropped.
  5. Cross-encoder pretraining: "hours of GPU for an uncertain gain". Verdict: skip.
  6. Typo repair in blocking: at most +0.0005 on the holdout, and it needs a full rebuild. Verdict: deferred, and taken up later as the blocking v3 repairs (D-BLK-11).
  7. A stricter France threshold (gate G8): in leave-one-country-out runs the proxy setting's best threshold equals the in-country one, so a stricter one "only loses in this regime". Verdict: rejected.
  8. An external transliterator (IndicXlit, MIT-licensed): trained on external data (Aksharantar), needs a human ruling on the external-data rule, and the Indic loss is already small (0.9872 against 0.9870). Verdict: rejected (D-NRM-02).
- **Choice and why:** Each idea was sized first. None promised more than 0.001, most promised far less, and several cost hours of compute or raised a rules question.
- **Evidence:** [M] unless stated; [ANALYSIS_v4 §1, §4](../../experiments/ameya/model-v1/ANALYSIS_v4.md), [ANALYSIS_v2 §3](../../experiments/ameya/model-v1/ANALYSIS_v2.md).
- **Outcome:** Item 6 returned as D-BLK-11. Item 8 never needed a ruling. The rest stayed closed.
- **Hindsight:** unknown (none recorded).
- **Links:** the France and rules records (areas FRA, RUL) for items 4 and 7 · D-NRM-02 · D-BLK-11 · [theory: evaluation methodology](../theory/05-evaluation-methodology.md)
