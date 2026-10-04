# Decisions: DEC (the decision layer: expected-F0.5 set selection, thresholds, ownership)

**Summary.**
- The decision layer turns calibrated pair probabilities (pc) into a set of records for each S1, the Source-1 reference business. Ownership gives each record to its single best S1 (the argmax, the highest score); set selection then picks, for each S1, the prefix of its candidates with the highest expected F0.5 (a dynamic programme, DP) instead of applying one threshold.
- Twenty decisions, in time order: the DP against a tuned threshold (gate G6, which the DP lost, won and won again depending on the model), the ownership rules, what we rejected (a stricter France threshold, renormalisation, tie-breaking, rescue rules, count priors, a consensus filter), the stacked layer (logit shift +0.2, crowd shift −0.3, phantom 0.01) and its France version.
- Scope: unless marked LB (public leaderboard), F0.5 means macro F0.5 on the local holdout (549,699 labelled US/India S1, no France). In the count form of F0.5, 1.25·c / (0.25·|T| + |P|), one false merge weighs as much as four missed copies. Evidence levels: [M] measured, [E] estimated, [R] reported, [U] uncertain. Times are IST. 1e-6 means 0.000001 of F0.5. No private-leaderboard score exists in our sources; only the ranking is known.

## Index

| ID | decision | when (IST) | status |
|---|---|---|---|
| D-DEC-01 | Per-S1 expected-F0.5 set selection, gated against a tuned threshold (G6) | 2026-09-25 11:23 | adopted as the target rule |
| D-DEC-02 | Ownership: argmax first; softmax with "none" only through gate G5 | 2026-09-25 14:15 | argmax adopted; G5 never run |
| D-DEC-03 | G6 at v0 (Sachi): keep the tuned threshold | 2026-09-25 17:31 | accepted for v0; superseded by D-DEC-05 |
| D-DEC-04 | Ownership computed over every S1, training folds included (Sachi's fix) | 2026-09-25 17:43 | adopted |
| D-DEC-05 | G6 at full scale: a threshold for stage-1 probabilities, the DP for calibrated stage-2 ones | 2026-09-25 18:43 | adopted |
| D-DEC-06 | No richer tuned rules (top/rest thresholds, thresholds by set size) | 2026-09-25 18:43 | rejected |
| D-DEC-07 | A separate "no match" (GFM) model parked | 2026-09-25 22:13 | rejected (never built) |
| D-DEC-08 | G6 applied model by model: the gate picks the DP or the threshold | 2026-09-25 23:31 | adopted; superseded by D-DEC-15 for the finals |
| D-DEC-09 | No "complete the duplicates" post-processing | 2026-09-26 00:40 | rejected |
| D-DEC-10 | No stricter France threshold (G8) | 2026-09-26 03:37 | adopted (no change) |
| D-DEC-11 | Per-record renormalisation of French probabilities | 2026-09-26 15:20 | rejected |
| D-DEC-12 | No copy-count tie-breaking between S1 that share an empty-address name | 2026-09-26 23:02 | rejected |
| D-DEC-13 | No empty-S1 rescue | 2026-09-26 23:25 | rejected |
| D-DEC-14 | Plain expected F0.5 at stage 3 judged a tie: threshold kept | 2026-09-27 02:53 | superseded by D-DEC-15 |
| D-DEC-15 | The stacked decision layer (`-dpc`): expected F0.5 with logit shift, crowd shift and phantom, plus acronym adds and caps | 2026-09-27 03:00 | adopted |
| D-DEC-16 | Keep France on the flat threshold (no expected-F0.5 decision for France) | 2026-09-27 04:24 | superseded by D-DEC-18 |
| D-DEC-17 | Reject the "consensus filter" | 2026-09-27 10:52 | rejected |
| D-DEC-18 | A France expected-F0.5 decision (`dp_france.py`); a French cross-encoder veto rejected | 2026-09-27 12:58 | decision adopted; veto rejected |
| D-DEC-19 | No India-only count prior | 2026-09-27 14:30 | rejected |
| D-DEC-20 | Reject mixfq and a more inclusive France DP (shift 0.5 or 0.8) | 2026-09-27 22:10 | rejected |

Related records: the rules that the stack layers on top are D-RUL-09 to D-RUL-11, the look-alike drop is D-RUL-14, and the 7B-based drop is D-LLM-05; the France decision layer from the France side is D-FRA-20 and D-FRA-21; the duplicates question also appears as D-PRB-04 and the ownership invariant as D-PRB-02; the stage stack that produces pc is in area MDL (D-MDL-03, D-MDL-11); the gate rules and the bar are D-EVL-03 and D-EVL-04; upload choices touching the decision layer are D-SUB-03, D-SUB-17 and D-SUB-23 to D-SUB-26.

## Records

### D-DEC-01 · Per-S1 expected-F0.5 set selection, gated against a tuned threshold (G6)
- **When (IST):** 2026-09-25 11:23 (stated) · 12:11 (Plan A §2) · 14:15 (FINAL_PLAN §2, gate G6) · **Phase:** P0 · **Area:** DEC
- **Decided by:** Ameya (proposed by: agent for Ameya). The rule that the DP must beat a tuned threshold, with ties going to the threshold, is Plan B's (Sachi's).
- **Status:** adopted as the target rule, subject to G6 (D-DEC-05, D-DEC-08). The final decision layer uses it (D-DEC-15).
- **Problem:** The metric is macro F0.5 per S1: F = 1.25·c / (0.25·|T| + |P|), where c is the number of correct predictions, T the true set and P the predicted set. A singleton S1 scores 1 only if nothing is predicted. Which rule turns pair probabilities into a set for each S1?
- **Options considered:**
  1. One global threshold on the calibrated probability (simple).
  2. Per S1, take the prefix of the candidates, sorted by probability, that maximises the exact expected F0.5. A Poisson-binomial dynamic programme over "true inside" and "true outside" computes it, with one global shrink.
