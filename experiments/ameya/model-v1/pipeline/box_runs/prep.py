"""Out-of-band detector inputs: the CE band + the US/India holdout predicted pairs (Bakshi's 631k-pair sample, as holdout
rows: scored, never trained on), and the French final pairs as the test band (target-only). A synth3 CE trained on these
scores the confident pairs (p1 > 0.99) that no cross-encoder ever looked at."""
import numpy as np, pandas as pd
from ber.eval.splits import fold_of
SP = "$SCRATCH"
R = "$REPO/work/bakshi_pull/train/box/rescore"
K = 4_000_000_000
tr = pd.read_parquet(f"{SP}/box/band_train.parquet")
h = pd.read_parquet(f"{R}/hold_pred_pairs.parquet")
new = h[~np.isin(h.s1.to_numpy() * K + h.r.to_numpy(), tr.s1.to_numpy() * K + tr.r.to_numpy())].reset_index(drop=True)
fo = fold_of(new.s1.to_numpy())
print("holdout predicted pairs", len(h), "not in the band", len(new), "folds", np.unique(fo))
assert (fo < 5).all()
add = pd.DataFrame({"s1": new.s1.astype("int64"), "r": new.r.astype("int64"), "row": np.arange(len(new), dtype="int64") + int(tr.row.max()) + 1,
                    "p1": new.p1.astype("float32"), "fold": fo.astype("int8"), "y": new.y.astype("int8")})
out = pd.concat([tr, add], ignore_index=True)
out.to_parquet(f"{SP}/oob/band_train.parquet", index=False)
f = pd.read_parquet(f"{R}/fr_final_pairs.parquet")
te = pd.DataFrame({"s1": f.s1.astype("int64"), "r": f.r.astype("int64"), "row": np.arange(len(f), dtype="int64"), "p1": f.p1.astype("float32")})
te.to_parquet(f"{SP}/oob/band_test.parquet", index=False)
print("band_train", len(out), "(+", len(add), "holdout rows); band_test (French final pairs)", len(te))
