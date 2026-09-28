#!/bin/bash
# grenuke-vast3: v7sqq7 = cmqq7 (qst, e5ls, e5ls2, bges, bges2, e5ls3, q7st = Bakshi's Qwen2.5-7B France self-trained CE)
# + guarded v7sq labels x3 at stage 2. Logs "R11 v7sqq7 DONE/FAILED".
R=/workspace/grenuke; B=$R/box
LEG=leg__rel,leg__n_s1,leg__n_r,leg__inter,leg__s1_only,leg__r_only
NX=nx__d1,nx__nudge,nx__digit_sub,nx__digit_swap,nx__suffix,nx__len_diff
source $R/env.sh; export OMP_NUM_THREADS=24 NUMBA_NUM_THREADS=24
python -c "import numpy as np,pandas as pd; t=pd.read_parquet('$B/out_q7st/ce_train.parquet'); e=pd.read_parquet('$B/out_q7st/ce_test.parquet'); r=pd.read_parquet('$B/out_qst/ce_train.parquet'); print('rows', len(t), len(e), 'aligned', bool((t.row.to_numpy()==r.row.to_numpy()).all()), 'nan train', int(t.ce__logit.isna().sum()), 'nan test', int(e.ce__logit.isna().sum()))"
cd $R/repo/experiments/ameya/model-v1
python $B/zmean_ce.py $B/out_cmqq7 $B/out_qst $B/out_e5ls $B/out_e5ls2 $B/out_bges $B/out_bges2 $B/out_e5ls3 $B/out_q7st || { echo "$(date +%H:%M:%S) R11 v7sqq7 FAILED zmean"; exit 1; }
python ce_import.py --feats ameya-fx5 --src $B/out_cmqq7 --group cmqq7 --column cmqq7__logit > $R/logs/imp_cmqq7.log 2>&1 || { echo "$(date +%H:%M:%S) R11 v7sqq7 FAILED import"; exit 1; }
python s2w.py --feats ameya-fx5 --s1 ameya-s1-v6all --groups str,cx,lo0,lg,ce,cmqq7,nx --cluster --extra $LEG,ce__logit,cmqq7__logit,$NX --all \
  --tag ameya-s2-v7sqq7 --pseudo $B/pseudo_s2_fr_v7sq_guard.parquet --pseudo-weight 3 > $R/logs/s2_v7sqq7.log 2>&1 \
  && echo "$(date +%H:%M:%S) R11 v7sqq7 DONE" || echo "$(date +%H:%M:%S) R11 v7sqq7 FAILED s2"
