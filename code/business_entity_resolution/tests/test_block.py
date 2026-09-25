"""Blocking v0: tokenizer, token keys, exact top-k search (vs brute force), union/trim and the stage end to end."""
import numpy as np
import pandas as pd
import pyarrow as pa
import pytest

from ber import pipeline
from ber.artifacts import read_table
from ber.block import VIEW_BITS, index, partitions, search, text, union_trim


def _rows(tok):
    out = {}
    for v, r in zip(tok.values.to_pylist(), tok.rows.tolist()):
        out.setdefault(r, []).append(v)
    return out


def test_tokenizer_folds_accents_scripts_legal_forms_and_numbers():
    names = pa.array(["Café Lumière SARL", "ACME Robotics, Inc.", "श्री Balaji Traders Pvt Ltd", "abcexports.com"])
    tok = _rows(text.name_tokens(names))
    assert tok[0] == ["cafe", "lumiere"]
    assert tok[1] == ["acme", "robotics"]
    assert tok[2] == ["balaji", "traders"]  # Devanagari dropped here (normalize stage transliterates)
    assert tok[3] == ["abcexports"]
    addrs = pa.array(["0054 RUE Negrier, Lille", "H.No 12-3-45, MG Road", "8444b Main Street", "<NULL>"])
    words = _rows(text.address_words(addrs))
    assert words[0] == ["r", "negrier", "lille"] and words[1] == ["mg", "rd"] and words[2] == ["main", "st"]
    assert 3 not in words  # '<NULL>' has no words
    nums = _rows(text.address_numbers(addrs))
    assert nums[0] == ["54"] and nums[1] == ["12", "3", "45"] and nums[2] == ["8444"]
    ordinals = pa.array(["D-587 1St Floor, 3rd Cross", "2 Nd Floor, 42nd Street"])
    assert _rows(text.address_words(ordinals)) == {0: ["cross"], 1: ["st"]}
    assert _rows(text.address_numbers(ordinals)) == {0: ["587", "1", "3"], 1: ["2", "42"]}


def test_name_concat_matches_domain_form():
    nt = text.name_tokens(pa.array(["ABC Exports", "abcexports.com", "Solo"]))
    cc = text.name_concat(nt, 3)
    assert cc.values.to_pylist() == ["abcexports"] and cc.rows.tolist() == [0]


def test_record_keys_share_compound_tokens_for_the_same_business():
    names = pa.array(["Sharma Enterprises", "SHARMA ENTERPRISES PVT LTD", "Verma Traders"])
    addrs = pa.array(["12 MG Road, Pune", "12, M.G. Road Pune", "7 Park Street"])
    ptr, keys = index.record_keys(names, addrs)
    k = [set(keys[ptr[i]:ptr[i + 1]].tolist()) for i in range(3)]
    shared = k[0] & k[1]
    assert any(x >> index.KIND_SHIFT == 1 for x in shared)  # (number, street word)
    assert any(x >> index.KIND_SHIFT == 3 for x in shared)  # (number, name token)
    assert any(x >> index.KIND_SHIFT == 2 for x in shared)  # name pair
    assert not (k[0] & k[2])


def _brute(q_sets, d_sets, w, k):
    qn = [np.sqrt(sum(w[t] for t in q)) for q in q_sets]
    dn = [np.sqrt(sum(w[t] for t in d)) for d in d_sets]
    out = []
    for i, q in enumerate(q_sets):
        sc = [(sum(w[t] for t in q & d) / (qn[i] * dn[j]), j) for j, d in enumerate(d_sets) if q & d]
        sc.sort(key=lambda x: (-x[0], x[1]))
        out.append(sc[:k])
    return out


def _csr(sets):
    ptr = np.zeros(len(sets) + 1, np.int64)
    ptr[1:] = np.cumsum([len(s) for s in sets])
    return ptr, np.array([t for s in sets for t in sorted(s)], np.int32)


