# Decisions: RUL (rules and post-processing)

**Summary.**
- Rules are hand-written steps after the model that add or drop pairs. The France rules run only for a country with no training labels, and each rule population was first measured on US/India labels. S1 is a Source-1 business record; "unheld" means a record that no S1 holds yet.
- They copy the organisers' generator (the program that made the records). Op A (a word dropped, a list word appended: a true copy) is added; op B (another real word put in the dropped word's slot: a look-alike decoy) is dropped. Versions v1 to v3 and the stacked layer `-dpc` (rules plus a per-S1 expected-F0.5 decision on top of the model) followed on 26-27 Sep 2026.
- Every attempt to add recall, or to drop on a model disagreement, failed. F0.5, the challenge metric, punishes a wrong merge more than a missed copy (in its count form one false merge weighs as much as four missed copies), so an added pair must be right about 72-77% of the time; no label-free signal passed 71%.

## Index

| ID | decision | when (IST) | status |
|---|---|---|---|
| D-RUL-01 | France rules from the generator: drop op B, add op A (`post_ops.py` v1), unlabelled countries only | 2026-09-26 04:17 | adopted |
| D-RUL-02 | France rules v2: add APP and ACR; reject NUM and CODE | 2026-09-26 06:26 | adopted |
| D-RUL-03 | France rules v3: a robust same-address test | 2026-09-26 15:41 | adopted |
| D-RUL-04 | Bakshi's composed-edit rules and address veto kept disabled | 2026-09-26 15:45 | rejected |
| D-RUL-05 | Bakshi's robust-B probe prepared, not selected; no slot spent on it | 2026-09-26 16:37 | deferred (never uploaded) |
| D-RUL-06 | French acronym join, unlabelled countries only | 2026-09-26 18:17 | adopted |
| D-RUL-07 | Brand-name join rejected (`brand_join.py` kept, not applied) | 2026-09-26 18:17 | rejected |
| D-RUL-08 | No new French rules overnight (typos, abbreviations, cities) | 2026-09-27 01:21 | adopted, partly reversed by D-RUL-10 |
| D-RUL-09 | Hunt rules: acronym adds and generator caps everywhere; crowded-record drop for US/India only | 2026-09-27 04:05 | adopted (acr, cap); nsa and rank0 superseded |
| D-RUL-10 | Polish rules for France: exact-address copy add and cross-commune drop | 2026-09-27 04:15 | adopted |
| D-RUL-11 | Stack the rules on every final candidate (`-dpc`) | 2026-09-27 06:36 | adopted |
| D-RUL-12 | Drop rule from cross-encoder disagreement (bge below 0 while e5 above 0) | 2026-09-27 09:17 | rejected |
| D-RUL-13 | Structural French recall recovery | 2026-09-27 11:25 | rejected |
| D-RUL-14 | Drop French look-alike word swaps at the S1's address (`apply_swapsim.py`) | 2026-09-27 11:38 | adopted (in mixmdp and Composite B) |
| D-RUL-15 | No further French rule adds or drops from data scans | 2026-09-27 12:20 | rejected |
| D-RUL-16 | Build later candidates without the look-alike drop | 2026-09-27 17:03 | adopted for builds never uploaded; the final keeps the drop |
| D-RUL-17 | No recall ("add") rules | 2026-09-27 19:24 | rejected |

Related records: the French acronym keep-or-drop test is D-FRA-19, the 7B-based drop and the rejection of 7B-driven adds are D-LLM-05 and D-LLM-08, and the expected-F0.5 decision layer is in area DEC.

## Records

### D-RUL-01 · France rules from the generator: drop op B, add op A (`post_ops.py` v1), unlabelled countries only
- **When (IST):** 2026-09-26 04:17 (root cause found 03:34) · **Phase:** P2 · **Area:** RUL / FRA
- **Decided by:** Ameya (proposed by: agent for Ameya, with a generator-catalogue sub-agent and a leave-one-country-out sub-agent)
- **Status:** adopted. Its own gate, the probe `v4-frab` against `v4`, was never uploaded.
- **Problem:** The generator edits one S1 name word at the S1's own address (same house number and street word) in two ways. Op A is a true copy: a word is dropped and a list word is appended after the legal form. Op B is a look-alike: another real word goes in the dropped word's slot ("Arcot Motors Corp" → "Arcot Solutions Corp"). US/India models tell them apart through label word odds. France has only the label-free proxy (D-FRA-03), which flags look-alike words by moved house numbers, and op B keeps the number. So v4 predicted 17,088 op-B records in France (65.9 per 1000 French S1, median pc 0.989) and left 4,746 op-A records unpredicted [M]. (pc is the calibrated probability that a pair is a true match.)
- **Options considered:**
  1. Rules after `decide.py`: drop predicted op-B pairs; add op-A pairs when the S1 is the record's argmax owner (best-scoring S1), the pair is a candidate and no other S1 holds the record.
  2. Position features (slot versus after the legal form) and a retrain: cleaner, but a full stage 1/2 rerun, and the US/India models already separate A and B through word odds.
  3. Synthetic French training pairs from the generator catalogue: about a day, and it would have to encode the same A/B rules (D-FRA-05).
  4. A stricter France-only threshold: "cannot help in this regime".
  5. Nothing.
