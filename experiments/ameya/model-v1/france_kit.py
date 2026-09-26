"""Export a France kit for French pattern discovery (the op-A/op-B method of post_ops.py), for a teammate's machine.

    python experiments/ameya/model-v1/france_kit.py --out france-kit-v1

Writes work/kits/<out>/:
- france_pairs.parquet: every French S1's stage-2 pair (p1 >= 0.002):
  - scores p1, pc;
  - flags in_cands (the final candidate set), pred_model (the model's decision before the rules) and pred_final
    (after France rules v2);
  - the edit profile of post_ops.classify: op (B/A/APP/ACR/NUM/CODE or ""), kind, pos, added, dropped, same_num,
    street_typo, num_kind;
  - s1_group (S1 sharing its core name), source;
  - raw names and addresses of both sides.
- holdout_pairs.parquet: the same columns for the US/India shared holdout (549,699 S1) plus y (truth), country and
  pred (the model's holdout decision), to measure truth rates per profile.
- README.md: columns, counts and the definitions (list words, nudge set, thresholds).
No labels of the test set exist or are used. The files are data: keep them out of git (work/ is ignored).
"""
from __future__ import annotations

import argparse
import json
import logging
import time

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from ber.artifacts import provenance, read_table
from ber.eval.splits import is_holdout
from ber.paths import artifact_path, records_path, work_dir
from gap_check import s1_groups
from post_ops import GARBLE_SIM, LIST_A, MIN_LEN, NUDGE, REAL_MIN, classify, preselect, record_text, s1_vocab

log = logging.getLogger("france_kit")
K = 4_000_000_000


def stage2_pairs(scores: str, split: str, keep_s1: np.ndarray) -> pd.DataFrame:
    """Stage-2 pairs (p1 >= 0.002) of the given S1, read row group by row group."""
    f = pq.ParquetFile(artifact_path("scores", scores, split))
    cols = ["s1", "r", "p1", "pc"] + (["y"] if split == "train" else [])
    parts = []
    for g in range(f.num_row_groups):
        t = f.read_row_group(g, columns=cols).to_pandas()
        parts.append(t[(t.p1 >= 0.002) & np.isin(t.s1.to_numpy(), keep_s1)])
    return pd.concat(parts, ignore_index=True)


def attach_scores(d: pd.DataFrame, scores: str, split: str) -> pd.DataFrame:
    """p1 and pc of the given pairs (any blocking candidate), read row group by row group."""
    f = pq.ParquetFile(artifact_path("scores", scores, split))
    want = np.sort(d.s1.to_numpy() * K + d.r.to_numpy())
    parts = []
    for g in range(f.num_row_groups):
        t = f.read_row_group(g, columns=["s1", "r", "p1", "pc"]).to_pandas()
        k = t.s1.to_numpy() * K + t.r.to_numpy()
        parts.append(t[np.isin(k, want)])
    sc = pd.concat(parts, ignore_index=True)
    return d.merge(sc, on=["s1", "r"], how="left")


def rule_pairs(feats: str, scores: str, split: str, s1_set: np.ndarray, cty: pd.Series, vocab: dict) -> pd.DataFrame:
    """The rule populations over ALL blocking candidates (as post_ops.py --measure), with p1/pc."""
    d = preselect(feats, split, s1_set)
    d = profile(d, split, cty, vocab)
    d = d[d.op != ""].reset_index(drop=True)
    return attach_scores(d, scores, split)


def in_table(d: pd.DataFrame, pairs: pd.DataFrame) -> np.ndarray:
    key = np.sort(pairs.s1.to_numpy() * K + pairs.r.to_numpy())
    return np.isin(d.s1.to_numpy() * K + d.r.to_numpy(), key)


def raw_text(split: str, ids: np.ndarray) -> tuple[pd.Series, pd.Series]:
    t = pq.read_table(records_path(split), columns=["eid", "name", "address"])
    t = t.filter(pc.is_in(t["eid"], value_set=pa.array(ids)))
    eid = t["eid"].to_numpy()
    return (pd.Series(t["name"].to_numpy(zero_copy_only=False), index=eid),
            pd.Series(t["address"].to_numpy(zero_copy_only=False), index=eid))