def test_topk_matches_brute_force():
    rng = np.random.default_rng(0)
    V = 60
    w = rng.uniform(0.2, 3.0, V).astype(np.float32)
    q_sets = [set(rng.choice(V, rng.integers(1, 8), replace=False).tolist()) for _ in range(40)]
    d_sets = [set(rng.choice(V, rng.integers(1, 8), replace=False).tolist()) for _ in range(90)]
    qp, qc = _csr(q_sets)
    dp, dc = _csr(d_sets)
    post = index.build_postings(dp, dc, V)
    k = 5
    idx, sc = search.topk(qp, qc, index.row_norms(qp, qc, w), post, (dp, dc), index.row_norms(dp, dc, w), w, k,
                          seed_cap=10**9)
    ref = _brute(q_sets, d_sets, w, k)
    for i in range(len(q_sets)):
        got = [(float(s), int(j)) for s, j in zip(sc[i], idx[i]) if j >= 0]
        assert len(got) == len(ref[i])
        assert np.allclose([g[0] for g in got], [r[0] for r in ref[i]], atol=1e-5)
        assert set(j for _, j in got) >= {j for s, j in ref[i] if s > ref[i][-1][0] + 1e-6}  # ties may differ


def test_seed_cap_skips_common_tokens_only_for_seeding():
    q_sets, d_sets = [{0, 1}], [{0}, {0, 1}, {0}]
    w = np.array([0.1, 2.0], np.float32)
    qp, qc = _csr(q_sets)
    dp, dc = _csr(d_sets)
    post = index.build_postings(dp, dc, 2)
    idx, sc = search.topk(qp, qc, index.row_norms(qp, qc, w), post, (dp, dc), index.row_norms(dp, dc, w), w, 3, seed_cap=2)
    assert idx[0].tolist() == [1, -1, -1]  # token 0 is in 3 docs > seed_cap, so only doc 1 (shares token 1) is seeded
    assert np.isclose(sc[0, 0], 1.0)  # ...but the verify step adds token 0 back: doc 1 == query


def test_union_trim_keeps_either_direction_and_metadata():
    qa = np.array([0, 1])
    a_idx = np.array([[0, 1, 2], [2, -1, -1]], np.int32)
    a_sc = np.array([[0.9, 0.5, 0.1], [0.8, 0, 0]], np.float32)
    b_idx = np.array([[0], [1], [0]], np.int32)  # r0 -> s1 0, r1 -> s1 1, r2 -> s1 0
    b_sc = np.array([[0.9], [0.4], [0.1]], np.float32)
    out = union_trim(qa, a_idx, a_sc, b_idx, b_sc, n_r=3, s1_kept=np.array([True, True]), trim_s1=2, trim_r=1)
    got = {(int(a), int(b)): (int(c), int(d)) for a, b, c, d in
           out[["s1_local", "r_local", "rank_s1", "rank_r"]].to_numpy()}
    # (0,2) is rank 2 for s1 0 (trimmed by trim_s1=2) but s1 0 is r2's best -> kept via the R direction
    assert got == {(0, 0): (0, 0), (0, 1): (1, -1), (0, 2): (2, 0), (1, 2): (0, -1), (1, 1): (-1, 0)}


def test_partitions_open_set_and_empty_labels():
    parts = dict(partitions(np.array(["US", "India", "", "France", "US"], dtype=object)))
    assert set(parts) == {"US", "India", "France"}
    assert parts["US"].tolist() == [0, 2, 4] and parts["France"].tolist() == [2, 3]


@pytest.fixture
def env(tmp_path, monkeypatch):
    from test_pipeline import _write

    data = tmp_path / "dataset"
    for split in ("train", "test"):
        _write(data / split / f"{split}_source1.tsv", [
            ("S1-1", "Acme Robotics Inc", "500 Market St, San Jose, CA", "US"),
            ("S1-2", "Sri Balaji Traders", "12 MG Road, Pune, MH", "India"),
            ("S1-3", "Balaji Traders", "12 MG Road, Pune, MH", "US"),
        ])
        _write(data / split / f"{split}_source2.tsv", [
            ("S2-5", "ACME ROBOTICS", "0500 MARKET STREET SAN JOSE", "US"),
            ("S2-6", "Balaji Traders Pvt Ltd", "12, M.G. Road, Pune", "India"),
        ])
        _write(data / split / f"{split}_source3.tsv", [("S3-7", "Zeta Foods", "9 Elm Rd, Austin", "US")])
    _write(data / "train" / "train_ground_truth.tsv", [("S1-1", "S2-5"), ("S1-2", "S2-6"), ("S1-3", "")],
           header="source1_entity_id\tmatched_entity_ids\n")
    monkeypatch.setenv("BER_DATA_DIR", str(data))
    monkeypatch.setenv("BER_WORK_DIR", str(tmp_path / "work"))
    monkeypatch.setenv("BER_OUTPUT_DIR", str(tmp_path / "output"))
    for split in ("train", "test"):
        assert pipeline.main(["--stage", "records", "--split", split]) == 0
    return tmp_path