- **Choice and why:** Option 1 now, option 2 only if time allowed, and only for countries absent from the training labels, so country stays an open set. It fixes the failing operation directly and can be checked on US/India labels. Lists and thresholds come from US/India labels and label-free test counts: a "real" word is used by at least 20 S1 names, a garble has Indel similarity of at least 0.5, minimum length 4. The list-A words are hand-written lexicons: English center, services, service, partners; French fils, cie, services, associés, groupe, développement, france. The rules are not applied to US/India: there the op-B drop would remove 27 pairs that are 93% true (holdout F0.5 −0.000003 [M]; the holdout is the fixed 25% of labelled US/India S1, 549,699 S1, that no model trained on).
- **Evidence:**
  - Op-B truth on the holdout: 0.6% of 5,364 pairs [M]. Op-A truth: US 99.8–99.9%, India 98.3–98.6% [M].
  - v4 predicts op B at 65.9 per 1000 French S1, against 0.04–0.05 in US/India [M].
  - Generator agent: in the true-copy cell, "groupe", "développement" and "france" appear at 27.6, 33.5 and 30.3 per 1000 French S1, against 1.2–1.9 for pure look-alike words [E] [chat:ameya/agent-afe57301 2026-09-26 03:44].
  - Forecast by per-S1 arithmetic (France is 0.14975 of test S1): drop +0.00248, add about +0.0002, total +0.0027 on the public leaderboard (LB) if France follows US/India rates; worst case −0.0017 [E].
- **Outcome:** Drops/adds on later models: v4ops 17,088 / 4,746; v5ops 19,336 / 3,278; v5all-ops 18,434 / 6,086 [M]. The share-shift estimator put the rules at +0.013–0.014 France F0.5 (+0.002 LB) [E]. The rules were first seen on the leaderboard inside upload 26 Sep #01 (public LB 0.98781, rank 15; France implied 0.971–0.976, up from about 0.93 [E]), together with five other changes, so their own value was never isolated [LB 2026-09-26 #01](../../submissions/records/2026-09-26_sub01.md).
- **Hindsight:** The forecast was optimistic. The method was the turning point for France: reverse-engineer the generator from labels, measure each population's truth rate on US/India, apply it only where labels are missing. The final methodology keeps its descendants. The chat figure of 16,971 op-B records on v4 (03:34) differs from the decision record's 17,088; the record is used here.
- **Links:** [decision france-generator-ops](../../docs/decisions/2026-09-26_0417_france-generator-ops-and-final-fit.md) · [handover 2026-09-26_0417](../../docs/handover/2026-09-26_0417_ameya_france-generator-ops.md) · [ANALYSIS_v4 §3](../../experiments/ameya/model-v1/ANALYSIS_v4.md) · [chat:ameya/19e315ba 2026-09-26 03:34] · [chat:ameya/19e315ba 2026-09-26 04:37] · [commit d5553cd]

