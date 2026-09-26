"""France self-trained LLM cross-encoder: Sachi's Qwen2.5 LoRA sequence classifier (experiments/sachi/ce_llm.py,
imported, unchanged) trained with the countries-without-labels pseudo-labels of ce_box.py --pseudo, a pair separator
and more weight on France.

    python experiments/ameya/model-v1/ce_llm_st.py --model Qwen/Qwen2.5-1.5B --name qst \
        --pseudo <pseudo_fr_v7ce3.parquet> --us-in-frac 0.5 [--smoke]

- Pairs are encoded as ce.encode's texts with --sep prepended to the record side (Qwen's tokenizer joins a text pair
  with no separator).
- Training rows per OOF group g: a --us-in-frac sample of the labelled band rows of the other groups, plus the
  pseudo-labelled target-country test pairs (pseudo_labels.py, band) whose S1 is not in third g (fold_of % 3).
- Scoring: labelled rows as ce_box.py (own group, holdout mean of 3); target-country test pairs by the model that did
  not see their third; other test pairs by the mean of the three models.
Writes $CE_BOX_DIR/out_<name>/ce_{train,test}.parquet (row, ce__logit) + config.json for ce_import.py / zmean_ce.py.
Model: Qwen/Qwen2.5-1.5B (Apache-2.0, 1.5B parameters).
"""
import argparse
import json
import logging
import os
import sys
import time

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import torch
from sklearn.metrics import roc_auc_score
from transformers import AutoTokenizer

import ce
from ber.eval.splits import fold_of, oof_group
from ber.paths import records_path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "sachi"))
import ce_llm  # noqa: E402  (Sachi's LoRA build / train / predict)

log = logging.getLogger("ce_llm_st")
BOX = os.environ.get("CE_BOX_DIR", "/workspace/grenuke/box")


def encode(tok, split: str, pairs: pd.DataFrame, sep: str) -> tuple[list, np.ndarray]:
    """ce.encode with a separator in front of the record text."""
    ids = np.unique(np.concatenate([pairs["s1"].to_numpy(), pairs["r"].to_numpy()]))
    parts = []
    for b in pq.ParquetFile(records_path(split)).iter_batches(batch_size=1_000_000, columns=["eid", "name", "address"]):
        m = np.isin(b.column(0).to_numpy(), ids)
        if m.any():
            parts.append(b.filter(pa.array(m)).to_pandas())
    t = pd.concat(parts).set_index("eid")
    text = (t["name"].fillna("") + " ; " + t["address"].fillna("")).str.slice(0, 300)
    del t, parts
    a = text.reindex(pairs["s1"]).tolist()
    b = [sep + x for x in text.reindex(pairs["r"]).tolist()]
    enc = []
    for i in range(0, len(a), 100_000):
        e = tok(a[i:i + 100_000], b[i:i + 100_000], truncation="longest_first", max_length=ce.MAX_LEN)["input_ids"]
        enc.extend(np.asarray(x, np.int32) for x in e)
    return enc, np.array([len(x) for x in enc], np.int32)


