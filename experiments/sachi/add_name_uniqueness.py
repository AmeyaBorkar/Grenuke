"""Add name-uniqueness features to dev kit v2 features -> work/features/sachi-fx2-name-dev (C8).

Idea (error analysis on v2): empty-address records are rejected even with an exact name, because names collide.
Tell the model how many S1 of the same country share each name, so exact + unique names can be trusted.
Counts use all S1 of the split (no labels), so the same features can be built on test.
    python experiments/sachi/add_name_uniqueness.py
"""
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from ber.artifacts import read_table, write_table
from ber.paths import records_path

IN, OUT = "ameya-fx2-dev", "sachi-fx2-name-dev"
HON = r"\b(?:mr|mrs|ms|dr|shri|sri|smt|m s|messrs)\b"
LEGAL = r"\b(?:inc|llc|ltd|limited|pvt|private|corp|corporation|co|company|lp|llp|pllc|pc|plc|the|sarl|sas|sasu|eurl|sa|sci|snc)\b"


def core(s: pd.Series) -> pd.Series:
    s = s.fillna("").str.normalize("NFKD").str.encode("ascii", "ignore").str.decode("ascii").str.lower()
    s = s.str.replace(r"[^a-z0-9]+", " ", regex=True).str.replace(LEGAL, " ", regex=True).str.replace(HON, " ", regex=True)
    return s.str.split().str.join(" ")


f = read_table("features", IN, "train")
print("features", f.shape)
tbl = pq.read_table(records_path("train"), columns=["eid", "source", "country", "name", "address"])
keep = pc.or_(pc.equal(tbl["source"], 1), pc.is_in(tbl["eid"], value_set=pa.array(np.unique(f["r"].to_numpy()))))
rec = tbl.filter(keep).to_pandas()
del tbl
rec["core"] = core(rec["name"])
rec.loc[rec["core"] == "", "core"] = np.nan
a = rec["address"].fillna("").str.strip().str.upper()
rec["addr_empty"] = a.isin(["", "NULL", "<NULL>"]).astype(np.float32)

s1 = rec[rec["source"] == 1]
n_s1 = s1.groupby(["country", "core"]).size()                    # how many S1 share (country, core name)
rec["s1_core_n"] = n_s1.reindex(pd.MultiIndex.from_arrays([rec["country"], rec["core"]])).to_numpy()
rec = rec.set_index("eid")

A, B = rec.reindex(f["s1"].to_numpy()), rec.reindex(f["r"].to_numpy())
eq = (A["core"].to_numpy() == B["core"].to_numpy()) & pd.notna(A["core"]).to_numpy()
r_n = np.nan_to_num(B["s1_core_n"].to_numpy(dtype=np.float64), nan=0.0)
f["ctx__s1_core_n"] = A["s1_core_n"].to_numpy(np.float32)       # S1 sharing this S1's name
f["ctx__r_core_n"] = r_n.astype(np.float32)                        # S1 sharing the record's name
f["name__core_eq"] = eq.astype(np.float32)
f["name__core_eq_unique"] = (eq & (r_n == 1)).astype(np.float32)  # exact name, and no other S1 has it
f["addr__r_empty"] = B["addr_empty"].to_numpy(np.float32)
write_table(f, "features", OUT, "train", inputs={"features": IN}, subset="dev kit v2 + name uniqueness")
e = f["addr__r_empty"] == 1
print(f"wrote {OUT}: {f.shape}; empty-address pairs {e.mean():.2%}; "
      f"of those, exact name {f.loc[e, 'name__core_eq'].mean():.1%}, exact+unique {f.loc[e, 'name__core_eq_unique'].mean():.1%}")
