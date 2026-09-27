# Final push, 27 Sep: results, candidates and the proposal for the last uploads

Owner: Bakshi. Status at about 19:40 IST. The plan is in `FINAL_PUSH_PLAN.md` and the machines are in `HANDOFF.md`.
Best measured upload so far: **mixmdp, 0.990699** (Ameya). It is +0.000154 over v7sq-dpc (0.990545): US/India +20e-6, France +134e-6.

## 1. What was built (all on our own boxes)

**Rebuild reproduces v7sq-dpc.**
- Blocking gives 66,429,057 train / 58,437,794 test pairs.
- Our band matches Ameya's to 99.9999% (1 missing pair).
- The g0 variant (v7sq recipe, Ameya's cross-encoders remapped by (s1, r)) scores holdout macro F0.5 **0.991261**; v7sq's original was 0.991246.
- g0 vs v7sq-dpc: France changes 4.3 per 1000, US/India about 1.2 per 1000. Validator and strict audit PASS.

**Qwen2.5-7B France cross-encoder `q7st`** (Apache-2.0, 7.6B).
- Recipe: ce_llm_st.py, trained on v7sq-dpc pseudo-labels, one OOF group per H100 via `llm_group.py` / `llm_merge.py`.
- Checkpoints are resumable. The run survived the interruptible box being taken away.
- Holdout AUC **0.9436**, OOF 0.9396. For comparison, e5ls is 0.9439 and qst 0.9381.
- It is not stronger on US/India. Its value is diversity and French rescoring.

**Qwen3-4B-Base `q34st`** (Apache-2.0, 4.0B): merged. Not used in any candidate (no time for a variant).

## 2. Stage-2 variants (US/India holdout macro F0.5, the labelled measure)

| variant | cross-encoder mix | holdout F0.5 | vs g0 |
|---|---|---|---|
| g0 | e5l, qst, e5ls, bge (= v7sq) | 0.991261 | — |
| g1 | + q7st | 0.991276 | +0.000015 |
| **g1w** | + q7st ×2 | **0.991323** | **+0.000062** |
| g1x3 | + q7st ×3 | 0.991322 | +0.000061 (flat) |
| g7only | q7st alone | 0.991286 | +0.000025 |
| gbag | bag of g0, g1, g1w stage 2 | 0.991313 | +0.000052 |

## 3. 7B rescoring of predictions outside the band

94.5% of final predictions have p1 > 0.99, so no cross-encoder ever scored them.

- **Method.** Score them with the q7st adapter (`score_pairs.py`). Check on labelled holdout S1, which no adapter trained on (`rescore_eval.py`).
- **Rule:** drop a predicted pair outside the band when its 7B logit < −6. On the holdout, that bucket is 8% true.
- **Measured effect:** +0.000033 on the holdout sample. Both fixed halves are positive (+0.000022, +0.000043).
  - At t = −4 and above, the effect turns negative, so the rule is kept at −6.
- **Size on test:** 859 French predictions (0.10% of French predictions, **25× the US/India rate** of 0.004%) and 310 US/India predictions.

## 4. Candidates (all: validator PASS, strict audit PASS)

The files are on the laptop under `Downloads/New folder/UPLOAD*`, and in Drive under `grenuke-train-backup/candidates/`.

| candidate | US/India | France | vs mixmdp (France, per 1000) | matching sha256 |
|---|---|---|---|---|
| **Composite B** (upload 1) | g1w − 7B drops | mixmdp − 7B drops | −3.2 (drops only) | `df4bccd7…` |
| **Composite B′** (upload 2) | g1w − 7B drops | g1w-dpcsfq (7B-driven) | 15.3 (+4.7 / −10.6) | `723be333…` |
| Composite A | g1w | mixmdp − French 7B drops | −3.2 | `cb260099…` |
| g1w-dpcsfq | g1w | g1w + swapsim + dp_france + French 7B drops | vs v7sq-dpc 15.8 | `ddb969c4…` |

Predicted: B about 0.9908; B′ 0.9906–0.9910. Composites are built per country group with `compose_tsv.py`. Records never cross countries, so ownership is preserved.

## 5. Proposal for the remaining uploads (superseded)

Superseded by #64: one upload tonight, `mixf2`. It is v7sq3 US + our g1w India + v7sq6r3 France, minus our 7B rejects in all three countries, predicted ~0.99091. Bakshi confirmed it; Composite B is the backup.

The original proposal, kept for the record:

The best upload counts, so every upload is a free shot.

1. **Upload B.** It is the safe step: every component is either leaderboard-proven (mixmdp France) or checked on the labelled holdout (g1w US/India, 7B drops).
2. **Upload B′.** B and B′ have identical US/India, so **the score difference is purely France**. It shows which French direction is right:
   - mixmdp adds French predictions (leaderboard-proven +134e-6 over v7sq-dpc);
   - the 7B-driven France drops them (−10.6 per 1000).
3. **Upload 3 follows the winner.**
   - If B′ > B: the "precise" France (dp_france with SHIFT −0.4, `fr_probe.sh g1w -0.4 frp`).
   - If B > B′: the "inclusive" France (SHIFT +0.8, `frr`), or keep B.
   - Both are built on the pipeline box: `output/g1w/{frp,frr}/`.
4. If upload slots reset at midnight, keep pushing the winning direction.

Open question for Ameya: his calibrated estimator scores the look-alike drop (`apply_swapsim`) at −26.7e-6. B′'s France (g1w-dpcsfq) includes swapsim; B's France is mixmdp's as uploaded.

## 6. Leads checked on labelled data and closed (so nobody repeats them)

| idea | measured | verdict |
|---|---|---|
| Where US/India loses (549,699 holdout S1) | 99.9% of predictions true. Loss is 69% partial misses, 20% S1 missed entirely, 8% FP | recall-bound |
| Missed true pairs (48,509) | 16,455 not candidates; only 237 went to another S1; 15,152 rejected at pc ≈ 0 | — |
| Empty-address + same core name, record left unassigned | 24% true (holdout-only); 17% true when all train S1 compete | decoys; the model already takes the 95%-true unique ones |
| + sibling / same-source evidence | best slice 59% true (193 pairs); break-even ~75% | no rule |
| Empty-S1 rescue (top free candidate) | negative at every pc threshold | DP already optimal |
| Same house number + different street (France's "biggest pattern") | 100% true among US/India *predictions*; the 7B rejects only 0.55–2.5% of the French ones | **corrected by Ameya (#62, #64):** it is both a copy pattern and a decoy pattern. The US/India decoys the model rejects are 0.5% true (7B median −9.9). In France, generic names (median 43 same-name S1) let the decoys through at p1 > 0.99. About 78% of the 859 French 7B drops are this pattern, so the q7 < −6 drop is catching real errors |
| 7B drop at logit −4 / −2 / 0 | −0.000003 … −0.0032 | only −6 is safe |
| 7B weight ×3, 7B alone | flat / lower than ×2 | ×2 kept |
| Drop mining on labelled predictions (7B logit, p1, pc, name/address similarity, house number, name frequency, matches per S1; depth-5 tree fit on half A) | 631,001 predictions, 654 false; one leaf < 70% true (140 pairs), half A +0.000033, **held-out half B −0.000015** | overfit; false positives too thin to isolate beyond the 7B −6 rule |
| 1-to-1 conflict resolution / France match-count histogram matching (external LLM suggestions) | 0 conflicts in every audit; France non-empty 94.21% vs 94.24/94.25%, 3.36 pairs/S1 vs 3.38/3.39 | nothing to fix |

Conclusion: **US/India is at this model family's ceiling.** A team at 0.992 must separate the generator's empty-address decoys better than name+address models do. None of tonight's measurements found a cheap lever of that size.

## 7. Files

- **Scripts:** `score_pairs.py` (7B scoring of any pairs), `rescore_export.py`, `rescore_eval.py`, `compose_tsv.py`, `fr_probe.sh`, plus the earlier `llm_group.py`, `llm_merge.py`, `remap_ce.py`, `phaseA.sh`, `phaseB.sh`, `train_jobs.sh`, `setup.sh`.
- **`analysis/`:** the scripts behind section 6 (run on the pipeline box, from the model dir, with `env.sh`).
- **`ops/`:** the one-off orchestration used tonight:
  - chain resume (s1 `--test-only` after the optional baseline read failed; an empty placeholder `ameya-baseline-v0` is written for report-only comparisons);
  - bagged variant;
  - Qwen3-4B scheduler;
  - rescoring launchers;
  - Drive backup loop.
- No data, parquet, TSV or credentials are committed. Ameya's `stack/` files (including swapsim, compose and dp_france from ameya/final-stack d6c2e38) were used as-is and not committed.

## 8. Leaderboard results (27 Sep evening)

Composite B **0.990879** (best, rank 16); mixf7 0.990833; mixf2 0.990819 (round-3 France: −0.00006 vs B); mixmdp 0.990699. The last upload candidate is **B+** (`bplus_tsv.py`): B plus the 255 look-alike pairs the 7B accepts, minus the 83 never-scored mixmdp French pairs it rejects. Matching sha256 `09c45bff…`.

## 9. The final upload: B7 (27 Sep 23:36 IST)

The last slot went to **B7** (matching sha256 `3d7b09d6c3b964b67d3ce164512bf22df5130dab53cd99e53d8f2d35673a468d`,
candidates `58c824a3…`), validator PASS, strict audit PASS. It is Composite B with France-only edits from the 7B/4B drop
ladder in `fr_drop_ladder.py` (+251 / −1,699 French pairs vs B). Why the ladder went past the labelled −6 cut-off: B's
+0.00018 over mixmdp was mostly its 840 French 7B drops, i.e. they were nearly all false; a French drop pays off at
about 18–25% false; and the Qwen3-4B agrees with the 7B's rejections 2–15× more often in France than on US/India at
the same score, the signature of decoys. Two more checks tonight, both on the labelled holdout:
- a cross-fitted blend of all six cross-encoder logits + stage-3 pc has band AUC 0.9575 (pc 0.9276) but **loses
  0.001** as a replacement decision score, and is worth only +2…4e-6 as an edit signal (`analysis/meta_band.py`,
  `meta_edit.py`): the pipeline's decisions are at the ceiling of these signals;
- the in-band two-model drop (B6's step) is +8e-6 overall, halves −7e-6 / +24e-6.
Staged but not uploaded: B++ (`5ed33137…`), B3 (`1cc0727d…`), B4 (`d8c7d522…`), B5 (`69da05f1…`), B6 (`37608e5b…`), B8.
