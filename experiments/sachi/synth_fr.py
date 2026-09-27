"""Synthetic French supervision: labelled French pairs built from real French S1 with the generator's measured
operations, so a cross-encoder can learn France with CORRECT labels instead of its own (self-trained) decisions.

    python experiments/sachi/synth_fr.py --n-s1 40000 --out work/box_synth

True copies (y=1), 1-3 of: case, accents, legal-form reformat/drop, list append, word drop + list append, acronym,
typo; plus street abbreviation, region drop, city-first reorder, "No" prefix, empty address (5%).
Look-alikes (y=0): one content word swapped for another real French S1 word, optionally a legal-form change or a
house-number nudge, plus light copy noise so noise alone never signals y.
Writes <out>/records_synth.parquet and <out>/band_synth.parquet (s1, r, row, fold, y). Test S1 text only, no labels.
"""
from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

LEGAL = ["SARL", "SAS", "SASU", "EURL", "SA", "SCI", "SNC", "EI"]
LEGAL_FMT = {"SARL": ["S.A.R.L.", "Sarl", "sarl"], "SAS": ["S.A.S.", "Sas"], "SASU": ["Sasu", "S.A.S.U."],
             "EURL": ["Eurl", "E.U.R.L."], "SA": ["S.A.", "Sa"], "SCI": ["Sci", "S.C.I."], "SNC": ["Snc"], "EI": ["E.I."]}
LIST = ["Services", "Associés", "Groupe", "France", "& Fils", "Et Fils", "Cie", "Développement", "& Frères"]
STREET = {"Rue": ["R", "R.", "RUE"], "Avenue": ["Av", "Av.", "AV"], "Boulevard": ["Bd", "Bd.", "BD"],
          "Allée": ["All.", "Allee", "ALL"], "Place": ["Pl", "Pl."], "Chemin": ["Ch", "Ch."], "Route": ["Rte", "Rte."],
          "Impasse": ["Imp", "Imp."], "Cours": ["Crs"], "Quai": ["Q."]}
WORD = re.compile(r"[A-Za-zÀ-ÿ'-]+")