def test_block_stage_end_to_end(env):
    assert pipeline.main(["--stage", "block", "--split", "train", "--tag", "t-block-v0"]) == 0
    c = read_table("candidates", "t-block-v0", "train")
    assert list(c.columns) == ["s1", "r", "views", "score_name_short", "rank_s1_name_short", "rank_r_name_short",
                               "score_tok", "rank_s1_tok", "rank_r_tok"]  # views in bit order
    pairs = set(map(tuple, c[["s1", "r"]].to_numpy().tolist()))
    assert (1_000_000_001, 2_000_000_005) in pairs and (1_000_000_002, 2_000_000_006) in pairs
    assert (1_000_000_003, 2_000_000_006) not in pairs  # S1-3 is US, S2-6 is India: never across countries
    assert not c.duplicated(["s1", "r"]).any()
    assert ((c["views"] & VIEW_BITS["tok"]) > 0).all()
    # S2-6 has a 3-token address ("12, M.G. Road, Pune"), so the name-only view also retrieves it
    row = c[(c["s1"] == 1_000_000_002) & (c["r"] == 2_000_000_006)].iloc[0]
    assert int(row["views"]) & VIEW_BITS["name_short"] and int(row["rank_r_name_short"]) == 0
    assert (c.loc[c["s1"] == 1_000_000_001, "rank_r_name_short"] == -1).all()  # US partition: no short records


def test_merge_views_or_bits_and_fills_absent_views():
    a = pd.DataFrame({"s1": [1, 1], "r": [10, 11], "score_tok": [0.9, 0.5], "rank_s1_tok": [0, 1], "rank_r_tok": [0, -1]})
    b = pd.DataFrame({"s1": [1, 2], "r": [11, 12], "score_name_short": [0.7, 0.6], "rank_s1_name_short": [0, 0],
                      "rank_r_name_short": [0, 0]})
    from ber.block import merge_views
    m = merge_views({"tok": a, "name_short": b}).sort_values(["s1", "r"]).reset_index(drop=True)
    assert m["views"].tolist() == [64, 68, 4]
    assert m["rank_s1_tok"].tolist() == [0, 1, -1] and np.isnan(m.loc[2, "score_tok"])


def test_indic_transliteration_and_skeleton_meet_latin_names():
    from ber.block import indic
    assert indic.transliterate("मार्केटिंग") == "maarketing" and indic.transliterate("राम") == "raam"
    assert indic.transliterate("லக்ஷ்மி") == "lakshmi"  # Tamil uses the same offsets
    sk = indic.skeleton(pa.array(["marketing", "maarketing", "builders", "bildars", "software", "sophtaveyar"]))
    assert sk.to_pylist() == ["mrktng", "mrktng", "bldrs", "bldrs", "sftvr", "sftvr"]
    ptr, keys = index.record_keys(pa.array(["Star Marketing Pvt Ltd", "स्टार मार्केटिंग प्राइवेट लिमिटेड"]), pa.array(["", ""]))
    shared = set(keys[ptr[0]:ptr[1]].tolist()) & set(keys[ptr[1]:ptr[2]].tolist())
    assert shared  # the skeletons (and here even the tokens "star"/"staar" skeletons) connect the two scripts


def test_indic_name_tokens_drop_legal_forms_and_apply_the_dictionary():
    from ber.block import indic
    names = pa.array(["गोल्डन इंफ्रा प्राइवेट लिमिटेड", "Golden Infra Pvt Ltd", "Shri Ram Traders"])
    tok, is_indic = indic.name_tokens(names, {"goldan": "golden", "inphraa": "infra", "ram": "never"})
    assert is_indic.tolist() == [True, False, False]
    # Indic legal forms go, the dictionary maps Indic-script tokens only (the Latin "ram" is untouched)
    assert tok.values.to_pylist() == ["golden", "infra", "golden", "infra", "ram", "traders"]
    assert tok.rows.tolist() == [0, 0, 1, 1, 2, 2]
    ptr, keys = index.record_keys(names[:2], pa.array(["", ""]), name_map={"goldan": "golden", "inphraa": "infra"})
    assert set(keys[ptr[0]:ptr[1]].tolist()) == set(keys[ptr[1]:ptr[2]].tolist())
