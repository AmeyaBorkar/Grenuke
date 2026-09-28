"""7B-assisted recall: candidate pairs we did NOT predict, whose record no S1 owns, for (a) Bakshi's US/India holdout sample
(with truth y, base = our v7sq3 stage-3 holdout predictions) and (b) test (base = mixf1). Scored later by the q7st 7B."""
import numpy as np, pandas as pd, pyarrow.parquet as pq
from ber.artifacts import read_table
from ber.paths import artifact_path
K = 4_000_000_000
SP = "C:/Users/ameya/AppData/Local/Temp/claude/C--Users-ameya-Documents-GrenukeAmazon/19e315ba-0725-4d6f-ae6a-972e1c1f0aa9/scratchpad"
R = "C:/Users/ameya/Documents/GrenukeAmazon/work/bakshi_pull/train/box/rescore"
def cut(df):  # p1 >= 0.02 rows already; keep each record's top-2 S1 by p1
    df = df.sort_values(["r", "p1"], ascending=[True, False], kind="mergesort")
    return df[df.groupby("r").cumcount() < 2]
# (a) holdout sample
samp = pd.read_parquet(f"{R}/hold_truth.parquet").s1.to_numpy()
samp.sort()
f = pq.ParquetFile(artifact_path("scores", "ameya-s3-v7sq3", "train"))
parts = []
for i in range(f.num_row_groups):
    t = f.read_row_group(i, columns=["s1", "r", "y", "p1", "pc", "fold"]).to_pandas()
    parts.append(t[(t.p1 >= 0.02) & (t.fold < 5)])
h = cut(pd.concat(parts, ignore_index=True)); del parts
h = h[np.isin(h.s1.to_numpy(), samp)]
mt = read_table("matches", "ameya-model-v7sq3-s3", "train", ["s1", "r"])
pk = mt.s1.to_numpy(np.int64) * K + mt.r.to_numpy(np.int64)
hk = h.s1.to_numpy(np.int64) * K + h.r.to_numpy(np.int64)
base = h[np.isin(hk, pk)]
add = h[~np.isin(hk, pk) & ~h.r.isin(mt.r).to_numpy()]
print(f"holdout sample S1 {len(samp):,}: cut rows {len(h):,}; base predictions {len(base):,} (precision {base.y.mean():.5f}); "
      f"addable (unpredicted, record unowned) {len(add):,}, true {int(add.y.sum()):,} ({add.y.mean():.3f})")
base[["s1", "r", "y"]].to_parquet(f"{SP}/q7add/hold_base.parquet", index=False)
add[["s1", "r", "p1", "pc", "y"]].to_parquet(f"{SP}/q7add/hold_add_pairs.parquet", index=False)
# (b) test
m = read_table("matches", "ameya-model-mixf1", "test", ["s1", "r"])
c = read_table("candidates", "ameya-cands-mixqc", "test", ["s1", "r"])
ck = c.s1.to_numpy(np.int64) * K + c.r.to_numpy(np.int64)
mk = m.s1.to_numpy(np.int64) * K + m.r.to_numpy(np.int64)
ta = c[~np.isin(ck, mk) & ~c.r.isin(m.r).to_numpy()].reset_index(drop=True)
print(f"test: candidates {len(c):,}, final {len(m):,}, addable (unpredicted, record unowned) {len(ta):,}")
ta.astype("int64").to_parquet(f"{SP}/q7add/test_add_pairs.parquet", index=False)
