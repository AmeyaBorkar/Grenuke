#!/usr/bin/env python3
"""Score arbitrary (s1, r) pairs with a saved q7st LoRA adapter (llm_group.py's adapter_<g>), same text encoding as
ce_llm_st.py (name ; address, " || " separator, max 96 tokens). Adds column q7__logit.

    CUDA_VISIBLE_DEVICES=2 python score_pairs.py --pairs P.parquet --split test --adapter box/out_q7st/adapter_0 \
        --out P_scored.parquet [--part 0/2]
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ameya", "model-v1"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", required=True)
    ap.add_argument("--split", required=True, choices=["train", "test"])
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="Qwen/Qwen2.5-7B")
    ap.add_argument("--sep", default=" || ")
    ap.add_argument("--max-len", type=int, default=96)
    ap.add_argument("--batch", type=int, default=512)
    ap.add_argument("--part", default="0/1", help="i/n: score only the i-th of n row slices")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    log = logging.getLogger("score_pairs")

    import torch
    from peft import PeftModel
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    import ce
    import ce_llm_st
    ce_llm = ce_llm_st.ce_llm

    t0 = time.perf_counter()
    ce.MAX_LEN = a.max_len
    i, n = (int(x) for x in a.part.split("/"))
    pairs = pd.read_parquet(a.pairs)
    pairs = pairs.iloc[np.array_split(np.arange(len(pairs)), n)[i]].reset_index(drop=True)
    tok = AutoTokenizer.from_pretrained(a.model)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    pad = tok.pad_token_id
    enc, lens = ce_llm_st.encode(tok, a.split, pairs, a.sep)
    log.info("encoded %d pairs (%.0fs)", len(pairs), time.perf_counter() - t0)
    base = AutoModelForSequenceClassification.from_pretrained(a.model, num_labels=1, torch_dtype=torch.bfloat16)
    base.config.pad_token_id = pad
    m = PeftModel.from_pretrained(base, a.adapter).to(ce_llm.DEV)
    logit = ce_llm.predict(m, enc, lens, np.arange(len(pairs)), pad, a.batch)
    pairs["q7__logit"] = logit.astype(np.float32)
    pairs.to_parquet(a.out, index=False)
    log.info("scored %d pairs in %.0fs -> %s", len(pairs), time.perf_counter() - t0, a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
