# Process and infrastructure (ORG): team, repo rules, machines, rented GPUs, failures

**Summary.** Three people built the solution in 40 hours with a rule set that made parallel work safe: one writer per coordination file, member branches, rebase-merge only, contracts for every artifact, and "code moves, data doesn't".
The plan was Ameya's Plan A with nine grafts from Sachi's Plan B; in practice most of the pipeline ran on one 24-core laptop, rented H100s carried the cross-encoders, and several failures (idle compute, a crashed laptop, spot boxes lost) shaped what we could try.
Names: Ameya (captain, coordinator, the only uploader), Sachi, Bakshi. "Agent for Ameya" means an AI agent working for him.

## 1. Purpose

Explain how the team organised itself, what rules kept three people and many AI sessions from colliding, what hardware ran what, and what went wrong.
This is the page for "how did you work" and "what would you do differently" questions.

## 2. How it works

### 2.1 People and roles ([`docs/TEAM.md`](../../docs/TEAM.md))

| member | roles | machine |
|---|---|---|
| Ameya | repo admin, coordinator, submissions captain (only uploader), blocking, pipeline, packaging, main model chain | the integration machine: RTX 5070 Ti 12 GB, 24 cores, 31 GB RAM; about 20 GB usable for a job [R] |
| Sachi | model, calibration, decision, gates and ablations, error analysis; later the Qwen2.5-1.5B code and synthetic French | MacBook Air M3, 8 GB, no CUDA; later a rented RTX 4090 |
| Bakshi | normalisation and lexicons, string features; from 26 Sep the audit, packaging, the 7B and Composite B | i5-12450H, RTX 2050 4 GB, 16 GB; later rented 2x RTX 4090 and 4x H100 boxes |

