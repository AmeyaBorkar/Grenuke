"""synth_fr3.py: synth_fr2.py re-weighted to the real French operation mix measured in our France error
analysis (27 Sep 17:20): true copies are mostly legal-form drops/changes and word reorders
(22.6% of real French copies), with whole-word garbles, -1/-2 house-number moves (the NUM operation) and few list
appends, typos, acronyms or brands; about 30% of real French non-matches are the same name at another address, and
only +d house-number nudges are look-alikes; 32% of real addresses name the department. Defaults follow those rates.

synth_fr2.py: Sachi's synth_fr.py (experiments/sachi, PR #61) plus three generator operations seen in our French
errors (RESEARCH_v6.md 6.18, inspection of v7sq6wg vs v7sq): brand-name copies (an invented pseudo-word at the S1's own
address, y=1), house-number look-alikes (a copy-like name at another number on the same street, y=0) and another real
French business at the S1's address (y=0). --brand, --numlike, --otherbiz set their rates per picked S1.

Synthetic French supervision: labelled French pairs built from real French S1 with the generator's measured
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
    OPS = ["legal", "case", "acc", "order", "garble", "app", "a", "acr", "typo"]
    OPW = np.array([0.45, 0.13, 0.12, 0.12, 0.06, 0.03, 0.03, 0.03, 0.03])
    ops = rng.choice(OPS, size=rng.integers(1, 3), replace=False, p=OPW / OPW.sum())
    legal_first = False
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
        elif op == "order":
            if legal and rng.random() < 0.5:
                legal_first = True
            elif len(core) >= 2:
                i, j = rng.choice(len(core), size=2, replace=False)
                core[i], core[j] = core[j], core[i]
        elif op == "garble":
            cw = [i for i in content_words(core) if len(core[i]) >= 5]
            if cw:
                i = rng.choice(cw)
                w = list(core[i])
                for _ in range(int(rng.integers(2, 4))):
                    k = int(rng.integers(1, len(w) - 1))
                    r = rng.random()
                    if r < 0.4:
                        w[k] = chr(int(rng.integers(97, 123)))
                    elif r < 0.7:
                        w.insert(k, chr(int(rng.integers(97, 123))))
                    elif len(w) > 4:
                        del w[k]
                core[i] = "".join(w)
        elif op == "typo":
            cw = [i for i in content_words(core) if len(core[i]) >= 5]
            if cw:
                i = rng.choice(cw)
                w, j = core[i], rng.integers(1, len(core[i]) - 1)
                core[i] = w[:j] + w[j + 1:] if rng.random() < 0.5 else w[:j] + w[j] + w[j:]
    if "legal" in ops and legal:
        up = legal.upper().strip(".")
        r = rng.random()
        legal = "" if r < 0.4 else (f"[{up}]" if r < 0.47 else (f"({up})" if r < 0.52 else rng.choice(LEGAL_FMT.get(up, [legal]))))
    out = " ".join((([legal] if legal else []) + core) if legal_first else (core + ([legal] if legal else [])))
    if "acc" in ops:
        out = strip_acc(out)
    if "case" in ops:
        out = out.upper() if rng.random() < 0.5 else out.lower()
    return out


DEPT = {"hauts-de-france": "Nord", "nouvelle-aquitaine": "Gironde", "pays de la loire": "Loire-Atlantique"}
PDC = {"calais", "boulogne-sur-mer", "arras", "lens", "bethune", "saint-omer"}


def noise_addr(addr: str, rng, num_move: bool = False) -> str:
    if not isinstance(addr, str) or not addr.strip() or rng.random() < 0.05:
        return ""
    parts = [p.strip() for p in addr.split(",")]
    first = parts[0]
    for full, abbr in STREET.items():
        if re.search(rf"\b{full}\b", first) and rng.random() < 0.6:
            first = re.sub(rf"\b{full}\b", rng.choice(abbr), first, count=1)
            break
    if num_move and rng.random() < 0.08:
        first = re.sub(r"^(\d+)", lambda m: str(max(1, int(m.group(1)) - int(rng.integers(1, 3)))), first)
    r = rng.random()
    if r < 0.12:
        first = re.sub(r"^(\d)", lambda m: str(rng.choice(["No ", "N ", "# ", "N° "])) + m.group(1), first)
    elif r < 0.15:
        first = re.sub(r"^(\d+)", lambda m: m.group(1).zfill(4), first)
    elif r < 0.17:
        first = re.sub(r"^(\d+)", lambda m: "(" + m.group(1) + ")", first)
    parts[0] = first
    if len(parts) >= 3 and rng.random() < 0.4:
        parts = parts[:-1]
    if rng.random() < 0.5:
        low = [strip_acc(p).lower() for p in parts]
        city = next((p for p in low[1:] if p not in DEPT and not re.search(r"\d", p)), "")
        for k, p in enumerate(low):
            if p in DEPT:
                parts[k] = "Pas-de-Calais" if city in PDC else DEPT[p]
    if len(parts) >= 2 and rng.random() < 0.15:
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
        a = re.sub(r"^(\d+)", lambda m: str(int(m.group(1)) + int(rng.choice([1, 2, 3, 4, 5, 7, 9, 11, 13, 21]))), a)
    nm = " ".join(core + ([legal] if legal else []))
    if rng.random() < 0.5:
        nm = strip_acc(nm) if rng.random() < 0.5 else nm.upper()
    return nm, noise_addr(a, rng) if a and rng.random() < 0.5 else a


SYL = ["fa", "ye", "del", "ta", "e", "vo", "ri", "za", "ca", "lo", "gild", "drex", "brix", "ke", "kor", "o", "nyx", "ci",
       "ra", "ve", "be", "ly", "a", "wex", "or", "bi", "xy", "ny", "la", "vi", "py", "mo", "zen", "tri", "qua", "sol"]


def brand_name(rng) -> str:
    """an invented pseudo-word of 5-15 letters, like the generator's trading names ("fayedelta", "onyxcira")."""
    while True:
        w = "".join(rng.choice(SYL, size=int(rng.integers(2, 5))))
        if 5 <= len(w) <= 15:
            return w.capitalize() if rng.random() < 0.6 else (w.upper() if rng.random() < 0.5 else w)


