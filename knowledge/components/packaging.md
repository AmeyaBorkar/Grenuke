# Packaging and reproducibility (PKG)

**Summary.**
- The ZIP holds the exact uploaded Composite B files, the code that makes them, pinned requirements, 115 unit tests, a strict audit and the methodology document. The root has exactly `output/`, `code/`, `Documentation_template.md` and its PDF.
- A rerun is not byte-identical. We claim it lands within about ±0.0001, because GPU training differs across machines and stage 3 moves about 500 decisions. We did not rerun the whole chain on a GPU after the final day.
- Path key: `fpk/` = `experiments/bakshi/final-package/` (in the ZIP, `src/`), `box/` = `experiments/bakshi/box/`, `pipe/` = `experiments/ameya/model-v1/pipeline/`, `mv1/` = `experiments/ameya/model-v1/`. Levels as in [STANDARD §3](../STANDARD.md).

## 1. Purpose

Let the organisers, and us, check that the submitted files come from the shipped code, and say plainly what is exact and what is not.

## 2. How it works

**The ZIP** ([D-PKG-21], [D-PKG-14]): the root is exactly `output/`, `code/`, `Documentation_template.md` and the PDF export (the only extra). `code/business_entity_resolution/` is exactly `src/`, `README.md` and `requirements.txt`; `reproduce.sh`, `tests/` and `pyproject.toml` sit under `src/`. Figures are embedded in the `.md` as base64 images at the end. `MANIFEST.sha256` is written beside the ZIP, and the build fails if anything falls outside the tree. Final ZIP `60b60152…`, 88,353,040 bytes, 146 files, built from `main` at `ed5bc7e` [M]. Outputs shipped verbatim: `output/matching_results.tsv` (97,854,781 bytes, sha256 `df4bccd7…`) and `output/candidate_pairs.tsv` (105,028,761 bytes, `58c824a3…`) ([D-PKG-11]). The 7B adapters and intermediates are left out ([D-PKG-14]).

**Drivers**
- `fpk/reproduce.sh`: a variant switch (`:88-107`); `VARIANT=compositeB` is the default and runs `box/compositeB.sh` (`:54, 60-65`); `STACK=1` adds the stack (`:266-273`); it ends with the organiser validator and the strict audit (`:280-289`). `v7sb` and `v7ensall2` are recognised but refuse to run, because their tags were never recorded (`:104-105`) ([D-PKG-06]).
- `box/compositeB.sh`: eight steps of its own (the data-flow table below has 18 in all), each skipped when its output exists. Knobs: `Q7_MODEL`, `Q7_GPUS` (default "0 1 2"; fewer than three GPUs run sequentially on the first), `SCORE_BATCH` (512), `FR_DIR`, `CHECK_7B`, `BER_OUTPUT_DIR` (default `output_rerun/`, never the shipped `output/`) (`:16-23`).
- `pipe/france_mixmdp.sh`: France block steps F1–F10; knobs `FR_DIR`, `CE_GPU`, `E5FR_PARALLEL` (`:26-28`) ([D-PKG-17]).

**The data flow** (`fpk/reproduce.sh` calls `box/compositeB.sh`, step 1 calls back with `VARIANT=v7sq STACK=1`)

| step | what | output or number |
|---|---|---|
| 1 | records from the raw TSVs (`ber.pipeline --stage records`) | `work/records/{train,test}.parquet`, truth; 45 s |
| 2 | Indic-to-Latin dictionary (`feats.py --dict-only`) | 693 entries |
| 3 | blocking v3 (`--set trim_s1=15 trim_r=4 ns_ngrams=4 ns_domain_len=8 nw_words=6`) | 66,429,057 train and 58,437,794 test pairs, about 34 per S1 |
| 4 | pair features, bundle `ameya-fx5` (six groups, row-aligned) | 52 min on the box |
| 5 | stage 0 and stage 1 (`s1.py`) | p0, p1 per pair |
| 6–7 | e5-small feature; band export | 1,568,554 train and 1,490,930 test band rows |
| 8 | teacher v7ce3: e5-large, e5-base, stage 2, decide, stage 3, rules | `ameya-cands-v6all-c2` (the c2 cut) |
| 9 | round-1 French pseudo-labels | band and stage-2 files |
| 10–11 | v7sq encoders (e5ls, qst, bge) and the v7sq chain with the stack | `ameya-model-v7sq-s3-ops3a-dpc` |
| 12–13 | round-2 band labels; q7st on three GPUs | 385,274 band pairs; adapters 0–2 |
| 14–15 | French pairs for the re-check; g1w with the 7B twice in the mix | holdout 0.991323 |
| 16 | 7B re-check scoring | `fr_scored`, `usin_scored` |
| 17 | France block (F1–F10) | 871,147 French pairs |
| 18 | compose, validator, audit, sha256 | the two TSVs |

