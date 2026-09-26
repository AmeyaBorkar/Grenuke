"""Context feature groups ``ret``, ``src``, ``ctx`` (owner: Ameya; issue #12; plans/FINAL_PLAN.md section 4.4).

``compute(cands, s1_records)`` returns float32 columns row-aligned with ``cands`` (C4 candidates of one split).
The features stage (``ber.features.run``) joins them with the string groups. Definitions: ``FEATURES`` below.

Rivalry features are **log-counts, not rates**: a name shared by 16 S1 among France's 259k S1 is as ambiguous as one
shared by 16 among 1.3M US S1, while rates would make France look 3-4x more common than anything in train
(data review of 25 Sep).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc

FEATURES = {
    "ret__<view>_score": "retrieval similarity of the pair in that blocking view (NaN if the view missed it)",
    "ret__<view>_rank_s1": "rank of the record in the S1's list for that view (0 = best; 99 if absent)",
    "ret__<view>_rank_r": "rank of the S1 in the record's list for that view (0 = best; 99 if absent)",
    "ret__n_views": "number of blocking views and keys that retrieved the pair",
    "ret__gap_s1_best": "best tok score among the S1's candidates minus this pair's",
    "ret__gap_r_best": "best tok score among the record's candidate S1 minus this pair's",
    "ret__margin_r": "this pair's tok score minus the best score of any other S1 for the same record",
    "ctx__log_cands_s1": "log1p of the number of candidates of the S1",
    "ctx__log_cands_r": "log1p of the number of candidate S1 of the record",
    "ctx__log_s1_same_name": "log1p of the number of other S1 (same split and country) with the same name key",
    "ctx__log_s1_same_numstreet": "log1p of the number of other S1 with the same (house number, street word) key",
    "src__is_s3": "1 if the record comes from Source 3, 0 if from Source 2",
}


def _views(cands: pd.DataFrame) -> list[str]:
    return [c[len("score_"):] for c in cands.columns if c.startswith("score_")]


def s1_keys(s1_records: pd.DataFrame) -> pd.DataFrame:
    """Name key and (number, street) key per S1, from the blocking tokenizer (no dependency on the norm stage).

    ``s1_records``: eid, country, name, address.
    """
    import pyarrow as pa

    from ..block import indic, text

    n = len(s1_records)
    names = indic.transliterate_array(pa.array(s1_records["name"].astype(str).tolist()))
    addrs = pa.array(s1_records["address"].astype(str).tolist())
    nt = text.name_tokens(names)
    tok = pd.DataFrame({"row": nt.rows, "tok": nt.values.to_numpy(zero_copy_only=False)})
    tok = tok.drop_duplicates().sort_values(["row", "tok"], kind="stable")
    name_key = tok.groupby("row")["tok"].agg(" ".join).reindex(range(n), fill_value="").to_numpy()
    numstreet = numstreet_keys(addrs)
    country = s1_records["country"].astype(str).to_numpy()
    return pd.DataFrame({"eid": s1_records["eid"].to_numpy(), "name_key": country + "|" + name_key.astype(str),
                         "numstreet_key": np.where(numstreet != "", country + "|" + numstreet, "")})


# Words skipped between a house number and the street name: street types (US, India, France, canonical forms too),
# articles and house/plot markers. "32 Rue André Maginot" -> 32|andre, "PA, AVELLA CITY, 972 OLD RIDGE RD" -> 972|old,
# "Sno 32/2/1 Hno 1048, Gulabnagar" -> 1048|gulabnagar.
_SKIP = ("rue|r|avenue|ave|av|boulevard|bd|blvd|impasse|imp|allee|all|chemin|ch|route|rte|place|pl|quai|cours|faubourg|fg|"
         "de|du|des|la|le|les|l|d|st|saint|no|nr|n|nos|bis|ter|quater|street|road|rd|lane|ln|drive|dr|the|"
         "hno|sno|h|plot|flat|door|house|shop|ward|block|sector|floor|fl|unit|apt|suite|ste|survey|khasra|gat|gut")
NUMSTREET = r"(?:^|[^0-9])0*(?P<num>[0-9]+)[^a-z0-9]*(?P<word>[a-z]{2,})"  # applied after blanking _SKIP words


def numstreet_keys(addresses: pa.Array) -> np.ndarray:
    """(house number, street word) key per address: the first number followed by a street name, and that name's
    first significant word. Reordered components and French street types no longer change the key. "" if none."""
    from ..block import text

    folded = pc.replace_substring_regex(text.fold(addresses), r"([0-9])(st|nd|rd|th)\b", r"\1")
    folded = pc.replace_substring_regex(folded, r"\b(?:" + _SKIP + r")\b", " ")  # RE2 has no negative lookahead
    ex = pc.extract_regex(folded, NUMSTREET)
    num = pc.fill_null(ex.field("num"), "")
    word = pc.fill_null(ex.field("word"), "")
    sep, blank = pa.scalar("|", type=num.type), pa.scalar("", type=num.type)  # string or large_string input
    key = pc.binary_join_element_wise(num, word, sep)
    empty = pc.or_(pc.equal(num, blank), pc.equal(word, blank))
    return np.asarray(pc.if_else(empty, blank, key).to_numpy(zero_copy_only=False), dtype=object)


def _group_top2(group: np.ndarray, score: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per row: the best and second-best score of its group (second = 0 if none) and the group size."""
    order = np.lexsort((-score, group))
    g, s = group[order], score[order]
    start = np.ones(g.size, bool)
    start[1:] = g[1:] != g[:-1]
    idx = np.cumsum(start) - 1
    first = np.flatnonzero(start)
    size = np.diff(np.append(first, g.size))
    second = np.zeros(first.size, np.float32)
    has2 = size > 1
    second[has2] = s[first[has2] + 1]
    best_o, second_o, size_o = (np.empty(g.size, np.float32), np.empty(g.size, np.float32), np.empty(g.size, np.int64))
    best_o[order], second_o[order], size_o[order] = s[first][idx], second[idx], size[idx]
    return best_o, second_o, size_o


