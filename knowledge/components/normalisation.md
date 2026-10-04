# Normalisation (NRM): text folding, lexicons, Indic transliteration, repairs

**Summary.** In the submitted pipeline normalisation is not a separate stage: it lives inside the blocking tokenizer, which the pair features reuse, plus a few hand-written lexicons in the rules.
The pieces are Unicode folding, name and address tokenisation, our own Indic transliteration with a dictionary learned from training pairs, S2/S3 name repairs (domains, OCR digits) and legal-form codes. No external transliterator, geocoder or data is used.
Path prefixes: `ber/` is `code/business_entity_resolution/src/ber/`; `mv1/` is `experiments/ameya/model-v1/`; `stk/` is `experiments/ameya/model-v1/stack/`. Constants are read from the code at the cited line.

## 1. Purpose

Make noisy names and addresses comparable (case, accents, abbreviations, legal suffixes, scripts, glued-together domains) so that blocking keys and pair features see the same tokens.
Do it with documented, hand-written lexicons and statistics learned only from the provided data.

## 2. How it works

Where it runs: `ber/block/text.py`, `ber/block/indic.py` and `ber/block/repair.py` for blocking; the features import the same functions (`mv1/feats.py:59`); `mv1/legal.py` for legal-form codes; `ber/features/context.py:59-83` for the (house number, street) key; `mv1/post_ops.py:63-164`, `stk/abbrlib.py` and `stk/citylib.py` for rule-side tokens.

### 2.1 Folding and name tokens ([`ber/block/text.py`](../../code/business_entity_resolution/src/ber/block/text.py))

- `fold` (`:57-62`): NFKD, combining marks U+0300 to U+036F removed, any remaining non-ASCII character replaced by a space, ASCII lowercase.
- Name tokens (`:96-98`): split on `[^a-z0-9]+`, drop tokens shorter than 2 and any token in `LEGAL` or `NAME_STOP`.
- `LEGAL` (`:24-27`): inc incorporated llc ltd limited pvt private corp corporation co company cos lp llp pllc pc plc gmbh sarl sas sasu eurl sa sci snc ei.
- `NAME_STOP` (`:32-34`): the and of a an de du des la le les et www com net org dba aka shri sri smt dr mr mrs ms. The words sree, shree, om and maa are kept on purpose: as stop words the dev pool lost 95 forward pairs and found 64, and they are often a name's only distinctive word (comment `:29-31`). The honorifics shri, sri and smt never occur in train S1 names, yet the generator adds each to about 1.6k copies.

### 2.2 Address words and numbers (`:131-152`)

- Ordinal words become digits for 1 to 39 ("twenty first" becomes 21); then `([0-9])(st|nd|rd|th)` becomes the digit (`ORDINALS` `:101-108`).
- French departments, when they are a whole comma component, become their region. This lexicon is hand-written for three regions only: hauts de france (5 departments), nouvelle aquitaine (12) and pays de la loire (5) (`DEPARTMENT_REGION` `:49-54`), the regions of the test data.
- Words: letters only; the one-letter "r" becomes "rue" (`SHORT_STREET` `:47`, applied in every country); words shorter than 2 and `ADDR_STOP` are dropped (`:35-39`: null none na no nos h hno house plot door flat unit apt apartment suite ste floor fl bldg building near nr opp opposite behind beside po box pmb nd th de du des la le les sur en au aux bis ter quater cedex).
- Street types are canonicalised (`STREET` `:41-46`): road to rd, street and str to st, saint to st, avenue and av to ave, boulevard and bd to blvd, allee to all, route to rte, and so on.
- Numbers: every digit run with leading zeros stripped.

### 2.3 Indic scripts ([`ber/block/indic.py`](../../code/business_entity_resolution/src/ber/block/indic.py))

