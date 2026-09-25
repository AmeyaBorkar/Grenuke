# Decision: france-generator-ops-and-final-fit

- **Date (IST):** 2026-09-26 04:17
- **Author:** ameya
- **Status:** proposed. The France rules are gated by leaderboard probes (`2026-09-26-probe-v4-frab` vs `2026-09-26-v4`); the captain uploads and decides the final
- **Affects:** model (`experiments/ameya/model-v1`: `post_ops.py` new; `s1.py`/`s2.py` gain `--all`), blocking tokenizer (`ber.block.text`, v5 commits), the submission

## Context

`experiments/ameya/model-v1/ANALYSIS_v4.md`, with two agent reports: the generator catalogue, and the leave-one-country-out anatomy.

The organisers' generator edits one S1 name word at the S1's own address (same house number and street word) in two ways:
- **Op A, true-copy noise.** One word is dropped and a list word appended after the legal form or at the end. The English list is center/services/service/partners; the French list is fils/cie/services/associés/groupe/développement/france. US/India: 98–99.8% true.
- **Op B, look-alike.** Another real word goes in the dropped word's slot. US/India holdout: 5,364 pairs, 0.6% true.

The models know this for US/India through the label word odds. France has only the label-free proxy odds, which flag look-alike words by moved house numbers, and op B keeps the number:
- v4 predicts 17,088 op-B records in France (65.9 per 1000 S1; median pc 0.989);
- it leaves 4,746 op-A records unpredicted.

## Options considered

1. **Rules for countries without training labels (`post_ops.py`).** Drop predicted op-B pairs; add op-A pairs that meet all of: argmax owner, in the candidate set, the record not predicted elsewhere.
2. **Position features** (new word in the slot vs after the legal form) with a retrain. This is cleaner, but the US/India models already separate A/B through the word odds, so the new feature may carry little weight, and it costs a full stage 1/2 rerun.
3. **Synthetic French training pairs from the generator catalogue.** About a day of work; it would have to encode the same A/B rules.
4. **Nothing.** v4 as is.

Also decided here:
- **v5.** v4 plus French address normalisation (department → region, R → rue, articles, bis/ter) and EI as a legal form.
- **The final fit on all of train (`--all`).** The holdout becomes a fourth out-of-fold group in stages 1 and 2.

## Decision

- **Option 1 for France**, now, as a pipeline step after `decide.py`. Option 2 later only if time allows.
- **v5 + rules + `--all` is the final-candidate recipe**, if the probes agree:
  - `ameya-model-v5all` → `post_ops.py` → `2026-09-26-v5all-ops`.

**Gates**

| check | result |
|---|---|
| op-B drop applied to the US/India holdout (predicted pairs it would remove) | 27 pairs, 93% true; macro F0.5 −0.000003. The rules therefore apply only to countries without labels |
| op-B population truth on the holdout | 5,364 pairs, 0.6% true |
| op-A population truth on the holdout (after the legal form / at the end) | US 99.8–99.9%, India 98.3–98.6% |
| France forecast (per-S1 arithmetic, share 0.14975) | +0.00248 (drop) + ~0.0002 (add) = **+0.0027** on the leaderboard if France follows the US/India rates; −0.0017 in the worst case |
| v5 vs v4, holdout | 0.99013 vs 0.99015 (tie); France +4 op-A and +9 op-B predictions per 1000 S1 (the rules remove the latter) |
| v5all vs v5, holdout | stage 1 0.98695 vs 0.98693; DP 0.99016 vs 0.99013, Δ +0.00002 [−0.00003, +0.00007] (tie, as expected: the holdout sees one 75% model, test the mean of four) |
| leaderboard probe | pending: `probe-v4-frab` minus `v4` is the France rules alone |

## Consequences (what changes, what we give up, how we'll know it was right)

- France predictions change for about 8% of French S1. US/India predictions are untouched by the rules.
- The rules are hand-written from label evidence and label-free counts. Documented lexicons: the two list-A word lists; the thresholds real ≥ 20 S1 names, garble similarity ≥ 0.5, length ≥ 4.
- A country without labels other than France would get the same treatment. Its list-A words would need adding, or op A is simply not applied.
- **Right if** `probe-v4-frab` beats `v4` by about +0.0025.
- **Wrong if** it loses (about −0.001). Then French in-slot swaps are true copies and the rules are dropped.

Commands:
```
python experiments/ameya/model-v1/post_ops.py --matches ameya-model-v4 --scores ameya-s2-v4 --cands ameya-cands-v4 --feats ameya-fx3 --tag ameya-model-v4ops
python experiments/ameya/model-v1/post_ops.py --matches ameya-model-v5 --scores ameya-s2-v5 --cands ameya-cands-v5 --feats ameya-fx4 --tag ameya-model-v5ops
python experiments/ameya/model-v1/s1.py --feats ameya-fx4 --tag ameya-s1-v5all --groups str,cx,lo0,lg --drop leg__r_only_bits,leg__s1_only_bits --all
python experiments/ameya/model-v1/s2.py --feats ameya-fx4 --s1 ameya-s1-v5all --tag ameya-s2-v5all --groups str,cx,lo0,lg,ce --cluster --extra leg__rel,leg__n_s1,leg__n_r,leg__inter,leg__s1_only,leg__r_only,ce__logit --all
python experiments/ameya/model-v1/decide.py --scores ameya-s2-v5all --col pc --tag ameya-model-v5all --base ameya-model-v5
python experiments/ameya/model-v1/cands_final.py --s1 ameya-s1-v5all --tag ameya-cands-v5all
python experiments/ameya/model-v1/post_ops.py --matches ameya-model-v5all --scores ameya-s2-v5all --cands ameya-cands-v5all --feats ameya-fx4 --tag ameya-model-v5all-ops
```
