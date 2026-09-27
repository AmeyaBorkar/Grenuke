#!/usr/bin/env python3
"""ONE out-of-fold group of ce_llm_st.py's France self-trained LLM cross-encoder, on one GPU.

ce_llm_st.py trains its three OOF-group models one after another. For a 7B model that is ~7 h on one H100, so the
three groups run here as three processes on three GPUs, and llm_merge.py joins their parts into exactly the files
ce_llm_st.py would have written. The recipe is unchanged -- same rows, same seeds:

- layout() is ce_llm_st.main's index arithmetic verbatim (band, pseudo-label merge on (s1, r), target third
  fold_of % 3, holdout rows, other test rows);
- the labelled training subsample of group g is drawn after REPLAYING the draws of groups < g from the same
  np.random.default_rng(seed), which is what the sequential loop consumes before it reaches group g;
- training is ce_llm_st.train_one (Sachi's ce_llm LoRA build + the non-finite-gradient guard), prediction is
  ce_llm.predict.

Only the inference batch may differ (--infer-batch, default 2 * --batch as in ce_llm_st); it changes nothing but
bf16 rounding.

Crash safety (the training box is interruptible):
- during training, a checkpoint every --ckpt-every seconds (out_<name>/ckpt_<g>.pt: trainable weights, optimiser,
  scheduler, step, torch CPU/CUDA RNG), written to a temp file and renamed, so it is never half-written. A rerun
  rebuilds the model from the same seed, loads the checkpoint and skips the batches already done -- the batch order
  is fixed by the seed -- so it continues the same run rather than starting a new one;
- the LoRA adapter is saved as soon as training ends (out_<name>/adapter_<g>/, DONE marker; the checkpoint is then
  deleted) and each of the four prediction sets is saved as it completes (out_<name>/g<g>_<set>.npy), so a rerun
  never retrains a finished group;
- the part is written last (out_<name>/part_<g>.npz); a rerun with the part present does nothing.
The training loop is ce_llm_st.train_one's, step for step (same build, optimiser, schedule, loss, gradient clip and
non-finite-gradient guard), with the checkpoint added.

    CUDA_VISIBLE_DEVICES=0 python llm_group.py --model Qwen/Qwen2.5-7B --name q7st --group 0 \
        --pseudo $CE_BOX_DIR/pseudo_fr_v7sq.parquet [--infer-batch 256] [--smoke]

--smoke runs the identical code on a 20k/20k random sample of the band into out_<name>_smoke (a ~3-minute check of
the GPU path: model load, LoRA, train steps, adapter save, all four predictions, part file, and llm_merge --smoke).
Needs PYTHONPATH with experiments/ameya/model-v1 and the ber package; $CE_BOX_DIR holds band_{train,test}.parquet.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ameya", "model-v1"))

from ber.eval.splits import fold_of, oof_group  # noqa: E402

log = logging.getLogger("llm_group")
BOX = os.environ.get("CE_BOX_DIR", "/workspace/grenuke/box")
GROUPS = (0, 1, 2)
SMOKE_N = 20_000


def parser() -> argparse.ArgumentParser:
    """ce_llm_st.py's arguments (same defaults) plus --group / --infer-batch."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-1.5B")
    ap.add_argument("--name", required=True)
    ap.add_argument("--pseudo", required=True, help="parquet (s1, r, y) of target-country band pairs")
    ap.add_argument("--sep", default=" || ")
    ap.add_argument("--us-in-frac", type=float, default=0.5)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--max-len", type=int, default=96)
    ap.add_argument("--lora-r", type=int, default=16)
    ap.add_argument("--grad-ckpt", action="store_true")
    ap.add_argument("--seed", type=int, default=26)
    ap.add_argument("--smoke", action="store_true", help=f"{SMOKE_N:,}/{SMOKE_N:,} band sample, out_<name>_smoke")
    return ap


def out_dir(name: str, smoke: bool) -> str:
    return f"{BOX}/out_{name}" + ("_smoke" if smoke else "")


def layout(pseudo: str, smoke: bool = False) -> dict:
    """ce_llm_st.main's index sets, without tokenising (shared with llm_merge.py)."""
    tr = pd.read_parquet(f"{BOX}/band_train.parquet")
    te = pd.read_parquet(f"{BOX}/band_test.parquet")
    if smoke:
        rs = np.random.default_rng(0)
        tr = tr.iloc[np.sort(rs.choice(len(tr), SMOKE_N, replace=False))].reset_index(drop=True)
        te = te.iloc[np.sort(rs.choice(len(te), SMOKE_N, replace=False))].reset_index(drop=True)
    fold, y = tr["fold"].to_numpy(), tr["y"].to_numpy()
    train_rows = fold >= 5
    grp = np.where(train_rows, oof_group(np.where(train_rows, tr["s1"].to_numpy(), 0)), -1)
    ps = te[["s1", "r"]].reset_index().merge(pd.read_parquet(pseudo), on=["s1", "r"])
    tgt, tgt_y = ps["index"].to_numpy(), ps["y"].to_numpy()
    tgt_g = (fold_of(ps["s1"].to_numpy()) % 3).astype(np.int64)
    rest_t = np.setdiff1d(np.arange(len(te)), tgt)
    hold = np.flatnonzero(~train_rows)
    return {"tr": tr, "te": te, "y": y, "train_rows": train_rows, "grp": grp, "tgt": tgt, "tgt_y": tgt_y,
            "tgt_g": tgt_g, "rest_t": rest_t, "hold": hold}


