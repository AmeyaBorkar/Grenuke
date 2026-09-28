"""Cross-encoder trained on real band pairs (US/India) + synthetic French pairs (correct labels).

    python experiments/sachi/ce_synth.py --name cesy --smoke
    python experiments/sachi/ce_synth.py --name cesy

Reads $CE_BOX_DIR/band_{train,test}.parquet (real band) and $CE_BOX_DIR/band_synth.parquet +
records_synth.parquet (from synth_fr.py). Writes $CE_BOX_DIR/out_<name>/ce_{train,test}.parquet
+ config.json for ce_import.py --group cesy --column cesy__logit.
Gate: holdout AUC must not fall below e5-base 0.9287.
"""
import argparse, json, logging, math, os, time
import numpy as np, pandas as pd, torch
from sklearn.metrics import roc_auc_score
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import ce
from ber.eval.splits import oof_group

log = logging.getLogger("ce_synth")
BOX = os.environ.get("CE_BOX_DIR", "/workspace/grenuke/box")
GATE_AUC = 0.9287


def encode_synth(tok, synth_path, rec_path, smoke):
    band = pd.read_parquet(synth_path)
    if smoke:
        band = band.sample(min(3000, len(band)), random_state=0).reset_index(drop=True)
    band["row"] = np.arange(len(band))
    rec = pd.read_parquet(rec_path, columns=["eid", "name", "address"])
    text = (rec["name"].fillna("") + " ; " + rec["address"].fillna("")).str.slice(0, 300)
    text.index = rec["eid"].to_numpy()
    a_list = text.reindex(band["s1"]).tolist()
    b_list = text.reindex(band["r"]).tolist()
    enc = []
    for i in range(0, len(a_list), 50_000):
        e = tok(a_list[i:i+50_000], b_list[i:i+50_000],
                truncation="longest_first", max_length=ce.MAX_LEN)["input_ids"]
        enc.extend(np.asarray(x, np.int32) for x in e)
    lens = np.array([len(x) for x in enc], np.int32)
    log.info("synth: %d pairs (%.3f true); tokens p50 %d", len(band), band.y.mean(), np.median(lens))
    return enc, lens, band["y"].to_numpy(), band["fold"].to_numpy()


