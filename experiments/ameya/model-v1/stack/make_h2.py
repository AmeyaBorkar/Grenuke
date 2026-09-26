"""The final tag plus the hunt's changes, narrowed for the countries without training labels (France):
- countries with labels (the train records' countries) keep every hunt change (acr adds, cap drops, nsa drops);
- other countries keep only acr adds whose record address has no digit (the number-dropped acronym copies; the others
  carry a nudged house number or another street) and no cap drops (their pc cannot rank near-identical copies).
Checks first that final + all hunt changes reproduces the hunt's own parquet.
usage: make_h2.py <final matches tag> <hunted parquet> <changes csv> <out parquet>"""
import sys

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from ber.artifacts import read_table
from ber.paths import records_path

K = 4_000_000_000


def key(d):
    return d.s1.to_numpy() * K + d.r.to_numpy()


def apply(base, c):
    drop, add = c[c.action == "drop"], c[c.action == "add"]
    b = base[~np.isin(key(base), key(drop))]
    return pd.concat([b, add[["s1", "r"]]], ignore_index=True).astype("int64")


def main() -> int:
    final, hunted, changes, out = sys.argv[1:5]
    f = read_table("matches", final, "test", ["s1", "r"]).astype("int64")
    h = pd.read_parquet(hunted)[["s1", "r"]].astype("int64")
    ch = pd.read_csv(changes)
    assert set(key(apply(f, ch))) == set(key(h)), "the changes csv does not reproduce the hunted parquet"
    labelled = set(pc.unique(pq.read_table(records_path("train"), columns=["country"])["country"]).to_pylist())
    other = ~ch.country.isin(labelled)
    o_acr = ch[other & (ch.rule == "acr")]
    ids = o_acr.r.unique()
    parts = [b.filter(pa.array(np.isin(b.column(0).to_numpy(), ids))).to_pandas()
             for b in pq.ParquetFile(records_path("test")).iter_batches(batch_size=2_000_000, columns=["eid", "address"])]
    addr = pd.concat(parts).set_index("eid").address.fillna("") if parts else pd.Series(dtype=object)
    nodigit = ~addr.reindex(o_acr.r).fillna("0").str.contains(r"\d").to_numpy()
    keep = pd.concat([ch[~other], o_acr[nodigit]], ignore_index=True)
    h2 = apply(f, keep)
    assert not h2.r.duplicated().any()
    h2.to_parquet(out, index=False)
    print(f"final {len(f)}; hunt all {len(h)}; h2 {len(h2)}")
    print(keep.groupby(["rule", "action", "country"]).size().to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
