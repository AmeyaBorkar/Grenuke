#!/usr/bin/env bash
# Training box (4x H100): France self-trained cross-encoders, trained on AMEYA's band (the pipeline side remaps the
# logits to our rebuild by (s1, r) with remap_ce.py). One OOF group per GPU via llm_group.py; llm_merge.py joins.
#
#   bash train_jobs.sh setup        # venv, packages, dataset -> records, model prefetch        (~10-15 min, once)
#   bash train_jobs.sh smoke        # the full group+merge path on a 20k/20k band sample, GPUs 0-2   (~3-5 min)
#   bash train_jobs.sh launch       # Qwen2.5-7B (q7st), groups 0,1,2 on GPUs 0,1,2 + auto-merge watcher
#   bash train_jobs.sh gpu3 q34     # Qwen3-4B-Base (q34st), groups 0,1,2 one after another on GPU 3, then merge
#   bash train_jobs.sh gpu3 small   # mDeBERTa-v3-base (mdbs) then gte-multilingual-reranker-base (gtes) on GPU 3
#   bash train_jobs.sh status       # progress of every job
#   bash train_jobs.sh merge NAME   # join the parts of a finished run by hand
#
# Expects under $ROOT: repo/ (code/business_entity_resolution, experiments/...), box/band_{train,test}.parquet and
# box/pseudo_fr_v7sq.parquet (+ pseudo_fr_v7ce3.parquet), and 6ab10eb3b23ba_student_resource.zip.
# Licences: Qwen2.5-7B, Qwen3-4B-Base Apache-2.0 (7.6B / 4.0B parameters); mDeBERTa-v3-base MIT;
# gte-multilingual-reranker-base Apache-2.0.
set -euo pipefail
ROOT="${ROOT:-/workspace/grenuke}"
CMD="${1:?usage: train_jobs.sh setup|smoke|launch|gpu3 q34|gpu3 small|status|merge NAME}"
LOGS="$ROOT/logs"
mkdir -p "$LOGS" "$ROOT/box" "$ROOT/work"

envs() {
  export PATH="$HOME/.local/bin:$PATH"
  [ -f "$ROOT/.venv/bin/activate" ] && . "$ROOT/.venv/bin/activate"
  export BER_DATA_DIR="$ROOT/student_resource/dataset" BER_WORK_DIR="$ROOT/work" BER_OUTPUT_DIR="$ROOT/output"
  export CE_BOX_DIR="$ROOT/box" HF_HOME="$ROOT/hf" TOKENIZERS_PARALLELISM=true
  export M="$ROOT/repo/experiments/ameya/model-v1" B="$ROOT/repo/experiments/bakshi"
  export PYTHONPATH="$M:$ROOT/repo/code/business_entity_resolution/src:${PYTHONPATH:-}"
  # round-2 teacher: v7sq-dpc, the best measured model (0.990545)
  export PSEUDO="$CE_BOX_DIR/pseudo_fr_v7sq.parquet"
}
envs
export Q7=Qwen/Qwen2.5-7B Q34=Qwen/Qwen3-4B-Base
export IB="${IB:-512}"   # prediction batch; only bf16 rounding depends on it

group() {  # name model gpu group [extra args]
  local name=$1 model=$2 gpu=$3 g=$4; shift 4
  CUDA_VISIBLE_DEVICES=$gpu python "$B/box/llm_group.py" --model "$model" --name "$name" --group "$g" \
    --pseudo "$PSEUDO" --infer-batch "$IB" "$@"
}

