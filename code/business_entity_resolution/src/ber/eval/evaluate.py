"""Stage ``evaluate``: the result report ``work/reports/<tag>.json`` (docs/CONTRACTS.md C7).

- ``--split train``: scores the shared holdout (or ``--folds``) against the truth. ``--set sample=dev`` restricts it to
  the dev sample (``ber.eval.splits.in_dev_sample``), e.g. ``--folds 0 --set sample=dev`` on a small machine.
  Adds ``holdout`` from C9 matches and ``blocking`` from C4 candidates, whichever exist for the input tags.
- ``--split test``: no labels; adds ``test_diagnostics`` per country (mean predicted matches per S1, share of
  S2/S3 records assigned), which gate G8 compares with the holdout.
The report keeps keys written by earlier runs with the same tag, so train and test results end up in one file.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import artifacts, ids
from ..config import RunConfig
from ..records import load_records, load_truth
from .metric import oracle_f05, pair_recall, report
from .splits import in_dev_sample, in_folds, is_holdout


def blocking_report(cands: pd.DataFrame, truth: pd.DataFrame, universe: np.ndarray, country: pd.Series) -> dict:
    """Pair recall and oracle F0.5 on ``universe``, candidates per S1, recall per country and per source."""
    c = cands[cands["s1"].isin(universe)]
    t = truth[truth["s1"].isin(universe)]
    per_s1 = c.groupby("s1").size().reindex(universe, fill_value=0)
    hit = t.merge(c[["s1", "r"]], on=["s1", "r"], how="left", indicator=True)
    hit["found"] = hit.pop("_merge") == "both"
    hit["country"] = country.reindex(hit["s1"]).to_numpy()
    hit["source"] = "S" + pd.Series(ids.source_of(hit["r"].to_numpy())).astype(str).to_numpy()
    return {
        "pair_recall": pair_recall(c, t),
        "oracle_f05": oracle_f05(c, t, universe),
        "cands_per_s1_mean": float(per_s1.mean()) if len(per_s1) else 0.0,
        "cands_per_s1_p99": int(np.percentile(per_s1, 99)) if len(per_s1) else 0,
        "recall_by_country": {str(k): float(v) for k, v in hit.groupby("country")["found"].mean().items()},
        "recall_by_source": {str(k): float(v) for k, v in hit.groupby("source")["found"].mean().items()},
    }


def prediction_diagnostics(matches: pd.DataFrame, rec: pd.DataFrame) -> dict:
    """Per-country prediction statistics without labels (compare with the holdout, gate G8)."""
    country = pd.Series(rec["country"].to_numpy(), index=rec["eid"].to_numpy())
    s1 = rec[rec["source"] == 1]
    r_all = rec[rec["source"] != 1]
    m = matches.assign(country=country.reindex(matches["s1"]).to_numpy())
    n_s1 = s1.groupby("country").size()
    n_r = r_all.groupby("country").size()
    pred = m.groupby("country").size().reindex(n_s1.index, fill_value=0)
    assigned = m.drop_duplicates("r").groupby("country").size().reindex(n_r.index, fill_value=0)
    return {
        "mean_pred_per_s1_by_country": {str(k): float(pred[k] / n_s1[k]) for k in n_s1.index},
        "frac_r_assigned_by_country": {str(k): float(assigned[k] / n_r[k]) for k in n_r.index},
    }


def run(cfg: RunConfig) -> dict:
    tag = cfg.require_tag()
    inputs, payload = {}, {}
    rec = load_records(cfg.split, columns=["eid", "source", "country"])
    has = {k: artifacts.exists(k, cfg.input_tag(k), cfg.split) for k in ("matches", "candidates")}
    if not any(has.values()):
        raise FileNotFoundError(f"no matches or candidates for split {cfg.split!r} under the input tags")

    if cfg.split == "test":
        if has["matches"]:
            inputs["matches"] = cfg.input_tag("matches")
            payload["test_diagnostics"] = prediction_diagnostics(artifacts.read_table("matches", inputs["matches"], "test", ["s1", "r"]), rec)
    else:
        s1 = rec[rec["source"] == 1]
        mask = is_holdout(s1["eid"]) if cfg.folds is None else in_folds(s1["eid"], cfg.folds)
        sample = cfg.param("sample")
        if sample not in (None, "dev"):
            raise ValueError(f"--set sample= must be 'dev', got {sample!r}")
        if sample == "dev":
            mask &= in_dev_sample(s1["eid"])
        universe = s1["eid"].to_numpy()[mask]
        country = pd.Series(s1["country"].to_numpy(), index=s1["eid"].to_numpy())
        truth = load_truth()
        payload["evaluated_on"] = ("holdout" if cfg.folds is None else f"folds {list(cfg.folds)}") + (" (dev sample)" if sample else "")
        if has["matches"]:
            inputs["matches"] = cfg.input_tag("matches")
            m = artifacts.read_table("matches", inputs["matches"], "train", ["s1", "r"])
            rep = report(m, truth, universe, groups=country)
            rep["by_country"] = rep.pop("by_group")
            payload["holdout"] = rep
        if has["candidates"]:
            inputs["candidates"] = cfg.input_tag("candidates")
            c = artifacts.read_table("candidates", inputs["candidates"], "train", ["s1", "r"])
            payload["blocking"] = blocking_report(c, truth, universe, country)

    path = artifacts.write_report(tag, payload, command=cfg.command, inputs=inputs)
    return {"report": str(path), **{k: v for k, v in payload.items() if k != "blocking"}}
