#!/usr/bin/env bash
# Package a modified test matching: stack_pkg.sh <matches.parquet (s1, r)> <new matches tag> <cands tag> <package name>
# Checks one owner per record and matches inside the candidate set, imports it as work/matches/<tag>/test.parquet,
# then package6.sh (write, validator --check-ids, sha256).
set -euo pipefail
SP=$SCRATCH
source $SP/env6.sh > /dev/null
PQ=$1; TAG=$2; CANDS=$3; NAME=$4
python - "$PQ" "$TAG" "$CANDS" <<'PY'
import sys
import numpy as np, pandas as pd
from ber.artifacts import read_table, write_table
pq, tag, cands = sys.argv[1:4]
m = pd.read_parquet(pq)[["s1", "r"]].astype("int64").drop_duplicates()
assert not m.r.duplicated().any(), "a record is predicted for two S1"
c = read_table("candidates", cands, "test", ["s1", "r"])
K = 4_000_000_000
inside = np.isin(m.s1.to_numpy() * K + m.r.to_numpy(), c.s1.to_numpy() * K + c.r.to_numpy())
assert inside.all(), f"{(~inside).sum()} matches outside the candidate set"
write_table(m, "matches", tag, "test", command=f"stack_pkg.sh {pq}")
print(f"imported {len(m)} pairs as matches/{tag}")
PY
bash $SP/package6.sh "$TAG" "$CANDS" "$NAME"
