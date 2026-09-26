import sys
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

sys.path.insert(0, str(Path(__file__).parent))
from audit_tsv import import_matching
import probe_exact
from ber.io import write_matching


def test_import_preserves_empty_rows_and_integer_ids(tmp_path):
    path = tmp_path / "matches.tsv"
    write_matching(path, ["S1-1", "S1-2"], pd.DataFrame({"s1": [1000000001], "r": [2000000003]}))
    ids, pairs, digest = import_matching(path)
    assert ids.tolist() == [1000000001, 1000000002]
    assert list(pairs.itertuples(index=False, name=None)) == [(1000000001, 2000000003)]
    assert len(digest) == 64


@pytest.mark.parametrize("body", ["S1-1\tS2-3,S2-3\n", "S1-1\tS2-3\nS1-1\t\n",
                                 "S1-1\tS1-2\n", "S2-1\tS3-2\n"])
def test_import_rejects_duplicates_and_wrong_sources(tmp_path, body):
    path = tmp_path / "bad.tsv"
    path.write_text("source1_entity_id\tmatched_entity_ids\n" + body, encoding="utf-8")
    with pytest.raises(ValueError):
        import_matching(path)


def test_strict_rescue_checks_all_owners_and_verifies_complete_text(tmp_path, monkeypatch):
    d = pd.DataFrame({
        "eid": [1000000001, 1000000002, 1000000003, 1000000004, 2000000001, 2000000002,
                2000000003, 2000000004, 2000000005],
        "source": [1, 1, 1, 1, 2, 2, 2, 2, 2], "country": ["X"] * 9,
        "name": ["Alpha Club SAS", "Duplicate Club SAS", "Duplicate Club SAS", "Missing Club SAS",
                 "ALPHA CLÚB SAS", "Alpha Club SAS", "Duplicate Club SAS", "Missing Club SAS", "Alpha Club SA"],
        "address": ["12 Rue Jean Moulin, Nantes", "13 Rue Jean Moulin, Nantes", "13 Rue Jean Moulin, Nantes", "",
                    "12 Rue Jean Moulin, Nantes", "12 Rue Jean Jaures, Nantes", "13 Rue Jean Moulin, Nantes", "",
                    "12 Rue Jean Moulin, Nantes"]})
    path = tmp_path / "records.parquet"
    pq.write_table(pa.Table.from_pandas(d), path)
    monkeypatch.setattr(probe_exact, "records_path", lambda split: path)
    result = probe_exact.retrieve("test", target_s1=[1000000001, 1000000002, 1000000004])
    assert list(result.itertuples(index=False, name=None)) == [(1000000001, 2000000001)]


def test_normalized_keys_preserve_street_city_house_suffix_and_unit(tmp_path):
    d = pd.DataFrame({"eid": [1000000001, 2000000001, 2000000002, 2000000003, 2000000004],
        "source": [1, 2, 2, 2, 2], "country": ["X"] * 5, "n_full": ["alpha club sas"] * 5,
        "a_street": ["jean moulin", "jean moulin", "jean jaures", "jean moulin", "jean moulin"],
        "a_city": ["nantes", "nantes", "nantes", "lille", "nantes"],
        "a_num1": [12] * 5, "a_num1_sfx": [""] * 5, "a_unit": [-1, -1, -1, -1, 2]})
    path = tmp_path / "norm.parquet"
    pq.write_table(pa.Table.from_pandas(d), path)
    result = probe_exact.retrieve("test", norm_file=path)
    assert list(result.itertuples(index=False, name=None)) == [(1000000001, 2000000001)]


def test_normalized_keys_exclude_missing_city_number_and_short_street():
    batch = pa.record_batch({"country": ["X"] * 4, "n_full": ["alpha club sas"] * 4,
        "a_street": ["jean moulin", "jean moulin", "jean moulin", "jean"],
        "a_city": ["nantes", "", "nantes", "nantes"], "a_num1": [12, 12, -1, 12],
        "a_num1_sfx": [""] * 4, "a_unit": [-1] * 4})
    _, valid = probe_exact.keys(batch)
    assert valid.tolist() == [True, False, False, False]


def test_residual_inspection_exposes_lost_numbers_and_compatible_old_owner(tmp_path, monkeypatch):
    raw = pd.DataFrame({"eid": [1000000001, 1000000002, 2000000001],
        "name": ["Alpha Club SAS", "Alpha Clúb SAS", "ALPHA CLUB SAS"],
        "address": ["27W 10 North Avenue, Chicago", "Chicago, 27W 13 North Avenue", "27W 13 North Avenue, Chicago"]})
    path = tmp_path / "raw.parquet"
    pq.write_table(pa.Table.from_pandas(raw), path)
    monkeypatch.setattr(probe_exact, "records_path", lambda split: path)
    residual = pd.DataFrame({"s1": [1000000001], "r": [2000000001], "existing_owner": [1000000002]})
    flags = probe_exact.inspect_residuals(residual, "test")
    assert not flags.numeric_sequence_equal.iloc[0]
    assert flags.existing_owner_compatible.iloc[0]


def test_empty_residual_inspection():
    empty = pd.DataFrame(columns=["s1", "r", "existing_owner"])
    flags = probe_exact.inspect_residuals(empty, "train")
    assert flags.empty
    assert flags.numeric_sequence_equal.dtype == bool