def profile(d: pd.DataFrame, split: str, cty: pd.Series, vocab: dict) -> pd.DataFrame:
    ids = np.unique(np.r_[d.s1.to_numpy(), d.r.to_numpy()])
    names, keys = record_text(split, ids)
    d = classify(d.assign(cty=cty.reindex(d.s1).to_numpy()), names, keys, vocab)
    raw_n, raw_a = raw_text(split, ids)
    return d.assign(s1_name=raw_n.reindex(d.s1).to_numpy(), s1_address=raw_a.reindex(d.s1).to_numpy(),
                    r_name=raw_n.reindex(d.r).to_numpy(), r_address=raw_a.reindex(d.r).to_numpy(),
                    source=(d.r.to_numpy() // 1_000_000_000).astype(np.int8))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores", default="ameya-s2-v5all")
    ap.add_argument("--cands", default="ameya-cands-v5all-c2")
    ap.add_argument("--model", default="ameya-model-v5all-c2", help="decisions before the France rules (train + test)")
    ap.add_argument("--final", default="ameya-model-v5all-c2-ops2", help="final test decisions (after the rules)")
    ap.add_argument("--out", default="france-kit-v1")
    ap.add_argument("--feats", default="ameya-fx4", help="feature set whose -str group preselects the rule pairs")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    t0 = time.perf_counter()
    out = work_dir() / "kits" / args.out
    out.mkdir(parents=True, exist_ok=True)
    meta = provenance(inputs=vars(args))

    # France (test)
    tr_c = set(pc.unique(pq.read_table(records_path("train"), columns=["country"])["country"]).to_pylist())
    te_c = set(pc.unique(pq.read_table(records_path("test"), columns=["country"])["country"]).to_pylist())
    targets = te_c - tr_c
    cty_t, vocab_t = s1_vocab("test", targets)
    fr_s1 = np.sort(cty_t.index.to_numpy()[cty_t.isin(targets).to_numpy()])
    d = stage2_pairs(args.scores, "test", fr_s1)
    log.info("France: %d S1, %d stage-2 pairs (%.2f per S1)", fr_s1.size, len(d), len(d) / fr_s1.size)
    d["in_cands"] = in_table(d, read_table("candidates", args.cands, "test"))
    d["pred_model"] = in_table(d, read_table("matches", args.model, "test"))
    d["pred_final"] = in_table(d, read_table("matches", args.final, "test"))
    g = s1_groups("test").set_index("s1").n_core
    d = profile(d, "test", cty_t, vocab_t).assign(s1_group=lambda x: g.reindex(x.s1).to_numpy())
    d = d.drop(columns=["cty", "num_edit"])
    d.to_parquet(out / "france_pairs.parquet", compression="zstd")
    fr_ops = d.groupby("op").agg(pairs=("r", "size"), pred_model=("pred_model", "mean"), pred_final=("pred_final", "mean"))
    rf = rule_pairs(args.feats, args.scores, "test", fr_s1, cty_t, vocab_t).drop(columns=["cty", "num_edit"])
    rf["in_cands"] = in_table(rf, read_table("candidates", args.cands, "test"))
    rf["pred_model"] = in_table(rf, read_table("matches", args.model, "test"))
    rf["pred_final"] = in_table(rf, read_table("matches", args.final, "test"))
    rf.to_parquet(out / "france_rule_pairs.parquet", compression="zstd")
    fr_rule = rf.groupby("op").agg(pairs=("r", "size"), pred_model=("pred_model", "mean"), pred_final=("pred_final", "mean"))
    log.info("France kit written (%.0fs)", time.perf_counter() - t0)
    n_fr = len(d)
    del d

    # US/India holdout (train)
    cty_h, vocab_h = s1_vocab("train", tr_c)
    hold = np.sort(cty_h.index.to_numpy()[is_holdout(cty_h.index.to_numpy())])
    h = stage2_pairs(args.scores, "train", hold)
    log.info("holdout: %d S1, %d stage-2 pairs", hold.size, len(h))
    h["pred"] = in_table(h, read_table("matches", args.model, "train"))
    g = s1_groups("train").set_index("s1").n_core
    h = profile(h, "train", cty_h, vocab_h).assign(s1_group=lambda x: g.reindex(x.s1).to_numpy())
    h = h.rename(columns={"cty": "country"}).drop(columns=["num_edit"])
    h.to_parquet(out / "holdout_pairs.parquet", compression="zstd")
    h_ops = h.groupby(["op", "country"]).agg(pairs=("r", "size"), true=("y", "mean"), pred=("pred", "mean"))
    n_h = len(h)
    del h
    rh = rule_pairs(args.feats, args.scores, "train", hold, cty_h, vocab_h).rename(columns={"cty": "country"})
    rh = rh.drop(columns=["num_edit"])
    rh["pred"] = in_table(rh, read_table("matches", args.model, "train"))
    rh.to_parquet(out / "holdout_rule_pairs.parquet", compression="zstd")
    h_rule = rh.groupby(["op", "country"]).agg(pairs=("r", "size"), true=("y", "mean"), pred=("pred", "mean"),
                                                below_stage2=("p1", lambda x: float((x < 0.002).mean())))

    readme = f"""# France kit ({args.out})

Made by `experiments/ameya/model-v1/france_kit.py`. Inputs:
- scores `{args.scores}`;
- candidate set `{args.cands}`;
- decisions `{args.model}` (before the rules) and `{args.final}` (final).

## Files
- `france_pairs.parquet`: {n_fr:,} pairs, every stage-2 pair (p1 >= 0.002) of the {fr_s1.size:,} French S1.
- `holdout_pairs.parquet`: {n_h:,} pairs, the same for the {hold.size:,} US/India holdout S1, with the truth `y`.
- `france_rule_pairs.parquet` / `holdout_rule_pairs.parquet`: the rule populations (`op` != "") over **all**
  blocking candidates (`post_ops.py --measure`), including pairs below stage 2 (p1 < 0.002). Use these for truth
  rates.

**Selection bias warning.** On the stage-2 set (p1 >= 0.002), US/India stage 1 has already removed most false
look-alikes. Op B looks 12-43% true there but is 0.6-3.1% true over all candidates. France's stage 1, which has no
French word odds, removes far fewer. So never compare France's stage-2 profile shares with the holdout's stage-2 truth
rates. Use the `*_rule_pairs` files, or the full candidate set, for rule decisions.

## Columns
- `s1`, `r`: integer ids (source * 1e9 + number); `source` 2/3.
- `p1`: stage-1 score; `pc`: calibrated stage-2 score.
- France only:
  - `in_cands`: in the final candidate file;
  - `pred_model`: the model's decision;
  - `pred_final`: after France rules v2.
- Holdout only: `y` (truth), `pred` (the model's decision), `country`.
- `s1_group`: S1 sharing the S1's core name (country, split).
- Edit profile (`post_ops.classify`, at the S1's address = same first house number and street word equal or within a
  typo):
  - `kind`: swap / add / same / acr / "";
  - `pos`: before_legal, after_legal, end_moved, end_same_slot, inner, end, legal_dropped;
  - `added` / `dropped`: the words;
  - `same_num`, `street_typo`;
  - `num_kind`: minus / sub / swap / indel / "";
  - `op`: the rule population. B = a real word swapped into the slot; A = drop + list append; APP = list append;
    ACR = acronym; NUM = same name with a house-number edit; CODE = short-code typo; "" = none.
- Raw `s1_name`, `s1_address`, `r_name`, `r_address`.

## Definitions
- List words: {sorted(LIST_A)}.
- Look-alike nudge set (record number minus S1 number): {sorted(NUDGE)}.
- A "real" added word is used in >= {REAL_MIN} S1 names of the country.
- Garble: Indel similarity >= {GARBLE_SIM} to the dropped word.
- B needs an added word of length >= {MIN_LEN}.

## Rule populations
France (share predicted before / after the rules):
```
{fr_ops.round(4).to_string()}
```

Holdout, stage-2 set (truth rate and share predicted; biased, see the warning):
```
{h_ops.round(4).to_string()}
```

Holdout, all blocking candidates (unbiased; `below_stage2` = share with p1 < 0.002):
```
{h_rule.round(4).to_string()}
```

France, all blocking candidates (share predicted before / after the rules):
```
{fr_rule.round(4).to_string()}
```

Provenance: {json.dumps(meta, default=str)}
"""
    (out / "README.md").write_text(readme, encoding="utf-8")
    log.info("done: %s (%.0fs)", out, time.perf_counter() - t0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