def fit_rows(L: dict, us_in_frac: float, seed: int, g: int) -> np.ndarray:
    """Group g's labelled training rows, drawn exactly where the sequential loop draws them."""
    rng = np.random.default_rng(seed)
    for gg in GROUPS:
        fit = np.flatnonzero(L["train_rows"] & (L["grp"] != gg))
        if us_in_frac < 1:
            fit = rng.choice(fit, int(fit.size * us_in_frac), replace=False)
        if gg == g:
            return fit
    raise ValueError(f"group {g} not in {GROUPS}")


def own_rows(L: dict, g: int) -> tuple[np.ndarray, np.ndarray]:
    """(labelled OOF rows scored by group g, target test rows scored by group g)."""
    return np.flatnonzero(L["train_rows"] & (L["grp"] == g)), L["tgt"][L["tgt_g"] == g]


def train_ckpt(model_name, enc, lens, y, rows, pad, a, ck: str):
    """ce_llm_st.train_one with a resumable checkpoint every a.ckpt_every seconds (0: every 25 steps, for smoke)."""
    import torch
    import ce_llm_st
    ce_llm = ce_llm_st.ce_llm
    torch.manual_seed(a.seed)
    rng = np.random.default_rng(a.seed)
    m = ce_llm.build(model_name, pad, a)
    named = [(n, p) for n, p in m.named_parameters() if p.requires_grad]
    names, params = [n for n, _ in named], [p for _, p in named]
    opt = torch.optim.AdamW(params, lr=a.lr, weight_decay=0.0)
    chunks = [c for _ in range(a.epochs) for c in ce_llm.batches_by_length(rows, lens, a.batch, rng)]
    steps, warm = len(chunks), max(1, int(0.03 * len(chunks)))
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / warm) * max(0.0, 1 - s / steps))
    lossf = torch.nn.BCEWithLogitsLoss()
    yt = torch.tensor(y, dtype=torch.float32)
    start, skipped = 0, 0
    if os.path.exists(ck):
        st = torch.load(ck, map_location="cpu", weights_only=False)
        if st["steps"] != steps or st["names"] != names or st["rows"] != int(rows.size):
            raise SystemExit(f"FAIL: {ck} belongs to a different run (steps/params/rows differ); move it away")
        with torch.no_grad():
            for p, t in zip(params, st["weights"]):
                p.copy_(t.to(p.device, p.dtype))
        opt.load_state_dict(st["opt"])
        sched.load_state_dict(st["sched"])
        torch.set_rng_state(st["rng_cpu"])
        torch.cuda.set_rng_state(st["rng_cuda"])
        start, skipped = int(st["step"]), int(st["skipped"])
        log.info("RESUMED training at step %d/%d from %s", start, steps, ck)

    def save(k: int) -> None:
        st = {"step": k, "steps": steps, "rows": int(rows.size), "skipped": skipped, "names": names,
              "weights": [p.detach().cpu() for p in params], "opt": opt.state_dict(), "sched": sched.state_dict(),
              "rng_cpu": torch.get_rng_state(), "rng_cuda": torch.cuda.get_rng_state()}
        torch.save(st, ck + ".tmp")
        os.replace(ck + ".tmp", ck)
        log.info("  checkpoint at step %d/%d -> %s", k, steps, ck)

    m.train()
    t0 = last = time.perf_counter()
    for k in range(start, steps):
        c = chunks[k]
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
        done = k + 1 - start
        if k % 200 == 0 or done == 20:
            el = time.perf_counter() - t0
            log.info("  step %d/%d loss %.4f (%.0fs, %.2f steps/s, eta %.1f min, %d skipped)", k, steps, loss.item(), el,
                     done / el, el / done * (steps - k - 1) / 60, skipped)
        due = (done % 25 == 0) if a.ckpt_every == 0 else (time.perf_counter() - last >= a.ckpt_every)
        if due and k + 1 < steps:
            save(k + 1)
            last = time.perf_counter()
            if a.die_at_step and k + 1 >= a.die_at_step:
                log.info("--die-at-step %d: exiting to test the resume path", a.die_at_step)
                raise SystemExit(3)
    return m


