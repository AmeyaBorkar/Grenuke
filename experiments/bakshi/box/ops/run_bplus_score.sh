#!/usr/bin/env bash
# 7B scoring on the 4090 box for B+: the look-alike pairs swapsim removed, and mixmdp's French pairs never scored.
cd /workspace/grenuke; . ./env.sh
export HF_HOME=/workspace/grenuke/hf
python -m pip install -q peft==0.21.0 > logs/bplus_pip.log 2>&1
python -c "import peft; print('peft', peft.__version__)" >> logs/bplus.log 2>&1
D=box/rescore
cat $D/lookalike_fr.parquet > /dev/null
python - <<PY
import pandas as pd
a = pd.read_parquet("$D/lookalike_fr.parquet"); a["src"] = "lookalike"
b = pd.read_parquet("$D/mixmdp_fr_unscored.parquet"); b["src"] = "mixmdp_unscored"
pd.concat([a, b], ignore_index=True).to_parquet("$D/bplus_pairs.parquet", index=False)
print("pairs", len(a) + len(b))
PY
CUDA_VISIBLE_DEVICES=0 python repo/experiments/bakshi/box/score_pairs.py --pairs $D/bplus_pairs.parquet --split test \
  --adapter box/out_q7st/adapter_0 --out $D/bplus_scored.parquet --batch 64 >> logs/bplus.log 2>&1
echo "$(date -u +%T) bplus scoring exit $?" >> logs/bplus.log
