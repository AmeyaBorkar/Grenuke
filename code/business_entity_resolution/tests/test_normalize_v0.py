"""Contract C3 and the high-noise strings from issue #6."""
import pandas as pd

from ber.artifacts import read_meta, read_table
from ber.config import RunConfig
from ber.normalize import run
from ber.normalize.address import parse_address
from ber.normalize.name import parse_name
from ber.paths import records_path


def test_names_keep_identity_and_flags():
    first = parse_name("SAS Café Lumière")
    second = parse_name("Café Lumière SAS")
    assert first[1:4] == second[1:4] == ("cafe lumiere", "cafelumiere", "sas")
    assert parse_name("श्री बालाजी ट्रेडर्स")[8] is True
    assert parse_name("தமிழ் கடை")[8] is True
    assert parse_name("श्री बालाजी ट्रेडर्स")[1]  # a usable Latin form
    flagged = parse_name("ABC DBA XYZ #xyz foo.com +1-415-555-1234")
    assert flagged[4:8] == (True, True, True, True)


def test_address_numbers_nulls_and_street_types():
    hno = parse_address("H.No 12-3-45, MG Road, Pune, MH")
    assert hno[4] == 12 and hno[6] == [12, 3, 45]
    assert hno[1] == "mg rd" and hno[2:4] == ("pune", "mh")
    assert parse_address("8444b Market Street")[4:6] == (8444, "b")
    assert parse_address("12 bis Rue St Honoré, Paris, Île-de-France")[4:6] == (12, "bis")
    assert parse_address("N°16 R. du Bac, Paris, Île-de-France")[4] == 16
    assert parse_address("Nantes, 6 Boulevard Pasteur, Pays de la Loire")[1:5] == (
        "blvd pasteur", "nantes", "pdl", 6,
    )
    assert parse_address("NY, Islip, 235 Furrows Road")[1:5] == (
        "furrows rd", "islip", "ny", 235,
    )
    assert parse_address("845 7th Street, Ottawa, KS")[1] == "7 st"
    assert parse_address("<NULL>")[9] is True
    assert parse_address("<NULL>")[14] is True
    assert parse_address("8e Rue de la Paix, Paris, Île-de-France")[15] is True


def test_stage_writes_one_row_per_record_and_provenance(tmp_path, monkeypatch):
    monkeypatch.setenv("BER_WORK_DIR", str(tmp_path / "work"))
    records = pd.DataFrame({
        "eid": [1_000_000_001, 2_000_000_002],
        "source": pd.Series([1, 2], dtype="int8"),
        "country": ["India", "France"],
        "name": ["Balaji Traders Pvt Ltd", "SAS Café Lumière"],
        "address": ["H.No 12-3-45, MG Road, Pune, MH", "12 bis Rue St Honoré, Paris"],
    })
    path = records_path("train")
    path.parent.mkdir(parents=True)
    records.to_parquet(path, index=False)
    result = run(RunConfig(split="train", tag="bakshi-norm-v0", n_jobs=1))
    out = read_table("norm", "bakshi-norm-v0", "train")
    assert result["records"] == 2
    assert out["eid"].tolist() == records["eid"].tolist()
    assert set(("n_full", "n_core", "a_nums", "f_indic", "f_addr_short")) <= set(out)
    assert out.loc[0, "a_nums"].tolist() == [12, 3, 45]
    assert read_meta(result["path"])["rows"] == 2
