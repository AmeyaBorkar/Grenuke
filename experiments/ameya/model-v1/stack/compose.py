"""Compose a final from two stacked models by country: the countries with training labels (read from the train records)
from one matches tag and its candidates, every other country from another (RESEARCH_v6.md 6.17).

    python compose.py <labelled matches tag> <labelled cands tag> <other matches tag> <other cands tag> <name>

Writes matches tag ameya-model-<name> and candidates tag ameya-cands-<name> (the union of both candidate sets, each
restricted to its own countries). Stops if a record would have two owners or a match falls outside the candidates.
Then write the submission as in stack.sh:
    python -m ber.pipeline --stage write --split test --tag <name> --in candidates=ameya-cands-<name> --in matches=ameya-model-<name>
"""
import sys

import numpy as np
import pandas as pd
import pyarrow.compute as pc
import pyarrow.parquet as pq

from ber.artifacts import read_table, write_table
from ber.paths import records_path

K = 4_000_000_000


def main(lm: str, lc: str, om: str, oc: str, name: str) -> None:
    labelled = set(pc.unique(pq.read_table(records_path("train"), columns=["country"])["country"]).to_pylist())
    r = pq.read_table(records_path("test"), columns=["eid", "source", "country"]).to_pandas()
    s1c = r[r.source == 1].set_index("eid").country

    def lab(d: pd.DataFrame) -> np.ndarray:
        return s1c.reindex(d.s1).isin(labelled).to_numpy()

    m1, c1 = read_table("matches", lm, "test", ["s1", "r"]), read_table("candidates", lc, "test", ["s1", "r"])
    m2, c2 = read_table("matches", om, "test", ["s1", "r"]), read_table("candidates", oc, "test", ["s1", "r"])
    m = pd.concat([m1[lab(m1)], m2[~lab(m2)]], ignore_index=True).astype("int64")
    c = pd.concat([c1[lab(c1)], c2[~lab(c2)]], ignore_index=True).astype("int64").drop_duplicates()
    if m.r.duplicated().any():
        raise SystemExit("a record has two owners")
    if not np.isin(m.s1.to_numpy() * K + m.r.to_numpy(), c.s1.to_numpy() * K + c.r.to_numpy()).all():
        raise SystemExit("matches outside the composed candidates")
    cmd = f"compose.py {lm} {lc} {om} {oc} {name}"
    write_table(c, "candidates", f"ameya-cands-{name}", "test", command=cmd)
    write_table(m, "matches", f"ameya-model-{name}", "test", command=cmd)
    print(f"composed {name}: labelled {int(lab(m).sum())} pairs from {lm}, other {int((~lab(m)).sum())} from {om}; "
          f"candidates {len(c)}")


if __name__ == "__main__":
    if len(sys.argv) != 6:
        raise SystemExit(__doc__)
    main(*sys.argv[1:6])
