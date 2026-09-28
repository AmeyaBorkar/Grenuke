"""Cross-encoder on a rented GPU: the same band, OOF groups and training loop as ce.py, with a larger multilingual-e5
model. It reads the band pairs from $CE_BOX_DIR/band_{train,test}.parquet (exported locally from the stage-1 scores
with ce.band_pairs: s1, r, row, p1, fold, y) instead of the score tables, and writes $CE_BOX_DIR/out_<name>/
ce_{train,test}.parquet (row, ce__logit) and config.json, which ce_import.py turns into a stage-2 feature group.

    python experiments/ameya/model-v1/ce_box.py --model intfloat/multilingual-e5-large --lr 2e-5 --name e5l
    python experiments/ameya/model-v1/ce_box.py --model intfloat/multilingual-e5-base --lr 3e-5 --name e5b

Models: intfloat/multilingual-e5-large (MIT, 560M parameters), intfloat/multilingual-e5-base (MIT, 278M).
26 Sep, one H100 80 GB (both runs together): e5-large 61 min, band AUC OOF 0.9350 / holdout 0.9391; e5-base 37 min,
0.9244 / 0.9287 (e5-small 0.9191 / 0.9240; stage-1 p1 on the holdout band 0.9297). Resumable per OOF group.

Self-training (``--pseudo``): test band pairs of the countries without labels (France), pseudo-labelled from a finished
chain's decisions (pseudo_labels.py: y 1/0, -1 unlabelled), join the training set, cross-fitted: their S1 are
split three ways (fold_of % 3); model g trains on the pseudo-labels of the other two thirds and alone scores the
target pairs of third g. The other test pairs get the mean of the three models, as before.
"""
import argparse
import json
import logging
import os
import time

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import roc_auc_score
from transformers import AutoTokenizer

import ce
from ber.eval.splits import fold_of, oof_group

