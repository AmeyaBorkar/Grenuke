"""French competence of finished models, label-free: AUC and mean pc of their test scores on France's rule
populations (rule_pop.py: A/APP/ACR = 1, op-B = 0).

    python experiments/ameya/model-v1/rule_auc.py <work dir> <rule_pop.parquet> ameya-s2-v7n ameya-s2-v7nst ...

It tracked the leaderboard's France gains (v6all 0.855, v7ce3 0.865, v7n 0.872; RESEARCH_v6.md section 6.8). A model
self-trained on the rules' decisions scores high by construction, so compare those among themselves only.
"""
import sys
import numpy as np, pandas as pd, pyarrow.parquet as pq
W, pop_path = sys.argv[1], sys.argv[2]
pop = pd.read_parquet(pop_path)
K = 4_000_000_000
pk = pop.s1.to_numpy() * K + pop.r.to_numpy()
def auc(y, s):
    o = np.argsort(s, kind="stable"); r = np.empty(len(s)); r[o] = np.arange(1, len(s) + 1)
    n1 = y.sum(); n0 = len(y) - n1
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
for tag in sys.argv[3:]:
    sc = pq.read_table(f"{W}/scores/{tag}/test.parquet", columns=["s1", "r", "pc"]).to_pandas()
    s = pd.Series(sc.pc.to_numpy(), index=sc.s1.to_numpy() * K + sc.r.to_numpy())
    p = s.reindex(pk).to_numpy()
    ok = ~np.isnan(p)
    y = pop.y.to_numpy()[ok]; pp = p[ok]; op = pop.op.to_numpy()[ok]
    per = " ".join(f"{o} {pp[op == o].mean():.3f}" for o in ("A", "APP", "ACR", "B"))
    print(f"{tag}: scored {ok.sum()} of {len(pop)}; AUC {auc(y, pp):.4f}; mean pc {per}; B above 0.7 {(pp[op == 'B'] > 0.7).mean():.3f}, true-copy ops above 0.7 {(pp[y == 1] > 0.7).mean():.3f}")
