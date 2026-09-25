"""Quick data checks for the points where Plan A (ameya) and Plan B (sachi) disagree.

Read-only. Uses the local parquet cache. Crude normalisation on purpose (ASCII fold + lowercase + alnum tokens):
the goal is to test the direction and rough size of each claim, not to build a pipeline.
"""
import re
import time
import unicodedata

import numpy as np
import pandas as pd

from nn_lib import DC  # parquet cache written by make_cache.py
T0 = time.time()
RNG = np.random.default_rng(0)


def log(*a):
    print(f"[{time.time() - T0:6.1f}s]", *a, flush=True)


def rd(name, cols=None):
    return pd.read_parquet(f"{DC}/{name}.parquet", columns=cols)


_TOK = re.compile(r"[a-z0-9]+")
_NUM = re.compile(r"\d+")
_INDIC = re.compile(r"[\u0900-\u0DFF]")
_DOMAIN = re.compile(r"\.(com|in|net|org|co|fr|biz|info)\b|^#", re.I)
LEGAL = set("inc llc ltd pvt private limited corp corporation co company lp llp pllc pc plc the".split())
NULLS = {"null"}


def fold(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def toks(s):
    return _TOK.findall(fold(s))


def core_tokens(s):
    return [t for t in toks(s) if t not in LEGAL]


def addr_tokens(s):
    return [t for t in toks(s) if t not in NULLS]


def nums(s):
    return [n.lstrip("0") or "0" for n in _NUM.findall(s)]


def words(tok_list):
    return {t for t in tok_list if not t.isdigit() and len(t) > 1}


def jac(a, b):
    if not a and not b:
        return np.nan
    return len(a & b) / len(a | b)


# ---------------------------------------------------------------- 1. distractor density, train vs test
out = []
for split in ("train", "test"):
    cnt = {s: rd(f"{split}_s{s}", ["country"])["country"].value_counts() for s in (1, 2, 3)}
    d = pd.DataFrame(cnt).fillna(0).astype(int)
    d.loc["ALL"] = d.sum()
    d["R_per_S1"] = ((d[2] + d[3]) / d[1]).round(3)
    d.insert(0, "split", split)
    out.append(d)
log("1. records and R per S1 by country\n" + pd.concat(out).to_string())

# ---------------------------------------------------------------- 2. S1 name / address collisions (sachi #6-#8)
s1 = rd("train_s1")
s1["core"] = [" ".join(core_tokens(x)) for x in s1.business_name]
s1["addr"] = [" ".join(addr_tokens(x)) for x in s1.business_address]
log("2. S1 normalised")
for c, g in s1.groupby("country"):
    n = len(g)
    core_dup = g.groupby("core")["core"].transform("size") >= 2
    ga = g[g.addr != ""]
    addr_sz = ga.groupby("addr")["addr"].transform("size")
    both = ga[ga.core != ""].groupby(["core", "addr"])["core"].transform("size") >= 2
    log(f"   {c}: S1 sharing exact core name with another S1 = {core_dup.mean():.1%}; "
        f"sharing exact normalised address = {(addr_sz >= 2).sum() / n:.2%} (max group {addr_sz.max()}); "
        f"sharing both = {both.sum()}")

# ---------------------------------------------------------------- 3. positives: difficulty, numbers, empty/short R addresses
gt = rd("train_gt")
gt = gt[gt.matched_entity_ids != ""]
pairs = gt.assign(r=gt.matched_entity_ids.str.split(",")).explode("r")[["source1_entity_id", "r"]]
pairs = pairs[pairs.r != ""]
log(f"3. true pairs = {len(pairs):,}")

R = pd.concat([rd("train_s2").assign(src=2), rd("train_s3").assign(src=3)], ignore_index=True)
R["orphan"] = ~R.entity_id.isin(pairs.r)
log("   orphan share (R matching no S1) by source x country\n"
    + R.groupby(["src", "country"])["orphan"].mean().round(3).to_string())

s1_idx = pd.Series(np.arange(len(s1)), index=s1.entity_id)
r_idx = pd.Series(np.arange(len(R)), index=R.entity_id)

ps = pairs.sample(200_000, random_state=0)
ia = s1_idx.loc[ps.source1_entity_id].to_numpy()
ib = r_idx.loc[ps.r].to_numpy()
A = s1.iloc[ia].reset_index(drop=True)
B = R.iloc[ib].reset_index(drop=True)


def pair_stats(A, B):
    rows = []
    for an, aa, bn, ba in zip(A.business_name, A.business_address, B.business_name, B.business_address):
        at, bt = set(core_tokens(an)), set(core_tokens(bn))
        aat, bat = addr_tokens(aa), addr_tokens(ba)
        anum, bnum = nums(fold(aa)), nums(fold(ba))
        aw, bw = words(aat), words(bat)
        rows.append((
            jac(at, bt),
            bool(_INDIC.search(bn)),
            bool(_DOMAIN.search(bn)),
            len(bat) == 0,
            len(bat),
            len(set(anum) & set(bnum)),
            len(aw & bw),
            (anum[0] == bnum[0]) if (anum and bnum) else np.nan,
            (set(anum) == set(bnum)) if (anum and bnum) else np.nan,
            (len(set(anum) & set(bnum)) > 0) if (anum and bnum) else np.nan,
            " ".join(aat) == " ".join(bat),
            jac(aw, bw),
            sorted(bt - at),
        ))
    return pd.DataFrame(rows, columns=["name_jac", "indic", "domain", "r_addr_empty", "r_addr_ntok", "shared_num",
                                       "shared_words", "num1_eq", "numset_eq", "num_overlap", "addr_exact",
                                       "addr_word_jac", "extra_r_tokens"])


P = pair_stats(A, B)
P["country"] = A.country.values
P["weak_name"] = (P.name_jac < 0.2) | P.indic | P.domain
P["weak_addr"] = P.r_addr_empty | ((P.shared_num == 0) & (P.shared_words < 2))
P["short_addr"] = P.r_addr_ntok <= 3
log("   positives (200k sample):")
for c, g in [("ALL", P)] + list(P.groupby("country")):
    log(f"   {c:6s} weak name {g.weak_name.mean():.1%} | weak addr {g.weak_addr.mean():.1%} "
        f"| both {(g.weak_name & g.weak_addr).mean():.2%} | R addr empty {g.r_addr_empty.mean():.1%} "
        f"| R addr <=3 tokens {g.short_addr.mean():.1%} | weak addr but >3 tokens {(g.weak_addr & ~g.short_addr).mean():.2%} "
        f"| weak addr & weak name & >3 tok {(g.weak_addr & g.weak_name & ~g.short_addr).mean():.2%}")
    log(f"          numbers (both sides have one): first number equal {g.num1_eq.mean():.1%}, "
        f"number sets equal {g.numset_eq.mean():.1%}, any overlap {g.num_overlap.mean():.1%} "
        f"| exact normalised address {g.addr_exact.mean():.1%} | Indic-script R name {g.indic.mean():.1%}")

# postcodes (sachi #11): 6-digit runs in India addresses, 5-digit trailing number in US addresses
smp = pd.concat([s1.sample(100_000, random_state=1)[["business_address", "country"]],
                 R.sample(200_000, random_state=1)[["business_address", "country"]]])
six = smp.business_address.str.contains(r"(?<!\d)\d{6}(?!\d)", regex=True)
five_last = smp.business_address.str.contains(r"\d.*\D(?<!\d)\d{5}(?!\d)\D*$", regex=True)
log(f"   postcode-like: India addresses with a 6-digit run {six[smp.country == 'India'].mean():.2%}; "
    f"US addresses ending in a 5-digit run after another number {five_last[smp.country == 'US'].mean():.2%}")

# ---------------------------------------------------------------- 4. orphans vs S1 names (sachi #14)
orph = R[R.orphan]
oc = pd.Series([" ".join(core_tokens(x)) for x in orph.business_name], index=orph.index)
s1_keys = set(zip(s1.country, s1.core))
s1_keys_addr = set(zip(s1.country, s1.core, s1.addr))
name_hit = np.fromiter(((c, k) in s1_keys for c, k in zip(orph.country, oc)), bool, len(orph))
oa = [" ".join(addr_tokens(x)) for x in orph.business_address[name_hit]]
both_hit = np.fromiter(((c, k, a) in s1_keys_addr for c, k, a in zip(orph.country[name_hit], oc[name_hit], oa)), bool)
log(f"4. orphans: {len(orph):,}; exact core-name match to some S1 = {name_hit.mean():.1%}; "
    f"of those also exact normalised address = {both_hit.mean():.2%}")

# ---------------------------------------------------------------- 5. orphan look-alikes: nearest S1 via rare-token retrieval
# index S1 name+address tokens per country, keep tokens with df <= 300, score = sum idf of shared tokens
s1_sets = [set(core_tokens(n)) | set(addr_tokens(a)) for n, a in zip(s1.business_name, s1.business_address)]
lens = np.fromiter((len(x) for x in s1_sets), np.int64, len(s1_sets))
flat_i = np.repeat(np.arange(len(s1)), lens)
flat_k = pd.Series([t for x in s1_sets for t in x])
flat_k = s1.country.to_numpy()[flat_i] + "|" + flat_k.to_numpy(dtype=object)
codes, uniq = pd.factorize(flat_k)
df_tok = np.bincount(codes)
n_by_country = s1.country.value_counts().to_dict()
keep = df_tok[codes] <= 300
idx_df = pd.DataFrame({"code": codes[keep], "s1i": flat_i[keep]})
uniq_index = pd.Index(uniq)
country_of_code = np.array([u.split("|", 1)[0] for u in uniq], dtype=object)
idf = np.log(np.array([n_by_country[c] for c in country_of_code]) / df_tok)
log(f"5. token index: {len(flat_k):,} postings, {keep.sum():,} rare")

q = pd.concat([R[R.orphan].sample(20_000, random_state=2).assign(kind="orphan"),
               R[~R.orphan].sample(20_000, random_state=2).assign(kind="positive")], ignore_index=True)
q_sets = [set(core_tokens(n)) | set(addr_tokens(a)) for n, a in zip(q.business_name, q.business_address)]
ql = np.fromiter((len(x) for x in q_sets), np.int64, len(q_sets))
q_i = np.repeat(np.arange(len(q)), ql)
q_k = q.country.to_numpy()[q_i] + "|" + pd.Series([t for x in q_sets for t in x]).to_numpy(dtype=object)
q_code = uniq_index.get_indexer(q_k)
ok = (q_code >= 0)
ok[ok] = df_tok[q_code[ok]] <= 300
qdf = pd.DataFrame({"qi": q_i[ok], "code": q_code[ok]})
j = qdf.merge(idx_df, on="code")
j["w"] = idf[j.code.to_numpy()]
sc = j.groupby(["qi", "s1i"], sort=False)["w"].sum().reset_index().sort_values(["qi", "w"], ascending=[True, False])
top = sc.groupby("qi").head(2)
top["rank"] = top.groupby("qi").cumcount()
t1 = top[top["rank"] == 0].set_index("qi")
t2 = top[top["rank"] == 1].set_index("qi")
q["top1"] = t1.s1i.reindex(range(len(q))).to_numpy()
q["w1"] = t1.w.reindex(range(len(q))).to_numpy()
q["w2"] = t2.w.reindex(range(len(q))).fillna(0).to_numpy()
log(f"   retrieved a top-1 S1 for {q.top1.notna().mean():.1%} of queries")

# sanity for the proxy: is the true owner the top-1 for positives?
owner = pairs.set_index("r").source1_entity_id
posq = q[q.kind == "positive"]
own_i = s1_idx.loc[owner.loc[posq.entity_id]].to_numpy()
log(f"   proxy check: top-1 is the true owner for {(posq.top1.to_numpy() == own_i).mean():.1%} of positives")

has = q.top1.notna()
qq = q[has].reset_index(drop=True)
S = pair_stats(s1.iloc[qq.top1.astype(int)].reset_index(drop=True), qq)
S["kind"] = qq.kind.values
S["ratio21"] = (qq.w2 / qq.w1).values
S["lookalike"] = (S.name_jac >= 0.5) & (S.addr_word_jac >= 0.5)
S["n_extra"] = S.extra_r_tokens.str.len()
for k, g in S.groupby("kind"):
    la = g[g.lookalike]
    log(f"   {k:8s}: nearest S1 is a look-alike (name Jaccard >= .5 and address-word Jaccard >= .5) for {g.lookalike.mean():.1%}; "
        f"among those: first number equal {la.num1_eq.mean():.1%}, R name has >=1 extra token {(la.n_extra >= 1).mean():.1%}, "
        f"name Jaccard == 1 {(la.name_jac == 1).mean():.1%}; median 2nd/1st score ratio {g.ratio21.median():.2f} "
        f"(share with a close rival S1, ratio >= .8: {(g.ratio21 >= 0.8).mean():.1%})")
for k, g in S[S.lookalike].groupby("kind"):
    ex = pd.Series([t for x in g.extra_r_tokens for t in x if not t.isdigit()]).value_counts().head(25)
    log(f"   most common extra R-name tokens vs nearest S1 ({k}, look-alikes): " + ", ".join(f"{t}:{n}" for t, n in ex.items()))
log("done")