case "$CMD" in
setup)
  command -v uv >/dev/null 2>&1 || curl -LsSf https://astral.sh/uv/install.sh | sh || python3 -m pip install --break-system-packages -q uv
  export PATH="$HOME/.local/bin:$PATH"
  # Choose the torch build from the DRIVER, not from nvidia-smi's "CUDA Version": a container can report 12.8 through
  # the forward-compat library while the driver itself (e.g. 560.x) natively supports only CUDA 12.6.
  DRV=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1 | cut -d. -f1)
  if [ "$DRV" -ge 570 ]; then IDX=cu128; else IDX=cu126; fi
  echo "driver $DRV -> torch build $IDX"
  [ -d "$ROOT/.venv" ] || uv venv -q --python 3.12 "$ROOT/.venv"
  . "$ROOT/.venv/bin/activate"
  uv pip install -q "torch==2.11.0" --index-url "https://download.pytorch.org/whl/$IDX" \
    || uv pip install -q torch --index-url "https://download.pytorch.org/whl/$IDX"
  uv pip install -q numpy==2.4.3 pandas==2.3.3 pyarrow==23.0.1 scipy==1.17.0 scikit-learn==1.8.0 numba==0.64.0 \
    "transformers==5.17.0" "peft==0.21.0" sentencepiece protobuf tokenizers safetensors huggingface_hub accelerate
  uv pip install -q --no-deps -e "$ROOT/repo/code/business_entity_resolution"
  python -c "import torch, transformers, peft; print('torch', torch.__version__, 'cuda', torch.cuda.is_available(), torch.cuda.device_count(), 'gpus | transformers', transformers.__version__, '| peft', peft.__version__)"
  # models download while the records build (both are I/O bound on different ends)
  nohup python - > "$LOGS/prefetch.log" 2>&1 <<EOF &
from huggingface_hub import snapshot_download
for r in "${PREFETCH:-$Q7 $Q34 microsoft/mdeberta-v3-base Alibaba-NLP/gte-multilingual-reranker-base}".split():
    p = snapshot_download(r, allow_patterns=["*.json", "*.safetensors", "*.py", "*.txt", "*.model", "*.tiktoken", "tokenizer*", "spm*"])
    print("fetched", r, p, flush=True)
EOF
  if [ ! -d "$ROOT/student_resource/dataset/test" ]; then
    python - <<EOF
import zipfile
z = zipfile.ZipFile("$ROOT/6ab10eb3b23ba_student_resource.zip")
z.extractall("$ROOT", [n for n in z.namelist() if n.startswith("student_resource/dataset/") and not n.endswith(".DS_Store")])
EOF
  fi
  for s in train test; do
    [ -f "$BER_WORK_DIR/records/$s.parquet" ] || python -m ber.pipeline --stage records --split $s > "$LOGS/records_$s.log" 2>&1 &
  done
  wait
  ls -la "$BER_WORK_DIR/records"
  cat "$LOGS/prefetch.log"
  (cd "$CE_BOX_DIR" && sha256sum band_train.parquet band_test.parquet)
  echo "expected 876987f008c17901ff95ba6576657a479ee0992f184430401564edc06340080b band_train.parquet"
  echo "expected ec8d1db8dfe3e730bb2db006f2349ea2270691c4c3a8424409c5967ebd088355 band_test.parquet"
  ;;
smoke)
  rm -rf "$CE_BOX_DIR/out_q7st_smoke"
  # g0 is killed right after its checkpoint at step 25 (exit 3) and rerun, so the resume path is exercised for real
  ( set +e; group q7st "$Q7" 0 0 --smoke --ckpt-every 0 --die-at-step 25 > "$LOGS/smoke_g0a.log" 2>&1; rc=$?
    [ $rc = 3 ] || { echo "SMOKE FAIL: g0 first leg exit $rc (expected 3)"; exit 1; }
    group q7st "$Q7" 0 0 --smoke --ckpt-every 0 > "$LOGS/smoke_g0.log" 2>&1 ) &
  for g in 1 2; do group q7st "$Q7" $g $g --smoke --ckpt-every 0 > "$LOGS/smoke_g$g.log" 2>&1 & done
  wait
  grep -q "RESUMED training at step 25" "$LOGS/smoke_g0.log" || { echo "SMOKE FAIL: g0 did not resume from its checkpoint"; exit 1; }
  python "$B/box/llm_merge.py" --name q7st --smoke
  grep -h "trained on\|predicted\|group . done\|Error\|error" "$LOGS"/smoke_g*.log | tail -20 || true
  ;;
