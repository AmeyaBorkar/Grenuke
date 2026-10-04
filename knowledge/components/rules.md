# Rules and post-processing (RUL)

**Summary.**
- Rules fix errors the model cannot, using how the data was generated: each look-alike or copy is made by a small set of edit operations. Op B (a real descriptor word swapped at the same address) is a different business; op A (a list word appended) is a true copy.
- France rules v1 to v3 drop op-B pairs and add op-A, acronym and exact-copy pairs, for countries without labels only. A stacked pass (`-dpc`) adds acronym adds, per-source caps and the French polish rules to every final candidate.
- The sign of the French look-alike word-swap drop is unresolved: the estimates run from −30e-6 to +60e-6 and it stayed in the final.
- Path key: `mv1/` = `experiments/ameya/model-v1/`, `stk/` = `experiments/ameya/model-v1/stack/`. Evidence levels as in [STANDARD §3](../STANDARD.md).

## 1. Purpose

Correct systematic errors that a pair classifier trained on US and India misjudges in France (no labels), and enforce structural facts of the data (caps, acronym copies). Each rule runs only where its truth rate was measured or can be argued label-free.

## 2. How it works

**Order inside every chain:** `decide.py` (stage 3) → `post_ops.py` (France) → `acr_join.py` (France) → `stk/stack.sh` (hunt → h2 → polish → combo → merge = the `-dpc` tag) → for France only `stk/apply_swapsim.py` (`-dpcs`) → `stk/dp_france.py` (`-dpcsf`) → in the composition, the 7B drop ([llm-recheck.md](llm-recheck.md)). "France" here means every test country absent from the train records, except in scripts that hard-code it ([CF-26]).

**`mv1/post_ops.py`: generator-operation rules, countries without labels only** (`:310-321`)
- **Pairs considered** (`preselect`, `:225-241`, read from `<feats>-str` over the full blocking graph): `num__rel1 == 1` (equal first house number) with at least one shared name word and exactly one extra record word (swaps, appends, code typos); `num__rel1 == 1` with a record name of at most 2 words sharing no word with the S1 (acronyms); `num__rel1` in {2, 3, 4} (other number relations) with the same name (same name, other number).
- **Same address.** v1: the number-street key has an equal number and an equal street word, or one within a typo (both at least 4 letters; Levenshtein ≤ 1 under 7 letters, else ≤ 2) (`:68-73, 187-194`). **v3, `--robust-addr`** (used in every final chain): also `addr_parts`, the first house number without suffix plus the set of street words after it with street types, typo'd types, articles and suffixes removed; a match needs equal numbers and one common street word up to an OSA typo (`:116-164`).
- **Name edit kinds** (`name_edit`, `:76-113`): `acr` (record = initials of at least 2 S1 content words, 2–5 letters), `same` (content words equal up to typos), `add` (one word added), `swap` (one content word replaced), each with the slot position.
- **Populations** (`:206-221`), with REAL_MIN 20, GARBLE_SIM 0.5, MIN_LEN 4 (`:54`):
  - **B (look-alike, op B):** same address, swap, the added word is "real" (in at least 20 S1 names of the country), not a list word, not a garble (Indel similarity to the dropped word below 0.5), at least 4 letters, position in {before_legal, after_legal, end_same_slot, inner}. On US/India 0.6% of these are true.
  - **A (true copy, op A):** same address, swap to a list word, not a garble, position in {after_legal, end_moved, end_same_slot}. 98–99.8% true.
  - **APP:** same address, a list word added with nothing dropped. **ACR:** same address, record = initials. **CODE:** the dropped word has at most 3 letters and is within one edit of the added one. **NUM:** same name with a true-copy house-number edit (−1/−2, one digit changed, swapped, inserted or deleted; never a +d nudge).
  - List words `LIST_A` (`:52`): center, services, service, partners, fils, cie, associes, groupe, developpement, france. These are hand-written lexicons, documented.
- **Applied by default** `--rules B,A,APP,ACR` (`:298`): drop predicted B pairs (`:333-336`); add unpredicted A, APP and ACR pairs that are in `--cands`, whose record no S1 holds and whose S1 is the record's argmax-pc S1, one per record (`:337-354`). NUM and CODE are measured but not applied.

