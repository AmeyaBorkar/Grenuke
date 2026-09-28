#!/usr/bin/env bash
# Ship the stage-2 inputs to grenuke-vast3 (so s2.py can run there): features (str, cx, lo0, ce, cmq; lg and nx are
# already there), stage-1 scores and models, the fx5 model files, the baseline matches, the full records + truth, and
# the round-1 stage-2 pseudo-labels. Large files go as 256 MB chunks, 8 scp streams at a time; every file is
# reassembled on the box and checked by sha256. Ends "UPLOAD DONE" (or "SHA MISMATCH ...").
set -euo pipefail
H=grenuke-vast3
W=/c/Users/ameya/Documents/GrenukeAmazon/work
SP=/c/Users/ameya/AppData/Local/Temp/claude/C--Users-ameya-Documents-GrenukeAmazon/19e315ba-0725-4d6f-ae6a-972e1c1f0aa9/scratchpad
R=/workspace/grenuke
CH=$SP/box3_chunks; rm -rf $CH; mkdir -p $CH
files="features/ameya-fx5-str/train.parquet features/ameya-fx5-str/test.parquet features/ameya-fx5-cx/train.parquet
features/ameya-fx5-cx/test.parquet features/ameya-fx5-lo0/train.parquet features/ameya-fx5-lo0/test.parquet
features/ameya-fx5-ce/train.parquet features/ameya-fx5-ce/test.parquet features/ameya-fx5-cmq/train.parquet
features/ameya-fx5-cmq/test.parquet scores/ameya-s1-v6all/train.parquet scores/ameya-s1-v6all/test.parquet
models/ameya-s1-v6all/config.json models/ameya-s1-v6all/stage0.ubj models/ameya-s1-v6all/stage1_g0.ubj
models/ameya-s1-v6all/stage1_g1.ubj models/ameya-s1-v6all/stage1_g2.ubj models/ameya-s1-v6all/stage1_g3.ubj
models/ameya-fx5/indic_dict.parquet models/ameya-fx5/lo_proxy_map.json models/ameya-fx5/token_lo.parquet
matches/ameya-baseline-v0/train.parquet records/train.parquet records/test.parquet records/truth.parquet"
echo "$(date +%H:%M:%S) split + sha"
: > $CH/manifest.txt; : > $CH/jobs.txt
ssh -n $H "cd $R/work && mkdir -p features/ameya-fx5-str features/ameya-fx5-cx features/ameya-fx5-lo0 features/ameya-fx5-ce features/ameya-fx5-cmq scores/ameya-s1-v6all models/ameya-s1-v6all models/ameya-fx5 matches/ameya-baseline-v0 records $R/chunks" 2>/dev/null
for f in $files; do
  id=$(echo $f | tr '/' '_')
  sha=$(sha256sum $W/$f | cut -c1-64); echo "$f $id $sha" >> $CH/manifest.txt
  if [ $(stat -c %s $W/$f) -gt 300000000 ]; then
    split -b 256M -d -a 3 $W/$f $CH/$id.part.
    for p in $CH/$id.part.*; do echo "$p" >> $CH/jobs.txt; done
  else
    cp $W/$f $CH/$id.part.000; echo "$CH/$id.part.000" >> $CH/jobs.txt
  fi
done
echo "$(date +%H:%M:%S) upload $(wc -l < $CH/jobs.txt) pieces, $(du -sh $CH | cut -f1)"
xargs -P 8 -I{} scp -q {} $H:$R/chunks/ < $CH/jobs.txt
echo "$(date +%H:%M:%S) reassemble + verify"
scp -q $CH/manifest.txt $H:$R/chunks/manifest.txt
ssh -n $H "cd $R/chunks && bad=0; while read f id sha; do
    dest=$R/work/\$f; [ \"\${f#records/}\" != \"\$f\" ] && dest=$R/work/\$f.full
    cat \$(ls \$id.part.* | sort) > \$dest
    got=\$(sha256sum \$dest | cut -c1-64); [ \"\$got\" = \"\$sha\" ] || { echo \"SHA MISMATCH \$f\"; bad=1; }
  done < manifest.txt
  if [ \$bad = 0 ]; then for s in train test truth; do mv -f $R/work/records/\$s.parquet.full $R/work/records/\$s.parquet; done; rm -f $R/chunks/*.part.*; echo verified; fi" 2>&1 | grep -vE "^Welcome|^Have fun|^AI agents"
scp -q $SP/box/pseudo_s2_fr_v7ce3.parquet $H:$R/box/
rm -rf $CH
echo "$(date +%H:%M:%S) UPLOAD DONE"
