"""DEV ONLY: small real-data candidates + features so the model code can run
before the team's feature stage exists.

    python experiments/sachi/make_dev_features.py --data student_resource/dataset --n-s1 20000
"""
from __future__ import annotations

import argparse, random, re, unicodedata, zlib
from pathlib import Path

import numpy as np
import pandas as pd
from rapidfuzz import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer

OUT = Path(__file__).parent / "work"
LEGAL = set("inc llc ltd limited pvt private co corp corporation company llp the".split())


def norm(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def core(s):
    return " ".join(t for t in norm(s).split() if t not in LEGAL)


def nums(s):
    return [n.lstrip("0") or "0" for n in re.findall(r"\d+", s)]


def dev_fold(s1_id):
    """DEV ONLY stable 20-fold id. The real split is the team's (contract C2)."""
    return zlib.crc32(s1_id.encode()) % 20


def read_tsv_lines(path, keep=None, sample_rate=0.0, seed=0):
    rng = random.Random(seed)
    rows = []
    with open(path, encoding="utf-8") as f:
        next(f)
        for line in f:
            eid = line[:line.index("\t")]
            if (keep is not None and eid in keep) or (sample_rate and rng.random() < sample_rate):
                rows.append(line.rstrip("\n").split("\t"))
    return pd.DataFrame(rows, columns=["eid", "name", "address", "country"])


def build(data, n_s1, extra_rate, k, seed=0):
    rng = random.Random(seed)
    gt = {}
    with open(data / "train" / "train_ground_truth.tsv") as f:
        next(f)
        for line in f:
            a, b = line.rstrip("\n").split("\t")
            gt[a] = [x for x in b.split(",") if x]
    s1_ids = rng.sample(sorted(gt), n_s1)
    true_recs = {r for s in s1_ids for r in gt[s]}
    print(f"sampled {n_s1} S1, {len(true_recs)} true records")

    s1 = read_tsv_lines(data / "train" / "train_source1.tsv", keep=set(s1_ids))
    pool = pd.concat([read_tsv_lines(data / "train" / f"train_source{i}.tsv", keep=true_recs,
                                     sample_rate=extra_rate, seed=seed + i) for i in (2, 3)])
    pool = pool.drop_duplicates("eid")
    print(f"record pool {len(pool)} (true + random distractors)")

    for d in (s1, pool):
        d["n"] = d["name"].map(core)
        d["a"] = d["address"].map(norm)
        d["txt"] = d["n"] + " | " + d["a"]

    cands = []
    for c in s1["country"].unique():
        A, B = s1[s1.country == c].reset_index(drop=True), pool[pool.country == c].reset_index(drop=True)
        vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 3), min_df=2, sublinear_tf=True,
                              dtype=np.float32).fit(pd.concat([A.txt, B.txt]))
        XA, XB = vec.transform(A.txt), vec.transform(B.txt).T.tocsc()
        for lo in range(0, len(A), 256):
            S = (XA[lo:lo + 256] @ XB).toarray()
            top = np.argpartition(-S, min(k, S.shape[1] - 1), axis=1)[:, :k]
            for i in range(top.shape[0]):
                order = top[i][np.argsort(-S[i, top[i]])]
                for rank, j in enumerate(order):
                    cands.append((A.eid[lo + i], B.eid[j], S[i, j], rank))
    cand = pd.DataFrame(cands, columns=["s1_eid", "r_eid", "ret__cos", "ret__rank"])

    truth = pd.DataFrame([(s, r) for s in s1_ids for r in gt[s]], columns=["s1_eid", "r_eid"])
    hit = cand.merge(truth, on=["s1_eid", "r_eid"]).shape[0]
    print(f"candidates {len(cand)} ({len(cand)/n_s1:.1f}/S1), pair recall {hit/len(truth):.4f}")

    S = s1.set_index("eid"); R = pool.set_index("eid")
    a_n, b_n = S.n.reindex(cand.s1_eid).to_numpy(), R.n.reindex(cand.r_eid).to_numpy()
    a_a, b_a = S.a.reindex(cand.s1_eid).to_numpy(), R.a.reindex(cand.r_eid).to_numpy()
    raw_a, raw_b = S.address.reindex(cand.s1_eid).to_numpy(), R.address.reindex(cand.r_eid).to_numpy()
    f = cand.copy()
    f["name__ratio"] = [fuzz.ratio(x, y) for x, y in zip(a_n, b_n)]
    f["name__token_set"] = [fuzz.token_set_ratio(x, y) for x, y in zip(a_n, b_n)]
    f["name__partial"] = [fuzz.partial_ratio(x, y) for x, y in zip(a_n, b_n)]
    ta, tb = [set(x.split()) for x in a_n], [set(y.split()) for y in b_n]
    f["name__jaccard"] = [len(x & y) / max(1, len(x | y)) for x, y in zip(ta, tb)]
    f["extra__r_not_s1"] = [len(y - x) for x, y in zip(ta, tb)]
    f["extra__s1_not_r"] = [len(x - y) for x, y in zip(ta, tb)]
    f["addr__token_set"] = [fuzz.token_set_ratio(x, y) for x, y in zip(a_a, b_a)]
    f["addr__ratio"] = [fuzz.ratio(x, y) for x, y in zip(a_a, b_a)]
    f["addr__empty_r"] = [float(not y) for y in b_a]
    na, nb = [nums(x) for x in raw_a], [nums(y) for y in raw_b]
    f["num__first_equal"] = [float(bool(x and y and x[0] == y[0])) for x, y in zip(na, nb)]
    f["num__first_prefix"] = [float(bool(x and y and (x[0].startswith(y[0]) or y[0].startswith(x[0]))))
                              for x, y in zip(na, nb)]
    f["num__jaccard"] = [len(set(x) & set(y)) / max(1, len(set(x) | set(y))) for x, y in zip(na, nb)]
    f["num__r_missing"] = [float(not y) for y in nb]
    f["ctx__s1_name_count"] = s1.n.value_counts().reindex(a_n).to_numpy()
    f["src__is_s3"] = cand.r_eid.str.startswith("S3").astype(float)
    f["ret__rank_in_r"] = f.groupby("r_eid")["ret__cos"].rank(ascending=False)
    f["fold"] = f.s1_eid.map(dev_fold)

    OUT.mkdir(exist_ok=True)
    f.to_parquet(OUT / "features_dev.parquet", index=False)
    truth.to_parquet(OUT / "truth_dev.parquet", index=False)
    s1[["eid", "country"]].rename(columns={"eid": "s1_eid"}).to_parquet(OUT / "s1_dev.parquet", index=False)
    print("wrote", OUT)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="student_resource/dataset")
    ap.add_argument("--n-s1", type=int, default=20000)
    ap.add_argument("--extra-rate", type=float, default=0.02)
    ap.add_argument("--k", type=int, default=20)
    a = ap.parse_args()
    build(Path(a.data), a.n_s1, a.extra_rate, a.k)