def number_lookalike(name: str, addr: str, rng):
    """the same business shape at another house number on the S1's street (y=0)."""
    a = addr if isinstance(addr, str) else ""
    m = re.match(r"^\s*(\d+)", a)
    if not m:
        return None
    n = int(m.group(1))
    new = n + int(rng.choice([1, 2, 3, 4, 5, 7, 9, 11, 13, 21]))
    if new <= 0 or new == n:
        new = n + 7
    a2 = str(new) + a[m.end():]
    nm = noise_name(name, rng) if rng.random() < 0.6 else name
    return nm, noise_addr(a2, rng) if rng.random() < 0.5 else a2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", default="work/records/test.parquet")
    ap.add_argument("--country", default="France")
    ap.add_argument("--n-s1", type=int, default=40000)
    ap.add_argument("--neg-per-pos", type=float, default=1.0)
    ap.add_argument("--out", default="work/box_synth")
    ap.add_argument("--seed", type=int, default=26)
    ap.add_argument("--brand", type=float, default=0.08)
    ap.add_argument("--numlike", type=float, default=0.12)
    ap.add_argument("--otheraddr", type=float, default=0.5)
    ap.add_argument("--otherbiz", type=float, default=0.03)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    rec = pd.read_parquet(a.records, columns=["eid", "source", "country", "name", "address"])
    s1 = rec[(rec.source == 1) & (rec.country == a.country)].reset_index(drop=True)
    vocab = pd.Series([w for n in s1.name.astype(str) for w in split_legal(n)[0] if len(w) >= 4 and WORD.fullmatch(w)])
    vocab = vocab.value_counts()
    vocab = vocab[vocab >= 20].index.to_numpy()
    pick = s1.sample(min(a.n_s1, len(s1)), random_state=a.seed).reset_index(drop=True)

    def city_of(x):
        parts = [strip_acc(p).strip().lower() for p in str(x).split(",")]
        c = [p for p in parts if p and p not in DEPT and not re.search(r"\d", p)]
        return c[-1] if c else ""
    by_city = {}
    for x in s1.address.dropna().astype(str):
        by_city.setdefault(city_of(x), []).append(x)
    recs, pairs, eid = [], [], 9_000_000_000
    for _, row in pick.iterrows():
        nm, ad = str(row["name"]), row["address"]
        recs.append((eid, 2 if rng.random() < 0.5 else 3, a.country, noise_name(nm, rng), noise_addr(ad, rng, num_move=True)))
        pairs.append((row.eid, eid, 1)); eid += 1
        if rng.random() < a.brand and isinstance(ad, str) and re.match(r"^\s*\d", ad):
            recs.append((eid, 2 if rng.random() < 0.5 else 3, a.country, brand_name(rng), noise_addr(ad, rng) or ad))
            pairs.append((row.eid, eid, 1)); eid += 1
        if rng.random() < a.numlike:
            nl = number_lookalike(nm, ad, rng)
            if nl:
                recs.append((eid, 3 if rng.random() < 0.5 else 2, a.country, nl[0], nl[1]))
                pairs.append((row.eid, eid, 0)); eid += 1
        if rng.random() < a.otheraddr and isinstance(ad, str) and ad.strip():
            pool = by_city.get(city_of(ad), [])
            if len(pool) > 1:
                oa = pool[int(rng.integers(0, len(pool)))]
                if oa != ad:
                    lv = noise_name(nm, rng) if rng.random() < 0.5 else nm
                    recs.append((eid, 2 if rng.random() < 0.5 else 3, a.country, lv, noise_addr(oa, rng)))
                    pairs.append((row.eid, eid, 0)); eid += 1
        if rng.random() < a.otherbiz and isinstance(ad, str) and ad.strip():
            other = str(s1.name.iloc[int(rng.integers(0, len(s1)))])
            if other.lower() != nm.lower():
                recs.append((eid, 2 if rng.random() < 0.5 else 3, a.country, other, noise_addr(ad, rng) or ad))
                pairs.append((row.eid, eid, 0)); eid += 1
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
