#!/usr/bin/env bash
# Set up grenuke-vast3 (27 Sep, H100 80 GB, 503 GB RAM, 128 CPU): dirs; a venv with torch (cu124, driver 555) +
# transformers/peft and the repo's pinned requirements; code from the final-stack worktree (main + stack, incl.
# experiments/sachi/ce_llm.py for the Qwen trainer); records, cross-encoder band pairs and pseudo-labels; model weights.
# Nothing is launched. Ends "SETUP DONE".
set -euo pipefail
H=grenuke-vast3
SP=$SCRATCH
WT=$REPO/.claude/worktrees/final-stack
R=/workspace/grenuke
echo "$(date +%H:%M:%S) dirs + venv (background)"
ssh -n $H "mkdir -p $R/box $R/work/records $R/logs $R/repo"
ssh -n $H "cd $R && nohup bash -c 'uv venv $R/venv --python 3.12 -q && . $R/venv/bin/activate && uv pip install -q torch --index-url https://download.pytorch.org/whl/cu124 && uv pip install -q transformers sentencepiece peft accelerate huggingface_hub psutil numpy==2.4.3 pandas==2.3.3 pyarrow==23.0.1 scipy==1.17.0 scikit-learn==1.8.0 xgboost==3.2.0 lightgbm==4.7.0 rapidfuzz==3.14.6 numba==0.64.0 && python -c \"import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))\" && uv pip freeze > $R/logs/pip_freeze.txt && echo PIP_DONE' > $R/logs/pip.log 2>&1 < /dev/null &"
echo "$(date +%H:%M:%S) code"
git -C $WT archive --format=tar HEAD code/business_entity_resolution/src experiments/ameya/model-v1 experiments/sachi/ce_llm.py > $SP/box3_code.tar
scp -q $SP/box3_code.tar $H:$R/repo/code.tar && ssh -n $H "cd $R/repo && tar xf code.tar && rm code.tar && cp experiments/ameya/model-v1/ce_box.py $R/box/"
cat > $SP/box3_env.sh <<ENV
export BER_WORK_DIR=$R/work
export PYTHONPATH=$R/repo/code/business_entity_resolution/src:$R/repo/experiments/ameya/model-v1
export CE_BOX_DIR=$R/box
export PYTHONIOENCODING=utf-8
. $R/venv/bin/activate
ENV
scp -q $SP/box3_env.sh $H:$R/env.sh
echo "$(date +%H:%M:%S) data: records (about 1.1 GB), band pairs, pseudo-labels"
scp -q $REPO/work/records/train.parquet $REPO/work/records/test.parquet $H:$R/work/records/
scp -q $SP/box/band_train.parquet $SP/box/band_test.parquet $SP/box/pseudo_fr_v7ce3.parquet $SP/box/pseudo_s2_fr_v7ce3.parquet $H:$R/box/
echo "$(date +%H:%M:%S) wait for pip, fetch weights"
ssh -n $H "until grep -qE 'PIP_DONE|rror' $R/logs/pip.log; do sleep 5; done; tail -2 $R/logs/pip.log; source $R/env.sh; python -c \"
from huggingface_hub import snapshot_download
for m in ('intfloat/multilingual-e5-large', 'BAAI/bge-reranker-v2-m3', 'Qwen/Qwen2.5-1.5B', 'FacebookAI/xlm-roberta-large'):
    print(snapshot_download(m, allow_patterns=['*.json', '*.safetensors', 'sentencepiece.bpe.model', 'tokenizer*', 'vocab*', 'merges.txt']))
\""
ssh -n $H "source $R/env.sh; cd $R/box; python -c 'import ce, ce_box; print(\"ce import ok\")'; ls $R/box $R/work/records; nvidia-smi --query-gpu=memory.used --format=csv,noheader"
echo "$(date +%H:%M:%S) SETUP DONE"
