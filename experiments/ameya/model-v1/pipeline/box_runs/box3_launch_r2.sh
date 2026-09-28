#!/usr/bin/env bash
# Round 2 of the French self-trained cross-encoders on grenuke-vast3, with a better teacher: CE-band pseudo-labels from
# v7sq-dpc (LB 0.990545) instead of v7ce3. Same settings as last night's runs, only --pseudo changes:
#   e5lsr2 = ce_box.py multilingual-e5-large, lr 2e-5, batch 128, 2 epochs, seed 7   (last night: e5ls)
#   qstr2  = ce_llm_st.py Qwen2.5-1.5B LoRA r16, lr 1e-4, batch 64, 1 epoch, us-in-frac 0.5   (last night: qst)
# Both run in parallel on the H100. usage: box3_launch_r2.sh <local pseudo_fr parquet (s1, r, y) of the CE band>
set -euo pipefail
H=grenuke-vast3
R=/workspace/grenuke
PS=$1
scp -q "$PS" $H:$R/box/pseudo_fr_v7sq.parquet
ssh -n $H "cd $R/box; source $R/env.sh; export HF_HUB_OFFLINE=1;
python -c \"import pandas as pd; d = pd.read_parquet('$R/box/pseudo_fr_v7sq.parquet'); print('pseudo', len(d), 'labelled', int((d.y >= 0).sum()), 'pos', round(float((d.y[d.y >= 0] == 1).mean()), 4))\";
nohup python ce_box.py --model intfloat/multilingual-e5-large --name e5lsr2 --lr 2e-5 --batch 128 --epochs 2 --seed 7 \
  --pseudo $R/box/pseudo_fr_v7sq.parquet > $R/logs/ce_e5lsr2.log 2>&1 < /dev/null &
nohup python $R/repo/experiments/ameya/model-v1/ce_llm_st.py --model Qwen/Qwen2.5-1.5B --name qstr2 \
  --pseudo $R/box/pseudo_fr_v7sq.parquet --us-in-frac 0.5 > $R/logs/ce_qstr2.log 2>&1 < /dev/null &
sleep 240; tail -2 $R/logs/ce_e5lsr2.log; tail -2 $R/logs/ce_qstr2.log; nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader"
echo "$(date +%H:%M:%S) LAUNCHED r2"
