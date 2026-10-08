#!/usr/bin/env bash
# (run_local_full_w.sh: stage 2 is $SP/s2w.py, so S2X may carry --pseudo-weight) Full local chain for a stage-2 variant: s2 -> decide (gate vs v7ce3-c2) -> stage 3 -> decide (gate vs v7ce3-s3) ->
# rules v3 -> acronym join -> package [-> France probes]. usage: run_local_full.sh <tag> <groups> <extra ce cols> [probes]
set -euo pipefail
SP=$SCRATCH
source $SP/env6.sh > /dev/null
TAG=$1; GRP=$2; CEX=$3
M=$REPO/.claude/worktrees/research-v5/experiments/ameya/model-v1
W=$REPO/work; L=$W/logs
ST=$L/${TAG}_state; mkdir -p $ST
LEG=leg__rel,leg__n_s1,leg__n_r,leg__inter,leg__s1_only,leg__r_only
NX=nx__d1,nx__nudge,nx__digit_sub,nx__digit_swap,nx__suffix,nx__len_diff
step() {
  local name=$1; shift
  if [ -f $ST/$name.done ]; then echo "$(date +%H:%M:%S) SKIP $name"; return 0; fi
  echo "$(date +%H:%M:%S) START $name"; "$@"; touch $ST/$name.done; echo "$(date +%H:%M:%S) DONE $name"
}
gate() { python -c "import json; d=json.load(open('$REPO/work/reports/$1.json')); g=d['gate_vs_base']; print('GATE $1: holdout %.6f vs base %+.6f [%+.6f, %+.6f] rule %s' % (d['holdout']['macro_f05'], g['delta'], g['ci_low'], g['ci_high'], d['rule']['method']))"; }
cd $M
step s2 bash -c "python $SP/s2w.py --feats ameya-fx5 --s1 ameya-s1-v6all --tag ameya-s2-$TAG --groups $GRP --cluster --extra $LEG,$CEX,$NX --all ${S2X:-} > $L/${TAG}_s2.log 2>&1"
step decide bash -c "python decide.py --scores ameya-s2-$TAG --col pc --tag ameya-model-$TAG-c2 --base ameya-model-v7ce3-c2 --p-cand 0.02 --top-r 2 > $L/${TAG}_decide.log 2>&1"
gate ameya-model-$TAG-c2
step s3 bash -c "python stage3.py --scores ameya-s2-$TAG --tag ameya-s3-$TAG --p-cand 0.02 --top-r 2 > $L/${TAG}_s3.log 2>&1"
step decide_s3 bash -c "python decide.py --scores ameya-s3-$TAG --col pc --tag ameya-model-$TAG-s3 --base ameya-model-v7ce3-s3 --p-cand 0.02 --top-r 2 > $L/${TAG}_s3_decide.log 2>&1"
gate ameya-model-$TAG-s3
step ops bash -c "python post_ops.py --matches ameya-model-$TAG-s3 --scores ameya-s3-$TAG --cands ameya-cands-v6all-c2 --feats ameya-fx5 --tag ameya-model-$TAG-s3-ops3 --robust-addr > $L/${TAG}_ops3.log 2>&1"
step acr bash -c "python acr_join.py --split test --matches ameya-model-$TAG-s3-ops3 --cands ameya-cands-v6all-c2 --tag ameya-model-$TAG-s3-ops3a --cands-tag ameya-cands-$TAG-c2a > $L/${TAG}_acr.log 2>&1"
step pkg bash -c "bash $SP/package6.sh ameya-model-$TAG-s3-ops3a ameya-cands-$TAG-c2a 2026-09-27-$TAG-s3-ops3a-c2 > $L/${TAG}_pkg.log 2>&1"
if [ "${4:-}" != "probes" ]; then echo "$(date +%H:%M:%S) ALL DONE $TAG (no probes)"; exit 0; fi
step fr090r bash -c "bash $SP/make_frcut.sh ameya-model-$TAG-s3 ameya-s3-$TAG 0.9 $TAG-fr090r 2026-09-27-probe-$TAG-fr090r > $L/${TAG}_fr090r.log 2>&1"
step fr095r bash -c "bash $SP/make_frcut.sh ameya-model-$TAG-s3 ameya-s3-$TAG 0.95 $TAG-fr095r 2026-09-27-probe-$TAG-fr095r > $L/${TAG}_fr095r.log 2>&1"
step fr080r bash -c "bash $SP/make_frcut.sh ameya-model-$TAG-s3 ameya-s3-$TAG 0.8 $TAG-fr080r 2026-09-27-probe-$TAG-fr080r > $L/${TAG}_fr080r.log 2>&1"
echo "$(date +%H:%M:%S) ALL DONE $TAG"
