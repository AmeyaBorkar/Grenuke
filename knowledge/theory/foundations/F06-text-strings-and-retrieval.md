# F06. Text, strings and retrieval

**Summary**

- Business records are noisy text. We clean it (Unicode folding, tokens), compare strings with edit distance, Jaro-Winkler, set overlap and TF-IDF cosine, and fix scripts with transliteration.
- To avoid comparing every pair we search an inverted index in both directions (S1 to records, records to S1), per country, and keep short top-k lists.
- This page builds each tool from zero with hand-worked examples, and ends with why exact keys fail on noisy data.

## What you need first

- [F01 data and problem](F01-data-and-problem.md): what S1, S2 and S3 records look like and how they are noisy.
- [F02 probability and statistics](F02-probability-and-statistics.md): independence (for the exact-key argument in section 11).
- Optional: [F13](F13-linear-algebra-and-optimisation.md) for vectors and cosine. The advanced pages are [02 blocking](../02-blocking.md) and [03 string similarity](../03-string-similarity.md).

---

## 1. Text is bytes: Unicode and normalisation

**Intuition.** A computer stores numbers, not letters. Unicode gives every character a number, its **code point**, written U+00E9 for "é". UTF-8 stores a code point in 1 to 4 bytes. The trouble is that the same visible text can be stored in different ways, so two strings that look equal can be unequal.

**Definition.** A **combining mark** (such as the acute accent U+0301) is a separate code point that attaches to the letter before it. So "é" can be one code point (U+00E9) or two ("e" then U+0301). **Normalisation** rewrites text into a standard form:

- NFC composes marks into single code points; NFD decomposes them.
- NFKC and NFKD also apply compatibility rewrites: the ligature "ﬁ" becomes "fi", "²" becomes "2", full-width "Ａ" becomes "A".

**Worked example** (checked in Python):

| text | code points | UTF-8 bytes | NFKD |
|---|---|---|---|
| e | U+0065 | 65 | e |
| é | U+00E9 | c3 a9 | U+0065 U+0301 |
| e + accent | U+0065 U+0301 | 65 cc 81 | the same two |
| म | U+092E | e0 a4 ae | unchanged |
| ß, œ | U+00DF, U+0153 | 2 bytes each | unchanged |

The two "é" are different byte strings, so an exact comparison fails. Our blocking function `fold` ([text.py](../../../code/business_entity_resolution/src/ber/block/text.py)) applies NFKD, deletes the combining marks U+0300 to U+036F, turns any other non-ASCII character into a space, and lowercases. So "Café Zoé" becomes "cafe zoe" and "Crème Brûlée SARL" becomes "creme brulee sarl".

**A limit.** Letters such as ß, œ, ø and ł have no decomposition into letter plus mark, so NFKD leaves them alone and `fold` turns them into a space. Running the real function gives: "Cœur de Lyon" becomes "c ur de lyon" and "Straße" becomes "stra e". The later normalise stage lowercases with `casefold`, which maps ß to "ss" but still splits "Cœur" into "c" and "ur". Both sides of a pair get the same treatment, so a clean S1 and a copy that both contain "œ" still match, but a copy that spells "coeur" would not. We did not measure how often this happens. The usual fix is a small hand-written table (œ to oe, ø to o, ł to l), which the project rules allow if documented.

## 2. Tokenisation

**Intuition.** To compare names we cut them into pieces. The pieces should be what a human would call "the same word".

**Definition.** A **token** is a unit of text after cutting. Word tokens come from splitting on non-letters. Character n-grams (section 3) slide a window over letters. Neural models use subword tokens ([F07](F07-neural-networks-transformers-llms.md)). Our blocking tokenizer works on whole pyarrow columns, with no Python loop over records:

- Name tokens: fold, split on non-alphanumerics, drop legal forms (inc, llc, sarl, sas...) and stop words (the, de, du...), keep tokens of 2+ letters.
- Address words: letters only, markers such as "flat", "near", "po box" removed, and street types mapped to one form (road to rd, street to st, avenue to ave, "R" to rue).
- Address numbers: every run of digits, leading zeros stripped. Spelled-out ordinals become digits ("Twentieth Ave" gives 20).

