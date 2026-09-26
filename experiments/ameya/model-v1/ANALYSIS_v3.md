# Model v3 on the leaderboard: where the 0.009 gap comes from, and models v3ce, v4, v5 (26 Sep, night)

Model v3 scores **0.98882** on the shared holdout and **0.97961** on the public leaderboard (v2: 0.98436 → 0.97608).
This note finds where the gap comes from and what fixes it. Holdout numbers are on the full shared holdout (549,699 S1,
folds 0–4); test numbers are label-free diagnostics on the 1,732,544 test S1.

Scripts: `analysis.py` (holdout outcomes), `loco.py` (leave one country out), `feats_lo_proxy.py` (label-free look-alike
odds), `probe.py` (leaderboard probes); throwaway checks in the session scratchpad.

## TL;DR

- **US and India on test behave exactly like the holdout.** Predicted records per S1, the empty share, the score
  profile of the predictions and the rate of look-alike patterns per S1 all match within 1–2%. The test's extra
  look-alike distractors (2× per S1) are rejected at the holdout rate.
- **So the gap is France** (15% of test S1): 0.97961 = 0.85 × 0.9888 + 0.15 × F_France gives **F_France ≈ 0.93**,
  against 0.989 for US/India.
- **France has about 0.18 false positives per S1.** US and India have exactly 3.46 true matches per S1 on the
  holdout, so the generator almost certainly gives France the same. Yet France predicts 3.54 per S1 (holdout 3.36)
  and leaves 4.4% of S1 empty (5.6% are true singletons).
- **Cause 1, verified: the legal-form bitmasks.** French forms (SAS, SASU, SARL, EURL, SNC, SCI, SA) live in bits
  12–19, which never occur in train, so every French value sits beyond the largest training split. French
  look-alikes that add or change the legal form and move the house number ("Demployeurs Patrimoine SAS 176" →
  "… SASU 177") get a mean stage-1 score of 0.456; with the bits zeroed, 0.027. 12.2k such pairs are predicted in
  France: 9× the US/India rate per prediction.
- **Cause 2: look-alike words that never occur in train.** The `lo` table gives unseen words 0 (neutral), so
  "Participations", "Développement", "Groupe", "Amicale" look like noise words. Leave-one-country-out shows how much
  this matters: a US-only model scores India at 0.961, and **0.882 with India's words unseen**.
- **France is 4× as uncertain as the holdout on both sides:** 9% of its predicted pairs are below pc 0.99 (holdout
  3%), and the rejected pairs it scores 0.3–0.7 are 4× as dense. A sample of those rejected pairs is mostly
  look-alikes (number moved + added business word, swapped descriptor or changed legal form).

## 1. Test vs holdout, per country (label-free)

| | holdout US | holdout India | test US | test India | test France |
|---|---|---|---|---|---|
| predicted records per S1 | 3.357 | 3.356 | 3.380 | 3.358 | **3.539** |
| S1 left empty | 5.8% | 5.7% | 5.8% | 5.8% | **4.4%** |
| predicted pairs with pc < 0.99 | 2.8% | 3.2% | 3.0% | 3.4% | **9.0%** |
| of which in [0.7, 0.9) | 0.51% | 0.57% | 0.57% | 0.61% | **2.72%** |
| "number nudged + extra word" among predictions | 0.27% | 0.68% | 0.28% | 0.67% | 1.09% |
| close look-alike-signature pairs per S1 (candidates) | 0.42 | 0.51 | 0.83 | 0.82 | 1.62 |
| of which predicted | 1.45% | 2.83% | 0.78% | 1.78% | 2.31% |

- The test has about twice the look-alike-signature candidates per S1, yet the number predicted per S1 is the same as
  on the holdout (India 0.0146 vs 0.0145). The model rejects the extra distractors.
- The holdout-cell estimate of false positives (holdout precision per pc bin × number relation × legal relation,
  applied to the test predictions) is 0.0018 per predicted pair for US/India test (holdout 0.0016–0.0018) and 0.0067
  for France. That assumes France is calibrated like the holdout, which the size mismatch below says it is not.

**Predicted set sizes** (share of S1):

