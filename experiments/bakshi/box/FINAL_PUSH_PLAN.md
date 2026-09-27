# Final push, 27 Sep: plan to beat 0.990545

Owner: Bakshi. Runs on two rented Vast.ai boxes, independent of the integration machine.
Status at writing (about 14:30 IST): both boxes up, both jobs started.

## 1. Where we are

| | score | note |
|---|---|---|
| our best measured upload | **0.990545** | v7sq-dpc |
| leaderboard top | 0.991811 | +0.001266 above us |
| uploads left today | 3 | the BEST upload counts, not the latest (this corrects the "live risk" note in `final-package/ledger.json`) |

- Post-processing is exhausted: thresholds, disagreement deletion, the alias bridge, structural recall and consensus were all measured. Every candidate we hold agrees with v7sq-dpc on 99.92-99.97% of pairs.
- France is 14.98% of test S1 and has no labels. US/India sit at the holdout ceiling.
- Rule of thumb from our own history: about +0.000016 LB per net-correct changed French prediction per 1000 French S1
  (v7nst-dpc -> v7sq-dpc changed 16.6/1000 for +0.000281). 0.991 needs about 28/1000; 0.9918 about 79/1000.

## 2. Evidence gathered today

- **More small encoders barely move France.** v7sq4 adds two more self-trained small encoders (e5ls2, bges) to v7sq's mix:
  France changes only 10.9 per 1000 vs v7sq-dpc (+7.0 / -3.9), so at most about +0.00017.
- **Self-training ladder (LOCO, US -> India, `loco.py --self-train 3`).**
  - Features in distribution: 0.96106 -> 0.9637 -> 0.96479 -> 0.96498 (+0.0026, +0.0011, +0.0002). Round 2 is worth about 40% of round 1; round 3 is worth almost nothing.
  - Features out of distribution (lo__* zeroed, like France): 0.88235 -> 0.8512 -> 0.83075 -> 0.82307. Self-training amplifies the errors.
- **Every cross-encoder we have saturates at 0.938-0.944 band AUC** on the labelled holdout: e5l 0.939, e5l2 0.944, bge 0.942, qst 0.938, e5ls 0.944, e5ls2 0.944, bges 0.942, e5lsr2g 0.944.
  The Qwen2.5-1.5B is not stronger than e5-large; its value in v7sq was diversity.
- Records carry only name, address and country, and the cross-encoders already see name and address. No unused field is left.

## 3. Decision

Pull the one lever never tried: **model scale** for the France self-trained cross-encoder. Keep everything else exactly as in v7sq.

| model | licence | params | role |
|---|---|---|---|
| Qwen/Qwen2.5-7B | Apache-2.0 | 7.6B | main bet; same recipe as qst (ce_llm_st.py), 3 GPUs in parallel |
| Qwen/Qwen3-4B-Base | Apache-2.0 | 4.0B | second big member, if it can finish by 17:45 IST |
| Alibaba-NLP/gte-multilingual-reranker-base | Apache-2.0 | 0.3B | cheap filler if the 4B does not fit |
| microsoft/mdeberta-v3-base | MIT | 0.28B | cheap filler if the 4B does not fit |

- All new models self-train on France with the **v7sq-dpc teacher's** pseudo-labels (`pseudo_fr_v7sq.parquet`), not v7ce3's.
- All models are at most 8B, MIT or Apache-2.0. No external data.

## 4. Forecast (honest)

| outcome | needs | chance |
|---|---|---|
| any new best above 0.990545 | about 15+/1000 net-correct French changes | about 2 in 3 |
| 0.991 or more | about 28/1000, plus a small US/India gain | about 1 in 3 |
| 0.9918 or more | France about as good as US/India, plus US/India gains | under 5% |

Central estimate: **about 0.9909**.

## 5. Infrastructure

| box | hardware | job | lifetime |
|---|---|---|---|
| pipeline | 2x RTX 4090 24 GB, 64 vCPU, 258 GB RAM, 700 GB; on-demand; Max CUDA 12.7, so torch cu126 | rebuild, V0 gate, stage-2 variants, rules, packaging | whole run |
| training | 4x H100 80 GB; **interruptible** | Qwen2.5-7B (GPUs 0-2), Qwen3-4B or the fillers (GPU 3) | about 3 h, then destroyed |

- Because the training box is interruptible, `llm_group.py` checkpoints every ~10 min and resumes by skipping the chunks already done.
- A backup loop copies checkpoints, adapters, parts and logs to Google Drive every 5 min (`rclone`, scope drive.file). The rclone config never enters the repo.

## 6. Pipeline

