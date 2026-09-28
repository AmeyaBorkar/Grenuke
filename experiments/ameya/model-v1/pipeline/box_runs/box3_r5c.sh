#!/bin/bash
# grenuke-vast3: v7sq8wg = cmq8 (qst, e5ls, e5ls2, bges, e5fr, bgefr [, cesy]) + guarded v7sq labels x3 at stage 2.
# (box3_r5c: + mdfr, French-heavy mdeberta-v3-base from the 5090, if ready by 15:50 IST)
# bgefr comes from the RTX 5090 (pulled here when its config.json exists); Sachi's out_cesy joins if it is in box/ by
# 15:50 IST (10:20 UTC) and passes the gate. Waits for box3_r4.sh (e5fr, v7sq7wg) to finish. Logs "R5 DONE"/"R5 FAILED".
R=/workspace/grenuke; B=$R/box
LEG=leg__rel,leg__n_s1,leg__n_r,leg__inter,leg__s1_only,leg__r_only
NX=nx__d1,nx__nudge,nx__digit_sub,nx__digit_swap,nx__suffix,nx__len_diff
G5="-i $HOME/.ssh/to4090 -p 28839 -o ConnectTimeout=20 root@180.189.55.43"
source $R/env.sh; export OMP_NUM_THREADS=32 NUMBA_NUM_THREADS=32
until ssh -n $G5 "test -s /workspace/grenuke/box/out_bgefr/config.json && echo yes" 2>/dev/null | grep -q yes; do sleep 60; done
mkdir -p $B/out_bgefr && scp -q -i $HOME/.ssh/to4090 -P 28839 "root@180.189.55.43:/workspace/grenuke/box/out_bgefr/*" $B/out_bgefr/ || { echo "$(date +%H:%M:%S) R5 FAILED pull"; exit 1; }
echo "$(date +%H:%M:%S) bgefr pulled"
gate() { python -c "import json,sys; c=json.load(open('$B/out_$1/config.json')); a=c['auc']['holdout']; print('$1 holdout band AUC', a); sys.exit(0 if a >= 0.90 else 1)"; }
M="$B/out_qst $B/out_e5ls $B/out_e5ls2 $B/out_bges"
while pgrep -f "bash box3_r4b.sh" > /dev/null; do sleep 30; done
gate e5fr && M="$M $B/out_e5fr"
gate bgefr && M="$M $B/out_bgefr"
have_md() { ssh -n $G5 "test -s /workspace/grenuke/box/out_mdfr/config.json && echo yes" 2>/dev/null | grep -q yes; }
until { [ -s $B/out_cesy/ce_test.parquet ] && have_md; } || [ "$(date -u +%H%M)" -ge 1020 ]; do sleep 30; done
if have_md; then mkdir -p $B/out_mdfr && scp -q -i $HOME/.ssh/to4090 -P 28839 "root@180.189.55.43:/workspace/grenuke/box/out_mdfr/*" $B/out_mdfr/ && gate mdfr && M="$M $B/out_mdfr"; fi
[ -s $B/out_cesy/ce_test.parquet ] && gate cesy && M="$M $B/out_cesy"
echo "$(date +%H:%M:%S) cmq8 from:$M"
cd $R/repo/experiments/ameya/model-v1
python $B/zmean_ce.py $B/out_cmq8 $M || { echo "$(date +%H:%M:%S) R5 FAILED zmean"; exit 1; }
python ce_import.py --feats ameya-fx5 --src $B/out_cmq8 --group cmq8 --column cmq8__logit || { echo "$(date +%H:%M:%S) R5 FAILED import"; exit 1; }
echo "$(date +%H:%M:%S) s2 v7sq8wg"
python s2w.py --feats ameya-fx5 --s1 ameya-s1-v6all --groups str,cx,lo0,lg,ce,cmq8,nx --cluster --extra $LEG,ce__logit,cmq8__logit,$NX --all \
  --tag ameya-s2-v7sq8wg --pseudo $B/pseudo_s2_fr_v7sq_guard.parquet --pseudo-weight 3 > $R/logs/s2_v7sq8wg.log 2>&1 \
  && echo "$(date +%H:%M:%S) R5 DONE" || echo "$(date +%H:%M:%S) R5 FAILED s2"