**Worked example** (real function output):

| input | tokens |
|---|---|
| name "Crème Brûlée SARL" | creme, brulee |
| address "42 R. Gutenberg" | words rue, gutenberg; number 42 |
| address "200 Twentieth Ave" | word ave; numbers 200, 20 |
| address "12 R. Victor Hugo, 1st Floor" | words rue, victor, hugo; numbers 12, 1 |

Legal forms are dropped from retrieval because they are common and often rewritten (about 23% of French copies drop or change them). They still matter as features, because look-alikes change them too.

## 3. Character n-grams

**Intuition.** A typo breaks a word, but most of its letter windows survive.

**Definition.** The **q-grams** of a string are all its substrings of length $q$. Compare two strings by the Jaccard overlap of their q-gram sets (section 6).

**Worked example.** "campbell" has 4-grams camp, ampb, mpbe, pbel, bell. "cbmpbell" has cbmp, bmpb, mpbe, pbel, bell. They share 3 of 7 distinct 4-grams: Jaccard $3/7 = 0.43$. As token sets they share nothing. Now join the words of a whole name, as our code does: "stormycampbellbrokerage" against "stormycbmpbell8rokerage" has 20 4-grams each, 12 shared, so Jaccard $12/28 = 0.43$ and containment $12/20 = 0.6$. At word level the same two names share 1 of 5 distinct tokens, Jaccard 0.2.

We use 4-grams in the names-only view ([index.py](../../../code/business_entity_resolution/src/ber/block/index.py)): the four letters are packed into a negative integer key so they never collide with word keys. Small $q$ tolerates more noise but also matches more strangers.

## 4. Edit distance

**Intuition.** How many single-letter repairs turn one string into the other?

**Definition.** The **Levenshtein distance** is the fewest insertions, deletions and substitutions. Dynamic programming fills a table $D$, where $D[i][j]$ is the distance between the first $i$ letters of $a$ and the first $j$ of $b$:

$$D[i][j] = \min\big(D[i-1][j]+1,\ D[i][j-1]+1,\ D[i-1][j-1] + [a_i \neq b_j]\big),$$

with $D[i][0]=i$ and $D[0][j]=j$. The answer is $D[m][n]$. Time is $O(mn)$.

**Worked example.** "ecole" to "ecoel" (the last two letters swapped):

| | "" | e | c | o | e | l |
|---|---|---|---|---|---|---|
| "" | 0 | 1 | 2 | 3 | 4 | 5 |
| e | 1 | 0 | 1 | 2 | 3 | 4 |
| c | 2 | 1 | 0 | 1 | 2 | 3 |
| o | 3 | 2 | 1 | 0 | 1 | 2 |
| l | 4 | 3 | 2 | 1 | 1 | 1 |
| e | 5 | 4 | 3 | 2 | 1 | **2** |

Distance 2: one swap costs two edits. The Damerau variant (optimal string alignment) also allows swapping neighbours and gives 1.

**Similarity.** Divide by the longer length: $1 - d/\max(m,n)$. Look at two real cases from the method note. "ehpad" typed as "ehpvd" has $d=1$, similarity 0.8, and is a garble of the same business. "osd" against "otd" also has $d=1$, similarity 0.667, and is a different business. The distance is the same and the meaning is opposite. Short names make one letter a large share, so string distance alone cannot decide; rarity and the address must help.

**Speed.** Libraries such as rapidfuzz use bit-parallel versions (Myers 1999) that handle many letters per machine word. Our typo-tolerant token matching accepts distance 1 (2 for tokens of 6+ letters) ([FEATURES.md](../../../experiments/ameya/model-v1/FEATURES.md)).

**Numbers are not words.** "42" against "43" has distance 1, similarity 0.5; "42" against "205" has Jaro-Winkler 0. Neither value means anything for house numbers. What matters is the relation: equal, truncated, nudged by a little, or different. Look-alike records move the first house number in 88% to 98% of cases and true copies seldom do ([feats_lo_proxy.py](../../../experiments/ameya/model-v1/feats_lo_proxy.py)), so our features code the relation (`num__rel1`: missing, equal, truncation, nudge of at most 10, other) and not a string score.

