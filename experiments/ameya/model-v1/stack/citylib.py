"""City vocabulary and per-record city ids (data-driven, per country, from S1 addresses)."""
from __future__ import annotations
import re
from collections import Counter, defaultdict
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
from ber.block.text import fold
from ber.paths import records_path

TOKMAP = {"st": "saint", "ste": "sainte", "ft": "fort", "mt": "mount"}
_CLEAN = re.compile(r"[^a-z0-9]+")


def norm_comp(c: str) -> str:
    """folded comma component -> normalized key (punctuation -> space, st/ste/ft/mt expanded)."""
    w = _CLEAN.sub(" ", c).split()
    if len(w) >= 2 and w[0] in TOKMAP:  # "st louis" -> "saint louis"; a lone "mt" (Montana) stays
        w[0] = TOKMAP[w[0]]
    return " ".join(w)


def components(addr: str) -> list[str]:
    """normalized comma components without digits (candidate city/region names)."""
    out = []
    for c in (addr or "").split(","):
        if any(ch.isdigit() for ch in c):
            continue
        k = norm_comp(c)
        if k and k not in ("null", "none", "na", "nan"):
            out.append(k)
    return out


def iter_records(split: str, columns=("eid", "source", "country", "address"), sources=None, eids=None):
    f = pq.ParquetFile(records_path(split))
    for g in range(f.num_row_groups):
        t = f.read_row_group(g, columns=list(columns))
        if sources is not None:
            t = t.filter(pc.is_in(t["source"], value_set=pa.array(list(sources), pa.int8())))
        if eids is not None:
            t = t.filter(pc.is_in(t["eid"], value_set=pa.array(eids)))
        if t.num_rows:
            yield t


def s1_component_counts(split: str, countries=None):
    """per country: Counter(component) over S1 addresses, and co-occurrence pairs Counter((a, b))."""
    cnt = defaultdict(Counter)
    co = defaultdict(Counter)
    n_s1 = Counter()
    for t in iter_records(split, sources=[1]):
        if countries is not None:
            t = t.filter(pc.is_in(t["country"], value_set=pa.array(sorted(countries), t["country"].type)))
        cty = t["country"].to_numpy(zero_copy_only=False)
        addr = fold(t["address"].combine_chunks()).to_numpy(zero_copy_only=False)
        for c, a in zip(cty, addr):
            comps = set(components(a))
            n_s1[c] += 1
            cnt[c].update(comps)
            if len(comps) <= 6:
                for x in comps:
                    for y in comps:
                        if x != y:
                            co[c][(x, y)] += 1
    return cnt, co, n_s1


# Hand-written lexicon (documented in REPORT.md): US state names (records spell them out; S1 uses abbreviations) and
# French sub-areas that belong to a city (communes associees): these are never "another city".
US_STATES = set("""alabama alaska arizona arkansas california colorado connecticut delaware florida georgia hawaii idaho
illinois indiana iowa kansas kentucky louisiana maine maryland massachusetts michigan minnesota mississippi missouri
montana nebraska nevada ohio oklahoma oregon pennsylvania tennessee texas utah vermont virginia wisconsin wyoming""".split()) | {
    "new hampshire", "new jersey", "new mexico", "new york", "north carolina", "north dakota", "rhode island",
    "south carolina", "south dakota", "west virginia", "washington", "district of columbia"}
US_ABBR = set("""al ak az ar ca co ct de fl ga hi id il in ia ks ky la me md ma mi mn ms mo mt ne nv nh nj nm ny nc nd oh
ok or pa ri sc sd tn tx ut vt va wa wv wi wy""".split())
ALIAS = {"lomme": "lille", "hellemmes": "lille", "hellemmes lille": "lille", "lille hellemmes": "lille",
         "lille lomme": "lille", "lomme lille": "lille", "le clion": "pornic", "le clion sur mer": "pornic"}


def canon(k: str) -> str:
    return ALIAS.get(k, k)