Details of each stage are on [blocking.md](blocking.md), [features.md](features.md), [model-stages.md](model-stages.md), [cross-encoders.md](cross-encoders.md), [decision-layer.md](decision-layer.md), [rules.md](rules.md), [france.md](france.md) and [llm-recheck.md](llm-recheck.md).

**Stated deviations from the 27 Sep run** (`box/compositeB.sh:208-212`, `pipe/france_mixmdp.sh:37-55`): the encoders train on the package's own band, so no remap; v7sq's own chain plays the role of g0; compose takes `g1w-dpc` directly; `export_usin.py` takes arguments and reads labelled countries from the train records. France block: paths only; same code under committed names; step F9 run on v7sq7wg-dpc itself, checked on 29 Sep with identical French rows (871,147 pairs, 0 differ either way) [M]. The bges seed is unknown; 26 is used [U]. As run on 27 Sep, steps 1–11 and 13–16 ran on a rented 2× RTX 4090 box (64 vCPU), the encoders trained on the laptop's band and were re-keyed by (s1, r) at 100.0000% (train) and 99.9999% (test).

**Pinned requirements** (`requirements.txt`, `box/setup.sh:28-29, 35`, `box/train_jobs.sh:47-57`): 15 packages. torch 2.11.0 (cu128; cu126 below driver 570), transformers 5.17.0, tokenizers 0.23.2, safetensors 0.8.0, huggingface_hub 1.7.2, peft 0.21.0, accelerate 1.15.0, xgboost 3.2.0, numpy 2.4.3, pandas 2.3.3, pyarrow 23.0.1, scipy 1.17.0, scikit-learn 1.8.0, numba 0.64.0, rapidfuzz 3.14.6. The first `pip install -r` failed with ResolutionImpossible (transformers 5.17.0 needs tokenizers 0.23.1 or later and safetensors 0.8.0 or later); Ameya fixed it in PR #74 with the captain's approval ([D-PKG-12]). A clean Python 3.13.2 environment installs on Windows [M]. The non-finite-gradient guard is mandatory on torch 2.11.

**Tests and audits**
- **115 unit tests** pass in the repo and in every ZIP build [M].
- **The strict audit**, `fpk/audit_matching.py:11-19` (shipped as `src/model_v1/audit_matching.py`), exits non-zero unless: the header is exact; there is one row per test S1; no id repeats within a list; every S2 and S3 id exists in the test sources; no record has two owners; no pair crosses countries; matches are a subset of the candidates. The organiser validator only warns on the last two ([D-PKG-04]). On Composite B: 0 / 0 / 0.
- **The package builder**, `make_package.py`, scans for credentials, writes a deterministic zip, re-extracts it and re-hashes every member, imports every `ber` submodule (34 of 34) and runs the shipped tests from the extracted archive as hard gates. It exists because a `*token*` glob once dropped `ber/features/tokens.py` from every ZIP and five hashes had to be withdrawn ([D-PKG-05]).
- **Provenance:** every artifact carries git commit, command and inputs (`ber/artifacts.py:42-63`). The stack port was checked byte for byte ("PORT OK", 115 tests) ([D-PKG-08]).
- **Review:** an eight-item reviewer check passed on ZIP `7f077875…`, including a byte-identical rebuild; four wording fixes were applied ([D-PKG-22]).

**Reproducibility limits.** XGBoost with fixed seeds is deterministic on one machine. Cross-encoders are not bit-identical across GPUs (TF32, cuDNN kernel choice). Stage 3 moves about 500 decisions between machines (232k test pc values differ, maximum 0.09). A rerun should land within about ±0.0001 and is checked against the holdout reports, q7st's AUC and the drop counts, not against hashes. The rebuilt g0 scored 0.991261 against v7sq's 0.991246 [M]. Hardware: CPU stages need 24 or more cores and 32 GB RAM (peak 18–19 GB), a CUDA GPU (XGBoost uses `device: cuda`, [CF-37]), encoders on one 80 GB H100, the 7B on three. e5-large at batch 128 does not fit in 12 GB. Rough costs: records 45 s, blocking about 11 and 15 min, features 52 min, France block about 4.5 h, the 7B about 2 h on three H100s ([D-PKG-18]).

