# Artifact request: integration machine → Bakshi session (Tracks A and B + the package blocker)

Raised 2026-09-27 ~01:00 IST from branch `bakshi/opus-exec`, base `2023ffbae034e274aab5cb262c982d6fef762e5c`.
Everything asked for here is a file copy or a read-only script run. No new GPU time, no new rental, no upload.

---

**Context.** I'm the agent session working as Bakshi, on Bakshi's Windows laptop (16 GB RAM, RTX 2050 4 GB).
It has the full repo and the raw dataset, but **no v7 artifacts at all**: `work/` here holds only dev-scale
and old `bakshi-block-*` tags — no scores, no matches, no `ameya-fx5-*` features — and no torch/transformers.
So Tracks A and B cannot execute here without the inputs below.

**Read-only, please don't disturb the queue.** `v7nst2` / `v7mst` / `v7s` are reported running on the
integration machine. Nothing here asks you to stop, restart, re-tag or overwrite any of it.

## Already verified locally — don't redo this

- `matching_resultsv7nst.tsv`: sha256 `659f5169cabbb2a3de2cb8580b614bbff718ea62d5b1fb4497243b50fcc34533`,
  97,909,982 bytes. Matches the `sub04` record exactly.
- It passes every hard check against the full test sources: **1,732,544 rows** (exactly one per test S1),
  5,856,096 pairs, 100,137 empty rows, 3.3801 per S1, **0** records claimed by more than one S1,
  **0** cross-country pairs, all 5.86M target IDs present in `test_source2/3.tsv`.
  France 259,452 S1 / 871,242 pairs; India 809,986 / 2,735,918; US 663,106 / 2,248,936.
- Against `candidate_pairsv6all.tsv`: **3,790 matched pairs over 3,725 S1 fall outside the candidate set.**
  Reading `acr_join.py`, that is exactly its `new_c`, so the v6all candidate file cannot be shipped with v7nst.

## Preferred: read-only access to the integration machine

A shell there (or an agent session on a `bakshi/*` branch) unblocks all of the below **plus** the Track A
rebuilds and the Track B stage-2 fit, and nothing large has to move. I'd need only three paths: the repo
root, `BER_WORK_DIR`, and the box/scratchpad dir.

Otherwise, the minimal list follows, in priority order.

---

## 1. BLOCKER — the v7nst candidate file

```
submissions/files/2026-09-27-v7nst-s3-ops3a-c2/candidate_pairs.tsv
expected sha256 510a33ea18a7ab4cd2ec5ad4e8ad113bbc4fd4f46818941c00f29852f3e258aa
```

Please send the file (~105 MB, team drive is fine). This is the single thing that makes a complete
submission package impossible right now: the matching file on its own fails the matches-⊆-candidates
requirement, and synthesising a candidate list from the final matches would not represent what the
pipeline actually considered.

**Prediction to confirm:** it should contain **6,410,247** pairs = v6all's 6,406,457 + acr_join's 3,790.
If it doesn't, the `--cands` input wasn't `ameya-cands-v6all-c2` and I need to know that before packaging.

## 2. Track A — validate the three probes without moving 600 MB

The probes are already packaged, so instead of copying them, please run my auditor **there**. It's
self-contained (numpy / pandas / pyarrow only) and lives on `bakshi/opus-exec` at
`experiments/bakshi/final-package/audit_matching.py`:

```bash
for P in v7nst-s3-ops3a-c2 probe-v7nst-fr080r probe-v7nst-fr090r probe-v7nst-fr095r; do
  python experiments/bakshi/final-package/audit_matching.py \
    --matching "submissions/files/2026-09-27-$P/matching_results.tsv" \
    --candidate "submissions/files/2026-09-27-$P/candidate_pairs.tsv" \
    --test-dir  "$BER_DATA_DIR/test" \
    --json "/tmp/audit_$P.json"
done
```

(Adjust the directory names if they differ — I'm taking them from the takeover brief and haven't confirmed
they exist.) Send back the four JSONs (a few KB each) and the sha256 of all eight TSVs. That gives me row
coverage, owner conflicts, cross-country pairs, target existence, and — the check the official validator
only *warns* about — matches ⊆ candidates, per probe.

Two things only that machine can answer:

**(a) Are the US and India final pair sets byte-identical to v7nst's, for each probe?**
The chain should leave them untouched, but I want it asserted rather than inferred from the script name.
If they're identical, each probe's public delta isolates France cleanly, which is the whole point of the
comparison.

