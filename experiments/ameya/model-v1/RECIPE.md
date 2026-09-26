# Reproducing the final submission (for the final package)

The exact commands behind the final candidates, from raw data to `output/*.tsv`, and answers to the reproduction questions (26 Sep).
- Run everything from the repo root with `pip install -e code/business_entity_resolution`, or with `PYTHONPATH` set to `code/business_entity_resolution/src` and `experiments/ameya/model-v1`.
- `BER_DATA_DIR` must point at `student_resource/dataset`.
- Integration machine: RTX 5070 Ti 12 GB, 24 cores, 31 GB RAM. Nothing else heavy may run next to stages 1/2, which peak at about 18–19 GB.

## Answers

1. **Blocking behind `ameya-fx4`.** `feats.py --cands ameya-block-v2 --tag ameya-fx4` (v5 text code). `ameya-block-v2` is:
   ```
   python -m ber.pipeline --stage block --split train --tag ameya-block-v2 --set trim_s1=15 --set trim_r=4 --set indic_dict=ameya-fx1 --set ns_ngrams=4 --set ns_domain_len=8 --set nw_words=6 --set dev_tag=ameya-block-v2-dev
   python -m ber.pipeline --stage block --split test  --tag ameya-block-v2 --set trim_s1=15 --set trim_r=4 --set indic_dict=ameya-fx1 --set ns_ngrams=4 --set ns_domain_len=8 --set nw_words=6
   ```
   - `indic_dict=ameya-fx1` means `work/models/ameya-fx1/indic_dict.parquet`, the Indic→Latin dictionary learned on train folds 5–19. The first feature run wrote it.
   - For a clean re-run, create it first: `python experiments/ameya/model-v1/feats.py --split train --tag ameya-fx1 --dict-only`.
   - `dev_tag` only writes the dev-sample subset; it is optional.
   - Blocking v3 (current main, used by v6all) takes the same parameters. The domain/OCR repairs are on by default (`seg_domains`, `ocr_repair`); the ordinal words are always converted. So v2 candidates cannot be rebuilt bit-for-bit with current main. Use commit `7568980` for the v5all recipe.
2. **`ce.py --s1` for fx4.** fx4's cross-encoder group was not recomputed: `run_v5.sh` copied `ameya-fx3-ce`, which has the same candidates and row groups. It was made by:
   ```
   python experiments/ameya/model-v1/ce.py --feats ameya-fx3 --s1 ameya-s1-v3 --tag ameya-ce-v1 --model intfloat/multilingual-e5-small
   ```
   For a clean, self-consistent re-run, use the recipe's own stage 1: stage 1 → `ce.py --s1 <that stage-1 tag>` → stage 2. v6all does this with `--s1 ameya-s1-v6all`.
3. **Is `feats_lo.py` still needed for `lo0`? Yes.**
   - `lo_mix.py` reads `<feats>-lo` (from `feats_lo.py`) and `<feats>-lop` (from `feats_lo_proxy.py`) and writes `<feats>-lo0`.
   - `feats_lo.py --split train` also writes `work/models/<feats>/token_lo.parquet`, which the test run reads. `feats_lo_proxy.py --split train --calib` writes the calibration map the test run reads.
   - Order: lo train → lo test → lop train `--calib` → lop test → `lo_mix`.
4. **Does `feats_legal.py` need `--group`? No.** It only renames the output group; the default `lg` is what stages 1/2 read.
5. **Can `decide.py --base` be optional? Yes.** It now defaults to empty and skips the comparison.

## The next candidate: v7ce3 (v6all + larger cross-encoders + stage 3 + rules v3 + acronym join)

**Status 26 Sep 19:40: holdout gate passed.**
- Holdout 0.991138 vs v6all-s3 0.990842: Δ +0.000296 [+0.000252, +0.000342]. vs v6all-c2: +0.00035.
- Decision record `docs/decisions/2026-09-26_1933_model-v7ce3.md`.
- Output `2026-09-27-v7ce3-s3-ops3a-c2`: matching sha256 `671dca1e96484c6a16618f9c26901f6cd73659a92894a28a39ebb48ef65386fd`, candidates `85a1ca7d0519329baa87995cbaf5cc621ba91e043eb2bd52564545b8c15fb476`.

