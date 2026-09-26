"""Cross-encoder on the uncertain band (gate G10), written as a feature group for stage 2.

    python experiments/ameya/model-v1/ce.py --feats ameya-fx3 --s1 ameya-s1-v3 --tag ameya-ce-v1

- Model: intfloat/multilingual-e5-small (MIT, 118M parameters; Indic scripts and French are in its vocabulary) with
  a fresh one-logit head, fine-tuned here on our train pairs only.
- Band: stage-1 rows (p0 >= tau0) with LO <= p1 <= HI. The same rule selects the pairs on train and test; the
  other rows get NaN (stage 2 learns what NaN means from the same rule on train).
- Text: "<name> ; <address>" for each side, the S1 first, encoded jointly and truncated to MAX_LEN tokens.
- Out of fold (C2): model g is trained on the band pairs of the training folds outside OOF group g (``EPOCHS`` epochs,
  AdamW, linear decay, bf16) and scores group g; the holdout and test get the mean logit of the 3 models.
Writes work/features/<feats>-ce/<split>.parquet (column ce__logit), row-aligned with <feats>-str, so stage 2 takes it
with ``--groups ...,ce --extra ce__logit``.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import time

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from ber.artifacts import provenance, read_table
from ber.eval.splits import oof_group
from ber.paths import artifact_dir, artifact_path, records_path

log = logging.getLogger("ce")
LO, HI = 0.02, 0.99
MAX_LEN = 96
BATCH = 128
EPOCHS = 1
LR = 5e-5
SEED = 26


def band_pairs(s1_tag: str, split: str, sample: float = 1.0) -> pd.DataFrame:
    cfg = json.loads((artifact_dir("models", s1_tag) / "config.json").read_text())
    cols = ["s1", "r", "p0", "p1"] + (["fold", "y"] if split == "train" else [])
    sc = read_table("scores", s1_tag, split, cols)
    band = (sc["p0"].to_numpy() >= cfg["tau0"]) & (sc["p1"].to_numpy() >= LO) & (sc["p1"].to_numpy() <= HI)
    if sample < 1.0:  # smoke tests only
        band &= np.random.default_rng(SEED).random(band.size) < sample
    out = sc.loc[band].copy()
    out["row"] = np.flatnonzero(band)
    return out.reset_index(drop=True)


def encode(tok, split: str, pairs: pd.DataFrame) -> tuple[list, np.ndarray]:
    ids = np.unique(np.concatenate([pairs["s1"].to_numpy(), pairs["r"].to_numpy()]))
    parts = []  # read in batches and keep only the needed records (low memory)
    for b in pq.ParquetFile(records_path(split)).iter_batches(batch_size=1_000_000, columns=["eid", "name", "address"]):
        m = np.isin(b.column(0).to_numpy(), ids)
        if m.any():
            parts.append(b.filter(pa.array(m)).to_pandas())
    t = pd.concat(parts).set_index("eid")
    text = (t["name"].fillna("") + " ; " + t["address"].fillna("")).str.slice(0, 300)
    del t, parts
    a, b = text.reindex(pairs["s1"]).tolist(), text.reindex(pairs["r"]).tolist()
    enc = []
    for i in range(0, len(a), 100_000):
        e = tok(a[i:i + 100_000], b[i:i + 100_000], truncation="longest_first", max_length=MAX_LEN)["input_ids"]
        enc.extend(np.asarray(x, np.int32) for x in e)
    return enc, np.array([len(x) for x in enc], np.int32)


def _batch(enc, idx, pad_id):
    n = max(len(enc[i]) for i in idx)
    ids = np.full((len(idx), n), pad_id, np.int64)
    mask = np.zeros((len(idx), n), np.int64)
    for j, i in enumerate(idx):
        ids[j, :len(enc[i])] = enc[i]
        mask[j, :len(enc[i])] = 1
    return torch.from_numpy(ids).cuda(non_blocking=True), torch.from_numpy(mask).cuda(non_blocking=True)


def train_one(model_name: str, enc, lens, y, pad_id) -> torch.nn.Module:
    torch.manual_seed(SEED)
    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=1).cuda()
    rng = np.random.default_rng(SEED)
    # length-bucketed batches: sort by length inside random windows of 50 batches, then shuffle the batches
    order = rng.permutation(len(enc))
    win = BATCH * 50
    batches = []
    for s in range(0, len(order), win):
        w = order[s:s + win]
        w = w[np.argsort(lens[w], kind="stable")]
        batches.extend(w[i:i + BATCH] for i in range(0, len(w), BATCH))
    steps = len(batches) * EPOCHS
    opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.01)
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda k: min(1.0, (k + 1) / max(1, int(0.05 * steps))) * max(0.0, (steps - k) / steps))
    yt = torch.from_numpy(y.astype(np.float32))
    model.train()
    k, t0, run, skipped = 0, time.perf_counter(), 0.0, 0
    for ep in range(EPOCHS):
        for bi in rng.permutation(len(batches)):
            idx = batches[bi]
            ids, mask = _batch(enc, idx, pad_id)
            with torch.autocast("cuda", dtype=torch.bfloat16):
                logit = model(input_ids=ids, attention_mask=mask).logits.squeeze(-1)
            loss = torch.nn.functional.binary_cross_entropy_with_logits(logit.float(), yt[idx].cuda())
            loss.backward()
            gn = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            if torch.isfinite(gn):  # a rare non-finite gradient (seen with torch 2.11) would turn every weight into NaN
                opt.step()
                run = 0.98 * run + 0.02 * float(loss) if k else float(loss)
            else:
                skipped += 1
            sched.step()
            opt.zero_grad(set_to_none=True)
            k += 1
            if k % 1000 == 0:
                log.info("step %d/%d loss %.4f (%.0f pairs/s; %d non-finite steps skipped)", k, steps, run,
                         k * BATCH / (time.perf_counter() - t0), skipped)
    model.eval()
    return model


@torch.no_grad()
def predict(model, enc, lens, pad_id) -> np.ndarray:
    out = np.empty(len(enc), np.float32)
    order = np.argsort(lens, kind="stable")
    for i in range(0, len(order), 1024):
        idx = order[i:i + 1024]
        ids, mask = _batch(enc, idx, pad_id)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            out[idx] = model(input_ids=ids, attention_mask=mask).logits.squeeze(-1).float().cpu().numpy()
    return out


def write_group(feats: str, split: str, rows: np.ndarray, logit: np.ndarray, command: str) -> None:
    src = pq.ParquetFile(artifact_path("features", f"{feats}-str", split))
    full = np.full(src.metadata.num_rows, np.nan, np.float32)
    full[rows] = logit
    path = artifact_path("features", f"{feats}-ce", split)
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = provenance(command, {"features": f"{feats}-str"}, split=split, rows=int(full.size), kind="features",
                      tag=f"{feats}-ce", band=[LO, HI], max_len=MAX_LEN, epochs=EPOCHS)
    schema = pa.schema([("ce__logit", pa.float32())]).with_metadata({b"ber": json.dumps(meta).encode()})
    w = pq.ParquetWriter(str(path) + ".tmp", schema, compression="zstd")
    start = 0
    for g in range(src.num_row_groups):
        n = src.metadata.row_group(g).num_rows
        w.write_table(pa.table({"ce__logit": full[start:start + n]}, schema=schema), row_group_size=n)
        start += n
    w.close()
    os.replace(str(path) + ".tmp", path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--feats", required=True)
    ap.add_argument("--s1", required=True)
    ap.add_argument("--tag", default="ameya-ce-v1")
    ap.add_argument("--model", default="intfloat/multilingual-e5-small")
    ap.add_argument("--limit", type=int, default=0, help="train on at most N pairs per model (smoke test)")
    ap.add_argument("--sample", type=float, default=1.0, help="keep this share of the band pairs (smoke test)")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    command = "python experiments/ameya/model-v1/ce.py " + " ".join(f"--{k} {v}" for k, v in vars(args).items())
    t0 = time.perf_counter()
    tok = AutoTokenizer.from_pretrained(args.model)
    pad = tok.pad_token_id

    tr = band_pairs(args.s1, "train", args.sample)
    enc, lens = encode(tok, "train", tr)
    fold, y = tr["fold"].to_numpy(), tr["y"].to_numpy()
    train_rows = fold >= 5
    grp = np.where(train_rows, oof_group(np.where(train_rows, tr["s1"].to_numpy(), 0)), -1)
    log.info("train band: %d pairs (%.3f positive), tokens p50 %d (%.0fs)", len(tr), y.mean(), np.median(lens),
             time.perf_counter() - t0)
    te = band_pairs(args.s1, "test", args.sample)
    enc_t, lens_t = encode(tok, "test", te)
    log.info("test band: %d pairs (%.0fs)", len(te), time.perf_counter() - t0)

    logit = np.full(len(tr), np.nan, np.float32)
    hold = np.flatnonzero(~train_rows)
    hold_sum = np.zeros(hold.size, np.float32)
    test_sum = np.zeros(len(te), np.float32)
    out_dir = artifact_dir("models", args.tag)
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    for g in range(3):
        fit = np.flatnonzero(train_rows & (grp != g))
        if args.limit:
            fit = rng.choice(fit, min(args.limit, fit.size), replace=False)
        model = train_one(args.model, [enc[i] for i in fit], lens[fit], y[fit], pad)
        own = np.flatnonzero(train_rows & (grp == g))
        logit[own] = predict(model, [enc[i] for i in own], lens[own], pad)
        hold_sum += predict(model, [enc[i] for i in hold], lens[hold], pad)
        test_sum += predict(model, enc_t, lens_t, pad)
        del model
        torch.cuda.empty_cache()
        from sklearn.metrics import roc_auc_score
        log.info("group %d: trained on %d pairs; OOF AUC %.4f (%.0fs)", g, fit.size,
                 roc_auc_score(y[own], logit[own]), time.perf_counter() - t0)
    logit[hold] = hold_sum / 3
    from sklearn.metrics import roc_auc_score
    auc = {"oof": float(roc_auc_score(y[train_rows], logit[train_rows])),
           "holdout": float(roc_auc_score(y[hold], logit[hold])),
           "holdout_p1": float(roc_auc_score(y[hold], tr["p1"].to_numpy()[hold]))}
    log.info("AUC in the band: %s", auc)
    write_group(args.feats, "train", tr["row"].to_numpy(), logit, command)
    write_group(args.feats, "test", te["row"].to_numpy(), test_sum / 3, command)
    (out_dir / "config.json").write_text(json.dumps({"model": args.model, "band": [LO, HI], "max_len": MAX_LEN,
                                                     "epochs": EPOCHS, "lr": LR, "batch": BATCH, "auc": auc,
                                                     "train_band": len(tr), "test_band": len(te)}, indent=1))
    log.info("done in %.0fs", time.perf_counter() - t0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
