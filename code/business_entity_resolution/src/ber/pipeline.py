"""Pipeline command line (plans/FINAL_PLAN.md section 3, docs/DEVELOPMENT.md).

    python -m ber.pipeline --stage records  --split train
    python -m ber.pipeline --stage block    --split train --tag ameya-block-v0 --in norm=m3-norm-v0
    python -m ber.pipeline --stage evaluate --split train --tag sachi-model-v0 --folds 0
    python -m ber.pipeline --stage all      --split test  --tag v0

Each stage reads its inputs by tag (``--in <kind>=<tag>``, default: this run's ``--tag``) and writes its own
artifact (docs/CONTRACTS.md), so any stage can be re-run, swapped or A/B-tested alone. Stages import their heavy
dependencies themselves, so this module stays light.
"""
from __future__ import annotations

import argparse
import importlib
import json
import logging
import sys
import time

from .config import ARTIFACT_KINDS, SEED, RunConfig

log = logging.getLogger("ber.pipeline")

# name -> (module, function, what it writes). The order is the order of --stage all.
STAGES: dict[str, tuple[str, str, str]] = {
    "records": ("ber.records", "run", "work/records/<split>.parquet (+ truth.parquet) - C3"),
    "normalize": ("ber.normalize", "run", "work/norm/<tag>/<split>.parquet - C3"),
    "block": ("ber.block", "run", "work/candidates/<tag>/<split>.parquet - C4"),
    "features": ("ber.features", "run", "work/features/<tag>/<split>.parquet - C8"),
    "train": ("ber.model", "train", "work/models/<tag>/, work/scores/<tag>-s1/train.parquet - C5"),
    "predict": ("ber.model", "predict", "work/scores/<tag>/<split>.parquet - C5"),
    "decide": ("ber.model", "decide", "work/matches/<tag>/<split>.parquet - C9"),
    "write": ("ber.outputs", "run", "output/matching_results.tsv, output/candidate_pairs.tsv - C6"),
    "evaluate": ("ber.eval.evaluate", "run", "work/reports/<tag>.json - C7"),
}
ONLY_SPLIT = {"train": "train", "write": "test"}
NO_TAG = {"records"}


def _pairs(items: list[str] | None, what: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items or []:
        key, sep, value = item.partition("=")
        if not sep or not key or not value:
            raise argparse.ArgumentTypeError(f"{what} expects key=value, got {item!r}")
        out[key.strip()] = value.strip()
    return out


def _folds(text: str | None) -> tuple[int, ...] | None:
    if not text:
        return None
    folds: list[int] = []
    for part in text.split(","):
        lo, _, hi = part.partition("-")
        folds.extend(range(int(lo), int(hi or lo) + 1))
    if not all(0 <= f < 20 for f in folds):
        raise argparse.ArgumentTypeError("folds must be in 0..19")
    return tuple(sorted(set(folds)))


def stages_for(stage: str, split: str) -> list[str]:
    """The stages to run, in order. ``all`` skips stages that belong to the other split."""
    if stage == "all":
        return [s for s in STAGES if ONLY_SPLIT.get(s, split) == split]
    if stage not in STAGES:
        raise ValueError(f"unknown stage {stage!r}; choose from: all, {', '.join(STAGES)}")
    if ONLY_SPLIT.get(stage, split) != split:
        raise ValueError(f"stage {stage!r} runs on --split {ONLY_SPLIT[stage]} only")
    return [stage]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="python -m ber.pipeline", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", required=True, help=f"all, or one of: {', '.join(STAGES)}")
    ap.add_argument("--split", required=True, choices=("train", "test"))
    ap.add_argument("--tag", help="output tag, e.g. ameya-block-v0 (docs/CONTRACTS.md C0); not needed for records")
    ap.add_argument("--in", dest="inputs", action="append", metavar="KIND=TAG",
                    help=f"read an input artifact from another tag; kinds: {', '.join(ARTIFACT_KINDS)}")
    ap.add_argument("--set", dest="params", action="append", metavar="KEY=VALUE", help="stage parameter (documented by the owner)")
    ap.add_argument("--folds", help="restrict train S1 to folds, e.g. 0 or 0-4 (dev runs; PR numbers use the holdout)")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--n-jobs", type=int, default=-1)
    ap.add_argument("--device", choices=("auto", "cuda", "cpu"), default="auto")
    return ap


def run_stage(name: str, cfg: RunConfig) -> dict:
    module, func, writes = STAGES[name]
    log.info("stage %s: start (%s)", name, writes)
    t0 = time.perf_counter()
    result = getattr(importlib.import_module(module), func)(cfg) or {}
    log.info("stage %s: done in %.1fs", name, time.perf_counter() - t0)
    return result


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    ap = build_parser()
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
    try:
        names = stages_for(args.stage, args.split)
        if args.tag is None and any(n not in NO_TAG for n in names):
            ap.error("--tag is required for every stage except records")
        cfg = RunConfig(
            split=args.split, tag=args.tag, inputs=_pairs(args.inputs, "--in"), params=_pairs(args.params, "--set"),
            folds=_folds(args.folds), seed=args.seed, n_jobs=args.n_jobs, device=args.device,
            command="python -m ber.pipeline " + " ".join(argv),
        )
    except (ValueError, argparse.ArgumentTypeError) as exc:
        ap.error(str(exc))
    for name in names:
        try:
            result = run_stage(name, cfg)
        except NotImplementedError as exc:
            log.error("stage %s is not implemented yet: %s", name, exc)
            return 2
        print(json.dumps({"stage": name, **result}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
