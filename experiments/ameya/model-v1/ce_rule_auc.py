"""Cross-encoder-level French check: the AUC of raw cross-encoder logits on France's rule populations inside the
band (rule_pop.py: A/APP/ACR = 1, op-B = 0), to rank cross-encoders without a stage-2 run.

    python experiments/ameya/model-v1/ce_rule_auc.py <band_test.parquet> <rule_pop.parquet> <out dir> [<out dir> ...]

Each out dir holds ce_test.parquet (row, ce__logit) from ce_box.py, ce_llm.py or zmean_ce.py; band_test.parquet
(s1, r, row) maps its rows to pairs.
"""
import sys

import numpy as np
import pandas as pd

K = 4_000_000_000


def auc(y, s):
    o = np.argsort(s, kind="stable")
    r = np.empty(len(s))
    r[o] = np.arange(1, len(s) + 1)
    n1 = y.sum()
    n0 = len(y) - n1
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


if __name__ == "__main__":
    band = pd.read_parquet(sys.argv[1], columns=["s1", "r", "row"])
    pop = pd.read_parquet(sys.argv[2])
    lab = pd.Series(pop.y.to_numpy(), index=pop.s1.to_numpy() * K + pop.r.to_numpy())
    lab = lab[~lab.index.duplicated()]
    band["y"] = lab.reindex(band.s1.to_numpy() * K + band.r.to_numpy()).to_numpy()
    band = band.dropna(subset=["y"])
    print(f"rule-population pairs in the band: {len(band)} (true-copy share {band.y.mean():.3f})")
    for d in sys.argv[3:]:
        ce = pd.read_parquet(f"{d}/ce_test.parquet").set_index("row").ce__logit
        s = ce.reindex(band.row.to_numpy()).to_numpy()
        ok = ~np.isnan(s)
        print(f"{d.rstrip('/').split('/')[-1]}: AUC {auc(band.y.to_numpy()[ok].astype(int), s[ok]):.4f} ({ok.sum()} pairs)")