def _rival_counts(keys: pd.Series) -> np.ndarray:
    """Number of *other* records with the same non-empty key."""
    counts = keys.map(keys.value_counts()).to_numpy().astype(np.float32) - 1
    counts[(keys == "").to_numpy() | keys.str.endswith("|").to_numpy()] = 0
    return counts


def compute(cands: pd.DataFrame, s1_records: pd.DataFrame) -> pd.DataFrame:
    """Context features for C4 candidates of one split. ``s1_records``: that split's S1 rows (eid, country, name,
    address)."""
    from ..block import VIEW_BITS

    out: dict[str, np.ndarray] = {}
    for v in _views(cands):
        out[f"ret__{v}_score"] = cands[f"score_{v}"].to_numpy(np.float32)
        for side in ("s1", "r"):
            rank = cands[f"rank_{side}_{v}"].to_numpy()
            out[f"ret__{v}_rank_{side}"] = np.where(rank >= 0, rank, 99).astype(np.float32)
    views = cands["views"].to_numpy().astype(np.int64)
    out["ret__n_views"] = sum(((views & bit) > 0).astype(np.float32) for bit in VIEW_BITS.values())

    primary = "tok" if "score_tok" in cands.columns else _views(cands)[0]
    score = cands[f"score_{primary}"].fillna(0).to_numpy(np.float32)
    best_s1, _, n_s1 = _group_top2(cands["s1"].to_numpy(), score)
    best_r, second_r, n_r = _group_top2(cands["r"].to_numpy(), score)
    # best score of any *other* S1 for the record: the second best when this pair is the best
    other_best = np.where(score >= best_r, second_r, best_r)
    out["ret__gap_s1_best"] = best_s1 - score
    out["ret__gap_r_best"] = best_r - score
    out["ret__margin_r"] = (score - other_best).astype(np.float32)
    out["ctx__log_cands_s1"] = np.log1p(n_s1).astype(np.float32)
    out["ctx__log_cands_r"] = np.log1p(n_r).astype(np.float32)

    keys = s1_keys(s1_records)
    rivals = pd.DataFrame({"eid": keys["eid"], "name": _rival_counts(keys["name_key"]),
                           "numstreet": _rival_counts(keys["numstreet_key"])}).set_index("eid")
    out["ctx__log_s1_same_name"] = np.log1p(rivals["name"].reindex(cands["s1"]).fillna(0).to_numpy()).astype(np.float32)
    out["ctx__log_s1_same_numstreet"] = np.log1p(
        rivals["numstreet"].reindex(cands["s1"]).fillna(0).to_numpy()).astype(np.float32)
    out["src__is_s3"] = (cands["r"].to_numpy() // 1_000_000_000 == 3).astype(np.float32)
    return pd.DataFrame(out)