**Versions.** v1 ([D-RUL-01]): drop B, add A. v2 ([D-RUL-02]): add APP and ACR; NUM and CODE rejected; street key tolerates a typo. v3 ([D-RUL-03]): the robust same-address test.

**`mv1/acr_join.py`: acronym copies by a join, countries without labels only** (`:40-72, 101-123`): S1 with 2–5 content words give their initials; records with exactly one content word of 2–5 letters; join on (country, initials); keep the robust same address and `name_edit == "acr"`. Add a pair when the record has exactly one such S1 and no S1 holds it; it goes into the matches and into the candidate set (`ameya-cands-<V>-c2a`). US/India holdout truth 99.8–99.9% [R]. ([D-RUL-06])

**`stk/stack.sh`, the `-dpc` pass** (`:29-38`)
1. `apply_hunt.py` on cut rows (p1 ≥ 0.02, top 2), owners by pc (`stk/apply_hunt.py:60-73`):
   - `cap`: an S1 keeps at most **5 S2, 6 S3 and 11 records**, highest pc first (`:142-152`). Train truth never exceeds 5 S2 or 6 S3 over 2.2M S1.
   - `nsa`: drop a prediction with pc in (threshold, **0.75**] on a record with **≥ 4** S1 at p1 ≥ 0.02 (`:45, 153-158`). It runs but cannot affect the final; the crowd shift replaced it.
   - `acr`: add an owned, unheld candidate with **pc ≥ 0.1** whose record name is the S1's initials and whose address is not empty (`:170-175`). 37 of 37 true on the holdout.
2. `make_h2.py` (`stk/make_h2.py:38-47`): labelled countries keep every hunt change; France keeps only `acr` adds whose record address has no digit (number-dropped acronym copies) and no `cap` drops, because French pc cannot rank near-identical copies.
3. `apply_polish.py --rules copy,city`, France only:
   - **`copy` (the exact-copy rule)** adds an unpredicted pair when (`stk/apply_polish.py:136-189`): names equal up to legal forms, stop words, word order and Cie/Ets/St/Ste (`stk/abbrlib.py`); the same address and every street word of the shorter street matched up to a typo; the same multiset of address numbers; the legal form equal, dropped or added but not changed; the S1 is the record's argmax pc; the record is free; no other candidate S1 of the record passes too; the cities do not mismatch; the 5/6/11 caps hold. Population truth on US/India: 99.992% (US, n = 332,869), 99.998% (India, n = 47,206) [M]. As run on v7sq7wg: +375.
   - **`city` (the cross-commune rule)** drops a predicted pair when both sides name a city of the country's S1 city vocabulary and the city sets are disjoint (`:119-134`; `stk/citylib.py:160-167`). French true copies change commune in 3 of 546,465 pairs [M]. As run: −76. In US/India it would cost −0.01054 [M], so it never runs there.
4. `apply_combo.py` (labelled countries): the expected-F0.5 selection plus `acr` and `cap` ([decision-layer.md](decision-layer.md)). 5. `merge_dpc.py`: labelled countries from step 4, others from step 3.

**`stk/apply_swapsim.py`: French look-alike word swaps** (`:47-76`). A predicted pair is dropped when, after legal forms and stop words, the names differ by exactly one content word (acronym, concatenation, typo, abbreviation, disjoint, one-word add or drop and multi-word cases are recognised first and kept), the record's word is real (at least 20 S1 names), has at least 4 letters, is not a list word, and has Indel similarity ≥ 0.5 to the S1's word ("college du marie" against "ecole du marie"). Labelled countries are never changed (99.3% of such pairs are true there). As run: −454. The France selection adds `dp_france` guards on top ([france.md](france.md)).

## 3. Why this design

