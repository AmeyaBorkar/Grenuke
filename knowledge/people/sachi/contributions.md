# Sachi: contributions

Summary: what Sachi built, owned, checked and originated, with the state of each piece in the repo. The final
pipeline (Composite B) used one piece of this work directly: the LoRA cross-encoder code. The rest was baseline work,
gates, diagnostics and packaging help.

Status labels: **in Composite B** (used by the final chain), **on main, not in B** (merged, but unused by the final
chain), **unmerged or unknown** (state not confirmed).

## 1. What Sachi built

| piece | what it is | state | source |
|---|---|---|---|
| `ber.model` train, predict, decide stages and the ownership fix | v0 baseline: stage-1 XGBoost, isotonic calibration, argmax ownership, threshold decision | **on main, not in B**. Merged 2026-09-25 ([commit fd7bf67]). Not imported by the final chain. | [issue #66], [chat:sachi/web-3 2026-09-29 00:40] |
| `experiments/sachi/model/` (`stage1.py`, `calibrate.py`, `decide.py`) | the early scripts behind `ber.model` | **on main, not in B**. Nothing in `experiments/ameya/model-v1` or `experiments/bakshi/box` imports it. | [chat:sachi/web-3 2026-09-29 00:45] |
| `make_dev_features.py`, `run_dev.py`, `run_real.py` | dev-kit feature builder and the dev-sample runners for v0 | **on main, not in B** (file names seen on the box listing) | [chat:sachi/web-1 2026-09-25 17:07] |
| Gate records G4, G6 on v2, name-uniqueness rejection | paired-bootstrap gate records in `docs/decisions/` | on main (file names unknown to me) | [chat:sachi/web-1 2026-09-25 18:03] |
| `france_probe.py` | script that empties every French S1 in a matching file, for the France-emptied upload | state unknown (said to be "in my commit") | [chat:sachi/web-1 2026-09-25 18:03] |
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
- Did not port stage 2 or the expected-F0.5 decision into `ber.model`, though Ameya's agent asked on 2026-09-25 23:29.
  The final chain stayed in `experiments/ameya/model-v1` ([chat:sachi/web-1 2026-09-25 23:29]).
- Did not finish the Qwen2.5-1.5B run (see S-X-07) or any 7B training that reached a result.

## 5. Mistakes that cost something

Recorded plainly because the jury asks about limits.

- **Wrong estimator figure.** On 2026-09-27 I said the pc-based cal estimator over-predicted mixmdp's France gain by
  about a third. That was wrong. Ameya corrected it: about 9 percent. The +234e-6 figure was a whole-package prediction ([issue #64]).
- **The pull request that merged empty.** My first PR for the three audit scripts ([PR #67]) merged with no file changes.
  The scripts sat in a local commit on my own `main` and never reached GitHub. A second PR fixed it.
- **A tie-audit artefact.** My first `tie_audit.py` run counted rule-added pairs as model predictions. It showed false
  shares of 0.64 to 0.87 that were not real. See S-X-11.
