# Decisions: SUB (leaderboard strategy, uploads, final-model choice)

**Summary.**
- The challenge allowed 5 leaderboard uploads a day. The public leaderboard (LB) was used as a sanity check and, from 26 Sep, as France's only measuring instrument, because France has no labels: slots went to real candidates and to one-change controls (two uploads that differ in one part, so the score gap isolates it), never to pure probes, and the file to be ranked was meant to go last.
- The path of record: v5all with France rules 0.98781, v7nst (France self-training) 0.990179, v7sq-dpc 0.990545, mixmdp 0.990699, then Composite B 0.990879 (the best: US/India from g1w, Bakshi's model with the 7B language model counted twice in its mix; France from mixmdp; minus the pairs the 7B rejects), and B7 0.990875 (the last upload, a tie). The ZIP carries Composite B.
- Open items: which upload the private ranking used (Composite B or B7) is unknown; the real close of the upload window (21:00 IST was planned, uploads were made until about 23:40) and the daily limit (7 uploads recorded on 27 Sep) are not explained in the records; no private score exists, only the ranking (2nd of the Top 10).

## Index

| ID | decision | when (IST) | status |
|---|---|---|---|
| D-SUB-01 | Leaderboard policy and upload budget | 2026-09-25 14:15 | adopted, then changed in practice |
| D-SUB-02 | Build our own baseline for Submission 1 early | 2026-09-25 15:32 | adopted |
| D-SUB-03 | A stricter decision variant (DP shift −0.5) kept as a backup probe | 2026-09-25 18:57 | deferred |
| D-SUB-04 | Take three ideas from another team's plans | 2026-09-25 23:11 | adopted (candidate cut, owner pruning, self-training) |
| D-SUB-05 | Plan for a 21:00 IST close; the last upload is the model to be ranked | 2026-09-26 00:41 | adopted for planning; contradicted later |
| D-SUB-06 | The candidate file is the set the matcher actually scores | 2026-09-26 02:00 | superseded by the candidate-set cut (area BLK) |
| D-SUB-07 | v4 as the recommended upload; v5 commits held back from PR #23 | 2026-09-26 02:02 | adopted for the merge; v4 never uploaded |
| D-SUB-08 | Upload plan of 12:24: v5all-ops2-c2 now, v4 plus a France probe, v6all after its gate | 2026-09-26 12:12 | partly done |
| D-SUB-09 | With one slot left, upload the candidate, not a probe | 2026-09-26 16:16 | adopted |
| D-SUB-10 | No slot for Bakshi's robust-B TSV | 2026-09-26 16:53 | adopted |
| D-SUB-11 | Upload v7n (safe) first, then v7nst (the bet); the last slot before midnight is not a probe | 2026-09-26 23:00 | adopted |
| D-SUB-12 | 27 Sep upload discipline: no pure probes, one change per upload, the best last | 2026-09-26 23:54 | adopted, then broken in the evening |
| D-SUB-13 | First uploads of 27 Sep: v7s-dpc, replaced by v7sq-dpc | 2026-09-27 05:19 | adopted |
| D-SUB-14 | Default final: v7sq-dpc over the bag of seven | 2026-09-27 08:27 | superseded by D-SUB-16 and the leaderboard |
| D-SUB-15 | Spend upload 2 on v7nst-dpc as a controlled comparison | 2026-09-27 09:11 | adopted |
| D-SUB-16 | Compose finals per country; measure France alone | 2026-09-27 10:55 | adopted |
| D-SUB-17 | Reject consensus editing; screen candidates by change footprint | 2026-09-27 12:16 | rejected (editing); footprint screen adopted |
| D-SUB-18 | US/India from v7sq3 rather than the four-model bag | 2026-09-27 12:42 | superseded by D-SUB-21 |
| D-SUB-19 | Check for hidden levers, then say 0.993 and 0.992 are out of reach | 2026-09-27 13:11 | adopted (advice) |
| D-SUB-20 | Hold uploads for the best package; upload mixmdp | 2026-09-27 14:46 | adopted |
| D-SUB-21 | US and India from Bakshi's g1w in Composite B | 2026-09-27 18:51 | adopted |
| D-SUB-22 | One evening upload, mixf2; a brief switch to mixf4 reverted | 2026-09-27 19:49 | superseded by D-SUB-23 |
| D-SUB-23 | Upload Composite B first, as a probe with a pre-set rule | 2026-09-27 20:46 | adopted (the best score) |
| D-SUB-24 | After B: a one-change follow-up (mixf7) and "always upload the best expected model" | 2026-09-27 20:53 | adopted |
| D-SUB-25 | The last hours: no switch away from Composite B | 2026-09-27 22:06 | adopted |
| D-SUB-26 | The last slot: B+ or B7 | 2026-09-27 22:09 | B7 uploaded (a tie); B+ never uploaded |

Related records: the France probes that were built and never uploaded are D-FRA-12; the 7B parts of Composite B are D-LLM-05 and D-LLM-09; the ZIP's choice of Composite B is D-PKG-10; the rules inside each package are in area RUL.

## Uploads referred to below

Public LB scores from [CHANGELOG](../../CHANGELOG.md) and [submissions/records/](../../submissions/records/). Times are those in the records ("about" means reported with the score).

| upload | package | public LB | what it isolated |
|---|---|---|---|
| 25 Sep, earlier | v2, then v3 | 0.97608, 0.97961 | the first models; France implied about 0.93 |
| 26 Sep #01, about 14:38 | v5all + France rules v2 + 3.70 candidates per S1 | 0.98781 (rank 15) | all France work since v3 |
| 26 Sep #02, evening | v6all + stage 3 + rules v3 + acronym join | 0.988609 (rank 15) | |
| 26 Sep #03, about 23:05 | v7n (two e5-large cross-encoders) | 0.989721 (rank 8) | France 0.978 |
| 26 Sep #04, about 23:35 | v7nst (France self-training) | 0.990179 (rank 7) | France alone: +0.000458 |
| 27 Sep #01 | v7nst-dpc | 0.990264 | the stack: +0.000085 |
| 27 Sep #02, about 10:05 | v7sq-dpc | 0.990545 (rank 7) | the model: +0.000281 |
| 27 Sep #03, about 16:40 | mixmdp | 0.990699 (rank 12) | guarded round 2 + France DP: +0.000154 |
| 27 Sep #04, about 20:55 | Composite B | 0.990879 (rank 16), the best | the 7B parts: +0.000180 |
| 27 Sep #05, about 21:55 | mixf7 (B with round-3 France) | 0.990833 | round 3: −0.000046 |
| 27 Sep #06, about 21:55 | mixf2 (mixf7 with v7sq3 US) | 0.990819 | g1w's US: +0.000014 |
| 27 Sep #07, about 23:40 | B7 (B + French drops toward −2) | 0.990875 | a tie with B |

Order note: the records number v7nst-dpc as 27 Sep #01 ("morning") and v7sq-dpc as #02 (about 10:05); the chat puts v7sq-dpc at about 10:05 and v7nst-dpc after it, at about 10:22.

## Records

### D-SUB-01 · Leaderboard policy and upload budget
- **When (IST):** 2026-09-25 14:15 · **Phase:** P0 · **Area:** SUB
- **Decided by:** Ameya
- **Status:** adopted, then changed in practice
- **Problem:** Five uploads a day (15 in total, per the plan), and the risk of overfitting the public LB.
- **Options considered:** not recorded.
- **Choice and why:** Plan about 10–11 uploads and keep one slot a day in reserve. The LB is a sanity check, plus one France-versus-empty probe (gate G7) and at most one threshold probe. "Never tune several knobs on the public leaderboard"; decisions come from the 550k-entity holdout. Every upload gets a record, a `sub/` tag and a changelog row, and the final upload is the chosen model. The captain's budget plan: Fri 25 Sep 5 slots (first valid baseline 1–2, a quick fix 1, keep 1–2 spare), Sat 26 Sep 5 (main improvements 3, France and threshold probes 1, 1 spare), Sun 27 Sep 5 (final candidates 2–3, 1 spare; the last upload must be the chosen final model).
- **Evidence:** [FINAL_PLAN §5.7, §8](../../plans/FINAL_PLAN.md) · [submissions/README](../../submissions/README.md).
- **Outcome:** The team's records list 4 uploads on 25 Sep (v2 was submission 3, then v3; only the v2 and v3 scores are in the changelog), 4 on 26 Sep and 7 on 27 Sep, against the stated limit of 5 a day; how the portal allowed seven on 27 Sep is not recorded. The LB became France's only measuring instrument, and uploads were designed so that a difference isolated France (v4 − v3ce; the France-only compositions mixf7, mixf2 and B7). The France-emptied probe was never uploaded (D-FRA-12).
- **Hindsight:** unknown (none recorded).
- **Links:** [CHANGELOG, Submissions](../../CHANGELOG.md) · D-SUB-12

### D-SUB-02 · Build our own baseline for Submission 1 early
- **When (IST):** 2026-09-25 15:32 · **Phase:** P1 · **Area:** SUB
- **Decided by:** Ameya ("Let's start right now"); proposed by: agent for Ameya
- **Status:** adopted
- **Problem:** The team pipeline (normalise, features, model) could slip past 23:00. The upload itself (about 100 MB) was untested, and no mapping from holdout score to leaderboard existed.
- **Options considered:** Wait for v0 at 23:00; build a fast baseline now; a fallback of a blocking-score cut-off plus house-number agreement (proposed at 15:20).
- **Choice and why:** Build the baseline now, a validated file by about 17:30. It "checks the upload itself works", "gets us our first public score" and "shows how our holdout score maps to the leaderboard". It also gave Sachi real features.
- **Evidence:** Sub 1 ready at 17:07: holdout 0.9683, validator PASS with `--check-ids` [M].
- **Outcome:** Whether and when Submission 1 was uploaded, and its public score, are not in the sources. The baseline became the reference for every later gate.
- **Hindsight:** unknown (none recorded).
- **Links:** [handover 2026-09-25_1706](../../docs/handover/2026-09-25_1706_ameya_block-v0-baseline.md)

### D-SUB-03 · A stricter decision variant (DP shift −0.5) kept as a backup probe
- **When (IST):** 2026-09-25 18:57–19:07 · **Phase:** P1 · **Area:** SUB / DEC
- **Decided by:** agent for Ameya
- **Status:** deferred (prepared, not recommended as the primary)
- **Problem:** On test, model v1 put about twice the holdout's owned-pair mass in the uncertain 0.5–0.9 band, a possible look-alike over-acceptance.
- **Options considered:** Submit model v1 as is; submit a stricter shift; prepare both.
- **Choice and why:** The stricter variant costs −0.0003 on the holdout (0.97975 against 0.98006) and predicts 0.9% fewer test pairs (3.27 against 3.30 per S1). It is cheap insurance if the LB disappoints.
- **Evidence:** [M] holdout; test pairs 5,666,845 against 5,719,569.
- **Outcome:** Archived in `submissions/files/probe-2026-09-25-sm05/`. No use is recorded.
- **Hindsight:** The v2 look-alike encoding cut the band excess to about 1.2 times, making the probe less relevant. Gate G8 later showed that a stricter France threshold "only loses" (D-FRA-12).
- **Links:** D-FRA-12

### D-SUB-04 · Take three ideas from another team's plans
- **When (IST):** 2026-09-25 23:11–23:19, and 2026-09-26 00:59 · **Phase:** P2 · **Area:** SUB / BLK / FRA
- **Decided by:** agent for Ameya (analysis); adopted by the team in later work
- **Status:** adopted for three ideas (the candidate cut, owner pruning, self-training); the other points were checked and not needed or not taken
- **Problem:** Ameya pasted another team's planning documents ("compare this to us").
- **Options considered, and what was taken:**
  1. An organiser update reportedly says smaller candidate sets rank higher (second-hand: "we need to verify that update ourselves"). Taken: cut the lists, and cut before the scoring model.
  2. Self-training on confident French pairs, tested first as US → India. Taken, later (D-FRA-13).
  3. Keep each record only with its best 1–2 S1 (owner pruning). Taken: the cut keeps a pair only if it is among its record's top 2 S1 (D-SUB-06).
  4. Other points: check content-identical duplicates (checked, "need nothing", D-PRB-04); portal hazards (Windows `.tsv` MIME "Bad Request", 60–100 MB "Failed", where the zip goes, failed uploads counting); AWS Builder Center verification for every member; questions for the organisers. From the second document: French address clusters and stratified calibration (measured and skipped, D-FRA-06), typo repair against the S1 vocabulary, and a claimed ceiling of 0.9955.
  Not taken: their doubts about pretrained encoders (ours were licence-clean), their memory limits, and accent stripping (ours already folded "Collège" to "college", checked in code).
- **Choice and why:** Take what we could verify. Our blocking was already at 98.99% recall with 30.3 per S1 on the full holdout, against their 98.0% at 29.8 on a 10% slice [M against R].
- **Evidence:** The candidate file went 34 → 4.75 → 3.70 per S1 (area BLK). Duplicates "need nothing": the truth groups exact duplicates under one S1.
- **Outcome:** Self-training was adopted on 26 Sep at 21:17 (D-FRA-13). The size rule was never verified first-hand in these sources; the cut was a holdout tie, so it cost nothing.
- **Hindsight:** unknown (none recorded).
- **Links:** [chat:ameya/19e315ba 2026-09-25 23:11] · D-SUB-06 · D-FRA-02

### D-SUB-05 · Plan for a 21:00 IST close; the last upload is the model to be ranked
- **When (IST):** 2026-09-26 00:41–00:49, upload policy 02:16–02:30; confirmed 26 Sep late evening (issue #45) and 27 Sep 01:49–02:38 · **Phase:** P2–P3 · **Area:** SUB / ORG
- **Decided by:** agent for Ameya and Ameya (proposed by: the research sub-agent ada9694b, which read the public pages); the captain read 21:00 on the portal
- **Status:** adopted for planning; contradicted later in the record
- **Problem:** `AGENTS.md` and the Unstop main page said the stage ends 23:59 IST on 27 Sep. The Unstop submission-round page said "Assessment Window: 25 Sep 26, 03:30 AM CUT to 27 Sep 26, 03:30 PM CUT" (27 Sep 15:30 UTC = 21:00 IST), and Internshala said 9:00 PM IST. The same page said the private leaderboard is "based on your final solution submission", and that ties go to the earlier submission. Also unknown: whether the day resets at IST or UTC midnight, and whether failed uploads count.
- **Options considered:** Plan for 23:59; plan for 21:00 with the final upload around 19:00; confirm in the logged-in portal.
- **Choice and why:** Plan for 21:00: "missing that would be fatal, and planning for it costs us only three hours". One person uploads (the captain, Ameya). Keep a spare slot and never leave a probe last. Plans used a 13:00 model cutoff, a 15:00 freeze and a 19:00 upload target. The `AGENTS.md` line needs a dedicated PR on a shared file, so it was left to Ameya; Bakshi flagged it repeatedly.
- **Evidence:** Web pages read by the agent and not re-checked [R] [chat:ameya/agent-ada9694b 2026-09-26 00:41]. The captain's reading is on [issue #45], recorded at 23:12 in one source and 23:43 in another. [handover 2026-09-26_0207](../../docs/handover/2026-09-26_0207_ameya_leaderboard-gap-france-v4.md) asks the captain to "confirm the deadline in the portal".
- **Outcome:** Every 27 Sep brief said "deadline 21:00 IST", and the ROADMAP records the window as ending 21:00. Yet Composite B scored at about 20:55, mixf7 and mixf2 followed at about 21:55 and B7 at about 23:40, and the agent planned uploads at 22:18 and 22:55 "before the 23:59 deadline". How the window was actually resolved is not in the sources. Later deadlines, for reference: ZIP and methodology due 29 Sep 10:00 IST; finale deck due Tue 6 Oct 14:00 IST; finale Wed 7 Oct.
- **Hindsight:** The conservative plan cost nothing. The reading "the final submission counts" shaped the rule "the best must be uploaded last" (D-SUB-12). Whether the private ranking used the best or the last upload was "reported both ways" (D-SUB-26).
- **Links:** [chat:ameya/19e315ba 2026-09-26 00:49] · [chat:ameya/19e315ba 2026-09-27 01:49] · [issue #45] · [handover 2026-09-27_0111](../../docs/handover/2026-09-27_0111_bakshi_final-package.md)

### D-SUB-06 · The candidate file is the set the matcher actually scores
- **When (IST):** 2026-09-26 ~02:00 · **Phase:** P2 · **Area:** SUB / BLK
- **Decided by:** Ameya
- **Status:** superseded by the candidate-set cut at 05:32 (area BLK)
- **Problem:** `candidate_pairs.tsv` was the raw blocking output (34 per test S1, 781 MB), but the README asks for "the exact set of records you feed into your matching model for inference … the last [filtering stage]".
- **Options considered:** Keep the blocking output; write the stage-2 input set; cut further to each record's top 1–2 S1.
- **Choice and why:** Write the stage-2 input (p0 at least tau0, p1 at least 0.002) with `cands_final.py`. Keeping only each record's top 2 S1 would cost recall ceiling (0.9825) for 20% fewer pairs, "not worth it unless a size-based ranking is confirmed. Nothing public says it is: the only tie-break is submission time."
- **Evidence:** 33.99 → 4.75 pairs per test S1 (US 4.49, India 4.50, France 6.21); 781 → 129 MB; holdout pair recall 0.98992 → 0.98926; oracle 0.99697 → 0.99676 [M] [A3 §6].
- **Outcome:** Reversed a few hours later, when the organisers announced a size-based ranking: smaller candidate sets per S1 rank higher. The cut to p1 of at least 0.02 and the record's top 2 S1 gives 3.70 per S1 for a holdout tie (F0.5 −0.000003), at the price of pair recall 0.98927 → 0.98198 and oracle 0.99676 → 0.99452 [M] [decision candidate-set-cut](../../docs/decisions/2026-09-26_0532_candidate-set-cut.md). Retrieval recall before the cut is 99.1% at about 34 per S1; the final 3.70-per-S1 file holds about 98.2–98.4% of the true holdout pairs.
- **Hindsight:** The methodology quotes 99.1% for the final 3.70-per-S1 file, which is the pre-cut figure (D-PKG-20).
- **Links:** [handover 2026-09-26_0207](../../docs/handover/2026-09-26_0207_ameya_leaderboard-gap-france-v4.md)

### D-SUB-07 · v4 as the recommended upload; v5 commits held back from PR #23
- **When (IST):** 2026-09-26 02:02–02:10 · **Phase:** P2 · **Area:** SUB / ORG
- **Decided by:** Ameya ("raise pr and merge"), on the recommendation of the agent for Ameya
- **Status:** adopted for the merge. The upload itself did not happen: v4 was never uploaded.
- **Problem:** Two packages were ready (v3ce, holdout 0.99021; v4, 0.99015), and the v5 tokenizer commits sat on the same branch, ungated.
- **Options considered:** 1. Upload v3ce. 2. Upload v4. 3. Both, to attribute the cross-encoder gain and the France fixes separately.
- **Choice and why:** v4. Its US/India predictions tie v3ce on the holdout (Δ −0.00006 [−0.00012, −0.00001]), so its extra LB would be France alone. The forecast was +0.006 to +0.009 over v3. For PR #23, a clean worktree from commit 3c94c5b kept v5's tokenizer commits off main, so that v4 could still be rebuilt exactly from main.
- **Evidence:** [M] [decision model-v4](../../docs/decisions/2026-09-26_0207_model-v4-france-and-cross-encoder.md).
- **Outcome:** Overtaken by later candidates before any upload.
- **Hindsight:** Keeping main reproducible per gated model was good discipline.
- **Links:** [PR #23] · [chat:ameya/19e315ba 2026-09-26 02:06] · D-FRA-03

### D-SUB-08 · Upload plan of 12:24: v5all-ops2-c2 now, v4 plus a France probe, v6all after its gate
- **When (IST):** 2026-09-26 12:12–12:24 · **Phase:** P3 · **Area:** SUB
- **Decided by:** Sachi proposed it; the agent for Ameya agreed and gave the files; Ameya uploads
- **Status:** proposed; the first item happened at about 14:38
- **Problem:** "Our board still shows v2 (0.976, ~89th)", with 5 slots a day.
- **Options considered:** Upload only the best, or spend 2 slots measuring France.
- **Choice and why:** Both. France's level decides whether France work is worth it. The last upload before the deadline must be the one to rank, because the private LB uses the final submission.
- **Evidence:** Package hashes: v5all-ops2-c2 `76fe7eff…`, v4 `cd09df65…`, probe-v4-fr0 `36247a77…`, v6all-ops-c2 `0f6d8985…` [chat:ameya/19e315ba 2026-09-26 12:24].
- **Outcome:** v5all-ops2-c2 went up (public LB 0.98781, rank 15 [M], [LB 2026-09-26 #01](../../submissions/records/2026-09-26_sub01.md)). The v4 and `fr0` uploads did not happen (D-FRA-12).
- **Hindsight:** unknown (none recorded).
- **Links:** [chat:ameya/19e315ba 2026-09-26 12:12]

### D-SUB-09 · With one slot left, upload the candidate, not a probe
- **When (IST):** 2026-09-26 16:16 · **Phase:** P3 · **Area:** SUB
- **Decided by:** Ameya, on the agent's advice
- **Status:** adopted
- **Problem:** Three packages were ready (`v6all-s3-ops3-c2`, `probe-v6s3-fr0`, `probe-v6s3-fr090`), and the record says only one upload remained that day.
- **Options considered:** The candidate; the France-emptied probe; the France threshold probe.
- **Choice and why:** The candidate: "it stacks every change that has evidence behind it". The probes "don't help on their own": `fr0` scores about 0.85 and means nothing without its pair; `fr090` "is a coin flip in expectation". The last slot before the deadline was reserved for the final pick, "never a probe".
- **Evidence:** Expected about 0.9885. Read-out table: 0.9884 or more = the changes carry over; below 0.98781 = fall back to `v5all-ops2-c2` [E] [chat:ameya/19e315ba 2026-09-26 16:16].
- **Outcome:** The "v6all" upload reported 0.988609 (rank 15) [M] [LB 2026-09-26 #02](../../submissions/records/2026-09-26_sub02.md). Which package folder was uploaded is not confirmed.
- **Hindsight:** Two more uploads followed on the same IST day (about 23:05 and about 23:35), so "one slot left" was not a literal count of the day's budget.
- **Links:** D-FRA-12

### D-SUB-10 · No slot for Bakshi's robust-B TSV
- **When (IST):** 2026-09-26 16:53 · **Phase:** P3 · **Area:** SUB / RUL
- **Decided by:** agent for Ameya (recommendation, parallel research session)
- **Status:** adopted
- **Problem:** Bakshi produced `matching_resultsBakshi.tsv` (v5all minus 1,148 French pairs; D-RUL-05).
- **Options considered:** Upload it as a probe, or skip.
- **Choice and why:** Skip. The removed pairs are op-B swaps at the same address that slipped through rules v2 because of messy addresses, and the rules-v3 packages already drop all but one of them. Bakshi's file is v5all plus about 0.0001 at best, while the next candidate also has v6all's gains.
- **Evidence:** [E] [chat:ameya/19e315ba 2026-09-26 16:53].
- **Outcome:** Not uploaded.
- **Hindsight:** An independent confirmation that rules v3 was right.
- **Links:** D-RUL-05 · D-RUL-03

### D-SUB-11 · Upload v7n (safe) first, then v7nst (the bet); the last slot before midnight is not a probe
- **When (IST):** 2026-09-26 23:00–23:32 · **Phase:** P3 · **Area:** SUB
- **Decided by:** Ameya, on the agent's advice ("we should be thoughtful")
- **Status:** adopted
- **Problem:** Two candidates were equal on US/India and differed only in France; one upload was left on 26 Sep.
- **Options considered:** v7nst first; v7n first; only one of them. For the last slot: v7nst; `fr0` ("information only, nothing to act on"); `fr090r` ("more useful once we know which model is final").
- **Choice and why:** v7n first, then v7nst, keeping the higher. The two are identical on US/India, so the difference is France alone. Under F0.5 v7nst's lean toward dropping is cheap: "a dropped false positive gains 0.18 while a dropped true pair costs 0.07. So it is about neutral even if only half its changes are right, and about +0.0003 LB if 75% are." The last slot went to v7nst because "it settles tomorrow's biggest decision": if self-training works, the self-trained cross-encoder (v7s) leads; if not, drop that line for v7m. Read-out: above 0.9899 it works; 0.9895–0.9899 a wash; below 0.9895 it hurts. France change = (score − 0.989711) / 0.14975.
- **Evidence:** Predicted before v7n: 0.9894 at France 0.976 and 0.9900 at 0.980; v7n hit it [E] [RESEARCH_v6 §6.10](../../experiments/ameya/model-v1/RESEARCH_v6.md).
- **Outcome:** v7n 0.989721 (rank 8, about 23:05), then v7nst 0.990179 (rank 7, about 23:35) [M] [LB 2026-09-26 #03](../../submissions/records/2026-09-26_sub03.md), [#04](../../submissions/records/2026-09-26_sub04.md): "self-training on France works".
- **Hindsight:** The pair isolated the self-training effect cleanly: US/India equal within 0.00002, so France +0.0031 (D-FRA-13).
- **Links:** [chat:ameya/19e315ba 2026-09-26 23:31] · D-FRA-13

### D-SUB-12 · 27 Sep upload discipline: no pure probes, one change per upload, the best last
- **When (IST):** 2026-09-26 23:54 → 2026-09-27 12:30 (Bakshi's restore rule 10:55–11:34) · **Phase:** P3–P4 · **Area:** SUB
- **Decided by:** Ameya (captain); the restore rule proposed by Bakshi and endorsed by the agent for Ameya
- **Status:** adopted, then broken in the evening (D-SUB-22 to D-SUB-24)
- **Problem:** Five slots, candidates only about ±0.00004 apart (the public LB's own noise), and the last upload possibly the one that is ranked.
- **Options considered:** Spend 2–3 slots on `fr0` and `fr090r` probes (D-FRA-12), or make every upload a real attempt at a new best. For the second, the record gives no list of options.
- **Choice and why:** "5 slots, no pure probes." Pairs of uploads that each isolate one change: v7nst-dpc against v7nst is the stack, v7sq-dpc against v7nst-dpc is the model, and `fr-v7sq4` would be France alone with US/India byte-identical. "The French threshold stays as the model decides it." "The final submission counts, so the best must also be the last upload", re-uploaded "early enough that nothing is rushed" (by 18:30). Bakshi's rule at 10:55: "if the best measured file isn't the last upload by 18:30, stop experimenting and restore." At 11:34 the last upload was v7nst-dpc (0.990264), below v7sq-dpc (0.990545).
- **Evidence:** The leaderboard "resolves gaps of about ±0.00004 between these candidates only". Self-training had emptied the band around the French threshold, so a threshold probe touches about 12 predictions per 1000 French S1, about ±0.00005 [M]/[E] (D-FRA-12).
- **Outcome:** The morning split worked: +0.000085 for the stack and +0.000281 for the model. The planned `fr-v7sq4`, `mixb` and `mixc` were never uploaded; mixmdp went up at 16:40 instead (D-SUB-20). At about 14:30 Bakshi's plan stated "the BEST upload counts, not the latest", correcting the "live risk" note in his ledger; at 14:46 Ameya still wrote "we have only 3 uploads, so we have to send in our best". The discipline broke in the evening: the plan of 20:14 for one upload became four (Composite B, mixf7, mixf2 and B7).
- **Hindsight:** Best versus last was never settled (D-SUB-26).
- **Links:** [status ameya @75b4276](../../docs/status/ameya.md) · [handover 2026-09-27_1228](../../docs/handover/2026-09-27_1228_ameya_final-day.md) · [FINAL_PUSH_PLAN §1](../../experiments/bakshi/box/FINAL_PUSH_PLAN.md) · [chat:ameya/19e315ba 2026-09-27 01:45] · [chat:ameya/19e315ba 2026-09-27 10:53]

### D-SUB-13 · First uploads of 27 Sep: v7s-dpc, replaced by v7sq-dpc
- **When (IST):** 2026-09-27 05:19 → 06:05; uploaded at about 10:05 · **Phase:** P4 · **Area:** SUB
- **Decided by:** Ameya (the upload), proposed by: agent for Ameya; Bakshi later concurred
- **Status:** adopted
- **Problem:** Pick the first of five slots. The last upload counts, and the LB cannot separate near-identical candidates (about ±0.00004–0.00005).
- **Options considered:** v7nst-dpc (the rules on the scored model), v7s-dpc, v7sb-dpc, v7sq-dpc. The unstacked v7mst, v7nst2 and v7ens2 were "too small to spend a slot on alone".
- **Choice and why:** v7s-dpc at 05:19 (best expected value: US/India part +0.000037 over v7nst, `fhs` +1.11, strict audit PASS). At 06:05 v7sq-dpc replaced it as best on every measure: holdout 0.991246, US/India part 0.843258, `fhs` +2.19, validator and strict audit PASS. Tests written down: "right if" the LB beats v7nst by more than the ±0.00004 noise; "wrong if" it falls below about 0.9902, with v7nst-dpc as the fallback.
- **Evidence:** [M] holdout; [E] `fhs` and an expected LB of about 0.9903 [decision stacked-rules](../../docs/decisions/2026-09-27_0636_stacked-rules.md) · [chat:ameya/19e315ba 2026-09-27 05:19] · [06:05].
- **Outcome:** Public LB 0.990545, rank 7 [M]: +0.000366 over v7nst, three times the estimate.
- **Hindsight:** The right call. The French self-trained encoders (qst, e5ls) were worth far more than the label-free check suggested.
- **Links:** [LB 2026-09-27 #02](../../submissions/records/2026-09-27_sub02.md) · D-RUL-11

### D-SUB-14 · Default final: v7sq-dpc over the bag of seven
- **When (IST):** 2026-09-27 08:27 (default) → 09:12–09:20 (the bag out of contention) · **Phase:** P4 · **Area:** SUB / PKG
- **Decided by:** Ameya and Bakshi agreed (Ameya's default at 08:27, Bakshi's pick at 09:15); the captain uploads
- **Status:** adopted; superseded by composition (D-SUB-16) and by the leaderboard (mixmdp, then Composite B)
- **Problem:** Choose the model that the ZIP must reproduce, before any stacked candidate had a public score. v7sq-dpc and v7ensall2-dpc tie on expected leaderboard score (0.990295 against 0.990299).
- **Options considered.** Holdout and expected values:

  | candidate | holdout | US/India part | `fhs` | expected LB |
  |---|---|---|---|---|
  | v7ensall2-dpc (bag of seven; the tags of its bagged members were never recorded) | 0.991256 | 0.843266 | +1.85 | 0.990299 |
  | v7sq-dpc | 0.991246 | 0.843258 | +2.19 | 0.990295 |
  | v7nst-dpc | 0.991194 | 0.843210 | +1.43 | |

  Also: upload both and let the LB decide. At 08:35 the plan briefly named v7ensall2 the default final, then switched.
- **Choice and why:** v7sq-dpc, unless the bag's public score beat it by more than 0.00004. "Ties go to the simpler option (AGENTS.md): v7sq reproduces from 4 cross-encoders and 1 stage 2, while the bag of seven needs 7 cross-encoder runs (hours of GPU each) and 7 stage-2 runs", and its exact inputs were never recorded, so Bakshi could not add it to `reproduce.sh`. v7sq also keeps more French true copies; more French self-trained members lose true copies against v7nst (COPY lost: v7sq −2.04, v7sq3 −2.83, v7sq2 −3.20 per 1000 S1). Bakshi stressed that v7sq against v7nst-dpc "is not a tie": v7sq wins on all three measures, its lead is on the French axis where the deficit is, it has four model families including a decoder, and Qwen passed a predeclared two-sided gate.
- **Evidence:** [M] holdout; [E] expected LB [MODEL_CHOICE](../../experiments/bakshi/final-package/MODEL_CHOICE.md) · [issue #45].
- **Outcome:** Measured 0.990545 against Bakshi's expected 0.990295: "I was low by 3.0x". A validated v7sq-dpc ZIP (`4282b939…`) existed by 11:47, but the leaderboard moved on to mixmdp and then Composite B. v7ensall2-dpc was never uploaded.
- **Hindsight:** Reproducibility was a real constraint, because the organisers re-run the top teams' code.
- **Links:** [decision stacked-rules, update 08:35](../../docs/decisions/2026-09-27_0636_stacked-rules.md) · [status ameya @fbdd7a1](../../docs/status/ameya.md) · [commit 44743d7] · [PR #56] · [chat:ameya/19e315ba 2026-09-27 08:27] · [09:12]

### D-SUB-15 · Spend upload 2 on v7nst-dpc as a controlled comparison
- **When (IST):** 2026-09-27 09:11–09:17 (plan) → about 10:22 (upload) · **Phase:** P4 · **Area:** SUB
- **Decided by:** Ameya (Bakshi had asked for v7nst-dpc as slot 2; the agent laid out both options)
- **Status:** adopted
- **Problem:** After v7sq-dpc, was a second upload of v7nst-dpc worth a slot?
- **Options considered:**
  1. "Floor-first": upload v7sq-dpc once and stop; nothing can go out of sync. Offered by Ameya's agent; Bakshi argued that v7nst-dpc is dominated on every measure.
  2. "Plus a French check": also upload v7nst-dpc, then re-upload v7sq-dpc last. It costs two slots and changes the final only if v7nst-dpc beats v7sq-dpc by more than 0.00008, put at 10–15%.
  3. At 10:09, after 0.990545 arrived, the agent proposed v7sq3-dpc as the next upload instead.
- **Choice and why:** The captain uploaded both. The control isolates the stack and the model.
- **Evidence:** v7nst-dpc 0.990264 against v7nst 0.990179 gives the stack +0.000085. v7sq-dpc 0.990545 gives the model change +0.000281, of which about +0.00023 is France (France F0.5 about +0.0016) [M, LB; the France share is E].
- **Outcome:** The split showed that French adaptation was the lever and launched round 2 with the v7sq-dpc teacher (D-FRA-17). It also left a worse file as the latest upload (−0.000281): Bakshi recorded a "live risk" and proposed the restore rule (D-SUB-12), a restore slot became mandatory, and only two test slots remained.
- **Hindsight:** The cleanest attribution of the competition, at the price of one slot plus a forced restore. See the order note above the records: the chat and the record numbering disagree on which of the two went up first.
- **Links:** [issue #45] · [PR #60] · [chat:ameya/19e315ba 2026-09-27 10:29] · [LB 2026-09-27 #01](../../submissions/records/2026-09-27_sub01.md)

### D-SUB-16 · Compose finals per country; measure France alone
- **When (IST):** 2026-09-27 10:55 (plan) → 11:06 (mixa) → 11:49 (mixb) → 11:55 (repo port) → 19:47 (Bakshi's `compose_tsv.py`) · **Phase:** P4 · **Area:** SUB
- **Decided by:** Ameya (agent: `compose.py`, later `compose3.py`); Bakshi wrote `compose_tsv.py` for Composites A, B and B′ the same way
- **Status:** adopted for every upload from mixmdp on
- **Problem:** Two kinds of evidence rank different parts of the submission. The best US/India model on labelled data (v7sq3) was not the best French model, only three uploads were left, and one leaderboard number cannot judge two countries at once.
- **Options considered:** 1. Upload whole models, one for every country. 2. Compose: the countries with labels (read from the train records) come from one matches-and-candidates tag, every other country from another. 3. Bag several models.
- **Choice and why:** Compose. US/India have a reliable judge, the labelled holdout, and carry 85% of the LB weight; France needs its own judge. Composition gives clean France-only tests: keep v7sq-dpc's US/India and "LB − 0.990545" is the French effect alone (`fr-<m>`). All models share the same US/India candidates, so that part is byte-identical. Records never cross countries, so taking both the matching row and the candidate row of each S1 from one audited source keeps one owner per record and matches inside the candidates by construction. The tool refuses a record with two owners and any match outside the candidates. Labelled countries are read from the train records, never hard-coded.
- **Evidence:** `compose.py` reproduced mixb pair for pair (5,853,354 matches, 6,410,310 candidates) [M]. Composite B: 5,851,832 pairs, 0 two-owner records, 0 cross-country pairs, 0 matches outside 6,410,308 candidates [M]. The first build, `mixa`, took US/India from v7ensall2-dpc and France from v7sq-dpc: validator PASS.
- **Outcome:** mixmdp (16:40), Composite B (the best), mixf7, mixf2 and B7 are all compositions. Composite B's candidate file is the per-country union, which is why Ameya's local rebuild matched B's matching file byte for byte but not its candidate file (`b55c2b1d…`); the ZIP therefore uses Bakshi's uploaded pair (D-PKG-11).
- **Hindsight:** Composite B took the idea further: g1w for US/India, mixmdp for France, built with `compose3.py`.
- **Links:** [handover 2026-09-27_1228](../../docs/handover/2026-09-27_1228_ameya_final-day.md) · [handover 2026-09-27_2006](../../docs/handover/2026-09-27_2006_bakshi_final-push.md) · [compose_tsv.py](../../experiments/bakshi/box/compose_tsv.py) · [commit dad245b] · [commit 120e507] · [issue #66]

### D-SUB-17 · Reject consensus editing; screen candidates by change footprint
- **When (IST):** 2026-09-27 12:16–12:28 · **Phase:** P4 · **Area:** SUB
- **Decided by:** Bakshi
- **Status:** rejected (consensus editing); the footprint screen adopted as a pre-upload check
- **Problem:** With several validated candidates, can voting edit the best one, and which candidates can still reach 0.991?
- **Options considered:** 1. Drop base pairs that at most one voter keeps, add pairs that at least four voters keep. 2. Measure footprints first.
- **Choice and why:** Every candidate agrees with the base on 99.92–99.97% of predictions ("one model with tiny perturbations"). Consensus editing changes 3.03 French predictions per 1000 S1 (850 drops, 967 adds), a ceiling of about +0.000048. Anchored on v7nst → v7sq-dpc (16.6 per 1000 French S1 for +0.000281, about 0.000016 per unit), a candidate must change France by about 28 per 1000 to be able to reach +0.000455.
- **Evidence:** v7qbag changes 5.46 per 1000 (ceiling +0.000088) and v7sq4 10.90 per 1000 (+0.000175) [E] ([commit 9c7cb51], [commit c7f95b3]).
- **Outcome:** v7qbag and v7sq4 were not uploaded. The screen motivated the final push for "a qualitatively different model, not another variant" (D-LLM-04).
- **Hindsight:** unknown (none recorded).
- **Links:** [diff_candidates.py](../../experiments/bakshi/final-package/diff_candidates.py) · [consensus.py](../../experiments/bakshi/recovery/consensus.py)

### D-SUB-18 · US/India from v7sq3 rather than the four-model bag
- **When (IST):** 2026-09-27 12:42–12:44 · **Phase:** P4 · **Area:** SUB
- **Decided by:** agent for Ameya (the decide sub-agent recommended the bag, with v7sq3 as fallback)
- **Status:** superseded by D-SUB-21 (g1w in Composite B)
- **Problem:** Which model's US/India decisions go into the final under the production combination rule?
- **Options considered:** `bag4` (mean logit of v7sq3, v7qbag, v7sq2, v7sq4) 0.991312; v7sq3 0.991307; `bag5` 0.991307; per-country picks (v7sq3 best for the US, v7qbag for India).
- **Choice and why:** v7sq3. The bag's lead is not significant (+4.6e-6 [−10.6, +21.1]); v7sq3 is the only single model whose gain over v7sq has a confidence interval above zero (+27.3e-6 [+2.2, +52.6]); per-country picks from 8–10 correlated candidates on one holdout are biased upward; and ties go to the simpler option.
- **Evidence:** [M] [chat:ameya/agent-acec839c 2026-09-27 12:42] · [chat:ameya/19e315ba 2026-09-27 12:44].
- **Outcome:** mixb, mixc, mixd, mixe, mixf and mixmdp all took US/India from v7sq3. Composite B took them from g1w.
- **Hindsight:** unknown (none recorded).
- **Links:** D-SUB-21

### D-SUB-19 · Check for hidden levers, then say 0.993 and 0.992 are out of reach
- **When (IST):** 2026-09-27 13:11–13:12, 13:42, 17:43 · **Phase:** P4 · **Area:** SUB
- **Decided by:** agent for Ameya
- **Status:** adopted (as advice; the work continued)
- **Problem:** Ameya asked for 0.993 ("to be top 2"), then 0.992. The best was 0.990545.
- **Options considered:** 1. Promise a push. 2. Look first for a lever big enough, such as a leak or hidden structure. 3. Give an honest assessment.
- **Choice and why:** Look, then be honest. +0.0025 was needed, against about +0.0001 from every verified gain combined. At weight 0.15, a perfect France (0.983 → 1.0) adds only +0.0025. 0.992 needs US/India at about 0.9925 (it was at 0.9913), or France at parity. The checks found nothing: no ID or file-order leak, a US/India test that matches the holdout band by band, normal French counts, unrecoverable blocking misses. In the agent's words: "I don't want to promise something the numbers say we can't reach."
- **Evidence:** corr(S1 id, copy id) −0.0008 [M] [RESEARCH_v6 §6.18](../../experiments/ameya/model-v1/RESEARCH_v6.md).
- **Outcome:** A realistic target of about 0.9907–0.9908 was set (13:42). The upload in this slice scored 0.990699.
- **Hindsight:** The team's final, Composite B at 0.990879, was still below 0.992. The diagnosis that France at parity was the missing gain held up.
- **Links:** [chat:ameya/19e315ba 2026-09-27 13:12]

### D-SUB-20 · Hold uploads for the best package; upload mixmdp
- **When (IST):** 2026-09-27 12:18–14:04 (interim picks) → 14:46 (the rule) → 16:29–16:35 (the upload) · **Phase:** P4 · **Area:** SUB
- **Decided by:** Ameya (the agent recommended the package)
- **Status:** adopted; public LB 0.990699 (rank 12)
- **Problem:** Three uploads were left. The agent had recommended test uploads: `fr-v7sq4` (about 12:00), mixc (12:18), mixf (13:03), mixi (14:04).
- **Options considered:** 1. Test uploads, to learn about France. 2. Upload only the best package. At 13:03 the interim picks were: mixf (France from v7sqwg; estimated gain +0.00003 to +0.00004, downside −0.00005), mixe (v7sq6; +0.00004 to +0.00005, −0.0001), mixd (v7sq4; +0.00002 to +0.00003, −0.00008). mixf was the best risk-adjusted option, since the public LB "likely carries some sampling noise" (±0.00004 assumed). At 14:04 the pick switched to mixi, to test the v7sq6 direction; at 17:07 it was mixnc.
- **Choice and why:** Best only. Ameya: "we have only 3 uploads, so we have to send in our best, and that too not now" (14:46). At 16:29 he asked for the best model. The agent gave him mixmdp = v7sq3 US/India + v7sq7wg France − 454 look-alikes + France DP (357 adds, 224 drops): 1,732,544 rows, 3.70 candidates per S1. It had the best `cal` value (+0.000174), tied with mixk (+0.000166) and mixp (+0.000167).
- **Evidence:** Predicted about 0.99078 ±0.00005 [E]; measured 0.990699, +0.000154 [M].
- **Outcome:** A new best. The shortfall of about 0.00008 was put down to `cal` error (about 0.00004) and the look-alike drop's size-bias value (D-RUL-14, D-RUL-16). mixmdp's France is the France of Composite B.
- **Hindsight:** The interim picks were superseded and never uploaded.
- **Links:** [LB 2026-09-27 #03](../../submissions/records/2026-09-27_sub03.md) · D-FRA-20 · [chat:ameya/19e315ba 2026-09-27 14:46] · [chat:ameya/19e315ba 2026-09-27 16:31]

### D-SUB-21 · US and India from Bakshi's g1w in Composite B
- **When (IST):** 2026-09-27 18:51 → 21:08 · **Phase:** P4 · **Area:** SUB
- **Decided by:** agent for Ameya and Ameya, with Bakshi, who built Composite B (the evidence by the France-diff sub-agent a2762d22)
- **Status:** adopted. The agent recommended India only; Composite B took both US and India from g1w.
- **Problem:** Was g1w's holdout gain real (Bakshi's model with the Qwen2.5-7B cross-encoder counted twice in the mix; D-LLM-09), and in which country?
- **Options considered:** US and India from g1w; India from g1w and the US from v7sq3; hybrids (only g1w's adds, only its drops, extra gbag pairs).
- **Choice and why:** The agent's recommendation was India from g1w: +66.1e-6 [+19.4, +112.9], P 0.998, which survives a multiple-testing correction for about 8 sources times 2 countries. The US stays on v7sq3: g1w's US gain (+26.2e-6, P 0.906) fails that correction. No hybrid beats full g1w. The records do not say why the US was included in Composite B anyway.
- **Evidence:** Per-country paired bootstrap, every model's decisions rebuilt with the same production code [M]. The composition is clean (no pair outside our candidates, no record owned twice), and g1w's 2,734,431 India test pairs differ from ours by about 850 each way [M] [chat:ameya/agent-a2762d22 2026-09-27 18:51].
- **Outcome:** Composite B (France from mixmdp, US/India from g1w, 7B drops) scored 0.990879, +0.000180 over mixmdp [M]. The leaderboard later showed g1w's US at +14e-6 over v7sq3 (D-SUB-24), so including it was right but small. The methodology reports the same two per-country numbers.
- **Hindsight:** The submission record says the holdout implied about +10e-6 for the US, against +26.2e-6 in the agent's bootstrap; the two were not reconciled.
- **Links:** [chat:ameya/agent-a2762d22 2026-09-27 19:00] · [chat:ameya/agent-a2762d22 2026-09-27 21:08] · [LB 2026-09-27 #04](../../submissions/records/2026-09-27_sub04.md) · D-LLM-09

### D-SUB-22 · One evening upload, mixf2; a brief switch to mixf4 reverted
- **When (IST):** 2026-09-27 19:49–20:43 (the switch and its reversal at 20:09–20:11) · **Phase:** P4 · **Area:** SUB
- **Decided by:** Ameya ("we want to do one upload, best model only not latest"), with Bakshi and Sachi agreeing on issue #64 (proposed by: agent for Ameya)
- **Status:** superseded by D-SUB-23. mixf2 was uploaded later, as the US control.
- **Problem:** Two estimated-best packages, two slots, and nobody knew whether the best or the last upload counts.
- **Options considered:**
  1. mixf2: US v7sq3, India g1w, France v7sq6r3 (round-3 labels), minus 832 French and 310 US/India 7B rejects (5,851,827 pairs); predicted 0.99091 (0.99087–0.99095): round-3 France +0.00007, French drops +0.00008, India +0.00003, US/India drops +0.00003.
  2. mixf4: France round 4 plus the France DP, +11e-6 by `cal` (round 4 changes 3,553 of 1.43M labels); about 0.99092.
  3. mixf3 or v7sqsyd: France from the synthetic cross-encoders; `cal` liked them, but own-cal and the leaderboard-confirmed moves did not (D-FRA-23).
  4. Composite B, "the team's backup" (France = mixmdp, leaderboard-proven), and B′ (France from g1w's 7B-driven model).
- **Choice and why:** mixf2. At 20:09 the agent proposed mixf4 (every estimator slightly ahead), but Sachi and Bakshi had confirmed mixf2 before that, and it went back to mixf2 at 20:11: "Round 4 on its own gains nothing" (`cal` +212 against +215) and "a within-noise edge, bought with one more self-training round, is not worth it". Sachi's risk settled it: extra rounds degrade out of distribution (Bakshi's LOCO ladder, 0.882 → 0.851 → 0.831 → 0.823), which is France's case. For a second slot Ameya argued by expected maximum: under "best counts", B′ adds about +1e-6 (P(B′ > mixf2) about 5%) while mixf4 adds about +13e-6; under "last counts", B′ would cost about −0.0001. Bakshi first preferred B′ as "the most different" answer, then revised to Composite B, because it hedges exactly mixf2's one unverified part (round-3 France). `cal`'s record supported mixf2: it gave mixmdp's France +146e-6 and the measured part was about +134e-6.
- **Evidence:** [E] estimators ([issue #64], [PR #62] comments, [PR #65] review).
- **Outcome:** Measured later: Composite B 0.990879 > mixf7 0.990833 > mixf2 0.990819 [M]. Round-3 France lost.
- **Hindsight:** The issue thread was the right forum, and Sachi's warning about extra rounds was the most prescient comment of the evening, though what lost was round 3 without the French decision layer (D-FRA-24). Bakshi's revised hedge, Composite B, was the winning file; the leaderboard, not the estimators, settled France.
- **Links:** [handover 2026-09-27_2014](../../docs/handover/2026-09-27_2014_ameya_final-upload.md) · [chat:ameya/19e315ba 2026-09-27 20:09] · [20:10] · [20:11]

### D-SUB-23 · Upload Composite B first, as a probe with a pre-set rule
- **When (IST):** 2026-09-27 20:46–20:53 (decision) → about 20:55 (upload) · **Phase:** P4 · **Area:** SUB
- **Decided by:** Ameya with Bakshi, who built Composite B (`compose_tsv.py`) and proposed it as the first upload ("their idea is to upload composite b instead of ours"; "we are using composite b as a probe"); the agent for Ameya supplied the rule
- **Status:** adopted; became the final best submission
- **Problem:** The French 7B drop was the biggest and least certain gain (about +0.00008 estimated, no French labels), and both mixf2 and mixf4 contained it, so uploading them could not hedge that risk.
- **Options considered:** 1. mixf2, then mixf4 (the agent's two-line answer at 20:47). 2. Composite B first, then decide. 3. B′ (Bakshi's preferred second shot).
- **Choice and why:** Option 2. B is the measured mixmdp (0.990699) plus only the 7B parts (the drops in all countries and g1w's US/India), so its score minus 0.990699 measures those parts cleanly. The pre-set rule: B at 0.99078 or more, upload mixf2 next (it adds round-3 France); below 0.99078, upload mixf6, which is mixf2 without the French drop.
- **Evidence:** B predicted about 0.99085 [E]. Measured 0.990879, public rank 16 [M] [LB 2026-09-27 #04](../../submissions/records/2026-09-27_sub04.md): +0.000180 against +0.000149 predicted, so the 7B parts worked slightly better than expected.
- **Outcome:** Composite B is the best public score and the submission in the ZIP (D-PKG-10). The handovers do not say why the team moved from mixf2 to Composite B at about 20:55; the chat gives the reason above (hedge the unverified French 7B drop).
- **Hindsight:** The most consequential decision of the evening, and it came from the humans, not the estimator. A one-change probe from a measured baseline is the cleanest experiment a leaderboard allows.
- **Links:** [chat:ameya/19e315ba 2026-09-27 20:49] · [issue #64] · D-LLM-05 · D-LLM-09

### D-SUB-24 · After B: a one-change follow-up (mixf7) and "always upload the best expected model"
- **When (IST):** 2026-09-27 20:53–21:08 · **Phase:** P4/P5 · **Area:** SUB
- **Decided by:** agent for Ameya (mixf7); Ameya ("We always upload the best performin model now")
- **Status:** adopted
- **Problem:** With B measured, which change should the next slot test, and should a slot be spent on a high-variance gamble?
- **Options considered:** 1. mixf2 as planned (changes US and France). 2. mixf7 = B with only France swapped to round 3 (predicted about 0.99095). 3. mixf8 (France v7sqsyd), the probe with the highest upside (estimates −0.000124 to +0.000078 against mixf7).
- **Choice and why:** mixf7, because it changes one thing against a measured score. Ameya ruled out gambles, so mixf8 was dropped.
- **Evidence:** Predictions [E] [chat:ameya/19e315ba 2026-09-27 20:53] · [21:05] · [21:08].
- **Outcome:** mixf7 0.990833 and mixf2 0.990819 [M], both below B (both about 21:55, order approximate). The design made the two results readable: mixf7 − B = −0.000046 (round-3 France), and mixf2 − mixf7 = −0.000014 (US from v7sq3 instead of g1w, so g1w's US is worth +0.000014).
- **Hindsight:** mixf7 differs from B in two ways, the round-3 model and the missing French decision layer (D-FRA-24), so it did not isolate the model alone.
- **Links:** [LB 2026-09-27 #05](../../submissions/records/2026-09-27_sub05.md) · [LB 2026-09-27 #06](../../submissions/records/2026-09-27_sub06.md)

### D-SUB-25 · The last hours: no switch away from Composite B
- **When (IST):** 2026-09-27 22:06 → 23:53 · **Phase:** P5 · **Area:** SUB
- **Decided by:** Ameya and Bakshi for the uploads; the agent for Ameya and the France-diff sub-agent a2762d22 for the recommendation
- **Status:** adopted ("no switch" held)
- **Problem:** Three French candidates each nominally met the switch rule (+15e-6 with under 20% of changed pairs lacking a 7B score): mixfq (the round-3 model with B's French treatment), mixmdp05 and mixmdp08 (DP variants).
- **Options considered:** Switch to one of them; keep B; keep B and add 8 more 7B-rejected decoys (B+).
- **Choice and why:** Keep B. Estimates against B, in 1e-6 [E]: mixfq +20.0 (joint pc-times-7B range +14.8 to +28.7); mixmdp05 +51.7 (range −9.7 to +15.8); mixmdp08 +105.7 (range −37.7 to +29.8). The 7B calibration had been measured only on pairs above pc 0.7 (99.9% true), and at pc 0.7–0.8 a positive 7B score means only 81% true. The leaderboard had just shown the estimators 53–98e-6 too optimistic on this model family, which puts mixfq near −33 after correction (D-FRA-26).
- **Evidence:** [chat:ameya/agent-a2762d22 2026-09-27 22:31] · [RESEARCH_v6 §6.20](../../experiments/ameya/model-v1/RESEARCH_v6.md).
- **Outcome:** Composite B 0.990879 stayed the team's best [M]. B+ ("B plus 8 extra 7B drops") was recommended and never uploaded; the last slot went to Bakshi's B7 (D-SUB-26). The status file written at 23:55 still names B+ as "the final", while the ROADMAP names Composite B.
- **Hindsight:** The correct hold: no candidate was better than B on evidence that survived the bias correction.
- **Links:** [status ameya](../../docs/status/ameya.md) · [ROADMAP Phase 5](../../docs/ROADMAP.md)

### D-SUB-26 · The last slot: B+ or B7
- **When (IST):** 2026-09-27 22:09 → about 23:40 · **Phase:** P5 · **Area:** SUB / LLM
- **Decided by:** Ameya and Bakshi (the agent for Ameya recommended B+ at 23:22; Ameya wrote "final upload stays B+" at 22:32, and at 22:45 the plan was still to finish with B+; B7 went up last). Who made the final call is not recorded.
- **Status:** B7 uploaded, a tie. B+ never uploaded.
- **Problem:** Bakshi's reading: B's +0.00018 over mixmdp came mostly from its 840 French 7B drops, so those drops were nearly all false. Should the French drop go below −6? One slot was left.
- **Options considered:**
  1. Ameya's B+: B plus 8 more French decoys dropped by the same rule, from pairs the 7B had not scored (`a5b0e90f…`); expected about 0.99088.
  2. Bakshi's B+: restore 255 look-alike pairs that the swap drop removed and the 7B accepts (above 2), and drop 83 of mixmdp's 2,301 never-scored French pairs at below −6 (`09c45bff…`).
  3. Bakshi's ladder B3–B8 (`fr_drop_ladder.py`): extend drops to [−6, −4), then [−4, 0) where Qwen3-4B also rejects, then the remaining out-of-band [−4, −2). B7 is +251 / −1,699 French pairs against B.
- **Choice and why:** B7. A French drop pays off at about 18–25% false, and the 4B agrees with the 7B's rejections 2–15 times more often in France than in US/India at the same score, "the signature of decoys". The labelled in-band two-model step was only +8e-6 (halves −7e-6 and +24e-6). B+ was the agent's safe pick; Bakshi wanted to test whether the French drop keeps paying below −6.
- **Evidence:** B7 0.990875, −0.000004 against B [M] [LB 2026-09-27 #07](../../submissions/records/2026-09-27_sub07.md).
- **Outcome:** A tie: "the labelled −6 cut-off was already about right, and the '25× decoys' extrapolation into the −6…−2 bands overstated the French false rate." Composite B stayed the best; B7 is the last upload. The ZIP carries Composite B (D-PKG-10). Which of the two the private ranking used is unknown: the Unstop page said the private board is "based on your final solution submission", Bakshi's handover said best versus last "was reported both ways today", and no source says what the organisers did. The public scores differ by 0.000004. No private score exists, only the ranking (2nd of the Top 10).
- **Hindsight:** The tie became a control in the methodology: the labelled −6 cut-off was already right.
- **Links:** [fr_drop_ladder.py](../../experiments/bakshi/box/fr_drop_ladder.py) · [bplus_tsv.py](../../experiments/bakshi/box/bplus_tsv.py) · [FINAL_PUSH_RESULTS §8–9](../../experiments/bakshi/box/FINAL_PUSH_RESULTS.md) · [chat:ameya/19e315ba 2026-09-27 23:53] · D-LLM-10
