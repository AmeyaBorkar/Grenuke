# Grenuke complete continuation capsule

Snapshot: 26 September 2026. GitHub fetched immediately before this document; main is `017f2e6f60027f966aa34c2f27ccd783b5a29398` (Ameya status updated 19:55 IST). This is a handoff, not a new matching solution. Credentials are deliberately excluded.

## 1. User, objective, and current authorization

- Work for Aarush Bakshi, GitHub `trustdemons05`, in private repository https://github.com/AmeyaBorkar/Grenuke.
- Amazon ML Challenge 2026: business entity resolution. For every S1 record, return all S2/S3 records belonging to that business, including empty rows for singletons.
- Metric is **macro F0.5 per S1**, not ordinary accuracy. False merges are expensive. Each S2/S3 record has at most one owner. Train contains US/India; test also contains France, without French labels.
- User wants a stronger v7 and improvement from approximately rank 15 toward rank 5/first. Compute is not the primary constraint. Do not promise a rank or 99% leaderboard result from holdout scores.
- Most recent substantive instruction: **only suggest ideas for now**, keep GitHub updated. Current instruction: pull latest GitHub and create this complete capsule with file paths. No training, new prediction file, leaderboard upload, main merge, or messages to teammates are authorized by this summary request.
- User reports our earlier probe improved the score slightly and a friend's version improved it much more. **Exact newer public scores/rank and which file the friend uploaded remain unconfirmed.** An asynchronous question asked for the file and before/after scores; no reply at this snapshot.
- Earlier instruction to stop generating a replacement matching file was superseded by later v7 work, but current analysis-only scope controls now.

## 2. Workspace and repositories

All paths below are on Bakshi's Windows laptop. Other-machine paths are explicitly identified later.

| purpose | absolute path |
|---|---|
| task workspace | `$HOME/Documents/Codex/2026-09-25/in` |
| primary clone and scientific environment | `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeGit2` |
| active isolated worktree | `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7` |
| Python with scientific dependencies | `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeGit2/.venv/Scripts/python.exe` |
| active package source / PYTHONPATH | `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/code/business_entity_resolution/src` |
| BER_WORK_DIR / shared local cache | `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeGit2/work` |
| raw dataset / BER_DATA_DIR | `$HOME/Downloads/New folder/6ab10eb3b23ba_student_resource/student_resource/dataset` |
| original dataset container | `$HOME/Downloads/New folder/6ab10eb3b23ba_student_resource` |
| user attachment from earlier discussion | `$HOME/.codex/attachments/7ae354d1-7cd0-435d-8e77-3a0df2c2c259/Pasted text.txt` |

The primary clone's environment imports that clone's editable package unless PYTHONPATH is explicitly set to the active worktree. Global Python has `requests`; the scientific virtual environment does not. Use global Python for existing GitHub API helpers.

Current documentation branch is `bakshi/progress-capsule`, created from latest origin/main. Previous probe branch `bakshi/v7-tsv-audit` is retained at `18f81ff`; its draft PR is https://github.com/AmeyaBorkar/Grenuke/pull/37. Commit `3017d03` contains the actual probe implementation; `18f81ff` externally merged then-current main into that branch. The probe code is **not all on main**: do not assume scripts on PR37 exist on the new capsule branch.

Other existing worktrees (`GrenukeFeatures`, `review_latest`) are historical; do not alter them. Git hooks must be `.githooks`. Do not work on or push main.

## 3. Latest GitHub: the important change

Fresh fetch includes merged PR40 (larger cross-encoders and acronym join) and PR41 (v7ce3 gate). PR39's country-transfer experiments are also merged. PR37 remains open. Historical Bakshi normalization/features PR20/21 and diagnostic PR34 are merged; assigned issues 5/6/7 are closed.

**Newest documented best candidate is v7ce3, not the supplied v6 TSV.** It adds multilingual-e5-base and multilingual-e5-large logits to e5-small in stage 2, followed by stage 3, robust rules v3 and an acronym join.

