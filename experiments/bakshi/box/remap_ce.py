#!/usr/bin/env python3
"""Re-key cross-encoder logits trained against ANOTHER machine's band onto THIS machine's band, by (s1, r).

Why this exists. `ce_import.py` places logits by positional `row` -- an index into `<feats>-str`:

    full[d["row"].to_numpy()] = d["ce__logit"].to_numpy()

A `row` from ameya's band indexes HIS `ameya-fx5-str`. Ours is rebuilt on a different machine, and nothing
guarantees the same row order there (parallel numba top-K selection with ties, thread counts, float drift in
stage 1 moving pairs across the band edge). Importing his `row` values against our features would put every
logit on the wrong pair -- silently, with no error, and stage 2 would train on noise.

So `row` never crosses machines. His band gives (s1, r, row); his logits give (row, logit); joining those gives
(s1, r, logit), which is machine-independent. Joining THAT to our band on (s1, r) recovers OUR row.

Coverage gate. The share of our band rows that receive a logit is the direct measurement of whether blocking and
stage 1 reproduced. Near 100% means they did. Below `--min-coverage` the run aborts: a feature that covers 90% of
the rows it was designed for is a different feature, and a stage 2 trained on it is a different model.

The output keeps EVERY row of our band (NaN where no logit was found), so every remapped source shares one row
array -- which `zmean_ce.py` asserts before it will average anything.

    python remap_ce.py --src-band DIR --src-out DIR/out_e5l --dst-band DIR --out DIR/out_e5l_mine \
        [--min-coverage 0.995]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

K = 4_000_000_000
COL = "ce__logit"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src-band", required=True, type=Path, help="dir with the band_{train,test}.parquet the logits were trained on")
    ap.add_argument("--src-out", required=True, type=Path, help="dir with ce_{train,test}.parquet and config.json")
    ap.add_argument("--dst-band", required=True, type=Path, help="dir with THIS machine's band_{train,test}.parquet")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--min-coverage", type=float, default=0.995)
    a = ap.parse_args()
    if a.out.resolve() == a.src_out.resolve():
        raise SystemExit("FAIL: --out is the source directory")
    a.out.mkdir(parents=True, exist_ok=True)

    report = {}
    for split in ("train", "test"):
        sb = pd.read_parquet(a.src_band / f"band_{split}.parquet", columns=["s1", "r", "row"])
        so = pd.read_parquet(a.src_out / f"ce_{split}.parquet", columns=["row", COL])
        db = pd.read_parquet(a.dst_band / f"band_{split}.parquet", columns=["s1", "r", "row"])
        for name, d in (("source band", sb), ("destination band", db)):
            if (d.s1.to_numpy() * K + d.r.to_numpy()).size != pd.Index(d.s1.to_numpy() * K + d.r.to_numpy()).unique().size:
                raise SystemExit(f"FAIL {split}: (s1, r) is not unique in the {name}")
        if so.row.duplicated().any():
            raise SystemExit(f"FAIL {split}: duplicate rows in {a.src_out}/ce_{split}.parquet")

        # (1) his rows -> pairs. Every logit must belong to his band, or these logits were not trained on it.
        m = so.merge(sb, on="row", how="left")
        orphan = int(m.s1.isna().sum())
        if orphan:
            raise SystemExit(f"FAIL {split}: {orphan:,} logits have a row absent from the source band -- "
                             f"{a.src_out} was not trained on {a.src_band}")
        key = pd.Series(m[COL].to_numpy(np.float32), index=m.s1.to_numpy(np.int64) * K + m.r.to_numpy(np.int64))

        # (2) pairs -> our rows
        dk = db.s1.to_numpy(np.int64) * K + db.r.to_numpy(np.int64)
        v = key.reindex(dk).to_numpy(np.float32)
        cov = float(np.isfinite(v).mean())
        extra = int(pd.Index(key.index).difference(pd.Index(dk)).size)
        report[split] = {"dst_rows": int(dk.size), "covered": int(np.isfinite(v).sum()), "coverage": cov,
                         "src_pairs_not_in_dst_band": extra}
        print(f"{split}: our band {dk.size:,} rows, {np.isfinite(v).sum():,} received a logit "
              f"(coverage {cov:.4%}); {extra:,} of the source's pairs are not in our band")
        if cov < a.min_coverage:
            raise SystemExit(f"FAIL {split}: coverage {cov:.4%} < {a.min_coverage:.2%}. Blocking or stage 1 did not "
                             f"reproduce closely enough to reuse these logits; retrain this cross-encoder on our band.")
        pd.DataFrame({"row": db.row.to_numpy(), COL: v}).to_parquet(a.out / f"ce_{split}.parquet", index=False)

    cfg = json.loads((a.src_out / "config.json").read_text()) if (a.src_out / "config.json").exists() else {}
    cfg["remap"] = {"from_band": str(a.src_band), "from_out": str(a.src_out), "to_band": str(a.dst_band),
                    "key": "(s1, r)", **report}
    (a.out / "config.json").write_text(json.dumps(cfg, indent=1))
    print(f"written {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