- **France rules from the generator** ([D-RUL-01]): fixes the failing operation directly, checkable on US/India labels, countries without labels only so country stays an open set. Forecast +0.0027 on the public LB if France follows US/India rates [E].
- **v2 and v3** ([D-RUL-02], [D-RUL-03]): adds pay above about 72–75% precision (a false add costs about 0.18, a miss about 0.07). v3 pairs the robust test with measured truth: look-alikes India 0.0% (3,178 pairs), US 1.2% (406); A India 87.4%, US 99.1% [M].
- **Acronyms by join, only without labels** ([D-RUL-06]): US acronym-at-address is 99.72% true but India's is 66.1%, so the rule is used where no label can contradict it. The label-free size-bias test says French acronym holders are true copies, f = 0.00 [0.00, 0.01] ([D-FRA-19]).
- **Hunt rules and the stack** ([D-RUL-09], [D-RUL-10], [D-RUL-11]): `acr` and `cap` follow from how the data was generated, so they apply broadly; `copy` and `city` rest on population truth measured in US and India.
- **Word-swap drop** ([D-RUL-14]): three signals agreed at 12:12 on 27 Sep. The size-bias false share was f = 0.83 [0.56, 1.10]; the count test of a sub-agent gave 4.39 against 4.01; US/India base rates imply at least 73% false. Break-even is f of about 0.28.

## 4. Alternatives and why not

- **NUM and CODE adds:** CODE is below any break-even; NUM was rejected because France's rate is unknown and the `nx` features let the model learn number edits ([D-RUL-02]).
- **Op-B drop in US/India:** it would remove 27 pairs that are 93% true (−0.000003) ([D-RUL-01]).
- **Composed-edit rules, address veto, robust-B probe:** no gain (Δ 0, CI [0, 0] on the dev kit) or never selected ([D-RUL-04], [D-RUL-05]).
- **Brand-name join:** records no S1 holds are only 37% (US) and 40% (India) true ([D-RUL-07]).
- **Drop rule from encoder disagreement** (bge below 0 while e5 above 0): anti-selective, firing on 17.76% of known-true French pairs against 8.74% of unknown ones ([D-RUL-12]).
- **Structural French recall recovery:** unconditional precision 0.8698 looks good, but conditional on the model having rejected the pair it is 0.4010 (−0.001077) ([D-RUL-13]).
- **Further data-scan rules and any recall ("add") rule:** none reached the 75% precision an add needs; the best 7B add rule is 71.4% ([D-RUL-15], [D-RUL-17], [D-LLM-08]).
- **Later candidates without the swap drop** ([D-RUL-16]): built, never uploaded.

## 5. Numbers

| fact | value | scope | level |
|---|---|---|---|
| Op B truth | 0.6% of 5,364 holdout pairs; v4 France predicted it at 65.9 per 1000 S1 against 0.04–0.05 in US/India | holdout; test | M |
| Op A / APP / ACR truth, US / India | A 99.7 / 98.3%; APP 98.9 / 99.6%; ACR 99.9 / 99.8%; NUM 97.6 / 78.2%; CODE 42.6 / 44.0% | holdout | M |
| France rules v3 on v6all | −21,365 op-B predictions; adds A 4,062, APP 3,167, ACR 770 | test France | M (counts) |
| Rule populations | 128,856 pairs: A 38,304, ACR 14,884, APP 11,652 (y = 1), op-B 64,016 (y = 0) | test France | M |
| Stack on v7sq7wg | copy +375, city −76, swap drop −454 | test France | R |
| French acronyms | 18,707 pairs predicted (72 per 1000 French S1); holdout acronym candidates 1,440 of 1,444 true | test; holdout | M |
| Combined decision layer incl. `acr` and `cap` | +48.1e-6 [+7.1, +91.2] | holdout v7s | M |
| Stack on the leaderboard | +0.000085 | public LB | M |

**The look-alike word-swap drop, unresolved.** 454 pairs in mixmdp and Composite B (592 in v7sq-dpc). Pc-based estimators put it at −20 to −31e-6; the size-bias method at +58e-6; the leaderboard remainder at about +18e-6; re-scoring six past uploads with these swaps forced to false predicted the leaderboard worse (mean error 0.000102 against 0.000056). Say: "a small rule whose value we could not pin down, between minus 30 and plus 60 millionths; it stayed in" ([D-RUL-16], [CF-27]).

## 6. Failure modes and limits