Steps 0–5 of v6all below, then:
```
cd experiments/ameya/model-v1
# 5b. larger cross-encoders on a GPU (multilingual-e5-base and -large, MIT, 278M / 560M; about 40 / 60 min on an H100)
python -c "from ce import band_pairs; [band_pairs('ameya-s1-v6all', s)[['s1','r','row','p1'] + (['fold','y'] if s == 'train' else [])].to_parquet(f'$CE_BOX_DIR/band_{s}.parquet', index=False) for s in ('train', 'test')]"
python ce_box.py --model intfloat/multilingual-e5-large --lr 2e-5 --name e5l      # CE_BOX_DIR must hold the band files
python ce_box.py --model intfloat/multilingual-e5-base  --lr 3e-5 --name e5b
python ce_import.py --feats ameya-fx5 --src $CE_BOX_DIR/out_e5l --group cel --column cel__logit
python ce_import.py --feats ameya-fx5 --src $CE_BOX_DIR/out_e5b --group ceb --column ceb__logit
# 5c. stage 2 with all three cross-encoder logits
python s2.py --feats ameya-fx5 --s1 ameya-s1-v6all --tag ameya-s2-v7ce3 --groups str,cx,lo0,lg,ce,cel,ceb,nx --cluster --extra $LEG,ce__logit,cel__logit,ceb__logit,$NX --all
# 6. decision, candidate set, stage 3, rules v3, acronym join
python decide.py --scores ameya-s2-v7ce3 --col pc --tag ameya-model-v7ce3-c2 --p-cand 0.02 --top-r 2
python cands_final.py --s1 ameya-s1-v6all --tag ameya-cands-v6all-c2 --p-cand 0.02 --top-r 2
python stage3.py --scores ameya-s2-v7ce3 --tag ameya-s3-v7ce3 --p-cand 0.02 --top-r 2
python decide.py --scores ameya-s3-v7ce3 --col pc --tag ameya-model-v7ce3-s3 --p-cand 0.02 --top-r 2
python post_ops.py --matches ameya-model-v7ce3-s3 --scores ameya-s3-v7ce3 --cands ameya-cands-v6all-c2 --feats ameya-fx5 --tag ameya-model-v7ce3-s3-ops3 --robust-addr
python acr_join.py --split test --matches ameya-model-v7ce3-s3-ops3 --cands ameya-cands-v6all-c2 --tag ameya-model-v7ce3-s3-ops3a --cands-tag ameya-cands-v7ce3-c2a
cd ../../..
# 7. write and validate
python -m ber.pipeline --stage write --split test --tag ameya-model-v7ce3-s3-ops3a --in candidates=ameya-cands-v7ce3-c2a --in matches=ameya-model-v7ce3-s3-ops3a
```

## The final recipe: v6all (current main), if its gate passes

**Status 26 Sep 14:27: final.** Holdout 0.990788 vs v5all-c2 0.990156, Δ +0.00063 [0.00057, 0.00070]; `decide.py` picks a threshold of 0.70 (G6). Output `2026-09-26-v6all-ops-c2`: matching sha256 `0f6d8985be05877276e16a4d95562d8d72f36c38f962441f1a6f9928d22890be`, candidates `cc3750d0c38e7d7863576fb1550668471cd65ad17b66187e8d457e5cf9dceaae`; 3.70 candidates per S1.

```
# 0. records and the Indic dictionary
python -m ber.pipeline --stage records --split train
python -m ber.pipeline --stage records --split test
python experiments/ameya/model-v1/feats.py --split train --tag ameya-fx1 --dict-only
# 1. blocking v3 (about 13 + 10 min)
BP="--set trim_s1=15 --set trim_r=4 --set indic_dict=ameya-fx1 --set ns_ngrams=4 --set ns_domain_len=8 --set nw_words=6"
python -m ber.pipeline --stage block --split train --tag ameya-block-v3 $BP
python -m ber.pipeline --stage block --split test  --tag ameya-block-v3 $BP
cd experiments/ameya/model-v1
# 2. features (about 1 h)
python feats.py --cands ameya-block-v3 --split train --tag ameya-fx5      # also learns work/models/ameya-fx5/indic_dict.parquet
python feats.py --cands ameya-block-v3 --split test  --tag ameya-fx5
python feats_nx.py --feats ameya-fx5 --split train
python feats_nx.py --feats ameya-fx5 --split test
python feats_lo.py --feats ameya-fx5 --split train
python feats_lo.py --feats ameya-fx5 --split test
python feats_legal.py --feats ameya-fx5 --split train
python feats_legal.py --feats ameya-fx5 --split test
python feats_lo_proxy.py --feats ameya-fx5 --split train --calib
python feats_lo_proxy.py --feats ameya-fx5 --split test
python lo_mix.py --feats ameya-fx5
# 3. stage 1 on all of train (4 out-of-fold groups; about 30 min, 18 GB)
python s1.py --feats ameya-fx5 --tag ameya-s1-v6all --groups str,cx,lo0,lg,nx --drop leg__r_only_bits,leg__s1_only_bits --all
# 4. cross-encoder feature (multilingual-e5-small, MIT, 118M; GPU about 40 min; HF_HUB_OFFLINE=1 once the weights are cached)
python ce.py --feats ameya-fx5 --s1 ameya-s1-v6all --tag ameya-ce-v6 --model intfloat/multilingual-e5-small
# 5. stage 2 on all of train (about 25 min, about 19 GB)
LEG=leg__rel,leg__n_s1,leg__n_r,leg__inter,leg__s1_only,leg__r_only
NX=nx__d1,nx__nudge,nx__digit_sub,nx__digit_swap,nx__suffix,nx__len_diff
python s2.py --feats ameya-fx5 --s1 ameya-s1-v6all --tag ameya-s2-v6all --groups str,cx,lo0,lg,ce,nx --cluster --extra $LEG,ce__logit,$NX --all
# 6. decision inside the final candidate set, the candidate set itself, France rules v2
python decide.py --scores ameya-s2-v6all --col pc --tag ameya-model-v6all-c2 --p-cand 0.02 --top-r 2
python cands_final.py --s1 ameya-s1-v6all --tag ameya-cands-v6all-c2 --p-cand 0.02 --top-r 2
python post_ops.py --matches ameya-model-v6all-c2 --scores ameya-s2-v6all --cands ameya-cands-v6all-c2 --feats ameya-fx5 --tag ameya-model-v6all-c2-ops
cd ../../..
# 7. write and validate
python -m ber.pipeline --stage write --split test --tag ameya-model-v6all-c2-ops --in candidates=ameya-cands-v6all-c2 --in matches=ameya-model-v6all-c2-ops
python student_resource/utils/validate_submission.py --matching output/matching_results.tsv --candidate output/candidate_pairs.tsv --test-dir student_resource/dataset/test
```

