#!/bin/bash
# grenuke-vast3: v7sq9wg = cmq9 (qst, e5ls, e5ls2, bges + bges2, e5ls3 [+ q7st, q34st from Bakshi] [+ cesy from Sachi])
# + guarded v7sq labels x3 at stage 2. Starts when e5ls3 is merged or at 17:30 IST (12:00 UTC), whichever is first; each
# optional member joins if its out_<name>/ce_test.parquet is in box/ and it passes the gate. Logs "R7 DONE"/"R7 FAILED".
R=/workspace/grenuke; B=$R/box
LEG=leg__rel,leg__n_s1,leg__n_r,leg__inter,leg__s1_only,leg__r_only
NX=nx__d1,nx__nudge,nx__digit_sub,nx__digit_swap,nx__suffix,nx__len_diff
source $R/env.sh; export OMP_NUM_THREADS=32 NUMBA_NUM_THREADS=32
until grep -qE "e5ls3 (DONE|FAILED)" $R/logs/box3_q.log 2>/dev/null || [ "$(date -u +%H%M)" -ge 1200 ]; do sleep 30; done
gate() { python -c "import json,sys,numpy as np,pandas as pd; c=json.load(open('$B/out_$1/config.json')); a=c.get('auc',{}).get('holdout',0); t=pd.read_parquet('$B/out_$1/ce_train.parquet').ce__logit.to_numpy(); ok=a>=$2 and np.isfinite(t).all(); print('$1 holdout band AUC', a, 'finite train', bool(np.isfinite(t).all())); sys.exit(0 if ok else 1)" 2>&1; }
M="$B/out_qst $B/out_e5ls $B/out_e5ls2 $B/out_bges"
for n in bges2 e5ls3 q7st q34st; do [ -s $B/out_$n/ce_test.parquet ] && gate $n 0.93 && M="$M $B/out_$n"; done
[ -s $B/out_cesy/ce_test.parquet ] && gate cesy 0.90 && M="$M $B/out_cesy"
echo "$(date +%H:%M:%S) cmq9 from:$M"
cd $R/repo/experiments/ameya/model-v1
python $B/zmean_ce.py $B/out_cmq9 $M || { echo "$(date +%H:%M:%S) R7 FAILED zmean"; exit 1; }
python ce_import.py --feats ameya-fx5 --src $B/out_cmq9 --group cmq9 --column cmq9__logit || { echo "$(date +%H:%M:%S) R7 FAILED import"; exit 1; }
echo "$(date +%H:%M:%S) s2 v7sq9wg"
python s2w.py --feats ameya-fx5 --s1 ameya-s1-v6all --groups str,cx,lo0,lg,ce,cmq9,nx --cluster --extra $LEG,ce__logit,cmq9__logit,$NX --all \
  --tag ameya-s2-v7sq9wg --pseudo $B/pseudo_s2_fr_v7sq_guard.parquet --pseudo-weight 3 > $R/logs/s2_v7sq9wg.log 2>&1 \
  && echo "$(date +%H:%M:%S) R7 DONE" || echo "$(date +%H:%M:%S) R7 FAILED s2"
