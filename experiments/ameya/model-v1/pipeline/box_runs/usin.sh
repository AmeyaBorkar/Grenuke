#!/bin/bash
# when Bakshi's 7B has scored g1w's confident US/India pairs (usin_scored_0..3), fetch them, build the US/India q7 drop list
# (q7 < -6, p1 > 0.99; the rule he validated on the holdout: +33e-6 F, both halves positive) and rebuild the final as mixf2.
SP=/c/Users/ameya/AppData/Local/Temp/claude/C--Users-ameya-Documents-GrenukeAmazon/19e315ba-0725-4d6f-ae6a-972e1c1f0aa9/scratchpad
source $SP/env6.sh > /dev/null; K=~/.ssh/grenuke_vast2; H="-i $K -p 28860 root@202.122.49.242"; D=/workspace/grenuke/box/rescore
until ssh -n -o ConnectTimeout=15 $H "ls $D/usin_scored_0.parquet $D/usin_scored_1.parquet $D/usin_scored_2.parquet $D/usin_scored_3.parquet >/dev/null 2>&1 && echo yes" 2>/dev/null | grep -q yes; do
  [ "$(date +%H%M)" -gt 2100 ] && { echo "$(date +%H:%M) USIN never arrived"; exit 0; }; sleep 60; done
sleep 20
mkdir -p $SP/q7drop/usin; scp -q -i $K -P 28860 "root@202.122.49.242:$D/usin_scored_*.parquet" $SP/q7drop/usin/ || { echo "USIN fetch FAILED"; exit 1; }
cd /c/Users/ameya/Documents/GrenukeAmazon
python - <<PY
import glob, numpy as np, pandas as pd, pyarrow.parquet as pq
from ber.paths import records_path
d = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(r"$(cygpath -m $SP/q7drop/usin)/usin_scored_*.parquet"))], ignore_index=True)
r = pq.read_table(records_path("test"), columns=["eid", "source", "country"], filters=[("source", "==", 1)]).to_pandas().set_index("eid").country
d["country"] = r.reindex(d.s1).to_numpy()
x = d[(d.q7__logit < -6) & (d.p1 > 0.99)]
print(f"USIN scored {len(d):,} pairs; q7 < -6 & p1 > 0.99: {len(x):,} ({len(x) / len(d):.4%}); by country {x.country.value_counts().to_dict()}")
print("q7 buckets:", pd.cut(d.q7__logit, [-99, -6, -4, -2, 0, 2, 99], right=False).value_counts().sort_index().to_dict())
x[["s1", "r"]].astype("int64").assign(action="drop").to_parquet(r"$(cygpath -m $SP/q7drop/drop_q7_usin.parquet)", index=False)
PY
A=$(cygpath -m $SP/agents/fdiff)
bash $SP/build_final.sh mixf2 ameya-cands-mixqc US=ameya-model-v7sq3-s3-ops3a-dpc India=$A/g1w_india_test.parquet France=ameya-model-v7sq6r3-s3-ops3a-dpc \
  --drop "$(cygpath -m $SP/q7drop/drop_q7_fr.parquet)" --drop "$(cygpath -m $SP/q7drop/drop_q7_usin.parquet)" 2>&1 | tail -12
