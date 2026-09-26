"""Would a bigger multilingual cross-encoder add more than e5-small? (roadmap 3.3, gate G10 follow-up)

    python experiments/sachi/ce_compare.py --models intfloat/multilingual-e5-small,intfloat/multilingual-e5-base

On the dev kit v2 (Mac-sized): the cross-encoder's band is the pairs stage 1 is unsure about (0.02 <= p1 <= 0.99).
- Train: a sample of band pairs from the training folds (5/10/15); eval: band pairs of dev fold 0 (the holdout).
- Each model reads "name ; address" of the S1 and of the record as one text pair and is fine-tuned for one epoch
  (binary cross-entropy), on Apple's GPU (mps) when available.
- What matters is what it adds on top of the current model: dev kit v2's pc has no cross-encoder, so we fit a
  logistic regression y ~ logit(pc) [+ ce_logit] with 2-fold cross-fitting over eval S1 and report log-loss and AUC.
  model v4 onwards already has e5-small, so the question is the gain of e5-base OVER e5-small.
Keep e5-base (propose a full run on the CUDA machine) if its log-loss gain over pc is clearly larger than e5-small's
(e.g. >= 5% more log-loss reduction) with a better AUC.
"""
from __future__ import annotations

import argparse
import json
import math
import time

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from ber.paths import artifact_path, records_path


def texts(ids: np.ndarray) -> pd.Series:
    t = pq.read_table(records_path("train"), columns=["eid", "name", "address"])
    t = t.filter(pc.is_in(t["eid"], value_set=pa.array(np.unique(ids))))
    d = t.to_pandas()
    addr = d["address"].fillna("").astype(str)
    addr = addr.where(~addr.str.strip().str.upper().isin(["<NULL>", "NULL", "NONE", "NAN"]), "")
    return pd.Series((d["name"].fillna("").astype(str) + " ; " + addr).to_numpy(), index=d["eid"].to_numpy())


def batches(n: int, bs: int, rng=None):
    idx = rng.permutation(n) if rng is not None else np.arange(n)
    for i in range(0, n, bs):
        yield idx[i:i + bs]


def run_model(name: str, tr: pd.DataFrame, ev: pd.DataFrame, txt: pd.Series, a, dev: torch.device) -> np.ndarray:
    torch.manual_seed(26)
    tok = AutoTokenizer.from_pretrained(name)
    model = AutoModelForSequenceClassification.from_pretrained(name, num_labels=1).to(dev)
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=0.01)
    steps = math.ceil(len(tr) / a.bs)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / (0.06 * steps)) * max(0.0, 1 - s / steps))
    lossf = torch.nn.BCEWithLogitsLoss()
    ta, tb = txt.reindex(tr.s1).tolist(), txt.reindex(tr.r).tolist()
    y = torch.tensor(tr.y.to_numpy(np.float32))
    model.train()
    t0 = time.perf_counter()
    for k, b in enumerate(batches(len(tr), a.bs, np.random.default_rng(26))):
        enc = tok([ta[i] for i in b], [tb[i] for i in b], truncation=True, max_length=a.max_len, padding=True,
                  return_tensors="pt").to(dev)
        loss = lossf(model(**enc).logits.squeeze(-1), y[b].to(dev))
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step(); sched.step(); opt.zero_grad()
        if k % 100 == 0:
            el = time.perf_counter() - t0
            print(f"  {name.split('/')[-1]} step {k}/{steps} loss {loss.item():.4f} "
                  f"({el:.0f}s, eta {el / (k + 1) * (steps - k - 1) / 60:.1f} min)", flush=True)
    model.eval()
    ea, eb = txt.reindex(ev.s1).tolist(), txt.reindex(ev.r).tolist()
    out = np.empty(len(ev), np.float32)
    with torch.no_grad():
        for b in batches(len(ev), a.bs * 2):
            enc = tok([ea[i] for i in b], [eb[i] for i in b], truncation=True, max_length=a.max_len, padding=True,
                      return_tensors="pt").to(dev)
            out[b] = model(**enc).logits.squeeze(-1).float().cpu().numpy()
    del model
    if dev.type == "mps":
        torch.mps.empty_cache()
    return out


