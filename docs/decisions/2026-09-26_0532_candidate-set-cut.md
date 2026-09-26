# Decision: candidate-set-cut

- **Date (IST):** 2026-09-26 05:32
- **Author:** ameya
- **Status:** accepted (holdout tie; the captain decides which package to upload)
- **Affects:**
  - the final candidate file: `experiments/ameya/model-v1/cands_final.py`, `common.candidate_mask`;
  - the decision: `decide.py --p-cand/--top-r`;
  - the submission.

## Context

The organisers added a ranking rule: `candidate_pairs.tsv` is part of the final submission. They review it and the code that produces it, and "the approach that generates a smaller candidate set per Source 1 entity will be ranked higher in the final evaluation beyond the public/private leaderboard".
- Our candidate file is the stage-2 input: blocking (34 per S1) → stage-0 filter → stage 1 → p1 ≥ 0.002. That is 4.68 pairs per test S1 (France 5.56).
- The predictions are 3.37 per S1.

## Options considered

`cand_size.py`; holdout F0.5 of the v5all predictions restricted to the kept pairs:

| cut (on top of p0 ≥ tau0) | holdout pairs/S1 | holdout F0.5 | test pairs/S1 |
|---|---|---|---|
| p1 ≥ 0.002 (now) | 4.593 | 0.99016 | 4.682 |
| p1 ≥ 0.02 | 3.928 | 0.99016 | 4.050 |
| the record's top 2 S1 by p1 | 3.758 | 0.99016 | 3.990 |
| **p1 ≥ 0.02 and the record's top 2 S1** | **3.592** | **0.99016** | **3.702** |
| p1 ≥ 0.05 and the record's top 2 S1 | 3.533 | 0.99014 | 3.607 |
| the record's top 1 S1 | 3.606 | 0.99010 | 3.795 |
| the S1's top 6 records | 4.157 | 0.98877 | 4.233 |

- A per-S1 top k is the wrong shape: true sets reach 11 records.
- A per-record cut matches the argmax ownership: a record's lower-ranked S1 are almost never predicted.

## Decision

- **The candidate set is p0 ≥ tau0, p1 ≥ 0.02 and the pair among its record's top 2 S1 by p1** (ties: lower S1 id). `common.candidate_mask` implements it for both `cands_final.py` and `decide.py`.
- Only these pairs can be owned or predicted, so the matching model's inference input is exactly the candidate file.

**Gate** (paired bootstrap, `decide.py --base ameya-model-v5all`): holdout 0.990156 vs 0.990159, Δ −0.000003 [−0.000015, +0.000011]. A tie that does not add a component; the reason is the organisers' size rule.

| | v5all + rules | v5all + rules, cut (`2026-09-26-v5all-ops-c2`) |
|---|---|---|
| candidates per test S1 (US / India / France) | 4.68 (4.55 / 4.51 / 5.56) | **3.70 (3.66 / 3.61 / 4.09)** |
| `candidate_pairs.tsv` | 8.11M pairs, 127 MB | 6.41M pairs, 105 MB |
| test predictions | 5,831,529 | 5,830,819 (726 dropped, 16 added) |
| France rules | 18,434 op-B dropped / 6,086 op-A added | 18,406 / 6,086 |
| validator | PASS | PASS; matching sha256 `482caa7b…`, candidates `a27e8679…` |

## Consequences (what changes, what we give up, how we'll know it was right)

- The candidate file shrinks by 21% with the matching unchanged. 3.4 per S1, the predictions themselves, is the floor for this model.
- We give up 0.7 points of pair recall in the set (0.98927 → 0.98198) and 0.0022 of oracle F0.5 (0.99676 → 0.99452). That is headroom the current decision layer does not use.
- A future model that predicts lower-ranked S1 of a record (joint decoding, stage 3) must be measured with the cut.

Commands:
```
python experiments/ameya/model-v1/decide.py --scores ameya-s2-v5all --col pc --tag ameya-model-v5all-c2 --base ameya-model-v5all --p-cand 0.02 --top-r 2
python experiments/ameya/model-v1/cands_final.py --s1 ameya-s1-v5all --tag ameya-cands-v5all-c2 --p-cand 0.02 --top-r 2
python experiments/ameya/model-v1/post_ops.py --matches ameya-model-v5all-c2 --scores ameya-s2-v5all --cands ameya-cands-v5all-c2 --feats ameya-fx4 --tag ameya-model-v5all-c2-ops
bash package_dir.sh ameya-model-v5all-c2-ops ameya-cands-v5all-c2 2026-09-26-v5all-ops-c2
```
