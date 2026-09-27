#!/usr/bin/env bash
# One-time environment for a Vast box. Idempotent: safe to re-run.
#
#   bash setup.sh main   # the pipeline box: blocking, features, XGBoost stages 1-3 (GPU XGBoost), rules, write
#   bash setup.sh ce     # a cross-encoder box: ce_box.py / ce_llm_st.py only
#
# Expects the repository at $ROOT/repo (streamed from the laptop, including experiments/ameya/model-v1/stack/).
# Verified requirements (see experiments/bakshi/final-package/requirements.txt and RECIPE.md):
#   - s1.py and s2.py hard-code XGBoost "device": "cuda", so the MAIN box needs a CUDA GPU too;
#   - ce.train_one has the non-finite-gradient guard that torch 2.11 needs;
#   - mDeBERTa-v3 needs sentencepiece; gte-multilingual needs trust_remote_code.
#
# Torch: the Vast PyTorch image ships a CUDA build of torch in /venv/main. The venv inherits it
# (--system-site-packages) and only replaces it with the CUDA 12.6 build if a real CUDA op fails -- e.g. a
# cu128 wheel on a host whose driver tops out at CUDA 12.7.
set -euo pipefail
ROLE="${1:?usage: setup.sh main|ce}"
ROOT="${ROOT:-/workspace/grenuke}"
cd "$ROOT"
[ -d repo ] || { echo "FAIL: $ROOT/repo missing -- stream the repository first"; exit 2; }
BASEPY="${BASEPY:-/venv/main/bin/python}"
[ -x "$BASEPY" ] || BASEPY="$(command -v python3)"
command -v uv >/dev/null || python3 -m pip install -q uv

[ -d .venv ] || uv venv -q --python "$BASEPY" --system-site-packages .venv
. .venv/bin/activate
# CPU stack pinned exactly as final-package/requirements.txt
uv pip install -q numpy==2.4.3 pandas==2.3.3 pyarrow==23.0.1 scipy==1.17.0 scikit-learn==1.8.0 \
  xgboost==3.2.0 rapidfuzz==3.14.6 numba==0.64.0 pytest==8.3.4
if ! python -c "import torch; x=torch.randn(256,256,device='cuda'); y=(x.bfloat16()@x.bfloat16()).float(); assert torch.isfinite(y).all()" 2>/dev/null; then
  echo "torch from the image cannot run a CUDA op here -> installing the CUDA 12.6 build"
  uv pip install -q torch --index-url https://download.pytorch.org/whl/cu126
fi
if [ "$ROLE" = ce ]; then
  uv pip install -q "transformers==5.17.0" "peft==0.21.0" sentencepiece protobuf tokenizers safetensors huggingface_hub hf_transfer
else
  uv pip install -q "transformers==5.17.0" sentencepiece protobuf
fi
uv pip install -q -e repo/code/business_entity_resolution

NT="${NTHREADS:-64}"   # cores ALLOCATED to the container, not nproc (nproc shows the whole host)
cat > "$ROOT/env.sh" <<EOF
. $ROOT/.venv/bin/activate
export BER_DATA_DIR=$ROOT/dataset
export BER_WORK_DIR=$ROOT/work
export BER_OUTPUT_DIR=$ROOT/output
export CE_BOX_DIR=$ROOT/box
export M=$ROOT/repo/experiments/ameya/model-v1
export B=$ROOT/repo/experiments/bakshi
export PYTHONPATH=$ROOT/repo/experiments/ameya/model-v1:$ROOT/repo/code/business_entity_resolution/src
export NUMBA_NUM_THREADS=$NT OMP_NUM_THREADS=$NT MKL_NUM_THREADS=$NT OPENBLAS_NUM_THREADS=$NT POLARS_MAX_THREADS=$NT
export RAYON_NUM_THREADS=$NT TOKENIZERS_PARALLELISM=true
export HF_HUB_ENABLE_HF_TRANSFER=\$(python -c "import hf_transfer" 2>/dev/null && echo 1 || echo 0)
EOF
mkdir -p "$ROOT/work" "$ROOT/output" "$ROOT/box" "$ROOT/logs"
. "$ROOT/env.sh"

echo "== sanity =="
python - <<'EOF'
import xgboost, numba, pandas, pyarrow
print("xgboost", xgboost.__version__, "| cuda build:", xgboost.build_info().get("USE_CUDA"))
import torch; print("torch", torch.__version__, "| cuda:", torch.cuda.is_available(), "| gpus:", torch.cuda.device_count())
import transformers; print("transformers", transformers.__version__)
import ber, ber.pipeline; print("ber from", ber.__file__)
EOF
nvidia-smi --query-gpu=index,name,memory.total,driver_version --format=csv,noheader || echo "NO GPU"
echo "threads $NT | $(free -g | awk '/Mem:/{print $2" GB RAM (host)"}') | disk: $(df -h "$ROOT" | awk 'NR==2{print $4" free"}')"
echo "setup done: . $ROOT/env.sh"
