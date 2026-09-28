"""Compose a package per S1 country: each country's matches from its own source, candidates the union of the sources'
candidates for that country's S1 (or one shared candidates tag), then drops (France 7B / detector, US/India 7B) from
change lists. Checks one owner per record and matches inside the candidates; imports matches/candidates as new tags.
usage: compose3.py <name> <cands tag> COUNTRY=<matches tag or .parquet with s1,r> ... [--drop <parquet s1,r> ...] [--add <parquet s1,r> ...]
  e.g. compose3.py mixf1 ameya-cands-mixqc US=ameya-model-v7sq3-s3-ops3a-dpc India=g1w_india_test.parquet \
       France=ameya-model-v7sq6r3-s3-ops3a-dpc --drop drop_q7_fr.parquet --drop drop_q7_usin.parquet
-> matches tag ameya-model-<name>, candidates tag ameya-cands-<name> (a copy of <cands tag>)"""
import sys
import numpy as np, pandas as pd, pyarrow.parquet as pq
from ber.artifacts import read_table, write_table
from ber.paths import records_path
K = 4_000_000_000
args = sys.argv[1:]
name, ctag = args[0], args[1]
srcs, drops, adds, i = {}, [], [], 2
while i < len(args):
    if args[i] == "--drop":
        drops.append(args[i + 1]); i += 2
    elif args[i] == "--add":
        adds.append(args[i + 1]); i += 2
    else:
        c, s = args[i].split("=", 1); srcs[c] = s; i += 1
r = pq.read_table(records_path("test"), columns=["eid", "source", "country"], filters=[("source", "==", 1)]).to_pandas()
s1c = r.set_index("eid").country
missing = set(s1c.unique()) - set(srcs)
if missing:
    raise SystemExit(f"no source for countries {missing}")
parts = []
for c, s in srcs.items():
    m = pd.read_parquet(s, columns=["s1", "r"]) if s.endswith(".parquet") else read_table("matches", s, "test", ["s1", "r"])
    m = m[(s1c.reindex(m.s1) == c).to_numpy()].astype("int64")
    parts.append(m); print(f"  {c}: {len(m):,} pairs on {m.s1.nunique():,} S1 from {s}")
m = pd.concat(parts, ignore_index=True)
key = lambda d: d.s1.to_numpy(np.int64) * K + d.r.to_numpy(np.int64)
for d in drops:
    x = pd.read_parquet(d, columns=["s1", "r"])
    keep = ~np.isin(key(m), key(x))
    print(f"  drop list {d.split('/')[-1]}: {len(x):,} listed, {int((~keep).sum()):,} present -> dropped")
    m = m[keep]
c = read_table("candidates", ctag, "test", ["s1", "r"]).astype("int64")
for d in adds:  # additions: inside the candidates, record not owned after the drops, one S1 per record (list order = priority)
    x = pd.read_parquet(d, columns=["s1", "r"]).astype("int64").drop_duplicates("r")
    ok = np.isin(key(x), key(c)) & ~x.r.isin(m.r).to_numpy()
    print(f"  add list {d.split('/')[-1]}: {len(x):,} listed, {int(ok.sum()):,} added")
    m = pd.concat([m, x[ok]], ignore_index=True)
if m.r.duplicated().any():
    raise SystemExit(f"a record has two owners ({int(m.r.duplicated().sum())})")
out = ~np.isin(key(m), key(c))
if out.any():
    raise SystemExit(f"{int(out.sum())} matches outside the candidates {ctag}")
write_table(c, "candidates", f"ameya-cands-{name}", "test", command=f"compose3.py {' '.join(args)}")
write_table(m.reset_index(drop=True), "matches", f"ameya-model-{name}", "test", command=f"compose3.py {' '.join(args)}")
print(f"composed {name}: {len(m):,} pairs; candidates {len(c):,}")