| size | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| holdout truth | 5.58 | 5.40 | 17.05 | 24.08 | 21.88 | 14.67 | 7.41 | 2.90 |
| holdout predicted | 5.74 | 6.20 | 18.22 | 24.60 | 21.37 | 13.79 | 6.73 | 2.49 |
| France predicted (S1 with stage-2 candidates) | **4.18** | 5.75 | 16.48 | 23.91 | 22.33 | 15.15 | 7.86 | 3.11 |

## 2. France: what the model gets wrong

**Predicted pairs by pattern** (per S1; "uncertain" = pc < 0.99; holdout precision in brackets):

| pattern | France per S1 | France uncertain | holdout per S1 | holdout uncertain (precision) |
|---|---|---|---|---|
| A: number moved + legal form added/changed | 0.047 | **93%** | 0.021 | 32% (0.94) |
| B: number moved + extra name word | 0.047 | **90%** | 0.094 | 11% (0.96) |
| C: number moved only | 0.037 | 33% | 0.293 | 6% (0.95) |
| D: same number + extra/swapped word | 0.793 | 16% | 0.669 | 3% (0.96) |
| E: no number on one side | 0.276 | 22% | 0.371 | 7% (0.94) |
| F: clean | 2.348 | 1.3% | 1.910 | 0.9% (0.94) |

- France's true records seldom move the house number (pattern C is 8× rarer per S1 than on the holdout, and only
  0.2% of France's confident predictions have a nudged number, against 0.7–2.7% in US/India). So in France a moved
  number is much stronger look-alike evidence than the model learned from US/India.
- Typical false positives in the 0.7–0.9 band: "Demployeurs Patrimoine SAS | 176 Rue Pierre Clostermann" →
  "Demployeurs Patrimoine SASU | 177 …"; "Collège de la François | 11 Rue Georges Mandel" → "… S.A.S | 20 …";
  "Aines (France) Ecole SAS | 41 Impasse Saint-Louis" → "AINES (FRANCE) CULTURELLE SAS | 43 …";
  "Bien Comite (France) SA | 12 Rue Richelieu" → "Bien Comite (France) Groupe SA | 13 …".

**The legal-form bitmask test.** 59k French pairs with p1 ≥ 0.05 re-scored with the v3 stage-1 models:

| | pairs | p1 as is | bits zeroed | French forms mapped to English bits |
|---|---|---|---|---|
| legal form added/changed + number moved | 30,518 | 0.456 (43% > 0.5) | 0.027 (0.8%) | 0.232 (21%) |
| everything else | 28,755 | 0.807 | 0.806 | 0.808 |

## 3. Leave one country out (gate G13, dev kit, stage-1 model, India holdout)

| training | features | India F0.5 | log-loss |
|---|---|---|---|
| US + India | all | 0.98346 | 0.0098 |
| US + India | without the legal bitmasks | 0.98286 | 0.0101 |
| US + India | all, India's words unseen (lo = 0) | 0.95997 | 0.0388 |
| US only | all | 0.96106 | 0.0241 |
| US only | without the legal bitmasks | 0.95996 | 0.0244 |
| US only | without the lo group | 0.94180 | 0.0359 |
| US only | all, India's words unseen (lo = 0) | **0.88235** | 0.0861 |

- An unseen country costs 0.022 even when its words are known, and 0.10 when they are not, which is France's case.
- The bitmasks barely matter for India: its forms (pvt, ltd, llp, opc) sit between the US bits. French bits sit
  above every training value.

**Self-training does not rescue it.** Pseudo-labels from the US-only model on India's pairs (all folds, labels never
read; positive: p ≥ 0.97 and the record's argmax; negative: p ≤ 0.03), then retrain on US + pseudo-India:

