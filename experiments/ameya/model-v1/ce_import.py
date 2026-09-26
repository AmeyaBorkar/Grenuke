"""Import cross-encoder logits trained elsewhere (e.g. a larger model on a rented GPU) as a feature group.

    python experiments/ameya/model-v1/ce_import.py --feats ameya-fx5 --src <dir with ce_{train,test}.parquet> \
        --group cel --column cel__logit

The source files hold (row, ce__logit) for the band rows of <feats>-str (ce.py's band on the same stage-1 scores);
the other rows get NaN, as in ce.py. Writes work/features/<feats>-<group>/{train,test}.parquet, row-aligned with
<feats>-str, so stage 2 takes it with ``--groups ...,<group> --extra <column>``.
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from ber.artifacts import provenance
from ber.paths import artifact_path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--feats", required=True)
    ap.add_argument("--src", required=True)
    ap.add_argument("--group", default="cel")
    ap.add_argument("--column", default="cel__logit")
    args = ap.parse_args()
    cfg = json.load(open(os.path.join(args.src, "config.json")))
    command = (f"python experiments/ameya/model-v1/ce_import.py --feats {args.feats} --src {args.src} "
               f"--group {args.group} --column {args.column}")
    for split in ("train", "test"):
        d = pd.read_parquet(os.path.join(args.src, f"ce_{split}.parquet"))
        src = pq.ParquetFile(artifact_path("features", f"{args.feats}-str", split))
        full = np.full(src.metadata.num_rows, np.nan, np.float32)
        full[d["row"].to_numpy()] = d["ce__logit"].to_numpy(np.float32)
        path = artifact_path("features", f"{args.feats}-{args.group}", split)
        path.parent.mkdir(parents=True, exist_ok=True)
        meta = provenance(command, {"features": f"{args.feats}-str"}, split=split, rows=int(full.size), kind="features",
                          tag=f"{args.feats}-{args.group}", model=cfg.get("model"), auc=cfg.get("auc"))
        schema = pa.schema([(args.column, pa.float32())]).with_metadata({b"ber": json.dumps(meta).encode()})
        w = pq.ParquetWriter(str(path) + ".tmp", schema, compression="zstd")
        start = 0
        for g in range(src.num_row_groups):
            n = src.metadata.row_group(g).num_rows
            w.write_table(pa.table({args.column: full[start:start + n]}, schema=schema), row_group_size=n)
            start += n
        w.close()
        os.replace(str(path) + ".tmp", path)
        print(split, "rows", full.size, "with a logit", int(np.isfinite(full).sum()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