- **Choice and why:** Option 2, on condition that it beats the threshold in a paired bootstrap. The metric punishes a wrong extra much more than a miss: in the count form one false merge weighs as much as four missed copies. A candidate therefore needs a break-even probability: 0.50 as the only candidate, 0.73 as the second (the first certain), 0.77 as the fourth (three certain), and the bar rises with set size toward 0.8 (the odds approach 4 to 1). One threshold cannot express a bar that rises. The DP "costs almost nothing in numba" over 1.7M entities. Plan B doubted the gain (5.6% of S1 are singletons, and records are not independent), hence the gate.
- **Evidence:** break-even table [M, analytic] ([FINAL_PLAN §2](../../plans/FINAL_PLAN.md), [Plan A §2](../../plans/ameya/PLAN.md)); when the pairs already chosen are certain, the k-th pair helps iff q > (5(k−1)+1)/(6.25(k−1)+2) = 0.500, 0.727, 0.759 … toward 0.8 [M, derived] [chat:ameya/agent-acec839c 2026-09-27 04:24]; [chat:ameya/19e315ba 2026-09-25 11:23].
- **Outcome:** On stage-1 probabilities the DP lost (−0.00029); on calibrated stage-2 probabilities it won (+0.00027 for v1, +0.00018 for v2, +0.00014 for v2 with legal features): D-DEC-05. The final pipeline keeps a per-S1 expected-F0.5 selection with a logit shift of +0.2 and −0.3 for contested records.
- **Hindsight:** The DP's edge over the best threshold shrank to +0.000048 [0.000007, 0.000091] in the final pipeline. In the record that number belongs to the whole combined layer (DP, crowd shift, acronym adds and caps); the DP alone was +33.2e-6 [−7.5, +75.0], not significant (D-DEC-15). The gain falls as the probabilities sharpen. Our own documents state the cost of a false merge differently: "about 3 times a miss" in the plan, "twice" in the submitted methodology §2.1, "2–3 times at typical sizes, approaching 4" in the theory page. The ratio depends on set size; in the count form it is four.
- **Links:** [FINAL_PLAN §2, §4.7, §9](../../plans/FINAL_PLAN.md) · [Plan A](../../plans/ameya/PLAN.md) · [theory: metrics and decisions](../theory/04-metrics-and-decisions.md) · D-DEC-05