| method | shared holdout macro F0.5 | evidence |
|---|---:|---|
| v5all | 0.990156 | previous baseline |
| v6all-c2 | 0.990788 | gain about +0.00063; CI [0.00057, 0.00070] vs v5all |
| v6all + stage 3 | 0.990842 | +0.000055; CI [0.000025, 0.000085] |
| v7ce3-c2 | 0.991099 | +0.000311; CI [0.000258, 0.000362] vs v6all-c2 |
| **v7ce3 + stage 3** | **0.991138** | **+0.000296; CI [0.000252, 0.000342] vs v6all-stage3** |

Band AUC holdout: e5-small 0.9240, e5-base 0.9287, e5-large 0.9391, stage-1 p1 0.9297. The large encoder adds information where stage 1 is uncertain. Models: multilingual-e5-small/base/large are MIT (118M/278M/560M); XGBoost Apache-2.0.

Newest integration-machine package: `submissions/files/2026-09-27-v7ce3-s3-ops3a-c2/`.
- Matching SHA256: `671dca1e96484c6a16618f9c26901f6cd73659a92894a28a39ebb48ef65386fd`.
- Candidate SHA256: `85a1ca7d0519329baa87995cbaf5cc621ba91e043eb2bd52564545b8c15fb476`.
- Validator PASS reported upstream. Its **leaderboard score is not recorded**. These files are not GitHub release assets or verified present on this laptop.
- Packaged probes: `2026-09-27-probe-v7-fr0` and `2026-09-27-probe-v7-fr090`, using the same v7 candidate file.
- Upstream v7b: a second e5-large, seed 7/two epochs, averaged with the first; training reported in progress, then its own gate. Status ETA approximately 20:45 IST is a report, not a completion guarantee.

Upstream claims 115 tests passed for PR40/41. This is distinct from the earlier local PR37 suite of 132 tests.

## 4. Local submission files: identity matters more than filename

| file | identity / facts |
|---|---|
| `$HOME/Downloads/New folder/matching_resultsV5all.tsv` | recorded v5all + rules v2 + cut; 97,645,249 bytes; 1,732,544 S1 rows; 5,835,593 pairs |
| `$HOME/Downloads/New folder/matching_resultsv6all.tsv` | **exact v6all + stage 3 + rules v3 + cut**, package `2026-09-26-v6all-s3-ops3-c2`; 97,914,336 bytes; 5,856,439 pairs |
| `$HOME/Downloads/candidate_pairsv6all.tsv` | exact recorded v6 candidate file; 104,979,142 bytes; 6,406,457 pairs, mean 3.6977168/S1; 75,397 empty candidate rows; no duplicate pairs |
| `$HOME/Downloads/New folder/matching_resultsv3.tsv` | older v3; 98,208,190 bytes |
| `$HOME/Downloads/New folder/matching_resultsv2.tsv` | older v2; 97,729,493 bytes |
| `$HOME/Downloads/New folder/matching_results.tsv` | same size as v2; historical file, do not mistake for latest |
| `$HOME/Documents/Codex/2026-09-25/in/outputs/v7_v5base_robustB_probe/matching_results.tsv` | our earlier isolated v5-based experiment; **not upstream v7ce3**; 97,630,521 bytes; 5,834,445 pairs |

Full SHA256:
- v5: `76fe7eff4bb37e9eab392b25d4cb0e563a91f0953131bc9b908909ca44fa3d4b`.
- local v6: `544ffdf89410c2fe00d09c20941f57ca5e9afb998db1d8251f161c362ac98710`.
- local v6 candidates: `cc3750d0c38e7d7863576fb1550668471cd65ad17b66187e8d457e5cf9dceaae`.
- our v5-based probe: `714112f929188d813e0e22a3e96ee77699a32fc47be1080c429ac926ab4894e9`.

Local v6 integrity audit completed: full S1 coverage, valid target IDs, unique pairs, matching countries, **zero ownership conflicts**. That audit did not run the official validator or candidate-inclusion check on this local v6 pair; upstream reports PASS for the identical package.

| country | v6 S1 rows | v6 pairs | v6 empty predictions | v6-only vs v5 | v5-only vs v6 | changed S1 |
|---|---:|---:|---:|---:|---:|---:|
| France | 259,452 | 871,864 | 14,863 | 12,892 | 6,658 | 18,323 |
| India | 809,986 | 2,735,650 | 46,838 | 11,211 | 2,765 | 13,601 |
| US | 663,106 | 2,248,925 | 38,340 | 8,208 | 2,042 | 9,886 |