def stacked(ev: pd.DataFrame, cols: list[str]) -> tuple[float, float]:
    """2-fold cross-fitted logistic regression of y on the columns; out-of-fold log-loss and AUC."""
    half = (pd.util.hash_array(ev.s1.to_numpy()) % 2).astype(bool)
    X, y = ev[cols].to_numpy(np.float64), ev.y.to_numpy()
    p = np.empty(len(ev))
    for h in (False, True):
        m = LogisticRegression(C=10.0, max_iter=1000).fit(X[half != h], y[half != h])
        p[half == h] = m.predict_proba(X[half == h])[:, 1]
    return log_loss(y, np.clip(p, 1e-6, 1 - 1e-6)), roc_auc_score(y, p)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores", default="ameya-s2-v2-dev")
    ap.add_argument("--models", default="intfloat/multilingual-e5-small,intfloat/multilingual-e5-base")
    ap.add_argument("--n-train", type=int, default=40000)
    ap.add_argument("--n-eval", type=int, default=20000)
    ap.add_argument("--bs", type=int, default=32)
    ap.add_argument("--lr", type=float, default=3e-5)
    ap.add_argument("--max-len", type=int, default=96)
    a = ap.parse_args()
    dev = torch.device("mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu")
    print("device:", dev, flush=True)

    sc = pd.read_parquet(artifact_path("scores", a.scores, "train"), columns=["s1", "r", "fold", "y", "p1", "pc"])
    band = sc[(sc.p1 >= 0.02) & (sc.p1 <= 0.99)]
    rng = np.random.default_rng(26)
    tr_all, ev_all = band[band.fold >= 5], band[band.fold == 0]
    tr = tr_all.iloc[rng.choice(len(tr_all), min(a.n_train, len(tr_all)), replace=False)].reset_index(drop=True)
    s1s = ev_all.s1.unique()
    keep = rng.permutation(s1s)[: max(1, int(len(s1s) * min(1.0, a.n_eval / max(len(ev_all), 1))))]
    ev = ev_all[ev_all.s1.isin(keep)].reset_index(drop=True)
    print(f"band pairs: train {len(tr_all):,} (using {len(tr):,}, {tr.y.mean():.3f} true), "
          f"eval {len(ev):,} ({ev.y.mean():.3f} true, {ev.s1.nunique():,} S1)", flush=True)
    txt = texts(np.r_[tr.s1, tr.r, ev.s1, ev.r])

    eps = 1e-6
    ev["lpc"] = np.log(np.clip(ev.pc, eps, 1 - eps) / (1 - np.clip(ev.pc, eps, 1 - eps)))
    res = {"pc_only": dict(zip(("logloss", "auc"), stacked(ev, ["lpc"])))}
    print("pc only:", res["pc_only"], flush=True)
    for name in a.models.split(","):
        t0 = time.perf_counter()
        col = "ce_" + name.split("/")[-1]
        ev[col] = run_model(name, tr, ev, txt, a, dev)
        ll_ce, auc_ce = log_loss(ev.y, 1 / (1 + np.exp(-ev[col].clip(-30, 30)))), roc_auc_score(ev.y, ev[col])
        ll, auc = stacked(ev, ["lpc", col])
        res[name] = {"ce_alone_logloss": ll_ce, "ce_alone_auc": auc_ce, "pc+ce_logloss": ll, "pc+ce_auc": auc,
                     "logloss_reduction_vs_pc": 1 - ll / res["pc_only"]["logloss"],
                     "minutes": (time.perf_counter() - t0) / 60}
        print(name, {k: round(v, 5) for k, v in res[name].items()}, flush=True)
    names = a.models.split(",")
    if len(names) == 2:
        both = stacked(ev, ["lpc"] + ["ce_" + n.split("/")[-1] for n in names])
        res["pc+both"] = {"logloss": both[0], "auc": both[1]}
        r0, r1 = (res[n]["logloss_reduction_vs_pc"] for n in names)
        print(f"\nlog-loss reduction over pc: {names[0]} {r0:.1%}, {names[1]} {r1:.1%}; both together "
              f"{1 - both[0] / res['pc_only']['logloss']:.1%}")
        print("verdict:", "PROPOSE the bigger model" if r1 - r0 >= 0.05 and res[names[1]]["pc+ce_auc"] >
              res[names[0]]["pc+ce_auc"] else "keep e5-small (no clear gain)")
    with open("ce_compare.json", "w") as fh:
        json.dump(res, fh, indent=1, default=float)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
