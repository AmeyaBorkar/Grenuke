#!/usr/bin/env bash
# build_pkg.sh <name> <us/india matches> <us/india cands> <france matches> <france cands> [changes.parquet]
# compose (labelled countries from the first model, others from the second) [+ apply France-only changes] -> package
# 2026-09-27-<name>-c2, validator + strict audit, and the matching sha256. Ends "PKG READY <name>".
set -euo pipefail
SP=/c/Users/ameya/AppData/Local/Temp/claude/C--Users-ameya-Documents-GrenukeAmazon/19e315ba-0725-4d6f-ae6a-972e1c1f0aa9/scratchpad
source $SP/env6.sh > /dev/null
F=C:/Users/ameya/Documents/GrenukeAmazon/submissions/files; T=C:/Users/ameya/Documents/GrenukeAmazon/student_resource/dataset/test
n=$1
(cd $SP/novel && python compose.py $2 $3 $4 $5 ${n}c 2>&1 | grep -E "composed|rror|owners|outside")
mt=ameya-model-${n}c
if [ -n "${6:-}" ]; then (cd $SP/novel && python apply_changes.py ameya-model-${n}c ameya-cands-${n}c "$(cygpath -m "$6")" $n); mt=ameya-model-$n; fi
bash $SP/package6.sh $mt ameya-cands-${n}c 2026-09-27-$n-c2 2>&1 | grep -E "PASS|FAIL|rror|matching_results.tsv$"
echo "AUDIT: $(python $SP/audit_matching.py --matching $F/2026-09-27-$n-c2/matching_results.tsv --candidate $F/2026-09-27-$n-c2/candidate_pairs.tsv --test-dir $T 2>&1 | tail -1)"
echo "$(date +%H:%M) PKG READY $n"
