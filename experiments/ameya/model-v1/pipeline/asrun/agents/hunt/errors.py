"""Task 1: FP / FN tables of v7nst (stage-3, threshold 0.675, argmax owner, candidate cut) on the holdout."""
from __future__ import annotations

import os
import time

import numpy as np
import pandas as pd

from base import D, K, Eval, load, pair_text_feats, text_for, universe_and_truth

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 30)
pd.set_option("display.max_rows", 400)


def main():
    t0 = time.time()
    df = load()
    uni, cty, th = universe_and_truth()
    ev = Eval(df, uni, th)
    base = df.pred.to_numpy()
    print("baseline holdout F0.5", round(ev.score(base), 6), "universe", uni.size)

    # truth distributions (all train S1): S2 and S3 copies per S1
    from base import load_truth  # noqa
    import pyarrow.parquet as pq
    from ber.paths import records_path
    import pyarrow.compute as pc
    t = pq.read_table(records_path("train"), columns=["eid", "source"])
    s1_all = t.filter(pc.equal(t["source"], 1))["eid"].to_numpy()
    del t
    from ber.records import load_truth as lt
    tr = lt()
    src = (tr.r.to_numpy() // 1_000_000_000)
    n2 = pd.Series(tr.s1[src == 2]).value_counts().reindex(s1_all, fill_value=0).to_numpy()
    n3 = pd.Series(tr.s1[src == 3]).value_counts().reindex(s1_all, fill_value=0).to_numpy()
    del tr
    print("\nTruth copy counts over all train S1 (n =", s1_all.size, ")")
    print("S2:", pd.Series(n2).value_counts(normalize=True).sort_index().round(5).to_dict())
    print("S3:", pd.Series(n3).value_counts(normalize=True).sort_index().round(5).to_dict())
    tot = n2 + n3
    print("total:", pd.Series(tot).value_counts(normalize=True).sort_index().round(5).to_dict())
    jt = pd.crosstab(n2, n3, normalize=True)
    ind = np.outer(jt.sum(1), jt.sum(0))
    print("joint / independent ratio (rows n2, cols n3):")
    print((jt / ind).round(3).to_string())
    pd.DataFrame({"s1": s1_all, "n2": n2, "n3": n3}).to_parquet(os.path.join(D, "truth_counts.parquet"), index=False)

    # per-S1 counts on the holdout
    thsrc = (th.r.to_numpy() // 1_000_000_000)
    s1i = np.searchsorted(uni, th.s1.to_numpy())
    nt = np.bincount(s1i, minlength=uni.size)
    nt2 = np.bincount(s1i[thsrc == 2], minlength=uni.size)
    nt3 = np.bincount(s1i[thsrc == 3], minlength=uni.size)
    h = df.hold.to_numpy()
    idx = np.full(len(df), -1)
    idx[h] = np.searchsorted(uni, df.s1.to_numpy()[h])
    pm = base & h
    np_ = np.bincount(idx[pm], minlength=uni.size)
    np2 = np.bincount(idx[pm & (df.src.to_numpy() == 2)], minlength=uni.size)
    np3 = np.bincount(idx[pm & (df.src.to_numpy() == 3)], minlength=uni.size)
    nh = np.bincount(idx[pm], weights=df.y.to_numpy()[pm], minlength=uni.size)
    print("\nholdout per-S1 predicted vs true: pred-true diff distribution",
          pd.Series(np_ - nt).value_counts().sort_index().to_dict())
    print("S2 pred count dist", pd.Series(np2).value_counts().sort_index().to_dict())
    print("S3 pred count dist", pd.Series(np3).value_counts().sort_index().to_dict())
    print("S2 true count dist (holdout)", pd.Series(nt2).value_counts().sort_index().to_dict())
    print("S3 true count dist (holdout)", pd.Series(nt3).value_counts().sort_index().to_dict())

    # pair features on all cache rows
    s1, r, p = df.s1.to_numpy(), df.r.to_numpy(), df.pc.to_numpy()
    rec_n03 = pd.Series(p >= 0.3).groupby(r).transform("sum").to_numpy()
    df["contested"] = rec_n03 >= 2
    order = np.lexsort((-p, s1))
    rk = np.empty(len(df), np.int32)
    ss = s1[order]
    start = np.r_[True, ss[1:] != ss[:-1]]
    first = np.maximum.accumulate(np.where(start, np.arange(ss.size), 0))
    rk[order] = np.arange(ss.size) - first
    df["rank_s1"] = rk
    order = np.lexsort((s1, -p, r))
    rr = r[order]
    start = np.r_[True, rr[1:] != rr[:-1]]
    first = np.maximum.accumulate(np.where(start, np.arange(rr.size), 0))
    rk2 = np.empty(len(df), np.int32)
    rk2[order] = np.arange(rr.size) - first
    df["rank_r"] = rk2
    df["band"] = pd.cut(df.pc, [-0.01, 0.1, 0.3, 0.5, 0.6, 0.675, 0.7, 0.8, 0.9, 0.95, 0.99, 0.999, 1.0]).astype(str)

    # marginal gains per error pair (alone)
    F = ev.per_entity(base)
    ii = idx.copy()
    fp = h & base & (df.y.to_numpy() == 0)
    fn_in = h & ~base & (df.y.to_numpy() == 1)
    def f(nh_, np__, nt_):
        den = 0.25 * nt_ + np__
        return np.where(den > 0, 1.25 * nh_ / np.where(den > 0, den, 1), 1.0)
    g_fp = f(nh[ii[fp]], np_[ii[fp]] - 1, nt[ii[fp]]) - F[ii[fp]]
    g_fn = f(nh[ii[fn_in]] + 1, np_[ii[fn_in]] + 1, nt[ii[fn_in]]) - F[ii[fn_in]]
    # blocking misses: truth pairs outside the cache candidate set
    ck = np.sort(s1[h] * K + r[h])
    tk = th.s1.to_numpy() * K + th.r.to_numpy()
    j = np.searchsorted(ck, tk); j[j >= ck.size] = 0
    out_c = ck[j] != tk
    print(f"\nholdout S1 {uni.size}; true pairs {len(th)}; outside the candidate set {out_c.sum()}; "
          f"FP {fp.sum()}; FN inside candidates {fn_in.sum()}")
    loss = 1 - F
    print("total loss", round(loss.mean(), 6))
    # loss decomposition per S1 type
    has_fp = np.bincount(ii[fp], minlength=uni.size) > 0
    has_fn = (nt - nh) > 0
    typ = np.where(has_fp & has_fn, "fp+fn", np.where(has_fp, "fp only", np.where(has_fn, "fn only", "ok")))
    print(pd.DataFrame({"typ": typ, "loss": loss}).groupby("typ").loss.agg(["size", "sum"]).assign(
        per_s1=lambda x: x["sum"] / uni.size).to_string())

    err = pd.concat([
        df.loc[fp].assign(err="FP", gain=g_fp),
        df.loc[fn_in].assign(err="FN_in", gain=g_fn),
    ], ignore_index=True)
    err["n_pred"] = np_[np.searchsorted(uni, err.s1.to_numpy())]
    err["n_true"] = nt[np.searchsorted(uni, err.s1.to_numpy())]
    ei = np.searchsorted(uni, err.s1.to_numpy())
    err["n_pred_src"] = np.where(err.src == 2, np2[ei], np3[ei])
    err["n_true_src"] = np.where(err.src == 2, nt2[ei], nt3[ei])
    err["cnt"] = np.sign(err.n_pred - err.n_true).map({-1: "pred<true", 0: "pred=true", 1: "pred>true"})
    err["country"] = cty.reindex(err.s1.to_numpy()).to_numpy()
    # is the FN record predicted for another S1?
    pr = df.loc[base, ["r", "s1"]].set_index("r").s1
    err["r_pred_elsewhere"] = pr.reindex(err.r.to_numpy()).notna().to_numpy() & (err.err == "FN_in")
    print("text features ...", round(time.time() - t0), "s", flush=True)
    txt = text_for("train", np.r_[err.s1.to_numpy(), err.r.to_numpy()])
    err = pair_text_feats(err, txt)
    err["r_empty"] = txt.aempty.reindex(err.r.to_numpy()).to_numpy()
    err["s1_empty"] = txt.aempty.reindex(err.s1.to_numpy()).to_numpy()
    err["sname"] = txt.name.reindex(err.s1.to_numpy()).to_numpy()
    err["saddr"] = txt.address.reindex(err.s1.to_numpy()).to_numpy()
    err["rname"] = txt.name.reindex(err.r.to_numpy()).to_numpy()
    err["raddr"] = txt.address.reindex(err.r.to_numpy()).to_numpy()
    err.drop(columns=["own", "pred", "hold"]).to_parquet(os.path.join(D, "errors.parquet"), index=False)
    N = uni.size
    for col in ["src", "r_empty", "contested", "cnt", "kind", "same_addr", "band", "rank_s1", "rank_r",
                "r_pred_elsewhere", "country"]:
        t = err.groupby(["err", col]).gain.agg(pairs="size", gain_sum="sum")
        t["oracle_gain"] = t.gain_sum / N
        print(f"\n== by {col}\n", t.drop(columns="gain_sum").round(6).to_string())
    t = err.groupby(["err", "src", "r_empty", "contested", "cnt"]).gain.agg(pairs="size", gain_sum="sum")
    t["oracle_gain"] = t.gain_sum / N
    print("\n== cross\n", t.drop(columns="gain_sum").sort_values("oracle_gain", ascending=False).head(40).round(6).to_string())
    print("done", round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
