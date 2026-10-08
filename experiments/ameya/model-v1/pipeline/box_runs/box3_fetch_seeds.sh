#!/usr/bin/env bash
# When the box's seed runs of v7sq (XGBoost seeds 1-3) end, fetch each (box3_fetch_s2.sh) for a later bag. Ends "SEEDS DONE".
set -uo pipefail
H=grenuke-vast3; R=/workspace/grenuke
SP=$SCRATCH
rsh() { ssh -n -o ConnectTimeout=20 $H "$@" 2>&1 | grep -vE "^Welcome|^Have fun|^AI agents"; }
for s in 1 2 3; do
  until rsh "pgrep -f 'ameya-s2-v7sq-sd$s' > /dev/null || echo ended" | grep -q ended; do sleep 60; done
  echo "$(date +%H:%M:%S) sd$s ended: $(rsh "tail -c 150 $R/logs/s2_v7sq-sd$s.log | tail -1 | cut -c1-100")"
  bash $SP/box3_fetch_s2.sh v7sq-sd$s 2>&1 | tail -3
done
echo "$(date +%H:%M:%S) SEEDS DONE"