## 5. Jaro-Winkler

**Intuition.** A measure built for short strings such as names: it counts letters that match close to each other, and rewards a shared beginning.

**Definition.** Two letters match if they are equal and no more than $\lfloor \max(|s|,|t|)/2 \rfloor - 1$ positions apart. With $m$ matches and $t$ equal to half the number of matched letters in the wrong order:

$$\text{Jaro} = \tfrac13\left(\frac{m}{|s|} + \frac{m}{|t|} + \frac{m-t}{m}\right), \qquad \text{JW} = \text{Jaro} + \ell\,p\,(1-\text{Jaro}),$$

where $\ell$ is the shared prefix length (at most 4) and $p = 0.1$.

**Worked example.** "MARTHA" and "MARHTA": all 6 letters match, two are swapped so $t=1$. Jaro $= (1 + 1 + 5/6)/3 = 0.944$. The prefix "MAR" gives $\ell=3$, so JW $= 0.944 + 3\times0.1\times0.056 = 0.961$. For "osd" and "otd": $m=2$, $t=0$, Jaro $= (2/3+2/3+1)/3 = 0.778$, JW $= 0.8$. Our feature `name__c_jw` is JW on the clean name tokens. Implementations differ in how they round $t$ when the mismatch count is odd, so compare numbers only within one library.

## 6. Jaccard, containment, Dice

**Definition.** For token sets $A$ and $B$: Jaccard $=|A\cap B|/|A\cup B|$; containment of $A$ in $B$ $=|A\cap B|/|A|$; Dice $=2|A\cap B|/(|A|+|B|)$.

**Worked example.**

| S1 tokens | record tokens | Jaccard | containment of S1 in record |
|---|---|---|---|
| abc, exports | abc, exports, pvt, ltd | 0.50 | 1.00 |
| antenne, danse | antenne, gaz | 0.33 | 0.50 |
| lille, ecole | ecole, lille | 1.00 | 1.00 |

Appended words punish Jaccard but not containment. A swapped business word ("danse" to "gaz") lowers both. That is why Table 2 of the [method note](../../../experiments/ameya/final-zip/doc/Documentation_template.md) lists both. The IDF-weighted versions replace counts by sums of IDF (next section): `f__jac_w`, `f__cont_s1`, `f__cont_r`.

**The fuzzy ratios in our features.** The library rapidfuzz gives four scores from 0 to 100 that our name features use (`name__tsort`, `name__partial`, `name__c_tset` and others). `ratio` is a normalised similarity where edits are only insertions and deletions. `token_sort_ratio` sorts the words first, so order does not matter. `token_set_ratio` ignores extra words when one side's words contain the other's. `partial_ratio` aligns the shorter string with the best-matching piece of the longer. Same pairs, four scores plus Jaro-Winkler (times 100):

| pair | ratio | sort | set | partial | JW |
|---|---|---|---|---|---|
| "abc exports" / "abc exports pvt ltd" (appended words) | 73.3 | 73.3 | 100 | 100 | 91.6 |
| "lille ecole" / "ecole lille" (reordered) | 45.5 | 100 | 100 | 62.5 | 71.0 |
| "antenne danse" / "antenne gaz" (business word swapped) | 75.0 | 75.0 | 77.8 | 85.7 | 90.2 |
| "osd" / "otd" (one letter, short) | 66.7 | 66.7 | 66.7 | 66.7 | 80.0 |

Each score handles one kind of noise well. The swapped-word decoy scores 75 to 90, as high as some true copies, so string similarity alone cannot separate copies from look-alikes. That is the job of the learned look-alike word odds and the address features.

## 7. TF-IDF and cosine

**Intuition.** Sharing "rue" says little; sharing "gutenberg" says a lot. Weight each word by how rare it is.

