"""Build synth_fr3.py from synth_fr2.py (raw-string patches)."""
import sys

D = "C:/Users/ameya/Documents/GrenukeAmazon/.claude/worktrees/final-stack/experiments/ameya/model-v1/"
s = open(D + "synth_fr2.py", encoding="utf-8").read()


def rep(old, new, count=1):
    global s
    assert s.count(old) == count, f"pattern not found {count}x: {old[:70]!r} (found {s.count(old)})"
    s = s.replace(old, new)


rep('"""synth_fr2.py:', r'''"""synth_fr3.py: synth_fr2.py re-weighted to the real French operation mix measured by the France-diff agent
(agents/fdiff/synth_vs_real.txt, 27 Sep 17:20): true copies are mostly legal-form drops/changes and word reorders
(22.6% of real French copies), with whole-word garbles, -1/-2 house-number moves (the NUM operation) and few list
appends, typos, acronyms or brands; about 30% of real French non-matches are the same name at another address, and
only +d house-number nudges are look-alikes; 32% of real addresses name the department. Defaults follow those rates.

synth_fr2.py:''')

rep('    ops = rng.choice(["case", "acc", "legal", "app", "a", "acr", "typo"], size=rng.integers(1, 3), replace=False)\n',
    r'''    OPS = ["legal", "case", "acc", "order", "garble", "app", "a", "acr", "typo"]
    OPW = np.array([0.45, 0.13, 0.12, 0.12, 0.06, 0.03, 0.03, 0.03, 0.03])
    ops = rng.choice(OPS, size=rng.integers(1, 3), replace=False, p=OPW / OPW.sum())
    legal_first = False
''')

rep('        elif op == "typo":\n', r'''        elif op == "order":
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
''')

rep('        legal = "" if rng.random() < 0.4 else rng.choice(LEGAL_FMT.get(up, [legal]))\n', r'''        r = rng.random()
        legal = "" if r < 0.4 else (f"[{up}]" if r < 0.47 else (f"({up})" if r < 0.52 else rng.choice(LEGAL_FMT.get(up, [legal]))))
''')

rep('    out = " ".join(core + ([legal] if legal else []))\n',
    '    out = " ".join((([legal] if legal else []) + core) if legal_first else (core + ([legal] if legal else [])))\n')

rep('def noise_addr(addr: str, rng) -> str:\n', r'''DEPT = {"hauts-de-france": "Nord", "nouvelle-aquitaine": "Gironde", "pays de la loire": "Loire-Atlantique"}
PDC = {"calais", "boulogne-sur-mer", "arras", "lens", "bethune", "saint-omer"}


def noise_addr(addr: str, rng, num_move: bool = False) -> str:
''')

rep(r'''    if rng.random() < 0.15:
        first = re.sub(r"^(\d)", r"No \1", first)
''', r'''    if num_move and rng.random() < 0.08:
        first = re.sub(r"^(\d+)", lambda m: str(max(1, int(m.group(1)) - int(rng.integers(1, 3)))), first)
    r = rng.random()
    if r < 0.12:
        first = re.sub(r"^(\d)", lambda m: str(rng.choice(["No ", "N ", "# ", "N° "])) + m.group(1), first)
    elif r < 0.15:
        first = re.sub(r"^(\d+)", lambda m: m.group(1).zfill(4), first)
    elif r < 0.17:
        first = re.sub(r"^(\d+)", lambda m: "(" + m.group(1) + ")", first)
''')

rep(r'''    if len(parts) >= 2 and rng.random() < 0.3:
        parts = parts[1:] + parts[:1]
''', r'''    if rng.random() < 0.5:
        low = [strip_acc(p).lower() for p in parts]
        city = next((p for p in low[1:] if p not in DEPT and not re.search(r"\d", p)), "")
        for k, p in enumerate(low):
            if p in DEPT:
                parts[k] = "Pas-de-Calais" if city in PDC else DEPT[p]
    if len(parts) >= 2 and rng.random() < 0.15:
        parts = parts[1:] + parts[:1]
''')

rep(r'        a = re.sub(r"^(\d+)", lambda m: str(int(m.group(1)) + int(rng.integers(1, 11))), a)',
    r'        a = re.sub(r"^(\d+)", lambda m: str(int(m.group(1)) + int(rng.choice([1, 2, 3, 4, 5, 7, 9, 11, 13, 21]))), a)')

rep('    new = n + int(rng.choice([-3, -2, -1, 1, 2, 3])) if rng.random() < 0.5 else int(rng.integers(1, 400))\n',
    '    new = n + int(rng.choice([1, 2, 3, 4, 5, 7, 9, 11, 13, 21]))\n')

rep('    ap.add_argument("--neg-per-pos", type=float, default=1.5)', '    ap.add_argument("--neg-per-pos", type=float, default=1.0)')
rep('    ap.add_argument("--brand", type=float, default=0.25)', '    ap.add_argument("--brand", type=float, default=0.08)')
rep('    ap.add_argument("--numlike", type=float, default=0.3)',
    '    ap.add_argument("--numlike", type=float, default=0.12)\n    ap.add_argument("--otheraddr", type=float, default=0.5)')
rep('    ap.add_argument("--otherbiz", type=float, default=0.2)', '    ap.add_argument("--otherbiz", type=float, default=0.03)')

rep('        recs.append((eid, 2, a.country, noise_name(nm, rng), noise_addr(ad, rng)))\n',
    '        recs.append((eid, 2 if rng.random() < 0.5 else 3, a.country, noise_name(nm, rng), noise_addr(ad, rng, num_move=True)))\n')

rep('        if rng.random() < a.otherbiz and isinstance(ad, str) and ad.strip():\n', r'''        if rng.random() < a.otheraddr and isinstance(ad, str) and ad.strip():
            pool = by_city.get(city_of(ad), [])
            if len(pool) > 1:
                oa = pool[int(rng.integers(0, len(pool)))]
                if oa != ad:
                    lv = noise_name(nm, rng) if rng.random() < 0.5 else nm
                    recs.append((eid, 2 if rng.random() < 0.5 else 3, a.country, lv, noise_addr(oa, rng)))
                    pairs.append((row.eid, eid, 0)); eid += 1
        if rng.random() < a.otherbiz and isinstance(ad, str) and ad.strip():
''')

rep("    pick = s1.sample(min(a.n_s1, len(s1)), random_state=a.seed).reset_index(drop=True)\n",
    r'''    pick = s1.sample(min(a.n_s1, len(s1)), random_state=a.seed).reset_index(drop=True)

    def city_of(x):
        parts = [strip_acc(p).strip().lower() for p in str(x).split(",")]
        c = [p for p in parts if p and p not in DEPT and not re.search(r"\d", p)]
        return c[-1] if c else ""
    by_city = {}
    for x in s1.address.dropna().astype(str):
        by_city.setdefault(city_of(x), []).append(x)
''')

open(D + "synth_fr3.py", "w", encoding="utf-8", newline="\n").write(s)
print("written synth_fr3.py")