def train_weighted(model_name, all_enc, all_lens, all_y, pad_id, w):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.manual_seed(ce.SEED)
    m = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=1).to(device)
    opt = torch.optim.AdamW(m.parameters(), lr=ce.LR, weight_decay=0.01)
    N = len(all_enc)
    order = np.random.default_rng(ce.SEED).permutation(N)
    steps = math.ceil(N * ce.EPOCHS / ce.BATCH)
    warm = max(1, int(0.03 * steps))
    sched = torch.optim.lr_scheduler.LambdaLR(opt,
        lambda s: min(1.0, (s+1)/warm) * max(0.0, 1 - s/steps))
    yt = torch.tensor(all_y, dtype=torch.float32)
    wt = torch.tensor(w, dtype=torch.float32)
    m.train(); t0 = time.perf_counter(); pos = 0
    for step in range(steps):
        idx = order[pos:pos+ce.BATCH]; pos = (pos + ce.BATCH) % N
        seqs = [all_enc[i] for i in idx]
        L = max(len(s) for s in seqs)
        ids = torch.full((len(seqs), L), pad_id, dtype=torch.long, device=device)
        att = torch.zeros_like(ids)
        for k, s in enumerate(seqs):
            ids[k, :len(s)] = torch.tensor(s, dtype=torch.long)
            att[k, :len(s)] = 1
        out = m(input_ids=ids, attention_mask=att).logits.squeeze(-1)
        loss_vec = torch.nn.functional.binary_cross_entropy_with_logits(
            out, yt[idx].to(device), reduction="none")
        loss = (loss_vec * wt[idx].to(device)).mean()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(m.parameters(), 1.0)
        opt.step(); sched.step(); opt.zero_grad(set_to_none=True)
        if step % 200 == 0:
            el = time.perf_counter() - t0
            log.info("  step %d/%d loss %.4f (%.0fs, eta %.1f min)",
                     step, steps, loss.item(), el, el/(step+1)*(steps-step-1)/60)
    return m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="intfloat/multilingual-e5-large")
    ap.add_argument("--name", required=True)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--batch", type=int, default=128)
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--max-len", type=int, default=96)
    ap.add_argument("--seed", type=int, default=26)
    ap.add_argument("--synth-weight", type=float, default=1.0)
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    torch.backends.cuda.matmul.allow_tf32 = True
    ce.LR, ce.BATCH, ce.EPOCHS, ce.MAX_LEN, ce.SEED = a.lr, a.batch, a.epochs, a.max_len, a.seed
    out = f"{BOX}/out_{a.name}" + ("_smoke" if a.smoke else "")
    os.makedirs(out, exist_ok=True)
    t0 = time.perf_counter()

    tok = AutoTokenizer.from_pretrained(a.model)
    pad = tok.pad_token_id

    tr = pd.read_parquet(f"{BOX}/band_train.parquet")
    te = pd.read_parquet(f"{BOX}/band_test.parquet")
    if a.smoke:
        tr = tr.sample(min(3000, len(tr)), random_state=0).reset_index(drop=True)
        te = te.sample(min(3000, len(te)), random_state=0).reset_index(drop=True)
    enc_r, lens_r = ce.encode(tok, "train", tr)
    enc_t, lens_t = ce.encode(tok, "test", te)
    fold_r, y_r = tr["fold"].to_numpy(), tr["y"].to_numpy()
    train_rows = fold_r >= 5
    grp = np.where(train_rows, oof_group(np.where(train_rows, tr["s1"].to_numpy(), 0)), -1)
    hold = np.flatnonzero(~train_rows)
    log.info("real band: train %d (%.3f +), test %d; (%.0fs)",
             len(tr), y_r.mean(), len(te), time.perf_counter() - t0)

    synth_path = f"{BOX}/band_synth.parquet"
    rec_path   = f"{BOX}/records_synth.parquet"
    have_synth = os.path.exists(synth_path) and os.path.exists(rec_path)
    if have_synth:
        enc_s, lens_s, y_s, fold_s = encode_synth(tok, synth_path, rec_path, a.smoke)
    else:
        log.warning("no synth files -- running on real band only")
        enc_s, lens_s, y_s, fold_s = [], np.empty(0, np.float32), np.empty(0, np.float32), np.empty(0, np.float32)

    logit    = np.full(len(tr), np.nan, np.float32)
    hold_sum = np.zeros(hold.size, np.float32)
    test_sum = np.zeros(len(te),   np.float32)
    done = []
    ck = f"{out}/checkpoint.npz"
    if os.path.exists(ck):
        z = np.load(ck)
        logit, hold_sum, test_sum, done = z["logit"], z["hold_sum"], z["test_sum"], list(z["done"])
        log.info("resuming: groups done %s", done)

    for g in range(3):
        if g in done:
            continue
        fit_r = np.flatnonzero(train_rows & (grp != g))
        fit_s = np.flatnonzero(np.asarray(fold_s, dtype=int) % 3 != g) if have_synth else np.array([], dtype=int)
        n_r, n_s = len(fit_r), len(fit_s)
        log.info("group %d: %d real + %d synth", g, n_r, n_s)

        all_enc  = [enc_r[i] for i in fit_r] + ([enc_s[i] for i in fit_s] if n_s else [])
        all_lens = np.concatenate([lens_r[fit_r], lens_s[fit_s]]) if n_s else lens_r[fit_r]
        all_y    = np.concatenate([y_r[fit_r],   y_s[fit_s]])    if n_s else y_r[fit_r]
        w = np.ones(n_r + n_s, np.float32)
        if n_s and a.synth_weight != 1.0:
            w[n_r:] = a.synth_weight

        model = train_weighted(a.model, all_enc, all_lens, all_y, pad, w)

        own = np.flatnonzero(train_rows & (grp == g))
        logit[own] = ce.predict(model, [enc_r[i] for i in own], lens_r[own], pad)
        hold_sum  += ce.predict(model, [enc_r[i] for i in hold], lens_r[hold], pad)
        test_sum  += ce.predict(model, enc_t, lens_t, pad)
        del model; torch.cuda.empty_cache()
        done.append(g)
        np.savez(ck, logit=logit, hold_sum=hold_sum, test_sum=test_sum, done=np.array(done))
        log.info("group %d done (%.0fs)", g, time.perf_counter() - t0)

    logit[hold] = hold_sum / 3
    auc = {"oof":     float(roc_auc_score(y_r[train_rows], logit[train_rows])),
           "holdout": float(roc_auc_score(y_r[hold], logit[hold]))}
    if "p1" in tr.columns:
        auc["holdout_p1"] = float(roc_auc_score(y_r[hold], tr["p1"].to_numpy()[hold]))
    gate_pass = auc["holdout"] >= GATE_AUC
    if gate_pass:
        log.info("GATE PASS: holdout AUC %.4f >= %.4f -- safe to import", auc["holdout"], GATE_AUC)
    else:
        log.error("GATE FAIL: holdout AUC %.4f < %.4f -- do NOT import", auc["holdout"], GATE_AUC)
    log.info("AUC: %s", auc)
    pd.DataFrame({"row": tr["row"].to_numpy(), "ce__logit": logit}).to_parquet(
        f"{out}/ce_train.parquet", index=False)
    pd.DataFrame({"row": te["row"].to_numpy(), "ce__logit": test_sum/3}).to_parquet(
        f"{out}/ce_test.parquet", index=False)
    json.dump({"model": a.model, "synth": have_synth, "synth_weight": a.synth_weight,
               "auc": auc, "gate_pass": gate_pass, "seconds": time.perf_counter() - t0},
              open(f"{out}/config.json", "w"), indent=1)
    log.info("done in %.0fs", time.perf_counter() - t0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