**Definition.** **Term frequency** is how often a word appears in a record; for short names it is almost always 1. **Inverse document frequency** is $\text{idf}(t)=\ln(N/\text{df}(t))$, where $N$ is the number of records and $\text{df}(t)$ the number containing $t$ (Spärck Jones 1972). The cosine of two vectors is $\cos\theta = a\cdot b/(\lVert a\rVert\lVert b\rVert)$. Our search score ([search.py](../../../code/business_entity_resolution/src/ber/block/search.py)) is the cosine of binary token vectors whose entries are $\sqrt{\text{idf}}$:

$$\text{score}(q,d) = \frac{\sum_{t \in q\cap d}\text{idf}(t)}{\sqrt{\sum_{t\in q}\text{idf}(t)}\ \sqrt{\sum_{t\in d}\text{idf}(t)}}.$$

The weight is floored at 0.01, and statistics are computed per country partition, so "lille" is rare in a US index and common in a French one.

**Worked example.** Six toy records (made-up, for illustration), $N=6$. Query: the S1 "lille ecole rue gutenberg".

| word | df | idf |
|---|---|---|
| rue | 5 | 0.182 |
| lille, gutenberg | 4 | 0.405 |
| ecole | 3 | 0.693 |
| club | 2 | 1.099 |
| quai, wault, paris, lyon, victor, danse | 1 | 1.792 |

Query norm: $\sqrt{0.405+0.693+0.182+0.405}=1.299$.

| record | shared words | numerator | record norm | score |
|---|---|---|---|---|
| d0 lille ecole rue gutenberg | all four | 1.686 | 1.299 | 1.000 |
| d3 paris ecole rue gutenberg | ecole, rue, gutenberg | 1.281 | 1.753 | 0.563 |
| d1 lille club rue gutenberg | lille, rue, gutenberg | 0.993 | 1.446 | 0.529 |
| d5 lille danse rue gutenberg | lille, rue, gutenberg | 0.993 | 1.669 | 0.458 |
| d2 lille ecole quai wault | lille, ecole | 1.099 | 2.164 | 0.391 |
| d4 lyon club rue victor | rue | 0.182 | 2.206 | 0.064 |

Record d2 plays the decoy: same name, other street (like "lille ecole sarl, 42 q. du wault" in the method note). Retrieval ranks it fifth of six here, so at a realistic depth it is still retrieved. The score cannot tell copy from decoy; later stages use house numbers and rivals for that.

**Limits.** A bag of words ignores order, and a typo ("cbmpbell") shares no token with "campbell". Section 3 and the repairs in section 11 cover that. BM25 (Robertson and Zaragoza 2009) adds saturation and length normalisation:

$$\text{BM25}(q,d)=\sum_{t\in q}\text{idf}(t)\,\frac{f\,(k_1+1)}{f + k_1\,(1-b+b\,|d|/\text{avgdl})},$$

with $f$ the count of $t$ in $d$, typical $k_1 = 1.2$ and $b = 0.75$. For $f=1$ the factor is 1.26 in a record half the average length and 0.71 in one twice as long. Names are short and words almost never repeat, so $f$ is 1 nearly always and BM25 is close to a sum of IDF times a length factor. Our cosine does the length normalisation through the two norms.

## 8. The inverted index

**Intuition.** The index at the back of a book maps each word to its pages. To find pages with two words, read two short lists instead of the whole book.

**Definition.** A **posting list** is the sorted list of record ids that contain a token. The **inverted index** is the table token to posting list. Building it is a counting sort: count the records per token, take prefix sums to get start offsets, then place each record id ([`build_postings`](../../../code/business_entity_resolution/src/ber/block/index.py)). That costs time linear in the total number of tokens.

**Query.** For each query token walk its posting list and add that token's weight to an accumulator for each record in it. The work is the sum of the posting lengths of the query's tokens, not the number of records $N$. In the toy above, "lille" adds 0.405 to d0, d1, d2, d5; "ecole" adds 0.693 to d0, d2, d3; and so on. Then divide by the norms and keep the $k$ best with a min-heap of size $k$: scan the scores, and replace the heap's smallest whenever a bigger one arrives. For scores 0.3, 0.9, 0.5, 0.7, 0.1, 0.8 and $k=3$ the heap ends as {0.7, 0.8, 0.9}. Cost $O(n\log k)$.

