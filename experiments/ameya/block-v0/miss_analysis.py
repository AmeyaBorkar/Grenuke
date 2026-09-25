"""Why does blocking miss true pairs? Categorize missed holdout pairs of a candidate tag (fold-restricted run).

python experiments/ameya/block-v0/miss_analysis.py <candidates tag> [fold]
"""
import sys

import numpy as np
import pandas as pd
import pyarrow as pa

from ber.artifacts import read_table
from ber.block import text
from ber.eval.splits import in_folds
from ber.records import load_records, load_truth

tag = sys.argv[1]
fold = int(sys.argv[2]) if len(sys.argv) > 2 else 0
rec = load_records("train")
truth = load_truth()
truth = truth[in_folds(truth["s1"].to_numpy(), (fold,))]
cands = read_table("candidates", tag, "train", ["s1", "r"])
hit = truth.merge(cands, on=["s1", "r"], how="left", indicator=True)
miss = hit[hit["_merge"] == "left_only"][["s1", "r"]]
print(f"true pairs {len(truth):,}, missed {len(miss):,} ({len(miss) / len(truth):.2%})")

r = rec.set_index("eid")
m = miss.assign(
    country=r.loc[miss["s1"], "country"].to_numpy(),
    s1_name=r.loc[miss["s1"], "name"].to_numpy(), s1_addr=r.loc[miss["s1"], "address"].to_numpy(),
    r_name=r.loc[miss["r"], "name"].to_numpy(), r_addr=r.loc[miss["r"], "address"].to_numpy(),
)
m["r_name_nonascii"] = m["r_name"].str.contains(r"[^\x00-\x7f]", regex=True)
m["r_addr_empty"] = m["r_addr"].str.strip().eq("") | m["r_addr"].str.upper().str.contains("NULL")
print(m.groupby("country").size().rename("missed").to_string())
print("share with a non-ASCII R name:", round(m["r_name_nonascii"].mean(), 3))
print("share with an empty/null R address:", round(m["r_addr_empty"].mean(), 3))
pd.set_option("display.width", 250, "display.max_colwidth", 60)
print(m.sample(min(25, len(m)), random_state=1)[["country", "s1_name", "s1_addr", "r_name", "r_addr"]].to_string())