## The fallback: v5all + rules v2 + cut (`2026-09-26-v5all-ops2-c2`, matching sha256 `76fe7eff…`)

Code at commit `7568980` (main before the blocking v3 merge). At that commit `decide.py` still needs an existing `--base` tag and `feats.py` has no `--dict-only`; use this PR's two small changes on top. Steps 0 and 3–7 are as above, with `ameya-block-v2` / `ameya-fx4` / `ameya-s1-v5all` / `ameya-s2-v5all` and without the `nx` group:
```
python -m ber.pipeline --stage block --split {train,test} --tag ameya-block-v2 $BP
python feats.py --cands ameya-block-v2 --split {train,test} --tag ameya-fx4
# lo, lg, lop, lo_mix on ameya-fx4 as above
python s1.py --feats ameya-fx4 --tag ameya-s1-v5all --groups str,cx,lo0,lg --drop leg__r_only_bits,leg__s1_only_bits --all
python ce.py --feats ameya-fx4 --s1 ameya-s1-v5all --tag ameya-ce-v5 --model intfloat/multilingual-e5-small   # the submitted run reused fx3's CE (answer 2)
python s2.py --feats ameya-fx4 --s1 ameya-s1-v5all --tag ameya-s2-v5all --groups str,cx,lo0,lg,ce --cluster --extra $LEG,ce__logit --all
python decide.py --scores ameya-s2-v5all --col pc --tag ameya-model-v5all-c2 --p-cand 0.02 --top-r 2
python cands_final.py --s1 ameya-s1-v5all --tag ameya-cands-v5all-c2 --p-cand 0.02 --top-r 2
python post_ops.py --matches ameya-model-v5all-c2 --scores ameya-s2-v5all --cands ameya-cands-v5all-c2 --feats ameya-fx4 --tag ameya-model-v5all-c2-ops2
```

## Notes for the methodology document

- **Pipeline.** Blocking reduces 34 pairs per S1 to the final candidate set, **3.70 per S1**:
  - blocking: token/name_short retrieval plus the Indic, domain and OCR repairs;
  - stage 0: a cheap filter;
  - stage 1: XGBoost on string/context/label-odds/legal/number features, p1 ≥ 0.02 and each record's top 2 S1.
- **Stage 2** is the matching model: XGBoost with rivalry and cluster features plus the cross-encoder logit, isotonic-calibrated.
- **Decision:** argmax ownership plus an exact expected-F0.5 choice per S1 (DP).
- **France:** label-free proxy look-alike odds, plus the generator-operation rules (`post_ops.py`) for countries without training labels.
- Models: XGBoost (Apache-2.0); intfloat/multilingual-e5-small (MIT, 118M).
- No external data: all lexicons (legal forms, street types, French departments → regions, list words, OCR map, ordinals) are hand-written and documented in the code.
- Evidence: `ANALYSIS_v2.md`–`ANALYSIS_v4.md`, `RESEARCH_v5.md`, and the decision records in `docs/decisions/`.