### D-RUL-02 · France rules v2: add APP and ACR; reject NUM and CODE
- **When (IST):** 2026-09-26 06:04–06:27 (decision record 06:26) · **Phase:** P2 · **Area:** RUL
- **Decided by:** Ameya (analysis: agent for Ameya, from the France fork's patterns a–e; Ameya merged PR #26)
- **Status:** adopted
- **Problem:** Five populations were left after v1: (a) look-alikes whose street has a typo; (b) list appends with nothing dropped (APP); (c) acronyms at the same address (ACR); (d) house-number edits (NUM); (e) typos in 2–3 letter codes (CODE).
- **Options considered.** `post_ops.py --measure` sorts every US/India holdout candidate pair into these populations with the code that runs on France. Truth rates [M]:

  | population at the S1's address | US truth | India truth | verdict |
  |---|---|---|---|
  | B look-alike swap, incl. street typo | 3.1% | 0.6% | drop |
  | A drop + list append, incl. street typo | 99.7% | 98.3% | add |
  | APP list append, nothing dropped | 98.9% | 99.6% | add |
  | ACR acronym | 99.9% | 99.8% | add |
  | NUM house number −1 or −2 | 97.6% | 78.2% | no |
  | NUM one digit substituted / inserted or deleted | 91.0% / 95.0% | 70.9% / 90.4% | no |
  | CODE short-code typo | 42.6% | 44.0% | no |
- **Choice and why:** B, A, APP and ACR. NUM was rejected because "the model's rejections are right in India and France's rate is unknown; adding pays only above 75% precision"; the `nx` features let the model learn number edits instead. CODE is below any break-even. An add must meet three conditions: the pair is in the candidate set, the S1 is the record's best S1, and the record is not predicted elsewhere. The street key now tolerates a typo in the street word.
- **Evidence:** On v5all-c2 in France: 19,503 drops (v1: 18,406); adds A 7,227 (v1: 6,086), APP 3,877, ACR 853; 1,562 further adds fell outside the candidate set and were not made, about +0.00005 LB forgone [M counts, E for the value]. Expected +0.002 France F0.5 (+0.0003 LB) over v1 [E].
- **Outcome:** In upload 26 Sep #01 (v5all-ops2-c2, public LB 0.98781 [M]). The isolating upload (`v5all-ops2-c2` against `v5all-ops-c2`) never happened. The rules stayed in every later package.
- **Hindsight:** Gating each rule population on labelled truth rates before applying it blind to France was the right discipline.
- **Links:** [decision france-rules-v2](../../docs/decisions/2026-09-26_0626_france-rules-v2.md) · [RESEARCH_v5 §6](../../experiments/ameya/model-v1/RESEARCH_v5.md) · [PR #26] · [chat:ameya/19e315ba 2026-09-26 06:04] · [chat:ameya/19e315ba 2026-09-26 06:06]

### D-RUL-03 · France rules v3: a robust same-address test
- **When (IST):** 2026-09-26 15:41–15:57 (decision record 15:57) · **Phase:** P3 · **Area:** RUL
- **Decided by:** Ameya (proposed by: agent for Ameya, research session)
- **Status:** adopted
- **Problem:** A hand review of 22 French S1 found 1,291 op-B look-alikes still predicted (5.0 per 1000 French S1). The rules test "at the S1's own address" with a (house number, first street word) key, and French addresses break it: suffixed numbers ("8BIS", "129 D", "51 T"), typo'd street types ("AVEUNE", "ASLEE", "Pace"), "Q." for Quai, and two-letter typos in short names ("Arts" / "Arst"). The same misreadings also blocked op-A and APP adds.
- **Options considered:**
  1. Keep rules v2.
  2. Rules v3 (`post_ops.py --robust-addr`): read the first number without its suffix; take the street as the set of words after it, skipping street types (exact or up to a typo), articles and suffixes; two addresses match when the numbers are equal and the street sets share a word up to a typo (edit distance 1 for short words, 2 for long).
- **Choice and why:** Option 2, after measuring the pairs that only the new test matches, on the US/India holdout [M]: look-alikes India 3,178 pairs at 0.0% true, US 406 at 1.2%; A India 1,305 at 87.4%, US 4,037 at 99.1%; APP 468 at 97.0% and 851 at 89.4%; ACR 48 at 95.8% and 27 at 100%. Adding pays above about 72% precision (a false add costs about 0.18 F0.5, a miss about 0.07). Unit checks pass on all nine misread cases, and two true negatives stay apart ("4 Rue de Saverne" against "4 R. Roger Astic").
- **Evidence:** On v6all it drops 21,365 French op-B predictions (v2: 20,168) and adds A 4,062, APP 3,167, ACR 770 [M counts]. Expected +0.001 France F0.5, about +0.00015 LB [E].
- **Outcome:** In every candidate from `v6all-s3-ops3` on (upload 26 Sep #02, public LB 0.988609, France implied about 0.973 [M]/[E]). Never isolated on the leaderboard: the planned package `v6all-ops3-c2` was not uploaded.
- **Hindsight:** Kept to the end. Bakshi's independent file (D-RUL-05) removed 1,148 French pairs from v5all, and the rules-v3 packages already drop all but one of them.
- **Links:** [decision rules-v3-and-stage3](../../docs/decisions/2026-09-26_1557_rules-v3-and-stage3.md) · [RESEARCH_v6 §2.7](../../experiments/ameya/model-v1/RESEARCH_v6.md) · [PR #35] · [LB 2026-09-26 #02](../../submissions/records/2026-09-26_sub02.md)

### D-RUL-04 · Bakshi's composed-edit rules and address veto kept disabled
- **When (IST):** 2026-09-26 15:45–16:13 · **Phase:** P3 · **Area:** RUL
- **Decided by:** Bakshi (with his agent)
- **Status:** rejected (no evidence of gain)
- **Problem:** Composed name edits fall outside `post_ops`' single-edit parser, and the address key can collapse distinct streets. Could new rules on top of rules v2 help France: an address veto on rule adds, swap-plus-list drops, multi-append adds, and exact or parsed-street "rescues"?
- **Options considered:** 1. Enable the new rules. 2. Keep them as diagnostics only (chosen).
- **Choice and why:** "Neither the composed-edit rules nor the address guard passed evidence requirements; all new changes stay disabled. No v7 submission or measured gain is claimed." On the released dev kit v3 (698,372 selected pairs, not v6): the address guard vetoed 3 eligible baseline adds, all true; `swap_list` predictions were 196 of 197 true (US) and 48 of 48 (India), so dropping them would hurt; `multi_append` had 0 eligible adds and `drop_multi_list` 1, false. The two rescue probes found 0 dev residuals, and on test 2 and 12 ambiguous residuals with compatible owners.
- **Evidence:** Dev macro F0.5 0.9885633928 before and after, paired Δ 0, CI [0, 0] [M, dev kit v3]. On v5 France the composed-edit families touch only 18 predictions [M].
- **Outcome:** NUM and CODE stayed disabled as in the recipe. `rule_edits.py` was merged as a diagnostic [PR #34]. Further work was blocked because the full v6 artifacts were "absent locally and in checked GitHub locations".
- **Hindsight:** A clean negative result, and the first appearance of Bakshi's later general lesson: "unconditional truth rates of an edit family do not establish precision among pairs a strong model rejects" (D-RUL-13).
- **Links:** [PR #34] · [v7 README](../../experiments/bakshi/v7/README.md) · [handover 2026-09-26_1545](../../docs/handover/2026-09-26_1545_bakshi_v7-france.md) · [status bakshi @7ee1ceb](../../docs/status/bakshi.md)

### D-RUL-05 · Bakshi's robust-B probe prepared, not selected; no slot spent on it
- **When (IST):** 2026-09-26 16:37 (probe built) → 16:53 (Ameya's side) · **Phase:** P3 · **Area:** RUL / SUB
- **Decided by:** Bakshi (prepare, do not select); agent for Ameya (do not spend an upload slot)
- **Status:** deferred (never uploaded; PR #37 left open)
- **Problem:** v5's op-B drop missed French look-alikes when street markers or suffixes broke the address key. Bakshi built a file from v5 (`matching_resultsBakshi.tsv`) that removes 1,148 French pairs over 1,137 S1 and changes nothing in US/India. Ameya's `research-v6` branch already had a robust-address fix (commit 717f00b).
- **Options considered:** 1. Apply the robust B drop as published. 2. Add a whole-token repetition exception (chosen for the probe): never drop a pair whose name repeats a word ("Pinnacle Asset Group" → "Pinnacle Asset Asset"). 3. Wait for v6, stage 3 and rules v3.
- **Choice and why:** Bakshi: on dev-v3 all 18 accepted pairs the unprotected rule would reject were true repeated-word copies, 3 of them in the holdout; with the exception the dev result is unchanged (Δ 0), "not a positive gate". The agent for Ameya at 16:53: the removed pairs are op-B swaps at the same address (98% same first number, 0% same name, 0% empty address) that rules v2 missed because of messy addresses. The rules-v3 packages still predict only 1 of them. Bakshi's file is v5all plus about 0.0001 at best, while the next candidate also carries v6all's gains. So no slot.
- **Evidence:** Probe sha256 `714112f9…`, validator PASS, 132 tests [M]. France effect unmeasured.
- **Outcome:** Ameya's rules v3 went into `v6all-s3-ops3` and later models. Whether the repetition exception was ever adopted is not recorded.
- **Hindsight:** An independent confirmation that rules v3 was right.
- **Links:** [PR #37] · [v7 README](../../experiments/bakshi/v7/README.md) · D-RUL-03 · [chat:ameya/19e315ba 2026-09-26 16:53]

### D-RUL-06 · French acronym join, unlabelled countries only
- **When (IST):** 2026-09-26 18:17–19:04 · **Phase:** P3 · **Area:** RUL
- **Decided by:** Ameya (proposed by: agent for Ameya, prompted by Ameya's "anything which adds is good")
- **Status:** adopted, France only
- **Problem:** Blocking v3 lost 2,186 French v5all predictions (8.4 per 1000 S1), 953 of them acronyms at the S1's address ("PU" for "Passion Union"). A record named by its S1's initials matches only through the address, and French records often carry a street typo ("Rue Vaubna"), so blocking misses it.
- **Options considered:**
  1. An exact-address blocking view: about a 3 h rebuild for 516 extra holdout pairs, about +0.00007.
  2. A join on (country, house number, initials), confirmed by the robust same-address test and `name_edit == "acr"`; keep records that no S1 holds and that have exactly one such S1 (`acr_join.py`).
  3. Nothing. A second choice sat inside option 2: apply it everywhere, or only without labels.
- **Choice and why:** Option 2, only where there are no labels. On the holdout the acronym-at-address pattern is 99.72% true in the US (723 pairs; the 19 records no S1 holds, France's case, are all true) but 66.1% true in India (758), because India's compound addresses make "same address" unreliable [M].
- **Evidence:** France: 20,471 acronym pairs at the S1's address; 3,872 have a record no S1 holds and exactly one S1 with those initials there, and only 75 of them were candidates; a 24-pair sample was all genuine [E]. Expected +0.0009 France F0.5 (+0.00014 LB) [E].
- **Outcome:** +3,872 pairs on v6all, +3,910 on v7ce3, +3,936 on v7n, +3,832 on v7nst. The adds go into the matches and the candidate file (about 3.8k pairs, 0.002 per S1); the strict audit later caught these as matches outside the older candidate file (D-PKG-04). The join is in every package from upload 26 Sep #02. Later 48 of 3,832 French adds (1.25%) crossed cities, because French streets share first names such as Jules; the `city` rule fixed that (D-RUL-10). The 27 Sep size-bias test confirmed that French acronyms are true copies (D-FRA-19).
- **Hindsight:** The methodology says "acronym joins and per-source caps apply everywhere". That sentence blends this France-only join with the hunt's `acr` rule (D-RUL-09), which does apply to all countries.
- **Links:** [RESEARCH_v6 §5.2](../../experiments/ameya/model-v1/RESEARCH_v6.md) · [handover 2026-09-26_1817](../../docs/handover/2026-09-26_1817_ameya_ce-large-box.md) · [PR #40] · [chat:ameya/19e315ba 2026-09-26 18:29]

### D-RUL-07 · Brand-name join rejected (`brand_join.py` kept, not applied)
- **When (IST):** 2026-09-26 18:17 (measured) → 19:02 (closed) · **Phase:** P3 · **Area:** RUL
- **Decided by:** agent for Ameya; Ameya
- **Status:** rejected. One record (the 18:17 handover) lists it as "deferred, outcome unknown"; the research note and the chat close it as not applied.
- **Problem:** The analysis suggested 6–9 per 1000 French S1 were missing invented brand names ("Nylabelo") at single-S1 addresses, with a different house number from the S1's.
- **Options considered:** 1. Join records that carry one invented 5–15 letter token, used by no S1 name in the country, to the only S1 at that address, and apply it only if the holdout truth is at least 0.9. 2. Skip.
- **Choice and why:** Skip. "Unlike acronyms, an invented name does not tie the record to its S1."
- **Evidence:** The model already predicts the good ones (US 7,559 pairs, 98.8% true). The records no S1 holds are only 37% true in the US (197 pairs) and 40% in India (20) [M] [RESEARCH_v6 §5.3](../../experiments/ameya/model-v1/RESEARCH_v6.md).
- **Outcome:** `brand_join.py` stayed in the repo, deliberately not applied. The 27 Sep re-checks of unowned brand copies agreed (D-RUL-15, item 5).
- **Hindsight:** unknown (none recorded).
- **Links:** [handover 2026-09-26_1817](../../docs/handover/2026-09-26_1817_ameya_ce-large-box.md) · [chat:ameya/19e315ba 2026-09-26 18:52]

### D-RUL-08 · No new French rules overnight (typos, abbreviations, cities)
- **When (IST):** 2026-09-27 01:21–01:26 and 02:17–02:40 · **Phase:** P3 · **Area:** RUL
- **Decided by:** agent for Ameya
- **Status:** adopted at the time; reversed for abbreviation copies and cross-city pairs at 04:15 (D-RUL-10)
- **Problem:** Find French rules that recover what the model misses.
- **Options considered:**
  1. A typo-at-address add rule. US/India garbled-word copies are 96.7% true and 96.7% predicted; France predicts only 75.3% of its 37,437, so 9,242 are unpredicted. But French descriptor words share suffixes (Ecole/Collège, Primaire/Sportive, Maternelle/Culturelle), so many French "typos" are look-alikes. Rejected.
  2. An abbreviation-expansion add (Cie/Compagnie, St/Saint, Ets, Sté, Assoc; a hand-written lexicon): 1,658 pairs at the address, 91% already predicted (1,884 in a wider chat count); judged too rare for a new rule, about +0.000005 LB.
  3. A city-mismatch drop: 140 French predictions name another city (0.5 per 1000 S1), 48 of them acronym-join adds (French streets share first names: Jules, Jean, Joseph). Worth about +0.00001 LB: "not worth a late pipeline change".
  4. Same-address swaps and unrelated-name records: France's acceptance matched the US/India truth in every population.
- **Choice and why:** No night rule. France's remaining gain was judged to be "in the models" (self-trained cross-encoders), not in new rules.
- **Evidence:** [M] counts above; [E] values [RESEARCH_v6 §6.12](../../experiments/ameya/model-v1/RESEARCH_v6.md) · [chat:ameya/19e315ba 2026-09-27 01:23] · [chat:ameya/19e315ba 2026-09-27 02:20].
- **Outcome:** Reversed in part once a gate existed: the polish agent's `copy` (+332 on v7s, 176 of them abbreviation-equal) and `city` (−89) rules were adopted at 04:15 on labelled population evidence (D-RUL-10). RESEARCH_v6 §6.16: the "small leak, not fixed" of the acronym join "is fixed by `city`".
- **Hindsight:** With rivals moving by 0.00001, small rules with strong population evidence were worth stacking. Size alone was the wrong reason to skip them.
- **Links:** D-RUL-10 · D-RUL-06

### D-RUL-09 · Hunt rules: acronym adds and generator caps everywhere; crowded-record drop for US/India only
- **When (IST):** 2026-09-27 04:05–04:25 · **Phase:** P4 · **Area:** RUL
- **Decided by:** Ameya (proposed by: the hunt sub-agent abb9ffcd, launched after Ameya's "Don't overlook or discard negligible gains, we are now at 13th rank"); the main-session agent for Ameya narrowed the French part
- **Status:** `acr` and `cap` adopted; `nsa` and `rank0` superseded by the decide agent's expected-F0.5 rule (area DEC)
- **Problem:** Find holdout error categories that a simple rule fixes and that are positive on both fixed halves A and B of the holdout.
- **Options considered.** Gates on v7s, change in holdout F0.5 in units of 1e-6 [M]:

  | rule | gain [95% interval] | note |
  |---|---|---|
  | `acr` | +2.3 [+1.1, +3.7] | 19 adds, all true |
  | `cap` | +0.4 [0.0, +0.9] | |
  | `nsa` | +6.7 [−0.8, +14.7] | |
  | `rank0` | +23.6 [+1.8, +46.7] | half A crosses zero on both models |
  | acr + cap + nsa | +9.4 [+1.7, +17.5] | |
  | all four | +33.1 [+9.4, +56.3] | |
- **Choice and why:**
  - `acr`: add an owned, unheld pair (pc at least 0.1) whose record name is the S1's initials and whose address is not empty. 37 of 37 such holdout pairs are true.
  - `cap`: an S1 keeps at most 5 S2, 6 S3 and 11 records, trimming its lowest-pc predictions. Train truth never exceeds 5 S2 or 6 S3 over 2.2M S1.
  - Both follow from how the data was generated, so they apply to all countries.
  - `nsa` (drop a prediction with pc in (threshold, 0.75] when 4 or more S1 compete for the record; these pairs are 65–68% true, below break-even) and `rank0` (an empty S1 takes its best owned pair at pc in (0.6, threshold]) rest on a calibration measured only on US/India, so US/India only.
  - The main-session agent narrowed France: it kept 16 of the 21 French acronym adds (5 carried a different house number or street, the generator's nudged look-alikes, for example 3 → 335 and 41 → 542) and skipped the 22 French cap drops as "a coin flip that hurts F0.5", because they included perfect copies at pc 0.997–1.000 that the French pc cannot rank.
- **Evidence:** Gates above [M] [chat:ameya/agent-abb9ffcd 2026-09-27 04:05] · [chat:ameya/19e315ba 2026-09-27 04:11].
- **Outcome:** The decide agent's dynamic programme subsumed `rank0` and turned `nsa` into a calibration shift. `acr` and `cap` were stacked in D-RUL-11. The methodology: "Acronym joins and per-source caps apply everywhere."
- **Hindsight:** unknown (none recorded).
- **Links:** [RESEARCH_v6 §6.16](../../experiments/ameya/model-v1/RESEARCH_v6.md) · [decision stacked-rules](../../docs/decisions/2026-09-27_0636_stacked-rules.md)

### D-RUL-10 · Polish rules for France: exact-address copy add and cross-commune drop
- **When (IST):** 2026-09-27 04:15–04:19 · **Phase:** P4 · **Area:** RUL
- **Decided by:** Ameya (proposed by: the polish sub-agent aeb3d218; the main-session agent read all 89 drops by hand before trusting them)
- **Status:** adopted, only for countries without training labels
- **Problem:** France missed abbreviation copies (Cie ↔ Compagnie, Ets ↔ Etablissements, St/Ste ↔ Saint/Sainte: 1,658 same-address pairs, 91% predicted, the 144 misses looking true), and the acronym join accepted cross-commune pairs (48 of the 140 French predictions whose two addresses name different communes).
- **Options considered:** The copy rule as briefed; a stricter copy rule; the city rule; `city_acr` (only the acronym part of the city rule).
- **Choice and why:** The stricter copy rule plus the city rule. The agent changed the brief on measured evidence: empty record addresses are excluded (25–33% true on US/India even when the S1 is the record's best and the record is free); equal address numbers are required (pairs differing only in a secondary number are 1–2% true); a strict street match is required (French streets share first names; v7nst adds 469 → 417); changed legal forms are excluded.
  - `copy`: add an unpredicted pair with equal names (up to legal forms, stop words, word order, Cie/Ets/St/Ste), the exact same address and the same numbers, where the S1 is the record's best candidate and the record is free.
  - `city`: drop a pair whose S1 and record name different communes.
- **Evidence:**
  - `copy` population truth: US 99.992% (n = 332,869), India 99.998% (n = 47,206) [M].
  - French adds +332 on v7s, at least 88% precise even if all about 40 expected false pairs fell among them, against a 73% break-even [E].
  - French true copies change commune 3 times in 546,465 pairs (5.5e-6), against 4.56% in the US and 0.90% in India [M].
  - `city` drops −89 on v7s with P(false) about 95% (at least 87%) [E]. Applied to US/India the city rule would cost −0.01054 [M], so it never runs there.
- **Outcome:** Stacked in D-RUL-11. The methodology: "an exact-address copy rule (99.99% precise on US and India), a cross-commune drop". The decision to skip these overnight (D-RUL-08) was reversed here.
- **Hindsight:** The agent's caveat stands: true copies that changed both street and commune were not measured.
- **Links:** [chat:ameya/agent-aeb3d218 2026-09-27 04:19] · [RESEARCH_v6 §6.16](../../experiments/ameya/model-v1/RESEARCH_v6.md) · D-RUL-08

### D-RUL-11 · Stack the rules on every final candidate (`-dpc`)
- **When (IST):** 2026-09-27 06:36 (update 08:35) · **Phase:** P4 · **Area:** RUL / DEC
- **Decided by:** Ameya (analysis: the hunt, polish and decide sub-agents for Ameya)
- **Status:** adopted. Applied to every final candidate from v7s on; the `-h2pc` package (threshold + acr + cap + nsa) is the conservative fallback.
- **Problem:** The threshold was already optimal (tuning it on the holdout overfits: repeated 2-fold CV gives −18.8e-6 out of sample). The plain expected-F0.5 rule looked like a tie (+0.00003 [−0.00002, +0.00007] on v7mst). France's remaining loss was substitutions, and two French populations had never been checked: exact copies the model misses and cross-commune pairs.
- **Options considered.** US/India holdout, v7s, gain in units of 1e-6 [M]:

  | rules on the labelled countries | full [95% interval] | P(better) | half A | half B |
  |---|---|---|---|---|
  | threshold + acr + cap + nsa | +9.4 [+1.7, +17.5] | 0.990 | +10.0 | +8.6 |
  | + rank0 | +33.1 [+9.4, +56.3] | 0.996 | +18.1 | +55.6 |
  | expected-F0.5 per S1 (shift +0.2, phantom 0.01) | +33.2 [−7.5, +75.0] | 0.945 | −7.8 | +94.7 |
  | + acr + cap | +35.9 [−4.8, +77.6] | 0.958 | −4.8 | +97.1 |
  | + crowd shift −0.3 (records with 4 or more S1 at p1 of at least 0.02) | +48.1 [+7.1, +91.2] | 0.987 | +7.7 | +108.7 |
- **Choice and why:** The whole stack, built by `stack/stack.sh <model>`. US/India: expected-F0.5 with the crowd shift, plus `acr` and `cap`. France: the narrowed hunt plus `copy` and `city`; no `cap` or `nsa` in France, because their evidence rests on calibration measured only on US/India. The shift and phantom were chosen on v7nst's half A and confirmed on half B (+45.5e-6); the crowd shift was chosen on v7s's half A from {0.15, 0.3, 0.45} and confirmed on half B.
- **Evidence:**
  - The +48.1e-6 [+7.1, +91.2] is the combined layer: expected-F0.5 with shift, phantom and crowd shift, plus `acr` and `cap`. The expected-F0.5 rule alone is +33.2e-6, P 0.945, and its halves disagree, so it is not significant [M].
  - Selection bias checked: repeated 2-fold CV of the rule with the phantom gives +23.7e-6 out of sample, positive in 86% of 42 splits [M].
  - `fhs.py` against v7s (a label-free count of true copies gained and lost, per 1000 French S1): the hunt's own French changes score −0.02; the narrowed hunt plus polish scores +1.09 [E].
- **Outcome:** The port to the repo was verified set for set (D-PKG-08). On the leaderboard, v7nst-dpc scored 0.990264 against v7nst's 0.990179: +0.000085 for the stack [M] [LB 2026-09-27 #01](../../submissions/records/2026-09-27_sub01.md). Expected total on v7sq: about 0.9903.
- **Hindsight:** The methodology credits the "+0.000048 (95% interval 0.000007 to 0.000091)" to the dynamic programme alone ("beat the best global threshold"). By the table above it belongs to the combined layer. The DP alone was +0.0000332 and not significant.
- **Links:** [decision stacked-rules](../../docs/decisions/2026-09-27_0636_stacked-rules.md) · [RESEARCH_v6 §6.16](../../experiments/ameya/model-v1/RESEARCH_v6.md) · D-RUL-09 · D-RUL-10 · [PR #58] · [theory: metrics and decisions](../theory/04-metrics-and-decisions.md)

### D-RUL-12 · Drop rule from cross-encoder disagreement (bge below 0 while e5 above 0)
- **When (IST):** 2026-09-27 09:17–09:20 (narrowed at 10:04) · **Phase:** P4 · **Area:** RUL / FRA
- **Decided by:** Bakshi
- **Status:** rejected
- **Problem:** 97% of v7sq-dpc's French predictions sit at pc of at least 0.99, so the remaining French loss looks like confident substitutions that no threshold reaches. Can disagreement between cross-encoders (text models that read both records together) find them?
- **Options considered:** 1. Drop kept French pairs where bge votes against both e5 runs. 2. No rule.
- **Choice and why:** No rule. The population is real and the right size (France 12.17% against a 2.04% US/India background, an excess of 8,111 pairs, up to +0.000843 LB if all were wrong), but the signal is anti-selective: it fires on 17.76% of known-true French kept pairs and on 8.74% of pairs of unknown truth. bge is the weakest single model on France and more conservative there (29.9% positive logits against e5-large's 36.9%). "Its value is in the averaged mix … a drop rule uses precisely the individual votes that are untrustworthy."
- **Evidence:** [M, proxy] [CONFIDENT_SUBSTITUTIONS](../../experiments/bakshi/final-package/CONFIDENT_SUBSTITUTIONS.md). Only 5.5% of final predictions are inside the cross-encoder band (France 9.2%).
- **Outcome:** At 10:04 Bakshi narrowed his own conclusion: the result rejects deletion on raw logit sign, not every verifier. That evening his 7B re-check, a separately trained verifier checked on labelled data, was the verifier that worked (D-LLM-05).
- **Hindsight:** unknown (none recorded).
- **Links:** [confident_disagree.py](../../experiments/bakshi/final-package/confident_disagree.py) · [commit 7ce6e34] · [issue #45]

### D-RUL-13 · Structural French recall recovery
- **When (IST):** 2026-09-27 11:25 · **Phase:** P4 · **Area:** RUL / FRA
- **Decided by:** Bakshi
- **Status:** rejected ("my first verdict was wrong")
- **Problem:** Can a structural criterion, calibrated on US/India train truth, add unpredicted French pairs at high precision?
- **Options considered:** Core name plus full address; core name plus house number; core name alone.
- **Choice and why:** Core name plus house number first looked like +0.000370 at 0.8698 unconditional precision. But the pairs a rule would add are ones the model already saw and rejected, so the figure that matters is precision conditional on rejection: 0.4010 (−0.001077), and 0.0563 for name alone (−0.009203), against a 75% break-even. The "record unowned" filter makes it worse, because unowned records are enriched for genuine orphans (26% of S2/S3 records match no S1).
- **Evidence:** [E, from train truth] [recall_headroom.py](../../experiments/bakshi/recovery/recall_headroom.py) · [commit 6a8df7b].
- **Outcome:** With thresholds, disagreement deletion (D-RUL-12), alias bridging and this, "four routes closed by measurement … all fail the same way: they compete with a well-tuned model on its own rejections."
- **Hindsight:** The same lesson as D-RUL-04, stated generally.
- **Links:** [commit 6a8df7b] · D-RUL-17

### D-RUL-14 · Drop French look-alike word swaps at the S1's address (`apply_swapsim.py`)
- **When (IST):** 2026-09-27 11:38 (flagged) → 12:12 (ported) · **Phase:** P4 · **Area:** RUL
- **Decided by:** Ameya (proposed by: agent for Ameya, from its size-bias scan; the French error-population sub-agent abeb7453 agreed)
- **Status:** adopted at 12:12; in the uploaded mixmdp and in Composite B. Questioned at 17:03 (D-RUL-16).
- **Problem:** 592 French predictions of v7sq-dpc swap one real word for a similar-looking real word at the S1's address (category `swap_real_sim`): "college du marie" → "ecole du marie", "phare ecole sasu" → "phare comite sasu", "escalade ecole sas" → "escalade college sas". France predicts these at 2.28 per 1000 S1, against 0.55 in the holdout.
- **Options considered:**
  1. Drop all of them. This is model-independent: the drop list covers all 8,297 such candidate pairs, so it works for any French model.
  2. Drop only the 80 that also have a nudged house number.
  3. Keep them.
- **Choice and why:** Drop, in France only, never touching the labelled countries. Three independent signals agreed. The size-bias test (D-FRA-19) gave f = 0.83 [0.56, 1.10], where f is the false share. The count test of the sub-agent gave holders an average of 4.39 against 4.01. US/India base rates imply about 130 genuine copies among 484 same-address cases, so at least 73% are false. Break-even is f of about 0.28. Value about +0.00004–0.00005.
- **Evidence:** All three signals [E]. The repo port reproduced the agent's 592 pairs exactly, in 13 s [M] [commit d475cdd]. The size-bias test under-states false shares for false records that do not attach to random S1.
- **Outcome:** Applied in mixc, mixd, mixe, mixf, mixg, mixh to mixm and the uploaded mixmdp; it drops 348 to 820 pairs depending on the French model (454 in mixmdp). mixc was rebuilt byte for byte from repo code at 12:27. After the leaderboard, RESEARCH_v6 §6.20 calls its effect "about neutral" (LB residual +18e-6) [E].
- **Hindsight:** The record warns that the test "under-states false shares" and "is invalid for a population that takes most of an S1's copies". The final methodology still lists "a look-alike word-swap drop" among the France rules. See D-RUL-16 for the argument that it hurt.
- **Links:** [RESEARCH_v6 §6.17](../../experiments/ameya/model-v1/RESEARCH_v6.md) · [handover 2026-09-27_1228](../../docs/handover/2026-09-27_1228_ameya_final-day.md) · [LB 2026-09-27 #03](../../submissions/records/2026-09-27_sub03.md) · [chat:ameya/agent-abeb7453 2026-09-27 11:34] · [chat:ameya/19e315ba 2026-09-27 12:12] · D-FRA-19

### D-RUL-15 · No further French rule adds or drops from data scans
- **When (IST):** 2026-09-27 12:20, 12:28, 13:38, 14:44, 15:22, 17:07 · **Phase:** P4 · **Area:** RUL
- **Decided by:** agent for Ameya (cell adds proposed by the France-diff sub-agent)
- **Status:** rejected, all seven
- **Problem:** Several French populations looked anomalous.
- **Options considered, with the evidence for each:**
  1. Drop `drop1/nudge` pairs (177). France predicts them at 4.7 times the US/India rate and size bias gives f = 0.78 [0.35, 1.24]. But the examples are ambiguous (many are "ecole primaire X" → "primaire X" at a nearby number), holdout candidates of this kind are 59.7% true, and the gain is negligible [E].
  2. Exact name, different street: at break-even [E].
  3. Fix wrong owners: 15 of 15 holdout cases were already correct; 278 French pairs share an exact address with a rival S1, and 174 of those already picked the exact-name match [M].
  4. Remove copies over the generator's per-source caps: 16 French S1 have more than 5 S2 copies (3 more than 6 S3), about 20 pairs, worth about +0.000002 [E].
  5. Add the 634 unowned French brand copies at single-S1 addresses (15%). In the US and India only 2.6% and 3.6% are unowned, and those are only 36% and 35% true; the French true rate is 60–95%, so the value is ±0.00003 [E].
  6. Cell adds where France under-predicts cells that are near-certain in US/India (claimed up to +0.0002–0.0005). In the same cells the US/India rows the model rejects are 93–100% false, so adding them would cost 0.00002–0.0006 [M].
  7. An address-only recall view for about 5,200 missed holdout pairs whose addresses match (+0.0007–0.0008 hoped). Earlier brand-join work showed such unowned records are only 37–40% true [M].
- **Choice and why:** Each failed its control. Under F0.5 an added pair must be right at least 75% of the time, and "for S1s that already have copies a false add costs 3× what a true one gains".
- **Evidence:** [chat:ameya/19e315ba 2026-09-27 12:20] · [14:44] · [15:22] · [17:07].
- **Outcome:** No rule. Nothing from these scans reached an upload.
- **Hindsight:** unknown (none recorded).
- **Links:** D-RUL-07 · D-RUL-13 · D-RUL-17

### D-RUL-16 · Build later candidates without the look-alike drop
- **When (IST):** 2026-09-27 17:03 · **Phase:** P4 · **Area:** RUL
- **Decided by:** agent for Ameya (proposed by: the France-diff sub-agent's leaderboard-history test); the upload stayed Ameya's call
- **Status:** adopted for the packages built after 17:03 (mixnc, mixqc, mixq7, mixsc, mixsd), none of which was uploaded. The final, Composite B, uses mixmdp's France, which has the drop.
- **Problem:** The look-alike drop (+0.00004 by the size-bias test) was the least validated part of mixmdp, and mixmdp landed about 0.00008 below its prediction.
- **Options considered:** 1. Keep dropping. 2. Stop dropping (mixnc). 3. Upload mixnc to settle the question on the leaderboard.
- **Choice and why:** Stop dropping. The France-diff agent re-scored all six past uploads with these same-address word swaps forced to "false"; predictions got worse (mean error 0.000102 against 0.000056). Every time a model dropped many of them, the leaderboard paid less than "false" implies. "In France these swaps ('ecole/college', 'comite/societe', 'amicale/amis') behave like true copies. The US/India look-alike rule doesn't transfer." The 30 "compagnie/etablissements" cases are op-A copies, a known true-copy operation.
- **Evidence:** The drop is worth about −27e-6 [E]. mixnc was expected at mixmdp + 0.000033, about 0.99073: +0.000006 from the v7sq8wg model and +0.000027 from keeping the 453 pairs [E] [chat:ameya/19e315ba 2026-09-27 17:06].
- **Outcome:** mixnc was built, passed the validator, and was recommended as the next upload at 17:07, but not uploaded by 18:08. The leaderboard never tested it. The team's final upload plan went to the 7B parts instead (D-SUB-23).
- **Hindsight:** RESEARCH_v6 §6.20 later found the drop "about neutral". The final document still describes the drop as part of the pipeline, so the record holds an unresolved inconsistency: three estimates of its value (+40e-6 to +50e-6 by size bias, −27e-6 by the leaderboard-history test, about +18e-6 as a leaderboard residual) never met a controlled upload.
- **Links:** [RESEARCH_v6 §6.20](../../experiments/ameya/model-v1/RESEARCH_v6.md) · D-RUL-14 · [chat:ameya/agent-a2762d22 2026-09-27 17:07]

### D-RUL-17 · No recall ("add") rules
- **When (IST):** 2026-09-27 19:24–21:03 · **Phase:** P4 · **Area:** RUL
- **Decided by:** agent for Ameya
- **Status:** rejected
- **Problem:** France predicted about 0.02–0.03 fewer matches per S1 than US/India, although true counts should be equal. The agent estimated about 7,800 missed French copies, worth up to about +0.0003 [E] [chat:ameya/19e315ba 2026-09-27 19:24].
- **Options considered:** 1. Add unpredicted pairs the 7B likes (D-LLM-08). 2. A two-way rule: our stage-3 probability and the 7B both high. 3. An empty-address exact-name rule. 4. A "(france)" acronym rule (acronyms that skip the word "(france)").
- **Choice and why:** None reached the 75% precision an F0.5 addition needs.
  - 7B add rule: at most 71.4% precise (42 adds, 30 true at logit above 5) [M].
  - Two-way rule: at pc of at least 0.5 and logit above 4, 30 adds at 66.7%; the two halves give −0.000014 and +0.000019 [M].
  - Empty-address exact name: 287 holdout pairs, 40.1% true [M].
  - "(france)" acronyms: 143 French pairs; even at 80–95% precision worth only +0.000001 to +0.000004, because a recovered copy gains about 0.06 per S1 while a wrong addition costs about 0.17 [E].
- **Evidence:** [chat:ameya/19e315ba 2026-09-27 19:35] · [19:37] · [19:38] · [21:02].
- **Outcome:** No recall rule in any upload. The methodology states that none of the recall rules tried was more than 71% precise.
- **Hindsight:** Consistent with Bakshi's and Sachi's own recall analyses (24–59% precise slices; copy-count ties 0.31 against 0.27 by chance).
- **Links:** D-LLM-08 · D-RUL-13 · D-RUL-15 · [theory: metrics and decisions](../theory/04-metrics-and-decisions.md)
