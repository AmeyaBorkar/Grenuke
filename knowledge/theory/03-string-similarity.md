# String similarity, normalisation and transliteration

**Summary.** A similarity measure is a statement about which edits are cheap. Our data generator applies two kinds of edits: noise that keeps a true copy (accents, typos, word order, legal forms, transliteration, domains) and edits that make a decoy (a swapped business word, an added word, a nudged house number). This page gives the maths of the standard measures (edit distances, Jaro–Winkler, token and TF-IDF measures, q-grams, phonetic codes), our transliteration and number handling, and which features we built from them and why.

Related pages: [entity resolution](01-entity-resolution.md), [blocking](02-blocking.md), [boosting](06-gradient-boosting-and-stacking.md), [cross-encoders](08-transformers-and-cross-encoders.md), [self-training and domain shift](09-self-training-and-domain-shift.md), [glossary](glossary.md).

---

## 1. Intuition

Copies in our data carry many kinds of noise ([methodology §2.1][doc], [FINAL_PLAN §1, #7–#12][plan]): case and accents; typos and OCR digits ("capita1", "8ROKERAGE"); legal forms dropped or rewritten (about 23% of French copies); reordered or appended words; acronyms; domains and handles ("BLUEGRILL.COM"); street types shortened ("Rue" → "R."); Indic-script names (18% of India true pairs); house numbers truncated or suffixed.

Decoys carry different edits: **one business word swapped at the same address** ("antenne danse" against "antenne gaz"), **a business-changing word added** ("holdings", "exports"), or **the house number nudged** on the same street.

No single measure is cheap for the first kind and expensive for the second. Edit distance forgives a typo but also forgives "osd" against "otd". A token-set score forgives word order but also forgives an added "Holdings". So we computed many measures, each invariant to some edits and sensitive to others, and let a gradient-boosted model learn how to combine them ([06](06-gradient-boosting-and-stacking.md)).

## 2. Formal definition

### 2.1 Normalisation

Our blocking tokenizer ([`text.py`][text]), which the features reuse:
- Unicode **NFKD** decomposition, then removal of combining marks (U+0300–U+036F), so "é" becomes "e"; any remaining non-ASCII character becomes a space, so Indic text must be transliterated first ([§2.7](#27-transliteration));
- lowercase, split on non-alphanumerics;
- name tokens of 2+ characters, without legal forms (inc, llc, ltd, pvt, sarl, sas, …), honorifics (shri, sri, smt, dr, mr) and stop words;
- address words with markers dropped (h.no, plot, flat, near, opp, bis, ter, cedex), one short form per street type across US, India and France ("avenue" and "av" → ave, "R" → rue, "saint" → st), ordinals as digits ("Twentieth Ave" → "20 ave"), and French departments mapped to their region;
- numbers as digit runs with leading zeros stripped ("0054" → 54, "8444b" → 8444).

### 2.2 Edit distances

**Levenshtein distance** is the minimum number of single-character insertions, deletions and substitutions turning a into b. Wagner–Fischer dynamic programming:

```
D[i,0] = i,  D[0,j] = j
D[i,j] = min( D[i−1,j] + 1,  D[i,j−1] + 1,  D[i−1,j−1] + [a_i ≠ b_j] )
```

It costs O(|a|·|b|); bit-parallel algorithms (Myers 1999) do it in O(⌈|a|/w⌉·|b|) for machine word size w, which is what rapidfuzz uses. A normalised similarity is 1 − d / max(|a|, |b|).

- **Damerau–Levenshtein** also counts an adjacent transposition ("ca" → "ac") as one edit. The restricted variant (optimal string alignment) adds D[i,j] = min(D[i,j], D[i−2,j−2] + 1) when a_i = b_{j−1} and a_{i−1} = b_j.
- **Indel distance** allows only insertions and deletions: d = |a| + |b| − 2·LCS(a, b), with LCS the longest common subsequence. rapidfuzz's `ratio` is 1 − d/(|a| + |b|) = 2·LCS/(|a| + |b|).

**Jaro similarity.** Characters match if they are equal and at most ⌊max(|a|,|b|)/2⌋ − 1 positions apart. With m matches and t = half the number of matched characters that appear in a different order,

```
J = (1/3) · ( m/|a| + m/|b| + (m − t)/m )         (J = 0 if m = 0)
JW = J + ℓ · p · (1 − J)                            (Jaro–Winkler)
```

where ℓ is the common prefix length (at most 4) and p = 0.1. Winkler's boost reflects that typos are rarer at the start of names. Example: MARTHA vs MARHTA has m = 6 and t = 1, so J = (1 + 1 + 5/6)/3 = 0.944; the prefix MAR gives ℓ = 3 and JW = 0.944 + 0.3 × 0.056 = 0.961.

### 2.3 Token measures

With token sets A and B and IDF weights w:
- **Jaccard** |A ∩ B| / |A ∪ B|; **containment** |A ∩ B| / |A| (asymmetric: did the record keep the S1's words?);
- **IDF-weighted Jaccard** Σ_{A∩B} w / Σ_{A∪B} w, and the **extra IDF mass** Σ_{B\A} w: how much specific content one side has that the other lacks;
- **token-sort ratio**: sort the tokens alphabetically, join, then `ratio`; immune to word order;
- **token-set ratio**: compares the intersection with each side; it returns 100 whenever one token set contains the other, which makes "X Holdings" against "X" look perfect;
- **partial ratio**: the best `ratio` of the shorter string against any equal-length window of the longer one; good for appended text;
- **Monge–Elkan** (1996): ME(A, B) = (1/|A|) Σ_{a∈A} max_{b∈B} sim′(a, b), a token-level average of the best inner similarity; asymmetric.

### 2.4 TF-IDF and soft TF-IDF

Each string becomes a vector with entries tf × idf, idf = log(N/df), compared by cosine. **Soft TF-IDF** (Cohen, Ravikumar and Fienberg 2003) also credits near-identical tokens: it sums V(w, A)·V(w*, B)·sim′(w, w*) over tokens w of A whose closest token w* in B has sim′ (usually Jaro–Winkler) above a threshold θ. Our typo-tolerant token matching is the same idea with an edit-distance threshold.

### 2.5 q-grams

A string's q-grams are its overlapping substrings of length q. One edit destroys at most q of them, so two strings within k edits still share most of their q-grams; this **count filter** (Gravano et al. 2001) makes q-grams a typo-tolerant blocking key. Our names-only view uses character 4-grams of the joined name: "stormy cbmpbell 8rokerage" still shares most 4-grams with "stormy campbell brokerage" ([`index.py`][index]).

### 2.6 Phonetic codes and our consonant skeleton

**Soundex** keeps the first letter and three digits for consonant classes (Robert to R163); **Metaphone** and **Double Metaphone** encode English pronunciation rules; **NYSIIS** is a similar name code. All are built for English surnames.

We used our own **consonant skeleton** ([`indic.py`][indic]), tuned to transliteration variants rather than English spelling: phonetic merges (ph → f, bh → b, dh → d, th → t, kh → k, gh → g, sh → s, ch and c and q → k, w → v, z → j, x → ks), then the first letter plus the remaining consonants (vowels, y and h dropped), with runs collapsed. "maarketing" (from मार्केटिंग) and "marketing" both give **mrktng**; "teknolojiij" and "technologies" share the 4-letter prefix **tknl**. The skeleton came from Plan B (Sachi) ([FINAL_PLAN §14][plan]).

### 2.7 Transliteration

**Rule-based step.** The nine Indic Unicode blocks (Devanagari, Bengali, Gurmukhi, Gujarati, Oriya, Tamil, Telugu, Kannada, Malayalam) share the ISCII-derived layout, so one table of offsets covers all of them. A consonant carries an inherent "a"; a vowel sign replaces it; the virama removes it; a word-final inherent vowel is dropped (schwa deletion): "राम" → "ram". Transliterated legal forms and honorifics (praivet, limitet, shrii) are recognised by skeleton and dropped. The offset table came from Plan A (Ameya).

**Learned dictionary.** Rules give "kanstrakshan", not "construction". From true pairs of training folds 5–19 only, for each transliterated token t of an Indic-script record name, we take the S1 name token w that co-occurs with t most often, and keep the mapping if it has at least 5 supporting pairs and covers at least half of t's pairs ([`feats.py` `learn_indic_dict`][feats]). The result has **693 entries**, for example tek → tech, kanstrakshan → construction, eksaports → exports [M] ([FEATURES.md][feat]). It is a one-step word alignment by majority co-occurrence, a much simpler cousin of the IBM translation models (Brown et al. 1993). Blocking v1, which added the dictionary and the character 4-grams, lifted India's pair recall from 0.959 to 0.984 [M] ([model-v1 handover][m1]).

### 2.8 Numbers

House numbers are identifiers, not text: "42" and "43" are one edit apart and a different building. Among records close to an S1 on name and street words, the first number is equal in 85% of true pairs and only 12% of look-alikes [M] ([FINAL_PLAN §1, #9][plan]). Over all true pairs the first number is equal 83% of the time (US 88%, India 77%), the number sets are equal 73% and overlap 95% [M] (#8). So we encoded **relations**, not equality ([FEATURES.md][feat]):
- `num__rel1`: first numbers missing, equal, truncated (1234 → 123), nudged (|d| ≤ 10) or other;
- `num__rel_best`: the best relation between the S1's first number and any number of the record;
- `num__s1first_in_r`: the S1's first number appears among the record's numbers, **the top stage-1 feature by gain** [M];
- `num__logdiff1`: log(1 + |difference|).

India's compound numbers ("Sno 32/2/1 Hno 1048") break first-number logic: a "number moved" rule that worked for US look-alikes was 45% true in India [M] ([RESEARCH_v6 §4][r6]).

### 2.9 Learned token evidence: look-alike word odds

After typo-tolerant matching, the leftover tokens decide the case. For each token we estimated the **log-odds of a true match when the token is extra in the record or missing from it**, counted on close pairs and computed out of fold ([FEATURES.md][feat]). Learned look-alike words: holdings −9.8, group −9.7, industries, enterprises and exports about −8.6; benign words: c0mpany, lnc, formerly [M]. This is a per-token Fellegi–Sunter weight ([01](01-entity-resolution.md)), and the idea came from Plan A (Ameya) with evidence from the data check of 25 Sep (#9).

France has no labels, so it used **proxy odds** that flag look-alike words by moved house numbers. They failed on dual-use words: "groupe", "france" and "developpement" are both true-copy list words and look-alike insert words, and the proxy gave them −4.84, the value of "holding" [M] ([RESEARCH_v6 §2.9][r6]); see [09](09-self-training-and-domain-shift.md).

## 3. Variants

- **Learned edit costs** (Bilenko and Mooney 2003): fit insertion and substitution costs from labelled pairs, so OCR confusions such as 0/o or 1/l become cheap.
- **Alignment with affine gaps** (Smith–Waterman style): cheap long gaps, good for abbreviations and appended text.
- **Character-n-gram embeddings and sentence encoders**: dense similarity; strong on paraphrase, weak on digits.
- **Cross-encoders** read both strings jointly and learn the measure end to end ([08](08-transformers-and-cross-encoders.md)).
- **Statistical transliteration** (Knight and Graehl 1998) instead of rules plus a dictionary.

## 4. Where we used it

| feature group | measures | input |
|---|---|---|
| `name__*` strings | token-sort and partial ratio on full folded names; token-set ratio, `ratio` and Jaro–Winkler on clean name tokens; `ratio` and partial on the joined tokens (domains such as onetechnologies.com) | rapidfuzz, 0–100, NaN if a side is empty |
| `name__`, `word__`, `num__` overlap | shared count, IDF-weighted Jaccard, containment each way, extra IDF mass each way, token counts | per-country IDF |
| name variants | the same overlap on consonant skeletons and their 4-letter prefixes | `name__skel*` |
| typo-tolerant matching | tokens matched within edit distance 1 (2 from 6 letters); unmatched IDF mass and maximum; `name__fz_sub`, the number of substituted tokens ("a swapped first name is not a typo") | `name__fz_*` |
| legal forms | a bitmask over 20 forms with OCR and dotted variants, Indic skeletons and French forms; relation same, dropped, added, changed | `leg__*` ([`legal.py`][legal]) |
| numbers, look-alike odds | §2.8, §2.9 | `num__*`, `lo__*` |
| addresses | token-set and token-sort ratios on folded addresses | `addr__*` |

All of it is vectorised (rapidfuzz `cpdist`, numba over token arrays), never a Python loop over pairs ([AGENTS.md §6][agents]). Who: Bakshi built normalisation v0 and the first features; Ameya built the model-v1 features ([`feats.py`][feats]); the dictionary and offset table are Plan A (Ameya), the skeleton and OCR variants Plan B (Sachi).

## 5. Why it fits this problem

Each generator edit has a measure that forgives it and a feature that notices it:

| edit | copy or decoy | forgiven by | noticed by |
|---|---|---|---|
| accents, case, punctuation | copy | normalisation | |
| word order | copy | token-sort, token-set, Jaccard | `ratio` |
| typo or OCR digit | copy | edit distance 1–2, Jaro–Winkler, 4-grams, OCR repair | exact-token Jaccard |
| transliteration | copy | offset table, dictionary, skeleton | |
| domain or handle | copy | joined-name ratio, segmentation | token Jaccard |
| list word appended ("services", "groupe") | copy | containment | word odds (benign words) |
| business word swapped | decoy | | `name__fz_sub`, word odds |
| business word added ("holdings") | decoy | token-set ratio (wrongly gives 100) | extra IDF mass, word odds |
| house number nudged | decoy | | `num__rel1` = nudge, `num__logdiff1` |

The model then learns the combinations, for example "same name and street, nudged number, one added rare word" as a decoy.

## 6. Pitfalls

- **Token-set ratio is 100 on a subset**, which is exactly the "word added" decoy. Never use it without extra-token features.
- **Jaro–Winkler rewards shared prefixes**, and on short generic names ("lille club" against "lille cafe") it is high for different businesses.
- **Normalising away evidence.** Dropping legal forms removed look-alike evidence, so the `leg__*` group was added back; making sree/shree/om/maa stop words removed short names' only distinctive word and was reverted (95 true pairs lost against 64 found on the dev pool) [M] ([blocking v3 record][blk3]).
- **Numbers compared as strings.**
- **IDF depends on the pool**: fit it per country; generic French names get low IDF, which is correct but leaves weak evidence.
- **Supervised lexicons leak if fitted on the holdout.** The dictionary and the word odds used training folds only ([CONTRACTS C2][contracts]).
- **Transliteration is many-to-many**: schwa deletion and vowel length vary, which is why the skeleton and the dictionary sit on top of the rules.

## 7. Jury questions with answers

**Q1. Why hand-crafted string features instead of embeddings or a transformer for everything?**
Scoring cost and the nature of the evidence. XGBoost on these features is cheap enough to score all 58M retrieved test pairs; the cross-encoders were affordable only on the 1.49M uncertain ones. Decoys differ by a house number or one word, which features capture exactly and dense embeddings blur. Where the features were unsure, the cross-encoders added real information: band AUC 0.930 for stage 1 against 0.944 for the 7B [M] ([methodology Table 3][doc]).

**Q2. How do you tell a typo from a look-alike?**
Three signals together: the edit size of the changed word (one character is a typo; a whole different word is a substitution), whether the new word is a real, frequent word in the country's S1 names, and its learned look-alike odds. Plus the house number: copies keep it, decoys often nudge it.

**Q3. How did you handle Hindi or Tamil names? Isn't a dictionary learned from labels leakage?**
One offset table transliterates all nine Indic scripts, a consonant skeleton absorbs vowel and aspiration variants, and a 693-entry dictionary learned from true pairs maps transliterations to their English words. It was learned on training folds 5–19 only, never the holdout, so the holdout numbers are honest. India's blocking recall went from 0.959 to 0.984 with it [M].

**Q4. Why did house numbers matter so much?**
Because the generator's decoys sit on the same street with a nudged number. Close to an S1, the first number is equal in 85% of true pairs and 12% of look-alikes [M], and "the S1's first number appears in the record" was the top stage-1 feature by gain.

**Q5. Which features mattered most?**
The top stage-1 feature by gain was `num__s1first_in_r`, the S1's house number found in the record [M] ([FEATURES.md][feat]); our records do not keep a full importance ranking, so do not quote one. SHAP on France named the two features that hurt most there: the proxy word odds on dual-use words, and the retrieval margin, depressed because French house numbers are small and shared [M] ([RESEARCH_v6 §2.9][r6]).

**Q6. Why not Soundex or Metaphone?**
They encode English pronunciation and keep too little (Soundex: one letter and three digits). Our variants are transliteration (aa/a, bh/b, kh/k), so we built a skeleton with exactly those merges, and kept it as an extra token rather than a replacement.

**Q7. What does a token-set score get wrong here?**
It returns 100 when one name's tokens contain the other's, so "Bright Voya Holdings" against "Bright Voya" looks perfect, and that is the added-word decoy. We pair it with the extra-IDF-mass and word-odds features.

**Q8. How expensive is this at scale?**
Linear in candidate pairs: string measures cost O(L²) per pair on names of a few dozen characters, vectorised in C++ and numba. The full feature build ran in minutes per split on one laptop at v1 (12 + 15 min) [M] ([model-v1 handover][m1]); at a billion records the cost follows the candidate count, which is why blocking keeps it near 3.7 per S1 ([11](11-scaling-to-billions.md)).

## 8. Self-test

1. Compute the Levenshtein distance and the Indel `ratio` of "kitten" and "sitting".
<details><summary>Answer</summary>Levenshtein 3 (k→s, e→i, insert g). LCS = "ittn" (4), so Indel = 6 + 7 − 8 = 5 and ratio = 1 − 5/13 = 8/13 ≈ 0.615.</details>

2. Compute Jaro and Jaro–Winkler for MARTHA and MARHTA.
<details><summary>Answer</summary>m = 6, t = 1: J = (6/6 + 6/6 + 5/6)/3 ≈ 0.944. Prefix MAR, ℓ = 3: JW = 0.944 + 3 × 0.1 × 0.056 ≈ 0.961.</details>

3. Give a pair on which token-set ratio is 100 but the records are different businesses. Which of our features catches it?
<details><summary>Answer</summary>"Bright Voya" against "Bright Voya Holdings": one token set contains the other, so the score is 100. The extra IDF mass on the record side and the look-alike odds of "holdings" (about −9.8) flag it.</details>

4. Derive the skeleton of "maarketing" and "marketing".
<details><summary>Answer</summary>No merge applies. Keep the first letter m, drop vowels, y and h from the rest: "rktng". Both give mrktng.</details>

5. Why does one edit destroy at most q of a string's q-grams?
<details><summary>Answer</summary>A q-gram covers q consecutive positions, so one changed position lies in at most q q-grams; the others are unchanged. k edits leave all but at most kq q-grams.</details>

6. Compute the IDF-weighted Jaccard of A = {lille, ecole, sarl} and B = {lille, ecole, gutenberg} with IDF lille 2, ecole 3, sarl 1, gutenberg 6. Why is it low although two of three words match?
<details><summary>Answer</summary>Intersection 2 + 3 = 5; union 2 + 3 + 1 + 6 = 12; 5/12 ≈ 0.42. The unmatched word is the rarest, so it dominates the union. Shared generic words are weak evidence.</details>

7. Why was the Indic dictionary fitted only on folds 5–19?
<details><summary>Answer</summary>It is learned from labels (true pairs). Fitting it on holdout pairs would let the holdout's own answers shape the features, inflating holdout scores (leakage).</details>

## 9. Further reading

- Levenshtein (1966), "Binary codes capable of correcting deletions, insertions, and reversals", Soviet Physics Doklady.
- Damerau (1964), "A technique for computer detection and correction of spelling errors", Communications of the ACM.
- Wagner and Fischer (1974), "The String-to-String Correction Problem", Journal of the ACM.
- Myers (1999), "A fast bit-vector algorithm for approximate string matching based on dynamic programming", Journal of the ACM.
- Winkler (1990), "String Comparator Metrics and Enhanced Decision Rules in the Fellegi-Sunter Model of Record Linkage", ASA Survey Research Methods.
- Monge and Elkan (1996), "The Field Matching Problem: Algorithms and Applications", KDD.
- Cohen, Ravikumar and Fienberg (2003), "A Comparison of String Distance Metrics for Name-Matching Tasks", IIWeb.
- Bilenko and Mooney (2003), "Adaptive Duplicate Detection Using Learnable String Similarity Measures", KDD.
- Navarro (2001), "A Guided Tour to Approximate String Matching", ACM Computing Surveys.
- Gravano et al. (2001), "Approximate String Joins in a Database (Almost) for Free", VLDB.
- Christen (2006), "A Comparison of Personal Name Matching: Techniques and Practical Issues", ICDM Workshops.
- Brown, Della Pietra, Della Pietra and Mercer (1993), "The Mathematics of Statistical Machine Translation: Parameter Estimation", Computational Linguistics.

[doc]: ../../experiments/ameya/final-zip/doc/Documentation_template.md
[plan]: ../../plans/FINAL_PLAN.md
[text]: ../../code/business_entity_resolution/src/ber/block/text.py
[index]: ../../code/business_entity_resolution/src/ber/block/index.py
[indic]: ../../code/business_entity_resolution/src/ber/block/indic.py
[feats]: ../../experiments/ameya/model-v1/feats.py
[feat]: ../../experiments/ameya/model-v1/FEATURES.md
[m1]: ../../docs/handover/2026-09-25_1958_ameya_model-v1.md
[r6]: ../../experiments/ameya/model-v1/RESEARCH_v6.md
[legal]: ../../experiments/ameya/model-v1/legal.py
[agents]: ../../AGENTS.md
[blk3]: ../../docs/decisions/2026-09-26_1122_blocking-v3-repairs.md
[contracts]: ../../docs/CONTRACTS.md