def strip_acc(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def split_legal(name: str):
    toks = name.split()
    legal = [t for t in toks if t.upper().strip(".") in LEGAL]
    core = [t for t in toks if t.upper().strip(".") not in LEGAL]
    return core, (legal[0] if legal else "")


def content_words(core):
    return [i for i, t in enumerate(core) if len(t) >= 4 and WORD.fullmatch(t) and t.lower() not in ("france",)]


def noise_name(name: str, rng) -> str:
    core, legal = split_legal(name)
    ops = rng.choice(["case", "acc", "legal", "app", "a", "acr", "typo"], size=rng.integers(1, 3), replace=False)
    for op in ops:
        if op == "app":
            core = core + [rng.choice(LIST)]
        elif op == "a":
            cw = content_words(core)
            if len(cw) >= 2:
                del core[rng.choice(cw)]
            core = core + [rng.choice(LIST)]
        elif op == "acr" and len(core) >= 2:
            core = ["".join(t[0].upper() for t in core if t[:1].isalpha())]
        elif op == "typo":
            cw = [i for i in content_words(core) if len(core[i]) >= 5]
            if cw:
                i = rng.choice(cw)
                w, j = core[i], rng.integers(1, len(core[i]) - 1)
                core[i] = w[:j] + w[j + 1:] if rng.random() < 0.5 else w[:j] + w[j] + w[j:]
    if "legal" in ops and legal:
        up = legal.upper().strip(".")
        legal = "" if rng.random() < 0.4 else rng.choice(LEGAL_FMT.get(up, [legal]))
    out = " ".join(core + ([legal] if legal else []))
    if "acc" in ops:
        out = strip_acc(out)
    if "case" in ops:
        out = out.upper() if rng.random() < 0.5 else out.lower()
    return out


def noise_addr(addr: str, rng) -> str:
    if not isinstance(addr, str) or not addr.strip() or rng.random() < 0.05:
        return ""
    parts = [p.strip() for p in addr.split(",")]
    first = parts[0]
    for full, abbr in STREET.items():
        if re.search(rf"\b{full}\b", first) and rng.random() < 0.6:
            first = re.sub(rf"\b{full}\b", rng.choice(abbr), first, count=1)
            break
    if rng.random() < 0.15:
        first = re.sub(r"^(\d)", r"No \1", first)
    parts[0] = first
    if len(parts) >= 3 and rng.random() < 0.4:
        parts = parts[:-1]
    if len(parts) >= 2 and rng.random() < 0.3:
        parts = parts[1:] + parts[:1]
    out = ", ".join(parts)
    if rng.random() < 0.3:
        out = out.upper()
    if rng.random() < 0.2:
        out = strip_acc(out)
    return out


def lookalike(name: str, addr: str, vocab: np.ndarray, rng):
    core, legal = split_legal(name)
    cw = content_words(core)
    if not cw:
        return None
    i = rng.choice(cw)
    new = core[i]
    while new.lower() == core[i].lower():
        new = str(rng.choice(vocab))
    core[i] = new
    if legal and rng.random() < 0.3:
        legal = rng.choice([l for l in LEGAL if l != legal.upper().strip(".")])
    a = addr if isinstance(addr, str) else ""
    if a and rng.random() < 0.35:
        a = re.sub(r"^(\d+)", lambda m: str(int(m.group(1)) + int(rng.integers(1, 11))), a)
    nm = " ".join(core + ([legal] if legal else []))
    if rng.random() < 0.5:
        nm = strip_acc(nm) if rng.random() < 0.5 else nm.upper()
    return nm, noise_addr(a, rng) if a and rng.random() < 0.5 else a


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", default="work/records/test.parquet")
    ap.add_argument("--country", default="France")
    ap.add_argument("--n-s1", type=int, default=40000)
    ap.add_argument("--neg-per-pos", type=float, default=1.5)
    ap.add_argument("--out", default="work/box_synth")
    ap.add_argument("--seed", type=int, default=26)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    rec = pd.read_parquet(a.records, columns=["eid", "source", "country", "name", "address"])
    s1 = rec[(rec.source == 1) & (rec.country == a.country)].reset_index(drop=True)
    vocab = pd.Series([w for n in s1.name.astype(str) for w in split_legal(n)[0] if len(w) >= 4 and WORD.fullmatch(w)])
    vocab = vocab.value_counts()
    vocab = vocab[vocab >= 20].index.to_numpy()
    pick = s1.sample(min(a.n_s1, len(s1)), random_state=a.seed).reset_index(drop=True)
    recs, pairs, eid = [], [], 9_000_000_000
    for _, row in pick.iterrows():
        nm, ad = str(row["name"]), row["address"]
        recs.append((eid, 2, a.country, noise_name(nm, rng), noise_addr(ad, rng)))
        pairs.append((row.eid, eid, 1)); eid += 1
        for _ in range(int(a.neg_per_pos) + (rng.random() < a.neg_per_pos % 1)):
            la = lookalike(nm, ad, vocab, rng)
            if la:
                recs.append((eid, 3 if rng.random() < 0.5 else 2, a.country, la[0], la[1]))
                pairs.append((row.eid, eid, 0)); eid += 1
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    syn = pd.DataFrame(recs, columns=["eid", "source", "country", "name", "address"])
    pd.concat([pick[["eid", "source", "country", "name", "address"]], syn], ignore_index=True) \
        .to_parquet(out / "records_synth.parquet", index=False)
    band = pd.DataFrame(pairs, columns=["s1", "r", "y"])
    band["row"] = np.arange(len(band))
    band["fold"] = 5 + (band.s1.to_numpy() % 15)
    band.to_parquet(out / "band_synth.parquet", index=False)
    print(f"{len(pick):,} French S1 -> {len(band):,} synthetic pairs ({band.y.mean():.3f} true); vocab {len(vocab):,} words")
    for _, r in band.sample(min(12, len(band)), random_state=1).iterrows():
        a1 = pick.set_index("eid").loc[r.s1]; b1 = syn.set_index("eid").loc[r.r]
        print(f"y={r.y}  S1: {str(a1['name'])[:34]:34s} | {str(a1['address'])[:44]}")
        print(f"      R : {str(b1['name'])[:34]:34s} | {str(b1['address'])[:44]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