**Phase A, pipeline box** (`phaseA.sh`), reproduce.sh steps 0-5:
records -> Indic dictionary -> blocking v3 -> fx5 features -> stage 1 (`ameya-s1-v6all`) -> e5-small (`ce.py`)
-> band export -> `cands_final.py` (c2).

**Cross-encoders, training box** (`train_jobs.sh`, `llm_group.py`, `llm_merge.py`):
- Each of ce_llm_st.py's three OOF groups runs on its own GPU. The rows and seeds are identical to the sequential script: the rng draws of the earlier groups are replayed.
- `llm_merge.py` assembles exactly what ce_llm_st.py writes.
- They train on **Ameya's band** (band_train 876987f0..., band_test ec8d1db8...), which is the band all his cross-encoders used.

**Remap** (`remap_ce.py`):
- Every logit moves from Ameya's band to ours by (s1, r), never by row number: `ce_import.py` places logits positionally.
- A coverage gate of at least 99.5% of our band rows proves that blocking and stage 1 reproduced. It was tested: identity is exact, permuted rows follow the pair, and a 2% gap fails.

**Phase B, per variant** (`phaseB.sh <variant> "<ce runs>" <s2 pseudo>`):
remap -> `zmean_ce.py` -> `ce_import.py` -> `s2.py --pseudo` -> decide -> stage3 -> decide -> post_ops -> acr_join -> `stack/stack.sh` (dpc)
-> write -> validator + `audit_matching.py` -> `diff_candidates.py` vs v7sq-dpc.

| variant | CE mix (z-mean) | stage-2 France labels | purpose |
|---|---|---|---|
| g0 | e5l, qst, e5ls, bge (= v7sq's cmq) | v7ce3 | **V0 reproduction gate**: France must differ from v7sq-dpc by only about 0-3/1000, or nothing built on this box counts |
| gA | cmq + q7st | v7ce3 | the single change: add the 7B |
| gB | cmq + q7st + q34st (or 7B-weighted) | v7ce3 | more weight on scale |
| gC | best of gA/gB | v7sq (round 2) | round-2 labels for stage 2 |

## 7. Choosing the uploads (3 slots, best counts)

1. **Hard gate:** the validator and the strict audit pass (one owner per record, no cross-country pairs, matches a subset of candidates, row set = test S1).
2. **No regression** on the labelled holdout (US/India) vs v7sq.
3. **Screen** by France footprint vs v7sq-dpc (want at least about 15/1000, ideally 28 or more) and by the direction of the fhs COPY net.
4. Upload the 2-3 most different bets. If the new chain fails, the fallback slots go to v7sq4 (audited, PASS) and v7qbag.

## 8. Timeline (IST)

| time | pipeline box | training box |
|---|---|---|
| 14:15-14:45 | upload, setup, phase A starts | Drive backup, upload, setup, smoke test |
| 14:45-17:15 | phase A, then g0 | Qwen2.5-7B (3 GPUs), GPU 3 per its rule |
| 17:15-18:30 | remap new logits, gA/gB/gC stage 2 (2 at a time) | merged outputs pulled; box destroyed |
| 18:30-19:30 | rules, stack, package, audit, screen | - |
| by 20:00 | uploads | - |

## 9. Inputs received from Ameya (27 Sep, verified)

- `grenuke_must_have.zip` sha256 44d86ae0...d2ac: out_qst, out_e5ls, pseudo_s2_fr_v7sq, pseudo_fr_v7sq (teacher ameya-model-v7sq-s3-ops3a-dpc).
- `grenuke_nice_to_have.zip` sha256 142c8ed3...5220: out_e5ls2, out_bges, out_e5lsr2g, pseudo_fr_v7ce3, pseudo_s2_fr_v7ce3.
- All 8 cross-encoder outputs are row-aligned with the band files above and contain no NaN.
- There was never a round-2 Qwen run. v7sq4's cmq4 = z-mean of e5l, qst, e5ls, e5ls2, bges.

## 10. Files

| file | what |
|---|---|
| `setup.sh` | box environment (pinned CPU stack, torch build matching the host CUDA) |
| `phaseA.sh`, `phaseB.sh` | rebuild and per-variant chain |
| `remap_ce.py` | (s1, r) re-keying with the coverage gate |
| `llm_group.py`, `llm_merge.py` | one OOF group per GPU with checkpoints; exact merge |
| `ce_rc.py` | trust_remote_code loader for gte |
| `train_jobs.sh` | training-box orchestration: setup / smoke / launch / gpu3 / status / merge |

The scripts are a snapshot taken while both runs are live. Fixes made on the boxes will be pushed to this branch.
