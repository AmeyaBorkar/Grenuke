#!/usr/bin/env bash
# Stage-2 runs on grenuke-vast3 (128 CPU, 503 GB), 4 in parallel, 32 XGBoost threads each:
#   v7sqwg        s2w.py, v7sq's features (cmq), the GUARDED v7sq stage-2 labels, French rows weighted x3 (plan Wg)
#   v7sq-sd1..3   s2.py, v7sq exactly (cmq, round-1 labels P1) with XGBoost seeds 1-3 (for a seed bag with v7sq)
# Needs box3_upload_s2.sh done. Writes work/scores/ameya-s2-<tag> + models + reports on the box. Ends "S2 RUNS LAUNCHED".
set -euo pipefail
H=grenuke-vast3
SP=/c/Users/ameya/AppData/Local/Temp/claude/C--Users-ameya-Documents-GrenukeAmazon/19e315ba-0725-4d6f-ae6a-972e1c1f0aa9/scratchpad
R=/workspace/grenuke
scp -q $SP/s2w.py $H:$R/repo/experiments/ameya/model-v1/s2w.py
scp -q $SP/agents/gpuplan/pseudo_s2_fr_v7sq_guard.parquet $H:$R/box/
LEG=leg__rel,leg__n_s1,leg__n_r,leg__inter,leg__s1_only,leg__r_only
NX=nx__d1,nx__nudge,nx__digit_sub,nx__digit_swap,nx__suffix,nx__len_diff
COMMON="--feats ameya-fx5 --s1 ameya-s1-v6all --groups str,cx,lo0,lg,ce,cmq,nx --cluster --extra $LEG,ce__logit,cmq__logit,$NX --all"
ssh -n $H "cd $R/repo/experiments/ameya/model-v1; source $R/env.sh; export OMP_NUM_THREADS=32 NUMBA_NUM_THREADS=32; mkdir -p $R/logs;
nohup python s2w.py $COMMON --tag ameya-s2-v7sqwg --pseudo $R/box/pseudo_s2_fr_v7sq_guard.parquet --pseudo-weight 3 > $R/logs/s2_v7sqwg.log 2>&1 < /dev/null &
for s in 1 2 3; do nohup python s2.py $COMMON --tag ameya-s2-v7sq-sd\$s --seed \$s --pseudo $R/box/pseudo_s2_fr_v7ce3.parquet > $R/logs/s2_v7sq-sd\$s.log 2>&1 < /dev/null & done
sleep 90; for f in $R/logs/s2_v7sqwg.log $R/logs/s2_v7sq-sd1.log; do echo == \$f; tail -2 \$f; done; free -g | head -2" 2>&1 | grep -vE "^Welcome|^Have fun|^AI agents" | cut -c1-200
echo "$(date +%H:%M:%S) S2 RUNS LAUNCHED"