**Hot tokens.** "rue" has the longest list but the smallest weight. Walking it is expensive and almost useless. Our search only lets a token start candidates if its list has at most `seed_cap` entries (3000 in the record index that S1 queries use, 1000 in the S1 index that record queries use). The best few hundred seeded candidates (`n_verify`) are then re-scored exactly: the query's common tokens are looked up in each candidate's sorted token list by binary search, so a shared "delhi" still counts. The price: a query that shares no rare token with anything gets no candidates.

## 9. Top-k retrieval in both directions

**Intuition.** From the S1's side, its true copies can be buried under many similar records (a popular name). From a record's side, its true S1 is usually near the top, because each record belongs to at most one S1. Searching both ways is cheap insurance.

**Definition.** Run S1 to records and record to S1 separately, and keep the union. Our setting, per country:

- retrieve each S1's top 40 records and each record's top 8 S1;
- keep a pair if the record is in its S1's top 15, or the S1 is in the record's top 4.

The depths differ because an S1 has 0 to 11 copies (3.46 on average) but a record has at most one S1.

**Worked example.** S1 A has five look-alike records scoring 0.9, 0.85, 0.8, 0.7, 0.6, and a garbled true copy $r^\ast$ at 0.45. Forward top-3 misses $r^\ast$. From $r^\ast$'s side, A scores 0.45 and the next S1 only 0.10, so A is its top-1 and the pair is kept by the reverse rule.

**Numbers.** Retrieval gives 58.4M pairs on test, about 34 per S1 (6,410,308 candidates at 3.70 per S1 is about 1.73M test S1). A learned cut then leaves 6.41M, 3.70 per S1, against 3.46 true copies per S1. See [02 blocking](../02-blocking.md), and the note on which set 99.1% recall belongs to in the [theory README](../README.md).

## 10. Transliteration

**Intuition.** "marketing" and "मार्केटिंग" share no character. To compare them, write both in one alphabet.

**Definition.** **Transliteration** maps letters of one script to another by sound. Nine Indic Unicode blocks share one layout, so one table of offsets covers them. A consonant carries an inherent "a"; a vowel sign replaces it; a virama (the "kill" sign) removes it; a word-final inherent vowel is dropped ([indic.py](../../../code/business_entity_resolution/src/ber/block/indic.py)). The result is phonetic and lossy.

**Worked example** (real output). "राम" gives "raam". "मार्केटिंग" gives "maarketing". A **consonant skeleton** (first letter plus consonants, with phonetic merges) maps both "maarketing" and "marketing" to "mrktng". Skeletons also catch "praivet" and "private" (both "prvt"). They do not unify everything: "limitet" gives "lmt" but "limited" gives "lmtd", so the legal-form list holds several variants.

**Learned dictionary.** Transliteration is many-to-many, since vendors spell the same sound differently. So we learn a dictionary from training pairs: for each Indic-script token, the S1 name token it most often sits next to in true pairs of train folds 5 to 19, kept if seen at least 5 times, in at least 50% of the cases, and different from the token itself. It has 693 entries, such as tek to tech, kanstrakshan to construction, eksaports to exports ([`learn_indic_dict`](../../../experiments/ameya/model-v1/feats.py)).

## 11. Why exact keys fail on noisy data

**Two failure modes.** An exact key joins records whose normalised name and address are identical.

- Misses. If edits hit a copy independently with rates $r_1,\dots,r_k$, the chance it keeps the key is $\prod (1-r_i)$. Toy case: six edit types, each hitting 10% of copies, gives $0.9^6 = 0.53$, so 47% of true copies miss. In our data legal forms change in about 23% of French copies alone, and case, accents, typos, street-type shortening, changed house numbers and empty addresses add more.
- Collisions. Between 46% and 54% of S1 share their name with another S1, so a name key puts a record in a block with several S1, and generic names make some blocks huge.

**What we do instead.** IDF-weighted soft overlap (partial agreement still ranks), several views, and repairs before matching: a dynamic programme cuts a domain-style name such as "bluegrill" into the country's S1 words "blue" and "grill" ([repair.py](../../../code/business_entity_resolution/src/ber/block/repair.py)); OCR digits are mapped back to letters (8 to b, 5 to s) when the result is a known S1 word; and the Indic dictionary above.