log = logging.getLogger("ce_box")
BOX = os.environ.get("CE_BOX_DIR", "/workspace/grenuke/box")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--batch", type=int, default=128)
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--max-len", type=int, default=96)
    ap.add_argument("--seed", type=int, default=26)
    ap.add_argument("--pseudo", default="", help="parquet (s1, r, y) of target-country test band pairs: self-training")
    ap.add_argument("--only-group", type=int, default=-1,
                    help="fold-parallel: train and score only this OOF group (0-2) into checkpoint_g<G>.npz, then stop")
    ap.add_argument("--merge", action="store_true",
                    help="combine the three --only-group checkpoints and write the outputs as a resumed run")
    ap.add_argument("--us-in-frac", type=float, default=1.0,
                    help="train each group on this sample of the labelled rows (with all its pseudo-labelled rows)")
    ap.add_argument("--target-only-test", action="store_true",
                    help="score only the pseudo-labelled countries' test rows; other test rows get NaN")
    ap.add_argument("--hold-groups", default="0,1,2", help="groups whose model scores the holdout (their mean is kept)")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    torch.backends.cuda.matmul.allow_tf32 = True
    ce.LR, ce.BATCH, ce.EPOCHS, ce.MAX_LEN, ce.SEED = args.lr, args.batch, args.epochs, args.max_len, args.seed
    out = f"{BOX}/out_{args.name}"
    os.makedirs(out, exist_ok=True)
    t0 = time.perf_counter()
    tok = AutoTokenizer.from_pretrained(args.model)
    pad = tok.pad_token_id
    tr = pd.read_parquet(f"{BOX}/band_train.parquet")
    te = pd.read_parquet(f"{BOX}/band_test.parquet")
    enc, lens = ce.encode(tok, "train", tr)
    enc_t, lens_t = ce.encode(tok, "test", te)
    fold, y = tr["fold"].to_numpy(), tr["y"].to_numpy()
    train_rows = fold >= 5
    grp = np.where(train_rows, oof_group(np.where(train_rows, tr["s1"].to_numpy(), 0)), -1)
    tgt = np.array([], np.int64)
    if args.pseudo:  # target-country test pairs: positions in te, pseudo-labels, cross-fitting third
        ps = te[["s1", "r"]].reset_index().merge(pd.read_parquet(args.pseudo), on=["s1", "r"])
        tgt, tgt_y = ps["index"].to_numpy(), ps["y"].to_numpy()
        tgt_g = (fold_of(ps["s1"].to_numpy()) % 3).astype(np.int64)
        log.info("pseudo: %d target pairs, %d labelled (%.3f positive)", tgt.size, int((tgt_y >= 0).sum()),
                 float((tgt_y[tgt_y >= 0] == 1).mean()))
    rest_t = np.setdiff1d(np.arange(len(te)), tgt)
    log.info("band: train %d (%.3f positive), test %d; tokens p50 %d (%.0fs)", len(tr), y.mean(), len(te),
             np.median(lens), time.perf_counter() - t0)
    logit = np.full(len(tr), np.nan, np.float32)
    hold = np.flatnonzero(~train_rows)
    hold_sum = np.zeros(hold.size, np.float32)
    test_sum = np.zeros(len(te), np.float32)
    tgt_logit = np.full(len(te), np.nan, np.float32)
    done = []
    ck = f"{out}/checkpoint.npz"
    if args.merge:  # the three fold-parallel runs each hold one group's rows and one third of the sums
        zs = [np.load(f"{out}/checkpoint_g{g}.npz") for g in range(3)]
        for z in zs:
            k = ~np.isnan(z["logit"])
            logit[k] = z["logit"][k]
            k = ~np.isnan(z["tgt_logit"])
            tgt_logit[k] = z["tgt_logit"][k]
        np.savez(ck, logit=logit, hold_sum=sum(z["hold_sum"] for z in zs), test_sum=sum(z["test_sum"] for z in zs),
                 tgt_logit=tgt_logit, done=np.array([0, 1, 2]))
    if args.only_group >= 0:
        ck = f"{out}/checkpoint_g{args.only_group}.npz"
    if os.path.exists(ck):  # resume after a crash: groups already scored are kept
        z = np.load(ck)
        logit, hold_sum, test_sum, done = z["logit"], z["hold_sum"], z["test_sum"], list(z["done"])
        if "tgt_logit" in z:
            tgt_logit = z["tgt_logit"]
        log.info("resuming: groups done %s", done)
    hold_groups = [int(x) for x in args.hold_groups.split(",")]
    for g in range(3) if args.only_group < 0 else [args.only_group]:
        if g in done:
            continue
        fit = np.flatnonzero(train_rows & (grp != g))
        if args.us_in_frac < 1:
            fit = np.sort(np.random.default_rng(args.seed + g).choice(fit, int(fit.size * args.us_in_frac), replace=False))
        if tgt.size:
            pl = (tgt_g != g) & (tgt_y >= 0)
            model = ce.train_one(args.model, [enc[i] for i in fit] + [enc_t[i] for i in tgt[pl]],
                                 np.r_[lens[fit], lens_t[tgt[pl]]], np.r_[y[fit], tgt_y[pl]], pad)
        else:
            model = ce.train_one(args.model, [enc[i] for i in fit], lens[fit], y[fit], pad)
        own = np.flatnonzero(train_rows & (grp == g))
        logit[own] = ce.predict(model, [enc[i] for i in own], lens[own], pad)
        if g in hold_groups:
            hold_sum += ce.predict(model, [enc[i] for i in hold], lens[hold], pad)
        if not args.target_only_test:
            test_sum[rest_t] += ce.predict(model, [enc_t[i] for i in rest_t], lens_t[rest_t], pad)
        if tgt.size:
            mine = tgt[tgt_g == g]
            tgt_logit[mine] = ce.predict(model, [enc_t[i] for i in mine], lens_t[mine], pad)
        del model
        torch.cuda.empty_cache()
        done.append(g)
        np.savez(ck, logit=logit, hold_sum=hold_sum, test_sum=test_sum, tgt_logit=tgt_logit, done=np.array(done))
        log.info("group %d: trained on %d pairs; OOF AUC %.4f (%.0fs)", g, fit.size,
                 roc_auc_score(y[own], logit[own]), time.perf_counter() - t0)
    if args.only_group >= 0:
        log.info("group %d done; run --merge once all three groups are", args.only_group)
        return 0
    logit[hold] = hold_sum / len(hold_groups)
    auc = {"oof": float(roc_auc_score(y[train_rows], logit[train_rows])),
           "holdout": float(roc_auc_score(y[hold], logit[hold]))}
    if "p1" in tr:
        auc["holdout_p1"] = float(roc_auc_score(y[hold], tr["p1"].to_numpy()[hold]))
    log.info("AUC in the band: %s", auc)
    pd.DataFrame({"row": tr["row"].to_numpy(), "ce__logit": logit}).to_parquet(f"{out}/ce_train.parquet", index=False)
    test_logit = test_sum / 3
    if args.target_only_test:
        test_logit[rest_t] = np.nan
    test_logit[tgt] = tgt_logit[tgt]  # target pairs: the cross-fitted model's logit
    pd.DataFrame({"row": te["row"].to_numpy(), "ce__logit": test_logit}).to_parquet(f"{out}/ce_test.parquet", index=False)
    json.dump({"model": args.model, "pseudo": args.pseudo, "lr": args.lr, "batch": args.batch, "epochs": args.epochs, "max_len": args.max_len,
               "auc": auc, "train_band": len(tr), "test_band": len(te), "seconds": time.perf_counter() - t0},
              open(f"{out}/config.json", "w"), indent=1)
    log.info("done in %.0fs", time.perf_counter() - t0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