- Nine Brahmic blocks (Devanagari, Bengali, Gurmukhi, Gujarati, Oriya, Tamil, Telugu, Kannada, Malayalam) share one ISCII-derived offset table (`BLOCKS` `:19`, `_table` `:30-50`). The inherent vowel is replaced by a vowel sign or the virama, and the word-final schwa is deleted (`:56-67`).
- Consonant skeleton (`:90-100`): merges ph to f, bh to b, dh to d, th to t, kh to k, gh to g, sh to s, ch to c, ck to k, q to k, c to k, w to v, z to j, x to ks; keep the first letter, drop `[aeiouyh]` after it, collapse doubled consonants. "maarketing" and "marketing" both give "mrktng".
- On Indic-script names, transliterated legal forms and honorifics with skeletons `prvt prbt prvr pr l lmt lmtd lmrd elp sr` are dropped (`:106, 121-123`), then the learned dictionary is applied (`:124-128`). A Latin-script name is never touched by the dictionary.
- Learned dictionary (`mv1/feats.py:66-86`): over true pairs of train folds 5 to 19 only whose record name is Indic, map each record token t to the S1 token w it co-occurs with most; keep it if count is at least 5, share at least 0.5 and t differs from w (`min_count=5, min_share=0.5`). 693 entries (for example tek to tech, kanstrakshan to construction, eksaports to exports) [R, [MB:35](../../experiments/bakshi/final-package/METHODOLOGY_bakshi.md)]. The holdout never enters it.

### 2.4 Name repairs for S2/S3 only ([`ber/block/repair.py`](../../code/business_entity_resolution/src/ber/block/repair.py))

