"""LLM cross-encoder (LoRA) on a rented GPU: the same band, OOF groups, inputs and outputs as ce_box.py, with a small
decoder LLM (default Qwen/Qwen2.5-1.5B, Apache-2.0, 1.5B parameters) fine-tuned with LoRA as a sequence classifier.

    python experiments/sachi/ce_llm.py --model Qwen/Qwen2.5-1.5B --name q15 --smoke      # 5-minute check
    python experiments/sachi/ce_llm.py --model Qwen/Qwen2.5-1.5B --name q15               # full run

Reads $CE_BOX_DIR/band_{train,test}.parquet (ce.band_pairs: s1, r, row, p1, fold, y) and tokenises exactly as
ce_box.py (ce.encode, so the text is identical). Writes $CE_BOX_DIR/out_<name>/ce_{train,test}.parquet
(row, ce__logit) + config.json, so ce_import.py takes it as one more stage-2 group:
    python ce_import.py --feats ameya-fx5 --src <out_q15> --group ceq --column ceq__logit
OOF like ce_box.py: 3 models (one per OOF group), each scores its own group, the holdout and test get the mean.
Resumable per group (checkpoint.npz). --train-frac subsamples each model's training rows to save time.
Licence check: Qwen2.5-0.5B / 1.5B / 7B are Apache-2.0 (3B is NOT); Mistral-7B-v0.3 is Apache-2.0. Keep <= 8B.
"""
import argparse
import json
import logging
import math
import os
import time

import numpy as np
import pandas as pd
import torch
from peft import LoraConfig, get_peft_model
from sklearn.metrics import roc_auc_score
from transformers import AutoModelForSequenceClassification, AutoTokenizer

import ce
from ber.eval.splits import oof_group

log = logging.getLogger("ce_llm")
BOX = os.environ.get("CE_BOX_DIR", "/workspace/grenuke/box")
DEV = torch.device("cuda")


def batches_by_length(idx: np.ndarray, lens: np.ndarray, bs: int, rng=None):
    """Batches of similar length (less padding); shuffled batch order when rng is given."""
    order = idx[np.argsort(lens[idx], kind="stable")]
    chunks = [order[i:i + bs] for i in range(0, order.size, bs)]
    if rng is not None:
        rng.shuffle(chunks)
    return chunks


def collate(enc, rows, pad):
    seqs = [enc[i] for i in rows]
    L = max(len(s) for s in seqs)
    ids = torch.full((len(seqs), L), pad, dtype=torch.long)
    att = torch.zeros((len(seqs), L), dtype=torch.long)
    for k, s in enumerate(seqs):
        ids[k, :len(s)] = torch.tensor(s, dtype=torch.long)
        att[k, :len(s)] = 1
    return ids.to(DEV), att.to(DEV)


def build(model_name: str, pad: int, a):
    m = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=1, torch_dtype=torch.bfloat16)
    m.config.pad_token_id = pad
    cfg = LoraConfig(r=a.lora_r, lora_alpha=2 * a.lora_r, lora_dropout=0.05, task_type="SEQ_CLS",
                     target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"])
    m = get_peft_model(m, cfg)
    for p in m.parameters():  # trainable weights (LoRA + score head) in fp32 for a stable optimiser
        if p.requires_grad:
            p.data = p.data.float()
    if a.grad_ckpt:
        m.gradient_checkpointing_enable()
        m.enable_input_require_grads()
    return m.to(DEV)


def train_one(model_name, enc, lens, y, rows, pad, a):
    torch.manual_seed(a.seed)
    rng = np.random.default_rng(a.seed)
    m = build(model_name, pad, a)
    params = [p for p in m.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=a.lr, weight_decay=0.0)
    chunks = [c for _ in range(a.epochs) for c in batches_by_length(rows, lens, a.batch, rng)]
    steps, warm = len(chunks), max(1, int(0.03 * len(chunks)))
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / warm) * max(0.0, 1 - s / steps))
    lossf = torch.nn.BCEWithLogitsLoss()
    yt = torch.tensor(y, dtype=torch.float32)
    m.train()
    t0 = time.perf_counter()
    for k, c in enumerate(chunks):
        ids, att = collate(enc, c, pad)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            out = m(input_ids=ids, attention_mask=att).logits.squeeze(-1)
        loss = lossf(out.float(), yt[c].to(DEV))
        loss.backward()
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        opt.step(); sched.step(); opt.zero_grad(set_to_none=True)
        if k % 200 == 0:
            el = time.perf_counter() - t0
            log.info("  step %d/%d loss %.4f (%.0fs, eta %.1f min)", k, steps, loss.item(), el,
                     el / (k + 1) * (steps - k - 1) / 60)
    return m


