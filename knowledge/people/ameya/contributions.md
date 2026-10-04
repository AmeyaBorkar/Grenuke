# Contributions: ameya

What Ameya built, owned, originated and reviewed, so the deck and the Q&A credit everyone accurately. Compiled by the agent for Ameya from his three sessions, the 26 sub-agent logs and the repository records.

**Key.** Ameya = done by Ameya himself (decisions, orders, uploads, GPU rentals, reviews). Agent for Ameya = his Claude Code sessions and sub-agents, under his direction. "On Sachi's / Bakshi's X" = built on their idea or code. Times IST. Final? = in the submitted ZIP (Composite B), or it decided what the ZIP contains. `model-v1/` = `experiments/ameya/model-v1/`. "e-6" = millionths of F0.5. The research documents do not separate Ameya's ideas from his agents' ([R]).

## Built or owned

| what | credit | when | where (paths, PRs) | final? |
|---|---|---|---|---|
| Repository rules, hooks, CI, shared `ber` package (io, ids, metric, 25% holdout, gate CLI), pipeline skeleton | agent for Ameya, at his request (skeleton: research session) | 25 Sep 12:40–15:40 | `AGENTS.md`, `.githooks/`, `.github/`, `code/business_entity_resolution/src/ber/`; PRs #1, #4, #14 | partly: `ber` is in the ZIP; holdout and gates judged every number |
| Plan A | agent for Ameya from his brief; Ameya owns it | 25 Sep 13:02 | `plans/ameya/PLAN.md` | base of the final plan; dense GPU retrieval never built |
| Final plan = Plan A + nine Plan B grafts (gates G1–G13, paired bootstrap, ties to the simpler option) | Ameya decided (14:15); research-session agent ran the data checks and wrote it; the grafts are Sachi's | 25 Sep 13:36–14:29 | `plans/FINAL_PLAN.md`, `plans/DECISION.md`, `experiments/ameya/plan-checks/`; PR #3 | process: yes, every gate |
| Contracts C0–C10, developer guide, roadmap, team and changelog files; issues #5–#13; dev kits, France kit, reproduction answers for Sachi | agent for Ameya; Ameya passed the files on | 25 Sep 14:15 → 26 Sep 12:22 | `docs/CONTRACTS.md`, `docs/DEVELOPMENT.md`; PRs #3, #14, #19, #29, #31 | no (enabled teammates) |
| Blocking v0–v3: token view, names-only view, compounds, repairs, per country | agent for Ameya (v3 repairs: fork a43953b5); "name-only view only for short addresses" is Sachi's Plan B rule | 25 Sep 15:27 → 26 Sep 06:25 | `src/ber/block/`, `model-v1/cands_final.py`; PRs #15, #18, #22, #28 | yes |
| Pair features: context, look-alike word odds, legal-form relations, signed house numbers, cluster support | agent for Ameya | 25 Sep 17:30 → 26 Sep 14:25 | `model-v1/feats.py`, `feats_lo.py`, `feats_legal.py`, `legal.py`, `feats_nx.py`, `cluster.py`; PRs #18, #22, #28 | yes |
| XGBoost stages 0–2, isotonic calibration, per-S1 set selection, stage 3 | agent for Ameya (stage 3: fork a2066847); the rule "set selection must beat a tuned threshold" (G6) is Sachi's | 25 Sep 17:30 → 26 Sep 06:27 | `model-v1/s1.py`, `s2.py`, `decide.py`, `stage3.py`; PRs #18, #22, #28 | yes |
| France fixes: label-free proxy odds, no bitmasks, generator rules (op A / op B), acronym join, French keys | agent for Ameya (generator catalogue and LOCO anatomy: sub-agents afe57301, a4957c58); LOCO as a stand-in country is Sachi's Plan B idea | 26 Sep 01:59 → 15:57 | `model-v1/feats_lo_proxy.py`, `lo_mix.py`, `post_ops.py`, `acr_join.py`, `loco.py`; PRs #23, #24, #26, #35, #40 | yes |
| Candidate cut, 4.68 → 3.70 per S1 [M] | agent for Ameya, after the organisers' rule that Ameya relayed (05:10) | 26 Sep 05:32 | `model-v1/cands_final.py`, `docs/decisions/2026-09-26_0532_candidate-set-cut.md`; PR #25 | yes |
| Cross-encoders: e5-small local; e5-base/large and bge on rented H100s; z-mean | agent for Ameya; Ameya rented the GPUs | 26 Sep 02:00 → 27 Sep 06:21 | `model-v1/ce.py`, `ce_box.py`, `ce_import.py`, `zmean_ce.py`; PRs #23, #40, #41, #43 | yes |
| French self-training: pseudo-labels, cross-fitting, rules-win guard, guarded round 2 | agent for Ameya (guarded labels: GPU-plan agent a4ea3fde) | 26 Sep 21:17 → 27 Sep 16:40 | `model-v1/pseudo_labels.py`, `pseudo_guard.py`, `s2.py --pseudo`; PRs #43, #47, #65 | yes (round 1: +0.000458 on the public LB [M]) |
| French self-trained Qwen2.5-1.5B cross-encoder `qst` | agent for Ameya, on Sachi's `ce_llm.py`; Ameya's review added the text separator | 26 Sep 23:40 → 27 Sep 06:21 | `model-v1/ce_llm_st.py`, `experiments/sachi/ce_llm.py`; PRs #46, #51 | yes |
| Stacked decision layer `-dpc`: set selection with shift, crowd and phantom terms; acronym, cap, copy and city rules | sub-agents hunt, polish, decide, on Ameya's order (~03:00); agent for Ameya merged and ported | 27 Sep 03:00–06:36 | `model-v1/stack/`, `docs/decisions/2026-09-27_0636_stacked-rules.md`; PR #58 | yes |
| France decision layer; look-alike swap drop | designed by sub-agents (France-diff; error agent); ported by agent for Ameya | 27 Sep 12:12–14:21 | `model-v1/stack/dp_france.py`, `apply_swapsim.py`; PR #65 | yes, in mixmdp; the swap drop's effect is unsettled |
| Per-country composer; mixmdp (v7sq3 US/India + v7sq7wg France) | agent for Ameya; Ameya decided the composition | 27 Sep 12:00–16:40 | `model-v1/stack/compose.py`, `compose3.py`; PR #65; [LB 2026-09-27 #03] | yes: Composite B's France half |
| Bakshi's 7B `q7st` wired into our stage 2 (v7sqq7); his 7B drop extended to US/India | agent for Ameya, on Bakshi's `q7st` and re-check | 27 Sep 17:10–20:43 | `model-v1/RESEARCH_v6.md` §6.19; PRs #62 (Bakshi), #65 | partly: the 310 US/India drops [M] are in; v7sqq7 tied and was not used |
| Synthetic French pairs: ran and fixed Sachi's trainer, re-weighted her generator | agent for Ameya, on Sachi's `synth_fr.py` | 27 Sep 13:50–17:16 | `model-v1/ce_synth2.py`, `synth_fr2.py`, `synth_fr3.py`; PRs #61 (Sachi), #65 | no: rejected for upload |
| Label-free France tools: rule-population AUC, `fhs`, `cal` estimator, size-bias test | agent for Ameya (`cal`: France-diff agent) | 26 Sep 20:00 → 27 Sep 15:18 | `model-v1/rule_pop.py`, `rule_auc.py`, `fhs.py`; `RESEARCH_v6.md` §§6.8, 6.17–6.18 | no: selection tools; their verdicts are in |
| Analyses and records: ANALYSIS_v2–v4, RESEARCH_v5–v6, RECIPE; most decision records and handovers; status file | agent for Ameya | 25–27 Sep | `model-v1/*.md`, `docs/decisions/`, `docs/handover/`, `docs/status/ameya.md` | record only |
| All 15 uploads [R] and what to send; status and decision threads #45, #63, #64, #66, #69, #71, #75 | Ameya (his agent wrote the records) | 25 Sep → 29 Sep | `submissions/records/`, `CHANGELOG.md`, the issues | yes: Composite B is the final submission |
| GPU rentals: three H100 boxes over time, two RTX 5090s | Ameya | 26 Sep ~17:00 → 27 Sep night | none in the repo; cost not recorded | yes: the final cross-encoders trained there |
| Composite B: France half = mixmdp; US/India half and 7B drops = Bakshi's g1w and re-check | Ameya + Bakshi; composed by Bakshi's `compose_tsv.py`, rebuilt by `stack/compose3.py` | 27 Sep 19:47–20:55 | PRs #62, #65; [LB 2026-09-27 #04] | yes: the final submission |
| Final package: France block, as-run scripts, ZIP structure, 7-page methodology and figures, independent ZIP check | agent for Ameya under his feedback; Bakshi's `compositeB.sh` driver and package builder | 29 Sep 00:08–04:09 | `experiments/ameya/final-zip/`, `model-v1/pipeline/france_mixmdp.sh`; PRs #73, #74, #76, #77 | yes |

