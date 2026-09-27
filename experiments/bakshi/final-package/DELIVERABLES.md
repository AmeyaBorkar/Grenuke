# Deliverables status, against the six required items

Checked 2026-09-27 03:10 IST. Branch `bakshi/opus-exec`. One item is **incomplete and cannot be completed on
this machine**; it is named as a blocker rather than quietly marked done.

---

## 1. Experiment ledger and comparison report — **complete**

`ledger.json` (machine-readable) plus `TRACK_B_FINDINGS.md`. Every figure is tagged by provenance:
`verified_locally: true` means recomputed here; anything else is attributed to its record, handover or issue
comment. Includes the honest limitations, the corrections the captain made to my claims, and the two
hypotheses I tested and rejected.

## 2. Protected best matching and its correct candidate TSV, both validated — **complete**

| file | bytes | sha256 |
|---|---|---|
| `matching_results.tsv` | 97,909,982 | `659f5169cabbb2a3de2cb8580b614bbff718ea62d5b1fb4497243b50fcc34533` |
| `candidate_pairs.tsv` | 105,027,973 | `510a33ea18a7ab4cd2ec5ad4e8ad113bbc4fd4f46818941c00f29852f3e258aa` |

**AUDIT PASS** on every hard check: 1,732,544 rows (exact set equality with the test S1), 5,856,096 pairs,
100,137 empty, 0 duplicate rows, 0 duplicate pairs, 0 bad prefixes, 0 targets absent from `test_source2/3`,
**0 records claimed by more than one S1**, **0 cross-country pairs**, **0 matched pairs outside the candidate
set**. Report: `audit_v7nst_FINAL.json`.

## 3. `Grenuke_submission.zip` with extracted validation, manifest and sha256 — **complete**

`4bd6c7a1d6b38cc5c7cfba197704d2004b4b9b607f91021053e29c7075b0f6ab`, 87,526,328 bytes, 103 files.
Verified **after extraction to a separate directory**: all 103 manifest hashes match, all 15 required paths
present, `code/` byte-compiles, organiser validator PASS, strict audit PASS. `MANIFEST.sha256` ships inside.

## 4. Reproduction instructions **and actual clean-run evidence** — **INSTRUCTIONS COMPLETE, CLEAN RUN NOT DONE**

**This is the one incomplete deliverable. Stating it plainly: `reproduce.sh` has never been executed
end-to-end, by me or by anyone, and it cannot be executed on this machine.**

Why not, concretely:
- `ce.py` / `ce_box.py` / `ce_llm_st.py` need a CUDA GPU with `torch`. **This machine has no `torch`
  installed** and a 4 GB RTX 2050; e5-large at the submitted settings needs the H100 the runs used.
- Stages 1–3 peak at **18–19 GB RAM each**. This machine has **16 GB**. A full run also contains several
  stage-2 fits that must run serially.
- The full chain is ~6–7 h wall clock on the reference machine *plus* an H100 for the encoders.

So the honest status is: the chain is **transcribed and statically verified**, not **executed**.

What *has* been verified, so the claim is neither more nor less than it is:

| check | result |
|---|---|
| `bash -n reproduce.sh` | syntax OK |
| every `VARIANT` dispatch path exercised | all 8 resolve to the right group/column/teacher/bag; unknown variant exits 2, and the two with unrecorded tags exit 4 naming what is missing |
| every flag cross-checked against the scripts' own `argparse` | matches `s2.py`, `decide.py`, `stage3.py`, `cands_final.py`, `ce_import.py`, `post_ops.py`, `acr_join.py`, `ce.py`, `ce_box.py` |
| chain correctness | reconstructed from `RECIPE.md` (which the captain wrote and has since extended with the teacher-before-student ordering this review asked for), the v7n handover and the sub04 record |
| **every `ber` submodule imports from the extracted archive, nothing else on the path** | **34 of 34, 0 failures** |
| **the shipped tests pass against the shipped src, run from the archive** | **115 passed** |
| `python -m ber.pipeline` responds from the archive | yes |
| package byte-compiles from the extracted archive | yes |

**A real defect was found by doing this, and it would have shipped.** Earlier builds ran the tests against the
*repository*, not the archive. Running them against the archive exposed that
`code/business_entity_resolution/src/ber/features/tokens.py` **was missing from the zip**: the builder's
secret-shaped-filename filter included the glob `*token*`, which matched a legitimate source file. The
archive byte-compiled cleanly — `compileall` compiles each file alone and never resolves an import — so every
check I had was passing on a package that could not run.

Fixed two ways: the filename globs are now narrow and are never applied to source suffixes at all (contents
are still scanned for secrets, which is the appropriate mechanism), and `make_package.py` now **walks and
imports every `ber` submodule and runs the shipped tests, from the extracted archive, as hard build gates**.
The lesson generalises: *verify the artifact, not the source it came from.*

**What would close this properly:** one run of `VARIANT=v7nst bash reproduce.sh` on the integration machine
plus an H100, into a fresh `BER_WORK_DIR` and `BER_OUTPUT_DIR` so the production cache is untouched,
recording commit, environment, runtime and the resulting hashes. **That is a 6–7 h job competing for the same
GPU and RAM as the remaining model variants, on a day with a 21:00 deadline.** My recommendation is *not* to
do it today — the marginal value is low next to the risk of disturbing the variant queue, and GPU
nondeterminism means the hashes would not match anyway. But it must be reported as not done, not implied.

## 5. GitHub handover/status and focused PRs — **complete**

- Handover `docs/handover/2026-09-27_0111_bakshi_final-package.md` (updated in place when the blocker cleared)
- Status `docs/status/bakshi.md`
- **PR #50** merged — auditor, reproduction script, package builder
- **PR #54** merged — cross-encoder family weighting, v7ens2 audit
- **PR #56** open — final ledger hash
- Five coordination comments on issue #45

## 6. Final message — pending

Owed at hand-off: best observed score, exact paths and hashes, upload confirmation if the captain reports it,
spend incurred, and remaining risk.

**Spend incurred by this session: nothing.** No GPU rental, no paid job, no upload slot. All work was local
CPU plus GitHub API reads and writes.

---

## Remaining risk

1. **No clean-run evidence** (item 4 above). The instructions are transcribed and statically checked, not
   executed.
2. **The shipped model may change.** The package currently carries `v7nst`, the best *measured* result, held
   at the captain's instruction. If v7s / v7sq / v7ensall is chosen, the zip must be reissued — one parameter
   plus ~4 min — and `make_package.py` refuses on a hash mismatch, so the bundle cannot silently disagree
   with what was uploaded. The **risk is procedural, not technical**: someone must remember to reissue it.
3. **Two documents on `main` are stale in ways that could mislead.** `AGENTS.md` line 15 still says the
   deadline is 23:59 IST when it is 21:00 — it is the first file every agent reads. And `docs/package/` is
   still @ssdhoka06's v6-era draft; the v7nst version lives in `experiments/bakshi/final-package/`. Both are
   shared or another owner's files, so this session did not edit them.
4. **The final upload must be the best measured file.** With 5 slots and several candidates that look
   indistinguishable offline, the ordering matters more than any remaining offline analysis. A probe or an
   unproven variant must never be left as the last upload.
