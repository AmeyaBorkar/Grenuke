"""Repo port vs scratchpad originals: every (s1, r) set must be identical."""
import sys
import numpy as np, pandas as pd
from ber.artifacts import read_table
K = 4_000_000_000
SP = "$SCRATCH"
RT, M, TS = sys.argv[1], sys.argv[2], sys.argv[3]  # repo STACK_OUT, model, tag suffix
def ks(d): return set((d.s1.to_numpy().astype(np.int64) * K + d.r.to_numpy().astype(np.int64)).tolist())
def pqf(p): return pd.read_parquet(p, columns=["s1", "r"])
def tag(t): return read_table("matches", t, "test", ["s1", "r"])
F = f"ameya-model-{M}-s3-ops3a"
pairs = [("hunted", pqf(f"{RT}/hunted_{M}.parquet"), pqf(f"{SP}/agents/hunt/hunted_{F}.parquet") if M == "v7s" else pqf(f"{SP}/agents/hunt/hunted_{M}.parquet")),
         ("h2", pqf(f"{RT}/{M}_h2.parquet"), pqf(f"{SP}/stack/{M}_h2.parquet")),
         ("h2pc", tag(f"{F}-h2pc{TS}"), tag(f"{F}-h2pc")),
         ("combo", pqf(f"{RT}/decided_combo_{M}.parquet"), pqf(f"{SP}/agents/decide/decided_combo_ameya-s3-{M}.parquet")),
         ("dpc", tag(f"{F}-dpc{TS}"), tag(f"{F}-dpc"))]
ok = True
for name, a, b in pairs:
    ka, kb = ks(a), ks(b); same = ka == kb; ok &= same
    print(f"{name:7s} repo {len(ka):>9,} scratch {len(kb):>9,} {'IDENTICAL' if same else f'DIFFER: only repo {len(ka - kb)}, only scratch {len(kb - ka)}'}")
print("PORT OK" if ok else "PORT DIFFERS")