## 3. Why this design

- Port the real model, then fix provenance: [D-PKG-01], [D-PKG-02]. A strict audit on top of the official validator: [D-PKG-04]. Hash-gate the package: [D-PKG-05].
- One variant-driven `reproduce.sh`, refusing unrecorded variants; no second script: [D-PKG-06], [D-PKG-09]. Port the stack with an equivalence test: [D-PKG-08].
- No clean end-to-end rerun on the final day: [D-PKG-07]. It would compete for the same GPU and RAM, and non-determinism means hashes would not match anyway.
- Ship the exact uploaded TSVs; the ZIP carries B, not B7 or mixf2: [D-PKG-10], [D-PKG-11]. A runnable driver, "exact by construction" for the last step: [D-PKG-12], [D-PKG-13], [D-PKG-17].
- Claim only what was tested: [D-PKG-18], [D-PKG-20]. One document on the template's headings: [D-PKG-15], [D-PKG-16], [D-PKG-19]. Match the organisers' tree: [D-PKG-21], [D-PKG-22].

## 4. Alternatives and why not

- **A second reproduction script** over overlapping chains would re-create the drift risk ([D-PKG-09]).
- **Four documents instead of one:** judges might open only one; decisions cross sections ([D-PKG-15]).
- **Shipping intermediates and adapters:** the ZIP only has to rebuild outputs from raw data; the size limit was unknown ([D-PKG-14]).
- **A full GPU rerun as proof:** not possible on the deadline; Bakshi's laptop could not run it (no torch, 4 GB GPU, 16 GB RAM against 18–19 GB peaks) ([D-PKG-07]).
- **B7 in the ZIP:** ties B and needs the Qwen3-4B step ([D-PKG-10]).

## 5. Numbers

| fact | value | level |
|---|---|---|
| Composite B outputs | 5,851,832 pairs, 1,732,544 S1, 3.3776 per S1; candidates 6,410,308 | M |
| Candidate file | 3.70 per S1 | M |
| Methodology | 7 pages, A4, Times New Roman 11.5 pt, 3 figures; body 19,461 characters; due 29 Sep 10:00 IST | M |
| Checks | validator PASS; strict audit PASS; 12 of 12 audits passed on the final candidates; 115 tests | M |
| Rebuild | g0 0.991261 against 0.991246; France block 871,147 pairs, 0 differences | M |

**What the methodology claims, and where it is loose** (it cannot change now; speak from the record). Five imprecisions were found afterwards; none changes a decision ([D-PKG-20]):

| the document says | the record says | say instead |
|---|---|---|
| Only 8% of strongly rejected predictions are real | the 34% sample; the whole holdout is 20% (16 of 80) ([CF-19]) | "20% on the whole holdout, 8% on the sample" |
| A wrong merge costs twice a missed copy | that is the β weighting; in counts one false merge weighs four misses, about 2.7 for a typical S1 ([CF-15]) | "precision counts twice as much as recall; about 2.7 times per S1" |
| The 3.70-per-S1 set keeps 99.1% of true pairs | 99.1% is retrieval recall before the cut (about 34 per S1); the file keeps 98.35% ([CF-13]) | "retrieval 99.1%, the cut 98.35%" |
| The DP beat the best threshold by +0.000048 | that is the combined layer; the DP alone is +0.0000332 and not significant ([CF-16]) | "the whole decision layer gained +0.000048" |
| Acronym joins apply everywhere | the French join is France only; the all-country rule is the hunt's `acr` ([CF-25]) | "each rule runs where we measured it" |

Further qualifications: 0.9913 is the stage-3 decision on g1w, not the stacked layer ([CF-17]); the holdout is a comparison set, because the final fit also saw its rows ([CF-18]); stage 0 removes about 85%, not 80% ([CF-22]); the self-training label sets are mixed ([CF-28]); the 7B ties e5-large ([CF-35]); a CUDA GPU is needed ([CF-37]).

## 6. Failure modes and limits

