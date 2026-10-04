# Grand Finale: 7 Oct 2026

Team Grenuke is in the **Top 10 of 32,000+ teams (2nd on the list)** and presents live to a jury of senior Amazon scientists.
This folder holds everything for the talk: logistics, the deck, the script and the rehearsal notes. The facts behind every slide come from [`knowledge/`](../knowledge/README.md).

## Logistics

| what | detail |
|---|---|
| finale | **Wed 7 Oct 2026, 09:00–14:00 IST**, virtual (the organisers send the joining link and our slot separately) |
| format | **10-minute presentation + 5-minute Q&A**; the talk is stopped at 10 minutes |
| deck | built on the organisers' template [`MLC_Presentation_template.pptx`](MLC_Presentation_template.pptx), submitted through the organisers' survey |
| deck deadline | **Tue 6 Oct 2026, 14:00 IST**. The e-mail says "Monday, 6 October"; 6 Oct 2026 is a Tuesday, and the date is what counts |
| to do now | confirm participation, and join the organisers' WhatsApp group |

## How finalists were ranked (from the organisers' e-mail)

1. **Private leaderboard** performance carried the most weight.
2. **Blocking strategy and ML novelty**: finer-grained blocking keys (for example city/state) and novel, compute-efficient methods scored higher.
3. **Candidate efficiency**: fewer candidate pairs per record scored higher.

| criterion | our evidence | the question to expect |
|---|---|---|
| leaderboard | public LB **0.990879** (Composite B). Private LB: the organisers publish only rankings, not scores; we are 2nd of the Top 10 | "Why is your local score (0.9913) higher than the leaderboard?" (France has no labels, so it cannot be in the holdout) |
| blocking | per-country multi-view retrieval; repairs (domain names, OCR digits, a learned Indic→Latin dictionary); a learned cut | "Why not city/state blocking keys?" ([Q&A](../knowledge/qa.md)) |
| novelty | self-training for an unlabelled country; per-S1 expected-F0.5 set selection; a 7B re-check of confident predictions | "How do you know self-training did not reinforce its own mistakes?" |
| compute | XGBoost on all pairs, cross-encoders only on the 1.49M uncertain pairs, the 7B only where a second opinion pays | "What would this cost on a billion records?" |
| candidates | retrieval finds **58.4M pairs (about 34 per S1, 99.1% of true holdout pairs)**; the learned cut keeps **6,410,308 = 3.70 per S1, 98.35% of true holdout pairs** (`knowledge/numbers.md`) | "What recall do you lose at 2 candidates per S1?" |

## What the organisers asked the talk to cover

1. **Problem understanding:** framing, and the challenges across the three sources.
2. **Blocking / candidate generation:** how we cut the search space at scale.
3. **Matching model and features:** the architecture, and features for noisy records.
4. **Edge cases:** singletons, unseen countries, noisy names and addresses.
5. **Results and evaluation:** the key metrics, the validation approach, the F0.5 precision-recall trade-off.
6. **Scalability and efficiency:** billions of records, the candidate-pairs-per-entity ratio.
7. **Learnings:** what worked, what didn't, what we would do differently.

**Jury tips (theirs):**
- Know the "why" behind every choice; they value reasoning over results.
- Be honest about limitations.
- Use concrete numbers.
- Think about scale.
- Anticipate tough questions.
- Stay concise.

## Draft running order (10 minutes)

This is a starting point. `deck-outline.md` replaces it once agreed.

| # | slide | time | message |
|---|---|---|---|
| 1 | Team (template title slide) | 0:15 | who we are |
| 2 | The problem and what makes it hard | 1:00 | look-alike decoys, France never seen in training, F0.5 punishes false merges and singletons |
| 3 | Strategy at a glance | 1:00 | spend compute where the uncertainty is; decide the way the metric scores |
| 4 | Blocking | 1:30 | multi-view, per country, repairs, learned cut: 58.4M → 6.4M pairs, 3.70 per S1 (recall 99.1% before the cut, 98.35% after) |
| 5 | Matching model and features | 1:30 | XGBoost cascade, context features, cross-encoders on the uncertain band |
| 6 | Edge cases | 1:30 | singletons (per-S1 set selection), France (guarded self-training), noise (repairs, transliteration) |
| 7 | Results and evaluation | 1:00 | holdout design, paired bootstrap, the leaderboard step chart |
| 8 | Scale and efficiency | 1:00 | cost per stage, the plan for billions |
| 9 | Learnings | 0:45 | what worked, what didn't, what we'd change |
| 10 | Close | 0:15 | one-line summary |

## Plan to the finale

Times are IST. Owners are **proposed**; confirm them in the team call. The live version is in [`docs/ROADMAP.md`](../docs/ROADMAP.md), Phase 6.

| when | what | owner |
|---|---|---|
| Sat 3 Oct night | repo rules and structure for the knowledge base; Ameya's chats and the repo mined into `knowledge/` | Ameya (agent) |
| **Sun 4 Oct 12:00** | Bakshi and Sachi each mine their own chats and notes into `knowledge/people/<member>/` ([`CAPTURE.md`](../knowledge/CAPTURE.md)) and open a PR | Bakshi, Sachi |
| Sun 4 Oct 15:00 | team call: capture status, Q&A leads, who reviews which pages | all |
| Sun 4 Oct evening | knowledge base v2 (the captures merged); each member reviews the pages on their own work; Q&A bank v1 | Ameya + agents; all review |
| Mon 5 Oct | the storyline and `deck-outline.md`; who presents which part; deck v1 on the template, with speaker notes | all; Ameya + agents build |
| Tue 6 Oct morning | rehearsal 1 (timed), fixes | all |
| **Tue 6 Oct 14:00** | **submit the deck** | Ameya |
| Sun 4 – Tue 6 Oct | theory self-tests in pairs; Q&A drills; rehearsals 2 and 3 (Tuesday evening) | all |
| Wed 7 Oct | the finale: test the call setup 30 minutes before our slot | all |

## Files

| file | what |
|---|---|
| [`MLC_Presentation_template.pptx`](MLC_Presentation_template.pptx) | the organisers' template (16:9; a title slide with photo slots, a light content slide, a dark framed slide) |
| [`Grenuke_Finale_Deck.pptx`](Grenuke_Finale_Deck.pptx) | **the deck**: 26 slides on the template in five sections, covering every topic in the organisers' guidelines (Understanding, Building, Feedback, Results, Looking ahead), about 8–9 minutes; charts and diagrams in one colour system, simple animations; the spoken script is in the speaker notes |
| [`build_deck.py`](build_deck.py) | rebuilds the deck from the template (`python finale/build_deck.py`); every number comes from `knowledge/numbers.md` |
| `deck-outline.md` | slide-by-slide content and the numbers behind each slide (to come) |
| `script.md` | the spoken script with timings, and who says what (to come) |
| `rehearsals.md` | timings and feedback from each rehearsal (to come) |