launch)
  for g in 0 1 2; do nohup bash -c "$(declare -f group); group q7st $Q7 $g $g" > "$LOGS/q7st_g$g.log" 2>&1 & done
  sleep 2
  nohup bash -c "until [ -f $CE_BOX_DIR/out_q7st/part_0.npz ] && [ -f $CE_BOX_DIR/out_q7st/part_1.npz ] && [ -f $CE_BOX_DIR/out_q7st/part_2.npz ]; do sleep 60; done; python $B/box/llm_merge.py --name q7st" > "$LOGS/q7st_merge.log" 2>&1 &
  echo "launched q7st on GPUs 0-2 (logs $LOGS/q7st_g*.log); merge watcher -> $LOGS/q7st_merge.log"
  ;;
gpu3)
  case "${2:?gpu3 q34|small}" in
    q34)
      nohup bash -c "$(declare -f group); set -e; for g in 0 1 2; do group q34st $Q34 3 \$g > $LOGS/q34st_g\$g.log 2>&1; done; python $B/box/llm_merge.py --name q34st > $LOGS/q34st_merge.log 2>&1" > "$LOGS/q34st_chain.log" 2>&1 &
      echo "launched q34st groups 0,1,2 sequentially on GPU 3" ;;
    small)
      nohup bash -c "CUDA_VISIBLE_DEVICES=3 python $M/ce_box.py --model microsoft/mdeberta-v3-base --name mdbs --lr 3e-5 --batch 128 --epochs 1 --seed 26 --pseudo $PSEUDO > $LOGS/mdbs.log 2>&1; CUDA_VISIBLE_DEVICES=3 python $B/box/ce_rc.py --model Alibaba-NLP/gte-multilingual-reranker-base --name gtes --lr 2e-5 --batch 128 --epochs 1 --seed 26 --pseudo $PSEUDO > $LOGS/gtes.log 2>&1" > "$LOGS/small_chain.log" 2>&1 &
      echo "launched mdbs then gtes on GPU 3" ;;
    *) echo "gpu3 q34|small" >&2; exit 2 ;;
  esac
  ;;
status)
  date
  nvidia-smi --query-gpu=index,utilization.gpu,memory.used --format=csv,noheader
  for f in "$LOGS"/q7st_g*.log "$LOGS"/q34st_g*.log "$LOGS"/mdbs.log "$LOGS"/gtes.log "$LOGS"/*merge.log; do
    [ -f "$f" ] && echo "== $(basename "$f"): $(grep -v Warning "$f" | tail -1 || true)" || true
  done
  ls "$CE_BOX_DIR"/out_*/part_*.npz "$CE_BOX_DIR"/out_*/ce_test.parquet 2>/dev/null || true
  ;;
merge)
  python "$B/box/llm_merge.py" --name "${2:?merge NAME}"
  ;;
run-group)  # NAME MODEL GPU GROUP: one llm_group.py run in the foreground
  group "${2:?name}" "${3:?model}" "${4:?gpu}" "${5:?group}"
  ;;
small)  # mdbs|gtes GPU: one small self-trained encoder (ce_box.py recipe, v7sq-dpc pseudo-labels) in the foreground
  case "${2:?mdbs|gtes}" in
    mdbs) CUDA_VISIBLE_DEVICES="${3:?gpu}" python "$M/ce_box.py" --model microsoft/mdeberta-v3-base --name mdbs \
            --lr 3e-5 --batch 128 --epochs 1 --seed 26 --pseudo "$PSEUDO" ;;
    gtes) CUDA_VISIBLE_DEVICES="${3:?gpu}" python "$B/box/ce_rc.py" --model Alibaba-NLP/gte-multilingual-reranker-base \
            --name gtes --lr 2e-5 --batch 128 --epochs 1 --seed 26 --pseudo "$PSEUDO" ;;
  esac
  ;;
after7b)  # replaces "gpu3 q34"'s sequential chain (kill that chain's bash first; its running group keeps going)
  bash "$B/box/sched_after7b.sh"
  ;;
*) echo "unknown command $CMD" >&2; exit 2 ;;
esac
