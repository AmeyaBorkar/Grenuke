"""Build the parquet cache the plan checks read: data_cache/{train,test}_s{1,2,3}.parquet and train_gt.parquet.

Reads the raw TSVs through ber.io (tab separator, quoting disabled). About 1 minute.
    pip install -e code/business_entity_resolution
    python experiments/ameya/plan-checks/make_cache.py
"""
from pathlib import Path

from ber.io import read_source, read_tsv
from ber.paths import data_dir

from nn_lib import DC


def main() -> None:
    out = Path(DC)
    out.mkdir(parents=True, exist_ok=True)
    for split in ("train", "test"):
        for k in (1, 2, 3):
            df = read_source(data_dir() / split / f"{split}_source{k}.tsv").astype(object)
            df.to_parquet(out / f"{split}_s{k}.parquet", index=False)
            print(split, k, len(df))
    gt = read_tsv(data_dir() / "train" / "train_ground_truth.tsv").astype(object)
    gt.to_parquet(out / "train_gt.parquet", index=False)
    print("truth", len(gt))


if __name__ == "__main__":
    main()
