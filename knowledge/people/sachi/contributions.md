# Sachi: contributions

Summary: what Sachi built, owned, checked and originated, with the state of each piece in the repo. The final
pipeline (Composite B) used one piece of this work directly: the LoRA cross-encoder code. The rest was baseline work,
gates, diagnostics and packaging help.

Status labels: **in Composite B** (used by the final chain), **on main, not in B** (merged, but unused by the final
chain), **unmerged or unknown** (state not confirmed).

## 1. What Sachi built

| piece | what it is | state | source |
|---|---|---|---|
| `ber.model` train, predict, decide stages and the ownership fix | v0 baseline: stage-1 XGBoost, isotonic calibration, argmax ownership, threshold decision | **on main, not in B**. Merged 2026-09-25 in two PRs: [PR #16] (opened by me, merged by Ameya; branch `sachi/model-v0`; 9 files, +776; the model in `experiments/sachi/`) and [PR #17] (opened by Ameya with my follow-up commit [commit fd7bf67] rebased onto main; 7 files, +544 -33; moves the model into `ber.model`, adds the ownership fix, closes #8 and #9). Not imported by the final chain. | [PR #16], [PR #17], [issue #66] |
| v3 port into `ber.model` ([PR #27], opened by me, merged) | ports Ameya's v3 chain (`v3.py`: stage 0 filter, stage 1, stage 2 with rivalry and optional cluster-support features, isotonic calibration; `legal.py` `build_group()`; `cluster.py`, `recs.py`; `decision.py` `expected_f_select`; `__init__.py` makes train, predict and decide default to v3, with `--set model=v0` keeping the old path; `split_devkit_groups.py`; `test_model_decision.py`). The draft description says: only I/O changed, 74 tests pass (43 existing plus one new), tested end to end on synthetic data, not yet run on real data | **on main, not in B**: Composite B drivers call only the records, block and write stages ([issue #66] check B). Whether the ported chain was ever run on real data: unknown | [PR #27], [chat:sachi/web-2 2026-09-26 10:09] |
| `experiments/sachi/model/` (`stage1.py`, `calibrate.py`, `decide.py`) | the early scripts behind `ber.model` | **on main, not in B**. Nothing in `experiments/ameya/model-v1` or `experiments/bakshi/box` imports it. | [chat:sachi/web-3 2026-09-29 00:45] |
| `make_dev_features.py`, `run_dev.py`, `run_real.py` | dev-kit feature builder and the dev-sample runners for v0 | **on main, not in B** (file names seen on the box listing) | [chat:sachi/web-1 2026-09-25 17:07] |
| Three gate records in `docs/decisions/` | `2026-09-25_1731_gate-g6-dp-vs-threshold.md` (holds my 18:00 pipeline-stage update and my 20:55 re-run on model v2 probabilities), `2026-09-25_2103_gate-g4-stage2.md`, `2026-09-25_2111_gate-name-uniqueness.md` | on main (commits `1537167`, `fd7bf67`, `222fbad`) | [G6 record](../../../docs/decisions/2026-09-25_1731_gate-g6-dp-vs-threshold.md), [G4 record](../../../docs/decisions/2026-09-25_2103_gate-g4-stage2.md), [name-uniqueness record](../../../docs/decisions/2026-09-25_2111_gate-name-uniqueness.md) |
| `error_analysis_v2.py`, `add_name_uniqueness.py`, `check_name_uniqueness.py` | error analysis of model v2 and the name-uniqueness gate's scripts | **on main, not in B** (cited by the G4 and name-uniqueness records) | G4 record |
| `france_probe.py` | script that empties every French S1 in a matching file, for the France-emptied upload | **not in git**: not on main and in no commit on any branch (checked 4 Oct). The assistant in my 25 Sep chat said it was in my commit; git does not support that. Who built the France-emptied upload: see Ameya's records. | [chat:sachi/web-1 2026-09-25 23:33] |
| Handover `docs/handover/2026-09-26_1800_sachi_llm-cross-encoder.md` | handover for the Qwen cross-encoder | on main. **No model-v0 handover and no `docs/status/sachi.md` exist on main** (checked 4 Oct); [PR #17]'s checklist says the v0 handover was "not included" | `git ls-tree`, [PR #17] |
| `loco_groups.py`, `loco_profile.py` | leave-one-country-out studies of feature groups and edit-profile features | **on main, not in B** | [chat:sachi/web-3 2026-09-26 22:00] |
| `france_discover.py`, `france_hypotheses.py`, `france_hyp_split.py` | label-free pattern discovery on France kit v1 | **on main, not in B** | same |
| `ce_compare.py` | compares e5-small and e5-base as the cross-encoder | **on main, not in B** | same |
| `ce_llm.py` | Qwen2.5 LoRA sequence classifier on the uncertain band, same band, folds and output as the e5 trainer | **in Composite B**. One commit on main ([commit 5bff1e7], 2026-09-26 23:37 per Ameya). Imported unchanged by `ce_llm_st.py`. | [issue #66], [chat:sachi/web-3 2026-09-29 00:35] |
| `reproduce_v7sq.sh` | script rebuilding the v7sq model, adapted from `reproduce_v7nst.sh` | **unmerged**. Pushed to `ameya/final-stack` ([commit 99a404d], 2026-09-27 before 08:41). Later dropped from the branch by Ameya ([commit 21bf128]). Bakshi's `reproduce.sh` replaced it. | [chat:sachi/web-3 2026-09-27 08:41] |
| Package drafts in `docs/package/` (`reproduce_v6all.sh`, `reproduce_v5all.sh`, README, requirements, template) | first reproduction drafts | superseded by Bakshi's final package | [chat:sachi/web-2 2026-09-26] |
| `size_bias_owner.py`, `tie_audit.py`, `street_swap.py` | three labelled audits on France kit v1 | **on main, not in B**. Merged 2026-09-29 after my first PR ([PR #67]) merged with no files; the scripts came in a second PR. | [issue #66], [chat:sachi/web-3 2026-09-29] |
| `synth_fr.py`, `ce_synth.py` | synthetic-French generator and cross-encoder trainer | **on main, not in B**. `ce_synth.py` has a one-line fix. Superseded by Ameya's `ce_synth2.py` and synth3. | [issue #63], [chat:sachi/web-3 2026-09-27] |

## 2. What Sachi originated

- **The LLM cross-encoder in the pipeline.** I proposed a LoRA-tuned Qwen2.5-1.5B pair classifier, in the same band and
  fold format as `ce_box.py`, so Ameya could import it as one more cross-encoder. Ameya made it `qst` and added
  self-training on France ([chat:sachi/web-3 2026-09-26 22:30]; `ce_llm_st.py` docstring). Bakshi used the same recipe for the 7B.
  I did not propose the 7B re-check of confident predictions or the use of the 7B in stage 2.
- **Synthetic French supervision.** The idea of building labelled French pairs from real French S1 text and the
  generator's measured operations. Ameya made it the day's priority and corrected the generator.
- **The e5-small vs e5-base check.** I ran it. Ameya's own H100 runs later covered e5-base and e5-large at scale.

## 3. What Sachi checked for the team

- Confirmed `ce_llm.py` on main is the version used, and that nothing in `ber/model` or `experiments/sachi/model`
  is imported by the final chain ([issue #66] items A, B).
- Verified the Hugging Face revisions of Qwen/Qwen2.5-1.5B and intfloat/multilingual-e5-large (see `numbers.md`).
- On 2026-10-03 (night) checked that the two TSVs in the `final_zip` Drive folder match the Composite B hashes.
  I did not open the submission ZIP itself.
- Ran three labelled audits whose results the documentation cites (see `experiments.md`: S-X-09, S-X-11, S-X-13).

## 4. What Sachi did not do

- Did not write the final pipeline stages (Ameya's `experiments/ameya/model-v1`) or the 7B training, re-check and
  composition code (Bakshi's `experiments/bakshi/box`).
- Did not run the ported v3 chain on real data before the final chain was settled (the [PR #27] draft says synthetic data only), and the submission used Ameya's own `experiments/ameya/model-v1` chain. Whether the port was ever validated on full features: unknown.
- Did not write a model-v0 handover or a status file (see the table above).
- Did not finish the Qwen2.5-1.5B run (see S-X-07) or any 7B training that reached a result.

## 5. Mistakes that cost something

Recorded plainly because the jury asks about limits.

- **Wrong estimator figure.** On 2026-09-27 I said the pc-based cal estimator over-predicted mixmdp's France gain by
  about a third. That was wrong. Ameya corrected it: about 9 percent. The +234e-6 figure was a whole-package prediction ([issue #64]).
- **The pull request that merged empty.** My first PR for the three audit scripts ([PR #67]) merged with no file changes.
  The scripts sat in a local commit on my own `main` and never reached GitHub. A second PR fixed it.
- **A tie-audit artefact.** My first `tie_audit.py` run counted rule-added pairs as model predictions. It showed false
  shares of 0.64 to 0.87 that were not real. See S-X-11.

## 6. My pull requests

Read from the repository's PR list on 4 Oct. All were merged ("merged last week") except the capture. Titles are as listed; which file came in which PR is known only where the title says so.

| PR | title | note |
|---|---|---|
| [PR #16] | feat(model): v0 stage-1 model + threshold decision (#8 #9) | opened by me, merged by Ameya |
| [PR #17] | feat(model): ber.model train/predict/decide stages + ownership fix | opened by Ameya, carries my follow-up commit |
| [PR #27] | feat(model): port v3 (stage 2, legal features, cluster support, all-candidate decision) into ber.model | opened by me |
| [PR #30] | docs(package): reproduce scripts, README, requirements, methodology draft | opened by me |
| [PR #39] | exp(model): LOCO gates (feature groups, edit-profile features), France-kit pattern discovery, e5-base vs e5-small comparison script | opened by me |
| [PR #46] | exp(model): LLM cross-encoder (Qwen2.5-1.5B LoRA), running independently | opened by me; one comment |
| [PR #61] | exp(sachi): synthetic French cross-encoder with correct labels (synth_fr.py + ce_synth.py) | opened by me |
| [PR #67] | exp(sachi): synthetic-French generator/trainer and three France diagnostics (ties, copy counts, street swap) | opened by me; merged with no file changes (see section 5) |
| [PR #68] | exp(sachi): France diagnostics cited in the documentation (three scripts) | opened by me; carried the three audit scripts |
| [PR #82] | docs(kb): Sachi knowledge capture | opened by me; merged on 4 Oct about 12:42, before my later corrections |

The list showed 10 closed PRs of mine and I could see 9 of them (the tenth is below the fold): unknown.
