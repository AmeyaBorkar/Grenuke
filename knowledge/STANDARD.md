# The knowledge standard

This page says how Grenuke records what it did: every decision, experiment, number and lesson, in one format, with a source for every claim.
It applies to people and to their AI agents. `AGENTS.md` §10 makes it binding for agents.

**Why we keep it.** The jury will ask why we chose each part, how we know it worked and what we would change. Every member must be able to answer for the whole pipeline, not just their own part. The deck, the Q&A sheet and the study guide all draw on this record, so their numbers stay consistent.

---

## 1. Two layers

| layer | where | who writes | IDs |
|---|---|---|---|
| **Contribution** | `knowledge/people/<member>/` | that member and their agents only | local (`B-D-07`, `S-X-03`) |
| **Curated** | every other file under `knowledge/` | the curator (Ameya, or an agent working for him), reviewed in a PR | global (`D-BLK-03`, `EXP-041`) |

- Contributions are the raw material. Capture what happened, in the formats below, from your chats, notes, scripts and memory (`knowledge/CAPTURE.md`).
- The curated layer merges all contributions and the repo's records into one consistent picture. Where sources disagree, the curator records both in `knowledge/conflicts.md` and keeps the discrepancy visible rather than picking one quietly.
- **Historical records are never rewritten:** `docs/handover/`, `docs/decisions/`, `submissions/records/`, `plans/`, PRs and issues. The knowledge base cites them.

---

## 2. Record types

Fill every field. Write `unknown` instead of guessing, and add the question to `open-questions.md` (contribution) or `knowledge/conflicts.md` (curated).

### 2.1 Decision: `D-<AREA>-<NN>`

One per choice that shaped the solution, including choices *not* to do something.

```markdown
### D-BLK-03 · Per-country blocking
- **When (IST):** 2026-09-25 15:40 · **Phase:** P1 · **Area:** BLK
- **Decided by:** Ameya (proposed by: agent for Ameya)
- **Status:** adopted | rejected | superseded by D-… | reverted | deferred
- **Problem:** what forced a choice.
- **Options considered:**
  1. option: what it is; evidence for and against
  2. …
- **Choice and why:** the reasoning at the time, in plain words.
- **Evidence:** numbers with level and source, e.g. "holdout pair recall 0.9752 → 0.9857 [M] [PR #18]".
- **Outcome:** what happened after; did it hold up?
- **Hindsight:** would we choose the same today, and what would we do differently?
- **Links:** sources · related decisions · component page · theory page
```

### 2.2 Experiment: `EXP-<NNN>`

One row per measured attempt, kept or not. Dead ends are as valuable as wins.

| field | content |
|---|---|
| ID, when, who, area | `EXP-041`, `2026-09-26 19:33`, Ameya, CE |
| hypothesis | what we expected and why |
| setup | tag / commit / data split / model / hardware |
| result | before → after, with scope: holdout all/US/India, public LB, AUC, recall, pairs per S1, runtime |
| verdict | kept · dropped · inconclusive · superseded |
| links | the decision it fed, and the source |

### 2.3 Timeline event

`| YYYY-MM-DD HH:MM | who | what happened | source |`. Times are IST. Include uploads, merges, runs started and finished, plan changes and turning points.

### 2.4 Number (fact sheet)

`| fact | value | scope | level | source |`. Scope says which split, country, model and version: "public LB, Composite B", or "local holdout, US/India, 549,699 S1, g1w".

### 2.5 Journal entry (`people/<member>/journal.md`)

One per working session, in time order: **when · goal · what was done · results (numbers) · decisions taken (→ IDs) · problems · next**.

### 2.6 Component page (`knowledge/components/`)

Fixed sections, in this order:
1. Purpose (two lines)
2. How it works: mechanics, parameters and file paths
3. Why this design: the decisions, by ID
4. Alternatives and why not
5. Numbers
6. Failure modes and limits
7. Scale: what happens at 100× or 1000× the data
8. Theory links
9. Likely questions

### 2.7 Theory page (`knowledge/theory/`)

Fixed sections:
1. Intuition
2. Formal definition (the maths)
3. Variants
4. Where we used it (links)
5. Why it fits this problem
6. Pitfalls
7. Jury questions with answers
8. Self-test, with answers in `<details>`
9. Further reading (classic sources)

### 2.8 Q&A entry (`knowledge/qa.md`)

**Question** → **say this** (at most three sentences, the way you would say it aloud) → **evidence** (numbers and links) → **likely follow-ups**.

### 2.9 Foundations page (`knowledge/theory/foundations/`)

These are theory pages written from scratch. They lead up to the advanced theory pages. Fixed sections:
1. Summary and "What you need first"
2. The concepts from zero, each with intuition, a definition and a worked example from our project
3. How it shows up in our project
4. How to read the numbers
5. Common misconceptions
6. Check yourself: exercises, with answers in `<details>`
7. Where next

---

## 3. Sources and evidence

**Every claim cites a source.** Use these forms:

