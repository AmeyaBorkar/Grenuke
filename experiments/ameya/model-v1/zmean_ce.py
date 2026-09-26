"""z-scored mean of several cross-encoder runs (same band rows) into a source dir for ce_import.py.
usage: zmean_ce.py <out dir> <src dir> [<src dir> ...]"""
import json, os, sys
import numpy as np, pandas as pd
out, srcs = sys.argv[1], sys.argv[2:]
os.makedirs(out, exist_ok=True)
tr = {s: pd.read_parquet(f"{s}/ce_train.parquet") for s in srcs}
te = {s: pd.read_parquet(f"{s}/ce_test.parquet") for s in srcs}
for s in srcs[1:]:
    assert (tr[s].row.to_numpy() == tr[srcs[0]].row.to_numpy()).all() and (te[s].row.to_numpy() == te[srcs[0]].row.to_numpy()).all()
st = {s: (float(tr[s].ce__logit.mean()), float(tr[s].ce__logit.std())) for s in srcs}
zm = lambda d: np.mean([(d[s].ce__logit.to_numpy() - st[s][0]) / st[s][1] for s in srcs], axis=0).astype(np.float32)
pd.DataFrame({"row": tr[srcs[0]].row, "ce__logit": zm(tr)}).to_parquet(f"{out}/ce_train.parquet", index=False)
pd.DataFrame({"row": te[srcs[0]].row, "ce__logit": zm(te)}).to_parquet(f"{out}/ce_test.parquet", index=False)
json.dump({"model": "mean of z-scored " + ", ".join(os.path.basename(s) for s in srcs), "z": st}, open(f"{out}/config.json", "w"), indent=1)
print("written", out)
