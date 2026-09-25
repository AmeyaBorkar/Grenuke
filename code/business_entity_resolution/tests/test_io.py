import pandas as pd
import pytest

from ber.ids import to_eid
from ber.io import read_id_lists, read_source, read_tsv, truth_pairs, write_candidates, write_matching


def test_read_tsv_keeps_quotes_and_empty_fields(tmp_path):
    p = tmp_path / "s.tsv"
    p.write_text(
        "entity_id\tbusiness_name\tbusiness_address\tcountry\n"
        "S1-1\tO'Neil \"Best\" Cafe, LLC\t\tUS\n"
        "S1-2\t\"Quoted Start\tMain St, Unit 5\tIndia\n",
        encoding="utf-8",
    )
    df = read_source(p)
    assert df["business_name"].tolist() == ["O'Neil \"Best\" Cafe, LLC", '"Quoted Start']
    assert df["business_address"].tolist() == ["", "Main St, Unit 5"]
    assert not df.isna().any().any()


def test_truth_pairs(tmp_path):
    p = tmp_path / "gt.tsv"
    p.write_text("source1_entity_id\tmatched_entity_ids\nS1-1\tS2-5,S3-6\nS1-2\t\n", encoding="utf-8")
    pairs = truth_pairs(read_tsv(p))
    assert sorted(map(tuple, pairs[["s1", "r"]].to_numpy().tolist())) == [
        (to_eid("S1-1"), to_eid("S2-5")),
        (to_eid("S1-1"), to_eid("S3-6")),
    ]


def test_write_matching_exact_format(tmp_path):
    order = ["S1-3", "S1-1", "S1-2"]
    pairs = pd.DataFrame(
        {
            "s1": [to_eid("S1-1"), to_eid("S1-1"), to_eid("S1-1"), to_eid("S1-3")],
            "r": [to_eid("S3-9"), to_eid("S2-7"), to_eid("S2-7"), to_eid("S2-1")],  # duplicate on purpose
        }
    )
    out = write_matching(tmp_path / "m.tsv", order, pairs)
    assert out.read_bytes().decode("utf-8") == (
        "source1_entity_id\tmatched_entity_ids\n"
        "S1-3\tS2-1\n"
        "S1-1\tS2-7,S3-9\n"
        "S1-2\t\n"
    )
    s1_order, back = read_id_lists(out)
    assert s1_order == order and len(back) == 3


def test_write_candidates_header_and_empty(tmp_path):
    out = write_candidates(tmp_path / "c.tsv", ["S1-1"], None)
    assert out.read_text(encoding="utf-8") == "source1_entity_id\tcandidate_entity_ids\nS1-1\t\n"


def test_writer_rejects_invalid_pairs(tmp_path):
    with pytest.raises(ValueError):  # S1 id in the match list
        write_matching(tmp_path / "x.tsv", ["S1-1"], pd.DataFrame({"s1": [to_eid("S1-1")], "r": [to_eid("S1-2")]}))
    with pytest.raises(ValueError):  # pair for an S1 that is not in the order
        write_matching(tmp_path / "x.tsv", ["S1-1"], pd.DataFrame({"s1": [to_eid("S1-9")], "r": [to_eid("S2-2")]}))
    with pytest.raises(ValueError):  # duplicate S1 rows
        write_matching(tmp_path / "x.tsv", ["S1-1", "S1-1"], None)