- **Constants are heuristics** read off US/India truth rates: REAL_MIN 20, GARBLE_SIM 0.5, MIN_LEN 4, caps 5/6/11, `acr` pc ≥ 0.1, `nsa` band 0.75, crowd ≥ 4. Transfer to France is argued from the generator, not measured.
- **Dual-use words.** "groupe", "france" and "développement" appear in the true-copy cell at 27.6–33.5 per 1000 French S1, against 1.2–1.9 for pure look-alike words, yet the same words can also build look-alikes (learned odds −4.7 to −4.8) [M/E]. The rules treat them as list words.
- **Where the rules run is country-specific.** The methodology says acronym joins and caps apply everywhere; `acr_join` adds only in countries without labels, caps drop only in US/India ([CF-25]).
- **Open-set breach.** A few late scripts name France ([CF-26]).
- **Population truth is measured conditional on the model keeping the pair.** Recall rules fail for exactly that reason ([D-RUL-13]).
- **City vocabulary** depends on S1 counts; French copies change commune in 3 of 546,465 pairs, but a drop is still an estimate in France.

## 7. Scale

Every rule is a hash join or a group-by on pairs that survive the cut, so cost is linear in surviving pairs (about 5.9M predictions). Memory peaks were `apply_polish.py` about 2 GB, `apply_swapsim.py` about 3 GB, `acr_join` 6.0 GB, `post_ops` 3.3 GB [R]. The `-dpcsf` stack step takes about 3 min and the rest of the France block's rule steps about 25 min on 24 cores [R]. At 100× the work shards by country (rules read per-country counts). The REAL_MIN 20 threshold is a count, so a small new country would need it rescaled.

## 8. Theory links

[01 entity resolution](../theory/01-entity-resolution.md), [03 string similarity](../theory/03-string-similarity.md), [04 metrics and decisions](../theory/04-metrics-and-decisions.md), [09 self-training and domain shift](../theory/09-self-training-and-domain-shift.md), foundations [F01](../theory/foundations/F01-data-and-problem.md), [F06](../theory/foundations/F06-text-strings-and-retrieval.md), [F15](../theory/foundations/F15-clustering-graphs-and-er-variants.md). Neighbours: [france.md](france.md), [normalisation.md](normalisation.md).

## 9. Likely questions

- **Are these rules overfit to the generator?** They encode how look-alikes and copies are made, and we measured each on US/India labels. For France we argue from the same operations and check label-free (size-bias test, population counts); we never measured France.
- **Why drop a pair the model is 99% sure of?** In France generic names make decoys pass stage 1. Rules drop only pairs with a measured or tested false rate above about 25%.
- **What is op A and op B?** Op A appends a list word (a true copy); op B swaps a real word at the same address (a different business). B is 0.6% true on US/India.
- **Why only countries without labels?** Where labels exist the model learns it (acronym truth 99.7% US, 66.1% India shows the rule is not universal), and the op-B drop would remove 93%-true pairs in US/India.
- **What did the stack gain?** +0.000085 on the public LB with the model fixed.
- **Is the word-swap drop good?** We do not know its sign; estimates span −30e-6 to +60e-6.
- **Why no recall rules?** An add needs about 75% precision; the best candidate reached 71.4%.

[CF-25]: ../conflicts.md
[CF-26]: ../conflicts.md
[CF-27]: ../conflicts.md
[D-FRA-19]: ../decisions/FRA.md
[D-LLM-08]: ../decisions/LLM.md
[D-RUL-01]: ../decisions/RUL.md
[D-RUL-02]: ../decisions/RUL.md
[D-RUL-03]: ../decisions/RUL.md
[D-RUL-04]: ../decisions/RUL.md
[D-RUL-05]: ../decisions/RUL.md
[D-RUL-06]: ../decisions/RUL.md
[D-RUL-07]: ../decisions/RUL.md
[D-RUL-09]: ../decisions/RUL.md
[D-RUL-10]: ../decisions/RUL.md
[D-RUL-11]: ../decisions/RUL.md
[D-RUL-12]: ../decisions/RUL.md
[D-RUL-13]: ../decisions/RUL.md
[D-RUL-14]: ../decisions/RUL.md
[D-RUL-15]: ../decisions/RUL.md
[D-RUL-16]: ../decisions/RUL.md
[D-RUL-17]: ../decisions/RUL.md
