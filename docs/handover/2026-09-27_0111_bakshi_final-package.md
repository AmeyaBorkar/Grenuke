# Handover: final-package (v7nst output audit, reproduction and packaging)

> **UPDATE, 01:50 IST — the blocker is resolved and the package is built.** ameya delivered the paired
> candidate file (`510a33ea…`, verified against the folder's own `SHA256SUMS.txt`, 13/13 files OK). It has
> **6,410,247** pairs, exactly the count predicted below before the file was seen. The real pair audits
> **AUDIT PASS with 0 matched pairs outside the candidate set**, and `Grenuke_submission.zip` is built and
> self-verified. See §"Resolution" at the end. **Track B is closed with evidence** — `out_bge` does not
> exist, so there is no independent family; details in `experiments/bakshi/final-package/TRACK_B_FINDINGS.md`.
> Everything before that section is the state as of 01:11 and is kept for the record.

- **Author:** bakshi (agent: Claude Code)
- **When (IST):** 2026-09-27 01:11, updated 01:50
- **Branch / PR / last commit:** `bakshi/opus-exec` / PR #50 / based on main `2023ffbae034e274aab5cb262c982d6fef762e5c`
- **Area and paths touched:** `experiments/bakshi/final-package/**` only, plus this handover and
  `docs/status/bakshi.md`. **No shared file, no pipeline code and no other owner's path was modified.**

## TL;DR (3 lines max)

- **The submitted v7nst matching file is sound**: hash confirmed, and it passes every hard check against the
  full test data — 1,732,544 rows, 0 owner conflicts, 0 cross-country pairs, all 5.86M targets present.
- **It has no valid package**: its paired `candidate_pairs.tsv` (`510a33ea…`) is not on this machine, and the
  v6all candidate file cannot substitute — **3,790 matched pairs over 3,725 S1 fall outside it**.
- Built the auditor, the full v7nst reproduction script (including the previously undocumented `v7ce3`
  teacher), pinned requirements, the methodology document and a self-verifying zip builder.

## What was done

1. **`audit_matching.py` — a strict output audit, because `PASS` is not sufficient.**
   `student_resource/utils/validate_submission.py` treats a **missing candidate file** and **matches outside
   the candidate set** as *warnings* and still prints `PASS`. It also never checks owner uniqueness or
   country consistency. The auditor checks all of it and exits non-zero.
2. **Audited the submitted v7nst output** against the provided test sources (see Numbers).
3. **Established that the v7nst candidate file is missing**, by recursive search of
   `C:/Users/baksh/{Documents/Codex,Desktop,Downloads}`. The only candidate TSV on the machine is
   `candidate_pairsv6all.tsv`.
4. **Quantified why v6all candidates cannot be shipped with v7nst**: 3,790 matched pairs / 3,725 S1 fall
   outside. Reading `acr_join.py`, that is exactly its `new_c` — the acronym copies it appends to *both*
   the matches and the candidate set. **Prediction for the real file: 6,410,247 pairs**
   (6,406,457 + 3,790); if it differs, `--cands` was not `ameya-cands-v6all-c2`.
5. **Ran a control** to prove the auditor is not producing a false alarm: the v6all matching/candidate pair
   audits with **0 pairs outside candidates, AUDIT PASS**. Same tool, same data, clean result.
6. **`reproduce_v7nst.sh` — the full chain.** v7nst's pseudo-labels come from **`v7ce3`**, so a clean run
   must build the teacher *before* the student, including `multilingual-e5-base` (in the teacher's feature
   set, absent from the student's). Cached pseudo-labels cannot be an undeclared prerequisite. The merged
   `docs/package/reproduce_v*.sh` scripts stop at v6 and do not cover this.
7. **`requirements.txt`** — dropped `lightgbm` (imported by no module in `src/ber`, `src/model_v1` or
   `tests`); left `torch`/`transformers` unpinned **with an explicit note** rather than guessing them from a
   machine that has neither installed.
8. **`Documentation_template.md`** — the official methodology document, rewritten for v7nst, with every
   figure tagged `[measured]` / `[holdout]` / `[public]` / `[proxy]`, and a §5.4 that states the limits of
   our own evidence.
9. **`make_package.py`** — refuses to build unless both TSVs match their expected sha256, optionally gates
   on the audit, scans staged text for credential patterns, writes a deterministic zip, then **extracts it
   to a scratch dir and re-hashes every member** against the manifest before reporting success.
10. **`ARTIFACT_REQUEST.md`** — the precise, prioritised list of what the integration machine must supply
    for Tracks A and B and for the package.

## Current state

- **Works:** the auditor, the control, the reproduction script, the requirements, the methodology
  document, the artifact request. 115/115 repository tests pass.
- **Half-done:** `make_package.py` is exercised end-to-end on the v6all pair as a dry run. It has **not**
  produced the real `Grenuke_submission.zip`, because the v7nst candidate file is missing.
- **Known caveats:**
  - The local `matching_resultsv6all.tsv` is `544ffdf8…`, **not** the packaged v6all `0f6d8985…` in
    `RECIPE.md`. It is a different v6 build. Its subset-cleanliness against the v6all candidate file shows
    the two are *consistent* (same candidate base) — it does **not** identify them as the uploaded pair.
    **Subset-consistency is necessary but not sufficient; only the hash identifies a package.** This is
    exactly why `make_package.py` gates on sha256.
  - On this machine 13 tests error first on `%TEMP%\pytest-of-baksh`, which is owned by another Windows
    account. Rerun with `--basetemp` somewhere writable. Not a code failure.
  - The repo checkouts under `in/work/` are owned by a different Windows account; `git` needs
    `safe.directory` entries for them.

## Numbers (shared holdout, `ber.eval`; include the command)

Model metrics are unchanged — this work touched no pipeline code. The figures below are *measured on the
submitted output bytes*, which had not been independently verified before.

| metric | value | command |
|---|---|---|
| v7nst matching sha256 / bytes | `659f5169…c34533` / 97,909,982 — matches `sub04` | `Get-FileHash -Algorithm SHA256` |
| rows vs test S1 | **1,732,544**, exact set equality, 0 duplicates | `audit_matching.py` |
| predicted pairs / empty rows / per S1 | 5,856,096 / 100,137 / 3.3801 | " |
| records claimed by >1 S1 | **0** | " |
| cross-country predicted pairs | **0** | " |
| targets absent from `test_source2/3.tsv` | **0** (all 5.86M exist) | " |
| France / India / US test S1 | 259,452 / 809,986 / 663,106 | " |
| France / India / US pairs | 871,242 / 2,735,918 / 2,248,936 | " |
| matched pairs outside the **v6all** candidate file | **3,790** over 3,725 S1 → package pairing FAILS | " |
| control: v6all matching vs v6all candidates | **0** outside, AUDIT PASS | " |
| repository tests | **115 passed** | `pytest -q --basetemp=<writable>` |
| holdout macro F0.5 (all / US / India), reported | 0.991194 / 0.991005 / 0.991472 | `sub04` record |

One incidental finding worth recording: **France is 14.9752% of test S1** (259,452 / 1,732,544), which is
exactly the `0.14975` in `F_France = (LB − 0.843226) / 0.14975`. That formula therefore assumes the *public*
subset has the whole test set's country mix. Unverified — so every "France ≈ 0.981" figure is an estimate,
not a measurement.

## How to reproduce or continue (exact commands)

```
# strict audit of any candidate package (exits non-zero on a hard issue)
python experiments/bakshi/final-package/audit_matching.py \
  --matching <matching.tsv> --candidate <candidates.tsv> \
  --test-dir "$BER_DATA_DIR/test" --json <report.json>

# build + self-verify the final zip (refuses on a hash mismatch)
python experiments/bakshi/final-package/make_package.py --repo-root . \
  --matching <matching.tsv> --candidate <candidates.tsv> \
  --expect-matching-sha 659f5169cabbb2a3de2cb8580b614bbff718ea62d5b1fb4497243b50fcc34533 \
  --expect-candidate-sha 510a33ea18a7ab4cd2ec5ad4e8ad113bbc4fd4f46818941c00f29852f3e258aa \
  --out dist --audit --test-dir "$BER_DATA_DIR/test"

# full reproduction of the submitted model, teacher included
MODEL_DIR="$PWD/experiments/ameya/model-v1" bash experiments/bakshi/final-package/reproduce_v7nst.sh
```

## Artifacts (local paths / drive links + sha256)

- `C:/Users/baksh/Downloads/New folder/matching_resultsv7nst.tsv` — `659f5169…c34533`, 97,909,982 bytes.
  **The protected best. Do not overwrite.**
- Its `candidate_pairs.tsv` — **`510a33ea…f3e258aa`, NOT PRESENT on this machine.**
- `C:/Users/baksh/Downloads/New folder/candidate_pairsv6all.tsv` — `cc3750d0…9dceaae`, 6,406,457 pairs.
  The c2 candidate base. **Not** v7nst's candidate file.
- Reports committed: `experiments/bakshi/final-package/audit_v7nst_vs_v6allcands.json`,
  `audit_v6all_pair.json`. Ledger: `ledger.json`.

## Next steps (ordered, with suggested owner)

1. **@AmeyaBorkar / integration machine —** supply the items in
   `experiments/bakshi/final-package/ARTIFACT_REQUEST.md`. Priority: (1) the v7nst `candidate_pairs.tsv`;
   (2) `out_bge` + `out_e5l` + `out_e5l2` + `out_cem2` + band files + `rule_pop` output for Track B;
   (3) the `pc` / operation-family breakdown of each probe's **final** removals, which decides Track A's
   sign before a slot is spent; (4) the four probe audit JSONs; (5) torch pins and the portal quota.
2. **bakshi —** on arrival: confirm the candidate hash and the 6,410,247 prediction, build and self-verify
   `Grenuke_submission.zip`, record its sha256, and hand it to the captain.
3. **bakshi —** Track B screening locally once the logits land: reproduce `out_cem2` bit-for-bit from
   `out_e5l` + `out_e5l2` as an alignment proof *before* building any blend, then the 50/50 E5-family/BGE
   arm, scored with `sklearn.metrics.roc_auc_score` on common finite rows.
4. **Owners —** decide whether this v7nst package supersedes the v6-era `docs/package/` draft (PR #30,
   @ssdhoka06). Not overwritten here.

## Blockers, open questions, decisions needed

- **BLOCKER —** the v7nst `candidate_pairs.tsv`. Without it there is no valid final package, only a valid
  matching file. Synthesising one from the final matches is not acceptable: it would not represent the
  candidates the pipeline actually considered.
- **`AGENTS.md` line 15 still says the deadline is 23:59 IST.** Issue #45 (captain, 23:43) says the window
  closes at **21:00 IST**. AGENTS.md is a shared file, so it was not edited here — but it is the first file
  every agent reads, and it is wrong. Needs its owner to fix it.
- **Not verified by this session:** the three `probe-v7nst-fr*` packages and their reported change counts;
  the completion or results of `v7nst2` / `v7mst` / `v7s`; the portal's remaining upload quota. All are
  reports, and the ledger marks them as such.
- **Track B cannot complete on this machine.** Stage 2 peaks at ~19 GB; this laptop has 16 GB. The blend
  screening is local, the downstream fit is not.
