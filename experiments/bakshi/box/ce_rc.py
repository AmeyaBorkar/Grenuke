#!/usr/bin/env python3
"""ce_box.py for models whose code lives in their Hugging Face repo (trust_remote_code), e.g.
Alibaba-NLP/gte-multilingual-reranker-base (Apache-2.0, 306M). ce.train_one and ce_box.main load with plain
AutoModelForSequenceClassification / AutoTokenizer, which refuse such models; this wrapper swaps in loaders that
pass trust_remote_code=True and then runs ce_box.main() unchanged, with ce_box.py's own arguments.

    python ce_rc.py --model Alibaba-NLP/gte-multilingual-reranker-base --name gtes --lr 2e-5 --batch 128 \
        --epochs 1 --seed 26 --pseudo $CE_BOX_DIR/pseudo_fr_v7sq.parquet
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ameya", "model-v1"))

import transformers  # noqa: E402

import ce  # noqa: E402
import ce_box  # noqa: E402


class _Remote:
    def __init__(self, cls):
        self.cls = cls

    def from_pretrained(self, *args, **kw):
        kw.setdefault("trust_remote_code", True)
        return self.cls.from_pretrained(*args, **kw)


ce.AutoModelForSequenceClassification = _Remote(transformers.AutoModelForSequenceClassification)
ce_box.AutoTokenizer = _Remote(transformers.AutoTokenizer)

if __name__ == "__main__":
    raise SystemExit(ce_box.main())
