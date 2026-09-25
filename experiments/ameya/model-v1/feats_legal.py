"""Legal-form features (features v3, group ``lg``), row-aligned with an existing feature set.

    python experiments/ameya/model-v1/feats_legal.py --feats ameya-fx2 --split train

Writes work/features/<feats>-lg/<split>.parquet in the row groups of <feats>-str: the leg__* features of ``legal.py``
(relation code, counts of legal forms per side, shared, only in the S1, only in the record) and the bitmasks of the
forms only in the record / only in the S1 (``leg__r_only_bits``, ``leg__s1_only_bits``: which form was added or
dropped; bits in ``legal.FORMS``).
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

from ber.artifacts import provenance
from ber.paths import artifact_path, records_path
from legal import legal_bits, pair_features

log = logging.getLogger("feats_legal")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--feats", default="ameya-fx2")
    ap.add_argument("--split", required=True, choices=["train", "test"])
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    t0 = time.perf_counter()
    t = pq.read_table(records_path(args.split), columns=["eid", "name"])
    eid = t["eid"].to_numpy()
    bits = legal_bits(t["name"].combine_chunks())
    order = np.argsort(eid)
    eid, bits = eid[order], bits[order]
    log.info("legal forms of %d records (%.0fs)", eid.size, time.perf_counter() - t0)

    src = pq.ParquetFile(artifact_path("features", f"{args.feats}-str", args.split))
    out = artifact_path("features", f"{args.feats}-lg", args.split)
    out.parent.mkdir(parents=True, exist_ok=True)
    command = f"python experiments/ameya/model-v1/feats_legal.py --feats {args.feats} --split {args.split}"
    meta = provenance(command, {"features": f"{args.feats}-str"}, split=args.split, rows=src.metadata.num_rows,
                      kind="features", tag=f"{args.feats}-lg")
    writer = None
    for g in range(src.num_row_groups):
        k = src.read_row_group(g, columns=["s1", "r"])
        b1 = bits[np.searchsorted(eid, k["s1"].to_numpy())]
        br = bits[np.searchsorted(eid, k["r"].to_numpy())]
        cols = pair_features(b1, br)
        cols["leg__r_only_bits"] = (br & ~b1).astype(np.float32)
        cols["leg__s1_only_bits"] = (b1 & ~br).astype(np.float32)
        table = pa.Table.from_pandas(pd.DataFrame(cols), preserve_index=False)
        if writer is None:
            schema = table.schema.with_metadata({b"ber": json.dumps(meta).encode()})
            writer = pq.ParquetWriter(str(out) + ".tmp", schema, compression="zstd")
        writer.write_table(table.replace_schema_metadata(writer.schema.metadata), row_group_size=len(table))
    writer.close()
    os.replace(str(out) + ".tmp", out)
    log.info("wrote %s: %d rows (%.0fs)", out, src.metadata.num_rows, time.perf_counter() - t0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