## Ideas I originated (even if someone else built them)

| idea | credit | when | where (paths, PRs, chat) | final? and what happened |
|---|---|---|---|---|
| The leaderboard gap is France, readable by leaderboard arithmetic | Ameya + main agent; the research session reached the same ~0.93 | 25 Sep 23:45 → 26 Sep 00:33 | `model-v1/RESEARCH_v5.md` §1; handover `2026-09-26_0207` | method, yes: it set the France programme; every upload was read with it |
| Label-free proxy look-alike odds | main agent; first formula from web-research agent ada9694b, replaced in 10 min | 26 Sep 01:59 | `feats_lo_proxy.py`, `lo_mix.py`; PR #23 | yes |
| France rules from the generator's op A / op B | main agent with sub-agents afe57301, a4957c58 | 26 Sep 02:30–04:17 | `post_ops.py`; PRs #24, #26 | yes |
| Rule-population AUC as a label-free France yardstick | main agent | 26 Sep ~20:00 | `rule_pop.py`, `rule_auc.py`; `RESEARCH_v6.md` §6.8 | no: saturated after self-training; replaced by `fhs`, then `cal` |
| One z-scored mean of cross-encoder logits | main agent | 26 Sep 20:59 | `zmean_ce.py`; `RESEARCH_v6.md` §6.6; PR #43 | yes |
| Rent GPUs and work in parallel | Ameya | 26 Sep 16:52 | [chat:ameya/19e315ba 2026-09-26 16:52] | yes: the large cross-encoders trained there |
| Revive self-training for France, with cross-fitting and rules-win | Ameya + main agent; Plan A had listed pseudo-labels as a gated extra; LOCO (Sachi's idea) had rejected it | 26 Sep 21:17 | `RESEARCH_v6.md` §6.7; PR #43 | yes: +0.000458 [M] |
| "Use the same weights, train more on the whole data, lean more on French" → `qst` | Ameya (idea); agent built it on Sachi's `ce_llm.py` | 26 Sep 23:57 | [chat:ameya/19e315ba 2026-09-26 23:57]; `ce_llm_st.py`; PR #51 | yes |
| Stack small verified rules; spin up 2–3 agents; do not discard negligible gains | Ameya's order; hunt, polish, decide found the rules | 27 Sep ~03:00 | `model-v1/stack/`; PR #58 | yes |
| Size-bias test for the French acronyms | main agent; the error agent found the anomaly | 27 Sep 11:38 | `RESEARCH_v6.md` §6.17 | verdict in (keep the acronyms); test not in the ZIP |
| Compose the final per country: best US/India by holdout, best France by leaderboard | Ameya + main agent | 27 Sep ~12:00 | `stack/compose.py`; PR #65 | yes |
| "Same name + number, different street" is both a copy and a decoy: gate the 7B drop, extend it to US/India | Ameya, via his agent, on Bakshi's 7B rejects; Sachi's street-swap check supported it | 27 Sep 18:48–20:43 | `RESEARCH_v6.md` §6.19; issue #64; PR #62 | yes: 840 French + 310 US/India drops [M] |
| Upload Composite B first, as a probe | Ameya with Bakshi | 27 Sep 20:46–20:53 | issue #64; [LB 2026-09-27 #04] | yes: it became the final submission |
| One change per upload, forecast written first, France-only composites | Ameya's practice; agents built the packages | 26–27 Sep | `submissions/records/`; `RESEARCH_v6.md` §§6.17–6.18 | method; it produced the `cal` estimator |
| The candidate file and duplicates look wrong (00:05 critique) | Ameya; the text may be pasted, origin not stated [U] | 26 Sep 00:05 | [chat:ameya/19e315ba 2026-09-26 00:05]; agents a1f88e87, a4fa18c7; PR #25 | yes: candidate file fixed, then cut to 3.70 |

## Reviews, checks and help given

| what (credit) | when | outcome | where | final? |
|---|---|---|---|---|
| Agent for Ameya reviewed Sachi's model v0 and rebased her ownership fix onto an `ameya/` branch, keeping her authorship | 25 Sep ~17:50 | merged; `ber.model` not used by the final chain | PRs #16, #17 | no |
| Agent for Ameya reviewed Bakshi's normalisation (three parsing bugs found) and judged his string features largely redundant with model-v1 | 25 Sep evening | both merged; neither used | PRs #20, #21 | no |
| Ameya's review of Sachi's Qwen LoRA PR: noted the missing separator; merged | 26 Sep 23:40 | her code trains `qst` and `q7st` | PR #46 | yes |
| Ameya's agent reviewed Bakshi's PRs #50, #54, #56; corrected his §6.13-based claims and his bge estimate | 27 Sep 01:00–13:14 | #54: the equal three-way mix stands | PRs #49–#56 | partly: his auditor and builder are in the ZIP |
| Research-session agent refuted two Bakshi claims by measurement: the "lost to another S1" bucket (834 pairs, not 20,134) and the empty-entity rescue (+0.000021, interval includes 0) | 26 Sep evening | both dropped | chat a2a1b62a | no |
| Ameya reviewed Bakshi's methodology (3 factual fixes) and PR #70 (2 accuracy fixes); fixed the package pins himself when #72 had no reply | 29 Sep 01:00–02:00 | applied | PRs #70, #72, #74 | yes |
| Agent for Ameya verified Sachi's `reproduce_v7sq.sh` handoff (385,274 pairs, 0 disagreements) | 27 Sep 08:42 | exact; folded into Bakshi's switch | PR #58 | no |
| Agent for Ameya ran and fixed Sachi's synthetic-French trainer and credited her in the docstrings | 27 Sep 13:50–17:16 | rejected for upload; a synthetic bge corroborated 82% of the 7B drops [M] | `ce_synth2.py`, `synth_fr3.py`; PR #61 | no |
| Agents for Ameya checked every port against its result: stack files byte for byte (the 0.990545 package), Composite B rebuilt by `compose3.py`, the ZIP's France block (871,147 French pairs) | 27–29 Sep | all exact | PRs #58, #65, #73 | yes |
| France-diff agent refereed late candidates and valued Bakshi's variants with `cal` | 27 Sep 10:16–22:31 | recommended B+; the team used the last slot for B7 | `RESEARCH_v6.md` §§6.19–6.20 | no: B7 tied B |
| Agent for Ameya hand-reviewed the 89 French city drops and narrowed the acronym adds to 16; Ameya declined weak recommendations (India count prior, bag4, SHAP fixes) | 27 Sep | simpler options kept | `RESEARCH_v6.md` §§6.16–6.18 | yes |
| Agents for Ameya checked licences (MIT or Apache-2.0, at most 8B; Qwen2.5-3B and jina excluded) and searched top-10 teams' GitHub (none public; code reuse flagged as a risk) | 26–27 Sep | no outside code or data used | sessions c0c64ad6, a2a1b62a | yes |
| Help for teammates: dev kits, France kit, answers to Sachi's five reproduction questions, GPU coordination on Bakshi's boxes, the organisers' update on #45 | 25–27 Sep | Sachi gated on the dev kits; Bakshi built the ZIP | issues #29, #45, #63; PRs #19, #29, #31 | no |

## What I can explain best to the jury

- Why France was the whole gap and how we read it without labels: the leaderboard arithmetic, the bitmask and proxy-odds fixes, the generator's op A / op B, LOCO.
- Self-training: why we rejected it, why we revived it, the guards (rules win, cross-fitting, calibration on labelled rows only), and why a third round lost (−46e-6 against Composite B [M]).
- The metric and the decision layer: the count form (one false merge = four missed copies), the 75% break-even, per-S1 set selection, calibration, and why the programme alone is not significant (+33.2e-6) while the combined layer is (+48.1e-6) [M].
- Blocking and candidate efficiency: per-country search, repairs, 58.4M → 6.41M pairs (3.70 per S1), recall 99.1% before the cut and about 98.2–98.4% after [M].
- How we judged changes: the 549,699-S1 holdout, paired bootstrap, ties to the simpler option, forecasts before uploads, and why estimators built on the model's own probabilities failed on decoys.
- The final choice: one change per upload, why Composite B went first, why B and B7 tie, and what we do not know (which upload the private ranking used).
- Compute and scale: what ran on a 31 GB laptop and what on rented H100s; why the 7B reads only confident predictions (about 27 GPU-hours otherwise [E]).
- Hand over: the 7B training and LoRA settings, the −6 cut-off and its leakage check, g1w and the ZIP driver go to Bakshi; Plan B's tags and gates, the Qwen LoRA code, the synthetic French pairs and the street-swap check go to Sachi.