### D-DEC-02 · Ownership: argmax first; softmax with "none" only through gate G5
- **When (IST):** 2026-09-25 14:15 · **Phase:** P0 · **Area:** DEC
- **Decided by:** Ameya (the softmax was proposed by Sachi, in Plan B)
- **Status:** argmax adopted in every model; G5 never run
- **Problem:** Every S2/S3 record has at most one owner (0 violations in 7,638,365 true pairs). How should records be assigned to S1?
- **Options considered:**
  1. Per-record argmax (Plan A): keep the record only under its highest-scoring S1.
  2. A softmax over the record's S1 candidates plus "none", trained on real orphans and on records whose owner was removed (Plan B).
  3. Argmax plus a margin rule (Plan B's simpler alternative).
- **Choice and why:** Argmax is "the most likely assignment … not guaranteed to be expected-F-optimal". The softmax had to beat it by Δ ≥ +0.002 (G5). The v0 baseline already used argmax with one threshold (D-MDL-02).
- **Evidence:** [M] ledger row 2 ([FINAL_PLAN §1, §4.7](../../plans/FINAL_PLAN.md)). Sachi's name-uniqueness gate later showed "taken by another S1" is only 0.26% of true pairs, so G5 had low expected value (D-FEA-08). No G5 result exists in any source.
- **Outcome:** Argmax ownership in every model, computed over all S1 (D-DEC-04). Contested records later got a stage-3 re-scoring instead (D-MDL-11). One owner per record became a hard invariant, audited everywhere (Bakshi's `audit_matching.py`, the stack's `import_tag.py`).
- **Hindsight:** Argmax lasted to the end. The 26 Sep research confirmed "one owner per record" in the ground truth.
- **Links:** [FINAL_PLAN §4.7](../../plans/FINAL_PLAN.md) · [Plan B](../../plans/sachi/PLAN.md) · [handover 2026-09-26_0554](../../docs/handover/2026-09-26_0554_ameya_research-part2-plan.md) · D-PRB-02 · D-FEA-08

### D-DEC-03 · G6 at v0 (Sachi): keep the tuned threshold
- **When (IST):** 2026-09-25 17:31 (numbers 17:52; updates 18:00 and 20:55) · **Phase:** P1 · **Area:** DEC
- **Decided by:** Sachi
- **Status:** accepted for v0; superseded by the full-scale G6 results (D-DEC-05) and finally by the stacked decision (D-DEC-15)
- **Problem:** Gate G6 on the dev sample: does an exact expected-F0.5 decision per S1 beat one tuned global threshold? Both ran on the same calibrated probabilities (stage-1 XGBoost, 3 OOF groups, cross-fitted isotonic) after argmax ownership.
- **Options considered:**
  1. A tuned threshold, t = 0.70: 0.9649.
  2. The DP over prefix sizes with one global logit shift b (best b = −0.25): 0.9647. The DP was checked against brute force on 40 random cases.
- **Choice and why:** Keep the threshold: Δ −0.00024 [−0.00091, +0.00049], p_better 0.234, n 27,651 (dev fold 0). Sachi applied the keep rule of plan §5.4 (Δ ≥ +0.002 with the interval above 0, ties to the threshold). An ownership bug (argmax over holdout S1 only) was fixed first (D-DEC-04). She kept the DP code "unused, so G6 can be re-run cheaply" and wrote down when to re-check: on the full holdout, after stage 2 and after softmax ownership, "because both change the probabilities the DP depends on". She also noted that test has 5.75 S2/S3 records per S1 against train's 4.68, so any test threshold shift is gate G8's question.
- **Evidence:** [M, dev]. Rerun through `ber.model` at 18:00: threshold 0.71 gives 0.96517, DP 0.96473, Δ −0.00044 [−0.00107, +0.00022]. On model v2's pc at 20:55: threshold 0.67 gives 0.98438, DP 0.98447, Δ +0.00010 [−0.00023, +0.00045], p 0.714: still below the bar, threshold kept.
- **Outcome:** Her prediction held: "with stronger probabilities the DP moved from slightly worse to slightly better". At full scale Ameya measured the DP at −0.00029 on stage 1 and +0.00027 and +0.00018 on stage 2 v1 and v2 (D-DEC-05).
- **Hindsight:** The right call at v0 and the right re-check plan; "calibration quality, not the DP, is the precondition" became the team's line (Bakshi's methodology §2.2). G6 changed sign with model quality all weekend. Note the bar: the plan states two keep rules, §5.4 (Δ ≥ +0.002 for components) and the §9 G6 row (Δ > 0 with the interval above 0, ties to the threshold). Sachi applied the first; Ameya's `decide.py` applied the second (D-DEC-08).
- **Links:** [decision gate-g6-dp-vs-threshold](../../docs/decisions/2026-09-25_1731_gate-g6-dp-vs-threshold.md) · [PR #16] · [PR #17] · [PR #18] · [PR #27] · D-DEC-04 · D-EVL-03

### D-DEC-04 · Ownership computed over every S1, training folds included (Sachi's fix)
- **When (IST):** 2026-09-25 17:43 (PR #16 reviewed; Ameya: "Merge") – 18:12 (the fix, PR #17) · **Phase:** P1 · **Area:** DEC / ORG
- **Decided by:** Sachi (the fix, merged by Ameya); Ameya ("Merge" for PR #16, after a review by agent for Ameya)
- **Status:** adopted
- **Problem:** [PR #16] (Sachi's model v0, in `experiments/sachi/`) assigned holdout records with `argmax_ownership(h)` over holdout pairs only. That ignored the rival S1 from the training folds, so the holdout score and the tuned threshold did not reflect test conditions, where every S1 competes.
- **Options considered:**
  1. Argmax over holdout S1 only (the bug).
  2. Argmax over all S1 candidates of the record, as on test (chosen).
  3. A softmax with "none" (G5, deferred).
- **Choice and why:** Option 2: evaluate only the pairs owned by holdout S1, but compute ownership over every S1, so the holdout sees the same competition as test. Ties go to the lower S1 eid. Merging PR #16 was harmless (her own folder plus a valid gate record); the fix came in [PR #17] with the port to `ber.model`.
- **Evidence:** dev fold 0 (27,651 S1): 0.9648 to 0.9652 after the fix; precision 0.988, recall 0.929 [M, Sachi's numbers].
- **Outcome:** The pipeline's train, predict and decide stages ran end to end; issues #8 and #9 closed. One owner per record became a hard invariant enforced and audited everywhere.
- **Hindsight:** A small fix with a long tail. The same "owners only from holdout S1" mistake recurred in the agent's own loss ledger on 26 Sep (D-DEC-12), so it is a recurring trap worth naming in the Q&A.
- **Links:** [PR #17] · [commit fd7bf67] · [chat:ameya/a2a1b62a 2026-09-25 17:43] · D-DEC-02

### D-DEC-05 · G6 at full scale: a threshold for stage-1 probabilities, the DP for calibrated stage-2 ones
- **When (IST):** 2026-09-25 18:43 (stage 1) · 18:48 (stage 2 v1) · 19:49 (v2) · 21:20 (v2 with legal features) · **Phase:** P1 · **Area:** DEC
- **Decided by:** agent for Ameya, applying the FINAL_PLAN G6 rule. Sachi's dev record (17:31) had kept the threshold for v0.
- **Status:** adopted
- **Problem:** Does the per-S1 DP beat a tuned threshold on the full holdout?
- **Options considered:**
  1. A tuned global threshold.
  2. The DP with one global logit shift tuned over {−1, −0.5, −0.25, 0, +0.25, +0.5, +1}.
- **Choice and why:** On stage-1 probabilities the DP is significantly worse (best 0.97777 at shift 0 against 0.97806 for the threshold, Δ −0.00029 [−0.00040, −0.00018]): "most probabilities sit near 0 or 1, and matches within an S1 aren't independent, which erodes its theoretical edge". The threshold was kept there. On calibrated stage-2 probabilities the DP wins. The best shift was 0 every time, "the untuned calibrated value, so there's little tuning optimism in that number". "The rivalry-aware stage-2 probabilities are what make the per-S1 rule work."
- **Evidence:** [M] full holdout (549,699 S1), paired bootstrap, 1,000 resamples: stage 2 v1 Δ +0.00027 [0.00020, 0.00036]; v2 +0.00018 [0.00009, 0.00026]; v2 with legal features +0.00014 [0.00008, 0.00021].
- **Outcome:** Models v1 and v2 use the DP.
- **Hindsight:** The DP stayed but its edge shrank (D-DEC-01). Later tuned shifts (+0.2, and −0.3 for records contested by 4 or more S1) replaced shift 0 (D-DEC-15).
- **Links:** [handover 2026-09-25_1958](../../docs/handover/2026-09-25_1958_ameya_model-v1.md) · [decision gate-legal-form-features](../../docs/decisions/2026-09-25_2142_gate-legal-form-features.md) · D-DEC-03 · D-DEC-08

### D-DEC-06 · No richer tuned rules (top/rest thresholds, thresholds by set size)
- **When (IST):** 2026-09-25 18:43 (designed) · 19:13 (measured) · **Phase:** P1 · **Area:** DEC / EVL
- **Decided by:** agent for Ameya
- **Status:** rejected (the richer rules); the untuned DP kept
- **Problem:** The DP's shift was tuned on the same holdout used to score it. Could simpler or other rules do as well, honestly?
- **Options considered:** a global threshold; separate thresholds for the S1's top candidate and for the rest; thresholds by the count of strong candidates. All were tuned on holdout folds 0–1 and scored on the untouched folds 2–4.
- **Choice and why:** On the untouched folds, top/rest (0.45 and 0.725) gives +0.00024 [+0.00012, +0.00036] and by-size +0.00022 [+0.00013, +0.00031] over the global threshold: "the same effect as the DP". The DP needs no tuned parameters, so it was kept.
- **Evidence:** tune then untouched: global 0.97989 to 0.97970; top/rest 0.98015 to 0.97994; by-size 0.98011 to 0.97992 [M] (stage-2 v1 scores).
- **Outcome:** The DP stays.
- **Hindsight:** The "tune on part, score on the rest" pattern returns in the final methodology ("gain on both halves of the holdout"). The top/rest result, a low bar for the first pair and a high one after, is the shape of the break-even table in D-DEC-01.
- **Links:** [handover 2026-09-25_1958](../../docs/handover/2026-09-25_1958_ameya_model-v1.md) · [`rules.py`](../../experiments/ameya/model-v1/rules.py)

### D-DEC-07 · A separate "no match" (GFM) model parked
- **When (IST):** 2026-09-25 22:13; again 2026-09-26 04:37 · **Phase:** P2 · **Area:** DEC
- **Decided by:** agent for Ameya. The research agent had ranked the idea sixth (+0.0005 to +0.002, an estimate).
- **Status:** rejected for now (never built)
- **Problem:** Singletons given matches and empty non-singletons cost about 25% of the v2 loss.
- **Options considered:**
  1. An S1-level P(no match) classifier feeding the DP's empty option (an exact F-beta rule that models "no match" directly, GFM).
  2. Keep independence, P0 = ∏(1 − q) (chosen).
- **Choice and why:** Keep it. Independence P0 is already calibrated overall (0.0563 against 0.0558), with only a slight underestimate in the 0.5–0.8 bins, which caps the gain at about +0.0001 to +0.0003. France's empty share after v4 (5.3%) is at the generator's 5.59%.
- **Evidence:** calibration by bin on the holdout [M] [chat:ameya/19e315ba 2026-09-25 22:13]; the cross-encoder had already raised singleton F0.5 from 0.99126 to 0.99742 [M] ([ANALYSIS_v3 §5](../../experiments/ameya/model-v1/ANALYSIS_v3.md)); "capped at +0.0001–0.0003" ([ANALYSIS_v4 §1](../../experiments/ameya/model-v1/ANALYSIS_v4.md)).
- **Outcome:** Never built.
- **Hindsight:** Fine. The cross-encoder removed most of the room. The later empty-S1 rescue (D-DEC-13) and the `rank0` hunt rule (D-DEC-15) ran into the same limit.
- **Links:** [ANALYSIS_v2 §3](../../experiments/ameya/model-v1/ANALYSIS_v2.md) · D-PRB-05 · D-CE-01

### D-DEC-08 · G6 applied model by model: the gate picks the DP or the threshold
- **When (IST):** 2026-09-25 23:31 (raised by Sachi) → 2026-09-26 14:30 (resolved) → per model through 27 Sep · **Phase:** P2–P3 · **Area:** DEC
- **Decided by:** Sachi raised it; agent for Ameya applied the rule per model; Ameya's v6all chose the threshold
- **Status:** adopted; superseded by the stacked layer (D-DEC-15) for the final candidates
- **Problem:** `decide.py` used the DP whenever its gain was above zero with the interval above zero, while Sachi's records applied the +0.002 bar. The DP and the threshold came out close on every model. The plan itself carries two keep rules: §5.4 (Δ ≥ +0.002 with the interval above 0, for components) and the §9 G6 row (Δ > 0 with the interval above 0; ties to the threshold).
- **Options considered:**
  1. Always the DP.
  2. Always a threshold.
  3. Per model, a paired bootstrap, with ties going to the simpler threshold (chosen).
- **Choice and why:** Per model, as the G6 row says. Ties go to the threshold.
- **Evidence** [M], DP minus the best threshold, and the rule used:
  - v3: +0.00011 [0.00005, 0.00017] over 0.650: DP, shift 0.
  - v4: +0.00006: DP. v5all: DP.
  - v6all-c2: +0.00004 [−0.00001, +0.00008]: threshold 0.70. v6all-s3: the same tie: threshold 0.675 (stage 3 retuned it).
  - v7ce3-c2: +0.00005 [+0.0000087, +0.0000924], p_better 0.993: DP.
  - v7m-c2: +0.0000395 [−0.0000014, +0.0000814]: threshold 0.70.
  - v7n-c2 and v7nst-c2: DP. v7n-s3 and v7nst-s3: threshold.
  - v7mst with stage 3: +0.00003 [−0.00002, +0.00007]: threshold (D-DEC-14).
  - On a stage-1-only score the DP lost (−0.00029; D-DEC-05).
- **Outcome:** The packages mix both rules, depending on the gate. v6all-c2 used threshold 0.70; one source adds a 0.25 logit shift to it [U] ([chat:ameya/a2a1b62a 2026-09-26 14:30]).
- **Hindsight:** The DP never came near the +0.002 bar with any model; it was used wherever it cleared the G6 row. In the final it needed more than the plain DP to clear it reliably (D-DEC-15). The methodology re-introduced the per-S1 selection and quotes +0.000048, the same small, real, below-bar effect; the rule was used flexibly for late gains, which is worth saying plainly.
- **Links:** [decision model-v3-end-to-end](../../docs/decisions/2026-09-25_2328_model-v3-end-to-end.md) · [decision model-v6all-final](../../docs/decisions/2026-09-26_1425_model-v6all-final.md) · [decision model-v7ce3](../../docs/decisions/2026-09-26_1933_model-v7ce3.md) · [FINAL_PLAN §5, §9](../../plans/FINAL_PLAN.md) · D-MDL-09 · D-MDL-12 · D-EVL-03 · D-EVL-04

### D-DEC-09 · No "complete the duplicates" post-processing
- **When (IST):** 2026-09-26 00:40 (analysis; reported to Ameya at 02:02 as "nothing to do") · **Phase:** P2 · **Area:** DEC
- **Decided by:** agent for Ameya (proposed by: agent a1f88e87; Ameya had heard the organisers might expect content-identical S2/S3 records to be listed together)
- **Status:** rejected (a decision not to do something)
- **Problem:** Should identical S2/S3 records always be predicted together?
- **Options considered:**
  1. Add the identical twins of predicted records to the same S1.
  2. Drop all members of a split group.
  3. Do nothing.
- **Choice and why:** Do nothing. All 43,910 exact-duplicate groups in train (same raw name, address and country) belong to one S1, and none is unmatched. Model v3 already predicts them together (10,680 of 10,827 holdout groups; 138 fully missed; 9 split). After case and punctuation folding, 4,389 groups belong to different S1 (for example three different "Raven LLC" with no address), so the truth does not list content-identical records together. Train has no identical S1 records.
- **Evidence:** adding exact twins +0.0000012; adding normalised twins −0.0000003 [M]. The SOTA research agent found no organiser statement on duplicates either [R].
- **Outcome:** No rule built.
- **Hindsight:** none recorded.
- **Links:** [ANALYSIS_v3 §6](../../experiments/ameya/model-v1/ANALYSIS_v3.md) · [chat:ameya/agent-a1f88e87 2026-09-26 00:40] · D-PRB-04

### D-DEC-10 · No stricter France threshold (G8)
- **When (IST):** 2026-09-26 03:37 → 04:37 · **Phase:** P2 · **Area:** DEC / FRA
- **Decided by:** agent for Ameya (proposed by: the leave-one-country-out anatomy agent a4957c58); Ameya's 04:37 report said a stricter France threshold "would only lose"
- **Status:** adopted (no change). The probe `probe_shift.py` and later France threshold probes were built and never uploaded.
- **Problem:** The model was less sure on France (v3: 9% of predicted pairs below pc 0.99, against 3% on the holdout). Would a stricter French threshold help (gate G8)?
- **Options considered:**
  1. Keep the in-country threshold.
  2. A stricter France threshold, for instance a logit shift of −0.5.
- **Choice and why:** Keep it. When a country's words are unseen, a stricter threshold gains (US-only model on the India holdout: 0.8824 at 0.95 to 0.8921 at 0.99). With the proxy odds the curve is flat and peaks at the in-country threshold (0.9598 at 0.75, 0.9590 at 0.85, 0.9522 at 0.95). What remains is confident convention error: 65% of the false positives have p ≥ 0.9 and 55% of the misses have p < 0.3.
- **Evidence:** dev-kit India holdout, 11,111 S1 [M] [chat:ameya/agent-a4957c58 2026-09-26 03:37] ([ANALYSIS_v4 §4](../../experiments/ameya/model-v1/ANALYSIS_v4.md)).
- **Outcome:** Not pursued; the final design has no global threshold at all (D-DEC-15).
- **Hindsight:** Consistent with the later finding that French errors are confident decoys, which needed an independent reader (the 7B re-check, area LLM).
- **Links:** [chat:ameya/19e315ba 2026-09-26 03:38] · [chat:ameya/19e315ba 2026-09-26 04:37] · D-FEA-11 · D-FRA-12 · D-SUB-03

### D-DEC-11 · Per-record renormalisation of French probabilities
- **When (IST):** 2026-09-26 15:20 and 18:34 · 2026-09-27 18:34 · Sachi's measurements on 27 Sep (scripts pushed 2026-09-29 00:55) · **Phase:** P3–P4 · **Area:** DEC / FRA
- **Decided by:** agent for Ameya (26 and 27 Sep); Sachi (the half-split measurements)
- **Status:** rejected
- **Problem:** A record has at most one owner, but French records' pc summed over their S1 exceeds 1.05 for 52 records per 1000 S1 (US/India 12–15). Label-free, Σ pc per S1 is 3.55 in France where the generator allows at most 3.46, so France's pc is overconfident. Would p / max(1, Σp) before ownership help?
- **Options considered:**
  1. Divide pc by max(1, Σ pc over the record's S1) before ownership.
  2. Leave it (chosen).
- **Choice and why:** Leave it: "too small to matter", and stage 3's mass calibration already covers it.
- **Evidence:** holdout 0.990780 to 0.990795 (+0.000015) on v6all [M]; on top of stage 3 unchanged at 0.990842 [M]; it would drop 6.6 French predictions per 1000 S1 [M] [chat:ameya/19e315ba 2026-09-26 18:34]. On v7sq, French records with Σ pc above 1.05 had fallen from 52.4 per 1000 S1 (v6all) to 0.7 (174 records), so the change would touch about 174 records, "worth about +0.00001 at most" [E] [chat:ameya/a2a1b62a 2026-09-27 18:34]. Sachi: holdout ΔF −0.000007 to −0.000137 across cuts; genuine French ties 2.9 per 1000 S1 [M, half-split] ([`tie_audit.py`](../../experiments/sachi/tie_audit.py), [PR #68]).
- **Outcome:** Not used. The methodology lists it among the measured-and-dropped ideas (up to −0.000137).
- **Hindsight:** Harmless to test and cheap to drop. The label-free proof that France was overconfident was real; the fix lay in the models (cross-encoders, self-training), not in the decision layer.
- **Links:** [RESEARCH_v6 §2.3, §5.3](../../experiments/ameya/model-v1/RESEARCH_v6.md) · [decision rules-v3-and-stage3](../../docs/decisions/2026-09-26_1557_rules-v3-and-stage3.md) · D-MDL-11

### D-DEC-12 · No copy-count tie-breaking between S1 that share an empty-address name
- **When (IST):** 2026-09-26 23:02–23:08 (ledger corrected, test limited) → 2026-09-27 (Sachi's test; scripts pushed 2026-09-29 00:55) · **Phase:** P3–P4 · **Area:** DEC / FRA
- **Decided by:** agent for Ameya (recommendation to Ameya on 26 Sep); Sachi (the test and the verdict on 27 Sep)
- **Status:** rejected
- **Problem:** Bakshi's plan ("Engine 1") rested on "lost to another S1: 20,134 pairs (+0.00342)". Empty-address records whose exact name several S1 share are 69% of the US/India misses. Does each S1's predicted copy count identify the owner?
- **Options considered:**
  1. Add the argmax owner when its posterior clears the 0.73–0.77 break-even (a copy-count tie-break).
  2. Leave the ties.
- **Choice and why:** Option 2.
  - On 26 Sep the agent recomputed the bucket with owners taken from all S1 and got 834 pairs (77% with an empty address), +0.00015. Its own 15:22 ledger had undercounted (187) because "I built the owner map from holdout S1s only", the trap of D-DEC-04. In v6all contested records go unpredicted ("below threshold"), mostly empty-address records with shared names, and stage 3 with rival counts gained only +0.00005. Engine 1 was limited to a copy-count informativeness test (about 3 h, verdict by 10:00): "Expect a negative result."
  - Sachi's test on 27 Sep: owner accuracy 0.31 against 0.27 by chance, no posterior above 0.6, and the add rule loses 0.00057 (LB-scaled).
  - Bakshi's own empty-address recall rules were 17–24% true (24% on the holdout alone, 17% when all train S1 compete) against a break-even near 75% ([FINAL_PUSH_RESULTS §6](../../experiments/bakshi/box/FINAL_PUSH_RESULTS.md)).
- **Evidence:** [M, holdout, half-split] ([`size_bias_owner.py`](../../experiments/sachi/size_bias_owner.py), [`tie_audit.py`](../../experiments/sachi/tie_audit.py), [PR #68]); [M] [chat:ameya/a2a1b62a 2026-09-26 23:02]. The two ledgers disagree on the size of the bucket: the 20,134 figure sits in [RESEARCH_v6 §4](../../experiments/ameya/model-v1/RESEARCH_v6.md) for v6all with stage 3 (19,383 for v3 in ANALYSIS_v4, 17,595 of them with an empty address), against 834 from the parallel session. They probably count different things (records whose highest-scoring S1 is another S1, against records actually predicted for another S1), but the sources do not say [U].
- **Outcome:** The methodology cites copy-count tie-breaking (−0.00057) among the measured-and-dropped ideas. No rule was built.
- **Hindsight:** Correct and cheap. It confirmed the same limit as D-FEA-08 and D-PRB-03: a name-only record with several same-name S1 is a coin toss that F0.5 tells us not to call.
- **Links:** [PR #68] · [chat:ameya/a2a1b62a 2026-09-26 23:08] · D-FEA-08 · D-PRB-03 · D-DEC-04

### D-DEC-13 · No empty-S1 rescue
- **When (IST):** 2026-09-26 23:25 · **Phase:** P3 · **Area:** DEC
- **Decided by:** agent for Ameya measured it, applying Bakshi's own gate
- **Status:** rejected
- **Problem:** Bakshi counted 4,488 test S1 predicted empty "that probably should not be" (India 3,076, US 1,332, France 80) and needed 1,976 rescues to reach first place.
- **Options considered:** Give each such S1 its best free candidate when the probability clears a bar; or leave them.
- **Choice and why:** Leave them. On the v7n-s3 holdout only 968 empty S1 are non-singletons; the best rule (bar 0.55, top-1) adds 68 pairs for +0.000021 [−0.000008, +0.000049]. In the mid band (p 0.4–0.7) about half the candidates are true and about half of those S1 are singletons, "a real coin flip". The test-side excess also exists on the holdout (5.74% empty against 5.58% singletons): those are blocking misses that no decision can reach.
- **Evidence:** [M] [chat:ameya/a2a1b62a 2026-09-26 23:25]. Bakshi's own closing check agrees: the empty-S1 rescue (top free candidate) is negative at every pc threshold, "DP already optimal" ([FINAL_PUSH_RESULTS §6](../../experiments/bakshi/box/FINAL_PUSH_RESULTS.md)).
- **Outcome:** Not built. A `rank0` rescue (pc 0.6–0.70) later appeared in the 27 Sep hunt at +33.1e-6 together with the other rules, and was subsumed by the DP (D-DEC-15).
- **Hindsight:** none recorded.
- **Links:** D-DEC-07 · D-DEC-15

### D-DEC-14 · Plain expected F0.5 at stage 3 judged a tie: threshold kept
- **When (IST):** 2026-09-27 02:53 · **Phase:** P3 · **Area:** DEC
- **Decided by:** agent for Ameya
- **Status:** superseded by D-DEC-15 about two hours later
- **Problem:** After the study of what the grader scores, is the decision rule the last lever?
- **Options considered:** the plain DP (no phantom, no crowd shift) against the flat threshold, on v7mst with stage 3.
- **Choice and why:** The plain DP was a tie (+0.00003 [−0.00002, +0.00007]), so the threshold stayed, and §6.15 wrote "the per-S1 decision rule is already optimised".
- **Evidence:** [M] ([RESEARCH_v6 §6.15](../../experiments/ameya/model-v1/RESEARCH_v6.md)).
- **Outcome:** §6.16 corrected it: that comparison ran the plain DP. With the phantom and the crowd shift it beats the threshold (D-DEC-15).
- **Hindsight:** An "already optimised" conclusion overturned within two hours by a dedicated sub-agent.
- **Links:** [RESEARCH_v6 §6.16](../../experiments/ameya/model-v1/RESEARCH_v6.md) · D-DEC-08

### D-DEC-15 · The stacked decision layer (`-dpc`): expected F0.5 with logit shift, crowd shift and phantom, plus acronym adds and caps
- **When (IST):** 2026-09-27 03:00–04:30 (analysis) · 04:24 (rule fixed) · 06:36 (decision record) · **Phase:** P4 · **Area:** DEC / RUL
- **Decided by:** Ameya (proposed by: three analysis agents for Ameya, called hunt, polish and decide; the decide agent acec839c proposed the DP variants). Bakshi reviewed and approved the scripts at 09:30.
- **Status:** adopted on every final candidate. `-h2pc` (threshold + acr + cap + nsa with the French stack) was kept as the conservative fallback.
- **Problem:** "The threshold was already optimal. Tuning it on the US/India holdout overfits: repeated 2-fold CV gives −18.8e-6 out of sample." The plain DP looked like a tie (D-DEC-14). Two French populations had never been checked: missed exact copies (Cie/Compagnie) and cross-commune acronym pairs. Small gains existed in both country groups but overlapped, and the DP recomputes US/India decisions from the stage-3 scores, so it overwrites the hunt rules' US/India changes.
- **Options considered** (US/India holdout, v7s; Δ in 1e-6, with the 95% interval; A and B are the fold-parity halves of the holdout):

  | rules | Δ [95% CI] | P(better) | A / B |
  |---|---|---|---|
  | threshold + acr + cap + nsa | +9.4 [+1.7, +17.5] | 0.990 | +10.0 / +8.6 |
  | + rank0 (rescue of an empty S1, pc 0.6–0.7) | +33.1 [+9.4, +56.3] | 0.996 | +18.1 / +55.6 |
  | DP (shift +0.2, phantom 0.01) | +33.2 [−7.5, +75.0] | 0.945 | −7.8 / +94.7 |
  | DP + acr + cap | +35.9 [−4.8, +77.6] | 0.958 | −4.8 / +97.1 |
  | **DP + acr + cap + crowd shift −0.3** | **+48.1 [+7.1, +91.2]** | **0.987** | **+7.7 / +108.7** |

  The decide agent also tried a threshold grid (0.600–0.850 in steps of 0.005), per-country thresholds, a greedy break-even schedule, first-pair against later-pair thresholds, contested against uncontested thresholds, DP with segment shifts, cross-fitted isotonic plus DP, and combinations, each selected on half A and confirmed on half B.
- **Choice and why:** The last row for US/India.
  - The rule: the DP works on an adjusted probability q = sigmoid(logit(pc) + 0.2 − 0.3·[the record has 4 or more S1 with p1 ≥ 0.02]), where logit is the log-odds; the exact expected-F0.5 prefix per S1 over its owned candidates; a phantom λ = 0.01 (0.01 expected true matches outside the candidate list, which lowers the value of an empty prediction); then `acr` and `cap`. `acr` adds an owned, unheld pair with pc ≥ 0.1 whose record name is the S1's initials and whose address is not empty (37 of 37 true on the holdout). `cap` allows at most 5 S2, 6 S3 and 11 records per S1, the training maximum, dropping the lowest pc first (the dropped pairs are false, 2 of 2). `nsa` (dropping predictions at pc between the threshold and 0.75 when 4 or more S1 compete) was replaced by the crowd shift, and `rank0` is subsumed by the DP.
  - Why a shift and not a flat 0.70: for an S1 whose chosen pairs are certain, the k-th pair helps iff q > (5(k−1)+1)/(6.25(k−1)+2) = 0.500, 0.727, 0.759 … toward 0.8, so a flat 0.70 is too strict for the first pair and too loose from the third on. Crowded records are overconfident, hence the crowd shift.
  - Selection discipline: the DP shift and phantom were chosen on v7nst's half A and confirmed on its half B (+45.5); the crowd shift was chosen on v7s's half A from {0.15, 0.3, 0.45} and confirmed on half B; repeated 2-fold CV of the DP with the phantom on v7nst (42 splits) gives +23.7 out of sample, positive in 86% of splits, while tuning the flat threshold the same way gives −18.8, positive in none; the DP part is positive on all 5 models tested.
  - France (no labels), where the hunt and the polish rules apply under population-truth evidence: `copy` (add same-name copies at the exact address, allowing legal forms, word order, Cie/Compagnie, Ets, St, Ste; the population is 99.992% true in the US and 99.998% in India; +332 on v7s), `city` (drop a pair whose S1 and record name different communes; French true copies change commune in 3 of 546,465 pairs, break-even 35%; −89), and a narrowed hunt (of 21 French acronym adds, the 5 that carry another house number or street, such as 3 and 335, are the generator's nudged look-alikes and were left out; in code, `acr` runs in France only when the record address has no digit, which leaves 16 adds). French `cap` drops were left out: they include perfect copies at pc 0.997–1.000 that the French pc cannot rank.
- **Evidence:** v7s holdout 0.991229 to 0.991277: +48.1e-6 [+7.1, +91.2], P 0.987; half A +7.7, half B +108.7 (interval [+43.9, +177.3]); US +70.8 [+12.1, +126.3], India +13.9 [−50.8, +70.8] [M]. The threshold grid lost out of sample (−18.8, positive in 0% of repeated splits); DP plus phantom, cross-fit +33.5 [M]. The French label-free score `fhs` (a tally per 1000 French S1 against v7nst): the hunt's own French changes −0.02, the narrowed hunt plus polish +1.09 [M, proxy]. The DP converges to the same density from any model: 3.389 (US) and 3.376 (India) predictions per S1 on v7s, v7sb and v7nst alike [M] [chat:ameya/19e315ba 2026-09-27 05:08]. LB: v7nst-dpc 0.990264 against v7nst 0.990179, so the stack is worth +0.000085 [M] ([LB 2026-09-27 #01](../../submissions/records/2026-09-27_sub01.md)).
- **Outcome:** The layer is on every final candidate; Composite B lists exactly these settings (shift +0.2, a further −0.3 for records that 4 or more S1 compete for, 0.01 expected matches outside the candidates, acronym joins and per-source caps everywhere, the French copy rule and the cross-commune drop).
- **Hindsight:** The methodology presents "+0.000048 (95% interval 0.000007 to 0.000091)" as the gain of the set selection over the best global threshold. In the record, that number belongs to the whole combination (DP, crowd shift, acr, cap); the DP alone was +33.2e-6 [−7.5, +75.0], not significant. The caveats limit the size, not the sign: the crowd shift was picked from {0.15, 0.3, 0.45} at noise-level differences on half A, and half B gained far more than half A on every model.
- **Links:** [decision stacked-rules](../../docs/decisions/2026-09-27_0636_stacked-rules.md) · [handover 2026-09-27_0706](../../docs/handover/2026-09-27_0706_ameya_final-stack.md) · [RESEARCH_v6 §6.16](../../experiments/ameya/model-v1/RESEARCH_v6.md) · [chat:ameya/agent-acec839c 2026-09-27 04:24] · D-RUL-09 · D-RUL-10 · D-RUL-11 · D-DEC-01 · D-DEC-14 · D-DEC-18

### D-DEC-16 · Keep France on the flat threshold (no expected-F0.5 decision for France)
- **When (IST):** 2026-09-27 04:24 (scope of the combo rule) · 09:21 (Bakshi agrees) · **Phase:** P4 · **Area:** DEC
- **Decided by:** agent for Ameya and Bakshi
- **Status:** adopted at the time; superseded by D-DEC-18
- **Problem:** Should France also get the DP decision?
- **Options considered:** the combo DP for France; the stage-3 threshold for France.
- **Choice and why:** No DP for France. The DP needs calibrated probabilities and France has no labels to calibrate against; the DP and the crowd shift were gated only on US/India; and any French use of `cap` and `nsa` depends "on calibration measured only on US/India".
- **Evidence:** the decision record, "What we give up" ([decision stacked-rules](../../docs/decisions/2026-09-27_0636_stacked-rules.md)); [chat:ameya/19e315ba 2026-09-27 09:21].
- **Outcome:** Reversed the same day: France got its own DP after the check in D-DEC-18. The methodology says France also got "the same set selection run on France's own probabilities".
- **Hindsight:** The caution was sound until v7sq's French pc was shown to be calibrated on its own changes.
- **Links:** D-DEC-15 · D-DEC-18

### D-DEC-17 · Reject the "consensus filter"
- **When (IST):** 2026-09-27 10:52–10:55 · **Phase:** P4 · **Area:** DEC
- **Decided by:** agent for Ameya (its own idea, after Ameya asked for a novel, niche approach)
- **Status:** rejected
- **Problem:** When two strong models disagree on a pair it is close to a coin flip, and under F0.5 an extra pair must be about 72% true to pay. Dropping disagreed pairs should therefore gain.
- **Options considered:** 15 intersections and majority votes over v7sq, v7sq2, v7sq3, v7qbag, v7ensall, v7ensall2, v7s and v7sb.
- **Choice and why:** Dropped. The score-averaging bags already capture what consensus offers.
- **Evidence:** on the labelled holdout the deltas run from −25.8 to +7.3 (×1e-6); every 95% interval spans zero [M] [chat:ameya/19e315ba 2026-09-27 10:55].
- **Outcome:** Not built.
- **Hindsight:** none recorded.
- **Links:** [chat:ameya/19e315ba 2026-09-27 10:52] · D-RUL-12 · D-SUB-17

### D-DEC-18 · A France expected-F0.5 decision (`dp_france.py`); a French cross-encoder veto rejected
- **When (IST):** 2026-09-27 12:58 (tasked) → 13:52 (validated) → 14:21 (commit d6c2e38) · **Phase:** P4 · **Area:** DEC / FRA
- **Decided by:** agent for Ameya (designed by the France-diff agent a2762d22, reusing the decide agent's combo DP; Ameya uploaded it in mixmdp)
- **Status:** the decision adopted for threshold-decided French models (not applied where stage 3 already chose by expected F0.5); the veto rejected
- **Problem:** US/India used the per-S1 DP (the combo rule) while France still used the stage-3 threshold. v7sq's French pc looked calibrated on its own changes (taking its pc as truth predicted the LB gain), so the US/India decision layer might transfer. Separately, 373 predicted French band pairs had all four self-trained cross-encoders against them (mean z below −0.5).
- **Options considered:**
  1. The DP with a crowd shift of 0 or −0.3, re-applying the look-alike and op-B drops to its additions.
  2. Apply it to every French base, or skip it.
  3. A veto of the 373 pairs.
- **Choice and why:** `apply_combo`'s DP on the French stage-3 pc, with logit shift +0.2, a further −0.3 for records that 4 or more S1 claim with p1 ≥ 0.02, and phantom λ 0.01. The rule layer is kept, look-alikes are removed, and look-alike or op-B swaps are never added. It was positive under every valuation on every threshold base and was checked on US/India labels. No veto: the size-bias false share of the veto pairs is f = −0.04 [−0.24, 0.24], against 0.89 [0.65, 1.12] for the look-alike drops and 0.01 for random predicted pairs, so the vetoed pairs are true copies [E].
- **Evidence:**
  - On v7sq: 276 adds and 1,199 drops; LB-unit estimates s1 / cal / s2 = +0.000035 / +0.000013 / +0.000020 [E]. Per base the conservative `cal` value is +10e-6 to +19e-6. v7sq6 DP +26 to +53 units and v7sqwg DP +17 to +45 units (1 unit is about 5.8e-7 LB) [E].
  - On v7sq6wg it is −3 units, because its stage 3 already chose by expected F0.5 [E].
  - The veto was valued −5.7 to −42.4 units by three of four estimators [E] [chat:ameya/agent-a2762d22 2026-09-27 13:54].
  - It reproduces mixh, mixi and mixj pair for pair [M] [14:21].
- **Outcome:** It is in mixmdp (357 adds and 224 drops; LB 0.990699) and in Composite B. At 22:09 the agent attributed B's French edge over mixf7 to this DP (+51e-6 by the 7B-based calibration, where the `pc`-based calibration saw +15) [E] ([RESEARCH_v6 §6.20](../../experiments/ameya/model-v1/RESEARCH_v6.md)). Not used on v7sq6wg, v7sq8wg, v7sq6w5 or v7sq6r3, where it was neutral or negative; the agent's script flags that case automatically.
- **Hindsight:** The rule was worth more than estimated.
- **Links:** [`dp_france.py`](../../experiments/ameya/model-v1/stack/dp_france.py) · [chat:ameya/19e315ba 2026-09-27 13:49] · [LB 2026-09-27 #03](../../submissions/records/2026-09-27_sub03.md) · D-FRA-20 · D-FRA-21 · D-DEC-16

### D-DEC-19 · No India-only count prior
- **When (IST):** 2026-09-27 14:30 · **Phase:** P4 · **Area:** DEC
- **Decided by:** agent for Ameya (proposed by: squeeze agent ac6dce8e)
- **Status:** rejected
- **Problem:** Find any further holdout-validated US/India gain over the v7sq3 combo. The squeeze agent's best tweak was a cardinality "tilt" in the DP for India only; it removes 724 India pairs across 719 S1.
- **Options considered:** about 160 variants: shifts by whether the record has a rival S1 (29), by S1 name collisions (15), India/S3 shifts and λ (12), joint grids (54), logistic recalibration (18), the runner-up taking records its owner left out (3), and count priors (29). The only winner was an India-only count prior P(Y) ∝ Π q^y(1−q)^(1−y)·w(|Y|), with w fitted by maximum likelihood on half A (w = 1.646 for no match … 0.011 for 11).
- **Choice and why:** Declined: "it hurts the US on every model, with no explanation"; it was picked from about 160 variants, so half B was not fully blind; and it is "too small to matter and too likely to be noise".
- **Evidence:** full +16.1e-6 [+2.2, +29.9]; India +40.3 [+6.6, +76.7]; +7.0 of the +8.8 net F-units came from 11 S1 [M] [chat:ameya/19e315ba 2026-09-27 14:30]. Worth about +0.00002 on the LB [E].
- **Outcome:** Packages unchanged.
- **Hindsight:** none recorded.
- **Links:** [RESEARCH_v6 §6.18](../../experiments/ameya/model-v1/RESEARCH_v6.md) · [chat:ameya/agent-ac6dce8e 2026-09-27 14:30] · D-MDL-15

### D-DEC-20 · Reject mixfq and a more inclusive France DP (shift 0.5 or 0.8)
- **When (IST):** 2026-09-27 22:10–22:53 · **Phase:** P5 · **Area:** DEC
- **Decided by:** agent for Ameya, on a rule set at 22:16: switch away from B+ only for at least +0.000015, measured mostly on 7B-scored pairs
- **Status:** rejected
- **Problem:** Ameya wanted a better final than Composite B ("we need more, a better best model").
- **Options considered:**
  1. mixfq: round-3 France with B's full treatment (look-alike drop, France DP, 7B drops).
  2. B with a more inclusive France DP: shift 0.5 (1,161 adds) or 0.8 (2,360 adds), against 357 adds at 0.2.
- **Choice and why:**
  - mixfq: nominal +0.000020, but the same estimator had scored mixf7 at +0.000007 against B while the LB said −0.000046; corrected for that bias, about −0.000033 [E] [chat:ameya/19e315ba 2026-09-27 22:31].
  - DP at 0.5 and 0.8: nominal +0.000052 and +0.000106, but half the additions sit at pc ≤ 0.7, where the 7B's calibration does not reach; realistic ranges −10e-6 to +16e-6 and −38e-6 to +30e-6 [E].
  - A direct valuation with holdout truth: the 1,008 French additions of shift 0.5 have a mean probability of being true of 0.756, right at F0.5's break-even, so about −2.5e-6 on the LB [E] [22:53].
- **Evidence:** all 193,524 unscored French candidates were scored by the 7B first, so every possible addition had a 7B score [22:27] [M].
- **Outcome:** B+ stayed the recommendation. The last upload slot later went to B7 (Bakshi), a tie with Composite B (LB 0.990875 against 0.990879; [LB 2026-09-27 #07](../../submissions/records/2026-09-27_sub07.md)). Which of the two the private ranking used is an open item (area SUB).
- **Hindsight:** A more inclusive decision rule cannot help when the extra pairs sit at break-even.
- **Links:** [RESEARCH_v6 §6.20](../../experiments/ameya/model-v1/RESEARCH_v6.md) · [chat:ameya/19e315ba 2026-09-27 22:16] · D-DEC-15 · D-DEC-18 · D-FRA-26 · D-SUB-26
