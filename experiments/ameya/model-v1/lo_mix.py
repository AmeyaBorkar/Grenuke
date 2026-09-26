"""Feature group ``lo0``: label-based look-alike odds where the country has training labels, the label-free proxy
(feats_lo_proxy.py, group ``lop``) where it does not (France).

    python experiments/ameya/model-v1/lo_mix.py --feats ameya-fx3

- train: ``lo`` with the "no statistics" value written as exactly 0 (feats_lo.py computes -1.94e-16 there on train
  and the holdout but 0.0 on test; the trees split between the two).
- test: pairs whose S1 country appears in the training records keep ``lo`` (exact zeros already); the others get
  ``lop``. Leave one country out on the dev kit (US -> India, stage-1 model trained on label odds): India's words
  unseen 0.8824, filled with the proxy 0.9598, known 0.9611.
Writes work/features/<feats>-lo0/{train,test}.parquet, row-aligned with <feats>-str (same row groups).
"""
from __future__ import annotations

import argparse
import json
import logging
import os

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from ber.artifacts import provenance
from ber.paths import artifact_path, records_path

log = logging.getLogger("lo_mix")
EPS = 1e-9


def s1_countries(split: str) -> pd.Series:
    t = pq.read_table(records_path(split), columns=["eid", "source", "country"])
    t = t.filter(pc.equal(t["source"], 1))
    return pd.Series(np.asarray(t["country"].to_numpy(zero_copy_only=False), dtype=object), index=t["eid"].to_numpy())


def write_like(df: pd.DataFrame, like: pq.ParquetFile, path, meta: dict) -> None:
    schema = pa.Schema.from_pandas(df, preserve_index=False).with_metadata({b"ber": json.dumps(meta).encode()})
    path.parent.mkdir(parents=True, exist_ok=True)
    w = pq.ParquetWriter(str(path) + ".tmp", schema, compression="zstd")
    start = 0
    for g in range(like.num_row_groups):
        n = like.metadata.row_group(g).num_rows
        w.write_table(pa.Table.from_pandas(df.iloc[start:start + n], preserve_index=False), row_group_size=n)
        start += n
    w.close()
    os.replace(str(path) + ".tmp", path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--feats", default="ameya-fx3")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    command = f"python experiments/ameya/model-v1/lo_mix.py --feats {args.feats}"
    trained = set(s1_countries("train").unique())
    for split in ("train", "test"):
        fl = pq.ParquetFile(artifact_path("features", f"{args.feats}-lo", split))
        df = fl.read().to_pandas()
        for c in df.columns:
            if not c.endswith("_nlow"):
                v = df[c].to_numpy()
                df[c] = np.where(np.abs(v) < EPS, np.float32(0), v).astype(np.float32)
        n_proxy = 0
        if split == "test":
            keys = pq.read_table(artifact_path("features", f"{args.feats}-str", split), columns=["s1"]).to_pandas()
            cty = s1_countries(split).reindex(keys["s1"].to_numpy()).to_numpy()
            new = ~pd.Series(cty).isin(trained).to_numpy()
            lop = pq.read_table(artifact_path("features", f"{args.feats}-lop", split)).to_pandas()
            for c in df.columns:
                df.loc[new, c] = lop.loc[new, c].to_numpy()
            n_proxy = int(new.sum())
        meta = provenance(command, {"features": f"{args.feats}-lo", "proxy": f"{args.feats}-lop"}, split=split,
                          rows=len(df), kind="features", tag=f"{args.feats}-lo0", trained_countries=sorted(trained),
                          proxy_rows=n_proxy)
        write_like(df, fl, artifact_path("features", f"{args.feats}-lo0", split), meta)
        log.info("%s: %d rows, %d from the proxy (countries without training labels)", split, len(df), n_proxy)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
