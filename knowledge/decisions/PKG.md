# Decisions: PKG (packaging, reproducibility, the methodology document)

**Summary.**
- The package is the ZIP the organisers required by 29 Sep 10:00 IST: code that regenerates both output files from the raw data, the exact submitted outputs of Composite B, and a 7-page methodology document on their template. All rented GPU boxes had been destroyed by then, so no end-to-end rerun was possible.
- Our rules: verify the artifact, not the source it came from (a strict audit beyond the official validator, sha256 gates where a file's fingerprint must match before it is packaged, byte-for-byte equivalence tests for the ported stack of rules and decision layer); one variant-driven script instead of many; ship the exact uploaded TSVs; and never claim a bit-identical rerun, because GPU training moves results by about 0.0001.
- The document was written by an agent at Ameya's direction, with passes to remove overstatement ("don't overstate"). Five imprecisions survived into the submitted text; they are listed in D-PKG-20.

## Index

| ID | decision | when (IST) | status |
|---|---|---|---|
| D-PKG-01 | Port the real model into the package: v3 (not v2), threshold by default | 2026-09-25 22:55 | adopted |
| D-PKG-02 | Reproducibility fixes for Sachi's package, checked against provenance | 2026-09-26 11:28 | adopted |
| D-PKG-03 | Clean rerun on Ameya's machine in a separate work folder | 2026-09-26 23:25 | deferred (not done; see D-PKG-07) |
| D-PKG-04 | A strict output audit on top of the official validator | 2026-09-27 00:57 | adopted |
| D-PKG-05 | Hash-gate the package, never substitute a candidate file | 2026-09-27 01:00 | adopted |
| D-PKG-06 | Hold the final package; one variant-driven `reproduce.sh`; refuse unrecorded variants | 2026-09-27 01:56 | adopted |
| D-PKG-07 | No clean end-to-end rerun on the final day | 2026-09-27 03:08 | adopted (never run) |
| D-PKG-08 | Port the stack into the repo with a byte-for-byte equivalence test | 2026-09-27 04:27 | adopted |
| D-PKG-09 | No second reproduction script | 2026-09-27 09:08 | adopted |
| D-PKG-10 | The ZIP carries Composite B, not B7 or mixf2 | 2026-09-29 00:10 | adopted |
| D-PKG-11 | Ship the exact uploaded TSVs, through the team Drive | 2026-09-29 00:10 | adopted |
| D-PKG-12 | A runnable driver, "exact by construction"; the captain writes the document | 2026-09-29 00:31 | adopted |
| D-PKG-13 | Rescue the production drivers from the session scratchpad into git | 2026-09-29 01:05 | adopted |
| D-PKG-14 | Leave the intermediates and the 7B adapters out of the ZIP | 2026-09-29 01:23 | adopted |
| D-PKG-15 | One methodology document, on the template's headings | 2026-09-29 01:40 | adopted |
| D-PKG-16 | The agent writes the final text; 7 pages; layout and style | 2026-09-29 01:46 | adopted |
| D-PKG-17 | The package's France block reproduces mixmdp as it ran | 2026-09-29 01:54 | adopted |
| D-PKG-18 | How to claim reproducibility: no GPU rerun, "within about 0.0001" | 2026-09-29 02:05 | adopted |
| D-PKG-19 | Make the Solution Strategy the centrepiece, with its own diagram | 2026-09-29 03:15 | adopted |
| D-PKG-20 | "Don't overstate": accuracy passes, and what we chose to claim | 2026-09-29 03:26 | adopted; five imprecisions remain |
| D-PKG-21 | Curate the package and match the organisers' tree exactly | 2026-09-29 03:27 | adopted |
| D-PKG-22 | Accept the reviewer-agent's checklist and its four wording fixes | 2026-09-29 03:37 | adopted |

Related records: the choice of Composite B as the final model is D-SUB-23 and D-SUB-26; the rules and stack inside the package are in area RUL (D-RUL-11); the 7B parts are in area LLM.

## Records

### D-PKG-01 · Port the real model into the package: v3 (not v2), threshold by default
- **When (IST):** 2026-09-25 22:55 and 23:31 · **Phase:** P2 · **Area:** PKG / MDL
- **Decided by:** agent for Ameya (a message drafted for Ameya to send to Sachi)
- **Status:** adopted
- **Problem:** The real model lived only in `experiments/ameya/model-v1/`, and the ZIP needs `code/` that reproduces it.
- **Options considered:** not recorded beyond v2 against v3.
- **Choice and why:** Port v3, not v2, with the threshold as the default decision rule.
- **Evidence:** unknown (none recorded).
- **Outcome:** Sachi's [PR #27] ported v3: stage 2, legal-form features, cluster support, the all-candidate decision. Her [PR #30] added reproduce scripts, a README, requirements and a methodology draft; those scripts stop at v6 (D-PKG-06).
- **Hindsight:** unknown (none recorded).
- **Links:** [chat:ameya/19e315ba 2026-09-25 22:55] · [chat:ameya/19e315ba 2026-09-25 23:31]

### D-PKG-02 · Reproducibility fixes for Sachi's package, checked against provenance
- **When (IST):** 2026-09-26 11:28–11:32 · **Phase:** P3 · **Area:** PKG
- **Decided by:** agent for Ameya, answering Sachi (who owns the package)
- **Status:** adopted ([PR #29])
- **Problem:** Sachi's five questions: the blocking tag behind `fx4`; the cross-encoder `--s1` tag; whether `feats_lo.py` is needed for `lo0`; whether `feats_legal.py` needs `--group`; whether `decide.py --base` can be optional.
- **Options considered:** Answer from memory, or check each against the code and the artifacts' provenance metadata.
- **Choice and why:** Check provenance. It found a chicken-and-egg problem: blocking needs an Indic dictionary that `feats.py` learns. Fixes: `feats.py --dict-only` and an optional `decide.py --base`. Also found: main now has blocking v3 with ordinals always converted, so v2 cannot be rebuilt bit for bit on main (use commit 7568980 for the v5all fallback); and `fx4`'s cross-encoder had been copied from `fx3`.
- **Evidence:** [M] [chat:ameya/19e315ba 2026-09-26 11:28] · [chat:ameya/19e315ba 2026-09-26 11:32] · [RECIPE](../../experiments/ameya/model-v1/RECIPE.md).
- **Outcome:** Sachi's reproduce scripts reached main by 14:25 ([commit 161dad9]).
- **Hindsight:** Answers checked against provenance, not memory, caught two real reproducibility gaps.
- **Links:** [PR #29]

### D-PKG-03 · Clean rerun on Ameya's machine in a separate work folder
- **When (IST):** 2026-09-26 23:25–23:35 · **Phase:** P3 · **Area:** PKG
- **Decided by:** agent for Ameya (recommendation), after Bakshi flagged the risk
- **Status:** deferred. A repo stack test ran at 08:21–08:25 on 27 Sep; a full raw-TSV rerun is not recorded (see D-PKG-07).
- **Problem:** "A full clean rerun from the raw TSVs is not achievable on this 15.6 GB GPU-less laptop" (Bakshi).
- **Options considered:** Run it on Ameya's machine, where the whole pipeline took about 3 h; do not.
- **Choice and why:** Run it there, in a separate work folder so the packaged artifacts are not overwritten, starting overnight (298 GB free disk).
- **Evidence:** unknown (none recorded).
- **Outcome:** Unknown in the sources; no end-to-end rerun is recorded anywhere (D-PKG-07, D-PKG-18).
- **Hindsight:** unknown (none recorded).
- **Links:** [chat:ameya/19e315ba 2026-09-26 23:25]

### D-PKG-04 · A strict output audit on top of the official validator
- **When (IST):** 2026-09-27 00:57–01:11 (Bakshi); adopted on Ameya's side 01:50; run 05:15–08:21 · **Phase:** P3–P4 · **Area:** PKG / EVL
- **Decided by:** Bakshi (agent: Claude Code); the agent for Ameya adopted it for every package
- **Status:** adopted (run on every candidate package; part of the ZIP as `src/model_v1/audit_matching.py`)
- **Problem:** "`PASS` is not a sufficient check". The official validator treats a missing candidate file and matches outside the candidate set as warnings and still prints PASS, and it never checks owner uniqueness or country consistency.
- **Options considered:** Trust the validator, or audit independently.
- **Choice and why:** `audit_matching.py` exits non-zero unless the header is right, there is one row per test S1 with no repeated IDs, every target exists, no record has two owners, no pair crosses countries, and the matches are a subset of the candidates.
- **Evidence** [M]:
  - The submitted v7nst file: 1,732,544 rows, 5,856,096 pairs, 0 owner conflicts, 0 cross-country pairs, 0 unknown targets.
  - Against the v6all candidate file, 3,790 matches over 3,725 S1 were outside it: exactly the acronym join's additions. The control, v6all's own pair, had 0 outside. The predicted 6,410,247 candidate pairs were confirmed when the real file arrived.
- **Outcome:** 12 of 12 overnight candidate audits passed (the first run was paused at 01:40 for memory; v7s-dpc passed at 05:15). Bakshi's own audit of v7nst-dpc: 5,853,049 pairs, 0 outside the unchanged 6,410,247-pair candidate set. The audit ships in the ZIP.
- **Hindsight:** The audit caught the real gap that the validator only warned about (D-RUL-06).
- **Links:** [audit_matching.py](../../experiments/bakshi/final-package/audit_matching.py) · [handover 2026-09-27_0111](../../docs/handover/2026-09-27_0111_bakshi_final-package.md) · [PR #50] · [status bakshi @7bb4d46](../../docs/status/bakshi.md) · [chat:ameya/19e315ba 2026-09-27 10:53]

### D-PKG-05 · Hash-gate the package, never substitute a candidate file
- **When (IST):** 2026-09-27 01:00 → 09:29 → 11:47 · **Phase:** P3–P4 · **Area:** PKG
- **Decided by:** Bakshi
- **Status:** adopted
- **Problem:** Packages are built from files that arrive by hand-off under time pressure; a wrong pairing or a missing source file is invisible to the usual checks.
- **Options considered:**
  1. Build from whatever candidate file is at hand (v6all's for v7nst, v7nst's for v7sq-dpc). Rejected: 3,790 and 69 matches would fall outside, and adding them would be "manufacturing a candidate list".
  2. Refuse to build unless both TSVs match pre-registered sha256 hashes (chosen).
- **Choice and why:** Option 2. `make_package.py` also scans for credentials, writes a deterministic zip, then re-extracts it and re-hashes every member. "Subset-consistency is necessary but not sufficient; only the hash identifies a package." After a `*token*` filename glob silently dropped `ber/features/tokens.py` from every ZIP (missed because `compileall` never resolves imports and the tests ran against the repo), the builder also imports every `ber` submodule and runs the shipped tests from the extracted archive as hard gates.
- **Evidence:** Five broken hashes withdrawn (`d2e62fb9`, `bad61fee`, `c241b788`, `f933f7df`, `4bd6c7a1`); the fixed build `d9eb4388…` imports 34 of 34 submodules and passes 115 tests [M]. The v7sq-dpc candidate file arrived named `candidate_pairs_7nst_dpc.tsv`; its hash (`55b766ef…`) showed it belonged to v7sq-dpc [M].
- **Outcome:** The final ZIP was built by the same `make_package.py` (Composite B hashes `df4bccd7…` and `58c824a3…`) and was byte-identical when Bakshi rebuilt it.
- **Hindsight:** "Verify the artifact, not the source it came from" is the most transferable engineering lesson in these sources.
- **Links:** [make_package.py](../../experiments/bakshi/final-package/make_package.py) · [DELIVERABLES](../../experiments/bakshi/final-package/DELIVERABLES.md) · [commit 4981ca5] · [commit 4263e33]

### D-PKG-06 · Hold the final package; one variant-driven `reproduce.sh`; refuse unrecorded variants
- **When (IST):** 2026-09-27 01:56 → 02:57 → 09:07 (precondition check 11:09) · **Phase:** P3–P4 · **Area:** PKG
- **Decided by:** Ameya (hold until the model is chosen); Bakshi (script design)
- **Status:** adopted
- **Problem:** The final model could be any of v7nst, v7s, v7sq or an ensemble, each with a different cross-encoder set and pseudo-label teacher, and the merged `docs/package/` scripts (Sachi, [PR #30]) stopped at v6.
- **Options considered:** 1. One script per model (rejected: "two scripts covering overlapping chains is how they drift apart"). 2. One script switched by `VARIANT` (chosen). 3. Guess the tags of variants never written down (rejected).
- **Choice and why:** The family reduces to two choices, the cross-encoder mix and the teacher. `reproduce.sh` covers eight variants, builds the teacher before the student (cached pseudo-labels may not be an undeclared input), and from 09:07 runs the stack (`STACK=1` by default). v7sb and v7ensall2 exit with code 4 naming the missing tag, because "a wrong tag would silently reproduce a different model than the one shipped". Round-2 teachers are recognised as stacked (`-dpc` final tag) with a hard precondition check.
- **Evidence:** Every dispatch path exercised with `bash -n`, and flags cross-checked against each script's argument parser [M, statically]. Ameya verified the pseudo-label join: 385,274 of 385,274 pairs, 0 disagreements.
- **Outcome:** The same switch later handed off to `compositeB.sh` (`VARIANT=compositeB`, the default) for the final ZIP (D-PKG-12).
- **Hindsight:** The reproduction was never executed end to end (D-PKG-07).
- **Links:** [reproduce.sh](../../experiments/bakshi/final-package/reproduce.sh) · [PR #50] · [PR #56] · [commit c696a3d] · [commit 9dac574] · [commit afbaf37]

### D-PKG-07 · No clean end-to-end rerun on the final day
- **When (IST):** 2026-09-27 03:08 · **Phase:** P4 · **Area:** PKG
- **Decided by:** Bakshi (recommendation, recorded as "not done")
- **Status:** adopted as a recommendation; never run
- **Problem:** `reproduce.sh` had never been executed end to end.
- **Options considered:** Run it on the integration machine plus an H100 into a fresh work folder (6–7 h), or skip it.
- **Choice and why:** Skip. It would compete for the same GPU and RAM as the remaining variants on a deadline day, and GPU non-determinism means the hashes would not match anyway. Bakshi's laptop could not run it: no torch, a 4 GB GPU, 16 GB RAM against stage peaks of 18–19 GB.
- **Evidence:** [R] [DELIVERABLES §4](../../experiments/bakshi/final-package/DELIVERABLES.md).
- **Outcome:** The final README states that a rerun lands within about ±0.0001, not byte-identical. The reference checks are holdout reports, `q7st`'s AUC and the drop counts (D-PKG-18).
- **Hindsight:** The static checks were as far as the hardware and the time allowed.
- **Links:** [PACKAGE_README](../../experiments/bakshi/final-package/PACKAGE_README.md) · D-PKG-03

### D-PKG-08 · Port the stack into the repo with a byte-for-byte equivalence test
- **When (IST):** 2026-09-27 04:27–09:33 (port), 11:34–11:41 (reproducible-winner preference) · **Phase:** P4 · **Area:** PKG
- **Decided by:** agent for Ameya; Bakshi reviewed (as package owner, his `reproduce.sh` refuses undocumented recipes)
- **Status:** adopted ([PR #58] ready for review, CI green; the merge awaited Ameya at 10:58)
- **Problem:** A `-dpc` final must ship its stacking scripts, because the organisers re-run the top teams' code. The scratchpad scripts wrote to scratch folders and hard-coded countries, and the shipped `-dpc` packages came from them (metadata commit 93497df). v7sq4, v7sb and v7ensall2 had undocumented feature-group or bag tags.
- **Options considered:** Keep the scratchpad scripts; port them with an equivalence test.
- **Choice and why:** Port.
  - Copy the 10 scripts to `experiments/ameya/model-v1/stack/` with only path changes; outputs go to `$STACK_OUT` (default `work/stack`).
  - Read the labelled countries from the train records (country is an open set; no France, US or India literals in the model path).
  - `import_tag.py` checks one owner per record and matches inside the candidates at every layer (`-h2`, `-h2pc`, `-dpc`).
  - Test under a `-rt` tag suffix so built tags are not overwritten.
  - On Bakshi's review, replace `assert` with explicit exits so `python -O` cannot strip the guards.
  - Prefer v7sq-family winners, or record exact recipes (v7sq4: `cmq4` = z-mean of out_e5l, out_qst, out_e5ls, out_e5ls2, out_bges; v7qbag = bag of s2-v7sq, s2-v7sq2, s2-v7sq3).
- **Evidence:** PORT OK: every layer (hunted, h2, h2pc, combo, dpc) identical set for set, `-dpc` 5,852,482 pairs; 115 tests pass [M]. Negative test: two S1 claiming one record gives "a record is predicted for two S1", exit 1, no tag written. Bakshi's dry-run bundle with `stack/` (117 members) imported every module and passed the shipped tests from inside the archive; his `make_package.py --stacked` hard-fails if `stack/` is missing.
- **Outcome:** The stack is in the ZIP (D-RUL-11).
- **Hindsight:** Reproducibility mattered because the organisers re-run the top teams' code.
- **Links:** [PR #58] · [chat:ameya/19e315ba 2026-09-27 08:25] · [chat:ameya/19e315ba 2026-09-27 09:32] · [chat:ameya/19e315ba 2026-09-27 09:38]

### D-PKG-09 · No second reproduction script
- **When (IST):** 2026-09-27 09:08–09:11 · **Phase:** P4 · **Area:** PKG / ORG
- **Decided by:** Bakshi asked; Ameya dropped the file
- **Status:** adopted
- **Problem:** Sachi pushed `reproduce_v7sq.sh` (built like `reproduce_v7nst.sh`) to Ameya's `ameya/final-stack` branch, under `experiments/bakshi/`, which is Bakshi's one-writer path.
- **Options considered:** Keep both scripts, or fold v7sq into the variant switch (chosen).
- **Choice and why:** A second script over overlapping chains "re-creates the drift risk I deleted `reproduce_v7nst.sh` to avoid". Bakshi took the `-dpc` write-tag detail and the pre-stack report caveat from Sachi's script.
- **Evidence:** none beyond the discussion.
- **Outcome:** Dropped in commit 0972fd3; Sachi's version stays in history at 99a404d.
- **Hindsight:** unknown (none recorded).
- **Links:** [PR #58 comments] · [issue #45]

### D-PKG-10 · The ZIP carries Composite B, not B7 or mixf2
- **When (IST):** 2026-09-29 00:10–00:30 · **Phase:** P5 · **Area:** PKG / SUB
- **Decided by:** Ameya (proposed by: agent for Ameya, accepted by the team on issue #66); Bakshi had pointed out on 27 Sep at 23:45 that the guidelines want artefacts for the best submitted solution
- **Status:** adopted
- **Problem:** The organisers want the code and outputs "for the best submission". Which upload must the ZIP reproduce?
- **Options considered:** Composite B (0.990879, the best); B7 (0.990875, the last upload); mixf2 (the agreed upload, 0.990819).
- **Choice and why:** Composite B. It is the best score. B7 only ties it, and "needs the Qwen3-4B step, so it is harder to reproduce for no gain".
- **Evidence:** Public LB scores [M] ([LB 2026-09-27 #04](../../submissions/records/2026-09-27_sub04.md), [#07](../../submissions/records/2026-09-27_sub07.md)).
- **Outcome:** The ZIP's `output/` holds Composite B: matching `df4bccd7…`, candidates `58c824a3…`.
- **Hindsight:** This choice does not settle which upload the private ranking used (D-SUB-26).
- **Links:** [issue #66] · [issue #64, comment 23:45] · [chat:ameya/19e315ba 2026-09-29 00:10]

### D-PKG-11 · Ship the exact uploaded TSVs, through the team Drive
- **When (IST):** 2026-09-29 00:10–01:18 (Drive route chosen 00:31) · **Phase:** P5 · **Area:** PKG
- **Decided by:** agent for Ameya (Drive instead of git: Ameya, 00:31)
- **Status:** adopted
- **Problem:** The outputs must be identical to the upload. The agent's local rebuild matched the matching file byte for byte, but its candidate file differed (`b55c2b1d…` against `58c824a3…`), because Bakshi had merged the candidate sets per country. Git may not hold TSVs or files over 5 MB.
- **Options considered:** 1. Ship the local rebuild. 2. Ship Bakshi's uploaded pair, moved through the Drive.
- **Choice and why:** Option 2. Bakshi put the pair on the team Drive with a SHA256 list. The agent downloaded it, checked both hashes and ran the validator: PASS, 5,851,832 matches, 6,410,308 candidates, 3.70 per S1 [M]. Ameya's own download of Bakshi's Drive zips matched too.
- **Evidence:** Hashes `df4bccd7…` and `58c824a3…` [M] [chat:ameya/19e315ba 2026-09-29 01:18] · [01:20] · [01:22].
- **Outcome:** Both files are in the ZIP verbatim, and every build gates on these hashes.
- **Hindsight:** Without the per-country candidate-merge detail the ZIP would have shipped a candidate file that was never uploaded.
- **Links:** D-SUB-16

### D-PKG-12 · A runnable driver, "exact by construction"; the captain writes the document
- **When (IST):** 2026-09-29 00:31 → 02:48 · **Phase:** P5 · **Area:** PKG / ORG
- **Decided by:** Ameya (captain)
- **Status:** adopted
- **Problem:** By 10:00 IST on 29 Sep the organisers needed one ZIP that regenerates both outputs from the raw data, with all GPU boxes already destroyed.
- **Options considered:**
  1. Members fill the template.
  2. The captain writes the document, and members put exact code and facts on git (chosen at 00:36).
  3. `REPRO_compositeB.sh` as a record that starts with `exit 0`.
  4. A runnable driver, "exact by construction: the same scripts and arguments that ran" (chosen, issue #71 B).
- **Choice and why:** Options 2 and 4. Bakshi wrote `compositeB.sh` with four listed deviations, all forced by running in one package instead of three machines: its own band, no remap; v7sq's chain plays g0; `compose_tsv.py` takes `g1w-dpc` directly; `export_usin.py` takes arguments and reads labelled countries from train. When `pip install -r requirements.txt` failed (`ResolutionImpossible`: transformers 5.17.0 needs tokenizers 0.23.1 or later and safetensors 0.8.0 or later) and [issue #72] had no reply at 02:41, Ameya made the fixes himself in [PR #74], "with the captain's approval because the ZIP is due at 10:00", asking Bakshi not to force-push.
- **Evidence:** `make_package.py --variant compositeB --audit`: PACKAGE OK, 156 files, 115 shipped tests pass, validator and audit PASS [M]. `pip install --dry-run` resolves with tokenizers 0.23.2 and safetensors 0.8.0 [M].
- **Outcome:** The final ZIP, after the later curation (D-PKG-21), has 146 files and 88,353,040 bytes, with outputs unchanged (`df4bccd7…` and `58c824a3…`) [R].
- **Hindsight:** unknown (none recorded).
- **Links:** [issue #66] · [issue #71] · [PR #70] · [PR #72] · [PR #74] · [compositeB.sh](../../experiments/bakshi/box/compositeB.sh)

### D-PKG-13 · Rescue the production drivers from the session scratchpad into git
- **When (IST):** 2026-09-29 00:10 (flagged), 01:05–01:08 (done), consolidation to 03:30 · **Phase:** P5 · **Area:** PKG
- **Decided by:** agent for Ameya; Ameya (consolidation for the ZIP, [issue #66])
- **Status:** adopted
- **Problem:** The drivers run on the last day lived only in the agent's temporary scratchpad, including `s2w.py` (the weighted stage 2 behind B's France), `run_local_full(_w).sh`, `stack_model.sh`, `stack_pkg.sh`, `package6.sh` and `env6.sh`. The folder could vanish with the session. Some of them differed from the repo copies.
- **Options considered:** Leave them, or commit everything as run, excluding secrets.
- **Choice and why:** Commit as run: 134 files under `experiments/ameya/model-v1/pipeline/` (the exact drivers, label builders, `asrun/` with the versions that ran, and `box_runs/` with the GPU-box launch scripts, the 7B re-check tools and the detector experiments). Three box-setup scripts were left out because they contained key material for box access. For the ZIP, the needed parts were consolidated into `code/business_entity_resolution/src`: Composite B's France block is the v7sq7wg chain (`france_mixmdp.sh`, called by `src/box/compositeB.sh` step 7), and its US/India part and the 7B re-check come from Bakshi's `experiments/bakshi/box/`. RECIPE was edited for "accurate claims in the documentation" ([commit c426861]).
- **Evidence:** [commit 1472c48] · [pipeline README](../../experiments/ameya/model-v1/pipeline/README.md).
- **Outcome:** The ZIP shipped only the two pipeline scripts the driver needs (`france_mixmdp.sh`, `s2w.py`); the rest stays in git as a record. v2 candidates cannot be rebuilt bit for bit with current main (the repairs are on by default), so the v5all recipe pins commit 7568980.
- **Hindsight:** Essential: `s2w.py` existed nowhere else.
- **Links:** [chat:ameya/19e315ba 2026-09-29 01:06] · [chat:ameya/19e315ba 2026-09-29 01:08] · D-PKG-17

### D-PKG-14 · Leave the intermediates and the 7B adapters out of the ZIP
- **When (IST):** 2026-09-29 01:23 · **Phase:** P5 · **Area:** PKG
- **Decided by:** agent for Ameya (recommendation); Bakshi had argued for an optional `artifacts/` folder
- **Status:** adopted (the final ZIP has neither)
- **Problem:** Without the cross-encoder logits and pseudo-labels (about 150 MB), reviewers need about 10 GPU-hours on H100s before any CPU stage can run (Bakshi). The three 7B adapters are 485 MB.
- **Options considered:** 1. Ship them as an optional folder with its own SHA256 list. 2. Leave them out; they stay on the team Drive.
- **Choice and why:** Option 2. The ZIP only has to rebuild the outputs from the raw data, and the size limit was unknown.
- **Evidence:** none beyond the discussion.
- **Outcome:** A ZIP of 88.4 MB.
- **Hindsight:** It fits the later decision to match the organisers' tree exactly (D-PKG-21).
- **Links:** [issue #71] · [chat:ameya/19e315ba 2026-09-29 01:23] · [01:32]

### D-PKG-15 · One methodology document, on the template's headings
- **When (IST):** 2026-09-29 01:40–01:52 · **Phase:** P5 · **Area:** PKG
- **Decided by:** Ameya, on the agent's recommendation
- **Status:** adopted
- **Problem:** Should the four requested items (methodology; blocking; model and features; other information) be four files or one?
- **Options considered:** 1. Four files. 2. One document with the template's headings.
- **Choice and why:** One document. The four items are word for word the four bullets of the challenge README, which asks for the one filled template. One document gives one version of the truth for the 10:00 submission and the ZIP. Our decisions cross sections (the candidate cut chosen by final F0.5, the band defined by stage 1). Judges might open only one of four files. Ameya then set the tone: "just a line a submission of before helped us notice", and "the why is should be there but not overshadow the main".
- **Evidence:** The README: "There is no page limit — prioritise clarity and technical depth over brevity" [chat:ameya/19e315ba 2026-09-29 01:43].
- **Outcome:** The final document keeps the template's headings and field labels (for example "Blocking keys used:") verbatim, with a contents index that maps the four items.
- **Hindsight:** unknown (none recorded).
- **Links:** [methodology](../../experiments/ameya/final-zip/doc/Documentation_template.md) · [chat:ameya/19e315ba 2026-09-29 01:44] · [01:52]

### D-PKG-16 · The agent writes the final text; 7 pages; layout and style
- **When (IST):** 2026-09-29 01:46–03:24 · **Phase:** P5 · **Area:** PKG
- **Decided by:** Ameya (each style rule below is his request), carried out by the agent for Ameya
- **Status:** adopted
- **Problem:** The judges must actually read the document, and "just eyeing" it should be enough.
- **Options considered:** 1. The agent drafts and the team hand-types it in its own words (Ameya's first idea, 00:34). 2. The agent writes the final text and the team reviews (Ameya, 01:48: "we won't hand type it").
- **Choice and why:** Option 2, then a sequence of Ameya's requirements: 01:48 not too long, "we want the best document"; 02:10 bigger font, diagrams only if needed, an index; 02:28 less detailed horizontal diagrams, "slightly like a research paper", 6–8 pages, grouping, highlighted keywords; about 02:51 "the document look AI genarated", more space between paragraphs; 02:57 "7 pages it is. Also times new roman font"; 03:10 bold the important words, size labels so levels differ; 03:23 no italics.
- **Evidence:** The agent's research behind the layout: scanning patterns (layer-cake and F-pattern), the assertion-evidence heading style (Michael Alley), Amazon's narrative memos, Kaggle write-ups, a 45–75 character line length, proximity grouping, and Wikipedia's "Signs of AI writing" (heavy bold, bold-headed bullet lists, summary lead lines, rule-of-three rhythm) [chat:ameya/19e315ba 2026-09-29 01:44] · [02:30] · [03:03].
- **Outcome:** A4, Times New Roman 11.5 pt justified, about 80 characters per line. Size steps: title 18, section 15, sub-section 13, colon labels 12.5, run-in heads 12 bold, body 11.5, tables 10 pt. Two to five bold key terms per paragraph; prose paragraphs, bullets only for real lists; no "At a glance" box, no italic lead lines, no colour highlights; numbered captions; a contents list on page 1. The page count went 12 → 10 → 8 → 10 → 8 → 7.
- **Hindsight:** The "looks AI-generated" feedback led to a plainer and more credible document.
- **Links:** `experiments/ameya/final-zip/doc/` ([build_pdf.py](../../experiments/ameya/final-zip/doc/build_pdf.py), [make_figures.py](../../experiments/ameya/final-zip/doc/make_figures.py)) · [chat:ameya/19e315ba 2026-09-29 02:19] · [03:24]

### D-PKG-17 · The package's France block reproduces mixmdp as it ran
- **When (IST):** 2026-09-29 01:54 → 02:11 · **Phase:** P5 · **Area:** PKG / FRA
- **Decided by:** agent for Ameya (written by the fork a0889d36)
- **Status:** adopted ([commit 5811460] on `ameya/final-zip`)
- **Problem:** Bakshi's Composite B driver ([PR #72], `compositeB.sh` step 7) calls `france_mixmdp.sh`, which did not exist yet.
- **Options considered:** Write the France chain afresh, or reuse the tags the driver's step 1 builds and the scripts that ran.
- **Choice and why:** Reuse, and skip finished steps. F1 trains e5ls2, bges and e5fr; F2 builds `cmq7` (z-mean of qst, e5ls, e5ls2, bges, e5fr); F3–F5 build the guarded round-2 labels; F6 runs stage 2 at pseudo-weight 3; F7 runs the laptop chain (decide, stage 3, decide, post_ops, acronym join); F8 the stack; F9 the look-alike drop and `dp_france.py`; F10 writes the TSVs. Deviations are limited to path translation, the package's own band, committed script names replacing scratch ones, and F9 run directly on v7sq7wg-dpc.
- **Evidence:** The last two steps reproduce mixmdp's French rows exactly: 871,147 pairs, 0 differ either way [M]. Uncertain: the bges seed (26) is inferred, and the box's `ce_box.py` cannot be byte-checked [U] [chat:ameya/agent-a0889d36 2026-09-29 02:11].
- **Outcome:** Shipped in the package. Nothing was rerun end to end (no GPUs).
- **Hindsight:** unknown (none recorded).
- **Links:** D-FRA-18 · D-FRA-20

### D-PKG-18 · How to claim reproducibility: no GPU rerun, "within about 0.0001", not bit-identical
- **When (IST):** 2026-09-29 00:10 (raised), 02:05 (decided) · **Phase:** P5 · **Area:** PKG
- **Decided by:** agent for Ameya; Ameya agreed ("Do you need 1 H100 to reproduce or anything ?" → no)
- **Status:** adopted
- **Problem:** Composite B is the end of a long GPU chain: two rounds of French self-training, about ten cross-encoders, and the 7B. All GPU boxes were destroyed by 01:05 on 29 Sep, and GPU training is not bit-exact across machines.
- **Options considered:**
  1. Rent an H100 and rerun before 10:00. Impossible: the 7B alone takes about 2 h on three H100s or 6 h on one, the re-check about 4 GPU-hours, eight more cross-encoders, then hours of CPU stages, and the result still would not be byte-identical.
  2. A development-sample smoke test. Impossible: the driver and most stage scripts have no small-sample mode.
  3. Static and partial checks plus an honest tolerance statement.
- **Choice and why:** Option 3. Every script the drivers call is in the package, and each artifact a step reads is written by an earlier step; `bash -n`, compile all Python, 115 unit tests, and the validator and strict audit on the shipped files; the last step is already proven, because the local recomposition of B was byte-identical. The documentation and README say that a rerun is not byte-identical and should land within about ±0.0001.
- **Evidence:** The README names the sources of non-determinism: XGBoost with fixed seeds is deterministic on one machine; the cross-encoders are not bit-reproducible across GPUs (TF32, cuDNN kernel choice, non-deterministic reductions); stage 3 moves about 500 decisions between machines [R] ([PACKAGE_README](../../experiments/bakshi/final-package/PACKAGE_README.md)). Bakshi's rebuild of v7sq on other hardware moved the holdout from 0.991246 to 0.991261 [M] [chat:ameya/19e315ba 2026-09-27 18:13].
- **Outcome:** Stated in Appendix A of the methodology.
- **Hindsight:** The honest tolerance statement is defensible in front of a jury; a "byte-identical" claim would not have been.
- **Links:** [chat:ameya/19e315ba 2026-09-29 02:05] · D-PKG-07

### D-PKG-19 · Make the Solution Strategy the centrepiece, with its own diagram
- **When (IST):** 2026-09-29 03:15–03:21 · **Phase:** P5 · **Area:** PKG
- **Decided by:** Ameya ("give more weight on the Solution strategy because it is the most important bit... a small diagram... high level")
- **Status:** adopted
- **Problem:** The strategy was a short subsection.
- **Options considered:** not recorded.
- **Choice and why:** Section 2.2 now holds Figure 2 (four rows: what makes it hard, what we did, the measured gain), two principles ("spend effort where the uncertainty is"; "decide the way the metric scores"), the three core innovations, "Why not a simpler design" with numbers, and "How we decided what to keep". The leaderboard chart became Figure 3, and the appendix ablation table was folded into one sentence to stay at 7 pages.
- **Evidence:** Figure 2's gains: cascade +0.0011 on the public LB; set selection +0.000048 on the local holdout; self-training +0.00046 and +0.00015 on the public LB; the 7B re-check about +0.00011 on the public LB (an estimate) [M]/[E] [chat:ameya/19e315ba 2026-09-29 03:21].
- **Outcome:** See D-PKG-20 for the corrections to these gains.
- **Hindsight:** The "why not simpler" paragraph pre-empts the obvious jury question about running the 7B on everything.
- **Links:** [methodology §2.2](../../experiments/ameya/final-zip/doc/Documentation_template.md) · D-PKG-20

### D-PKG-20 · "Don't overstate": accuracy passes, and what we chose to claim
- **When (IST):** 2026-09-29 00:38–04:03 (Ameya's instruction at 03:26) · **Phase:** P5 · **Area:** PKG
- **Decided by:** Ameya ("don't overstate something which is not asked or needed which would make us view poorly"); fixes by the agent for Ameya and by Bakshi
- **Status:** adopted. Five imprecisions remain in the submitted text (below).
- **Problem:** The drafts contained claims stronger than the evidence.
- **Options considered:** not recorded.
- **Choice and why:** Each fix makes a claim match what was tested.
  - 00:38–01:04: round 3 reframed (it lacked the France decision layer and the look-alike treatment); per-country blocking and the feature list verified in code; "acronym agreement" removed from the features, because it is a rule.
  - 01:15–01:22: the stage-2 pseudo-label weight is 3 for France but 1 for US/India; e5-small learning rate 5e-5; −6 is the cut-off with the largest gain, not "the loosest that gains in both halves" (−5 also gains in both halves); the +48e-6 [+7, +91] bootstrap replaced a tuned threshold together with the acronym join and caps; the re-check needs about 4 GPU-hours, not 4.5; "25×" became "0.10% against 0.004–0.007%".
  - 01:57–02:00: F0.5 "weights precision twice as much as recall" (the README's wording), not "four times"; the first leaderboard row already had stage 2; e5-base, the first French teacher, added to the model list; the "phantom" setting and the France DP described correctly.
  - 02:37: "99.99%" became "> 99.9%" in one place (the shipped section 4 still says 99.99% for the exact-address copy rule, which the measured 99.992% and 99.998% support).
  - 03:28: three overstatements removed: a paired bootstrap was used for the main decisions, not for every gain; late rules such as the 7B cut-off were checked on both halves of the holdout; running the 7B on everything was ruled out by a compute estimate, not by measurement. One plain compliance sentence added; the note about encoders that failed to train removed as not needed.
  - 04:03, from Bakshi's review: "String features cannot tell the decoys apart" was overstated (they do on US/India; France failed because the names are generic); one sentence mixed the whole holdout (+0.000037) with the 34% sample (+0.000033); the 7B "runs on three 80 GB GPUs in about two hours (about six on one)"; the US gain marked "(P 0.906, not significant)".
- **Evidence:** [chat:ameya/19e315ba 2026-09-29 03:26] · [03:38] · [04:09].
- **Outcome:** What the final document deliberately does not claim: a bit-identical rerun; that the 7B is more accurate than the smaller cross-encoders (both 0.944); that running the 7B on everything was measured; any private-leaderboard result; significance for the US gain; internal package names such as B+ or mixf7. It states plainly that the private leaderboard had not been published when it was written.
- **Hindsight:** Five imprecisions survived into the submitted text, found afterwards by checking it against the records. None changes a decision.
  1. Section 2.2 says only 8% of the strongly rejected predictions are real matches. That is the 34% sample; the whole holdout gives 20% (16 of 80) (D-LLM-05).
  2. Section 2.1 says "a wrong merge costs twice as much as a missed copy", the challenge README's wording. In the F0.5 count form one false merge weighs as much as four missed copies; per S1 that has copies, a false add costs about 0.18 and a miss about 0.07.
  3. Sections 1 and 3 say the 3.70-per-S1 candidate set keeps 99.1% of the true pairs. 99.1% is the retrieval recall before the cut (58.4M pairs, about 34 per S1); the 3.70-per-S1 file keeps about 98.2–98.4% (D-SUB-06).
  4. Section 2.2 credits +0.000048 to the dynamic programme. It is the combined layer (the DP with its shifts, plus `acr` and `cap`); the DP alone is +0.0000332 and not significant (D-RUL-11).
  5. Section 4 says acronym joins apply everywhere. The French join is France only; the all-country rule is the hunt's `acr` (D-RUL-06, D-RUL-09).
- **Links:** [methodology](../../experiments/ameya/final-zip/doc/Documentation_template.md) · [finale README](../../finale/README.md) · D-PKG-15

### D-PKG-21 · Curate the package and match the organisers' tree exactly
- **When (IST):** 2026-09-29 03:27–03:54 · **Phase:** P5 · **Area:** PKG
- **Decided by:** agent for Ameya (curation, under the 03:26 instruction); Ameya ("It should match this", 03:41)
- **Status:** adopted
- **Problem:** The trial ZIP (289 files) carried personal paths, box-access details (as-run box records), internal research notes, two backup scripts with a personal path, code comments crediting internal "agents", and the organisers' own validator. Its root also had extras (`MANIFEST.sha256`, `figures/`), and `reproduce.sh`, `tests/` and `pyproject.toml` sat outside `src/`.
- **Options considered:** 1. Ship everything, for completeness. 2. Ship only what the run needs, in the organisers' structure.
- **Choice and why:** Option 2.
  - Curation ([commit 57ec7bf]): the model chain without research notes (only `RECIPE.md` kept), only `france_mixmdp.sh` and `s2w.py` from `pipeline/`, only `compositeB.sh` among Bakshi's shell scripts, and no organisers' validator (the README says to place `student_resource/` at the unzipped root). Code comments neutralised ([commit 4ac988d]).
  - Structure ([PR #76]): the root is exactly `output/`, `code/`, `Documentation_template.md` and the PDF (the only extra; the organisers accept a PDF export). `code/business_entity_resolution/` is exactly `src/`, `README.md` and `requirements.txt`. `reproduce.sh`, `tests/` and `pyproject.toml` moved under `src/`. The figures are embedded in the `.md` as base64 images at the end of the file. `MANIFEST.sha256` is written beside the ZIP. The build now fails if anything falls outside this tree.
- **Evidence:** An independent check found zero flagged paths, addresses, e-mails, agent mentions, TODOs or secrets; no data files besides the two outputs; no CRLF line endings in scripts. Trial build: PACKAGE OK, 146 files, 115 tests from `src/tests`, validator and audit PASS, output hashes unchanged [M] [chat:ameya/19e315ba 2026-09-29 03:54].
- **Outcome:** 289 → 146 files.
- **Hindsight:** unknown (none recorded).
- **Links:** [PR #74] · [PR #76] · [issue #75] · [chat:ameya/19e315ba 2026-09-29 03:30] · [03:38] · [03:41]

### D-PKG-22 · Accept the reviewer-agent's checklist and its four wording fixes
- **When (IST):** 2026-09-29 03:37–04:09 · **Phase:** P5 · **Area:** PKG
- **Decided by:** Ameya ("Do them"); proposed by: Bakshi's agent on [issue #75]
- **Status:** adopted
- **Problem:** An independent check of the ZIP before upload.
- **Options considered:** not recorded.
- **Choice and why:** Issue #75 gave Bakshi's agent eight checks: the hash, the outputs, a clean install and tests, the drivers, the README, every number about his part, nothing sensitive, and an optional rebuild. All eight passed on the ZIP `7f077875…`, including a byte-identical rebuild. The four suggested fixes plus an optional fifth were applied in [PR #77] and the ZIP rebuilt.
- **Evidence:** [R] [chat:ameya/19e315ba 2026-09-29 04:02] · [04:09].
- **Outcome:** Final ZIP `60b60152…` [R]. Bakshi's 04:01 check covered the earlier ZIP; the restructured and final ZIPs were verified by the builder's own gates.
- **Hindsight:** Cross-member review caught real overstatements late. The two ZIP hashes come from chat statements only; the repo does not record them.
- **Links:** [issue #75] · [PR #77]