Credit by role: Ameya (main chain and decisions), Bakshi (7B, audit, package, Composite B), Sachi (Plan B's gates, the 1.5B code, diagnostics) (CF-52o in [conflicts](../conflicts.md)). Q&A leads per topic are in TEAM.md.

### 2.2 Repo rules ([AGENTS.md](../../AGENTS.md), [CONTRIBUTING.md](../../CONTRIBUTING.md))

- `main` is protected: PR required, CI checks "repo policy" and "unit tests", linear history, no force-push. Work goes on `<member>/<topic>` branches; merges are rebase-merge only (squash would add co-author lines); a human reviews and merges.
- One writer per coordination file: `docs/status/<member>.md`, one handover per session, one decision record per decision, one upload record per upload, `experiments/<member>/**`. Shared files change only through a dedicated, small PR.
- No attribution lines in commits or PRs, enforced in four places: a commit-message hook, a CI check, agent settings with attribution off, squash merges disabled. Conventional Commit subjects.
- Hygiene hooks: no commits on main, no data, no file over 5 MB, no secrets, no pushes to main. Data and large artifacts stay out of git (`work/` is git-ignored).
- Contracts C0 to C10 (D-ORG-05): tags `<member>-<stage>-v<N>`, artifacts at `work/<stage>/<tag>/<split>.parquet` with commit and command inside, integer eids, one holdout, calibrated scores, outputs only through `ber.io`, matches a subset of candidates, gate records.
- Hard competition rules: only the provided data; licences MIT or Apache-2.0 with at most 8B parameters; `country` an open set; only humans upload to the leaderboard and choose the final submission.

### 2.3 Day-1 workflow

Plans A (Ameya) and B (Sachi) were pitched, scored on a weighted rubric with hard gates and merged: Plan A as base, nine Plan B grafts (D-ORG-02, D-ORG-03). Tasks became nine GitHub issues (#5 to #13) with specs, contracts and due times so that a member's agent could pick them up (D-ORG-04). Dev artifacts were shared as private pre-releases (D-ORG-06): devkit-v0 179,797,164 bytes, devkit-v2 383,533,421 bytes [M]. Everyone developed on the dev sample (about 110k S1) and Ameya re-ran full-scale stages.

### 2.4 Compute

- Laptop: only about 20 GB usable, so heavy jobs run one at a time (D-ORG-07). Text work stays on the CPU; only XGBoost and the cross-encoders use the GPU (D-ORG-08).
- Rented GPUs: H100 80 GB boxes for e5-large, bge and later the 7B; the upload was limited to records and band pairs under a 30 GB traffic cap (D-ORG-15), stage 2 stayed on the laptop. Interruptible boxes were lost on 26 Sep, so the policy became one on-demand 80 GB GPU (D-ORG-17). Two RTX 5090 (32 GB) for the synthetic-French jobs; Bakshi's 2x RTX 4090 box (64 vCPU) rebuilt the pipeline and his 4x H100 box trained the 7B. Total spend is not recorded: only estimates exist (CF-12).
- Last evening: every idle GPU was used, including Bakshi's boxes, until 19:37 (D-ORG-24).

### 2.5 Coordination

- Issue #45 held a live status comment listing every running job; Bakshi was asked for status every 30 to 45 minutes while Ameya slept; only the captain uploads; merges only on Ameya's orders (D-ORG-18).
- Sub-agents (helper AI sessions) did analysis in their own scratch folders without git, memory-capped, and gains had to hold on two disjoint halves of the holdout (D-EVL-13).
- After the crash: a memory guard (at least 15 GB free before each stage 2), a `PAUSE` flag and one heavy job at a time (D-ORG-19). Artifact writes are atomic and chains resume from step markers, so nothing was lost.
- Packaging on 29 Sep: Bakshi wrote the driver, a fork wrote the France block, the agent for Ameya wrote the document and assembled the ZIP, always from `main` (D-ORG-25 to D-ORG-27).
- Knowledge capture for the finale: a script turns chat logs into redacted digests that agents extract from (D-ORG-29, [STANDARD](../STANDARD.md)).

## 3. Why this design

Decision records: [ORG](../decisions/ORG.md). D-ORG-01 one-writer files, branches, rebase-merge, hooks, no attribution lines. D-ORG-02 and D-ORG-03 base plan by rubric and gates, Plan A plus nine grafts. D-ORG-04 roles and "code moves, data doesn't" ("passing multi-GB feature files between three laptops at 21:00 is a bigger risk than any modelling choice"). D-ORG-05 contracts. D-ORG-06 private pre-releases. D-ORG-07 and D-ORG-08 serial heavy jobs, text on CPU. D-ORG-09 and D-ORG-10 point Bakshi at France and documentation; no AWS for slow features before testing their value. D-ORG-11 treat the window as closing at 21:00 IST. D-ORG-12 reaped jobs. D-ORG-13 competitors' public work: ideas only, no code. D-ORG-14 code freeze. D-ORG-15 to D-ORG-17 and D-ORG-20, D-ORG-22, D-ORG-24 rented GPUs. D-ORG-16 rebuild v7m's design locally as v7n. D-ORG-18 coordination. D-ORG-19 crash guards. D-ORG-21 handling a push to a PR branch. D-ORG-23 sub-agent pause. D-ORG-25 to D-ORG-27 packaging roles and merge order. D-ORG-28 finale emphasis (deferred). D-ORG-29 knowledge capture.

## 4. Alternatives and why not

- Pass features between laptops: rejected, too risky at the deadline. Cost: knowledge and artifacts concentrated on one machine, which blocked Bakshi twice on the last day.
- Squash-merge: adds co-author lines, so disabled.
- AWS for slow features: test their value first (D-ORG-10).
- Reusing competitors' code: forbidden by integrity rules and moot (nothing public to read) (D-ORG-13).
- Editing AGENTS.md for the deadline: a shared file, left alone (D-ORG-11); it still says 23:59.
- Restarting reaped jobs without asking: rejected after 4.7 hours idle (D-ORG-12).

## 5. Numbers

| fact | value | level | source |
|---|---|---|---|
| Unit tests | 24 (12:56) to 49 (16:25) to 96 (21:27) on 25 Sep; 115 in the ZIP | M | [numbers §9](../numbers.md) |
| Repo on 3 Oct | 229 commits on `main`, 14 remote branches, PRs up to #77 | M | [numbers §9](../numbers.md) |
| Uploads | 5 per day and 15 in all allowed; 13 scored uploads on record, 7 on 27 Sep | M | [numbers §6](../numbers.md) |
| Idle compute | about 4.7 h on 26 Sep (06:37 to 11:19) | M | D-ORG-12 |
| Data moved to rented boxes | about 7.8 GB, later about 23.7 GB against a 30 GB cap | R | D-ORG-15, D-ORG-17 |
| Memory peaks | stage 2 16.5 to 19 GB; decide 9.8 GB; acronym join 6.0 GB | M | D-ORG-19 |
| Plan rubric (coordinator's scores only) | Plan A 3.9, Plan B 3.1 | R | D-ORG-03 |

## 6. Failure modes and limits

Recorded plainly; the full list is in [failures.md](../failures.md).
- 26 Sep, 06:37 to 11:19: about 4.7 hours idle after background tasks were reaped and the agent waited for approval (D-ORG-12).
- 26 Sep evening: a spot box died and took v7m, the model with the best French AUC (0.878) (D-ORG-15); box 2 died at about 23:10; on-demand box 3 from 23:15 (D-ORG-17); v7n rebuilt locally (D-ORG-16).
- 27 Sep, about 03:35: the laptop froze under memory pressure and rebooted at 03:40; later an alias-rule test growing to 21.8 GB was killed to avoid a second freeze (D-ORG-19, D-BLK-15).
- Teammates' day-1 modules (normalise, string features, `ber.model`) never ran at full scale and were bypassed by the faster experiment chain (D-ORG-04, D-FEA-07). Teammates could not reproduce v6 and v7 locally (D-MDL-07).
- The deadline was read as 21:00 IST while AGENTS.md says 23:59; uploads were accepted at about 21:55 and 23:40 anyway (D-ORG-11, CF-04). The planned 15:00 code freeze was not held (D-ORG-14); the best submission (Composite B) went up at about 20:55.
- The plan's rubric was scored by its own author; the +0.002 gate bar proved too high for late gains (D-ORG-03 hindsight).
- No clean end-to-end rerun on the final day (D-PKG-07).

## 7. Scale

The process scaled to three people and many agent sessions because ownership was explicit. It would not scale to a larger team without a shared artifact store and CI that runs stages on the dev sample; the single integration machine was the bottleneck. At production scale the same contracts (tags, schemas, holdout hash, gate records) map onto a pipeline orchestrator, and the one-writer rule onto a registry of models and runs ([theory F17](../theory/foundations/F17-production-ml-and-mlops.md)) [E].

## 8. Theory links

[F17 Production ML and MLOps](../theory/foundations/F17-production-ml-and-mlops.md), [F08 Computing at scale](../theory/foundations/F08-computing-at-scale.md), [F09 Experiments and evidence](../theory/foundations/F09-experiments-and-evidence.md), [11 Scaling to billions](../theory/11-scaling-to-billions.md).

## 9. Likely questions

- **How did three people work in parallel?** Contracts first, one writer per file, branches and rebase-merge, issues with full specs, and a live status thread; see 2.2 and 2.5.
- **Why one laptop for most runs?** It was the only machine that fit the data (31 GB RAM, GPU); "code moves, data doesn't" avoided shipping multi-GB files. The price is in section 6.
- **What did the rented GPUs do?** Cross-encoders (e5-large, bge), the Qwen2.5-7B and the synthetic-French jobs; stage 2 stayed on the laptop.
- **What would you change?** Make long chains resumable and memory-aware from the start, upload a France probe on day 2, and keep artifacts in a shared store.
- **How much did it cost?** Unknown: only estimates exist (CF-12).
- More in [qa.md](../qa.md), [lessons.md](../lessons.md).