def main() -> int:
    ap = parser()
    ap.add_argument("--group", type=int, required=True, choices=GROUPS)
    ap.add_argument("--infer-batch", type=int, default=0, help="prediction batch (default 2 * --batch)")
    ap.add_argument("--ckpt-every", type=int, default=600, help="seconds between training checkpoints (0: every 25 steps)")
    ap.add_argument("--die-at-step", type=int, default=0, help="testing only: exit after the first checkpoint at/after this step")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format=f"%(asctime)s g{a.group} %(message)s", datefmt="%H:%M:%S")

    import torch
    from transformers import AutoTokenizer

    import ce
    import ce_llm_st
    ce_llm = ce_llm_st.ce_llm

    g = a.group
    out = out_dir(a.name, a.smoke)
    os.makedirs(out, exist_ok=True)
    part = f"{out}/part_{g}.npz"
    if os.path.exists(part):
        log.info("%s exists: group %d already done", part, g)
        return 0
    t0 = time.perf_counter()
    torch.backends.cuda.matmul.allow_tf32 = True
    ce.MAX_LEN, ce.SEED = a.max_len, a.seed
    tok = AutoTokenizer.from_pretrained(a.model)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    pad = tok.pad_token_id

    L = layout(a.pseudo, a.smoke)
    tr, te, y = L["tr"], L["te"], L["y"]
    tgt, tgt_y, tgt_g = L["tgt"], L["tgt_y"], L["tgt_g"]
    enc, lens = ce_llm_st.encode(tok, "train", tr, a.sep)
    enc_t, lens_t = ce_llm_st.encode(tok, "test", te, a.sep)
    n_tr = len(enc)
    enc_all, lens_all = enc + enc_t, np.r_[lens, lens_t]
    y_all = np.r_[y, np.zeros(len(te), y.dtype)]
    y_all[n_tr + tgt[tgt_y >= 0]] = tgt_y[tgt_y >= 0]
    log.info("band: train %d, test %d (target %d, %d labelled); tokens p50 %d (%.0fs)", len(tr), len(te), tgt.size,
             int((tgt_y >= 0).sum()), int(np.median(lens)), time.perf_counter() - t0)

    fit = fit_rows(L, a.us_in_frac, a.seed, g)
    pl = n_tr + tgt[(tgt_g != g) & (tgt_y >= 0)]
    ad = f"{out}/adapter_{g}"
    t1 = time.perf_counter()
    if os.path.exists(f"{ad}/DONE"):
        from peft import PeftModel
        from transformers import AutoModelForSequenceClassification
        base = AutoModelForSequenceClassification.from_pretrained(a.model, num_labels=1, torch_dtype=torch.bfloat16)
        base.config.pad_token_id = pad
        m = PeftModel.from_pretrained(base, ad).to(ce_llm.DEV)
        log.info("resumed: loaded the trained adapter %s", ad)
    else:
        ck = f"{out}/ckpt_{g}.pt"
        m = train_ckpt(a.model, enc_all, lens_all, y_all, np.r_[fit, pl], pad, a, ck)
        m.save_pretrained(ad)
        with open(f"{ad}/DONE", "w") as f:
            f.write(json.dumps({"fit": int(fit.size), "pseudo": int(pl.size), "seconds": time.perf_counter() - t1}))
        if os.path.exists(ck):
            os.remove(ck)
        log.info("trained on %d labelled + %d pseudo pairs in %.0fs (%.1f pairs/s); adapter saved", fit.size, pl.size,
                 time.perf_counter() - t1, (fit.size + pl.size) * a.epochs / (time.perf_counter() - t1))
    train_s = time.perf_counter() - t1

    ib = a.infer_batch or 2 * a.batch
    own, mine = own_rows(L, g)
    sets = {"own": (enc, lens, own), "hold": (enc, lens, L["hold"]), "rest": (enc_t, lens_t, L["rest_t"]),
            "mine": (enc_t, lens_t, mine)}
    pred = {}
    for k, (e, ln, rows) in sets.items():
        f = f"{out}/g{g}_{k}.npy"
        if os.path.exists(f):
            pred[k] = np.load(f)
            continue
        t2 = time.perf_counter()
        pred[k] = ce_llm.predict(m, e, ln, rows, pad, ib) if rows.size else np.zeros(0, np.float32)
        np.save(f, pred[k])
        log.info("predicted %-4s %9d pairs in %.0fs (%.0f pairs/s)", k, rows.size, time.perf_counter() - t2,
                 rows.size / max(time.perf_counter() - t2, 1e-9))

    from sklearn.metrics import roc_auc_score
    auc_own = float(roc_auc_score(y[own], pred["own"])) if np.unique(y[own]).size == 2 else float("nan")
    meta = {"model": a.model, "name": a.name, "pseudo": a.pseudo, "sep": a.sep, "us_in_frac": a.us_in_frac,
            "lora_r": a.lora_r, "lr": a.lr, "batch": a.batch, "epochs": a.epochs, "max_len": a.max_len,
            "grad_ckpt": a.grad_ckpt, "seed": a.seed, "smoke": a.smoke, "group": g, "infer_batch": ib,
            "fit": int(fit.size), "pseudo_rows": int(pl.size), "train_seconds": train_s,
            "seconds": time.perf_counter() - t0, "auc_own": auc_own}
    np.savez(part + ".tmp.npz", own=own, own_l=pred["own"], hold_l=pred["hold"], rest_l=pred["rest"], mine=mine,
             mine_l=pred["mine"], meta=np.array(json.dumps(meta)))
    os.replace(part + ".tmp.npz", part)
    log.info("group %d done: OOF AUC %.4f, %.0fs total -> %s", g, auc_own, time.perf_counter() - t0, part)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