@torch.no_grad()
def predict(m, enc, lens, rows, pad, bs):
    m.eval()
    out = np.empty(rows.size, np.float32)
    pos = {r: i for i, r in enumerate(rows)}
    for c in batches_by_length(rows, lens, bs):
        ids, att = collate(enc, c, pad)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            v = m(input_ids=ids, attention_mask=att).logits.squeeze(-1).float().cpu().numpy()
        out[[pos[r] for r in c]] = v
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-1.5B")
    ap.add_argument("--name", required=True)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--max-len", type=int, default=96)
    ap.add_argument("--lora-r", type=int, default=16)
    ap.add_argument("--train-frac", type=float, default=1.0)
    ap.add_argument("--grad-ckpt", action="store_true")
    ap.add_argument("--seed", type=int, default=26)
    ap.add_argument("--smoke", action="store_true", help="group 0 only, 3000 training rows, 3000 scored rows")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    torch.backends.cuda.matmul.allow_tf32 = True
    ce.MAX_LEN, ce.SEED = a.max_len, a.seed
    out = f"{BOX}/out_{a.name}" + ("_smoke" if a.smoke else "")
    os.makedirs(out, exist_ok=True)
    t0 = time.perf_counter()
    tok = AutoTokenizer.from_pretrained(a.model)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    pad = tok.pad_token_id
    tr = pd.read_parquet(f"{BOX}/band_train.parquet")
    te = pd.read_parquet(f"{BOX}/band_test.parquet")
    enc, lens = ce.encode(tok, "train", tr)
    enc_t, lens_t = ce.encode(tok, "test", te)
    lens, lens_t = np.asarray(lens), np.asarray(lens_t)
    fold, y = tr["fold"].to_numpy(), tr["y"].to_numpy()
    train_rows = fold >= 5
    grp = np.where(train_rows, oof_group(np.where(train_rows, tr["s1"].to_numpy(), 0)), -1)
    log.info("band: train %d (%.3f positive), test %d; tokens p50 %d (%.0fs)", len(tr), y.mean(), len(te),
             np.median(lens), time.perf_counter() - t0)
    rng = np.random.default_rng(a.seed)
    logit = np.full(len(tr), np.nan, np.float32)
    hold = np.flatnonzero(~train_rows)
    test_rows = np.arange(len(te))
    if a.smoke:
        hold = rng.choice(hold, min(3000, hold.size), replace=False)
        test_rows = test_rows[:3000]
    hold_sum = np.zeros(hold.size, np.float32)
    test_sum = np.zeros(test_rows.size, np.float32)
    done = []
    ck = f"{out}/checkpoint.npz"
    if os.path.exists(ck) and not a.smoke:
        z = np.load(ck)
        logit, hold_sum, test_sum, done = z["logit"], z["hold_sum"], z["test_sum"], list(z["done"])
        log.info("resuming: groups done %s", done)
    groups = [0] if a.smoke else [0, 1, 2]
    for g in groups:
        if g in done:
            continue
        fit = np.flatnonzero(train_rows & (grp != g))
        if a.smoke:
            fit = rng.choice(fit, min(3000, fit.size), replace=False)
        elif a.train_frac < 1:
            fit = rng.choice(fit, int(fit.size * a.train_frac), replace=False)
        m = train_one(a.model, enc, lens, y, fit, pad, a)
        own = np.flatnonzero(train_rows & (grp == g))
        if a.smoke:
            own = rng.choice(own, min(3000, own.size), replace=False)
        logit[own] = predict(m, enc, lens, own, pad, 2 * a.batch)
        hold_sum += predict(m, enc, lens, hold, pad, 2 * a.batch)
        test_sum += predict(m, enc_t, lens_t, test_rows, pad, 2 * a.batch)
        del m
        torch.cuda.empty_cache()
        done.append(g)
        if not a.smoke:
            np.savez(ck, logit=logit, hold_sum=hold_sum, test_sum=test_sum, done=np.array(done))
        log.info("group %d: trained on %d pairs; OOF AUC %.4f (%.0fs)", g, fit.size,
                 roc_auc_score(y[own], logit[own]), time.perf_counter() - t0)
    n = len(groups)
    auc = {"holdout": float(roc_auc_score(y[hold], hold_sum / n))}
    if "p1" in tr:
        auc["holdout_p1"] = float(roc_auc_score(y[hold], tr["p1"].to_numpy()[hold]))
    if not a.smoke:
        logit[hold] = hold_sum / n
        auc["oof"] = float(roc_auc_score(y[train_rows], logit[train_rows]))
        pd.DataFrame({"row": tr["row"].to_numpy(), "ce__logit": logit}).to_parquet(f"{out}/ce_train.parquet", index=False)
        pd.DataFrame({"row": te["row"].to_numpy(), "ce__logit": test_sum / n}).to_parquet(f"{out}/ce_test.parquet", index=False)
    log.info("AUC in the band: %s  (compare: e5-large holdout 0.9391, e5-small 0.9240, stage-1 p1 0.9297)", auc)
    json.dump({"model": a.model, "lora_r": a.lora_r, "lr": a.lr, "batch": a.batch, "epochs": a.epochs,
               "max_len": a.max_len, "train_frac": a.train_frac, "smoke": a.smoke, "auc": auc,
               "train_band": len(tr), "test_band": len(te), "seconds": time.perf_counter() - t0},
              open(f"{out}/config.json", "w"), indent=1)
    log.info("done in %.0fs", time.perf_counter() - t0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
