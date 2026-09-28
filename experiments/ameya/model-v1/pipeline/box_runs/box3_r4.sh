#!/bin/bash
# grenuke-vast3, 14:25 IST: e5fr = French-heavy multilingual-e5-large (round-1 labels v7ce3, a quarter of the US/India
# band, 1 epoch, French test rows only), three folds in parallel; then v7sq7wg = cmq7 (qst, e5ls, e5ls2, bges, e5fr)
# + guarded v7sq labels x3 at stage 2. Logs "R3B DONE" / "R3B FAILED ..." (final_night18 watches this file).
R=/workspace/grenuke; B=$R/box
LEG=leg__rel,leg__n_s1,leg__n_r,leg__inter,leg__s1_only,leg__r_only
NX=nx__d1,nx__nudge,nx__digit_sub,nx__digit_swap,nx__suffix,nx__len_diff
source $R/env.sh; export HF_HUB_OFFLINE=1 OMP_NUM_THREADS=32 NUMBA_NUM_THREADS=32
while pgrep -f "s2w.py --feats ameya-fx5 --s1 ameya-s1-v6all --groups str,cx,lo0,lg,ce,cmq6" > /dev/null; do sleep 20; done
echo "$(date +%H:%M:%S) e5fr folds start"
cd $B
A="--model intfloat/multilingual-e5-large --name e5fr --lr 2e-5 --batch 128 --epochs 1 --seed 31 --pseudo $B/pseudo_fr_v7ce3.parquet --us-in-frac 0.25 --target-only-test --hold-groups 0"
for g in 0 1 2; do python ce_box.py $A --only-group $g > $R/logs/ce_e5fr_g$g.log 2>&1 & done
wait
python ce_box.py $A --merge > $R/logs/ce_e5fr_merge.log 2>&1 || { echo "$(date +%H:%M:%S) R3B FAILED e5fr merge"; exit 1; }
python - <<PY || { echo "$(date +%H:%M:%S) R3B FAILED gate"; exit 1; }
import json; c = json.load(open("$B/out_e5fr/config.json")); a = c["auc"]["holdout"]; print("e5fr holdout band AUC", a, "oof", c["auc"]["oof"])
raise SystemExit(0 if a >= 0.93 else 1)
PY
cd $R/repo/experiments/ameya/model-v1
python $B/zmean_ce.py $B/out_cmq7 $B/out_qst $B/out_e5ls $B/out_e5ls2 $B/out_bges $B/out_e5fr || { echo "$(date +%H:%M:%S) R3B FAILED zmean"; exit 1; }
python ce_import.py --feats ameya-fx5 --src $B/out_cmq7 --group cmq7 --column cmq7__logit || { echo "$(date +%H:%M:%S) R3B FAILED import"; exit 1; }
echo "$(date +%H:%M:%S) s2 v7sq7wg"
python s2w.py --feats ameya-fx5 --s1 ameya-s1-v6all --groups str,cx,lo0,lg,ce,cmq7,nx --cluster --extra $LEG,ce__logit,cmq7__logit,$NX --all \
  --tag ameya-s2-v7sq7wg --pseudo $B/pseudo_s2_fr_v7sq_guard.parquet --pseudo-weight 3 > $R/logs/s2_v7sq7wg.log 2>&1 \
  && echo "$(date +%H:%M:%S) R3B DONE" || echo "$(date +%H:%M:%S) R3B FAILED s2"