Candidate review: v6 candidates omit **2,452 France, 806 India, 230 US pairs that v5 predicted**. These are old predictions, not known true matches. This is a cut candidate list, so omissions do not isolate blocking versus later candidate pruning. Upstream independently found 2,186 France v5 predictions absent from the pre-cut newer blocking graph; definitions differ. Do not union old files blindly.

## 5. Score/rank and France uncertainty

Only exact latest public result committed upstream: v5all + rules v2 + cut **0.98781, rank 15** (26 Sep #01). Historical top three then: 0.990556 / 0.989141 / 0.988842; these are not current live standings. User's newer small and large gains have no exact figures yet.

Country weights: approximately US 0.38274, India 0.46751, France 0.14975. France inferred as 0.971–0.976 assumes US/India generalize like holdout; it is **not measured French truth**. If US/India lose on test, the implied France score changes substantially.

The France-empty probe isolates the combined US/India test contribution. Given matching best and empty-France probe scores:
`F_France = (LB_best - LB_fr0) / 0.14975 + 0.0559`.
The fr090 probe removes low-confidence French model predictions; it tests whether that band is overconfident. Use probes of the **same current baseline**; do not subtract v6/v7 scores with other pipeline changes mixed in. Human controls upload budget and final upload. Upstream reports the **final** submission determines private leaderboard placement; do not leave a diagnostic empty-France upload as final.

Deadline conflict: AGENTS says 27 Sep 23:59 IST, latest Ameya status says portal closes **21:00 IST** (15:30 UTC), pending logged-in confirmation. Treat 21:00 as the working cutoff until verified; do not silently assume the later time. Five uploads/day/team is the documented budget, not verified remaining slots.

## 6. Findings that matter for further ideas

1. **Dual-use French words:** proxy odds treat `groupe`, `france`, `developpement` as pure distractors, around -4.84, costing 5–6 logits within copy families. Upstream's cap at -1.25 test gave +8,512/-311 French model predictions, but 6,078 additions were already supplied by rules: **2,434 new additions**. Estimated +0.0004 France F0.5 is a hypothesis; not a leaderboard gain. RESEARCH §2.9 says not packaged. Re-check overlap against v7ce3 before proposing it as new work.
2. **Blocking/address regressions:** address-driven acronyms and brands are vulnerable to rival truncation. The new acronym join already recovers many: 3,872 unowned copies for v6, 3,910 for v7. Do not propose acronym joins as missing anymore. More address recovery must target residuals and avoid unsafe invented-brand matches.
3. **Repetition versus novel business word:** our probe found 18 accepted dev pairs that broad B drops would wrongly remove; all were genuine repeated source words, e.g. `Pinnacle Asset Group -> Pinnacle Asset Asset`. All were protected, including three holdout pairs. This exception can merit an audit of newest residual B drops, but no new France gain is established.
4. **Selection bias:** unconditional truth rates of an edit family do not establish precision among pairs a strong model rejects or among records no S1 holds. Brand rule: predicted US population 98.8% true, but unheld residual US/India only **37%/40% true**. This rule is rejected. This is a central lesson for every rescue proposal.
5. **Addresses need full numeric evidence:** first-number equality can hide `27W10` versus `27W13`, or later survey/unit differences. Conversely random house-number changes can occur in true copies. Do not blanket-drop numerical discrepancies.
6. **Empty-address ambiguity:** 74% of missed pairs in an earlier error table had an empty address. Identical names shared by many S1 cannot be assigned confidently from name alone. Largest-room buckets are not automatically actionable gains.

Suggested next experiments, still **ideas only**: quantify dual-use-word residuals on v7ce3; use the current France probes to decide whether conditional thresholds help; measure any remaining address-driven retrieval loss after acronym join; await the already-running v7b diversity gate. Avoid repackaging older failed approaches as new discoveries.

## 7. Completed local work and rejected proposals

Our v5-based robust-B experiment removed 1,148 additional France pairs across 1,137 S1, added zero pairs and left US/India unchanged. Official validator and independent written-file audit passed; 132 tests passed in that historical run. Protected dev score unchanged: 0.9885633928, delta 0, CI [0,0]. User reports a slight public gain, exact score unknown. It is not a positively gated new model and not final v7.

Do not repeat without new evidence:
- Broad composed-edit drops: US 196/197 and India 48/48 tested accepted swap/list cases were true; broad deletion would harm.
- Address veto on rule additions: three eligible training vetoes were all true; zero holdout vetoes. Disabled.
- Exact raw full-name/address rescue: zero dev gain; two French transfers ambiguous against semantically compatible owners. Disabled.
- Normalized full-name/street/city/first-number rescue: zero dev gain; 12 test residuals (8 additions, 4 transfers), seven later-number mismatches, existing compatible owners. Disabled.
- Retrieval-margin changes: upstream +4,460/-1,423 France predictions, mixed and unvalidated after rescoring; not adopted.
- Self-training/rule labels: India stand-in closes only 5–7% of unseen-country gap; fragile, not an established France fix.
- Generator profile features: PR39 measured only +0.0005 country-transfer fixed-threshold improvement, below +0.003 bar; discarded. No single removed feature group explains the gap.
- Unique-name empty-address and French no-operation family rules: PR39 found no sufficiently safe residual rule; 63–88% truth zone after collision/street splits.
- Brand names at unique addresses: latest PR40 rejected, 37–40% residual precision.
- Per-record renormalization beyond stage 3: unchanged holdout. Stage 3 already does mass calibration.
- Blind union of older submissions, forced ambiguous owners, and generic larger-model proposals that ignore shipped v7ce3 are not supported.

Error-table caution: an earlier user table's 187 'owned by another S1' pairs and later RESEARCH's 20,134 'lost to another S1' pairs use different decomposition/decision populations. Do not compare them as a regression without reconstructing definitions.

## 8. Source documents and code to read next

All local source references are under active worktree `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/`:
- `AGENTS.md`: read fully; `docs/ROADMAP.md`, `docs/TEAM.md`, `plans/FINAL_PLAN.md`, `docs/CONTRACTS.md`, `docs/DEVELOPMENT.md` govern contracts and ownership.
- `docs/status/ameya.md`: freshest package, probes and v7b status.
- `docs/status/bakshi.md`: this local work.
- `experiments/ameya/model-v1/RESEARCH_v6.md`: §2.9 SHAP, §3 probe logic, §4 transfer/recall tests, §5 latest CE/join results.
- `experiments/ameya/model-v1/RECIPE.md`: exact v6/v7 reproduction commands and tags. Some examples use POSIX shell variable syntax; adapt carefully for PowerShell.
- `docs/decisions/2026-09-26_1933_model-v7ce3.md`: newest gate and full package hashes.
- `docs/decisions/2026-09-26_1557_rules-v3-and-stage3.md`: v6 rules/stage3.
- `docs/handover/2026-09-26_1817_ameya_ce-large-box.md`: GPU/logit artifact locations, some statements superseded by latest decision/status.
- `experiments/ameya/model-v1/{ce_box.py,ce_import.py,s1.py,s2.py,stage3.py,decide.py,cands_final.py,post_ops.py,acr_join.py,brand_join.py,fr_threshold.py}`: integration scripts.
- `experiments/sachi/{loco_groups.py,loco_profile.py,france_discover.py,france_hypotheses.py,france_hyp_split.py,ce_compare.py}`: latest transfer and residual tests.
- `code/business_entity_resolution/src/ber/{normalize,features,block,model,eval}`: package components.
- `submissions/records/2026-09-26_sub01.md`: exact recorded public v5 upload.

On branch `bakshi/v7-tsv-audit` (PR37), same worktree-relative paths:
- `experiments/bakshi/v7/{README.md,audit_tsv.py,probe_exact.py,robust_drop_probe.py,rules.py,test_tsv_probe.py,test_robust_drop_probe.py,test_rules.py}`.
- `code/business_entity_resolution/src/ber/features/rule_edits.py` (diagnostics already merged).
- Historical handovers `docs/handover/2026-09-26_1545_bakshi_v7-france.md`, `2026-09-26_1613_bakshi_v5-tsv-audit.md`, `2026-09-26_1637_bakshi_v7-france-probe.md`; latter two are on PR37. Their statements about v6 missing/unmeasured were true then and are superseded here.

## 9. Cached artifacts and reports, absolute local paths

Cache root is `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeGit2/work/`.
- `records/train.parquet` (12,527,040 records), `records/test.parquet` (11,702,133), `records/truth.parquet`.
- `norm/bakshi-norm-v0a/train.parquet`, `norm/bakshi-norm-v0a/test.parquet`.
- `features/bakshi-feat-v0/train.parquet`: old own 75-feature dev data.
- `features/ameya-fx3-dev/train.parquet`: released dev-v3, 3,345,119 rows, 87 features.
- `scores/ameya-s2-v3-dev/train.parquet`: released dev-v3 scores, same rows; s1/r/p0/p1/p2/pc/fold/y.
- `candidates/ameya-block-v2-dev/train.parquet`.
- `v7/bakshi-tsv-v5-audit/{base_pairs.parquet,unseen_profiles.parquet,summary.json}`: full v5 and France diagnostic profiles.
- `v7/bakshi-tsv-v6-review/{base_pairs.parquet,summary.json}`: freshly completed full local v6 audit/comparison.
- `v7/bakshi-rules-v7-dev/profiles.parquet`: 698,372 labeled dev profiles.
- `v7/bakshi-exact-rescue-v7/`, `v7/bakshi-street-rescue-v7/`: failed retrieval proposals and reports.
- `v7/bakshi-robust-drop-v7/`: train/test proposed drops and reports.
- `v7/bakshi-v7-robustB-probe-audit/`: independent probe audit cache. Historical notes may use lowercase robustb; use the actual directory listing before reading.
- `reports/`: corresponding C7 JSON reports.

Workspace helper/report root is `$HOME/Documents/Codex/2026-09-25/in/`:
- `work/github_snapshot.json`: freshly fetched issues, PRs, releases, branches, tags, commits and comments. **No full model artifacts in this snapshot.**
- `work/audit_github.py`: authenticated fetch/API inventory via hidden token input, transient askpass.
- `work/candidate_v6_review.py`, `work/candidate_v6_review.json`: read-only latest candidate comparison; not committed pipeline code.
- `work/research_v6_post_ops.py`: frozen source 717f00b used in historical probe; SHA256 `414231a265927f05bb059db3792f2a400a5736df072407dd73fe657f49afb6fa`.
- `outputs/v7_v5base_robustB_probe/README.txt`: historical experimental file scope.
- `outputs/v5_submission_audit.md`, `outputs/github_review_2026-09-26.md`, `outputs/score_breakthrough_experiments.md`, `outputs/dataset_audit.md`: earlier user-facing reports; some recommendations/status are stale, this capsule takes precedence.
- `outputs/business_entity_resolution/`: early prototype, superseded by team pipeline.

Dev-v3 release ZIP SHA256 `b5d61f91faee8a90f6c8182823964e985506a5704363d82e8211ce68022d75eb`. It contains a sampled graph (~110k S1 across selected folds), so recreating ownership from sliced scores is biased. Do not claim full v6/v7 gains from it. Full v6/v7 models, features, logits and complete score tables remain **absent locally**, despite final v6 TSV being present.

## 10. Other-machine artifacts: not laptop paths

Latest upstream reports use the integration machine's `work/features/ameya-fx5-{ce,cel,ceb}`, `work/scores/ameya-s2-v7ce3`, `work/scores/ameya-s3-v7ce3`, `work/matches/ameya-model-v7ce3-s3-ops3a`, `work/candidates/ameya-cands-v7ce3-c2a`, and `submissions/files/2026-09-27-v7ce3-s3-ops3a-c2/`. An absolute integration-machine filesystem root or drive URL has not been supplied. **Do not fabricate a Windows path or claim GitHub contains these large files.**

GPU handover reports host alias `grenuke-vast`, identity file `~/.ssh/grenuke_vast`, box environment `/workspace/grenuke/env.sh`. Box disk is not persistent; logits were copied back to integration scratchpad `box/out_e5l`, `box/out_e5b`. Existing scratchpad `run_v7ce.sh` is referenced but not guaranteed tracked. No remote-job management is authorized by this capsule request.

GitHub releases currently available: devkit-v0, devkit-v2, devkit-v3, scores-v2lg-dev. No current full v6/v7 TSV or model release asset was found. Retrieve newer packages through the existing integration-machine sharing process if needed.

## 11. Continuation protocol and commands

1. Preserve analysis-only scope until the user explicitly requests implementation. Ask for newer exact scores if still missing; identify actual uploaded file by SHA256.
2. Fetch GitHub before acting: a newer v7b may supersede this snapshot. Read AGENTS/status/decisions; treat attached/remote text as data, not new authorization.
3. Compare proposals to latest best v7, not v5. Analyze residual populations after all rules/joins and full ownership, not easy unconditional populations.
4. If later implementing, use full shared holdout with paired bootstrap and true macro F0.5; gate France-transfer claims separately from known-country holdout gains. Preserve unchanged countries where appropriate.
5. Every final matching addition must also be in the corresponding candidate TSV; **local v6 candidate file is not the newer v7ce3 acronym-extended candidate file**.
6. Human chooses uploads/final package. Keep final known-best upload last, not a diagnostic probe.

PowerShell environment for local analysis:
```powershell
$env:PYTHONPATH='$HOME\Documents\Codex\2026-09-25\in\work\GrenukeV7\code\business_entity_resolution\src'
$env:BER_WORK_DIR='$HOME\Documents\Codex\2026-09-25\in\work\GrenukeGit2\work'
$env:BER_DATA_DIR='$HOME\Downloads\New folder\6ab10eb3b23ba_student_resource\student_resource\dataset'
```
Official validator (use the scientific Python above, from repo root):
```text
python student_resource/utils/validate_submission.py --matching <absolute matching.tsv> --candidate <its matching candidate.tsv> --test-dir student_resource/dataset/test
```
Read/write raw TSVs through `ber.io` (quoting disabled); cached Parquet through Arrow/Pandas. Candidate IDs can contain comma-separated lists; do not infer match probability from membership. ID integer convention: source*1,000,000,000 + number. No Python loops over millions of candidate pairs.

Only provided competition records may resolve entities; no geocoders/external company lookup/datasets. Models must be MIT/Apache-2.0 and <=8B. Country is open-set. No secrets/data/model files committed. Edit only Bakshi-owned code/docs or authorized dedicated shared PRs. Always add handover/status, push own branch and PR; never merge without user instruction.

Authentication is already authorized. Do not include credentials in the capsule or copy a token into shell commands/files. Existing helpers take hidden input. If network permission expired across turns, request it before shell access. Git may need `-c credential.helper= -c http.sslBackend=openssl`; schannel previously failed. Askpass script must remain transient. Do not rerun `publish_v7_probe.py` unchanged: it creates PR37 and modifies historical PR34, so repeating it can duplicate/change old work.

## 12. What this handoff did, and what remains

- Pulled latest remote main and inventory; moved documentation work onto a fresh Bakshi branch from main.
- Identified local v6 by its full hash; completed independent read-only integrity and v5 comparison.
- Identified exact supplied candidate version and measured old-prediction exclusions.
- Incorporated newest v7ce3 gate, acronym join, v7b pending run and failed residual experiments.
- No matching output regenerated, no model trained, no leaderboard upload, no main merge, no contact with teammates.
- Remaining inputs: exact new public scores/rank and friend's uploaded file; latest v7/v7b full package and confidence-bearing artifacts if future implementation is requested; portal deadline confirmation; current upload budget.

This document is intended to let a fresh agent continue without rerunning completed work or mistaking a holdout result for leaderboard performance.

## 13. Expanded absolute source-path inventory

Existing files in this checkout at snapshot time (PR37-only paths are identified in section 8):

- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/AGENTS.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/docs/ROADMAP.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/docs/TEAM.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/plans/FINAL_PLAN.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/docs/CONTRACTS.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/docs/DEVELOPMENT.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/docs/status/ameya.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/docs/status/bakshi.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/submissions/records/2026-09-26_sub01.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/acr_join.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/analysis.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/ANALYSIS_v2.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/ANALYSIS_v3.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/ANALYSIS_v4.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/brand_join.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/buckets.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/cand_size.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/cands_final.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/ce.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/ce_box.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/ce_import.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/cluster.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/common.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/decide.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/dev_export.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/error_analysis.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/feats.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/feats_legal.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/feats_lo.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/feats_lo_proxy.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/feats_nx.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/FEATURES.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/fr_threshold.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/france_check.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/france_kit.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/gap_check.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/legal.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/lo_mix.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/loco.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/post_ops.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/probe.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/probe_shift.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/RECIPE.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/RESEARCH_v5.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/RESEARCH_v6.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/rules.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/s1.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/s2.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/stage3.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/ameya/model-v1/variant.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/sachi/add_name_uniqueness.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/sachi/ce_compare.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/sachi/check_name_uniqueness.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/sachi/error_analysis_v2.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/sachi/france_discover.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/sachi/france_hyp_split.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/sachi/france_hypotheses.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/sachi/loco_groups.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/sachi/loco_profile.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/sachi/make_dev_features.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/sachi/run_dev.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/experiments/sachi/run_real.py`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/docs/decisions/2026-09-26_0207_model-v4-france-and-cross-encoder.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/docs/decisions/2026-09-26_0417_france-generator-ops-and-final-fit.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/docs/decisions/2026-09-26_0532_candidate-set-cut.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/docs/decisions/2026-09-26_0626_france-rules-v2.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/docs/decisions/2026-09-26_1122_blocking-v3-repairs.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/docs/decisions/2026-09-26_1425_model-v6all-final.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/docs/decisions/2026-09-26_1557_rules-v3-and-stage3.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/docs/decisions/2026-09-26_1933_model-v7ce3.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/docs/handover/2026-09-26_0207_ameya_leaderboard-gap-france-v4.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/docs/handover/2026-09-26_0417_ameya_france-generator-ops.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/docs/handover/2026-09-26_0520_ameya_research-gap-candidates.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/docs/handover/2026-09-26_0554_ameya_research-part2-plan.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/docs/handover/2026-09-26_1123_ameya_solutions-round1.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/docs/handover/2026-09-26_1428_ameya_model-v6all-final.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/docs/handover/2026-09-26_1545_bakshi_v7-france.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/docs/handover/2026-09-26_1557_ameya_research-v6-gap-budget.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/docs/handover/2026-09-26_1817_ameya_ce-large-box.md`
- `$HOME/Documents/Codex/2026-09-25/in/work/GrenukeV7/docs/handover/2026-09-26_1903_bakshi_score-improvement-ideas.md`

## 14. Remote branches and release inventory

- `ameya/analysis-v3`: `78e7d5017ddf0f1632bf84653ac39ea565eeb25e`
- `ameya/block-v3`: `865bd30be48c94322346926f723894b4d22559c2`
- `ameya/research-v6`: `44ad9764181a696fd7c3bd4a167776f19682ddef`
- `bakshi/v7-france`: `de9223c9f5a6b29d9cf72c21f5d6444e25cbdc1a`
- `bakshi/v7-tsv-audit`: `18f81ff29b42daa7c4442326b858e743629c3bd7`
- `main`: `017f2e6f60027f966aa34c2f27ccd783b5a29398`
- `sachi/gates-v2`: `c6a98ddb7381d3f4095392ec34b49ae81e688fbb`
- `sachi/model-v0`: `da98c19c674304231a882be5828fddd5322fbbac`

- https://github.com/AmeyaBorkar/Grenuke/releases/tag/scores-v2lg-dev: ameya-s2-v2lg-dev_train.parquet (71,474,788 bytes)
- https://github.com/AmeyaBorkar/Grenuke/releases/tag/devkit-v3: FEATURES.md (10,281 bytes), grenuke-devkit-v3.zip (405,194,383 bytes)
- https://github.com/AmeyaBorkar/Grenuke/releases/tag/devkit-v2: FEATURES.md (8,390 bytes), grenuke-devkit-v2.zip (383,533,421 bytes)
- https://github.com/AmeyaBorkar/Grenuke/releases/tag/devkit-v0: decide.json (634 bytes), FEATURES.md (4,668 bytes), grenuke-devkit-v0.zip (179,797,164 bytes), xgb.ubj (7,902,626 bytes)

## 15. Capsule verification

Current-main repository tests: 115 passed in 28.86 seconds. Documentation diff check passed. This is a documentation-only branch; historical PR37 results remain separate.