Vocabulary: per country, the number of S1 names containing each token (`:43-53`). So the repair adapts to each country's own S1 words with no external list.
- Domain and handle segmentation (`segment`, `:61-99`): a minimum-cost dynamic programme over split points. Eligible are alphabetic tokens when the name is one token of at least 8 letters (`SEG_MIN_LEN`), or the name carries a marker (.com .net .org .in .co .info .biz, www, @, #) and the token has at least 6 letters. Piece cost: an S1 word costs `log(total/count) + 3.0`, a domain affix 2.0, a legal word 6.0, a single-letter initial 9.0; pieces up to 24 characters. A cover needs at least 2 pieces, at least 1 real word, at most 2 initials, at most 4 words.
- OCR repair (`:102-114`): digit map 0 to o, 1 to l or i, 3 to e, 4 to a, 5 to s, 6 to g, 8 to b (2, 7, 9 are unmappable); a token of at least 4 characters with at least 2 letters and at most 4 ambiguous digits takes the most frequent S1 word among its expansions.
- Repaired words are appended to the record's own tokens; the originals stay (`:167-174`). Loops run over distinct (country, token), never over records.

### 2.5 Legal forms and the house-number key

- `mv1/legal.py`: 21 bit positions (pvt ltd llc inc corp co llp lp pllc pc plc opc sas sarl sa sasu eurl sci snc gmbh ei) (`:25-26`); dots removed; single-character OCR variants for forms of 3 or more letters; "pvtltd" and "privatelimited" map to pvt plus ltd; Indic skeletons prvt, prbt, prvr map to pvt and lmt, lmtd, lmrd to ltd. The relation features use these ([features.md](features.md)).
- `ber/features/context.py:59-83`: blank street types, articles and house markers, then take the first number followed by a word of at least 2 letters; "32 Rue Andre Maginot" gives `32|andre`.
- Other hand-written lexicons: `stk/abbrlib.py:8-9` (cie to compagnie, ets and etabl to etablissements, st to saint); `stk/dp_france.py:46` (cte to comite, asso to association); `stk/citylib.py` (st, ste, ft, mt expansion; US state names; two French aliases, Lomme and Hellemmes to Lille, Le Clion to Pornic). Rule-side token sets in `mv1/post_ops.py:50-51, 63-65`.

### 2.6 Not on the final path

`ber/normalize/` (a streaming parser with legal forms, honorifics, US/India states and French regions, by Bakshi, delivered and tested on day 1) is imported only by tests; Composite B does not use it (D-FEA-07, D-BLK-04).

## 3. Why this design

Decision records: [NRM](../decisions/NRM.md), [BLK](../decisions/BLK.md), [FEA](../decisions/FEA.md).
- D-NRM-01 no postcode field or feature: postcodes appear in at most 0.5% of addresses (India 0.02%, US 0.33%) [M].
- D-NRM-02 our own Indic transliteration, skeletons and learned dictionary, no external transliterator: no dependency, no external data (transliterated 752,869 Indic names in 3.8 s [M]). IndicXlit was set aside; the question of its external training data was left for a human ruling that was never needed.
- D-BLK-04 blocking uses its own tokenizer so it does not wait on the normalise stage. Speed won, and per-country statistics later gave France its own vocabulary.
- D-BLK-11 repairs (domains, OCR digits, ordinals) built from each pool's own S1 names; honorific stop words tried and reverted.
- D-NRM-03 French address normalisation and EI as a legal form (a tie on the local holdout, 0.99013 against 0.99015 [M]; a France-only fix whose value cannot be seen there).
- D-NRM-05 no further vendor-format normalisation: every other transformation was already recovered at or above average rate.
- D-FEA-06 the (number, street) key fixed for French addresses; D-FEA-07 the day-1 normalise stage was never wired into the chain.
- D-NRM-04 (final fit on all of train) is a modelling choice; see [model-stages.md](model-stages.md).

## 4. Alternatives and why not

- External transliterator (IndicXlit, MIT): needs external training data and a ruling; the Indic slice was already at parity (0.9872 against 0.9870 on the holdout).
- A full parser (`ber/normalize/`): never evaluated at full scale; the chain's own tokenizer was faster and already measured ahead.
- Honorifics and sree/shree/om/maa as stop words: lost recall (95 lost against 64 found on the dev pool) and was reverted.
- Postcode keys: fire on at most one address in two hundred.
- GPL libraries such as `unidecode`: excluded; folding is our own few lines.

## 5. Numbers

| fact | value | level | source |
|---|---|---|---|
| Indic dictionary | 693 entries from train folds 5-19 | R | [MB:35](../../experiments/bakshi/final-package/METHODOLOGY_bakshi.md) |
| India pair recall at blocking | 0.9590 (v0 with transliteration) to 0.9836 (v1 with dictionary and 4-grams); US 0.9860 to 0.9872 | M, local holdout | [D-NRM-02](../decisions/NRM.md) |
| Blocking v3 repairs, dev pool | forward recall 0.97240 to 0.97939: domains 0.868 to 0.937, OCR 0.906 to 0.952, ordinals 0.972 to 0.990 | M, 110k-S1 dev pool | [D-BLK-11](../decisions/BLK.md) |
| Repaired tokens | 1,211,326 (train), 890,435 (test) | M | [numbers §2](../numbers.md) |
| Full-scale retrieval recall | 0.98992 to 0.99135; misses 19,163 to 16,455 | M, local holdout | [D-BLK-11](../decisions/BLK.md) |
| Indic slice vs rest | 0.9872 against 0.9870 | M, local holdout | [D-NRM-02](../decisions/NRM.md) |

## 6. Failure modes and limits

- **Open-set weakness.** `fold` turns every non-Latin, non-Indic character into a space, so a new country in Cyrillic or CJK would lose its names in blocking and features.
- **France-specific lexicons written after seeing test data.** The three French regions and the Lille and Pornic aliases are documented hand-written lexicons, which the rules allow, but they are France-only and are test-informed. We say so.
- `R` becomes `rue` in every country, not only in France.
- The dictionary maps one token to one token; multi-word idioms are not handled.
- The legal-form bitmasks were dropped for stages 0 to 2 because bit values unseen in training behave like a country feature (D-FEA-10); the relation codes stayed.
- The number-by-word blocking compound does not skip street types, although the methodology table says it does ([CF-24](../conflicts.md)).

## 7. Scale

Every step is vectorised over pyarrow arrays and applied to the dictionary of distinct values, never row by row; repairs loop over distinct (country, token) pairs. Cost is linear in records and parallel by country. At 100 times the data the vocabularies per country grow slowly, but the S1-count vocabulary used by the repairs would need to be built per shard and merged. A new script would need its own transliteration table (the Brahmic table is the only one) [E].

## 8. Theory links

[03 String similarity, normalisation and transliteration](../theory/03-string-similarity.md), [02 Blocking](../theory/02-blocking.md), [F06 Text, strings and retrieval](../theory/foundations/F06-text-strings-and-retrieval.md).

## 9. Likely questions

- **How do you handle Hindi names without an external model?** One offset table for nine Brahmic scripts, a consonant skeleton, and a 693-entry dictionary learned from train pairs only.
- **Why not a stronger normaliser?** The held-out misses are not format problems: variant-only pairs in France are predicted 99.84% of the time (D-NRM-05).
- **Are your French lexicons tuned on the test?** Partly informed by it, hand-written and documented, France-only. No labels and no external data are involved.
- **What happens with an unseen country?** Latin-script countries work through per-country statistics; a non-Latin script would not.
- **Why keep om and maa as name words?** They are often the only distinctive word of a short name, and treating them as stop words lost recall.
- More in [qa.md](../qa.md).
