"""Pair-feature noise cases from issue #7 (optional full-environment test)."""
import pandas as pd
import pytest

pytest.importorskip("rapidfuzz")
pytest.importorskip("sklearn")
pytest.importorskip("numba")

from ber.features.string import FEATURES, compute
from ber import artifacts
from ber.config import RunConfig
from ber.features import run
from ber.paths import records_path, truth_path


def _record(name, address, number, *, extra="", indic=False):
    return {
        "n_core": name, "n_concat": name.replace(" ", ""), "n_legal": "",
        "f_domain": False, "f_hashtag": False, "f_indic": indic,
        "a_norm": address, "a_street": address, "a_city": "pune",
        "a_state": "mh", "a_num1": number, "a_num1_sfx": "", "a_unit": -1,
        "a_ntok": len(address.split()), "f_addr_empty": not address,
        "f_addr_short": len(address.split()) <= 3, "f_landmark": False,
        "f_pobox": False, "f_addr_null": False,
    }


def test_added_business_word_and_nudged_house_number():
    left = pd.DataFrame([
        _record("acme solutions", "4104 market road", 4104),
        _record("balaji traders", "", -1, indic=True),
    ])
    right = pd.DataFrame([
        _record("acme solutions exports", "4108 market road", 4108),
        _record("balaji traders", "", -1),
    ])
    out = compute(left, right, left["a_state"].to_numpy())
    assert set(out.columns) == set(FEATURES)
    assert out.loc[0, "extra__r_count"] == 1
    assert out.loc[0, "num__nudge"] == 1
    assert out.loc[0, "num__abs_diff"] == 4
    assert out.loc[1, "name__indic_mismatch"] == 1
    assert out.loc[1, "addr__either_empty"] == 1
    assert all(dtype.name == "float32" for dtype in out.dtypes)


def test_stage_writes_c8_pairs_labels_and_metadata(tmp_path, monkeypatch):
    monkeypatch.setenv("BER_WORK_DIR", str(tmp_path / "work"))
    norm = pd.DataFrame([
        {**_record("acme solutions", "4104 market road", 4104),
         "eid": 1_000_000_001, "source": 1, "country": "US", "a_nums": [4104]},
        {**_record("acme solutions", "4104 market road", 4104),
         "eid": 2_000_000_002, "source": 2, "country": "US", "a_nums": [4104]},
        {**_record("acme solutions exports", "4108 market road", 4108),
         "eid": 3_000_000_003, "source": 3, "country": "US", "a_nums": [4108]},
    ])
    artifacts.write_table(norm, "norm", "bakshi-norm-v0", "train")
    candidates = pd.DataFrame({"s1": [1_000_000_001, 1_000_000_001],
                               "r": [2_000_000_002, 3_000_000_003]})
    artifacts.write_table(candidates, "candidates", "ameya-block-v0-dev", "train")
    truth = candidates.iloc[:1].copy()
    truth_path().parent.mkdir(parents=True, exist_ok=True)
    truth.to_parquet(truth_path(), index=False)
    cfg = RunConfig(split="train", tag="bakshi-feat-v0",
                    inputs={"norm": "bakshi-norm-v0", "candidates": "ameya-block-v0-dev"},
                    params={"batch_size": "1", "idf_docs": "2"})
    result = run(cfg)
    out = artifacts.read_table("features", "bakshi-feat-v0", "train")
    assert result["pairs"] == 2
    assert out["y"].tolist() == [1, 0]
    assert out["s1"].tolist() == candidates["s1"].tolist()
    assert out["num__abs_diff"].tolist() == [0, 4]
    assert set(FEATURES) <= set(out.columns)
    meta = artifacts.read_meta(result["path"])
    assert meta["inputs"] == {"norm": "bakshi-norm-v0", "candidates": "ameya-block-v0-dev"}

    # Context uses the full candidate set and raw S1 records, independent of
    # the string-feature batches. Keep a two-batch test to catch API drift.
    raw = pd.DataFrame({
        "eid": norm["eid"], "source": norm["source"], "country": norm["country"],
        "name": ["Acme Solutions", "Acme Solutions", "Acme Solutions Exports"],
        "address": ["4104 Market Road", "4104 Market Road", "4108 Market Road"],
    })
    records_path("train").parent.mkdir(parents=True, exist_ok=True)
    raw.to_parquet(records_path("train"), index=False)
    candidates["views"] = 64
    candidates["score_tok"] = [0.9, 0.7]
    candidates["rank_s1_tok"] = [0, 1]
    candidates["rank_r_tok"] = [0, 0]
    artifacts.write_table(candidates, "candidates", "ameya-block-v0-dev", "train")
    cfg = RunConfig(split="train", tag="bakshi-feat-context-v0",
                    inputs={"norm": "bakshi-norm-v0", "candidates": "ameya-block-v0-dev"},
                    params={"batch_size": "1", "idf_docs": "2", "include_context": "true"})
    run(cfg)
    with_context = artifacts.read_table("features", "bakshi-feat-context-v0", "train")
    assert with_context["ctx__log_cands_s1"].tolist() == [pytest.approx(1.0986123)] * 2
    assert with_context["src__is_s3"].tolist() == [0.0, 1.0]
