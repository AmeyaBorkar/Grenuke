#!/usr/bin/env bash
# g1w-dpcsf minus the French predictions the 7B rejects hardest (q7 logit < -6, outside the band): validated on the
# labelled holdout (+0.000033, both halves positive). US/India unchanged.
set -euo pipefail
R=/workspace/grenuke; cd $R; . ./env.sh
V=g1w; SRC=ameya-model-$V-s3-ops3a-dpcsf; NEW=ameya-model-$V-s3-ops3a-dpcsfq; CA=ameya-cands-$V-c2a
python - <<PY
import glob, numpy as np, pandas as pd
from ber.artifacts import read_table
K = 4_000_000_000
fr = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob("$R/box/rescore/fr_scored_*.parquet"))])
d = fr[(fr.q7__logit < -6) & (fr.p1 > 0.99)]
m = read_table("matches", "$SRC", "test")
k = m.s1.to_numpy(np.int64) * K + m.r.to_numpy(np.int64); dk = d.s1.to_numpy(np.int64) * K + d.r.to_numpy(np.int64)
keep = ~np.isin(k, dk)
print(f"drop list {len(d):,}; present in $SRC: {int((~keep).sum()):,}; pairs {len(m):,} -> {int(keep.sum()):,}")
m[keep].reset_index(drop=True).to_parquet("$R/box/rescore/${V}_dpcsfq.parquet", index=False)
PY
cd $M/stack && python import_tag.py "$R/box/rescore/${V}_dpcsfq.parquet" $NEW $CA
export BER_OUTPUT_DIR=$R/output/$V/dpcsfq; mkdir -p $BER_OUTPUT_DIR
MR=$BER_OUTPUT_DIR/matching_results.tsv; CP=$BER_OUTPUT_DIR/candidate_pairs.tsv
python -m ber.pipeline --stage write --split test --tag $NEW --in candidates=$CA --in matches=$NEW > $R/logs/q7drop_write.log 2>&1
python $R/repo/student_resource/utils/validate_submission.py --matching $MR --candidate $CP --test-dir $BER_DATA_DIR/test 2>&1 | tail -1
python $B/final-package/audit_matching.py --matching $MR --candidate $CP --test-dir $BER_DATA_DIR/test 2>&1 | grep AUDIT
python $B/final-package/diff_candidates.py --base v7sq-dpc=$R/ref/v7sq_dpc_matching.tsv --cand g1w-dpcsfq=$MR --s1-tsv $BER_DATA_DIR/test/test_source1.tsv 2>&1 | grep -E "^g1w"
sha256sum $MR $CP
