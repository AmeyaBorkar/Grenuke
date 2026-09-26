"""The countries with training labels (the train records' countries) from apply_combo.py's parquet, every other
country from a matches tag (the France stack: make_h2.py + apply_polish.py).
usage: merge_dpc.py <combo parquet> <other-countries matches tag> <out parquet>"""
import sys

import pandas as pd
import pyarrow.compute as pc
import pyarrow.parquet as pq

from ber.artifacts import read_table
from ber.paths import records_path


def main() -> int:
    dec, ftag, out = sys.argv[1:4]
    labelled = sorted(pc.unique(pq.read_table(records_path("train"), columns=["country"])["country"]).to_pylist())
    r = pq.read_table(records_path("test"), columns=["eid", "source", "country"]).to_pandas()
    s1c = r[r.source == 1].set_index("eid").country
    d = pd.read_parquet(dec)[["s1", "r"]].astype("int64")
    f = read_table("matches", ftag, "test", ["s1", "r"]).astype("int64")
    dl = d[s1c.reindex(d.s1).isin(labelled).to_numpy()]
    fo = f[~s1c.reindex(f.s1).isin(labelled).to_numpy()]
    m = pd.concat([dl, fo], ignore_index=True)
    assert not m.r.duplicated().any(), "a record has two owners"
    m.to_parquet(out, index=False)
    print(f"{'/'.join(labelled)} {len(dl)} from {dec.replace(chr(92), '/').split('/')[-1]}; other countries {len(fo)} "
          f"from {ftag}; total {len(m)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