---

## How it shows up in our project

- Blocking code: [text.py](../../../code/business_entity_resolution/src/ber/block/text.py), [index.py](../../../code/business_entity_resolution/src/ber/block/index.py), [search.py](../../../code/business_entity_resolution/src/ber/block/search.py), [indic.py](../../../code/business_entity_resolution/src/ber/block/indic.py), [repair.py](../../../code/business_entity_resolution/src/ber/block/repair.py).
- Method: Table 1 (views) in the [method note](../../../experiments/ameya/final-zip/doc/Documentation_template.md); features in [FEATURES.md](../../../experiments/ameya/model-v1/FEATURES.md).
- Scale and cost of retrieval: [F08](F08-computing-at-scale.md).

## How to read the numbers

- **Scores live on different scales.** Normalised edit similarity, Jaro-Winkler, Jaccard and cosine all run from 0 to 1 but mean different things. For "osd" against "otd": edit similarity 0.67, Jaro-Winkler 0.80, token Jaccard 0 (the one token differs). A model learns what each value means; never apply one threshold to all.
- **IDF magnitude.** With $N=1{,}000{,}000$ (toy), df 10 gives 11.5, df 1,000 gives 6.9, df 50,000 gives 3.0 and df 500,000 gives 0.69. A word in half the records is nearly free.
- **Costs at a glance.** Levenshtein: $O(mn)$ per pair. Jaccard on sorted token lists: $O(|A|+|B|)$. Scanning all $N$ records per query: $N$ times the pair cost. Inverted index: the sum of the query tokens' posting lengths, plus $O(P\log k)$ for the heap over $P$ touched records.
- **Top-k depth.** Recall at depth $k$ is the share of true pairs inside the top $k$. Deeper lists raise recall and cost, since every later stage pays per pair ([F08](F08-computing-at-scale.md)).

## Common misconceptions

1. "Two strings that look equal are equal." Not without normalisation (two "é").
2. "Edit distance 1 means a typo." It also separates "osd" from "otd".
3. "NFKD makes any text ASCII." It strips accents, but ß, œ, ø and ł have no decomposition.
4. "Rare words are always better." A rare word can be a typo; typo-tolerant matching and n-grams exist for that.
5. "TF-IDF is a model." It is a weighting; the model decides what the scores mean.
6. "An inverted index gives approximate answers." Ours is exact except for the deliberate seeding cap.
7. "One direction of search is enough." It misses copies buried among look-alikes.
8. "Transliteration is a lookup." It is many-to-many; we learn the dictionary from pairs.

## Check yourself

Exercise 1. Give the UTF-8 bytes of "é" in NFC and the bytes of NFD "é". Why can a database miss a match between them?

<details><summary>Answer</summary>

NFC: one code point U+00E9, bytes c3 a9. NFD: "e" (65) followed by U+0301 (cc 81), so 65 cc 81. The byte strings differ, so equality fails even though both display "é". Normalising both sides to the same form fixes it.

</details>

Exercise 2. What does our `fold` do to "Cœur de Lyon", and why?

<details><summary>Answer</summary>

It gives "c ur de lyon". NFKD does not decompose "œ" (it is not letter plus mark), so the remaining non-ASCII character is replaced by a space. A documented table (œ to oe) would fix it; we did not measure how often it matters.

</details>

Exercise 3. Tokenise the address "5 R. Victor Hugo, 2nd Floor" with our rules.

<details><summary>Answer</summary>

Words: rue, victor, hugo ("R" is read as rue; "floor" is a marker and dropped). Numbers: 5 and 2 (the ordinal ending "nd" is removed).

</details>

Exercise 4. Compute the Levenshtein distance and the normalised similarity of "sarl" and "sas".

<details><summary>Answer</summary>

Substitute r by s, delete l: distance 2. Similarity $1 - 2/4 = 0.5$.

</details>

Exercise 5. Compute Jaro and Jaro-Winkler for "abcd" and "abdc".

