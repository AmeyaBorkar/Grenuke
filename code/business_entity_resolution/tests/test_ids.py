import numpy as np
import pytest

from ber.ids import source_of, to_eid, to_eids, to_entity_id, to_entity_ids


def test_roundtrip_examples():
    for s in ["S1-965667", "S2-681193310", "S3-5", "S1-0", "S3-999999999"]:
        assert to_entity_id(to_eid(s)) == s
    assert to_eid("S2-681193310") == 2_681_193_310


def test_vectorized_matches_scalar():
    ids = ["S1-217", "S2-576", "S3-10", "S2-999999727"]
    e = to_eids(ids)
    assert e.dtype == np.int64
    assert e.tolist() == [to_eid(s) for s in ids]
    assert to_entity_ids(e).tolist() == ids
    assert source_of(e).tolist() == [1, 2, 3, 2]


@pytest.mark.parametrize("bad", ["S4-1", "X1-5", "S1-01", "S1-1234567890", "S1-", "S1-12a", "s1-5"])
def test_rejects_bad_ids(bad):
    with pytest.raises(ValueError):
        to_eid(bad)
    with pytest.raises(ValueError):
        to_eids([bad])
