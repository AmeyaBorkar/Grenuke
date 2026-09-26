"""Import a matching parquet (s1, r) as a test matches tag after two checks: one S1 per record, and every pair inside the
candidate tag (the submission's matches must be a subset of its candidates).
usage: import_tag.py <parquet> <new matches tag> <candidates tag>"""
import sys

import numpy as np
import pandas as pd

from ber.artifacts import read_table, write_table

K = 4_000_000_000


def main() -> int:
    src, tag, cands = sys.argv[1:4]
    m = pd.read_parquet(src)[["s1", "r"]].astype("int64").drop_duplicates()
    assert not m.r.duplicated().any(), "a record is predicted for two S1"
    c = read_table("candidates", cands, "test", ["s1", "r"])
    inside = np.isin(m.s1.to_numpy() * K + m.r.to_numpy(), c.s1.to_numpy() * K + c.r.to_numpy())
    assert inside.all(), f"{(~inside).sum()} matches outside the candidate set"
    write_table(m, "matches", tag, "test", command=f"import_tag.py {src}")
    print(f"imported {len(m)} pairs as matches/{tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