**(b) For the pairs each probe removes from the *final* output, please report the `pc` distribution and the
`post_ops` operation family.** This is the most decision-relevant number in the whole request and it's a
cheap groupby. The reported counts are fr080r 3,629 pairs / 3,601 S1; fr090r 7,353 / 7,190;
fr095r 11,101 / 10,663 — but a count alone can't tell us the sign of the effect.

Specifically: a histogram of `pc` for the removed pairs, and how many fall in op `A`/`APP`/`ACR`
(97–99.8% true in US/India — removing those is a *mistake*), op `B` (0–1.2% true — removing those is
right), or no rule family at all. I expect mostly "no family", because `fr_threshold` cuts before the
rules and the rules re-add their true copies — and that expectation being confirmed *is* the useful
answer, because it tells us the removals are exactly the pairs no label-free rule can adjudicate.
Needs the `fx5-str` features, which I don't have here.

## 3. Track B — the cached logits (small, and enough for me to do all the screening here)

From the box scratchpad, each directory with `ce_train.parquet`, `ce_test.parquet`, `config.json`:

| dir | what |
|---|---|
| `out_e5l/` | e5-large, 1 epoch, seed 26 |
| `out_e5l2/` | e5-large, 2 epochs, seed 7 |
| `out_bge/` | bge-reranker-v2-m3 — **Track B is dead without this one** |
| `out_cem2/` | the existing production z-mean (see below) |
| `out_q15/` | Qwen2.5-1.5B, **only if it already finished**; skip otherwise |

plus:

- `band_train.parquet` and `band_test.parquet` (`s1, r, row, p1` [, `fold, y`]).
  `band_train`'s `fold` column is essential — I need it to fit the z-moments on training folds only.
- the `rule_pop.py` output parquet (`s1, r, op, y`). I can't build this here: it calls
  `preselect("ameya-fx5", "test", ...)`, i.e. it needs the fx5 `str` feature group.

Order of 100–300 MB total. With it I can do all of the screening locally tonight:

1. **Reproduce `out_cem2` exactly** from `out_e5l` + `out_e5l2` via `zmean_ce.py`. If it comes out
   bit-identical, my copies and my tooling are provably aligned with production *before* I change
   anything. If it doesn't, I need to know why before trusting any blend I build.
2. Build the **50/50 E5-family / BGE** blend — and only then, if the evidence and the clock justify it,
   one BGE-heavy arm. Not a weight sweep.
3. Verify row alignment against the band, no missing or duplicate rows, finite values, nonzero standard
   deviations, and report coverage alongside every AUC.
4. Score every arm on the rule populations with `sklearn.metrics.roc_auc_score` on common finite rows.
   **Note a real caveat:** `ce_rule_auc.py`'s own `auc()` ranks with `np.argsort` and does **not** average
   tied scores, which biases it for saturated or rounded logits. I'll report both numbers so they stay
   comparable with the 0.803 / 0.792 / 0.806 figures in issue #45.

**What I cannot do here:** the downstream `ce_import.py` → `s2.py --pseudo` → `stage3.py` → `decide.py` →
`post_ops.py` → `acr_join.py` chain. Stage 2 peaks at ~19 GB and this laptop has 16 GB. So if a blend
screens well I'll send back the blend directory and an exact command list, and it has to run there — under
a **Bakshi-owned feature-bundle tag**, never overwriting `ameya-fx5-*`.

## 4. Two small things for the package (not Track A/B)

**(a)** From the machine that actually produced the v7nst logits:

```bash
pip freeze | grep -E "^(torch|transformers|tokenizers|safetensors|huggingface-hub)=="
python -V && nvcc --version | tail -1
```

The whole CPU stack is already pinned and verified. I deliberately left these two unpinned rather than
guess them from a laptop that has neither installed.

**(b)** The portal's **actual** remaining upload quota for Sunday and its reset time, read from the portal.
I won't plan slots against an inferred number, and I won't spend a slot to discover how the accounting works.

---

## Priority, if only some of it is possible

1. **§1** the v7nst `candidate_pairs.tsv` — without it there is no valid final package at all.
2. **§3** `out_bge` + `out_e5l` + `out_e5l2` + `out_cem2` + band files + `rule_pop` — Track B needs `out_bge`.
3. **§2(b)** the removed-pair `pc` / operation breakdown — decides Track A's sign before a slot is spent.
4. **§2** the four audit JSONs and the eight hashes.
5. **§4** the torch pins and the quota.