def build_vocab(cnt, co, n_s1, min_count=20, region_share=0.002, parent_frac=0.9, alone_frac=0.5, alone=None):
    """per country: (cities set, regions set). region: frequent and the more frequent partner in >= parent_frac of
    its co-occurrences; city: count >= min_count, not a region, not a US state name, and (if ``alone`` is given)
    the only non-region component in >= alone_frac of its S1 addresses."""
    out = {}
    for c in cnt:
        C = cnt[c]
        big = {k for k, v in C.items() if v >= min_count}
        par, tot = {}, {}
        for (a, b), v in co[c].items():
            if a in big and b in big:
                tot[a] = tot.get(a, 0) + v
                if C[a] > C[b]:
                    par[a] = par.get(a, 0) + v
        regions = {k for k in big if C[k] >= region_share * n_s1[c] and tot.get(k, 0) > 0
                   and par.get(k, 0) / tot[k] >= parent_frac}
        excl = US_STATES | (US_ABBR if c == "US" else set())
        cities = {canon(k) for k in big if k not in regions and k not in excl and canon(k) not in regions}
        if alone is not None:
            A = alone[c]
            cities = {k for k in cities if A.get(k, 0) >= alone_frac * C.get(k, 1)
                      or any(A.get(a, 0) >= alone_frac * C.get(a, 1) for a, v in ALIAS.items() if v == k)}
        out[c] = (cities, regions)
    return out


def alone_counts(split, regions_by_country):
    """per country: Counter(component) of S1 addresses whose only non-region component it is."""
    res = defaultdict(Counter)
    for t in iter_records(split, sources=[1]):
        cty = t["country"].to_numpy(zero_copy_only=False)
        addr = fold(t["address"].combine_chunks()).to_numpy(zero_copy_only=False)
        for c, a in zip(cty, addr):
            if c not in regions_by_country:
                continue
            reg = regions_by_country[c]
            comps = {k for k in components(a) if k not in reg and k not in US_STATES}
            if len(comps) == 1:
                res[c][canon(next(iter(comps)))] += 1
    return res


def city_table(split: str, eids: np.ndarray, vocab: dict, city_id: dict) -> pd.DataFrame:
    """eid -> up to 3 city ids (sorted, -1 padded) named by the record's address in its country's vocabulary."""
    rows_e, rows_c = [], []
    eids = np.unique(np.asarray(eids, np.int64))
    for t in iter_records(split, columns=("eid", "country", "address"), eids=eids):
        e = t["eid"].to_numpy()
        cty = t["country"].to_numpy(zero_copy_only=False)
        addr = fold(t["address"].combine_chunks()).to_numpy(zero_copy_only=False)
        out = np.full((e.size, 3), -1, np.int32)
        for i, (c, a) in enumerate(zip(cty, addr)):
            voc = vocab.get(c)
            if voc is None:
                continue
            ids = sorted({city_id[(c, canon(k))] for k in components(a) if canon(k) in voc[0]})[:3]
            out[i, :len(ids)] = ids
        rows_e.append(e)
        rows_c.append(out)
    e = np.concatenate(rows_e)
    c = np.concatenate(rows_c)
    return pd.DataFrame({"eid": e, "c1": c[:, 0], "c2": c[:, 1], "c3": c[:, 2]})


def make_city_id(vocab: dict) -> dict:
    ids = {}
    for c in sorted(vocab):
        for k in sorted(vocab[c][0]):
            ids[(c, k)] = len(ids)
    return ids


def mismatch(cs: np.ndarray, cr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(both name a city, the city sets are disjoint) for aligned (n, 3) city-id arrays."""
    both = (cs[:, 0] >= 0) & (cr[:, 0] >= 0)
    ov = np.zeros(len(cs), bool)
    for i in range(3):
        for j in range(3):
            ov |= (cs[:, i] >= 0) & (cs[:, i] == cr[:, j])
    return both, both & ~ov