def train_one(model_name, enc, lens, y, rows, pad, a):
    """ce_llm.train_one with a guard: a step whose gradient is not finite is skipped (with torch 2.11 one such step
    turned every weight into NaN, see ce.train_one)."""
    torch.manual_seed(a.seed)
    rng = np.random.default_rng(a.seed)
    m = ce_llm.build(model_name, pad, a)
    params = [p for p in m.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=a.lr, weight_decay=0.0)
    chunks = [c for _ in range(a.epochs) for c in ce_llm.batches_by_length(rows, lens, a.batch, rng)]
    steps, warm = len(chunks), max(1, int(0.03 * len(chunks)))
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / warm) * max(0.0, 1 - s / steps))
    lossf = torch.nn.BCEWithLogitsLoss()
    yt = torch.tensor(y, dtype=torch.float32)
    m.train()
    t0, skipped = time.perf_counter(), 0
    for k, c in enumerate(chunks):
        ids, att = ce_llm.collate(enc, c, pad)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            out = m(input_ids=ids, attention_mask=att).logits.squeeze(-1)
        loss = lossf(out.float(), yt[c].to(ce_llm.DEV))
        loss.backward()
        gn = torch.nn.utils.clip_grad_norm_(params, 1.0)
        if torch.isfinite(gn):
            opt.step()
        else:
            skipped += 1
        sched.step()
        opt.zero_grad(set_to_none=True)
        if k % 500 == 0:
            el = time.perf_counter() - t0
            log.info("  step %d/%d loss %.4f (%.0fs, eta %.1f min, %d skipped)", k, steps, loss.item(), el,
                     el / (k + 1) * (steps - k - 1) / 60, skipped)
    return m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-1.5B")
    ap.add_argument("--name", required=True)
    ap.add_argument("--pseudo", required=True, help="parquet (s1, r, y) of target-country band pairs (pseudo_labels.py)")
    ap.add_argument("--sep", default=" || ")
    ap.add_argument("--us-in-frac", type=float, default=0.5, help="share of the labelled rows each model trains on")
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--max-len", type=int, default=96)
    ap.add_argument("--lora-r", type=int, default=16)
    ap.add_argument("--grad-ckpt", action="store_true")
    ap.add_argument("--seed", type=int, default=26)
    ap.add_argument("--smoke", action="store_true", help="group 0 only, 3000 rows of each kind")
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
    enc, lens = encode(tok, "train", tr, a.sep)
    enc_t, lens_t = encode(tok, "test", te, a.sep)
    n_tr = len(enc)
    enc_all, lens_all = enc + enc_t, np.r_[lens, lens_t]  # one index space: train rows, then test rows
    fold, y = tr["fold"].to_numpy(), tr["y"].to_numpy()
    train_rows = fold >= 5
    grp = np.where(train_rows, oof_group(np.where(train_rows, tr["s1"].to_numpy(), 0)), -1)
    ps = te[["s1", "r"]].reset_index().merge(pd.read_parquet(a.pseudo), on=["s1", "r"])
    tgt, tgt_y = ps["index"].to_numpy(), ps["y"].to_numpy()
    tgt_g = (fold_of(ps["s1"].to_numpy()) % 3).astype(np.int64)
    rest_t = np.setdiff1d(np.arange(len(te)), tgt)
    y_all = np.r_[y, np.zeros(len(te), y.dtype)]
    y_all[n_tr + tgt[tgt_y >= 0]] = tgt_y[tgt_y >= 0]
    log.info("band: train %d, test %d (target %d, %d labelled, %.3f positive); tokens p50 %d (%.0fs)", len(tr), len(te),
             tgt.size, int((tgt_y >= 0).sum()), float((tgt_y[tgt_y >= 0] == 1).mean()), np.median(lens),
             time.perf_counter() - t0)
    rng = np.random.default_rng(a.seed)
    logit = np.full(len(tr), np.nan, np.float32)
    hold = np.flatnonzero(~train_rows)
    if a.smoke:
        hold = rng.choice(hold, min(3000, hold.size), replace=False)
        rest_t = rest_t[:3000]
    hold_sum = np.zeros(hold.size, np.float32)
    test_sum = np.zeros(len(te), np.float32)
    tgt_logit = np.full(len(te), np.nan, np.float32)
    done = []
    ck = f"{out}/checkpoint.npz"
    if os.path.exists(ck) and not a.smoke:
        z = np.load(ck)
        logit, hold_sum, test_sum, tgt_logit, done = z["logit"], z["hold_sum"], z["test_sum"], z["tgt_logit"], list(z["done"])
        log.info("resuming: groups done %s", done)
    groups = [0] if a.smoke else [0, 1, 2]
    for g in groups:
        if g in done:
            continue
        fit = np.flatnonzero(train_rows & (grp != g))
        fit = rng.choice(fit, int(fit.size * a.us_in_frac), replace=False) if a.us_in_frac < 1 else fit
        pl = n_tr + tgt[(tgt_g != g) & (tgt_y >= 0)]
        if a.smoke:
            fit, pl = rng.choice(fit, 3000, replace=False), rng.choice(pl, 3000, replace=False)
        rows = np.r_[fit, pl]
        m = train_one(a.model, enc_all, lens_all, y_all, rows, pad, a)
        own = np.flatnonzero(train_rows & (grp == g))
        mine = tgt[tgt_g == g]
        if a.smoke:
            own, mine = rng.choice(own, 3000, replace=False), mine[:3000]
        logit[own] = ce_llm.predict(m, enc, lens, own, pad, 2 * a.batch)
        hold_sum += ce_llm.predict(m, enc, lens, hold, pad, 2 * a.batch)
        test_sum[rest_t] += ce_llm.predict(m, enc_t, lens_t, rest_t, pad, 2 * a.batch)
        tgt_logit[mine] = ce_llm.predict(m, enc_t, lens_t, mine, pad, 2 * a.batch)
        del m
        torch.cuda.empty_cache()
        done.append(g)
        if not a.smoke:
            np.savez(ck, logit=logit, hold_sum=hold_sum, test_sum=test_sum, tgt_logit=tgt_logit, done=np.array(done))
        log.info("group %d: trained on %d labelled + %d pseudo pairs; OOF AUC %.4f (%.0fs)", g, fit.size, pl.size,
                 roc_auc_score(y[own], logit[own]), time.perf_counter() - t0)
    n = len(groups)
    auc = {"holdout": float(roc_auc_score(y[hold], hold_sum / n))}
    if not a.smoke:
        logit[hold] = hold_sum / n
        auc["oof"] = float(roc_auc_score(y[train_rows], logit[train_rows]))
        test_logit = test_sum / n
        test_logit[tgt] = tgt_logit[tgt]
        pd.DataFrame({"row": tr["row"].to_numpy(), "ce__logit": logit}).to_parquet(f"{out}/ce_train.parquet", index=False)
        pd.DataFrame({"row": te["row"].to_numpy(), "ce__logit": test_logit}).to_parquet(f"{out}/ce_test.parquet", index=False)
    log.info("AUC in the band: %s", auc)
    json.dump({"model": a.model, "pseudo": a.pseudo, "sep": a.sep, "us_in_frac": a.us_in_frac, "lora_r": a.lora_r,
               "lr": a.lr, "batch": a.batch, "epochs": a.epochs, "max_len": a.max_len, "smoke": a.smoke, "auc": auc,
               "seconds": time.perf_counter() - t0}, open(f"{out}/config.json", "w"), indent=1)
    log.info("done in %.0fs", time.perf_counter() - t0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
