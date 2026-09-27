#!/usr/bin/env bash
# Rules stacked on a finished model (RESEARCH_v6.md 6.16). usage: stack.sh <model>   (e.g. v7s)
# Needs the model's tags: matches ameya-model-<model>-s3-ops3a, scores ameya-s3-<model>, candidates
# ameya-cands-<model>-c2a, and its report ameya-model-<model>-s3 (decide threshold). Outputs go to $STACK_OUT
# (default <work dir>/stack); the final matches tag is ameya-model-<model>-s3-ops3a-dpc ($STACK_TAG_SUFFIX, default
# empty, is appended to the new tags, e.g. for a test run beside the real ones).
#   1. apply_hunt.py   acr + cap (every country), nsa (countries with training labels), at the model's threshold
#   2. make_h2.py      other countries keep only the number-dropped acronym adds and no cap drops -> tag ...-h2
#   3. apply_polish.py other countries: copy (add same-name copies at the exact address) + city (drop cross-commune
#                      pairs) -> tag ...-h2pc
#   4. apply_combo.py  countries with labels: expected-F0.5 per S1 (logit shift 0.2, phantom 0.01, crowd shift -0.3)
#                      + acr + cap
#   5. merge_dpc.py    labelled countries from 4, other countries from 3 -> tag ...-dpc
# Optional, countries without labels only: apply_swapsim.py <matches tag> <new tag> drops look-alike word swaps
# (RESEARCH_v6.md 6.17).
# To take the countries without labels from another stacked model, compose.py <labelled matches> <labelled cands>
# <other matches> <other cands> <name> writes ameya-model-<name> / ameya-cands-<name> (RESEARCH_v6.md 6.17).
# Then write the submission from the -dpc (or composed) tag with its candidates:
#   python -m ber.pipeline --stage write --split test --tag <tag> --in candidates=<cands> --in matches=<tag>
set -euo pipefail
cd "$(dirname "$0")"
M=$1
FIN=ameya-model-$M-s3-ops3a; SC=ameya-s3-$M; CA=ameya-cands-$M-c2a; TS=${STACK_TAG_SUFFIX:-}
export STACK_OUT=${STACK_OUT:-$(python -c "from ber.paths import work_dir; print((work_dir() / 'stack').as_posix())")}
mkdir -p "$STACK_OUT"
THR=$(python -c "import json; from ber.paths import report_path; print(json.load(open(report_path('ameya-model-$M-s3')))['rule']['threshold'])")
LAB=$(python -c "import pyarrow.compute as pc, pyarrow.parquet as pq; from ber.paths import records_path; print('+'.join(sorted(pc.unique(pq.read_table(records_path('train'), columns=['country'])['country']).to_pylist())))")
echo "$(date +%H:%M:%S) $M: threshold $THR; countries with labels $LAB; outputs $STACK_OUT"
python apply_hunt.py --matches $FIN --scores $SC --cands $CA --thr $THR --rules acr,cap,nsa@$LAB --out hunted_$M
python make_h2.py $FIN "$STACK_OUT/hunted_$M.parquet" "$STACK_OUT/hunted_${M}_changes.csv" "$STACK_OUT/${M}_h2.parquet"
python import_tag.py "$STACK_OUT/${M}_h2.parquet" $FIN-h2$TS $CA
python apply_polish.py $FIN-h2$TS --cands $CA --scores $SC --rules copy,city --out-dir "$STACK_OUT"
python import_tag.py "$STACK_OUT/polished_$FIN-h2$TS.parquet" $FIN-h2pc$TS $CA
NUMBA_NUM_THREADS=${NUMBA_NUM_THREADS:-8} python apply_combo.py --scores $SC --final $FIN --cands $CA \
  --hunted "$STACK_OUT/hunted_$M.parquet" --base-thr $THR --shift 0.2 --lam 0.01 --crowd 4 --delta 0.3 --rules acr,cap \
  --out decided_combo_$M | tail -3
python merge_dpc.py "$STACK_OUT/decided_combo_$M.parquet" $FIN-h2pc$TS "$STACK_OUT/${M}_dpc.parquet"
python import_tag.py "$STACK_OUT/${M}_dpc.parquet" $FIN-dpc$TS $CA
echo "$(date +%H:%M:%S) stack done: matches tag $FIN-dpc$TS (candidates $CA)"
