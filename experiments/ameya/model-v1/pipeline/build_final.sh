#!/usr/bin/env bash
# build_final.sh <name> <cands tag> COUNTRY=<src> ... [--drop <parquet>] ... : compose3 -> package 2026-09-27-<name>-c2,
# validator + strict audit, sha256, and a copy to Downloads as matching_results<name>.tsv / candidate_pairs<name>.tsv.
set -euo pipefail
SP=$SCRATCH
source $SP/env6.sh > /dev/null
F=$REPO/submissions/files; T=$REPO/student_resource/dataset/test
n=$1
(cd $SP/novel && python compose3.py "$@")
bash $SP/package6.sh ameya-model-$n ameya-cands-$n 2026-09-27-$n-c2 2>&1 | grep -E "PASS|FAIL|rror"
echo "AUDIT: $(python $SP/audit_matching.py --matching $F/2026-09-27-$n-c2/matching_results.tsv --candidate $F/2026-09-27-$n-c2/candidate_pairs.tsv --test-dir $T 2>&1 | tail -1)"
P=$REPO/submissions/files/2026-09-27-$n-c2
sha256sum $P/matching_results.tsv $P/candidate_pairs.tsv | cut -c1-16,66-
echo "$(date +%H:%M) FINAL PKG READY $n"