- **Not bit-exact.** The claim is "within about ±0.0001".
- **Only the last step is proven exact.** The local recomposition of B was byte-identical; the whole GPU chain was not rerun on one package on the final day.
- **As-run scripts are records.** The `pipe/*.sh` as-run files hard-code laptop paths and a box alias; they are not runnable drivers. The as-run `apply_combo.py` hard-coded ("US", "India"); the repo version reads the train records, and the port was verified.
- **bges seed 26 is assumed;** e5ls2's seed 11 comes from `pipe/france_mixmdp.sh:94` and its as-run launch script is not in the repo [U].
- **Hardware heavy.** 24+ cores, 32 GB RAM, a CUDA GPU, an 80 GB card for the 7B.
- **Document loose spots** above, plus small code differences ([CF-38]).

## 7. Scale

The package is built for one 64-vCPU box plus GPUs. At 100× the records the first bottlenecks would be the blocking pair table (66M train pairs at about 34 per S1, growing with name collisions), the feature table (about 19 GB at test scale) and stage-2 memory (16.5–19 GB peaks): all would need sharding by country or block key, and the band-only cross-encoders keep the transformer cost proportional to the uncertain pairs. The design favours restartable steps ("skip if output exists"), which is what a 100× run would need. Beyond about 10× this is a redesign, not a rerun; see [theory 11](../theory/11-scaling-to-billions.md) and [F17](../theory/foundations/F17-production-ml-and-mlops.md). These are projections [E].

## 8. Theory links

[11 scaling to billions](../theory/11-scaling-to-billions.md), [10 LLM verification and compute](../theory/10-llm-verification-and-compute.md), foundations [F08](../theory/foundations/F08-computing-at-scale.md), [F09](../theory/foundations/F09-experiments-and-evidence.md), [F17](../theory/foundations/F17-production-ml-and-mlops.md). Neighbours: [process-and-infra.md](process-and-infra.md), [submission-strategy.md](submission-strategy.md).

## 9. Likely questions

- **Can I reproduce your result?** Yes within about ±0.0001. The code, pins, tests and audit are in the ZIP. It is not byte-identical, and a full run needs a CUDA GPU, 24+ cores and an 80 GB card for the 7B.
- **How do you know the shipped output is what you uploaded?** The TSVs are the uploaded bytes, with sha256 in `MANIFEST.sha256`; the audit and validator pass on them.
- **What exactly is non-deterministic?** GPU training (TF32, kernel choice) and stage 3, which moves about 500 decisions.
- **Why no full rerun?** It would compete for the GPU on the deadline day and could not match hashes anyway; we verified the last step and the France block rows.
- **Where is the document loose?** Five places, listed above; none changes a number we used.
- **What is not in the ZIP?** Intermediates and the 7B adapters; they are rebuilt.
- **Is the data kept out?** Yes: no data files besides the two outputs, no secrets, no paths.

[CF-13]: ../conflicts.md
[CF-15]: ../conflicts.md
[CF-16]: ../conflicts.md
[CF-17]: ../conflicts.md
[CF-18]: ../conflicts.md
[CF-19]: ../conflicts.md
[CF-22]: ../conflicts.md
[CF-25]: ../conflicts.md
[CF-28]: ../conflicts.md
[CF-35]: ../conflicts.md
[CF-37]: ../conflicts.md
[CF-38]: ../conflicts.md
[D-PKG-01]: ../decisions/PKG.md
[D-PKG-02]: ../decisions/PKG.md
[D-PKG-04]: ../decisions/PKG.md
[D-PKG-05]: ../decisions/PKG.md
[D-PKG-06]: ../decisions/PKG.md
[D-PKG-07]: ../decisions/PKG.md
[D-PKG-08]: ../decisions/PKG.md
[D-PKG-09]: ../decisions/PKG.md
[D-PKG-10]: ../decisions/PKG.md
[D-PKG-11]: ../decisions/PKG.md
[D-PKG-12]: ../decisions/PKG.md
[D-PKG-13]: ../decisions/PKG.md
[D-PKG-14]: ../decisions/PKG.md
[D-PKG-15]: ../decisions/PKG.md
[D-PKG-16]: ../decisions/PKG.md
[D-PKG-17]: ../decisions/PKG.md
[D-PKG-18]: ../decisions/PKG.md
[D-PKG-19]: ../decisions/PKG.md
[D-PKG-20]: ../decisions/PKG.md
[D-PKG-21]: ../decisions/PKG.md
[D-PKG-22]: ../decisions/PKG.md
