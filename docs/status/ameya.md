# Status: ameya

- **Last updated (IST):** 2026-09-27 12:30
- **Current focus:** the last 3 uploads of 27 Sep. The window closes **21:00 IST**; the final upload counts, so the chosen best goes up last (by 18:30).
- **Branch(es):** `ameya/final-stack` (#58, approved: the stacked rules `experiments/ameya/model-v1/stack/`, RESEARCH_v6.md §6.16, the decision record, an `fhs.py` fix, this file). #35–#57 merged.
- **Leaderboard vs holdout:**

  | model | holdout (s3) | leaderboard | France implied |
  |---|---|---|---|
  | v5all + rules v2 + cut (26 Sep #01) | 0.99016 | 0.98781 | 0.971 |
  | v6all + stage 3 + rules v3 + acronym join | 0.99084 | 0.988609 | 0.973 |
  | v7n (e5-small + mean of two e5-large) | 0.99121 | 0.989721 | 0.978 |
  | v7nst (v7n + France stage-2 self-training) | 0.99119 | 0.990179 | 0.981 |
  | v7nst-dpc (27 Sep, the stack on v7nst) | 0.99119 | 0.990264 | about 0.982 |
  | **v7sq-dpc** (27 Sep, the stack on v7sq) | 0.99125 | **0.990545 (rank 7, then 8)** | **about 0.983** |

  LB = US/India part + 0.14975 × F_France. The two 27 Sep uploads split the gain: the stack +0.000085, the model v7nst → v7sq +0.000281 (France F about +0.0016).

- **Models since** (US/India holdout; the dpc stack; `fhs` is the French heuristic score of the stacked package):

  | model | cross-encoder mean | holdout (s3) | US/India part | combo-rule holdout | `fhs` (dpc) |
  |---|---|---|---|---|---|
  | v7sq (uploaded) | e5l, qst, e5ls, bge | 0.991246 | 0.843258 | 0.991280 | +2.19 |
  | v7sq3 | v7sq + e5ls2 | 0.991250 | 0.843265 | **0.991307** (+27.3e-6 [+2.2, +52.6] vs v7sq) | +1.13 |
  | v7qbag | bag of v7sq, v7sq2, v7sq3 | 0.991249 | 0.843261 | 0.991299 | +1.26 |
  | **v7sq4** | e5l, qst, e5ls, e5ls2, bges (4/5 French self-trained) | **0.991255** | **0.843269** | 0.991293 | **+2.23** |

- **Why v7sq gained on France** (France-diff agent): the French self-trained cross-encoders (qst, e5ls) overruled the US-trained ones, mostly by dropping confident false pairs. US/India truth by v7sq's new pc band, carried to France, predicts +362 of the LB-implied +441 F-units. More French cross-encoder weight is the lever: v7sq4 now, v7sq6 (only the four self-trained) next.
- **French acronyms are true copies (keep them):** 72 predicted acronym matches per 1000 French S1 against 5 true per 1000 in US/India looked like planted look-alikes. A label-free size-bias test says no: the other copies of an S1 holding an acronym follow the size-biased distribution of a true copy (fitted false share 0% [0, 1%]; S2 alone [0, 6%]), and on the holdout true populations score −0.05 to 0.0 while false same-address look-alikes score 0.47. The error agent's count test agrees. The `noacr` packages are not proposed.
- **Packages ready** (validator and strict audit PASS):
  - `2026-09-27-fr-v7sq4-c2` (sha `e7334cce…`): v7sq-dpc with France from v7sq4 (+1,809 / −1,018 French pairs), US/India byte-identical. The LB minus 0.990545 is the French effect alone.
  - `2026-09-27-mixb-c2` (sha `e67e9b81…`): US/India from v7sq3-dpc, France from v7sq-dpc. The low-risk final candidate (about +0.00002 expected).
  - `2026-09-27-mixc-c2` (sha `3688950c…`): `mixb` minus 592 French look-alike word swaps (`stack/apply_swapsim.py`,
    RESEARCH_v6.md 6.17). Expected about 0.99061. Rebuilt from this branch alone (`stack.sh` v7sq3 and v7sq, then
    `compose.py` and `apply_swapsim.py`): both TSVs byte-identical.
- **Upload plan (3 left, the captain decides):** every upload is a candidate final: `mixc` now; about 15:00 `mixc` with France from the best new variant (France-diff E-method); the final by 18:30 = the best measured, re-uploaded.
- **Running:**
  - laptop queue: v7sq6 → v7sqwg (guarded v7sq labels at stage 2, French rows ×3) → v7sq5g (round-2 cross-encoders), then v7xbag (stage-2 bag of all variants and v7sq's seeds 1–3); each gets a France-only test package.
  - `grenuke-vast3` (H100, 128 CPU): stage 2 for v7sqwg, v7sq seeds 1–3 and v7sq5g, and the round-2 cross-encoders (guarded labels), fetched back sha-checked so the laptop skips those stage-2 runs.
- **Vast.ai:** `grenuke-vast` stopped at 06:21; `grenuke-vast3` is running. Destroy both in the console after the competition and remove the SSH keys.
- **Candidate set (organisers, 27 Sep ~12:50):** `candidate_pairs.tsv` is part of the final submission and is reviewed
  with its code; smaller per S1 ranks higher beyond the leaderboard. Ours is the stage-2 input (`cands_final.py`:
  p1 ≥ 0.02 and each record's top 2 S1, plus acronym joins): **3.70 pairs per test S1** (matches 3.38; blocking
  about 34). Relayed on #45.
- **Blocked on / need from others:** the captain's uploads and their scores; the final zip must hold both TSVs of the chosen package (Bakshi had only the matching file of v7sq-dpc); merge #58 when ready (rebase-merge).
- **Latest handover:** `docs/handover/2026-09-27_0706_ameya_final-stack.md`.