| India's words | US only | + 1 round | + 2 rounds |
|---|---|---|---|
| known | 0.96106 | 0.96370 | 0.96479 |
| unseen (France's case) | 0.88235 | 0.85120 | **0.83075** |

With unseen words the confident pseudo-positives include look-alikes, and each round teaches the model to accept more
of them (confirmation bias). The look-alike odds must be restored first; self-training can then add a little.

## 4. Label-free look-alike odds for a country without labels (groups `lop`, `lo0`)

`feats_lo_proxy.py`: look-alikes move the first house number (nudge or other) and true records seldom do, so a word's
**moved-number share** among the close pairs where it is the extra record word (or the missing S1 word), counted in its
own country without labels, says how look-alike it is. A decreasing isotonic fit on US/India words maps the share to
the label-odds scale (`lo_proxy_map.json`); rare words are shrunk toward the neutral share and words below 30 close
pairs get exactly 0.

| moved share | 0.05 | 0.2 | 0.45 (neutral) | 0.5 | 0.8 | 0.95 | 0.98 |
|---|---|---|---|---|---|---|---|
| mapped odds (extra word) | +2.2 | +1.4 | 0 | −0.2 | −4.8 | −5.0 | about −7.5 |

- On US/India words the mapped odds follow the label odds with Spearman 0.74 (US) and 0.40 (India). Without labels
  it finds the look-alike vocabulary: US midtown/uptown/holdings/group/north/valley −7.3 to −7.8; India industries,
  enterprises, exports, group −4.8; benign formerly/fka/doing/as +1.4 to +2.2.
- **France:** groupe, holding, participations, développement, distribution, international, france −4.8 (moved share
  0.79–0.90 over 59k–98k pairs each); descriptors (club, école, amicale, comité, union, collège, sportive) −2.1 to −3.8;
  benign suffixes (services, associés, fils, cie) +0.2. The misapplied US/India odds shrink: centre −5.3 → −2.5,
  union −5.4 → −3.8.
- An earlier version inverted a two-class mixture with train's P(moved | false). France's close pairs are 75%
  moved (US/India 73%), above that rate, so its prior saturated and every French word came out at 0. The share →
  odds map has no prior to saturate.

**Leave one country out with the proxy** (India's words replaced by India's own label-free odds):

| model (stage 1, dev kit) | India F0.5 |
|---|---|
| US + India, label odds | 0.98346 |
| US + India, label odds, India fed the proxy | 0.98240 |
| US + India, trained on the proxy | 0.98309 |
| US only, label odds (India's words known) | 0.96106 |
| **US only, label odds, India fed the proxy** | **0.95984** |
| US only, trained on the proxy | 0.93679 |
| US only, India's words unseen | 0.88235 |

So the models keep the label odds where labels exist and a country without labels gets the proxy: group `lo0`
(`lo_mix.py`) = `lo` with the "no statistics" value written as exactly 0 (it was −1.94e-16 on train and the holdout,
0.0 on test: audit finding 3) plus `lop` for France.

## 5. Model v3 + cross-encoder (G10)

The cross-encoder chain (multilingual-e5-small, MIT, out of fold on the p1 band [0.02, 0.99]) as a stage-2 feature:

| | v3 | v3 + CE (`ameya-model-v3ce`) |
|---|---|---|
| holdout macro F0.5 | 0.98882 | **0.99021** (Δ +0.00140 [0.00131, 0.00148]) |
| India / US | 0.9887 / 0.9889 | 0.9905 / 0.9900 |
| precision / recall | 0.99833 / 0.96893 | 0.99868 / 0.97221 |
| singleton F0.5 | 0.99126 | **0.99742** |
| stage-2 early-stopping log-loss | 0.0438–0.0445 | 0.0389 |
| test France: predicted per S1 / empty | 3.539 / 4.4% | **3.470 / 5.1%** |
| test US / India: predicted per S1 | 3.380 / 3.358 | 3.386 / 3.370 |

- The holdout gain is below the +0.003 bar for heavy components (G10), but the cross-encoder moves France toward the
  US/India profile, so the leaderboard gain should be larger than +0.0014.
- Packaged: `submissions/files/2026-09-26-v3ce/` (validator PASS; candidate file = the stage-2 input set).

## 6. Candidate set and identical duplicates

- **The candidate file was the wrong set.** The README asks for "the exact set of records you feed into your matching
  model for inference … the last [filtering stage]". Ours was the raw blocking output (34 per test S1, 781 MB), while
  stage 0 filters it and stage 2 scores only p0 ≥ tau0 and p1 ≥ 0.002. `cands_final.py` writes that stage-2 input set:

  | set | per test S1 (US / India / France) | TSV | holdout pair recall | oracle F0.5 | predictions outside |
  |---|---|---|---|---|---|
  | blocking output (was) | 33.99 (33.20 / 34.62 / 34.08) | 781 MB | 0.98992 | 0.99697 | 0 |
  | **stage-2 input (now)** | **4.75 (4.49 / 4.50 / 6.21)** | **129 MB** | 0.98926 | 0.99676 | 0 |

- Keeping each record's best 1–2 S1 only would cost recall ceiling (top-2: 0.9825) for 20% fewer pairs; not worth it
  unless a size-based ranking is confirmed. Nothing public says it is: the only tie-break is submission time.
- **Identical duplicates need nothing.** Exact duplicates (raw name + address + country) are always the same S1's
  records (43,910 of 43,910 train groups) and v3 already predicts them together (9 split groups of 10,827 on the
  holdout; completing them: +0.0000012). After casefolding, the truth splits 4,389 groups across different S1 (common
  names with an empty address), so the truth does not list content-identical records together.

## 7. Pipeline audit: every finding and what we do

| # | finding | evidence | status |
|---|---|---|---|
| 1 | French look-alike words have no odds; some US/India odds mislead French descriptors | participations/développement/groupe pairs 71–72% nudged at pc ~0.36; centre/union/collège −4.7 to −5.4 yet 98% same number | **v4**: `lo0` (proxy for France) |
| 2 | French legal forms are bits ≥ 4096 (0.08% of train rows, 6–8% of test) | "changed" p1 0.281 → 0.038 with English analogs | **v4**: bitmasks dropped from stages 0–2 |
| 3 | unseen words: −1.94e-16 on train and holdout, 0.0 on test (every country) | 11–14% of test predicted pairs, 0% on the holdout; adversarial AUC 0.95 | **v4**: exact zeros in `lo0` |
| 4 | rarity/rival counts depend on pool size (test US has half train US's S1) | KS 0.10–0.13; US predicts +0.022 per S1 over the holdout | open: −0.0002 to −0.0004 |
| 5 | French address normalization: department vs region, articles in key slots, "R" dropped, first-name street keys | a third of French true pairs carry 1–3 unmatched region/department words; 4.1% of French predictions absent from the S1's token list (US/India ~1%) | v5 candidate (full rebuild) |
| 6 | stage-2 cluster features amplify accepted look-alikes | France 3.70 pairs with p1 > 0.5 per S1 vs 3.38–3.41 | v5 candidate |
| 7 | candidate file = blocking output | see section 6 | **done** |

Checked and consistent: row alignment across all 125.7M train+test rows; the scoring protocol (holdout and test both
use the mean of the three group models); thresholds, tau0, P_MIN, isotonic; the write stage; US/India text statistics
(train vs test within 3 decimals). Bakshi's C3 normalization is not used by v3.

## 8. Research: what we take and what we skip

From the research pass (papers, Kaggle write-ups, model cards; full notes in the session scratchpad):

- **Operational (most urgent).** The competition's submission-round page gives the window as 25 Sep 03:30 UTC → 27 Sep
  15:30 UTC, which closes at **21:00 IST on Sunday**, not 23:59 (the main timeline says 23:59 for the hackathon stage,
  which also covers the zip and document). The same page ranks by "the maximum score of the submission and submission
  time", and the private leaderboard is "based on your final solution submission". Plan the last upload well before
  21:00 IST and make it the model we want ranked. A human should confirm this in the logged-in portal.
- **Domain adaptation.** Self-training fails through confirmation bias when the model is confidently wrong on the
  target (our India test: 0.882 → 0.831). What works for gradient-boosted pair features is filling in the target's
  missing statistics (our proxy odds) and keeping features country-agnostic, not adversarial alignment.
- **Label shift (2× distractors).** Saerens EM / BBSE on the hard subset is the textbook correction. Our test US/India
  diagnostics show no over-acceptance (predicted per S1 and look-alike acceptance per S1 match the holdout), so there
  is nothing to correct there now; France's shift is covariate shift, not prior shift.
- **Decision.** A separate "this S1 has no match" model feeding the DP's empty option (Instacart "None" practice) is
  the remaining decision-level idea: +0.0005–0.002 estimated. The cross-encoder already raised singleton F0.5 from
  0.9913 to 0.9974, so its room is smaller now.
- **Cross-encoders.** Licences checked: multilingual-e5 (MIT), mdeberta-v3 (MIT), LaBSE (Apache-2.0),
  bge-reranker-v2-m3 (Apache-2.0), Qwen2.5-0.5B/1.5B and Qwen3-0.6B/1.7B (Apache-2.0) are allowed; Qwen2.5-3B
  ("other") and jina-reranker-v2 (CC-BY-NC) are not. A diff-aware input (the extra words and the number relation
  written into the text) is the next cross-encoder step if GPU time allows.
- **French lexicons** (legal forms incl. EI, street types from the La Poste/AFNOR lists, departments → regions) are
  ready for the normalization work (audit #5).

## 9. Model v4: the France fixes

`ameya-model-v4` = v3 + cross-encoder + `lo0` (proxy odds for France, exact zeros for unseen words) − the legal-form
bitmasks (stages 0–2). Chain: `lo_mix.py` → `s1.py --groups str,cx,lo0,lg --drop leg__r_only_bits,leg__s1_only_bits`
→ `s2.py --groups str,cx,lo0,lg,ce --cluster --extra <leg>,ce__logit` → `decide.py` → `cands_final.py`.

| | v3 | v3ce | **v4** |
|---|---|---|---|
| holdout macro F0.5 | 0.98882 | 0.99021 | **0.99015** (Δ vs v3ce −0.00006 [−0.00012, −0.00001]) |
| stage 1 (p1, best threshold) | 0.9871 | 0.9871 | 0.9869 |
| decision rule | DP | threshold 0.70 | DP (shift 0; +0.00006 over the threshold) |
| test France: predicted per S1 / empty | 3.539 / 4.4% | 3.470 / 5.1% | **3.370 / 5.3%** |
| test US / India: predicted per S1 | 3.380 / 3.358 | 3.386 / 3.370 | 3.382 / 3.367 |
| model's forecast of F0.5, France / US / India | 0.970 / 0.991 / 0.992 | | **0.980** / 0.993 / 0.994 |

**France's predictions by pattern** (per S1; US for reference):

| pattern | v3 | v3ce | **v4** | US (v4) |
|---|---|---|---|---|
| A: number moved + legal form added/changed | 0.047 | 0.023 | **0.002** | 0.022 |
| B: number moved + extra word | 0.047 | 0.021 | **0.007** | 0.071 |
| C: number moved only | 0.037 | 0.040 | 0.040 | 0.196 |
| D: same number + extra word | 0.793 | 0.767 | 0.709 | 0.740 |
| E: no number | 0.276 | 0.278 | 0.272 | 0.356 |
| F: clean | 2.348 | 2.340 | 2.340 | 1.998 |
| total | 3.539 | 3.470 | **3.370** | 3.382 |

- v4 removes 0.17 predictions per French S1 (44k pairs), the size of the false-positive excess estimated in
  section 1. The two look-alike patterns (A, B) are gone; the confident core (F) is untouched.
- The risk is pattern D: 0.058 fewer same-number predictions per S1, and 21% of the rest are now uncertain. Same-number
  descriptor swaps are mostly true under "look-alikes move the number", so part of that drop may be recall.
- US/India are unchanged (holdout tie with v3ce), so **the leaderboard difference v4 − v3ce is France's alone**
  (× 0.15): a clean read of the France fixes.
- Packaged: `submissions/files/2026-09-26-v4/` (validator PASS; candidates = the stage-2 input set, 4.73 per S1).

## 10. What next

| step | what | status |
|---|---|---|
| upload | v4 (`2026-09-26-v4`): the France fixes + cross-encoder | ready; the captain decides |
| upload (optional) | v3ce (`2026-09-26-v3ce`): isolates the cross-encoder; v4 − v3ce is then France alone | ready |
| v5 | French address normalization (department → region, R → rue, articles, bis/ter) + EI as a legal form, same candidates, features `ameya-fx4` | running (about 2 h) |
| G8 probe | a stricter France-only decision (`probe_shift.py --delta -0.5`) if v4's leaderboard move is smaller than the forecast | ready to build |
| open | pool-size-invariant rarity features (audit #4, about −0.0003); a "no match" S1 model for the DP (research R4.1); a diff-aware cross-encoder | not started |

**Leaderboard reading.** US/India predictions of v4 equal v3ce's on the holdout (Δ −0.00006), so
LB(v4) − LB(v3) ≈ 0.85 × 0.0013 (cross-encoder, US/India) + 0.15 × ΔF_France. If France gains what the diagnostics
suggest (+0.03 to +0.05), the leaderboard moves +0.006 to +0.009.
