"""Ameya's pattern on the kit: same name, same house number, DIFFERENT street. Labelled truth rate on the US/India
holdout vs how often France keeps such pairs, split by how different the street is (a typo/abbreviation is a true
copy per RESEARCH_v6 §2.4; a different street name is the suspected look-alike).

    python experiments/sachi/street_swap.py --kit work/kits/france-kit-v1
"""
import argparse, re, unicodedata
from difflib import SequenceMatcher
from pathlib import Path
import numpy as np, pandas as pd

LEGAL = set("sarl sas sasu eurl sa sci snc ei llc inc ltd pvt private limited co corp corporation company llp lp "
            "pllc pc plc the".split())
TYPES = set("rue r av ave avenue bd blvd boulevard allee all place pl chemin ch route rte impasse imp cours crs quai q "
            "street st road rd lane ln drive dr way nagar marg".split())
TOK = re.compile(r"[a-z0-9]+")


def fold(s):
    s = "" if not isinstance(s, str) else s
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def name_key(s):
    return " ".join(sorted(t for t in TOK.findall(fold(s)) if t not in LEGAL))


def num_street(a):
    first = fold(a).split(",")[0]
    toks = TOK.findall(first)
    num = next((t for t in toks if t.isdigit()), "")
    street = " ".join(t for t in toks if not t.isdigit() and t not in TYPES and len(t) > 1)
    return num, street


def tag(df):
    ns = df.s1_address.map(num_street)
    nr = df.r_address.map(num_street)
    df["same_name"] = df.s1_name.map(name_key) == df.r_name.map(name_key)
    df["same_num"] = [a[0] != "" and a[0] == b[0] for a, b in zip(ns, nr)]
    sim = [SequenceMatcher(None, a[1], b[1]).ratio() if a[1] and b[1] else np.nan for a, b in zip(ns, nr)]
    df["street_sim"] = sim
    df["pattern"] = df.same_name & df.same_num & (df.street_sim < 1.0)
    df["band"] = pd.cut(df.street_sim, [-0.01, 0.5, 0.8, 0.999], labels=["different street", "similar", "near-typo"])
    return df


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--kit", default="work/kits/france-kit-v1"); a = ap.parse_args()
    cols = ["s1", "r", "pc", "s1_name", "r_name", "s1_address", "r_address"]
    ho = pd.read_parquet(Path(a.kit) / "holdout_pairs.parquet", columns=cols + ["y", "pred"])
    fr = pd.read_parquet(Path(a.kit) / "france_pairs.parquet", columns=cols + ["pred_model", "pred_final"])
    n_ho, n_fr = 549_699, fr.s1.nunique()
    ho, fr = tag(ho[ho.pc >= 0.3].copy()), tag(fr[fr.pc >= 0.3].copy())
    h, f = ho[ho.pattern], fr[fr.pattern]
    print("same name + same house number + different street text, candidates with pc >= 0.3:\n")
    rows = []
    for b in ["different street", "similar", "near-typo"]:
        hb, fb = h[h.band == b], f[f.band == b]
        rows.append({"street similarity": b,
                     "holdout /1000 S1": round(1000 * len(hb) / n_ho, 2),
                     "holdout TRUE rate": round(hb.y.mean(), 3) if len(hb) else np.nan,
                     "holdout predicted": round(hb.pred.mean(), 3) if len(hb) else np.nan,
                     "France /1000 S1": round(1000 * len(fb) / n_fr, 2),
                     "France kept (model)": round(fb.pred_model.mean(), 3) if len(fb) else np.nan,
                     "France kept (final)": round(fb.pred_final.mean(), 3) if len(fb) else np.nan,
                     "France median pc": round(fb.pc.median(), 3) if len(fb) else np.nan})
    print(pd.DataFrame(rows).to_string(index=False))
    d = f[(f.band == "different street") & (f.pred_final == 1)]
    print(f"\nFrance: kept 'different street' pairs {len(d):,} = {1000 * len(d) / n_fr:.1f} per 1000 French S1; examples:")
    print(d[["pc", "s1_name", "s1_address", "r_address"]].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
