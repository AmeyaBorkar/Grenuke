"""Apply a list of pair changes to a matches tag: drops first, then adds (only if the pair is in the candidates and the
record is not owned by another S1 after the drops). usage: apply_changes.py <matches tag> <cands tag> <changes.parquet
with s1, r, action in {add, drop}> <new name>  -> matches tag ameya-model-<name> (candidates unchanged: <cands tag>)."""
import sys
import numpy as np, pandas as pd
from ber.artifacts import read_table, write_table
K = 4_000_000_000
mt, ct, chg, name = sys.argv[1:5]
m = read_table("matches", mt, "test", ["s1", "r"]).astype("int64")
c = read_table("candidates", ct, "test", ["s1", "r"]).astype("int64")
x = pd.read_parquet(chg)
dk = x[x.action == "drop"]; ak = x[x.action == "add"]
key = lambda d: d.s1.to_numpy(np.int64) * K + d.r.to_numpy(np.int64)
keep = ~np.isin(key(m), key(dk))
m2 = m[keep]
ak = ak[np.isin(key(ak), key(c)) & ~np.isin(key(ak), key(m2)) & ~ak.r.isin(m2.r).to_numpy()].drop_duplicates("r")
m3 = pd.concat([m2, ak[["s1", "r"]].astype("int64")], ignore_index=True)
if m3.r.duplicated().any():
    raise SystemExit("a record has two owners")
write_table(m3, "matches", f"ameya-model-{name}", "test", command=f"apply_changes.py {' '.join(sys.argv[1:])}")
print(f"{name}: dropped {int((~keep).sum())} of {len(dk)} listed, added {len(ak)} of {int((x.action == 'add').sum())} listed; pairs {len(m)} -> {len(m3)}")