<details><summary>Answer</summary>

Window $= 4//2 - 1 = 1$. All four letters match. Matched sequences "abcd" and "abdc" disagree in 2 places, so $t = 1$. Jaro $= (1+1+3/4)/3 = 0.9167$. Prefix "ab" gives $\ell = 2$: JW $= 0.9167 + 2\times0.1\times0.0833 = 0.9333$.

</details>

Exercise 6. S1 tokens {lille, club}, record tokens {lille, ecole}. Give Jaccard, Dice and containment of the S1 in the record.

<details><summary>Answer</summary>

Intersection 1, union 3: Jaccard 0.333. Dice $2\times1/4 = 0.5$. Containment $1/2 = 0.5$.

</details>

Exercise 7. $N=1000$. Word a has df 10, word b has df 500. The query is {a, b}. Record 1 is {a}, record 2 is {b}. Compute both cosine scores.

<details><summary>Answer</summary>

idf(a) $=\ln 100 = 4.605$, idf(b) $=\ln 2 = 0.693$. Query norm $=\sqrt{5.298}$. Record 1: $4.605/(\sqrt{5.298}\sqrt{4.605}) = \sqrt{4.605/5.298} = 0.932$. Record 2: $\sqrt{0.693/5.298} = 0.362$. Matching the rare word is worth far more.

</details>

Exercise 8. A query has tokens with posting lists of 20, 4,000 and 150,000 records. `seed_cap` is 3000. Which tokens seed candidates, and how many postings are walked?

<details><summary>Answer</summary>

Only the token with 20 entries seeds (the other two exceed the cap). Only 20 postings are walked. The top seeded candidates are then re-scored by binary search for the other two tokens in each candidate's token list, instead of walking 154,000 postings.

</details>

Exercise 9. A true copy $r$ has S1 A. Five other records outscore it for A, forward depth is 3, reverse depth is 1, and A is $r$'s best S1. Is the pair kept?

<details><summary>Answer</summary>

Yes. The forward rule fails (rank 6 is outside the top 3), but A is in $r$'s top 1, so the reverse rule keeps it.

</details>

Exercise 10. Five independent edit types each hit 8% of copies. What share of copies keeps an exact key?

<details><summary>Answer</summary>

$0.92^5 = 0.659$. About 34% of true copies miss, before counting that real edits are not independent.

</details>

Exercise 11. Why does the skeleton of "limited" differ from that of "limitet", and what does the code do about it?

<details><summary>Answer</summary>

Skeleton keeps the first letter and consonants: "limited" gives "lmtd", "limitet" gives "lmt". The two spellings keep different last consonants. The code lists several legal-form skeletons (lmt, lmtd, prvt, prbt, ...) and drops Indic tokens matching any of them.

</details>

## Going deeper

- Levenshtein (1966). Binary codes capable of correcting deletions, insertions, and reversals.
- Wagner and Fischer (1974). The string-to-string correction problem.
- Myers (1999). A fast bit-vector algorithm for approximate string matching based on dynamic programming.
- Jaro (1989). Advances in record-linkage methodology as applied to matching the 1985 census of Tampa, Florida. Winkler (1990). String comparator metrics and enhanced decision rules in the Fellegi-Sunter model of record linkage.
- Spärck Jones (1972). A statistical interpretation of term specificity and its application in retrieval. Salton and Buckley (1988). Term-weighting approaches in automatic text retrieval.
- Robertson and Zaragoza (2009). The probabilistic relevance framework: BM25 and beyond.
- Manning, Raghavan and Schütze (2008). Introduction to Information Retrieval.
- Unicode Standard Annex 15: Unicode Normalization Forms.

## Where next

- [F07](F07-neural-networks-transformers-llms.md): tokens in neural models and what they do with these strings.
- [F08](F08-computing-at-scale.md): hashing, LSH, ANN, and the cost of retrieval.
- [F13](F13-linear-algebra-and-optimisation.md): vectors, sparse versus dense, SVD.
- [03 string similarity](../03-string-similarity.md) and [02 blocking](../02-blocking.md) for the advanced treatment.