| source | form |
|---|---|
| a repo file | a relative link, e.g. `[RESEARCH_v6 §6.13](../experiments/ameya/model-v1/RESEARCH_v6.md)` |
| a PR, issue or commit | `[PR #43]`, `[issue #45]`, `[commit 72a221f]` |
| a leaderboard upload | `[LB 2026-09-27 #04]`, which is the record in `submissions/records/` |
| an AI chat | `[chat:<member>/<first 8 chars of session id> YYYY-MM-DD HH:MM]`. The transcript stays on the member's machine; the reference lets them find it |
| a call, WhatsApp or in-person talk | `[call:<who> YYYY-MM-DD]`, `[whatsapp YYYY-MM-DD]` |
| a member's memory, written down later | `[memory:<member>]` (always level R) |

**Evidence levels.** Put the level next to every number.

| level | meaning | example |
|---|---|---|
| **M** measured | computed on labels, or scored by the leaderboard, with the tag or record | holdout F0.5 0.991323; public LB 0.990879 |
| **E** estimated | derived without labels, or inferred | "France ≈ 0.93", backed out of the LB formula |
| **R** reported | stated in a chat or doc and not re-checked | "the box took about 2 h" |
| **U** uncertain | sources conflict, or it is unverified; also list it in `conflicts.md` | |

**Naming the evaluation, always:**
- **local holdout:** the fixed 25% of labelled US/India S1 (549,699 S1). It has no France.
- **public LB:** the leaderboard during the challenge, on a subset of test.
- **private LB:** the final ranking, on the rest of test.
- Never write a bare "F0.5 = …".

---

## 4. IDs, areas and phases

**Area codes** are used in decision IDs and in every ledger.

| code | area |
|---|---|
| PRB | problem framing, data analysis |
| EVL | metric, holdout, gates, bootstrap, leaderboard probes |
| ORG | team, process, repo, compute, GPU boxes, tooling |
| NRM | normalisation, lexicons, transliteration |
| BLK | blocking and candidate generation |
| FEA | pair features |
| MDL | XGBoost stages 0–3, calibration, out-of-fold training |
| CE | cross-encoders (e5, bge, Qwen as a pair classifier) |
| DEC | the decision layer: expected-F0.5 set selection, thresholds, ownership |
| RUL | rules and post-processing (France rules, acronym join, stacked rules) |
| FRA | France: the unseen country, self-training, probes |
| LLM | the Qwen2.5-7B re-check of confident predictions |
| SUB | leaderboard strategy, final-model choice |
| PKG | packaging, reproducibility, the methodology document |

**Phases.** The curator may refine the boundaries; `knowledge/timeline.md` has the final ones.

| phase | when (IST) | what |
|---|---|---|
| P0 | 25 Sep 11:00–14:30 | kick-off, rules, competing plans, the final plan |
| P1 | 25 Sep 14:30–21:30 | v0 baseline, blocking v1, model v1, the first uploads |
| P2 | 25 Sep 21:30 → 26 Sep 11:00 | error analysis, the France gap, rules, candidate cut |
| P3 | 26 Sep 11:00 → 27 Sep 03:00 | v6all, stage 3, cross-encoders, France self-training |
| P4 | 27 Sep 03:00–21:00 | the final day: stack, Qwen 7B, composites, the final upload |
| P5 | 27 Sep 21:00 → 29 Sep 10:00 | the package, reproducibility, the methodology document |
| P6 | 3 Oct → 7 Oct | Grand Finale preparation |

- Experiments are numbered `EXP-001…` in time order across the whole project.
- In contributions, use local IDs: `<initial>-D-NN` and `<initial>-X-NN`, where the initial is A, B or S. The curator maps them to global IDs.

---

## 5. Style

- Plain English and short sentences. Explain each term the first time it appears on a page.
- Every page starts with a summary of two or three lines.
- Numbers carry their scope and unit. Times are IST.
- Bold the key words of a paragraph, sparingly. No italics.
- Say who did what: Ameya, Bakshi, Sachi, or "agent for Ameya". Credit ideas to whoever had them.
- Keep hindsight apart, under a **Hindsight:** label, so readers can tell what we knew then from what we know now.
- Record failures and reversals as plainly as successes.

---

## 6. Privacy and safety (hard rules)

- **Never commit** raw transcripts, chat exports or digests: `*.jsonl`, `work/kb_digest/`, ChatGPT or WhatsApp exports. They stay on your machine.
- **Redact** IP addresses, ports, hostnames of rented machines, SSH keys, tokens, e-mail addresses, phone numbers, personal paths, and anything personal or unrelated to the project.
- Short examples from the dataset are fine where the methodology already uses them. Never paste data rows in bulk.
- Do not invent facts. A plausible but unsourced claim is worse than "unknown".

---

## 7. Who does what

| step | who | where |
|---|---|---|
| capture your own sources | each member and their agents | `knowledge/people/<member>/`, by following `knowledge/CAPTURE.md` |
| merge, resolve conflicts, assign IDs | the curator | the curated files |
| keep the story, the deck and the Q&A consistent with the record | the curator, reviewed by all | `knowledge/story.md`, `knowledge/qa.md`, `finale/` |
| learn the theory and test each other | everyone | `knowledge/theory/` |
