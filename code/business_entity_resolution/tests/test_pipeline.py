"""The pipeline skeleton on a tiny synthetic dataset: records -> (fake stage outputs) -> write / evaluate."""
import json

import pandas as pd
import pytest

from ber import artifacts, pipeline
from ber.config import RunConfig
from ber.outputs import check_subset
from ber.paths import check_name, records_path, report_path, truth_path

HEADER = "entity_id\tbusiness_name\tbusiness_address\tcountry\n"


def _write(path, rows, header=HEADER):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header + "".join("\t".join(r) + "\n" for r in rows), encoding="utf-8")


@pytest.fixture
def env(tmp_path, monkeypatch):
    data = tmp_path / "dataset"
    for split in ("train", "test"):
        _write(data / split / f"{split}_source1.tsv", [
            ("S1-1", 'Acme "Robotics" Inc', "500 Market St, San Jose, CA", "US"),
            ("S1-2", "Sri Balaji Traders", "12 MG Road, Pune, MH", "India"),
            ("S1-3", "Café Lumière", "", "France" if split == "test" else "US"),
        ])
        _write(data / split / f"{split}_source2.tsv", [
            ("S2-5", "ACME ROBOTICS", "500 MARKET ST", "US"),
            ("S2-6", "Balaji Traders Pvt Ltd", "", "India"),
        ])
        _write(data / split / f"{split}_source3.tsv", [
            ("S3-7", "Acme Robotix", "12 Elm Rd", "US"),
        ])
    _write(data / "train" / "train_ground_truth.tsv",
           [("S1-1", "S2-5"), ("S1-2", "S2-6"), ("S1-3", "")], header="source1_entity_id\tmatched_entity_ids\n")
    monkeypatch.setenv("BER_DATA_DIR", str(data))
    monkeypatch.setenv("BER_WORK_DIR", str(tmp_path / "work"))
    monkeypatch.setenv("BER_OUTPUT_DIR", str(tmp_path / "output"))
    for split in ("train", "test"):
        assert pipeline.main(["--stage", "records", "--split", split]) == 0
    return tmp_path


def test_records_stage(env):
    rec = pd.read_parquet(records_path("train"))
    assert list(rec.columns) == ["eid", "source", "country", "name", "address"]
    assert rec["eid"].tolist() == [1_000_000_001, 1_000_000_002, 1_000_000_003, 2_000_000_005, 2_000_000_006, 3_000_000_007]
    assert rec.loc[0, "name"] == 'Acme "Robotics" Inc'  # quotes survive
    truth = pd.read_parquet(truth_path())
    assert sorted(map(tuple, truth[["s1", "r"]].to_numpy())) == [(1_000_000_001, 2_000_000_005), (1_000_000_002, 2_000_000_006)]
    meta = artifacts.read_meta(records_path("test"))
    assert meta["kind"] == "records" and meta["rows"] == 6 and "git_commit" in meta


def test_artifact_roundtrip_and_names(env):
    df = pd.DataFrame({"s1": [1_000_000_001], "r": [2_000_000_005]})
    path = artifacts.write_table(df, "candidates", "t-block-v0", "train", inputs={"norm": "t-norm-v0"})
    assert artifacts.read_table("candidates", "t-block-v0", "train").equals(df)
    meta = artifacts.read_meta(path)
    assert meta["inputs"] == {"norm": "t-norm-v0"} and meta["tag"] == "t-block-v0"
    with pytest.raises(FileNotFoundError):
        artifacts.read_table("candidates", "missing", "train")
    with pytest.raises(ValueError):
        check_name("Bad/Tag")


def test_write_stage(env):
    cands = pd.DataFrame({"s1": [1_000_000_001, 1_000_000_001, 1_000_000_002], "r": [2_000_000_005, 3_000_000_007, 2_000_000_006]})
    artifacts.write_table(cands, "candidates", "t", "test")
    artifacts.write_table(cands.iloc[[0, 2]], "matches", "t", "test")
    assert pipeline.main(["--stage", "write", "--split", "test", "--tag", "t"]) == 0
    lines = (env / "output" / "matching_results.tsv").read_text(encoding="utf-8").splitlines()
    assert lines == ["source1_entity_id\tmatched_entity_ids", "S1-1\tS2-5", "S1-2\tS2-6", "S1-3\t"]
    cand_lines = (env / "output" / "candidate_pairs.tsv").read_text(encoding="utf-8").splitlines()
    assert cand_lines[1] == "S1-1\tS2-5,S3-7"
    with pytest.raises(ValueError):
        check_subset(pd.DataFrame({"s1": [1_000_000_003], "r": [2_000_000_005]}), cands)


def test_evaluate_stage_train_and_test(env):
    truth = pd.read_parquet(truth_path())
    artifacts.write_table(truth, "matches", "t", "train")
    extra = pd.DataFrame({"s1": [1_000_000_001], "r": [3_000_000_007]})
    artifacts.write_table(pd.concat([truth, extra]), "candidates", "t", "train")
    assert pipeline.main(["--stage", "evaluate", "--split", "train", "--tag", "t", "--folds", "0-19"]) == 0
    artifacts.write_table(truth.iloc[:1], "matches", "t", "test")
    assert pipeline.main(["--stage", "evaluate", "--split", "test", "--tag", "t"]) == 0
    rep = json.loads(report_path("t").read_text(encoding="utf-8"))
    assert rep["holdout"]["macro_f05"] == 1.0 and set(rep["holdout"]["by_country"]) == {"US", "India"}
    assert rep["blocking"]["pair_recall"] == 1.0 and rep["blocking"]["cands_per_s1_p99"] >= 1
    assert rep["test_diagnostics"]["mean_pred_per_s1_by_country"]["US"] == 1.0
    assert rep["inputs"] == {"matches": "t", "candidates": "t"} and "git_commit" in rep


def test_cli_rules(env):
    assert pipeline.stages_for("all", "test") == ["records", "normalize", "block", "features", "predict", "decide", "write", "evaluate"]
    assert "write" not in pipeline.stages_for("all", "train") and "train" in pipeline.stages_for("all", "train")
    assert pipeline.main(["--stage", "normalize", "--split", "train", "--tag", "t"]) == 2  # stub: not implemented yet
    for bad in (["--stage", "write", "--split", "train", "--tag", "t"],
                ["--stage", "block", "--split", "train"],
                ["--stage", "block", "--split", "train", "--tag", "t", "--in", "nope=x"]):
        with pytest.raises(SystemExit):
            pipeline.main(bad)


def test_config_inputs_and_params():
    cfg = RunConfig(split="train", tag="t", inputs={"norm": "other"}, params={"k": "40"})
    assert cfg.input_tag("norm") == "other" and cfg.input_tag("candidates") == "t"
    assert cfg.param("k", 10, int) == 40 and cfg.param("missing", 3) == 3
    with pytest.raises(ValueError):
        RunConfig(split="valid")
