#!/usr/bin/env bash
cd /workspace/grenuke; . ./env.sh; export HF_HOME=/workspace/grenuke/hf; D=box/rescore
rclone copy gdrive:grenuke-train-backup/box/out_q34st/adapter_0 box/out_q34st/adapter_0 &
python -c "from huggingface_hub import snapshot_download; snapshot_download('Qwen/Qwen3-4B-Base', allow_patterns=['*.json','*.safetensors','*.txt','*.jinja'])" > logs/b5_dl.log 2>&1 &
python - <<PY
import glob, pandas as pd
D="box/rescore"
h=pd.read_parquet(f"{D}/hold_scored.parquet"); h=h[h.q7__logit<0].rename(columns={"q7__logit":"q7"})[["s1","r","p1","y","q7"]]; h.to_parquet(f"{D}/b5_hold_pairs.parquet",index=False)
fr=pd.concat([pd.read_parquet(f) for f in glob.glob(f"{D}/fr_scored_*.parquet")]); fr=fr[(fr.p1>0.99)&(fr.q7__logit<0)]
bp=pd.read_parquet(f"{D}/bplus_scored.parquet"); bp=bp[(bp.src=="mixmdp_unscored")&(bp.q7__logit<0)]
t=pd.concat([fr,bp],ignore_index=True).rename(columns={"q7__logit":"q7"})[["s1","r","p1","q7"]]; t.to_parquet(f"{D}/b5_test_pairs.parquet",index=False)
print("hold",len(h),"test",len(t))
PY
wait
S="python repo/experiments/bakshi/box/score_pairs.py --model Qwen/Qwen3-4B-Base --adapter box/out_q34st/adapter_0 --batch 64"
CUDA_VISIBLE_DEVICES=0 $S --pairs $D/b5_hold_pairs.parquet --split train --out $D/b5_hold_4b.parquet > logs/b5_hold.log 2>&1 &
CUDA_VISIBLE_DEVICES=1 $S --pairs $D/b5_test_pairs.parquet --split test --out $D/b5_test_4b.parquet > logs/b5_test.log 2>&1 &
wait
tail -1 logs/b5_hold.log; tail -1 logs/b5_test.log
python - <<PY
import numpy as np, pandas as pd
D="box/rescore"
h=pd.read_parquet(f"{D}/b5_hold_4b.parquet").rename(columns={"q7__logit":"q4"})
full=pd.read_parquet(f"{D}/hold_scored.parquet"); truth=pd.read_parquet(f"{D}/hold_truth.parquet").set_index("s1")
def f05(tp,n,nt):
    fp,fn=n-tp,nt-tp; den=1.25*tp+0.25*fn+fp
    return np.where((n==0)&(nt==0),1.0,np.where(den>0,1.25*tp/np.maximum(den,1e-12),0.0))
def macro(keep):
    g=full[keep].groupby("s1").agg(tp=("y","sum"),n=("y","size")).reindex(truth.index).fillna(0)
    return pd.Series(f05(g.tp.to_numpy(),g.n.to_numpy(),truth.n_true.to_numpy()),index=truth.index)
base=macro(np.ones(len(full),bool)); hh=(truth.index.to_numpy()//7)%2
K=4_000_000_000; key=lambda d: d.s1.to_numpy(np.int64)*K+d.r.to_numpy(np.int64)
print("holdout, OUT-OF-BAND (p1>0.99) predictions by 7B band x 4B agreement: n / truth rate")
ob=h[h.p1>0.99]
for lo,hi in [(-99,-6),(-6,-4),(-4,-2),(-2,0)]:
    m=(ob.q7>=lo)&(ob.q7<hi); row=f"7B[{lo:>3},{hi:>2}) all n={m.sum():>5} true={ob.y[m].mean() if m.any() else float('nan'):.3f}"
    for t4 in (0,-2,-4): mm=m&(ob.q4<t4); row+=f" | 4B<{t4:>2}: n={mm.sum():>5} true={ob.y[mm].mean() if mm.any() else float('nan'):.3f}"
    print(row)
for t4 in (0,-2,-4):
    for lo in (-6,-4,-2):
        sel=ob[(ob.q7<0)&(ob.q7>=lo)&(ob.q4<t4)]; drop=np.isin(key(full),key(sel))&(full.q7__logit<0).to_numpy()
        d=macro(~drop)-base
        print(f"drop out-of-band 7B in [{lo},0) & 4B<{t4}: n={int(drop.sum())} true={int(full.y[drop].sum())} dF {d.mean():+.7f} A {d[hh==0].mean():+.7f} B {d[hh==1].mean():+.7f}")
t=pd.read_parquet(f"{D}/b5_test_4b.parquet").rename(columns={"q7__logit":"q4"})
print("France test out-of-band pairs with 7B<0:",len(t))
for lo,hi in [(-99,-6),(-6,-4),(-4,-2),(-2,0)]:
    m=(t.q7>=lo)&(t.q7<hi); print(f"  7B[{lo},{hi}): n={m.sum()} 4B<0: {(m&(t.q4<0)).sum()} 4B<-2: {(m&(t.q4<-2)).sum()} 4B<-4: {(m&(t.q4<-4)).sum()}")
t.to_parquet(f"{D}/b5_test_4b.parquet",index=False)
PY
