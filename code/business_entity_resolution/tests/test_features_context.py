"""Context feature groups (ber.features.context): retrieval metadata, competition margins, rivalry log-counts."""
import numpy as np
import pandas as pd

from ber.features.context import FEATURES, _group_top2, compute, numstreet_keys


def test_group_top2():
    best, second, size = _group_top2(np.array([5, 5, 7, 5]), np.array([0.2, 0.9, 0.4, 0.5], np.float32))
    assert np.allclose(best, [0.9, 0.9, 0.4, 0.9]) and np.allclose(second, [0.5, 0.5, 0.0, 0.5])
    assert size.tolist() == [3, 3, 1, 3]


def test_compute_margins_ranks_and_rival_counts():
    cands = pd.DataFrame({
        "s1": [1_000_000_001, 1_000_000_001, 1_000_000_002], "r": [2_000_000_005, 3_000_000_007, 2_000_000_005],
        "views": np.array([64, 68, 64], np.int16), "score_tok": np.array([0.9, 0.3, 0.6], np.float32),
        "rank_s1_tok": np.array([0, 1, 0], np.int16), "rank_r_tok": np.array([0, -1, 1], np.int16)})
    s1 = pd.DataFrame({"eid": [1_000_000_001, 1_000_000_002, 1_000_000_003], "country": ["US", "US", "France"],
                       "name": ["Acme Robotics Inc", "Robotics ACME", "Acme Robotics"],
                       "address": ["500 Market St", "500 Market Street", "500 Market St"]})
    f = compute(cands, s1)
    assert len(f) == 3 and all(f[c].dtype == np.float32 for c in f.columns)
    assert np.allclose(f["ret__margin_r"], [0.3, 0.3, -0.3])       # S2-5: 0.9 vs its other S1 at 0.6
    assert f["ret__tok_rank_r"].tolist() == [0, 99, 1]              # absent rank -> 99
    assert f["ret__n_views"].tolist() == [1, 2, 1]
    assert np.allclose(f["ctx__log_s1_same_name"], np.log1p(1))     # the French S1 is not a rival (other country)
    assert f["src__is_s3"].tolist() == [0, 1, 0]
    assert all(k.split("__")[0] in ("ret", "ctx", "src") for k in FEATURES)


def test_numstreet_keys_skip_street_types_and_survive_reordering():
    import pyarrow as pa
    keys = numstreet_keys(pa.array([
        "32 Rue André Maginot, Mérignac", "PA, AVELLA CITY, 972 OLD RIDGE RD", "4809 Harrison Ferry Road, Hurlock, MD",
        "0020718 ADAMS MILL PLACE, VA", "Sno 32/2/1 Hno 1048, Gulabnagar", "HARRISON FERRY ROAD, HURLOCK, MD"]))
    assert keys.tolist() == ["32|andre", "972|old", "4809|harrison", "20718|adams", "1048|gulabnagar", ""]
