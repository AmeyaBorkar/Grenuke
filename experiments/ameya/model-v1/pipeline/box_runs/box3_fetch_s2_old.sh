#!/usr/bin/env bash
# Download a stage-2 run from grenuke-vast3 (scores in 256 MB chunks, 8 streams, sha256-checked; models, report, log)
# into work/incoming, then place it and mark <tag>_state/s2.done, unless the laptop queue already started that s2.
# usage: box3_fetch_s2.sh <model tag, e.g. v7sqwg>. Ends "PLACED <tag>", "TOO LATE <tag>" or an error.
set -euo pipefail
H=grenuke-vast3; R=/workspace/grenuke; W=$REPO/work; L=$W/logs
t=$1; T=ameya-s2-$t; IN=$W/incoming/$T
rm -rf $IN; mkdir -p $IN/chunks $IN/models
ssh -n $H "set -e; cd $R/work; test -s scores/$T/train.parquet; test -s scores/$T/test.parquet; test -s reports/$T.json; test -d models/$T
  rm -rf $R/dl/$T; mkdir -p $R/dl/$T; cd $R/dl/$T
  for s in train test; do split -b 256M -d -a 3 $R/work/scores/$T/\$s.parquet \$s.part.; done
  (cd $R/work/scores/$T && sha256sum train.parquet test.parquet) > sha.txt; ls *.part.* > parts.txt; echo split ok" 2>&1 | grep -vE "^Welcome|^Have fun|^AI agents"
scp -q $H:$R/dl/$T/sha.txt $H:$R/dl/$T/parts.txt $IN/
echo "$(date +%H:%M:%S) download $(wc -l < $IN/parts.txt) pieces"
sed "s#^#$H:$R/dl/$T/#" $IN/parts.txt | tr -d '\r' | xargs -P 8 -I{} scp -q {} $IN/chunks/
for s in train test; do cat $(ls $IN/chunks/$s.part.* | sort) > $IN/$s.parquet; done
(cd $IN && sha256sum -c sha.txt) || { echo "SHA MISMATCH $t"; exit 1; }
scp -q -r $H:$R/work/models/$T/. $IN/models/
scp -q $H:$R/work/reports/$T.json $IN/$T.json
scp -q $H:$R/logs/s2_$t.log $IN/s2.log || true
ssh -n $H "rm -rf $R/dl/$T" > /dev/null 2>&1 || true
if grep -q "START s2" $L/${t}_local.log 2>/dev/null; then echo "$(date +%H:%M:%S) TOO LATE $t: the laptop already started this stage 2"; exit 1; fi
mkdir -p $W/scores/$T $W/models/$T $L/${t}_state
mv -f $IN/train.parquet $W/scores/$T/train.parquet; mv -f $IN/test.parquet $W/scores/$T/test.parquet
cp -r $IN/models/. $W/models/$T/; cp $IN/$T.json $W/reports/$T.json; [ -f $IN/s2.log ] && cp $IN/s2.log $L/${t}_s2.log
touch $L/${t}_state/s2.done; rm -rf $IN
echo "$(date +%H:%M:%S) PLACED $t"
