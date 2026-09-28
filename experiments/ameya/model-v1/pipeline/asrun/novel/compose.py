"""Compose a package from two sources by country group: the countries with training labels (read from the train
records) from one final matches tag + its candidates, every other country (France) from another. Checks one owner per
record and matches inside the composed candidates, imports both as new tags, then packages with package6.sh.
usage: compose.py <labelled matches tag> <labelled cands tag> <other matches tag> <other cands tag> <new name>
       -> matches tag ameya-model-<name>, candidates tag ameya-cands-<name>, package 2026-09-27-<name>-c2"""
import subprocess, sys
import numpy as np, pandas as pd, pyarrow.compute as pc, pyarrow.parquet as pq
from ber.artifacts import read_table, write_table
from ber.paths import records_path
K = 4_000_000_000
lm, lc, om, oc, name = sys.argv[1:6]
labelled = set(pc.unique(pq.read_table(records_path("train"), columns=["country"])["country"]).to_pylist())
r = pq.read_table(records_path("test"), columns=["eid", "source", "country"]).to_pandas()
s1c = r[r.source == 1].set_index("eid").country
lab = lambda d: s1c.reindex(d.s1).isin(labelled).to_numpy()
m1, c1 = read_table("matches", lm, "test", ["s1", "r"]), read_table("candidates", lc, "test", ["s1", "r"])
m2, c2 = read_table("matches", om, "test", ["s1", "r"]), read_table("candidates", oc, "test", ["s1", "r"])
m = pd.concat([m1[lab(m1)], m2[~lab(m2)]], ignore_index=True).astype("int64")
c = pd.concat([c1[lab(c1)], c2[~lab(c2)]], ignore_index=True).astype("int64").drop_duplicates()
if m.r.duplicated().any():
    raise SystemExit("a record has two owners")
if not np.isin(m.s1.to_numpy() * K + m.r.to_numpy(), c.s1.to_numpy() * K + c.r.to_numpy()).all():
    raise SystemExit("matches outside the composed candidates")
write_table(c, "candidates", f"ameya-cands-{name}", "test", command=f"compose.py {' '.join(sys.argv[1:])}")
write_table(m, "matches", f"ameya-model-{name}", "test", command=f"compose.py {' '.join(sys.argv[1:])}")
print(f"composed {name}: labelled {int(lab(m).sum())} pairs from {lm}, other {int((~lab(m)).sum())} from {om}; candidates {len(c)}")
sp = "/c/Users/ameya/AppData/Local/Temp/claude/C--Users-ameya-Documents-GrenukeAmazon/19e315ba-0725-4d6f-ae6a-972e1c1f0aa9/scratchpad"
out = subprocess.run(["bash", f"{sp}/package6.sh", f"ameya-model-{name}", f"ameya-cands-{name}", f"2026-09-27-{name}-c2"],
                     capture_output=True, text=True)
print("\n".join(l for l in out.stdout.splitlines() if "PASS" in l or "FAIL" in l or "matching_results.tsv" in l or "rror" in l))
print(out.stderr[-800:] if out.returncode else "", end="")
